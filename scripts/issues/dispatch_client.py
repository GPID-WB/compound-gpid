"""Live mutation client for the Stage 3 Copilot dispatcher.

``GhDispatchMutator`` performs the three GitHub mutations the dispatcher needs,
each with its own least-privilege credential:

- :meth:`assign` and :meth:`comment` run with the Copilot-assignment credential
  (``COPILOT_ASSIGN_TOKEN``).
- :meth:`set_project_status` runs with the Project-synchronization credential
  (``PROJECT_SYNC_TOKEN``).

The two tokens are never combined and never appear in a single command. Issue
content is never interpolated into a shell string; all request bodies are
written to temp files and passed through ``gh`` ``--input`` / ``--body-file``
flags (argv-safe and path-safe). Temp-file I/O failures surface as
``ApiError``, not a raw traceback, so the documented exit-code contract holds.

Project-v2 GraphQL queries and verification live in :mod:`issues.dispatch_project`;
process/temp-file helpers live in :mod:`issues.dispatch_util`; this module keeps
only the thin mutation surface the orchestrator depends on.
"""
from __future__ import annotations

import json
from collections.abc import Callable, Mapping
import os
import subprocess
from typing import Optional

from .client_utils import expect_mapping
from .contract import ApiError, ConfigError
from .dispatch_contract import COPILOT_ASSIGN_LOGIN, IN_PROGRESS_STATUS
from .dispatch_project import (
    PROJECT_TOKEN_ENV,
    item_query_args,
    mutation_args,
    option_id_for,
    resolve_item_id,
    supported_status,
    verify_mutation_success,
)
from .dispatch_util import _default_mutation_runner, _unlink_best_effort, _write_temp_file
from .gh_process import _classify_gh_error

ASSIGN_TOKEN_ENV = "COPILOT_ASSIGN_TOKEN"


class GhDispatchMutator:
    """Live mutation client with separated assignment and Project credentials.

    Args:
        runner: Optional ``gh`` runner callable ``(args, token) -> CompletedProcess``
            for deterministic tests.
        owner: Optional repository owner override (resolved from ``gh`` when absent).
        name: Optional repository name override (resolved from ``gh`` when absent).
    """

    def __init__(
        self,
        runner: Optional[Callable[[list, str], subprocess.CompletedProcess]] = None,
        owner: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        self._runner = runner or _default_mutation_runner
        self._owner = owner
        self._name = name
        self._base_branch = "main"

    def _token(self, env_name: str) -> str:
        """Return a required credential value or fail closed when missing.

        Args:
            env_name: Name of the environment variable holding the credential.

        Returns:
            The token value.

        Raises:
            ConfigError: When the variable is unset or empty (fail closed).
        """
        value = os.environ.get(env_name, "").strip()
        if not value:
            raise ConfigError(
                f"required credential {env_name} is not configured"
            )
        return value

    def _run(self, args: list, token_env: str) -> subprocess.CompletedProcess:
        """Run one mutation command with the credential for its token."""
        token = self._token(token_env)
        completed = self._runner(args, token)
        if completed.returncode != 0:
            _classify_gh_error(completed, args)
        return completed

    def _repo(self) -> tuple[str, str]:
        """Resolve the current repository owner and name."""
        if self._owner and self._name:
            return self._owner, self._name
        out = self._run(
            ["repo", "view", "--json", "nameWithOwner,defaultBranchRef"],
            ASSIGN_TOKEN_ENV,
        )
        try:
            data = json.loads(out.stdout)
        except (json.JSONDecodeError, RecursionError) as error:
            raise ApiError(f"malformed repo response from gh: {error}") from error
        data = expect_mapping(data, "repo response", ApiError)
        name_with_owner = data.get("nameWithOwner", "")
        if not isinstance(name_with_owner, str) or "/" not in name_with_owner:
            raise ConfigError(
                f"could not determine repository from gh: {name_with_owner!r}"
            )
        owner, name = name_with_owner.split("/", 1)
        if not owner or not name:
            raise ConfigError(
                f"could not determine repository from gh: {name_with_owner!r}"
            )
        branch_ref = data.get("defaultBranchRef")
        if isinstance(branch_ref, Mapping):
            self._base_branch = branch_ref.get("name") or "main"
        self._owner, self._name = owner, name
        return owner, name

    def assign(self, issue_number: int, login: str) -> None:
        """Assign exactly the Copilot bot to the issue.

        Args:
            issue_number: Issue number to assign.
            login: Exact assignee login. Anything other than
                ``copilot-swe-agent[bot]`` is rejected at this boundary.

        Raises:
            ApiError: On a failed, malformed, or no-op assign response.
            ConfigError: When the assignment credential is not configured, the
                repository cannot be resolved, or ``login`` is not the canonical
                Copilot bot login.
        """
        if login != COPILOT_ASSIGN_LOGIN:
            raise ConfigError(
                f"refusing to assign {login!r}; only {COPILOT_ASSIGN_LOGIN!r} "
                f"may be assigned by the dispatcher"
            )
        owner, name = self._repo()
        body = {
            "assignees": [login],
            "agent_assignment": {
                "target_repo": f"{owner}/{name}",
                "base_branch": self._base_branch,
            },
        }
        tmp = _write_temp_file(json.dumps(body), ".json")
        try:
            out = self._run(
                [
                    "api", "-X", "POST",
                    f"repos/{owner}/{name}/issues/{issue_number}/assignees",
                    "--input", str(tmp),
                ],
                ASSIGN_TOKEN_ENV,
            )
        finally:
            _unlink_best_effort(tmp)
        # Verify the mutation landed: the response is the updated issue, whose
        # assignees must now include the requested login. A silent no-op (or a
        # wrong-shape response) must not be reported as a successful assignment.
        try:
            data = json.loads(out.stdout)
        except (json.JSONDecodeError, RecursionError) as error:
            raise ApiError(f"malformed assign response from gh: {error}") from error
        data = expect_mapping(data, "assign response", ApiError)
        assignees = data.get("assignees")
        if not isinstance(assignees, list) or not any(
            isinstance(item, Mapping) and item.get("login") == login
            for item in assignees
        ):
            raise ApiError(
                f"assignment did not persist: assignee {login!r} not returned "
                f"in the updated issue"
            )

    def set_project_status(self, issue_number: int, status: str) -> None:
        """Set the issue Project Status field using the Project credential.

        Args:
            issue_number: Issue number whose Project item status is updated.
            status: Target status (only ``In progress`` is supported).

        Raises:
            ApiError: On a failed, malformed, or rejected GraphQL response.
            ConfigError: When the Project credential is missing, the status is
                unsupported, or the issue is not on the target project.
        """
        if not supported_status(status):
            raise ConfigError(
                f"unsupported Project Status {status!r}; dispatcher only sets "
                f"{IN_PROGRESS_STATUS!r}"
            )
        item_id = self._resolve_item_id(issue_number)
        option_id = option_id_for(status)
        query_out = self._run(
            mutation_args(item_id, option_id), PROJECT_TOKEN_ENV
        )
        verify_mutation_success(query_out.stdout)

    def _resolve_item_id(self, issue_number: int) -> str:
        """Resolve the issue's Project item node id via the project node.

        Args:
            issue_number: Issue number to look up.

        Returns:
            The Project item node id.

        Raises:
            ApiError: On a malformed or failed response, or a truncated scan.
            ConfigError: When the issue is not on the target project.
        """
        out = self._run(item_query_args(issue_number), PROJECT_TOKEN_ENV)
        return resolve_item_id(out.stdout, issue_number)

    def comment(self, issue_number: int, body: str) -> None:
        """Post an audit comment to the issue using the Copilot credential.

        Args:
            issue_number: Issue number to comment on.
            body: Comment body text.

        Raises:
            ApiError: On a failed response or temp-file write failure.
            ConfigError: When the assignment credential is not configured.
        """
        tmp = _write_temp_file(body, ".md")
        try:
            self._run(
                ["issue", "comment", str(issue_number), "--body-file", str(tmp)],
                ASSIGN_TOKEN_ENV,
            )
        finally:
            _unlink_best_effort(tmp)


class DispatchMutator:
    """Protocol for the mutation surface used by :func:`run_dispatch`.

    Implemented by :class:`GhDispatchMutator` in production and by fakes in
    deterministic tests.

    Note:
        The concrete implementation documents Args/Raises per method; the
        protocol mirrors the same signatures.
    """

    def assign(self, issue_number: int, login: str) -> None:
        """Assign ``login`` (must be ``copilot-swe-agent[bot]``) to the issue."""

    def set_project_status(self, issue_number: int, status: str) -> None:
        """Set the issue Project Status field (``In progress`` only)."""

    def comment(self, issue_number: int, body: str) -> None:
        """Post an audit comment to the issue."""
