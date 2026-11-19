"""Regressions for review-cycle help remedies, ranking, and source eligibility."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import cg_help
import cg_project_manifest as manifest
import help_catalog

ROOT = Path(__file__).resolve().parents[2]


def _consumer(root: Path, suites: str = "cg") -> Path:
    """Create a minimal consumer fixture, never a linked real project."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "compound-gpid.local.md").write_text(
        f"---\nsuites: [{suites}]\n---\n", encoding="utf-8")
    return root


def _catalog_file(path: Path) -> Path:
    """Build current sources into external scratch without refreshing shared output."""
    path.write_text(json.dumps(help_catalog.build_catalog(ROOT)), encoding="utf-8")
    return path


def test_inactive_remedy_preserves_manifest_platforms_and_cites_relink(
    tmp_path: Path,
) -> None:
    consumer = _consumer(tmp_path / "consumer")
    active = manifest.resolve_active_manifest(
        consumer, platforms=["copilot", "kilo"], source_root=ROOT)
    assert manifest.validate_manifest(active) == []
    assert manifest.ensure_managed_state(consumer, active) == []
    active_path = consumer / manifest.ACTIVE_MANIFEST_PATH
    active_path.write_text(manifest.canonical_manifest_bytes(active), encoding="utf-8")
    before = {p.relative_to(consumer): p.read_bytes()
              for p in consumer.rglob("*") if p.is_file()}
    result = cg_help.query("Explain /cr-work", consumer,
                           catalog_path=_catalog_file(tmp_path / "catalog.json"))
    assert result["state"] == "inactive"
    assert result["evidence"] == []
    candidate = result["candidates"][0]
    assert "cg-link --platforms copilot,kilo" in candidate["remedy"]
    assert "suites: [cg, cr]" in candidate["remedy"]
    assert "intended full platform list" in candidate["remedy"]
    assert "then refresh with cg-update" not in candidate["remedy"]
    citation = candidate["remedy_source"]
    assert citation["source"] == "docs/installation.md"
    lines = (ROOT / citation["source"]).read_text(encoding="utf-8").splitlines()
    excerpt = "\n".join(lines[citation["start_line"] - 1:citation["end_line"]])
    assert "immutable selection" in excerpt and "cg-link --platforms" in excerpt
    assert before == {p.relative_to(consumer): p.read_bytes()
                      for p in consumer.rglob("*") if p.is_file()}


@pytest.mark.parametrize("platform", ["Windows", "macOS"])
@pytest.mark.parametrize("configured", [True, False])
def test_install_question_returns_real_platform_clone_install_and_link_steps(
    tmp_path: Path, platform: str, configured: bool,
) -> None:
    consumer = tmp_path / "consumer"
    if configured:
        _consumer(consumer)
    else:
        consumer.mkdir()
    question = f"How to install on {platform}?"
    catalog = _catalog_file(tmp_path / "catalog.json")
    result = cg_help.query(question, consumer, catalog_path=catalog)
    assert result["status"] == "ok"
    assert result["candidates"] == []
    assert result == cg_help.query(question, consumer, catalog_path=catalog)
    evidence = result["evidence"]
    assert all(row["source"] == "docs/installation.md" for row in evidence)
    assert all(row["platform"] in {"all", platform.casefold()} for row in evidence)
    body = "\n".join(row["body"] for row in evidence)
    assert "git clone https://github.com/GPID-WB/compound-gpid.git" in body
    assert ("install.ps1" if platform == "Windows" else "scripts/install.sh") in body
    if configured or platform == "macOS":
        assert any("Step 3" in row["heading"] and "cg-link" in row["body"]
                   for row in evidence)
    assert not any(word in row["heading"].casefold() for row in evidence
                   for word in ("uninstall", "tracking main", "repair", "updating"))
    assert any(row["prerequisites"] for row in evidence)
    if platform == "Windows":
        assert any(row["warnings"] for row in evidence)
    if not configured:
        assert result["state"] == "unknown"
        assert all(row["general_setup"] for row in evidence)
    assert len(cg_help.serialize(result).encode()) <= cg_help.MAX_OUTPUT_BYTES


def test_yaml_decoded_summary_cannot_leak_inactive_research_reference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    consumer = _consumer(tmp_path / "consumer")
    read_source = help_catalog._text

    def escaped_description(root: Path, source: str) -> str:
        """Change only a source fixture in memory; leave canonical files untouched."""
        if source == ".github/prompts/cg-help.prompt.md":
            return '---\ndescription: "Use \\u002fcr-work for research"\n---\n# Help\n'
        return read_source(root, source)

    monkeypatch.setattr(help_catalog, "_text", escaped_description)
    data = help_catalog.build_catalog(ROOT)
    row = next(r for r in data["records"] if r["id"] == "cg-help")
    assert row["summary"] == "Use /cr-work for research"
    assert "suite-cr" in row["required_owners"]
    catalog_path = tmp_path / "escaped.json"
    catalog_path.write_text(json.dumps(data), encoding="utf-8")
    result = cg_help.query("Explain /cg-help", consumer, catalog_path=catalog_path)
    assert "Use /cr-work" not in cg_help.serialize(result)
    assert result["evidence"] == []
    assert all("summary" not in candidate for candidate in result["candidates"])


@pytest.mark.parametrize("configured", [True, False])
def test_inherited_table_heading_cannot_leak_research_to_cg_or_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, configured: bool,
) -> None:
    consumer = tmp_path / "consumer"
    if configured:
        _consumer(consumer)
    else:
        consumer.mkdir()
    read_source = help_catalog._text

    def research_table(root: Path, source: str) -> str:
        """Keep the suite marker only in the inherited heading, not the row."""
        if source == "docs/help/index.md":
            return ("# Help\n\n## /cr-work research\n\n| Task | Procedure |\n"
                    "|---|---|\n| research | Run the research implementation workflow |\n")
        return read_source(root, source)

    monkeypatch.setattr(help_catalog, "_text", research_table)
    data = help_catalog.build_catalog(ROOT)
    catalog_path = tmp_path / "heading.json"
    catalog_path.write_text(json.dumps(data), encoding="utf-8")
    result = cg_help.query("research", consumer, catalog_path=catalog_path)
    assert result["state"] == ("active" if configured else "unknown")
    serialized = cg_help.serialize(result)
    assert "Run the research implementation workflow" not in serialized
    assert "/cr-work research" not in serialized
    rows = [row for row in data["records"]
            if row["source"] == "docs/help/index.md" and row["body"].startswith("|")]
    assert rows
    assert all("suite-cr" in row["required_owners"] for row in rows)
    assert all(not row["general_setup"] for row in rows)


@pytest.mark.parametrize("quote", ['"', "'"])
def test_quoted_unindented_description_continuation_has_full_source_citation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, quote: str,
) -> None:
    read_source = help_catalog._text
    source_text = (f"---\ndescription: {quote}First line\nsecond line{quote}\n"
                   "owner: kernel\n---\n# Help\n")

    def continued_description(root: Path, source: str) -> str:
        """Use the existing parser's valid unindented quoted continuation form."""
        if source == ".github/prompts/cg-help.prompt.md":
            return source_text
        return read_source(root, source)

    monkeypatch.setattr(help_catalog, "_text", continued_description)
    data = help_catalog.build_catalog(ROOT)
    row = next(row for row in data["records"] if row["id"] == "cg-help")
    assert row["summary"] == "First line second line"
    assert row["body"] == f"description: {quote}First line\nsecond line{quote}"
    assert (row["start_line"], row["end_line"]) == (2, 3)
    lines = source_text.splitlines()
    assert row["body"] == "\n".join(lines[row["start_line"] - 1:row["end_line"]])
    consumer = _consumer(tmp_path / "consumer")
    catalog_path = tmp_path / "continued.json"
    catalog_path.write_text(json.dumps(data), encoding="utf-8")
    result = cg_help.query("Explain /cg-help", consumer, catalog_path=catalog_path)
    evidence = next(row for row in result["evidence"] if row["id"] == "cg-help")
    assert evidence["end_line"] == 3 and f"second line{quote}" in evidence["body"]


def test_deeply_nested_catalog_is_bounded_cli_error_without_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture,
) -> None:
    installation = tmp_path / "installation"
    (installation / "scripts").mkdir(parents=True)
    (installation / "scripts/help_catalog.json").write_text(
        "[" * 2000 + "0" + "]" * 2000, encoding="utf-8")
    monkeypatch.setattr(cg_help, "INSTALLATION_ROOT", installation)
    assert cg_help.main(["query", "work", "--root", str(tmp_path)]) == 1
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["status"] == "error" and result["evidence"] == []
    assert "malformed" in result["limitation"]
    assert "Traceback" not in captured.out + captured.err
    assert len(captured.out.encode()) <= cg_help.MAX_OUTPUT_BYTES
