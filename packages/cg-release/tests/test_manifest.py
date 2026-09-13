"""P1.5: every returned manifest must satisfy the reader and reapply exactly."""

import json
from dataclasses import replace

import pytest
from test_preview import snapshot

from cg_release.cli import parse_args
from cg_release.events import ControllerError
from cg_release.manifest import validate_manifest
from cg_release.metadata import SourceBlob, proposed_edits
from cg_release.models import Policy, canonical_bytes, load_record
from cg_release.policy import validate_policy
from cg_release.preview import create_proposal


@pytest.mark.parametrize("second_path", ["dist/package.whl", "DIST/Package.whl"])
def test_duplicate_output_paths_fail_in_policy_and_first_proposal(
    second_path: str,
) -> None:
    state = snapshot()
    data = json.loads(state.policy_raw)
    data["build"]["max_artifacts"] = 2
    data["build"]["artifacts"].append(
        {**data["build"]["artifacts"][0], "name": "other.whl", "path": second_path}
    )
    state = replace(state, policy_raw=canonical_bytes(data))
    with pytest.raises(ControllerError) as error:
        validate_policy(
            load_record(Policy, state.policy_raw), repository_id=123, host="github.com"
        )
    assert error.value.code == "E_POLICY"
    with pytest.raises(ControllerError) as error:
        create_proposal(state, parse_args(["plan", "--version", "1.0.0"]))
    assert error.value.code == "E_POLICY"


@pytest.mark.parametrize("tag_length", [256, 260])
def test_combined_tag_limit_is_enforced_before_returning_a_proposal(
    tag_length: int,
) -> None:
    state = snapshot()
    data = json.loads(state.policy_raw)
    data["tag_prefix"] = "v" * 64
    state = replace(state, policy_raw=canonical_bytes(data))
    version = "1.0.0-" + "a" * (tag_length - 70)
    with pytest.raises(ControllerError) as error:
        create_proposal(state, parse_args(["plan", "--version", version]))
    assert error.value.code == "E_REF"


@pytest.mark.parametrize("tag_length", [254, 255])
def test_accepted_tag_boundary_and_distinct_outputs_reapply_exactly(
    tag_length: int,
) -> None:
    state = snapshot()
    data = json.loads(state.policy_raw)
    data["tag_prefix"] = "v" * 64
    data["build"]["max_artifacts"] = 2
    data["build"]["artifacts"].append(
        {**data["build"]["artifacts"][0], "name": "other.whl", "path": "dist/other.whl"}
    )
    state = replace(state, policy_raw=canonical_bytes(data))
    args = parse_args(["plan", "--version", "1.0.0-" + "a" * (tag_length - 70)])
    first = create_proposal(state, args)
    assert len(first.tag) == tag_length
    manifest = next(e for e in first.edits if e.path == ".release-manifest.json")
    assert validate_manifest(manifest.content).outputs == [
        "dist/package.whl",
        "dist/other.whl",
    ]
    reapplied = replace(
        state,
        blobs={**state.blobs, **{e.path: SourceBlob(e.content) for e in first.edits}},
    )
    again = create_proposal(reapplied, args)
    assert [(e.path, e.content) for e in again.edits] == [
        (e.path, e.content) for e in first.edits
    ]
    validate_manifest(
        next(e.content for e in again.edits if e.path == ".release-manifest.json")
    )


@pytest.mark.parametrize(
    "change",
    [
        {"outputs": ["dist/package.whl", "dist/package.whl"]},
        {"outputs": ["dist/package.whl", "DIST/Package.whl"]},
        {"tag": "v" * 255 + "1.0.0"},
        {"source_sha": "invalid"},
        {"line": ""},
        {"request_id": ""},
        {"outputs": ["../outside"]},
    ],
)
def test_direct_edit_producer_validates_generated_manifest(change: dict) -> None:
    state = snapshot()
    policy = load_record(Policy, state.policy_raw)
    kwargs = dict(
        version="1.0.0",
        tag="v1.0.0",
        line="current",
        source_sha=state.source_sha,
        policy_digest="b" * 64,
        request_id="preview-not-submitted",
        notes=state.notes,
        projections_history={},
        outputs=["dist/package.whl"],
    )
    kwargs.update(change)
    with pytest.raises(ControllerError) as error:
        proposed_edits(policy.metadata, policy.changelog, state.blobs, **kwargs)
    assert error.value.code == "E_MANIFEST"
