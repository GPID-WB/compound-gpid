"""Fast semantic contracts for secure stable and dev-prerelease publication."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RELEASE_PROMPTS = (
    ".github/prompts/cg-release.prompt.md",
    ".kilo/commands/cg-release.md",
    ".claude/commands/cg-release.md",
    ".agents/commands/cg-release.md",
    ".opencode/commands/cg-release.md",
)


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_release_branch_matrix_is_explicit() -> None:
    prompt = _read(".github/prompts/cg-release.prompt.md")
    script = _read("create-release.ps1")

    assert "Set `<release-branch>` to `dev` when `<prerelease>` is `true`" in prompt
    assert 'if ($isPrereleaseTag) { $releaseBranch = "dev" }' in script
    assert "$Tag -cmatch '^v\\d+\\.\\d+\\.\\d+\\.\\d+$'" in script
    assert "Draft releases are not supported" in script


def test_prerelease_lineage_does_not_depend_on_main() -> None:
    prompt = _read(".github/prompts/cg-release.prompt.md")
    script = _read("create-release.ps1")
    builder = _read(".github/workflows/release-docs.yml")
    controller = _read(".github/workflows/release-pages.yml")

    assert "exact `origin/dev` lineage is the prerelease authorization boundary" in prompt
    assert "merge-base --is-ancestor origin/main HEAD" not in prompt
    assert "Prerelease branch is stale: origin/main" not in script
    assert "merge-base --is-ancestor $remoteMainCommit $headCommit" not in script
    assert 'git merge-base --is-ancestor "$RELEASE_SHA" "origin/$required_branch"' in builder
    assert 'git merge-base --is-ancestor "$RELEASE_SHA" "origin/$required_branch"' in controller
    assert 'git fetch origin "$required_branch"' in builder
    assert 'git fetch origin "$required_branch"' in controller
    assert "git fetch origin main dev" not in builder
    assert "git fetch origin main dev" not in controller
    assert 'git merge-base --is-ancestor origin/main "$RELEASE_SHA"' not in builder
    assert 'git merge-base --is-ancestor origin/main "$RELEASE_SHA"' not in controller


def test_all_materialized_release_commands_allow_prereleases_from_dev() -> None:
    for relative in RELEASE_PROMPTS:
        prompt = _read(relative)

        assert (
            "Set `<release-branch>` to `dev` when `<prerelease>` is `true`" in prompt
        )
        assert "four-component prerelease tags are released directly" in prompt
        assert (
            "Require a clean, up-to-date `main` checkout before writing payloads"
            not in prompt
        )


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


def test_tag_build_is_unprivileged_and_dev_preview_controller_is_branch_local() -> None:
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
    assert "push:\n    branches: [dev]" in pages
    assert "workflow_run:" not in pages


def test_combined_docs_build_validates_legacy_main_separately_from_dev() -> None:
    workflow = _read(".github/workflows/docs-site-build.yml")

    assert (
        'working-directory: sources/main\n'
        '        run: node "$GITHUB_WORKSPACE/sources/dev/scripts/check-docs-site.js" --legacy'
    ) in workflow
    assert (
        'working-directory: sources/dev\n'
        '        run: node scripts/check-docs-site.js'
    ) in workflow


def test_combined_docs_build_does_not_rebuild_legacy_main_source() -> None:
    workflow = _read(".github/workflows/docs-site-build.yml")

    assert "sources/main/scripts/rebuild-docs.js" not in workflow
    assert "sources/dev/scripts/rebuild-docs.js --root \"$GITHUB_WORKSPACE/sources/dev\" --all" in workflow


def test_dev_pages_controller_is_branch_local_and_uses_main_as_content_only() -> None:
    pages = _read(".github/workflows/pages.yml")

    assert "push:\n    branches: [dev]" in pages
    assert "workflow_run:" not in pages
    assert "ref: dev" in pages
    assert "ref: main" in pages
    assert "path: sources/main" in pages
    assert "--dev-root \"$GITHUB_WORKSPACE\"" in pages
    assert "scripts/assemble-docs-site.js" in pages
    assert "actions/upload-pages-artifact" in pages
    assert "actions/deploy-pages" in pages
    assert "run-id:" not in pages
    assert "current-dev" not in pages


def test_combined_docs_build_checks_metadata_as_a_workflow_step() -> None:
    workflow = _read(".github/workflows/docs-site-build.yml")

    assert (
        "\n      - name: Require combined build metadata\n"
        "        run: test -f combined-artifact/.docs-build-metadata.json\n"
        in workflow
    )
    assert (
        "\n          - name: Require combined build metadata\n"
        "            run: test -f combined-artifact/.docs-build-metadata.json\n"
        not in workflow
    )
