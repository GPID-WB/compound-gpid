"""Publication and PR observation reconciliation (Phase 4, Step 10).

Injected argv runners cover the closed ``gh`` wire shapes, the Git-based
source/consumer classification, base-before-existing-PR ordering, publication
state distinctions and byte-idempotent covered-payload drift. A temporary Git
repository with a local bare remote exercises the real Git commands without any
live remote mutation.
"""

import json
import subprocess
from pathlib import Path

import pytest

from autopilot import queries as q

SHA = "a" * 40
BSHA = "b" * 40
_GH = ("gh", "pr", "view", "--json",
       "url,number,title,state,baseRefName,headRefName,headRefOid")


def _out(rc, out="", err=""):
    return q.CommandOutcome(rc, out, err)


def _runner(responses):
    def run(argv):
        key = tuple(argv)
        if key not in responses:
            raise AssertionError(f"unscripted argv: {argv}")
        value = responses[key]
        return value() if callable(value) else value
    return run


def _pr_view(*, number=7, state="OPEN", base="origin/dev", head="feature"):
    return _out(0, json.dumps({
        "url": f"https://github.com/o/r/pull/{number}", "number": number,
        "title": "t", "state": state, "baseRefName": base,
        "headRefName": head, "headRefOid": BSHA,
    }))


def _gh_no_pr():
    return _out(1, "", "no open pull requests found")


def _clean_common(branch="feature", head=SHA, base=BSHA):
    return {
        ("git", "status", "--porcelain"): _out(0),
        ("git", "branch", "--show-current"): _out(0, branch),
        ("git", "rev-parse", "HEAD"): _out(0, head),
        ("git", "rev-parse", "--verify", "origin/dev^{commit}"): _out(0, base),
    }


def _with_upstream(responses, name="origin/feature", remote_head=BSHA,
                   counts=None):
    responses[("git", "rev-parse", "--abbrev-ref", "@{u}")] = _out(0, name)
    responses[("git", "rev-parse", f"{name}^{{commit}}")] = _out(0, remote_head)
    if counts is not None:
        responses[("git", "rev-list", "--left-right", "--count", f"{name}...HEAD")] = _out(0, counts)
    return responses


# --- base ordering and wire shapes --------------------------------------------


def test_required_base_precedes_existing_pr_resolution() -> None:
    assert q.require_selected_base("origin/dev") == "origin/dev"
    for missing in (None, "", "   "):
        with pytest.raises(q.QueryError, match="base-required"):
            q.require_selected_base(missing)


def test_pr_view_exact_fields_and_typed_shape() -> None:
    payload = json.loads(
        '{"url": "u", "number": 3, "title": "t", "state": "OPEN", '
        '"baseRefName": "main", "headRefName": "f", "headRefOid": null}'
    )
    pr = q.parse_pr_view(payload, "p")
    assert (pr.number, pr.base_ref_name, pr.head_ref_name) == (3, "main", "f")
    with pytest.raises(q.QueryError, match="number"):
        q.parse_pr_view({**payload, "number": "3"}, "p")
    with pytest.raises(q.QueryError, match="missing"):
        q.parse_pr_view({key: v for key, v in payload.items() if key != "state"}, "p")


def test_rollup_normalizes_checkruns_and_status_contexts() -> None:
    payload = [
        {"__typename": "CheckRun", "name": "CI", "status": "COMPLETED",
         "conclusion": "SUCCESS", "detailsUrl": None},
        {"__typename": "StatusContext", "context": "ctx", "state": "PENDING",
         "targetUrl": None},
    ]
    checks = q.normalize_rollup(payload, "rollup")
    assert checks[0].conclusion == "SUCCESS"
    assert (checks[1].status, checks[1].conclusion) == ("IN_PROGRESS", None)


def test_rollup_rejects_unknown_typename_and_conclusion() -> None:
    with pytest.raises(q.QueryError, match="unknown"):
        q.normalize_rollup([{"__typename": "PullRequestReview"}], "r")
    with pytest.raises(q.QueryError, match="unknown"):
        q.normalize_rollup(
            [{"__typename": "CheckRun", "name": "CI", "status": "COMPLETED",
              "conclusion": "PURPLE", "detailsUrl": None}], "r"
        )


def test_index_routing_distinguishes_source_versus_consumer() -> None:
    marker = q.GitIndexEntry("100644", BSHA, "0", q.SOURCE_MARKER)
    mapping = q.GitIndexEntry("100644", BSHA, "0", q.CANONICAL_MAPPING)
    generator = q.GitIndexEntry("100644", BSHA, "0", q.GENERATOR)
    assert q.classify_routing([marker]).kind == "source"
    assert q.classify_routing([mapping, generator]).kind == "source"
    assert q.classify_routing([]).kind == "consumer"
    with pytest.raises(q.QueryError, match="non-regular"):
        q.parse_index_entries("120000 deadbeef 0\t.link\n", "idx")


# --- publication state classification ----------------------------------


def test_dirty_tree_blocks_before_push() -> None:
    responses = _clean_common()
    responses[("git", "status", "--porcelain")] = _out(0, " M scripts/x.py\n")
    state = q.observe_publication(_runner(responses), selected_base="origin/dev")
    assert state.state == "dirty"


def test_clean_unpushed_without_upstream() -> None:
    responses = _clean_common()
    responses[("git", "rev-parse", "--abbrev-ref", "@{u}")] = _out(1)
    state = q.observe_publication(_runner(responses), selected_base="origin/dev")
    assert state.state == "clean-unpushed"
    # Without an upstream the ahead/behind counts are unknown, never invented.
    assert state.ahead == 0
    assert state.behind == 0


def test_gh_exit_one_without_no_pr_diagnostic_is_an_error() -> None:
    responses = _with_upstream(_clean_common(), remote_head=SHA, counts="0\t0\n")
    for stderr in (
        "", "unexpected error", "connection reset by peer",
        "could not resolve host", "timeout while waiting",
    ):
        responses[_GH] = _out(1, "", stderr)
        with pytest.raises(q.QueryError, match="gh-pr-error"):
            q.observe_publication(_runner(responses), selected_base="origin/dev")


def test_clean_unpushed_ahead_of_remote() -> None:
    responses = _with_upstream(_clean_common(), remote_head=BSHA, counts="0\t2\n")
    state = q.observe_publication(_runner(responses), selected_base="origin/dev")
    assert state.state == "clean-unpushed"
    assert state.ahead == 2


def test_pushed_no_pr() -> None:
    responses = _with_upstream(_clean_common(), remote_head=SHA, counts="0\t0\n")
    responses[_GH] = _gh_no_pr()
    state = q.observe_publication(_runner(responses), selected_base="origin/dev")
    assert state.state == "pushed-no-pr"


def test_existing_matching_pr_is_reused() -> None:
    responses = _with_upstream(_clean_common(), remote_head=SHA, counts="0\t0\n")
    responses[_GH] = _pr_view()
    state = q.observe_publication(_runner(responses), selected_base="origin/dev")
    assert state.state == "existing-matching-pr"
    assert state.pr.number == 7


def test_base_conflict_never_silently_adopts() -> None:
    responses = _with_upstream(_clean_common(), remote_head=SHA, counts="0\t0\n")
    responses[_GH] = _pr_view(base="main")
    with pytest.raises(q.QueryError, match="base-conflict"):
        q.observe_publication(_runner(responses), selected_base="origin/dev")


def test_closed_pr_blocks_duplicates() -> None:
    responses = _with_upstream(_clean_common(), remote_head=SHA, counts="0\t0\n")
    responses[_GH] = _pr_view(state="MERGED")
    with pytest.raises(q.QueryError, match="pr-closed"):
        q.observe_publication(_runner(responses), selected_base="origin/dev")


def test_gh_auth_failure_is_never_a_fallback() -> None:
    responses = _with_upstream(_clean_common(), remote_head=SHA, counts="0\t0\n")
    responses[_GH] = _out(1, "", "gh: not authenticated; run gh auth login")
    with pytest.raises(q.QueryError, match="gh-auth"):
        q.observe_publication(_runner(responses), selected_base="origin/dev")


def test_diverged_and_remote_ahead_block() -> None:
    diverged = _with_upstream(_clean_common(), remote_head=BSHA, counts="1\t1\n")
    with pytest.raises(q.QueryError, match="diverged"):
        q.observe_publication(_runner(diverged), selected_base="origin/dev")

    behind = _with_upstream(_clean_common(), remote_head=BSHA, counts="2\t0\n")
    with pytest.raises(q.QueryError, match="remote-ahead"):
        q.observe_publication(_runner(behind), selected_base="origin/dev")


def test_missing_base_blocks() -> None:
    with pytest.raises(q.QueryError, match="base-required"):
        q.observe_publication(_runner({}), selected_base=None)


# --- coverage inventory and idempotent drift ---------------------------


def _ident(path, status="present", sha="c" * 64, size=3):
    return q.PathIdentity(path, status, sha if status == "present" else None,
                          size if status == "present" else None)


def _coverage(*entries):
    return q.coverage_of(list(entries))


def test_coverage_digest_and_idempotency() -> None:
    expected = _coverage(_ident("a.py"), _ident("b.py"))
    assert q.idempotent(expected, _coverage(_ident("a.py"), _ident("b.py")))
    assert q.coverage_drift(expected, _coverage(_ident("a.py", sha="d" * 64), _ident("b.py"))) == ("a.py",)
    assert q.coverage_drift(expected, _coverage(_ident("a.py"), _ident("b.py"), _ident("c.py"))) == ("c.py",)
    assert q.coverage_drift(expected, _coverage(_ident("a.py"))) == ("b.py",)
    with pytest.raises(q.QueryError, match="duplicate"):
        q.coverage_of([_ident("a.py"), _ident("a.py")])


# --- temporary git repository integration (real git, faked gh) ---------


def _run_git(repo: Path, *args: str):
    return subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=False, timeout=30
    )


def _head(repo: Path) -> str:
    return _run_git(repo, "rev-parse", "HEAD").stdout.strip()


def _setup_repo(repo: Path) -> None:
    remote = repo.parent / "remote.git"
    remote.mkdir(parents=True, exist_ok=True)
    repo.mkdir(parents=True, exist_ok=True)
    _run_git(remote, "init", "-q", "--bare")
    _run_git(repo, "init", "-q", "-b", "dev")
    _run_git(repo, "config", "user.email", "a@example.com")
    _run_git(repo, "config", "user.name", "A")
    (repo / "f.txt").write_text("base", encoding="utf-8")
    _run_git(repo, "add", "f.txt")
    _run_git(repo, "commit", "-qm", "base")
    _run_git(repo, "remote", "add", "origin", str(remote))
    _run_git(repo, "push", "-qu", "origin", "dev")
    _run_git(repo, "checkout", "-qb", "feature")
    (repo / "f.txt").write_text("feature", encoding="utf-8")
    _run_git(repo, "commit", "-qam", "feature")
    _run_git(repo, "push", "-qu", "origin", "feature")


def _real_git_runner(repo: Path, gh_response):
    def run(argv):
        if argv[0] == "gh":
            return gh_response
        result = _run_git(repo, *argv[1:])
        return q.CommandOutcome(result.returncode, result.stdout, result.stderr)
    return run


def test_temp_repo_pushed_no_pr_via_real_git(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _setup_repo(repo)
    state = q.observe_publication(
        _real_git_runner(repo, _gh_no_pr()), branch="feature", selected_base="origin/dev"
    )
    assert state.state == "pushed-no-pr"
    assert state.head == _head(repo)


def test_temp_repo_existing_matching_pr_via_real_git(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _setup_repo(repo)
    response = q.CommandOutcome(0, json.dumps({
        "url": "https://github.com/o/r/pull/1", "number": 1, "title": "t",
        "state": "OPEN", "baseRefName": "origin/dev", "headRefName": "feature",
        "headRefOid": _head(repo),
    }), "")
    state = q.observe_publication(
        _real_git_runner(repo, response), branch="feature", selected_base="origin/dev"
    )
    assert state.state == "existing-matching-pr"
    assert state.pr.number == 1


def test_temp_repo_dirty_tree_via_real_git(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _setup_repo(repo)
    (repo / "f.txt").write_text("dirty", encoding="utf-8")
    state = q.observe_publication(
        _real_git_runner(repo, _gh_no_pr()), branch="feature", selected_base="origin/dev"
    )
    assert state.state == "dirty"