"""Disabled publisher template keeps pre-approval evidence and secret jobs separate."""

from pathlib import Path


def test_publish_template_separates_seal_and_gate():
    raw = (Path(__file__).parents[1] / "templates/publish.yml").read_text()
    seal, publisher = raw.split("  publish:", 1)
    assert "environment: release-control" in seal
    assert "RELEASE_PUBLISHING_APP_PRIVATE_KEY" not in seal
    assert "RELEASE_SIGNING_PRIVATE_KEY" not in seal
    assert "needs: seal" in publisher
    assert "url: ${{ needs.seal.outputs.evidence_url }}" in publisher
    assert "name: ${{ needs.seal.outputs.environment }}" in publisher
    assert (
        "CG_RELEASE_CONTROL_TOKEN" in publisher
        and "CG_RELEASE_PUBLISHING_TOKEN" in publisher
    )
    assert "github.run_attempt == 1" in seal and "github.run_attempt == 1" in publisher
    assert "false &&" in seal
    assert (
        "persist-credentials: false" in seal
        and "persist-credentials: false" in publisher
    )
    assert "permission-workflows: write" in publisher
    assert "-I -m cg_release.publish_worker seal" in seal
    assert "-I -m cg_release.publish_worker publish" in publisher
    assert "pull_request_target" not in raw and "actions/cache" not in raw
