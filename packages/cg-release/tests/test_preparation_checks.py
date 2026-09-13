"""Required PR checks use real check-suite/run producer fields, not names alone."""

from types import SimpleNamespace

import pytest

from cg_release.events import ControllerError
from cg_release.github_checks import required_pr_checks


@pytest.mark.parametrize("bad", [None, "app", "workflow", "sha", "skipped", "missing"])
def test_required_check_has_exact_run_producer(bad):
    sha = "a" * 40
    check = {
        "id": 11,
        "name": "gate",
        "head_sha": sha,
        "status": "completed",
        "conclusion": "success",
        "app": {"id": 42},
        "check_suite": {"id": 15},
    }
    run = {
        "id": 21,
        "run_attempt": 1,
        "check_suite_id": 15,
        "head_sha": sha,
        "path": ".github/workflows/ci.yml",
        "status": "completed",
        "conclusion": "success",
    }
    if bad == "app":
        check["app"]["id"] = 99
    if bad == "workflow":
        run["path"] = ".github/workflows/untrusted.yml"
    if bad == "sha":
        run["head_sha"] = "b" * 40
    if bad == "skipped":
        check["conclusion"] = "skipped"
    api = SimpleNamespace(
        slug="owner/repo",
        _request=lambda path, page: (
            {
                "check_runs": [] if bad == "missing" else [check],
                "total_count": 0 if bad == "missing" else 1,
            }
            if "check-runs" in path
            else {"workflow_runs": [run], "total_count": 1}
        ),
    )
    policy = SimpleNamespace(
        required_checks=[
            SimpleNamespace(
                stage="preparation-and-release",
                name="gate",
                app_id=42,
                workflow_path=run["path"]
                if bad != "workflow"
                else ".github/workflows/ci.yml",
            )
        ]
    )
    if bad:
        with pytest.raises(ControllerError):
            required_pr_checks(api, policy, sha)
    else:
        assert required_pr_checks(api, policy, sha)[0]["run_id"] == 21
