"""Created 2026-08-13. Documentation contracts for the evidence workbench."""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _corpus() -> str:
    """Load canonical evidence documentation surfaces as one lower-case corpus."""
    paths = (
        REPO_ROOT / "README.md",
        REPO_ROOT / "c-research/README.md",
        REPO_ROOT / "docs/reference.md",
        REPO_ROOT / "research_evidence/README.md",
        REPO_ROOT / ".github/skills/cr-skill-evidence-provenance/SKILL.md",
        REPO_ROOT / ".github/prompts/cr-work.prompt.md",
        REPO_ROOT / ".github/prompts/cr-review.prompt.md",
    )
    return "\n".join(path.read_text(encoding="utf-8") for path in paths).lower()


def test_documentation_describes_local_evidence_operating_boundary() -> None:
    """Document setup, canonical/derived state, review, and v1 non-goals."""
    corpus = _corpus()
    for term in (
        "research_evidence",
        "c-research/evidence",
        "manuscripts/",
        "local-only",
        "original files remain authoritative",
        "canonical yaml",
        "external-quarantine",
        "ocr",
        "fastapi",
        "loopback",
        "candidate",
        "no internet search",
        "no external api",
        "stale",
        "recovery",
    ):
        assert term in corpus, term


def test_every_research_evidence_python_artifact_has_creation_header() -> None:
    """Keep the repository's creation-date requirement machine-checkable."""
    source_root = REPO_ROOT / "research_evidence"
    for path in sorted(source_root.rglob("*.py")):
        if any(part in {".venv", ".pytest_cache", "__pycache__"} for part in path.parts):
            continue
        first_lines = "\n".join(path.read_text(encoding="utf-8").splitlines()[:3])
        assert "Created 2026-08-" in first_lines, path
