"""Unprivileged exact-source GPID builder; no control or publishing credentials.

Example: python scripts/release_profile_build.py (only inside a registered source job).
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def main(argv=None):
    """Run source-only checks and export one immutable snapshot plus native receipt.

    Args: argv accepts --dev or read-only --check-environment; default is sys.argv.
    Returns: 0 on success. Raises SystemExit for invalid job/credential input,
    ControllerError for an invalid interpreter/lock, or CalledProcessError and
    TimeoutExpired for a failed child. Writes only the
    source job's generated docs and new release-output directory; never remote data.
    Example: main(['--check-environment']) probes the actual locked native Python.
    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", action="store_true")
    parser.add_argument("--check-environment", action="store_true")
    args = parser.parse_args(argv)
    root = Path.cwd()
    native = None
    if not args.dev or args.check_environment:
        sys.path.insert(0, str(root / "packages/cg-release/src"))
        from cg_release.profile_native import environment

        native = environment(root)
    if args.check_environment:
        sys.stdout.write(json.dumps(native, sort_keys=True) + "\n")
        return 0
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    if os.environ.get("CG_RELEASE_SOURCE_JOB") != "true" or sha != os.environ.get(
        "CG_RELEASE_SOURCE_SHA"
    ):
        raise SystemExit("Exact registered source-only job required")
    if any(
        os.environ.get(name)
        for name in ("GH_TOKEN", "RELEASE_CONTROL_TOKEN", "RELEASE_PUBLISH_TOKEN")
    ):
        raise SystemExit("Privileged credentials must not enter source builds")
    manifest = (
        None if args.dev else json.loads((root / ".release-manifest.json").read_text())
    )
    os.environ["CG_RELEASE_REPOSITORY"] = os.environ["GITHUB_REPOSITORY"]
    commands = (
        []
        if args.dev
        else [
            [
                sys.executable,
                "scripts/cg_pr_preflight.py",
                "--phase",
                "committed",
                "--full-gate",
                "--run-native-target",
                "--gate-owner",
                "gpid-native-profile",
            ],
            [sys.executable, "scripts/cg_generate_targets.py", "--all", "--dry-run"],
        ]
    )
    commands += [
        ["node", "scripts/rebuild-docs.js", "--all"],
        ["node", "scripts/check-docs-site.js"],
    ]
    for command in commands:
        subprocess.run(command, cwd=root, check=True, timeout=1200)
    output = root / "release-output"
    output.mkdir(exist_ok=False)
    if native is not None:
        native.update(
            schema_version=1,
            source_sha=sha,
            run_id=int(os.environ["GITHUB_RUN_ID"]),
            run_attempt=int(os.environ["GITHUB_RUN_ATTEMPT"]),
        )
        (output / "native-environment.json").write_text(
            json.dumps(native, sort_keys=True) + "\n", encoding="utf-8"
        )
    snapshot = output / "snapshot"
    config = {
        "root": str(root),
        "out": str(snapshot),
        "kind": "dev" if args.dev else "release",
        "tag": None if args.dev else manifest["tag"],
        "sha": sha,
        "runId": int(os.environ["GITHUB_RUN_ID"]),
        "runAttempt": int(os.environ["GITHUB_RUN_ATTEMPT"]),
    }
    config_path = output / "snapshot-input.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    subprocess.run(
        ["node", "scripts/assemble-docs-site.js", "--snapshot", str(config_path)],
        check=True,
        timeout=120,
    )
    subprocess.run(
        [
            "node",
            "scripts/docs-snapshots.js",
            "export",
            str(snapshot),
            str(output / ("dev-docs.json" if args.dev else "release-docs.json")),
        ],
        check=True,
        timeout=120,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
