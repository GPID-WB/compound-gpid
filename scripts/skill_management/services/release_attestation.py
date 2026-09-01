"""Read-only immutable plugin release and project revision grace verification."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Mapping, Sequence, Tuple

import secure_fs

from skill_management import contracts
from skill_management.services import provenance


ATTESTATION_ROOT = ".github/shared/skill-management/release-attestations"
_REPARSE_POINT_FLAG = 0x400
_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
_TAG_VERSION = re.compile(
    r"^v([0-9]+)\.([0-9]+)\.([0-9]+)(?:-([A-Za-z0-9.-]+))?(?:\+([A-Za-z0-9.-]+))?$"
)


class ReleaseAttestationError(ValueError):
    """Raised when immutable lifecycle grace cannot be proven."""


@dataclass(frozen=True)
class PluginGraceEvidence:
    """Two verified published release identities for plugin grace."""

    anchor_release: str
    anchor_commit: str
    descendant_release: str
    descendant_commit: str

    @property
    def removed_revision(self) -> str:
        """Return the later immutable release commit."""
        return self.descendant_commit

    @property
    def summary(self) -> str:
        """Return one stable public evidence summary."""
        return (
            f"plugin:{self.anchor_release}@{self.anchor_commit}->"
            f"{self.descendant_release}@{self.descendant_commit}"
        )


@dataclass(frozen=True)
class ProjectGraceEvidence:
    """Earliest containing commit and one later descendant project revision."""

    anchor_revision: str
    removed_revision: str

    @property
    def summary(self) -> str:
        """Return one stable public evidence summary."""
        return f"project:{self.anchor_revision}->{self.removed_revision}"


def _is_link_or_reparse(metadata: os.stat_result) -> bool:
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & _REPARSE_POINT_FLAG
    )


def _git(root: Path, arguments: Sequence[str]) -> str:
    environment = os.environ.copy()
    for name in tuple(environment):
        if name.startswith("GIT_"):
            environment.pop(name, None)
    environment["GIT_TERMINAL_PROMPT"] = "0"
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
            stdin=subprocess.DEVNULL,
            env=environment,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ReleaseAttestationError(
            f"Git evidence command could not complete: {' '.join(arguments)}"
        ) from error
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "Git returned an error"
        raise ReleaseAttestationError(
            f"Git evidence command failed: {' '.join(arguments)}: {detail}"
        )
    return result.stdout.strip()


def _git_bytes(root: Path, object_path: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "show", object_path],
            capture_output=True,
            timeout=20,
            check=False,
            stdin=subprocess.DEVNULL,
            env={
                **{
                    key: value
                    for key, value in os.environ.items()
                    if not key.startswith("GIT_")
                },
                "GIT_TERMINAL_PROMPT": "0",
            },
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ReleaseAttestationError(
            f"Tagged tree bytes could not be read: {object_path}"
        ) from error
    if result.returncode != 0:
        raise ReleaseAttestationError(
            f"Tagged tree is missing required bytes: {object_path}"
        )
    return result.stdout


def _attestation_schema() -> Dict[str, Any]:
    path = Path(__file__).resolve().parents[3] / (
        ".github/shared/skill-management/contracts/release-attestation-v1.schema.json"
    )
    return contracts.load_contract(path)


def load_release_attestations(source_root: Path) -> Tuple[Mapping[str, Any], ...]:
    """Load every bounded regular release attestation in version order."""
    root = Path(source_root).resolve(strict=True)
    directory = root / ATTESTATION_ROOT
    try:
        metadata = os.lstat(str(directory))
    except FileNotFoundError:
        return ()
    except OSError as error:
        raise ReleaseAttestationError(
            f"Cannot inspect release attestation root: {error}"
        ) from error
    if _is_link_or_reparse(metadata) or not stat.S_ISDIR(metadata.st_mode):
        raise ReleaseAttestationError(
            "Release attestation root must be one real directory"
        )
    schema = _attestation_schema()
    loaded = []
    with os.scandir(str(directory)) as entries:
        ordered = sorted(entries, key=lambda item: item.name)
    for entry in ordered:
        metadata = entry.stat(follow_symlinks=False)
        relative = f"{ATTESTATION_ROOT}/{entry.name}"
        if (
            _is_link_or_reparse(metadata)
            or not stat.S_ISREG(metadata.st_mode)
            or not entry.name.endswith(".json")
        ):
            raise ReleaseAttestationError(
                f"Release attestation must be regular JSON: {relative}"
            )
        try:
            content = secure_fs.secure_read_bytes(
                root,
                PurePosixPath(relative),
                reject_hardlinks=True,
                max_bytes=contracts.MAX_CONTRACT_BYTES,
            )
            value = contracts.load_contract_bytes(content, source=relative)
        except (OSError, UnicodeError, ValueError) as error:
            raise ReleaseAttestationError(
                f"Cannot load release attestation safely: {relative}: {error}"
            ) from error
        findings = contracts.validate_instance(value, schema)
        if findings:
            raise ReleaseAttestationError(
                f"Release attestation is invalid: {relative}: {findings[0].code}"
            )
        tag = str(value["releaseTag"])
        if entry.name != f"{tag}.json":
            raise ReleaseAttestationError(
                f"Release attestation filename must match releaseTag: {relative}"
            )
        try:
            provenance.validate_audit_metadata(
                "release-attestation", str(value["reviewReference"])
            )
        except provenance.ProvenanceValidationError as error:
            raise ReleaseAttestationError(str(error)) from error
        loaded.append(value)
    return tuple(sorted(loaded, key=lambda item: _version_key(str(item["releaseTag"]))))


def _version_key(tag: str) -> Tuple[int, int, int, int, str]:
    match = _TAG_VERSION.fullmatch(tag)
    if match is None:
        raise ReleaseAttestationError(f"Release tag is not supported: {tag}")
    prerelease = match.group(4)
    return (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)),
        0 if prerelease else 1,
        prerelease or "",
    )


def _remote_tag_identity(root: Path, tag: str) -> Tuple[str, str]:
    output = _git(
        root,
        (
            "ls-remote",
            "origin",
            f"refs/tags/{tag}",
            f"refs/tags/{tag}^{{}}",
        ),
    )
    rows = {}
    for line in output.splitlines():
        fields = line.split()
        if len(fields) == 2:
            rows[fields[1]] = fields[0].casefold()
    object_sha = rows.get(f"refs/tags/{tag}")
    peeled_sha = rows.get(f"refs/tags/{tag}^{{}}")
    if not object_sha or not peeled_sha:
        raise ReleaseAttestationError(
            f"Remote release tag must exist as one annotated tag: {tag}"
        )
    return object_sha, peeled_sha


def _verify_attestation(
    root: Path,
    attestation: Mapping[str, Any],
    identifier: str,
    record_digest: str,
    provenance_path: str,
    bundle_path: str,
) -> str:
    tag = str(attestation["releaseTag"])
    object_sha = _git(root, ("rev-parse", f"refs/tags/{tag}"))
    object_type = _git(root, ("cat-file", "-t", f"refs/tags/{tag}"))
    commit_sha = _git(root, ("rev-parse", f"refs/tags/{tag}^{{commit}}"))
    if object_type != "tag":
        raise ReleaseAttestationError(
            f"Release grace requires an annotated tag: {tag}"
        )
    remote_object, remote_commit = _remote_tag_identity(root, tag)
    expected_object = str(attestation["tagRefObjectSha"])
    expected_commit = str(attestation["peeledCommitSha"])
    if (
        object_sha != expected_object
        or commit_sha != expected_commit
        or remote_object != expected_object
        or remote_commit != expected_commit
    ):
        raise ReleaseAttestationError(
            f"Release tag identity moved, changed type, or disagrees with attestation: {tag}"
        )
    payload_path = f"releases/{tag}.json"
    try:
        live_payload = secure_fs.secure_read_bytes(
            root,
            PurePosixPath(payload_path),
            reject_hardlinks=True,
            max_bytes=contracts.MAX_CONTRACT_BYTES,
        )
    except (OSError, ValueError) as error:
        raise ReleaseAttestationError(
            f"Immutable release payload is unavailable: {payload_path}"
        ) from error
    tagged_payload = _git_bytes(root, f"{commit_sha}:{payload_path}")
    expected_payload = str(attestation["releasePayloadSha256"])
    if (
        hashlib.sha256(live_payload).hexdigest() != expected_payload
        or hashlib.sha256(tagged_payload).hexdigest() != expected_payload
        or live_payload != tagged_payload
    ):
        raise ReleaseAttestationError(
            f"Release payload bytes disagree with attestation: {tag}"
        )
    tagged_record_bytes = _git_bytes(root, f"{commit_sha}:{provenance_path}")
    try:
        tagged_record = json.loads(tagged_record_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ReleaseAttestationError(
            f"Tagged deprecation record is invalid: {tag}"
        ) from error
    if (
        not isinstance(tagged_record, dict)
        or tagged_record.get("deprecatedRecordDigest") != record_digest
        or tagged_record.get("skillId") != identifier
    ):
        raise ReleaseAttestationError(
            f"Tagged tree does not contain the exact deprecation record: {tag}"
        )
    _git(root, ("cat-file", "-e", f"{commit_sha}:{bundle_path}/SKILL.md"))
    return commit_sha


def verify_plugin_grace(
    source_root: Path,
    identifier: str,
    record_digest: str,
    provenance_path: str,
    bundle_path: str,
) -> PluginGraceEvidence:
    """Verify an anchor release and one later attested descendant release."""
    root = Path(source_root).resolve(strict=True)
    candidates = [
        item
        for item in load_release_attestations(root)
        if item.get("deprecationRecordDigests", {}).get(identifier) == record_digest
    ]
    if len(candidates) < 2:
        raise ReleaseAttestationError(
            "Plugin removal requires an attested containing release and a later attested release"
        )
    verified = []
    for item in candidates:
        commit = _verify_attestation(
            root,
            item,
            identifier,
            record_digest,
            provenance_path,
            bundle_path,
        )
        verified.append((str(item["releaseTag"]), commit))
    anchor_tag, anchor_commit = verified[0]
    for later_tag, later_commit in verified[1:]:
        if later_commit == anchor_commit:
            continue
        try:
            _git(root, ("merge-base", "--is-ancestor", anchor_commit, later_commit))
        except ReleaseAttestationError:
            continue
        return PluginGraceEvidence(
            anchor_tag, anchor_commit, later_tag, later_commit
        )
    raise ReleaseAttestationError(
        "No later attested published release descends from the grace anchor"
    )


def verify_project_grace(
    project_root: Path,
    identifier: str,
    record_digest: str,
    provenance_path: str,
    bundle_path: str,
) -> ProjectGraceEvidence:
    """Derive the earliest exact containing commit and require a later HEAD."""
    root = Path(project_root).resolve(strict=True)
    head = _git(root, ("rev-parse", "--verify", "HEAD^{commit}"))
    revisions = _git(
        root, ("log", "--reverse", "--format=%H", "--", provenance_path)
    ).splitlines()
    anchor = ""
    for revision in revisions:
        if _FULL_SHA.fullmatch(revision) is None:
            continue
        try:
            content = _git_bytes(root, f"{revision}:{provenance_path}")
            value = json.loads(content.decode("utf-8"))
            if (
                isinstance(value, dict)
                and value.get("skillId", identifier) == identifier
                and value.get("deprecatedRecordDigest") == record_digest
            ):
                _git(root, ("cat-file", "-e", f"{revision}:{bundle_path}/SKILL.md"))
                anchor = revision
                break
        except (ReleaseAttestationError, UnicodeError, json.JSONDecodeError):
            continue
    if not anchor:
        raise ReleaseAttestationError(
            "No committed project revision contains the exact deprecation record and skill"
        )
    if head == anchor:
        raise ReleaseAttestationError(
            "Project removal requires a later descendant revision after deprecation"
        )
    _git(root, ("merge-base", "--is-ancestor", anchor, head))
    try:
        head_record = json.loads(
            _git_bytes(root, f"{head}:{provenance_path}").decode("utf-8")
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ReleaseAttestationError(
            "Later project revision has no valid deprecation record"
        ) from error
    if not isinstance(head_record, dict) or head_record.get(
        "deprecatedRecordDigest"
    ) != record_digest:
        raise ReleaseAttestationError(
            "Later project revision does not preserve the exact deprecation record"
        )
    _git(root, ("cat-file", "-e", f"{head}:{bundle_path}/SKILL.md"))
    return ProjectGraceEvidence(anchor, head)


def project_is_git_repository(project_root: Path) -> bool:
    """Return whether a project has one readable committed Git revision."""
    try:
        value = _git(
            Path(project_root).resolve(strict=True),
            ("rev-parse", "--verify", "HEAD^{commit}"),
        )
    except ReleaseAttestationError:
        return False
    return _FULL_SHA.fullmatch(value) is not None
