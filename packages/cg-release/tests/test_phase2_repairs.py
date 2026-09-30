"""Regressions for the seven independently reported Phase 2 review findings."""

import json
from pathlib import Path
from urllib.parse import unquote

import pytest
from test_metadata import edits
from test_preview import snapshot
from test_source import Remote, acquire

from cg_release import cli, source
from cg_release.cli import parse_args
from cg_release.events import ControllerError
from cg_release.github import GitHubReads
from cg_release.metadata import SourceBlob
from cg_release.preview import create_proposal


@pytest.mark.parametrize(
    "number", ["1e-1000", "1e400", "0.12345678901234567890123456789", "-0.0"]
)
def test_json_numbers_and_surrounding_bytes_do_not_change(number: str) -> None:
    raw = (
        '{ "version" : "1.4.2", "nested": [ ' + number + ', {"other":true}] }'
    ).encode()
    output = next(e.content for e in edits("json", raw) if e.path == "metadata")
    assert output == raw.replace(b'"1.4.2"', b'"1.5.0"')


def test_json_overflow_literal_is_preserved_through_cli(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    state = snapshot()
    state.blobs["package.json"] = SourceBlob(b'{"version":"0.9.0","value":1e400}')
    monkeypatch.setattr(cli, "acquire_snapshot", lambda *_a, **_k: state)
    assert cli.main(["plan", "--version", "1.0.0", "--json"]) == 0
    output = capsys.readouterr()
    assert json.loads(output.out)["kind"] == "preview" and "Traceback" not in output.err


def test_json_token_edit_handles_escaped_keys_and_array_indices() -> None:
    from cg_release.json_edit import edit_json_string

    raw = '{"a/b":{"~key":[{"version":"1.0.0"}]},"n":1e400,"s":"1.0.0"}'
    expected = raw.replace('"version":"1.0.0"', '"version":"1.1.0"')
    assert edit_json_string(raw, "/a~1b/~0key/0/version", "1.1.0") == expected
    for pointer in ("/n", "/absent", "/a~1b/~0key/00/version"):
        with pytest.raises(ControllerError):
            edit_json_string(raw, pointer, "1.1.0")


@pytest.mark.parametrize(
    "raw", [b'{"version":"0.9.0","x":NaN}', b'{"version":"0.9.0","x":1,"x":2}']
)
def test_invalid_json_is_a_typed_cli_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture, raw: bytes
) -> None:
    state = snapshot()
    state.blobs["package.json"] = SourceBlob(raw)
    monkeypatch.setattr(cli, "acquire_snapshot", lambda *_a, **_k: state)
    assert cli.main(["plan", "--version", "1.0.0", "--json"]) == 2
    output = capsys.readouterr()
    assert (
        json.loads(output.out)["code"] == "E_METADATA" and "Traceback" not in output.err
    )


@pytest.mark.parametrize(
    "raw",
    [
        b"not JSON",
        b'{"schema_version":2}',
        b'{"schema_version":1,"schema_version":1}',
        b"[]",
        b'{"schema_version":1,"version":"1.0.0"}',
    ],
)
def test_invalid_existing_manifest_never_becomes_a_validated_edit(raw: bytes) -> None:
    state = snapshot()
    state.blobs[".release-manifest.json"] = SourceBlob(raw)
    with pytest.raises(ControllerError):
        create_proposal(state, parse_args(["plan", "--version", "1.0.0"]))


def test_supported_prior_manifest_and_unknown_fields() -> None:
    args = parse_args(["plan", "--version", "1.0.0"])
    original = create_proposal(snapshot(), args)
    manifest = next(
        e.content for e in original.edits if e.path == ".release-manifest.json"
    )
    state = snapshot()
    state.blobs[".release-manifest.json"] = SourceBlob(manifest)
    assert create_proposal(state, args).version == "1.0.0"
    for change in (
        {"unexpected": 1},
        {"outputs": "not-a-list"},
        {"source_sha": "bad"},
        {"version": "invalid"},
        {"outputs": ["../outside"]},
        {"projections": {"x": 7}},
    ):
        data = json.loads(manifest)
        data.update(change)
        state.blobs[".release-manifest.json"] = SourceBlob(json.dumps(data).encode())
        with pytest.raises(ControllerError):
            create_proposal(state, args)


@pytest.mark.parametrize(
    "role,permission,allowed",
    [
        ("maintain", "write", True),
        ("admin", "admin", True),
        ("write", "write", False),
        ("triage", "read", False),
        ("read", "read", False),
        ("custom", "admin", False),
        ("admin", "read", False),
        (None, "write", False),
    ],
)
def test_real_permission_envelope_controls_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    role: str | None,
    permission: str,
    allowed: bool,
) -> None:
    remote = Remote()
    data = json.loads(remote.policy)
    data["release_lines"][0]["branches"].append("feature")
    remote.policy = json.dumps(data).encode()
    original_get = remote.get

    def get(endpoint: str, **kwargs: object):
        if endpoint.endswith("/permission"):
            return {"permission": permission, "role_name": role, "user": {"id": 7}}
        return original_get(endpoint, **kwargs)

    remote.get = get
    argv = [
        "plan",
        "--version",
        "1.0.0",
        "--branch",
        "feature",
        "--allow-non-deployment-branch",
        "--reason",
        "Reviewed emergency",
    ]
    if allowed:
        state = acquire(monkeypatch, tmp_path, remote, argv)
        assert state.role == role
        assert (
            create_proposal(state, parse_args(argv)).approval_environment
            == "release-override"
        )
    else:
        with pytest.raises(ControllerError):
            state = acquire(monkeypatch, tmp_path, remote, argv)
            create_proposal(state, parse_args(argv))


@pytest.mark.parametrize("host", ["github.com", "enterprise.example"])
def test_graphql_endpoint_is_exact_for_public_and_enterprise(
    host: str, tmp_path: Path
) -> None:
    import subprocess

    calls = []

    def run(_tool: str, args: list[str], **_kwargs: object):
        calls.append(args)
        payload = {
            "data": {
                "repository": {
                    "databaseId": 123,
                    "refs": {
                        "nodes": [],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    },
                }
            }
        }
        return subprocess.CompletedProcess(
            [], 0, "HTTP/2.0 200 OK\r\n\r\n" + json.dumps(payload), ""
        )

    GitHubReads(host, "owner/repo", cwd=tmp_path, runner=run).refs()
    argv = calls[0]
    assert argv[argv.index("--method") + 1] == "GET"
    assert "graphql" in argv and not any(a.startswith("graphql?") for a in argv)
    assert "--raw-field" in argv
    field = argv[argv.index("--raw-field") + 1]
    assert field.startswith("query=query {") and "mutation" not in field
    # gh's routing key must see the exact endpoint before encoding the GET field.
    endpoint = argv[-1]
    route = (
        ("/graphql" if host == "github.com" else "/api/graphql")
        if endpoint == "graphql"
        else "/api/v3/" + endpoint
    )
    assert route == ("/graphql" if host == "github.com" else "/api/graphql")
    assert 'repository(owner:"owner",name:"repo")' in unquote(field)


@pytest.mark.parametrize(
    "flags,expected",
    [
        (["--bump", "patch"], "a" * 40),
        (["--version", "1.5.0"], "d" * 40),
        (["--bump", "prerelease", "--channel", "rc"], "d" * 40),
    ],
)
def test_notes_baseline_matches_resolved_version(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, flags: list[str], expected: str
) -> None:
    remote = Remote()
    history = [
        {
            "release_id": i,
            "tag": "v" + version,
            "commit": sha,
            "line": "current",
            "version": version,
            "legacy_version": None,
            "projections": {},
        }
        for i, version, sha in [(1, "1.4.2", "a" * 40), (2, "1.5.0-rc.1", "d" * 40)]
    ]
    monkeypatch.setattr(
        source,
        "adopted_history",
        lambda *_a: (history, [r["version"] for r in history]),
    )
    calls = []
    monkeypatch.setattr(
        source,
        "release_notes",
        lambda _api, sha, baseline: calls.append(baseline) or "notes",
    )
    state = acquire(monkeypatch, tmp_path, remote, ["plan", "--branch", "main", *flags])
    assert calls == [expected]
    assert create_proposal(
        state, parse_args(["plan", "--branch", "main", *flags])
    ).version
