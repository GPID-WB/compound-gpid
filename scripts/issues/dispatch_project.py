"""Project-v2 GraphQL queries and mutation verification (leaf module).

The dispatcher sets exactly one Project Status value (``In progress``). This
module owns the Project node/field/option identifiers (verified in Stage 0A,
2026-08-06, for the ``CompoundGPID-progress`` project) and the two GraphQL
operations the dispatcher needs: resolving an issue's project item via the
**project node** (so a least-privilege ``PROJECT_SYNC_TOKEN`` never requires
repository/issue read access) and verifying the mutation's success shape.
"""
from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any

from .client_utils import expect_mapping
from .contract import ApiError, ConfigError
from .dispatch_contract import IN_PROGRESS_STATUS
from .gh_client import PROJECT_TITLE
from .gh_process import _classify_graphql_errors

# Verified in Stage 0A (2026-08-06) for the CompoundGPID-progress org project.
# These are the deployed project's node/field/option IDs (not secrets), recorded
# from read-only GraphQL.
_PROJECT_NODE_ID = "PVT_kwDOA9TrWc4BfRSv"
_PROJECT_STATUS_FIELD_ID = "PVTSSF_lADOA9TrWc4BfRSvzhZlWns"
_PROJECT_STATUS_OPTION_IDS = {
    IN_PROGRESS_STATUS: "47fc9ee4",
}

PROJECT_TOKEN_ENV = "PROJECT_SYNC_TOKEN"

_MUTATION_QUERY = """mutation SetProjectStatus($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $projectId
    itemId: $itemId
    fieldId: $fieldId
    value: { singleSelectOptionId: $optionId }
  }) {
    projectV2Item { id }
  }
}"""

_ITEM_QUERY = """query DispatchItem($projectId: ID!, $number: Int!) {
  node(id: $projectId) {
    ... on ProjectV2 {
      items(first: 50) {
        nodes {
          id
          content {
            ... on Issue { number }
          }
        }
        pageInfo {
          hasNextPage
        }
      }
    }
  }
}"""


def mutation_args(item_id: str, option_id: str) -> list:
    """Return the Project Status mutation command arguments after "graphql".

    Args:
        item_id: The issue's Project item node id.
        option_id: The target single-select option id.

    Returns:
        The ``gh api graphql`` argument list (query + typed variables).
    """
    return [
        "api", "graphql",
        "-f", f"query={_MUTATION_QUERY}",
        "-F", f"projectId={_PROJECT_NODE_ID}",
        "-F", f"itemId={item_id}",
        "-F", f"fieldId={_PROJECT_STATUS_FIELD_ID}",
        "-F", f"optionId={option_id}",
    ]


def item_query_args(issue_number: int) -> list:
    """Return the project-item resolution query arguments after "graphql".

    Args:
        issue_number: Issue number to look up.

    Returns:
        The ``gh api graphql`` argument list for the item query.
    """
    return [
        "api", "graphql",
        "-f", f"query={_ITEM_QUERY}",
        "-F", f"projectId={_PROJECT_NODE_ID}",
        "-F", f"number={issue_number}",
    ]


def supported_status(status: str) -> bool:
    """Return whether the dispatcher may set the given status.

    Args:
        status: Target status string.

    Returns:
        True only for ``In progress``.
    """
    return status in _PROJECT_STATUS_OPTION_IDS


def option_id_for(status: str) -> str:
    """Return the option id for a supported status.

    Args:
        status: A status returned by :func:`supported_status`.

    Returns:
        The single-select option id.

    Raises:
        ConfigError: When the status is unsupported.
    """
    if status not in _PROJECT_STATUS_OPTION_IDS:
        raise ConfigError(
            f"unsupported Project Status {status!r}; dispatcher only sets "
            f"one of {sorted(_PROJECT_STATUS_OPTION_IDS)}"
        )
    return _PROJECT_STATUS_OPTION_IDS[status]


def verify_mutation_success(stdout: str) -> None:
    """Require the Project mutation's success shape, or raise ``ApiError``.

    Args:
        stdout: The ``gh api graphql`` stdout for the mutation.

    Raises:
        ApiError: When errors are present, the response is malformed, or the
            success subtree is missing/empty (a no-errors ``null`` must not be
            reported as success).
        ConfigError: On classified GraphQL configuration/schema failures.
    """
    try:
        data = json.loads(stdout)
    except (json.JSONDecodeError, RecursionError) as error:
        raise ApiError(f"malformed graphql response from gh: {error}") from error
    data = expect_mapping(data, "graphql response", ApiError)
    _classify_graphql_errors(data.get("errors"))
    try:
        updated = data["data"]["updateProjectV2ItemFieldValue"]["projectV2Item"]["id"]
    except (KeyError, TypeError) as error:
        raise ApiError(
            "Project Status update accepted by GitHub but success shape "
            "missing; refusing to report success"
        ) from error
    if not isinstance(updated, str) or not updated:
        raise ApiError("Project Status update returned an empty item id")


def parse_mutation_result(stdout: str) -> str:
    """Alias for :func:`verify_mutation_success` returning the item id.

    Provided for call sites that want the returned item node id as proof.

    Args:
        stdout: The ``gh api graphql`` stdout for the mutation.

    Returns:
        The returned project item id.

    Raises:
        ApiError / ConfigError: As documented for :func:`verify_mutation_success`.
    """
    verify_mutation_success(stdout)
    data = json.loads(stdout)
    return data["data"]["updateProjectV2ItemFieldValue"]["projectV2Item"]["id"]


def resolve_item_id(stdout: str, issue_number: int) -> str:
    """Resolve the issue's Project item node id from the item-query response.

    Resolving through the project node means a least-privilege
    ``PROJECT_SYNC_TOKEN`` (project read/write) never requires repository or
    issue read access.

    Args:
        stdout: The ``gh api graphql`` stdout for the item query.
        issue_number: Issue number that must match the item content.

    Returns:
        The Project item node id.

    Raises:
        ApiError: On a malformed or failed response, or a truncated scan.
        ConfigError: When the issue is not on the target project.
    """
    try:
        data = json.loads(stdout)
    except (json.JSONDecodeError, RecursionError) as error:
        raise ApiError(f"malformed graphql response from gh: {error}") from error
    data = expect_mapping(data, "graphql response", ApiError)
    _classify_graphql_errors(data.get("errors"))
    try:
        item_connection = data["data"]["node"]["items"]
    except (KeyError, TypeError) as error:
        raise ApiError(
            "malformed graphql response from gh: missing project items"
        ) from error
    item_connection = expect_mapping(item_connection, "project items", ApiError)
    nodes = item_connection.get("nodes")
    if not isinstance(nodes, list):
        raise ApiError("malformed graphql response from gh: nodes not a list")
    page_info = item_connection.get("pageInfo")
    has_next = (
        isinstance(page_info, Mapping) and page_info.get("hasNextPage") is True
    )
    for node in nodes:
        if isinstance(node, Mapping):
            content = node.get("content")
            if content is not None:
                content = expect_mapping(content, "project item content", ApiError)
            if content and content.get("number") == issue_number:
                item_id = node.get("id")
                if isinstance(item_id, str) and item_id:
                    return item_id
        elif node is not None:
            raise ApiError(
                "malformed graphql response from gh: project item node is "
                "not an object"
            )
    if has_next:
        raise ApiError("project item scan truncated; refusing to resolve item id")
    raise ConfigError(f"issue #{issue_number} is not on the {PROJECT_TITLE} project")
