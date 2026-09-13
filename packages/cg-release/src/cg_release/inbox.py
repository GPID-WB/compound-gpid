"""GitHub durable issue inbox; complete read-only discovery and one-shot creation."""

import json
import re

from cg_release.admission import Locator
from cg_release.events import ControllerError
from cg_release.github import MAX_PAGES, GitHubReads
from cg_release.models import canonical_bytes


class GitHubInbox:
    """Use GitHub's documented issue/edit-history wire shapes, not labels or titles."""

    def __init__(self, api: GitHubReads) -> None:
        """Bind a reader and its command deadline, e.g. GitHubInbox(api)."""
        self.api = api

    def _repository(self, locator: Locator) -> str:
        value = self.api.get("")
        if (
            self.api.host != locator.host
            or not isinstance(value, dict)
            or type(value.get("id")) is not int
            or value["id"] != locator.repository_id
            or value.get("has_issues") is not True
            or not isinstance(value.get("full_name"), str)
            or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value["full_name"])
            or any(part in {".", ".."} for part in value["full_name"].split("/"))
        ):
            raise ControllerError(
                "E_INBOX",
                "Verified repository identity and enabled Issues are required.",
            )
        # A redirect/rename is acceptable only after unchanged numeric identity.
        return value["full_name"]

    def create(self, locator: str, body: bytes) -> None:
        """Attempt one bounded issue POST after intent emission; never retry.

        Args: locator is provisional; body is the strict schema-v1 inbox envelope.
        Returns: None; callers must discover and verify read-back even on success.
        Raises: ControllerError on HTTP/transport uncertainty, e.g. lost response.
        """
        identity = Locator.decode(locator)
        slug = self._repository(identity)
        payload = canonical_bytes(
            {"title": "Release request " + identity.nonce, "body": body.decode("utf-8")}
        )
        result = self.api.runner(
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
                f"repos/{slug}/issues",
            ],
            cwd=self.api.cwd,
            timeout=min(self.api.read_seconds, self.api.remaining()),
            allow_failure=True,
            input_text=payload.decode("utf-8"),
        )
        status = re.match(r"HTTP/[0-9.]+ 201(?: |\r?\n)", result.stdout)
        if result.returncode or not status:
            raise ControllerError(
                "E_SUBMISSION_UNKNOWN",
                "Issue-create outcome needs read-only reconciliation.",
            )

    def inventory(self, locator: Locator) -> list[dict]:
        """Paginate all open/closed issues and verify edit-history availability.

        Args: locator identifies host/repository; no local cache or search index.
        Returns: Complete bounded normalized inventory, e.g. inbox.inventory(locator).
        Raises: ControllerError on partial/ambiguous pagination or wrong shapes.
        """
        slug = self._repository(locator)
        owner, repository_name = slug.split("/")
        cursor, cursors, identities, results = None, set(), set(), []
        for _page in range(MAX_PAGES):
            after = "null" if cursor is None else json.dumps(cursor)
            query = (
                "query { repository(owner:"
                + json.dumps(owner)
                + ",name:"
                + json.dumps(repository_name)
                + ") { databaseId issues(first:100, states:[OPEN,CLOSED], "
                "orderBy:{field:CREATED_AT,direction:ASC}, after:"
                + after
                + ") { nodes { id number body url createdAt lastEditedAt "
                "userContentEdits(first:1) { totalCount } "
                "author { __typename ... on User { databaseId } "
                "... on Bot { databaseId } } } "
                "pageInfo { hasNextPage endCursor } } } }"
            )
            value = self.api._request("graphql", None, query=query)
            try:
                if not isinstance(value, dict) or value.get("errors"):
                    raise ValueError
                repository = value["data"]["repository"]
                if (
                    type(repository["databaseId"]) is not int
                    or repository["databaseId"] != locator.repository_id
                ):
                    raise ValueError
                connection = repository["issues"]
                nodes, info = connection["nodes"], connection["pageInfo"]
                if (
                    not isinstance(nodes, list)
                    or len(nodes) > 100
                    or type(info["hasNextPage"]) is not bool
                ):
                    raise ValueError
                for node in nodes:
                    if (
                        not isinstance(node, dict)
                        or not isinstance(node["id"], str)
                        or not node["id"]
                        or node["id"] in identities
                        or not isinstance(node["body"], str)
                    ):
                        raise ValueError
                    identities.add(node["id"])
                    author = node["author"]
                    author_id = (
                        author.get("databaseId") if isinstance(author, dict) else None
                    )
                    results.append(
                        {
                            "number": node["number"],
                            "node_id": node["id"],
                            "body": node["body"],
                            "url": node["url"],
                            "author_id": author_id,
                            "repository_id": repository["databaseId"],
                            "repository_slug": slug,
                            "created_at": node.get("createdAt"),
                            "last_edited_at": node["lastEditedAt"],
                            "edit_count": node["userContentEdits"]["totalCount"],
                        }
                    )
                if not info["hasNextPage"]:
                    return results
                cursor = info["endCursor"]
                if (
                    not nodes
                    or not isinstance(cursor, str)
                    or not 1 <= len(cursor) <= 1024
                    or cursor in cursors
                ):
                    raise ValueError
                cursors.add(cursor)
            except (KeyError, TypeError, ValueError, AttributeError):
                raise ControllerError(
                    "E_INBOX", "Incomplete or malformed durable inbox inventory."
                ) from None
        raise ControllerError(
            "E_PAGINATION", "Durable inbox exceeds the bounded page limit."
        )
