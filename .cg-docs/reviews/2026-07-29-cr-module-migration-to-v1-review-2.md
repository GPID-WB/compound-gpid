---
date: 2026-07-30
depth: architecture
type: standard
plan: .cg-docs/plans/2026-07-29-cr-module-migration-to-v1.md
findings:
  P1.1: fixed
  P1.2: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: open
---

## Review Report

**Review mode**: architecture
**Files reviewed**: 42
**Findings**: 6 (P0: 0, P1: 2, P2: 4, P3: 0)

### P1 — CRITICAL (must fix before merge)
- **[P1.1]** [cg-data-quality] `.github/prompts/cg-work.prompt.md:28` and `.github/prompts/cg-work.prompt.md:224` — `/cg-work` cannot accept `review:research` even though the shared routing contract defines `research` as a first-class route. [manual]
  **Why**: The canonical routing contract now exposes `research` as a resolved mode, but `/cg-work` still parses only `auto, manual, none, light, standard, data-risk, architecture, full` and only documents explicit dispatch for `review:light|standard|data-risk|architecture|full`. A user cannot force the research review route from `/cg-work`, so the contract and the work-handoff surface have drifted apart.
  **Fix**: Add `research` to `/cg-work` review-mode parsing and to the explicit route table, then add a regression test proving `review:research` is accepted and dispatched intentionally.

- **[P1.2]** [cg-data-quality] `.github/shared/review-routing.contract.md:67` — precedence `full > research` can silently drop CR methodology agents when research signals overlap with `security-risk` or other `full` triggers. [manual]
  **Why**: `research` dispatches the CR agent set, but `full` does not. The current “highest coverage” precedence upgrades mixed research/security diffs to `full`, which removes research-specific review exactly where high-risk review breadth is needed most.
  **Fix**: Make research coverage additive when `research` co-occurs with `full` triggers, or define a composite route that dispatches `full` plus CR agents.

### P2 — IMPORTANT (should fix)
- **[P2.1]** [cg-architecture] `.github/prompts/cr-review.prompt.md:48` — `/cr-review` forks the shared research-route policy by always dispatching its own reduced shared agent set instead of consuming the canonical `research` route. [manual]
  **Why**: The shared contract says `research` includes all standard `cg-*` reviewers plus the CR agents, but `/cr-review` hard-codes a different shared-agent fan-out and then layers task-specific CR agents separately. That creates two policy sinks for the same review mode and makes coverage depend on the entry point.
  **Fix**: Refactor `/cr-review` to consume the shared `research` route first, then layer task-type-specific additions only where they are truly distinct.

- **[P2.2]** [cg-testing] `.github/prompts/cg-review.prompt.md:197` and `.github/prompts/cg-review.prompt.md:253` — the saved report template omitted `research` from the allowed review/depth enums. [safe_auto]
  **Why**: The routing logic already allowed `research`, but the reporting template and persisted `depth` example were stale, so a correct research-routed review would be asked to save invalid metadata.
  **Fix**: Fixed in the canonical prompt and validated with updated `prompt-tools` assertions.

- **[P2.3]** [cg-data-quality] `scripts/brain/utils.py:117` and `scripts/cg_generate_targets.py:516` — folded multiline prompt descriptions were truncated/corrupted when generating adapter command frontmatter. [safe_auto]
  **Why**: The shared frontmatter parser only preserved the first line of folded YAML string values, and the generator then emitted malformed one-line descriptions in generated CR command files.
  **Fix**: Fixed folded-scalar parsing in `scripts/brain/utils.py`, removed the fragile generator-side line sniffing, regenerated all targets, and added generated-frontmatter parity checks in `tests/cr-prompts.Tests.ps1`.

- **[P2.4]** [cg-version-control] Generated CR adapter artifacts in `.agents/`, `.claude/`, and `.opencode/` remain untracked in the current worktree after regeneration. [advisory]
  **Why**: The canonical generator and generated manifests now expect the expanded CR surfaces, but many of the newly emitted CR command/agent/skill files are still untracked. That leaves the adapter trees easy to commit partially.
  **Fix**: Stage and review the generated additions together with the canonical source changes before merge so the target trees stay closed over the generator output.

### ✅ Passed
- `cg-reproducibility`: No issues found.
- Focused validation passed under Pester 4.10.1: `prompt-tools` 1404 passed / 0 failed; `cr-prompts` 563 passed / 0 failed.
- Generated CR command frontmatter now preserves full descriptions across `.agents`, `.claude`, and `.opencode` command outputs.
