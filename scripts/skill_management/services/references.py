"""Deterministic source-neutral lifecycle reference inventory and classification."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import secure_fs

from skill_management import contracts
from skill_management.services import bundles, registry


MAX_REFERENCE_FILE_BYTES = 4 * 1024 * 1024
_REPARSE_POINT_FLAG = 0x400
_TEXT_SUFFIXES = frozenset(
    {
        ".cmd",
        ".do",
        ".html",
        ".js",
        ".json",
        ".md",
        ".mjs",
        ".ps1",
        ".py",
        ".r",
        ".sh",
        ".toml",
        ".ts",
        ".tsx",
        ".txt",
        ".yaml",
        ".yml",
    }
)
_EXCLUDED_PREFIXES = (
    ".git/",
    ".pytest_cache/",
    ".compound-gpid/quarantine/",
    ".compound-gpid/skill-plans/",
    ".compound-gpid/skill-transactions/",
    ".compound-gpid/vendor-reviews/",
)
_FENCE_CONTRACT_PREFIXES = (
    ".github/prompts/",
    ".github/agents/",
    ".github/instructions/",
    ".github/skills/",
    ".agents/commands/",
    ".agents/agents/",
    ".agents/instructions/",
    ".agents/skills/",
    ".claude/commands/",
    ".claude/agents/",
    ".claude/instructions/",
    ".claude/skills/",
    ".kilo/commands/",
    ".kilo/agents/",
    ".kilo/instructions/",
    ".kilo/skills/",
    ".opencode/commands/",
    ".opencode/agents/",
    ".opencode/instructions/",
    ".opencode/skills/",
)


class ReferenceScanError(ValueError):
    """Raised when a complete safe reference inventory cannot be formed."""


@dataclass(frozen=True)
class ReferenceTarget:
    """One immutable skill identity and the aliases that can reference it."""

    identifier: str
    origin: str
    source_path: str
    capability: str
    provenance_path: str
    source_root: Path

    @property
    def aliases(self) -> Tuple[str, ...]:
        """Return deterministic textual aliases that identify this skill."""
        values = {self.identifier, self.source_path, f"{self.source_path}/SKILL.md"}
        if self.origin == "project-imported" and self.capability:
            values.add(self.capability)
        return tuple(sorted(values, key=lambda item: (-len(item), item)))


@dataclass(frozen=True)
class ReferenceRecord:
    """One classified textual reference with stable source coordinates."""

    skill_id: str
    root: str
    path: str
    line: int
    classification: str
    category: str
    alias: str

    def to_dict(self) -> Dict[str, Any]:
        """Return the operation-contract representation."""
        return {
            "skillId": self.skill_id,
            "root": self.root,
            "path": self.path,
            "line": self.line,
            "classification": self.classification,
            "category": self.category,
            "alias": self.alias,
        }


@dataclass(frozen=True)
class ReferenceReport:
    """One complete deterministic reference snapshot."""

    references: Tuple[ReferenceRecord, ...]
    findings: Tuple[contracts.ContractFinding, ...]
    digest: str

    @property
    def active(self) -> Tuple[ReferenceRecord, ...]:
        """Return references that must be zero before destructive removal."""
        return tuple(
            item for item in self.references if item.classification == "active"
        )


@dataclass(frozen=True)
class _Document:
    root: str
    path: str
    content: bytes


def _is_link_or_reparse(metadata: os.stat_result) -> bool:
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & _REPARSE_POINT_FLAG
    )


def _is_text_candidate(relative: str) -> bool:
    path = PurePosixPath(relative)
    if path.suffix.casefold() in _TEXT_SUFFIXES:
        return True
    return bool(path.parts and path.parts[0] == "bin" and not path.suffix)


def _excluded(relative: str) -> bool:
    normalized = relative.replace("\\", "/")
    return "__pycache__" in PurePosixPath(normalized).parts or any(
        normalized.startswith(prefix) for prefix in _EXCLUDED_PREFIXES
    )


def _inventory_root(
    root: Path,
    root_kind: str,
) -> Tuple[List[_Document], List[contracts.ContractFinding]]:
    documents = []  # type: List[_Document]
    findings = []  # type: List[contracts.ContractFinding]
    pending = [Path(root).resolve(strict=True)]
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(str(directory)) as entries:
                ordered = sorted(entries, key=lambda item: item.name, reverse=True)
        except OSError as error:
            raise ReferenceScanError(
                f"Cannot enumerate reference root safely: {directory}: {error}"
            ) from error
        for entry in ordered:
            path = Path(entry.path)
            relative = path.relative_to(root).as_posix()
            if _excluded(relative):
                continue
            try:
                metadata = entry.stat(follow_symlinks=False)
            except OSError as error:
                raise ReferenceScanError(
                    f"Cannot inspect reference candidate safely: {relative}: {error}"
                ) from error
            if _is_link_or_reparse(metadata):
                findings.append(
                    contracts.ContractFinding(
                        relative,
                        "reference.unsafe-entry",
                        "error",
                        "Reference inventory contains a link or reparse point.",
                        "Replace the entry with a confined regular file or directory.",
                    )
                )
                continue
            if stat.S_ISDIR(metadata.st_mode):
                pending.append(path)
                continue
            if not stat.S_ISREG(metadata.st_mode) or not _is_text_candidate(relative):
                continue
            if metadata.st_size > MAX_REFERENCE_FILE_BYTES:
                findings.append(
                    contracts.ContractFinding(
                        relative,
                        "reference.file-size",
                        "error",
                        "Reference candidate exceeds the bounded scan size.",
                        "Reduce the text file below the reference scan byte ceiling.",
                    )
                )
                continue
            try:
                content = secure_fs.secure_read_bytes(
                    root,
                    PurePosixPath(relative),
                    reject_hardlinks=True,
                    max_bytes=MAX_REFERENCE_FILE_BYTES,
                )
                content.decode("utf-8-sig")
            except (OSError, UnicodeError, ValueError) as error:
                findings.append(
                    contracts.ContractFinding(
                        relative,
                        "reference.unreadable",
                        "error",
                        f"Reference candidate is not bounded regular UTF-8 text: {error}",
                        "Replace it with bounded regular UTF-8 text and rerun audit.",
                    )
                )
                continue
            documents.append(_Document(root_kind, relative, content))
    return documents, findings


def _classification(path: str) -> str:
    if path.startswith(".cg-docs/") or path.startswith("releases/"):
        return "historical"
    if path.startswith(".compound-gpid/skill-migrations/") or path == (
        "docs/skills/management/migration.md"
    ):
        return "migration"
    return "active"


def _category(path: str) -> str:
    if path == "roadmap.json":
        return "roadmap"
    if path == "compound-gpid.context.md":
        return "context"
    if path.startswith("adapters/") or path == "AGENTS.md":
        return "adapter"
    if path == "install.ps1" or path.startswith("scripts/install"):
        return "installer"
    if path.startswith(".github/prompts/") or "/commands/" in path:
        return "command"
    if path.startswith(".github/agents/") or "/agents/" in path:
        return "agent"
    if path.startswith(".github/instructions/") or "/instructions/" in path:
        return "instruction"
    if path.endswith("module-registry.json") or path.endswith(
        "project-skill-registry.json"
    ):
        return "registry"
    if path == "compound-gpid.local.md":
        return "config"
    if path.endswith("active-manifest.json"):
        return "manifest"
    if "/contracts/" in path:
        return "contract"
    if "/workflows/" in path:
        return "workflow"
    if "/skills/" in path:
        return "skill-resource"
    if path.startswith("docs/"):
        return "documentation"
    if path.startswith(".cg-docs/") or path.startswith("releases/"):
        return "historical"
    return "runtime"


def _mask_fenced_code(text: str) -> str:
    """Mask fenced content while preserving every source line coordinate."""
    output = []
    fence_character = None  # type: Optional[str]
    fence_length = 0
    for line in text.splitlines(keepends=True):
        match = re.match(r"^[ \t]{0,3}(`{3,}|~{3,})", line)
        if fence_character is None:
            if match:
                fence_character = match.group(1)[0]
                fence_length = len(match.group(1))
                output.append("\n" if line.endswith(("\n", "\r")) else "")
            else:
                output.append(line)
        else:
            output.append("\n" if line.endswith(("\n", "\r")) else "")
            if (
                match
                and match.group(1)[0] == fence_character
                and len(match.group(1)) >= fence_length
            ):
                fence_character = None
                fence_length = 0
    return "".join(output)


def _searchable_text(
    document: _Document,
    target: ReferenceTarget,
    target_source_kind: str,
) -> Optional[str]:
    if document.path == target.provenance_path:
        return None
    if document.root == target_source_kind and document.path == target.source_path:
        return None
    if document.root == target_source_kind and document.path.startswith(
        target.source_path + "/"
    ):
        return None
    try:
        text = document.content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None
    if document.path == registry.PROJECT_REGISTRY_PATH:
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            return text
        records = value.get("records") if isinstance(value, dict) else None
        if isinstance(records, list):
            value["records"] = [
                item
                for item in records
                if not isinstance(item, dict) or item.get("id") != target.identifier
            ]
            text = json.dumps(value, sort_keys=True, ensure_ascii=False)
    if document.path.casefold().endswith((".md", ".markdown")) and any(
        document.path.startswith(prefix) for prefix in _FENCE_CONTRACT_PREFIXES
    ):
        text = _mask_fenced_code(text)
    return text


def _alias_pattern(alias: str) -> re.Pattern[str]:
    escaped = re.escape(alias)
    return re.compile(r"(?<![A-Za-z0-9_-])" + escaped + r"(?![A-Za-z0-9_-])")


def _matches(text: str, aliases: Sequence[str]) -> Iterable[Tuple[int, str]]:
    occupied = []  # type: List[Tuple[int, int]]
    for alias in aliases:
        for match in _alias_pattern(alias).finditer(text):
            span = match.span()
            if any(span[0] < prior[1] and prior[0] < span[1] for prior in occupied):
                continue
            occupied.append(span)
            yield match.start(), alias


def _report(
    records: Sequence[ReferenceRecord],
    findings: Sequence[contracts.ContractFinding],
) -> ReferenceReport:
    ordered_records = tuple(
        sorted(
            set(records),
            key=lambda item: (
                item.skill_id,
                item.classification,
                item.root,
                item.path,
                item.line,
                item.alias,
            ),
        )
    )
    ordered_findings = contracts.sort_findings(findings)
    digest = hashlib.sha256(
        contracts.canonical_json_bytes(
            {
                "references": [item.to_dict() for item in ordered_records],
                "findings": [item.to_dict() for item in ordered_findings],
            }
        )
    ).hexdigest()
    return ReferenceReport(ordered_records, ordered_findings, digest)


def empty_reference_report() -> ReferenceReport:
    """Return the stable digest representation of an empty reference scan."""
    return _report((), ())


def scan_references(
    project_root: Path,
    source_root: Path,
    targets: Sequence[ReferenceTarget],
    *,
    staged: Optional[Mapping[Tuple[str, str], Optional[bytes]]] = None,
) -> ReferenceReport:
    """Scan all bounded repository text once and classify target references.

    Args:
        project_root: Project and runtime root.
        source_root: Canonical source root.
        targets: Immutable skill identities to locate.
        staged: Optional exact future bytes keyed by ``(root, relative path)``.

    Returns:
        Deterministic active, migration, and historical reference report.

    Example:
        ``scan_references(project, source, (target,))``
    """
    project = Path(project_root).resolve(strict=True)
    source = Path(source_root).resolve(strict=True)
    documents, findings = _inventory_root(project, "project")
    if source != project:
        source_documents, source_findings = _inventory_root(source, "source")
        documents.extend(source_documents)
        findings.extend(source_findings)
    by_key = {(item.root, item.path): item for item in documents}
    for key, content in sorted((staged or {}).items()):
        root_kind, relative = key
        if root_kind not in {"project", "source"}:
            raise ReferenceScanError(f"Unknown staged reference root: {root_kind}")
        if content is None:
            by_key.pop(key, None)
        else:
            secure_fs.normalize_relative_path(relative)
            by_key[key] = _Document(root_kind, relative, content)
    records = []  # type: List[ReferenceRecord]
    for document in sorted(by_key.values(), key=lambda item: (item.root, item.path)):
        for target in sorted(targets, key=lambda item: item.identifier):
            target_source_kind = (
                "project"
                if Path(target.source_root).resolve() == project
                else "source"
            )
            text = _searchable_text(document, target, target_source_kind)
            if text is None:
                continue
            for offset, alias in _matches(text, target.aliases):
                records.append(
                    ReferenceRecord(
                        target.identifier,
                        document.root,
                        document.path,
                        text.count("\n", 0, offset) + 1,
                        _classification(document.path),
                        _category(document.path),
                        alias,
                    )
                )
    return _report(records, findings)


def targets_from_snapshot(
    snapshot: registry.CombinedRegistrySnapshot,
) -> Tuple[ReferenceTarget, ...]:
    """Return every current or tombstoned skill identity in one snapshot."""
    rows = {}  # type: Dict[str, ReferenceTarget]
    source = snapshot.canonical.source_root
    for inventory in snapshot.canonical_bundles:
        owner = snapshot.canonical.owner_for_asset(
            f"{inventory.source_path}/SKILL.md"
        )
        capability = snapshot.canonical.capability_for_owner(owner)
        rows[inventory.identifier] = ReferenceTarget(
            inventory.identifier,
            "plugin-canonical",
            inventory.source_path,
            str(capability.get("id", "")) if capability else "",
            (
                f".github/shared/skill-management/provenance/"
                f"{inventory.identifier}.json"
            ),
            source,
        )
    for record in snapshot.project_records:
        identifier = str(record["id"])
        rows[identifier] = ReferenceTarget(
            identifier,
            "project-imported",
            str(record["sourcePath"]),
            str(record["capability"]),
            f"{registry.PROVENANCE_ROOT}/{identifier}.json",
            snapshot.project_root,
        )
    for record in tuple(snapshot.canonical_provenance_records) + tuple(
        snapshot.provenance_records
    ):
        if record.get("lifecycle") != "removed":
            continue
        identifier = str(record["skillId"])
        origin = str(record["origin"])
        if identifier in rows:
            continue
        project_origin = origin == "project-imported"
        rows[identifier] = ReferenceTarget(
            identifier,
            origin,
            (
                f".compound-gpid/skills/{identifier}"
                if project_origin
                else f".github/skills/{identifier}"
            ),
            f"project-skill-{identifier}" if project_origin else "",
            (
                f"{registry.PROVENANCE_ROOT}/{identifier}.json"
                if project_origin
                else (
                    ".github/shared/skill-management/provenance/"
                    f"{identifier}.json"
                )
            ),
            snapshot.project_root if project_origin else source,
        )
    return tuple(rows[identifier] for identifier in sorted(rows))
