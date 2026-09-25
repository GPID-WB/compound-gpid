"""Step7 source-bound support evidence and offline host protocol tests."""
from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


def support_module():
    """Assert the required implementation exists before importing it."""
    assert importlib.util.find_spec("help.support") is not None, "Step7 support verifier is missing"
    return importlib.import_module("help.support")


def git(root, *args):
    """Run Git only in this owned synthetic history."""
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def write(root, path, content):
    destination = root / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content.encode("utf-8"))


def successful_probes(support):
    """Synthetic success is test-only, never a production evidence writer."""
    return [dict(name=name, arguments=list(support.PROBE_ARGUMENTS),
                 receivedQuerySha256=hashlib.sha256(text.encode()).hexdigest(),
                 outcome="passed") for name, text in support.PROBE_CASES.items()]


@pytest.fixture
def history(tmp_path):
    support = support_module()
    root = tmp_path / "h"
    root.mkdir()
    git(root, "init", "-b", "dev")
    # Per-command identity is confined to the synthetic repository, not git config.
    write(root, ".github/shared/help-catalog.json", json.dumps({
        "sourceDigest": "a" * 64, "commands": [], "workflows": []}))
    write(root, ".github/shared/target-mapping.json", json.dumps({"targets": [
        {"id": platform, "outputPaths": {"commands": directory}}
        for platform, directory in support.PROMPT_ROOTS.items()]}))
    for platform, directory in support.PROMPT_ROOTS.items():
        suffix = ".prompt.md" if platform == "copilot" else ".md"
        write(root, directory + "/cg-help" + suffix, "# Help " + platform + "\n")
    write(root, "scripts/help/query.py", "# query implementation\n")
    write(root, "scripts/help/support.py", "# verifier implementation\n")
    git(root, "add", ".")
    git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "commit", "-m", "subject")
    subject = git(root, "rev-parse", "HEAD")
    evidence = support.build_evidence(root, subject)
    return support, root, evidence


def commit(root, message):
    git(root, "add", ".")
    git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", message)


def test_step7_support_implementation_exists():
    support_module()


def test_duplicate_git_blobs_retain_every_sensitive_path(history):
    support, root, _ = history
    content = "identical generated adapter\n"
    for directory in (".claude/commands", ".kilo/commands", ".opencode/commands"):
        write(root, directory + "/cg-help.md", content)
    commit(root, "same content at distinct paths")
    subject = git(root, "rev-parse", "HEAD")
    bindings = support.subject_bindings(root, subject)
    rows = {row["path"]: row for row in bindings["sensitivePaths"]}
    for directory in (".claude/commands", ".kilo/commands", ".opencode/commands"):
        assert rows[directory + "/cg-help.md"]["sha256"] == hashlib.sha256(content.encode()).hexdigest()


def test_working_bytes_honor_only_protected_crlf_checkout_policy():
    support = support_module()
    assert hasattr(support, "checkout_bytes")
    attributes = Path(__file__).resolve().parents[2].joinpath(".gitattributes").read_bytes()
    raw = b"@echo off\nexit /b 0\n"
    assert support.checkout_bytes("bin/cg-help.cmd", raw, attributes) == b"@echo off\r\nexit /b 0\r\n"
    assert support.checkout_bytes("scripts/cg_help.py", raw, attributes) == raw
    with pytest.raises(ValueError, match="checkout policy"):
        support.checkout_bytes("bin/cg-help.cmd", raw, attributes + b"bin/cg-help.cmd eol=lf\n")


def test_subject_verifier_accepts_declared_crlf_but_rejects_mixed_or_changed_bytes(history):
    support, root, evidence = history
    attributes = Path(__file__).resolve().parents[2].joinpath(".gitattributes").read_bytes()
    root.joinpath(".gitattributes").write_bytes(attributes)
    wrapper = root / "bin/cg-help.cmd"
    wrapper.parent.mkdir()
    wrapper.write_bytes(b"@echo off\r\nexit /b 0\r\n")
    commit(root, "declared Windows checkout")
    subject = git(root, "rev-parse", "HEAD")
    evidence = support.build_evidence(root, subject)
    support.verify_evidence(root, evidence)
    wrapper.write_bytes(b"@echo off\r\nexit /b 0\n")
    with pytest.raises(ValueError, match="working bytes"):
        support.verify_evidence(root, evidence)
    wrapper.write_bytes(b"@echo off\r\nexit /b 1\r\n")
    with pytest.raises(ValueError, match="changed"):
        support.verify_evidence(root, evidence)


def test_probe_flow_validator_exists():
    assert hasattr(support_module(), "validate_host_flow"), "Step7 host operation/final-output validator is missing"


def test_support_cli_rejects_missing_evidence(tmp_path, capsys):
    verifier = importlib.import_module("cg_verify_help_support")
    assert verifier.main(["--root", str(tmp_path), "--evidence", "missing.json"]) == 2
    assert "verification failed" in capsys.readouterr().err


def test_support_cli_preserves_error_contract_for_stale_catalog(tmp_path, capsys, monkeypatch):
    """A stale catalog must give the documented failure code, not a traceback."""
    verifier = importlib.import_module("cg_verify_help_support")
    write(tmp_path, "support.json", "{}")
    monkeypatch.setattr(verifier.support, "verify_evidence", lambda *_: None)

    def stale(_root):
        raise verifier.catalog.HelpCatalogStaleError("catalog differs from generated bytes")

    monkeypatch.setattr(verifier.catalog, "check_catalog", stale)
    assert verifier.main(["--root", str(tmp_path), "--evidence", "support.json"]) == 2
    assert "verification failed" in capsys.readouterr().err


def test_support_accepts_exact_subject_and_evidence_only_followup(history):
    support, root, evidence = history
    support.verify_evidence(root, evidence)
    write(root, ".cg-docs/work-reports/support.json", json.dumps(evidence))
    write(root, "docs/help-support.md", "Unverified hosts have no runtime claim.\n")
    commit(root, "evidence only")
    support.verify_evidence(root, evidence)


@pytest.mark.parametrize("field", ["subjectCommit", "subjectTree", "sensitiveDigest"])
def test_support_rejects_missing_foreign_identity_or_digest(history, field):
    support, root, evidence = history
    evidence[field] = "f" * (64 if field == "sensitiveDigest" else 40)
    with pytest.raises(ValueError):
        support.verify_evidence(root, evidence)


@pytest.mark.parametrize("field", ["catalogSourceDigest", "catalogSha256", "canonicalPromptSha256",
                                    "targetMappingSha256", "generatedPromptSha256"])
def test_support_rejects_each_stale_platform_binding(history, field):
    support, root, evidence = history
    evidence["platforms"][0][field] = "f" * 64
    with pytest.raises(ValueError, match="binding"):
        support.verify_evidence(root, evidence)


@pytest.mark.parametrize("path", ["scripts/help/query.py", "scripts/help/new.py",
                                  ".github/prompts/cg-help.prompt.md",
                                  ".kilo/commands/cg-help.md"])
@pytest.mark.parametrize("committed", [False, True])
def test_support_rejects_changed_or_added_bound_paths(history, path, committed):
    support, root, evidence = history
    write(root, path, "changed bytes\n")
    if committed:
        commit(root, "changed bound implementation")
    with pytest.raises(ValueError, match="sensitive"):
        support.verify_evidence(root, evidence)


def test_support_rejects_nonancestor_subject(history):
    support, root, evidence = history
    git(root, "checkout", "--orphan", "unrelated")
    write(root, "unrelated.txt", "different history\n")
    commit(root, "unrelated")
    with pytest.raises(ValueError, match="ancestor"):
        support.verify_evidence(root, evidence)


def test_support_rejects_existing_default_checkout_instead_of_exact_subject(history):
    support, root, evidence = history
    write(root, "default-only.txt", "default branch moved\n")
    commit(root, "default branch differs from certified subject")
    evidence["subjectCommit"] = git(root, "rev-parse", "HEAD")
    with pytest.raises(ValueError, match="Subject tree"):
        support.verify_evidence(root, evidence)


@pytest.mark.parametrize("mutation", ["missing-platform", "raw-query", "duplicate",
                                       "future-schema", "runtime-claim"])
def test_support_schema_and_platform_matrix_fail_closed(history, mutation):
    support, root, evidence = history
    if mutation == "missing-platform":
        evidence["platforms"].pop()
    elif mutation == "raw-query":
        evidence["query"] = "secret input"
    elif mutation == "duplicate":
        evidence["platforms"][0] = dict(evidence["platforms"][3])
    elif mutation == "runtime-claim":
        evidence["runtimeCertifications"] = []
    else:
        evidence["schemaVersion"] = 3
    with pytest.raises(ValueError):
        support.verify_evidence(root, evidence)


def test_support_has_no_required_host_or_runtime_claim(history):
    support, root, evidence = history
    assert all(set(row) == {
        "platform", "catalogSourceDigest", "catalogSha256",
        "canonicalPromptSha256", "targetMappingSha256", "generatedPromptSha256",
    } for row in evidence["platforms"])
    support.verify_evidence(root, evidence)


def test_generator_writes_only_the_stable_current_manifest(history, monkeypatch):
    support, root, evidence = history
    generator = importlib.import_module("cg_generate_help_support")
    root.joinpath(".cg-docs/work-reports").mkdir(parents=True)
    monkeypatch.setattr(generator.catalog, "check_catalog", lambda _: None)
    assert generator.main(["--root", str(root)]) == 0
    actual = json.loads(root.joinpath(generator.OUTPUT_PATH).read_text(encoding="utf-8"))
    assert actual == evidence
    with pytest.raises(SystemExit, match="output must be"):
        generator.main(["--root", str(root), "--output", "support.json"])


@pytest.mark.parametrize("received", ["$ARGUMENTS", "", "plan review ; normalized"])
def test_probe_rejects_literal_missing_or_normalized_query(received):
    support = support_module()
    receipt = successful_probes(support)[2]
    receipt["receivedQuerySha256"] = hashlib.sha256(received.encode()).hexdigest()
    with pytest.raises(ValueError, match="fingerprint"):
        support.validate_probe(receipt)
