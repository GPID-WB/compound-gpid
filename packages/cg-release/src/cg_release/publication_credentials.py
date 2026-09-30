"""Per-process credential roles, never mutable global token selection."""

import os
import re

from cg_release.events import ControllerError
from cg_release.process import run_process


def role_runner(role: str, *, runner=run_process):
    """Return a bounded role runner, e.g. role_runner('publishing').

    Token values stay in the child environment only, never argv or journal records.
    Journal writes and release writes have disjoint local operation allowlists;
    verified remote rulesets supply the separate server-side protection.
    """
    if role not in {"control", "publishing"}:
        raise ControllerError("E_CREDENTIAL_ROLE", "Unknown release credential role.")
    key = "CG_RELEASE_" + role.upper() + "_TOKEN"
    token = os.environ.get(key)
    if not token:
        raise ControllerError(
            "E_CREDENTIAL_ROLE", "Required protected job credential is absent."
        )

    def execute(tool, args, **kwargs):
        method = args[args.index("--method") + 1] if "--method" in args else None
        endpoint = args[-1]
        if tool == "gh":
            allowed = args[0] == "api" and method == "GET"
            if role == "control":
                allowed |= method == "POST" and endpoint == "graphql"
            else:
                allowed |= (
                    method == "POST"
                    and re.fullmatch(
                        r"(?:https://[a-z0-9.-]+(?:/api/uploads)?/)?repos/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/releases(?:/[1-9][0-9]*/assets\?name=[A-Za-z0-9._%-]+)?",
                        endpoint,
                    )
                    is not None
                )
                allowed |= (
                    method == "PATCH"
                    and re.fullmatch(
                        r"repos/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/releases/[1-9][0-9]*",
                        endpoint,
                    )
                    is not None
                )
        elif tool == "git":
            allowed = role == "publishing" and any(
                command in args for command in ("init", "fetch", "hash-object", "push")
            )
            allowed &= not any(arg.startswith(("--force", "+")) for arg in args)
            if "push" in args:
                allowed &= (
                    re.fullmatch(r"[0-9a-f]{40}:refs/tags/[^\s]+", endpoint) is not None
                )
        else:
            allowed = False
        if not allowed:
            raise ControllerError(
                "E_CREDENTIAL_ROLE", "Operation is outside the credential role."
            )
        supplied = kwargs.pop("environment", None)
        env = {
            k: v
            for k, v in (supplied or os.environ).items()
            if k.upper()
            in {
                "PATH",
                "SYSTEMROOT",
                "WINDIR",
                "TEMP",
                "TMP",
                "COMSPEC",
                "HOME",
                "GIT_CONFIG_NOSYSTEM",
                "GIT_CONFIG_GLOBAL",
                "GIT_TERMINAL_PROMPT",
            }
        }
        env.update(GH_TOKEN=token, GH_PROMPT_DISABLED="1", GIT_TERMINAL_PROMPT="0")
        return runner(tool, args, **kwargs, environment=env)

    return execute
