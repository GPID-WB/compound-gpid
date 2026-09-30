"""Artifact archives are bounded data and must match their registered run."""

import hashlib
import io
import stat
import struct
import zipfile

import pytest

from cg_release.artifacts import verify_archive
from cg_release.events import ControllerError
from cg_release.models import Artifact


def archive(name="dist/file.bin", data=b"release", mode=None):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as zipped:
        info = zipfile.ZipInfo(name)
        if mode is not None:
            info.external_attr = mode << 16
        zipped.writestr(info, data)
    return output.getvalue()


def metadata(raw):
    return {
        "id": 51,
        "name": "release-assets",
        "expired": False,
        "size_in_bytes": len(raw),
        "digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "workflow_run": {"id": 21, "head_sha": "c" * 40},
    }


def declared():
    return [
        Artifact(
            name="file.bin",
            path="dist/file.bin",
            media_type="application/octet-stream",
            required=True,
            max_bytes=10,
        )
    ]


def test_registered_archive_produces_only_verified_byte_inventory():
    raw = archive()
    result = verify_archive(
        raw,
        metadata(raw),
        run_id=21,
        controller_sha="c" * 40,
        declared=declared(),
        max_total_bytes=10,
        max_artifacts=1,
    )
    assert result["files"][0]["sha256"] == hashlib.sha256(b"release").hexdigest()


@pytest.mark.parametrize(
    "case",
    [
        "other-run",
        "expired",
        "digest",
        "traversal",
        "absolute",
        "symlink",
        "oversize",
        "undeclared",
    ],
)
def test_swapped_expired_or_unsafe_artifact_is_rejected(case):
    raw = archive()
    if case == "traversal":
        raw = archive("../file.bin")
    elif case == "absolute":
        raw = archive("/dist/file.bin")
    elif case == "symlink":
        raw = archive(mode=stat.S_IFLNK | 0o777)
    elif case == "oversize":
        raw = archive(data=b"x" * 11)
    elif case == "undeclared":
        raw = archive("unlisted")
    meta = metadata(raw)
    if case == "other-run":
        meta["workflow_run"]["id"] = 22
    elif case == "expired":
        meta["expired"] = True
    elif case == "digest":
        meta["digest"] = "sha256:" + "0" * 64
    with pytest.raises(ControllerError):
        verify_archive(
            raw,
            meta,
            run_id=21,
            controller_sha="c" * 40,
            declared=declared(),
            max_total_bytes=10,
            max_artifacts=1,
        )


@pytest.mark.parametrize("forgery", ["count", "offset", "zip64"])
def test_forged_directory_is_rejected_before_any_zip_parser_allocation(
    monkeypatch, forgery
):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as zipped:
        zipped.writestr("dist/file.bin", b"one")
        if forgery != "offset":
            zipped.writestr("other", b"two")
    raw = bytearray(output.getvalue())
    end = raw.rfind(b"PK\x05\x06")
    if forgery == "count":
        struct.pack_into("<HH", raw, end + 8, 1, 1)
    elif forgery == "offset":
        struct.pack_into("<L", raw, end + 16, 0)
    else:
        size, offset = struct.unpack_from("<LL", raw, end + 12)
        zip64 = struct.pack(
            "<4sQ2H2L4Q", b"PK\x06\x06", 44, 45, 45, 0, 0, 2, 2, size, offset
        )
        locator = struct.pack("<4sLQL", b"PK\x06\x07", 0, end, 1)
        tail = raw[end:]
        struct.pack_into("<HH", tail, 8, 1, 1)
        raw = raw[:end] + zip64 + locator + tail
    raw = bytes(raw)
    monkeypatch.setattr(
        "cg_release.artifacts.zipfile.ZipFile",
        lambda *a: pytest.fail("forged directory reached parser"),
    )
    with pytest.raises(ControllerError):
        verify_archive(
            raw,
            metadata(raw),
            run_id=21,
            controller_sha="c" * 40,
            declared=declared(),
            max_total_bytes=10,
            max_artifacts=1,
        )


def test_excessive_member_inventory_is_rejected_before_zip_object_allocation(
    monkeypatch,
):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as zipped:
        zipped.writestr("dist/file.bin", b"one")
        zipped.writestr("other", b"two")
    raw = output.getvalue()
    monkeypatch.setattr(
        "cg_release.artifacts.zipfile.ZipFile",
        lambda *a: pytest.fail("oversized inventory reached parser"),
    )
    with pytest.raises(ControllerError):
        verify_archive(
            raw,
            metadata(raw),
            run_id=21,
            controller_sha="c" * 40,
            declared=declared(),
            max_total_bytes=10,
            max_artifacts=1,
        )
