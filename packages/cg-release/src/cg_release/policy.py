"""Pure semantic checks after loading policy from a protected default commit."""

import re
from pathlib import PurePosixPath, PureWindowsPath

from cg_release.events import ControllerError
from cg_release.models import Policy, ReleaseLine
from cg_release.versions import parse_version


def safe_path(value: str) -> str:
    """Validate one portable regular-file path, e.g. ``safe_path('pkg/info.json')``.

    Args:
        value: Repository-relative forward-slash path.
    Returns:
        Unchanged safe path; no filesystem access is made.
    Raises:
        ControllerError: Traversal, Windows aliases, or nonportable names.
    """
    parts = value.split("/")
    if (
        not value
        or len(value) > 255
        or PurePosixPath(value).is_absolute()
        or PureWindowsPath(value).drive
        or "\\" in value
        or any(
            p in {"", ".", ".."}
            or p.casefold() == ".git"
            or p.endswith((".", " "))
            or re.search(r'[<>:"|?*\x00-\x1f\x7f]', p)
            or p.split(".")[0].upper()
            in {
                "CON",
                "PRN",
                "AUX",
                "NUL",
                *(f"COM{i}" for i in range(10)),
                *(f"LPT{i}" for i in range(10)),
            }
            for p in parts
        )
    ):
        raise ControllerError(
            "E_PATH", "Expected a portable repository-relative regular-file path."
        )
    return value


def safe_ref(value: str) -> str:
    """Validate a Git ref suffix, e.g. ``safe_ref('feature/release')``.

    Args:
        value: Branch or complete tag name, at most 255 characters, without refs/.
    Returns:
        Valid name, without executing Git.
    Raises:
        ControllerError: Invalid or option-like ref.
    """
    if (
        not value
        or len(value) > 255
        or value.startswith(("-", "/"))
        or value.endswith(("/", "."))
        or ".." in value
        or "@{" in value
        or value == "@"
        or re.search(r"[\x00-\x20\x7f~^:?*\[\\]", value)
        or any(
            not p or p.startswith(".") or p.endswith(".lock") for p in value.split("/")
        )
    ):
        raise ControllerError("E_REF", "Invalid branch or tag name.")
    return value


def validate_policy(policy: Policy, *, repository_id: int, host: str) -> None:
    """Validate controls and repository binding, e.g. for numeric repository 123.

    Args:
        policy: Strictly decoded policy from the protected default branch only.
        repository_id: Provider-verified repository ID.
        host: Provider-verified host.
    Returns:
        None; this is not evidence of remote environment or App enforcement.
    Raises:
        ControllerError: Unsafe or contradictory semantic controls.
    """
    if policy.repository_id != repository_id or policy.host != host:
        raise ControllerError(
            "E_REPOSITORY", "Policy belongs to a different repository."
        )
    if policy.gpid_profile:
        from cg_release.hooks import selected_profile

        selected_profile(policy).validate_policy(policy)
    elif policy.profile is not None:
        raise ControllerError(
            "E_PROFILE", "Generic policy cannot declare a profile contract."
        )
    branches = {b for line in policy.release_lines for b in line.branches}
    for branch in [*branches, *policy.production_branches, policy.state_branch]:
        safe_ref(branch)
    safe_ref(policy.tag_prefix + "1.0.0")
    if (
        policy.apps.control == policy.apps.publishing
        or policy.state_branch in branches
        or policy.state_branch in policy.production_branches
        or len(set(policy.environments.model_dump().values())) != 3
        or (policy.signing_required and not policy.allowed_signing_fingerprints)
    ):
        raise ControllerError(
            "E_POLICY", "Policy lacks distinct authority or signing controls."
        )
    if len({line.id for line in policy.release_lines}) != len(policy.release_lines):
        raise ControllerError("E_POLICY", "Release-line IDs must be unique.")
    if not any(c.stage == "preparation-and-release" for c in policy.required_checks):
        raise ControllerError(
            "E_POLICY", "At least one preparation PR check is required."
        )
    for line in policy.release_lines:
        low, high = line.minimum_core, line.maximum_core_exclusive
        if any(n < 0 for n in low) or (
            high is not None and (any(n < 0 for n in high) or high <= low)
        ):
            raise ControllerError("E_POLICY", "Invalid numeric core bounds.")
    paths = [a.path for a in policy.metadata] + [
        policy.changelog.path,
        ".release-manifest.json",
    ]
    for path in (
        paths + policy.build.lock_paths + [a.path for a in policy.build.artifacts]
    ):
        safe_path(path)
    if policy.build.cwd != ".":
        safe_path(policy.build.cwd)
    validate_edit_paths(policy.metadata, policy.changelog.path)
    for adapter in policy.metadata:
        if (
            adapter.kind == "json"
            and (not adapter.pointer or not adapter.pointer.startswith("/"))
        ) or (adapter.kind != "json" and adapter.pointer is not None):
            raise ControllerError(
                "E_POLICY", "Metadata pointer does not match its adapter."
            )
    if len(policy.build.artifacts) > policy.build.max_artifacts:
        raise ControllerError("E_POLICY", "Artifact inventory exceeds its limit.")
    if len({a.name.casefold() for a in policy.build.artifacts}) != len(
        policy.build.artifacts
    ):
        raise ControllerError("E_POLICY", "Artifact names are not unique.")
    if len({a.path.casefold() for a in policy.build.artifacts}) != len(
        policy.build.artifacts
    ):
        raise ControllerError("E_POLICY", "Artifact paths are not unique.")
    for item in policy.bootstrap:
        parse_version(item.version)
        if item.line not in {line.id for line in policy.release_lines}:
            raise ControllerError("E_HISTORY", "Bootstrap references an unknown line.")
        safe_ref(item.tag)
        if item.legacy_version is None and item.tag != policy.tag_prefix + item.version:
            raise ControllerError("E_HISTORY", "Adopted tag and version disagree.")
        if (
            item.legacy_version is not None
            and item.tag != policy.tag_prefix + item.legacy_version
        ):
            raise ControllerError(
                "E_HISTORY", "Legacy bootstrap must retain its original tag."
            )


def validate_edit_paths(adapters: list, changelog_path: str) -> None:
    """Allow distinct JSON fields in one file, but no duplicate or case-aliased edits.

    Example: two JSON adapters for /version and /nested/version share one output.
    """
    reserved = [changelog_path, ".release-manifest.json"]
    paths = [a.path for a in adapters] + reserved
    for path in paths:
        safe_path(path)
    if len({p.casefold() for p in set(paths)}) != len(set(paths)):
        raise ControllerError("E_PATH", "Declared metadata paths have case aliases.")
    if len(set(reserved)) != 2 or any(a.path in reserved for a in adapters):
        raise ControllerError("E_PATH", "Metadata overlaps changelog or manifest.")
    seen = {}
    for adapter in adapters:
        fields = seen.setdefault(adapter.path, set())
        if fields and (adapter.kind != "json" or None in fields):
            raise ControllerError(
                "E_PATH", "Only distinct JSON fields may share a metadata file."
            )
        if adapter.pointer in fields:
            raise ControllerError(
                "E_PATH", "A metadata field is declared more than once."
            )
        fields.add(adapter.pointer)


def select_line(policy: Policy, branch: str, requested: str | None) -> ReleaseLine:
    """Select exactly one eligible line, e.g. ``select_line(p, 'main', None)``.

    Args:
        policy: Validated policy.
        branch: Verified same-repository remote source branch.
        requested: Explicit line ID, or None for unique membership.
    Returns:
        The selected release line.
    Raises:
        ControllerError: Missing or ambiguous membership; an ID cannot bypass it.
    """
    matches = [
        line
        for line in policy.release_lines
        if branch in line.branches and (requested is None or line.id == requested)
    ]
    if len(matches) != 1:
        raise ControllerError(
            "E_LINE", "Select one release line containing the source branch."
        )
    return matches[0]


def approval_route(
    policy: Policy,
    branch: str,
    version: str,
    role: str,
    default_branch: str,
    reason: str | None,
) -> str:
    """Choose the required gate, e.g. a maintainer exception uses override.

    Args:
        policy: Validated policy; enabled is not permission to bypass checks.
        branch: Same-repository remote branch.
        version: Resolved canonical version.
        role: Current actor permission from GitHub, not local configuration.
        default_branch: Remote default used when production branches are empty.
        reason: Explicit bounded stable-branch exception reason.
    Returns:
        Required environment name; not proof that approval has occurred.
    Raises:
        ControllerError: Unauthorized actor or production-branch exception.
    """
    if role not in {"write", "maintain", "admin"}:
        raise ControllerError(
            "E_AUTHORITY", "Current write, maintain, or admin permission is required."
        )
    production = policy.production_branches or [default_branch]
    if reason is not None:
        if (
            role not in {"maintain", "admin"}
            or not reason.strip()
            or len(reason) > 1024
        ):
            raise ControllerError(
                "E_OVERRIDE",
                "Override requires maintainer authority and a bounded reason.",
            )
        return policy.environments.override
    if parse_version(version).prerelease is None and branch not in production:
        raise ControllerError(
            "E_BRANCH",
            "Stable release needs a production branch or a maintainer override.",
        )
    return policy.environments.publish
