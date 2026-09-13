"""Real updater/link continuations against local-only distribution repositories."""

import base64
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from cg_release.bridge_client import roundtrip
from cg_release.events import ControllerError
from cg_release.profile_models import BridgeRelease, BridgeSpec

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def distribution(tmp_path_factory):
    """Use complete real helper dependencies, never no-op helpers or readers alone."""
    root = tmp_path_factory.mktemp("bridge-distribution")
    for name in ("scripts", ".github", ".opencode", "bin"):
        shutil.copytree(
            ROOT / name,
            root / name,
            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "tests"),
        )
    for name in ("compound-gpid.md", "compound-gpid.local.md", "SCHEMA_VERSION"):
        shutil.copy2(ROOT / name, root / name)
    shutil.copy2(ROOT / ".gitattributes", root / ".gitattributes")
    (root / ".gitignore").write_text(".cg-version\n__pycache__/\n")
    for path in (root / "scripts").glob("*.sh"):
        path.chmod(0o755)
    env = dict(
        os.environ,
        GIT_AUTHOR_NAME="Offline Fixture",
        GIT_COMMITTER_NAME="Offline Fixture",
        GIT_AUTHOR_EMAIL="fixture@example.invalid",
        GIT_COMMITTER_EMAIL="fixture@example.invalid",
    )

    def git(*args):
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=90,
        )
        return result.stdout.strip()

    git("init", "-b", "main")
    frozen = ROOT / "scripts/tests/fixtures/release-bridge"
    source = json.loads((frozen / "source.json").read_text())
    for ext in ("ps1", "sh"):
        raw = (frozen / ("update." + ext + ".fixture")).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == source["sha256"]["update." + ext]
        (root / ("scripts/update." + ext)).write_bytes(raw)
    identities = []
    for index, tag in enumerate(["v1.0.0", "v1.0.1", "v1.1.0-rc.10"]):
        if index == 1:
            for ext in ("ps1", "sh"):
                shutil.copy2(
                    ROOT / ("scripts/update." + ext), root / ("scripts/update." + ext)
                )
                if ext == "sh":
                    (root / "scripts/update.sh").chmod(0o755)
        (root / ".opencode/AGENTS.md").write_text(
            "Actual managed fixture revision " + str(index) + "\n"
        )
        git("add", ".")
        git("commit", "-m", "offline distribution " + str(index))
        git("tag", "-a", tag, "-m", "offline only")
        identities.append(
            BridgeRelease(
                tag=tag,
                release_id=10 + index,
                revision=git("rev-parse", "HEAD"),
                tree=git("rev-parse", "HEAD^{tree}"),
                tag_object=git("rev-parse", tag),
            )
        )
    spec = BridgeSpec(
        repository_id=123,
        repository_slug="offline/fixture",
        previous=identities[0],
        bridge=identities[1],
        successor=identities[2],
    )
    return root, spec


def test_actual_client_tree_helpers_managed_refresh_and_link(distribution, tmp_path):
    kind = "windows" if os.name == "nt" else "unix"
    remote, spec = distribution
    result = roundtrip(
        spec, tmp_path / "private client", remote=str(remote), shell_kind=kind
    )
    assert set(result) == {"previous", "bridge", "successor"}
    for key in result:
        assert result[key]["release"] == getattr(spec, key).model_dump(mode="json")
        assert result[key]["pin"] == getattr(spec, key).tag
        assert result[key]["copilot_refreshed"] is True
        assert set(result[key]["managed"]) == {
            ".opencode/AGENTS.md",
            ".opencode/opencode.json",
        }
    assert result["previous"]["managed"] != result["bridge"]["managed"]
    assert result["bridge"]["managed"] != result["successor"]["managed"]


def test_existing_client_directory_cannot_be_used(distribution, tmp_path):
    remote, spec = distribution
    with pytest.raises(ControllerError, match="must not exist"):
        roundtrip(spec, tmp_path, remote=str(remote), shell_kind="unix")


@pytest.mark.parametrize("token_key", ["GH_TOKEN", "GITHUB_TOKEN"])
def test_private_clone_has_exact_scoped_read_credential_without_argv_secret(
    tmp_path, monkeypatch, token_key
):
    token = "offline-token-not-a-credential"
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setenv(token_key, token)
    spec = SimpleNamespace(repository_slug="owner/repo")
    captured = {}

    def spawn(argv, **kwargs):
        captured.update(argv=argv, **kwargs)
        raise RuntimeError("outer transport capture")

    monkeypatch.setattr(subprocess, "run", spawn)
    with pytest.raises(RuntimeError, match="outer transport"):
        roundtrip(
            spec,
            tmp_path / "private",
            remote="https://github.com/owner/repo.git",
            shell_kind="unix",
        )
    env = captured["env"]
    assert token not in str(captured["argv"])
    assert (
        env.get("GIT_CONFIG_KEY_1")
        == "http.https://github.com/owner/repo.git.extraheader"
    )
    assert env["GIT_CONFIG_COUNT"] == "3"
    assert (
        env["GIT_CONFIG_VALUE_1"]
        == "AUTHORIZATION: basic "
        + base64.b64encode(("x-access-token:" + token).encode()).decode()
    )
    assert env["GIT_CONFIG_KEY_2"] == "http.followRedirects"
    assert env.get("GIT_CONFIG_VALUE_2") == "false"
    assert "GH_TOKEN" not in env and "GITHUB_TOKEN" not in env


@pytest.mark.parametrize("token", [None, "", "fake\r\ninjected-header"])
def test_private_clone_rejects_missing_or_malformed_credential_before_subprocess(
    tmp_path, monkeypatch, token
):
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    if token is not None:
        monkeypatch.setenv("GH_TOKEN", token)

    def forbidden(*args, **kwargs):
        pytest.fail("Credential refusal must precede every client subprocess")

    monkeypatch.setattr(subprocess, "run", forbidden)
    with pytest.raises(ControllerError, match="read-only Git credential"):
        roundtrip(
            SimpleNamespace(repository_slug="owner/repo"),
            tmp_path / "private",
            remote="https://github.com/owner/repo.git",
            shell_kind="unix",
        )
    assert not (tmp_path / "private/client").exists()


@pytest.mark.parametrize(
    "remote",
    [
        "https://github.com/owner/other.git",
        "https://other.invalid/owner/repo.git",
        "https://github.com/owner/repo.git/other",
    ],
)
def test_private_clone_rejects_unapproved_remote_before_subprocess(
    tmp_path, monkeypatch, remote
):
    monkeypatch.setenv("GH_TOKEN", "offline-token-not-a-credential")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    def forbidden(*args, **kwargs):
        pytest.fail("Unapproved remote must not receive a client subprocess")

    monkeypatch.setattr(subprocess, "run", forbidden)
    with pytest.raises(ControllerError, match="not the approved repository"):
        roundtrip(
            SimpleNamespace(repository_slug="owner/repo"),
            tmp_path / "private",
            remote=remote,
            shell_kind="unix",
        )


def test_private_clone_error_never_echoes_raw_or_encoded_credential(
    tmp_path, monkeypatch
):
    token = "offline-token-not-a-credential"
    monkeypatch.setenv("GH_TOKEN", token)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    output = []

    def refused(argv, **kwargs):
        raw = (token + "\n" + kwargs["env"]["GIT_CONFIG_VALUE_1"]).encode()
        output.append(raw)
        return subprocess.CompletedProcess(argv, 1, raw, raw)

    monkeypatch.setattr(subprocess, "run", refused)
    with pytest.raises(
        ControllerError, match="credential-bearing child output is withheld"
    ) as error:
        roundtrip(
            SimpleNamespace(repository_slug="owner/repo"),
            tmp_path / "private",
            remote="https://github.com/owner/repo.git",
            shell_kind="unix",
        )
    assert len(output) == 1
    assert all(
        value.decode() not in str(error.value) for value in output[0].splitlines()
    )
