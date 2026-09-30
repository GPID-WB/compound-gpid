"""Private clean-consumer updater/link round trip with real delivered dependencies."""

import base64
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

from cg_release.events import ControllerError
from cg_release.journal import digest
from cg_release.profile_bridge import LINKS, MANAGED


def run(argv, *, cwd, env, check=True, input_bytes=None):
    """Run bounded credential-redacted I/O; return CompletedProcess or raise.
    Example: run(['git', 'rev-parse', 'HEAD'], cwd=client, env=isolated_env).
    """
    result = subprocess.run(
        argv, cwd=cwd, env=env, input=input_bytes, capture_output=True, timeout=180
    )
    if check and result.returncode:
        raise ControllerError(
            "E_BRIDGE_CLIENT",
            "Bridge process failed; credential-bearing child output is withheld.",
        )
    return result


def inspect_client(client: Path, consumer: Path, identity, env: dict) -> dict:
    """Read Git, tracked bytes, managed copies and links; return exact consumer proof.
    Raises ControllerError on checkout/byte/pin/refresh/link mismatch. No writes.
    Example: inspect_client(client, consumer, spec.bridge, isolated_env).
    """
    detail = "HEAD"
    try:
        for suffix, expected in [("", identity.revision), ("^{tree}", identity.tree)]:
            observed = (
                run(["git", "rev-parse", "HEAD" + suffix], cwd=client, env=env)
                .stdout.decode()
                .strip()
            )
            if observed != expected:
                raise ValueError
        rows = []
        run(
            ["git", "diff-index", "--cached", "--quiet", "--no-ext-diff", "HEAD", "--"],
            cwd=client,
            env=env,
        )
        raw = run(["git", "ls-files", "--stage", "-z"], cwd=client, env=env).stdout
        names = [line.split(b"\t", 1)[1] for line in raw.split(b"\0") if line]
        attrs = (
            run(
                [
                    "git",
                    "check-attr",
                    "--cached",
                    "-z",
                    "--stdin",
                    "text",
                    "eol",
                    "filter",
                    "working-tree-encoding",
                    "ident",
                ],
                cwd=client,
                env=env,
                input_bytes=b"\0".join(names) + b"\0",
            )
            .stdout.decode("utf-8")
            .split("\0")[:-1]
        )
        attributes = {}
        for index in range(0, len(attrs), 3):
            name, key, value = attrs[index : index + 3]
            attributes.setdefault(name, {})[key] = value
        for line in raw.split(b"\0"):
            if not line:
                continue
            header, name = line.decode("utf-8").split("\t", 1)
            mode, oid, stage = header.split()
            path = client / name
            detail = "tracked file " + name
            if stage != "0" or mode not in {"100644", "100755"} or path.is_symlink():
                raise ValueError
            data = path.read_bytes()
            attr = attributes[name]
            if any(
                attr[key] not in {"unspecified", "unset"}
                for key in ("filter", "working-tree-encoding", "ident")
            ):
                raise ValueError
            # Verify Git identity and the declared checkout bytes separately.
            # No source-defined clean/smudge or encoding filter is executed.
            canonical = data
            if attr["eol"] in {"lf", "crlf"} and attr["text"] != "unset":
                canonical = data.replace(b"\r\n", b"\n")
                expected = (
                    canonical.replace(b"\n", b"\r\n")
                    if attr["eol"] == "crlf"
                    else canonical
                )
                if data != expected:
                    raise ValueError
            if (
                hashlib.sha1(
                    b"blob " + str(len(canonical)).encode() + b"\0" + canonical
                ).hexdigest()
                != oid
            ):
                raise ValueError
            rows.append((name, mode, oid))
        detail = "pin"
        pin = (client / ".cg-version").read_text().strip()
        if pin != identity.tag:
            raise ValueError
        detail = "managed manifest"
        manifest = json.loads(
            (consumer / ".compound-gpid/managed-files.json").read_text(
                encoding="utf-8-sig"
            )
        )
        managed = {}
        for name in MANAGED:
            detail = "managed file " + name
            data = (consumer / name).read_bytes()
            item = manifest["files"][name]
            if item["source"] != name or data != (client / name).read_bytes():
                raise ValueError
            managed[name] = hashlib.sha256(data).hexdigest()
            if item["checksum"] != managed[name]:
                raise ValueError
        for name in LINKS:
            detail = "link " + name
            if (consumer / name).resolve() != (client / name).resolve():
                raise ValueError
        detail = "Copilot instructions"
        instructions = (consumer / ".github/copilot-instructions.md").read_text(
            encoding="utf-8-sig"
        )
        if (
            "<!-- compound-gpid:managed -->" not in instructions
            or "QUALIFIER_STALE" in instructions
        ):
            raise ValueError
        return dict(
            release=identity.model_dump(mode="json"),
            tracked_digest=digest(sorted(rows)),
            managed=managed,
            links=list(LINKS),
            pin=pin,
            copilot_refreshed=True,
        )
    except (KeyError, ValueError, OSError, TypeError):
        raise ControllerError(
            "E_BRIDGE_CLIENT",
            "Installed bridge tree or managed continuation differs: " + detail,
        ) from None


def roundtrip(spec, root: Path, *, remote: str, shell_kind: str) -> dict:
    """Install previous -> bridge -> successor in a new private directory.

    Args: strict explicit release spec; nonexistent root; outer Git remote URL; native
    'windows' or 'unix' shell. Tests may use local bare Git and Git Bash for the Unix
    code path, but that is not native Unix delivery. Returns exact stage proofs.
    Raises ControllerError on any failure. Clones/updates only root/client, creates
    root/consumer and root/home. Uses real helpers and normal link/update continuation;
    never sets CG_INTERNAL_CALL or CG_SKIP_UPDATE. Example: roundtrip(spec, scratch,
    remote='https://github.com/owner/repo.git', shell_kind='windows').
    """
    if shell_kind not in {"windows", "unix"}:
        raise ControllerError("E_BRIDGE_CLIENT", "Unknown bridge shell kind.")
    if root.exists():
        raise ControllerError(
            "E_BRIDGE_CLIENT", "Clean bridge scratch directory must not exist."
        )
    root.mkdir()
    home, consumer, client = root / "home", root / "consumer", root / "client"
    home.mkdir()
    consumer.mkdir()
    env = {
        k: v for k, v in os.environ.items()
        if not k.startswith(("CG_", "GIT_", "GH_", "GITHUB_"))
        and k.upper() != "PSMODULEPATH"
    }
    env.update(
        HOME=str(home),
        USERPROFILE=str(home),
        XDG_CONFIG_HOME=str(home / "config"),
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_TERMINAL_PROMPT="0",
        GIT_CONFIG_COUNT="1",
        GIT_CONFIG_KEY_0="core.autocrlf",
        GIT_CONFIG_VALUE_0="false",
    )
    if remote.startswith("https://"):
        if remote != f"https://github.com/{spec.repository_slug}.git":
            raise ControllerError(
                "E_BRIDGE_CLIENT", "Bridge Git remote is not the approved repository."
            )
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token or any(c in token for c in "\r\n"):
            raise ControllerError(
                "E_BRIDGE_CLIENT",
                "Repository-scoped read-only Git credential is required.",
            )
        env.update(
            GIT_CONFIG_COUNT="3",
            GIT_CONFIG_KEY_1=f"http.{remote}.extraheader",
            GIT_CONFIG_VALUE_1="AUTHORIZATION: basic "
            + base64.b64encode(("x-access-token:" + token).encode()).decode(),
            GIT_CONFIG_KEY_2="http.followRedirects",
            GIT_CONFIG_VALUE_2="false",
        )
    run(["git", "clone", "--no-local", remote, str(client)], cwd=root, env=env)
    run(["git", "checkout", "--detach", spec.previous.tag], cwd=client, env=env)
    (client / ".cg-version").write_text(spec.previous.tag, encoding="utf-8")
    if shell_kind == "windows":
        shell = shutil.which("powershell")
        if not shell:
            raise ControllerError(
                "E_BRIDGE_CLIENT", "Windows PowerShell 5.1 is required."
            )
        driver = root / "driver.ps1"
        driver.write_text(
            "param([string]$Entry, [string[]]$Arguments)\n"
            'Set-StrictMode -Version Latest\n$ErrorActionPreference = "Stop"\n'
            '$PROFILE = Join-Path $env:USERPROFILE "isolated-profile.ps1"\n'
            "& $Entry @Arguments\nif ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }\n",
            encoding="utf-8",
        )

        def command(action, *args):
            # A fixed driver isolates the real helper's profile cleanup path.
            return [
                shell,
                "-NoProfile",
                "-File",
                str(driver),
                "-Entry",
                str(client / ("scripts/" + action + ".ps1")),
                "-Arguments",
                *args,
            ]
    else:
        shell = (
            "C:/Program Files/Git/bin/bash.exe"
            if os.name == "nt"
            else shutil.which("bash")
        )
        if not shell:
            raise ControllerError("E_BRIDGE_CLIENT", "Native Bash is required.")

        def command(action, *args):
            return [
                shell,
                "--noprofile",
                "--norc",
                (client / ("scripts/" + action + ".sh")).as_posix(),
                *args,
            ]

    link_args = ("--platforms=opencode,copilot",)
    run(command("link", *link_args), cwd=consumer, env=env)
    proofs = {"previous": inspect_client(client, consumer, spec.previous, env)}
    denied = run(
        command("update", spec.successor.tag), cwd=consumer, env=env, check=False
    )
    if (
        not denied.returncode
        or inspect_client(client, consumer, spec.previous, env) != proofs["previous"]
    ):
        raise ControllerError(
            "E_BRIDGE_CLIENT", "Old reader did not reject the new pin without effects."
        )
    for name in ("bridge", "successor"):
        # Matching management checksums make these copies eligible for real refresh.
        manifest_path = consumer / ".compound-gpid/managed-files.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        for path in MANAGED:
            data = b"QUALIFIER_STALE\n"
            (consumer / path).write_bytes(data)
            manifest["files"][path]["checksum"] = hashlib.sha256(data).hexdigest()
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        (consumer / ".github/copilot-instructions.md").write_text(
            "<!-- compound-gpid:managed -->\nQUALIFIER_STALE\n", encoding="utf-8"
        )
        identity = getattr(spec, name)
        run(command("update", identity.tag), cwd=consumer, env=env)
        proofs[name] = inspect_client(client, consumer, identity, env)
        run(command("link", *link_args), cwd=consumer, env=env)
        if inspect_client(client, consumer, identity, env) != proofs[name]:
            raise ControllerError(
                "E_BRIDGE_CLIENT", "Bridge link continuation changed verified content."
            )
    return proofs
