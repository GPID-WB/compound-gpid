"""Subprocess execution and error classification for the GitHub CLI."""
from __future__ import annotations

import re
import subprocess
from typing import NoReturn

from .contract import ApiError, ConfigError


GH_TIMEOUT_SECONDS = 60

# Word-boundary patterns for GitHub CLI stderr classification.
# ``\b`` prevents ``auth`` from matching inside ``author``.
_AUTH_PATTERN = re.compile(
    r"\b(?:auth(?:orized?|enticated?|orization|entication)?|oauth)\b",
    re.IGNORECASE,
)
_SCOPE_PATTERN = re.compile(r"\bscope\b", re.IGNORECASE)
_PERMISSION_PATTERN = re.compile(r"\bpermission\b", re.IGNORECASE)
_NOT_FOUND_PATTERN = re.compile(
    r"(?:\bnot\s+found\b|\bcould\s+not\s+find\b|\bdoes\s+not\s+exist\b)",
    re.IGNORECASE,
)


def _default_run_gh(args: list[str]) -> subprocess.CompletedProcess:
    """Run ``gh`` with argv-safe subprocess arguments and a fixed timeout.

    Args:
        args: Argument list passed to ``gh`` after the program name.

    Returns:
        The completed process result.

    Raises:
        ConfigError: When ``gh`` is not installed or the OS cannot execute it.
        ApiError: On timeout, undecodable output, or other runtime failures.
    """
    try:
        return subprocess.run(
            ["gh", *args], capture_output=True, text=True,
            encoding="utf-8", timeout=GH_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as error:
        raise ConfigError(
            "gh CLI not found; install GitHub CLI (https://cli.github.com) and run "
            "`gh auth login` before using --issue"
        ) from error
    except subprocess.TimeoutExpired as error:
        raise ApiError(f"gh command timed out after {GH_TIMEOUT_SECONDS}s") from error
    except UnicodeError as error:
        raise ApiError(f"gh command returned undecodable output: {error}") from error
    except OSError as error:
        raise ConfigError(f"could not execute gh CLI: {error}") from error


def _classify_gh_error(completed: subprocess.CompletedProcess, args: list[str]) -> NoReturn:
    """Map a failed ``gh`` process to its documented config/API exception.

    This function always raises; it never returns normally.

    Args:
        completed: The failed subprocess result.
        args: The original argument list passed to ``gh``.

    Raises:
        ApiError: For rate limits, timeouts, 5xx errors, and unknown failures.
        ConfigError: For auth/scope issues, 404s, GraphQL schema errors, and
            empty stderr on exit code 1.
    """
    stderr = (completed.stderr or "").strip()
    returncode = completed.returncode
    lower = stderr.lower()
    status_match = re.search(r"HTTP (\d{3})", stderr)
    status = status_match.group(1) if status_match else None
    if status and 500 <= int(status) < 600:
        raise ApiError(f"gh command failed (HTTP {status}): {stderr}")
    if "rate limit" in lower:
        raise ApiError(f"GitHub rate limited: {stderr}")
    if "timeout" in lower or "timed out" in lower:
        raise ApiError(f"gh command timed out: {stderr}")
    if status == "404" or _NOT_FOUND_PATTERN.search(stderr):
        raise ConfigError(f"GitHub resource not found: {stderr}")
    if status in ("401", "403") or _AUTH_PATTERN.search(stderr) or _SCOPE_PATTERN.search(stderr) or _PERMISSION_PATTERN.search(stderr):
        raise ConfigError(f"GitHub authorization/scope error: {stderr}")
    if "graphql" in args:
        raise ConfigError(f"GitHub GraphQL query/schema error: {stderr}")
    if returncode == 1 and not stderr:
        raise ConfigError("gh command failed with no message (not authenticated?)")
    raise ApiError(f"gh command failed (rc={returncode}): {stderr}")


def _classify_graphql_errors(errors: list | str | None) -> None:
    """Classify GraphQL error payloads into ApiError or ConfigError.

    ``None`` and empty lists are treated as successful responses (no error).
    Non-list, non-string, empty-string, and mapping payloads are treated as
    malformed transient failures (``ApiError``).  Non-empty error lists are
    classified by inspecting their string representation for rate-limit,
    timeout, transient, and server-side keywords.

    Args:
        errors: The ``errors`` field from a GraphQL response.

    Raises:
        ApiError: For rate-limit, timeout, transient, server-side, or
            malformed error payloads.
        ConfigError: For client configuration, schema, auth, or permission
            errors in well-formed error arrays.
    """
    if errors is None or (isinstance(errors, list) and len(errors) == 0):
        return
    if isinstance(errors, str) and errors.strip() == "":
        raise ApiError(
            f"malformed GraphQL errors from gh: empty string"
        )
    if not isinstance(errors, (list, str)):
        raise ApiError(
            f"malformed GraphQL errors from gh: expected list or null, "
            f"got {type(errors).__name__}"
        )
    text = str(errors).lower()
    if any(kw in text for kw in ("rate limit", "secondary rate limit", "timeout", "timed out")):
        raise ApiError(f"GitHub GraphQL transient error: {errors}")
    if any(kw in text for kw in ("internal error", "server error", "try again")):
        raise ApiError(f"GitHub GraphQL server error: {errors}")
    raise ConfigError(f"GitHub GraphQL error: {errors}")
