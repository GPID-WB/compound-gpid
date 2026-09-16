"""Static isolation checks supplement, but never substitute for live boundary trials."""

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[3]


def test_release_workflow_isolates_registration_from_source_build():
    workflow = (ROOT / ".github/workflows/release-controller-ci.yml").read_text()
    register = workflow.split("  register:", 1)[1].split("  build:", 1)[0]
    build = workflow.split("  build:", 1)[1].split("  package:", 1)[0]
    assert "environment: release-control" in register
    assert "cg_release.build_worker register" in register
    assert "needs.register.outputs.source_sha" not in register
    assert (
        "secrets." not in build
        and "environment:" not in build
        and "GH_TOKEN" not in build
    )
    assert "CG_RELEASE_SOURCE_JOB: 'true'" in build
    assert "-I -m cg_release.build_worker build" in build
    assert "persist-credentials: false" in build
    assert "name: release-assets" in build and "if-no-files-found: error" in build
    assert "cache:" not in workflow and "pull_request_target" not in workflow


def test_generic_build_template_is_disabled_and_has_no_publication_secret():
    template = (ROOT / "packages/cg-release/templates/build.yml").read_text()
    assert "false &&" in template and "cg_release.build_worker register" in template
    assert (
        "RELEASE_PUBLISH" not in template
        and "permission-actions: write" not in template
    )
    assert "-I -m cg_release.build_worker build" in template


@pytest.mark.parametrize(
    "register,build,expected",
    [
        ("success", "success", 0),
        ("failure", "success", 1),
        ("success", "skipped", 1),
        ("success", "cancelled", 1),
    ],
)
def test_release_aggregate_requires_registration_and_build(register, build, expected):
    workflow = (ROOT / ".github/workflows/release-controller-ci.yml").read_text()
    command = next(
        line.strip()[len("run: python -c ") :]
        for line in workflow.splitlines()
        if "run: python -c " in line
    )
    result = subprocess.run(
        [sys.executable, "-c", ast.literal_eval(command)],
        env={
            **os.environ,
            "PACKAGE_RESULT": "success",
            "RUFF_RESULT": "success",
            "REGISTER_RESULT": register,
            "BUILD_RESULT": build,
            "RELEASE_MODE": "true",
        },
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == expected
