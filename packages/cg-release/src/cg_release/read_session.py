"""Bounded command-local immutable reads; mutable authorization is never cached."""

import json
import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from cg_release.events import ControllerError
from cg_release.jsonio import decode_json

if TYPE_CHECKING:
    from cg_release.github import GitHubReads


class ReadCache:
    """Cache only exact Git object OIDs; never branches, permissions, or run state."""

    def __init__(
        self, *, max_bytes: int = 32 * 1024 * 1024, max_entries: int = 1024
    ) -> None:
        """Create bounded ephemeral storage, e.g. ReadCache(max_bytes=1024)."""
        self.max_bytes, self.max_entries = max_bytes, max_entries
        self.values: dict[str, str] = {}
        self.byte_count = 0

    def read(
        self,
        resource: str,
        page: int | None,
        query: str | None,
        remaining: Callable[[], float],
        load: Callable[[], object],
    ) -> object:
        """Read immutable objects once and return independent decoded values."""
        immutable = (
            page is None
            and query is None
            and re.fullmatch(
                r"repos/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/"
                r"(?:git/(?:blobs|trees|commits)|commits)/[0-9a-f]{40}"
                r"(?:\?recursive=1)?",
                resource,
            )
        )
        if not immutable:
            return load()
        remaining()
        if resource not in self.values:
            value = load()
            raw = json.dumps(
                value, ensure_ascii=True, allow_nan=False, separators=(",", ":")
            )
            size = len(raw)
            if size > min(self.max_bytes, 4 * 1024 * 1024) or self.max_entries <= 0:
                return value
            while self.values and (
                self.byte_count + size > self.max_bytes
                or len(self.values) >= self.max_entries
            ):
                self.byte_count -= len(self.values.pop(next(iter(self.values))))
            self.values[resource] = raw
            self.byte_count += size
        result = decode_json(self.values[resource])
        remaining()
        return result


class ReadSession:
    """Reuse readers across preview/recheck/status within one CLI invocation only."""

    def __init__(self) -> None:
        """Start a new isolated read session, e.g. ReadSession()."""
        self.readers: dict[tuple[str, str], GitHubReads] = {}

    def __call__(self, host: str, slug: str, **kwargs: Any) -> "GitHubReads":
        """Return a repository-scoped reader with the caller's current deadline."""
        from cg_release.github import GitHubReads

        key = (host, slug.casefold())
        if key not in self.readers:
            if len(self.readers) >= 4:
                raise ControllerError(
                    "E_REPOSITORY", "Command repository scope changed too often."
                )
            self.readers[key] = GitHubReads(host, slug, **kwargs)
        reader = self.readers[key]
        if kwargs.get("deadline") is not None:
            reader.deadline = kwargs["deadline"]
        return reader
