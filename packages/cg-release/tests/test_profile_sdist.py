"""Build identical sdist bytes with hostile external resources and no source tree."""

import hashlib
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
RESOURCES = (
    "release_profile_gpid.py",
    "docs-snapshots.js",
    "snapshot-data.js",
    "release-version.js",
)


def build(root, output, kind):
    """Execute the actual backend in scratch; return its only distribution."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--" + kind,
            "--outdir",
            str(output),
            str(root),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return next(output.glob("*.tar.gz" if kind == "sdist" else "*.whl"))


def test_identical_sdist_uses_complete_bundled_resources(tmp_path):
    sdist = build(PACKAGE, tmp_path / "dist", "sdist")
    original_digest = hashlib.sha256(sdist.read_bytes()).hexdigest()
    inventories = []
    for parent in (tmp_path / "clean", tmp_path / "hostile/tmp"):
        parent.mkdir(parents=True)
        with tarfile.open(sdist) as archive:
            archive.extractall(parent, filter="data")
        root = next(parent.glob("cg_release-*"))
        if "hostile" in parent.parts:
            external = parent.parent / "scripts"
            external.mkdir()
            for name in RESOURCES:
                (external / name).write_text("raise RuntimeError('hostile external')")
        wheel = build(root, parent / "wheel", "wheel")
        with zipfile.ZipFile(wheel) as archive:
            names = ["_cg_release_gpid.py"] + [
                "cg_release_profile_data/" + name for name in RESOURCES[1:]
            ]
            inventory = {name: archive.read(name) for name in names}
            assert (
                inventory["_cg_release_gpid.py"]
                == (root / "profile" / RESOURCES[0]).read_bytes()
            )
            inventories.append(inventory)
    assert inventories[0] == inventories[1]
    assert hashlib.sha256(sdist.read_bytes()).hexdigest() == original_digest


def test_incomplete_sdist_never_uses_surrounding_scripts(tmp_path):
    sdist = build(PACKAGE, tmp_path / "dist", "sdist")
    parent = tmp_path / "hostile/tmp"
    parent.mkdir(parents=True)
    with tarfile.open(sdist) as archive:
        archive.extractall(parent, filter="data")
    root = next(parent.glob("cg_release-*"))
    (root / "profile/snapshot-data.js").unlink()
    external = parent.parent / "scripts"
    external.mkdir()
    for name in RESOURCES:
        (external / name).write_text("external")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--wheel",
            "--outdir",
            str(tmp_path / "wheel"),
            str(root),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode != 0
    assert "Incomplete bundled profile" in result.stderr + result.stdout


def test_repository_markers_alone_cannot_enable_source_fallback(tmp_path):
    root = tmp_path / "pretend-repository"
    package = root / "packages/cg-release"
    package.mkdir(parents=True)
    for name in ("pyproject.toml", "hatch_build.py"):
        shutil.copy2(PACKAGE / name, package / name)
    shutil.copytree(
        PACKAGE / "src", package / "src", ignore=shutil.ignore_patterns("__pycache__")
    )
    (root / ".github/shared").mkdir(parents=True)
    (root / ".github/shared/module-registry.json").write_text("{}")
    (root / "compound-gpid.md").write_text("marker-only")
    (root / ".git").write_text("not a git repository")
    (root / "scripts").mkdir()
    for name in RESOURCES:
        (root / "scripts" / name).write_text("hostile external content")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--wheel",
            "--outdir",
            str(tmp_path / "wheel"),
            str(package),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode != 0
    assert "Unverified canonical" in result.stdout + result.stderr
