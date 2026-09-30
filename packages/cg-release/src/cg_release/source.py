"""Acquire an exact read-only provider snapshot without fetching into the checkout."""

import argparse
import re
import time
from collections.abc import Callable
from pathlib import Path
from urllib.parse import quote, urlsplit

from cg_release.events import ControllerError
from cg_release.github import GitHubReads
from cg_release.history import adopted_history
from cg_release.models import Policy, Request, load_record
from cg_release.notes import release_notes
from cg_release.policy import safe_ref, select_line, validate_policy
from cg_release.preview import Snapshot
from cg_release.process import run_process
from cg_release.source_blobs import commit_tree, read_blobs
from cg_release.versions import baseline_version, resolve_version


def acquire_snapshot(
    args: argparse.Namespace,
    *,
    cwd: Path,
    api_factory: Callable = GitHubReads,
    clock: Callable = time.monotonic,
    deadline: float | None = None,
    origin: tuple[str, str] | None = None,
    requester_id: int | None = None,
    sealed_request: Request | None = None,
) -> Snapshot:
    """Acquire fresh immutable inputs, e.g. for plan --branch feature --version 1.0.0.

    Args:
        args: Validated CLI namespace.
        cwd: Existing checkout directory; dirty files are never read or changed.
        api_factory: Injectable read adapter constructor.
        clock: Monotonic shared command clock.
        deadline: Absolute command deadline, including earlier reads and rechecks.
    Returns:
        Exact-source snapshot; no permission or state inferred from source files.
    Raises:
        ControllerError: Identity, policy, history, authority, or prerequisite failure.
    """
    started = clock()
    deadline = started + 120 if deadline is None else deadline

    def git(argv: list[str], allow_failure: bool = False):
        remaining = deadline - clock()
        if remaining <= 0:
            raise ControllerError(
                "E_DEADLINE", "Source discovery exceeded the command deadline."
            )
        return run_process(
            "git",
            argv,
            cwd=cwd,
            timeout=min(20, remaining),
            allow_failure=allow_failure,
        )

    url = (
        git(["remote", "get-url", "origin"]).stdout.strip()
        if origin is None
        else f"https://{origin[0]}/{origin[1]}"
    )
    ssh = re.fullmatch(r"git@([a-z0-9.-]+):([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", url)
    if ssh:
        host, slug = ssh[1], ssh[2]
    else:
        try:
            parsed = urlsplit(url)
            port = parsed.port
        except ValueError:
            raise ControllerError("E_REPOSITORY", "Origin URL is malformed.") from None
        if (
            parsed.scheme not in {"https", "ssh"}
            or parsed.password
            or parsed.query
            or parsed.fragment
            or (parsed.scheme == "https" and parsed.username is not None)
            or (parsed.scheme == "ssh" and parsed.username != "git")
            or port
        ):
            raise ControllerError(
                "E_REPOSITORY",
                "Origin must be a credential-free GitHub HTTPS or SSH URL.",
            )
        host, slug = parsed.hostname or "", parsed.path.lstrip("/")
    slug = slug.removesuffix(".git")
    api = api_factory(host, slug, cwd=cwd, clock=clock, deadline=deadline)
    branch = args.branch
    if branch is None:
        symbolic = git(["symbolic-ref", "--quiet", "--short", "HEAD"], True)
        if symbolic.returncode:
            raise ControllerError(
                "E_DETACHED", "Detached HEAD requires an explicit --branch."
            )
        branch = symbolic.stdout.strip()
    safe_ref(branch)
    repository = api.get("")
    if (
        not isinstance(repository, dict)
        or type(repository.get("id")) is not int
        or repository["id"] <= 0
        or not isinstance(repository.get("full_name"), str)
        or repository.get("full_name", "").casefold() != slug.casefold()
        or repository.get("fork") is not False
        or not isinstance(repository.get("default_branch"), str)
    ):
        raise ControllerError(
            "E_REPOSITORY",
            "Resolve one non-fork same-repository origin and default branch.",
        )
    slug = repository["full_name"]
    api.slug = slug
    default = repository["default_branch"]
    trusted_branch = api.branch(default)
    if trusted_branch.get("protected") is not True:
        raise ControllerError(
            "E_POLICY_TRUST", "Default policy branch must be protected before preview."
        )
    policy_sha = trusted_branch["commit"]["sha"]
    policy_tree = commit_tree(api, policy_sha)
    raw = read_blobs(api, policy_tree, [".release-controller.json"])[
        ".release-controller.json"
    ].content
    try:
        policy = load_record(Policy, raw)
    except ValueError:
        raise ControllerError(
            "E_POLICY", "Protected default-branch policy is not valid schema v1."
        ) from None
    validate_policy(policy, repository_id=repository["id"], host=host)
    api.read_seconds, api.read_attempts = (
        policy.timeouts.read_seconds,
        policy.timeouts.read_attempts,
    )
    api.deadline = min(api.deadline, started + policy.timeouts.start_seconds)
    api.remaining()
    actor = (
        api.actor()
        if requester_id is None
        else api._request(f"user/{requester_id}", None)
    )
    if requester_id is not None and (
        not isinstance(actor, dict)
        or type(actor.get("id")) is not int
        or actor["id"] != requester_id
    ):
        raise ControllerError("E_AUTHORITY", "Original requester identity changed.")
    permission = api.get(
        "collaborators/" + quote(actor["login"], safe="") + "/permission"
    )
    legacy_permissions = {
        "read": "read",
        "triage": "read",
        "write": "write",
        "maintain": "write",
        "admin": "admin",
    }
    if (
        not isinstance(permission, dict)
        or not isinstance(permission.get("user"), dict)
        or type(permission["user"].get("id")) is not int
        or permission["user"].get("id") != actor["id"]
        or not isinstance(permission.get("role_name"), str)
        or permission["role_name"] not in legacy_permissions
        or permission.get("permission") != legacy_permissions[permission["role_name"]]
    ):
        raise ControllerError(
            "E_AUTHORITY", "Current actor permission cannot be verified."
        )
    reservations = []
    try:
        api.branch(policy.state_branch)
    except ControllerError as error:
        if error.code != "E_NOT_FOUND":
            raise
        if policy.enabled:
            raise ControllerError(
                "E_STATE_REQUIRED",
                "Enabled policy requires a verified reservation journal.",
            ) from None
    else:
        reservations = (
            read_reservations(api, policy, default, sealed_request=sealed_request)
            if sealed_request is not None
            else read_reservations(api, policy, default)
        )
    history, occupied = adopted_history(api, policy)
    occupied = sorted(set(occupied + reservations))
    source_branch = api.branch(branch)
    source_sha = source_branch["commit"]["sha"]
    tree = commit_tree(api, source_sha)
    paths = [a.path for a in policy.metadata] + [
        policy.changelog.path,
        ".release-manifest.json",
    ]
    blobs = read_blobs(api, tree, paths, optional={".release-manifest.json"})
    line = select_line(policy, branch, args.line)
    selected = [r for r in history if r["line"] == line.id]
    versions = [r["version"] for r in selected]
    version = resolve_version(
        versions,
        line=line,
        occupied=occupied,
        bump=args.bump,
        version=args.version,
        channel=args.channel,
    )
    if policy.gpid_profile:
        from cg_release.hooks import selected_profile

        profile = selected_profile(policy)
        profile.verify_bridge(api, policy)
        blobs.update(
            profile.source_blobs(
                api, tree, policy.tag_prefix + version, default_tree=policy_tree
            )
        )
        from cg_release.profile_selection import preflight

        preflight(api, policy, version)
    baseline_id = baseline_version(versions, version=version, bump=args.bump)
    baseline = next((r for r in selected if r["version"] == str(baseline_id)), None)
    notes = release_notes(api, source_sha, baseline["commit"] if baseline else None)
    if (
        api.branch(default)["commit"]["sha"] != policy_sha
        or api.branch(branch)["commit"]["sha"] != source_sha
    ):
        raise ControllerError(
            "E_STALE_PROPOSAL", "Source or trusted policy changed during preview reads."
        )
    api.remaining()
    return Snapshot(
        repository["id"],
        host,
        slug,
        actor["id"],
        permission["role_name"],
        default,
        branch,
        source_sha,
        policy_sha,
        raw,
        history,
        occupied,
        blobs,
        notes,
    )


def read_reservations(
    api: GitHubReads,
    policy: Policy,
    default: str,
    *,
    sealed_request: Request | None = None,
) -> list[str]:
    """Read verified global reservations, e.g. during read-only preview."""
    from cg_release.authority import verify_controls
    from cg_release.github_journal import GitHubJournalStore
    from cg_release.journal import Journal

    bot_id = verify_controls(api, policy, default)
    journal = Journal(GitHubJournalStore(api, policy, bot_id=bot_id))
    if sealed_request is None:
        return journal.reservations()
    from cg_release.admission import Locator

    records = journal.records()
    locator = Locator.from_request(sealed_request).encode()
    own = next((r for r in records if r.request_id == locator), None)
    if own is None or own.request != sealed_request or own.state == "abandoned":
        raise ControllerError(
            "E_RESERVATION", "Exact active sealed request is required for replay."
        )
    return [
        r.request.version.split("+")[0]
        for r in records
        if r.request_id != locator and r.state != "abandoned"
    ]
