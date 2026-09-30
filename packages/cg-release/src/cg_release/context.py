"""Protected remote policy and journal context, independent of local Git state."""

import re
import time
from dataclasses import dataclass
from pathlib import Path

from cg_release.admission import Locator
from cg_release.authority import verify_controls
from cg_release.events import ControllerError
from cg_release.github import GitHubReads
from cg_release.github_journal import GitHubJournalStore
from cg_release.journal import Journal
from cg_release.models import Policy, load_record
from cg_release.policy import validate_policy
from cg_release.source_blobs import commit_tree, read_blobs


@dataclass
class Context:
    """Verified remote policy and protected journal, not source checkout authority."""

    api: GitHubReads
    policy: Policy
    policy_sha: str
    default: str
    journal: Journal


def context_for(
    request_id: str,
    *,
    deadline: float,
    cwd: Path | None = None,
    clock=time.monotonic,
    writable: bool = False,
    api_factory=GitHubReads,
) -> Context:
    """Resolve remote context, e.g. context_for(locator, deadline=end)."""
    locator = Locator.decode(request_id)
    api = api_factory(
        locator.host,
        locator.repository_slug,
        cwd=cwd or Path.cwd(),
        deadline=deadline,
        clock=clock,
    )
    repository = api.get("")
    try:
        if (
            type(repository["id"]) is not int
            or repository["id"] != locator.repository_id
        ):
            raise ValueError
        slug, default = repository["full_name"], repository["default_branch"]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", slug):
            raise ValueError
        api.slug = slug
        branch = api.branch(default)
        if branch["protected"] is not True:
            raise ValueError
        policy_sha = branch["commit"]["sha"]
        raw = read_blobs(
            api, commit_tree(api, policy_sha), [".release-controller.json"]
        )[".release-controller.json"].content
        policy = load_record(Policy, raw)
        validate_policy(policy, repository_id=locator.repository_id, host=locator.host)
        api.read_seconds, api.read_attempts = (
            policy.timeouts.read_seconds,
            policy.timeouts.read_attempts,
        )
        bot_id = verify_controls(api, policy, default)
        if api.branch(default)["commit"]["sha"] != policy_sha:
            raise ControllerError(
                "E_STALE_PROPOSAL", "Trusted policy advanced during verification."
            )
        return Context(
            api,
            policy,
            policy_sha,
            default,
            Journal(GitHubJournalStore(api, policy, bot_id=bot_id, writable=writable)),
        )
    except (ValueError, KeyError, TypeError, AttributeError):
        raise ControllerError(
            "E_POLICY_TRUST",
            "Exact trusted policy or repository identity is unavailable.",
        ) from None
