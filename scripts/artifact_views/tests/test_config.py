"""Tests for secure project-local artifact publication configuration."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from artifact_views import config  # pylint: disable=import-error


def test_missing_config_defaults_to_disabled(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()

    result = config.load_artifact_view_config(root)

    assert result.automatic_html is False
    assert result.warning is None


def test_missing_artifact_html_field_defaults_to_disabled(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "compound-gpid.local.md").write_text(
        "---\nlanguage: python\n---\n",
        encoding="utf-8",
    )

    result = config.load_artifact_view_config(root)

    assert result.automatic_html is False
    assert result.warning is None


def test_explicit_true_enables_automatic_html(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "compound-gpid.local.md").write_text(
        "---\nartifact-html: true\n---\n",
        encoding="utf-8",
    )

    result = config.load_artifact_view_config(root)

    assert result.automatic_html is True
    assert result.warning is None


@pytest.mark.parametrize(
    "value",
    ("sometimes", "null", "~"),
    ids=("text", "null", "tilde"),
)
def test_invalid_artifact_html_defaults_to_disabled_with_warning(
    tmp_path: Path,
    value: str,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "compound-gpid.local.md").write_text(
        f"---\nartifact-html: {value}\n---\n",
        encoding="utf-8",
    )

    result = config.load_artifact_view_config(root)

    assert result.automatic_html is False
    assert result.warning is not None
    assert "defaulting disabled" in result.warning.lower()


def test_config_uses_bounded_secure_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "compound-gpid.local.md").write_text(
        "---\nartifact-html: false\n---\n",
        encoding="utf-8",
    )
    observed = {}
    original_read = config.secure_read_bytes

    def observe(root_path, relative_path, **kwargs):
        observed.update(kwargs)
        return original_read(root_path, relative_path, **kwargs)

    monkeypatch.setattr(config, "secure_read_bytes", observe)

    result = config.load_artifact_view_config(root)

    assert result.automatic_html is False
    assert observed["reject_hardlinks"] is True
    assert observed["max_bytes"] > 0


def test_unsafe_config_identity_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    config_path = root / "compound-gpid.local.md"
    config_path.write_text("---\nartifact-html: false\n---\n", encoding="utf-8")
    alias = root / "alias.md"
    os.link(config_path, alias)

    with pytest.raises(OSError, match="multiple hard links"):
        config.load_artifact_view_config(root)


@pytest.mark.usefixtures("require_symlink_support")
def test_config_final_component_swap_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    policy = root / "compound-gpid.local.md"
    policy.write_text("---\nartifact-html: false\n---\n", encoding="utf-8")
    outside = tmp_path / "outside.md"
    outside.write_text("---\nartifact-html: true\n---\n", encoding="utf-8")
    original_read = config.secure_read_bytes

    def swap_then_read(root_path, relative_path, **kwargs):
        def swap(_path: Path) -> None:
            policy.unlink()
            policy.symlink_to(outside)

        return original_read(root_path, relative_path, before_open=swap, **kwargs)

    monkeypatch.setattr(config, "secure_read_bytes", swap_then_read)

    with pytest.raises(OSError):
        config.load_artifact_view_config(root)