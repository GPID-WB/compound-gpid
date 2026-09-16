"""Verify source-bound help support evidence; never create certification claims.

Example: verify_evidence(Path('.'), parsed_evidence). Git operations are read-only.
All evidence strings are data. Fixed schema patterns define the sensitive surface.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import secure_fs
from help import catalog

SCHEMA_PATH = "scripts/schemas/help_support_evidence_schema.json"
PROMPT_ROOTS = {"copilot": ".github/prompts", "claude-code": ".claude/commands",
                "codex": ".agents/commands", "opencode": ".opencode/commands",
                "kilo": ".kilo/commands"}
PROBE_CASES = {"overview": "", "exact": "/cg-help",
               "metacharacters": 'plan review ; & | $(echo sentinel) `x` "quoted" next'}
PROBE_ARGUMENTS = ["run", "--format", "json", "--command", "cg-help"]
MAX_GIT_BYTES = 16 * 1024 * 1024
MAX_BLOB_BYTES = 4 * 1024 * 1024
# Git probes must never be redirected by ambient GIT_* variables to a foreign
# repository; snapshot the environment without them for every git call.
_GIT_SAFE_ENV = {key: value for key, value in os.environ.items()
                 if not key.startswith("GIT_")}


def _sha(content: bytes) -> str:
    """Return the SHA-256 hex digest of one exact byte payload.

    Args:
        content: Exact bytes to hash.

    Returns:
        Lowercase 64-character hex digest.

    Example:
        ``_sha(b"x")`` returns the sha256 of the single byte.
    """
    return hashlib.sha256(content).hexdigest()


def _git(root: Path, *arguments: str, data: Optional[bytes] = None) -> bytes:
    """Use fixed argument vectors and disk spools for bounded Git inventories.

    Args:
        root: Consumer root (a git worktree or bare repository).
        arguments: Fixed git argument vector; never user-controlled flags.
        data: Optional exact stdin payload (used by batch probes).

    Returns:
        Bounded stdout bytes from the single verified git process.

    Raises:
        ValueError: If git fails or returns more than the inventory limit.

    Example:
        ``_git(root, "rev-parse", "--verify", subject + "^{commit}")``.
    """
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        input_stream = None
        if data is not None:
            input_stream = tempfile.TemporaryFile()
            input_stream.write(data)
            input_stream.seek(0)
        try:
            result = subprocess.run(
                ["git", "-C", str(root), *arguments],
                stdout=output,
                stderr=errors,
                stdin=input_stream,
                timeout=30,
                check=False,
                env=_GIT_SAFE_ENV,
            )
        finally:
            if input_stream is not None:
                input_stream.close()
        if result.returncode:
            errors.seek(0)
            detail = errors.read(MAX_GIT_BYTES + 1).decode("utf-8", errors="replace").strip()
            raise ValueError(
                "Git support check failed: {}{}".format(
                    arguments[0], ": " + detail[:512] if detail else ""
                )
            )
        size = output.tell()
        if size > MAX_GIT_BYTES:
            raise ValueError("Git support inventory exceeds limit")
        output.seek(0)
        return output.read(MAX_GIT_BYTES + 1)


def _schema() -> dict:
    root = Path(__file__).resolve().parents[2]
    return catalog.load_strict_json_bytes(secure_fs.secure_read_bytes(
        root, SCHEMA_PATH, reject_hardlinks=True, max_bytes=MAX_BLOB_BYTES), source=SCHEMA_PATH)


def _commit(root: Path, subject: str) -> None:
    """Require an exact full lowercase commit id in the subject repository.

    Args:
        root: Consumer root (a git worktree or bare repository).
        subject: Full 40-hex commit id.

    Raises:
        ValueError: If the subject is not an exact commit.

    Example:
        ``_commit(root, "0" * 40)`` rejects most ids; real probes use the
        exact published commit from the review evidence.
    """
    if not isinstance(subject, str) or re.fullmatch(r"[0-9a-f]{40}", subject) is None:
        raise ValueError("subjectCommit must be a full lowercase 40-hex commit")
    if _git(root, "rev-parse", "--verify", subject + "^{commit}").decode().strip() != subject:
        raise ValueError("subjectCommit is not an exact commit")


def _tree(root: Path, subject: str) -> dict:
    """Inventory one subject commit's exact verified file tree.

    Args:
        root: Consumer root (a git worktree or bare repository).
        subject: Exact full commit id (validated by ``_commit``).

    Returns:
        Mapping of subject-relative path to ``(mode, kind, oid, size)``.

    Example:
        ``_tree(root, "0" * 40)`` raises; ``_tree(root, HEAD)`` inventories
        the checked-out subject.
    """
    _commit(root, subject)
    result = {}
    for row in _git(root, "ls-tree", "-rzl", "--full-tree", subject).split(b"\0"):
        if not row:
            continue
        metadata, path_bytes = row.split(b"\t", 1)
        mode, kind, oid, size = metadata.decode("ascii").split()
        path = path_bytes.decode("utf-8", errors="strict")
        catalog._validate_relative_path(path, "Git path")
        result[path] = (mode, kind, oid, size)
    return result


def _blobs(root: Path, tree: dict, paths: Sequence[str]) -> Dict[str, bytes]:
    """Read exact subject blob contents in one bounded batch cat-file probe.

    Args:
        root: Consumer root (a git worktree or bare repository).
        tree: Subject file tree from ``_tree``.
        paths: Subject-relative paths to read.

    Returns:
        Mapping of path to exact blob bytes.

    Raises:
        ValueError: For missing, unsafe, oversized, or truncated batch reads.

    Example:
        ``_blobs(root, tree, [".github/prompts/cg-help.prompt.md"])``
        returns the exact canonical prompt bytes from the subject commit.
    """
    requests: Dict[str, str] = {}
    for path in paths:
        if path not in tree:
            raise ValueError("Missing subject binding: " + path)
        mode, kind, oid, size = tree[path]
        if mode not in ("100644", "100755") or kind != "blob" or int(size) > MAX_BLOB_BYTES:
            raise ValueError("Unsafe subject binding: " + path)
        requests.setdefault(oid, path)
    if not requests:
        return {}
    payload = "".join(oid + "\n" for oid in requests)
    output = _git(root, "cat-file", "--batch", data=payload.encode("ascii"))
    values: Dict[str, bytes] = {}
    position = 0
    for oid in requests:
        header_end = output.index(b"\n", position)
        header = output[position:header_end].split(b" ")
        if len(header) != 3 or header[0] != oid.encode("ascii") or header[1] != b"blob":
            raise ValueError("Git batch read returned an unexpected blob")
        try:
            size = int(header[2])
        except ValueError as error:
            raise ValueError("Git batch read returned a malformed header") from error
        if size > MAX_BLOB_BYTES:
            raise ValueError("Git batch read returned an oversized blob")
        body = output[header_end + 1:header_end + 1 + size]
        if len(body) != size:
            raise ValueError("Git batch read returned truncated content")
        position = header_end + 1 + size + 1
        values[requests[oid]] = body
    return values


def _blob(root: Path, tree: dict, path: str) -> bytes:
    """Read one exact subject blob through the shared batch probe.

    Args:
        root: Consumer root (a git worktree or bare repository).
        tree: Subject file tree from ``_tree``.
        path: Subject-relative path to read.

    Returns:
        Exact blob bytes.

    Example:
        ``_blob(root, tree, ".github/shared/help-catalog.json")``.
    """
    if path not in tree:
        raise ValueError("Missing subject binding: " + path)
    return _blobs(root, tree, [path])[path]


def _sensitive(tree: dict, source_catalog: dict) -> list:
    patterns = _schema()["helpSensitivePatterns"]
    paths = {path for path in tree if any(fnmatch.fnmatchcase(path, item) for item in patterns)}
    for command in source_catalog.get("commands", []):
        sources = list(command["definitionSources"])
        sources.extend(item["path"] for item in command.get("documentationTargets", []))
        sources.extend(item["sourcePath"] for item in command.get("activation", []))
        sources.extend(item["sourcePath"] for item in command.get("availability", {}).get("evidence", []))
        for path in sources:
            catalog._validate_relative_path(path, "definition source")
            paths.add(path)
    for workflow in source_catalog.get("workflows", []):
        catalog._validate_relative_path(workflow["sourcePath"], "workflow sourcePath")
        paths.add(workflow["sourcePath"])
        for step in workflow["steps"]:
            for item in step["evidence"]:
                catalog._validate_relative_path(item["sourcePath"], "workflow evidence sourcePath")
                paths.add(item["sourcePath"])
    # Evidence/claims cannot become their own implementation inputs.
    if any(path.startswith(".cg-docs/") for path in paths):
        raise ValueError("Claim/evidence paths cannot enter the sensitive inventory")
    if len(paths) > 8192:
        raise ValueError("Help-sensitive inventory exceeds limit")
    return sorted(paths)


def subject_bindings(root: Path, subject: str) -> Dict[str, Any]:
    """Compute sorted subject file/mode hashes from Git objects, not the checkout."""
    tree = _tree(root, subject)
    value = catalog.load_strict_json_bytes(_blob(root, tree, catalog.CATALOG_OUTPUT_PATH), source="subject catalog")
    paths = _sensitive(tree, value)
    blobs = _blobs(root, tree, paths)
    rows = [dict(path=path, mode=tree.get(path, (None,))[0],
                 sha256=_sha(blobs[path])) for path in paths]
    return dict(sensitivePaths=rows, sensitiveDigest=_sha(
        json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")))


def platform_bindings(root: Path, subject: str, platform: str) -> Dict[str, str]:
    """Hash a platform's exact subject catalog, canonical prompt, mapping and asset."""
    tree = _tree(root, subject)
    canonical = ".github/prompts/cg-help.prompt.md"
    mapping_path = ".github/shared/target-mapping.json"
    mapping_bytes = _blob(root, tree, mapping_path)
    mapping = catalog.load_strict_json_bytes(mapping_bytes, source="subject mapping")
    targets = [item for item in mapping["targets"] if item["id"] == platform]
    if len(targets) != 1:
        raise ValueError("Missing or duplicate platform binding")
    generated = canonical if platform == "copilot" else targets[0]["outputPaths"]["commands"] + "/cg-help.md"
    catalog._validate_relative_path(generated, "generated binding")
    blobs = _blobs(root, tree, [catalog.CATALOG_OUTPUT_PATH, canonical, generated])
    content = blobs[catalog.CATALOG_OUTPUT_PATH]
    source_catalog = catalog.load_strict_json_bytes(content, source="subject catalog")
    return dict(catalogSourceDigest=source_catalog["sourceDigest"], catalogSha256=_sha(content),
                canonicalPromptSha256=_sha(blobs[canonical]),
                targetMappingSha256=_sha(mapping_bytes),
                generatedPromptSha256=_sha(blobs[generated]))


def validate_probe(receipt: dict) -> None:
    """Reject a failed probe or a host that changed/omitted the received query."""
    schema = _schema()
    catalog._validate_against_schema(receipt, schema["$defs"]["probe"], "probe", root_schema=schema)
    name = receipt["name"]
    if receipt["arguments"] != PROBE_ARGUMENTS:
        raise ValueError("Probe arguments differ from the non-secret contract")
    if receipt["receivedQuerySha256"] != _sha(PROBE_CASES[name].encode("utf-8")):
        raise ValueError("Received query fingerprint mismatch")
    if receipt["outcome"] != "passed":
        raise ValueError("Executed failed probe blocks support")


def validate_host_flow(name: str, records: list, final_text: str,
                       shell_commands: list, platform: str = "kilo") -> dict:
    """Validate observed backend operations and the unchanged host final answer.

    Records come from the certified fixture's backend observer, not model claims.
    Only fixed public probe names and query fingerprints enter returned evidence.
    """
    if name not in PROBE_CASES or platform not in PROMPT_ROOTS or not isinstance(records, list):
        raise ValueError("Unknown host flow")
    if len(records) != (3 if name == "metacharacters" else 2):
        raise ValueError("Missing or extra host operations")
    expected_ops = ["request-prepared", "selection-prepared", "selection-rendered"] if name == "metacharacters" else ["request-prepared", "query-completed"]
    flags = ["--prepare-request", "--consume-request", "--render-selection"]
    request_id = None
    expected_commands = []
    fingerprints = []
    for index, record in enumerate(records):
        if set(record) != {"argv", "exitCode", "envelope", "queryFingerprints"}:
            raise ValueError("Unknown observer record fields")
        envelope = record["envelope"]
        catalog.validate_transport_envelope(envelope)
        if len(json.dumps(envelope).encode("utf-8")) > 262144:
            raise ValueError("Host envelope exceeds limit")
        if index == 0:
            request_id = envelope["requestId"]
        if envelope.get("operation") != expected_ops[index] or envelope.get("requestId") != request_id or record["exitCode"] != 0:
            raise ValueError("Host operation/schema/request/exit mismatch")
        argv = [flags[index]] + ([] if index == 0 else [request_id]) + ["--root", ".", "--platform", platform]
        if record["argv"] != argv:
            raise ValueError("Query leaked into backend arguments or fixed arguments changed")
        expected_commands.append("cg-help " + " ".join(argv))
        fingerprints.extend(record["queryFingerprints"])
    if shell_commands != expected_commands:
        raise ValueError("Host used non-contract shell commands or shell query transport")
    expected_hash = _sha(PROBE_CASES[name].encode("utf-8"))
    if not fingerprints or fingerprints[0] != expected_hash or any(
        value != _sha(b"") for value in fingerprints[1:]
    ):
        raise ValueError("Received query fingerprint mismatch")
    result = records[-1]["envelope"]["result"]
    state = {"overview": "overview", "exact": "exact", "metacharacters": "candidates"}[name]
    if result["state"] != state or final_text not in (result["display"]["content"], result["display"]["content"] + "\n"):
        raise ValueError("Host did not relay the deterministic final answer unchanged")
    if name == "metacharacters":
        allowed = records[1]["envelope"]["candidateIds"]
        selected = result["data"]["commandIds"]
        if not set(selected) <= set(allowed) or records[1]["envelope"]["evidenceIds"] != allowed:
            raise ValueError("Host selected IDs outside its prepared evidence")
    receipt = dict(name=name, arguments=list(PROBE_ARGUMENTS),
                   receivedQuerySha256=expected_hash, outcome="passed")
    validate_probe(receipt)
    return receipt


def _require_rfc3339_utc(value: str) -> None:
    """Reject runAt values that are not strict literal-Z UTC RFC3339 dates."""
    datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ") or None


def verify_evidence(root: Path, evidence: dict) -> None:
    """Validate schema, status, subject ancestry and unchanged sensitive bytes.

    Args: root: Current Git checkout. evidence: Parsed support JSON.
    Raises: ValueError on missing, stale, unsafe, failed or unverified Kilo proof.
    Example: verify_evidence(Path('.'), evidence).
    """
    schema = _schema()
    catalog._validate_against_schema(evidence, schema, "support evidence")
    if type(evidence["schemaVersion"]) is not int:
        raise ValueError("schemaVersion must be an integer")
    subject = evidence["subjectCommit"]
    _commit(root, subject)
    if evidence["probeCommit"] != subject:
        raise ValueError("Probe commit does not match subjectCommit")
    if evidence["probeTree"] != _git(root, "rev-parse", subject + "^{tree}").decode().strip():
        raise ValueError("Probe tree does not match subjectCommit")
    try:
        _git(root, "merge-base", "--is-ancestor", subject, "HEAD")
    except ValueError as error:
        raise ValueError("subjectCommit is not an ancestor of current HEAD") from error
    expected = subject_bindings(root, subject)
    if any(evidence[key] != value for key, value in expected.items()):
        raise ValueError("Help-sensitive subject inventory/digest mismatch")
    current = _git(root, "rev-parse", "HEAD").decode().strip()
    if subject_bindings(root, current) != expected:
        raise ValueError("Help-sensitive committed paths changed after subject")
    # One bounded NUL inventory avoids Windows argv limits and catches additions.
    names = _git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    present = {item.decode("utf-8") for item in names.split(b"\0") if item}
    subject_tree = _tree(root, subject)
    source_catalog = catalog.load_strict_json_bytes(
        _blob(root, subject_tree, catalog.CATALOG_OUTPUT_PATH), source="subject catalog")
    if _sensitive(dict.fromkeys(present), source_catalog) != [row["path"] for row in expected["sensitivePaths"]]:
        raise ValueError("Help-sensitive working inventory changed")
    changed = {path.decode("utf-8") for path in _git(root, "diff", "--name-only", "-z", subject, "--").split(b"\0") if path}
    if changed.intersection(row["path"] for row in expected["sensitivePaths"]):
        raise ValueError("Help-sensitive working/index paths or modes changed")
    for row in expected["sensitivePaths"]:
        try:
            content = secure_fs.secure_read_bytes(root, row["path"], reject_hardlinks=True, max_bytes=MAX_BLOB_BYTES)
        except (OSError, ValueError) as error:
            raise ValueError("Unsafe or missing help-sensitive working path: " + row["path"]) from error
        if _sha(content) != row["sha256"]:
            raise ValueError("Help-sensitive working bytes changed: " + row["path"])
    rows = evidence["platforms"]
    if [row["platform"] for row in rows] != sorted(PROMPT_ROOTS):
        raise ValueError("Support matrix must contain all five sorted unique platforms")
    for row in rows:
        binding = platform_bindings(root, subject, row["platform"])
        if any(row[key] != value for key, value in binding.items()):
            raise ValueError("Platform subject binding mismatch: " + row["platform"])
        # Literal-Z RFC3339: Python 3.8/3.9 fromisoformat rejects "Z" forms.
        _require_rfc3339_utc(row["runAt"])
        if any(value != "passed" for value in row["staticResults"].values()):
            raise ValueError("All platform static checks must pass")
        if row["runtimeStatus"] == "failed":
            raise ValueError("Executed failed runtime probe blocks support")
        if row["runtimeStatus"] == "unverified-no-certified-host":
            if row["platform"] == "kilo" or row["host"] is not None or row["probes"] or not row["reason"]:
                raise ValueError("Invalid unverified host status; Kilo certification is required")
            continue
        host = row["host"]
        if host is None or row["reason"] or host["pinnedVersion"] != host["observedVersion"] or host["pinnedSha256"] != host["observedSha256"]:
            raise ValueError("Certified host version/hash mismatch")
        if [probe["name"] for probe in row["probes"]] != list(PROBE_CASES):
            raise ValueError("Every exact probe is required in contract order")
        for probe in row["probes"]:
            validate_probe(probe)
