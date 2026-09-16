"""Offline parity checks for the compatibility readers and immutable grace."""

import ast
import importlib
import inspect
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from skill_management.services import release_attestation

CORPUS = json.loads((ROOT / "packages/cg-release/tests/fixtures/versions.json").read_text())


@pytest.mark.parametrize("name", [
    "cg_pr_preflight", "cg_validate_modules",
    "skill_management.services.release_attestation",
])
def test_attestation_and_native_annotations_keep_python38_grammar(name):
    """The ordinary Python 3.8 reader job also imports the lint-touched natives."""
    module = importlib.import_module(name)
    source = Path(module.__file__).read_text(encoding="utf-8")
    ast.parse(source, feature_version=8)
    functions = [
        value for value in vars(module).values()
        if inspect.isfunction(value) and value.__module__ == name
    ]
    assert functions
    assert all(
        isinstance(annotation, str)
        for function in functions for annotation in function.__annotations__.values()
    )
    if name == "cg_pr_preflight":
        from typing import Tuple
        assert module.Command == Tuple[str, ...]  # Evaluated alias must work on 3.8.
        assert module.full_gate_selection().controller_required


def test_attestation_numeric_prerelease_order():
    """Numeric identifiers must not use suffix string order."""
    key = release_attestation._version_key
    assert key("v1.5.0-rc.2") < key("v1.5.0-rc.10") < key("v1.5.0")
    assert sorted(CORPUS["ascending"], key=lambda value: key("v" + value)) == CORPUS["ascending"]


@pytest.mark.parametrize("value", CORPUS["invalid"])
def test_attestation_rejects_invalid_semver(value):
    with pytest.raises(release_attestation.ReleaseAttestationError):
        release_attestation._version_key("v" + value)


@pytest.mark.parametrize("left,right", CORPUS["equivalent"])
def test_build_metadata_does_not_create_grace(left, right):
    assert release_attestation._version_key("v" + left) == release_attestation._version_key("v" + right)


def test_node_payload_accepts_semver_without_mutation():
    source = """
const fs = require('node:fs');
const {validatePayload} = require('./scripts/generate-whats-new.js');
const payload = JSON.parse(fs.readFileSync('releases/latest.json', 'utf8'));
for (const tag of ['v1.5.0-rc.2', 'v1.5.0-rc.10', 'v1.5.0+build.01']) {
  const value = {...payload, tag, url: `https://github.com/GPID-WB/compound-gpid/releases/tag/${tag}`,
    sourceUrl: `https://github.com/GPID-WB/compound-gpid/tree/${tag}`};
  validatePayload(value, tag);
}
"""
    result = subprocess.run(["node", "-e", source], cwd=ROOT, capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("tags,expected", [
    *[(["v1.0.0-" + a, "v1.0.0-" + b], ["v1.0.0-" + b, "v1.0.0-" + a])
      for a, b in [("alpha", "alpha1"), ("rc", "rca"), ("a", "aa"), ("a", "a-")]],
    (
        ["v1.5.0-rc.2", "v1.5.0", "v1.5.0-rc.10"],
        ["v1.5.0", "v1.5.0-rc.10", "v1.5.0-rc.2"],
    ),
    (
        ["v1.0.0-rc.999999999999999999998", "v1.0.0-rc.999999999999999999999"],
        ["v1.0.0-rc.999999999999999999999", "v1.0.0-rc.999999999999999999998"],
    ),
    (
        ["v999999999999999999998.0.0", "v999999999999999999999.0.0"],
        ["v999999999999999999999.0.0", "v999999999999999999998.0.0"],
    ),
])
def test_bash_actual_reader_corpus(tmp_path, tags, expected):
    """Execute only the actual pure reader region in Git Bash or native Bash."""
    bash = shutil.which("bash")
    if sys.platform == "win32":
        candidate = Path("C:/Program Files/Git/bin/bash.exe")
        bash = str(candidate) if candidate.is_file() else bash
    assert bash, "Bash is required for offline shell-reader parity"
    source = (ROOT / "scripts/update.sh").read_text(encoding="utf-8")
    region = re.search(r"# BEGIN RELEASE READERS(.*?)# END RELEASE READERS", source, re.DOTALL)
    assert region, "updater must expose its actual side-effect-free reader region"
    script = region[1] + "\n"
    # Environment transport avoids shell interpolation of hostile fixture values.
    import os
    env = dict(os.environ)
    for index, value in enumerate(CORPUS["valid"] + ["1.5.0.9000"]):
        env[f"V{index}"] = "v" + value
        script += f'[[ "$V{index}" =~ $VERSION_ACCEPT_PATTERN ]] || exit 11\n'
    for index, value in enumerate(CORPUS["invalid"]):
        env[f"I{index}"] = "v" + value
        script += f'if [[ "$I{index}" =~ $VERSION_ACCEPT_PATTERN ]]; then exit 12; fi\n'
    for index, tag in enumerate(tags):
        env[f"SORT{index}"] = tag
    arguments = " ".join(f'"$SORT{index}"' for index in range(len(tags)))
    script += f"printf '%s\\n' {arguments} | cg_sort_release_tags\n"
    result = subprocess.run([bash, "--noprofile", "--norc", "-c", script], env=env,
                            capture_output=True, text=True, timeout=30, cwd=tmp_path, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == expected


@pytest.mark.parametrize("show_dev", [False, True])
def test_powershell_clean_client_list(tmp_path, show_dev):
    """Execute the complete updater with fixture-only Git and profile helpers."""
    shell = shutil.which("powershell") or shutil.which("pwsh")
    assert shell, "PowerShell is required for clean-client reader evidence"
    scripts = tmp_path / "install/scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(ROOT / "scripts/update.ps1", scripts / "update.ps1")
    pin = scripts.parent / ".cg-version"
    pin.write_text("v1.5.0-rc.10", encoding="utf-8")
    (scripts / "helpers.ps1").write_text(
        "function Remove-LegacyProfileCommands {}\n"
        "function git { $global:LASTEXITCODE = 0; if ($args[0] -eq 'tag') { "
        "'v1.5.0-rc.2'; 'v1.5.0.9000'; 'v1.5.0'; 'v1.5.0-rc.10'; 'v1.4.0'; 'v1.0.0+build-x' } }\n",
        encoding="utf-8",
    )
    result = subprocess.run([shell, "-NoProfile", "-File", str(scripts / "update.ps1"),
                             "-List", *(["-ShowDev"] if show_dev else [])],
                            cwd=tmp_path, capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stderr
    listing = result.stdout.split("Available releases:")[1].split("Current:")[0]
    assert "v1.5.0\n" in listing
    assert "v1.0.0+build-x (pre-release)" not in listing
    assert ("v1.5.0-rc.10" in listing) is show_dev
    assert ("v1.5.0.9000" in listing) is show_dev
    if show_dev:
        assert listing.index("rc.10") < listing.index("rc.2")
        assert "(pre-release)" in listing and "(legacy dev)" in listing
    assert pin.read_text() == "v1.5.0-rc.10"


@pytest.mark.parametrize("shell_kind", ["powershell", "bash"])
def test_old_updater_bridge_then_new_pin_offline(tmp_path, shell_kind):
    """Run the frozen source.json-hashed historical reader, then the current reader.

    These are fixture identities, not evidence of bridge delivery or live Releases.
    """
    import os
    extension = "ps1" if shell_kind == "powershell" else "sh"
    filename = "scripts/update." + extension
    import hashlib
    fixtures = ROOT / "scripts/tests/fixtures/release-bridge"
    old = (fixtures / ("update." + extension + ".fixture")).read_bytes()
    source = json.loads((fixtures / "source.json").read_text())
    assert hashlib.sha256(old).hexdigest() == source["sha256"]["update." + extension]
    repo = tmp_path / "origin"
    repo.mkdir()
    env = dict(os.environ, GIT_AUTHOR_NAME="Fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
               GIT_COMMITTER_NAME="Fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid",
               CG_INTERNAL_CALL="1", GIT_TERMINAL_PROMPT="0")

    def git(*args, cwd=repo):
        return subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True,
                              text=True, check=True, timeout=30).stdout.strip()

    git("init", "-b", "main")
    (repo / "scripts").mkdir()
    (repo / filename).write_bytes(old)
    (repo / "scripts/helpers.ps1").write_text("function Remove-LegacyProfileCommands {}\n")
    (repo / ".gitignore").write_text(".cg-version\n")
    (repo / ".gitattributes").write_text("* -text\n")
    git("add", ".")
    git("commit", "-m", "old fixture reader")
    git("tag", "v1.0.0")
    client = tmp_path / "client"
    git("clone", str(repo), str(client), cwd=tmp_path)
    (repo / filename).write_bytes((ROOT / filename).read_bytes())
    git("add", filename)
    git("commit", "-m", "bridge fixture reader")
    git("tag", "v1.0.1")
    git("tag", "v1.1.0-rc.10")
    consumer = tmp_path / "consumer"
    consumer.mkdir()

    def update(tag):
        entry = client / filename
        if shell_kind == "powershell":
            shell = shutil.which("powershell") or shutil.which("pwsh")
            assert shell
            argv = [shell, "-NoProfile", "-File", str(entry), tag]
        else:
            shell = "C:/Program Files/Git/bin/bash.exe" if os.name == "nt" else shutil.which("bash")
            argv = [shell, "--noprofile", "--norc", entry.as_posix(), tag]
        return subprocess.run(argv, cwd=consumer, env=env, capture_output=True, text=True, timeout=60, check=False)

    rejected = update("v1.1.0-rc.10")
    assert rejected.returncode != 0
    assert not (client / ".cg-version").exists()
    for tag in ["v1.0.1", "v1.1.0-rc.10"]:
        result = update(tag)
        assert result.returncode == 0, result.stdout + result.stderr
        assert (client / ".cg-version").exists(), result.stdout + result.stderr
        assert (client / ".cg-version").read_text().strip() == tag
        assert git("rev-parse", "HEAD", cwd=client) == git("rev-parse", tag)
    assert (client / filename).read_bytes() == (ROOT / filename).read_bytes()
