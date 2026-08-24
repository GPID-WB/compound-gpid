"""Fast semantic contracts for secure stable and dev-prerelease publication."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_release_branch_matrix_is_explicit() -> None:
    prompt = _read(".github/prompts/cg-release.prompt.md")
    script = _read("create-release.ps1")

    assert "Set `<release-branch>` to `dev` when `<prerelease>` is `true`" in prompt
    assert 'if ($isPrereleaseTag) { $releaseBranch = "dev" }' in script
    assert "$Tag -cmatch '^v\\d+\\.\\d+\\.\\d+\\.\\d+$'" in script
    assert "Draft releases are not supported" in script


def test_release_rulesets_and_exact_run_chain_are_required() -> None:
    script = _read("create-release.ps1")

    for contract in (
        "Protect release tags",
        "Restrict release tag creation",
        "Protect dev",
        "actions/workflows/release-docs.yml/runs",
        "actions/workflows/release-pages.yml/runs",
        "Assert-CgRemoteReleaseLineage",
        "Assert-CgRemoteTagCommit",
        "has no published GitHub Release",
        "Method Delete",
    ):
        assert contract in script


def test_tag_build_is_unprivileged_and_controller_is_main_owned() -> None:
    builder = _read(".github/workflows/release-docs.yml")
    controller = _read(".github/workflows/release-pages.yml")
    pages = _read(".github/workflows/pages.yml")

    assert 'tags: ["v*.*.*"]' in builder
    assert "pages: write" not in builder
    assert "id-token: write" not in builder
    assert 'workflows: ["Build release documentation"]' in controller
    assert "ref: main" in controller
    assert "Refusing to deploy an older release artifact" in controller
    assert "Recheck release is still newest" in controller
    assert "pages: write" in controller
    assert "push:" not in pages
    assert "workflow_dispatch:" not in pages
