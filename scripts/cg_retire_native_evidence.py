#!/usr/bin/env python3
"""Retire only receipt-proven native-evidence files in a local project.

This helper does not change receipts, config, journals, locks or directories.
9021 install units do not deliver the canonical .github plugin sources to
consumers, so those paths are deliberately not retirement destinations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

try:
    from . import secure_fs
except ImportError:  # Direct CLI invocation.
    import secure_fs


NATIVE_PATHS = (
    ".kilo/plugins/cg-native-evidence.js",
    ".kilo/plugin-support/cg-native-evidence/evidence.mjs",
    ".kilo/plugin-support/cg-native-evidence/records.mjs",
    ".kilo/plugin-support/cg-native-evidence/transport.mjs",
    ".kilo/plugin-support/cg-native-evidence/wire.mjs",
)
RECEIPTS = (
    ".kilo/.compound-gpid-generated.json",
    ".kilo/plugins/.compound-gpid-managed-copy.json",
    ".kilo/plugin-support/cg-native-evidence/.compound-gpid-managed-copy.json",
    ".compound-gpid/managed-files.json",
    ".compound-gpid/projection-ownership.json",
)
HASH_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
READ_LIMIT = 16 * 1024 * 1024


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    """Reject ambiguous duplicate JSON keys in ownership evidence."""
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate receipt key: {key}")
        result[key] = value
    return result


def _snapshot(root: Path) -> dict[str, bytes | None]:
    """Read only the fixed receipt paths, with no links or hardlink aliases."""
    result: dict[str, bytes | None] = {}
    for relative in RECEIPTS:
        try:
            result[relative] = secure_fs.secure_read_bytes(
                root, relative, reject_hardlinks=True, max_bytes=READ_LIMIT
            )
        except FileNotFoundError:
            result[relative] = None
    return result


def _claims(snapshot: dict[str, bytes | None]) -> dict[str, str]:
    """Validate existing receipt schemas and exact native destination claims."""
    claims: dict[str, str] = {}
    for receipt, content in snapshot.items():
        if content is None:
            continue
        data = json.loads(content.decode("utf-8-sig"), object_pairs_hook=_unique_object)
        if not isinstance(data, dict):
            raise ValueError(f"receipt must be an object: {receipt}")
        scalar = receipt.endswith("/managed-files.json")
        expected_schema = "compound-gpid-managed-files-v1" if scalar else 1
        if type(data.get("schemaVersion")) is not type(expected_schema) or (
            data["schemaVersion"] != expected_schema
        ):
            raise ValueError(f"unsupported receipt schema: {receipt}")
        generated = receipt == RECEIPTS[0]
        copied = receipt in RECEIPTS[1:3]
        if generated:
            if data.get("target") != "kilo" or type(data.get("policyVersion")) is not int or data["policyVersion"] != 1:
                raise ValueError(f"invalid generated receipt identity: {receipt}")
            entries = data.get("files")
            if not isinstance(entries, list):
                raise ValueError(f"receipt files must be an array: {receipt}")
            records: dict = {}
            for entry in entries:
                if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                    raise ValueError(f"invalid generated receipt entry: {receipt}")
                relative = entry["path"]
                if relative in records:
                    raise ValueError(f"duplicate receipt destination: {relative}")
                records[relative] = entry
        else:
            records = data.get("entries" if receipt == RECEIPTS[4] else "files")
            if not isinstance(records, dict):
                raise ValueError(f"receipt records must be an object: {receipt}")
        copy_root = receipt.rsplit("/", 1)[0]
        if copied and data.get("source") != copy_root:
            raise ValueError(f"invalid copy receipt source: {receipt}")
        for relative, record in records.items():
            if secure_fs.normalize_relative_path(relative) != relative:
                raise ValueError(f"noncanonical receipt destination: {relative}")
            full_relative = f"{copy_root}/{relative}" if copied else relative
            native_key = "/".join(
                part.rstrip(" .").casefold() for part in full_relative.split("/")
            )
            if full_relative not in NATIVE_PATHS and any(
                native_key == path.casefold() for path in NATIVE_PATHS
            ):
                raise ValueError(f"aliased native receipt destination: {relative}")
            if copied:
                checksum = record
            else:
                if not isinstance(record, dict) or not isinstance(record.get("source"), str):
                    raise ValueError(f"invalid ownership record in {receipt}: {relative}")
                checksum = record.get("checksum" if scalar else "sha256")
                if generated and (
                    not isinstance(record.get("kind"), str)
                    or not isinstance(record.get("executable"), bool)
                ):
                    raise ValueError(f"invalid generated record: {relative}")
            if not isinstance(checksum, str) or not HASH_PATTERN.fullmatch(checksum):
                raise ValueError(f"invalid ownership checksum in {receipt}: {relative}")
        for destination in NATIVE_PATHS:
            key = destination[len(copy_root) + 1:] if copied else destination
            if copied and not destination.startswith(copy_root + "/"):
                continue
            if key not in records:
                continue
            record = records[key]
            if copied:
                checksum = record
            else:
                if not isinstance(record, dict):
                    raise ValueError(f"invalid ownership record: {destination}")
                source = destination.replace(".kilo/", ".github/", 1) if generated or receipt == RECEIPTS[4] else destination
                if record.get("source") != source:
                    raise ValueError(f"unexpected ownership source: {destination}")
                if generated and (record.get("kind") != "native-plugin" or record.get("executable") is not False):
                    raise ValueError(f"invalid native-plugin record: {destination}")
                if receipt == RECEIPTS[4] and (
                    record.get("platform") != "kilo"
                    or record.get("kind") != "native-plugin"
                    or record.get("preserved") is not False
                    or record.get("origin") != "plugin-canonical"
                    or record.get("provenanceIdentity") != "canonical/.github"
                ):
                    raise ValueError(f"invalid projection ownership: {destination}")
                checksum = record.get("checksum" if scalar else "sha256")
            if not isinstance(checksum, str) or not HASH_PATTERN.fullmatch(checksum):
                raise ValueError(f"invalid ownership checksum: {destination}")
            if destination in claims and claims[destination] != checksum:
                raise ValueError(f"conflicting ownership receipts: {destination}")
            claims[destination] = checksum
    return claims


def retire_native_evidence(root: Path) -> tuple[list[str], dict[str, str]]:
    """Delete only exact, unchanged, ownership-proven regular files.

    Args:
        root: Existing project directory, not a link.
    Returns:
        Deleted paths and preserved paths with reasons. Any preserved active
        path blocks deletion of the whole set and downstream receipt refresh.
    Example:
        ``deleted, preserved = retire_native_evidence(Path("project"))``.
    """
    root = Path(root).absolute()
    candidates: dict[str, str] = {}
    preserved: dict[str, str] = {}
    for relative in NATIVE_PATHS:
        try:
            content = secure_fs.secure_read_bytes(
                root, relative, reject_hardlinks=True, max_bytes=READ_LIMIT
            )
            candidates[relative] = hashlib.sha256(content).hexdigest()
        except FileNotFoundError:
            continue
        except (OSError, ValueError) as error:
            preserved[relative] = f"unsafe file or ancestor: {error}"
    if not candidates and not preserved:
        return [], {}
    try:
        snapshot = _snapshot(root)
        claims = _claims(snapshot)
    except (OSError, ValueError, UnicodeError) as error:
        for relative in candidates:
            preserved[relative] = f"invalid or unsafe ownership receipt: {error}"
        return [], preserved
    for relative, checksum in candidates.items():
        if relative not in claims:
            preserved[relative] = "no valid ownership receipt"
        elif claims[relative] != checksum:
            preserved[relative] = "file differs from its ownership checksum"
    if preserved:
        for relative in candidates:
            preserved.setdefault(relative, "retirement blocked by other preserved residue")
        return [], preserved

    def recheck(path: Path) -> None:
        """Recheck all evidence and reject file aliases at the delete boundary."""
        if _snapshot(root) != snapshot:
            raise ValueError("ownership receipts changed before deletion")
        content = secure_fs.secure_read_bytes(
            root, path.relative_to(root), reject_hardlinks=True, max_bytes=READ_LIMIT
        )
        if hashlib.sha256(content).hexdigest() != claims[path.relative_to(root).as_posix()]:
            raise ValueError("file changed before deletion")

    deleted: list[str] = []
    for relative in candidates:
        try:
            secure_fs.secure_delete_verified(
                root, relative, claims[relative], before_unlink=recheck
            )
            deleted.append(relative)
        except (OSError, ValueError) as error:
            for remaining in candidates:
                if remaining not in deleted:
                    preserved[remaining] = f"deletion stopped: {error}"
            break
    return deleted, preserved


def main(argv: list[str] | None = None) -> int:
    """Run narrow retirement and return nonzero for preserved active residue.

    Args:
        argv: CLI arguments, or process arguments when omitted.
    Returns:
        Zero when no active residue remains; one when manual review is needed.
    Example:
        ``main(["--root", "project"])``.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args(argv)
    deleted, preserved = retire_native_evidence(args.root)
    for relative in deleted:
        sys.stdout.write(f"Retired unchanged owned native-evidence file: {relative}\n")
    for relative, reason in preserved.items():
        sys.stderr.write(f"Preserved native-evidence file: {relative}: {reason}\n")
    if preserved:
        sys.stderr.write(
            "Link/update is blocked. Do not launch Kilo with this residue. "
            "Review the preserved files and ownership evidence; archive or disable "
            "the loader manually after review, then retry. Keep receipts, journals "
            "and locks. No user files were authorized for deletion.\n"
        )
    return 1 if preserved else 0


if __name__ == "__main__":
    raise SystemExit(main())
