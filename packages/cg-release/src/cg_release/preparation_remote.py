"""One-shot preparation writes with exact-object and all-state PR reconciliation."""

import base64
import re
from datetime import UTC, datetime
from urllib.parse import quote

from cg_release.events import ControllerError
from cg_release.github import MAX_PAGES
from cg_release.models import canonical_bytes
from cg_release.preparation import object_id


def commit_spec(request, tree: str, created_at: str) -> tuple[str, dict]:
    """Bind commit bytes to receipt time, e.g. commit_spec(req, tree, date).

    The fixed Git author is metadata, not App authority. The protected caller and
    operation allowlist supply authority; no signing or publication is performed.
    """
    try:
        date = datetime.fromisoformat(created_at)
        if date.utcoffset() is None or not re.fullmatch(r"[0-9a-f]{40}", tree):
            raise ValueError
        timestamp = int(date.timestamp())
    except (ValueError, TypeError, AttributeError, OverflowError):
        raise ControllerError(
            "E_PREPARATION", "Immutable receipt timestamp is required."
        ) from None
    author = {
        "name": "Release Controller",
        "email": "release-controller@users.noreply.github.com",
        "date": datetime.fromtimestamp(timestamp, UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    message = f"Prepare release {request.version}\n\nRequest nonce: {request.nonce}\n"
    identity = f"{author['name']} <{author['email']}> {timestamp} +0000"
    raw = (
        f"tree {tree}\nparent {request.source_sha}\nauthor {identity}\n"
        f"committer {identity}\n\n{message}"
    ).encode()
    return object_id("commit", raw), {
        "tree": tree,
        "parents": [request.source_sha],
        "message": message,
        "author": author,
        "committer": author,
    }


class PreparationRemote:
    """Control-App preparation transport; caller must persist intent before ensure."""

    def __init__(self, api, *, fresh=lambda: None):
        """Use verified API and fresh checks, e.g. from prepare_step."""
        self.api, self.fresh = api, fresh

    def optional(self, endpoint: str):
        """Treat only HTTP 404 as absent; retain permission/transport failures."""
        try:
            return self.api.get(endpoint)
        except ControllerError as error:
            if error.code != "E_NOT_FOUND":
                raise
            return None

    def write(self, endpoint: str, payload: dict) -> None:
        """Attempt one allowlisted write; caller must always reconcile its outcome."""
        if endpoint not in {
            "git/blobs",
            "git/trees",
            "git/commits",
            "git/refs",
            "pulls",
        }:
            raise ControllerError("E_ENDPOINT", "Write is outside preparation scope.")
        self.fresh()
        try:
            self.api.runner(
                "gh",
                [
                    "api",
                    "--method",
                    "POST",
                    "--hostname",
                    self.api.host,
                    "--include",
                    "--input",
                    "-",
                    f"repos/{self.api.slug}/{endpoint}",
                ],
                cwd=self.api.cwd,
                timeout=min(self.api.read_seconds, self.api.remaining()),
                allow_failure=True,
                input_text=canonical_bytes(payload).decode(),
            )
        except ControllerError as error:
            if error.code not in {
                "E_TIMEOUT",
                "E_PROCESS",
                "E_RESPONSE",
                "E_RESPONSE_SIZE",
            }:
                raise
        # Even an HTTP success is not a checkpoint. The caller reads exact remote IDs.

    def object(self, kind: str, oid: str, payload: dict) -> dict:
        """Create only an absent content-addressed object, then verify its identity."""
        endpoint = f"git/{kind}/{oid}"
        observed = self.optional(endpoint)
        if observed is None:
            self.write(f"git/{kind}", payload)
            observed = self.optional(endpoint)
        if not isinstance(observed, dict) or observed.get("sha") != oid:
            raise ControllerError(
                "E_WRITE_UNKNOWN", "Preparation object requires exact read-back."
            )
        return observed

    def pulls(self, request, branch: str, head: str) -> list[dict]:
        """Read all-state exact-head PRs, including closed/merged prior requests."""
        values, seen = [], set()
        resource = f"repos/{self.api.slug}/pulls?state=all&head=" + quote(
            self.api.slug.split("/")[0] + ":" + branch, safe=""
        )
        try:
            for page in range(1, MAX_PAGES + 1):
                rows = self.api._request(resource, page)
                if not isinstance(rows, list):
                    raise ValueError
                for row in rows:
                    number = row["number"]
                    if (
                        type(number) is not int
                        or type(row["id"]) is not int
                        or row["id"] <= 0
                        or number <= 0
                        or number in seen
                        or row["head"]["ref"] != branch
                        or row["head"]["sha"] != head
                        or row["base"]["ref"] != request.source_branch
                        or row["head"]["repo"]["id"] != request.repository_id
                        or row["base"]["repo"]["id"] != request.repository_id
                        or row["state"] not in {"open", "closed"}
                        or (row["state"] == "closed" and not row["merged_at"])
                    ):
                        raise ValueError
                    seen.add(number)
                    values.append(row)
                if len(rows) < 100:
                    if len(values) > 1:
                        raise ValueError
                    return values
            raise ValueError
        except (ValueError, TypeError, KeyError, AttributeError):
            raise ControllerError(
                "E_PREPARATION_CONFLICT",
                "Preparation PR inventory is ambiguous or changed.",
            ) from None

    def ensure(
        self, request, prepared, source_tree: str, modes: dict, created_at: str
    ) -> dict:
        """Reconcile one branch and PR after caller persists their exact input intent.

        Args: validated edit tree, source tree/modes, and immutable receipt time.
        Returns: One read-back PR identity. Example: remote.ensure(req, prepared, ...).
        Raises: ControllerError on conflicting or unverifiable remote effects.
        """
        head, commit = commit_spec(request, prepared.tree, created_at)
        branch = "release-controller/" + request.nonce
        prs = self.pulls(request, branch, head)
        ref_endpoint = "git/ref/heads/" + quote(branch, safe="")
        ref = self.optional(ref_endpoint)
        if prs and ref is None:
            raise ControllerError(
                "E_PREPARATION_CONFLICT", "Recorded preparation branch disappeared."
            )
        if ref is None:
            entries = []
            for edit in prepared.edits:
                oid = object_id("blob", edit.content)
                self.object(
                    "blobs",
                    oid,
                    {
                        "encoding": "base64",
                        "content": base64.b64encode(edit.content).decode(),
                    },
                )
                entries.append(
                    {
                        "path": edit.path,
                        "mode": modes.get(edit.path, "100644"),
                        "type": "blob",
                        "sha": oid,
                    }
                )
            self.object(
                "trees", prepared.tree, {"base_tree": source_tree, "tree": entries}
            )
            observed = self.object("commits", head, commit)
            if (
                observed.get("tree", {}).get("sha") != prepared.tree
                or observed.get("parents") is None
                or [p.get("sha") for p in observed["parents"]] != [request.source_sha]
            ):
                raise ControllerError(
                    "E_PREPARATION_CONFLICT",
                    "Preparation commit does not match expected tree/parent.",
                )
            self.write("git/refs", {"ref": "refs/heads/" + branch, "sha": head})
            ref = self.optional(ref_endpoint)
        if (
            not isinstance(ref, dict)
            or ref.get("ref") != "refs/heads/" + branch
            or ref.get("object", {}).get("type") != "commit"
            or ref["object"].get("sha") != head
        ):
            raise ControllerError(
                "E_PREPARATION_CONFLICT",
                "Preparation ref is absent or differs; no force update.",
            )
        if not prs:
            self.write(
                "pulls",
                {
                    "title": "Prepare release " + request.version,
                    "head": branch,
                    "base": request.source_branch,
                    "body": "Release controller request: " + request.nonce,
                    "draft": False,
                },
            )
            prs = self.pulls(request, branch, head)
        if len(prs) != 1:
            raise ControllerError(
                "E_WRITE_UNKNOWN", "Preparation PR creation is not reconciled."
            )
        return {
            "number": prs[0]["number"],
            "id": prs[0]["id"],
            "head": head,
            "branch": branch,
            "tree": prepared.tree,
            "source_sha": request.source_sha,
        }
