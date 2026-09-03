"""Byte-preserving strict capability editor tests."""
from __future__ import annotations

import pytest

from skill_management.services.config_editor import ConfigEditError, plan_capability_edit


def test_add_preserves_crlf_comments_quotes_order_and_body() -> None:
    before = (
        b"---\r\n"
        b'language: "r"\r\n'
        b"capabilities: ['python']  # explicit\r\n"
        b'review-depth: "standard"\r\n'
        b"---\r\n# Body\r\n"
    )

    edit = plan_capability_edit(before, "project-skill-demo", activate=True)

    assert edit.after == before.replace(
        b"['python']", b"['python', project-skill-demo]"
    )
    assert edit.before_digest != edit.after_digest


def test_insert_absent_field_before_closing_delimiter_with_original_newline() -> None:
    before = b'---\nlanguage: "r"\n---\n# Body\n'
    edit = plan_capability_edit(before, "project-skill-demo", activate=True)
    assert edit.after == (
        b'---\nlanguage: "r"\ncapabilities: [project-skill-demo]\n---\n# Body\n'
    )


def test_remove_only_requested_explicit_value_and_noop_is_byte_identical() -> None:
    before = b"---\nsuites: [cg]\ncapabilities: [python, project-skill-demo]\n---\n"
    edit = plan_capability_edit(before, "project-skill-demo", activate=False)
    assert edit.after == b"---\nsuites: [cg]\ncapabilities: [python]\n---\n"
    noop = plan_capability_edit(edit.after, "project-skill-demo", activate=False)
    assert noop.after == edit.after
    assert not noop.changed


@pytest.mark.parametrize(
    "content",
    [
        b"---\ncapabilities:\n  - python\n---\n",
        b"---\ncapabilities: [python]\ncapabilities: [r]\n---\n",
        b"\xef\xbb\xbf---\ncapabilities: [python]\n---\n",
    ],
)
def test_block_duplicate_or_bom_config_fails_closed(content: bytes) -> None:
    with pytest.raises(ConfigEditError):
        plan_capability_edit(content, "project-skill-demo", activate=True)
