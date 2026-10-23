"""Synthetic 9021 receipt tests for narrow native-evidence retirement."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from scripts import cg_retire_native_evidence as retire


PAYLOAD = b"// synthetic 9021 native-evidence file\n"
DIGEST = hashlib.sha256(PAYLOAD).hexdigest()
LOADER = retire.NATIVE_PATHS[0]
GENERATED = retire.RECEIPTS[0]


def _write(root: Path, relative: str, content: bytes) -> Path:
    """Create a small fixture without touching any installation."""
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _receipt(root: Path, kind: str = "generated") -> Path:
    """Write the existing receipt wire format, not a new ownership schema."""
    if kind == "generated":
        relative = GENERATED
        data = {
            "schemaVersion": 1, "target": "kilo", "policyVersion": 1,
            "files": [
                {"path": path, "source": path.replace(".kilo/", ".github/", 1),
                 "kind": "native-plugin", "sha256": DIGEST, "executable": False}
                for path in retire.NATIVE_PATHS
            ],
        }
    elif kind == "copy":
        for index in (1, 2):
            relative = retire.RECEIPTS[index]
            source = relative.rsplit("/", 1)[0]
            data = {"schemaVersion": 1, "source": source, "files": {
                path[len(source) + 1:]: DIGEST for path in retire.NATIVE_PATHS
                if path.startswith(source + "/")
            }}
            _write(root, relative, json.dumps(data).encode())
        return root / retire.RECEIPTS[1]
    elif kind == "scalar":
        relative = retire.RECEIPTS[3]
        data = {"schemaVersion": "compound-gpid-managed-files-v1", "files": {
            path: {"source": path, "checksum": DIGEST} for path in retire.NATIVE_PATHS
        }}
    else:
        relative = retire.RECEIPTS[4]
        data = {"schemaVersion": 1, "entries": {
            path: {"sha256": DIGEST, "platform": "kilo",
                   "source": path.replace(".kilo/", ".github/", 1),
                   "kind": "native-plugin", "preserved": False,
                   "origin": "plugin-canonical", "provenanceIdentity": "canonical/.github"}
            for path in retire.NATIVE_PATHS
        }}
    return _write(root, relative, json.dumps(data).encode("utf-8"))


@pytest.mark.parametrize("kind", ["generated", "copy", "scalar", "projection"])
def test_unchanged_owned_files_deleted_and_all_evidence_preserved(
    tmp_path: Path, kind: str
) -> None:
    for path in retire.NATIVE_PATHS:
        _write(tmp_path, path, PAYLOAD)
    _receipt(tmp_path, kind)
    protected = [
        LOADER + ".disabled", ".kilo/kilo.json", ".kilo/kilo.jsonc",
        ".opencode/opencode.json", "kilo.json", ".kilo/agent-manager.json",
        ".kilo/plugins/user-plugin.js", ".kilo/plugins/.keep",
        ".compound-gpid/projection-transaction.json", ".compound-gpid-ownership.lock",
        ".compound-gpid/skill-transaction.lock", ".compound-gpid/runtime/journal.json",
        ".github/plugins/cg-native-evidence.js",
        ".github/plugin-support/cg-native-evidence/evidence.mjs",
    ]
    for relative in protected:
        _write(tmp_path, relative, b"private fixture sentinel\n")
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    observed_reads: list[str] = []
    original = retire.secure_fs.secure_read_bytes

    def observe(root: Path, relative: str, **kwargs: object) -> bytes:
        normalized = Path(relative).as_posix()
        observed_reads.append(normalized)
        assert normalized in (*retire.NATIVE_PATHS, *retire.RECEIPTS)
        return original(root, relative, **kwargs)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(retire.secure_fs, "secure_read_bytes", observe)
        deleted, preserved = retire.retire_native_evidence(tmp_path)
    assert deleted == list(retire.NATIVE_PATHS)
    assert not preserved
    assert observed_reads
    for path, content in before.items():
        if path.relative_to(tmp_path).as_posix() in retire.NATIVE_PATHS:
            assert not path.exists()
        else:
            assert path.read_bytes() == content
    assert (tmp_path / ".kilo/plugins").is_dir()
    assert (tmp_path / ".kilo/plugin-support/cg-native-evidence").is_dir()
    assert retire.retire_native_evidence(tmp_path) == ([], {})


@pytest.mark.parametrize("owned", [True, False])
def test_modified_and_unowned_preserved_and_block_cli(
    tmp_path: Path, owned: bool, capsys: pytest.CaptureFixture[str]
) -> None:
    loader = _write(tmp_path, LOADER, b"user changes\n" if owned else PAYLOAD)
    if owned:
        receipt = _receipt(tmp_path)
        before = receipt.read_bytes()
    assert retire.main(["--root", str(tmp_path)]) == 1
    assert loader.read_bytes() == (b"user changes\n" if owned else PAYLOAD)
    if owned:
        assert receipt.read_bytes() == before
    output = capsys.readouterr().err
    assert LOADER in output
    assert "Preserved" in output and "manually" in output
    assert "Do not launch Kilo" in output


@pytest.mark.parametrize("bad", [
    b"{", b"[]", b'{"schemaVersion":true,"files":[]}',
    b'{"schemaVersion":1,"schemaVersion":1,"files":[]}',
    b'{"schemaVersion":1,"target":"opencode","policyVersion":1,"files":[]}',
])
def test_malformed_receipt_never_authorizes_deletion(tmp_path: Path, bad: bytes) -> None:
    loader = _write(tmp_path, LOADER, PAYLOAD)
    receipt = _write(tmp_path, GENERATED, bad)
    deleted, preserved = retire.retire_native_evidence(tmp_path)
    assert not deleted and LOADER in preserved
    assert loader.read_bytes() == PAYLOAD and receipt.read_bytes() == bad


@pytest.mark.parametrize("field,value", [
    ("source", "../private"), ("sha256", "invalid"), ("kind", "config"),
    ("executable", True), ("path", LOADER + ".disabled"),
])
def test_invalid_claim_preserves_file(tmp_path: Path, field: str, value: object) -> None:
    loader = _write(tmp_path, LOADER, PAYLOAD)
    receipt = _receipt(tmp_path)
    data = json.loads(receipt.read_bytes())
    data["files"][0][field] = value
    receipt.write_text(json.dumps(data), encoding="utf-8")
    deleted, preserved = retire.retire_native_evidence(tmp_path)
    assert not deleted and LOADER in preserved
    assert loader.read_bytes() == PAYLOAD


def test_conflicting_receipts_preserve_whole_set(tmp_path: Path) -> None:
    loader = _write(tmp_path, LOADER, PAYLOAD)
    _receipt(tmp_path)
    receipt = _receipt(tmp_path, "copy")
    data = json.loads(receipt.read_bytes())
    data["files"]["cg-native-evidence.js"] = "0" * 64
    receipt.write_text(json.dumps(data), encoding="utf-8")
    deleted, preserved = retire.retire_native_evidence(tmp_path)
    assert not deleted and "conflicting" in preserved[LOADER]
    assert loader.read_bytes() == PAYLOAD


def test_duplicate_destination_is_not_ownership_proof(tmp_path: Path) -> None:
    _write(tmp_path, LOADER, PAYLOAD)
    receipt = _receipt(tmp_path)
    data = json.loads(receipt.read_bytes())
    data["files"].append(data["files"][0])
    receipt.write_text(json.dumps(data), encoding="utf-8")
    deleted, preserved = retire.retire_native_evidence(tmp_path)
    assert not deleted and "duplicate" in preserved[LOADER]


@pytest.mark.parametrize("alias", [
    "./cg-native-evidence.js", "nested/../cg-native-evidence.js",
    "nested//file.js", "nested/./file.js", "nested\\file.js",
    "CG-native-evidence.js", "cg-native-evidence.js.", "cg-native-evidence.js ",
])
def test_noncanonical_receipt_key_cannot_hide_conflicting_claim(
    tmp_path: Path, alias: str
) -> None:
    loader = _write(tmp_path, LOADER, PAYLOAD)
    receipt = _receipt(tmp_path, "copy")
    data = json.loads(receipt.read_bytes())
    data["files"][alias] = "0" * 64
    receipt.write_text(json.dumps(data), encoding="utf-8")
    before = receipt.read_bytes()
    deleted, preserved = retire.retire_native_evidence(tmp_path)
    assert not deleted and LOADER in preserved
    assert loader.read_bytes() == PAYLOAD and receipt.read_bytes() == before


@pytest.mark.parametrize("receipt_link", [False, True])
@pytest.mark.parametrize("hardlink", [False, True])
def test_links_and_hardlinks_rejected(
    tmp_path: Path, receipt_link: bool, hardlink: bool
) -> None:
    loader = _write(tmp_path, LOADER, PAYLOAD)
    receipt = _receipt(tmp_path)
    target = receipt if receipt_link else loader
    outside = tmp_path / "outside-sentinel"
    content = target.read_bytes()
    target.rename(outside)
    try:
        if hardlink:
            os.link(outside, target)
        else:
            target.symlink_to(outside)
    except OSError as error:
        pytest.skip(f"fixture link creation unavailable: {error}")
    deleted, preserved = retire.retire_native_evidence(tmp_path)
    assert not deleted and LOADER in preserved
    assert os.path.lexists(target) and outside.read_bytes() == content


def test_directory_link_rejected_without_following(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    loader = _write(outside, "plugins/cg-native-evidence.js", PAYLOAD)
    try:
        (tmp_path / ".kilo").symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"fixture directory link unavailable: {error}")
    deleted, preserved = retire.retire_native_evidence(tmp_path)
    assert not deleted and LOADER in preserved
    assert loader.read_bytes() == PAYLOAD


@pytest.mark.skipif(os.name != "nt", reason="Windows junction fixture")
def test_windows_junction_ancestor_rejected(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    loader = _write(outside, "cg-native-evidence.js", PAYLOAD)
    kilo = tmp_path / ".kilo"
    kilo.mkdir()
    junction = kilo / "plugins"
    result = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(outside)],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        pytest.skip(f"junction fixture unavailable: {result.stderr}")
    try:
        deleted, preserved = retire.retire_native_evidence(tmp_path)
        assert not deleted and LOADER in preserved
        assert loader.read_bytes() == PAYLOAD
    finally:
        junction.rmdir()


@pytest.mark.parametrize("swap", ["receipt", "new-receipt", "file", "hardlink"])
def test_delete_boundary_rechecks_evidence_and_aliases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, swap: str
) -> None:
    loader = _write(tmp_path, LOADER, PAYLOAD)
    receipt = _receipt(tmp_path)
    original = retire.secure_fs.secure_delete_verified

    def mutate(root: Path, relative: str, checksum: str, **kwargs: object) -> None:
        if swap == "receipt":
            receipt.write_bytes(b"{}")
        elif swap == "new-receipt":
            _receipt(tmp_path, "scalar")
        elif swap == "hardlink":
            os.link(loader, tmp_path / "alias")
        else:
            loader.write_bytes(b"changed at boundary")
        original(root, relative, checksum, **kwargs)

    monkeypatch.setattr(retire.secure_fs, "secure_delete_verified", mutate)
    deleted, preserved = retire.retire_native_evidence(tmp_path)
    assert not deleted and "deletion stopped" in preserved[LOADER]
    assert loader.exists()
    assert loader.read_bytes() == (b"changed at boundary" if swap == "file" else PAYLOAD)


def test_empty_root_is_idempotent_and_creates_nothing(tmp_path: Path) -> None:
    assert retire.retire_native_evidence(tmp_path) == ([], {})
    assert retire.retire_native_evidence(tmp_path) == ([], {})
    assert list(tmp_path.iterdir()) == []


def test_modified_file_blocks_other_unchanged_deletion(tmp_path: Path) -> None:
    for relative in retire.NATIVE_PATHS:
        _write(tmp_path, relative, PAYLOAD)
    _receipt(tmp_path)
    (tmp_path / LOADER).write_bytes(b"user modified")
    deleted, preserved = retire.retire_native_evidence(tmp_path)
    assert not deleted and set(preserved) == set(retire.NATIVE_PATHS)
    assert all((tmp_path / relative).exists() for relative in retire.NATIVE_PATHS)


@pytest.mark.parametrize("name", ["kilo.json", "kilo.jsonc", "opencode.json", "opencode.jsonc"])
@pytest.mark.parametrize("parent", ["", ".kilo/", ".opencode/", "nested/project/"])
def test_private_config_names_ignored_at_any_depth(
    tmp_path: Path, name: str, parent: str
) -> None:
    """Use an offline Git fixture, with no user or system Git configuration."""
    git = shutil.which("git")
    if git is None:
        pytest.skip("Git unavailable")
    env = os.environ.copy()
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    repo_root = Path(__file__).resolve().parents[2]
    shutil.copyfile(repo_root / ".gitignore", tmp_path / ".gitignore")
    subprocess.run([git, "init", "-q", str(tmp_path)], env=env, check=True, capture_output=True)
    relative = parent + name
    result = subprocess.run(
        [git, "check-ignore", "--no-index", relative], cwd=tmp_path,
        env=env, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0 and result.stdout.strip() == relative
