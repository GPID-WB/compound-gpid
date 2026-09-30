#!/usr/bin/env python3
"""Non-publishing release benchmark; run with the standalone package's locked env."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

from cg_release.process import run_process
from cg_release.timing import STAGES, TimingRecorder
from cg_release.trials import plan_sandbox, read_input, summarize_measurements

MAX_OFFLINE_GIT_CALLS = 3


class OfflineGit:
    """Count calls at a restricted local Git boundary, never a provider transport."""

    def __init__(self) -> None:
        """Create an unused three-call budget, e.g. ``git = OfflineGit()``."""
        self.count = 0

    def run(self, args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        """Run one allowed local command and count the attempted process call.

        Args:
            args: Exact init, worktree-check, or status argv; no remote operations.
            cwd: The temporary fixture directory.
        Returns:
            Successful Git result, e.g. ``git.run(['status', '--porcelain'], cwd=p)``.
        Raises:
            ValueError: An unlisted operation or exhausted offline process budget.
        """
        allowed = {
            ("init", "--quiet"),
            ("rev-parse", "--is-inside-work-tree"),
            ("status", "--porcelain"),
        }
        if tuple(args) not in allowed:
            raise ValueError("Offline benchmark rejects this Git operation")
        if self.count >= MAX_OFFLINE_GIT_CALLS:
            raise ValueError("Offline Git process budget exceeded")
        self.count += 1
        return run_process("git", args, cwd=cwd)


def benchmark_offline() -> dict:
    """Measure an offline fixture repository without invoking a release publisher.

    Returns:
        Environment, stage definitions, observations, and missing live evidence.
    Example:
        ``report = benchmark_offline()`` performs three local Git calls only.
    """
    timing = TimingRecorder(enabled=True)
    git = OfflineGit()
    with tempfile.TemporaryDirectory(prefix="cg-release-benchmark-") as temporary:
        root = Path(temporary)
        with timing.span("preparation"), timing.span("subprocess"):
            git.run(["init", "--quiet"], cwd=root)
        with timing.span("gates"):
            with timing.span("subprocess"):
                result = git.run(["rev-parse", "--is-inside-work-tree"], cwd=root)
            if result.stdout.strip() != "true":
                raise RuntimeError("Offline fixture is not a Git worktree")
            with timing.span("subprocess"):
                result = git.run(["status", "--porcelain"], cwd=root)
            if result.stdout.strip():
                raise RuntimeError("Offline fixture is not clean")
        # Fixed in-memory provider response; no network or submission is simulated
        # as a durable request. Remote timing evidence is explicitly absent.
        provider = {"published_releases": (), "remote_writes": 0}
        for stage in STAGES:
            if stage not in {"preparation", "gates", "subprocess"}:
                timing.remote_interval(stage, started=None, finished=None)
    totals = {}
    for stage in STAGES:
        durations = [
            row["elapsed_seconds"]
            for row in timing.records
            if row["stage"] == stage and row["elapsed_seconds"] is not None
        ]
        totals[stage] = sum(durations) if durations else None
    return {
        "schema_version": 1,
        "mode": "offline",
        "environment": {
            "python": platform.python_version(),
            # platform.platform() can spawn ver/uname outside the offline budget.
            "platform": sys.platform,
            "controller_version": version("cg-release"),
        },
        "stage_definitions": STAGES,
        "stage_totals_seconds": totals,
        "records": timing.records,
        "git_subprocess_count": git.count,
        "gate_count": sum(row["stage"] == "gates" for row in timing.records),
        "remote_writes": provider["remote_writes"],
        "provider": "in-memory empty published history; no transport",
        "legacy_baseline": {"status": "missing", "reason": "No authorized live trial"},
        "live_speedup": None,
        "timing_note": "Nested local spans overlap; do not sum stage totals as wall time.",
    }


def main() -> int:
    """Run only offline measurement; e.g. ``benchmark_release.py --offline``.

    Returns:
        Zero after JSON output; two for expected input or output failures.
        No flag enables remote publication.
    """
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--offline", action="store_true", help="explicit default mode")
    parser.add_argument("--sandbox-config", type=Path, help="offline trial plan only")
    parser.add_argument(
        "--repository-id", type=int, help="explicit planning allowlist ID"
    )
    parser.add_argument(
        "--measurements", type=Path, help="unverified sample JSON summary"
    )
    parser.add_argument("--output", type=Path, help="create a new local evidence file")
    args = parser.parse_args()
    try:
        if args.sandbox_config:
            if args.offline or args.repository_id is None:
                raise ValueError(
                    "Sandbox planning needs an explicit ID and no --offline"
                )
            report = plan_sandbox(
                read_input(args.sandbox_config), repository_id=args.repository_id
            )
            if args.measurements:
                report["measurements"] = summarize_measurements(
                    read_input(args.measurements), repository_id=args.repository_id
                )
        else:
            if args.repository_id is not None or args.measurements:
                raise ValueError("Explicit sandbox configuration is required")
            report = benchmark_offline()
    except (ValueError, OSError):
        # Never echo untrusted paths, JSON values or validation exception contents.
        sys.stdout.write(
            json.dumps(
                {
                    "code": "E_BENCHMARK_INPUT",
                    "message": "Invalid local trial input; see --help and the release-controller guide.",
                }
            )
            + "\n"
        )
        return 2
    try:
        output = json.dumps(report, sort_keys=True, indent=2, allow_nan=False)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(output + "\n")
    except (ValueError, OSError):
        sys.stdout.write(
            json.dumps(
                {
                    "code": "E_BENCHMARK_OUTPUT",
                    "message": "Cannot serialize or write report. Select a new "
                    "writable output path; if it persists, inspect local measurements.",
                }
            )
            + "\n"
        )
        return 2
    if not args.output:
        sys.stdout.write(output + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
