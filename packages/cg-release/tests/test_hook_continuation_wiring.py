"""Keep the finite Phase6 continuation audit connected to production call sites."""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "src/cg_release"


@pytest.mark.parametrize(
    "filename, callee, count",
    [
        ("hook_authority.py", "checkpoint", 1),
        ("profile_docs.py", "checkpoint", 1),
        ("profile_evidence_inputs.py", "checkpoint", 1),
        ("profile_evidence.py", "checkpoint", 2),
        ("recovery.py", "checkpoint", 1),
        ("recovery.py", "finish_hooks", 1),
        ("recovery.py", "release_owner", 1),
        ("build_worker.py", "register_build", 1),
        ("recovery_actions.py", "record_audit", 1),
        ("stranded_recovery.py", "record_audit", 1),
    ],
)
def test_phase6_continuations_supply_per_operation_authority(filename, callee, count):
    tree = ast.parse((ROOT / filename).read_text())
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == callee
    ]
    assert len(calls) == count
    for call in calls:
        guards = [arg.value for arg in call.keywords if arg.arg == "before_write"]
        assert len(guards) == 1 and not isinstance(guards[0], ast.Constant)
