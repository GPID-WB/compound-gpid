"""Bounded nonrecursive GitHub Git-tree and raw-blob acquisition."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Dict, List, Mapping, Optional, Tuple
import urllib.error
import urllib.parse
import urllib.request

from skill_management import paths as path_policy


_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
_REPOSITORY_COMPONENT = re.compile(r"^[A-Za-z0-9_.-]+$")


class GitHubAcquisitionError(ValueError):
    """Raised when bounded public GitHub acquisition cannot be proven safe."""


@dataclass(frozen=True)
class AcquisitionLimits:
    """Non-overridable provider and decoded-content ceilings."""

    max_metadata_bytes: int = 1024 * 1024
    max_tree_depth: int = 16
    max_entries: int = 64
    max_file_bytes: int = 262144
    max_total_bytes: int = 1048576

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if type(value) is not int or value <= 0:
                raise ValueError(f"Acquisition limit {name} must be a positive integer")


@dataclass(frozen=True)
class HttpResponse:
    """One already bounded HTTP response returned by an injected transport."""

    status: int
    headers: Mapping[str, str]
    body: bytes


@dataclass(frozen=True)
class AcquiredFile:
    """One verified regular non-executable Git blob."""

    path: str
    content: bytes
    object_id: str
    declared_size: int
    mode: str


@dataclass(frozen=True)
class AcquiredBundle:
    """Complete deterministic candidate acquired from one exact source."""

    origin: str
    commit: str
    source_path: str
    files: Tuple[AcquiredFile, ...]
    digest: str


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        del request, file_pointer, code, message, headers, new_url
        return None


class UrllibTransport:
    """Public unauthenticated HTTPS transport with redirects disabled."""

    def __init__(self, *, timeout: float = 30.0) -> None:
        self._timeout = timeout
        self._opener = urllib.request.build_opener(_NoRedirect)

    def get(self, url: str, *, accept: str, max_bytes: int) -> HttpResponse:
        """Read at most ``max_bytes`` plus one byte from one HTTPS response."""
        request = urllib.request.Request(
            url,
            headers={
                "Accept": accept,
                "User-Agent": "compound-gpid-skill-management/1",
            },
            method="GET",
        )
        try:
            response = self._opener.open(request, timeout=self._timeout)
        except urllib.error.HTTPError as error:
            if 300 <= error.code < 400:
                raise GitHubAcquisitionError("GitHub redirects are not allowed") from error
            raise GitHubAcquisitionError(
                f"GitHub request failed with HTTP {error.code}"
            ) from error
        except (OSError, urllib.error.URLError) as error:
            raise GitHubAcquisitionError("GitHub request failed without a bounded response") from error
        with response:
            status = int(response.getcode())
            if status != 200:
                raise GitHubAcquisitionError(f"GitHub request returned HTTP {status}")
            content_length = response.headers.get("Content-Length")
            if content_length is not None:
                try:
                    declared = int(content_length)
                except ValueError as error:
                    raise GitHubAcquisitionError("GitHub Content-Length is invalid") from error
                if declared < 0 or declared > max_bytes:
                    raise GitHubAcquisitionError("GitHub HTTP body exceeds bounded response limit")
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise GitHubAcquisitionError("GitHub HTTP body exceeds bounded response limit")
            headers = {name.casefold(): value for name, value in response.headers.items()}
            return HttpResponse(status, headers, body)


def normalize_public_github_origin(origin: str) -> str:
    """Normalize one credential-free public GitHub HTTPS repository origin."""
    try:
        parsed = urllib.parse.urlsplit(origin.strip())
    except ValueError as error:
        raise GitHubAcquisitionError("Repository origin is not a valid URL") from error
    if (
        parsed.scheme.casefold() != "https"
        or parsed.hostname is None
        or parsed.hostname.casefold() != "github.com"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port is not None
        or parsed.query
        or parsed.fragment
    ):
        raise GitHubAcquisitionError(
            "Only credential-free https://github.com/<owner>/<repo> origins are supported"
        )
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2:
        raise GitHubAcquisitionError("GitHub origin must identify exactly one repository")
    owner, repository = parts
    if repository.casefold().endswith(".git"):
        repository = repository[:-4]
    if not owner or not repository or not all(
        _REPOSITORY_COMPONENT.fullmatch(part) for part in (owner, repository)
    ):
        raise GitHubAcquisitionError("GitHub owner or repository name is invalid")
    return f"https://github.com/{owner.casefold()}/{repository.casefold()}"


def normalize_source_path(source_path: str) -> str:
    """Return one portable normalized non-root Git tree path."""
    if "\\" in source_path or "\x00" in source_path:
        raise GitHubAcquisitionError("GitHub source path must use POSIX separators")
    pure = PurePosixPath(source_path)
    if pure.is_absolute() or not pure.parts or any(
        part in {"", ".", ".."} for part in pure.parts
    ):
        raise GitHubAcquisitionError("GitHub source path is absolute or traverses")
    normalized = pure.as_posix()
    errors = path_policy.validate_repo_relative_path("GitHub source path", normalized)
    if errors:
        raise GitHubAcquisitionError("; ".join(errors))
    return normalized


def _strict_json(content: bytes, label: str) -> Dict[str, Any]:
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate member {key!r}")
            result[key] = value
        return result

    try:
        value = json.loads(content.decode("utf-8"), object_pairs_hook=no_duplicates)
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise GitHubAcquisitionError(f"GitHub {label} metadata is invalid JSON") from error
    if not isinstance(value, dict):
        raise GitHubAcquisitionError(f"GitHub {label} metadata must be an object")
    return value


class GitHubProvider:
    """Acquire one exact bundle without clone, archive, redirects, or execution."""

    def __init__(self, transport: Optional[Any] = None) -> None:
        self._transport = transport if transport is not None else UrllibTransport()
        self._metadata_used = 0

    def _get_metadata(self, url: str, limits: AcquisitionLimits, label: str) -> Dict[str, Any]:
        remaining = limits.max_metadata_bytes - self._metadata_used
        if remaining <= 0:
            raise GitHubAcquisitionError("GitHub response metadata exceeds its byte ceiling")
        response = self._transport.get(
            url, accept="application/vnd.github+json", max_bytes=remaining
        )
        if response.status != 200:
            raise GitHubAcquisitionError(f"GitHub {label} request failed")
        self._metadata_used += len(response.body)
        return _strict_json(response.body, label)

    @staticmethod
    def _tree_entries(value: Mapping[str, Any], label: str) -> List[Dict[str, Any]]:
        if value.get("truncated") is not False:
            raise GitHubAcquisitionError(f"GitHub {label} tree is truncated or unsupported")
        entries = value.get("tree")
        if not isinstance(entries, list):
            raise GitHubAcquisitionError(f"GitHub {label} tree has no entry array")
        result = []
        seen = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise GitHubAcquisitionError(f"GitHub {label} tree entry is invalid")
            name = entry.get("path")
            entry_type = entry.get("type")
            mode = entry.get("mode")
            object_id = entry.get("sha")
            if (
                not isinstance(name, str)
                or "/" in name
                or name in {"", ".", ".."}
                or not isinstance(entry_type, str)
                or not isinstance(mode, str)
                or not isinstance(object_id, str)
                or _FULL_SHA.fullmatch(object_id) is None
            ):
                raise GitHubAcquisitionError(f"GitHub {label} tree entry metadata is incomplete")
            key = path_policy.portable_path_key(name)
            if key in seen:
                raise GitHubAcquisitionError(f"GitHub {label} tree entries collide portably")
            seen.add(key)
            result.append(entry)
        return sorted(result, key=lambda item: str(item["path"]))

    def acquire(
        self,
        origin: str,
        commit: str,
        source_path: str,
        limits: AcquisitionLimits,
    ) -> AcquiredBundle:
        """Acquire and verify all blobs below one exact Git tree path."""
        normalized_origin = normalize_public_github_origin(origin)
        normalized_path = normalize_source_path(source_path)
        if _FULL_SHA.fullmatch(commit) is None:
            raise GitHubAcquisitionError("Commit must be one full lowercase SHA-1")
        self._metadata_used = 0
        owner, repository = normalized_origin.rsplit("/", 2)[-2:]
        api = f"https://api.github.com/repos/{owner}/{repository}/git"
        commit_data = self._get_metadata(
            f"{api}/commits/{commit}", limits, "commit"
        )
        if commit_data.get("sha") != commit:
            raise GitHubAcquisitionError("GitHub resolved commit identity does not match the request")
        tree = commit_data.get("tree")
        tree_sha = tree.get("sha") if isinstance(tree, dict) else None
        if not isinstance(tree_sha, str) or _FULL_SHA.fullmatch(tree_sha) is None:
            raise GitHubAcquisitionError("GitHub commit has no exact root tree identity")

        for component in PurePosixPath(normalized_path).parts:
            tree_data = self._get_metadata(
                f"{api}/trees/{tree_sha}", limits, "path"
            )
            entries = self._tree_entries(tree_data, "path")
            match = next((entry for entry in entries if entry["path"] == component), None)
            if match is None or match.get("type") != "tree" or match.get("mode") != "040000":
                raise GitHubAcquisitionError(
                    f"GitHub selected path component is not one tree: {component}"
                )
            tree_sha = str(match["sha"])

        declared = []  # type: List[Tuple[str, str, int, str]]
        pending = [(tree_sha, PurePosixPath(), 0)]
        entry_count = 0
        declared_total = 0
        while pending:
            current_sha, prefix, depth = pending.pop()
            if depth > limits.max_tree_depth:
                raise GitHubAcquisitionError("GitHub selected tree exceeds depth ceiling")
            tree_data = self._get_metadata(
                f"{api}/trees/{current_sha}", limits, "selected"
            )
            for entry in reversed(self._tree_entries(tree_data, "selected")):
                entry_count += 1
                if entry_count > limits.max_entries:
                    raise GitHubAcquisitionError("GitHub selected tree exceeds entry ceiling")
                relative = (prefix / str(entry["path"])).as_posix()
                entry_type = entry["type"]
                mode = entry["mode"]
                if entry_type == "tree" and mode == "040000":
                    pending.append((str(entry["sha"]), PurePosixPath(relative), depth + 1))
                    continue
                if entry_type == "commit" or mode == "160000":
                    raise GitHubAcquisitionError("Git submodules are not supported")
                if entry_type != "blob" or mode != "100644":
                    if mode in {"100755", "120000"}:
                        detail = "executable or symbolic-link"
                    else:
                        detail = "unsupported type or mode"
                    raise GitHubAcquisitionError(f"GitHub selected tree contains {detail}: {relative}")
                size = entry.get("size")
                if type(size) is not int or size < 0:
                    raise GitHubAcquisitionError("GitHub blob has missing or invalid size metadata")
                if size > limits.max_file_bytes:
                    raise GitHubAcquisitionError("GitHub declared blob exceeds per-file ceiling")
                declared_total += size
                if declared_total > limits.max_total_bytes:
                    raise GitHubAcquisitionError("GitHub declared blob total exceeds bundle ceiling")
                declared.append((relative, str(entry["sha"]), size, mode))

        acquired = []
        streamed_total = 0
        for relative, object_id, size, mode in sorted(declared):
            response = self._transport.get(
                f"{api}/blobs/{object_id}",
                accept="application/vnd.github.raw+json",
                max_bytes=min(limits.max_file_bytes, limits.max_total_bytes - streamed_total),
            )
            if response.status != 200 or len(response.body) != size:
                raise GitHubAcquisitionError("GitHub raw blob size differs from declared metadata")
            streamed_total += len(response.body)
            if streamed_total > limits.max_total_bytes:
                raise GitHubAcquisitionError("GitHub decoded blob stream exceeds total ceiling")
            actual_id = hashlib.sha1(
                b"blob " + str(len(response.body)).encode("ascii") + b"\0" + response.body
            ).hexdigest()
            if actual_id != object_id:
                raise GitHubAcquisitionError("Git blob object identity verification failed")
            acquired.append(AcquiredFile(relative, response.body, object_id, size, mode))
        if not acquired:
            raise GitHubAcquisitionError("GitHub selected tree contains no regular files")
        digest_rows = [
            {"path": item.path, "objectId": item.object_id, "size": item.declared_size}
            for item in acquired
        ]
        digest = hashlib.sha256(
            json.dumps(digest_rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return AcquiredBundle(
            normalized_origin,
            commit,
            normalized_path,
            tuple(acquired),
            digest,
        )
