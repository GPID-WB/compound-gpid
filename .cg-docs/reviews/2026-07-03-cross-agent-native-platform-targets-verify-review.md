---
date: 2026-07-03
title: "Cross-Agent Native Platform Targets — Verify Review"
review-depth: light
mode: verify
parent-review: ".cg-docs/reviews/2026-05-21-knowledge-brain-engine-review.md"
branch: feat/cross-agent-native-trees
plan: ".cg-docs/plans/2026-07-03-cross-agent-native-platform-targets.md"
files-reviewed: 18
findings:
  P2.1:
    status: fixed
    description: "validate_target_mapping is 72 lines — exceeds 30-line function guideline"
  P2.2:
    status: fixed
    description: "_emit_command has repeated frontmatter formatting patterns across platform branches (DRY)"
  P2.3:
    status: fixed
    description: "emit_for_target uses next() with StopIteration risk if source asset not found in manifest"
  P2.4:
    status: fixed
    description: "No edge case tests for empty frontmatter, malformed prompts, or missing model catalog assignments"
  P3.1:
    status: fixed
    description: "build_output_manifest is 54 lines — could extract per-type manifest builders"
  P3.2:
    status: fixed
    description: "Drift test test_github_not_modified_by_generator copies entire repo via shutil.copytree — slow"
  P3.3:
    status: fixed
    description: "No explicit test for --target copilot passthrough (should produce no output)"
---

# Cross-Agent Native Platform Targets — Verify Review

## Review Context

- **Mode**: verify (light depth, per `mode:verify`)
- **Parent review**: `.cg-docs/reviews/2026-05-21-knowledge-brain-engine-review.md` (50 fixed findings — unrelated to current work; suppression context applied but no overlap)
- **Plan**: `.cg-docs/plans/2026-07-03-cross-agent-native-platform-targets.md`
- **Branch**: `feat/cross-agent-native-trees`
- **Files reviewed**: 18 key files (scripts, tests, linker changes, docs)

## Verification Suppression Context

> **Verification mode**: This is a verify pass following fix-triage.
> The prior review file is `2026-05-21-knowledge-brain-engine-review.md` with 50 fixed findings from the Knowledge Brain Engine work. None of these findings overlap with the current cross-agent native platform targets work.
>
> **Suppression policy**: P0/P1 always report. P2/P3 suppressed only for explicitly `fixed` scope. Since the prior review is unrelated, no suppression applied — all findings are genuine new issues.

## Changed Files

**Modified**: README.md, adapters/README.md, docs/context-files.md, roadmap.json, scripts/link.ps1, scripts/link.sh, scripts/unlink.ps1, scripts/unlink.sh, tests/bash-scripts.Tests.ps1

**New**: .github/shared/target-mapping.json, scripts/cg_generate_targets.py, scripts/schemas/target_mapping_schema.json, 7 test files

**Generated**: .claude/ (64 files), .agents/ (81 files), .opencode/ (65 files)

## Findings

### @cg-code-quality

**[P2.1]** `scripts/cg_generate_targets.py:62` — `validate_target_mapping` is 72 lines, exceeding the 30-line function guideline.
**Issue**: Long function with nested validation loops makes it harder to test individual validation rules in isolation.
**Fix**: Extract per-section validators: `_validate_capabilities(prefix, caps)`, `_validate_formats(prefix, formats)`, `_validate_output_paths(prefix, output_paths)`.
**Tag**: [manual]

**[P2.2]** `scripts/cg_generate_targets.py:330` — `_emit_command` repeats frontmatter formatting patterns across `claude-code`, `codex`, and `opencode` branches.
**Issue**: The `f"---\ndescription: {desc}\n{model_line}---\n\n{body.split('---', 2)[-1].lstrip()}"` pattern is duplicated with minor variations. DRY violation.
**Fix**: Extract a `_format_command_frontmatter(desc, model_or_role, body, platform)` helper that handles the common pattern with platform-specific model/role insertion.
**Tag**: [manual]

**[P2.3]** `scripts/cg_generate_targets.py:310` — `emit_for_target` uses `next(a for a in assets["prompts"] if ...)` to find source assets by relative path.
**Issue**: If the manifest references a source path that doesn't exist in the assets list (e.g., race condition or stale manifest), `next()` raises `StopIteration` — unhandled crash.
**Fix**: Use a dict lookup (`{a["relative_path"]: a for a in assets["prompts"]}`) or catch `StopIteration` with a clear error message.
**Tag**: [safe_auto]

**[P3.1]** `scripts/cg_generate_targets.py:228` — `build_output_manifest` is 54 lines.
**Issue**: Manually builds manifest entries for each asset type in a single function. Could extract per-type builders for clarity.
**Fix**: Extract `_manifest_commands(target, prompts)`, `_manifest_skills(target, skills)`, `_manifest_agents(target, agents)` helpers.
**Tag**: [advisory]

### @cg-testing

**[P2.4]** `scripts/tests/test_cg_generate_targets.py` — No edge case tests for empty frontmatter, malformed prompts, or missing model catalog assignments.
**Issue**: The generator parses frontmatter and resolves model roles from the catalog. If a prompt has no frontmatter, or the catalog is missing an assignment, the generator should handle it gracefully. Current tests only cover the happy path.
**Fix**: Add tests for: (a) prompt with no frontmatter at all, (b) agent with no `tools` field, (c) model catalog with no assignments array, (d) skill with no frontmatter.
**Tag**: [manual]

**[P3.2]** `scripts/tests/test_target_drift.py:83` — `test_github_not_modified_by_generator` copies the entire repo via `shutil.copytree`.
**Issue**: Copying the entire repo (including .git, .cg-docs, docs, etc.) is slow and unnecessary — the test only needs `.github/` to verify the generator doesn't modify it.
**Fix**: Copy only `.github/` and the scripts needed to run the generator, or use a minimal fixture repo.
**Tag**: [advisory]

**[P3.3]** `scripts/tests/test_cg_generate_targets.py` — No explicit test for `--target copilot` passthrough behavior.
**Issue**: The copilot target has `generatedTreePath: null` and should produce no output. This is implicitly tested by `test_copilot_target_skipped` but the assertion is weak (`or True`).
**Fix**: Assert that no files are written and the exit code is 0 when `--target copilot` is used.
**Tag**: [safe_auto]

## Summary

| Priority | Count | Open |
|----------|-------|------|
| P0 | 0 | 0 |
| P1 | 0 | 0 |
| P2 | 4 | 4 |
| P3 | 3 | 3 |
| **Total** | **7** | **7** |

No P0 or P1 findings. All P2 findings are code quality improvements (function length, DRY, error handling, test coverage). P3 findings are advisory. The implementation is functionally correct — 219 Python tests + Pester tests pass. The findings are improvements, not blockers.
