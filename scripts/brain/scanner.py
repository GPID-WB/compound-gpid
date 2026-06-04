"""brain.scanner — Entity discovery for the brain engine.

Scans all ``.cg-docs/`` sub-directories and ``roadmap.json`` features to
produce a flat list of :class:`~brain.Entity` objects ready for keyword
extraction.

Supported entity types and their source directories::

    solution    →  .cg-docs/solutions/**/*.md
    plan        →  .cg-docs/plans/*.md
    brainstorm  →  .cg-docs/brainstorms/*.md
    review      →  .cg-docs/reviews/*.md
                   .cg-docs/competitive-reviews/*.md
    strategy    →  .cg-docs/strategy/*.md
    feature     →  roadmap.json (virtual paths: roadmap.json#<feature-id>)

Files in ``.cg-docs/archive/`` and any unrecognised top-level directories
(e.g. the ``DIGEST.md`` file placed directly in ``.cg-docs/``) are silently
skipped.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Dict, List, Optional

from brain import Entity
from brain.utils import extract_summary, parse_frontmatter

# ---------------------------------------------------------------------------
# Directory → entity_type mapping
# ---------------------------------------------------------------------------

#: Maps .cg-docs/ top-level directory names to entity_type strings.
#: A value of ``None`` means "skip this directory entirely".
_DIR_TO_TYPE: Dict[str, Optional[str]] = {
    "solutions": "solution",
    "plans": "plan",
    "brainstorms": "brainstorm",
    "reviews": "review",
    "competitive-reviews": "review",
    "strategy": "strategy",
    "archive": None,  # Archived files are excluded from the brain
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def scan_all(root: Path) -> List[Entity]:
    """Scan all ``.cg-docs/`` subdirectories for markdown entities.

    Walks the entire ``.cg-docs/`` tree with ``rglob("*.md")``, determines the
    entity type from the top-level subdirectory name, and builds one
    :class:`~brain.Entity` per file.  Directories not in :data:`_DIR_TO_TYPE`
    and the ``archive/`` directory are silently skipped.

    The raw file text is stored in :attr:`~brain.Entity.text` so that the
    extractor can process it without re-reading the file.

    Args:
        root: Project root directory (must contain ``.cg-docs/``).

    Returns:
        List of :class:`~brain.Entity` objects sorted by path.

    Example:
        >>> from pathlib import Path
        >>> from brain.scanner import scan_all
        >>> entities = scan_all(root=Path("."))
        >>> print(len(entities), "entities found")
    """
    cg_docs = root / ".cg-docs"
    if not cg_docs.is_dir():
        return []

    entities: List[Entity] = []

    # Pre-compute once outside the loop (P2.1 fix: avoid O(n) resolve() syscalls)
    cg_docs_real = cg_docs.resolve()

    for md_path in sorted(cg_docs.rglob("*.md")):
        # Guard: reject symlinks that escape the .cg-docs/ directory (P1.1 fix).
        # Use relative_to() for component-level comparison — startswith() is vulnerable
        # to sibling directories sharing the same string prefix (e.g. .cg-docs-evil).
        try:
            resolved_path = md_path.resolve()
        except OSError:
            continue
        try:
            resolved_path.relative_to(cg_docs_real)
        except ValueError:
            warnings.warn(
                f"[brain.scanner] Skipping {md_path}: symlink escapes .cg-docs/ boundary.",
                stacklevel=2,
            )
            continue

        # Guard: reject files over 10 MB to prevent memory exhaustion (adversarial P2.1 fix)
        try:
            file_size = md_path.stat().st_size
        except OSError:
            continue
        if file_size > 10 * 1024 * 1024:
            warnings.warn(
                f"[brain.scanner] Skipping {md_path}: file size {file_size // 1024 // 1024} MB "
                "exceeds 10 MB limit.",
                stacklevel=2,
            )
            continue

        # Determine the top-level directory under .cg-docs/
        try:
            rel_parts = md_path.relative_to(cg_docs).parts
        except ValueError:
            continue

        if len(rel_parts) < 2:
            # File is directly in .cg-docs/ (e.g. DIGEST.md) — skip
            continue

        top_dir = rel_parts[0]
        entity_type = _DIR_TO_TYPE.get(top_dir)
        if entity_type is None:
            if top_dir not in _DIR_TO_TYPE:
                warnings.warn(
                    f"[brain.scanner] Unknown .cg-docs/ subdirectory '{top_dir}' — skipping. "
                    "Add it to _DIR_TO_TYPE to index it.",
                    stacklevel=2,
                )
            continue  # archive/ or unrecognised directory

        try:
            text = md_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            warnings.warn(
                f"[brain.scanner] Could not read {md_path}: {exc}",
                stacklevel=2,
            )
            continue

        frontmatter = parse_frontmatter(text)
        if not frontmatter and text.lstrip("\ufeff\r\n").startswith("---"):
            warnings.warn(
                f"[brain.scanner] {md_path}: frontmatter block found but could not be parsed "
                "(missing closing '---'?). Entity indexed with empty frontmatter.",
                stacklevel=2,
            )
        summary = extract_summary(text)

        entities.append(
            Entity(
                path=md_path.relative_to(root),
                entity_type=entity_type,
                frontmatter=frontmatter,
                summary=summary,
                text=text,
            )
        )

    return entities


def scan_roadmap(root: Path) -> List[Entity]:
    """Scan ``roadmap.json`` and produce one :class:`~brain.Entity` per feature.

    Each feature is given a virtual path ``roadmap.json#<feature-id>`` so that
    edge detection can link plan files to their roadmap feature via the
    ``plan:`` frontmatter field.

    The ``text`` field is populated with milestone title, feature title, and
    milestone objective to give the keyword extractor useful signal.

    Args:
        root: Project root directory (must contain ``roadmap.json``).

    Returns:
        List of feature :class:`~brain.Entity` objects.  Returns ``[]`` if
        ``roadmap.json`` is absent or malformed.

    Example:
        >>> from pathlib import Path
        >>> from brain.scanner import scan_roadmap
        >>> features = scan_roadmap(root=Path("."))
        >>> print(len(features), "roadmap features found")
    """
    roadmap_path = root / "roadmap.json"
    if not roadmap_path.is_file():
        return []

    try:
        data = json.loads(roadmap_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        warnings.warn(
            f"[brain.scanner] Could not parse roadmap.json: {exc}",
            stacklevel=2,
        )
        return []

    if not isinstance(data, dict):
        warnings.warn(
            "[brain.scanner] roadmap.json is not a JSON object — skipping.",
            stacklevel=2,
        )
        return []

    entities: List[Entity] = []

    for milestone in data.get("milestones", []):
        if not isinstance(milestone, dict):
            warnings.warn(
                "[brain.scanner] roadmap milestone is not a dict; skipping.",
                stacklevel=2,
            )
            continue
        m_title: str = milestone.get("title", "")
        m_objective: str = milestone.get("objective", "")

        for feature in milestone.get("features", []):
            if not isinstance(feature, dict):
                warnings.warn(
                    f"[brain.scanner] roadmap feature in milestone '{m_title}' is not a dict; skipping.",
                    stacklevel=2,
                )
                continue
            feature_id: str = feature.get("id", "")
            if not feature_id:
                warnings.warn(
                    f"[brain.scanner] roadmap feature in milestone '{m_title}' has no 'id'; skipping.",
                    stacklevel=2,
                )
                continue

            feature_title: str = feature.get("title", feature_id)
            virtual_path = Path(f"roadmap.json#{feature_id}")

            # Build text corpus for keyword extraction
            text_parts = [f"Feature: {feature_title}"]
            if m_title:
                text_parts.append(f"Milestone: {m_title}")
            if m_objective:
                text_parts.append(f"Objective: {m_objective}")

            frontmatter = {
                "id": feature_id,
                "title": feature_title,
                "status": feature.get("status", ""),
                "milestone": m_title,
                "plan": feature.get("plan"),
                "brainstorm": feature.get("brainstorm"),
            }

            entities.append(
                Entity(
                    path=virtual_path,
                    entity_type="feature",
                    frontmatter=frontmatter,
                    summary=feature_title,
                    text="\n".join(text_parts),
                )
            )

    return entities
