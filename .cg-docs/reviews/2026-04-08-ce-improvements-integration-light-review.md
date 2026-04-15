---
plan: .cg-docs/plans/2026-04-08-ce-improvements-integration.md
findings:
  P1.1: fixed
  P1.2: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P3.1: fixed
  P3.2: fixed
---

## Review Report

**Review depth**: light (argument override; local config is `thorough`)
**Branch**: `feat/ce-improvements` (3 commits ahead of `main`)
**Files reviewed**: 22
**Findings**: 2 P1, 5 P2, 2 P3

---

### P0 — BLOCKING (immediate remediation required)

_None identified._

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-code-quality] `.github/agents/*.agent.md`:5 — All 10 agent files use `user-invokable: false/true`, but the VS Code schema attribute is `user-invocable` (confirmed by [official docs](https://code.visualstudio.com/docs/copilot/customization/custom-agents)).
  **Why**: VS Code silently ignores unknown frontmatter keys. The typo means `user-invokable: false` is silently ignored and all 8 review-only agents default to `user-invocable: true`, appearing in the agent dropdown despite being intended as internal-only subagents.
  **Fix**: Rename `user-invokable` → `user-invocable` in all 10 `.agent.md` files (`cg-code-quality`, `cg-testing`, `cg-documentation`, `cg-performance`, `cg-architecture`, `cg-data-quality`, `cg-reproducibility`, `cg-version-control`, `cg-roadmap`, `cg-learnings-researcher`).

- **[P1.2]** [cg-testing] `tests/prompt-tools.Tests.ps1`:missing — No tests verify that `.agent.md` files declare a `tools: ['read', 'search']` restriction.
  **Why**: The file header (lines 8–16) documents the lesson that only agent files should declare tool restrictions, but no test enforces this. If an agent accidentally loses its `tools:` key, tests won't catch it — silently granting write access to a read-only reviewer.
  **Fix**: Add a Describe block that iterates over all `.agent.md` files and verifies each has a `tools:` key in frontmatter (excluding cg-roadmap which intentionally has full write access, and verifying review agents don't include write tools).

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `.github/prompts/cg-review.prompt.md`:3 — The `agents:` key in YAML frontmatter is dead metadata.
  **Why**: The `agents:` frontmatter key is valid for `.agent.md` files where it controls available subagents, but VS Code silently ignores it in `.prompt.md` files. The comment at the top of the file (`<!-- When adding or removing review agents, update the agents list in the YAML frontmatter above -->`) implies this list is functional, but it is not.
  **Fix**: Move the agents list to a comment-only block (remove it from the YAML frontmatter, keep it as a `<!-- -->` comment) so the intent is documented without misleading future maintainers.

- **[P2.2]** [cg-testing] `tests/prompt-tools.Tests.ps1`:missing — No structural test for `cg-compound.prompt.md` which was changed on this branch.
  **Why**: The changed file gained a new P0 severity option in its schema snippet. No test verifies the file exists, has valid frontmatter, or lacks a `tools:` restriction (as required for orchestrating prompts).
  **Fix**: Add a Describe block similar to `cg-strategy.prompt.md` tests (lines 134–169): verify file exists, has `description:` and `model:` in frontmatter, and does NOT have a `tools:` key.

- **[P2.3]** [cg-testing] `tests/prompt-tools.Tests.ps1`:missing — No structural tests for orchestrating prompts `cg-work`, `cg-brainstorm`, `cg-plan`.
  **Why**: Tests verify cg-review, cg-fix-triage, and cg-strategy do not have `tools:` restrictions, but three other orchestrating prompts have no structural tests. A future accidental `tools:` addition would go undetected.
  **Fix**: Add minimal Describe blocks for each: verify file exists and has no `tools:` key.

- **[P2.4]** [cg-testing] `tests/prompt-tools.Tests.ps1`:missing — No tests verify agent files contain a body (non-empty content beyond frontmatter).
  **Why**: Eight agent files were modified on this branch. No test verifies the body is substantive (e.g., > 100 bytes after frontmatter). A stub agent with only frontmatter would pass all existing tests.
  **Fix**: Add a test in the agent files Describe block checking that body content (after frontmatter) is non-trivial.

- **[P2.5]** [cg-testing] `tests/Run-Tests.ps1`:37–47 — Hardcoded `$testNames` array may miss newly added test files.
  **Why**: `Run-Tests.ps1` maintains a static list of test file names. If a new `.Tests.ps1` file is added to `tests/` without updating this list, it won't be included in the full suite run.
  **Fix**: Add a check (or note in Run-Tests.ps1) that scans for `.Tests.ps1` files not in the list and warns if any are found.

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `.github/prompts/*.prompt.md` — "Step 0: Get Bearings" pattern is repeated verbatim across 7+ prompt files.
  **Why**: DRY violation — if the standard guidance for reading charter files changes, it must be updated in 7+ places. Low risk but creates maintenance burden.
  **Fix**: Document this as an intentional convention in `.github/instructions/` or add a note acknowledging the duplication is deliberate (since prompts are standalone).

- **[P3.2]** [cg-testing] `tests/prompt-tools.Tests.ps1`:missing — No edge-case tests for the `Get-Frontmatter` helper with malformed input.
  **Why**: Tests assume well-formed YAML. No negative tests exist for incomplete frontmatter (missing closing `---`) or non-existent files.
  **Fix**: Add a small negative-case Describe block for the `Get-Frontmatter` helper.

---

### ✅ Passed

- `@cg-code-quality`: `compound-gpid.md`, `roadmap.json`, `tests/Run-Tests.ps1`, `tests/prompt-tools.Tests.ps1` (functional correctness), `docs/reference.md`, `docs/workflow.md` — No issues
- `@cg-code-quality`: `cg-fix-triage.prompt.md`, `cg-compound.prompt.md` content changes — Correct
- `@cg-testing`: Existing test coverage for cg-review, cg-fix-triage, cg-strategy, model-assignments — Solid
- `@cg-testing`: P0 sentinel added to prompt tests (commits 79c203d, 559f77f) — Correct
