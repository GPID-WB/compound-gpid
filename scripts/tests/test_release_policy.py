"""Fast semantic contracts for secure stable and dev-prerelease publication."""

import os
import re
import subprocess
from pathlib import Path

import yaml


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


def _workflow(relative: str) -> dict:
    """Parse workflow structure without interpreting GitHub's `on` as a bool."""
    return yaml.load(_read(relative), Loader=yaml.BaseLoader)


def _commands(job: dict) -> str:
    """Read executable commands from actual job steps, excluding comments."""
    return "\n".join(step.get("run", "") for step in job["steps"])


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


def test_tag_build_is_unprivileged_and_release_controller_remains_protected() -> None:
    builder = _read(".github/workflows/release-docs.yml")
    controller = _read(".github/workflows/release-pages.yml")

    assert 'tags: ["v*.*.*", "!v*.*.*.*"]' in builder
    assert "pages: write" not in builder
    assert "id-token: write" not in builder
    assert 'workflows: ["Build release documentation"]' in controller
    assert "ref: main" in controller
    assert "Refusing to deploy an older release artifact" in controller
    assert "Recheck release is still newest" in controller
    assert "pages: write" in controller


def test_combined_docs_build_validates_stable_separately_from_proposed_source() -> None:
    workflow = _workflow(".github/workflows/docs-site-build.yml")
    build = workflow["jobs"]["build"]
    commands = _commands(build)
    stable = [step for step in build["steps"] if step.get("with", {}).get("path") == ".docs-stable"]
    assert len(stable) == 1
    assert stable[0]["with"]["ref"] == "main"
    assert "npm run docs:build" in commands
    assert "check-docs-site.js --source-root .docs-stable --docs-root .docs-stable/docs --legacy" in commands
    assert "check-rendered-docs.js .site" in commands
    assert "check-rendered-docs.js .docs-combined/site/dev" in commands


def test_combined_docs_build_rebuilds_sources_without_publication_credentials() -> None:
    workflow = _workflow(".github/workflows/docs-site-build.yml")
    build = workflow["jobs"]["build"]
    commands = _commands(build)
    assert set(workflow["on"]) == {"pull_request", "workflow_dispatch"}
    assert set(workflow["on"]["pull_request"]["branches"]) == {"main", "dev"}
    assert workflow["permissions"] == {"contents": "read"}
    assert build.get("permissions", workflow["permissions"]) == {"contents": "read"}
    assert "npm run docs:build" in commands
    assert "node scripts/rebuild-docs.js --root .docs-stable --all" in commands
    assert "node scripts/rebuild-docs.js --all" in _read("package.json")
    assert all("actions/deploy-pages@" not in step.get("uses", "") for step in build["steps"])


def test_pages_builds_both_branches_and_deploys_only_verified_current_artifacts() -> None:
    pages = _workflow(".github/workflows/pages.yml")
    build, deploy = pages["jobs"]["build"], pages["jobs"]["deploy"]
    assert set(pages["on"]) == {"push", "workflow_dispatch"}
    assert pages["on"]["push"] == {"branches": ["main", "dev"]}
    assert pages["permissions"] == {"contents": "read"}
    assert build.get("permissions", pages["permissions"]) == {"contents": "read"}
    checkouts = [step["with"] for step in build["steps"] if step.get("uses", "").startswith("actions/checkout@")]
    assert checkouts[0]["ref"] == "${{ github.sha }}"
    assert all(checkout["persist-credentials"] == "false" for checkout in checkouts)
    for branch in ("main", "dev"):
        source = [checkout for checkout in checkouts if checkout.get("path") == f"sources/{branch}"]
        assert len(source) == 1
        assert source[0]["ref"] == "${{ github.ref_name == '" + branch + "' && github.sha || '" + branch + "' }}"
        assert f"rebuild-docs.js --root sources/{branch} --all" in _commands(build)
        assert f"commits/{branch}" in _commands(deploy)
        assert f'= "${branch.upper()}_SHA"' in _commands(deploy)
    assert "assemble-docs-site.js --verify combined-artifact" in _commands(build)
    uploads = [step for step in build["steps"] if step.get("uses", "").startswith("actions/upload-pages-artifact@")]
    assert len(uploads) == 1
    assert uploads[0]["with"]["path"] == "combined-artifact/site"
    assert deploy["needs"] == "build"
    assert deploy["permissions"] == {"contents": "read", "pages": "write", "id-token": "write"}
    assert deploy["environment"]["name"] == "github-pages"
    assert all("actions/checkout@" not in step.get("uses", "") for step in deploy["steps"])
    assert "node scripts/" not in _commands(deploy)
    assert any(step.get("uses", "").startswith("actions/deploy-pages@") for step in deploy["steps"])
    assert pages["concurrency"] == {"group": "pages", "cancel-in-progress": "false"}


def test_combined_docs_build_verifies_metadata_before_upload() -> None:
    build = _workflow(".github/workflows/docs-site-build.yml")["jobs"]["build"]
    verification = [index for index, step in enumerate(build["steps"])
                    if "assemble-docs-site.js --verify .docs-combined --main-root .docs-stable --dev-root ." in step.get("run", "")]
    uploads = [index for index, step in enumerate(build["steps"])
               if step.get("uses", "").startswith("actions/upload-artifact@")]
    assert len(verification) == len(uploads) == 1
    assert verification[0] < uploads[0]


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
