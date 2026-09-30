"""One bounded encoding contract for real journal writes and publication preflight."""

import base64
import re

from cg_release.events import ControllerError
from cg_release.models import MAX_RECORD_BYTES, canonical_bytes
from cg_release.process import MAX_INPUT_BYTES


def encode_files(slug, branch, parent, files, message):
    """Encode the complete GraphQL transaction or fail before transport execution."""
    changes = {"additions": [], "deletions": []}
    for path, raw in files.items():
        if not re.fullmatch(
            r"(?:events/[0-9]{10,}|(?:requests|reservations|recoveries|compositions)/[0-9a-f]{64}|queue)\.json",
            path,
        ):
            raise ControllerError("E_JOURNAL", "Journal path is outside its allowlist.")
        if raw is None:
            changes["deletions"].append({"path": path})
        elif not isinstance(raw, bytes) or len(raw) > MAX_RECORD_BYTES:
            raise ControllerError(
                "E_JOURNAL_CAPACITY",
                "Journal file exceeds its bounded record capacity.",
            )
        else:
            changes["additions"].append(
                {"path": path, "contents": base64.b64encode(raw).decode()}
            )
    payload = {
        "query": "mutation($input:CreateCommitOnBranchInput!){"
        "createCommitOnBranch(input:$input){commit{oid}}}",
        "variables": {
            "input": {
                "branch": {"repositoryNameWithOwner": slug, "branchName": branch},
                "expectedHeadOid": parent,
                "message": {"headline": message},
                "fileChanges": changes,
            }
        },
    }
    encoded = canonical_bytes(payload)
    if len(encoded) > MAX_INPUT_BYTES:
        raise ControllerError(
            "E_JOURNAL_CAPACITY",
            "Encoded journal transaction exceeds its bounded transport capacity.",
        )
    return encoded.decode()
