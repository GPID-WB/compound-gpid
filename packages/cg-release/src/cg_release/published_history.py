"""Convert verified journal publication receipts into exact adopted history."""

from cg_release.authority import verify_controls
from cg_release.events import ControllerError
from cg_release.github_journal import GitHubJournalStore
from cg_release.journal import Journal
from cg_release.models import HistoricalRelease, canonical_bytes, load_record


def published_inputs(record):
    """Resolve exact original publication inputs from the immutable receipt."""
    from cg_release.journal import digest

    try:
        receipt = record.evidence["publication-receipt"]
        seal = record.evidence[f"publication-seal-{receipt['run_id']}"]
        inputs = seal["inputs"]
        if (
            seal["run_id"] != receipt["run_id"]
            or seal["digest"] != receipt["inputs_digest"]
            or digest(inputs) != seal["digest"]
            or inputs["tag"] != record.request.tag
            or inputs["release_sha"] != receipt["release_sha"]
        ):
            raise ValueError
        return inputs
    except (KeyError, TypeError, ValueError):
        raise ControllerError(
            "E_HISTORY", "Published receipt lacks its exact immutable approval inputs."
        ) from None


def verified_records(api, policy):
    """Read the complete protected journal, e.g. verified_records(api, policy)."""
    default = api.get("")["default_branch"]
    bot_id = verify_controls(api, policy, default)
    return Journal(GitHubJournalStore(api, policy, bot_id=bot_id)).records()


def journal_adoptions(policy, records, *, current=None):
    """Combine explicit bootstrap and published receipts without mutating policy."""
    rows = {r.tag: r for r in policy.bootstrap}
    if len(rows) != len(policy.bootstrap):
        raise ControllerError("E_HISTORY", "Duplicate bootstrap tag identity.")
    tag_objects = {}
    for record in records:
        if current is not None and record.request_id == current.request_id:
            continue
        if record.publication_started and not record.published:
            raise ControllerError(
                "E_INCOMPLETE_PUBLICATION",
                "An unfinished publication blocks new admission/publication.",
            )
        if not record.published:
            continue
        try:
            request = record.request
            receipt = record.evidence["publication-receipt"]
            tag = record.evidence["publication-tag-object"]
            if (
                request.repository_id != policy.repository_id
                or receipt["tag_oid"] != tag["oid"]
            ):
                raise ValueError
            row = load_record(
                HistoricalRelease,
                canonical_bytes(
                    {
                        "release_id": receipt["release_id"],
                        "tag": request.tag,
                        "commit": receipt["release_sha"],
                        "line": request.line,
                        "version": request.version,
                        "legacy_version": None,
                        "projections": receipt["projections"],
                    }
                ),
            )
            if row.tag in rows and rows[row.tag] != row:
                raise ValueError
            rows[row.tag] = row
            tag_objects[row.tag] = tag["oid"]
        except (KeyError, ValueError, TypeError, AttributeError):
            raise ControllerError(
                "E_HISTORY",
                "Published journal receipt conflicts with adopted release history.",
            ) from None
    return list(rows.values()), tag_objects
