"""Actual qualifier artifact boundaries, not successful arbitrary reader jobs."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from profile_transport import ProfileTransport

from cg_release.events import ControllerError
from cg_release.github import GitHubReads


def test_successful_synthetic_reader_jobs_are_not_bridge_delivery(
    tmp_path, monkeypatch
):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[3] / "scripts"))
    import release_profile_gpid

    world = ProfileTransport(tmp_path)
    # This is the former evidence: a successful reader job but no real qualifier steps.
    from profile_bridge_fixture import wire

    world.get = (
        lambda original: (
            lambda endpoint, **kwargs: (
                {
                    "total_count": 1,
                    "jobs": [{**wire(world, endpoint)["jobs"][0], "steps": []}],
                }
                if endpoint.endswith("jobs") and endpoint.split("/")[2] in {"91", "92"}
                else original(endpoint, **kwargs)
            )
        )
    )(world.get)
    api = GitHubReads(world.host, world.slug, cwd=tmp_path, runner=world.run)
    with pytest.raises(ControllerError, match="bridge|Bridge"):
        release_profile_gpid.verify_bridge(api, world.policy)


def test_actual_qualifier_refuses_without_explicit_authorization(tmp_path):
    from cg_release.bridge_qualifier import qualify

    with pytest.raises(ControllerError, match="authorization"):
        qualify(SimpleNamespace(), tmp_path, {}, authorized=False)
    assert list(tmp_path.iterdir()) == []
