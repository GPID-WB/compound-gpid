"""Live, read-only GitHub client backed by documented ``gh`` commands."""
from __future__ import annotations

from collections.abc import Callable, Mapping
import json
import subprocess
from typing import Any, Optional

from .client_models import IssueRecord, PRRecord
from .client_utils import expect_mapping, normalize_objects, require_int, require_string
from .contract import ApiError, ConfigError, pr_closes_issue
from .gh_process import _classify_gh_error, _default_run_gh


PROJECT_TITLE = "CompoundGPID-progress"
PR_LIST_LIMIT = 1000


class GhCliClient:
    """Read-only GitHub access through documented ``gh`` CLI commands."""

    def __init__(
        self,
        runner: Optional[Callable[[list[str]], subprocess.CompletedProcess]] = None,
    ) -> None:
        self._runner = runner or _default_run_gh
        self._repo: Optional[tuple[str, str]] = None

    def _gh(self, args: list[str]) -> str:
        """Run one read-only ``gh`` command and classify nonzero exits."""
        completed = self._runner(args)
        if completed.returncode != 0:
            _classify_gh_error(completed, args)
        return completed.stdout

    @staticmethod
    def _parse_json(out: str, label: str) -> Any:
        """Parse command output, mapping JSON syntax failures to ``ApiError``."""
        try:
            return json.loads(out)
        except (json.JSONDecodeError, RecursionError) as error:
            raise ApiError(f"malformed {label} response from gh: {error}") from error

    def get_issue(self, issue_number: int) -> IssueRecord:
        """Fetch and normalize one issue without mutating GitHub."""
        out = self._gh([
            "issue", "view", str(issue_number), "--json",
            "number,title,body,state,assignees,labels",
        ])
        data = expect_mapping(self._parse_json(out, "issue"), "issue", ApiError)
        return IssueRecord(
            number=require_int(data.get("number", issue_number), "issue.number", ApiError),
            title=require_string(data.get("title"), "issue.title", ApiError),
            body=require_string(data.get("body"), "issue.body", ApiError),
            state=require_string(data.get("state", ""), "issue.state", ApiError).upper(),
            assignees=normalize_objects(data.get("assignees", []), "login", "issue.assignees", ApiError),
            labels=normalize_objects(data.get("labels", []), "name", "issue.labels", ApiError),
        )

    def get_open_closing_prs(self, issue_number: int) -> list[PRRecord]:
        """List open PRs once and fail closed if the configured limit is hit."""
        out = self._gh([
            "pr", "list", "--state", "open", "--json",
            "number,title,body,url,headRefName,author",
            "--limit", str(PR_LIST_LIMIT),
        ])
        items = self._parse_json(out, "pr")
        if not isinstance(items, list):
            raise ApiError(
                "malformed pr response from gh: expected list, "
                f"got {type(items).__name__}"
            )
        if len(items) >= PR_LIST_LIMIT:
            raise ApiError(
                f"gh pr list reached configured limit {PR_LIST_LIMIT}; "
                "refusing a potentially truncated closing-PR scan"
            )
        records: list[PRRecord] = []
        for item in items:
            item_map = expect_mapping(item, "pr", ApiError)
            author = item_map.get("author")
            if author is None:
                author_login = ""
            elif isinstance(author, Mapping):
                author_login = require_string(author.get("login"), "pr.author.login", ApiError)
            elif isinstance(author, str):
                author_login = author
            else:
                raise ApiError("malformed pr.author: expected object or string")
            number = require_int(item_map.get("number"), "pr.number", ApiError)
            title = require_string(item_map.get("title"), "pr.title", ApiError)
            body = require_string(item_map.get("body"), "pr.body", ApiError)
            url = require_string(item_map.get("url"), "pr.url", ApiError)
            head_ref = require_string(item_map.get("headRefName"), "pr.headRefName", ApiError)
            if pr_closes_issue(body, issue_number):
                records.append(PRRecord(number, title, body, url, head_ref, author_login))
        return records

    def get_project_status(self, issue_number: int) -> Optional[str]:
        """Read the canonical Project Status, preserving deliberate absence."""
        owner, name = self._repo_owner_name()
        query = _PROJECT_STATUS_QUERY.format(number=issue_number)
        out = self._gh([
            "api", "graphql", "-f", f"query={query}",
            "-F", f"owner={owner}", "-F", f"name={name}",
        ])
        data = expect_mapping(self._parse_json(out, "graphql"), "graphql", ApiError)
        if data.get("errors"):
            raise ConfigError(f"GitHub GraphQL error: {data['errors']}")
        if "data" not in data:
            raise ApiError("malformed graphql response from gh: missing data")
        graphql_data = expect_mapping(data["data"], "graphql.data", ApiError)
        if "repository" not in graphql_data:
            raise ApiError("malformed graphql response from gh: missing repository")
        repository = graphql_data["repository"]
        if repository is None:
            return None
        repository = expect_mapping(repository, "graphql.repository", ApiError)
        if "issue" not in repository:
            raise ApiError("malformed graphql response from gh: missing issue")
        issue = repository["issue"]
        if issue is None:
            return None
        issue = expect_mapping(issue, "graphql.issue", ApiError)
        if "projectItems" not in issue:
            raise ApiError("malformed graphql response from gh: missing projectItems")
        project_items = issue["projectItems"]
        if project_items is None:
            return None
        project_items = expect_mapping(project_items, "graphql.projectItems", ApiError)
        if "nodes" not in project_items:
            raise ApiError("malformed graphql response from gh: missing projectItems.nodes")
        nodes = project_items["nodes"]
        if not isinstance(nodes, list):
            raise ApiError("malformed graphql response from gh: projectItems.nodes is not a list")
        for node in nodes:
            node = expect_mapping(node, "graphql.projectItems.nodes item", ApiError)
            if "project" not in node:
                raise ApiError("malformed graphql response from gh: missing project")
            project = node["project"]
            if project is None:
                continue
            project = expect_mapping(project, "graphql.project", ApiError)
            if "title" not in project:
                raise ApiError("malformed graphql response from gh: missing project.title")
            title = project["title"]
            if title is None:
                continue
            if not isinstance(title, str):
                raise ApiError("malformed graphql response from gh: project.title is not a string")
            if title != PROJECT_TITLE:
                continue
            if "fieldValueByName" not in node:
                raise ApiError("malformed graphql response from gh: missing fieldValueByName")
            field_value = node["fieldValueByName"]
            if field_value is None:
                return None
            field_value = expect_mapping(field_value, "graphql.fieldValueByName", ApiError)
            if "name" not in field_value or field_value["name"] is None:
                return None
            if not isinstance(field_value["name"], str):
                raise ApiError("malformed graphql response from gh: status name is not a string")
            return field_value["name"]
        return None

    def _repo_owner_name(self) -> tuple[str, str]:
        """Resolve and cache the current repository owner and name."""
        if self._repo is not None:
            return self._repo
        out = self._gh(["repo", "view", "--json", "nameWithOwner"])
        data = expect_mapping(self._parse_json(out, "repo"), "repo", ApiError)
        name_with_owner = data.get("nameWithOwner", "")
        if not isinstance(name_with_owner, str):
            raise ApiError("malformed repo response from gh: nameWithOwner is not a string")
        if "/" not in name_with_owner:
            raise ConfigError(f"could not determine repository from gh: {name_with_owner!r}")
        owner, name = name_with_owner.split("/", 1)
        if not owner or not name:
            raise ConfigError(f"could not determine repository from gh: {name_with_owner!r}")
        self._repo = (owner, name)
        return self._repo


_PROJECT_STATUS_QUERY = """query ReadinessStatus($owner: String!, $name: String!) {{
  repository(owner: $owner, name: $name) {{
    issue(number: {number}) {{
      projectItems(first: 20) {{
        nodes {{
          project {{ title }}
          fieldValueByName(name: "Status") {{
            ... on ProjectV2ItemFieldSingleSelectValue {{ name }}
          }}
        }}
      }}
    }}
  }}
}}"""
