"""Publication recovery preserves objects, lineage, owner authority and hook state."""

from copy import deepcopy
from types import SimpleNamespace

import pytest
from test_publisher import invoke

from cg_release.events import ControllerError
from cg_release.recovery import (
    check_lineage,
    finish_hooks,
    owner_available,
    verify_restore,
)


@pytest.mark.parametrize(
    "tagged,tip,relation,ok",
    [
        (False, "a" * 40, None, True),
        (False, "b" * 40, "ahead", False),
        (True, "b" * 40, "ahead", True),
        (True, "b" * 40, "diverged", False),
        (True, "b" * 40, "behind", False),
        (True, None, None, False),
    ],
)
def test_checkpoint_dependent_branch_rule(tagged, tip, relation, ok):
    api = SimpleNamespace(
        branch=lambda name: {"commit": {"sha": tip}},
        get=lambda endpoint: {
            "status": relation,
            "merge_base_commit": {"sha": "a" * 40},
            "base_commit": {"sha": "a" * 40},
        },
    )
    if ok:
        check_lineage(api, "feature/rc", "a" * 40, tagged=tagged)
    else:
        with pytest.raises(ControllerError):
            check_lineage(api, "feature/rc", "a" * 40, tagged=tagged)


@pytest.mark.parametrize(
    "status,expiry,effects,expected",
    [
        ("in_progress", 10, True, False),
        ("completed", 200, True, False),
        ("completed", 10, False, False),
        ("completed", 10, True, True),
    ],
)
def test_owner_not_stolen_by_age(status, expiry, effects, expected):
    owner = {"run_id": 41, "credential_expires_at": expiry}
    run = {"id": 41, "status": status, "run_attempt": 1}
    assert owner_available(owner, run, now=100, effects_reconciled=effects) is expected


def test_restore_requires_exact_mirror_prefix(publication):
    journal = publication[0]
    original = deepcopy(journal.events())
    invoke(publication)
    verify_restore(original, journal.events())
    with pytest.raises(ControllerError):
        verify_restore(journal.events(), original)
    changed = deepcopy(original)
    changed[0]["digest"] = "a" * 64
    with pytest.raises(ControllerError):
        verify_restore(changed, journal.events())


def test_published_does_not_complete_with_missing_profile_hooks(publication):
    record = invoke(publication)
    assert (
        finish_hooks(
            publication[0], record, required={"docs", "evidence"}, verified={}
        ).state
        == "published"
    )
    done = finish_hooks(
        publication[0],
        record,
        required={"docs", "evidence"},
        verified={
            "docs": {"verified": True, "release_sha": "a" * 40},
            "evidence": {"verified": True, "release_sha": "a" * 40},
        },
    )
    assert done.state == "complete"


def test_hook_substitution_rejected(publication):
    record = invoke(publication)
    with pytest.raises(ControllerError):
        finish_hooks(
            publication[0],
            record,
            required={"docs"},
            verified={"docs": {"verified": True, "release_sha": "f" * 40}},
        )
