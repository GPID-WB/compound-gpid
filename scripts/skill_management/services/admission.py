"""Strict shared admission policy for project import and plugin vendoring."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
import stat
import unicodedata
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

import secure_fs

from skill_management import contracts
from skill_management import paths as path_policy
from skill_management.providers.github import AcquisitionLimits
from skill_management.providers.github import AcquiredBundle
from skill_management.services import bundles


POLICY_PATH = PurePosixPath(".github/shared/vendor-policy.json")
_REPARSE_POINT_FLAG = 0x400
_LFS_PREFIX = b"version https://git-lfs.github.com/spec/v1"
_ZERO_WIDTH = "".join(chr(value) for value in (0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF))
_BARE_SECRET = re.compile(
    r"(?i)(?:api[_-]?key|secret|password|token|credential)\s*[:=]\s*[\"']?"
    r"[A-Za-z0-9_./+\-=]{8,}"
)
_REVIEW_SCOPE = re.compile(r"^[a-z][a-z0-9-]*$")


class AdmissionPolicyError(ValueError):
    """Raised when the committed canonical policy is absent or malformed."""


@dataclass(frozen=True, order=True)
class AdmissionFinding:
    """One deterministic admission rejection without candidate content."""

    path: str
    code: str
    message: str


@dataclass(frozen=True)
class AdmissionPolicy:
    """Validated non-overridable project and plugin security policy."""

    allowed_repositories: Tuple[str, ...]
    allowed_roots: Tuple[str, ...]
    max_bundle_bytes: int
    max_files: int
    max_file_bytes: int
    max_metadata_bytes: int
    max_tree_depth: int
    allowed_extensions: Tuple[str, ...]
    blocked_extensions: Tuple[str, ...]
    blocked_names: Tuple[str, ...]
    opaque_extensions: Tuple[str, ...]
    approved_resource_classes: Tuple[str, ...]
    secret_patterns: Tuple[str, ...]
    injection_patterns: Tuple[str, ...]
    approved_licenses: Tuple[str, ...]
    digest: str

    @property
    def acquisition_limits(self) -> AcquisitionLimits:
        """Return provider limits equal to the canonical admission ceilings."""
        return AcquisitionLimits(
            max_metadata_bytes=self.max_metadata_bytes,
            max_tree_depth=self.max_tree_depth,
            max_entries=self.max_files,
            max_file_bytes=self.max_file_bytes,
            max_total_bytes=self.max_bundle_bytes,
        )


@dataclass(frozen=True)
class AdmissionResult:
    """Strict admission result and deterministic redacted evidence bytes."""

    ok: bool
    findings: Tuple[AdmissionFinding, ...]
    inventory: Optional[bundles.BundleInventory]
    evidence_bytes: bytes


@dataclass(frozen=True)
class QuarantinedCandidate:
    """Confined candidate and deterministic redacted review evidence."""

    relative_root: str
    inventory: bundles.BundleInventory
    admission: AdmissionResult
    evidence_path: str
    evidence_bytes: bytes


def _tuple_of_strings(value: Any, field: str, *, nonempty: bool = True) -> Tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise AdmissionPolicyError(f"vendor-policy.json {field} must be an array of strings")
    if nonempty and not value:
        raise AdmissionPolicyError(f"vendor-policy.json {field} must not be empty")
    if len(set(value)) != len(value):
        raise AdmissionPolicyError(f"vendor-policy.json {field} must contain unique values")
    return tuple(value)


def _positive_integer(value: Any, field: str) -> int:
    if type(value) is not int or value <= 0:
        raise AdmissionPolicyError(f"vendor-policy.json {field} must be a positive integer")
    return value


def load_admission_policy(source_root: Path) -> AdmissionPolicy:
    """Load and strictly validate the committed canonical security policy."""
    root = Path(source_root).resolve(strict=True)
    try:
        content = secure_fs.secure_read_bytes(
            root,
            POLICY_PATH,
            reject_hardlinks=True,
            max_bytes=contracts.MAX_CONTRACT_BYTES,
        )
        value = contracts.load_contract_bytes(content, source=POLICY_PATH.as_posix())
    except (OSError, UnicodeError, ValueError) as error:
        raise AdmissionPolicyError(f"Cannot load vendor policy safely: {error}") from error
    required = {
        "schemaVersion",
        "allowedRepositoryIdentities",
        "allowedUpstreamSkillRoots",
        "maxBundleSizeBytes",
        "maxFileCount",
        "maxFileSizeBytes",
        "maxProviderMetadataBytes",
        "maxProviderTreeDepth",
        "allowedFileExtensions",
        "blockedFileExtensions",
        "blockedDataFileExtensions",
        "blockedCredentialFileNames",
        "opaqueFileExtensions",
        "approvedNonDataResourceClasses",
        "blockedSecretPatterns",
        "blockedMarkdownInstructions",
        "approvedLicenses",
    }
    allowed_fields = required | {
        "description",
        "quarantineDirectoryName",
        "reviewEvidenceDirectoryName",
        "managedSkillRoot",
        "vendorApprovalRequired",
        "consumerReviewOnly",
        "canonicalSourceBranches",
        "canonicalSourceOrigin",
    }
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - allowed_fields)
    if missing or unknown or value.get("schemaVersion") != 1:
        raise AdmissionPolicyError(
            "vendor-policy.json closed schema mismatch: "
            + ", ".join(
                ([f"missing {item}" for item in missing]
                + [f"unknown {item}" for item in unknown])
                or ["schemaVersion=1 required"]
            )
        )
    allowed_extensions = _tuple_of_strings(value["allowedFileExtensions"], "allowedFileExtensions")
    blocked_extensions = tuple(sorted(set(
        _tuple_of_strings(value["blockedFileExtensions"], "blockedFileExtensions")
        + _tuple_of_strings(value["blockedDataFileExtensions"], "blockedDataFileExtensions")
    )))
    if set(allowed_extensions) & set(blocked_extensions):
        raise AdmissionPolicyError("vendor-policy.json allowed and blocked extensions overlap")
    opaque = _tuple_of_strings(value["opaqueFileExtensions"], "opaqueFileExtensions")
    if not set(opaque).issubset(allowed_extensions):
        raise AdmissionPolicyError("Opaque extensions must also be allowed extensions")
    secret_patterns = _tuple_of_strings(value["blockedSecretPatterns"], "blockedSecretPatterns")
    injection_patterns = _tuple_of_strings(
        value["blockedMarkdownInstructions"], "blockedMarkdownInstructions"
    )
    for field, patterns in (
        ("blockedSecretPatterns", secret_patterns),
        ("blockedMarkdownInstructions", injection_patterns),
    ):
        for pattern in patterns:
            try:
                re.compile(pattern)
            except re.error as error:
                raise AdmissionPolicyError(f"Invalid regex in {field}") from error
    return AdmissionPolicy(
        allowed_repositories=_tuple_of_strings(
            value["allowedRepositoryIdentities"], "allowedRepositoryIdentities"
        ),
        allowed_roots=_tuple_of_strings(
            value["allowedUpstreamSkillRoots"], "allowedUpstreamSkillRoots"
        ),
        max_bundle_bytes=_positive_integer(value["maxBundleSizeBytes"], "maxBundleSizeBytes"),
        max_files=_positive_integer(value["maxFileCount"], "maxFileCount"),
        max_file_bytes=_positive_integer(value["maxFileSizeBytes"], "maxFileSizeBytes"),
        max_metadata_bytes=_positive_integer(
            value["maxProviderMetadataBytes"], "maxProviderMetadataBytes"
        ),
        max_tree_depth=_positive_integer(value["maxProviderTreeDepth"], "maxProviderTreeDepth"),
        allowed_extensions=allowed_extensions,
        blocked_extensions=blocked_extensions,
        blocked_names=tuple(
            name.casefold()
            for name in _tuple_of_strings(
                value["blockedCredentialFileNames"], "blockedCredentialFileNames"
            )
        ),
        opaque_extensions=opaque,
        approved_resource_classes=_tuple_of_strings(
            value["approvedNonDataResourceClasses"], "approvedNonDataResourceClasses"
        ),
        secret_patterns=secret_patterns,
        injection_patterns=injection_patterns,
        approved_licenses=_tuple_of_strings(value["approvedLicenses"], "approvedLicenses"),
        digest=hashlib.sha256(content).hexdigest(),
    )


def repository_allowed_for_plugin(origin: str, policy: AdmissionPolicy) -> bool:
    """Return whether normalized plugin vendoring origin is allowlisted."""
    normalized = origin.rstrip("/").casefold()
    return any(normalized == item.rstrip("/").casefold() for item in policy.allowed_repositories)


def _is_link_or_reparse(metadata: os.stat_result) -> bool:
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & _REPARSE_POINT_FLAG
    )


def _resource_classes(frontmatter: Mapping[str, Any]) -> Dict[str, str]:
    value = frontmatter.get("resource-classes", {})
    if value is None:
        return {}
    if isinstance(value, list):
        result = {}
        for item in value:
            if not isinstance(item, str) or "=" not in item:
                raise bundles.BundleValidationError(
                    "SKILL.md resource-classes entries must use path=class."
                )
            path, class_name = item.rsplit("=", 1)
            if not path or not class_name or path in result:
                raise bundles.BundleValidationError(
                    "SKILL.md resource-classes entries must be unique path=class values."
                )
            result[path] = class_name
        return result
    if not isinstance(value, dict) or any(
        not isinstance(path, str) or not isinstance(class_name, str)
        for path, class_name in value.items()
    ):
        raise bundles.BundleValidationError(
            "SKILL.md resource-classes must map relative paths to class names."
        )
    return dict(value)


def _scan_security_text(
    path: str,
    content: bytes,
    policy: AdmissionPolicy,
) -> Iterable[AdmissionFinding]:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        yield AdmissionFinding(path, "admission.encoding", "Resource is not valid UTF-8")
        return
    if "\x00" in text:
        yield AdmissionFinding(path, "admission.binary", "Resource contains binary NUL bytes")
        return
    normalized = unicodedata.normalize("NFKC", text).translate(
        {ord(character): None for character in _ZERO_WIDTH}
    )
    if _BARE_SECRET.search(normalized) or any(
        re.search(pattern, normalized) for pattern in policy.secret_patterns
    ):
        yield AdmissionFinding(path, "admission.secret", "Resource contains a potential secret")
    if path.casefold().endswith((".md", ".markdown")):
        joined = " ".join(normalized.split())
        if any(re.search(pattern, joined) for pattern in policy.injection_patterns):
            yield AdmissionFinding(
                path,
                "admission.prompt-injection",
                "Markdown contains a blocked instruction pattern",
            )


def _enumerate_candidate(
    candidate_root: Path, policy: AdmissionPolicy
) -> Tuple[List[Tuple[str, os.stat_result]], List[AdmissionFinding]]:
    findings = []  # type: List[AdmissionFinding]
    files = []  # type: List[Tuple[str, os.stat_result]]
    try:
        root_metadata = os.lstat(str(candidate_root))
    except OSError:
        return files, [AdmissionFinding("", "admission.root", "Candidate root is missing")]
    if _is_link_or_reparse(root_metadata) or not stat.S_ISDIR(root_metadata.st_mode):
        return files, [AdmissionFinding("", "admission.root", "Candidate root is not a real directory")]
    pending = [(candidate_root, 0)]
    total_bytes = 0
    while pending:
        directory, depth = pending.pop()
        if depth > policy.max_tree_depth:
            findings.append(AdmissionFinding("", "admission.depth", "Bundle exceeds depth ceiling"))
            break
        with os.scandir(str(directory)) as entries:
            ordered = sorted(entries, key=lambda item: item.name, reverse=True)
        for entry in ordered:
            path = Path(entry.path)
            relative = path.relative_to(candidate_root).as_posix()
            # Windows DirEntry.stat() reports st_nlink=0. os.lstat() returns
            # the real link count and still does not follow the leaf.
            metadata = os.lstat(str(path))
            if _is_link_or_reparse(metadata):
                findings.append(AdmissionFinding(relative, "admission.link", "Links and reparse points are rejected"))
                continue
            if stat.S_ISDIR(metadata.st_mode):
                pending.append((path, depth + 1))
                continue
            if not stat.S_ISREG(metadata.st_mode):
                findings.append(AdmissionFinding(relative, "admission.non-regular", "Non-regular resources are rejected"))
                continue
            files.append((relative, metadata))
            if len(files) > policy.max_files:
                findings.append(AdmissionFinding("", "admission.file-count", "Bundle exceeds file-count ceiling"))
            total_bytes += metadata.st_size
            if metadata.st_size > policy.max_file_bytes:
                findings.append(AdmissionFinding(relative, "admission.file-size", "Resource exceeds per-file ceiling"))
            if total_bytes > policy.max_bundle_bytes:
                findings.append(AdmissionFinding("", "admission.total-size", "Bundle exceeds total-byte ceiling"))
    return sorted(files), findings


def _inventory_policy_findings(
    inventory: bundles.BundleInventory,
    policy: AdmissionPolicy,
) -> List[AdmissionFinding]:
    """Apply common non-data, reference, and content policy to one inventory."""
    findings = []  # type: List[AdmissionFinding]
    if len(inventory.files) > policy.max_files:
        findings.append(
            AdmissionFinding("", "admission.file-count", "Bundle exceeds file-count ceiling")
        )
    total_bytes = sum(len(item.content) for item in inventory.files)
    if total_bytes > policy.max_bundle_bytes:
        findings.append(
            AdmissionFinding("", "admission.total-size", "Bundle exceeds total-byte ceiling")
        )
    try:
        resource_classes = _resource_classes(inventory.frontmatter)
    except bundles.BundleValidationError as error:
        findings.append(
            AdmissionFinding("SKILL.md", "admission.opaque-class", str(error))
        )
        resource_classes = {}
    for issue in bundles.validate_markdown_references(inventory):
        findings.append(AdmissionFinding(issue.path, issue.code, issue.message))
    for item in inventory.files:
        relative = item.bundle_path
        errors = path_policy.validate_repo_relative_path("bundle resource", relative)
        if errors:
            findings.append(
                AdmissionFinding(relative, "admission.path", "Resource path is not portable")
            )
            continue
        if item.executable:
            findings.append(
                AdmissionFinding(
                    relative,
                    "admission.executable",
                    "Executable mode bits are rejected",
                )
            )
        if len(item.content) > policy.max_file_bytes:
            findings.append(
                AdmissionFinding(
                    relative,
                    "admission.file-size",
                    "Resource exceeds per-file ceiling",
                )
            )
            continue
        suffix = PurePosixPath(relative).suffix.casefold()
        name = PurePosixPath(relative).name.casefold()
        if suffix in policy.blocked_extensions or name in policy.blocked_names:
            findings.append(
                AdmissionFinding(
                    relative,
                    "admission.blocked-extension",
                    "Data, archive, environment, or credential resource is rejected",
                )
            )
            continue
        if (
            relative != "SKILL.md"
            and suffix not in policy.allowed_extensions
            and name not in {"license", "notice"}
        ):
            findings.append(
                AdmissionFinding(
                    relative,
                    "admission.blocked-extension",
                    "Resource extension is not allowed and is rejected",
                )
            )
            continue
        if suffix in policy.opaque_extensions:
            declared_class = resource_classes.get(relative)
            if declared_class not in policy.approved_resource_classes:
                findings.append(
                    AdmissionFinding(
                        relative,
                        "admission.opaque-class",
                        "Opaque resource lacks an approved non-data class",
                    )
                )
        if item.content.startswith(_LFS_PREFIX):
            findings.append(
                AdmissionFinding(
                    relative,
                    "admission.lfs",
                    "Git LFS pointer content is rejected",
                )
            )
        findings.extend(_scan_security_text(relative, item.content, policy))
        if suffix == ".json":
            try:
                contracts.load_contract_bytes(item.content, source=relative)
            except ValueError:
                findings.append(
                    AdmissionFinding(relative, "admission.json", "JSON resource is invalid")
                )
    return findings


def admit_inventory(
    inventory: bundles.BundleInventory,
    policy: AdmissionPolicy,
    *,
    license_id: Optional[str] = None,
) -> AdmissionResult:
    """Admit an in-memory bundle through the canonical common policy.

    Args:
        inventory: Complete atomic bundle inventory.
        policy: Validated canonical admission policy.
        license_id: Optional required approved license for imported content.

    Returns:
        Deterministic redacted admission result.

    Example:
        ``result = admit_inventory(scaffold, policy)``
    """
    findings = _inventory_policy_findings(inventory, policy)
    if license_id is not None and license_id not in policy.approved_licenses:
        findings.append(
            AdmissionFinding("", "admission.license", "License is not approved")
        )
    ordered = tuple(
        sorted(set(findings), key=lambda item: (item.path, item.code, item.message))
    )
    evidence = {
        "schema": "cg-skill-admission-evidence-v1",
        "candidateDigest": inventory.digest,
        "policyDigest": policy.digest,
        "license": license_id,
        "ok": not ordered,
        "files": [
            {"path": item.bundle_path, "size": len(item.content)}
            for item in inventory.files
        ],
        "findings": [
            {"code": finding.code, "path": finding.path, "message": finding.message}
            for finding in ordered
        ],
    }
    return AdmissionResult(
        not ordered,
        ordered,
        inventory,
        contracts.canonical_json_bytes(evidence) + b"\n",
    )


def admit_bundle(
    candidate_root: Path,
    license_id: str,
    policy: AdmissionPolicy,
) -> AdmissionResult:
    """Apply strict no-follow, non-data, content, link, and license admission."""
    candidate = Path(candidate_root)
    files, findings = _enumerate_candidate(candidate, policy)
    file_paths = {path for path, _metadata in files}
    if "SKILL.md" not in file_paths:
        findings.append(AdmissionFinding("SKILL.md", "admission.skill-missing", "Bundle is missing SKILL.md"))
    if license_id not in policy.approved_licenses:
        findings.append(AdmissionFinding("", "admission.license", "License is not approved"))

    inventory = None
    if not any(finding.code in {"admission.root", "admission.link", "admission.non-regular"} for finding in findings):
        try:
            inventory = bundles.inventory_bundle(
                candidate.parent,
                candidate.name,
                origin="project-imported",
            )
        except (OSError, bundles.BundleValidationError) as error:
            code = "admission.hard-link" if "hard link" in str(error).casefold() else "admission.bundle"
            findings.append(AdmissionFinding("", code, str(error)))

    if inventory is not None:
        findings.extend(_inventory_policy_findings(inventory, policy))
    for relative, metadata in files:
        if metadata.st_nlink != 1:
            findings.append(AdmissionFinding(relative, "admission.hard-link", "Hard-linked resources are rejected"))

    ordered = tuple(sorted(set(findings), key=lambda item: (item.path, item.code, item.message)))
    evidence = {
        "schema": "cg-skill-admission-evidence-v1",
        "candidateDigest": inventory.digest if inventory is not None else None,
        "policyDigest": policy.digest,
        "license": license_id,
        "ok": not ordered,
        "files": [
            {"path": path, "size": metadata.st_size}
            for path, metadata in files
        ],
        "findings": [
            {"code": finding.code, "path": finding.path, "message": finding.message}
            for finding in ordered
        ],
    }
    return AdmissionResult(
        not ordered,
        ordered,
        inventory,
        contracts.canonical_json_bytes(evidence) + b"\n",
    )


def quarantine_key(origin: str, commit: str, source_path: str) -> str:
    """Return the deterministic confined key for one exact approved source."""
    return hashlib.sha256(
        contracts.canonical_json_bytes(
            {"origin": origin, "commit": commit, "path": source_path}
        )
    ).hexdigest()


def validate_acquired_source(
    acquired: AcquiredBundle,
    origin: str,
    commit: str,
    source_path: str,
) -> None:
    """Require provider output to match the exact requested immutable source."""
    if (
        acquired.origin != origin
        or acquired.commit != commit
        or acquired.source_path != source_path
    ):
        raise AdmissionPolicyError(
            "Acquired bundle identity differs from the exact approved source"
        )


def materialize_quarantine(
    project_root: Path,
    acquired: AcquiredBundle,
    license_id: str,
    policy: AdmissionPolicy,
    *,
    review_scope: str = "project-import",
) -> QuarantinedCandidate:
    """Write only confined quarantine/evidence and run strict local admission."""
    if _REVIEW_SCOPE.fullmatch(review_scope) is None:
        raise AdmissionPolicyError("Admission review scope is invalid")
    project = Path(project_root).resolve(strict=True)
    identifier = PurePosixPath(acquired.source_path).name
    key = quarantine_key(acquired.origin, acquired.commit, acquired.source_path)
    relative_root = f".compound-gpid/quarantine/{key}/{identifier}"
    seen = set()
    for item in acquired.files:
        errors = path_policy.validate_repo_relative_path("acquired bundle path", item.path)
        if errors:
            raise AdmissionPolicyError("Acquired path is unsafe: " + "; ".join(errors))
        portable = path_policy.portable_path_key(item.path)
        if portable in seen:
            raise AdmissionPolicyError("Acquired paths collide portably")
        seen.add(portable)
        relative = f"{relative_root}/{item.path}"
        current = None
        try:
            current = secure_fs.secure_read_bytes(
                project,
                PurePosixPath(relative),
                reject_hardlinks=True,
                max_bytes=policy.max_file_bytes,
            )
        except FileNotFoundError:
            current = None
        if current is not None and current != item.content:
            raise AdmissionPolicyError(
                f"Quarantine path changed for exact source: {item.path}"
            )
        if current is None:
            secure_fs.secure_write_bytes(
                project,
                PurePosixPath(relative),
                item.content,
                executable=False,
                expected_state=secure_fs.ExpectedFileState.absent(),
            )
    candidate_root = project / Path(*PurePosixPath(relative_root).parts)
    result = admit_bundle(candidate_root, license_id, policy)
    if result.inventory is None:
        raise AdmissionPolicyError("Quarantined candidate has no valid inventory")
    if result.inventory.digest != hashlib.sha256(
        b"".join(
            item.path.encode("utf-8")
            + b"\0"
            + hashlib.sha256(item.content).hexdigest().encode("ascii")
            + b"\n"
            for item in sorted(acquired.files, key=lambda candidate: candidate.path)
        )
    ).hexdigest():
        raise AdmissionPolicyError(
            "Quarantined candidate digest differs from verified GitHub blobs"
        )
    evidence_value = {
        "schema": "cg-skill-admission-review-v1",
        "scope": review_scope,
        "source": {
            "origin": acquired.origin,
            "commit": acquired.commit,
            "path": acquired.source_path,
        },
        "acquisitionDigest": acquired.digest,
        "admission": json.loads(result.evidence_bytes.decode("utf-8")),
    }
    evidence_bytes = contracts.canonical_json_bytes(evidence_value) + b"\n"
    evidence_path = f".compound-gpid/vendor-reviews/{review_scope}-{key}.json"
    current_evidence = None
    try:
        current_evidence = secure_fs.secure_read_bytes(
            project,
            PurePosixPath(evidence_path),
            reject_hardlinks=True,
            max_bytes=contracts.MAX_CONTRACT_BYTES,
        )
    except FileNotFoundError:
        current_evidence = None
    if current_evidence is not None and current_evidence != evidence_bytes:
        raise AdmissionPolicyError("Review evidence path changed for exact source")
    if current_evidence is None:
        secure_fs.secure_write_bytes(
            project,
            PurePosixPath(evidence_path),
            evidence_bytes,
            expected_state=secure_fs.ExpectedFileState.absent(),
        )
    return QuarantinedCandidate(
        relative_root,
        result.inventory,
        result,
        evidence_path,
        evidence_bytes,
    )


def load_quarantined_candidate(
    project_root: Path,
    origin: str,
    commit: str,
    source_path: str,
    license_id: str,
    policy: AdmissionPolicy,
    *,
    review_scope: str = "project-import",
) -> QuarantinedCandidate:
    """Re-admit exact existing quarantine/evidence without network acquisition."""
    if _REVIEW_SCOPE.fullmatch(review_scope) is None:
        raise AdmissionPolicyError("Admission review scope is invalid")
    project = Path(project_root).resolve(strict=True)
    key = quarantine_key(origin, commit, source_path)
    identifier = PurePosixPath(source_path).name
    relative_root = f".compound-gpid/quarantine/{key}/{identifier}"
    candidate_root = project / Path(*PurePosixPath(relative_root).parts)
    result = admit_bundle(candidate_root, license_id, policy)
    if result.inventory is None:
        raise AdmissionPolicyError("Quarantined candidate has no valid inventory")
    evidence_path = f".compound-gpid/vendor-reviews/{review_scope}-{key}.json"
    try:
        evidence_bytes = secure_fs.secure_read_bytes(
            project,
            PurePosixPath(evidence_path),
            reject_hardlinks=True,
            max_bytes=contracts.MAX_CONTRACT_BYTES,
        )
        evidence = contracts.load_contract_bytes(evidence_bytes, source=evidence_path)
    except (OSError, UnicodeError, ValueError) as error:
        raise AdmissionPolicyError("Project import review evidence is missing or invalid") from error
    source = evidence.get("source", {})
    if (
        evidence.get("schema") != "cg-skill-admission-review-v1"
        or evidence.get("scope") != review_scope
    ):
        raise AdmissionPolicyError("Admission review evidence scope mismatch")
    if source != {"origin": origin, "commit": commit, "path": source_path}:
        raise AdmissionPolicyError("Project import review evidence source mismatch")
    expected_admission = json.loads(result.evidence_bytes.decode("utf-8"))
    if evidence.get("admission") != expected_admission:
        raise AdmissionPolicyError("Project import admission evidence changed")
    return QuarantinedCandidate(
        relative_root,
        result.inventory,
        result,
        evidence_path,
        evidence_bytes,
    )
