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


def test_release_branch_matrix_is_explicit() -> None:
    prompt = _read(".github/prompts/cg-release.prompt.md")
    script = _read("create-release.ps1")

    assert "production_branches" in prompt
    assert "remotely discovered default branch" in prompt
    assert "any verified same-repository remote branch" in prompt
    assert "-SourceBranch <release-branch>" in prompt
    assert "$releaseBranch = $SourceBranch" in script
    assert "symbolic-ref --quiet --short HEAD" in script
    assert "detached release checkout requires explicit -SourceBranch" in script
    assert "$Tag -cmatch '^v\\d+\\.\\d+\\.\\d+\\.\\d+$'" in script
    assert "Draft releases are not supported" in script


def test_prerelease_lineage_does_not_depend_on_main() -> None:
    prompt = _read(".github/prompts/cg-release.prompt.md")
    script = _read("create-release.ps1")
    builder = _read(".github/workflows/release-docs.yml")
    controller = _read(".github/workflows/release-pages.yml")

    assert "identity and remote lineage are the source authorization boundary" in prompt
    assert "merge-base --is-ancestor origin/main HEAD" not in prompt
    assert "Prerelease branch is stale: origin/main" not in script
    stable_start = script.index("function Assert-CgStableDocsContract {")
    stable_end = script.index('\nif ([string]::IsNullOrWhiteSpace($Name))', stable_start)
    stable_gate = script[stable_start:stable_end]
    prerelease_path = script[:stable_start] + script[stable_end:]
    assert "$controllerCommit = $Authority.Commit" in stable_gate
    assert 'show "$controllerCommit`:.github/workflows/release-pages.yml"' in stable_gate
    assert "merge-base --is-ancestor origin/main" not in stable_gate
    assert "merge-base --is-ancestor origin/main" not in prerelease_path
    assert "merge-base --is-ancestor $remoteMainCommit $headCommit" not in prerelease_path
    stable_call = (
        "if (-not $isPrereleaseTag) { "
        "Assert-CgStableDocsContract -ExpectedCommit $headCommit -Authority $authority }"
    )
    assert script.count("Assert-CgStableDocsContract -ExpectedCommit $headCommit -Authority $authority }") == 1
    assert stable_call in script
    assert script.index('if ($Phase -eq "Reserve") {') < script.index(stable_call)
    assert script.index(stable_call) < script.index('push origin --no-follow-tags')
    assert 'git merge-base --is-ancestor "$RELEASE_SHA" "origin/$required_branch"' in builder
    assert 'git merge-base --is-ancestor "$RELEASE_SHA" "origin/$required_branch"' in controller
    assert 'git fetch origin "$required_branch"' in builder
    assert 'git fetch origin "$required_branch"' in controller
    assert "release-version.js --resolve-source" in builder
    assert "release-version.js --resolve-source" in controller
    assert "git fetch origin main dev" not in builder
    assert "git fetch origin main dev" not in controller
    assert 'git merge-base --is-ancestor origin/main "$RELEASE_SHA"' not in builder
    assert 'git merge-base --is-ancestor origin/main "$RELEASE_SHA"' not in controller


def test_all_materialized_release_commands_allow_prereleases_from_dev() -> None:
    for relative in RELEASE_PROMPTS:
        prompt = _read(relative)

        assert "any verified same-repository remote branch" in prompt
        assert "including `dev`" in prompt
        assert "production_branches" in prompt
        assert "Set `<release-branch>` to `dev`" not in prompt
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


def test_tag_build_is_unprivileged_and_both_builders_use_protected_controller() -> None:
    builder = _read(".github/workflows/release-docs.yml")
    controller = _read(".github/workflows/release-pages.yml")
    pages = _read(".github/workflows/pages.yml")

    assert 'tags: ["v*.*.*"]' in builder
    assert "pages: write" not in builder
    assert "id-token: write" not in builder
    parsed = yaml.load(controller, Loader=yaml.BaseLoader)
    assert parsed["on"]["workflow_run"] == {
        "workflows": ["Build release documentation", "Deploy documentation site"],
        "types": ["completed"],
    }
    for job in parsed["jobs"].values():
        checkout = job["steps"][0]["with"]
        assert checkout["ref"] == "${{ github.sha }}"
        assert checkout["persist-credentials"] == "false"
    assert "Refusing to deploy an older release artifact" in controller
    assert "Recheck release is still newest" in controller
    assert "pages: write" in controller
    assert "push:\n    branches: [dev]" in pages
    assert "workflow_run:" not in pages


def test_prerelease_docs_destination_is_separate_from_source_authority() -> None:
    """Only stable tag classification enables the privileged full-site job."""
    controller = yaml.load(_read(".github/workflows/release-pages.yml"), Loader=yaml.BaseLoader)
    jobs = controller["jobs"]
    classifier = jobs["classify"]
    assert classifier["permissions"] == {"contents": "read", "actions": "read"}
    assert "environment" not in classifier
    assert jobs["deploy"]["needs"] == "classify"
    assert "needs.classify.outputs.full_site == 'true'" in jobs["deploy"]["if"]
    classify_step = next(step for step in classifier["steps"] if step.get("id") == "tag")
    assert 'node scripts/release-version.js --full-site-tag "$RELEASE_TAG"' in classify_step["run"]
    assert classify_step["env"]["RELEASE_TAG"] == "${{ github.event.workflow_run.head_branch }}"
    assert "needs" not in jobs["deploy-dev"]
    pages = yaml.load(_read(".github/workflows/pages.yml"), Loader=yaml.BaseLoader)
    assert "releases/**" in pages["on"]["push"]["paths"]
    assert ".github/shared/**" not in pages["on"]["push"]["paths"]


def test_official_sealing_preserves_existing_recovery_token_authority() -> None:
    """Recovery sealing uses the same App token as initial and final checks."""
    workflow = yaml.load(_read(".github/workflows/release-pages.yml"), Loader=yaml.BaseLoader)
    steps = workflow["jobs"]["deploy"]["steps"]
    token = "${{ steps.recovery-authority.outputs.token || github.token }}"
    initial = next(step for step in steps if step.get("id") == "authority")
    seal = next(step for step in steps if step.get("name") == "Seal durable official snapshot in the Pages artifact")
    final = next(step for step in steps if step.get("name") == "Recheck release is still newest")
    assert initial["env"]["GH_TOKEN"] == token
    assert seal["env"]["GH_TOKEN"] == token
    assert final["env"]["GH_TOKEN"] == token
    assert seal["run"] == "node scripts/legacy-pages.js seal-official release-source release-artifact"
    app = next(step for step in steps if step.get("id") == "recovery-authority")
    assert "workflow_dispatch" in app["if"]
    assert app["with"]["permission-administration"] == "read"


def test_combined_docs_build_validates_legacy_main_separately_from_dev() -> None:
    workflow = _read(".github/workflows/docs-site-build.yml")

    assert (
        'working-directory: sources/main\n'
        '        run: node "$GITHUB_WORKSPACE/sources/dev/scripts/check-docs-site.js" --legacy'
    ) in workflow
    assert (
        'working-directory: producer-input\n'
        '        run: node "$GITHUB_WORKSPACE/sources/dev/scripts/check-docs-site.js"'
    ) in workflow


def test_combined_docs_build_does_not_rebuild_legacy_main_source() -> None:
    workflow = _read(".github/workflows/docs-site-build.yml")

    assert "sources/main/scripts/rebuild-docs.js" not in workflow
    assert "cp -R sources/dev producer-input" in workflow
    assert "sources/dev/scripts/rebuild-docs.js --root \"$GITHUB_WORKSPACE/producer-input\" --all" in workflow
    assert "--root \"$GITHUB_WORKSPACE/sources/dev\" --all" not in workflow


def test_dev_builder_has_no_authority_and_controller_preserves_authenticated_official_data() -> None:
    pages = _read(".github/workflows/pages.yml")
    controller = yaml.load(
        _read(".github/workflows/release-pages.yml"), Loader=yaml.BaseLoader
    )["jobs"]["deploy-dev"]
    builder = yaml.load(pages, Loader=yaml.BaseLoader)

    assert "push:\n    branches: [dev]" in pages
    assert "workflow_run:" not in pages
    assert builder["permissions"] == {"contents": "read"}
    source_job = builder["jobs"]["deploy-dev-preview"]
    assert source_job["permissions"] == {"contents": "read"}
    assert "environment" not in source_job
    assert "ref: ${{ github.sha }}" in pages
    assert "persist-credentials: false" in pages
    assert "name: legacy-dev-docs" in pages
    assert ".docs-build-metadata.json" in pages
    assert "actions/upload-pages-artifact" not in pages
    assert "actions/deploy-pages" not in pages
    assert "run-id:" not in pages
    assert "current-dev" not in pages
    steps = controller["steps"]
    checkouts = [s["with"] for s in steps if s.get("uses", "").startswith("actions/checkout@")]
    assert [(s.get("path"), s["ref"]) for s in checkouts] == [
        (None, "${{ github.sha }}"),
        ("sources/dev", "${{ steps.authority.outputs.release_sha }}"),
    ]
    assert all(s["persist-credentials"] == "false" for s in checkouts)
    download = next(s["with"] for s in steps if s.get("uses", "").startswith("actions/download-artifact@") and s["with"]["path"] == "dev-artifact")
    assert download["run-id"] == "${{ github.event.workflow_run.id }}"
    assert download["artifact-ids"] == "${{ steps.authority.outputs.artifact_id }}"
    runs = "\n".join(s.get("run", "") for s in steps)
    assert "scripts/legacy-pages.js import-dev sources/dev dev-artifact" in runs
    assert "scripts/legacy-pages.js restore-official official-source official-state.json" in runs
    assert "scripts/legacy-pages.js recheck-official official-state.json" in runs
    assert "scripts/legacy-pages.js stamp-preview official-state.json combined-artifact" in runs
    assert "--main-root official-source" in runs
    assert "scripts/assemble-docs-site.js --verify combined-artifact" in runs
    assert "rebuild-docs.js" not in runs
    assert "node sources/" not in runs
    assert runs.count("node scripts/legacy-pages.js check") == 2
    assert controller["permissions"] == {
        "contents": "read", "actions": "read", "pages": "write", "id-token": "write",
    }


def test_combined_docs_build_checks_metadata_as_a_workflow_step() -> None:
    workflow = _read(".github/workflows/docs-site-build.yml")

    parsed = yaml.load(workflow, Loader=yaml.BaseLoader)
    steps = [step for job in parsed["jobs"].values() for step in job["steps"]
             if step.get("name") == "Require combined build metadata"]
    assert len(steps) == 1
    assert "test -f combined-artifact/.docs-build-metadata.json" in steps[0]["run"]
    assert "assemble-docs-site.js --verify combined-artifact" in steps[0]["run"]
    for flag in ("--main-root", "--dev-root", "--main-sha", "--dev-sha"):
        assert flag in steps[0]["run"]


def test_release_docs_build_checks_metadata_as_a_workflow_step() -> None:
    workflow = _read(".github/workflows/release-docs.yml")

    assert (
        "\n      - name: Require isolated release metadata\n"
        "        run: test -f .docs-build-metadata.json\n"
        in workflow
    )
    assert (
        "\n          - name: Require isolated release metadata\n"
        "            run: test -f .docs-build-metadata.json\n"
        not in workflow
    )
