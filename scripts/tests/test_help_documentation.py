"""Behavioral contracts for the canonical catalog-owned documentation writer."""
import importlib
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def writer():
    return importlib.import_module("help.documentation")


@pytest.fixture
def source(tmp_path):
    root = tmp_path / "source"
    for name in [".github", "docs", "scripts", "bin"]:
        shutil.copytree(ROOT / name, root / name)
    shutil.copyfile(ROOT / "install.ps1", root / "install.ps1")
    return root


def test_explicit_bootstrap_and_repeated_generation_preserve_editorial_bytes(source):
    doc = writer()
    # The committed bootstrap fixture is independent of later generated output.
    for name in doc.TARGETS:
        shutil.copyfile(ROOT / "scripts/tests/fixtures/help-docs" / name,
                        source / "docs" / name)
    before = {name: doc.editorial((source / "docs" / name).read_text()) for name in doc.TARGETS}
    with pytest.raises(ValueError, match="marker"):
        doc.expected_documents(source)
    assert doc.bootstrap(source)["status"] == "bootstrapped"
    first = {name: (source / "docs" / name).read_bytes() for name in doc.TARGETS}
    assert doc.bootstrap(source)["status"] == "already-bootstrapped"
    assert first == {name: (source / "docs" / name).read_bytes() for name in doc.TARGETS}
    doc.write_documents(source)
    doc.check_documents(source)
    assert doc.write_documents(source) == []
    for name in doc.TARGETS:
        assert doc.editorial((source / "docs" / name).read_text()) == before[name]


def test_stale_catalog_and_duplicate_markers_fail_without_writes(source):
    doc = writer()
    doc.bootstrap(source)
    target = source / "docs/reference.md"
    target.write_text(target.read_text() + "\n<!-- cg:auto:help-commands -->\nx\n<!-- cg:auto:end -->\n")
    before = target.read_bytes()
    with pytest.raises(ValueError, match="duplicate"):
        doc.write_documents(source)
    assert target.read_bytes() == before
    catalog = source / ".github/shared/help-catalog.json"
    catalog.write_text(catalog.read_text().replace('"generatorVersion": "1.0.0"', '"generatorVersion": "stale"'))
    with pytest.raises(Exception, match="catalog|generator"):
        doc.expected_documents(source)


def test_ambiguous_bootstrap_refuses_all_mutation(source):
    doc = writer()
    for name in doc.TARGETS:
        shutil.copyfile(ROOT / "scripts/tests/fixtures/help-docs" / name,
                        source / "docs" / name)
    target = source / "docs/reference/commands.md"
    target.write_text(target.read_text().replace("## Shell commands", "## Renamed shell commands"))
    before = {name: (source / "docs" / name).read_bytes() for name in doc.TARGETS}
    with pytest.raises(ValueError, match="legacy|bootstrap"):
        doc.bootstrap(source)
    assert before == {name: (source / "docs" / name).read_bytes() for name in doc.TARGETS}


def test_display_text_is_inert_and_shared_slash_commands_use_supported_suites():
    doc = writer()
    row = {"id": "slash:cg-help", "kind": "slash", "name": "/cg-help",
           "usage": "/cg-help `<script>|x", "summary": "<img> [x](javascript:bad)",
           "supportedSuites": ["cg", "cr"]}
    for section in ["help-commands", "help-research-commands"]:
        rendered = doc.render_table({"commands": [row]}, section)
        assert "&lt;script&gt;" in rendered and "<img>" not in rendered
        assert "CG, CR" in rendered and "javascript:bad)" not in rendered


def test_wiki_ownership_conflict_fails_before_document_mutation(source):
    doc = writer()
    file = source / "docs/_wiki.yml"
    file.write_text(file.read_text().replace('generator: "help-catalog"', 'generator: "wiki"', 1))
    before = {name: (source / "docs" / name).read_bytes() for name in doc.TARGETS}
    with pytest.raises(ValueError, match="owner"):
        doc.write_documents(source)
    assert before == {name: (source / "docs" / name).read_bytes() for name in doc.TARGETS}
