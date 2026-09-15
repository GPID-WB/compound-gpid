"""Disabled bootstrap templates preserve the job and credential boundaries."""

import json
from pathlib import Path

from cg_release.models import Policy, load_record

TEMPLATES = Path(__file__).parents[1] / "templates"


def test_controller_template_is_disabled_pinned_and_default_ref_only():
    raw = (TEMPLATES / "controller.yml").read_text()
    assert "false && github.ref" in raw
    assert "issues:" in raw and "schedule:" in raw and "*/5 * * * *" in raw
    assert "cancel-in-progress: false" in raw
    assert "environment: release-control" in raw
    assert "permission-contents: write" in raw
    assert "fee1f7d63c2ff003460e3d139729b119787bc349" in raw
    assert "persist-credentials: false" in raw
    assert "pull_request_target" not in raw
    assert "publishing" not in raw.lower()


def test_example_policy_is_strict_and_disabled():
    policy = load_record(Policy, (TEMPLATES / "policy.example.json").read_bytes())
    assert policy.enabled is False
    assert policy.apps.control != policy.apps.publishing
    assert len(policy.journal_root) == 40


def test_bootstrap_example_separates_write_bypass_from_immutable_history():
    setup = json.loads((TEMPLATES / "bootstrap.example.json").read_bytes())
    assert setup["enabled"] is False
    assert len(setup["rulesets"]) == 4
    state_write, state_history, tag_create, tag_history = setup["rulesets"]
    assert state_write["bypass_actors"][0]["actor_id"] == 100
    assert not state_history["bypass_actors"] and not tag_history["bypass_actors"]
    assert tag_create["bypass_actors"][0]["actor_id"] == 200
