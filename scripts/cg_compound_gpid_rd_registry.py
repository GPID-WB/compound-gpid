"""Validate and update the Compound GPID competitive-review registry.

The utility performs deterministic local transformations only. It does not
access GitHub or any other network service.

Example:
    Run ``python scripts/cg_compound_gpid_rd_registry.py add --url
    https://github.com/acme/widget --check-only`` to inspect a proposed entry.
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 8):
    sys.stderr.write("Python 3.8 or newer is required.\n")
    raise SystemExit(1)

import argparse
import copy
from datetime import date
from decimal import Decimal
import errno
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import urlsplit
import warnings

import secure_fs


EXPECTED_SCHEMA_VERSION = "compound-gpid-competitive-reviews-v1"
REGISTRY_RELATIVE_PATH = Path(".cg-docs/competitive-reviews/repos.json")
MAX_REGISTRY_BYTES = 1_048_576
MAX_ID_LENGTH = 50
MAX_SHORT_NAME_LENGTH = 10
MAX_RELEASE_LENGTH = 128
MAX_JSON_DEPTH = 100
MAX_RESPONSE_BYTES = 1_048_576

WARNING_CODES = (
    "secure-fs-recovery-preserved",
    "secure-fs-cleanup-durability-unconfirmed",
    "secure-fs-temporary-cleanup-failed",
    "secure-fs-runtime-warning",
)

_ABSENT = object()

JsonObject = Dict[str, Any]

_OWNER_PATTERN = re.compile(r"[A-Za-z0-9-]+", re.ASCII)
_REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9._-]+", re.ASCII)
_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,49}", re.ASCII)
_SHORT_NAME_PATTERN = re.compile(r"[A-Za-z0-9]{1,10}", re.ASCII)
_DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", re.ASCII)
_RELEASE_PATTERN = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._+/-]{0,127}",
    re.ASCII,
)
_NON_ALPHANUMERIC_PATTERN = re.compile(r"[^A-Za-z0-9]+", re.ASCII)


class RegistryError(ValueError):
    """Report an expected registry or domain validation failure."""


def _before_secure_replace(_path: Path) -> None:
    """Provide the sole test hook at the final secure replacement boundary."""


def normalize_github_url(raw_url: str) -> str:
    """Normalize one public GitHub repository URL.

    Args:
        raw_url: Candidate ``https://github.com/<owner>/<repository>`` URL.

    Returns:
        The canonical URL without a trailing slash or one terminal ``.git``.

    Raises:
        RegistryError: If the URL or either GitHub name is invalid.

    Example:
        >>> normalize_github_url("https://github.com/Acme/widget.git/")
        'https://github.com/Acme/widget'
    """
    if type(raw_url) is not str:
        raise RegistryError("GitHub URL must be a string.")
    if any(
        character.isspace() or ord(character) < 32 or ord(character) == 127
        for character in raw_url
    ):
        raise RegistryError(
            "GitHub repository URL must not contain whitespace or control characters."
        )
    if "?" in raw_url:
        raise RegistryError("GitHub URL must not contain a query.")
    if "#" in raw_url:
        raise RegistryError("GitHub URL must not contain a fragment.")
    try:
        parsed = urlsplit(raw_url)
    except ValueError as error:
        raise RegistryError("GitHub URL could not be parsed: {}.".format(error)) from error

    if parsed.scheme != "https":
        raise RegistryError("GitHub URL must use https.")
    if parsed.username is not None or parsed.password is not None:
        raise RegistryError("GitHub URL must not contain credentials.")
    try:
        port = parsed.port
    except ValueError as error:
        raise RegistryError("GitHub URL contains an invalid port.") from error
    if port is not None:
        raise RegistryError("GitHub URL must not contain a port.")
    if parsed.hostname != "github.com":
        raise RegistryError("GitHub URL host must be exactly github.com.")
    if parsed.netloc.casefold() != "github.com":
        if ":" in parsed.netloc:
            raise RegistryError("GitHub URL must not contain a port.")
        raise RegistryError("GitHub URL host must be exactly github.com.")

    path = parsed.path[:-1] if parsed.path.endswith("/") else parsed.path
    segments = path.split("/")
    if len(segments) != 3 or segments[0] != "":
        if len(segments) < 3 or not any(segments[1:2]):
            raise RegistryError(
                "GitHub URL must contain one owner and one repository."
            )
        raise RegistryError("GitHub URL path must contain exactly two segments.")
    owner, repository = segments[1], segments[2]
    if not owner:
        raise RegistryError("GitHub URL owner must not be empty.")
    if not repository:
        raise RegistryError("GitHub URL repository must not be empty.")
    if repository.endswith(".git"):
        repository = repository[:-4]

    _validate_owner(owner)
    _validate_repository_name(repository)
    return "https://github.com/{}/{}".format(owner, repository)


def derive_repository_id(
    owner: str,
    repository: str,
    normalized_url: str,
    existing_repos: Sequence[Mapping[str, Any]],
) -> str:
    """Derive a unique registry ID from a normalized repository URL.

    Args:
        owner: Valid GitHub owner name.
        repository: Valid GitHub repository name without ``.git``.
        normalized_url: Canonical URL used for deterministic hash shortening.
        existing_repos: Valid existing registry entries.

    Returns:
        A unique ID of at most 50 characters.

    Raises:
        RegistryError: If the base and owner-qualified IDs both collide.

    Example:
        >>> derive_repository_id(
        ...     "Acme",
        ...     "alpha_tools",
        ...     "https://github.com/Acme/alpha_tools",
        ...     [],
        ... )
        'alpha-tools'
    """
    repository_slug = _slugify(repository)
    owner_slug = _slugify(owner)
    base = repository_slug or "{}-repo".format(owner_slug)
    existing_ids = {item["id"] for item in existing_repos}

    candidate = _shorten_id(base, normalized_url)
    if candidate not in existing_ids and _ID_PATTERN.fullmatch(candidate):
        return candidate

    qualified_base = "{}-{}".format(
        owner_slug,
        repository_slug or "repo",
    )
    qualified = _shorten_id(qualified_base, normalized_url)
    if qualified not in existing_ids and _ID_PATTERN.fullmatch(qualified):
        return qualified
    raise RegistryError(
        "Could not derive a valid unique repository id from URL {!r}.".format(
            normalized_url
        )
    )


def derive_short_name(
    owner: str,
    repository: str,
    existing_repos: Sequence[Mapping[str, Any]],
) -> str:
    """Derive the smallest unique registry short name.

    Args:
        owner: Valid GitHub owner name.
        repository: Valid GitHub repository name without ``.git``.
        existing_repos: Valid existing registry entries.

    Returns:
        A case-insensitively unique alphanumeric name of at most ten characters.

    Raises:
        RegistryError: If suffixes 2 through 99 are all occupied.

    Example:
        >>> derive_short_name("Acme", "alpha-tools", [])
        'AT'
    """
    tokens = [
        token
        for token in _NON_ALPHANUMERIC_PATTERN.split(repository)
        if token
    ]
    if len(tokens) > 1:
        base = "".join(token[0].upper() for token in tokens)
    elif tokens:
        base = "".join(
            character for character in repository if character.isascii() and character.isalnum()
        )
    else:
        base = "".join(
            character for character in owner if character.isascii() and character.isalnum()
        )
    base = base[:MAX_SHORT_NAME_LENGTH]
    existing = {item["shortName"].casefold() for item in existing_repos}
    if base.casefold() not in existing and _SHORT_NAME_PATTERN.fullmatch(base):
        return base
    for suffix_number in range(2, 100):
        suffix = str(suffix_number)
        candidate = base[: MAX_SHORT_NAME_LENGTH - len(suffix)] + suffix
        if (
            candidate.casefold() not in existing
            and _SHORT_NAME_PATTERN.fullmatch(candidate)
        ):
            return candidate
    raise RegistryError("Could not derive a unique repository shortName.")


def validate_registry(data: Any) -> None:
    """Validate the complete v1 registry without changing it.

    Args:
        data: Parsed JSON value expected to contain the v1 registry object.

    Returns:
        ``None`` after successful validation.

    Raises:
        RegistryError: If any required schema, type, format, or uniqueness rule
            fails.

    Example:
        >>> validate_registry({"schemaVersion": EXPECTED_SCHEMA_VERSION,
        ...                    "repos": []})
    """
    _validate_json_tree(data)
    if not isinstance(data, dict):
        raise RegistryError("Registry root must be a JSON object.")
    if "schemaVersion" not in data:
        raise RegistryError("Registry root is missing schemaVersion.")
    if data["schemaVersion"] != EXPECTED_SCHEMA_VERSION:
        raise RegistryError(
            "Registry schemaVersion must equal {!r}.".format(
                EXPECTED_SCHEMA_VERSION
            )
        )
    if "repos" not in data:
        raise RegistryError("Registry root is missing repos.")
    repos = data["repos"]
    if not isinstance(repos, list):
        raise RegistryError("Registry repos must be a JSON array.")

    if "lastFullReview" in data and data["lastFullReview"] is not None:
        _validate_date(data["lastFullReview"], "lastFullReview in registry root")
    if "lastFullReviewNote" in data:
        note = data["lastFullReviewNote"]
        if type(note) is not str or not note:
            raise RegistryError(
                "lastFullReviewNote in registry root must be a non-empty string."
            )
        if "lastFullReview" not in data or data["lastFullReview"] is not None:
            raise RegistryError(
                "lastFullReviewNote requires lastFullReview to be present and null."
            )

    seen_ids = set()
    seen_urls = set()
    seen_short_names = set()
    for index, entry in enumerate(repos):
        _validate_entry(entry, index)
        repo_id = entry["id"]
        normalized_url = entry["url"].casefold()
        short_name = entry["shortName"].casefold()
        if repo_id in seen_ids:
            raise RegistryError("Duplicate repository id {!r}.".format(repo_id))
        if normalized_url in seen_urls:
            raise RegistryError(
                "Duplicate repository URL {!r}.".format(entry["url"])
            )
        if short_name in seen_short_names:
            raise RegistryError(
                "Duplicate repository shortName {!r}.".format(entry["shortName"])
            )
        seen_ids.add(repo_id)
        seen_urls.add(normalized_url)
        seen_short_names.add(short_name)


def load_registry(root: Path) -> Tuple[JsonObject, bytes]:
    """Securely load and validate the root-relative registry.

    Args:
        root: Existing project root.

    Returns:
        The validated registry and the exact source bytes used for write state.

    Raises:
        RegistryError: If secure reading or strict parsing fails.
        UnicodeDecodeError: If the source is not strict UTF-8.
        json.JSONDecodeError: If the source is malformed JSON.

    Example:
        ``registry, source = load_registry(Path.cwd())`` loads the tracked file.
    """
    try:
        source = secure_fs.secure_read_bytes(
            root,
            REGISTRY_RELATIVE_PATH,
            reject_hardlinks=True,
            max_bytes=MAX_REGISTRY_BYTES,
        )
    except FileNotFoundError as error:
        raise RegistryError(
            "Registry {} was not found.".format(REGISTRY_RELATIVE_PATH)
        ) from error
    except secure_fs.SecureMutationError as error:
        if "size" in str(error).casefold() and "limit" in str(error).casefold():
            raise RegistryError(
                "Registry size exceeds the {} byte limit.".format(
                    MAX_REGISTRY_BYTES
                )
            ) from error
        raise RegistryError(
            "Secure registry read rejected an unsafe link or file state: {}".format(
                error
            )
        ) from error
    except OSError as error:
        if error.errno in {errno.ELOOP, errno.ENOTDIR}:
            raise RegistryError(
                "Secure registry read rejected an unsafe link or file state: {}".format(
                    error
                )
            ) from error
        raise RegistryError("Could not read registry: {}".format(error)) from error

    if len(source) > MAX_REGISTRY_BYTES:
        raise RegistryError(
            "Registry size exceeds the {} byte limit.".format(MAX_REGISTRY_BYTES)
        )
    text = source.decode("utf-8", errors="strict")
    try:
        data = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonfinite_constant,
            parse_float=Decimal,
            parse_int=Decimal,
        )
    except (RegistryError, json.JSONDecodeError):
        raise
    except (RecursionError, ValueError) as error:
        raise RegistryError(
            "Registry JSON exceeds supported parser limits: {}".format(error)
        ) from error
    validate_registry(data)
    return data, source


def add_repository(data: JsonObject, raw_url: str) -> Tuple[JsonObject, JsonObject]:
    """Return a copy of a registry with one proposed repository appended.

    Args:
        data: Valid v1 registry object.
        raw_url: Candidate GitHub repository URL.

    Returns:
        A tuple containing the transformed registry and the new entry.

    Raises:
        RegistryError: If the registry, URL, or derived fields are invalid.

    Example:
        >>> source = {"schemaVersion": EXPECTED_SCHEMA_VERSION, "repos": []}
        >>> updated, repo = add_repository(source, "https://github.com/a/b")
        >>> repo["id"]
        'b'
    """
    validate_registry(data)
    normalized_url = normalize_github_url(raw_url)
    repos = data["repos"]
    for entry in repos:
        if entry["url"].casefold() == normalized_url.casefold():
            raise RegistryError(
                "Duplicate repository URL {!r}; existing id is {!r}.".format(
                    normalized_url,
                    entry["id"],
                )
            )

    url_path = normalized_url[len("https://github.com/") :]
    owner, repository = url_path.split("/", 1)
    proposed = {
        "id": derive_repository_id(owner, repository, normalized_url, repos),
        "url": normalized_url,
        "releasesUrl": normalized_url + "/releases",
        "shortName": derive_short_name(owner, repository, repos),
        "lastReviewedRelease": None,
    }
    transformed = copy.deepcopy(data)
    transformed["repos"].append(proposed)
    validate_registry(transformed)
    return transformed, proposed


def remove_repository(
    data: JsonObject,
    repo_id: str,
    confirm_id: str,
    expected_url: Optional[str] = None,
) -> Tuple[JsonObject, JsonObject]:
    """Return a copy of a registry with one exactly confirmed entry removed.

    Args:
        data: Valid v1 registry object.
        repo_id: Case-sensitive ID to remove.
        confirm_id: Confirmation token that must exactly equal ``repo_id``.
        expected_url: Optional exact stored URL authorization.

    Returns:
        A tuple containing the transformed registry and removed entry.

    Raises:
        RegistryError: If validation, confirmation, or exact ID lookup fails.

    Example:
        >>> item = {"id": "a", "url": "https://github.com/a/a",
        ... "releasesUrl": "https://github.com/a/a/releases",
        ... "shortName": "A", "lastReviewedRelease": None}
        >>> source = {"schemaVersion": EXPECTED_SCHEMA_VERSION, "repos": [item]}
        >>> updated, removed = remove_repository(source, "a", "a")
        >>> updated["repos"]
        []
    """
    validate_registry(data)
    if repo_id != confirm_id:
        raise RegistryError(
            "Confirmation id must exactly match the case-sensitive repository id."
        )
    matching_index, matching_entry = _find_repository(data, repo_id)
    if expected_url is not None and matching_entry["url"] != expected_url:
        raise RegistryError(
            "Repository URL changed for id {!r}; expected {!r}, found {!r}.".format(
                repo_id,
                expected_url,
                matching_entry["url"],
            )
        )
    transformed = copy.deepcopy(data)
    removed = transformed["repos"].pop(matching_index)
    validate_registry(transformed)
    return transformed, removed


def review_repository(
    data: JsonObject,
    repo_id: str,
    expected_url: str,
    release: Optional[str],
    review_date: Any = _ABSENT,
) -> Tuple[JsonObject, JsonObject]:
    """Return a registry copy with one exact repository review state updated.

    Args:
        data: Valid v1 registry object.
        repo_id: Exact case-sensitive repository ID.
        expected_url: Exact stored URL authorization.
        release: Non-empty release string or explicit ``None``.
        review_date: YYYY-MM-DD string, explicit ``None``, or omitted to remove
            ``lastReviewDate``.

    Returns:
        The transformed registry and complete transformed repository entry.

    Raises:
        RegistryError: If validation or exact identity authorization fails.

    Example:
        >>> item = {"id": "a", "url": "https://github.com/a/a",
        ...         "releasesUrl": "https://github.com/a/a/releases",
        ...         "shortName": "A", "lastReviewedRelease": None}
        >>> source = {"schemaVersion": EXPECTED_SCHEMA_VERSION, "repos": [item]}
        >>> updated, repo = review_repository(
        ...     source, "a", item["url"], "v1", "2026-08-28"
        ... )
        >>> repo["lastReviewedRelease"]
        'v1'
    """
    validate_registry(data)
    matching_index, matching_entry = _find_repository(data, repo_id)
    if matching_entry["url"] != expected_url:
        raise RegistryError(
            "Repository URL changed for id {!r}; expected {!r}, found {!r}.".format(
                repo_id,
                expected_url,
                matching_entry["url"],
            )
        )
    transformed = copy.deepcopy(data)
    updated = transformed["repos"][matching_index]
    updated["lastReviewedRelease"] = release
    if review_date is _ABSENT:
        updated.pop("lastReviewDate", None)
    else:
        updated["lastReviewDate"] = review_date
    validate_registry(transformed)
    return transformed, updated


def review_full(
    data: JsonObject,
    outcome: str,
    review_date: str,
    reviewed_ids: Sequence[str],
    failed_ids: Sequence[str],
) -> Tuple[JsonObject, List[str], List[str]]:
    """Return a registry copy with one deterministic full-review outcome.

    Args:
        data: Valid v1 registry object.
        outcome: Exact value ``complete`` or ``partial``.
        review_date: Date for this full-review run.
        reviewed_ids: IDs successfully reviewed in this run.
        failed_ids: IDs that failed in this run.

    Returns:
        The transformed registry plus reviewed and failed IDs in registry order.

    Raises:
        RegistryError: If lists do not partition scope or dates do not prove
            the declared outcome.

    Example:
        >>> item = {"id": "a", "url": "https://github.com/a/a",
        ...         "releasesUrl": "https://github.com/a/a/releases",
        ...         "shortName": "A", "lastReviewedRelease": "v1",
        ...         "lastReviewDate": "2026-08-28"}
        >>> source = {"schemaVersion": EXPECTED_SCHEMA_VERSION, "repos": [item]}
        >>> updated, reviewed, failed = review_full(
        ...     source, "complete", "2026-08-28", ["a"], []
        ... )
        >>> (updated["lastFullReview"], reviewed, failed)
        ('2026-08-28', ['a'], [])
    """
    validate_registry(data)
    _validate_date(review_date, "review-full review date")
    if outcome not in {"complete", "partial"}:
        raise RegistryError("review-full outcome must be complete or partial.")
    if not data["repos"]:
        raise RegistryError("review-full requires a non-empty registry scope.")

    current_ids = [entry["id"] for entry in data["repos"]]
    reviewed = _validate_scope_ids(reviewed_ids, "reviewed")
    failed = _validate_scope_ids(failed_ids, "failed")
    overlap = set(reviewed).intersection(failed)
    if overlap:
        raise RegistryError(
            "reviewed and failed repository IDs must be disjoint; overlap: {}.".format(
                ", ".join(repo_id for repo_id in current_ids if repo_id in overlap)
            )
        )
    declared = set(reviewed).union(failed)
    if declared != set(current_ids):
        missing = [repo_id for repo_id in current_ids if repo_id not in declared]
        unknown = [repo_id for repo_id in reviewed + failed if repo_id not in current_ids]
        raise RegistryError(
            "reviewed and failed repository IDs must partition current scope; "
            "missing: {}; unknown: {}.".format(
                ", ".join(missing) or "none",
                ", ".join(unknown) or "none",
            )
        )

    ordered_reviewed = [repo_id for repo_id in current_ids if repo_id in reviewed]
    ordered_failed = [repo_id for repo_id in current_ids if repo_id in failed]
    if outcome == "complete":
        if ordered_failed:
            raise RegistryError("A complete review-full outcome cannot contain failures.")
        if ordered_reviewed != current_ids:
            raise RegistryError("A complete review-full outcome must review all repos.")
    elif not ordered_failed:
        raise RegistryError("A partial review-full outcome requires failed repos.")

    entries = {entry["id"]: entry for entry in data["repos"]}
    for repo_id in ordered_reviewed:
        if entries[repo_id].get("lastReviewDate", _ABSENT) != review_date:
            raise RegistryError(
                "Reviewed repository {!r} must have lastReviewDate {!r}.".format(
                    repo_id,
                    review_date,
                )
            )

    transformed = copy.deepcopy(data)
    if outcome == "complete":
        transformed["lastFullReview"] = review_date
        transformed.pop("lastFullReviewNote", None)
    else:
        transformed["lastFullReview"] = None
        transformed["lastFullReviewNote"] = "partial - {}".format(
            ", ".join(ordered_failed)
        )
    validate_registry(transformed)
    return transformed, ordered_reviewed, ordered_failed


def render_registry(data: JsonObject) -> bytes:
    """Render a validated registry as deterministic UTF-8 JSON.

    Args:
        data: Complete v1 registry object.

    Returns:
        Two-space-indented UTF-8 JSON with one final newline.

    Raises:
        RegistryError: If validation or strict JSON serialization fails.

    Example:
        >>> value = {"schemaVersion": EXPECTED_SCHEMA_VERSION, "repos": []}
        >>> render_registry(value).endswith(b"\\n")
        True
    """
    validate_registry(data)
    try:
        text = _serialize_json(data, indent=2)
        return (text + "\n").encode("utf-8", errors="strict")
    except (RecursionError, TypeError, ValueError, UnicodeEncodeError) as error:
        raise RegistryError(
            "Registry cannot be serialized as strict UTF-8 JSON: {}".format(error)
        ) from error


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the registry command-line interface.

    Args:
        argv: Optional arguments without the program name. Defaults to
            ``sys.argv[1:]``.

    Returns:
        Zero on a flushed valid response, one for a definite precommit
        rejection, or three for an ambiguous post-writer-dispatch outcome.
        Invalid argparse syntax raises ``SystemExit(2)``.

    Example:
        ``main(["add", "--url", "https://github.com/a/b", "--check-only"])``
        checks the registry below the current directory.
    """
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    _validate_cli_arguments(parser, arguments)
    writer_dispatched = False
    try:
        root = Path(arguments.root).resolve()
        data, source = load_registry(root)
        before_sha256 = _sha256(source)
        before_scope_digest = _scope_digest(data)

        if arguments.command == "state":
            payload = _state_payload(
                data,
                before_sha256,
                before_scope_digest,
                arguments.repo_id,
                arguments.expected_url,
            )
            return _emit_precommit_response(_render_response(payload))

        check_only = arguments.check_only
        if check_only and arguments.command in {"review-repo", "review-full"}:
            _require_expected_sha256(
                arguments.expected_chain_sha256,
                before_sha256,
            )
        elif not check_only:
            _require_expected_sha256(arguments.expected_sha256, before_sha256)

        if arguments.command == "add":
            transformed, repo = add_repository(data, arguments.url)
            response_values = {"repo": repo}
        elif arguments.command == "remove":
            confirm_id = arguments.repo_id if check_only else arguments.confirm_id
            expected_url = None if check_only else arguments.expected_url
            transformed, repo = remove_repository(
                data,
                arguments.repo_id,
                confirm_id,
                expected_url,
            )
            response_values = {"repo": repo}
        elif arguments.command == "review-repo":
            _require_expected_review_state(
                data,
                arguments.repo_id,
                arguments.expected_url,
                arguments.expected_last_reviewed_release,
                arguments.expected_last_review_date,
            )
            if arguments.release is not None:
                _validate_release(arguments.release, "New reviewed release")
            transformed, repo = review_repository(
                data,
                arguments.repo_id,
                arguments.expected_url,
                arguments.release,
                arguments.review_date,
            )
            response_values = {"repo": repo}
        else:
            if check_only:
                _require_expected_scope_digest(
                    arguments.expected_scope_digest_sha256,
                    before_scope_digest,
                )
            transformed, reviewed, failed = review_full(
                data,
                arguments.outcome,
                arguments.review_date,
                arguments.reviewed_ids,
                arguments.failed_ids,
            )
            response_values = {
                "outcome": arguments.outcome,
                "reviewDate": arguments.review_date,
                "reviewedIds": reviewed,
                "failedIds": failed,
                "rootReview": _root_review_projection(transformed),
            }

        rendered_registry = render_registry(transformed)
        if len(rendered_registry) > MAX_REGISTRY_BYTES:
            raise RegistryError(
                "Rendered registry size exceeds the {} byte limit.".format(
                    MAX_REGISTRY_BYTES
                )
            )
        after_sha256 = _sha256(rendered_registry)
        after_scope_digest = _scope_digest(transformed)
        should_write = not check_only and after_sha256 != before_sha256
        payload = {
            "action": arguments.command,
            "changed": should_write,
            "beforeSha256": before_sha256,
            "afterSha256": after_sha256,
            "beforeScopeDigestSha256": before_scope_digest,
            "afterScopeDigestSha256": after_scope_digest,
            **response_values,
        }

        if not should_write:
            payload["warnings"] = []
            return _emit_precommit_response(_render_response(payload))

        response_variants = _render_writer_response_variants(payload)
        writer_dispatched = True
        try:
            warning_codes = _secure_write_registry(root, source, rendered_registry)
        except Exception as error:
            _write_ambiguous(
                "Registry writer outcome is ambiguous after dispatch: {}".format(error)
            )
            return 3
        response = response_variants[tuple(warning_codes)]
        try:
            _write_success(response)
        except Exception as error:
            _write_ambiguous(
                "Registry committed but response delivery is ambiguous: {}".format(error)
            )
            return 3
        return 0
    except UnicodeDecodeError as error:
        _write_error("Registry is not valid UTF-8: {}".format(error))
    except json.JSONDecodeError as error:
        _write_error("Registry JSON is invalid: {}".format(error))
    except RegistryError as error:
        _write_error(str(error))
    except OSError as error:
        _write_error("Registry operation failed: {}".format(error))
    except Exception as error:
        if writer_dispatched:
            _write_ambiguous(
                "Registry outcome is ambiguous after writer dispatch: {}".format(error)
            )
            return 3
        _write_error("Registry operation failed: {}".format(error))
    return 1


def _validate_owner(owner: str) -> None:
    if not 1 <= len(owner) <= 39 or not _OWNER_PATTERN.fullmatch(owner):
        raise RegistryError(
            "GitHub owner must be 1-39 ASCII alphanumeric or hyphen characters."
        )
    if not owner[0].isalnum() or not owner[-1].isalnum() or "--" in owner:
        raise RegistryError(
            "GitHub owner must start and end with an alphanumeric character "
            "and contain no consecutive hyphens."
        )


def _validate_repository_name(repository: str) -> None:
    if (
        not 1 <= len(repository) <= 100
        or not _REPOSITORY_PATTERN.fullmatch(repository)
        or set(repository) == {"."}
    ):
        raise RegistryError(
            "GitHub repository must be 1-100 ASCII letters, digits, dots, "
            "underscores, or hyphens and cannot consist only of dots."
        )


def _slugify(value: str) -> str:
    return _NON_ALPHANUMERIC_PATTERN.sub("-", value.lower()).strip("-")


def _shorten_id(candidate: str, normalized_url: str) -> str:
    if len(candidate) <= MAX_ID_LENGTH:
        return candidate
    digest = hashlib.sha256(
        normalized_url.casefold().encode("utf-8")
    ).hexdigest()[:8]
    return candidate[: MAX_ID_LENGTH - 9] + "-" + digest


def _validate_date(value: Any, label: str) -> None:
    if type(value) is not str or not _DATE_PATTERN.fullmatch(value):
        raise RegistryError("{} must use YYYY-MM-DD format.".format(label))
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise RegistryError("{} must be a valid YYYY-MM-DD date.".format(label)) from error
    if parsed > date.today():
        raise RegistryError("{} must not be in the future.".format(label))


def _validate_entry(entry: Any, index: int) -> None:
    if not isinstance(entry, dict):
        raise RegistryError("Repository at index {} must be a JSON object.".format(index))
    required = (
        "id",
        "url",
        "releasesUrl",
        "shortName",
        "lastReviewedRelease",
    )
    for field in required:
        if field not in entry:
            raise RegistryError(
                "Repository at index {} is missing required field {!r}.".format(
                    index,
                    field,
                )
            )
    repo_id = entry["id"]
    if type(repo_id) is not str or not _ID_PATTERN.fullmatch(repo_id):
        raise RegistryError(
            "Repository id at index {} must be 1-50 alphanumeric or hyphen "
            "characters and start with an alphanumeric character.".format(index)
        )
    url = entry["url"]
    if type(url) is not str:
        raise RegistryError("Repository url at index {} must be a string.".format(index))
    normalized_url = normalize_github_url(url)
    if normalized_url != url:
        raise RegistryError(
            "Repository url {!r} at index {} is not canonical.".format(url, index)
        )
    releases_url = entry["releasesUrl"]
    if type(releases_url) is not str:
        raise RegistryError(
            "Repository releasesUrl at index {} must be a string.".format(index)
        )
    if releases_url != url + "/releases":
        raise RegistryError(
            "Repository releasesUrl at index {} must match its canonical URL "
            "and end with /releases.".format(index)
        )
    short_name = entry["shortName"]
    if type(short_name) is not str or not _SHORT_NAME_PATTERN.fullmatch(short_name):
        raise RegistryError(
            "Repository shortName at index {} must be 1-10 ASCII alphanumeric "
            "characters.".format(index)
        )
    release = entry["lastReviewedRelease"]
    if release is not None:
        _validate_release(
            release,
            "Repository lastReviewedRelease at index {}".format(index),
        )
    review_date_present = "lastReviewDate" in entry
    review_date = entry.get("lastReviewDate")
    if review_date_present and review_date is not None:
        _validate_date(review_date, "lastReviewDate for repository {!r}".format(repo_id))
    if release is None and review_date_present and review_date is not None:
        raise RegistryError(
            "Repository {!r} cannot have lastReviewDate without a reviewed release.".format(
                repo_id
            )
        )
    if release is not None and (not review_date_present or review_date is None):
        raise RegistryError(
            "Repository {!r} with a reviewed release requires lastReviewDate.".format(
                repo_id
            )
        )


def _reject_duplicate_keys(pairs: List[Tuple[str, Any]]) -> JsonObject:
    result: JsonObject = {}
    for key, value in pairs:
        if key in result:
            raise RegistryError("Duplicate JSON key {!r}.".format(key))
        result[key] = value
    return result


def _reject_nonfinite_constant(value: str) -> Any:
    raise RegistryError("Non-finite JSON constant {} is not permitted.".format(value))


def _validate_json_tree(value: Any) -> None:
    stack = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        if depth > MAX_JSON_DEPTH:
            raise RegistryError(
                "Registry JSON nesting exceeds the supported depth of {}.".format(
                    MAX_JSON_DEPTH
                )
            )
        if isinstance(current, dict):
            for key, child in current.items():
                if not isinstance(key, str):
                    raise RegistryError("Registry JSON object keys must be strings.")
                stack.append((child, depth + 1))
        elif isinstance(current, list):
            stack.extend((child, depth + 1) for child in current)
        elif isinstance(current, Decimal):
            if not current.is_finite():
                raise RegistryError("Registry JSON numbers must be finite.")
        elif current is None or isinstance(current, (bool, int, str)):
            continue
        elif isinstance(current, float):
            raise RegistryError(
                "Registry JSON floating-point values must be parsed exactly."
            )
        else:
            raise RegistryError(
                "Registry contains unsupported JSON value type {}.".format(
                    type(current).__name__
                )
            )


def _serialize_json(value: Any, *, indent: Optional[int]) -> str:
    _validate_json_tree(value)
    return _encode_json_value(value, indent=indent, level=0)


def _encode_json_value(value: Any, *, indent: Optional[int], level: int) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise RegistryError("Registry JSON numbers must be finite.")
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        if not value:
            return "[]"
        if indent is None:
            return "[{}]".format(
                ",".join(
                    _encode_json_value(item, indent=None, level=level + 1)
                    for item in value
                )
            )
        prefix = " " * (indent * (level + 1))
        closing = " " * (indent * level)
        items = [
            prefix + _encode_json_value(item, indent=indent, level=level + 1)
            for item in value
        ]
        return "[\n{}\n{}]".format(",\n".join(items), closing)
    if isinstance(value, dict):
        if not value:
            return "{}"
        if indent is None:
            return "{{{}}}".format(
                ",".join(
                    "{}:{}".format(
                        json.dumps(key, ensure_ascii=False),
                        _encode_json_value(item, indent=None, level=level + 1),
                    )
                    for key, item in value.items()
                )
            )
        prefix = " " * (indent * (level + 1))
        closing = " " * (indent * level)
        items = [
            "{}{}: {}".format(
                prefix,
                json.dumps(key, ensure_ascii=False),
                _encode_json_value(item, indent=indent, level=level + 1),
            )
            for key, item in value.items()
        ]
        return "{{\n{}\n{}}}".format(",\n".join(items), closing)
    raise RegistryError(
        "Registry contains unsupported JSON value type {}.".format(
            type(value).__name__
        )
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and update the Compound GPID repository registry."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Project root containing .cg-docs (default: current directory).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    state_parser = subparsers.add_parser(
        "state",
        help="Validate and project registry state without writing.",
    )
    state_parser.add_argument("--id", dest="repo_id")
    state_parser.add_argument("--expected-url")

    add_parser = subparsers.add_parser("add", help="Add one GitHub repository.")
    add_parser.add_argument("--url", required=True, help="Public GitHub repository URL.")
    _add_plan_apply_arguments(add_parser)

    remove_parser = subparsers.add_parser(
        "remove",
        help="Remove one exactly confirmed registry entry.",
    )
    remove_parser.add_argument("--id", dest="repo_id", required=True)
    remove_parser.add_argument("--confirm-id")
    remove_parser.add_argument("--expected-url")
    _add_plan_apply_arguments(remove_parser)

    review_repo_parser = subparsers.add_parser(
        "review-repo",
        help="Update one repository review state.",
    )
    review_repo_parser.add_argument("--id", dest="repo_id", required=True)
    review_repo_parser.add_argument("--expected-url", required=True)
    release_group = review_repo_parser.add_mutually_exclusive_group(required=True)
    release_group.add_argument("--release")
    release_group.add_argument(
        "--release-null",
        dest="release",
        action="store_const",
        const=None,
    )
    review_repo_parser.set_defaults(review_date=_ABSENT)
    date_group = review_repo_parser.add_mutually_exclusive_group()
    date_group.add_argument("--review-date")
    date_group.add_argument(
        "--review-date-null",
        dest="review_date",
        action="store_const",
        const=None,
    )
    expected_release_group = review_repo_parser.add_mutually_exclusive_group(
        required=True
    )
    expected_release_group.add_argument("--expected-last-reviewed-release")
    expected_release_group.add_argument(
        "--expected-last-reviewed-release-null",
        dest="expected_last_reviewed_release",
        action="store_const",
        const=None,
    )
    review_repo_parser.set_defaults(expected_last_review_date=_ABSENT)
    expected_date_group = review_repo_parser.add_mutually_exclusive_group(required=True)
    expected_date_group.add_argument("--expected-last-review-date")
    expected_date_group.add_argument(
        "--expected-last-review-date-null",
        dest="expected_last_review_date",
        action="store_const",
        const=None,
    )
    expected_date_group.add_argument(
        "--expected-last-review-date-absent",
        dest="expected_last_review_date",
        action="store_const",
        const=_ABSENT,
    )
    _add_expected_chain_argument(review_repo_parser)
    _add_plan_apply_arguments(review_repo_parser)

    review_full_parser = subparsers.add_parser(
        "review-full",
        help="Finalize one complete or partial full-review run.",
    )
    review_full_parser.add_argument(
        "--outcome",
        choices=("complete", "partial"),
        required=True,
    )
    review_full_parser.add_argument("--review-date", required=True)
    review_full_parser.add_argument(
        "--reviewed-id",
        dest="reviewed_ids",
        action="append",
        default=[],
    )
    review_full_parser.add_argument(
        "--failed-id",
        dest="failed_ids",
        action="append",
        default=[],
    )
    _add_expected_chain_argument(review_full_parser)
    review_full_parser.add_argument(
        "--expected-scope-digest-sha256",
        type=_parse_sha256,
        help="Exact scope digest from the last accepted chain state.",
    )
    _add_plan_apply_arguments(review_full_parser)
    return parser


def _add_plan_apply_arguments(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--check-only",
        action="store_true",
        help="Validate and render the deterministic plan without writing.",
    )
    group.add_argument(
        "--expected-sha256",
        type=_parse_sha256,
        help="Exact beforeSha256 from the accepted check-only plan.",
    )


def _add_expected_chain_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--expected-chain-sha256",
        type=_parse_sha256,
        help="Exact source SHA-256 from the last accepted chain state.",
    )


def _validate_cli_arguments(
    parser: argparse.ArgumentParser,
    arguments: argparse.Namespace,
) -> None:
    if arguments.command == "state":
        if (arguments.repo_id is None) != (arguments.expected_url is None):
            parser.error("state requires --id and --expected-url together")
        return
    if arguments.command == "remove":
        apply_values = (arguments.confirm_id, arguments.expected_url)
        if arguments.check_only and any(value is not None for value in apply_values):
            parser.error(
                "remove --check-only does not accept --confirm-id or --expected-url"
            )
        if not arguments.check_only and any(value is None for value in apply_values):
            parser.error(
                "remove apply requires --confirm-id and --expected-url"
            )
        return
    if arguments.command in {"review-repo", "review-full"}:
        if arguments.check_only and arguments.expected_chain_sha256 is None:
            parser.error(
                "{} --check-only requires --expected-chain-sha256".format(
                    arguments.command
                )
            )
        if not arguments.check_only and arguments.expected_chain_sha256 is not None:
            parser.error(
                "{} apply does not accept --expected-chain-sha256".format(
                    arguments.command
                )
            )
    if arguments.command == "review-full":
        if arguments.check_only and arguments.expected_scope_digest_sha256 is None:
            parser.error(
                "review-full --check-only requires --expected-scope-digest-sha256"
            )
        if (
            not arguments.check_only
            and arguments.expected_scope_digest_sha256 is not None
        ):
            parser.error(
                "review-full apply does not accept --expected-scope-digest-sha256"
            )


def _parse_sha256(value: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{64}", value, re.ASCII):
        raise argparse.ArgumentTypeError(
            "expected SHA-256 must be exactly 64 lowercase hexadecimal characters"
        )
    return value


def _render_response(payload: Mapping[str, Any]) -> str:
    line = _serialize_json(dict(payload), indent=None) + "\n"
    try:
        encoded = line.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise RegistryError("Response is not valid UTF-8: {}".format(error)) from error
    if len(encoded) > MAX_RESPONSE_BYTES:
        raise RegistryError(
            "Response size exceeds the {} byte limit.".format(MAX_RESPONSE_BYTES)
        )
    return line


def _render_writer_response_variants(
    payload: Mapping[str, Any],
) -> Dict[Tuple[str, ...], str]:
    variants: Dict[Tuple[str, ...], str] = {}
    for mask in range(1 << len(WARNING_CODES)):
        codes = tuple(
            code
            for index, code in enumerate(WARNING_CODES)
            if mask & (1 << index)
        )
        variant = dict(payload)
        variant["warnings"] = list(codes)
        variants[codes] = _render_response(variant)
    return variants


def _state_payload(
    data: JsonObject,
    source_sha256: str,
    scope_digest_sha256: str,
    repo_id: Optional[str],
    expected_url: Optional[str],
) -> JsonObject:
    repositories = [_repo_projection(entry) for entry in data["repos"]]
    selection = None
    if repo_id is not None and expected_url is not None:
        matching = next(
            (entry for entry in data["repos"] if entry["id"] == repo_id),
            None,
        )
        selection = {
            "id": repo_id,
            "expectedUrl": expected_url,
            "found": matching is not None,
            "url": None if matching is None else matching["url"],
            "urlMatches": None if matching is None else matching["url"] == expected_url,
        }
        if matching is not None:
            selection["lastReviewedRelease"] = matching["lastReviewedRelease"]
            selection["lastReviewDate"] = _presence_projection(
                matching,
                "lastReviewDate",
            )
    return {
        "action": "state",
        "changed": False,
        "beforeSha256": source_sha256,
        "afterSha256": source_sha256,
        "beforeScopeDigestSha256": scope_digest_sha256,
        "afterScopeDigestSha256": scope_digest_sha256,
        "repositories": repositories,
        "rootReview": _root_review_projection(data),
        "selection": selection,
        "warnings": [],
    }


def _repo_projection(entry: Mapping[str, Any]) -> JsonObject:
    return {
        "id": entry["id"],
        "url": entry["url"],
        "lastReviewedRelease": entry["lastReviewedRelease"],
        "lastReviewDate": _presence_projection(entry, "lastReviewDate"),
    }


def _root_review_projection(data: Mapping[str, Any]) -> JsonObject:
    return {
        "lastFullReview": _presence_projection(data, "lastFullReview"),
        "lastFullReviewNote": _presence_projection(data, "lastFullReviewNote"),
    }


def _presence_projection(data: Mapping[str, Any], field: str) -> JsonObject:
    return {
        "present": field in data,
        "value": data.get(field),
    }


def _scope_digest(data: Mapping[str, Any]) -> str:
    projection = {
        "repositories": [_repo_projection(entry) for entry in data["repos"]],
        "rootReview": _root_review_projection(data),
    }
    return _sha256(
        _serialize_json(projection, indent=None).encode("utf-8", errors="strict")
    )


def _find_repository(
    data: Mapping[str, Any],
    repo_id: str,
) -> Tuple[int, Mapping[str, Any]]:
    matching_index = next(
        (
            index
            for index, entry in enumerate(data["repos"])
            if entry["id"] == repo_id
        ),
        None,
    )
    if matching_index is None:
        available = ", ".join(entry["id"] for entry in data["repos"]) or "none"
        raise RegistryError(
            "Repository id {!r} was not found; available ids: {}.".format(
                repo_id,
                available,
            )
        )
    return matching_index, data["repos"][matching_index]


def _validate_scope_ids(values: Sequence[str], label: str) -> List[str]:
    result = list(values)
    for value in result:
        if type(value) is not str or not _ID_PATTERN.fullmatch(value):
            raise RegistryError(
                "{} repository IDs must satisfy the exact ID format.".format(label)
            )
    if len(result) != len(set(result)):
        raise RegistryError("{} repository IDs must not contain duplicates.".format(label))
    return result


def _validate_release(value: Any, label: str) -> None:
    if type(value) is not str or not _RELEASE_PATTERN.fullmatch(value):
        raise RegistryError(
            "{} must be 1-{} ASCII characters, start with an alphanumeric "
            "character, and contain only letters, digits, dot, underscore, "
            "plus, slash, or hyphen.".format(label, MAX_RELEASE_LENGTH)
        )


def _require_expected_review_state(
    data: Mapping[str, Any],
    repo_id: str,
    expected_url: str,
    expected_release: Optional[str],
    expected_review_date: Any,
) -> None:
    _, entry = _find_repository(data, repo_id)
    if entry["url"] != expected_url:
        raise RegistryError(
            "Repository URL changed for id {!r}; expected {!r}, found {!r}.".format(
                repo_id,
                expected_url,
                entry["url"],
            )
        )
    if expected_release is not None:
        _validate_release(expected_release, "Expected last reviewed release")
    if entry["lastReviewedRelease"] != expected_release:
        raise RegistryError(
            "Prior lastReviewedRelease changed for repository {!r}.".format(repo_id)
        )

    actual_date_present = "lastReviewDate" in entry
    if expected_review_date is _ABSENT:
        if actual_date_present:
            raise RegistryError(
                "Prior lastReviewDate presence changed for repository {!r}.".format(
                    repo_id
                )
            )
        return
    if expected_review_date is not None:
        _validate_date(expected_review_date, "Expected last review date")
    if not actual_date_present or entry["lastReviewDate"] != expected_review_date:
        raise RegistryError(
            "Prior lastReviewDate presence/value changed for repository {!r}.".format(
                repo_id
            )
        )


def _require_expected_scope_digest(expected: str, actual: str) -> None:
    if expected != actual:
        raise RegistryError(
            "Registry review scope is stale; expected digest {}, found {}.".format(
                expected,
                actual,
            )
        )


def _require_expected_sha256(expected: str, actual: str) -> None:
    if expected != actual:
        raise RegistryError(
            "Registry state is stale; expected SHA-256 {}, found {}.".format(
                expected,
                actual,
            )
        )


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _secure_write_registry(root: Path, source: bytes, rendered: bytes) -> List[str]:
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", RuntimeWarning)
        secure_fs.secure_write_bytes(
            root,
            REGISTRY_RELATIVE_PATH,
            rendered,
            before_replace=_before_secure_replace,
            expected_state=secure_fs.ExpectedFileState.from_bytes(source),
        )
    observed = {_warning_code(str(item.message)) for item in captured}
    return [code for code in WARNING_CODES if code in observed]


def _warning_code(message: str) -> str:
    lowered = message.casefold()
    if "recovery cleanup durability" in lowered:
        return "secure-fs-cleanup-durability-unconfirmed"
    if "recovery preserved" in lowered:
        return "secure-fs-recovery-preserved"
    if "temporary publication file" in lowered:
        return "secure-fs-temporary-cleanup-failed"
    return "secure-fs-runtime-warning"


def _emit_precommit_response(line: str) -> int:
    try:
        _write_success(line)
    except Exception as error:
        _write_error("Response delivery failed before writer dispatch: {}".format(error))
        return 1
    return 0


def _write_success(line: str) -> None:
    sys.stdout.write(line)
    sys.stdout.flush()


def _write_error(message: str) -> None:
    single_line = " ".join(message.splitlines()).strip()
    try:
        sys.stderr.write("Error: {}\n".format(single_line))
        sys.stderr.flush()
    except Exception:
        pass


def _write_ambiguous(message: str) -> None:
    single_line = " ".join(message.splitlines()).strip()
    try:
        sys.stderr.write("Ambiguous: {}\n".format(single_line))
        sys.stderr.flush()
    except Exception:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
