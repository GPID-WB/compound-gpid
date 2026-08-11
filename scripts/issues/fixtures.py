"""Offline readiness client with strict ``gh``-compatible fixture parsing."""
from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any, Optional

from .client_models import IssueRecord, PRRecord
from .client_utils import expect_mapping, normalize_objects, require_int, require_string
from .contract import ConfigError


class FixtureClient:
    """Offline client whose JSON shape mirrors the ``gh`` wire format.

    Args:
        fixture_path: Path to a JSON fixture file containing issue data and
            optionally ``bodyFile``, ``openClosingPRs``, and
            ``projectStatus`` fields.

    Raises:
        ConfigError: When the fixture cannot be loaded, contains malformed
            data, or ``bodyFile`` escapes the fixture directory.
    """

    def __init__(self, fixture_path: str) -> None:
        try:
            path = Path(fixture_path)
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError, RecursionError) as error:
            raise ConfigError(f"cannot load fixture {fixture_path}: {error}") from error
        data = expect_mapping(data, "fixture root", ConfigError)
        issue = data.get("issue")
        if not isinstance(issue, Mapping):
            raise ConfigError("fixture issue must be an object")
        body = _fixture_string(issue.get("body"), "issue.body")
        body_file = data.get("bodyFile")
        if body_file is not None:
            body_file = _fixture_string(body_file, "bodyFile", allow_none=False)
            base = path.parent.resolve()
            try:
                target = (base / body_file).resolve()
            except (ValueError, OSError) as error:
                raise ConfigError(
                    f"fixture bodyFile {body_file} is invalid: {error}"
                ) from error
            if not target.is_relative_to(base):
                raise ConfigError(
                    f"fixture bodyFile {body_file} escapes the fixture directory"
                )
            try:
                body = target.read_text(encoding="utf-8")
            except (OSError, UnicodeError, ValueError, RecursionError) as error:
                raise ConfigError(f"cannot load fixture bodyFile {body_file}: {error}") from error

        self.issue_number = _fixture_int(issue.get("number", 0), "issue.number")
        self._issue = IssueRecord(
            number=self.issue_number,
            title=_fixture_string(issue.get("title"), "issue.title"),
            body=body,
            state=_fixture_string(issue.get("state", "OPEN"), "issue.state").upper(),
            assignees=normalize_objects(issue.get("assignees", []), "login", "issue.assignees", ConfigError),
            labels=normalize_objects(issue.get("labels", []), "name", "issue.labels", ConfigError),
        )
        raw_prs = data.get("openClosingPRs", [])
        if not isinstance(raw_prs, list):
            raise ConfigError("fixture openClosingPRs must be a list")
        self._prs = [_fixture_pr(item, index) for index, item in enumerate(raw_prs)]
        status = data.get("projectStatus")
        if status is not None and not isinstance(status, str):
            raise ConfigError("fixture projectStatus must be a string or null")
        self._status = status

    def get_issue(self, issue_number: int) -> IssueRecord:
        """Return the fixture issue without network access."""
        return self._issue

    def get_open_closing_prs(self, issue_number: int) -> list[PRRecord]:
        """Return fixture PRs that are already marked as closing candidates."""
        return self._prs

    def get_project_status(self, issue_number: int) -> Optional[str]:
        """Return the fixture Project Status or deliberate ``None`` absence."""
        return self._status


def _fixture_string(value: Any, label: str, *, allow_none: bool = True) -> str:
    """Validate a fixture string field and normalize allowed nulls to empty."""
    return require_string(value, label, ConfigError, allow_none=allow_none)


def _fixture_int(value: Any, label: str) -> int:
    """Validate a fixture integer field."""
    return require_int(value, label, ConfigError)


def _fixture_pr(value: Any, index: int) -> PRRecord:
    """Normalize one fixture PR object and reject shape drift."""
    label = f"openClosingPRs[{index}]"
    item = expect_mapping(value, label, ConfigError)
    for field in ("number", "title", "body", "url", "headRefName"):
        if field not in item:
            raise ConfigError(f"fixture {label} is missing {field}")
    author = item.get("author")
    if author is None:
        author_login = ""
    elif isinstance(author, Mapping):
        author_login = _fixture_string(author.get("login"), f"{label}.author.login")
    elif isinstance(author, str):
        author_login = author
    else:
        raise ConfigError(f"{label}.author must be an object or string")
    return PRRecord(
        number=_fixture_int(item.get("number"), f"{label}.number"),
        title=_fixture_string(item.get("title"), f"{label}.title"),
        body=_fixture_string(item.get("body"), f"{label}.body"),
        url=_fixture_string(item.get("url"), f"{label}.url"),
        head_ref=_fixture_string(item.get("headRefName"), f"{label}.headRefName"),
        author=author_login,
    )
