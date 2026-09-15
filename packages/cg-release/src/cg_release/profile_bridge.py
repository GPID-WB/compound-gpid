"""Exact published bridge and real clean-consumer qualification evidence."""

import hashlib
import io
import re
import zipfile

from cg_release.artifact_download import download_archive
from cg_release.events import ControllerError
from cg_release.github_checks import inventory
from cg_release.journal import digest
from cg_release.jsonio import decode_json
from cg_release.models import canonical_bytes
from cg_release.profile_models import BridgeRelease, BridgeSpec
from cg_release.publication_remote import GitHubPublicationRemote
from cg_release.source_blobs import commit_tree, read_blobs
from cg_release.versions import parse_version

WORKFLOW = ".github/workflows/release-controller-bridge.yml"
MANAGED = (".opencode/AGENTS.md", ".opencode/opencode.json")
LINKS = (".github/prompts", ".opencode/commands")
STEPS = ("Qualify actual delivered bridge", "Upload actual bridge qualification")


def bridge_spec(policy, slug: str) -> BridgeSpec:
    """Return strict qualification inputs from reviewed policy and verified slug.

    No I/O. Raises validation errors for incomplete identities. Example:
    bridge_spec(policy, api.slug) retains prior, bridge and successor releases.
    """
    item = policy.profile.bridge
    return BridgeSpec(
        repository_id=policy.repository_id,
        repository_slug=slug,
        previous=item.previous,
        successor=item.successor,
        bridge=BridgeRelease(
            **{k: getattr(item, k) for k in BridgeRelease.model_fields}
        ),
    )


def verify_releases(api, spec: BridgeSpec) -> dict:
    """Read the repository and three published distributions; return tree proofs.

    Raises ControllerError on changed Release/tag/tree/grammar. GET-only; no source
    code runs. Example: verify_releases(api, spec) before a private client clone.
    """
    try:
        repo = api.get("")
        if (
            repo["id"] != spec.repository_id
            or repo["full_name"] != spec.repository_slug
        ):
            raise ValueError
        if api.slug != spec.repository_slug:
            raise ValueError
        for item in (spec.previous, spec.bridge):
            if re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+(?:\.[0-9]+)?", item.tag) is None:
                raise ValueError
        if parse_version(spec.successor.tag.removeprefix("v")).prerelease is None:
            raise ValueError
        if (
            len({item.tag for item in (spec.previous, spec.bridge, spec.successor)})
            != 3
        ):
            raise ValueError
        proofs = {}
        for name in ("previous", "bridge", "successor"):
            item = getattr(spec, name)
            release = api.get(f"releases/{item.release_id}")
            tag = GitHubPublicationRemote(api).observe_tag(item.tag)
            if (
                release["id"] != item.release_id
                or release["tag_name"] != item.tag
                or release["draft"] is not False
                or not release["published_at"]
                or tag is None
                or tag["commit"] != item.revision
                or tag["oid"] != item.tag_object
                or commit_tree(api, item.revision) != item.tree
            ):
                raise ValueError
            tree = api.tree(item.tree, recursive=True)
            rows = sorted(
                (r["path"], r["mode"], r["sha"])
                for r in tree["tree"]
                if r["type"] != "tree"
            )
            if not rows or any(mode not in {"100644", "100755"} for _, mode, _ in rows):
                raise ValueError
            blobs = read_blobs(api, item.tree, list(MANAGED))
            proofs[name] = {
                "release": item.model_dump(mode="json"),
                "tracked_digest": digest(rows),
                "managed": {
                    p: hashlib.sha256(blobs[p].content).hexdigest() for p in MANAGED
                },
                "links": list(LINKS),
                "pin": item.tag,
                "copilot_refreshed": True,
            }
        return proofs
    except (KeyError, ValueError, TypeError, AttributeError):
        raise ControllerError(
            "E_BRIDGE_REQUIRED", "Published bridge distribution identities are invalid."
        ) from None


def verify_bridge(api, policy) -> None:
    """Require exact real qualifier outputs, run, job, steps and artifact digests.

    Args: production GET reader and validated reviewed GPID policy. Returns None
    only after both native host results match all remote distributions. Raises
    ControllerError on expired, synthetic, malformed or substituted evidence.
    Example: verify_bridge(api, policy) before admission. No remote/local writes.
    """
    bridge = policy.profile.bridge
    spec = bridge_spec(policy, api.slug)
    proofs = verify_releases(api, spec)
    try:
        for platform in ("windows", "unix"):
            run_id = getattr(bridge, platform + "_run_id")
            job_id = getattr(bridge, platform + "_job_id")
            artifact_id = getattr(bridge, platform + "_artifact_id")
            expected_digest = getattr(bridge, platform + "_artifact_digest")
            run = api.get(f"actions/runs/{run_id}")
            suite = api.get(f"check-suites/{run['check_suite_id']}")
            jobs = inventory(api, f"actions/runs/{run_id}/attempts/1/jobs", "jobs")
            expected = "bridge-clean-client-" + platform
            cells = [j for j in jobs if j.get("name") == expected]
            if (
                run["id"] != run_id
                or run["head_sha"] != bridge.revision
                or run["path"] != WORKFLOW
                or type(run["run_attempt"]) is not int
                or run["run_attempt"] != 1
                or run["repository"]["id"] != policy.repository_id
                or run["event"] != "workflow_dispatch"
                or run["status"] != "completed"
                or run["conclusion"] != "success"
                or suite["app"]["id"] != bridge.app_id
                or suite["head_sha"] != bridge.revision
                or len(cells) != 1
            ):
                raise ValueError
            job = cells[0]
            if (
                any(type(job[k]) is not int for k in ("id", "run_id", "run_attempt"))
                or job["id"] != job_id
                or job["run_id"] != run_id
                or job["run_attempt"] != 1
                or job["status"] != "completed"
                or job["conclusion"] != "success"
            ):
                raise ValueError
            for name in STEPS:
                steps = [s for s in job["steps"] if s.get("name") == name]
                if (
                    len(steps) != 1
                    or steps[0]["status"] != "completed"
                    or steps[0]["conclusion"] != "success"
                ):
                    raise ValueError
            rows = inventory(api, f"actions/runs/{run_id}/artifacts", "artifacts")
            matches = [r for r in rows if r.get("name") == expected]
            if len(matches) != 1:
                raise ValueError
            metadata = matches[0]
            if (
                type(metadata["id"]) is not int
                or type(metadata["size_in_bytes"]) is not int
                or type(metadata["workflow_run"]["id"]) is not int
                or metadata["id"] != artifact_id
                or metadata["workflow_run"]["id"] != run_id
                or metadata["workflow_run"]["head_sha"] != bridge.revision
                or metadata["digest"] != "sha256:" + expected_digest
                or not 1 <= metadata["size_in_bytes"] <= 131072
            ):
                raise ValueError
            raw = download_archive(api, metadata)
            if hashlib.sha256(raw).hexdigest() != expected_digest:
                raise ValueError
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                entries = archive.infolist()
                if (
                    len(entries) != 1
                    or entries[0].filename != "qualification.json"
                    or entries[0].file_size > 65536
                    or entries[0].is_dir()
                ):
                    raise ValueError
                result = decode_json(archive.read(entries[0]).decode("utf-8"))
            expected_result = {
                "schema_version": 1,
                "kind": "actual-bridge-clean-consumer-v1",
                "platform": platform,
                "spec_digest": digest(spec),
                "repository_id": policy.repository_id,
                "repository_slug": api.slug,
                "workflow_revision": bridge.revision,
                "run_id": run_id,
                "run_attempt": 1,
                "stages": proofs,
                "new_pin_rejected_before_bridge": True,
            }
            if canonical_bytes(result) != canonical_bytes(expected_result):
                raise ValueError
    except (
        KeyError,
        ValueError,
        TypeError,
        AttributeError,
        OSError,
        zipfile.BadZipFile,
    ):
        raise ControllerError(
            "E_BRIDGE_REQUIRED", "Exact actual-bridge qualifier evidence is required."
        ) from None
