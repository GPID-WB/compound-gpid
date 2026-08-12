"""Stable documentation contracts for generated native target packaging."""
from __future__ import annotations

import ast
import json
import re
import urllib.parse
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCUMENT_PATHS = (
    "README.md",
    "docs/context-files.md",
    "docs/workflow.md",
    "docs/reference/commands.md",
    "docs/reference/files.md",
    "docs/configuration/index.md",
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
        ".kilo/.compound-gpid-generated.json",
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


def test_python_instructions_require_non_clobbering_filesystem_operations() -> None:
    canonical_path = REPO_ROOT / ".github/instructions/python.instructions.md"
    canonical = canonical_path.read_text(encoding="utf-8")
    _assert_terms(
        canonical,
        "preserve concurrent winners",
        "shared `secure_fs` APIs",
        "non-replacing collision semantics",
        "preserve quarantine/recovery artifacts",
        "process umask",
        "reject hard-link aliases",
        "Atomic replacement alone is not non-clobbering",
    )
    for generated_root in (".claude", ".agents", ".opencode", ".kilo"):
        generated = (
            REPO_ROOT / generated_root / "instructions/python.instructions.md"
        ).read_text(encoding="utf-8")
        assert generated == canonical
    _assert_terms(CORPUS, "deterministic", "real CLI", "optional", "evidence")


def test_docs_cover_artifact_view_authority_versions_paths_and_modes() -> None:
    _assert_terms(
        CORPUS,
        "canonical Markdown",
        "artifact-schema-version",
        "compatible legacy",
        ".cg-docs/views/brainstorms/",
        ".cg-docs/views/plans/",
        ".cg-docs/views/documents/",
        "cg-render-artifact --automatic",
        "cg-render-artifact --validate-only",
        "cg-render-artifact --check",
    )

def test_docs_cover_generic_markdown_publication_core_contracts() -> None:
    _assert_terms(
        CORPUS,
        "cg-publish-markdown",
        "generic Markdown",
        ".cg-docs/views/documents/",
        "generic-markdown",
        "provenance schema 2",
        "outputPath",
        "one source owner",
        "reference",
        "theme version",
        "NOTE",
        "TIP",
        "IMPORTANT",
        "WARNING",
        "CAUTION",
        "DECISION",
        "PROS",
        "CONS",
        "PNG",
        "JPEG",
        "GIF",
        "WebP",
        "alt text",
        "5 MiB",
        "non-clobbering",
        "recovery",
        "dependency-free",
        "network-free",
        "browser-free",
    )


def test_docs_preserve_typed_authority_and_follow_up_boundary() -> None:
    _assert_terms(
        CORPUS,
        "Brainstorms and Plans",
        "strict validation",
        "cg-render-artifact",
        "cannot",
        "editorial theme",
        "blocked follow-up",
        "no agent publishing workflow",
        "no browser evidence",
    )


def test_docs_distinguish_opt_out_skip_provenance_and_recovery() -> None:
    _assert_terms(
        CORPUS,
        "artifact-html: false",
        "--no-html",
        "never disable validation",
        "exact pinned-byte source SHA-256",
        "missing",
        "stale",
        "current",
        "one-file recovery",
        "prior valid view",
    )


def test_docs_cover_context_exclusion_open_design_and_v1_boundaries() -> None:
    _assert_terms(
        CORPUS,
        "generated HTML bodies",
        "model context",
        "Open Design",
        "design-time only",
        "no bulk",
        "no hosted",
        "no PDF",
        "no live execution updates",
    )


def test_complete_reference_documents_render_modes_outputs_and_exit_codes() -> None:
    reference = (REPO_ROOT / "docs/reference.md").read_text(encoding="utf-8")
    _assert_terms(
        reference,
        "cg-render-artifact",
        "--automatic",
        "--validate-only",
        "--check",
        "missing",
        "stale",
        "current",
        "exit code",
        "artifact-html",
    )


def test_installation_lists_renderer_on_windows_and_macos() -> None:
    installation = (REPO_ROOT / "docs/installation.md").read_text(encoding="utf-8")
    assert installation.count("cg-render-artifact") >= 2
    _assert_terms(installation, "Python 3.8+", "Brainstorm", "Plan", "validation")

def test_installation_lists_generic_publisher_on_windows_and_macos() -> None:
    installation = (REPO_ROOT / "docs/installation.md").read_text(encoding="utf-8")
    assert installation.count("cg-publish-markdown") >= 2
    _assert_terms(installation, "Python 3.8+", "generic Markdown", "reference")


def test_public_artifact_view_functions_have_complete_docstrings() -> None:
    missing = []
    paths = sorted((REPO_ROOT / "scripts/artifact_views").glob("*.py"))
    paths.append(REPO_ROOT / "scripts/secure_fs.py")
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            parent = parents.get(node)
            if (
                node.name.startswith("_")
                or not isinstance(parent, (ast.Module, ast.ClassDef))
                or isinstance(parent, ast.ClassDef) and parent.name.startswith("_")
            ):
                continue
            docstring = ast.get_docstring(node) or ""
            for section in ("Args:", "Returns:", "Example:"):
                if section not in docstring:
                    missing.append(
                        f"{path.relative_to(REPO_ROOT)}:{node.name}:{section}"
                    )
    assert not missing, f"Incomplete public API docstrings: {missing}"


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


MODULAR_GUIDE = REPO_ROOT / "docs/modular-guide.md"
MODULAR_TOPICS = (
    "choosing a suite",
    "suites compose",
    "module preferences",
    "extension rules",
    "migration",
)


def test_modular_guide_exists_and_covers_all_five_topics() -> None:
    assert MODULAR_GUIDE.is_file(), "docs/modular-guide.md is missing"
    text = MODULAR_GUIDE.read_text(encoding="utf-8").lower()
    for topic in MODULAR_TOPICS:
        assert topic.lower() in text, f"Modular guide missing topic: {topic!r}"


def test_modular_guide_is_linked_from_reference_and_skills_index() -> None:
    reference = (REPO_ROOT / "docs/reference.md").read_text(encoding="utf-8")
    skills_index = (REPO_ROOT / "docs/skills/index.md").read_text(encoding="utf-8")
    assert "modular-guide.md" in reference
    assert "modular-guide.md" in skills_index



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
