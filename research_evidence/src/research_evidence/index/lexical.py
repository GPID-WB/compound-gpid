"""Created 2026-08-13. Generalized derived SQLite FTS lexical baseline."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sqlite3
import threading
from typing import Optional

from ..filesystem import validate_path_components
from ..schemas import SourceUnit, TypedLocator

_TOKEN_PATTERN = re.compile(r"[\w]+(?:[-'][\w]+)*", re.UNICODE)
_INDEX_SCHEMA = "research-evidence-lexical-v2"


class LexicalIndex:
    """Maintain a deterministic local SQLite FTS5 index of typed source units.

    Args:
        path: Derived SQLite database path; canonical YAML remains authoritative.

    Returns:
        An open lexical index.

    Example:
        ``index = LexicalIndex(Path(".runtime/lexical.sqlite"))``.
    """

    def __init__(self, path: Path) -> None:
        """Open or create the versioned derived FTS database.

        Args:
            path: SQLite database path.

        Returns:
            ``None``; the index is ready for rebuild or search.

        Raises:
            sqlite3.DatabaseError: If an existing database is corrupt.

        Example:
            ``LexicalIndex(tmp_path / "index.sqlite")``.
        """
        self.path = Path(path)
        self._validate_storage_path(create_parent=True)
        if self.path.exists() and not self.path.is_file():
            raise ValueError("Lexical index path must be a regular file.")
        self._lock = threading.RLock()
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self._ensure_schema()

    @classmethod
    def open_or_rebuild(cls, path: Path, units: list[SourceUnit]) -> "LexicalIndex":
        """Open a derived index or replace a corrupt one from source units.

        Args:
            path: Derived SQLite database path.
            units: Canonical source units used for an explicit rebuild.

        Returns:
            An open rebuilt or existing index.

        Example:
            ``LexicalIndex.open_or_rebuild(path, parsed.units)``.
        """
        try:
            index = cls(path)
        except sqlite3.DatabaseError:
            Path(path).unlink(missing_ok=True)
            index = cls(path)
        index.rebuild(units)
        return index

    def rebuild(self, units: list[SourceUnit]) -> None:
        """Replace the complete derived index with deterministic source units.

        Args:
            units: Source units to index.

        Returns:
            ``None`` after the SQLite transaction commits.

        Example:
            ``index.rebuild(parsed.units)`` creates a clean lexical baseline.
        """
        with self._lock:
            self._validate_storage_path()
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
        with self._lock:
            self._validate_storage_path()
            self._insert_units(units)
            self.connection.commit()

    def replace_units(self, old_source_unit_ids: list[str], units: list[SourceUnit]) -> None:
        """Remove affected derived units and insert their replacements atomically.

        Args:
            old_source_unit_ids: IDs no longer present after a source update.
            units: Current replacement units.

        Returns:
            ``None`` after the derived update commits.

        Example:
            ``index.replace_units([old_id], [new_unit])`` updates one resource.
        """
        with self._lock:
            self._validate_storage_path()
            self._remove_ids(old_source_unit_ids)
            self._insert_units(units)
            self.connection.commit()

    def remove(self, source_unit_ids: list[str]) -> None:
        """Remove deleted or stale source units from the derived index.

        Args:
            source_unit_ids: Deterministic IDs to remove.

        Returns:
            ``None`` after the derived update commits.

        Example:
            ``index.remove([deleted_unit_id])`` removes one deleted unit.
        """
        with self._lock:
            self._validate_storage_path()
            self._remove_ids(source_unit_ids)
            self.connection.commit()

    def search(self, query: str, limit: int = 20) -> list[SourceUnit]:
        """Search text, headings, and typed metadata with stable tie-breaking.

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
        with self._lock:
            self._validate_storage_path()
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
            return [
                unit
                for (source_unit_id,) in rows
                if (unit := self.get(source_unit_id)) is not None
            ]

    def get(self, source_unit_id: str) -> Optional[SourceUnit]:
        """Return one indexed source unit by ID.

        Args:
            source_unit_id: Deterministic source-unit identifier.

        Returns:
            The source unit, or ``None`` when it is not indexed.

        Example:
            ``index.get("source-unit:...")`` retrieves source context.
        """
        with self._lock:
            self._validate_storage_path()
            row = self.connection.execute(
                """
                SELECT source_version_id, locator_json, text, heading_path,
                       unit_type, review_required, parser_metadata_json
                FROM source_units WHERE source_unit_id = ?
                """,
                (source_unit_id,),
            ).fetchone()
        if row is None:
            return None
        (
            source_version_id,
            locator_json,
            text,
            heading_path,
            unit_type,
            review_required,
            parser_metadata_json,
        ) = row
        return SourceUnit(
            source_unit_id=source_unit_id,
            source_version_id=source_version_id,
            locator=TypedLocator.model_validate(json.loads(locator_json)),
            text=text,
            heading_path=json.loads(heading_path),
            unit_type=unit_type,
            review_required=bool(review_required),
            parser_metadata=json.loads(parser_metadata_json),
        )

    def metadata(self, source_unit_id: str) -> dict[str, object]:
        """Return typed index metadata without exposing a raw-text side channel.

        Args:
            source_unit_id: Deterministic source-unit identifier.

        Returns:
            Unit type, review flag, source version, and parser metadata.

        Raises:
            KeyError: If the source unit is not indexed.

        Example:
            ``index.metadata(unit_id)["review_required"]`` gates review display.
        """
        with self._lock:
            self._validate_storage_path()
            row = self.connection.execute(
                """
                SELECT source_version_id, unit_type, review_required, parser_metadata_json
                FROM source_units WHERE source_unit_id = ?
                """,
                (source_unit_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Source unit is not indexed: {source_unit_id}")
        return {
            "source_version_id": row[0],
            "unit_type": row[1],
            "review_required": bool(row[2]),
            "parser_metadata": json.loads(row[3]),
        }

    def manifest(self) -> dict[str, object]:
        """Return a rebuildable index manifest without raw corpus text.

        Args:
            None.

        Returns:
            Schema, profile, indexed-unit count, and raw-text logging policy.

        Example:
            ``index.manifest()["raw_text_logging"]`` is always ``False``.
        """
        with self._lock:
            self._validate_storage_path()
            count = self.connection.execute("SELECT COUNT(*) FROM source_units").fetchone()[0]
        return {
            "schema_version": _INDEX_SCHEMA,
            "profile": "lexical-baseline",
            "indexed_units": int(count),
            "raw_text_logging": False,
        }

    def close(self) -> None:
        """Close the local SQLite connection.

        Args:
            None.

        Returns:
            ``None`` after the derived connection closes.

        Example:
            ``index.close()`` releases the file handle after a run.
        """
        with self._lock:
            self.connection.close()

    def _validate_storage_path(self, *, create_parent: bool = False) -> None:
        """Validate the SQLite path immediately before filesystem use."""
        try:
            validate_path_components(self.path.parent)
            if create_parent:
                self.path.parent.mkdir(parents=True, exist_ok=True)
            validate_path_components(self.path.parent, require_directory=True)
            validate_path_components(self.path)
        except OSError as error:
            raise ValueError("Lexical index path contains an unsafe component.") from error

    def _ensure_schema(self) -> None:
        """Create the current derived schema or migrate an older Phase 1 schema."""
        expected_columns = {
            "source_unit_id",
            "source_version_id",
            "locator_json",
            "text",
            "heading_path",
            "unit_type",
            "review_required",
            "parser_metadata_json",
            "source_order",
        }
        existing = {
            row[1]
            for row in self.connection.execute("PRAGMA table_info(source_units)").fetchall()
        }
        if existing and not expected_columns.issubset(existing):
            self.connection.execute("DROP TABLE IF EXISTS source_units_fts")
            self.connection.execute("DROP TABLE IF EXISTS source_units")
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS source_units (
                source_unit_id TEXT PRIMARY KEY,
                source_version_id TEXT NOT NULL,
                locator_json TEXT NOT NULL,
                text TEXT NOT NULL,
                heading_path TEXT NOT NULL,
                unit_type TEXT NOT NULL,
                review_required INTEGER NOT NULL,
                parser_metadata_json TEXT NOT NULL,
                source_order TEXT NOT NULL
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS source_units_fts USING fts5(
                source_unit_id UNINDEXED,
                text,
                heading_path,
                metadata
            );
            """
        )
        self.connection.commit()

    def _remove_ids(self, source_unit_ids: list[str]) -> None:
        """Remove IDs from both the source table and FTS table."""
        for source_unit_id in source_unit_ids:
            self.connection.execute(
                "DELETE FROM source_units_fts WHERE source_unit_id = ?",
                (source_unit_id,),
            )
            self.connection.execute(
                "DELETE FROM source_units WHERE source_unit_id = ?",
                (source_unit_id,),
            )

    def _insert_units(self, units: list[SourceUnit]) -> None:
        """Insert units into source and FTS tables with typed metadata."""
        for unit in units:
            locator_json = json.dumps(
                unit.locator.model_dump(mode="json", exclude_none=True),
                sort_keys=True,
            )
            parser_metadata_json = json.dumps(unit.parser_metadata, sort_keys=True)
            metadata = " ".join(
                [unit.unit_type, "review-required" if unit.review_required else ""]
                + list(unit.parser_metadata.values())
            )
            source_order = locator_json
            self._remove_ids([unit.source_unit_id])
            self.connection.execute(
                """
                INSERT INTO source_units(
                    source_unit_id, source_version_id, locator_json, text,
                    heading_path, unit_type, review_required,
                    parser_metadata_json, source_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    unit.source_unit_id,
                    unit.source_version_id,
                    locator_json,
                    unit.text,
                    json.dumps(unit.heading_path, ensure_ascii=False),
                    unit.unit_type,
                    int(unit.review_required),
                    parser_metadata_json,
                    source_order,
                ),
            )
            self.connection.execute(
                """
                INSERT INTO source_units_fts(source_unit_id, text, heading_path, metadata)
                VALUES (?, ?, ?, ?)
                """,
                (unit.source_unit_id, unit.text, " ".join(unit.heading_path), metadata),
            )
