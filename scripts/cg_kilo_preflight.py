#!/usr/bin/env python3
"""Validate and launch the certified, contained Kilo project host.

The Kilo editor extension can discover compatible skills outside a project. This
module keeps the containment decision in one stdlib-only implementation so the
Windows and POSIX launchers share the same status codes and remediation text.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Optional, Sequence


CONTAINMENT_ENVIRONMENT = "KILO_DISABLE_EXTERNAL_SKILLS"
SUPPORTED_KILO_VERSIONS = frozenset({"7.4.20", "7.4.21", "7.4.22"})
REQUIRED_LOCAL_ROOTS = (
    ".kilo/commands",
    ".kilo/skills",
    ".kilo/agents",
    ".kilo/instructions",
    ".kilo/shared",
)
REPARSE_POINT_FLAG = 0x400
MANAGED_COPY_MARKER = ".compound-gpid-managed-copy.json"
MAX_HOST_OUTPUT_BYTES = 2 * 1024 * 1024
VERSION_PATTERN = re.compile(r"(?<!\d)(\d+\.\d+\.\d+)(?!\d)")
COMPATIBILITY_ROOTS = frozenset({".agents", "agents", ".claude", "claude"})

EXIT_OK = 0
EXIT_CONFIGURATION = 2
EXIT_HOST_UNAVAILABLE = 3
EXIT_CONTAINMENT = 4
EXIT_HOST_SCHEMA = 5


class PreflightStatus:
    """Stable machine-readable status identifiers."""

    OK = "ok"
    NO_COEXISTENCE = "ok-no-coexistence"
    MISSING_KILO = "missing-kilo"
    UNSUPPORTED_VERSION = "unsupported-kilo-version"
    LOCAL_PROJECTION_MISSING = "local-projection-missing"
    LOCAL_PROJECTION_INVALID = "local-projection-invalid"
    LOCAL_CONTENT_INVALID = "local-content-invalid"
    HOST_COMMAND_ERROR = "host-command-error"
    HOST_SCHEMA_ERROR = "host-schema-error"
    LOCAL_INVENTORY_MISSING = "local-inventory-missing"
    CONTAINMENT_UNHONORED = "containment-unhonored"


@dataclass(frozen=True)
class InventorySummary:
    """Safe summary of a Kilo skill inventory without skill bodies."""

    names: tuple[str, ...] = ()
    locations: tuple[str, ...] = ()
    records: tuple[tuple[str, str], ...] = ()
    external_compatibility_locations: tuple[str, ...] = ()


@dataclass(frozen=True)
class PreflightResult:
    """Typed result returned by validation and consumed by launchers."""

    status: str
    exit_code: int
    message: str
    remediation: str
    project_root: str
    kilo_executable: Optional[str] = None
    kilo_version: Optional[str] = None
    kilo_executable_sha256: Optional[str] = None
    codex_root_present: bool = False
    claude_root_present: bool = False
    certified_launch_required: bool = False
    direct_launch_supported: bool = True
    certified_command: str = "cg-kilo"
    local_skill_names: tuple[str, ...] = ()
    inventory: InventorySummary = field(default_factory=InventorySummary)
    containment_environment: Optional[str] = None
    host_evidence: str = "unavailable"

    def as_json(self) -> dict[str, Any]:
        """Return a JSON-safe dictionary with deterministic nested values."""
        return {
            "status": self.status,
            "exit_code": self.exit_code,
            "message": self.message,
            "remediation": self.remediation,
            "project_root": self.project_root,
            "kilo_executable": self.kilo_executable,
            "kilo_executable_sha256": self.kilo_executable_sha256,
            "kilo_version": self.kilo_version,
            "codex_root_present": self.codex_root_present,
            "claude_root_present": self.claude_root_present,
            "certified_launch_required": self.certified_launch_required,
            "direct_launch_supported": self.direct_launch_supported,
            "certified_command": self.certified_command,
            "local_skill_names": list(self.local_skill_names),
            "inventory": {
                "names": list(self.inventory.names),
                "locations": list(self.inventory.locations),
                "records": [list(record) for record in self.inventory.records],
                "external_compatibility_locations": list(
                    self.inventory.external_compatibility_locations
                ),
            },
            "containment_environment": self.containment_environment,
            "host_evidence": self.host_evidence,
        }


def _normalise_path(path: str) -> str:
    """Normalise a path for case-insensitive inventory comparisons."""
    return path.replace("\\", "/").rstrip("/").casefold()


def _is_reparse_point(path: Path) -> bool:
    """Return whether ``path`` is a symlink or Windows reparse point."""
    if path.is_symlink():
        return True
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return True
    return bool(attributes & REPARSE_POINT_FLAG)


def _iter_regular_files(root: Path) -> Iterable[Path]:
    """Walk a local projection without following links or reparse points."""
    pending = [root]
    while pending:
        current = pending.pop()
        try:
            entries = list(os.scandir(current))
        except OSError as exc:
            raise OSError(f"cannot scan Kilo projection directory {current}: {exc}") from exc
        for entry in entries:
            item = Path(entry.path)
            if _is_reparse_point(item):
                yield item
                continue
            if entry.is_dir(follow_symlinks=False):
                pending.append(item)
            elif entry.is_file(follow_symlinks=False):
                yield item


def _validate_frontmatter(path: Path, required_fields: Sequence[str]) -> Optional[str]:
    """Validate the minimal Kilo Markdown frontmatter contract."""
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return f"cannot read {path}: {exc}"
    if raw.startswith(b"\xef\xbb\xbf"):
        return f"{path} contains a UTF-8 BOM"
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return f"{path} is not valid UTF-8: {exc}"
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return f"{path} is missing a YAML frontmatter opening delimiter"
    try:
        closing = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return f"{path} is missing a YAML frontmatter closing delimiter"
    fields = {}
    for line in lines[1:closing]:
        if not line.strip():
            continue
        # Kilo skills legitimately use folded/multiline scalar values. Only
        # top-level ``key:`` lines contribute required fields; indented lines
        # are continuation content and are intentionally left to Kilo's own
        # schema validator.
        field_match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*)\s*:", line)
        if field_match:
            fields[field_match.group(1)] = line[field_match.end() :].strip()
    for required in required_fields:
        if not fields.get(required):
            return f"{path} frontmatter is missing '{required}'"
    return None


def _read_managed_relative_files(
    root: Path, expected_source: str
) -> tuple[bool, Optional[dict[str, str]], Optional[str]]:
    """Read a valid copy-directory marker when one is present."""
    marker = root / MANAGED_COPY_MARKER
    if not marker.exists():
        return False, None, None
    if not marker.is_file() or _is_reparse_point(marker):
        return True, None, f"managed-copy marker is not a regular file: {marker}"
    try:
        raw = marker.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return True, None, f"invalid managed-copy marker {marker}: {exc}"
    if not isinstance(data, dict) or data.get("schemaVersion") != 1:
        return True, None, f"managed-copy marker has unsupported schema: {marker}"
    if data.get("source") != expected_source:
        return True, None, f"managed-copy marker source does not match {expected_source}: {marker}"
    files = data.get("files")
    if not isinstance(files, dict) or not files:
        return True, None, f"managed-copy marker has no managed files: {marker}"
    result: dict[str, str] = {}
    for relative, checksum in files.items():
        relative_text = str(relative).replace("\\", "/")
        checksum_text = str(checksum).casefold()
        if (
            not relative_text
            or relative_text == MANAGED_COPY_MARKER
            or any(part in {"", ".", ".."} for part in relative_text.split("/"))
            or not re.fullmatch(r"[0-9a-f]{64}", checksum_text)
        ):
            return True, None, f"managed-copy marker has an unsafe entry: {marker}"
        result[relative_text] = checksum_text
    return True, result, None


def _sha256(path: Path) -> str:
    """Return a file's lowercase SHA-256 digest."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_local_projection(project_root: Path) -> tuple[str, tuple[str, ...], str]:
    """Validate project-local Kilo files and return status, names, detail."""
    missing = [root for root in REQUIRED_LOCAL_ROOTS if not (project_root / root).is_dir()]
    if missing:
        return (
            PreflightStatus.LOCAL_PROJECTION_MISSING,
            (),
            "Missing project-local Kilo roots: " + ", ".join(missing),
        )

    for root_name in REQUIRED_LOCAL_ROOTS:
        root = project_root / root_name
        marker_present, managed_files, marker_error = _read_managed_relative_files(
            root, root_name
        )
        if marker_error:
            return PreflightStatus.LOCAL_PROJECTION_INVALID, (), marker_error
        if _is_reparse_point(root):
            return (
                PreflightStatus.LOCAL_PROJECTION_INVALID,
                (),
                f"Project-local Kilo root is a link or reparse point: {root_name}",
            )
        for item in _iter_regular_files(root):
            if _is_reparse_point(item):
                return (
                    PreflightStatus.LOCAL_PROJECTION_INVALID,
                    (),
                    f"Project-local Kilo projection contains a link or reparse point: {item}",
                )
            if managed_files is not None:
                relative = item.relative_to(root).as_posix()
                if relative not in managed_files:
                    continue
                if _sha256(item) != managed_files[relative]:
                    continue
            elif root_name in {".kilo/agents", ".kilo/commands"}:
                # A marker-less directory may contain user-owned agents. The
                # linker performs its baseline sync first; managed files are
                # validated on the next pass once the marker exists.
                continue
            if item.suffix.lower() not in {".md", ".mdc"}:
                continue
            if item.name == "SKILL.md":
                error = _validate_frontmatter(item, ("name", "description"))
                if error:
                    return PreflightStatus.LOCAL_CONTENT_INVALID, (), error
            elif root_name == ".kilo/agents":
                error = _validate_frontmatter(item, ("description", "mode"))
                if error:
                    return PreflightStatus.LOCAL_CONTENT_INVALID, (), error
            elif root_name == ".kilo/commands" and item.name.startswith("cg-"):
                error = _validate_frontmatter(item, ("description",))
                if error:
                    return PreflightStatus.LOCAL_CONTENT_INVALID, (), error

    skills_root = project_root / ".kilo/skills"
    skill_files = sorted(skills_root.glob("*/SKILL.md"))
    _marker_present, managed_skill_files, marker_error = _read_managed_relative_files(
        skills_root, ".kilo/skills"
    )
    if marker_error:
        return PreflightStatus.LOCAL_PROJECTION_INVALID, (), marker_error
    if managed_skill_files is not None:
        skill_files = [
            path
            for path in skill_files
            if path.relative_to(skills_root).as_posix() in managed_skill_files
            and _sha256(path)
            == managed_skill_files[path.relative_to(skills_root).as_posix()]
        ]
    if not skill_files:
        return (
            PreflightStatus.LOCAL_PROJECTION_MISSING,
            (),
            "Project-local .kilo/skills contains no SKILL.md files",
        )
    skill_names = tuple(sorted(path.parent.name for path in skill_files))
    return PreflightStatus.OK, skill_names, "project-local Kilo projection is valid"


def _has_compatibility_root(location: str) -> bool:
    """Return whether an inventory path is under a Codex/Claude skill root."""
    parts = [part for part in re.split(r"[\\/]+", location.casefold()) if part]
    for index, part in enumerate(parts[:-1]):
        if part in COMPATIBILITY_ROOTS and parts[index + 1] == "skills":
            return True
    return False


def summarise_inventory(payload: Any) -> InventorySummary:
    """Parse Kilo's JSON inventory without retaining skill body content."""
    if not isinstance(payload, list):
        raise ValueError("Kilo debug skill output must be a JSON array")
    names: set[str] = set()
    locations: set[str] = set()
    records: set[tuple[str, str]] = set()
    external: set[str] = set()
    for record in payload:
        if not isinstance(record, dict):
            raise ValueError("Kilo debug skill output contains a non-object record")
        name = record.get("name")
        location = record.get("location")
        if not isinstance(name, str) or not name:
            raise ValueError("Kilo debug skill record has no string name")
        if not isinstance(location, str) or not location:
            raise ValueError(f"Kilo skill record '{name}' has no string location")
        names.add(name)
        locations.add(location)
        records.add((name, location))
        if _has_compatibility_root(location):
            external.add(location)
    return InventorySummary(
        names=tuple(sorted(names)),
        locations=tuple(sorted(locations, key=_normalise_path)),
        records=tuple(sorted((name, location) for name, location in records)),
        external_compatibility_locations=tuple(sorted(external, key=_normalise_path)),
    )


def _candidate_kilo_executables(explicit: Optional[str] = None) -> list[Path]:
    """Return unique executable candidates in deterministic order."""
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    for name in ("kilo.exe", "kilo"):
        resolved = shutil.which(name)
        if resolved:
            candidates.append(Path(resolved))

    home = Path.home()
    extension_roots = (
        home / ".vscode/extensions",
        home / ".vscode-insiders/extensions",
        home / ".positron/extensions",
    )
    executable_name = "kilo.exe" if os.name == "nt" else "kilo"
    for extension_root in extension_roots:
        if extension_root.is_dir():
            candidates.extend(sorted(
                extension_root.glob(f"kilocode.kilo-code-*/bin/{executable_name}"),
                key=lambda path: (_normalise_path(str(path)), str(path)),
            ))

    result: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
        except OSError:
            continue
        key = _normalise_path(str(resolved))
        if key in seen or not resolved.is_file() or _is_reparse_point(resolved):
            continue
        seen.add(key)
        result.append(resolved)
    ordered = sorted(result, key=lambda path: (_normalise_path(str(path)), str(path)))
    if explicit:
        explicit_key = _normalise_path(str(Path(explicit).expanduser().resolve()))
        ordered.sort(key=lambda path: 0 if _normalise_path(str(path)) == explicit_key else 1)
    return ordered


def resolve_kilo_executable(explicit: Optional[str] = None) -> Optional[Path]:
    """Resolve the first available Kilo executable without changing PATH."""
    candidates = _candidate_kilo_executables(explicit)
    for candidate in candidates:
        version, _error = _read_version(candidate, Path.cwd())
        if version in SUPPORTED_KILO_VERSIONS:
            return candidate
    return candidates[0] if candidates else None


def _run_host_command(
    executable: Path,
    project_root: Path,
    arguments: Sequence[str],
    environment: Optional[dict[str, str]] = None,
) -> tuple[Optional[str], Optional[str], Optional[int]]:
    """Run a read-only Kilo command and return stdout, stderr, exit code."""
    process: Optional[subprocess.Popen[str]] = None
    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    stdout_size = 0
    stderr_size = 0

    def read_stream(stream: Any, parts: list[str], size_box: list[int]) -> None:
        nonlocal process
        try:
            while True:
                chunk = stream.read(8192)
                if not chunk:
                    break
                encoded_size = len(chunk.encode("utf-8", errors="replace"))
                remaining = MAX_HOST_OUTPUT_BYTES - size_box[0]
                if remaining <= 0:
                    if process is not None:
                        process.kill()
                    break
                if encoded_size > remaining:
                    parts.append(chunk.encode("utf-8", errors="replace")[:remaining].decode("utf-8", errors="ignore"))
                    size_box[0] = MAX_HOST_OUTPUT_BYTES + 1
                    if process is not None:
                        process.kill()
                    break
                parts.append(chunk)
                size_box[0] += encoded_size
        finally:
            stream.close()

    try:
        process = subprocess.Popen(
            [str(executable), *arguments],
            cwd=str(project_root),
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert process.stdout is not None
        assert process.stderr is not None
        stdout_box = [0]
        stderr_box = [0]
        stdout_thread = threading.Thread(
            target=read_stream, args=(process.stdout, stdout_parts, stdout_box), daemon=True
        )
        stderr_thread = threading.Thread(
            target=read_stream, args=(process.stderr, stderr_parts, stderr_box), daemon=True
        )
        stdout_thread.start()
        stderr_thread.start()
        return_code = process.wait(timeout=45)
        stdout_thread.join(timeout=5)
        stderr_thread.join(timeout=5)
        stdout_size = stdout_box[0]
        stderr_size = stderr_box[0]
        if stdout_size > MAX_HOST_OUTPUT_BYTES or stderr_size > MAX_HOST_OUTPUT_BYTES:
            return "".join(stdout_parts), "host output exceeded the bounded limit", return_code
        return "".join(stdout_parts), "".join(stderr_parts), return_code
    except (OSError, subprocess.TimeoutExpired) as exc:
        if process is not None:
            process.kill()
            process.wait()
        return None, type(exc).__name__, None


def _read_version(executable: Path, project_root: Path) -> tuple[Optional[str], Optional[str]]:
    """Read and normalize the Kilo executable version."""
    stdout, stderr, return_code = _run_host_command(executable, project_root, ("--version",))
    if return_code != 0 or stdout is None:
        return None, "Kilo version command failed"
    match = VERSION_PATTERN.search(stdout)
    if not match:
        return None, "Kilo version output was not recognized"
    return match.group(1), None


def _file_sha256(path: Path) -> Optional[str]:
    """Return an executable digest when it can be read safely."""
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _inventory(
    executable: Path,
    project_root: Path,
    *,
    contained: bool,
) -> tuple[Optional[InventorySummary], Optional[str], Optional[str]]:
    """Collect and summarize the Kilo skill inventory."""
    environment = os.environ.copy()
    if contained:
        environment[CONTAINMENT_ENVIRONMENT] = "1"
    else:
        environment.pop(CONTAINMENT_ENVIRONMENT, None)
    stdout, _stderr, return_code = _run_host_command(
        executable, project_root, ("debug", "skill"), environment
    )
    if return_code != 0 or stdout is None:
        return None, "command", "Kilo skill inventory command failed"
    if _stderr == "host output exceeded the bounded limit" or len(stdout.encode("utf-8", errors="replace")) > MAX_HOST_OUTPUT_BYTES:
        return None, "output", "Kilo skill inventory exceeded the bounded output limit"
    try:
        payload = json.loads(stdout)
        return summarise_inventory(payload), None, None
    except json.JSONDecodeError as exc:
        return None, "syntax", f"Kilo skill inventory was not valid JSON: {exc}"
    except (ValueError, RecursionError) as exc:
        return None, "schema", f"Kilo skill inventory failed schema validation: {exc}"


def _result(
    status: str,
    exit_code: int,
    message: str,
    remediation: str,
    project_root: Path,
    **kwargs: Any,
) -> PreflightResult:
    """Construct a result with common launch-policy fields."""
    return PreflightResult(
        status=status,
        exit_code=exit_code,
        message=message,
        remediation=remediation,
        project_root=str(project_root),
        **kwargs,
    )


def run_preflight(
    project_root: Path,
    *,
    kilo_executable: Optional[str] = None,
    require_host_inventory: bool = True,
    force_certified_launch: bool = False,
    validate_projection: bool = True,
) -> PreflightResult:
    """Validate one project and the installed Kilo host.

    Args:
        project_root: Project directory containing the local Kilo projection.
        kilo_executable: Optional explicit executable path, primarily for tests.
        require_host_inventory: Whether the Kilo skill inventory must be queried.
        force_certified_launch: Require containment even before a compatibility
            root has been materialized.
        validate_projection: Whether to validate the project-local Kilo
            files before querying the host. Host-only checks set this false.

    Returns:
        A typed result suitable for JSON output or launcher diagnostics.

    Example:
        ``result = run_preflight(Path.cwd())``
    """
    try:
        root = project_root.expanduser().resolve(strict=True)
    except OSError as exc:
        return _result(
            PreflightStatus.LOCAL_PROJECTION_INVALID,
            EXIT_CONFIGURATION,
            f"Project root cannot be resolved: {exc}",
            "Run cg-kilo from the project root or pass an existing project path.",
            project_root,
        )
    if not root.is_dir():
        return _result(
            PreflightStatus.LOCAL_PROJECTION_INVALID,
            EXIT_CONFIGURATION,
            "Project root is not a directory.",
            "Run cg-kilo from the project root or pass an existing project path.",
            root,
        )

    codex_root = root / ".agents/skills"
    claude_root = root / ".claude/skills"
    codex_present = codex_root.is_dir()
    claude_present = claude_root.is_dir()
    certified_required = force_certified_launch or codex_present or claude_present
    direct_supported = not certified_required

    if validate_projection:
        try:
            projection_status, local_skill_names, projection_detail = validate_local_projection(root)
        except OSError as exc:
            projection_status, local_skill_names, projection_detail = (
                PreflightStatus.LOCAL_PROJECTION_INVALID,
                (),
                f"Kilo projection could not be inspected safely: {exc}",
            )
        if projection_status != PreflightStatus.OK:
            return _result(
                projection_status,
                EXIT_CONFIGURATION,
                projection_detail,
                "Run cg-link --platforms kilo to recreate a project-local Kilo copy, "
                "then fix any invalid UTF-8 or frontmatter before retrying.",
                root,
                codex_root_present=codex_present,
                claude_root_present=claude_present,
                certified_launch_required=certified_required,
                direct_launch_supported=direct_supported,
                local_skill_names=local_skill_names,
            )
    else:
        local_skill_names = ()

    if not require_host_inventory:
        return _result(
            PreflightStatus.OK if certified_required else PreflightStatus.NO_COEXISTENCE,
            EXIT_OK,
            "Project-local Kilo projection is valid; host inventory check was not requested.",
            "",
            root,
            codex_root_present=codex_present,
            claude_root_present=claude_present,
            certified_launch_required=certified_required,
            direct_launch_supported=direct_supported,
            local_skill_names=local_skill_names,
            containment_environment=CONTAINMENT_ENVIRONMENT if certified_required else None,
            host_evidence="not-run",
        )

    executable = resolve_kilo_executable(kilo_executable)
    if executable is None:
        return _result(
            PreflightStatus.MISSING_KILO,
            EXIT_HOST_UNAVAILABLE,
            "No supported Kilo executable was found on PATH or in the installed editor extensions.",
            "Install or enable the Kilo editor extension, then rerun cg-kilo. "
            "Combined Kilo+Codex use is blocked until this certified host is available.",
            root,
            codex_root_present=codex_present,
            claude_root_present=claude_present,
            certified_launch_required=certified_required,
            direct_launch_supported=direct_supported,
            local_skill_names=local_skill_names,
        )

    version, version_error = _read_version(executable, root)
    executable_sha256 = _file_sha256(executable)
    if version_error or version not in SUPPORTED_KILO_VERSIONS:
        detail = version_error or f"Kilo version {version} is not in the certified host set."
        return _result(
            PreflightStatus.UNSUPPORTED_VERSION,
            EXIT_HOST_UNAVAILABLE,
            detail,
            "Use a certified Kilo host version and rerun cg-kilo. "
            "Direct launches remain unsupported for a combined project.",
            root,
            kilo_executable=str(executable),
            kilo_version=version,
            kilo_executable_sha256=executable_sha256,
            codex_root_present=codex_present,
            claude_root_present=claude_present,
            certified_launch_required=certified_required,
            direct_launch_supported=direct_supported,
            local_skill_names=local_skill_names,
        )

    plain_inventory, plain_reason, plain_error = _inventory(executable, root, contained=False)
    if plain_error and certified_required:
        plain_inventory = None
    elif plain_error:
        status = (
            PreflightStatus.HOST_SCHEMA_ERROR
            if plain_reason in {"syntax", "schema", "output"}
            else PreflightStatus.HOST_COMMAND_ERROR
        )
        return _result(
            status,
            EXIT_HOST_SCHEMA if status == PreflightStatus.HOST_SCHEMA_ERROR else EXIT_HOST_UNAVAILABLE,
            plain_error,
            "Inspect Kilo's host diagnostics separately from local Markdown validation. "
            "A parser/schema error is not evidence of external-root containment.",
            root,
            kilo_executable=str(executable),
            kilo_version=version,
            kilo_executable_sha256=executable_sha256,
            codex_root_present=codex_present,
            claude_root_present=claude_present,
            certified_launch_required=certified_required,
            direct_launch_supported=direct_supported,
            local_skill_names=local_skill_names,
        )
    containment_required = certified_required or bool(
        plain_inventory and plain_inventory.external_compatibility_locations
    )
    if containment_required:
        contained_inventory, contained_reason, contained_error = _inventory(
            executable, root, contained=True
        )
        if contained_error:
            status = (
                PreflightStatus.HOST_SCHEMA_ERROR
                if contained_reason in {"syntax", "schema", "output"}
                else PreflightStatus.HOST_COMMAND_ERROR
            )
            return _result(
                status,
                EXIT_HOST_SCHEMA if status == PreflightStatus.HOST_SCHEMA_ERROR else EXIT_HOST_UNAVAILABLE,
                contained_error,
                "The certified containment check could not complete. "
                "Do not use a direct Kilo launch with Codex or Claude roots present.",
                root,
                kilo_executable=str(executable),
                kilo_version=version,
                kilo_executable_sha256=executable_sha256,
                codex_root_present=codex_present,
                claude_root_present=claude_present,
                certified_launch_required=certified_required,
                direct_launch_supported=direct_supported,
                local_skill_names=local_skill_names,
                inventory=plain_inventory or InventorySummary(),
            )
        assert contained_inventory is not None
        if contained_inventory.external_compatibility_locations:
            return _result(
                PreflightStatus.CONTAINMENT_UNHONORED,
                EXIT_CONTAINMENT,
                "Kilo still discovered external Codex/Claude skill roots with the "
                f"{CONTAINMENT_ENVIRONMENT}=1 child-process control.",
                "Use the certified cg-kilo launcher with a supported Kilo version, "
                "or upgrade/report the incompatible host. Direct editor/CLI launches "
                "are unsupported while compatibility roots are present.",
                root,
                kilo_executable=str(executable),
                kilo_version=version,
                kilo_executable_sha256=executable_sha256,
                codex_root_present=codex_present,
                claude_root_present=claude_present,
                certified_launch_required=certified_required,
                direct_launch_supported=False,
                local_skill_names=local_skill_names,
                inventory=contained_inventory,
                containment_environment=CONTAINMENT_ENVIRONMENT,
            )
        inventory = contained_inventory
        host_evidence = "verified-contained"
        certified_required = True
        direct_supported = False
    else:
        if plain_inventory is None:
            return _result(
                PreflightStatus.HOST_SCHEMA_ERROR,
                EXIT_HOST_SCHEMA,
                "Kilo returned no usable skill inventory.",
                "Inspect Kilo's host diagnostics separately from local Markdown validation.",
                root,
                kilo_executable=str(executable),
                kilo_version=version,
                codex_root_present=codex_present,
                claude_root_present=claude_present,
                certified_launch_required=certified_required,
                direct_launch_supported=direct_supported,
                local_skill_names=local_skill_names,
            )
        inventory = plain_inventory
        host_evidence = "verified-local"

    expected_root = _normalise_path(str((root / ".kilo/skills").resolve())) + "/"
    local_records: dict[str, list[str]] = {}
    for name, location in inventory.records:
        normalized_location = _normalise_path(location)
        local_records.setdefault(name, []).append(normalized_location)
    missing_local = []
    for name in local_skill_names:
        expected_location = f"{expected_root}{name.casefold()}/skill.md"
        matches = [
            location
            for location in local_records.get(name, [])
            if location == expected_location
        ]
        if len(matches) != 1:
            missing_local.append(name)
    if missing_local:
        return _result(
            PreflightStatus.LOCAL_INVENTORY_MISSING,
            EXIT_HOST_SCHEMA,
            "Kilo did not advertise valid local skills: " + ", ".join(missing_local),
            "Treat this as a local content or upstream Kilo schema problem, not as "
            "external discovery. Validate frontmatter and check the certified host version.",
            root,
            kilo_executable=str(executable),
            kilo_version=version,
            kilo_executable_sha256=executable_sha256,
            codex_root_present=codex_present,
            claude_root_present=claude_present,
            certified_launch_required=certified_required,
            direct_launch_supported=direct_supported,
            local_skill_names=local_skill_names,
            inventory=inventory,
            containment_environment=CONTAINMENT_ENVIRONMENT if certified_required else None,
            host_evidence=host_evidence,
        )

    status = PreflightStatus.OK if certified_required else PreflightStatus.NO_COEXISTENCE
    message = (
        "Certified Kilo containment verified: local .kilo/skills is available and "
        "external compatibility roots are excluded."
        if certified_required
        else "Kilo host and project-local projection verified; no Codex/Claude coexistence root is present."
    )
    return _result(
        status,
        EXIT_OK,
        message,
        "",
        root,
        kilo_executable=str(executable),
        kilo_version=version,
        kilo_executable_sha256=executable_sha256,
        codex_root_present=codex_present,
        claude_root_present=claude_present,
        certified_launch_required=certified_required,
        direct_launch_supported=direct_supported,
        local_skill_names=local_skill_names,
        inventory=inventory,
        containment_environment=CONTAINMENT_ENVIRONMENT if certified_required else None,
        host_evidence=host_evidence,
    )


def _infer_project_root(arguments: Sequence[str]) -> tuple[Path, Optional[int]]:
    """Infer a project path from Kilo's positional arguments."""
    for index, argument in enumerate(arguments):
        if not argument or argument == "--" or argument.startswith("-"):
            continue
        candidate = Path(argument).expanduser()
        if candidate.is_dir():
            return candidate.resolve(), index
    return Path.cwd().resolve(), None


def _emit_result(result: PreflightResult, json_output: bool) -> None:
    """Emit a bounded human or machine-readable result."""
    if json_output:
        sys.stdout.write(json.dumps(result.as_json(), sort_keys=True) + "\n")
        return
    prefix = "PASS" if result.exit_code == EXIT_OK else "BLOCKED"
    sys.stdout.write(f"{prefix}: {result.status} - {result.message}\n")
    if result.certified_launch_required:
        sys.stdout.write(
            "Certified command: cg-kilo (direct Kilo editor/CLI launches are unsupported "
            "for this combined project)\n"
        )
    if result.remediation:
        sys.stdout.write(f"Remediation: {result.remediation}\n")


def _parse_arguments(argv: Sequence[str]) -> tuple[argparse.Namespace, list[str]]:
    """Parse preflight options while preserving all Kilo launch arguments."""
    options = list(argv)
    launch_arguments: list[str] = []
    if "--" in options:
        separator = options.index("--")
        launch_arguments = options[separator + 1 :]
        options = options[:separator]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="project root; defaults to the current directory")
    parser.add_argument("--kilo-executable", help="explicit Kilo executable path")
    parser.add_argument("--json", action="store_true", help="emit a bounded JSON result")
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="validate only the project-local projection; do not query Kilo",
    )
    parser.add_argument(
        "--require-coexistence",
        action="store_true",
        help="require the certified containment path before compatibility roots exist",
    )
    parser.add_argument(
        "--host-only",
        action="store_true",
        help="verify the Kilo host containment capability without requiring a local projection",
    )
    parser.add_argument("--launch", action="store_true", help="launch Kilo after a passing preflight")
    return parser.parse_args(options), launch_arguments


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run preflight and optionally launch Kilo."""
    args, launch_arguments = _parse_arguments(argv if argv is not None else sys.argv[1:])
    root, project_argument_index = _infer_project_root(launch_arguments)
    if args.root:
        root = Path(args.root).expanduser().resolve()
    if args.local_only and (args.require_coexistence or args.host_only):
        sys.stderr.write("ERROR: --local-only cannot be combined with --require-coexistence or --host-only.\n")
        return EXIT_CONFIGURATION
    result = run_preflight(
        root,
        kilo_executable=args.kilo_executable,
        require_host_inventory=not args.local_only,
        force_certified_launch=args.require_coexistence,
        validate_projection=not args.host_only,
    )
    _emit_result(result, args.json)
    if result.exit_code != EXIT_OK or not args.launch:
        return result.exit_code
    if not result.kilo_executable:
        return EXIT_HOST_UNAVAILABLE

    child_arguments = list(launch_arguments)
    if project_argument_index is not None and not Path(child_arguments[project_argument_index]).is_absolute():
        child_arguments[project_argument_index] = str(root)
    child_environment = os.environ.copy()
    if result.certified_launch_required:
        child_environment[CONTAINMENT_ENVIRONMENT] = "1"
    try:
        completed = subprocess.run(
            [result.kilo_executable, *child_arguments],
            cwd=str(root),
            env=child_environment,
            check=False,
        )
    except OSError as exc:
        sys.stderr.write(f"ERROR: certified Kilo launch failed: {exc}\n")
        return EXIT_HOST_UNAVAILABLE
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
