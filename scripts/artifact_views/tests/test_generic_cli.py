"""Tests for the generic one-file publication CLI and ownership lifecycle."""
from __future__ import annotations

# pylint: disable=import-error

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from artifact_views import generic_cli
from artifact_views.provenance import PublicationProvenance
from artifact_views.tests.test_publishing_security import PNG

SOURCE = Path("docs/guide.md")
OUTPUT = Path(".cg-docs/views/documents/docs/guide.html")
FIXED_TIME = datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc)


def _project(tmp_path: Path, *, automatic: bool = True) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "compound-gpid.md").write_text("# Project\n", encoding="utf-8")
    (root / "compound-gpid.local.md").write_text(
        f"---\nartifact-html: {str(automatic).lower()}\n---\n",
        encoding="utf-8",
    )
    source = root / SOURCE
    source.parent.mkdir(parents=True)
    source.write_text("# Guide\n\n## Section\n\nBounded content.\n", encoding="utf-8")
    return root


def _run(root: Path, arguments: list[str], capsys) -> tuple[int, str, str]:
    result = generic_cli.main(
        ["--root", str(root), *arguments],
        now=FIXED_TIME,
    )
    captured = capsys.readouterr()
    return result, captured.out, captured.err


def _provenance(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    marker = '<script id="artifact-provenance" type="application/json">'
    return json.loads(text.split(marker, 1)[1].split("</script>", 1)[0])


def test_generic_render_writes_owned_schema_2_view(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    root = _project(tmp_path)

    result, stdout, stderr = _run(root, [str(SOURCE)], capsys)

    assert result == 0
    assert stdout == f"{OUTPUT.as_posix()}\n"
    assert stderr == ""
    provenance = _provenance(root / OUTPUT)
    assert provenance["provenanceSchemaVersion"] == 2
    assert provenance["sourcePath"] == SOURCE.as_posix()
    assert provenance["outputPath"] == OUTPUT.as_posix()
    assert provenance["documentType"] == "generic-markdown"
    assert provenance["themeName"] == "reference"
    assert provenance["themeVersion"] == 1


def test_validate_only_and_disabled_automatic_do_not_inspect_or_write_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    root = _project(tmp_path, automatic=False)
    output = root / OUTPUT
    output.parent.mkdir(parents=True)
    output.write_bytes(b"corrupt existing bytes")

    result, stdout, stderr = _run(
        root,
        ["--validate-only", "--theme", "reference", str(SOURCE)],
        capsys,
    )
    assert result == 0
    assert stdout == f"Validated {SOURCE.as_posix()}\n"
    assert stderr == ""
    assert output.read_bytes() == b"corrupt existing bytes"

    result, stdout, stderr = _run(root, ["--automatic", str(SOURCE)], capsys)
    assert result == 0
    assert stdout == f"HTML disabled; validated {SOURCE.as_posix()}\n"
    assert stderr == ""
    assert output.read_bytes() == b"corrupt existing bytes"


def test_generic_check_reports_missing_current_and_stale(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    root = _project(tmp_path)

    assert _run(root, ["--check", str(SOURCE)], capsys)[:2] == (
        1,
        f"missing {OUTPUT.as_posix()}\n",
    )
    assert _run(root, [str(SOURCE)], capsys)[0] == 0
    assert _run(root, ["--check", str(SOURCE)], capsys)[:2] == (
        0,
        f"current {OUTPUT.as_posix()}\n",
    )
    (root / SOURCE).write_text("# Guide\n\nChanged.\n", encoding="utf-8")
    assert _run(root, ["--check", str(SOURCE)], capsys)[:2] == (
        1,
        f"stale {OUTPUT.as_posix()}\n",
    )


@pytest.mark.parametrize(
    "content",
    (
        b"corrupt output",
        b'<script id="artifact-provenance" type="application/json">{bad}</script>',
        b'<script id="artifact-provenance" type="application/json">{}</script>',
    ),
)
def test_check_classifies_corrupt_output_as_stale(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
    content: bytes,
) -> None:
    root = _project(tmp_path)
    output = root / OUTPUT
    output.parent.mkdir(parents=True)
    output.write_bytes(content)

    result, stdout, stderr = _run(root, ["--check", str(SOURCE)], capsys)

    assert result == 1
    assert stdout == f"stale {OUTPUT.as_posix()}\n"
    assert stderr == ""
    assert output.read_bytes() == content


def test_check_with_explicit_theme_classifies_foreign_owner_as_stale(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    root = _project(tmp_path)
    output = root / OUTPUT
    output.parent.mkdir(parents=True)
    foreign = PublicationProvenance.from_source(
        source_path=Path("docs/other.md"),
        source_bytes=b"# Other\n",
        output_path=OUTPUT,
        document_type="generic-markdown",
        renderer_version="0.2.0",
        theme_name="reference",
        theme_version=1,
        generated_at=FIXED_TIME,
    )
    output.write_text(
        '<script id="artifact-provenance" type="application/json">'
        f"{foreign.to_json()}</script>",
        encoding="utf-8",
    )

    result, stdout, stderr = _run(
        root,
        ["--check", "--theme", "reference", str(SOURCE)],
        capsys,
    )

    assert result == 1
    assert stdout == f"stale {OUTPUT.as_posix()}\n"
    assert stderr == ""


def test_check_classifies_oversize_duplicate_and_unknown_theme_as_stale(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _project(tmp_path)
    output = root / OUTPUT
    output.parent.mkdir(parents=True)

    monkeypatch.setattr(generic_cli, "_MAX_VIEW_BYTES", 8)
    output.write_bytes(b"123456789")
    assert _run(root, ["--check", str(SOURCE)], capsys)[:2] == (
        1,
        f"stale {OUTPUT.as_posix()}\n",
    )

    monkeypatch.setattr(generic_cli, "_MAX_VIEW_BYTES", 32 * 1024 * 1024)
    duplicate = PublicationProvenance.from_source(
        source_path=SOURCE,
        source_bytes=(root / SOURCE).read_bytes(),
        output_path=OUTPUT,
        document_type="generic-markdown",
        renderer_version="0.2.0",
        theme_name="reference",
        theme_version=1,
        generated_at=FIXED_TIME,
    ).to_json()
    marker = '<script id="artifact-provenance" type="application/json">'
    output.write_text(
        f"{marker}{duplicate}</script>{marker}{duplicate}</script>",
        encoding="utf-8",
    )
    assert _run(root, ["--check", str(SOURCE)], capsys)[:2] == (
        1,
        f"stale {OUTPUT.as_posix()}\n",
    )

    unknown = PublicationProvenance(
        **{
            **PublicationProvenance.from_source(
                source_path=SOURCE,
                source_bytes=(root / SOURCE).read_bytes(),
                output_path=OUTPUT,
                document_type="generic-markdown",
                renderer_version="0.2.0",
                theme_name="reference",
                theme_version=1,
                generated_at=FIXED_TIME,
            ).__dict__,
            "theme_name": "removed-theme",
        }
    )
    output.write_text(f"{marker}{unknown.to_json()}</script>", encoding="utf-8")
    assert _run(root, ["--check", str(SOURCE)], capsys)[:2] == (
        1,
        f"stale {OUTPUT.as_posix()}\n",
    )


def test_unowned_destination_fails_without_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    root = _project(tmp_path)
    output = root / OUTPUT
    output.parent.mkdir(parents=True)
    output.write_bytes(b"concurrent owner")

    result, stdout, stderr = _run(root, [str(SOURCE)], capsys)

    assert result == 1
    assert stdout == ""
    assert "owner|provenance".replace("|", "") not in stderr
    assert "owner" in stderr.lower() or "provenance" in stderr.lower()
    assert output.read_bytes() == b"concurrent owner"


def test_destination_created_after_authorization_is_not_overwritten(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _project(tmp_path)
    output = root / OUTPUT
    original_write = generic_cli.write_view

    def insert_concurrent_owner(*args, **kwargs):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"late concurrent owner")
        return original_write(*args, **kwargs)

    monkeypatch.setattr(generic_cli, "write_view", insert_concurrent_owner)

    result, _, stderr = _run(root, [str(SOURCE)], capsys)

    assert result == 1
    assert "changed after authorization" in stderr.lower()
    assert output.read_bytes() == b"late concurrent owner"


def test_owned_destination_replaced_after_authorization_is_not_overwritten(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _project(tmp_path)
    assert _run(root, [str(SOURCE)], capsys)[0] == 0
    output = root / OUTPUT
    original_write = generic_cli.write_view

    def replace_authorized_owner(*args, **kwargs):
        output.write_bytes(b"late replacement")
        return original_write(*args, **kwargs)

    monkeypatch.setattr(generic_cli, "write_view", replace_authorized_owner)

    result, _, stderr = _run(root, [str(SOURCE)], capsys)

    assert result == 1
    assert "changed after authorization" in stderr.lower()
    assert output.read_bytes() == b"late replacement"


def test_different_owner_and_output_identity_are_preserved(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    root = _project(tmp_path)
    output = root / OUTPUT
    output.parent.mkdir(parents=True)
    provenance = PublicationProvenance.from_source(
        source_path=Path("docs/other.md"),
        source_bytes=b"# Other\n",
        output_path=OUTPUT,
        document_type="generic-markdown",
        renderer_version="0.1.0",
        theme_name="reference",
        theme_version=1,
        generated_at=FIXED_TIME,
    )
    payload = provenance.to_json()
    original = (
        '<script id="artifact-provenance" type="application/json">'
        f"{payload}</script>"
    ).encode("utf-8")
    output.write_bytes(original)

    result, _, stderr = _run(root, [str(SOURCE)], capsys)

    assert result == 1
    assert "different source" in stderr.lower()
    assert output.read_bytes() == original


def test_explicit_output_and_theme_are_validated(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    root = _project(tmp_path)
    custom = Path(".cg-docs/views/documents/custom/view.html")

    result, stdout, _ = _run(
        root,
        ["--theme", "reference", "--output", str(custom), str(SOURCE)],
        capsys,
    )

    assert result == 0
    assert stdout == f"{custom.as_posix()}\n"
    assert _provenance(root / custom)["outputPath"] == custom.as_posix()

    result, _, stderr = _run(
        root,
        ["--validate-only", "--theme", "unknown", str(SOURCE)],
        capsys,
    )
    assert result == 2
    assert "unknown theme" in stderr.lower()


def test_help_explains_modes_ownership_defaults_and_exit_codes(
    capsys: pytest.CaptureFixture,
) -> None:
    assert generic_cli.main(["--help"]) == 0
    help_text = capsys.readouterr().out

    for term in (
        "--automatic",
        "--validate-only",
        "--check",
        "--theme",
        "--output",
        ".cg-docs/views/documents",
        "ownership",
        "exit code",
    ):
        assert term in help_text


def test_recovery_preserves_custom_output_and_explicit_theme(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    root = _project(tmp_path)
    custom = Path(".cg-docs/views/documents/custom/view.html")
    output = root / custom
    output.parent.mkdir(parents=True)
    output.write_bytes(b"unowned")

    result, _, stderr = _run(
        root,
        ["--theme", "reference", "--output", str(custom), str(SOURCE)],
        capsys,
    )

    assert result == 1
    assert "--theme reference" in stderr
    assert f"--output {custom.as_posix()}" in stderr


def test_invalid_source_and_resource_return_input_exit_code(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    root = _project(tmp_path)
    (root / SOURCE).write_bytes(b"\xff")
    assert _run(root, [str(SOURCE)], capsys)[0] == 2

    (root / SOURCE).write_text(
        "# Guide\n\n![Missing](assets/missing.png)\n",
        encoding="utf-8",
    )
    assert _run(root, ["--validate-only", str(SOURCE)], capsys)[0] == 2


def test_typed_root_is_rejected_with_strict_recovery(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    root = _project(tmp_path)
    typed = root / ".cg-docs/plans/example.md"
    typed.parent.mkdir(parents=True)
    typed.write_text("# Plan\n", encoding="utf-8")

    result, _, stderr = _run(
        root,
        [str(typed.relative_to(root))],
        capsys,
    )

    assert result == 2
    assert "cg-render-artifact" in stderr


def test_generic_render_embeds_local_image(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    root = _project(tmp_path)
    image = root / "docs/assets/figure.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(PNG)
    (root / SOURCE).write_text(
        "# Guide\n\n![Figure](assets/figure.png)\n",
        encoding="utf-8",
    )

    assert _run(root, [str(SOURCE)], capsys)[0] == 0
    assert "data:image/png;base64," in (root / OUTPUT).read_text(encoding="utf-8")