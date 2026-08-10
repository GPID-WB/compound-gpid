"""Subprocess execution and error classification for the GitHub CLI."""
from __future__ import annotations

import re
import subprocess
from typing import NoReturn

from .contract import ApiError, ConfigError


GH_TIMEOUT_SECONDS = 60


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
    if status == "404" or "not found" in lower or "could not find" in lower or "does not exist" in lower:
        raise ConfigError(f"GitHub resource not found: {stderr}")
    if status in ("401", "403") or "auth" in lower or "scope" in lower or "permission" in lower:
        raise ConfigError(f"GitHub authorization/scope error: {stderr}")
    if "graphql" in args:
        raise ConfigError(f"GitHub GraphQL query/schema error: {stderr}")
    if returncode == 1 and not stderr:
        raise ConfigError("gh command failed with no message (not authenticated?)")
    raise ApiError(f"gh command failed (rc={returncode}): {stderr}")


def _classify_graphql_errors(errors: list | str | None) -> None:
    """Classify GraphQL error payloads into ApiError or ConfigError.

    Rate-limit, timeout, transient, and server-side errors are classified as
    ``ApiError`` (exit code 4).  Configuration, schema, authentication, scope,
    and permission errors are classified as ``ConfigError`` (exit code 3).

    Args:
        errors: The ``errors`` array from a GraphQL response.

    Raises:
        ApiError: For rate-limit, timeout, transient, or server-side errors.
        ConfigError: For client configuration, schema, auth, or permission errors.
    """
    if errors is None:
        return
    text = str(errors).lower()
    if any(kw in text for kw in ("rate limit", "secondary rate limit", "timeout", "timed out")):
        raise ApiError(f"GitHub GraphQL transient error: {errors}")
    if any(kw in text for kw in ("internal error", "server error", "try again")):
        raise ApiError(f"GitHub GraphQL server error: {errors}")
    raise ConfigError(f"GitHub GraphQL error: {errors}")
