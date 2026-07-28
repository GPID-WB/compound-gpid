---
date: 2026-07-28
depth: light
parent-review: .cg-docs/reviews/2026-07-23-wb-report-writing-technical-methodology-review.md
type: verification
plan: .cg-docs/plans/2026-07-27-canonical-native-packaging-foundation.md
findings:
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
---

## Review Report

**Review mode**: light (verify)
**Files reviewed**: 107
**Findings**: 10 (P0: 0, P1: 0, P2: 6, P3: 4)

**Verification context**: Prior review `.cg-docs/reviews/2026-07-23-wb-report-writing-technical-methodology-review.md` — 8 fixed findings (P1.1, P1.2, P1.4, P2.1, P2.2, P2.3, P2.4, P2.5), 1 skipped (P1.3). None of the current findings overlap with the fixed-finding scope; all are new findings in the changed files.

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `scripts/cg_generate_targets.py:826` — Unused parameter `del root` workaround instead of signature cleanup
  **Why**: `_render_output_entry()` declares `root: Path` but never uses it; line 826 uses `del root` as a linter-suppression workaround, confusing the function contract.
  **Fix**: Remove `root` from the function signature and update the single call site at line 407.

- **[P2.2]** [cg-code-quality] `scripts/tests/test_cg_generate_targets.py:232` — `set` passed where `Sequence[str]` is declared
  **Why**: `commit_generation_plan()` receives a set literal `{"claude-code"}`, but the signature declares `Sequence[str]`. Sets have no ordering guarantee and lack `Sequence` methods.
  **Fix**: Use a tuple `("claude-code",)` or a list `["claude-code"]`.

- **[P2.3]** [cg-testing] `scripts/tests/test_cg_generate_targets.py` — Ownership manifest commit/write path has no direct test coverage
  **Why**: Four new functions (`_ownership_manifest_bytes`, `_read_prior_ownership_manifest`, `_preflight_target_commit`, `_prune_empty_parents`) have zero direct tests. The manifest-writing path is only indirectly exercised.
  **Fix**: Add tests validating manifest structure, stale-file cleanup, and conflict detection.

- **[P2.4]** [cg-testing] `scripts/schemas/target_mapping_schema.json` / `test_target_mapping.py` — JSON Schema `repoPath` pattern weaker than Python validator
  **Why**: The schema's `repoPath` regex doesn't reject path components with empty parts, `.` components, trailing dots/spaces, or Windows reserved names, creating a false-pass risk for schema-first validators.
  **Fix**: Either extend the schema regex to match Python validation or add a comment stating Python validation is canonical.

- **[P2.5]** [cg-testing] `scripts/tests/test_cg_generate_targets.py:283-293` — Default agent TOML output never parsed or validated for well-formedness
  **Why**: Only the tricky-agent TOML is parsed; the default agent `cg-test-agent` is checked for file count but not content validity.
  **Fix**: Parse the default agent's TOML output and verify name, description, model, tools, instructions fields.

- **[P2.6]** [cg-testing] `scripts/tests/test_target_drift.py:95-115` — Skill-bundle drift test reads from disk, conflating "not generated yet" with "incomplete"
  **Why**: `test_generated_skill_bundles_recursively_match_canonical_files` uses `rglob("*")` on disk, so a missing generated directory (before first generator run) triggers a mismatch failure rather than a clean skip.
  **Fix**: Add a guard to skip when the generated directory doesn't exist, or compare against the dry-run manifest.

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `scripts/tests/test_target_drift.py:73,150,168,176,206` — Local imports at function scope instead of module level
  **Why**: `import hashlib`, `import tempfile`, `import shutil`, and `import cg_generate_targets as gen` are inside functions, inconsistent with PEP 8 and the other test file.
  **Fix**: Move stdlib imports to module top level.

- **[P3.2]** [cg-code-quality] `scripts/cg_generate_targets.py:42-44` — Module-level `sys.path` mutation at import time
  **Why**: `sys.path.insert(0, _scripts_dir)` runs at import time, polluting the global search path and causing fragility when imported as a library.
  **Fix**: Move to `main()` or wrap in a try/except with a clear error message; consider installing as a package.

- **[P3.3]** [cg-testing] `scripts/cg_generate_targets.py` — `_yaml_scalar`, `_strip_fenced_code`, `_validate_bundle_markdown_references` have no unit tests
  **Why**: These new functions have zero direct coverage; the YAML-reserved-keyword branch and fenced-code/reference validation paths are never exercised.
  **Fix**: Add parametrized unit tests for edge cases (YAML booleans, unterminated fences, missing local references).

- **[P3.4]** [cg-testing] `scripts/tests/test_cg_generate_targets.py:223-236` — Byte-fidelity test covers claude-code only, not codex or opencode
  **Why**: `test_emit_plan_writes_exact_planned_bytes` verifies byte fidelity only for claude-code. Codex and opencode emitter bugs would only be caught by drift tests requiring real repo state.
  **Fix**: Parametrize across all non-copilot targets or add separate byte-fidelity tests for codex and opencode.

### ✅ Passed

- **Structural scan**: All 17 `.agents/subagents/*.toml` files parse correctly. All `.opencode/commands/*.md` and `.opencode/agents/*.md` files have valid frontmatter. `.github/shared/target-mapping.json` validates against schema. Generated trees are consistent across `.claude/`, `.agents/`, `.opencode/`.
- **No regression from prior fixed findings**: None of the 8 `fixed` findings from the prior review regressed in the current change set. The stale-tree, source-pack, active-state, roadmap, validator, and behavioral test fixes remain intact.
- **No cross-file breakage detected**: The generated native-target trees are self-consistent.

> Review report saved to `.cg-docs/reviews/2026-07-23-wb-report-writing-technical-methodology-verify-review-2.md`. Use `/cg-fix-triage` in a future session to apply findings by ID (e.g., `/cg-fix-triage P2.1 P2.3`) or by priority level (e.g., `/cg-fix-triage P2`).
