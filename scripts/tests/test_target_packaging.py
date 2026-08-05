"""Red-phase tests for atomic skill-bundle packaging."""
from __future__ import annotations

import hashlib
import json
import os
import stat
import urllib.parse
from pathlib import Path
from pathlib import PurePosixPath

import pytest

import cg_generate_targets as gen


REPO_ROOT = Path(__file__).resolve().parents[2]
PILOT = "cg-skill-brainstorming"
PILOT_FILES = {
    "SKILL.md",
    "references/decision-template.md",
    "workflows/approach-comparison.md",
    "workflows/requirement-elicitation.md",
}
TARGET_SKILL_ROOTS = {
    "claude-code": ".claude/skills",
    "codex": ".agents/skills",
    "opencode": ".opencode/skills",
    "kilo": ".kilo/skills",
}


def _write_bytes(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _mkfifo(path: Path) -> None:
    mkfifo = getattr(os, "mkfifo", None)
    if mkfifo is None:
        pytest.skip("FIFO creation is unavailable")
    mkfifo.__call__(path)


def _fixture_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    mapping = json.loads(
        (REPO_ROOT / ".github/shared/target-mapping.json").read_text(encoding="utf-8")
    )
    _write_bytes(
        root / ".github/shared/target-mapping.json",
        (json.dumps(mapping) + "\n").encode(),
    )
    _write_bytes(root / ".github/shared/runtime-contract.md", b"# Runtime contract\n")
    _write_bytes(
        root / ".github/prompts/cg-fixture.prompt.md",
        b"---\ndescription: Fixture\n---\n\n# Fixture\n",
    )
    _write_bytes(
        root / ".github/agents/cg-fixture.agent.md",
        b"---\ndescription: Fixture\ntools: [read]\n---\n\n# Fixture\n",
    )
    _write_bytes(root / ".github/instructions/python.instructions.md", b"# Python\n")
    return root


def _skill_file(
    root: Path,
    relative: str,
    content: bytes,
    skill_name: str = PILOT,
) -> Path:
    return _write_bytes(root / ".github/skills" / skill_name / relative, content)


def _plan(root: Path) -> gen.GenerationPlan:
    return gen.build_generation_plan(
        root,
        gen.load_target_mapping(root),
        gen.scan_canonical_assets(root),
    )


def _pilot_entries(plan: gen.GenerationPlan, target_id: str):
    prefix = f"{TARGET_SKILL_ROOTS[target_id]}/{PILOT}/"
    return tuple(
        entry
        for entry in plan.by_target[target_id].entries
        if entry.destination.startswith(prefix)
    )


def _relative_inventory(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }


def _canonical_skills(root: Path = REPO_ROOT) -> tuple[Path, ...]:
    return tuple(sorted(path for path in (root / ".github/skills").glob("cg-skill-*") if path.is_dir()))


def _local_markdown_targets(markdown: Path, bundle_root: Path) -> tuple[Path, ...]:
    text = gen._strip_fenced_code(  # pylint: disable=protected-access
        markdown.read_text(encoding="utf-8")
    )
    references = gen.MARKDOWN_LINK_PATTERN.findall(text)
    references.extend(gen.MARKDOWN_REFERENCE_PATTERN.findall(text))
    targets: list[Path] = []
    for raw_reference in references:
        reference = urllib.parse.unquote(raw_reference).split("#", 1)[0].split("?", 1)[0]
        parsed = urllib.parse.urlparse(reference)
        if not reference or parsed.scheme or reference.startswith(("#", "/")):
            continue
        relative = PurePosixPath(markdown.relative_to(bundle_root).as_posix()).parent / reference
        targets.append(bundle_root.joinpath(*relative.parts))
    return tuple(targets)


def _assert_markdown_closure(bundle_root: Path) -> None:
    for markdown in bundle_root.rglob("*.md"):
        for target in _local_markdown_targets(markdown, bundle_root):
            try:
                target.resolve().relative_to(bundle_root.resolve())
            except ValueError:
                pytest.fail(f"Escaping skill-local link from {markdown}: {target}")
            assert target.is_file(), f"Broken skill-local link from {markdown}: {target}"


def _is_executable(path: Path) -> bool:
    return bool(path.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))


def test_pilot_canonical_and_all_generated_targets_have_exact_four_file_inventory() -> None:
    canonical = REPO_ROOT / ".github/skills" / PILOT
    assert _relative_inventory(canonical) == PILOT_FILES

    for skill_root in TARGET_SKILL_ROOTS.values():
        generated = REPO_ROOT / skill_root / PILOT
        assert _relative_inventory(generated) == PILOT_FILES


def test_every_canonical_skill_recursively_matches_all_generated_targets() -> None:
    mapping = json.loads(
        (REPO_ROOT / ".github/shared/target-mapping.json").read_text(encoding="utf-8")
    )
    targets = {
        target["outputPaths"]["skills"]: target
        for target in mapping["targets"]
        if target.get("generatedTreePath")
    }
    assets = gen.scan_canonical_assets(REPO_ROOT)
    for canonical in _canonical_skills():
        canonical_inventory = _relative_inventory(canonical)
        assert canonical_inventory, f"Empty canonical skill bundle: {canonical.name}"
        for skill_root in TARGET_SKILL_ROOTS.values():
            generated = REPO_ROOT / skill_root / canonical.name
            assert _relative_inventory(generated) == canonical_inventory
            for relative in canonical_inventory:
                source = canonical / relative
                output = generated / relative
                if relative.casefold().endswith((".md", ".markdown")):
                    source_identity = source.relative_to(REPO_ROOT).as_posix()
                    expected = gen._rewrite_runtime_dependencies(  # pylint: disable=protected-access
                        source.read_text(encoding="utf-8"),
                        targets[skill_root],
                        assets,
                        source_identity,
                    ).encode("utf-8")
                    assert output.read_bytes() == expected
                else:
                    assert hashlib.sha256(output.read_bytes()).digest() == hashlib.sha256(source.read_bytes()).digest()
                assert _is_executable(output) == _is_executable(source)


def test_fixture_packages_nested_unknown_binary_and_executable_resources_in_all_targets(
    tmp_path: Path,
) -> None:
    root = _fixture_repo(tmp_path)
    fixtures = {
        "SKILL.md": b"[workflow](workflows/deep/flow.md)\n",
        "workflows/deep/flow.md": b"[template](../../templates/example.tpl)\n",
        "references/topic.md": b"# Topic\n",
        "packages/tool/source.xyzzy": b"future extension\n",
        "assets/pixels.dat": bytes(range(256)),
        "templates/example.tpl": b"{{ value }}\n",
        "evaluations/cases.json": b"{}\n",
        "benchmarks/baseline.csv": b"name,value\nfixture,1\n",
        "grades/rubric.txt": b"pass\n",
        "fixtures/input.raw": b"\x00\xfffixture",
        "source-packs/source.txt": b"source\n",
        "scripts/check.tool": b"opaque executable\n",
    }
    for relative, content in fixtures.items():
        path = _skill_file(root, relative, content)
        if relative == "scripts/check.tool":
            path.chmod(path.stat().st_mode | stat.S_IXUSR)

    plan = _plan(root)

    for target_id, skill_root in TARGET_SKILL_ROOTS.items():
        entries = _pilot_entries(plan, target_id)
        assert {
            Path(entry.destination).relative_to(Path(skill_root) / PILOT).as_posix()
            for entry in entries
        } == set(fixtures)
        for entry in entries:
            relative = Path(entry.destination).relative_to(Path(skill_root) / PILOT).as_posix()
            assert entry.content == fixtures[relative]
            assert entry.sha256 == hashlib.sha256(fixtures[relative]).hexdigest()
            assert entry.executable == (relative == "scripts/check.tool" and os.name != "nt")


def test_pilot_plan_has_exact_bytes_hashes_and_executable_flags_for_all_targets(
    tmp_path: Path,
) -> None:
    root = _fixture_repo(tmp_path)
    canonical = REPO_ROOT / ".github/skills" / PILOT
    for relative in PILOT_FILES:
        source = canonical / relative
        destination = _skill_file(root, relative, source.read_bytes())
        destination.chmod(source.stat().st_mode)

    plan = _plan(root)

    for target_id, skill_root in TARGET_SKILL_ROOTS.items():
        entries = _pilot_entries(plan, target_id)
        assert {
            Path(entry.destination).relative_to(Path(skill_root) / PILOT).as_posix()
            for entry in entries
        } == PILOT_FILES
        for entry in entries:
            relative = Path(entry.destination).relative_to(Path(skill_root) / PILOT)
            source = root / ".github/skills" / PILOT / relative
            expected = gen._skill_bundle_content(source)  # pylint: disable=protected-access
            assert entry.source == source.relative_to(root).as_posix()
            assert entry.content == expected
            assert entry.sha256 == hashlib.sha256(expected).hexdigest()
            assert entry.executable == _is_executable(source)


def test_pilot_nested_relative_markdown_links_are_valid(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    _skill_file(root, "SKILL.md", b"[workflow](workflows/flow.md)\n")
    _skill_file(root, "workflows/flow.md", b"![reference](../references/ref.md#details)\n")
    _skill_file(root, "references/ref.md", b"# Details\n")

    plan = _plan(root)

    assert len(_pilot_entries(plan, "claude-code")) == 3


@pytest.mark.parametrize(
    ("link", "message"),
    [
        ("workflows/missing.md", "missing"),
        ("../../../outside.md", "escape"),
    ],
)
def test_pilot_missing_or_escaping_markdown_link_is_rejected_before_writes(
    tmp_path: Path, link: str, message: str
) -> None:
    root = _fixture_repo(tmp_path)
    _skill_file(root, "SKILL.md", f"[unsafe]({link})\n".encode())

    with pytest.raises(ValueError, match=message):
        _plan(root)

    assert not any((root / path).exists() for path in (".claude", ".agents", ".opencode"))


@pytest.mark.usefixtures("require_symlink_support")
def test_pilot_symlink_entry_is_rejected_without_following(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    sentinel = _write_bytes(tmp_path / "outside.txt", b"must not be read")
    _skill_file(root, "SKILL.md", b"# Fixture\n")
    link = root / ".github/skills" / PILOT / "linked.txt"
    link.symlink_to(sentinel)

    with pytest.raises(ValueError, match="symlink"):
        gen.scan_canonical_assets(root)

    assert sentinel.read_bytes() == b"must not be read"


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO creation is unavailable")
def test_pilot_special_entry_is_rejected_without_opening(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    _skill_file(root, "SKILL.md", b"# Fixture\n")
    fifo = root / ".github/skills" / PILOT / "named-pipe"
    _mkfifo(fifo)

    with pytest.raises(ValueError, match="regular|special|FIFO"):
        gen.scan_canonical_assets(root)


def test_special_entry_in_non_pilot_skill_is_rejected(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    skill_root = root / ".github/skills/cg-skill-not-pilot"
    _write_bytes(skill_root / "SKILL.md", b"# Fixture\n")
    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFO creation is unavailable")
    _mkfifo(skill_root / "named-pipe")

    with pytest.raises(ValueError, match="regular|special|FIFO"):
        gen.scan_canonical_assets(root)


def test_non_pilot_skill_is_packaged_recursively(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    skill_name = "cg-skill-future"
    _skill_file(root, "SKILL.md", b"[resource](nested/resource.unknown)\n", skill_name)
    _skill_file(root, "nested/resource.unknown", b"opaque\x00bytes", skill_name)

    plan = _plan(root)

    for target_id, skill_root in TARGET_SKILL_ROOTS.items():
        prefix = f"{skill_root}/{skill_name}/"
        entries = tuple(
            entry
            for entry in plan.by_target[target_id].entries
            if entry.destination.startswith(prefix)
        )
        assert {entry.destination[len(prefix):] for entry in entries} == {
            "SKILL.md",
            "nested/resource.unknown",
        }


def test_codex_fallback_agent_cannot_collide_with_skill_namespace(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    collision = "cg-skill-collision.md"
    _write_bytes(root / ".github/skills" / collision / "SKILL.md", b"# Skill\n")
    _write_bytes(
        root / ".github/agents/cg-skill-collision.agent.md",
        b"---\ndescription: Collision fixture\ntools: [read]\n---\n\n# Agent\n",
    )

    with pytest.raises(ValueError, match="collid|file.*directory|namespace"):
        _plan(root)


def test_all_current_skill_local_markdown_links_and_generated_links_resolve() -> None:
    for canonical in _canonical_skills():
        _assert_markdown_closure(canonical)

    for canonical in _canonical_skills():
        for skill_root in TARGET_SKILL_ROOTS.values():
            _assert_markdown_closure(REPO_ROOT / skill_root / canonical.name)


def test_executable_script_is_opaque_preserves_mode_and_never_runs(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    sentinel = root / "EXECUTED"
    script_bytes = (
        b"#!/bin/sh\n"
        + b"printf executed > "
        + os.fsencode(sentinel)
        + b"\n\xffopaque\x00payload\n"
    )
    _skill_file(root, "SKILL.md", b"# Executable fixture\n")
    script = _skill_file(root, "scripts/sentinel.sh", script_bytes)
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    mode_supported = _is_executable(script)

    plan = _plan(root)
    gen.commit_generation_plan(root, plan, TARGET_SKILL_ROOTS)

    assert not sentinel.exists()
    for target_id, skill_root in TARGET_SKILL_ROOTS.items():
        entry = next(
            entry
            for entry in _pilot_entries(plan, target_id)
            if entry.destination.endswith("/scripts/sentinel.sh")
        )
        output = root / skill_root / PILOT / "scripts/sentinel.sh"
        assert entry.content == script_bytes
        assert entry.sha256 == hashlib.sha256(script_bytes).hexdigest()
        assert entry.executable is mode_supported
        assert output.read_bytes() == script_bytes
        if mode_supported:
            assert _is_executable(output)


def test_executable_inventory_distinguishes_non_executable_script(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    _skill_file(root, "SKILL.md", b"# Non-executable fixture\n")
    script = _skill_file(root, "scripts/data.sh", b"#!/bin/sh\nexit 99\n")
    script.chmod(script.stat().st_mode & ~0o111)

    plan = _plan(root)

    for target_id in TARGET_SKILL_ROOTS:
        entry = next(
            entry
            for entry in _pilot_entries(plan, target_id)
            if entry.destination.endswith("/scripts/data.sh")
        )
        assert entry.executable is False


def test_executable_inventory_copies_binary_bytes_without_decoding(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    binary = bytes(range(256)) + b"\x00\xff\xfe"
    _skill_file(root, "SKILL.md", b"# Binary fixture\n")
    _skill_file(root, "assets/blob.bin", binary)

    plan = _plan(root)

    for target_id in TARGET_SKILL_ROOTS:
        entry = next(
            entry
            for entry in _pilot_entries(plan, target_id)
            if entry.destination.endswith("/assets/blob.bin")
        )
        assert entry.content == binary
        assert entry.sha256 == hashlib.sha256(binary).hexdigest()
        assert entry.executable is False
