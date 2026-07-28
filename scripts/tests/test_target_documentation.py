"""Stable documentation contracts for generated native target packaging."""
from __future__ import annotations

import json
import re
import urllib.parse
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCUMENT_PATHS = (
    "README.md",
    "docs/context-files.md",
    "docs/installation.md",
    "docs/reference.md",
    "docs/troubleshooting.md",
)
DOCUMENTS = {
    path: (REPO_ROOT / path).read_text(encoding="utf-8") for path in DOCUMENT_PATHS
}
CORPUS = "\n".join(DOCUMENTS.values()).lower()
LOCAL_LINK = re.compile(r"(?<!!)\[[^]]*]\(([^)]+)\)")


def _assert_terms(text: str, *terms: str) -> None:
    missing = [term for term in terms if term.lower() not in text.lower()]
    assert not missing, f"Missing documentation contract terms: {missing}"


def _slug(heading: str) -> str:
    heading = re.sub(r"<[^>]+>", "", heading).strip().lower()
    heading = re.sub(r"[^\w\- ]", "", heading)
    return re.sub(r"[ -]+", "-", heading).strip("-")


def _anchors(markdown: Path) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    in_fence = False
    for line in markdown.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if in_fence:
            continue
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if match:
            base = _slug(match.group(1))
            count = counts.get(base, 0)
            anchors.add(base if count == 0 else f"{base}-{count}")
            counts[base] = count + 1
    return anchors


def test_docs_describe_atomic_recursive_skill_bundles_and_opaque_executables() -> None:
    _assert_terms(CORPUS, "atomic", "skill bundle", "regular files", "include by default")
    _assert_terms(CORPUS, "executable", "opaque", "never executed")


def test_docs_list_every_target_local_support_root_from_mapping() -> None:
    mapping = json.loads(
        (REPO_ROOT / ".github/shared/target-mapping.json").read_text(encoding="utf-8")
    )
    for target in mapping["targets"]:
        if not target.get("generatedTreePath"):
            continue
        for kind in ("commands", "skills", "agents", "instructions", "shared"):
            path = target["outputPaths"][kind]
            assert path.lower() in CORPUS, f"Undocumented {target['id']} {kind} root: {path}"


def test_docs_define_fixed_deterministic_generated_ownership_manifests() -> None:
    for path in (
        ".claude/.compound-gpid-generated.json",
        ".agents/.compound-gpid-generated.json",
        ".opencode/.compound-gpid-generated.json",
    ):
        assert path in CORPUS, f"Undocumented generated ownership manifest: {path}"
    _assert_terms(
        CORPUS,
        "schemaVersion",
        "target",
        "policyVersion",
        "files",
        "path",
        "source",
        "kind",
        "sha256",
        "executable",
        "deterministic",
    )


def test_docs_separate_generated_ownership_from_consumer_managed_files() -> None:
    _assert_terms(CORPUS, ".compound-gpid-generated.json", ".compound-gpid/managed-files.json")
    assert re.search(
        r"\.compound-gpid-generated\.json.{0,500}(?:different|distinct|separate|not the same).{0,500}"
        r"\.compound-gpid/managed-files\.json|"
        r"\.compound-gpid/managed-files\.json.{0,500}(?:different|distinct|separate|not the same).{0,500}"
        r"\.compound-gpid-generated\.json",
        CORPUS,
        re.DOTALL,
    ), "Generated-tree and consumer-project ownership must be explicitly distinguished"


def test_docs_cover_checksum_cleanup_manifest_last_recovery_and_conflicts() -> None:
    _assert_terms(CORPUS, "checksum", "stale", "manifest", "written last", "recovery")
    for conflict in ("modified stale", "malformed manifest", "unsafe path", "unowned destination"):
        assert conflict in CORPUS, f"Missing generated-tree conflict guidance: {conflict}"
    assert "maintainer" in CORPUS and "resolve" in CORPUS


def test_docs_define_ci_drift_release_and_evidence_gates() -> None:
    _assert_terms(CORPUS, "CI", "drift", "release gate", "isolated", "dependency closure")
    _assert_terms(CORPUS, "deterministic", "real CLI", "optional", "evidence")


def test_docs_do_not_claim_generated_skills_contain_only_skill_md() -> None:
    obsolete_claims = (
        r"skills?\s+(?:contain|include|consist of|are)\s+only\s+`?skill\.md`?",
        r"only\s+`?skill\.md`?\s+(?:is|gets)\s+(?:copied|packaged|generated)",
        r"one[- ]file\s+skills?",
    )
    for path, text in DOCUMENTS.items():
        for pattern in obsolete_claims:
            assert not re.search(pattern, text, re.IGNORECASE), (
                f"Obsolete single-file skill claim in {path}: {pattern}"
            )


@pytest.mark.parametrize("document", DOCUMENT_PATHS)
def test_document_local_markdown_links_and_anchors_resolve(document: str) -> None:
    source = REPO_ROOT / document
    for raw_link in LOCAL_LINK.findall(DOCUMENTS[document]):
        link = raw_link.strip().split(maxsplit=1)[0].strip("<>")
        parsed = urllib.parse.urlparse(link)
        if parsed.scheme or link.startswith(("mailto:", "/")):
            continue
        relative = urllib.parse.unquote(parsed.path)
        target = source if not relative else (source.parent / relative).resolve()
        try:
            target.relative_to(REPO_ROOT.resolve())
        except ValueError:
            pytest.fail(f"Local link escapes repository in {document}: {raw_link}")
        assert target.is_file(), f"Broken local link in {document}: {raw_link}"
        if parsed.fragment and target.suffix.lower() == ".md":
            anchor = urllib.parse.unquote(parsed.fragment).lower()
            assert anchor in _anchors(target), (
                f"Broken Markdown anchor in {document}: {raw_link}"
            )
