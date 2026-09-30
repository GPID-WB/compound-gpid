"""Materialize explicitly disabled GPID workflow installations from reviewed templates.

Example: python scripts/release_profile_install.py --check.
This does not configure GitHub, resolve authority, install secrets or enable a writer.
"""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def outputs(root=ROOT):
    """Read reviewed templates under root and return path-to-text disabled outputs.

    Args: root is the canonical repository Path. Returns a dict for four workflow
    files and .release-controller.json. Raises file/JSON errors on incomplete input.
    Example: outputs(ROOT)['.release-controller.json']. No files or remote state
    change. Repository/App/bridge/pin identities remain explicitly unresolved.
    """
    templates = root / "packages/cg-release/templates"
    result = {}
    for template, name in (
        ("controller", "release-controller"),
        ("build", "release-controller-build"),
        ("publish", "release-controller-publish"),
        ("gpid-docs", "release-controller-docs"),
    ):
        content = (templates / (template + ".yml")).read_text(encoding="utf-8")
        if template == "build":
            content += "\n  gpid-native-profile:\n    name: gpid-native-profile\n    needs: build\n    runs-on: ubuntu-24.04\n    steps:\n      - run: test '${{ needs.build.result }}' = success\n"
            content = content.replace(
                "      - name: Execute policy argv in the source-only job",
                "      - uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020\n        with:\n          node-version: '22'\n      - name: Execute policy argv in the source-only job",
            )
            content = (
                content.replace(
                    "      - name: Execute policy argv in the source-only job",
                    "      - name: Provision locked GPID native-test environment\n"
                    "        shell: bash\n"
                    "        run: |\n"
                    "          set -euo pipefail\n"
                    '          UV_PROJECT_ENVIRONMENT="$RUNNER_TEMP/gpid-native" uv sync --project source/packages/cg-release --python 3.12 --locked --no-default-groups --group dev --group gpid-native --no-install-project\n'
                    '          echo "CG_RELEASE_NATIVE_PYTHON=$RUNNER_TEMP/gpid-native/bin/python" >> "$GITHUB_ENV"\n'
                    "      - name: Execute policy argv in the source-only job",
                )
                .replace(
                    'export PATH="$GITHUB_WORKSPACE/_controller/packages/cg-release/.venv/bin:$PATH"',
                    'export PATH="$(dirname "$CG_RELEASE_NATIVE_PYTHON"):$PATH"',
                )
                .replace(
                    "          python -I -m cg_release.build_worker build",
                    "          _controller/packages/cg-release/.venv/bin/python -I -m cg_release.build_worker build",
                )
            )
        result[f".github/workflows/{name}.yml"] = content
    policy = json.loads((templates / "policy.example.json").read_text())
    policy.update(
        repository_id=None,
        controller={"revision": None, "wheel_digest": None},
        journal_root=None,
        apps={"control": None, "control_slug": None, "publishing": None},
        gpid_profile="v1",
    )
    policy["metadata"] = [
        {"kind": "json", "path": ".release-version.json", "pointer": "/version"}
    ]
    policy["changelog"] = {
        "path": "CHANGELOG.md",
        "marker": "<!-- release-controller -->",
    }
    policy["build"] = {
        "argv": ["python", "scripts/release_profile_build.py"],
        "cwd": ".",
        "lock_paths": [
            "packages/cg-release/uv.lock",
            "packages/cg-release/pyproject.toml",
            "package-lock.json",
        ],
        "artifacts": [
            {
                "name": "release-docs.json",
                "path": "release-output/release-docs.json",
                "media_type": "application/json",
                "required": True,
                "max_bytes": 67108864,
            },
            {
                "name": "native-environment.json",
                "path": "release-output/native-environment.json",
                "media_type": "application/json",
                "required": True,
                "max_bytes": 65536,
            },
        ],
        "max_artifacts": 2,
        "max_total_bytes": 67174400,
    }
    policy["required_checks"] = [
        {
            "name": "gpid-native-profile",
            "app_id": None,
            "workflow_path": ".github/workflows/release-controller-build.yml",
            "stage": "release",
        },
        {
            "name": "release-controller-ci",
            "app_id": None,
            "workflow_path": ".github/workflows/release-controller-ci.yml",
            "stage": "preparation-and-release",
        },
    ]
    policy["profile"] = {
        "bridge": None,
        "payload_directory": "releases",
        "latest_payload": "releases/latest.json",
        "attestation_directory": ".github/shared/skill-management/release-attestations",
        "docs_workflow": ".github/workflows/release-controller-docs.yml",
        "composition_retries": 3,
        "docs_baselines": [],
    }
    result[".release-controller.json"] = json.dumps(policy, indent=2) + "\n"
    return result


def main(argv=None):
    """Check or write disabled source installations, or capture old reader fixtures.

    Args: argv accepts --check or --capture-readers EXACT_LOCAL_REVISION; None uses
    process arguments. Returns 0 on success. Raises SystemExit for drift/invalid
    options and I/O/subprocess errors for unavailable files or Git objects.
    Example: main(['--check']) is read-only. Default writes only outputs() paths;
    it must not target a reviewed active installation. Capture creates a new fixture
    directory with original Git bytes and source.json hashes; it never overwrites
    frozen evidence. No GitHub settings, secrets, publication or activation occurs.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--capture-readers", metavar="EXACT_LOCAL_REVISION")
    args = parser.parse_args(argv)
    if args.capture_readers:
        if args.check or not re.fullmatch(r"[0-9a-f]{40}", args.capture_readers):
            raise SystemExit("Reader fixture capture requires one exact local revision")
        directory = ROOT / "scripts/tests/fixtures/release-bridge"
        directory.mkdir(exist_ok=False)
        metadata = {
            "revision": args.capture_readers,
            "kind": "offline-fixture-only",
            "sha256": {},
        }
        for extension in ("ps1", "sh"):
            name = "update." + extension
            raw = subprocess.run(
                ["git", "show", args.capture_readers + ":scripts/" + name],
                cwd=ROOT,
                capture_output=True,
                check=True,
                timeout=30,
            ).stdout
            (directory / (name + ".fixture")).write_bytes(raw)
            metadata["sha256"][name] = hashlib.sha256(raw).hexdigest()
        (directory / "source.json").write_text(
            json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
        )
        return 0
    for name, content in outputs().items():
        path = ROOT / name
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Disabled installation differs: {name}")
        else:
            path.write_text(content, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
