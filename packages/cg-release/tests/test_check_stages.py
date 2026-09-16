"""Check stages are explicit trusted policy, not inferred from a workflow filename."""

import json
from pathlib import Path

import pytest

from cg_release.events import ControllerError
from cg_release.models import Policy, canonical_bytes, load_record
from cg_release.policy import validate_policy


@pytest.mark.parametrize("stage", [None, "preparation", "unknown"])
def test_implicit_or_unknown_check_stage_is_rejected(stage):
    raw = json.loads((Path(__file__).parent / "fixtures/policy.json").read_bytes())
    if stage is None:
        del raw["required_checks"][0]["stage"]
    else:
        raw["required_checks"][0]["stage"] = stage
    with pytest.raises(ValueError):
        load_record(Policy, canonical_bytes(raw))


def test_dispatch_only_policy_cannot_remove_all_preparation_checks():
    raw = json.loads((Path(__file__).parent / "fixtures/policy.json").read_bytes())
    raw["required_checks"][0]["stage"] = "release"
    policy = load_record(Policy, canonical_bytes(raw))
    with pytest.raises(ControllerError) as caught:
        validate_policy(policy, repository_id=123, host="github.com")
    assert caught.value.code == "E_POLICY"
