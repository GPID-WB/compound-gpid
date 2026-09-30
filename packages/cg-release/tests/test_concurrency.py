"""Real local bare-Git sibling updates and immutable transaction records."""

import subprocess
from pathlib import Path

import pytest

from cg_release.events import ControllerError
from cg_release.git_journal import LocalGitStore
from cg_release.journal import Journal
from cg_release.models import Request, load_record


def git(directory: Path, *args: str, text: str | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=directory,
        input=text,
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    return result.stdout.strip()


@pytest.fixture
def git_store(tmp_path: Path) -> LocalGitStore:
    bare = tmp_path / "state.git"
    bare.mkdir()
    git(bare, "init", "--bare")
    tree = git(bare, "mktree", text="")
    commit = git(
        bare,
        "-c",
        "user.name=Control",
        "-c",
        "user.email=control@example.invalid",
        "commit-tree",
        tree,
        "-m",
        "Reviewed journal bootstrap",
    )
    git(bare, "update-ref", "refs/heads/release-controller-state", commit)
    return LocalGitStore(
        bare,
        "release-controller-state",
        anchor=commit,
        writer="Control <control@example.invalid>",
    )


def fixture_request() -> Request:
    return load_record(
        Request, (Path(__file__).parent / "fixtures/request.json").read_bytes()
    )


def test_real_git_siblings_reject_loser_without_force_or_lost_record(
    git_store: LocalGitStore,
) -> None:
    original = git_store.append
    first = fixture_request()
    second = first.model_copy(
        update={"nonce": "b" * 32, "version": "2.0.0", "tag": "v2.0.0"}
    )
    raced = False

    def sibling(parent, event, record):
        nonlocal raced
        if not raced:
            raced = True
            git_store.append = original
            Journal(git_store).admit(second)
            git_store.append = sibling
        return original(parent, event, record)

    git_store.append = sibling
    Journal(git_store).admit(first)
    assert len(Journal(git_store).records()) == 2
    anchor, history = git_store.history()
    assert history[0].parent == anchor
    assert history[1].parent == history[0].commit
    assert len(history) == 2


def test_real_git_rejects_rewritten_or_missing_anchor(git_store: LocalGitStore) -> None:
    Journal(git_store).admit(fixture_request())
    # A wrong bootstrap identity must fail even when each event is otherwise valid.
    other = LocalGitStore(
        git_store.directory, git_store.branch, anchor="f" * 40, writer=git_store.writer
    )
    with pytest.raises(ControllerError):
        Journal(other).records()


def test_real_git_persists_record_and_reservation_in_one_tree(
    git_store: LocalGitStore,
) -> None:
    record = Journal(git_store).admit(fixture_request())
    paths = git(
        git_store.directory,
        "ls-tree",
        "-r",
        "--name-only",
        f"refs/heads/{git_store.branch}",
    ).splitlines()
    assert "events/0000000001.json" in paths
    assert any(path.startswith("requests/") for path in paths)
    assert any(path.startswith("reservations/") for path in paths)
    assert Journal(git_store).get(record.request_id) == record


def test_real_git_queue_checkpoint_coexists_with_request_history(
    git_store: LocalGitStore,
) -> None:
    from cg_release.queue import cursor_for, scan

    journal = Journal(git_store)
    record = journal.admit(fixture_request())
    scan(journal, [{"number": 1}], lambda item: None)
    restarted = Journal(git_store)
    assert restarted.get(record.request_id) == record
    assert cursor_for(restarted).cycle == 1
    assert len(restarted.events()) == 2


def test_local_store_cannot_target_a_normal_checkout(tmp_path: Path) -> None:
    git(tmp_path, "init")
    with pytest.raises(ControllerError):
        LocalGitStore(
            tmp_path,
            "state",
            anchor="a" * 40,
            writer="Control <control@example.invalid>",
        )
