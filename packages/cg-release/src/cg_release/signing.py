"""Exact public annotated tag bytes with isolated GPG signing and verification."""

import hashlib
import os
import re
import shutil
import stat
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from cg_release.events import ControllerError
from cg_release.policy import safe_ref
from cg_release.process import run_process


def _gpg_path(path: Path) -> str:
    executable = shutil.which("gpg")
    text = path.resolve().as_posix()
    if (
        os.name == "nt"
        and executable
        and (Path(executable).parent / "msys-2.0.dll").is_file()
    ):
        return "/" + text[0].lower() + text[2:]
    return text


def _oid(text: str) -> str:
    raw = text.encode("utf-8")
    return hashlib.sha1(b"tag " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


@contextmanager
def _signer(key_file: Path, fingerprint: str):
    try:
        if not re.fullmatch(r"(?:[A-F0-9]{40}|[A-F0-9]{64})", fingerprint):
            raise ValueError
        info = key_file.lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or not 1 <= info.st_size <= 65536
        ):
            raise ValueError
    except (ValueError, OSError, AttributeError, TypeError):
        raise ControllerError(
            "E_SIGNING", "Signing key or fingerprint is unavailable."
        ) from None
    with TemporaryDirectory(prefix="cg-release-sign-") as directory:
        root = Path(directory)
        home = root / "gnupg"
        home.mkdir(mode=0o700)
        environment = {
            k: v
            for k, v in os.environ.items()
            if k.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "COMSPEC"}
        }
        environment.update(
            GNUPGHOME=_gpg_path(home),
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_TERMINAL_PROMPT="0",
        )

        def call(tool, argv, **kwargs):
            return run_process(tool, argv, cwd=root, environment=environment, **kwargs)

        try:
            call("gpg", ["--batch", "--import", _gpg_path(key_file)])
            listing = call(
                "gpg", ["--batch", "--with-colons", "--list-keys", fingerprint]
            ).stdout
            if fingerprint not in [
                line.split(":")[9]
                for line in listing.splitlines()
                if line.startswith("fpr:")
            ]:
                raise ControllerError("E_SIGNING", "Allowlisted signing key is absent.")
            yield call
        finally:
            # GPG agents are temporary key holders, never session services.
            run_process(
                "gpgconf",
                ["--homedir", _gpg_path(home), "--kill", "gpg-agent"],
                cwd=root,
                environment=environment,
                allow_failure=True,
            )


def create_tag(
    tag: str,
    commit: str,
    name: str,
    email: str,
    timestamp: int,
    *,
    key_file: Path | None = None,
    fingerprint: str | None = None,
) -> dict:
    """Create public tag bytes without a ref write, e.g. create_tag('v1.0.0', sha, ...).

    Args: Identity/timestamp are sealed approval inputs. Optional key file is
        trusted job-local secret material, imported only into a new temporary home.
    Returns: Exact text, Git object ID and signing fingerprint for durable storage.
    Raises: ControllerError on unsafe identities or unavailable signing capability.
    """
    safe_ref(tag)
    if (
        not re.fullmatch(r"[0-9a-f]{40}", commit)
        or not re.fullmatch(r"[A-Za-z0-9 ._-]{1,100}", name)
        or not re.fullmatch(r"[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+", email)
        or type(timestamp) is not int
        or not 1 <= timestamp <= 253402300799
        or (key_file is None) != (fingerprint is None)
    ):
        raise ControllerError(
            "E_SIGNING", "Invalid sealed tag identity or signing key."
        )
    text = (
        f"object {commit}\ntype commit\ntag {tag}\n"
        f"tagger {name} <{email}> {timestamp} +0000\n\nRelease {tag}\n"
    )
    if fingerprint is not None:
        with _signer(key_file, fingerprint) as call:
            signature = call(
                "gpg",
                [
                    "--batch",
                    "--pinentry-mode",
                    "error",
                    "--armor",
                    "--local-user",
                    fingerprint + "!",
                    "--detach-sign",
                    "--output",
                    "-",
                ],
                input_text=text,
            ).stdout
            if not signature.startswith("-----BEGIN PGP SIGNATURE-----"):
                raise ControllerError(
                    "E_SIGNING", "GPG did not return an armored signature."
                )
            text += signature.replace("\r\n", "\n")
    result = {"text": text, "oid": _oid(text), "fingerprint": fingerprint}
    verify_tag(result, tag, commit, key_file=key_file, fingerprint=fingerprint)
    return result


def verify_tag(
    value: dict,
    tag: str,
    commit: str,
    *,
    key_file: Path | None = None,
    fingerprint: str | None = None,
) -> None:
    """Verify exact bytes and requested signer, e.g. verify_tag(saved, tag, sha).

    No tag ref is created and no source is checked out or executed.
    """
    try:
        text = value["text"]
        if (
            set(value) != {"text", "oid", "fingerprint"}
            or len(text.encode()) > 16384
            or _oid(text) != value["oid"]
            or not text.startswith(f"object {commit}\ntype commit\ntag {tag}\ntagger ")
            or value["fingerprint"] != fingerprint
            or (fingerprint is None and "-----BEGIN PGP" in text)
        ):
            raise ValueError
        if fingerprint is not None:
            with _signer(key_file, fingerprint) as call:
                call("git", ["init", "--bare", "."])
                call(
                    "git",
                    ["hash-object", "-t", "tag", "--stdin", "-w"],
                    input_text=text,
                )
                result = call(
                    "git",
                    ["-c", "gpg.program=gpg", "verify-tag", "--raw", value["oid"]],
                )
                signatures = [
                    line.split()[2]
                    for line in result.stderr.splitlines()
                    if line.startswith("[GNUPG:] VALIDSIG ")
                ]
                if signatures != [fingerprint]:
                    raise ValueError
    except (KeyError, ValueError, TypeError, AttributeError):
        raise ControllerError(
            "E_SIGNING", "Exact annotated tag or signature differs."
        ) from None
