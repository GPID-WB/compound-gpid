"""Offline native-probe contract checks, never installed-runtime V1 evidence.

Run: python -B -m pytest scripts/tests/test_autopilot_runtime.py -q
These tests inspect declared permissions and protocol requirements. They do not
invoke Task, establish effective permissions or qualify a host from fixtures.
"""

import copy
import json
import re
from pathlib import Path

import pytest

import cg_generate_targets as gen


ROOT = Path(__file__).resolve().parents[2]


def test_fix_agent_has_read_only_probe_before_mode_detection() -> None:
    """A bootstrap request must not fall into interactive repairs."""
    source = (ROOT / ".github/agents/cg-fix-problems.agent.md").read_text(encoding="utf-8")
    assert source.index("## Read-Only Bootstrap Probe") < source.index("**Mode detection**")
    assert "Never enter Auto Mode or Interactive Mode for a probe request" in source
    assert "No edits, tests or control writes in probe-only mode" in source
    assert "Do NOT delegate this step to a subagent" in source
    frontmatter = source.split("---", 2)[1]
    assert "'agent'" in frontmatter
    assert "'editFiles'" in frontmatter


def test_fix_agent_only_delegates_execution_to_general() -> None:
    """Typed override adds one execution leaf with the approved ask baseline."""
    mapping = gen.load_target_mapping(ROOT)
    kilo = next(t for t in mapping["targets"] if t["id"] == "kilo")
    assert kilo["assetMetadata"]["cg-fix-problems.agent.md"] == {
        "permission": {"task": {"*": "ask", "general": "allow"}}}
    source = (ROOT / ".github/agents/cg-fix-problems.agent.md").read_text(encoding="utf-8")
    assert "## Test-Execution Delegation" in source
    assert "execution_subagent" in source
    assert "cg-skill-pester-safety" in source
    assert "Never delegate file edits to a subagent" in source


@pytest.mark.parametrize("clause", [
    "Depth 1 must", "depth 2 can support direct stage leaves", "depth 3 must prove",
    "denied-target", "native-identity-unverified", "wrong mode", "unsupported-alias",
    "Missing model fields", "not inferred", "Offline fixtures", "4096",
])
def test_native_negative_cases_remain_required(clause: str) -> None:
    """Static requirements remain explicit; these checks are not native probes."""
    source = (ROOT / ".github/shared/autopilot-stage.contract.md").read_text(encoding="utf-8")
    assert clause in " ".join(source.split())


@pytest.mark.parametrize("child", ["general", "cg-code-quality", "unknown", "cg-workflow-*"])
def test_parent_rejects_non_stage_task_targets(child: str) -> None:
    """Offline metadata validation rejects undeclared direct children."""
    mapping = gen.load_target_mapping(ROOT)
    kilo = next(t for t in mapping["targets"] if t["id"] == "kilo")
    kilo["assetMetadata"]["cg-autopilot.agent.md"]["permission"]["task"][child] = "allow"
    assert gen.validate_target_mapping(mapping)


def _shapes() -> dict:
    """Read the source's closed offline shape notation, not a production API."""
    text = (ROOT / ".github/shared/autopilot-stage.contract.md").read_text(encoding="utf-8")
    section = text.split("## Bootstrap Packet Shapes\n", 1)[1]
    return json.loads(section.split("```json\n", 1)[1].split("```", 1)[0])


def _check(value: object, shape: dict, definitions: dict) -> None:
    """Interpret only the contract's finite shape notation for offline tests."""
    if "ref" in shape:
        shape = definitions[shape["ref"]]
    kinds = shape["type"] if isinstance(shape["type"], list) else [shape["type"]]
    types = {"object": dict, "array": list, "string": str, "integer": int,
             "boolean": bool, "null": type(None)}
    if type(value) not in [types[k] for k in kinds]:
        raise ValueError("type")
    if "enum" in shape and value not in shape["enum"]:
        raise ValueError("enum")
    if value is None:
        return
    if isinstance(value, dict):
        if set(value) != set(shape["fields"]):
            raise ValueError("fields")
        for key, item in value.items():
            _check(item, shape["fields"][key], definitions)
    elif isinstance(value, list):
        if not shape.get("min", 0) <= len(value) <= shape["max"]:
            raise ValueError("items")
        for item in value:
            _check(item, shape["items"], definitions)
    elif isinstance(value, str):
        if not shape.get("min", 0) <= len(value.encode("utf-8")) <= shape["utf8-max"]:
            raise ValueError("string-bytes")
        if "pattern" in shape and not re.fullmatch(shape["pattern"], value):
            raise ValueError("pattern")
    elif type(value) is int and not shape.get("min", value) <= value <= shape.get("max", value):
        raise ValueError("range")


def _packet(kind: str, raw: bytes, request: dict) -> dict:
    """Check offline shape and declared correlations; never return V1 success."""
    definitions = _shapes()
    if len(raw) > definitions[kind]["packet-max"]:
        raise ValueError("packet-bytes")
    def unique(pairs: list[tuple[str, object]]) -> dict:
        if len(dict(pairs)) != len(pairs):
            raise ValueError("duplicate-keys")
        return dict(pairs)
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
    _check(value, definitions[kind], definitions)
    if value["probe-id"] != request["probe-id"] or value["edge"] != request["edge"]:
        raise ValueError("correlation")
    if kind == "receipt":
        if (value["status"] == "succeeded") != (value["reason"] is None):
            raise ValueError("status-reason")
        observations = value["observations"]
        if value["status"] == "succeeded":
            if not observations or any(
                any(obs[key] is None for key in (
                    "task-id", "parent-task-id", "directory", "branch", "head", "tools"))
                or obs["settled"] is not True or obs["permission-status"] != "allowed"
                for obs in observations
            ):
                raise ValueError("incomplete-success")
    if kind == "qualification" and value["status"] == "complete":
        if (value["receipt-sha256"] is None or value["depth"] is None
                or not value["installed"] or not value["permissions"]
                or value["denial"] != "passed" or value["settled"] is not True
                or value["native-dispatch"] is not True
                or any(item["path"] is None or item["sha256"] is None for item in value["installed"])
                or any(any(item[key] is None for key in (
                    "mode", "declared-task-targets", "effective-task-targets"))
                    for item in value["permissions"])):
            raise ValueError("incomplete-qualification")
    return value


@pytest.fixture
def probe_packets() -> tuple[dict, dict]:
    """Complete synthetic example; identities are deliberately not runtime IDs."""
    request = {"schema-version": 1, "kind": "bootstrap-probe", "probe-id": "offline",
               "edge": "stage-general"}
    observation = {
        "agent": "general", "task-id": "fixture-leaf", "parent-task-id": "fixture-stage",
        "directory": "C:/fixture", "branch": "fixture", "head": "a" * 40,
        "tools": ["bash"], "permission-status": "allowed", "model-fields": None,
        "settled": True,
    }
    receipt = {**request, "kind": "bootstrap-probe-result", "status": "succeeded",
               "reason": None, "observations": [observation]}
    return request, receipt


def test_complete_offline_receipt_and_request(probe_packets: tuple[dict, dict]) -> None:
    """Both complete shapes pass; this is not a native qualification result."""
    request, receipt = probe_packets
    _packet("request", json.dumps(request).encode(), request)
    _packet("receipt", json.dumps(receipt).encode(), request)


@pytest.mark.parametrize("kind", ["request", "receipt"])
def test_every_required_packet_field_and_unknown_field(probe_packets: tuple[dict, dict], kind: str) -> None:
    """Delete each field separately and add one unknown field to valid packets."""
    request, receipt = probe_packets
    original = request if kind == "request" else receipt
    for key in original:
        candidate = copy.deepcopy(original)
        del candidate[key]
        with pytest.raises(ValueError, match="fields"):
            _packet(kind, json.dumps(candidate).encode(), request)
    with pytest.raises(ValueError, match="fields"):
        _packet(kind, json.dumps({**original, "scope": ["../escape"]}).encode(), request)


@pytest.mark.parametrize("field,value,error", [
    ("schema-version", True, "type"), ("schema-version", "1", "type"),
    ("schema-version", 2, "enum"), ("observations", {}, "type"),
    ("observations", None, "type"), ("observations", [None], "type"),
    ("status", "complete", "enum"), ("probe-id", "other", "correlation"),
    ("edge", "stage-reviewer", "correlation"), ("reason", "denied", "status-reason"),
])
def test_malformed_receipt_fields(probe_packets: tuple[dict, dict], field: str, value: object, error: str) -> None:
    """Each single mutation has an explicit shape or correlation failure."""
    request, receipt = probe_packets
    receipt[field] = value
    with pytest.raises(ValueError, match=error):
        _packet("receipt", json.dumps(receipt).encode(), request)


@pytest.mark.parametrize("field,value,error", [
    ("tools", {}, "type"), ("tools", [1], "type"),
    ("permission-status", True, "type"), ("model-fields", {}, "type"),
    ("settled", 1, "type"), ("settled", False, "incomplete-success"),
    ("task-id", None, "incomplete-success"), ("agent", "unknown", "enum"),
])
def test_malformed_observation(probe_packets: tuple[dict, dict], field: str, value: object, error: str) -> None:
    """Check typed native observations, including unavailable success evidence."""
    request, receipt = probe_packets
    receipt["observations"][0][field] = value
    with pytest.raises(ValueError, match=error):
        _packet("receipt", json.dumps(receipt).encode(), request)


def test_observation_count_and_exact_byte_boundary(probe_packets: tuple[dict, dict]) -> None:
    """Four observations and 4096 bytes fit; five or 4097 bytes must fail."""
    request, receipt = probe_packets
    receipt["observations"] *= 4
    raw = json.dumps(receipt).encode()
    _packet("receipt", raw + b" " * (4096 - len(raw)), request)
    with pytest.raises(ValueError, match="packet-bytes"):
        _packet("receipt", raw + b" " * (4097 - len(raw)), request)
    receipt["observations"].append(receipt["observations"][0])
    with pytest.raises(ValueError, match="items"):
        _packet("receipt", json.dumps(receipt).encode(), request)


def test_fixed_reviewer_scope_is_bounded() -> None:
    """Reviewer paths are fixed, contained native assets, not caller input."""
    definitions = _shapes()
    assert definitions["reviewer-scope"] == {
        "paths": [".kilo/agents/cg-autopilot.md", ".kilo/agents/cg-workflow-stage.md",
                  ".kilo/commands/cg-autopilot.md"],
        "per-file-bytes": 16384, "total-bytes": 49152,
    }
    contract = (ROOT / ".github/shared/autopilot-stage.contract.md").read_text(encoding="utf-8")
    assert "reject links, aliases, missing files and paths outside the worktree" in contract


def test_primary_qualification_record_has_required_evidence() -> None:
    """Primary-visible evidence has a closed shape independent of child claims."""
    fields = _shapes()["qualification"]["fields"]
    assert {"installed", "depth", "denial", "settled", "permissions",
             "receipt-sha256", "native-dispatch", "probe-id", "edge"} <= set(fields)


@pytest.mark.parametrize("status", ["blocked", "complete"])
def test_offline_qualification_record_types_and_missing_fields(probe_packets: tuple[dict, dict], status: str) -> None:
    """Primary record shape covers hashes/depth/denial; fake data is not V1."""
    request, _ = probe_packets
    record = {**request, "kind": "bootstrap-qualification", "status": "complete",
              "receipt-sha256": "b" * 64, "installed": [{"path": "fixture", "sha256": "a" * 64}],
              "depth": 3, "denial": "passed", "settled": True, "native-dispatch": True,
              "permissions": [{"agent": "general", "mode": "subagent",
                               "declared-task-targets": [], "effective-task-targets": []}]}
    _packet("qualification", json.dumps(record).encode(), request)
    for key in record:
        candidate = {k: v for k, v in record.items() if k != key}
        with pytest.raises(ValueError, match="fields"):
            _packet("qualification", json.dumps(candidate).encode(), request)
    for key, value in [("depth", True), ("depth", 0), ("installed", {}), ("permissions", None),
                       ("receipt-sha256", "bad"), ("settled", 1), ("denial", {}),
                       ("native-dispatch", False), ("depth", None), ("installed", [])]:
        with pytest.raises(ValueError):
            _packet("qualification", json.dumps({**record, key: value}).encode(), request)
    # An unknown source can be recorded, but must never qualify as complete.
    record["installed"][0]["path"] = None
    record["status"] = status
    if status == "blocked":
        assert _packet("qualification", json.dumps(record).encode(), request)["status"] == "blocked"
    else:
        with pytest.raises(ValueError, match="incomplete-qualification"):
            _packet("qualification", json.dumps(record).encode(), request)


def test_blocked_receipt_and_duplicate_keys(probe_packets: tuple[dict, dict]) -> None:
    """Unavailable observations stay blocked; duplicate keys never override status."""
    request, receipt = probe_packets
    receipt.update(status="blocked", reason="native-identity-unverified", observations=[])
    raw = json.dumps(receipt).encode()
    _packet("receipt", raw, request)
    with pytest.raises(ValueError, match="duplicate-keys"):
        _packet("receipt", raw[:-1] + b', "status": "succeeded"}', request)
    for candidate in ([], None, 1):
        with pytest.raises(ValueError, match="type"):
            _packet("receipt", json.dumps(candidate).encode(), request)


def test_observation_missing_and_unknown_fields(probe_packets: tuple[dict, dict]) -> None:
    """Every observation field is required even when its value can be null."""
    request, receipt = probe_packets
    original = receipt["observations"][0]
    for key in original:
        receipt["observations"] = [{k: v for k, v in original.items() if k != key}]
        with pytest.raises(ValueError, match="fields"):
            _packet("receipt", json.dumps(receipt).encode(), request)
    receipt["observations"] = [{**original, "extra": "not-authority"}]
    with pytest.raises(ValueError, match="fields"):
        _packet("receipt", json.dumps(receipt).encode(), request)
