"""Sole writer of catalog-derived command facts; editorial text stays unchanged.

Explicit bootstrap recognizes pinned old table ranges. Normal generation never
creates markers, runs source code, or accepts a stale catalog.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from typing import Dict, List

import secure_fs
from help import catalog

TARGETS = ("reference.md", "reference/commands.md")
SECTIONS = ("help-commands", "help-research-commands", "help-shell-commands")
BOOTSTRAP = json.loads(Path(__file__).with_name("docs-bootstrap-v1.json").read_text())


def _read(root: Path, name: str) -> str:
    return secure_fs.secure_read_bytes(root, "docs/" + name,
                                      reject_hardlinks=True, max_bytes=4 * 1024 * 1024).decode("utf-8")


def _markers(text: str) -> dict:
    found, active, fence, offset = {}, None, None, 0
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
        elif fence is None:
            match = re.fullmatch(r"\s*<!--\s*cg:auto:([a-z0-9-]+)\s*-->\s*", line)
            if match:
                name = match.group(1)
                if name == "end":
                    if active is None:
                        raise ValueError("Unbalanced documentation marker")
                    key, start, interior = active
                    found[key] = (start, interior, offset, offset + len(line))
                    active = None
                else:
                    if active or name in found:
                        raise ValueError("Nested or duplicate documentation marker: " + name)
                    active = (name, offset, offset + len(line))
        offset += len(line)
    if active:
        raise ValueError("Unclosed documentation marker")
    return found


def _legacy_table(text: str, rule: dict) -> tuple:
    sections = list(re.finditer(r"^" + re.escape(rule["heading"]) +
                               r"[ \t]*\n(.*?)(?=^#{1,6} |\Z)", text, re.M | re.S))
    if len(sections) != 1:
        raise ValueError("Missing or ambiguous legacy bootstrap heading")
    section = sections[0]
    tables = list(re.finditer(r"^\|[^\n]*\n(?:^\|[^\n]*\n)+", section.group(1), re.M))
    if len(tables) != 1 or hashlib.sha256(tables[0].group().encode()).hexdigest() != rule["sha256"]:
        raise ValueError("Unrecognized legacy bootstrap table; review exact bounds")
    return section.start(1) + tables[0].start(), section.start(1) + tables[0].end()


def _bootstrap_text(name: str, text: str) -> str:
    markers = _markers(text)
    present = set(SECTIONS).intersection(markers)
    if present:
        if present != set(SECTIONS):
            raise ValueError("Partial help marker migration; restore or finish the reviewed migration")
        return text
    for key, rule in BOOTSTRAP[name].items():
        if "legacy" in rule:
            if rule["legacy"] not in _markers(text):
                raise ValueError("Missing legacy bootstrap marker")
            text = text.replace("<!-- cg:auto:" + rule["legacy"] + " -->",
                                "<!-- cg:auto:" + key + " -->", 1)
        else:
            start, end = _legacy_table(text, rule)
            text = text[:start] + "<!-- cg:auto:" + key + " -->\n" + text[start:end] + "<!-- cg:auto:end -->\n" + text[end:]
    return text


def _write(root: Path, outputs: Dict[str, str]) -> List[str]:
    changed = []
    for name, text in outputs.items():
        before = _read(root, name)
        if text != before:
            secure_fs.secure_write_bytes(root, Path("docs") / name, text.encode("utf-8"),
                expected_state=secure_fs.ExpectedFileState.from_bytes(before.encode("utf-8")))
            changed.append(name)
    return changed


def bootstrap(root: Path) -> dict:
    """Migrate only recognized legacy ranges, after validating every target.

    Args: root: Canonical repository root.
    Returns: A stable status and list of changed files.
    Raises: ValueError for ambiguous or malformed old ranges.
    Example: bootstrap(Path('.')) returns already-bootstrapped on a repeat.
    """
    outputs = {name: _bootstrap_text(name, _read(root, name)) for name in TARGETS}
    changed = _write(root, outputs)
    return {"status": "bootstrapped" if changed else "already-bootstrapped", "files": changed}


def _cell(value: str) -> str:
    # Entity escaping covers both HTML and Markdown control characters.
    text = html.escape(value, quote=True).replace("\n", " ")
    for char in "`|[]()*_\\":
        text = text.replace(char, "&#{};".format(ord(char)))
    return text


def render_table(value: dict, section: str) -> str:
    """Render safe usage/summary facts selected by kind and supported suites.

    Args: value: Validated catalog. section: One declared help section.
    Returns: A deterministic Markdown table.
    Raises: ValueError for unknown sections.
    Example: render_table(catalog, 'help-commands').
    """
    if section not in SECTIONS:
        raise ValueError("Unknown help documentation section")
    rows = ["| Command | Suites | Purpose |", "| --- | --- | --- |"]
    for command in value["commands"]:
        eligible = command["kind"] == "shell" if section == "help-shell-commands" else (
            command["kind"] == "slash" and ("cr" if section == "help-research-commands" else "cg") in command["supportedSuites"])
        if eligible:
            rows.append("| {} | {} | {} |".format(_cell(command["usage"]),
                ", ".join(s.upper() for s in command["supportedSuites"]), _cell(command["summary"])))
    return "\n".join(rows) + "\n"


def expected_documents(root: Path) -> Dict[str, str]:
    """Compute exact owned output from a current, independently validated catalog.

    Args: root: Canonical repository root.
    Returns: Complete document bytes as UTF-8 strings with editorial text intact.
    Raises: ValueError for stale catalog, missing or malformed markers.
    Example: expected_documents(Path('.')) is a no-write build operation.
    """
    return expected_bundle(root)["documents"]


def expected_bundle(root: Path) -> dict:
    """Return documents and their single validated catalog snapshot.

    Args: root: Canonical repository root.
    Returns: A catalog/documents envelope for the protected website builder.
    Raises: ValueError for stale sources, catalog or documentation ownership.
    Example: expected_bundle(Path('.'))['catalog'] supplies browser facts.
    """
    _validate_ownership(root)
    expected = catalog.generate_catalog_bytes(root)
    observed = secure_fs.secure_read_bytes(root, catalog.CATALOG_OUTPUT_PATH,
                                          reject_hardlinks=True, max_bytes=catalog.MAX_JSON_BYTES)
    if observed != expected:
        raise catalog.HelpCatalogStaleError("help catalog is stale or unexpected")
    value = catalog.load_strict_json_bytes(expected, source="validated catalog snapshot")
    outputs = {}
    for name in TARGETS:
        text = _read(root, name)
        markers = _markers(text)
        if not set(SECTIONS).issubset(markers):
            raise ValueError("Missing help marker; explicit --bootstrap-docs-markers is required")
        for key in sorted(SECTIONS, key=lambda s: markers[s][1], reverse=True):
            _, start, end, _ = markers[key]
            text = text[:start] + render_table(value, key) + text[end:]
        outputs[name] = text
    return {"catalog": value, "documents": outputs}


def _validate_ownership(root: Path) -> None:
    """Check the bounded wiki ownership declaration without a YAML dependency."""
    text = _read(root, "_wiki.yml").replace("\r\n", "\n")
    blocks = re.findall(r"^externalGenerators:\n(.*?)(?=^\S|\Z)", text, re.M | re.S)
    expected = (
        '  help-catalog:\n'
        '    files: ["reference.md", "reference/commands.md"]\n'
        '    sections: ["help-commands", "help-research-commands", "help-shell-commands"]\n'
        '    writer: "python scripts/cg_generate_help_catalog.py --write-docs"\n'
        '    checker: "python scripts/cg_generate_help_catalog.py --check-docs"\n'
    )
    if blocks != [expected]:
        raise ValueError("Wiki help ownership declaration differs from the supported contract")
    for section in SECTIONS:
        declaration = ('      - id: "' + section + '"\n'
                       '        managed: true\n        generator: "help-catalog"\n')
        if text.count(declaration) != 1:
            raise ValueError("Wiki section must have exactly one help-catalog owner: " + section)


def write_documents(root: Path) -> List[str]:
    """Write only validated changed documents. Example: write_documents(Path('.'))."""
    return _write(root, expected_documents(root))


def check_documents(root: Path) -> None:
    """Fail on stale owned bytes without writing. Example: check_documents(Path('.'))."""
    stale = [name for name, text in expected_documents(root).items() if _read(root, name) != text]
    if stale:
        raise catalog.HelpCatalogStaleError("help documentation is stale: " + ", ".join(stale))


def editorial(text: str) -> str:
    """Return all bytes outside owned interiors for preservation tests.

    Args: text: A legacy or migrated target document.
    Returns: Text with owned facts replaced by fixed sentinel interiors.
    Raises: ValueError for unrecognized marker boundaries.
    Example: editorial(before) == editorial(after) proves editorial preservation.
    """
    name = "reference.md" if text.startswith("# Reference\n") else "reference/commands.md"
    text = _bootstrap_text(name, text)
    markers = _markers(text)
    for key in sorted(SECTIONS, key=lambda s: markers[s][1], reverse=True):
        _, start, end, _ = markers[key]
        text = text[:start] + "<owned facts>\n" + text[end:]
    return text
