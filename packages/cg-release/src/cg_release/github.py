"""GitHub GET-only transport with bounded pages, retries, and shared deadlines."""

import json
import re
import time
from collections.abc import Callable
from pathlib import Path
from urllib.parse import quote

from cg_release.events import ControllerError
from cg_release.github_profile_reads import ProfileReads
from cg_release.jsonio import decode_json
from cg_release.process import run_process
from cg_release.read_session import ReadCache

MAX_PAGES = 1000


class GitHubReads(ProfileReads):
    """Read one verified host/slug; no method can dispatch or mutate a resource."""

    def __init__(
        self,
        host: str,
        slug: str,
        *,
        cwd: Path,
        runner: Callable = run_process,
        clock: Callable = time.monotonic,
        deadline: float | None = None,
        sleep: Callable = time.sleep,
    ) -> None:
        """Create a reader, e.g. GitHubReads('github.com', 'owner/repo', cwd=path).

        Args: host/slug identify the repository without credentials; cwd is the
        process directory. runner, monotonic clock, and backoff sleep are injectable.
        deadline is absolute and shared, defaulting to 120 seconds from now.
        Raises: ControllerError for an unsafe host or slug.
        """
        if (
            not re.fullmatch(r"[a-z0-9]+(?:[.-][a-z0-9]+)*", host)
            or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", slug)
            or any(p in {".", ".."} for p in slug.split("/"))
        ):
            raise ControllerError(
                "E_REPOSITORY", "Invalid GitHub host or repository slug."
            )
        self.host, self.slug, self.cwd = host, slug, cwd
        self.runner, self.clock, self.sleep = runner, clock, sleep
        self.deadline = clock() + 120 if deadline is None else deadline
        self.read_seconds, self.read_attempts = 20, 3
        self._read_cache = ReadCache()

    def remaining(self) -> float:
        """Return time remaining, e.g. before a read; raise E_DEADLINE on expiry."""
        remaining = self.deadline - self.clock()
        if remaining <= 0:
            raise ControllerError(
                "E_DEADLINE",
                "Command deadline exceeded; reconcile any attempted remote writes.",
            )
        return remaining

    def get(self, endpoint: str, *, page: int | None = None) -> object:
        """GET a repository endpoint, e.g. get('releases', page=1).

        Args: endpoint is a relative REST resource with no host/query override.
        page selects a bounded page number with 100 items per page.
        Returns: Decoded data. HTTP 403 and 404 remain distinct typed errors.
        Raises: ControllerError for input, HTTP, response, or deadline errors.
        """
        if (
            not re.fullmatch(r"[A-Za-z0-9_./%~-]*", endpoint)
            or endpoint.startswith("/")
            or (
                ".." in endpoint
                and not re.fullmatch(
                    r"compare/[0-9a-f]{40}\.\.\.[0-9a-f]{40}", endpoint
                )
            )
            or (
                page is not None
                and (type(page) is not int or not 1 <= page <= MAX_PAGES)
            )
        ):
            raise ControllerError("E_ENDPOINT", "Unsafe API endpoint rejected.")
        return self._request(
            f"repos/{self.slug}" + (f"/{endpoint}" if endpoint else ""), page
        )

    def actor(self) -> dict:
        """Read authenticated actor, e.g. reader.actor(); no local identity fallback."""
        value = self._request("user", None)
        if (
            not isinstance(value, dict)
            or type(value.get("id")) is not int
            or value["id"] <= 0
            or not isinstance(value.get("login"), str)
            or not re.fullmatch(r"[A-Za-z0-9-]+", value["login"])
        ):
            raise ControllerError(
                "E_RESPONSE", "Authenticated actor identity is unavailable."
            )
        return value

    def _request(
        self, resource: str, page: int | None, *, query: str | None = None
    ) -> object:
        return self._read_cache.read(
            resource,
            page,
            query,
            self.remaining,
            lambda: self._uncached_request(resource, page, query=query),
        )

    def _uncached_request(
        self, resource: str, page: int | None, *, query: str | None = None
    ) -> object:
        separator = "&" if "?" in resource else "?"
        endpoint = resource + (
            f"{separator}per_page=100&page={page}" if page is not None else ""
        )
        argv = ["api", "--method", "GET", "--hostname", self.host, "--include"]
        if query is not None:
            argv.extend(["--raw-field", "query=" + query])
        argv.append(endpoint)
        for attempt in range(self.read_attempts):
            try:
                result = self.runner(
                    "gh",
                    argv,
                    cwd=self.cwd,
                    timeout=min(self.read_seconds, self.remaining()),
                    allow_failure=True,
                )
            except ControllerError as error:
                if error.code != "E_TIMEOUT" or attempt + 1 == self.read_attempts:
                    raise
            else:
                self.remaining()
                raw = result.stdout.replace("\r\n", "\n")
                header, separator, body = raw.partition("\n\n")
                match = re.match(r"HTTP/[0-9.]+ ([0-9]{3})(?: |\n)", header)
                if not separator or not match:
                    raise ControllerError(
                        "E_RESPONSE", "GitHub CLI returned no verifiable HTTP status."
                    )
                status = int(match[1])
                if status == 200 and result.returncode == 0:
                    return decode_json(body)
                codes = {401: "E_AUTH", 403: "E_FORBIDDEN", 404: "E_NOT_FOUND"}
                if status in codes:
                    raise ControllerError(
                        codes[status],
                        f"GitHub read returned HTTP {status}; history is not empty.",
                    )
                if (
                    status not in {429, 500, 502, 503, 504}
                    or attempt + 1 == self.read_attempts
                ):
                    raise ControllerError(
                        "E_HTTP", f"GitHub read failed with HTTP {status}."
                    )
            delay = 0.25 * (2**attempt)
            if self.remaining() <= delay:
                raise ControllerError(
                    "E_DEADLINE", "Insufficient command time for read retry."
                )
            self.sleep(delay)
        raise ControllerError("E_HTTP", "Read attempts exhausted.")

    def pages(self, endpoint: str) -> list[dict]:
        """Read complete objects, e.g. pages('releases'); reject duplicates."""
        return self._object_pages(lambda page: self.get(endpoint, page=page))

    def _object_pages(self, read) -> list[dict]:
        """Apply the same shape and identity checks to dedicated query operations."""
        results, seen = [], set()
        for page in range(1, MAX_PAGES + 1):
            values = read(page)
            if not isinstance(values, list) or any(
                not isinstance(v, dict) for v in values
            ):
                raise ControllerError(
                    "E_RESPONSE", "Expected a paginated list of objects."
                )
            for value in values:
                identity = value.get("id", value.get("ref", value.get("name")))
                if (
                    not isinstance(identity, (str, int))
                    or isinstance(identity, bool)
                    or identity in seen
                ):
                    raise ControllerError(
                        "E_PAGINATION",
                        "Missing or duplicate identity in paginated response.",
                    )
                seen.add(identity)
                results.append(value)
            if len(values) < 100:
                return results
        raise ControllerError("E_PAGINATION", "History exceeds the bounded page limit.")

    def branch(self, name: str) -> dict:
        """GET one exact branch, e.g. branch('feature/rc'); verify returned name/SHA."""
        from cg_release.policy import safe_ref

        safe_ref(name)
        value = self.get("branches/" + quote(name, safe=""))
        if (
            not isinstance(value, dict)
            or value.get("name") != name
            or not isinstance(value.get("commit"), dict)
            or not isinstance(value["commit"].get("sha"), str)
            or not re.fullmatch(r"[0-9a-f]{40}", value["commit"]["sha"])
        ):
            raise ControllerError(
                "E_RESPONSE", "Branch identity or commit is not verifiable."
            )
        return value

    def refs(self) -> list[dict]:
        """Read all tag refs through cursor pagination, e.g. reader.refs().

        GraphQL GET paginates without mutation; REST matching-refs has no page API.
        Returned object IDs are peeled through exact REST reads.
        """
        owner, repository_name = self.slug.split("/")
        cursor, seen, result = None, set(), []
        for _page in range(MAX_PAGES):
            after = "null" if cursor is None else json.dumps(cursor)
            query = (
                "query { repository(owner:"
                + json.dumps(owner)
                + ",name:"
                + json.dumps(repository_name)
                + ') { databaseId refs(refPrefix:"refs/tags/", first:100, after:'
                + after
                + ") { nodes { name target { oid __typename } } "
                "pageInfo { hasNextPage endCursor } } } }"
            )
            value = self._request("graphql", None, query=query)
            try:
                if not isinstance(value, dict) or value.get("errors"):
                    raise ValueError
                repository = value["data"]["repository"]
                if type(repository["databaseId"]) is not int:
                    raise ValueError
                connection = repository["refs"]
                nodes, info = connection["nodes"], connection["pageInfo"]
                if not isinstance(nodes, list) or type(info["hasNextPage"]) is not bool:
                    raise ValueError
                for node in nodes:
                    name, target = node["name"], node["target"]
                    if (
                        not isinstance(name, str)
                        or name in seen
                        or not re.fullmatch(r"[0-9a-f]{40}", target["oid"])
                    ):
                        raise ValueError
                    seen.add(name)
                    result.append(
                        {
                            "ref": "refs/tags/" + name,
                            "object": {
                                "sha": target["oid"],
                                "type": {"Tag": "tag", "Commit": "commit"}.get(
                                    target["__typename"], "invalid"
                                ),
                            },
                            "repository_id": repository["databaseId"],
                        }
                    )
                if not info["hasNextPage"]:
                    return result
                next_cursor = info["endCursor"]
                if (
                    not nodes
                    or not isinstance(next_cursor, str)
                    or not next_cursor
                    or next_cursor == cursor
                    or len(next_cursor) > 1024
                ):
                    raise ValueError
                cursor = next_cursor
            except (KeyError, TypeError, ValueError, AttributeError):
                raise ControllerError(
                    "E_PAGINATION", "Incomplete or malformed tag-ref cursor inventory."
                ) from None
        raise ControllerError("E_PAGINATION", "Tag-ref page limit exceeded.")
