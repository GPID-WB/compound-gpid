"""Trusted data-only attestation projection, sealed before the evidence PR exists."""

import hashlib
import json
import re

from cg_release.events import ControllerError
from cg_release.github import decode_json
from cg_release.metadata import Edit
from cg_release.policy import safe_path
from cg_release.source_blobs import read_blobs

TARGETS = {
    "claude-code": ".claude",
    "codex": ".agents",
    "opencode": ".opencode",
    "kilo": ".kilo",
}
DIRECTORY = "shared/skill-management/release-attestations/"


def attestation_edits(
    api, tree: str, path: str, raw: bytes
) -> tuple[dict, tuple[Edit, ...]]:
    """Generate nine edits, e.g. attestation_edits(api, tree, path, raw).

    Args: immutable base tree; canonical attestation path; already validated bytes.
    Returns: Verified base blobs and canonical/native/ownership edits. The installed
    generator only appends this shared JSON family and uses the native generator's
    exact manifest format. All unrelated manifest entries and historical bytes stay
    unchanged. No repository code, file writes or remote mutations occur.
    Raises: ControllerError for unsupported mapping, drift or immutable conflicts.
    """
    if not path.startswith(".github/" + DIRECTORY) or not re.fullmatch(
        r"v[A-Za-z0-9.+-]+\.json", path.rsplit("/", 1)[-1]
    ):
        raise ControllerError("E_HOOK", "Invalid canonical attestation path.")
    mapping_path = ".github/shared/target-mapping.json"
    mapping = decode_json(
        read_blobs(api, tree, [mapping_path])[mapping_path].content.decode()
    )
    try:
        targets = {
            t["id"]: t
            for t in mapping["targets"]
            if t.get("generatedTreePath") is not None
        }
        if mapping["schemaVersion"] != 1 or set(targets) != set(TARGETS):
            raise ValueError
        for name, root in TARGETS.items():
            if (
                targets[name]["generatedTreePath"] != root
                or targets[name]["outputPaths"]["shared"] != root + "/shared"
            ):
                raise ValueError
        outputs = {path: raw}
        manifests = [
            root + "/.compound-gpid-generated.json" for root in TARGETS.values()
        ]
        manifest_blobs = read_blobs(api, tree, manifests)
        history = {}
        for name, root in TARGETS.items():
            manifest_path = root + "/.compound-gpid-generated.json"
            value = decode_json(manifest_blobs[manifest_path].content.decode())
            if (
                set(value) != {"schemaVersion", "target", "policyVersion", "files"}
                or type(value["schemaVersion"]) is not int
                or value["schemaVersion"] != 1
                or type(value["policyVersion"]) is not int
                or value["policyVersion"] != 1
                or value["target"] != name
                or not isinstance(value["files"], list)
            ):
                raise ValueError
            destination = root + path[len(".github") :]
            addition = {
                "path": destination,
                "source": path,
                "kind": "shared",
                "sha256": hashlib.sha256(raw).hexdigest(),
                "executable": False,
            }
            prior, seen = [], set()
            for item in value["files"]:
                if (
                    set(item) != {"path", "source", "kind", "sha256", "executable"}
                    or not item["path"].startswith(root + "/")
                    or item["path"].lower() in seen
                    or type(item["executable"]) is not bool
                    or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"])
                ):
                    raise ValueError
                safe_path(item["path"])
                seen.add(item["path"].lower())
                if item["path"] == destination:
                    if item != addition:
                        raise ValueError
                    continue
                prior.append(item)
                if item["path"].startswith(root + "/" + DIRECTORY):
                    if (
                        item["source"] != ".github" + item["path"][len(root) :]
                        or item["kind"] != "shared"
                        or item["executable"]
                    ):
                        raise ValueError
                    history[item["path"]] = (item["source"], item["sha256"])
            value["files"] = sorted([*prior, addition], key=lambda row: row["path"])
            outputs[manifest_path] = (
                json.dumps(value, indent=2, ensure_ascii=False) + "\n"
            ).encode()
            outputs[destination] = raw
        historical = read_blobs(
            api, tree, sorted(set(history) | {v[0] for v in history.values()})
        )
        for target, (source, expected) in history.items():
            if (
                historical[target].content != historical[source].content
                or hashlib.sha256(historical[target].content).hexdigest() != expected
            ):
                raise ValueError
        blobs = read_blobs(
            api, tree, sorted(outputs), optional=set(outputs) - set(manifests)
        )
        for name, content in outputs.items():
            if (
                name not in manifests
                and name in blobs
                and blobs[name].content != content
            ):
                raise ValueError
        edits = tuple(
            Edit(
                name,
                hashlib.sha256(blobs[name].content).hexdigest()
                if name in blobs
                else None,
                hashlib.sha256(content).hexdigest(),
                content,
            )
            for name, content in sorted(outputs.items())
        )
        return blobs, edits
    except (KeyError, ValueError, TypeError, AttributeError):
        raise ControllerError(
            "E_HOOK", "Attestation mapping, ownership or historical bytes conflict."
        ) from None
