"""Typed optional hooks must never import a profile in generic mode."""

import importlib
from types import SimpleNamespace

import pytest

from cg_release.events import ControllerError


def test_generic_mode_never_loads_profile(monkeypatch):
    from cg_release.hooks import selected_profile

    def deny(*args):
        raise AssertionError("Generic mode imported an extension")

    monkeypatch.setattr(importlib, "import_module", deny)
    assert selected_profile(SimpleNamespace(gpid_profile=None)) is None


def test_profile_is_explicit_and_installed():
    from cg_release.hooks import selected_profile

    profile = selected_profile(SimpleNamespace(gpid_profile="v1"))
    assert profile.VERSION == "v1"
    with pytest.raises(ControllerError):
        selected_profile(SimpleNamespace(gpid_profile="unknown"))


def test_complete_release_routes_only_mutable_docs_refresh(monkeypatch):
    import cg_release.profile_docs as docs
    from cg_release import stage_router

    calls = []
    monkeypatch.setattr(
        docs,
        "docs_step",
        lambda context, record, **kwargs: calls.append(record) or None,
    )
    context = SimpleNamespace(policy=SimpleNamespace(gpid_profile="v1"))
    record = SimpleNamespace(state="complete")
    assert stage_router.advance(context, record) is record
    assert calls == [record]
