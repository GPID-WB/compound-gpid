"""Evidence-backed help service and CLI-owned, single-use file transport.

query_service checks installed-clone freshness and project proof on every call.
answer renders validated evidence only. Selection is a single-use request-bound
in-memory boundary, also persisted by the authenticated local transport.

CLI exit categories: 0 success, 2 invalid transport/input, 3 invalid evidence,
4 filesystem/I/O failure. Each operation emits one schema-v1 JSON envelope;
nonzero categories also emit a concise stderr diagnostic. No query argument is
accepted. Use --prepare-request --root ., write the returned query file in place,
then --consume-request UUID; candidates alone permit --render-selection UUID.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import hmac
import itertools
import json
import math
import os
import re
import secrets
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Optional, Sequence

import cg_project_manifest as manifest
import secure_fs
from help import catalog, query

INSTALLED_ROOT = Path(__file__).resolve().parents[1]
SELECTION_SECONDS = 300
RUNTIME = ".compound-gpid/runtime/help-requests"
OWNER_KEY = RUNTIME + "/.owner-key"
CLEANUP_LIMIT = 16
CLEANUP_SCAN_LIMIT = 256
REQUEST_BYTES = 4096
SELECTION_BYTES = 1024
# Cleanup must not allocate unbounded input even for a corrupted owned file.
TRANSPORT_READ_LIMIT = 1024 * 1024
# Candidate relevance bands shown in rendered rows; the same thresholds are
# used by the ranked scoring pipeline in help.query.
HIGH_SCORE_THRESHOLD = 24
MEDIUM_SCORE_THRESHOLD = 12
# Ambient GIT_DIR/GIT_INDEX_FILE-style variables must never redirect the
# proof-staging probes to a foreign repository. Snapshot the environment once,
# stripping every GIT_* variable for all git subprocess calls.
_GIT_SAFE_ENV = {key: value for key, value in os.environ.items()
                 if not key.startswith("GIT_")}


def _text(value: str) -> str:
    """Escape inert extracted text, including HTML, links, and embedded lines."""
    value = " ".join(value.split())
    return re.sub(r"([\\`*_{}\[\]()#+.!|<>])", r"\\\1", value)


def _code(value: str) -> str:
    """Use a longer code delimiter so extracted syntax cannot end its code span."""
    fence = "`" * (max((len(part) for part in re.findall(r"`+", value)), default=0) + 1)
    return fence + " " + " ".join(value.split()) + " " + fence


def _result(state: str, digest: str, ids: list, data: dict, lines: list, recovery: Optional[list] = None) -> dict:
    """Build only the current strict semantic result fields."""
    return {"state": state, "catalogDigest": digest, "evidenceIds": list(dict.fromkeys(ids)),
            "data": data, "display": {"format": "markdown", "content": "\n".join(lines)},
            "warnings": [], "recovery": recovery or []}


def answer(value: dict, registry: dict, text: str, suites: Sequence[str], platform: str, os_name: str) -> dict:
    """Validate, retrieve, and render one semantic result without filesystem I/O.

    Args: value/registry: Strict evidence. text: Query. suites/platform/os_name:
        Installation context already proved by query_service.
    Returns: A current-schema semantic result, without transport state.
    Raises: HelpValidationError for invalid evidence or input.
    Example: answer(value, registry, '/cg-work', ['cg'], 'kilo', 'windows').
    """
    catalog.validate_catalog(value, registry)
    if value["generatorVersion"] != catalog.GENERATOR_VERSION:
        raise catalog.HelpValidationError("unsupported catalog generatorVersion")
    decision = query.retrieve(value, text, suites, platform, os_name)
    state, data = decision["state"], decision["data"]
    commands = {item["id"]: item for item in value["commands"]}
    workflows = {item["id"]: item for item in value["workflows"]}
    ids, lines = [], []
    if state == "exact":
        command = commands[data["commandId"]]
        ids = [command["id"]]
        lines = ["## " + _text(command["name"]), _text(command["summary"]),
                 query.availability(command, suites, platform, os_name)[2],
                 "Syntax: " + _code(command["usage"])]
        for label, field in [("Use Cases", "intents"), ("Examples", "examples"),
                             ("Prerequisites", "prerequisites"), ("Outputs", "outputs"),
                             ("Constraints", "constraints")]:
            lines.append("### " + label)
            lines.extend("- " + (_code(item) if field == "examples" else _text(item)) for item in command[field])
        lines.append("Source: " + _code(command["sourcePath"]))
        for target in command["documentationTargets"]:
            lines.append("Documentation: " + _code(target["path"] + "#" + target["section"]))
        if not set(command["supportedSuites"]) & set(suites):
            for activation in command["activation"]:
                lines.append("Activation evidence: " + _code(activation["sourcePath"] + "#" + activation["sourceSection"]))
        for relation in command["relatedCommands"]:
            lines.append("Next (" + _text(relation["relation"]) + "): " + _code(query.follow_up(relation["id"])))
        lines.append("Follow up: " + _code(query.follow_up(command["id"])))
    elif state == "candidates":
        ids = data["commandIds"]
        lines = ["## Command Candidates"]
        follow_ups = data["followUpQueries"]
        for row, follow_up_text in zip(decision["rows"], follow_ups):
            key, score, reason = row
            command = commands[key]
            band = "high" if score >= HIGH_SCORE_THRESHOLD else (
                "medium" if score >= MEDIUM_SCORE_THRESHOLD else "possible")
            label = query.availability(command, suites, platform, os_name)[2]
            lines.append("- {}: {} | {} | {} | {} | {}".format(
                _code(command["name"]), _text(command["summary"]), band,
                _text(label), _text(reason), _code(follow_up_text)))
    elif state == "workflow":
        workflow = workflows[data["workflowId"]]
        ids = [workflow["id"]] + data["commandIds"]
        lines = ["## " + _text(workflow["title"]), _text(workflow["summary"])]
        lines.extend("Prerequisite: " + _text(item) for item in workflow["prerequisites"])
        for step in workflow["steps"]:
            lines.append("{}. {}: {}. {}".format(step["order"], _code(commands[step["commandId"]]["name"]),
                         _text(step["purpose"]), _code(query.follow_up(step["commandId"]))))
            lines.extend("Evidence: " + _code(item["sourcePath"] + "#" + item["sourceSection"]) for item in step["evidence"])
        lines.append("Source: " + _code(workflow["sourcePath"] + "#" + workflow["sourceSection"]))
    elif state == "overview":
        ids = data["commandIds"] + data["workflowIds"]
        lines = ["## Command Overview"]
        category = None
        for key in data["commandIds"]:
            command = commands[key]
            if command["category"] != category:
                category = command["category"]
                lines.append("### " + _text(category))
            lines.append("- " + _code(command["name"]) + ": " + _text(command["summary"]) + " | " + _code(query.follow_up(key)))
        if data["workflowIds"]:
            lines.append("### Common Workflows")
            for key in data["workflowIds"]:
                workflow = workflows[key]
                lines.append("- " + _text(workflow["title"]) + " | " + _code("/cg-help " + workflow["intents"][0]))
        lines.append("Exact query syntax: " + _code("/cg-help slash:<name> or shell:<name>"))
    else:
        lines = ["## Unsupported", data["reason"], "Command overview: " + _code("/cg-help")]
    return _result(state, value["sourceDigest"], ids, data, lines)


def query_service(text: str, *, root: Path, platform: str,
                  source_root: Optional[Path] = None, catalog_path: Optional[Path] = None) -> dict:
    """Read only the installed clone and exact project activation evidence.

    Args: text: Raw query. root: Consumer root. platform: Invoking adapter.
        source_root/catalog_path: Required-pair local test overrides only.
    Returns: Semantic result including error on broken evidence; no writes.
    Example: query_service('/cg-work', root=Path('.'), platform='kilo').
    """
    digest = "0" * 64
    try:
        if (source_root is None) != (catalog_path is None):
            raise catalog.HelpValidationError("catalog and source-root overrides require a pair")
        source_root = INSTALLED_ROOT if source_root is None else Path(source_root).resolve()
        path = source_root / catalog.CATALOG_OUTPUT_PATH if catalog_path is None else Path(catalog_path)
        relative = path.relative_to(source_root).as_posix()
        content = secure_fs.secure_read_bytes(source_root, relative, reject_hardlinks=True, max_bytes=catalog.MAX_JSON_BYTES)
        value = catalog.load_strict_json_bytes(content, source=relative)
        source = catalog.validate_source_metadata(source_root)
        # Pin every declared definition and display reference. The validation
        # pass consumes these captured bytes instead of following later changes.
        paths = {identity.partition("#")[0] for identity, _ in source.source_inputs}
        for command in source.slash_commands + source.shell_commands:
            paths.update(item["path"] for item in command["documentationTargets"])
            paths.update(item["sourcePath"] for item in command["activation"] + command["availability"]["evidence"])
        for workflow in source.workflows:
            paths.update(item["sourcePath"] for step in workflow["steps"] for item in step["evidence"])
        captured = {key: secure_fs.secure_read_bytes(source_root, key, reject_hardlinks=True,
                    max_bytes=catalog.MAX_JSON_BYTES) for key in sorted(paths)}
        source = catalog.validate_source_metadata(source_root, source_overrides=captured)
        registry = catalog.load_strict_json_bytes(captured[catalog.MODULE_REGISTRY_PATH], source=catalog.MODULE_REGISTRY_PATH)
        expected = catalog.merge_catalog(registry, source)
        catalog.validate_catalog(value, registry)
        if value != expected or content != catalog.serialize_catalog(expected):
            raise catalog.HelpValidationError("installed help catalog is stale or incompatible; run catalog --check")
        digest = value["sourceDigest"]
        suites = manifest.validate_help_activation(Path(root), source_root, value, platform)
        return answer(value, registry, text, suites, platform, query.host_os())
    except (ValueError, OSError, manifest.ManifestResolutionError) as error:
        recovery = ["python scripts/cg_generate_help_catalog.py --check", "cg-link --platforms " + platform]
        message = str(error)
        return _result("error", digest, [], {"code": "help.evidence-invalid", "message": message},
                       ["## Help Error", _text(message), "Recovery: " + "; ".join(_code(item) for item in recovery)], recovery)


class Selection:
    """Single-use opaque selection capability bound to one result and UUID.

    Args: request_id: Validated transport UUID. result: Candidate semantic result.
        now: Creation time in seconds (injectable for tests).
    Example: selection = Selection(request_id, result); selection.render(...).
    """

    def __init__(self, request_id: str, result: dict, *, now: Optional[float] = None) -> None:
        """Capture immutable candidate evidence and a 300-second lifetime."""
        catalog.validate_transport_envelope(dict(schemaVersion=1, operation="query-completed", requestId=request_id, result=result))
        if result["state"] != "candidates":
            raise catalog.HelpValidationError("selection requires candidates")
        self.request_id = request_id
        self.token = secrets.token_urlsafe(32)
        self._result = copy.deepcopy(result)
        self._expires = (time.time() if now is None else now) + SELECTION_SECONDS
        self._used = False

    @property
    def candidate_ids(self) -> list:
        """Return a copy of the closed allowed-ID list, not mutable stored evidence."""
        return list(self._result["data"]["commandIds"])

    def render(self, request_id: str, token: str, ids: list, *, now: Optional[float] = None) -> dict:
        """Validate selection and return deterministic Markdown in selected order.

        Args: request_id/token: Original capability. ids: Ordered nonempty subset.
            now: Current time, injectable for tests.
        Returns: Candidate result; no model prose or new evidence is accepted.
        Raises: HelpValidationError for replay, expiry, or any invalid selection.
        Example: selection.render(request_id, selection.token, [allowed_id]).
        """
        current = time.time() if now is None else now
        valid = (not self._used and current < self._expires and request_id == self.request_id
                 and isinstance(token, str) and token.isascii()
                 and hmac.compare_digest(token, self.token)
                 and isinstance(ids, list) and 1 <= len(ids) <= query.MAX_CANDIDATES
                 and all(isinstance(key, str) and key in self.candidate_ids for key in ids))
        if not valid or len(set(ids)) != len(ids):
            raise catalog.HelpValidationError("unknown, duplicate, expired, cross-request, or consumed selection")
        result = copy.deepcopy(self._result)
        indices = [self.candidate_ids.index(key) for key in ids]
        for field in ("commandIds", "reasons", "followUpQueries"):
            result["data"][field] = [result["data"][field][index] for index in indices]
        lines = result["display"]["content"].splitlines()
        result["display"]["content"] = "\n".join([lines[0]] + [lines[index + 1] for index in indices])
        result["evidenceIds"] = list(ids)
        self._used = True
        return result


def _json_bytes(value: object) -> bytes:
    """Serialize local transport state deterministically, without executable data."""
    return (json.dumps(value, sort_keys=True, ensure_ascii=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def _path(request_id: str, suffix: str) -> str:
    """Derive a confined file path only after strict UUID validation."""
    if not isinstance(request_id, str) or not catalog.UUID_PATTERN.fullmatch(request_id):
        raise catalog.HelpValidationError("Invalid lowercase request UUID.")
    return RUNTIME + "/" + request_id + suffix


def _root(value: str) -> Path:
    """Reject lexical root aliases before resolving the invoking project."""
    root = Path(os.path.abspath(value))
    for component in [root] + list(root.parents):
        metadata = component.lstat()
        if component.is_symlink() or getattr(metadata, "st_file_attributes", 0) & 0x400:
            raise secure_fs.SecureMutationError("Project root has a link or reparse ancestor.")
    if not root.is_dir() or root.resolve() != root:
        raise secure_fs.SecureMutationError("Project root must be a canonical directory.")
    secure_fs.revalidate_destination_ancestors(root, root / OWNER_KEY)
    return root


def _check_ignored(root: Path, request_id: str) -> None:
    """Before prepare, require Git to ignore runtime files in versioned projects."""
    probe = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root,
                           env=_GIT_SAFE_ENV, capture_output=True, timeout=15, check=False)
    if probe.returncode:
        if b"not a git repository" in probe.stderr.lower():
            return
        raise catalog.HelpValidationError("Cannot verify project Git ignore state.")
    paths = [OWNER_KEY] + [_path(request_id, suffix) for suffix in (
        ".query.txt", ".selection.json", ".query.state.json", ".selection.state.json",
        ".query.lock", ".selection.lock")]
    ignored = subprocess.run(["git", "check-ignore", "--no-index", "--stdin"],
        cwd=root, env=_GIT_SAFE_ENV, input=("\n".join(paths) + "\n").encode("utf-8"),
        capture_output=True, timeout=15, check=False)
    tracked = subprocess.run(["git", "ls-files", "--", ".compound-gpid/runtime/"],
        cwd=root, env=_GIT_SAFE_ENV, capture_output=True, timeout=15, check=False)
    if (ignored.returncode or set(ignored.stdout.decode("utf-8").splitlines()) != set(paths)
            or tracked.returncode or tracked.stdout):
        raise catalog.HelpValidationError(
            "Runtime files must be untracked and ignored; run cg-link to update managed ignores.")


def _owner_key(root: Path, *, create: bool = False) -> bytes:
    """Read the private local signing key; publish exclusively only on prepare."""
    try:
        key = secure_fs.secure_read_bytes(root, OWNER_KEY, reject_hardlinks=True, max_bytes=32)
    except FileNotFoundError:
        if not create:
            raise
        key = secrets.token_bytes(32)
        try:
            secure_fs.secure_create_bytes(root, OWNER_KEY, key)
        except OSError:
            # Another prepare may have published first. Never replace its key.
            return _owner_key(root)
    if len(key) != 32:
        raise catalog.HelpValidationError("Invalid local request ownership key.")
    return key


def _state(root: Path, request_id: str, stage: str, key: bytes) -> tuple:
    """Read a bounded authenticated ownership record, not a filename/mtime claim."""
    path = _path(request_id, "." + stage + ".state.json")
    raw = secure_fs.secure_read_bytes(root, path, reject_hardlinks=True,
                                    max_bytes=TRANSPORT_READ_LIMIT)
    wrapped = catalog.load_strict_json_bytes(raw, source="request ownership")
    if not isinstance(wrapped, dict) or set(wrapped) != {"record", "mac"}:
        raise catalog.HelpValidationError("Invalid request ownership record.")
    record, mac = wrapped["record"], wrapped["mac"]
    expected = hmac.new(key, _json_bytes(record), hashlib.sha256).hexdigest()
    if not isinstance(mac, str) or not mac.isascii() or not hmac.compare_digest(expected, mac):
        raise catalog.HelpValidationError("Unproved request ownership.")
    fields = {"version", "root", "requestId", "stage", "identity", "expires", "binding"}
    if stage == "selection":
        fields.update(("token", "result", "freshness"))
    if (not isinstance(record, dict) or set(record) != fields or record["version"] != 1
            or record["root"] != str(root) or record["requestId"] != request_id
            or record["stage"] != stage
            or not isinstance(record["identity"], list) or len(record["identity"]) != 3
            or any(type(item) is not int or item < 0 for item in record["identity"])
            or type(record["expires"]) not in (int, float) or not math.isfinite(record["expires"])):
        raise catalog.HelpValidationError("Mismatched request ownership fields.")
    return record, path, raw


def _save_state(root: Path, record: dict, key: bytes) -> None:
    """Exclusively publish signed state after the payload identity is captured."""
    wrapped = {"record": record, "mac": hmac.new(key, _json_bytes(record), hashlib.sha256).hexdigest()}
    secure_fs.secure_create_bytes(root,
        _path(record["requestId"], "." + record["stage"] + ".state.json"), _json_bytes(wrapped))


def _remove(root: Path, path: str, content: bytes, identity: Optional[tuple] = None) -> None:
    """Authorize deletion by both captured bytes and prepared identity."""
    secure_fs.secure_delete_verified(root, path, hashlib.sha256(content).hexdigest(),
                                    expected_identity=identity)


def _take(root: Path, record: dict, state_path: str, raw_state: bytes) -> bytes:
    """Consume only the prepared payload; never delete a replacement on failure."""
    suffix = ".query.txt" if record["stage"] == "query" else ".selection.json"
    path = _path(record["requestId"], suffix)
    identity = tuple(record["identity"])
    try:
        content = secure_fs.secure_read_bytes(root, path, expected_identity=identity,
            reject_hardlinks=True, max_bytes=TRANSPORT_READ_LIMIT)
    except secure_fs.SecureReadLimitError as error:
        # An oversize error is not deletion authority. Recheck the prepared
        # identity and single-link regular type through the deletion handle.
        secure_fs.secure_delete_verified(root, path, None, expected_identity=identity)
        _remove(root, state_path, raw_state)
        raise catalog.HelpValidationError("Transport input exceeds secure read limit.") from error
    _remove(root, path, content, identity)
    _remove(root, state_path, raw_state)
    return content


def _lock_identity_path(request_id: str, stage: str) -> str:
    """Return the sidecar that records one stage-claim lock's exact identity."""
    return _path(request_id, "." + stage + ".lock.identity.json")


def _lock_identity_bytes(request_id: str, stage: str, key: bytes, identity: tuple) -> bytes:
    """Build the authenticated lock-identity sidecar for one stage claim."""
    record = {"version": 1, "requestId": request_id, "stage": stage,
              "identity": list(identity)}
    wrapped = {"record": record,
               "mac": hmac.new(key, _json_bytes(record), hashlib.sha256).hexdigest()}
    return _json_bytes(wrapped)


def _verified_lock_identity(root: Path, request_id: str, stage: str, key: bytes) -> Optional[Tuple[tuple, bytes]]:
    """Return the recorded lock identity and raw sidecar when provably ours."""
    try:
        raw = secure_fs.secure_read_bytes(root, _lock_identity_path(request_id, stage),
                                          reject_hardlinks=True, max_bytes=TRANSPORT_READ_LIMIT)
        wrapped = catalog.load_strict_json_bytes(raw, source="lock ownership")
        if (
            not isinstance(wrapped, dict)
            or not isinstance(wrapped.get("record"), dict)
            or not isinstance(wrapped.get("mac"), str)
        ):
            return None
        record, mac = wrapped["record"], wrapped["mac"]
        expected = hmac.new(key, _json_bytes(record), hashlib.sha256).hexdigest()
        if (isinstance(mac, str) and mac.isascii() and hmac.compare_digest(expected, mac)
                and isinstance(record, dict)
                and set(record) == {"version", "requestId", "stage", "identity"}
                and record["version"] == 1
                and record["requestId"] == request_id and record["stage"] == stage
                and isinstance(record["identity"], list) and len(record["identity"]) == 3
                and all(type(item) is int and item >= 0 for item in record["identity"])):
            return tuple(record["identity"]), raw
    except (OSError, ValueError, TypeError):
        return None
    return None


def _cleanup(root: Path, key: bytes) -> None:
    """Retire at most CLEANUP_LIMIT expired records after bounded local discovery."""
    retired = 0
    with os.scandir(root / RUNTIME) as entries:
        for entry in itertools.islice(entries, CLEANUP_SCAN_LIMIT):
            match = re.fullmatch(r"([0-9a-f-]+)\.(query|selection)\.state\.json", entry.name)
            if not match or retired >= CLEANUP_LIMIT:
                continue
            request_id, stage = match.groups()
            try:
                record, path, raw = _state(root, request_id, stage, key)
                if time.time() < record["expires"]:
                    continue
                retired += 1
                # Authenticated expiry revokes the payload capability even if a
                # consumer left a lock. A recorded lock identity proves one CLI
                # stage claim and is removed with the expired state; an
                # unrecorded or foreign lock is never deleted.
                verified = _verified_lock_identity(root, request_id, stage, key)
                if verified is not None:
                    lock_identity, raw_identity = verified
                    lock_path = _path(request_id, "." + stage + ".lock")
                    try:
                        secure_fs.secure_delete_verified(root, lock_path, None,
                                                         expected_identity=lock_identity)
                        _remove(root, _lock_identity_path(request_id, stage), raw_identity)
                    except (OSError, ValueError):
                        pass
                _take(root, record, path, raw)
            except (OSError, ValueError):
                # Unknown or replaced identities are not cleanup authority.
                continue


def _prepared(request_id: str, selection: Optional[Selection] = None) -> dict:
    """Build and validate the public write capability before creating its file."""
    envelope = dict(schemaVersion=1, requestId=request_id, expiresInSeconds=300,
                    cleanupPolicy="consume-once-and-expire")
    if selection is None:
        envelope.update(operation="request-prepared", maxBytes=REQUEST_BYTES,
                        queryPath=_path(request_id, ".query.txt"))
    else:
        envelope.update(operation="selection-prepared", maxBytes=SELECTION_BYTES,
            selectionPath=_path(request_id, ".selection.json"), selectionToken=selection.token,
            catalogDigest=selection._result["catalogDigest"],
            evidenceIds=selection.candidate_ids, candidateIds=selection.candidate_ids)
    catalog.validate_transport_envelope(envelope)
    return envelope


class _Parser(argparse.ArgumentParser):
    """Keep invalid CLI arguments inside the documented transport-error boundary."""

    def error(self, message: str) -> None:
        """Raise instead of printing usage or terminating the callable CLI."""
        raise catalog.HelpValidationError(message)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Execute one fixed transport operation and emit one validated JSON envelope.

    Args: argv: Operation, root, platform, and optional paired fixture paths.
    Returns: Documented success (0), transport (2), evidence (3), or I/O (4) code.
    Example: main(['--prepare-request', '--root', '.']).
    """
    status = 0
    try:
        parser = _Parser(description=__doc__, allow_abbrev=False)
        operations = parser.add_mutually_exclusive_group(required=True)
        operations.add_argument("--prepare-request", action="store_true")
        operations.add_argument("--consume-request")
        operations.add_argument("--render-selection")
        parser.add_argument("--root", default=".")
        parser.add_argument("--platform", default="copilot",
            choices=("copilot", "claude-code", "codex", "opencode", "kilo"))
        parser.add_argument("--catalog")
        parser.add_argument("--source-root")
        args = parser.parse_args(argv)
        if (args.catalog is None) != (args.source_root is None):
            raise catalog.HelpValidationError("catalog and source-root overrides require a pair")
        for value in (args.catalog, args.source_root):
            if value is not None and ("://" in value or value.startswith(("//", "\\\\"))):
                raise catalog.HelpValidationError("Catalog overrides must be local paths.")
        source_root = INSTALLED_ROOT if args.source_root is None else Path(args.source_root).resolve()
        catalog_path = source_root / catalog.CATALOG_OUTPUT_PATH if args.catalog is None else Path(args.catalog).resolve()
        catalog_path.relative_to(source_root)
        binding = [str(source_root), str(catalog_path), args.platform]
        request_id = str(uuid.uuid4()) if args.prepare_request else (args.consume_request or args.render_selection)
        _path(request_id, ".query.txt")
        root = _root(args.root)
        service_args = dict(root=root, platform=args.platform, source_root=source_root, catalog_path=catalog_path)
        if args.prepare_request:
            envelope = _prepared(request_id)
            _check_ignored(root, request_id)
            key = _owner_key(root, create=True)
            _cleanup(root, key)
            identity = secure_fs.secure_create_bytes(root, envelope["queryPath"], b"")
            record = dict(version=1, root=str(root), requestId=request_id, stage="query",
                          identity=identity, expires=time.time() + SELECTION_SECONDS, binding=binding)
            try:
                _save_state(root, record, key)
            except (OSError, ValueError):
                _remove(root, envelope["queryPath"], b"", identity)
                raise
        else:
            stage = "query" if args.consume_request else "selection"
            key = _owner_key(root)
            record, state_path, raw_state = _state(root, request_id, stage, key)
            if record["binding"] != binding:
                raise catalog.HelpValidationError("Request belongs to a different catalog or platform.")
            lock = _path(request_id, "." + stage + ".lock")
            lock_identity = secure_fs.secure_create_bytes(root, lock, b"")
            lock_id_path = _lock_identity_path(request_id, stage)
            lock_id_bytes = _lock_identity_bytes(request_id, stage, key, lock_identity)
            try:
                secure_fs.secure_create_bytes(root, lock_id_path, lock_id_bytes)
            except (OSError, ValueError):
                _remove(root, lock, b"", lock_identity)
                raise
            try:
                # Read state again under the exclusive stage claim. A replay may
                # have read the old record just before the first consumer finished.
                record, state_path, raw_state = _state(root, request_id, stage, key)
                content = _take(root, record, state_path, raw_state)
                if time.time() >= record["expires"]:
                    raise catalog.HelpValidationError("Request or selection expired.")
                limit = REQUEST_BYTES if stage == "query" else SELECTION_BYTES
                if len(content) > limit:
                    raise catalog.HelpValidationError("Transport input exceeds {} bytes.".format(limit))
                if stage == "query":
                    text = content.decode("utf-8")
                    query.normalize_query(text)
                    result = query_service(text, **service_args)
                    envelope = dict(schemaVersion=1, operation="query-completed", requestId=request_id, result=result)
                    if result["state"] == "candidates":
                        selection = Selection(request_id, result)
                        # Reuse the first snapshot: a second empty-query pass can
                        # only restate this synchronous invocation's evidence and
                        # doubles the validation work. The render stage still
                        # revalidates against the stored snapshot below.
                        freshness = result
                        envelope = _prepared(request_id, selection)
                        identity = secure_fs.secure_create_bytes(root, envelope["selectionPath"], b"")
                        record = dict(version=1, root=str(root), requestId=request_id, stage="selection",
                            identity=identity, expires=selection._expires, binding=binding,
                            token=selection.token, result=result, freshness=freshness)
                        try:
                            _save_state(root, record, key)
                        except (OSError, ValueError):
                            _remove(root, envelope["selectionPath"], b"", identity)
                            raise
                else:
                    ids = catalog.load_strict_json_bytes(content, source="selection")
                    freshness = query_service("", **service_args)
                    if (freshness["state"] == "error"
                            or freshness["catalogDigest"] != record["freshness"]["catalogDigest"]):
                        raise catalog.HelpValidationError("Catalog or project evidence changed; prepare a new request.")
                    selection = Selection(request_id, record["result"])
                    selection.token, selection._expires = record["token"], record["expires"]
                    result = selection.render(request_id, record["token"], ids)
                    envelope = dict(schemaVersion=1, operation="selection-rendered", requestId=request_id, result=result)
            finally:
                _remove(root, lock, b"", lock_identity)
                try:
                    _remove(root, lock_id_path, lock_id_bytes)
                except (OSError, ValueError):
                    pass
        if envelope.get("result", {}).get("state") == "error":
            status = 3
            sys.stderr.write("cg-help: evidence: " + envelope["result"]["data"]["message"] + "\n")
    except (ValueError, OSError, TypeError, subprocess.SubprocessError) as error:
        status = 4 if isinstance(error, (OSError, subprocess.SubprocessError)) else 2
        message = " ".join(str(error).split()) or "Invalid transport input."
        envelope = dict(schemaVersion=1, operation="transport-error",
                        code="help.io" if status == 4 else "help.transport-invalid",
                        message=message, recovery=["cg-help --prepare-request --root ."])
        sys.stderr.write("cg-help: " + envelope["code"] + ": " + message + "\n")
    try:
        catalog.validate_transport_envelope(envelope)
        sys.stdout.write(_json_bytes(envelope).decode("ascii"))
    except (ValueError, OSError) as error:
        sys.stderr.write("cg-help: response validation or output failed: " + str(error) + "\n")
        return 4
    return status


if __name__ == "__main__":
    raise SystemExit(main())
