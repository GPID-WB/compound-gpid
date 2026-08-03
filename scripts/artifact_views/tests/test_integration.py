"""End-to-end failure-preservation and dependency-isolation tests."""
from __future__ import annotations

# pylint: disable=import-error

import json
from pathlib import Path
import shutil

import pytest

from artifact_views import cli
from artifact_views.provenance import source_sha256

FIXTURES = Path(__file__).parent / "fixtures"
SOURCE_RELATIVE = Path(".cg-docs/plans/integration.md")
VIEW_RELATIVE = Path(".cg-docs/views/plans/integration.html")


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "compound-gpid.md").write_text("# Project\n", encoding="utf-8")
    (root / "compound-gpid.local.md").write_text("---\nartifact-html: true\n---\n", encoding="utf-8")
    source = root / SOURCE_RELATIVE
    source.parent.mkdir(parents=True)
    shutil.copyfile(FIXTURES / "strict_plan.md", source)
    return root


def _provenance(view: Path) -> dict:
    text = view.read_text(encoding="utf-8")
    marker = '<script id="artifact-provenance" type="application/json">'
    payload = text.split(marker, 1)[1].split("</script>", 1)[0]
    return json.loads(payload)


def test_end_to_end_render_provenance_and_stale_check(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    root = _project(tmp_path)
    source = root / SOURCE_RELATIVE

    assert cli.main(["--root", str(root), str(SOURCE_RELATIVE)]) == 0
    capsys.readouterr()
    view = root / VIEW_RELATIVE
    provenance = _provenance(view)
    assert provenance["sourcePath"] == SOURCE_RELATIVE.as_posix()
    assert provenance["sourceSha256"] == source_sha256(source.read_bytes())
    assert cli.main(["--root", str(root), "--check", str(SOURCE_RELATIVE)]) == 0


def test_renderer_failure_preserves_source_and_prior_view(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _project(tmp_path)
    assert cli.main(["--root", str(root), str(SOURCE_RELATIVE)]) == 0
    capsys.readouterr()
    source = root / SOURCE_RELATIVE
    view = root / VIEW_RELATIVE
    source_before = source.read_bytes()
    view_before = view.read_bytes()

    def fail_render(*_args, **_kwargs):
        raise RuntimeError("injected renderer failure")

    monkeypatch.setattr(cli, "render_document", fail_render)
    assert cli.main(["--root", str(root), str(SOURCE_RELATIVE)]) == 1
    captured = capsys.readouterr()

    assert "injected renderer failure" in captured.err
    assert "(stale)" in captured.err
    assert source.read_bytes() == source_before
    assert view.read_bytes() == view_before


def test_writer_failure_preserves_source_and_prior_view(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _project(tmp_path)
    assert cli.main(["--root", str(root), str(SOURCE_RELATIVE)]) == 0
    capsys.readouterr()
    source = root / SOURCE_RELATIVE
    view = root / VIEW_RELATIVE
    source_before = source.read_bytes()
    view_before = view.read_bytes()

    def fail_write(*_args, **_kwargs):
        raise OSError("injected write failure")

    monkeypatch.setattr(cli, "write_view", fail_write)
    assert cli.main(["--root", str(root), str(SOURCE_RELATIVE)]) == 1
    captured = capsys.readouterr()

    assert "injected write failure" in captured.err
    assert source.read_bytes() == source_before
    assert view.read_bytes() == view_before


def test_runtime_modules_have_no_model_network_or_subprocess_dependency() -> None:
    runtime_files = [
        Path(cli.__file__),
        Path(cli.__file__).with_name("validator.py"),
        Path(cli.__file__).with_name("renderer.py"),
        Path(cli.__file__).with_name("writer.py"),
        Path(cli.__file__).with_name("generic_cli.py"),
        Path(cli.__file__).with_name("generic_model.py"),
        Path(cli.__file__).with_name("generic_parser.py"),
        Path(cli.__file__).with_name("generic_renderer.py"),
        Path(cli.__file__).with_name("paths.py"),
        Path(cli.__file__).with_name("provenance.py"),
        Path(cli.__file__).with_name("publishing.py"),
        Path(cli.__file__).with_name("reference_theme.py"),
        Path(cli.__file__).with_name("security.py"),
        Path(cli.__file__).with_name("templates.py"),
        Path(cli.__file__).with_name("themes.py"),
    ]
    forbidden = (
        "subprocess",
        "urllib.request",
        "httpx",
        "requests",
        "openai",
        "anthropic",
        "playwright",
        "selenium",
        "open_design",
    )

    for path in runtime_files:
        source = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert f"import {token}" not in source
            assert f"from {token}" not in source


def test_view_only_sentinel_never_enters_brain_or_context_audit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import cg_audit_context as audit
    from brain.scanner import scan_all

    sentinel = "VIEW_ONLY_SENTINEL_7E5C9A"
    view = tmp_path / ".cg-docs/views/plans/sentinel.html"
    view.parent.mkdir(parents=True)
    view.write_text(f"<html><body>{sentinel}</body></html>", encoding="utf-8")
    monkeypatch.setattr(audit, "SCAN_CATEGORIES", {"all": ".cg-docs/**/*"})

    entities = scan_all(tmp_path)
    files, _ = audit.scan_files(tmp_path)
    duplicates = audit.detect_duplicates(tmp_path, files)

    assert sentinel not in "\n".join(entity.text for entity in entities)
    assert sentinel not in json.dumps(files)
    assert sentinel not in json.dumps(duplicates)


def test_generic_view_only_sentinel_never_enters_model_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import cg_audit_context as audit
    from brain.scanner import scan_all

    sentinel = "GENERIC_VIEW_ONLY_SENTINEL_3A9D"
    view = tmp_path / ".cg-docs/views/documents/docs/guide.html"
    view.parent.mkdir(parents=True)
    view.write_text(f"<html><body>{sentinel}</body></html>", encoding="utf-8")
    monkeypatch.setattr(audit, "SCAN_CATEGORIES", {"all": ".cg-docs/**/*"})

    entities = scan_all(tmp_path)
    files, _ = audit.scan_files(tmp_path)
    duplicates = audit.detect_duplicates(tmp_path, files)

    assert sentinel not in "\n".join(entity.text for entity in entities)
    assert sentinel not in json.dumps(files)
    assert sentinel not in json.dumps(duplicates)
