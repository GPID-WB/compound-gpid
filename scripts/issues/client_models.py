"""Normalized data records shared by readiness clients and orchestration."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IssueRecord:
    """Normalized issue state returned by a readiness client."""

    number: int
    title: str
    body: str
    state: str
    assignees: list[str]
    labels: list[str]


@dataclass
class PRRecord:
    """Normalized pull-request state used by rule R020."""

    number: int
    title: str
    body: str
    url: str
    head_ref: str
    author: str
