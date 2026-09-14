"""Real temporary Git objects and ephemeral GPG keys, with no remote operations."""

import base64
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from cg_release.events import ControllerError
from cg_release.process import run_process
from cg_release.signing import _gpg_path, _signer, create_tag, verify_tag


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


def test_signed_object_and_wrong_key_are_verified(signing_key, monkeypatch):
    def observed(tool, args, **kwargs):
        try:
            return run_process(tool, args, **kwargs)
        except ControllerError as error:
            if tool == "gpg" and args[:2] == ["--batch", "--import"]:
                home = kwargs["environment"]["GNUPGHOME"]
                diagnostic = {
                    "import_code": error.code,
                    "home_bytes": len(os.fsencode(home)),
                }
                try:
                    socket = run_process(
                        "gpgconf",
                        ["--homedir", home, "--list-dirs", "agent-socket"],
                        **kwargs,
                        timeout=5,
                    ).stdout.strip()
                    diagnostic["agent_socket_bytes"] = len(os.fsencode(socket))
                except ControllerError as probe_error:
                    diagnostic["socket_probe_code"] = probe_error.code
                # This fixture-only daemon probe creates no keys and cannot detach.
                try:
                    probe = subprocess.run(
                        ["gpg-agent", "--homedir", home, "--daemon", "--no-detach"],
                        cwd=kwargs["cwd"],
                        env=kwargs["environment"],
                        stdin=subprocess.DEVNULL,
                        capture_output=True,
                        timeout=3,
                    )
                    stderr = probe.stderr
                    diagnostic["agent_probe_exit"] = probe.returncode
                except subprocess.TimeoutExpired as probe_error:
                    stderr = probe_error.stderr or b""
                    diagnostic["agent_probe_timed_out"] = True
                except OSError:
                    stderr = b""
                    diagnostic["agent_probe_unavailable"] = True
                diagnostic["socket_too_long"] = (
                    b"socket name" in stderr and b"too long" in stderr
                )
                error.add_note("Offline GPG diagnostic: " + json.dumps(diagnostic))
            raise

    monkeypatch.setattr("cg_release.signing.run_process", observed)
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


@pytest.mark.parametrize("socket_result", ["ok", "failure", "timeout"])
@pytest.mark.parametrize(
    "agent_result", ["exit", "timeout", "timeout-empty", "unavailable"]
)
def test_gpg_failure_diagnostic_preserves_error_and_cleanup(
    tmp_path, monkeypatch, socket_result, agent_result
):
    """Inject every probe outcome without a real key, process, or daemon."""
    key = tmp_path / "fixture-key.asc"
    key.write_bytes(b"fixture-only")
    secret = "fixture-private-value"
    encoded = base64.b64encode(secret.encode()).decode()
    private_path = "/fixture-private/path/" + secret
    noise = (secret + " " + encoded + " " + private_path).encode()
    import_error = ControllerError(
        "E_TIMEOUT", "Process deadline exceeded; reconcile writes."
    )
    monkeypatch.setenv("GH_TOKEN", secret)
    calls, roots, expected = [], [], {"import_code": "E_TIMEOUT"}

    def injected_process(tool, args, **kwargs):
        root = kwargs["cwd"]
        home = _gpg_path(root / "gnupg")
        assert kwargs["environment"]["GNUPGHOME"] == home
        assert "GH_TOKEN" not in kwargs["environment"]
        if tool == "gpg" and args == ["--batch", "--import", _gpg_path(key)]:
            assert kwargs.get("timeout", 20) == 20
            roots.append(root)
            expected["home_bytes"] = len(os.fsencode(home))
            calls.append("import")
            raise import_error
        assert tool == "gpgconf"
        assert root == roots[0]
        if args == ["--homedir", home, "--list-dirs", "agent-socket"]:
            assert kwargs["timeout"] == 5
            calls.append("socket")
            if socket_result != "ok":
                code = "E_PROCESS" if socket_result == "failure" else "E_TIMEOUT"
                expected["socket_probe_code"] = code
                raise ControllerError(code, noise.decode())
            socket_path = home + private_path + "/" + encoded
            expected["agent_socket_bytes"] = len(os.fsencode(socket_path))
            return subprocess.CompletedProcess(
                [], 0, " " + socket_path + "\n", noise.decode()
            )
        assert args == ["--homedir", home, "--kill", "gpg-agent"]
        assert kwargs["allow_failure"] is True
        assert kwargs.get("timeout", 20) == 20
        calls.append("cleanup")
        return subprocess.CompletedProcess([], 0, "", "")

    def injected_agent(argv, **kwargs):
        root = roots[0]
        home = _gpg_path(root / "gnupg")
        assert argv == ["gpg-agent", "--homedir", home, "--daemon", "--no-detach"]
        assert kwargs["cwd"] == root
        assert kwargs["env"]["GNUPGHOME"] == home
        assert "GH_TOKEN" not in kwargs["env"]
        assert kwargs["timeout"] == 3
        assert kwargs["capture_output"] is True
        assert kwargs["stdin"] == subprocess.DEVNULL
        calls.append("agent")
        stderr = b"socket name " + noise + b" too long"
        if agent_result == "unavailable":
            expected.update(agent_probe_unavailable=True, socket_too_long=False)
            raise FileNotFoundError(noise.decode())
        if agent_result.startswith("timeout"):
            empty = agent_result == "timeout-empty"
            expected.update(agent_probe_timed_out=True, socket_too_long=not empty)
            raise subprocess.TimeoutExpired(
                argv, 3, output=noise, stderr=None if empty else stderr
            )
        expected.update(agent_probe_exit=2, socket_too_long=True)
        return subprocess.CompletedProcess(argv, 2, noise, stderr)

    def forbidden(*args, **kwargs):
        pytest.fail("Injected GPG diagnostic must not start a real subprocess")

    monkeypatch.setattr(f"{__name__}.run_process", injected_process)
    monkeypatch.setattr(subprocess, "run", injected_agent)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    with pytest.raises(ControllerError) as caught:
        test_signed_object_and_wrong_key_are_verified((key, "A" * 40), monkeypatch)
    assert caught.value is import_error
    assert caught.value.code == "E_TIMEOUT"
    assert str(caught.value) == "Process deadline exceeded; reconcile writes."
    assert len(caught.value.__notes__) == 1
    note = caught.value.__notes__[0]
    prefix = "Offline GPG diagnostic: "
    assert note.startswith(prefix)
    assert json.loads(note[len(prefix) :]) == expected
    assert all(
        value not in note
        for value in (secret, encoded, private_path, _gpg_path(roots[0] / "gnupg"))
    )
    assert calls == ["import", "socket", "agent", "cleanup"]
    assert not roots[0].exists()
    assert key.read_bytes() == b"fixture-only"


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


@pytest.mark.parametrize("interrupted", [False, True])
def test_signer_keeps_short_private_home_isolation_and_cleanup(
    tmp_path, monkeypatch, interrupted
):
    """The socket-path repair must retain private key storage and scoped cleanup."""
    key = tmp_path / "fixture-key.asc"
    key.write_bytes(b"fixture-only")
    fingerprint = "A" * 40
    monkeypatch.setenv("GH_TOKEN", "fixture-secret-must-not-leak")
    monkeypatch.setenv("GNUPGHOME", "untrusted-inherited-home")
    calls = []
    roots = []

    def observed(tool, args, **kwargs):
        root = kwargs["cwd"]
        home = root / "gnupg"
        assert root.name.startswith("cg-sign-")
        # Include the longest default socket name, not only S.gpg-agent.
        assert len(os.fsencode(root.name + "/gnupg/S.gpg-agent.browser")) <= 42
        assert home.is_dir() and not home.is_symlink()
        if os.name != "nt":
            assert stat.S_IMODE(root.stat().st_mode) == 0o700
            assert stat.S_IMODE(home.stat().st_mode) == 0o700
        env = kwargs["environment"]
        assert env["GNUPGHOME"] == _gpg_path(home)
        assert "GH_TOKEN" not in env
        assert "untrusted-inherited-home" not in env.values()
        assert env["GIT_CONFIG_NOSYSTEM"] == "1"
        assert env["GIT_CONFIG_GLOBAL"] == os.devnull
        assert kwargs.get("timeout", 20) == 20
        calls.append((tool, args, kwargs.get("allow_failure", False)))
        roots.append(root)
        return subprocess.CompletedProcess(
            [], 0, "fpr:::::::::" + fingerprint + ":\n", ""
        )

    monkeypatch.setattr("cg_release.signing.run_process", observed)
    try:
        with _signer(key, fingerprint):
            if interrupted:
                raise RuntimeError("fixture interruption")
    except RuntimeError:
        assert interrupted
    assert len(calls) == 3
    assert calls[0][1][:2] == ["--batch", "--import"]
    assert calls[-1] == (
        "gpgconf",
        ["--homedir", _gpg_path(roots[-1] / "gnupg"), "--kill", "gpg-agent"],
        True,
    )
    assert all(not root.exists() for root in roots)
    assert key.read_bytes() == b"fixture-only"
