"""Verify archive bytes as bounded data; never extract files or execute source."""

import hashlib
import io
import stat
import struct
import zipfile
import zlib

from cg_release.events import ControllerError
from cg_release.policy import safe_path


def verify_archive(
    raw: bytes,
    metadata: dict,
    *,
    run_id: int,
    controller_sha: str,
    declared: list,
    max_total_bytes: int,
    max_artifacts: int,
) -> dict:
    """Verify one registered-run archive and its complete declared byte inventory.

    Args: raw is bounded downloaded GitHub archive data; metadata is from the exact
        artifact API. declared contains trusted policy Artifact records, never a
        source-written manifest. Limits apply before and during decompression.
    Returns: Digests, sizes and IDs, e.g. verify_archive(raw, metadata, ...).
    Raises: ControllerError for substitution, expiry, unsafe entries, or mismatch.
    """
    try:
        archive_digest = hashlib.sha256(raw).hexdigest()
        if (
            not isinstance(raw, bytes)
            or len(raw) > max_total_bytes + 1024 * 1024
            or metadata["expired"] is not False
            or type(metadata["id"]) is not int
            or metadata["id"] <= 0
            or metadata["workflow_run"]["id"] != run_id
            or type(metadata["workflow_run"]["id"]) is not int
            or metadata["workflow_run"]["head_sha"] != controller_sha
            or type(metadata["size_in_bytes"]) is not int
            or metadata["size_in_bytes"] != len(raw)
            or (
                metadata.get("digest") is not None
                and metadata["digest"] != "sha256:" + archive_digest
            )
        ):
            raise ValueError
        allowed = {a.path: a for a in declared}
        if len(allowed) != len(declared) or len(allowed) > max_artifacts:
            raise ValueError
        entry_limit = min(max_artifacts, len(allowed))
        # EOCD counts are untrusted. Bind the physical range used by ZipFile's
        # non-ZIP64 reader, then walk it before any per-entry objects are allocated.
        end = raw.rfind(b"PK\x05\x06", max(0, len(raw) - 65557))
        if end < 0 or len(raw) - end < 22:
            raise ValueError
        (
            _,
            disk,
            start_disk,
            disk_count,
            count,
            directory_size,
            directory_offset,
            comment_size,
        ) = struct.unpack_from("<4s4H2LH", raw, end)
        if (
            disk != 0
            or start_disk != 0
            or disk_count != count
            or count == 65535
            or count > entry_limit
            or end + 22 + comment_size != len(raw)
            or directory_offset + directory_size != end
            or (end >= 20 and raw[end - 20 : end - 16] == b"PK\x06\x07")
        ):
            raise ValueError
        cursor, actual_count = directory_offset, 0
        while cursor < end:
            actual_count += 1
            if (
                actual_count > entry_limit
                or cursor + 46 > end
                or raw[cursor : cursor + 4] != b"PK\x01\x02"
            ):
                raise ValueError
            name_size, extra_size, entry_comment_size, start_volume = (
                struct.unpack_from("<4H", raw, cursor + 28)
            )
            compressed, uncompressed = struct.unpack_from("<2L", raw, cursor + 20)
            local_offset = struct.unpack_from("<L", raw, cursor + 42)[0]
            following = cursor + 46 + name_size + extra_size + entry_comment_size
            if (
                name_size == 0
                or start_volume != 0
                or following > end
                or max(compressed, uncompressed, local_offset) == 0xFFFFFFFF
                or local_offset >= directory_offset
            ):
                raise ValueError
            cursor = following
        if cursor != end or actual_count != count:
            raise ValueError
        seen, files, total = set(), [], 0
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            members = archive.infolist()
            if len(members) != actual_count:
                raise ValueError
            for member in members:
                path = safe_path(member.filename)
                mode = member.external_attr >> 16
                if (
                    path.casefold() in seen
                    or path not in allowed
                    or member.is_dir()
                    or stat.S_IFMT(mode) not in {0, stat.S_IFREG}
                    or member.flag_bits & 1
                    or member.compress_type
                    not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
                    or member.file_size > allowed[path].max_bytes
                    or total + member.file_size > max_total_bytes
                ):
                    raise ValueError
                seen.add(path.casefold())
                hashed, size = hashlib.sha256(), 0
                with archive.open(member) as stream:
                    while chunk := stream.read(
                        min(65536, allowed[path].max_bytes - size + 1)
                    ):
                        size += len(chunk)
                        if (
                            size > allowed[path].max_bytes
                            or total + size > max_total_bytes
                        ):
                            raise ValueError
                        hashed.update(chunk)
                if size != member.file_size:
                    raise ValueError
                total += size
                files.append(
                    {
                        "name": allowed[path].name,
                        "path": path,
                        "size": size,
                        "sha256": hashed.hexdigest(),
                        "media_type": allowed[path].media_type,
                    }
                )
        if any(a.required and a.path.casefold() not in seen for a in declared):
            raise ValueError
        return {
            "artifact_id": metadata["id"],
            "run_id": run_id,
            "archive_sha256": archive_digest,
            "files": sorted(files, key=lambda f: f["path"]),
        }
    except (
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        OSError,
        zipfile.BadZipFile,
        NotImplementedError,
        RuntimeError,
        zlib.error,
    ):
        raise ControllerError(
            "E_ARTIFACT",
            "Artifact identity, retention, inventory or bytes failed verification.",
        ) from None
