"""Pure metadata parsers and complete hashed edit sets; never write source files."""

import hashlib
import re
from dataclasses import dataclass

import tomlkit
from packaging.version import InvalidVersion
from packaging.version import Version as PythonVersion

from cg_release.events import ControllerError
from cg_release.json_edit import edit_json_string
from cg_release.manifest import validate_manifest
from cg_release.models import Changelog, MetadataAdapter, canonical_bytes
from cg_release.policy import safe_path, validate_edit_paths
from cg_release.versions import parse_version

MAX_BLOB_BYTES = 1024 * 1024


@dataclass(frozen=True)
class SourceBlob:
    """Immutable Git blob bytes and mode, e.g. SourceBlob(b'{}', mode='100644')."""

    content: bytes
    mode: str = "100644"

    def __post_init__(self) -> None:
        """Reject nonregular files, invalid UTF-8, and excessive input immediately."""
        if (
            self.mode not in {"100644", "100755"}
            or not isinstance(self.content, bytes)
            or len(self.content) > MAX_BLOB_BYTES
        ):
            raise ControllerError("E_BLOB", "Expected a bounded regular source blob.")
        try:
            self.content.decode("utf-8")
        except UnicodeError:
            raise ControllerError(
                "E_ENCODING", "Metadata must be valid UTF-8."
            ) from None


@dataclass(frozen=True)
class Edit:
    """Validated output bytes and both digests; None input means a new manifest."""

    path: str
    input_digest: str | None
    output_digest: str
    content: bytes
    projection: str | None = None


def project_version(version: str, history: list[str]) -> str:
    """Project SemVer into supported PEP 440, e.g. rc.2 -> rc2.

    Args:
        version: Canonical proposal already checked against SemVer history.
        history: Explicit adopted per-distribution projected history for this line.
    Returns:
        Monotonically increasing PEP 440 value.
    Raises:
        ControllerError: Unsupported channel/build metadata or projection downgrade.
    """
    parsed = parse_version(version)
    core = f"{parsed.major}.{parsed.minor}.{parsed.patch}"
    if parsed.build is not None:
        raise ControllerError(
            "E_PROJECTION", "Python projection does not support build metadata."
        )
    projected = core
    if parsed.prerelease is not None:
        match = re.fullmatch(r"(alpha|beta|rc|dev)\.(0|[1-9][0-9]*)", parsed.prerelease)
        if not match:
            raise ControllerError(
                "E_PROJECTION", "Unsupported Python pre-release representation."
            )
        projected += {"alpha": "a", "beta": "b", "rc": "rc", "dev": ".dev"}[
            match[1]
        ] + match[2]
    try:
        proposal = PythonVersion(projected)
        if any(proposal <= PythonVersion(v) for v in history):
            raise ControllerError(
                "E_PROJECTION_ORDER",
                "Python projection must increase adopted distribution history.",
            )
    except (InvalidVersion, TypeError):
        raise ControllerError(
            "E_PROJECTION_HISTORY", "Invalid adopted Python projection history."
        ) from None
    return projected


def _format_edit(
    adapter: MetadataAdapter, raw: str, version: str, history: list[str]
) -> tuple[str, str]:
    if adapter.kind == "json":
        return edit_json_string(raw, adapter.pointer, version), version
    if adapter.kind == "python-project":
        projected = project_version(version, history)
        try:
            document = tomlkit.parse(raw)
            project = document["project"]
            if (
                not isinstance(project, dict)
                or not isinstance(project.get("version"), str)
                or "version" in project.get("dynamic", [])
            ):
                raise ValueError
            project["version"] = projected
            return tomlkit.dumps(document), projected
        except (ValueError, TypeError, KeyError, tomlkit.exceptions.TOMLKitError):
            raise ControllerError(
                "E_METADATA", "Python metadata requires a static project.version."
            ) from None
    if (
        parse_version(version).prerelease is not None
        or parse_version(version).build is not None
    ):
        raise ControllerError(
            "E_PROJECTION", "R DESCRIPTION supports stable versions only."
        )
    lines, fields, version_index = raw.splitlines(keepends=True), set(), None
    for i, text in enumerate(lines):
        if text.startswith((" ", "\t")):
            if not fields or (version_index is not None and i == version_index + 1):
                raise ControllerError(
                    "E_METADATA", "Invalid DCF continuation or multiline version."
                )
            continue
        match = re.fullmatch(r"([A-Za-z][A-Za-z0-9_.-]*):[^\r\n]*(?:\r?\n)?", text)
        if not match or match[1].casefold() in fields:
            raise ControllerError("E_METADATA", "Expected one unambiguous DCF record.")
        fields.add(match[1].casefold())
        if match[1] == "Version":
            version_index = i
    if version_index is None:
        raise ControllerError("E_METADATA", "DESCRIPTION Version is missing.")
    newline = "\r\n" if lines[version_index].endswith("\r\n") else "\n"
    lines[version_index] = f"Version: {version}{newline}"
    return "".join(lines), version


def proposed_edits(
    adapters: list[MetadataAdapter],
    changelog: Changelog,
    blobs: dict[str, SourceBlob],
    *,
    version: str,
    tag: str,
    line: str,
    source_sha: str,
    policy_digest: str,
    request_id: str,
    notes: str,
    projections_history: dict[str, list[str]],
    outputs: list[str],
) -> tuple[Edit, ...]:
    """Compute all edits from immutable blobs, e.g. JSON version plus changelog.

    Args:
        adapters: Declared format/path/field records; no executable source hooks.
        changelog: One insertion marker.
        blobs: Regular Git blobs at one source commit, never working-tree files.
        version: Canonical SemVer version.
        tag: Exact proposed tag.
        line: Selected release-line ID.
        source_sha: Bound source commit.
        policy_digest: Trusted policy digest.
        request_id: Caller-supplied request identity; preview labels are not receipts.
        notes: Bounded deterministic release notes from committed inventory.
        projections_history: Audited per-path history; explicit empty for bootstrap.
        outputs: Declared build output paths.
    Returns:
        Sorted complete immutable edit tuple with SHA-256 input/output digests.
    Raises:
        ControllerError: Any invalid file, format, alias, projection, or marker.
    """
    parse_version(version)
    if ".release-manifest.json" in blobs:
        validate_manifest(blobs[".release-manifest.json"].content)
    if len(notes.encode("utf-8")) > 65536 or "\x00" in notes:
        raise ControllerError("E_NOTES", "Release notes exceed the supported bound.")
    declared = [a.path for a in adapters] + [changelog.path, ".release-manifest.json"]
    for path in declared:
        safe_path(path)
    validate_edit_paths(adapters, changelog.path)
    if len({p.casefold() for p in blobs}) != len(blobs):
        raise ControllerError("E_PATH", "Source tree has case-fold path collisions.")
    result = []

    def add(path: str, raw: bytes, projection: str | None = None) -> None:
        if len(raw) > MAX_BLOB_BYTES:
            raise ControllerError("E_BLOB", "Proposed metadata exceeds the size limit.")
        prior = blobs.get(path)
        result.append(
            Edit(
                path,
                hashlib.sha256(prior.content).hexdigest() if prior else None,
                hashlib.sha256(raw).hexdigest(),
                raw,
                projection,
            )
        )

    staged = {}
    for adapter in adapters:
        if adapter.path not in blobs:
            raise ControllerError("E_METADATA", "Declared metadata blob is missing.")
        if adapter.kind == "python-project" and adapter.path not in projections_history:
            raise ControllerError(
                "E_PROJECTION_HISTORY",
                "An explicit adopted projection baseline is required.",
            )
        previous = staged.get(
            adapter.path, (blobs[adapter.path].content.decode("utf-8"), None)
        )[0]
        raw, projection = _format_edit(
            adapter, previous, version, projections_history.get(adapter.path, [])
        )
        staged[adapter.path] = (raw, projection)
    for path, (raw, projection) in staged.items():
        add(path, raw.encode("utf-8"), projection)
    if changelog.path not in blobs:
        raise ControllerError("E_METADATA", "Changelog blob is missing.")
    raw = blobs[changelog.path].content.decode("utf-8")
    entry = f"\n\n## {version}\n\n{notes.rstrip()}\n"
    if raw.count(changelog.marker) != 1:
        raise ControllerError(
            "E_CHANGELOG", "Changelog needs exactly one insertion marker."
        )
    if re.search(rf"^## {re.escape(version)}\s*$", raw, re.MULTILINE):
        if entry not in raw:
            raise ControllerError(
                "E_CHANGELOG", "Existing release notes differ from this request."
            )
    else:
        raw = raw.replace(changelog.marker, changelog.marker + entry, 1)
    add(changelog.path, raw.encode("utf-8"))
    manifest = {
        "schema_version": 1,
        "version": version,
        "tag": tag,
        "request_id": request_id,
        "source_sha": source_sha,
        "policy_digest": policy_digest,
        "line": line,
        "projections": {e.path: e.projection for e in result if e.projection},
        "outputs": outputs,
    }
    manifest_bytes = canonical_bytes(manifest) + b"\n"
    validate_manifest(manifest_bytes)
    add(".release-manifest.json", manifest_bytes)
    return tuple(sorted(result, key=lambda item: item.path))
