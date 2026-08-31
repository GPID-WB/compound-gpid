"""Contract tests for the Compound GPID repository registry utility.

These tests intentionally precede ``cg_compound_gpid_rd_registry.py``. They use
only temporary registries and define the complete Phase 1 Step 1 contract.
"""
from __future__ import annotations

import ast
import copy
from decimal import Decimal
import doctest
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Mapping, Set, Tuple
import urllib.request
import warnings

import pytest

import secure_fs
from secure_fs import ExpectedFileState, SecureMutationError

import cg_compound_gpid_rd_registry as registry


EXPECTED_SCHEMA_VERSION = "compound-gpid-competitive-reviews-v1"
REGISTRY_RELATIVE_PATH = Path(".cg-docs/competitive-reviews/repos.json")
MAX_REGISTRY_BYTES = 1_048_576


def _entry(
    repo_id: str = "alpha",
    owner: str = "example",
    repository: str = "alpha",
    short_name: str = "A",
    **overrides: Any,
) -> Dict[str, Any]:
    url = "https://github.com/{}/{}".format(owner, repository)
    result = {
        "id": repo_id,
        "url": url,
        "releasesUrl": url + "/releases",
        "shortName": short_name,
        "lastReviewedRelease": "v1.0.0",
        "lastReviewDate": "2026-08-28",
    }
    result.update(overrides)
    if result["lastReviewedRelease"] is None and "lastReviewDate" not in overrides:
        result.pop("lastReviewDate", None)
    return result


def _registry_data(repos: List[Mapping[str, Any]]) -> Dict[str, Any]:
    return {
        "schemaVersion": EXPECTED_SCHEMA_VERSION,
        "lastFullReview": "2026-08-28",
        "repos": [dict(repo) for repo in repos],
    }


def _render_fixture(data: Any) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _registry_path(root: Path) -> Path:
    return root / REGISTRY_RELATIVE_PATH


def _has_option(arguments: List[str], names: Set[str]) -> bool:
    return any(
        argument in names
        or any(argument.startswith(name + "=") for name in names)
        for argument in arguments
    )


def _write_registry(
    root: Path,
    data: Any = None,
    *,
    raw: bytes = b"",
) -> Path:
    path = _registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    if data is not None:
        raw = _render_fixture(data)
    path.write_bytes(raw)
    return path


@pytest.fixture
def valid_registry_root(tmp_path: Path) -> Path:
    _write_registry(tmp_path, _registry_data([_entry()]))
    return tmp_path


@pytest.fixture
def empty_registry_root(tmp_path: Path) -> Path:
    _write_registry(tmp_path, _registry_data([]))
    return tmp_path


@pytest.fixture
def malformed_registry_root(tmp_path: Path) -> Path:
    _write_registry(tmp_path, raw=b'{"schemaVersion":')
    return tmp_path


@pytest.fixture
def unknown_field_registry_root(tmp_path: Path) -> Path:
    data = {
        "schemaVersion": EXPECTED_SCHEMA_VERSION,
        "rootExtension": {"enabled": True},
        "lastFullReview": "2026-08-28",
        "repos": [
            _entry(
                extension={"owner": "maintainer"},
                disabled=False,
            )
        ],
        "trailingExtension": [1, 2, 3],
    }
    _write_registry(tmp_path, data)
    return tmp_path


def _invoke(
    root: Path,
    arguments: List[str],
    capsys: Any,
) -> Tuple[int, str, str]:
    authorized = list(arguments)
    path = _registry_path(root)
    if authorized and authorized[0] in {"review-repo", "review-full"}:
        try:
            data = json.loads(
                path.read_text("utf-8"),
                parse_float=Decimal,
                parse_int=Decimal,
            )
        except (OSError, UnicodeError, json.JSONDecodeError):
            data = None
        if data is not None and authorized[0] == "review-repo":
            repo_id = authorized[authorized.index("--id") + 1]
            entry = next(item for item in data["repos"] if item["id"] == repo_id)
            expected_release_flags = {
                "--expected-last-reviewed-release",
                "--expected-last-reviewed-release-null",
            }
            if not _has_option(authorized, expected_release_flags):
                if entry["lastReviewedRelease"] is None:
                    authorized.append("--expected-last-reviewed-release-null")
                else:
                    authorized.extend(
                        [
                            "--expected-last-reviewed-release",
                            entry["lastReviewedRelease"],
                        ]
                    )
            expected_date_flags = {
                "--expected-last-review-date",
                "--expected-last-review-date-null",
                "--expected-last-review-date-absent",
            }
            if not _has_option(authorized, expected_date_flags):
                if "lastReviewDate" not in entry:
                    authorized.append("--expected-last-review-date-absent")
                elif entry["lastReviewDate"] is None:
                    authorized.append("--expected-last-review-date-null")
                else:
                    authorized.extend(
                        ["--expected-last-review-date", entry["lastReviewDate"]]
                    )
        if "--check-only" in authorized and "--expected-chain-sha256" not in authorized:
            authorized.extend(
                ["--expected-chain-sha256", hashlib.sha256(path.read_bytes()).hexdigest()]
            )
        if (
            data is not None
            and authorized[0] == "review-full"
            and "--check-only" in authorized
            and "--expected-scope-digest-sha256" not in authorized
        ):
            authorized.extend(
                ["--expected-scope-digest-sha256", registry._scope_digest(data)]
            )
    if (
        authorized
        and authorized[0] in {"add", "remove"}
        and "--check-only" not in authorized
        and "--expected-sha256" not in authorized
    ):
        path = _registry_path(root)
        authorized.extend(
            ["--expected-sha256", hashlib.sha256(path.read_bytes()).hexdigest()]
        )
        if authorized[0] == "remove" and "--expected-url" not in authorized:
            expected_url = "https://github.com/example/alpha"
            try:
                data = json.loads(path.read_text("utf-8"))
                repo_id = authorized[authorized.index("--id") + 1]
                expected_url = next(
                    (
                        item["url"]
                        for item in data["repos"]
                        if item["id"] == repo_id
                    ),
                    expected_url,
                )
            except (KeyError, TypeError, ValueError):
                pass
            authorized.extend(["--expected-url", expected_url])
    exit_code = registry.main(["--root", str(root)] + authorized)
    captured = capsys.readouterr()
    return exit_code, captured.out, captured.err


def _success_line(
    action: str,
    changed: bool,
    repo: Mapping[str, Any],
    before_sha256: str,
    after_sha256: str,
    before_scope_digest: str,
    after_scope_digest: str,
) -> str:
    payload = {
        "action": action,
        "changed": changed,
        "beforeSha256": before_sha256,
        "afterSha256": after_sha256,
        "beforeScopeDigestSha256": before_scope_digest,
        "afterScopeDigestSha256": after_scope_digest,
        "repo": dict(repo),
        "warnings": [],
    }
    return json.dumps(payload, separators=(",", ":")) + "\n"


def _assert_failure(
    root: Path,
    arguments: List[str],
    capsys: Any,
    *message_terms: str,
) -> str:
    path = _registry_path(root)
    existed_before = path.exists() or path.is_symlink()
    before = path.read_bytes() if existed_before else None

    exit_code, stdout, stderr = _invoke(root, arguments, capsys)

    assert exit_code == 1
    assert stdout == ""
    assert stderr
    assert "Traceback" not in stderr
    assert len(stderr.rstrip("\n").splitlines()) == 1
    lowered = stderr.lower()
    for term in message_terms:
        assert term.lower() in lowered
    assert (path.exists() or path.is_symlink()) is existed_before
    if existed_before:
        assert path.read_bytes() == before
    return stderr


def _assert_ambiguous(
    root: Path,
    arguments: List[str],
    capsys: Any,
    *message_terms: str,
) -> str:
    exit_code, stdout, stderr = _invoke(root, arguments, capsys)
    assert exit_code == 3
    assert stdout == ""
    assert stderr.startswith("Ambiguous: ")
    assert "Traceback" not in stderr
    assert len(stderr.rstrip("\n").splitlines()) == 1
    lowered = stderr.casefold()
    for term in message_terms:
        assert term.casefold() in lowered
    return stderr


def _proposed_repo(
    repo_id: str,
    url: str,
    short_name: str,
) -> Dict[str, Any]:
    return {
        "id": repo_id,
        "url": url,
        "releasesUrl": url + "/releases",
        "shortName": short_name,
        "lastReviewedRelease": None,
    }


def _short_name_collision_entries(base: str, through: int) -> List[Dict[str, Any]]:
    entries = []
    suffixes = [None] + list(range(2, through + 1))
    for index, suffix in enumerate(suffixes):
        suffix_text = "" if suffix is None else str(suffix)
        candidate = base[: 10 - len(suffix_text)] + suffix_text
        entries.append(
            _entry(
                repo_id="existing-{}".format(index),
                owner="existing",
                repository="repo-{}".format(index),
                short_name=candidate,
            )
        )
    return entries


def test_contract_constants_are_exact() -> None:
    assert registry.EXPECTED_SCHEMA_VERSION == EXPECTED_SCHEMA_VERSION
    assert registry.MAX_REGISTRY_BYTES == MAX_REGISTRY_BYTES
    assert registry.MAX_RELEASE_LENGTH == 128
    assert registry.REGISTRY_RELATIVE_PATH == REGISTRY_RELATIVE_PATH


def test_tracked_registry_prompt_and_utility_share_exact_schema_version() -> None:
    root = Path(__file__).resolve().parents[2]
    registry_path = root / REGISTRY_RELATIVE_PATH
    prompt_path = root / ".github/prompts/cg-compound-gpid-rd.prompt.md"
    source_bytes = registry_path.read_bytes()
    tracked_registry = json.loads(source_bytes.decode("utf-8"))

    assert tracked_registry["schemaVersion"] == registry.EXPECTED_SCHEMA_VERSION
    try:
        prompt_text = prompt_path.read_text(encoding="utf-8")
        prompt_schema = re.search(
            r"Verify that `schemaVersion` equals\s*`\"([^\"]+)\"`",
            prompt_text,
        )
        assert prompt_schema is not None
        assert prompt_schema.group(1) == registry.EXPECTED_SCHEMA_VERSION
    finally:
        assert registry_path.read_bytes() == source_bytes


def test_python_38_guard_precedes_project_local_import() -> None:
    source = Path(registry.__file__).read_text(encoding="utf-8")
    ast.parse(source, feature_version=8)

    guard_index = source.index("sys.version_info < (3, 8)")
    secure_fs_imports = [
        index
        for token in ("import secure_fs", "from secure_fs import")
        for index in [source.find(token)]
        if index >= 0
    ]
    assert secure_fs_imports
    assert guard_index < min(secure_fs_imports)


@pytest.mark.parametrize(
    ("raw_url", "normalized"),
    [
        (
            "https://github.com/Acme/Widget",
            "https://github.com/Acme/Widget",
        ),
        (
            "https://github.com/Acme/Widget/",
            "https://github.com/Acme/Widget",
        ),
        (
            "https://github.com/Acme/Widget.git",
            "https://github.com/Acme/Widget",
        ),
        (
            "https://github.com/Acme/Widget.git/",
            "https://github.com/Acme/Widget",
        ),
        (
            "https://github.com/Acme/Widget.git.git",
            "https://github.com/Acme/Widget.git",
        ),
    ],
)
def test_normalize_github_url_accepts_documented_forms(
    raw_url: str,
    normalized: str,
) -> None:
    assert registry.normalize_github_url(raw_url) == normalized


@pytest.mark.parametrize(
    ("raw_url", "term"),
    [
        ("http://github.com/owner/repo", "https"),
        ("git://github.com/owner/repo", "https"),
        ("https://gitlab.com/owner/repo", "github.com"),
        ("https://www.github.com/owner/repo", "github.com"),
        ("https://user@github.com/owner/repo", "credential"),
        ("https://user:pass@github.com/owner/repo", "credential"),
        ("https://github.com:443/owner/repo", "port"),
        ("https://github.com/owner/repo?tab=readme", "query"),
        ("https://github.com/owner/repo#readme", "fragment"),
        ("https://github.com/owner/repo/issues", "segment"),
        ("https://github.com/owner/repo//", "segment"),
        ("https://github.com/owner", "owner"),
        ("https://github.com//repo", "owner"),
        ("https://github.com///", "owner"),
        ("github.com/owner/repo", "https"),
        ("https://github.com/-owner/repo", "owner"),
        ("https://github.com/owner-/repo", "owner"),
        ("https://github.com/a--b/repo", "owner"),
        ("https://github.com/owner_name/repo", "owner"),
        ("https://github.com/own.er/repo", "owner"),
        ("https://github.com/own\u00e9r/repo", "owner"),
        ("https://github.com/owner+name/repo", "owner"),
        ("https://github.com/owner/re po", "repository"),
        ("https://github.com/owner/r\u00e9po", "repository"),
        ("https://github.com/owner/repo+tools", "repository"),
        ("https://github.com/owner/...", "repository"),
        ("https://github.com/owner/.git", "repository"),
        ("https://github.com/owner/repo%2Fother", "repository"),
        ("https://github.com/{}/repo".format("a" * 40), "owner"),
        ("https://github.com/owner/{}".format("r" * 101), "repository"),
    ],
)
def test_cli_rejects_malformed_urls_without_changing_registry(
    valid_registry_root: Path,
    capsys: Any,
    raw_url: str,
    term: str,
) -> None:
    _assert_failure(
        valid_registry_root,
        ["add", "--url", raw_url, "--check-only"],
        capsys,
        term,
    )


@pytest.mark.parametrize(
    ("owner", "repository"),
    [
        ("a", "r"),
        ("a" * 39, "r" * 100),
        ("a-b", ".valid-repo_name"),
    ],
)
def test_url_name_boundaries_are_accepted(
    empty_registry_root: Path,
    capsys: Any,
    owner: str,
    repository: str,
) -> None:
    url = "https://github.com/{}/{}".format(owner, repository)
    before = _registry_path(empty_registry_root).read_bytes()

    exit_code, stdout, stderr = _invoke(
        empty_registry_root,
        ["add", "--url", url, "--check-only"],
        capsys,
    )

    assert exit_code == 0
    assert json.loads(stdout)["repo"]["url"] == url
    assert stderr == ""
    assert _registry_path(empty_registry_root).read_bytes() == before


@pytest.mark.parametrize(
    ("url", "expected_id"),
    [
        ("https://github.com/Acme/.github", "github"),
        ("https://github.com/Acme/-repo", "repo"),
        ("https://github.com/Acme/_repo", "repo"),
        ("https://github.com/Acme/repo__tools", "repo-tools"),
        ("https://github.com/Acme-Tools/__", "acme-tools-repo"),
    ],
)
def test_id_derivation_strips_slug_edges_and_uses_owner_fallback(
    empty_registry_root: Path,
    capsys: Any,
    url: str,
    expected_id: str,
) -> None:
    exit_code, stdout, stderr = _invoke(
        empty_registry_root,
        ["add", "--url", url, "--check-only"],
        capsys,
    )

    assert exit_code == 0
    assert json.loads(stdout)["repo"]["id"] == expected_id
    assert stderr == ""


def test_id_collision_uses_owner_qualified_slug(
    tmp_path: Path,
    capsys: Any,
) -> None:
    data = _registry_data(
        [_entry("widget", "other", "widget", "OtherWidg")]
    )
    _write_registry(tmp_path, data)

    exit_code, stdout, stderr = _invoke(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
    )

    assert exit_code == 0
    assert json.loads(stdout)["repo"]["id"] == "acme-widget"
    assert stderr == ""


def test_long_id_uses_casefolded_url_hash_shortening(
    empty_registry_root: Path,
    capsys: Any,
) -> None:
    repository = "A" * 100
    url = "https://github.com/Acme/{}".format(repository)
    digest = hashlib.sha256(url.casefold().encode("utf-8")).hexdigest()[:8]
    expected_id = "{}-{}".format("a" * 41, digest)

    exit_code, stdout, stderr = _invoke(
        empty_registry_root,
        ["add", "--url", url, "--check-only"],
        capsys,
    )

    assert exit_code == 0
    assert json.loads(stdout)["repo"]["id"] == expected_id
    assert len(expected_id) == 50
    assert stderr == ""


def test_id_collision_exhaustion_fails_without_change(
    tmp_path: Path,
    capsys: Any,
) -> None:
    data = _registry_data(
        [
            _entry("widget", "other", "widget", "OW"),
            _entry("acme-widget", "third", "widget", "TW"),
        ]
    )
    _write_registry(tmp_path, data)

    _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
        "id",
        "unique",
    )


def test_duplicate_normalized_url_is_case_insensitive_and_reports_existing_id(
    tmp_path: Path,
    capsys: Any,
) -> None:
    data = _registry_data(
        [_entry("registered-id", "Acme", "Widget", "Registered")]
    )
    _write_registry(tmp_path, data)

    stderr = _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget.git/",
            "--check-only",
        ],
        capsys,
        "duplicate",
        "registered-id",
    )

    assert "https://github.com/acme/widget" in stderr.casefold()


@pytest.mark.parametrize(
    ("url", "expected_short_name"),
    [
        ("https://github.com/acme/alpha-beta", "AB"),
        ("https://github.com/acme/alpha__beta---gamma", "ABG"),
        ("https://github.com/acme/SuperPowerTool", "SuperPower"),
        ("https://github.com/Acme-Tools/__", "AcmeTools"),
    ],
)
def test_short_name_derivation_is_deterministic(
    empty_registry_root: Path,
    capsys: Any,
    url: str,
    expected_short_name: str,
) -> None:
    exit_code, stdout, stderr = _invoke(
        empty_registry_root,
        ["add", "--url", url, "--check-only"],
        capsys,
    )

    assert exit_code == 0
    assert json.loads(stdout)["repo"]["shortName"] == expected_short_name
    assert stderr == ""


def test_short_name_collision_uses_smallest_case_insensitive_suffix(
    tmp_path: Path,
    capsys: Any,
) -> None:
    _write_registry(
        tmp_path,
        _registry_data(
            [_entry("existing", "other", "existing", "ab")]
        ),
    )

    exit_code, stdout, stderr = _invoke(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/alpha-beta",
            "--check-only",
        ],
        capsys,
    )

    assert exit_code == 0
    assert json.loads(stdout)["repo"]["shortName"] == "AB2"
    assert stderr == ""


@pytest.mark.parametrize(
    ("through", "expected"),
    [(9, "abcdefgh10"), (98, "abcdefgh99")],
)
def test_short_name_suffix_truncates_base_to_ten_characters(
    tmp_path: Path,
    capsys: Any,
    through: int,
    expected: str,
) -> None:
    base = "abcdefghij"
    _write_registry(
        tmp_path,
        _registry_data(_short_name_collision_entries(base, through)),
    )

    exit_code, stdout, stderr = _invoke(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/abcdefghij",
            "--check-only",
        ],
        capsys,
    )

    assert exit_code == 0
    assert json.loads(stdout)["repo"]["shortName"] == expected
    assert len(expected) == 10
    assert stderr == ""


def test_short_name_collision_exhaustion_fails_without_change(
    tmp_path: Path,
    capsys: Any,
) -> None:
    _write_registry(
        tmp_path,
        _registry_data(_short_name_collision_entries("ABC", 99)),
    )

    _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/a-b-c",
            "--check-only",
        ],
        capsys,
        "short",
        "unique",
    )


def test_pure_add_transform_does_not_mutate_input_and_matches_cli(
    empty_registry_root: Path,
    capsys: Any,
) -> None:
    source = _registry_data([])
    source_before = copy.deepcopy(source)
    transformed, proposed = registry.add_repository(
        source,
        "https://github.com/Acme/alpha-tools.git/",
    )

    assert source == source_before
    assert transformed["repos"] == [proposed]
    assert proposed == _proposed_repo(
        "alpha-tools",
        "https://github.com/Acme/alpha-tools",
        "AT",
    )

    exit_code, stdout, stderr = _invoke(
        empty_registry_root,
        [
            "add",
            "--url",
            "https://github.com/Acme/alpha-tools.git/",
            "--check-only",
        ],
        capsys,
    )
    assert exit_code == 0
    assert json.loads(stdout)["repo"] == proposed
    assert stderr == ""


def test_pure_validation_and_rendering_preserve_data_and_exact_format() -> None:
    source = _registry_data([_entry(lastReviewedRelease=None)])
    source_before = copy.deepcopy(source)

    registry.validate_registry(source)
    rendered = registry.render_registry(source)

    assert source == source_before
    assert rendered == _render_fixture(source)
    assert rendered.endswith(b"\n")


def test_add_to_nonempty_registry_has_exact_output_and_review_state(
    valid_registry_root: Path,
    capsys: Any,
) -> None:
    path = _registry_path(valid_registry_root)
    before = path.read_bytes()
    expected_repo = _proposed_repo(
        "beta-tools",
        "https://github.com/Acme/beta-tools",
        "BT",
    )

    exit_code, stdout, stderr = _invoke(
        valid_registry_root,
        ["add", "--url", "https://github.com/Acme/beta-tools.git/"],
        capsys,
    )

    assert exit_code == 0
    assert stderr == ""
    raw = path.read_bytes()
    assert stdout == _success_line(
        "add",
        True,
        expected_repo,
        hashlib.sha256(before).hexdigest(),
        hashlib.sha256(raw).hexdigest(),
        registry._scope_digest(json.loads(before.decode("utf-8"))),
        registry._scope_digest(json.loads(raw.decode("utf-8"))),
    )
    assert raw.endswith(b"\n")
    assert not raw.endswith(b"\n\n")
    updated = json.loads(raw.decode("utf-8"))
    assert [item["id"] for item in updated["repos"]] == ["alpha", "beta-tools"]
    assert updated["repos"][-1] == expected_repo
    assert "lastReviewDate" not in updated["repos"][-1]


def test_add_to_empty_registry_is_valid(
    empty_registry_root: Path,
    capsys: Any,
) -> None:
    exit_code, stdout, stderr = _invoke(
        empty_registry_root,
        ["add", "--url", "https://github.com/acme/widget"],
        capsys,
    )

    assert exit_code == 0
    response = json.loads(stdout)
    assert response["action"] == "add"
    assert response["changed"] is True
    assert response["repo"] == _proposed_repo(
        "widget",
        "https://github.com/acme/widget",
        "widget",
    )
    assert response["warnings"] == []
    assert re.fullmatch(r"[0-9a-f]{64}", response["beforeSha256"])
    assert re.fullmatch(r"[0-9a-f]{64}", response["afterSha256"])
    assert stderr == ""
    updated = json.loads(_registry_path(empty_registry_root).read_text("utf-8"))
    assert len(updated["repos"]) == 1


def test_add_preserves_unknown_fields_and_field_order(
    unknown_field_registry_root: Path,
    capsys: Any,
) -> None:
    exit_code, _, stderr = _invoke(
        unknown_field_registry_root,
        ["add", "--url", "https://github.com/acme/beta"],
        capsys,
    )

    assert exit_code == 0
    assert stderr == ""
    path = _registry_path(unknown_field_registry_root)
    raw = path.read_bytes()
    updated = json.loads(raw.decode("utf-8"))
    assert list(updated) == [
        "schemaVersion",
        "rootExtension",
        "lastFullReview",
        "repos",
        "trailingExtension",
    ]
    assert updated["rootExtension"] == {"enabled": True}
    assert updated["trailingExtension"] == [1, 2, 3]
    assert updated["repos"][0]["extension"] == {"owner": "maintainer"}
    assert updated["repos"][0]["disabled"] is False
    assert list(updated["repos"][0]) == [
        "id",
        "url",
        "releasesUrl",
        "shortName",
        "lastReviewedRelease",
        "lastReviewDate",
        "extension",
        "disabled",
    ]
    assert raw == registry.render_registry(updated)


def test_check_only_has_exact_output_and_preserves_exact_bytes(
    valid_registry_root: Path,
    capsys: Any,
) -> None:
    path = _registry_path(valid_registry_root)
    before = path.read_bytes()
    proposed = _proposed_repo(
        "beta-tools",
        "https://github.com/acme/beta-tools",
        "BT",
    )

    exit_code, stdout, stderr = _invoke(
        valid_registry_root,
        [
            "add",
            "--url",
            "https://github.com/acme/beta-tools/",
            "--check-only",
        ],
        capsys,
    )

    assert exit_code == 0
    transformed, _ = registry.add_repository(
        json.loads(before.decode("utf-8")),
        "https://github.com/acme/beta-tools/",
    )
    assert stdout == _success_line(
        "add",
        False,
        proposed,
        hashlib.sha256(before).hexdigest(),
        hashlib.sha256(registry.render_registry(transformed)).hexdigest(),
        registry._scope_digest(json.loads(before.decode("utf-8"))),
        registry._scope_digest(transformed),
    )
    assert stderr == ""
    assert path.read_bytes() == before


def test_check_only_never_writes_or_fetches_network(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("check-only attempted an external effect")

    monkeypatch.setattr(registry.secure_fs, "secure_write_bytes", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)

    exit_code, stdout, stderr = _invoke(
        valid_registry_root,
        [
            "add",
            "--url",
            "https://github.com/acme/beta",
            "--check-only",
        ],
        capsys,
    )

    assert exit_code == 0
    assert json.loads(stdout)["changed"] is False
    assert stderr == ""


def test_duplicate_check_stops_before_writer_or_network(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("duplicate check attempted an external effect")

    monkeypatch.setattr(registry.secure_fs, "secure_write_bytes", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)

    _assert_failure(
        valid_registry_root,
        [
            "add",
            "--url",
            "https://github.com/EXAMPLE/ALPHA.git",
            "--check-only",
        ],
        capsys,
        "duplicate",
        "alpha",
    )


def test_mutating_add_rejects_state_changed_after_check_only(
    empty_registry_root: Path,
    capsys: Any,
) -> None:
    url = "https://github.com/acme/widget"
    first_code, first_stdout, first_stderr = _invoke(
        empty_registry_root,
        ["add", "--url", url, "--check-only"],
        capsys,
    )
    assert first_code == 0
    plan = json.loads(first_stdout)
    assert plan["repo"]["id"] == "widget"
    assert first_stderr == ""

    concurrent = _registry_data(
        [_entry("widget", "other", "widget", "widget")]
    )
    _write_registry(empty_registry_root, concurrent)

    second_code, second_stdout, second_stderr = _invoke(
        empty_registry_root,
        [
            "add",
            "--url",
            url,
            "--expected-sha256",
            plan["beforeSha256"],
        ],
        capsys,
    )
    assert second_code == 1
    assert second_stdout == ""
    assert "stale" in second_stderr.casefold()
    assert json.loads(_registry_path(empty_registry_root).read_text("utf-8")) == concurrent


def test_pure_remove_transform_is_case_sensitive_and_does_not_mutate_input() -> None:
    source = _registry_data([_entry()])
    source_before = copy.deepcopy(source)

    transformed, removed = registry.remove_repository(source, "alpha", "alpha")

    assert source == source_before
    assert transformed["repos"] == []
    assert removed == source["repos"][0]
    with pytest.raises(registry.RegistryError, match="confirm|match"):
        registry.remove_repository(source, "alpha", "Alpha")
    assert source == source_before


def test_remove_has_exact_output_and_preserves_history_files(
    valid_registry_root: Path,
    capsys: Any,
) -> None:
    history = valid_registry_root / ".cg-docs/competitive-reviews/assessment-alpha.md"
    delta = valid_registry_root / ".cg-docs/competitive-reviews/deltas/alpha.md"
    history.write_bytes(b"historical assessment\n")
    delta.parent.mkdir(parents=True)
    delta.write_bytes(b"historical delta\n")
    removed = _entry()
    path = _registry_path(valid_registry_root)
    before = path.read_bytes()

    exit_code, stdout, stderr = _invoke(
        valid_registry_root,
        ["remove", "--id", "alpha", "--confirm-id", "alpha"],
        capsys,
    )

    assert exit_code == 0
    assert stderr == ""
    after = path.read_bytes()
    assert stdout == _success_line(
        "remove",
        True,
        removed,
        hashlib.sha256(before).hexdigest(),
        hashlib.sha256(after).hexdigest(),
        registry._scope_digest(json.loads(before.decode("utf-8"))),
        registry._scope_digest(json.loads(after.decode("utf-8"))),
    )
    updated = json.loads(after.decode("utf-8"))
    assert updated["repos"] == []
    assert history.read_bytes() == b"historical assessment\n"
    assert delta.read_bytes() == b"historical delta\n"


@pytest.mark.parametrize(
    ("repo_id", "confirmation", "terms"),
    [
        ("Alpha", "Alpha", ("not found", "alpha")),
        ("missing", "missing", ("not found", "alpha")),
        ("alpha", "Alpha", ("confirm", "exact")),
        ("alpha", "alpha ", ("confirm", "exact")),
        ("alpha", " alpha", ("confirm", "exact")),
    ],
)
def test_remove_rejects_missing_or_mismatched_exact_id_without_change(
    valid_registry_root: Path,
    capsys: Any,
    repo_id: str,
    confirmation: str,
    terms: Tuple[str, ...],
) -> None:
    _assert_failure(
        valid_registry_root,
        ["remove", "--id", repo_id, "--confirm-id", confirmation],
        capsys,
        *terms,
    )


def test_remove_final_entry_is_valid(
    valid_registry_root: Path,
    capsys: Any,
) -> None:
    exit_code, stdout, stderr = _invoke(
        valid_registry_root,
        ["remove", "--id", "alpha", "--confirm-id", "alpha"],
        capsys,
    )

    assert exit_code == 0
    assert json.loads(stdout)["repo"]["id"] == "alpha"
    assert stderr == ""
    assert json.loads(_registry_path(valid_registry_root).read_text("utf-8"))[
        "repos"
    ] == []


def test_remove_preserves_unknown_fields_and_unchanged_entry_order(
    tmp_path: Path,
    capsys: Any,
) -> None:
    first = _entry("first", "one", "first", "ONE", custom="keep-first")
    middle = _entry("middle", "two", "middle", "TWO", custom="remove-me")
    last = _entry("last", "three", "last", "THREE", custom="keep-last")
    data = {
        "schemaVersion": EXPECTED_SCHEMA_VERSION,
        "unknownBefore": 1,
        "repos": [first, middle, last],
        "unknownAfter": {"keep": True},
    }
    _write_registry(tmp_path, data)

    exit_code, _, stderr = _invoke(
        tmp_path,
        ["remove", "--id", "middle", "--confirm-id", "middle"],
        capsys,
    )

    assert exit_code == 0
    assert stderr == ""
    updated = json.loads(_registry_path(tmp_path).read_text("utf-8"))
    assert list(updated) == [
        "schemaVersion",
        "unknownBefore",
        "repos",
        "unknownAfter",
    ]
    assert updated["unknownAfter"] == {"keep": True}
    assert updated["repos"] == [first, last]


@pytest.mark.parametrize(
    ("raw", "term"),
    [
        (b'{"schemaVersion":', "json"),
        (b"\xff\xfe", "utf-8"),
        (
            b'{"schemaVersion":"compound-gpid-competitive-reviews-v1",'
            b'"schemaVersion":"compound-gpid-competitive-reviews-v1","repos":[]}',
            "duplicate",
        ),
        (
            b'{"schemaVersion":"compound-gpid-competitive-reviews-v1",'
            b'"repos":[{"id":"a","id":"b","url":"https://github.com/a/b",'
            b'"releasesUrl":"https://github.com/a/b/releases",'
            b'"shortName":"B","lastReviewedRelease":null}]}',
            "duplicate",
        ),
        (
            b'{"schemaVersion":"compound-gpid-competitive-reviews-v1",'
            b'"repos":[],"extension":NaN}',
            "nan",
        ),
        (
            b'{"schemaVersion":"compound-gpid-competitive-reviews-v1",'
            b'"repos":[],"extension":Infinity}',
            "infinity",
        ),
        (
            b'{"schemaVersion":"compound-gpid-competitive-reviews-v1",'
            b'"repos":[],"extension":-Infinity}',
            "infinity",
        ),
    ],
    ids=[
        "malformed-json",
        "invalid-utf8",
        "duplicate-root-key",
        "duplicate-entry-key",
        "nan",
        "infinity",
        "negative-infinity",
    ],
)
def test_strict_json_rejections_preserve_source_bytes(
    tmp_path: Path,
    capsys: Any,
    raw: bytes,
    term: str,
) -> None:
    _write_registry(tmp_path, raw=raw)
    _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
        term,
    )


@pytest.mark.parametrize("root_value", [None, [], "registry", 7, True])
def test_registry_root_must_be_object(
    tmp_path: Path,
    capsys: Any,
    root_value: Any,
) -> None:
    _write_registry(tmp_path, raw=_render_fixture(root_value))
    _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
        "root",
        "object",
    )


@pytest.mark.parametrize("schema_value", [None, 1, True, "wrong-schema"])
def test_wrong_schema_is_rejected_without_change(
    tmp_path: Path,
    capsys: Any,
    schema_value: Any,
) -> None:
    data = _registry_data([])
    data["schemaVersion"] = schema_value
    _write_registry(tmp_path, data)

    _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
        "schema",
    )


def test_missing_schema_is_rejected_without_change(
    tmp_path: Path,
    capsys: Any,
) -> None:
    data = {"repos": []}
    _write_registry(tmp_path, data)
    _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
        "schemaVersion",
    )


@pytest.mark.parametrize("repos_value", [None, {}, "repos", 1, True])
def test_repos_must_be_array(
    tmp_path: Path,
    capsys: Any,
    repos_value: Any,
) -> None:
    data = _registry_data([])
    data["repos"] = repos_value
    _write_registry(tmp_path, data)
    _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
        "repos",
        "array",
    )


def test_missing_repos_is_rejected_without_change(
    tmp_path: Path,
    capsys: Any,
) -> None:
    data = {"schemaVersion": EXPECTED_SCHEMA_VERSION}
    _write_registry(tmp_path, data)
    _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
        "repos",
    )


@pytest.mark.parametrize("entry_value", [None, [], "repo", 3, True])
def test_each_repo_must_be_object(
    tmp_path: Path,
    capsys: Any,
    entry_value: Any,
) -> None:
    data = _registry_data([])
    data["repos"] = [entry_value]
    _write_registry(tmp_path, data)
    _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
        "repo",
        "object",
    )


@pytest.mark.parametrize(
    "field",
    ["id", "url", "releasesUrl", "shortName", "lastReviewedRelease"],
)
def test_missing_required_entry_fields_are_rejected_without_change(
    tmp_path: Path,
    capsys: Any,
    field: str,
) -> None:
    item = _entry()
    del item[field]
    _write_registry(tmp_path, _registry_data([item]))
    _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
        field,
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", None),
        ("id", 1),
        ("id", True),
        ("url", None),
        ("url", []),
        ("releasesUrl", 3),
        ("shortName", False),
        ("lastReviewedRelease", 1),
        ("lastReviewedRelease", []),
        ("lastReviewDate", 20260828),
    ],
)
def test_wrong_entry_field_types_are_rejected_without_change(
    tmp_path: Path,
    capsys: Any,
    field: str,
    value: Any,
) -> None:
    item = _entry()
    item[field] = value
    _write_registry(tmp_path, _registry_data([item]))
    _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
        field,
    )


@pytest.mark.parametrize(
    "repo_id",
    ["", "-alpha", "alpha_", "alpha.repo", "alpha repo", "a" * 51],
)
def test_invalid_existing_ids_are_rejected_without_change(
    tmp_path: Path,
    capsys: Any,
    repo_id: str,
) -> None:
    _write_registry(tmp_path, _registry_data([_entry(repo_id=repo_id)]))
    _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
        "id",
    )


@pytest.mark.parametrize(
    "short_name",
    ["", "has space", "under_score", "dot.name", "a" * 11],
)
def test_invalid_existing_short_names_are_rejected_without_change(
    tmp_path: Path,
    capsys: Any,
    short_name: str,
) -> None:
    _write_registry(
        tmp_path,
        _registry_data([_entry(short_name=short_name)]),
    )
    _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
        "shortName",
    )


def test_duplicate_existing_ids_are_rejected_without_change(
    tmp_path: Path,
    capsys: Any,
) -> None:
    repos = [
        _entry("same", "one", "first", "ONE"),
        _entry("same", "two", "second", "TWO"),
    ]
    _write_registry(tmp_path, _registry_data(repos))
    _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
        "duplicate",
        "id",
    )


def test_duplicate_existing_short_names_are_case_insensitive(
    tmp_path: Path,
    capsys: Any,
) -> None:
    repos = [
        _entry("first", "one", "first", "Name"),
        _entry("second", "two", "second", "name"),
    ]
    _write_registry(tmp_path, _registry_data(repos))
    _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
        "duplicate",
        "short",
    )


def test_duplicate_existing_urls_are_case_insensitive(
    tmp_path: Path,
    capsys: Any,
) -> None:
    repos = [
        _entry("first", "Acme", "Widget", "ONE"),
        _entry("second", "acme", "widget", "TWO"),
    ]
    _write_registry(tmp_path, _registry_data(repos))
    _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/new/repo",
            "--check-only",
        ],
        capsys,
        "duplicate",
        "url",
    )


@pytest.mark.parametrize(
    ("field", "value", "term"),
    [
        ("url", "http://github.com/example/alpha", "https"),
        ("url", "https://github.com/example/alpha/", "canonical"),
        (
            "url",
            "https://github.com/example/alpha.git",
            "canonical",
        ),
        (
            "releasesUrl",
            "https://github.com/example/alpha/tags",
            "releases",
        ),
        (
            "releasesUrl",
            "https://github.com/other/alpha/releases",
            "match",
        ),
    ],
)
def test_invalid_existing_urls_are_rejected_without_change(
    tmp_path: Path,
    capsys: Any,
    field: str,
    value: str,
    term: str,
) -> None:
    item = _entry()
    item[field] = value
    _write_registry(tmp_path, _registry_data([item]))
    _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
        term,
    )


@pytest.mark.parametrize(
    ("location", "value", "term"),
    [
        ("entry", "2026-8-28", "lastReviewDate"),
        ("entry", "28-08-2026", "lastReviewDate"),
        ("root", "2026-8-28", "lastFullReview"),
        ("root", 20260828, "lastFullReview"),
        ("note", None, "lastFullReviewNote"),
        ("note", "", "lastFullReviewNote"),
        ("note", 1, "lastFullReviewNote"),
    ],
)
def test_invalid_existing_dates_and_notes_are_rejected_without_change(
    tmp_path: Path,
    capsys: Any,
    location: str,
    value: Any,
    term: str,
) -> None:
    data = _registry_data([_entry()])
    if location == "entry":
        data["repos"][0]["lastReviewDate"] = value
    elif location == "root":
        data["lastFullReview"] = value
    else:
        data["lastFullReviewNote"] = value
    _write_registry(tmp_path, data)

    _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
        term,
    )


def test_missing_registry_returns_controlled_failure(
    tmp_path: Path,
    capsys: Any,
) -> None:
    _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
        "repos.json",
        "not found",
    )


def test_secure_read_oserror_is_controlled_and_preserves_bytes(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        registry.secure_fs,
        "secure_read_bytes",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            OSError("simulated read failure")
        ),
    )

    _assert_failure(
        valid_registry_root,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
        "read",
        "simulated",
    )


@pytest.mark.parametrize(
    "failure",
    [
        OSError("simulated write failure"),
        SecureMutationError("simulated secure writer failure"),
    ],
    ids=["oserror", "secure-mutation"],
)
def test_secure_writer_failures_are_controlled_and_preserve_bytes(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
    failure: OSError,
) -> None:
    before = _registry_path(valid_registry_root).read_bytes()
    monkeypatch.setattr(
        registry.secure_fs,
        "secure_write_bytes",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(failure),
    )

    _assert_ambiguous(
        valid_registry_root,
        ["add", "--url", "https://github.com/acme/widget"],
        capsys,
        "ambiguous",
        "failure",
    )
    assert _registry_path(valid_registry_root).read_bytes() == before


def test_validation_completes_before_writer_is_called(
    tmp_path: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_registry(tmp_path, raw=b"not json")

    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("writer called before validation completed")

    monkeypatch.setattr(registry.secure_fs, "secure_write_bytes", forbidden)
    _assert_failure(
        tmp_path,
        ["add", "--url", "https://github.com/acme/widget"],
        capsys,
        "json",
    )


@pytest.mark.parametrize(
    "size",
    [MAX_REGISTRY_BYTES - 1, MAX_REGISTRY_BYTES],
    ids=["one-below", "exact"],
)
def test_registry_size_at_or_below_limit_is_accepted_without_byte_change(
    tmp_path: Path,
    capsys: Any,
    size: int,
) -> None:
    base = _render_fixture(_registry_data([]))
    assert len(base) < size
    source = base + (b" " * (size - len(base)))
    path = _write_registry(tmp_path, raw=source)

    exit_code, stdout, stderr = _invoke(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
    )

    assert exit_code == 0
    assert json.loads(stdout)["repo"]["id"] == "widget"
    assert stderr == ""
    assert path.read_bytes() == source


def test_registry_one_byte_over_limit_fails_before_parsing_and_preserves_bytes(
    tmp_path: Path,
    capsys: Any,
) -> None:
    base = _render_fixture(_registry_data([]))
    source = base + (b" " * (MAX_REGISTRY_BYTES + 1 - len(base)))
    _write_registry(tmp_path, raw=source)

    stderr = _assert_failure(
        tmp_path,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
        "size",
        str(MAX_REGISTRY_BYTES),
    )
    assert "json" not in stderr.casefold()


def test_secure_reader_receives_hardlink_rejection_and_exact_size_limit(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: Dict[str, Any] = {}
    original_read = registry.secure_fs.secure_read_bytes

    def observe(root: Path, relative: Path, **kwargs: Any) -> bytes:
        observed["root"] = root
        observed["relative"] = relative
        observed.update(kwargs)
        return original_read(root, relative, **kwargs)

    monkeypatch.setattr(registry.secure_fs, "secure_read_bytes", observe)
    exit_code, _, stderr = _invoke(
        valid_registry_root,
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
    )

    assert exit_code == 0
    assert stderr == ""
    assert observed["root"] == valid_registry_root.resolve()
    assert observed["relative"] == REGISTRY_RELATIVE_PATH
    assert observed["reject_hardlinks"] is True
    assert observed["max_bytes"] == MAX_REGISTRY_BYTES


@pytest.mark.usefixtures("require_symlink_support")
def test_registry_file_symlink_is_rejected_without_touching_target(
    tmp_path: Path,
    capsys: Any,
) -> None:
    outside = tmp_path / "outside.json"
    outside_bytes = _render_fixture(_registry_data([_entry()]))
    outside.write_bytes(outside_bytes)
    path = _registry_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.symlink_to(outside)

    _assert_failure(
        tmp_path,
        ["add", "--url", "https://github.com/acme/widget"],
        capsys,
        "link",
    )
    assert outside.read_bytes() == outside_bytes
    assert path.is_symlink()


@pytest.mark.usefixtures("require_symlink_support")
def test_registry_parent_symlink_is_rejected_without_touching_target(
    tmp_path: Path,
    capsys: Any,
) -> None:
    outside_parent = tmp_path / "outside-registry"
    outside_parent.mkdir()
    outside = outside_parent / "repos.json"
    outside_bytes = _render_fixture(_registry_data([_entry()]))
    outside.write_bytes(outside_bytes)
    local_parent = tmp_path / ".cg-docs/competitive-reviews"
    local_parent.parent.mkdir(parents=True)
    local_parent.symlink_to(outside_parent, target_is_directory=True)

    _assert_failure(
        tmp_path,
        ["add", "--url", "https://github.com/acme/widget"],
        capsys,
        "link",
    )
    assert outside.read_bytes() == outside_bytes


def test_registry_hard_link_is_rejected_without_touching_alias(
    tmp_path: Path,
    capsys: Any,
) -> None:
    outside = tmp_path / "outside.json"
    outside_bytes = _render_fixture(_registry_data([_entry()]))
    outside.write_bytes(outside_bytes)
    path = _registry_path(tmp_path)
    path.parent.mkdir(parents=True)
    try:
        os.link(str(outside), str(path))
    except (OSError, NotImplementedError) as error:
        pytest.skip("hard-link creation is unavailable: {}".format(error))

    _assert_failure(
        tmp_path,
        ["add", "--url", "https://github.com/acme/widget"],
        capsys,
        "hard",
        "link",
    )
    assert outside.read_bytes() == outside_bytes
    assert path.read_bytes() == outside_bytes


def test_writer_receives_expected_state_and_only_final_boundary_hook(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _registry_path(valid_registry_root)
    source = path.read_bytes()
    observed: Dict[str, Any] = {}
    original_write = registry.secure_fs.secure_write_bytes

    def hook(_path: Path) -> None:
        observed["hook_called"] = True

    def observe(
        root: Path,
        relative: Path,
        content: bytes,
        **kwargs: Any,
    ) -> Path:
        observed["root"] = root
        observed["relative"] = relative
        observed["content"] = content
        observed.update(kwargs)
        return original_write(root, relative, content, **kwargs)

    monkeypatch.setattr(registry, "_before_secure_replace", hook)
    monkeypatch.setattr(registry.secure_fs, "secure_write_bytes", observe)

    exit_code, _, stderr = _invoke(
        valid_registry_root,
        ["add", "--url", "https://github.com/acme/widget"],
        capsys,
    )

    assert exit_code == 0
    assert stderr == ""
    assert observed["root"] == valid_registry_root.resolve()
    assert observed["relative"] == REGISTRY_RELATIVE_PATH
    assert observed["expected_state"] == ExpectedFileState.from_bytes(source)
    assert observed["before_replace"] is hook
    assert observed["hook_called"] is True
    assert observed["content"] == path.read_bytes()


def test_before_replace_concurrent_winner_is_preserved(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _registry_path(valid_registry_root)
    winner = b'{"concurrent":"winner"}\n'

    def publish_winner(boundary_path: Path) -> None:
        assert boundary_path == path
        boundary_path.write_bytes(winner)

    monkeypatch.setattr(registry, "_before_secure_replace", publish_winner)

    exit_code, stdout, stderr = _invoke(
        valid_registry_root,
        ["add", "--url", "https://github.com/acme/widget"],
        capsys,
    )

    assert exit_code == 3
    assert stdout == ""
    assert stderr
    assert "Traceback" not in stderr
    assert path.read_bytes() == winner


def test_expected_state_race_after_secure_read_preserves_winner(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _registry_path(valid_registry_root)
    winner = b'{"concurrent":"after-read"}\n'
    original_read = registry.secure_fs.secure_read_bytes

    def read_then_change(root: Path, relative: Path, **kwargs: Any) -> bytes:
        source = original_read(root, relative, **kwargs)
        path.write_bytes(winner)
        return source

    monkeypatch.setattr(registry.secure_fs, "secure_read_bytes", read_then_change)

    exit_code, stdout, stderr = _invoke(
        valid_registry_root,
        ["add", "--url", "https://github.com/acme/widget"],
        capsys,
    )

    assert exit_code == 3
    assert stdout == ""
    assert "Traceback" not in stderr
    assert "ambiguous" in stderr.casefold()
    assert path.read_bytes() == winner


@pytest.mark.backend_posix
@pytest.mark.skipif(
    os.name == "nt" or not secure_fs.supports_secure_dir_fd(),
    reason="requires a POSIX parent rename after dir_fd pinning",
)
def test_parent_identity_change_at_replace_boundary_cannot_escape_root(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _registry_path(valid_registry_root)
    original = path.read_bytes()
    parent = path.parent
    displaced = parent.with_name("competitive-reviews-displaced")
    outside = valid_registry_root.parent / "outside-registry-parent"
    outside.mkdir()

    def swap_parent(_path: Path) -> None:
        parent.rename(displaced)
        parent.symlink_to(outside, target_is_directory=True)

    monkeypatch.setattr(registry, "_before_secure_replace", swap_parent)
    exit_code, stdout, stderr = _invoke(
        valid_registry_root,
        ["add", "--url", "https://github.com/acme/widget"],
        capsys,
    )

    assert exit_code == 3
    assert stdout == ""
    assert "Traceback" not in stderr
    assert list(outside.iterdir()) == []
    assert (displaced / "repos.json").read_bytes() == original


@pytest.mark.backend_windows
@pytest.mark.skipif(os.name != "nt", reason="requires Windows handle pinning")
def test_windows_parent_change_attempt_is_blocked_by_pinned_handle(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _registry_path(valid_registry_root)
    parent = path.parent
    displaced = parent.with_name("competitive-reviews-displaced")
    swap_blocked = False

    def attempt_parent_swap(_path: Path) -> None:
        nonlocal swap_blocked
        try:
            parent.rename(displaced)
        except OSError:
            swap_blocked = True

    monkeypatch.setattr(registry, "_before_secure_replace", attempt_parent_swap)
    exit_code, stdout, stderr = _invoke(
        valid_registry_root,
        ["add", "--url", "https://github.com/acme/widget"],
        capsys,
    )

    assert exit_code == 0
    assert json.loads(stdout)["changed"] is True
    assert stderr == ""
    assert swap_blocked is True
    assert json.loads(path.read_text("utf-8"))["repos"][-1]["id"] == "widget"


def test_default_root_is_current_directory(
    empty_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(empty_registry_root)

    exit_code = registry.main(
        [
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert json.loads(captured.out)["repo"]["id"] == "widget"
    assert captured.err == ""


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["unknown"],
        ["add"],
        ["add", "--url"],
        ["add", "--url", "https://github.com/a/b", "extra"],
        ["remove"],
        ["remove", "--id", "alpha"],
        ["remove", "--confirm-id", "alpha"],
        ["remove", "--id", "alpha", "--confirm-id", "alpha", "--check-only"],
        ["add", "--url", "https://github.com/a/b", "remove"],
    ],
)
def test_argparse_invalid_syntax_exits_two(
    valid_registry_root: Path,
    capsys: Any,
    arguments: List[str],
) -> None:
    before = _registry_path(valid_registry_root).read_bytes()

    with pytest.raises(SystemExit) as caught:
        registry.main(["--root", str(valid_registry_root)] + arguments)
    captured = capsys.readouterr()

    assert caught.value.code == 2
    assert captured.out == ""
    assert "usage:" in captured.err.casefold()
    assert "Traceback" not in captured.err
    assert _registry_path(valid_registry_root).read_bytes() == before


def test_all_expected_failures_emit_one_stderr_line_and_no_partial_json(
    malformed_registry_root: Path,
    capsys: Any,
) -> None:
    stderr = _assert_failure(
        malformed_registry_root,
        ["remove", "--id", "alpha", "--confirm-id", "alpha"],
        capsys,
        "json",
    )

    assert not stderr.lstrip().startswith("{")


@pytest.mark.parametrize(
    "number_token",
    ["0.123456789012345678901234567890", "1e400", "-0.0000000000000000001"],
)
def test_unknown_json_numbers_round_trip_exactly(
    tmp_path: Path,
    capsys: Any,
    number_token: str,
) -> None:
    raw = (
        f'{{"schemaVersion":"{EXPECTED_SCHEMA_VERSION}",'
        f'"repos":[],"extension":{number_token}}}'
    ).encode("utf-8")
    _write_registry(tmp_path, raw=raw)

    exit_code, stdout, stderr = _invoke(
        tmp_path,
        ["add", "--url", "https://github.com/acme/widget"],
        capsys,
    )

    assert exit_code == 0
    assert stderr == ""
    assert json.loads(stdout, parse_float=Decimal)["changed"] is True
    updated = json.loads(
        _registry_path(tmp_path).read_text("utf-8"),
        parse_float=Decimal,
        parse_int=Decimal,
    )
    assert updated["extension"] == Decimal(number_token)


def test_large_unknown_integer_round_trips_without_parser_limit(
    tmp_path: Path,
    capsys: Any,
) -> None:
    number_token = "9" * 5000
    raw = (
        f'{{"schemaVersion":"{EXPECTED_SCHEMA_VERSION}",'
        f'"repos":[],"extension":{number_token}}}'
    ).encode("utf-8")
    _write_registry(tmp_path, raw=raw)

    exit_code, _, stderr = _invoke(
        tmp_path,
        ["add", "--url", "https://github.com/acme/widget"],
        capsys,
    )

    assert exit_code == 0
    assert stderr == ""
    assert number_token.encode("ascii") in _registry_path(tmp_path).read_bytes()


def test_deep_unknown_json_is_a_controlled_failure(
    tmp_path: Path,
    capsys: Any,
) -> None:
    nested = ("[" * 150) + "0" + ("]" * 150)
    raw = (
        f'{{"schemaVersion":"{EXPECTED_SCHEMA_VERSION}",'
        f'"repos":[],"extension":{nested}}}'
    ).encode("utf-8")
    _write_registry(tmp_path, raw=raw)

    _assert_failure(
        tmp_path,
        ["add", "--url", "https://github.com/acme/widget", "--check-only"],
        capsys,
        "depth",
    )


@pytest.mark.parametrize("control", ["\n", "\r", "\t", " ", "\x00", "\x7f"])
def test_url_controls_and_whitespace_are_rejected_before_parsing(
    valid_registry_root: Path,
    capsys: Any,
    control: str,
) -> None:
    _assert_failure(
        valid_registry_root,
        [
            "add",
            "--url",
            control + "https://github.com/acme/widget",
            "--check-only",
        ],
        capsys,
        "whitespace" if control.isspace() else "control",
    )


@pytest.mark.parametrize("command", ["add", "remove"])
def test_rendered_registry_cannot_exceed_read_limit(
    tmp_path: Path,
    capsys: Any,
    command: str,
) -> None:
    repos = [] if command == "add" else [_entry()]
    data = {
        "schemaVersion": EXPECTED_SCHEMA_VERSION,
        "repos": repos,
        "values": [0] * 1000,
        "padding": "",
    }
    compact = json.dumps(data, separators=(",", ":")).encode("utf-8")
    data["padding"] = "x" * (MAX_REGISTRY_BYTES - len(compact))
    source = json.dumps(data, separators=(",", ":")).encode("utf-8")
    assert len(source) == MAX_REGISTRY_BYTES
    _write_registry(tmp_path, raw=source)
    arguments = (
        ["add", "--url", "https://github.com/acme/widget"]
        if command == "add"
        else ["remove", "--id", "alpha", "--confirm-id", "alpha"]
    )

    _assert_failure(tmp_path, arguments, capsys, "rendered", "size")


def test_real_writer_boundary_failure_restores_exact_source(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = _registry_path(valid_registry_root).parent

    def fail_at_boundary(_path: Path) -> None:
        raise OSError("simulated final-boundary failure")

    monkeypatch.setattr(registry, "_before_secure_replace", fail_at_boundary)
    _assert_ambiguous(
        valid_registry_root,
        ["add", "--url", "https://github.com/acme/widget"],
        capsys,
        "boundary",
        "failure",
    )
    assert [path.name for path in parent.iterdir()] == ["repos.json"]


def test_success_response_is_rendered_before_registry_write(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: List[str] = []
    original_render = registry._render_response
    original_write = registry.secure_fs.secure_write_bytes

    def observe_render(*args: Any, **kwargs: Any) -> str:
        events.append("render")
        return original_render(*args, **kwargs)

    def observe_write(*args: Any, **kwargs: Any) -> Path:
        events.append("write")
        return original_write(*args, **kwargs)

    monkeypatch.setattr(registry, "_render_response", observe_render)
    monkeypatch.setattr(registry.secure_fs, "secure_write_bytes", observe_write)

    exit_code, _, stderr = _invoke(
        valid_registry_root,
        ["add", "--url", "https://github.com/acme/widget"],
        capsys,
    )

    assert exit_code == 0
    assert stderr == ""
    assert events[-1] == "write"
    assert set(events[:-1]) == {"render"}
    assert len(events[:-1]) == 2 ** len(registry.WARNING_CODES)


def test_remove_response_preserves_large_finite_unknown_number(
    tmp_path: Path,
    capsys: Any,
) -> None:
    item = _entry()
    item["extension"] = "NUMBER_TOKEN"
    raw = _render_fixture(_registry_data([item])).replace(
        b'"NUMBER_TOKEN"',
        b"1e400",
    )
    _write_registry(tmp_path, raw=raw)

    exit_code, stdout, stderr = _invoke(
        tmp_path,
        ["remove", "--id", "alpha", "--confirm-id", "alpha"],
        capsys,
    )

    assert exit_code == 0
    assert stderr == ""
    response = json.loads(stdout, parse_float=Decimal)
    assert response["repo"]["extension"] == Decimal("1e400")
    assert json.loads(_registry_path(tmp_path).read_text("utf-8"))["repos"] == []


def test_public_examples_are_valid_doctests() -> None:
    result = doctest.testmod(registry, raise_on_error=False)
    assert result.failed == 0


def test_process_cli_exit_and_stream_contracts(tmp_path: Path) -> None:
    script = Path(registry.__file__).resolve()
    valid_root = tmp_path / "valid"
    invalid_root = tmp_path / "invalid"
    valid_path = _write_registry(valid_root, _registry_data([]))
    invalid_path = _write_registry(invalid_root, raw=b'{"schemaVersion":')

    success = subprocess.run(
        [
            sys.executable,
            str(script),
            "--root",
            str(valid_root),
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    failure = subprocess.run(
        [
            sys.executable,
            str(script),
            "--root",
            str(invalid_root),
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--check-only",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    syntax = subprocess.run(
        [sys.executable, str(script), "--root", str(valid_root), "add"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert success.returncode == 0
    assert json.loads(success.stdout)["changed"] is False
    assert success.stderr == ""
    assert failure.returncode == 1
    assert failure.stdout == ""
    assert "Traceback" not in failure.stderr
    assert syntax.returncode == 2
    assert syntax.stdout == ""
    assert "usage:" in syntax.stderr.casefold()
    assert json.loads(valid_path.read_text("utf-8"))["repos"] == []
    assert invalid_path.read_bytes() == b'{"schemaVersion":'


def test_state_returns_exact_bounded_projection_and_never_writes(
    tmp_path: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _entry("first", "one", "first", "ONE", extension=Decimal("1e400"))
    second = _entry(
        "second",
        "two",
        "second",
        "TWO",
        lastReviewedRelease=None,
    )
    data = {
        "schemaVersion": EXPECTED_SCHEMA_VERSION,
        "lastFullReview": None,
        "lastFullReviewNote": "partial - second",
        "repos": [first, second],
        "rootExtension": {"keep": True},
    }
    path = _write_registry(tmp_path, raw=registry.render_registry(data))
    source = path.read_bytes()

    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("state dispatched a writer")

    monkeypatch.setattr(registry.secure_fs, "secure_write_bytes", forbidden)
    exit_code, stdout, stderr = _invoke(
        tmp_path,
        [
            "state",
            "--id",
            "second",
            "--expected-url",
            second["url"],
        ],
        capsys,
    )

    assert exit_code == 0
    assert stderr == ""
    assert len(stdout.encode("utf-8")) <= registry.MAX_RESPONSE_BYTES
    response = json.loads(stdout)
    digest = hashlib.sha256(source).hexdigest()
    assert response == {
        "action": "state",
        "changed": False,
        "beforeSha256": digest,
        "afterSha256": digest,
        "beforeScopeDigestSha256": registry._scope_digest(data),
        "afterScopeDigestSha256": registry._scope_digest(data),
        "repositories": [
            {
                "id": "first",
                "url": first["url"],
                "lastReviewedRelease": "v1.0.0",
                "lastReviewDate": {"present": True, "value": "2026-08-28"},
            },
            {
                "id": "second",
                "url": second["url"],
                "lastReviewedRelease": None,
                "lastReviewDate": {"present": False, "value": None},
            },
        ],
        "rootReview": {
            "lastFullReview": {"present": True, "value": None},
            "lastFullReviewNote": {
                "present": True,
                "value": "partial - second",
            },
        },
        "selection": {
            "id": "second",
            "expectedUrl": second["url"],
            "found": True,
            "url": second["url"],
            "urlMatches": True,
            "lastReviewedRelease": None,
            "lastReviewDate": {"present": False, "value": None},
        },
        "warnings": [],
    }
    assert path.read_bytes() == source


def test_mutation_response_key_sets_expose_before_and_after_scope_digests(
    tmp_path: Path,
    capsys: Any,
) -> None:
    common = {
        "action",
        "changed",
        "beforeSha256",
        "afterSha256",
        "beforeScopeDigestSha256",
        "afterScopeDigestSha256",
        "warnings",
    }
    repo_keys = common.union({"repo"})

    add_root = tmp_path / "add"
    _write_registry(add_root, _registry_data([]))
    _, stdout, _ = _invoke(
        add_root,
        ["add", "--url", "https://github.com/acme/widget", "--check-only"],
        capsys,
    )
    assert set(json.loads(stdout)) == repo_keys

    review_root = tmp_path / "review"
    reviewed = _entry(lastReviewDate="2026-08-30")
    _write_registry(review_root, _registry_data([reviewed]))
    _, stdout, _ = _invoke(
        review_root,
        ["remove", "--id", "alpha", "--check-only"],
        capsys,
    )
    assert set(json.loads(stdout)) == repo_keys
    _, stdout, _ = _invoke(
        review_root,
        [
            "review-repo",
            "--id",
            "alpha",
            "--expected-url",
            reviewed["url"],
            "--release",
            "v2.0.0",
            "--review-date",
            "2026-08-30",
            "--check-only",
        ],
        capsys,
    )
    assert set(json.loads(stdout)) == repo_keys
    _, stdout, _ = _invoke(
        review_root,
        [
            "review-full",
            "--outcome",
            "complete",
            "--review-date",
            "2026-08-30",
            "--reviewed-id",
            "alpha",
            "--check-only",
        ],
        capsys,
    )
    assert set(json.loads(stdout)) == common.union(
        {"outcome", "reviewDate", "reviewedIds", "failedIds", "rootReview"}
    )


def test_add_plan_apply_uses_exact_before_and_after_hashes(
    empty_registry_root: Path,
    capsys: Any,
) -> None:
    path = _registry_path(empty_registry_root)
    source = path.read_bytes()
    url = "https://github.com/acme/widget"
    plan_code, plan_stdout, plan_stderr = _invoke(
        empty_registry_root,
        ["add", "--url", url, "--check-only"],
        capsys,
    )
    plan = json.loads(plan_stdout)

    assert plan_code == 0
    assert plan_stderr == ""
    assert plan["changed"] is False
    assert plan["beforeSha256"] == hashlib.sha256(source).hexdigest()
    assert path.read_bytes() == source

    apply_code, apply_stdout, apply_stderr = _invoke(
        empty_registry_root,
        [
            "add",
            "--url",
            url,
            "--expected-sha256",
            plan["beforeSha256"],
        ],
        capsys,
    )
    applied = json.loads(apply_stdout)
    assert apply_code == 0
    assert apply_stderr == ""
    assert applied["changed"] is True
    assert applied["beforeSha256"] == plan["beforeSha256"]
    assert applied["afterSha256"] == plan["afterSha256"]
    assert applied["afterSha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_remove_plan_displays_complete_entry_and_apply_binds_url_and_hash(
    tmp_path: Path,
    capsys: Any,
) -> None:
    removed = _entry(extension={"exact": Decimal("0.12345678901234567890")})
    survivor = _entry("survivor", "two", "survivor", "TWO")
    source_data = _registry_data([removed, survivor])
    path = _write_registry(tmp_path, raw=registry.render_registry(source_data))
    source = path.read_bytes()

    plan_code, plan_stdout, plan_stderr = _invoke(
        tmp_path,
        ["remove", "--id", "alpha", "--check-only"],
        capsys,
    )
    plan = json.loads(plan_stdout, parse_float=Decimal)
    assert plan_code == 0
    assert plan_stderr == ""
    assert plan["repo"] == removed
    assert plan["beforeSha256"] == hashlib.sha256(source).hexdigest()
    assert plan["afterSha256"] != plan["beforeSha256"]
    assert path.read_bytes() == source

    apply_code, apply_stdout, apply_stderr = _invoke(
        tmp_path,
        [
            "remove",
            "--id",
            "alpha",
            "--confirm-id",
            "alpha",
            "--expected-url",
            removed["url"],
            "--expected-sha256",
            plan["beforeSha256"],
        ],
        capsys,
    )
    applied = json.loads(apply_stdout, parse_float=Decimal)
    assert apply_code == 0
    assert apply_stderr == ""
    assert applied["repo"] == removed
    assert applied["afterSha256"] == plan["afterSha256"]
    assert json.loads(path.read_text("utf-8"))["repos"] == [survivor]


def test_remove_rejects_same_id_url_replacement_independently_of_hash(
    valid_registry_root: Path,
    capsys: Any,
) -> None:
    path = _registry_path(valid_registry_root)
    original_url = _entry()["url"]
    replacement = _registry_data(
        [_entry("alpha", "attacker", "replacement", "A")]
    )
    replacement_bytes = _render_fixture(replacement)
    path.write_bytes(replacement_bytes)

    code, stdout, stderr = _invoke(
        valid_registry_root,
        [
            "remove",
            "--id",
            "alpha",
            "--confirm-id",
            "alpha",
            "--expected-url",
            original_url,
            "--expected-sha256",
            hashlib.sha256(replacement_bytes).hexdigest(),
        ],
        capsys,
    )

    assert code == 1
    assert stdout == ""
    assert "url changed" in stderr.casefold()
    assert path.read_bytes() == replacement_bytes


def test_remove_rejects_unrelated_state_change_from_plan(
    valid_registry_root: Path,
    capsys: Any,
) -> None:
    path = _registry_path(valid_registry_root)
    _, plan_stdout, _ = _invoke(
        valid_registry_root,
        ["remove", "--id", "alpha", "--check-only"],
        capsys,
    )
    plan = json.loads(plan_stdout)
    changed = _registry_data([_entry()])
    changed["unrelated"] = True
    changed_bytes = _render_fixture(changed)
    path.write_bytes(changed_bytes)

    code, stdout, stderr = _invoke(
        valid_registry_root,
        [
            "remove",
            "--id",
            "alpha",
            "--confirm-id",
            "alpha",
            "--expected-url",
            _entry()["url"],
            "--expected-sha256",
            plan["beforeSha256"],
        ],
        capsys,
    )
    assert code == 1
    assert stdout == ""
    assert "stale" in stderr.casefold()
    assert path.read_bytes() == changed_bytes


def test_remove_final_boundary_same_id_winner_is_preserved(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _registry_path(valid_registry_root)
    winner = _render_fixture(
        _registry_data([_entry("alpha", "winner", "replacement", "A")])
    )

    def publish_winner(boundary_path: Path) -> None:
        assert boundary_path == path
        boundary_path.write_bytes(winner)

    monkeypatch.setattr(registry, "_before_secure_replace", publish_winner)
    code, stdout, stderr = _invoke(
        valid_registry_root,
        ["remove", "--id", "alpha", "--confirm-id", "alpha"],
        capsys,
    )
    assert code == 3
    assert stdout == ""
    assert "ambiguous" in stderr.casefold()
    assert path.read_bytes() == winner


def test_review_repo_plan_apply_preserves_all_unrelated_state_and_order(
    tmp_path: Path,
    capsys: Any,
) -> None:
    first = _entry(extension={"number": Decimal("1e400")})
    second = _entry("second", "two", "second", "TWO", custom="keep")
    data = {
        "schemaVersion": EXPECTED_SCHEMA_VERSION,
        "rootBefore": 1,
        "lastFullReview": "2026-08-28",
        "repos": [first, second],
        "rootAfter": [1, 2],
    }
    path = _write_registry(tmp_path, raw=registry.render_registry(data))
    arguments = [
        "review-repo",
        "--id",
        "alpha",
        "--expected-url",
        first["url"],
        "--release",
        "v2.0.0",
        "--review-date",
        "2026-08-30",
    ]
    _, plan_stdout, plan_stderr = _invoke(
        tmp_path,
        arguments + ["--check-only"],
        capsys,
    )
    plan = json.loads(plan_stdout, parse_float=Decimal)
    assert plan_stderr == ""
    assert plan["repo"]["extension"]["number"] == Decimal("1e400")
    assert plan["beforeScopeDigestSha256"] == registry._scope_digest(data)
    assert plan["afterScopeDigestSha256"] != plan["beforeScopeDigestSha256"]

    code, stdout, stderr = _invoke(
        tmp_path,
        arguments + ["--expected-sha256", plan["beforeSha256"]],
        capsys,
    )
    applied = json.loads(stdout, parse_float=Decimal)
    assert code == 0
    assert stderr == ""
    assert applied["afterSha256"] == plan["afterSha256"]
    assert applied["beforeScopeDigestSha256"] == plan["beforeScopeDigestSha256"]
    assert applied["afterScopeDigestSha256"] == plan["afterScopeDigestSha256"]
    updated = json.loads(
        path.read_text("utf-8"),
        parse_float=Decimal,
        parse_int=Decimal,
    )
    assert list(updated) == list(data)
    assert list(updated["repos"][0]) == list(first)
    assert updated["repos"][0]["lastReviewedRelease"] == "v2.0.0"
    assert updated["repos"][0]["lastReviewDate"] == "2026-08-30"
    assert updated["repos"][0]["extension"] == first["extension"]
    assert updated["repos"][1] == second
    assert updated["rootBefore"] == Decimal(1)
    assert updated["rootAfter"] == [Decimal(1), Decimal(2)]


def test_review_repo_supports_explicit_null_and_absent_date_states(
    valid_registry_root: Path,
    capsys: Any,
) -> None:
    path = _registry_path(valid_registry_root)
    first_args = [
        "review-repo",
        "--id",
        "alpha",
        "--expected-url",
        _entry()["url"],
        "--release-null",
        "--review-date-null",
    ]
    _, first_plan_stdout, _ = _invoke(
        valid_registry_root,
        first_args + ["--check-only"],
        capsys,
    )
    first_plan = json.loads(first_plan_stdout)
    code, _, stderr = _invoke(
        valid_registry_root,
        first_args + ["--expected-sha256", first_plan["beforeSha256"]],
        capsys,
    )
    assert code == 0
    assert stderr == ""
    explicit_null = json.loads(path.read_text("utf-8"))["repos"][0]
    assert explicit_null["lastReviewedRelease"] is None
    assert "lastReviewDate" in explicit_null
    assert explicit_null["lastReviewDate"] is None

    second_args = [
        "review-repo",
        "--id",
        "alpha",
        "--expected-url",
        _entry()["url"],
        "--release-null",
    ]
    _, second_plan_stdout, _ = _invoke(
        valid_registry_root,
        second_args + ["--check-only"],
        capsys,
    )
    second_plan = json.loads(second_plan_stdout)
    code, _, stderr = _invoke(
        valid_registry_root,
        second_args + ["--expected-sha256", second_plan["beforeSha256"]],
        capsys,
    )
    assert code == 0
    assert stderr == ""
    absent = json.loads(path.read_text("utf-8"))["repos"][0]
    assert absent["lastReviewedRelease"] is None
    assert "lastReviewDate" not in absent


def test_review_repo_rejects_url_and_stale_state_conflicts(
    valid_registry_root: Path,
    capsys: Any,
) -> None:
    path = _registry_path(valid_registry_root)
    before = path.read_bytes()
    common = [
        "review-repo",
        "--id",
        "alpha",
        "--release",
        "v2",
        "--review-date",
        "2026-08-30",
    ]
    bad_url_code, bad_url_stdout, bad_url_stderr = _invoke(
        valid_registry_root,
        common
        + [
            "--expected-url",
            "https://github.com/other/replacement",
            "--expected-sha256",
            hashlib.sha256(before).hexdigest(),
        ],
        capsys,
    )
    assert bad_url_code == 1
    assert bad_url_stdout == ""
    assert "url changed" in bad_url_stderr.casefold()
    assert path.read_bytes() == before

    _, plan_stdout, _ = _invoke(
        valid_registry_root,
        common + ["--expected-url", _entry()["url"], "--check-only"],
        capsys,
    )
    plan = json.loads(plan_stdout)
    unrelated = json.loads(before.decode("utf-8"))
    unrelated["other"] = "winner"
    winner = _render_fixture(unrelated)
    path.write_bytes(winner)
    stale_code, stale_stdout, stale_stderr = _invoke(
        valid_registry_root,
        common
        + [
            "--expected-url",
            _entry()["url"],
            "--expected-sha256",
            plan["beforeSha256"],
        ],
        capsys,
    )
    assert stale_code == 1
    assert stale_stdout == ""
    assert "stale" in stale_stderr.casefold()
    assert path.read_bytes() == winner


@pytest.mark.parametrize(
    "unsafe_release",
    [
        "",
        "-v2.0.0",
        "$(whoami)",
        "`whoami`",
        'v"2',
        "v'2",
        "v 2",
        "v&2",
        "v;2",
        "v\x01",
        "v\u00e9",
        "v" * 129,
    ],
    ids=[
        "empty",
        "leading-hyphen",
        "dollar-command",
        "backticks",
        "double-quote",
        "single-quote",
        "whitespace",
        "ampersand",
        "semicolon",
        "control",
        "non-ascii",
        "overlength",
    ],
)
@pytest.mark.parametrize("value_kind", ["new", "expected"])
def test_review_repo_rejects_unsafe_new_and_expected_release_values(
    valid_registry_root: Path,
    capsys: Any,
    unsafe_release: str,
    value_kind: str,
) -> None:
    arguments = [
        "review-repo",
        "--id",
        "alpha",
        "--expected-url",
        _entry()["url"],
        "--review-date",
        "2026-08-30",
        "--expected-last-review-date",
        "2026-08-28",
        "--check-only",
    ]
    if value_kind == "new":
        arguments.extend(
            [
                "--release={}".format(unsafe_release),
                "--expected-last-reviewed-release",
                "v1.0.0",
            ]
        )
    else:
        arguments.extend(
            [
                "--release",
                "v2.0.0",
                "--expected-last-reviewed-release={}".format(unsafe_release),
            ]
        )

    _assert_failure(valid_registry_root, arguments, capsys, "1-128", "ascii")


@pytest.mark.parametrize(
    "unsafe_release",
    [
        "",
        "-v2.0.0",
        "$(whoami)",
        "`whoami`",
        'v"2',
        "v'2",
        "v 2",
        "v&2",
        "v;2",
        "v\x01",
        "v\u00e9",
        "v" * 129,
    ],
)
def test_state_rejects_unsafe_stored_release_values(
    tmp_path: Path,
    capsys: Any,
    unsafe_release: str,
) -> None:
    source = _render_fixture(
        _registry_data([_entry(lastReviewedRelease=unsafe_release)])
    )
    _write_registry(tmp_path, raw=source)

    _assert_failure(tmp_path, ["state"], capsys, "1-128", "ascii")


def test_review_repo_accepts_release_allowlist_length_boundary(
    tmp_path: Path,
    capsys: Any,
) -> None:
    prior_release = "p" + ("a" * 127)
    new_release = "v" + ("b" * 125) + "/c"
    item = _entry(lastReviewedRelease=prior_release)
    path = _write_registry(tmp_path, _registry_data([item]))

    code, stdout, stderr = _invoke(
        tmp_path,
        [
            "review-repo",
            "--id",
            "alpha",
            "--expected-url",
            item["url"],
            "--release",
            new_release,
            "--review-date",
            "2026-08-30",
            "--expected-last-reviewed-release",
            prior_release,
            "--expected-last-review-date",
            "2026-08-28",
            "--expected-chain-sha256",
            hashlib.sha256(path.read_bytes()).hexdigest(),
            "--check-only",
        ],
        capsys,
    )

    assert code == 0
    assert stderr == ""
    assert json.loads(stdout)["repo"]["lastReviewedRelease"] == new_release


def test_review_repo_check_only_rejects_stale_accepted_chain_before_transform(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _registry_path(valid_registry_root)
    accepted_source = path.read_bytes()
    changed = json.loads(accepted_source.decode("utf-8"))
    changed["concurrent"] = "winner"
    winner = _render_fixture(changed)
    path.write_bytes(winner)

    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("review transformation ran after stale chain")

    monkeypatch.setattr(registry, "review_repository", forbidden)
    _assert_failure(
        valid_registry_root,
        [
            "review-repo",
            "--id",
            "alpha",
            "--expected-url",
            _entry()["url"],
            "--release",
            "v2.0.0",
            "--review-date",
            "2026-08-30",
            "--expected-last-reviewed-release",
            "v1.0.0",
            "--expected-last-review-date",
            "2026-08-28",
            "--expected-chain-sha256",
            hashlib.sha256(accepted_source).hexdigest(),
            "--check-only",
        ],
        capsys,
        "stale",
    )
    assert path.read_bytes() == winner


@pytest.mark.parametrize(
    ("expected_arguments", "term"),
    [
        (
            [
                "--expected-last-reviewed-release",
                "v0.9.0",
                "--expected-last-review-date",
                "2026-08-28",
            ],
            "lastReviewedRelease",
        ),
        (
            [
                "--expected-last-reviewed-release",
                "v1.0.0",
                "--expected-last-review-date",
                "2026-08-27",
            ],
            "lastReviewDate",
        ),
        (
            [
                "--expected-last-reviewed-release",
                "v1.0.0",
                "--expected-last-review-date-null",
            ],
            "lastReviewDate",
        ),
        (
            [
                "--expected-last-reviewed-release",
                "v1.0.0",
                "--expected-last-review-date-absent",
            ],
            "presence",
        ),
    ],
    ids=["release-value", "date-value", "date-null", "date-absent"],
)
def test_review_repo_check_only_rejects_exact_prior_projection_mismatch(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
    expected_arguments: List[str],
    term: str,
) -> None:
    path = _registry_path(valid_registry_root)

    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("review transformation ran after projection mismatch")

    monkeypatch.setattr(registry, "review_repository", forbidden)
    _assert_failure(
        valid_registry_root,
        [
            "review-repo",
            "--id",
            "alpha",
            "--expected-url",
            _entry()["url"],
            "--release",
            "v2.0.0",
            "--review-date",
            "2026-08-30",
            *expected_arguments,
            "--expected-chain-sha256",
            hashlib.sha256(path.read_bytes()).hexdigest(),
            "--check-only",
        ],
        capsys,
        term,
    )


@pytest.mark.parametrize("prior_date_state", ["value", "null", "absent"])
def test_review_repo_check_only_accepts_unambiguous_prior_date_states(
    tmp_path: Path,
    capsys: Any,
    prior_date_state: str,
) -> None:
    if prior_date_state == "value":
        item = _entry()
        expected = [
            "--expected-last-reviewed-release",
            "v1.0.0",
            "--expected-last-review-date",
            "2026-08-28",
        ]
    else:
        item = _entry(lastReviewedRelease=None)
        expected = ["--expected-last-reviewed-release-null"]
        if prior_date_state == "null":
            item["lastReviewDate"] = None
            expected.append("--expected-last-review-date-null")
        else:
            expected.append("--expected-last-review-date-absent")
    path = _write_registry(tmp_path, _registry_data([item]))

    code, stdout, stderr = _invoke(
        tmp_path,
        [
            "review-repo",
            "--id",
            "alpha",
            "--expected-url",
            item["url"],
            "--release",
            "v2.0.0",
            "--review-date",
            "2026-08-30",
            *expected,
            "--expected-chain-sha256",
            hashlib.sha256(path.read_bytes()).hexdigest(),
            "--check-only",
        ],
        capsys,
    )

    assert code == 0
    assert stderr == ""
    assert json.loads(stdout)["repo"]["lastReviewedRelease"] == "v2.0.0"


def test_review_repo_post_commit_exception_recovers_through_read_only_state(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _registry_path(valid_registry_root)
    original_write = registry.secure_fs.secure_write_bytes
    arguments = [
        "review-repo",
        "--id",
        "alpha",
        "--expected-url",
        _entry()["url"],
        "--release",
        "v2",
        "--review-date",
        "2026-08-30",
    ]
    _, plan_stdout, _ = _invoke(
        valid_registry_root,
        arguments + ["--check-only"],
        capsys,
    )
    plan = json.loads(plan_stdout)

    def commit_then_raise(*args: Any, **kwargs: Any) -> Path:
        result = original_write(*args, **kwargs)
        raise OSError("simulated post-commit exception")

    monkeypatch.setattr(registry.secure_fs, "secure_write_bytes", commit_then_raise)
    code, stdout, stderr = _invoke(
        valid_registry_root,
        arguments + ["--expected-sha256", plan["beforeSha256"]],
        capsys,
    )
    assert code == 3
    assert stdout == ""
    assert "ambiguous" in stderr.casefold()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == plan["afterSha256"]

    monkeypatch.setattr(registry.secure_fs, "secure_write_bytes", original_write)
    state_code, state_stdout, state_stderr = _invoke(
        valid_registry_root,
        [
            "state",
            "--id",
            "alpha",
            "--expected-url",
            _entry()["url"],
        ],
        capsys,
    )
    state = json.loads(state_stdout)
    assert state_code == 0
    assert state_stderr == ""
    assert state["beforeSha256"] == plan["afterSha256"]
    assert state["selection"]["urlMatches"] is True
    assert state["selection"]["lastReviewedRelease"] == "v2"
    assert state["selection"]["lastReviewDate"]["value"] == "2026-08-30"


def test_review_repo_final_boundary_race_preserves_winner_and_reconciles_read_only(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _registry_path(valid_registry_root)
    arguments = [
        "review-repo",
        "--id",
        "alpha",
        "--expected-url",
        _entry()["url"],
        "--release",
        "v2.0.0",
        "--review-date",
        "2026-08-30",
    ]
    _, plan_stdout, _ = _invoke(
        valid_registry_root,
        arguments + ["--check-only"],
        capsys,
    )
    plan = json.loads(plan_stdout)
    winner_data = _registry_data([_entry()])
    winner_data["concurrent"] = {"exact": "review-repo-winner"}
    winner = _render_fixture(winner_data)
    hook_calls = 0

    def publish_winner(boundary_path: Path) -> None:
        nonlocal hook_calls
        hook_calls += 1
        assert boundary_path == path
        boundary_path.write_bytes(winner)

    monkeypatch.setattr(registry, "_before_secure_replace", publish_winner)
    code, stdout, stderr = _invoke(
        valid_registry_root,
        arguments + ["--expected-sha256", plan["beforeSha256"]],
        capsys,
    )
    assert code == 3
    assert stdout == ""
    assert "ambiguous" in stderr.casefold()
    assert path.read_bytes() == winner
    assert hook_calls == 1

    state_code, state_stdout, state_stderr = _invoke(
        valid_registry_root,
        ["state", "--id", "alpha", "--expected-url", _entry()["url"]],
        capsys,
    )
    assert state_code == 0
    assert state_stderr == ""
    assert json.loads(state_stdout)["beforeSha256"] == hashlib.sha256(winner).hexdigest()
    assert path.read_bytes() == winner
    assert hook_calls == 1


def test_review_full_complete_sets_clean_root_state_and_preserves_other_data(
    tmp_path: Path,
    capsys: Any,
) -> None:
    repos = [
        _entry("first", "one", "first", "ONE", lastReviewDate="2026-08-30"),
        _entry("second", "two", "second", "TWO", lastReviewDate="2026-08-30"),
    ]
    data = {
        "schemaVersion": EXPECTED_SCHEMA_VERSION,
        "rootExtension": Decimal("1e400"),
        "lastFullReview": None,
        "lastFullReviewNote": "partial - second",
        "repos": repos,
    }
    path = _write_registry(tmp_path, raw=registry.render_registry(data))
    arguments = [
        "review-full",
        "--outcome",
        "complete",
        "--review-date",
        "2026-08-30",
        "--reviewed-id",
        "second",
        "--reviewed-id",
        "first",
    ]
    _, plan_stdout, plan_stderr = _invoke(
        tmp_path,
        arguments + ["--check-only"],
        capsys,
    )
    plan = json.loads(plan_stdout)
    assert plan_stderr == ""
    assert plan["reviewedIds"] == ["first", "second"]
    assert plan["failedIds"] == []
    assert plan["beforeScopeDigestSha256"] == registry._scope_digest(data)
    assert plan["afterScopeDigestSha256"] != plan["beforeScopeDigestSha256"]
    assert plan["rootReview"]["lastFullReview"]["value"] == "2026-08-30"
    assert plan["rootReview"]["lastFullReviewNote"]["present"] is False

    code, stdout, stderr = _invoke(
        tmp_path,
        arguments + ["--expected-sha256", plan["beforeSha256"]],
        capsys,
    )
    applied = json.loads(stdout)
    assert code == 0
    assert stderr == ""
    assert applied["afterSha256"] == plan["afterSha256"]
    assert applied["afterScopeDigestSha256"] == plan["afterScopeDigestSha256"]
    updated = json.loads(path.read_text("utf-8"), parse_float=Decimal)
    assert updated["lastFullReview"] == "2026-08-30"
    assert "lastFullReviewNote" not in updated
    assert updated["repos"] == repos
    assert updated["rootExtension"] == Decimal("1e400")


def test_review_full_final_boundary_race_preserves_winner_and_reconciles_read_only(
    tmp_path: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repos = [
        _entry("first", "one", "first", "ONE", lastReviewDate="2026-08-30"),
        _entry("second", "two", "second", "TWO", lastReviewDate="2026-08-30"),
    ]
    path = _write_registry(tmp_path, _registry_data(repos))
    arguments = [
        "review-full",
        "--outcome",
        "complete",
        "--review-date",
        "2026-08-30",
        "--reviewed-id",
        "first",
        "--reviewed-id",
        "second",
    ]
    _, plan_stdout, _ = _invoke(tmp_path, arguments + ["--check-only"], capsys)
    plan = json.loads(plan_stdout)
    winner_data = _registry_data(repos)
    winner_data["concurrent"] = {"exact": "review-full-winner"}
    winner = _render_fixture(winner_data)
    hook_calls = 0

    def publish_winner(boundary_path: Path) -> None:
        nonlocal hook_calls
        hook_calls += 1
        assert boundary_path == path
        boundary_path.write_bytes(winner)

    monkeypatch.setattr(registry, "_before_secure_replace", publish_winner)
    code, stdout, stderr = _invoke(
        tmp_path,
        arguments + ["--expected-sha256", plan["beforeSha256"]],
        capsys,
    )
    assert code == 3
    assert stdout == ""
    assert "ambiguous" in stderr.casefold()
    assert path.read_bytes() == winner
    assert hook_calls == 1

    state_code, state_stdout, state_stderr = _invoke(tmp_path, ["state"], capsys)
    assert state_code == 0
    assert state_stderr == ""
    assert json.loads(state_stdout)["beforeSha256"] == hashlib.sha256(winner).hexdigest()
    assert path.read_bytes() == winner
    assert hook_calls == 1


def test_review_full_partial_orders_failed_ids_and_updates_only_root(
    tmp_path: Path,
    capsys: Any,
) -> None:
    repos = [
        _entry("first", "one", "first", "ONE", lastReviewDate="2026-08-30"),
        _entry("second", "two", "second", "TWO"),
        _entry("third", "three", "third", "THREE"),
    ]
    data = _registry_data(repos)
    data["rootExtension"] = {"keep": True}
    path = _write_registry(tmp_path, data)
    arguments = [
        "review-full",
        "--outcome",
        "partial",
        "--review-date",
        "2026-08-30",
        "--reviewed-id",
        "first",
        "--failed-id",
        "third",
        "--failed-id",
        "second",
    ]
    _, plan_stdout, _ = _invoke(tmp_path, arguments + ["--check-only"], capsys)
    plan = json.loads(plan_stdout)
    assert plan["reviewedIds"] == ["first"]
    assert plan["failedIds"] == ["second", "third"]
    assert plan["rootReview"] == {
        "lastFullReview": {"present": True, "value": None},
        "lastFullReviewNote": {
            "present": True,
            "value": "partial - second, third",
        },
    }

    code, _, stderr = _invoke(
        tmp_path,
        arguments + ["--expected-sha256", plan["beforeSha256"]],
        capsys,
    )
    assert code == 0
    assert stderr == ""
    updated = json.loads(path.read_text("utf-8"))
    assert updated["lastFullReview"] is None
    assert updated["lastFullReviewNote"] == "partial - second, third"
    assert updated["repos"] == repos
    assert updated["rootExtension"] == {"keep": True}


@pytest.mark.parametrize(
    ("outcome", "reviewed", "failed", "term"),
    [
        ("complete", ["first"], ["second"], "complete"),
        ("partial", ["first", "second"], [], "partial"),
        ("partial", ["first"], ["first", "second"], "disjoint"),
        ("partial", ["first"], [], "partition"),
        ("partial", ["first"], ["unknown"], "partition"),
        ("partial", ["first", "first"], ["second"], "duplicates"),
    ],
)
def test_review_full_rejects_invalid_scope_declarations(
    tmp_path: Path,
    capsys: Any,
    outcome: str,
    reviewed: List[str],
    failed: List[str],
    term: str,
) -> None:
    repos = [
        _entry("first", "one", "first", "ONE", lastReviewDate="2026-08-30"),
        _entry("second", "two", "second", "TWO", lastReviewDate="2026-08-30"),
    ]
    _write_registry(tmp_path, _registry_data(repos))
    arguments = [
        "review-full",
        "--outcome",
        outcome,
        "--review-date",
        "2026-08-30",
    ]
    for repo_id in reviewed:
        arguments.extend(["--reviewed-id", repo_id])
    for repo_id in failed:
        arguments.extend(["--failed-id", repo_id])
    arguments.append("--check-only")
    _assert_failure(tmp_path, arguments, capsys, term)


def test_review_full_requires_this_runs_date_for_each_reviewed_repo(
    tmp_path: Path,
    capsys: Any,
) -> None:
    repos = [
        _entry("first", "one", "first", "ONE", lastReviewDate="2026-08-29"),
        _entry("second", "two", "second", "TWO", lastReviewDate="2026-08-30"),
    ]
    _write_registry(tmp_path, _registry_data(repos))
    _assert_failure(
        tmp_path,
        [
            "review-full",
            "--outcome",
            "complete",
            "--review-date",
            "2026-08-30",
            "--reviewed-id",
            "first",
            "--reviewed-id",
            "second",
            "--check-only",
        ],
        capsys,
        "first",
        "lastreviewdate",
    )


def test_review_full_check_only_requires_last_accepted_chain_before_transform(
    tmp_path: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repos = [
        _entry("first", "one", "first", "ONE", lastReviewDate="2026-08-30"),
        _entry("second", "two", "second", "TWO", lastReviewDate="2026-08-30"),
    ]
    path = _write_registry(tmp_path, _registry_data(repos))
    accepted_source = path.read_bytes()
    accepted_data = json.loads(accepted_source.decode("utf-8"))
    changed = copy.deepcopy(accepted_data)
    changed["unrelated"] = "winner"
    winner = _render_fixture(changed)
    path.write_bytes(winner)

    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("review-full transformed after stale chain")

    monkeypatch.setattr(registry, "review_full", forbidden)
    _assert_failure(
        tmp_path,
        [
            "review-full",
            "--outcome",
            "complete",
            "--review-date",
            "2026-08-30",
            "--reviewed-id",
            "first",
            "--reviewed-id",
            "second",
            "--expected-chain-sha256",
            hashlib.sha256(accepted_source).hexdigest(),
            "--expected-scope-digest-sha256",
            registry._scope_digest(accepted_data),
            "--check-only",
        ],
        capsys,
        "stale",
    )
    assert path.read_bytes() == winner


@pytest.mark.parametrize(
    "mutation",
    [
        "same-id-url",
        "release-regression",
        "review-date",
        "add-repo",
        "remove-repo",
        "root-review",
    ],
)
def test_review_full_check_only_rejects_scope_projection_drift_before_transform(
    tmp_path: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    repos = [
        _entry("first", "one", "first", "ONE", lastReviewDate="2026-08-30"),
        _entry("second", "two", "second", "TWO", lastReviewDate="2026-08-30"),
    ]
    accepted = _registry_data(repos)
    accepted_scope_digest = registry._scope_digest(accepted)
    changed = copy.deepcopy(accepted)
    if mutation == "same-id-url":
        replacement_url = "https://github.com/replacement/first"
        changed["repos"][0]["url"] = replacement_url
        changed["repos"][0]["releasesUrl"] = replacement_url + "/releases"
    elif mutation == "release-regression":
        changed["repos"][0]["lastReviewedRelease"] = "v0.9.0"
    elif mutation == "review-date":
        changed["repos"][0]["lastReviewDate"] = "2026-08-29"
    elif mutation == "add-repo":
        changed["repos"].append(
            _entry("third", "three", "third", "THREE", lastReviewDate="2026-08-30")
        )
    elif mutation == "remove-repo":
        changed["repos"].pop()
    else:
        changed["lastFullReview"] = "2026-08-29"
    path = _write_registry(tmp_path, changed)
    winner = path.read_bytes()

    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("review-full transformed after scope drift")

    monkeypatch.setattr(registry, "review_full", forbidden)
    _assert_failure(
        tmp_path,
        [
            "review-full",
            "--outcome",
            "complete",
            "--review-date",
            "2026-08-30",
            "--reviewed-id",
            "first",
            "--reviewed-id",
            "second",
            "--expected-chain-sha256",
            hashlib.sha256(winner).hexdigest(),
            "--expected-scope-digest-sha256",
            accepted_scope_digest,
            "--check-only",
        ],
        capsys,
        "scope",
        "stale",
    )
    assert path.read_bytes() == winner


def test_scope_digest_is_deterministic_and_covers_ordered_review_projection() -> None:
    first = _registry_data(
        [
            _entry("first", "one", "first", "ONE"),
            _entry("second", "two", "second", "TWO"),
        ]
    )
    duplicate = copy.deepcopy(first)
    unrelated = copy.deepcopy(first)
    unrelated["extension"] = "not in the review projection"
    reordered = copy.deepcopy(first)
    reordered["repos"].reverse()

    assert registry._scope_digest(first) == registry._scope_digest(duplicate)
    assert registry._scope_digest(first) == registry._scope_digest(unrelated)
    assert registry._scope_digest(first) != registry._scope_digest(reordered)


@pytest.mark.parametrize(
    ("mutate", "term"),
    [
        (lambda data: data["repos"][0].update(lastReviewedRelease=""), "1-128"),
        (lambda data: data["repos"][0].update(lastReviewedRelease="   "), "1-128"),
        (lambda data: data["repos"][0].pop("lastReviewDate"), "requires"),
        (
            lambda data: data["repos"][0].update(
                lastReviewedRelease=None,
                lastReviewDate="2026-08-28",
            ),
            "without",
        ),
        (
            lambda data: data["repos"][0].update(lastReviewDate="2999-01-01"),
            "future",
        ),
        (lambda data: data.update(lastFullReview="2999-01-01"), "future"),
        (
            lambda data: data.update(
                lastFullReview="2026-08-28",
                lastFullReviewNote="partial - alpha",
            ),
            "null",
        ),
        (
            lambda data: (
                data.pop("lastFullReview", None),
                data.update(lastFullReviewNote="partial - alpha"),
            ),
            "null",
        ),
    ],
)
def test_review_state_schema_invariants_are_enforced(
    tmp_path: Path,
    capsys: Any,
    mutate: Any,
    term: str,
) -> None:
    data = _registry_data([_entry()])
    mutate(data)
    _write_registry(tmp_path, data)
    _assert_failure(tmp_path, ["state"], capsys, term)


def test_every_writer_response_variant_is_bounded_before_dispatch(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _registry_path(valid_registry_root)
    before = path.read_bytes()
    calls = 0
    original_render = registry._render_response

    def reject_warning_variant(payload: Mapping[str, Any]) -> str:
        if payload.get("warnings"):
            raise registry.RegistryError("simulated response size bound")
        return original_render(payload)

    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        raise AssertionError("writer dispatched before all responses were bounded")

    monkeypatch.setattr(registry, "_render_response", reject_warning_variant)
    monkeypatch.setattr(registry.secure_fs, "secure_write_bytes", forbidden)
    _assert_failure(
        valid_registry_root,
        ["add", "--url", "https://github.com/acme/widget"],
        capsys,
        "response",
        "bound",
    )
    assert calls == 0
    assert path.read_bytes() == before


def test_response_byte_limit_is_enforced_for_read_only_state(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(registry, "MAX_RESPONSE_BYTES", 32)
    _assert_failure(valid_registry_root, ["state"], capsys, "response", "32")


def test_runtime_warning_is_captured_under_warnings_as_errors_and_is_success(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _registry_path(valid_registry_root)
    original_write = registry.secure_fs.secure_write_bytes

    def write_then_warn(*args: Any, **kwargs: Any) -> Path:
        result = original_write(*args, **kwargs)
        warnings.warn(
            "Publication committed; recovery preserved as .repos.previous",
            RuntimeWarning,
        )
        return result

    monkeypatch.setattr(registry.secure_fs, "secure_write_bytes", write_then_warn)
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        code, stdout, stderr = _invoke(
            valid_registry_root,
            ["add", "--url", "https://github.com/acme/widget"],
            capsys,
        )

    assert code == 0
    assert stderr == ""
    assert json.loads(stdout)["warnings"] == ["secure-fs-recovery-preserved"]
    assert json.loads(path.read_text("utf-8"))["repos"][-1]["id"] == "widget"


@pytest.mark.parametrize("failure_point", ["write", "flush"])
def test_stdout_write_or_flush_failure_after_commit_is_exit_three_and_reconciles(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
    failure_point: str,
) -> None:
    path = _registry_path(valid_registry_root)
    before_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    original_stdout = registry.sys.stdout

    class FailingStdout:
        def write(self, value: str) -> int:
            if failure_point == "write":
                raise OSError("simulated stdout write failure")
            return len(value)

        def flush(self) -> None:
            if failure_point == "flush":
                raise OSError("simulated stdout flush failure")

    monkeypatch.setattr(registry.sys, "stdout", FailingStdout())
    code = registry.main(
        [
            "--root",
            str(valid_registry_root),
            "add",
            "--url",
            "https://github.com/acme/widget",
            "--expected-sha256",
            before_sha256,
        ]
    )
    captured = capsys.readouterr()
    assert code == 3
    assert "ambiguous" in captured.err.casefold()
    assert json.loads(path.read_text("utf-8"))["repos"][-1]["id"] == "widget"

    monkeypatch.setattr(registry.sys, "stdout", original_stdout)
    state_code = registry.main(
        [
            "--root",
            str(valid_registry_root),
            "state",
            "--id",
            "widget",
            "--expected-url",
            "https://github.com/acme/widget",
        ]
    )
    state_captured = capsys.readouterr()
    state = json.loads(state_captured.out)
    assert state_code == 0
    assert state_captured.err == ""
    assert state["beforeSha256"] != before_sha256
    assert state["selection"]["urlMatches"] is True


def test_writer_exception_is_dispatched_once_and_never_retried(
    valid_registry_root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def fail_once(*_args: Any, **_kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        raise OSError("simulated ambiguous writer failure")

    monkeypatch.setattr(registry.secure_fs, "secure_write_bytes", fail_once)
    _assert_ambiguous(
        valid_registry_root,
        ["add", "--url", "https://github.com/acme/widget"],
        capsys,
        "ambiguous",
    )
    assert calls == 1


def test_subprocess_exit_three_has_one_ambiguous_diagnostic(tmp_path: Path) -> None:
    root = tmp_path / "ambiguous"
    path = _write_registry(root, _registry_data([]))
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    code = (
        "import sys; sys.path.insert(0, sys.argv[1]); "
        "import cg_compound_gpid_rd_registry as r; "
        "r.secure_fs.secure_write_bytes=lambda *a,**k: "
        "(_ for _ in ()).throw(OSError('subprocess writer failure')); "
        "raise SystemExit(r.main(['--root',sys.argv[2],'add','--url',"
        "'https://github.com/acme/widget','--expected-sha256',sys.argv[3]]))"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            code,
            str(Path(registry.__file__).resolve().parent),
            str(root),
            expected,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 3
    assert result.stdout == ""
    assert result.stderr.startswith("Ambiguous: ")
    assert len(result.stderr.rstrip("\n").splitlines()) == 1
    assert path.read_bytes() == _render_fixture(_registry_data([]))


@pytest.mark.parametrize(
    "arguments",
    [
        ["state", "--id", "alpha"],
        ["state", "--expected-url", "https://github.com/example/alpha"],
        ["add", "--url", "https://github.com/a/b"],
        [
            "add",
            "--url",
            "https://github.com/a/b",
            "--check-only",
            "--expected-sha256",
            "0" * 64,
        ],
        ["remove", "--id", "alpha", "--check-only", "--confirm-id", "alpha"],
        [
            "review-repo",
            "--id",
            "alpha",
            "--expected-url",
            "https://github.com/example/alpha",
            "--check-only",
        ],
        [
            "review-full",
            "--outcome",
            "complete",
            "--review-date",
            "2026-08-30",
        ],
        [
            "review-repo",
            "--id",
            "alpha",
            "--expected-url",
            "https://github.com/example/alpha",
            "--release",
            "v2",
            "--review-date",
            "2026-08-30",
            "--expected-last-review-date",
            "2026-08-28",
            "--expected-chain-sha256",
            "0" * 64,
            "--check-only",
        ],
        [
            "review-repo",
            "--id",
            "alpha",
            "--expected-url",
            "https://github.com/example/alpha",
            "--release",
            "v2",
            "--review-date",
            "2026-08-30",
            "--expected-last-reviewed-release",
            "v1.0.0",
            "--expected-chain-sha256",
            "0" * 64,
            "--check-only",
        ],
        [
            "review-repo",
            "--id",
            "alpha",
            "--expected-url",
            "https://github.com/example/alpha",
            "--release",
            "v2",
            "--review-date",
            "2026-08-30",
            "--expected-last-reviewed-release",
            "v1.0.0",
            "--expected-last-review-date",
            "2026-08-28",
            "--check-only",
        ],
        [
            "review-full",
            "--outcome",
            "complete",
            "--review-date",
            "2026-08-30",
            "--reviewed-id",
            "alpha",
            "--expected-chain-sha256",
            "0" * 64,
            "--check-only",
        ],
        [
            "review-full",
            "--outcome",
            "complete",
            "--review-date",
            "2026-08-30",
            "--reviewed-id",
            "alpha",
            "--expected-scope-digest-sha256",
            "0" * 64,
            "--check-only",
        ],
    ],
)
def test_new_cli_contract_syntax_errors_exit_two(
    valid_registry_root: Path,
    capsys: Any,
    arguments: List[str],
) -> None:
    before = _registry_path(valid_registry_root).read_bytes()
    with pytest.raises(SystemExit) as caught:
        registry.main(["--root", str(valid_registry_root)] + arguments)
    captured = capsys.readouterr()
    assert caught.value.code == 2
    assert captured.out == ""
    assert "usage:" in captured.err.casefold()
    assert _registry_path(valid_registry_root).read_bytes() == before
