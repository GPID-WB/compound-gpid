#!/usr/bin/env python3
"""cg-autopilot — deterministic evidence and control-state helper.

Implements the read-only ``inspect`` operation: strict invocation parsing,
plan validation, batch expansion, prior-run reporting, and (Phase 5) the
installed helper identity. The consumer root is always passed explicitly via
``--root``: the helper resolves its own code wrapper-relative from the
installation directory and never changes the working directory or selects
consumer tests from the installed source test inventory. Remaining helper
operations are implemented in later phases and refuse with a typed error
instead of a fallback. Machine stdout carries only the JSON inspection
result; diagnostics go to stderr with a bounded exit code.

Usage:
    python scripts/cg_autopilot.py inspect --root . --plan <path> \\
        --batches <segments> --base <branch> [--ci-timeout 30m]
    python scripts/cg_autopilot.py inspect --root . --resume <active-state path>
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Optional, Sequence

import secure_fs
from autopilot.arguments import Invocation, expand_single_phase_commands, parse_invocation
from autopilot.contracts import AutopilotError, sha256_hex
from autopilot.install import validate_installed_layout
from autopilot.plan import read_plan, validate_batches
from autopilot.recovery import reconcile
from autopilot.records import validate_cursor_record
from autopilot.state import resolve_coordination_root

CONTRACT_RELATIVE = ".github/shared/autopilot-stage.contract.md"
INSTALLED_COMMAND_RELATIVE = ".kilo/commands/cg-autopilot.md"
ACTIVE_STATE_RELATIVE = ".cg-docs/active-state/current.json"
CURSOR_READ_LIMIT = 32768
GIT_PROBE_TIMEOUT_SECONDS = 30
OPERATIONS = (
    "inspect",
    "prepare",
    "begin-stage",
    "begin-effect",
    "record-result",
    "validate-stage",
    "checkpoint",
    "reconcile",
    "observe-ci",
    "extend-ci-deadline",
)


def _bounded_hash(root: Path, relative_path: str) -> Optional[str]:
    try:
        raw = secure_fs.secure_read_bytes(
            root, PurePosixPath(relative_path), max_bytes=262144, reject_hardlinks=True
        )
    except (FileNotFoundError, secure_fs.SecureMutationError, OSError):
        return None
    return sha256_hex(raw)


def _git_probe(root: Path, args: Sequence[str]) -> Optional[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=GIT_PROBE_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _read_cursor(root: Path, resume_path: str) -> dict:
    try:
        normalized = secure_fs.normalize_relative_path(PurePosixPath(resume_path))
        raw = secure_fs.secure_read_bytes(
            root,
            PurePosixPath(normalized),
            max_bytes=CURSOR_READ_LIMIT,
            reject_hardlinks=True,
        )
    except (secure_fs.SecureMutationError, OSError, ValueError) as error:
        raise AutopilotError(
            f"resume cursor cannot be read: {error}",
            error_code="autopilot-argument-error",
        ) from error
    return validate_cursor_record(raw)


def run_inspect(root: Path, invocation: Invocation) -> dict:
    """Read-only inspection: eligibility, blockers and a normalized run spec."""
    blockers: list[dict] = []
    run_spec: dict[str, Any] = {}
    if invocation.form == "fresh":
        plan = read_plan(root, invocation.plan)
        union = validate_batches(plan, invocation.segments)
        run_spec = {
            "plan": invocation.plan,
            "plan-title": plan.title,
            "plan-execution-digest": plan.digest,
            "current-phase": plan.current_phase,
            "completed-phases": list(plan.completed_phases),
            "execution-report": plan.execution_report,
            "batches": [segment.display() for segment in invocation.segments],
            "batch-phase-union": list(union),
            "expanded-commands": list(
                expand_single_phase_commands(invocation.segments)
            ),
            "base": invocation.base,
            "ci-timeout-seconds": invocation.ci_timeout_seconds,
        }
    else:
        cursor = _read_cursor(root, invocation.resume_path)
        section = cursor["autopilot"]
        run_spec = {
            "resume-path": invocation.resume_path,
            "run-id": section["run-id"],
            "revision": section["revision"],
            "next-action": section["next-action"],
            "plan-execution-digest": section["plan-execution-digest"],
            "batch-pointer": section["batch-pointer"],
            "stage-pointer": section["stage-pointer"],
        }
    installed_identities = {
        "contract-digest": _bounded_hash(root, CONTRACT_RELATIVE),
        "installed-command-digest": _bounded_hash(root, INSTALLED_COMMAND_RELATIVE),
    }
    installed_helper = validate_installed_layout()
    if installed_helper["problems"]:
        blockers.append(
            {
                "code": "helper-layout-invalid",
                "detail": installed_helper["problems"][0],
            }
        )
    git_state = {
        "branch": _git_probe(root, ["branch", "--show-current"]),
        "head": _git_probe(root, ["rev-parse", "HEAD"]),
    }
    prior_run: Optional[dict] = None
    try:
        coordination = resolve_coordination_root(root)
        prior_run = {
            "coordination-root": str(coordination),
            "reconciliation": reconcile(
                root, coordination, root / ACTIVE_STATE_RELATIVE
            ).status,
        }
    except AutopilotError as error:
        prior_run = {
            "coordination-root": None,
            "reconciliation": None,
            "detail": error.message,
        }
    if installed_identities["contract-digest"] is None:
        blockers.append(
            {"code": "contract-identity-unavailable", "detail": CONTRACT_RELATIVE}
        )
    if invocation.form == "fresh" and invocation.base:
        base_check = _git_probe(root, ["rev-parse", "--verify", invocation.base])
        if base_check is None:
            blockers.append(
                {
                    "code": "base-unresolved",
                    "detail": f"base ref {invocation.base!r} is not resolvable here.",
                }
            )
    return {
        "status": "eligible" if not blockers else "blocked",
        "form": invocation.form,
        "run-spec": run_spec,
        "installed-identities": installed_identities,
        "installed-helper": installed_helper,
        "git": git_state,
        "prior-run": prior_run,
        "blockers": blockers,
    }


def _split_root(argv: Sequence[str]) -> tuple[str, list[str]]:
    remainder: list[str] = []
    root: Optional[str] = None
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--root":
            if index + 1 >= len(argv):
                raise AutopilotError(
                    "missing value for flag --root.",
                    error_code="autopilot-argument-error",
                )
            root = argv[index + 1]
            index += 2
            continue
        remainder.append(token)
        index += 1
    if root is None:
        raise AutopilotError(
            "explicit --root is required: the helper never derives a project "
            "root from its own installation directory.",
            error_code="autopilot-argument-error",
        )
    return root, remainder


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        _print_error(AutopilotError(
            f"an operation is required: one of {', '.join(OPERATIONS)}.",
            error_code="autopilot-argument-error",
        ))
        return 1
    operation, rest = arguments[0], arguments[1:]
    if operation not in OPERATIONS:
        _print_error(AutopilotError(
            f"unknown operation {operation!r}; expected one of {OPERATIONS}.",
            error_code="autopilot-argument-error",
        ))
        return 1
    if operation != "inspect":
        _print_error(AutopilotError(
            f"operation-not-implemented: {operation} arrives in a later phase; "
            "no fallback behavior is performed.",
            error_code="autopilot-state-error",
        ))
        return 1
    try:
        root_text, rest = _split_root(rest)
        root = Path(root_text).resolve()
        if not root.is_dir():
            raise AutopilotError(
                f"root {root_text!r} is not an existing directory.",
                error_code="autopilot-argument-error",
            )
        invocation = parse_invocation(rest)
        report = run_inspect(root, invocation)
    except AutopilotError as error:
        _print_error(error)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def _print_error(error: AutopilotError) -> None:
    print(
        f"cg-autopilot: {error.error_code}: {error.message}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    raise SystemExit(main())
