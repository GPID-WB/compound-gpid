"""Frozen design-token and stable semantic-structure contract tests."""
from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
from typing import Dict, List, Optional, Set

from artifact_views.parser import parse_artifact
from artifact_views.provenance import ArtifactProvenance
from artifact_views.renderer import render_document
from artifact_views.schema import ArtifactKind
from artifact_views.templates import design_contract

TEST_ROOT = Path(__file__).parent
FIXTURES = TEST_ROOT / "fixtures"
SNAPSHOTS = TEST_ROOT / "snapshots"


class _SemanticSummary(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.kind: Optional[str] = None
        self.landmarks: List[str] = []
        self.derived: Set[str] = set()
        self.meta_names: Set[str] = set()
        self.classes: Set[str] = set()
        self.source_blocks: List[str] = []
        self.source_line_blocks = 0
        self.provenance_script = False

    def handle_starttag(self, tag, attrs) -> None:
        attributes = dict(attrs)
        if tag == "body":
            self.kind = attributes.get("data-artifact-kind")
        if tag in {"header", "nav", "main", "article", "footer"}:
            self.landmarks.append(tag)
        if attributes.get("data-derived"):
            self.derived.add(attributes["data-derived"])
        if tag == "meta" and attributes.get("name"):
            self.meta_names.add(attributes["name"])
        for class_name in (attributes.get("class") or "").split():
            self.classes.add(class_name)
        if attributes.get("data-source-block"):
            self.source_blocks.append(attributes["data-source-block"])
            if attributes.get("data-source-lines"):
                self.source_line_blocks += 1
        if tag == "script" and attributes.get("id") == "artifact-provenance":
            self.provenance_script = True

    def to_dict(self) -> Dict[str, object]:
        return {
            "artifactKind": self.kind,
            "landmarks": self.landmarks,
            "derived": sorted(self.derived),
            "metaNames": sorted(self.meta_names),
            "classes": sorted(self.classes),
            "sourceOwnerCount": len(self.source_blocks),
            "sourceOwnersUnique": len(self.source_blocks) == len(set(self.source_blocks)),
            "sourceLinesComplete": self.source_line_blocks == len(self.source_blocks),
            "provenanceScript": self.provenance_script,
        }


def _render_summary(fixture: str, kind: ArtifactKind) -> Dict[str, object]:
    source = (FIXTURES / fixture).read_text(encoding="utf-8")
    source_path = Path(f".cg-docs/{kind.value}s/{fixture}")
    document = parse_artifact(source, source_path, kind)
    provenance = ArtifactProvenance.from_source(
        source_path=source_path,
        source_bytes=source.encode("utf-8"),
        artifact_schema_version=1,
        renderer_version="0.1.0",
        generated_at=datetime(2026, 7, 31, tzinfo=timezone.utc),
    )
    parser = _SemanticSummary()
    parser.feed(render_document(document, provenance).decode("utf-8"))
    return parser.to_dict()


def test_design_contract_matches_frozen_snapshot() -> None:
    expected = json.loads(
        (SNAPSHOTS / "design-contract.json").read_text(encoding="utf-8")
    )

    assert design_contract() == expected


def test_brainstorm_structure_matches_frozen_snapshot() -> None:
    expected = json.loads(
        (SNAPSHOTS / "brainstorm-structure.json").read_text(encoding="utf-8")
    )

    assert _render_summary("strict_brainstorm.md", ArtifactKind.BRAINSTORM) == expected


def test_plan_structure_matches_frozen_snapshot() -> None:
    expected = json.loads(
        (SNAPSHOTS / "plan-structure.json").read_text(encoding="utf-8")
    )

    assert _render_summary("strict_deep_plan.md", ArtifactKind.PLAN) == expected


def test_frozen_contract_retains_accessibility_and_print_guards() -> None:
    contract = design_contract()

    assert contract["breakpoints"] == ["48rem"]
    assert contract["focus"]["outlineWidth"] == "3px"
    assert contract["motion"]["reduced"] is True
    assert contract["print"]["preservesCanonicalContent"] is True
    assert contract["layout"]["readingFlow"] == "unframed"
    assert contract["components"]["nestedCards"] is False
