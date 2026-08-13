"""Created 2026-08-12. Derived SQLite FTS lexical index for source units."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sqlite3
from typing import Optional

from ..schemas import SourceUnit, TypedLocator

_TOKEN_PATTERN = re.compile(r"[\w]+(?:[-'][\w]+)*", re.UNICODE)


class LexicalIndex:
    """Maintain a deterministic local SQLite FTS5 index of source units.

    Args:
        path: Derived SQLite database path; canonical YAML remains authoritative.

    Returns:
        An open lexical index.

    Example:
        ``index = LexicalIndex(Path(".runtime/lexical.sqlite"))``.
    """

    def __init__(self, path: Path) -> None:
        """Open or create the derived FTS database.

        Args:
            path: SQLite database path.

        Returns:
            ``None``; the index is ready for rebuild or search.

        Example:
            ``LexicalIndex(tmp_path / "index.sqlite")``.
        """
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS source_units (
                source_unit_id TEXT PRIMARY KEY,
                source_version_id TEXT NOT NULL,
                locator_json TEXT NOT NULL,
                text TEXT NOT NULL,
                heading_path TEXT NOT NULL
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS source_units_fts USING fts5(
                source_unit_id UNINDEXED,
                text,
                heading_path
            );
            """
        )
        self.connection.commit()

    def rebuild(self, units: list[SourceUnit]) -> None:
        """Replace the complete derived index with deterministic source units.

        Args:
            units: Source units to index.

        Returns:
            ``None`` after the SQLite transaction commits.

        Example:
            ``index.rebuild(parsed.units)`` creates a clean lexical baseline.
        """
        self.connection.execute("DELETE FROM source_units")
        self.connection.execute("DELETE FROM source_units_fts")
        self._insert_units(units)
        self.connection.commit()

    def upsert(self, units: list[SourceUnit]) -> None:
        """Insert or replace only the supplied source units.

        Args:
            units: Changed or newly parsed source units.

        Returns:
            ``None`` after the SQLite transaction commits.

        Example:
            ``index.upsert(changed_units)`` updates an incremental slice.
        """
        self._insert_units(units)
        self.connection.commit()

    def search(self, query: str, limit: int = 20) -> list[SourceUnit]:
        """Search source text and headings with deterministic score tie-breaking.

        Args:
            query: User-entered lexical query.
            limit: Maximum result count.

        Returns:
            Source units ordered by FTS score, then source-unit ID.

        Raises:
            ValueError: If ``limit`` is not positive.

        Example:
            ``index.search("weighted poverty")`` returns matching units.
        """
        if limit <= 0:
            raise ValueError("Search limit must be positive.")
        tokens = _TOKEN_PATTERN.findall(query)
        if not tokens:
            return []
        match_query = " AND ".join('"' + token.replace('"', '""') + '"' for token in tokens)
        rows = self.connection.execute(
            """
            SELECT source_unit_id
            FROM source_units_fts
            WHERE source_units_fts MATCH ?
            ORDER BY bm25(source_units_fts) ASC, source_unit_id ASC
            LIMIT ?
            """,
            (match_query, limit),
        ).fetchall()
        return [unit for (source_unit_id,) in rows if (unit := self.get(source_unit_id)) is not None]

    def get(self, source_unit_id: str) -> Optional[SourceUnit]:
        """Return one indexed source unit by ID.

        Args:
            source_unit_id: Deterministic source-unit identifier.

        Returns:
            The source unit, or ``None`` when it is not indexed.

        Example:
            ``index.get("source-unit:...")`` retrieves source context.
        """
        row = self.connection.execute(
            "SELECT source_version_id, locator_json, text, heading_path FROM source_units WHERE source_unit_id = ?",
            (source_unit_id,),
        ).fetchone()
        if row is None:
            return None
        source_version_id, locator_json, text, heading_path = row
        return SourceUnit(
            source_unit_id=source_unit_id,
            source_version_id=source_version_id,
            locator=TypedLocator.model_validate(json.loads(locator_json)),
            text=text,
            heading_path=json.loads(heading_path),
        )

    def close(self) -> None:
        """Close the local SQLite connection.

        Args:
            None.

        Returns:
            ``None`` after the derived connection closes.

        Example:
            ``index.close()`` releases the file handle after a run.
        """
        self.connection.close()

    def _insert_units(self, units: list[SourceUnit]) -> None:
        """Insert units into both the source table and FTS table."""
        for unit in units:
            self.connection.execute(
                "DELETE FROM source_units_fts WHERE source_unit_id = ?",
                (unit.source_unit_id,),
            )
            self.connection.execute(
                """
                INSERT INTO source_units(source_unit_id, source_version_id, locator_json, text, heading_path)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(source_unit_id) DO UPDATE SET
                    source_version_id = excluded.source_version_id,
                    locator_json = excluded.locator_json,
                    text = excluded.text,
                    heading_path = excluded.heading_path
                """,
                (
                    unit.source_unit_id,
                    unit.source_version_id,
                    json.dumps(unit.locator.model_dump(mode="json", exclude_none=True), sort_keys=True),
                    unit.text,
                    json.dumps(unit.heading_path, ensure_ascii=False),
                ),
            )
            self.connection.execute(
                "INSERT INTO source_units_fts(source_unit_id, text, heading_path) VALUES (?, ?, ?)",
                (unit.source_unit_id, unit.text, " ".join(unit.heading_path)),
            )
