"""Fast semantic contracts for secure stable and dev-prerelease publication."""

import os
import re
import subprocess
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
        "Get-CgReleaseReservation",
    ):
        assert contract in script
    assert "-Method Delete" not in script
    assert "-Method Patch" not in script
    assert 'push origin --no-follow-tags "$tagObject`:refs/tags/$Tag"' in script
    assert script.index('-Method Post -Body $payload') < script.index('actions/workflows/release-docs.yml/runs')
    assert '"FINALIZED|' in script
    assert 'make_latest = "false"' in script
    assert 'Write-Host "RESERVED ($reservationStatus)' in script
    assert 'Write-Host "FINALIZED:' in script


def test_release_push_does_not_follow_other_annotated_tags(tmp_path: Path) -> None:
    """The production push must publish only its raw-object refspec."""
    push_flags = re.findall(
        r'git -C \$PSScriptRoot push origin\s+([^"\r\n]*)'
        r'"\$tagObject`:refs/tags/\$Tag"',
        _read("create-release.ps1"),
    )
    assert len(push_flags) == 1
    source = tmp_path / "source"
    remote = tmp_path / "remote.git"
    hooks = tmp_path / "empty-hooks"
    source.mkdir()
    hooks.mkdir()
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_ALLOW_PROTOCOL="file",
    )

    def git(*args: str) -> str:
        return subprocess.run(
            [
                "git", "-C", str(source),
                "-c", f"core.hooksPath={hooks.as_posix()}",
                "-c", f"init.templateDir={hooks.as_posix()}",
                "-c", "user.name=Release Test",
                "-c", "user.email=release-test@example.invalid",
                "-c", "commit.gpgSign=false",
                "-c", "tag.gpgSign=false",
                "-c", "push.gpgSign=false",
                *args,
            ],
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout.strip()

    git("init")
    git("init", "--bare", str(remote))
    git("remote", "add", "origin", remote.as_posix())
    git("commit", "--allow-empty", "-m", "Release fixture")
    for tag in ("v1.2.0.9015", "v1.2.0.9016"):
        git("tag", "-a", tag, "-m", tag, "HEAD")
    tag_object = git("rev-parse", "refs/tags/v1.2.0.9015")
    assert git("cat-file", "-t", tag_object) == "tag"

    git(
        "-c", "push.followTags=true", "push", "origin",
        *push_flags[0].split(), f"{tag_object}:refs/tags/v1.2.0.9015",
    )

    assert git("ls-remote", "--tags", "--refs", "origin").splitlines() == [
        f"{tag_object}\trefs/tags/v1.2.0.9015"
    ]


def test_generated_release_commands_reserve_before_docs_and_finalize() -> None:
    for relative in RELEASE_PROMPTS:
        prompt = _read(relative)
        assert prompt.index("git tag -a <next-tag>") < prompt.index(".\\create-release.ps1 -Phase Reserve")
        assert prompt.index(".\\create-release.ps1 -Phase Reserve") < prompt.index("Wait for the unprivileged `release-docs.yml`")
        assert prompt.index("Wait for the unprivileged `release-docs.yml`") < prompt.index(".\\create-release.ps1 -Phase Finalize")
        assert "git push origin <next-tag>" not in prompt
        assert "no true distributed atomicity" in prompt
        assert "canonical and generated evidence" in prompt
        assert 'Every reservation sets `make_latest: "false"`, including stable tags' in prompt
        assert "Neither Reserve nor Finalize promotes a Release" in prompt


def test_release_identity_text_comparisons_are_case_sensitive() -> None:
    script = _read("create-release.ps1")
    assert "[string]$recordedPayload.name -cne $Name" in script
    assert "[string]$Release.name -cne $ExpectedName" in script
    assert "(ConvertTo-CgNormalizedReleaseText $Release.body) -cne" in script
    assert "$_.head_sha -ceq $headCommit -and $_.head_branch -ceq $Tag" in script
    assert "$_.name -ceq $controllerRunName -and $_.display_title -ceq $controllerRunName" in script


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


def test_release_docs_build_checks_metadata_as_a_workflow_step() -> None:
    workflow = _read(".github/workflows/release-docs.yml")

    assert (
        "\n      - name: Require combined release metadata\n"
        "        run: test -f combined-artifact/.docs-build-metadata.json\n"
        in workflow
    )
    assert (
        "\n          - name: Require combined release metadata\n"
        "            run: test -f combined-artifact/.docs-build-metadata.json\n"
        not in workflow
    )
