"""Real temporary Git objects and ephemeral GPG keys, with no remote operations."""

import os
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from cg_release.events import ControllerError
from cg_release.signing import _gpg_path, create_tag, verify_tag


def test_annotated_object_is_exact_and_reusable(tmp_path):
    tag = create_tag(
        "v1.5.0", "a" * 40, "Release Bot", "release@example.invalid", 1720000000
    )
    subprocess.run(
        ["git", "init", "--bare", str(tmp_path)], check=True, capture_output=True
    )
    result = subprocess.run(
        ["git", "hash-object", "-t", "tag", "--stdin", "-w"],
        cwd=tmp_path,
        input=tag["text"].encode(),
        capture_output=True,
        check=True,
    )
    assert result.stdout.decode().strip() == tag["oid"]
    verify_tag(tag, "v1.5.0", "a" * 40)
    assert tag == create_tag(
        "v1.5.0", "a" * 40, "Release Bot", "release@example.invalid", 1720000000
    )


@pytest.mark.parametrize("tag", ["--force", "v1\nobject x", "v1..2", "v1:other"])
def test_hostile_tag_rejected(tag):
    with pytest.raises(ControllerError):
        create_tag(tag, "a" * 40, "Bot", "bot@example.invalid", 1720000000)


def test_object_mismatch_and_lightweight_object_rejected():
    tag = create_tag("v1.5.0", "a" * 40, "Bot", "bot@example.invalid", 1720000000)
    for changed in ({**tag, "oid": "b" * 40}, {**tag, "text": "a" * 40}):
        with pytest.raises(ControllerError):
            verify_tag(changed, "v1.5.0", "a" * 40)


@pytest.fixture
def signing_key(tmp_path, monkeypatch):
    # Git for Windows bundles GPG but does not add usr/bin to normal PATH.
    git = Path(shutil.which("git")).resolve()
    bundled = git.parent.parent / "usr/bin"
    if not shutil.which("gpg") and (bundled / "gpg.exe").is_file():
        monkeypatch.setenv("PATH", str(bundled) + os.pathsep + os.environ["PATH"])
    assert shutil.which("gpg"), "Required local GPG test tool is unavailable"
    # GPG's local agent socket cannot use pytest's deeply nested Windows path.
    temporary = TemporaryDirectory(prefix="cg-key-")
    home = Path(temporary.name)
    args = [
        "gpg",
        "--homedir",
        _gpg_path(home),
        "--batch",
        "--pinentry-mode",
        "loopback",
    ]
    generated = subprocess.run(
        [
            *args,
            "--passphrase",
            "",
            "--quick-generate-key",
            "Fixture <fixture@example.invalid>",
            "ed25519",
            "sign",
            "0",
        ],
        check=False,
        capture_output=True,
        timeout=30,
    )
    if generated.returncode:
        diagnosis = subprocess.run(
            ["gpg-agent", "--homedir", _gpg_path(home), "--server"],
            input=b"",
            capture_output=True,
            timeout=20,
        )
        pytest.fail((generated.stderr + diagnosis.stderr).decode(errors="replace"))
    listing = subprocess.run(
        [*args, "--with-colons", "--list-secret-keys"],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    fingerprint = next(
        line.split(":")[9]
        for line in listing.stdout.splitlines()
        if line.startswith("fpr:")
    )
    exported = subprocess.run(
        [*args, "--armor", "--export-secret-keys", fingerprint],
        check=True,
        capture_output=True,
        timeout=20,
    ).stdout
    key = tmp_path / "fixture-key.asc"
    key.write_bytes(exported)
    yield key, fingerprint
    subprocess.run(
        ["gpgconf", "--homedir", _gpg_path(home), "--kill", "gpg-agent"],
        capture_output=True,
        timeout=20,
    )
    temporary.cleanup()


def test_signed_object_and_wrong_key_are_verified(signing_key):
    key, fingerprint = signing_key
    tag = create_tag(
        "v1.5.0",
        "a" * 40,
        "Bot",
        "bot@example.invalid",
        1720000000,
        key_file=key,
        fingerprint=fingerprint,
    )
    assert "BEGIN PGP SIGNATURE" in tag["text"]
    verify_tag(tag, "v1.5.0", "a" * 40, key_file=key, fingerprint=fingerprint)
    with pytest.raises(ControllerError):
        verify_tag(tag, "v1.5.0", "a" * 40, key_file=key, fingerprint="A" * 40)


def test_requested_signing_requires_key():
    with pytest.raises(ControllerError):
        create_tag(
            "v1.5.0",
            "a" * 40,
            "Bot",
            "bot@example.invalid",
            1720000000,
            fingerprint="A" * 40,
        )
