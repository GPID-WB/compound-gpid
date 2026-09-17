"""Step 5 callable service, activation, freshness, and selection tests."""
from __future__ import annotations

import json
import hashlib
import os
import shutil
import subprocess
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

import cg_help
import cg_generate_targets as targets
import cg_project_manifest as manifest
import secure_fs
from help import catalog
from scripts.tests.test_help_catalog import _copy_catalog_source_graph
from scripts.tests.test_help_query import evidence

REQUEST = "12345678-1234-4234-8234-123456789abc"
OTHER = "12345678-1234-4234-8234-123456789abd"


def test_step7_prompt_is_thin_and_uses_only_validated_transport():
    root = Path(__file__).resolve().parents[2]
    path = root / ".github/prompts/cg-help.prompt.md"
    assert path.is_file(), "Step7 canonical help prompt is missing"
    text = path.read_text(encoding="utf-8")
    assert len(text.encode("utf-8")) < 7000
    for required in ("--prepare-request --root .", "--consume-request <uuid>",
                     "--render-selection <uuid>", "structured file-write tool",
                     "selection-prepared", "transport-error", "4096", "1024",
                     "unchanged", "model-visible", "Never scan", "Do not compose"):
        assert required in text
    for forbidden in ("$ARGUMENTS", "definitionDigest", "--catalog", "--source-root"):
        assert forbidden not in text


def test_step7_catalog_includes_exact_cross_suite_slash_help():
    root = Path(__file__).resolve().parents[2]
    value = json.loads(catalog.generate_catalog_bytes(root))
    command = next((item for item in value["commands"] if item["id"] == "slash:cg-help"), None)
    assert command is not None, "Step7 slash:cg-help is missing from the validated inventory"
    assert command["ownerModule"] == "cap-help"
    assert command["supportedSuites"] == ["cg", "cr"]


@pytest.mark.parametrize("name", ["overview", "exact", "metacharacters"])
def test_step7_observed_prompt_operations_and_final_relay(transport, capsys, monkeypatch, name):
    """Exercise the actual backend, then reject changed observed host evidence."""
    import copy
    from help import support
    root, source = transport
    monkeypatch.chdir(root)
    monkeypatch.setattr(cg_help, "INSTALLED_ROOT", source)
    observed = []
    original = cg_help.query_service

    def observe(text, **kwargs):
        observed.append(hashlib.sha256(text.encode("utf-8")).hexdigest())
        return original(text, **kwargs)

    monkeypatch.setattr(cg_help, "query_service", observe)
    records = []

    def operation(flag, request_id=None):
        observed.clear()
        argv = [flag] + ([request_id] if request_id else []) + ["--root", ".", "--platform", "copilot"]
        status = cg_help.main(argv)
        output = capsys.readouterr()
        assert status == 0, output.err
        envelope = catalog.parse_transport_envelope(output.out.encode(), source="observer")
        records.append(dict(argv=argv, exitCode=status, envelope=envelope, queryFingerprints=list(observed)))
        return envelope

    prepared = operation("--prepare-request")
    (root / prepared["queryPath"]).write_bytes(support.PROBE_CASES[name].encode("utf-8"))
    response = operation("--consume-request", prepared["requestId"])
    if name == "metacharacters":
        assert response["operation"] == "selection-prepared"
        (root / response["selectionPath"]).write_bytes(json.dumps(response["candidateIds"][::-1]).encode())
        response = operation("--render-selection", prepared["requestId"])
    final = response["result"]["display"]["content"]
    commands = ["cg-help " + " ".join(record["argv"]) for record in records]
    assert support.validate_host_flow(name, records, final, commands, "copilot")["outcome"] == "passed"
    for mutation in ("schema", "operation", "request", "exit", "path", "query-argv", "fingerprint", "append", "shell"):
        altered = copy.deepcopy(records)
        changed_final, changed_commands = final, commands
        if mutation == "schema":
            altered[0]["envelope"]["schemaVersion"] = 2
        elif mutation == "operation":
            altered[0]["envelope"]["operation"] = "invented"
        elif mutation == "request":
            altered[-1]["envelope"]["requestId"] = OTHER
        elif mutation == "exit":
            altered[-1]["exitCode"] = 3
        elif mutation == "path":
            altered[0]["envelope"]["queryPath"] = "../outside"
        elif mutation == "query-argv":
            altered[0]["argv"].append("injected query")
        elif mutation == "fingerprint":
            altered[1]["queryFingerprints"][0] = "f" * 64
        elif mutation == "append":
            changed_final += "\nInvented command."
        else:
            changed_commands = commands + ["echo query > file"]
        with pytest.raises(ValueError):
            support.validate_host_flow(name, altered, changed_final, changed_commands, "copilot")


@pytest.fixture(scope="module")
def source_template(tmp_path_factory):
    """Copy the actual declared source graph without changing repository evidence."""
    root = _copy_catalog_source_graph(tmp_path_factory.mktemp("help-source"))
    catalog.write_catalog(root)
    mapping = targets.load_target_mapping(root)
    assets = targets.scan_canonical_assets(root)
    plan = targets.build_generation_plan(root, mapping, assets)
    for entry in plan.entries:
        if entry.kind == "command":
            path = root / entry.destination
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(entry.content)
    return root


@pytest.fixture
def source(source_template, tmp_path):
    """Give each mutation test a separate copy of the generated fixture clone."""
    return Path(shutil.copytree(source_template, tmp_path / "source"))


def project(source, root, suites="cg", platform="kilo"):
    """Build a real resolver manifest and exact mapped command evidence."""
    root.mkdir(parents=True, exist_ok=True)
    (root / manifest.LOCAL_CONFIG_PATH).write_text(
        "---\nsuites: [{}]\n---\n".format(suites), encoding="utf-8")
    current = manifest.resolve_active_manifest(root, platforms=[platform], source_root=source)
    path = root / manifest.ACTIVE_MANIFEST_PATH
    path.parent.mkdir(exist_ok=True)
    path.write_text(manifest.canonical_manifest_bytes(current), encoding="utf-8")
    value = catalog.load_strict_json(source / catalog.CATALOG_OUTPUT_PATH)
    paths = manifest.help_command_paths(source, value, platform, current["selection"]["suites"])
    for relative, source_relative in paths.items():
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((source / source_relative).read_bytes())
    return root


def ask(root, source, text="/cg-work"):
    """Invoke only the callable service; no shell query transport exists here."""
    return cg_help.query_service(text, root=root, platform="kilo", source_root=source,
                                catalog_path=source / catalog.CATALOG_OUTPUT_PATH)


@pytest.mark.parametrize("suites", ["cg", "cr", "cg, cr"])
def test_valid_manifest_shared_command_and_deterministic_render(source, tmp_path, suites):
    """The strict resolver, not a mock activation parser, supplies active suites."""
    root = project(source, tmp_path / "consumer", suites)
    first = ask(root, source, "shell:cg-skill")
    assert first["state"] == "exact"
    assert "active" in first["display"]["content"]
    assert first == ask(root, source, "shell:cg-skill")
    catalog.validate_transport_envelope(dict(schemaVersion=1, operation="query-completed",
                                            requestId=REQUEST, result=first))


@pytest.mark.parametrize("text", ["", "/cg-help", "shell:cg-skill", "review"])
def test_workflow_pointer_changes_do_not_affect_help(source, tmp_path, text):
    """Workflow restart pointers are not help activation or catalog inputs."""
    root = project(source, tmp_path / "consumer")
    expected = ask(root, source, text)
    assert expected["state"] != "error"
    for base in (root, source):
        path = base / ".cg-docs/active-state/current.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        for branch, phase in (("cg-autopilot", 6), ("wealthy-salmonberry", 5)):
            state = {
                "schemaVersion": "compound-gpid-active-state-v1",
                "updatedAt": "2026-09-16T15:33:12Z",
                "workflow": "/cg-work",
                "status": "active",
                "branch": branch,
                "plan": None,
                "executionReport": None,
                "currentPhase": phase,
                "evidenceStatus": [],
                "unresolvedDecisions": [],
                "artifactRefs": [],
                "nextCommand": "/cg-compound" if phase == 6 else "/cg-work phase5",
            }
            content = json.dumps(state).encode("utf-8")
            path.write_bytes(content)
            assert ask(root, source, text) == expected
            assert path.read_bytes() == content


@pytest.mark.parametrize("change", ["missing", "config", "suite", "closure", "platform", "registry", "command", "duplicate"])
def test_incomplete_or_contradictory_activation_is_error(source, tmp_path, change):
    """No unverified active command is recommended on any activation failure."""
    root = project(source, tmp_path / "consumer")
    path = root / manifest.ACTIVE_MANIFEST_PATH
    value = json.loads(path.read_text(encoding="utf-8"))
    if change == "missing":
        path.unlink()
    elif change == "config":
        (root / manifest.LOCAL_CONFIG_PATH).write_text("---\nsuites: [cr]\n---\n", encoding="utf-8")
    elif change == "command":
        (root / ".kilo/commands/cg-work.md").unlink()
    elif change == "duplicate":
        path.write_text('{"header":"first","header":"second"}', encoding="utf-8")
    else:
        field = {"suite": "suites", "closure": "moduleClosure", "platform": "platforms", "registry": "registryDigest"}[change]
        value["selection"][field] = "0" * 64 if change == "registry" else []
        path.write_text(json.dumps(value), encoding="utf-8")
    result = ask(root, source)
    assert result["state"] == "error"
    assert result["evidenceIds"] == []
    assert result["recovery"]


@pytest.mark.parametrize("config", ["---\nsuites: []\n---", "---\nsuites: cg\n---", "---\nsuites: [xx]\n---", "---\nsuites: [cg]\nsuites: [cr]\n---", "---\nlanguage: python\n---"])
def test_strict_config_is_reused_and_existing_config_requires_manifest(source, tmp_path, config):
    """Link tooling identifies any existing config as manifest-driven mode."""
    root = tmp_path / "consumer"
    root.mkdir()
    (root / manifest.LOCAL_CONFIG_PATH).write_text(config, encoding="utf-8")
    assert ask(root, source)["state"] == "error"


def test_absent_config_without_legacy_proof_is_error(source, tmp_path):
    """An empty project cannot acquire the legacy CG default by assumption."""
    root = tmp_path / "consumer"
    root.mkdir()
    assert ask(root, source)["state"] == "error"


def test_recognized_complete_legacy_link_and_missing_expected_path(source, tmp_path):
    """Only a complete exact link to this clone proves legacy CG activation."""
    root = tmp_path / "consumer"
    (root / ".kilo").mkdir(parents=True)
    link = root / ".kilo/commands"
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(source / ".kilo/commands")], check=True, capture_output=True)
    else:
        link.symlink_to(source / ".kilo/commands", target_is_directory=True)
    assert ask(root, source)["state"] == "exact"
    (source / ".kilo/commands/cg-work.md").unlink()
    assert ask(root, source)["state"] == "error"


def test_secure_project_reads_reject_hardlink_alias(source, tmp_path):
    """Regular-looking command evidence cannot alias another writable file."""
    root = project(source, tmp_path / "consumer")
    path = root / ".kilo/commands/cg-work.md"
    os.link(str(path), str(root / "alias.md"))
    assert ask(root, source)["state"] == "error"


def test_complete_legacy_managed_copy_requires_every_checksum(source, tmp_path):
    """The current Kilo copy-directory marker proves only its exact complete set."""
    root = project(source, tmp_path / "consumer")
    (root / manifest.ACTIVE_MANIFEST_PATH).unlink()
    (root / manifest.LOCAL_CONFIG_PATH).unlink()
    directory = root / ".kilo/commands"
    value = catalog.load_strict_json(source / catalog.CATALOG_OUTPUT_PATH)
    paths = manifest.help_command_paths(source, value, "kilo", ["cg"])
    marker = {"schemaVersion": 1, "source": ".kilo/commands", "files": {
        Path(relative).name: hashlib.sha256((root / relative).read_bytes()).hexdigest()
        for relative in paths}}
    path = directory / ".compound-gpid-managed-copy.json"
    path.write_text(json.dumps(marker), encoding="utf-8")
    assert ask(root, source)["state"] == "exact"
    del marker["files"]["cg-work.md"]
    path.write_text(json.dumps(marker), encoding="utf-8")
    assert ask(root, source)["state"] == "error"


def test_source_freshness_is_recomputed_before_each_query(source, tmp_path):
    """A cached catalog digest cannot hide changed pinned prompt bytes."""
    root = project(source, tmp_path / "consumer")
    assert ask(root, source)["state"] == "exact"
    path = source / ".github/prompts/cg-work.prompt.md"
    path.write_bytes(path.read_bytes() + b"\nChanged definition.\n")
    result = ask(root, source)
    assert result["state"] == "error"
    assert "definitionDigest" in result["data"]["message"]


@pytest.mark.parametrize("change", ["missing", "digest", "generator", "alias"])
def test_catalog_failure_never_becomes_unsupported(source, tmp_path, change):
    """Missing, stale, incompatible, and ambiguous evidence fail closed."""
    root = project(source, tmp_path / "consumer")
    path = source / catalog.CATALOG_OUTPUT_PATH
    value = catalog.load_strict_json(path)
    if change == "missing":
        path.unlink()
    else:
        if change == "alias":
            value["commands"][0]["aliases"] = [value["commands"][1]["name"]]
        else:
            value[{"digest": "sourceDigest", "generator": "generatorVersion"}[change]] = "0" * 64
        path.write_text(json.dumps(value), encoding="utf-8")
    assert ask(root, source, "unrelated banana")["state"] == "error"


def test_override_pair_is_required_and_default_catalog_is_installed_clone(tmp_path):
    """The consumer and native catalogs are never auto-discovered."""
    assert cg_help.INSTALLED_ROOT == Path(cg_help.__file__).resolve().parents[1]
    result = cg_help.query_service("", root=tmp_path, platform="kilo", source_root=tmp_path)
    assert result["state"] == "error"
    assert "pair" in result["data"]["message"]


@pytest.mark.parametrize("text,state", [("", "overview"), ("/cg-work", "exact"), ("cg-skill", "candidates"), ("manage a skill", "workflow"), ("banana", "unsupported")])
def test_rendered_results_use_only_catalog_evidence(text, state):
    """All semantic displays are deterministic and valid in the current schema."""
    value, registry = evidence()
    result = cg_help.answer(value, registry, text, ("cg",), "kilo", "windows")
    assert result["state"] == state
    assert result == cg_help.answer(value, registry, text, ("cg",), "kilo", "windows")
    catalog.validate_transport_envelope(dict(schemaVersion=1, operation="query-completed", requestId=REQUEST, result=result))
    assert "/cg-help" in result["display"]["content"]


def test_candidate_labels_followups_and_inert_rendering():
    """Metadata does not become Markdown instructions or invented activation actions."""
    value, registry = evidence()
    value["commands"][0]["summary"] = "<script>bad()</script> [click](https://evil.invalid)"
    result = cg_help.answer(value, registry, "cg-skill", ("cr",), "kilo", "windows")
    display = result["display"]["content"]
    assert "<script>" not in display and "[click](https://evil.invalid)" not in display
    assert "inactive" in display and "active" in display and "high" in display
    assert result["data"]["followUpQueries"] == ["/cg-help shell:cg-skill", "/cg-help /cg-skill"]
    exact = cg_help.answer(value, registry, "/cg-skill", ("cr",), "kilo", "windows")
    assert "docs/configuration.md#strict-configuration-schema" in exact["display"]["content"]


def test_selection_is_request_bound_expiring_closed_and_single_use():
    """Only returned IDs cross the model boundary; replay is rejected."""
    value, registry = evidence()
    result = cg_help.answer(value, registry, "cg-skill", ("cg",), "kilo", "windows")
    selection = cg_help.Selection(REQUEST, result, now=100)
    assert selection.token and selection.token != cg_help.Selection(OTHER, result, now=100).token
    assert selection.candidate_ids == result["data"]["commandIds"]
    for request, token, ids, now in [
        (OTHER, selection.token, selection.candidate_ids, 101),
        (REQUEST, "wrong", selection.candidate_ids, 101),
        (REQUEST, "\u00e9", selection.candidate_ids, 101),
        (REQUEST, selection.token, ["slash:not-real"], 101),
        (REQUEST, selection.token, [selection.candidate_ids[0]] * 2, 101),
        (REQUEST, selection.token, selection.candidate_ids * 2, 101),
        (REQUEST, selection.token, [], 101),
        (REQUEST, selection.token, selection.candidate_ids, 400),
    ]:
        with pytest.raises(catalog.HelpValidationError):
            selection.render(request, token, ids, now=now)
    selected = list(reversed(selection.candidate_ids))
    rendered = selection.render(REQUEST, selection.token, selected, now=101)
    assert rendered["data"]["commandIds"] == selected
    assert rendered["evidenceIds"] == selected
    catalog.validate_transport_envelope(dict(schemaVersion=1, operation="selection-rendered", requestId=REQUEST, result=rendered))
    with pytest.raises(catalog.HelpValidationError):
        selection.render(REQUEST, selection.token, selected, now=102)


@pytest.mark.parametrize("platform", ["copilot", "claude-code", "codex", "opencode", "kilo"])
def test_current_platform_paths_derive_from_mapping(source, tmp_path, platform):
    """Every current adapter uses its mapped command paths, not discovery."""
    root = project(source, tmp_path / "consumer", platform=platform)
    result = cg_help.query_service("/cg-work", root=root, platform=platform,
        source_root=source, catalog_path=source / catalog.CATALOG_OUTPUT_PATH)
    assert result["state"] == "exact"


# Step 6 uses the real source graph and strict schema; no metadata is repinned.
RUNTIME = ".compound-gpid/runtime/help-requests"
_REQUEST_UUID = "00000000-0000-4000-8000-000000000000"


@pytest.fixture
def transport(source_template: Path, tmp_path: Path) -> tuple:
    """Return (consumer, clone) with canonical Copilot activation for CLI tests."""
    return project(source_template, tmp_path / "consumer", platform="copilot"), source_template


def _transport_args(root: Path, source: Path, *operation: str) -> list:
    """Build fixed CLI arguments; query text is never an argument."""
    args = ["--root", str(root), *operation]
    if source is not None:
        args += ["--catalog", str(source / catalog.CATALOG_OUTPUT_PATH),
                 "--source-root", str(source)]
    return args


def _transport_output(status: int, stdout: str, stderr: str) -> tuple:
    """Parse the one stdout envelope before interpreting the process status."""
    assert isinstance(status, int)
    assert "Traceback" not in stderr
    envelope = catalog.parse_transport_envelope(stdout.encode("utf-8"), source="CLI stdout")
    return status, envelope, stderr


def _run_help(capsys: pytest.CaptureFixture, root: Path, source: Path, *operation: str) -> tuple:
    """Invoke main(argv) and require a schema-v1, machine-clean response."""
    status = cg_help.main(_transport_args(root, source, *operation))
    output = capsys.readouterr()
    return _transport_output(status, output.out, output.err)


def _help_process(root: Path, source: Path, *operation: str) -> tuple:
    """Run a fresh foreground process to prove state survives interpreter exit."""
    result = subprocess.run(
        [sys.executable, str(Path(cg_help.__file__).resolve()),
         *_transport_args(root, source, *operation)],
        cwd=root, capture_output=True, encoding="utf-8", timeout=60, check=False,
    )
    return _transport_output(result.returncode, result.stdout, result.stderr)


def _prepare_help(capsys: pytest.CaptureFixture, root: Path, source: Path) -> tuple:
    """Prepare one empty CLI-owned file and return its envelope and exact path."""
    status, envelope, stderr = _run_help(capsys, root, source, "--prepare-request")
    assert (status, stderr, envelope["operation"]) == (0, "", "request-prepared")
    assert catalog.UUID_PATTERN.fullmatch(envelope["requestId"])
    assert envelope["queryPath"] == RUNTIME + "/" + envelope["requestId"] + ".query.txt"
    assert envelope["maxBytes"] == 4096 and envelope["expiresInSeconds"] == 300
    path = root / envelope["queryPath"]
    assert path.is_file() and not path.is_symlink() and path.read_bytes() == b""
    assert envelope["cleanupPolicy"] == "consume-once-and-expire"
    return envelope, path


def _assert_transport_error(response: tuple) -> None:
    """Require a nonzero category, a diagnostic, and no semantic success."""
    status, envelope, stderr = response
    assert status != 0 and stderr.strip()
    assert envelope["operation"] == "transport-error"


def _replace_same_bytes(path: Path) -> None:
    """Keep the original inode alive so equal-content replacement is certain."""
    content = path.read_bytes()
    path.rename(path.with_name(path.name + ".original"))
    path.write_bytes(content)


def _directory_alias(link: Path, target: Path) -> None:
    """Create a real Windows junction or POSIX symlink for confinement tests."""
    if os.name == "nt":
        subprocess.run(["cmd", "/d", "/c", "mklink", "/J", str(link), str(target)],
                       check=True, capture_output=True, timeout=15)
    else:
        link.symlink_to(target, target_is_directory=True)


@pytest.mark.parametrize("text,state", [
    ("", "overview"), ("/cg-work", "exact"), ("banana", "unsupported"),
    ("configure a new Compound GPID project", "workflow"),
    ("x" * 4096, "unsupported"), ("\u00e9" * 2048, "unsupported"),
])
def test_transport_query_result_matches_callable_rendering(transport, capsys, text, state):
    """The CLI adds transport only; semantic bytes and Step 5 limits stay intact."""
    root, source = transport
    prepared, path = _prepare_help(capsys, root, source)
    path.write_bytes(text.encode("utf-8"))
    status, envelope, stderr = _run_help(capsys, root, source, "--consume-request", prepared["requestId"])
    expected = cg_help.query_service(text, root=root, platform="copilot",
                                    source_root=source, catalog_path=source / catalog.CATALOG_OUTPUT_PATH)
    assert (status, stderr, envelope["operation"]) == (0, "", "query-completed")
    assert envelope["result"] == expected and expected["state"] == state
    assert not path.exists()
    _assert_transport_error(_run_help(capsys, root, source, "--consume-request", prepared["requestId"]))


def test_transport_injection_text_is_inert_and_byte_exact(transport, capsys, monkeypatch):
    """Quotes, shell syntax, and Unicode reach the service only as file data."""
    root, source = transport
    text = "'\"; | & `echo owned` $(touch owned) ${HOME} %PATH% \u00e9 \u4e2d"
    seen = []
    original = cg_help.query_service

    def observe(value, **kwargs):
        seen.append(value)
        return original(value, **kwargs)

    monkeypatch.setattr(cg_help, "query_service", observe)
    prepared, path = _prepare_help(capsys, root, source)
    path.write_bytes(text.encode("utf-8"))
    _run_help(capsys, root, source, "--consume-request", prepared["requestId"])
    assert seen == [text]
    assert not (root / "owned").exists() and not path.exists()
    assert all(text.encode("utf-8") not in item.read_bytes()
               for item in (root / RUNTIME).iterdir() if item.is_file())


@pytest.mark.parametrize("content", [
    b"\xff", b"\xef\xbb\xbf/cg-work", b"x\x00y", b"line1\nline2", b"x\ty", b"x\x7fy",
    "x\u0085y".encode("utf-8"), "x\u202ey".encode("utf-8"),
    b"x" * 4097, ("\u00e9" * 2049).encode("utf-8"), ("\ufdfa" * 1000).encode("utf-8"),
])
def test_transport_invalid_input_is_nonzero_cleaned_and_single_use(transport, capsys, content):
    """Invalid bytes/controls and normalized overflow never bypass Step 5 validation."""
    root, source = transport
    prepared, path = _prepare_help(capsys, root, source)
    path.write_bytes(content)
    status, envelope, stderr = _run_help(capsys, root, source, "--consume-request", prepared["requestId"])
    assert status != 0 and stderr.strip()
    assert envelope["operation"] == "transport-error" or envelope["result"]["state"] == "error"
    assert not path.exists()
    _assert_transport_error(_run_help(capsys, root, source, "--consume-request", prepared["requestId"]))


def test_transport_persists_ownership_across_processes_and_consumes_atomically(transport):
    """Two independent consumers cannot both win one persistent request."""
    root, source = transport
    status, prepared, stderr = _help_process(root, source, "--prepare-request")
    assert (status, stderr, prepared["operation"]) == (0, "", "request-prepared")
    path = root / prepared["queryPath"]
    path.write_bytes(b"/cg-work")
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(
            lambda _: _help_process(root, source, "--consume-request", prepared["requestId"]), range(2)))
    assert sum(status == 0 for status, _, _ in results) == 1
    assert sorted(item[1]["operation"] for item in results) == ["query-completed", "transport-error"]
    assert not path.exists()


def test_transport_concurrent_prepare_uuids_and_payloads_are_isolated(transport):
    """Simultaneous prepare operations retain separate files and request state."""
    root, source = transport
    with ThreadPoolExecutor(max_workers=2) as executor:
        prepared = list(executor.map(lambda _: _help_process(root, source, "--prepare-request"), range(2)))
    assert all(status == 0 and envelope["operation"] == "request-prepared" for status, envelope, _ in prepared)
    assert prepared[0][1]["requestId"] != prepared[1][1]["requestId"]
    for (_, envelope, _), text in zip(prepared, [b"/cg-work", b"banana"]):
        (root / envelope["queryPath"]).write_bytes(text)
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(
            lambda item: _help_process(root, source, "--consume-request", item[1]["requestId"]), prepared))
    assert [item[1]["result"]["state"] for item in results] == ["exact", "unsupported"]


def test_transport_duplicate_generated_uuid_never_clobbers_existing_request(transport, capsys, monkeypatch):
    """A UUID collision may retry or fail, but cannot replace an existing query."""
    root, source = transport
    prepared, path = _prepare_help(capsys, root, source)
    path.write_bytes(b"keep this pending query")
    identity = path.stat().st_ino
    original = uuid.uuid4
    calls = []

    def collide_once():
        calls.append(True)
        return uuid.UUID(prepared["requestId"]) if len(calls) == 1 else original()

    monkeypatch.setattr(uuid, "uuid4", collide_once)
    status, envelope, _ = _run_help(capsys, root, source, "--prepare-request")
    assert calls
    assert status != 0 or envelope["requestId"] != prepared["requestId"]
    assert path.read_bytes() == b"keep this pending query" and path.stat().st_ino == identity


@pytest.mark.parametrize("request_id", [REQUEST.upper(), "../" + REQUEST, REQUEST + ".query.txt", "not-a-uuid", REQUEST + ";echo owned"])
def test_transport_uuid_grammar_fails_before_file_access(transport, capsys, request_id):
    """Invalid operation identifiers cannot name query or selection paths."""
    root, source = transport
    for operation in ("--consume-request", "--render-selection"):
        _assert_transport_error(_run_help(capsys, root, source, operation, request_id))
    assert not (root / RUNTIME).exists()


def test_transport_unknown_cli_lookalike_and_cross_root_are_not_owned(transport, capsys, tmp_path):
    """An unregistered UUID file is neither readable nor eligible for cleanup."""
    root, source = transport
    prepared, path = _prepare_help(capsys, root, source)
    unknown = path.parent / (OTHER + ".query.txt")
    unknown.write_bytes(b"unknown user content")
    os.utime(unknown, (1, 1))
    _assert_transport_error(_run_help(capsys, root, source, "--consume-request", OTHER))
    other_root = project(source, tmp_path / "other", platform="copilot")
    _assert_transport_error(_run_help(capsys, other_root, source, "--consume-request", prepared["requestId"]))
    _prepare_help(capsys, root, source)
    assert path.exists() and unknown.read_bytes() == b"unknown user content"


@pytest.mark.parametrize("boundary", ["root", ".compound-gpid", ".compound-gpid/runtime", RUNTIME])
def test_transport_prepare_rejects_symlink_or_reparse_ancestors(transport, capsys, tmp_path, boundary):
    """Prepare never writes through a root alias or runtime-directory escape."""
    root, source = transport
    outside = tmp_path / "outside"
    outside.mkdir()
    marker = outside / "keep.txt"
    marker.write_bytes(b"outside")
    if boundary == "root":
        alias = tmp_path / "root-alias"
        _directory_alias(alias, root)
        target_root = alias
    else:
        link = root / boundary
        if link.exists():
            link.rename(link.with_name(link.name + "-original"))
        link.parent.mkdir(parents=True, exist_ok=True)
        _directory_alias(link, outside)
        target_root = root
    _assert_transport_error(_run_help(capsys, target_root, source, "--prepare-request"))
    assert list(outside.iterdir()) == [marker] and marker.read_bytes() == b"outside"


@pytest.mark.parametrize("replacement", ["equal-bytes", "hardlink", "directory"])
def test_transport_replaced_query_is_not_read_or_deleted(transport, capsys, tmp_path, replacement):
    """A regular file with identical bytes is not the prepared file identity."""
    root, source = transport
    prepared, path = _prepare_help(capsys, root, source)
    path.write_bytes(b"/cg-work")
    if replacement == "equal-bytes":
        _replace_same_bytes(path)
    elif replacement == "hardlink":
        os.link(path, tmp_path / "alias")
    else:
        path.unlink()
        path.mkdir()
    _assert_transport_error(_run_help(capsys, root, source, "--consume-request", prepared["requestId"]))
    assert path.exists()
    if replacement != "directory":
        assert path.read_bytes() == b"/cg-work"


@pytest.mark.parametrize("boundary", ["read", "delete"])
@pytest.mark.parametrize("phase", ["query", "selection"])
def test_transport_equal_content_swap_at_pinned_io_is_rejected(transport, capsys, monkeypatch, boundary, phase):
    """Ownership reaches the secure handle boundary, not only a prior path check."""
    root, source = transport
    prepared, path = _prepare_help(capsys, root, source)
    content = b"/cg-work"
    operation = "--consume-request"
    if phase == "selection":
        path.write_bytes(b"cg-skill")
        _, selected, _ = _run_help(capsys, root, source, operation, prepared["requestId"])
        assert selected["operation"] == "selection-prepared"
        path = root / selected["selectionPath"]
        content = json.dumps(selected["candidateIds"]).encode("utf-8")
        operation = "--render-selection"
    path.write_bytes(content)
    name = "secure_read_bytes" if boundary == "read" else "secure_delete_verified"
    hook = "before_open" if boundary == "read" else "before_unlink"
    original = getattr(secure_fs, name)
    attacked = []

    def swap_at_boundary(io_root, relative, *args, **kwargs):
        if Path(io_root) / relative == path and not attacked:
            assert kwargs.get("expected_identity") is not None
            attacked.append(True)
            kwargs[hook] = _replace_same_bytes
        return original(io_root, relative, *args, **kwargs)

    monkeypatch.setattr(secure_fs, name, swap_at_boundary)
    _assert_transport_error(_run_help(capsys, root, source, operation, prepared["requestId"]))
    assert attacked and path.read_bytes() == content


def test_transport_runtime_reparse_replacement_after_prepare_is_confined(transport, capsys, tmp_path):
    """Consume rechecks runtime ancestors and never reads or cleans the escape."""
    root, source = transport
    prepared, path = _prepare_help(capsys, root, source)
    runtime = path.parent
    runtime.rename(runtime.with_name("original-requests"))
    outside = tmp_path / "outside-requests"
    outside.mkdir()
    replacement = outside / path.name
    replacement.write_bytes(b"outside owned content")
    _directory_alias(runtime, outside)
    _assert_transport_error(_run_help(capsys, root, source, "--consume-request", prepared["requestId"]))
    assert replacement.read_bytes() == b"outside owned content"
    assert list(outside.iterdir()) == [replacement]


def test_transport_operation_order_does_not_destroy_pending_files(transport, capsys):
    """Render before consume and consume after selection cannot steal another stage."""
    root, source = transport
    prepared, path = _prepare_help(capsys, root, source)
    _assert_transport_error(_run_help(capsys, root, source, "--render-selection", prepared["requestId"]))
    assert path.exists()
    path.write_bytes(b"cg-skill")
    _, selected, _ = _run_help(capsys, root, source, "--consume-request", prepared["requestId"])
    assert selected["operation"] == "selection-prepared"
    _assert_transport_error(_run_help(capsys, root, source, "--consume-request", prepared["requestId"]))
    assert (root / selected["selectionPath"]).exists()


def test_transport_expiry_and_cleanup_preserve_unknown_replaced_and_active_files(transport, capsys, monkeypatch):
    """Prepare cleans expired CLI identities, not files selected only by age/name."""
    root, source = transport
    monkeypatch.setattr(cg_help.time, "time", lambda: 1000)
    expired, expired_path = _prepare_help(capsys, root, source)
    _, replaced_path = _prepare_help(capsys, root, source)
    _replace_same_bytes(replaced_path)
    unknown = expired_path.parent / (OTHER + ".query.txt")
    unknown.write_bytes(b"unowned")
    os.utime(unknown, (1, 1))
    monkeypatch.setattr(cg_help.time, "time", lambda: 1299)
    _, active_path = _prepare_help(capsys, root, source)
    active_path.write_bytes(b"pending")
    monkeypatch.setattr(cg_help.time, "time", lambda: 1300)
    _prepare_help(capsys, root, source)
    assert not expired_path.exists()
    assert replaced_path.exists() and unknown.read_bytes() == b"unowned"
    assert active_path.read_bytes() == b"pending"
    _assert_transport_error(_run_help(capsys, root, source, "--consume-request", expired["requestId"]))


def test_transport_expired_consume_cleans_owned_query_without_a_prepare(transport, capsys, monkeypatch):
    """Expiry is checked during consume, including the exact 300-second boundary."""
    root, source = transport
    monkeypatch.setattr(cg_help.time, "time", lambda: 1000)
    prepared, path = _prepare_help(capsys, root, source)
    path.write_bytes(b"private pending query")
    monkeypatch.setattr(cg_help.time, "time", lambda: 1300)
    _assert_transport_error(_run_help(capsys, root, source, "--consume-request", prepared["requestId"]))
    assert not path.exists()


def test_transport_expired_query_cleanup_survives_interrupted_consumer_lock(transport, capsys, monkeypatch):
    """An interrupted stage claim cannot retain expired raw query bytes forever."""
    root, source = transport
    monkeypatch.setattr(cg_help.time, "time", lambda: 1000)
    prepared, path = _prepare_help(capsys, root, source)
    path.write_bytes(b"private interrupted query")
    lock_relative = RUNTIME + "/" + prepared["requestId"] + ".query.lock"
    original = secure_fs.secure_create_bytes

    def interrupt_after_claim(io_root, relative, content):
        identity = original(io_root, relative, content)
        if relative == lock_relative:
            raise SystemExit("simulated interruption after stage claim")
        return identity

    with monkeypatch.context() as interrupted:
        interrupted.setattr(secure_fs, "secure_create_bytes", interrupt_after_claim)
        with pytest.raises(SystemExit, match="simulated interruption"):
            cg_help.main(_transport_args(root, source, "--consume-request", prepared["requestId"]))
    lock = root / lock_relative
    assert lock.is_file() and path.read_bytes() == b"private interrupted query"
    _replace_same_bytes(lock)
    lock_identity = lock.stat().st_ino
    monkeypatch.setattr(cg_help.time, "time", lambda: 1300)
    _prepare_help(capsys, root, source)
    assert not path.exists()
    assert lock.is_file() and lock.stat().st_ino == lock_identity and lock.read_bytes() == b""
    _assert_transport_error(_run_help(capsys, root, source, "--consume-request", prepared["requestId"]))


def test_transport_expired_cleanup_retires_recorded_stage_claim(transport, capsys, monkeypatch):
    """An expired request retires a recorded consumer lock with its state."""
    root, source = transport
    monkeypatch.setattr(cg_help.time, "time", lambda: 1000)
    prepared, path = _prepare_help(capsys, root, source)
    path.write_bytes(b"private pending query")
    lock_relative = RUNTIME + "/" + prepared["requestId"] + ".query.lock"
    identity_relative = RUNTIME + "/" + prepared["requestId"] + ".query.lock.identity.json"
    calls = {"count": 0}
    original_state = cg_help._state
    original_remove = cg_help._remove

    def interrupt_before_take(io_root, request_id, stage, key):
        calls["count"] += 1
        if calls["count"] >= 2:
            raise SystemExit("simulated interruption after recorded claim")
        return original_state(io_root, request_id, stage, key)

    def fail_lock_removal(io_root, rel_path, content, identity=None):
        if rel_path.endswith((".query.lock", ".selection.lock")):
            raise OSError("simulated stuck stage claim")
        return original_remove(io_root, rel_path, content, identity)

    with monkeypatch.context() as interrupted:
        interrupted.setattr(cg_help, "_state", interrupt_before_take)
        interrupted.setattr(cg_help, "_remove", fail_lock_removal)
        _assert_transport_error(_run_help(capsys, root, source, "--consume-request", prepared["requestId"]))
    lock = root / lock_relative
    assert lock.is_file() and (root / identity_relative).is_file()
    calls["count"] = 0
    monkeypatch.setattr(cg_help.time, "time", lambda: 1300)
    _prepare_help(capsys, root, source)
    assert not path.exists()
    assert not lock.exists()
    assert not (root / identity_relative).exists()
    _assert_transport_error(_run_help(capsys, root, source, "--consume-request", prepared["requestId"]))


def test_transport_expired_cleanup_preserves_unverifiable_stage_claim(transport, capsys, monkeypatch):
    """A foreign or unverifiable lock sidecar is never treated as deletion authority."""
    root, source = transport
    monkeypatch.setattr(cg_help.time, "time", lambda: 1000)
    prepared, path = _prepare_help(capsys, root, source)
    path.write_bytes(b"private pending query")
    lock_relative = RUNTIME + "/" + prepared["requestId"] + ".query.lock"
    identity_relative = RUNTIME + "/" + prepared["requestId"] + ".query.lock.identity.json"
    calls = {"count": 0}
    original_state = cg_help._state
    original_remove = cg_help._remove

    def interrupt_before_take(io_root, request_id, stage, key):
        calls["count"] += 1
        if calls["count"] >= 2:
            raise SystemExit("simulated interruption after recorded claim")
        return original_state(io_root, request_id, stage, key)

    def fail_lock_removal(io_root, rel_path, content, identity=None):
        if rel_path.endswith((".query.lock", ".selection.lock")):
            raise OSError("simulated stuck stage claim")
        return original_remove(io_root, rel_path, content, identity)

    with monkeypatch.context() as interrupted:
        interrupted.setattr(cg_help, "_state", interrupt_before_take)
        interrupted.setattr(cg_help, "_remove", fail_lock_removal)
        _assert_transport_error(_run_help(capsys, root, source, "--consume-request", prepared["requestId"]))
    lock = root / lock_relative
    identity_path = root / identity_relative
    assert lock.is_file() and identity_path.is_file()
    identity_path.write_bytes(b'{"foreign": true}')
    calls["count"] = 0
    monkeypatch.setattr(cg_help.time, "time", lambda: 1300)
    _prepare_help(capsys, root, source)
    assert not path.exists()
    assert lock.is_file()
    assert identity_path.read_bytes() == b'{"foreign": true}'
    _assert_transport_error(_run_help(capsys, root, source, "--consume-request", prepared["requestId"]))


@pytest.mark.parametrize("phase", ["query", "selection"])
def test_transport_input_beyond_read_limit_is_rejected_cleaned_and_single_use(transport, capsys, monkeypatch, phase):
    """Oversized owned payloads are retired without an unbounded content read."""
    root, source = transport
    prepared, path = _prepare_help(capsys, root, source)
    operation = "--consume-request"
    if phase == "selection":
        path.write_bytes(b"cg-skill")
        _, selected, _ = _run_help(capsys, root, source, operation, prepared["requestId"])
        assert selected["operation"] == "selection-prepared"
        path = root / selected["selectionPath"]
        operation = "--render-selection"
    with path.open("wb") as handle:
        handle.seek(cg_help.TRANSPORT_READ_LIMIT)
        handle.write(b"x")
    original = secure_fs.secure_read_bytes

    def bounded_payload_read(io_root, relative, **kwargs):
        if Path(io_root) / relative == path:
            assert 0 <= kwargs["max_bytes"] <= cg_help.TRANSPORT_READ_LIMIT
        return original(io_root, relative, **kwargs)

    monkeypatch.setattr(secure_fs, "secure_read_bytes", bounded_payload_read)
    _assert_transport_error(_run_help(capsys, root, source, operation, prepared["requestId"]))
    assert not path.exists()
    _assert_transport_error(_run_help(capsys, root, source, operation, prepared["requestId"]))


def test_transport_prepare_cleanup_has_a_test_visible_work_bound(transport, capsys, monkeypatch):
    """Each prepare retires at most CLEANUP_LIMIT expired request records."""
    root, source = transport
    monkeypatch.setattr(cg_help, "CLEANUP_LIMIT", 2)
    monkeypatch.setattr(cg_help.time, "time", lambda: 1000)
    paths = [_prepare_help(capsys, root, source)[1] for _ in range(3)]
    monkeypatch.setattr(cg_help.time, "time", lambda: 1300)
    _prepare_help(capsys, root, source)
    removed = sum(not path.exists() for path in paths)
    assert 0 < removed <= 2


def test_transport_selection_persists_closed_order_and_single_use(transport):
    """Only returned IDs survive process boundaries; rendering is deterministic."""
    root, source = transport
    _, prepared, _ = _help_process(root, source, "--prepare-request")
    path = root / prepared["queryPath"]
    path.write_bytes(b"cg-skill")
    status, selected, stderr = _help_process(root, source, "--consume-request", prepared["requestId"])
    assert (status, stderr, selected["operation"]) == (0, "", "selection-prepared")
    assert not path.exists() and 1 <= len(selected["candidateIds"]) <= 3
    assert selected["selectionToken"] and selected["requestId"] == prepared["requestId"]
    assert selected["catalogDigest"] and selected["evidenceIds"] == selected["candidateIds"]
    selection_path = root / selected["selectionPath"]
    assert selection_path.is_file() and selection_path.read_bytes() == b""
    ids = list(reversed(selected["candidateIds"]))
    selection_path.write_text(json.dumps(ids), encoding="utf-8")
    status, rendered, stderr = _help_process(root, source, "--render-selection", prepared["requestId"])
    assert (status, stderr, rendered["operation"]) == (0, "", "selection-rendered")
    assert rendered["result"]["data"]["commandIds"] == ids
    expected = cg_help.query_service("cg-skill", root=root, platform="copilot",
                                    source_root=source, catalog_path=source / catalog.CATALOG_OUTPUT_PATH)
    capability = cg_help.Selection(prepared["requestId"], expected)
    assert rendered["result"] == capability.render(prepared["requestId"], capability.token, ids)
    assert not selection_path.exists()
    _assert_transport_error(_help_process(root, source, "--render-selection", prepared["requestId"]))


def test_transport_concurrent_selection_has_exactly_one_winner(transport):
    """Persistent selection consumption is atomic across independent processes."""
    root, source = transport
    _, prepared, _ = _help_process(root, source, "--prepare-request")
    (root / prepared["queryPath"]).write_bytes(b"cg-skill")
    _, selected, _ = _help_process(root, source, "--consume-request", prepared["requestId"])
    assert selected["operation"] == "selection-prepared"
    path = root / selected["selectionPath"]
    path.write_text(json.dumps(selected["candidateIds"]), encoding="utf-8")
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(
            lambda _: _help_process(root, source, "--render-selection", prepared["requestId"]), range(2)))
    assert sum(status == 0 for status, _, _ in results) == 1
    assert sorted(item[1]["operation"] for item in results) == ["selection-rendered", "transport-error"]
    assert not path.exists()


@pytest.mark.parametrize("content", [
    b'[]', b'["slash:not-real"]', b'["shell:cg-skill","shell:cg-skill"]',
    b'["shell:cg-skill","slash:cg-skill","slash:cg-work","shell:cg-index"]',
    b'{"ids":["shell:cg-skill"],"selectionToken":"injected"}', b'null', b'[1]', b'[', b'\xff', b' ' * 1025,
])
def test_transport_selection_rejects_untrusted_lists_and_cleans_once(transport, capsys, content):
    """Persisted selection accepts a bounded nonempty ordered subset, not prose."""
    root, source = transport
    prepared, path = _prepare_help(capsys, root, source)
    path.write_bytes(b"cg-skill")
    _, envelope, _ = _run_help(capsys, root, source, "--consume-request", prepared["requestId"])
    assert envelope["operation"] == "selection-prepared"
    selection_path = root / envelope["selectionPath"]
    selection_path.write_bytes(content)
    _assert_transport_error(_run_help(capsys, root, source, "--render-selection", prepared["requestId"]))
    assert not selection_path.exists()
    _assert_transport_error(_run_help(capsys, root, source, "--render-selection", prepared["requestId"]))


def test_transport_selection_token_and_file_identity_are_request_bound(transport, capsys):
    """Two candidate requests have distinct tokens and cannot swap selection files."""
    root, source = transport
    selections = []
    for _ in range(2):
        prepared, path = _prepare_help(capsys, root, source)
        path.write_bytes(b"cg-skill")
        _, envelope, _ = _run_help(capsys, root, source, "--consume-request", prepared["requestId"])
        selections.append(envelope)
    assert selections[0]["selectionToken"] != selections[1]["selectionToken"]
    first, second = [root / item["selectionPath"] for item in selections]
    first.write_text(json.dumps(selections[0]["candidateIds"]), encoding="utf-8")
    second.unlink()
    first.rename(second)
    _assert_transport_error(_run_help(capsys, root, source, "--render-selection", selections[1]["requestId"]))
    assert second.exists()


def test_transport_selection_expiry_is_independent_and_cleans_owned_file(transport, capsys, monkeypatch):
    """A selection token expires 300 seconds after its own creation."""
    root, source = transport
    monkeypatch.setattr(cg_help.time, "time", lambda: 1000)
    prepared, path = _prepare_help(capsys, root, source)
    path.write_bytes(b"cg-skill")
    monkeypatch.setattr(cg_help.time, "time", lambda: 1100)
    _, selected, _ = _run_help(capsys, root, source, "--consume-request", prepared["requestId"])
    path = root / selected["selectionPath"]
    path.write_text(json.dumps(selected["candidateIds"]), encoding="utf-8")
    monkeypatch.setattr(cg_help.time, "time", lambda: 1400)
    _assert_transport_error(_run_help(capsys, root, source, "--render-selection", prepared["requestId"]))
    assert not path.exists()


@pytest.mark.parametrize("change", ["definition", "catalog", "activation"])
def test_transport_revalidates_evidence_between_query_and_selection(source, tmp_path, capsys, change):
    """Persisted candidate evidence cannot render after clone or project drift."""
    root = project(source, tmp_path / "consumer", platform="copilot")
    prepared, path = _prepare_help(capsys, root, source)
    path.write_bytes(b"cg-skill")
    _, selected, _ = _run_help(capsys, root, source, "--consume-request", prepared["requestId"])
    assert selected["operation"] == "selection-prepared"
    selection_path = root / selected["selectionPath"]
    selection_path.write_text(json.dumps(selected["candidateIds"]), encoding="utf-8")
    changed = {"definition": source / ".github/prompts/cg-work.prompt.md",
               "catalog": source / catalog.CATALOG_OUTPUT_PATH,
               "activation": root / manifest.LOCAL_CONFIG_PATH}[change]
    changed.write_bytes(changed.read_bytes() + b"\nChanged evidence.\n")
    if change == "activation":
        changed.write_text("---\nsuites: [cr]\n---\n", encoding="utf-8")
    status, envelope, stderr = _run_help(capsys, root, source, "--render-selection", prepared["requestId"])
    assert status != 0 and stderr.strip()
    assert envelope["operation"] == "transport-error" or envelope["result"]["state"] == "error"
    assert not selection_path.exists()


def test_transport_default_catalog_is_only_the_installed_clone(transport, capsys, monkeypatch):
    """--root controls the consumer, not catalog discovery or source inventory."""
    root, source = transport
    monkeypatch.setattr(cg_help, "INSTALLED_ROOT", source)
    for relative in (catalog.CATALOG_OUTPUT_PATH, ".kilo/shared/help-catalog.json"):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"not a catalog")
    monkeypatch.chdir(root)
    prepared, path = _prepare_help(capsys, Path("."), None)
    path.write_bytes(b"/cg-work")
    status, envelope, _ = _run_help(capsys, Path("."), None, "--consume-request", prepared["requestId"])
    assert status == 0 and envelope["result"]["state"] == "exact"


@pytest.mark.parametrize("args", [
    ["--catalog", "catalog.json"], ["--source-root", "."],
    ["--catalog", "https://invalid.example/catalog.json", "--source-root", "."],
    ["--catalog", "catalog.json", "--source-root", "https://invalid.example/source"],
])
def test_transport_catalog_overrides_require_a_local_pair(transport, capsys, args):
    """Test overrides cannot enable URL fetching or implicit source discovery."""
    root, _ = transport
    _assert_transport_error(_run_help(capsys, root, None, "--prepare-request", *args))
    assert not (root / RUNTIME).exists()


@pytest.mark.parametrize("change", ["missing", "stale", "selector"])
def test_transport_semantic_evidence_error_has_envelope_and_nonzero_status(source, tmp_path, capsys, change):
    """Evidence errors stay semantic errors and never become unsupported answers."""
    root = project(source, tmp_path / "consumer", platform="copilot")
    prepared, path = _prepare_help(capsys, root, source)
    path.write_bytes(b"/cg-work")
    if change == "missing":
        (source / catalog.CATALOG_OUTPUT_PATH).unlink()
    elif change == "stale":
        stale = source / ".github/prompts/cg-work.prompt.md"
        stale.write_bytes(stale.read_bytes() + b"\nChanged.\n")
    else:
        (root / manifest.LOCAL_CONFIG_PATH).write_text("---\nsuites: broken\n---\n", encoding="utf-8")
    status, envelope, stderr = _run_help(capsys, root, source, "--consume-request", prepared["requestId"])
    assert status == 3 and stderr.strip()
    assert envelope["operation"] == "query-completed" and envelope["result"]["state"] == "error"
    assert envelope["result"]["evidenceIds"] == [] and not path.exists()


def test_transport_runtime_queries_are_ignored_without_ignoring_the_manifest():
    """Read-only Git checks cover interrupted request paths, not only a text rule."""
    root = Path(cg_help.__file__).resolve().parents[1]
    relative = RUNTIME + "/" + REQUEST + ".query.txt"
    result = subprocess.run(["git", "check-ignore", "--no-index", "--stdin"], cwd=root,
                            input=(relative + "\n").encode("utf-8"), capture_output=True, check=False)
    result.stdout = result.stdout.decode("utf-8")
    assert result.returncode == 0 and result.stdout.strip() == relative
    manifest_check = subprocess.run(["git", "check-ignore", "--no-index", manifest.ACTIVE_MANIFEST_PATH],
                                    cwd=root, capture_output=True, text=True, check=False)
    assert manifest_check.returncode == 1


def test_transport_prepare_in_git_consumer_requires_runtime_ignore(transport, capsys, monkeypatch):
    """Exercise real Git in the consumer; ambient GIT_* redirection is inert."""
    root, source = transport
    repo = Path(cg_help.__file__).resolve().parents[1]
    git_dir = subprocess.run(["git", "rev-parse", "--absolute-git-dir"], cwd=repo,
                             capture_output=True, encoding="utf-8", check=True).stdout.strip()
    subprocess.run(["git", "init", "-q"], cwd=root, capture_output=True, check=True)
    monkeypatch.setenv("GIT_DIR", git_dir)
    monkeypatch.setenv("GIT_WORK_TREE", str(root))
    monkeypatch.setenv("GIT_OPTIONAL_LOCKS", "0")
    # The scrubbed environment must ignore the foreign GIT_DIR/GIT_WORK_TREE and
    # probe only the consumer repository: without the managed runtime ignore the
    # prepare must fail exactly as in an unredirected consumer.
    _assert_transport_error(_run_help(capsys, root, source, "--prepare-request"))
    assert not (root / RUNTIME).exists()
    (root / ".gitignore").write_bytes(b".compound-gpid/runtime/\n")
    _, path = _prepare_help(capsys, root, source)
    path.write_bytes(b"private pending query")
    status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all",
                             "--", ".compound-gpid/runtime/"], cwd=root,
                            capture_output=True, check=True)
    assert status.stdout == b""
    manifest_check = subprocess.run(["git", "check-ignore", "--no-index", manifest.ACTIVE_MANIFEST_PATH],
                                    cwd=root, capture_output=True, check=False)
    assert manifest_check.returncode == 1


def test_check_ignored_succeeds_without_git_repository(transport, monkeypatch):
    """A consumer without Git metadata has no ignore state to verify."""
    root, _source = transport
    cg_help._check_ignored(root, _REQUEST_UUID)


def test_check_ignored_fails_when_runtime_is_not_ignored(transport, monkeypatch):
    """A Git consumer without the managed runtime ignore fails closed."""
    root, _source = transport
    subprocess.run(["git", "init", "-q"], cwd=root, capture_output=True, check=True)
    with pytest.raises(catalog.HelpValidationError, match="untracked and ignored"):
        cg_help._check_ignored(root, _REQUEST_UUID)


def test_check_ignored_fails_on_inconclusive_git_probe(transport, monkeypatch):
    """An unknown git failure is never treated as absence of Git metadata."""

    def failing_probe(*_args, **_kwargs):
        import subprocess as probe_module

        return probe_module.CompletedProcess(
            _args, 1, stdout=b"", stderr=b"git is not available here"
        )

    monkeypatch.setattr(subprocess, "run", failing_probe)
    root, _source = transport
    with pytest.raises(catalog.HelpValidationError, match="Cannot verify"):
        cg_help._check_ignored(root, _REQUEST_UUID)
