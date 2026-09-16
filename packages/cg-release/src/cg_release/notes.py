"""Deterministic notes from complete bounded GitHub commit inventories."""

import re

from cg_release.events import ControllerError
from cg_release.github import MAX_PAGES, GitHubReads


def release_notes(api: GitHubReads, source_sha: str, baseline_sha: str | None) -> str:
    """Read commits at exact SHAs, e.g. release_notes(api, source, baseline).

    Args:
        api: Bounded GET-only reader; no local Git history or fetch.
        source_sha: Exact proposed source commit.
        baseline_sha: Adopted line baseline commit, or None for explicit bootstrap.
    Returns:
        Bounded deterministic Markdown identifying each commit and its subject.
    Raises:
        ControllerError: Incomplete/invalid inventory, divergence, or note size limit.
    """
    if any(
        not re.fullmatch(r"[0-9a-f]{40}", value)
        for value in [source_sha, *([baseline_sha] if baseline_sha else [])]
    ):
        raise ControllerError(
            "E_NOTES", "Notes require exact source and baseline commits."
        )
    resource = (
        f"compare/{baseline_sha}...{source_sha}"
        if baseline_sha
        else f"commits?sha={source_sha}"
    )
    inventory, seen, expected = [], set(), None
    for page in range(1, MAX_PAGES + 1):
        value = api._request(f"repos/{api.slug}/{resource}", page)
        if baseline_sha:
            if (
                not isinstance(value, dict)
                or value.get("status") not in {"ahead", "identical"}
                or type(value.get("total_commits")) is not int
                or value["total_commits"] < 0
            ):
                raise ControllerError(
                    "E_NOTES",
                    "Baseline comparison is invalid or source history diverged.",
                )
            if expected is not None and expected != value["total_commits"]:
                raise ControllerError(
                    "E_NOTES", "Commit inventory changed during pagination."
                )
            expected, value = value["total_commits"], value.get("commits")
        if not isinstance(value, list):
            raise ControllerError(
                "E_NOTES", "Expected a complete list of source commits."
            )
        for item in value:
            try:
                sha, message = item["sha"], item["commit"]["message"]
                if (
                    not re.fullmatch(r"[0-9a-f]{40}", sha)
                    or sha in seen
                    or not isinstance(message, str)
                ):
                    raise ValueError
            except (KeyError, TypeError, ValueError):
                raise ControllerError(
                    "E_NOTES", "Invalid or duplicate committed input."
                ) from None
            seen.add(sha)
            subject = (
                message.splitlines()[0] if message.splitlines() else "(no subject)"
            )
            inventory.append((sha, subject))
        notes = (
            f"Source commit: `{source_sha}`.\n"
            + "".join(f"\n- `{sha}` {subject}" for sha, subject in sorted(inventory))
            + "\n"
        )
        if len(notes.encode("utf-8")) > 65536:
            raise ControllerError("E_NOTES", "Commit inventory exceeds the note limit.")
        if len(value) < 100:
            if expected is not None and len(inventory) != expected:
                raise ControllerError("E_NOTES", "Commit inventory is incomplete.")
            return notes
    raise ControllerError("E_NOTES", "Commit inventory exceeds the page limit.")
