"""Synthetic identities and exact source Git objects for GPID wire tests."""

import base64
import hashlib
import json
from pathlib import Path

from phase5_transport import Phase5Transport
from profile_bridge_fixture import configure
from profile_git import GitData
from test_profile_adapter_reads import REQUIRED
from test_profile_evidence_edits import fixture_files

from cg_release.models import Policy, canonical_bytes, load_record


def snapshot_bytes(tag, sha, run_id, kind="release"):
    files = dict.fromkeys(REQUIRED, b"exact static snapshot")
    record = dict(
        schemaVersion=2,
        kind=kind,
        tag=tag,
        sha=sha,
        runId=run_id,
        runAttempt=1,
        files={p: hashlib.sha256(b).hexdigest() for p, b in sorted(files.items())},
    )
    record["snapshotDigest"] = hashlib.sha256(
        json.dumps(record, separators=(",", ":")).encode()
    ).hexdigest()
    return json.dumps(
        {
            "record": record,
            "files": {p: base64.b64encode(b).decode() for p, b in files.items()},
        }
    ).encode()


class ProfileFixture(Phase5Transport):
    def __init__(self, cwd, *, baseline=True):
        super().__init__(cwd)
        self.git = GitData()
        self.builds, self.build_jobs, self.archives = {}, {}, {}
        self.docs_runs, self.docs_jobs, self.deployments = {}, {}, []
        self.deleted_doc_runs = set()
        self.downloads = []
        self.bridge_sha, self.bridge_oid = "e" * 40, "f" * 40
        raw = self.policy.model_dump(mode="json")
        raw["gpid_profile"] = "v1"
        raw["bootstrap"] = [
            dict(
                release_id=70,
                tag="v1.0.0",
                commit=self.bridge_sha,
                line="current",
                version="1.0.0",
                legacy_version=None,
                projections={},
            )
        ]
        docs = snapshot_bytes("v1.0.0", self.bridge_sha, 90)
        raw["profile"] = dict(
            bridge=dict(
                tag="v1.0.0",
                release_id=70,
                revision=self.bridge_sha,
                workflow_path=".github/workflows/release-controller-bridge.yml",
                windows_run_id=91,
                unix_run_id=92,
                app_id=15368,
            ),
            payload_directory="releases",
            latest_payload="releases/latest.json",
            attestation_directory=".github/shared/skill-management/release-attestations",
            docs_workflow=".github/workflows/release-controller-docs.yml",
            docs_baselines=[
                dict(
                    tag="v1.0.0",
                    sha=self.bridge_sha,
                    release_id=70,
                    asset_id=80,
                    sha256=hashlib.sha256(docs).hexdigest(),
                    size=len(docs),
                    run_id=90,
                    run_attempt=1,
                )
            ]
            if baseline
            else [],
        )
        raw["required_checks"].insert(
            0,
            dict(
                name="gpid-native-profile",
                app_id=15368,
                workflow_path=".github/workflows/release-controller-build.yml",
                stage="release",
            ),
        )
        raw["build"]["argv"] = ["python", "scripts/release_profile_build.py"]
        raw["build"]["lock_paths"] = [
            "packages/cg-release/uv.lock",
            "packages/cg-release/pyproject.toml",
        ]
        raw["build"]["artifacts"] = [
            dict(
                name="release-docs.json",
                path="release-output/release-docs.json",
                media_type="application/json",
                required=True,
                max_bytes=67108864,
            ),
            dict(
                name="native-environment.json",
                path="release-output/native-environment.json",
                media_type="application/json",
                required=True,
                max_bytes=65536,
            ),
        ]
        raw["build"]["max_artifacts"] = 2
        raw["build"]["max_total_bytes"] = 67174400
        configure(self, raw)
        self.policy = load_record(Policy, canonical_bytes(raw))
        self.tags["v1.0.0"] = {"oid": self.bridge_oid, "commit": self.bridge_sha}
        self.tag_nodes.insert(
            0,
            {"name": "v1.0.0", "target": {"oid": self.bridge_oid, "__typename": "Tag"}},
        )
        self.release_rows.insert(
            0,
            dict(
                id=70,
                tag_name="v1.0.0",
                draft=False,
                prerelease=False,
                published_at="2026-09-10T00:00:00Z",
                target_commitish=self.bridge_sha,
                body="old",
            ),
        )
        self.asset_rows[80] = dict(
            id=80,
            release_id=70,
            name="release-docs.json",
            size=len(docs),
            bytes=docs,
            state="uploaded",
            content_type="application/json",
        )
        self.latest = 70
        self.roles[999] = "maintain"
        self.branches["dev"] = "c" * 40
        self.payload = b'{"tag":"v1.0.0"}\n'
        self.files = {
            **fixture_files(),
            "compound-gpid.md": b"# Fixture GPID\n",
            ".github/shared/module-registry.json": b"{}\n",
            "releases/v1.0.0.json": self.payload,
            "releases/latest.json": self.payload,
            "package.json": b'{"version":"1.0.0"}\n',
            "CHANGELOG.md": b"# Changes\n\n<!-- release -->\n",
            "uv.lock": b"locked\n",
            "packages/cg-release/uv.lock": (
                Path(__file__).parents[1] / "uv.lock"
            ).read_bytes(),
            "packages/cg-release/pyproject.toml": (
                Path(__file__).parents[1] / "pyproject.toml"
            ).read_bytes(),
        }
        for sha in self.branches.values():
            self.install_profile_source(sha)

    def install_profile_source(self, sha, files=None):
        files = {
            **(files or self.files),
            ".release-controller.json": canonical_bytes(self.policy),
        }
        root = self.git.tree(files)
        self.objects.update(self.git.blobs)
        self.trees.update(self.git.trees)
        self._commit(sha, None, {})
        self.commits[sha]["commit"]["tree"]["sha"] = root
