---
date: 2026-04-20
title: "Reduce late-sequence token cost in prompts"
status: decided
scope: "Standard"
chosen-approach: "Combined prose compression + Step 0 dedup (top 5 prompts only)"
tags: [performance, tokens, prompts, optimization]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Reduce Late-Sequence Token Cost

## Context

The roadmap feature "Reduce token cost by extracting late-sequence content"
(Performance milestone) was inspired by compound-engineering-plugin PR #540,
which extracted Phase 3–4 shipping content from ce:work into on-demand
reference files, saving ~29% tokens per session.

Analysis of our 16 prompt files (3,029 total lines) found ~611 lines (~20%)
of late-sequence content — instructions that ride in context for the entire
session but are only used at the very end. Top offenders: cg-work (33% late),
cg-plan (32%), cg-fix-triage (33%), cg-review (24%), cg-setup (15%).

## Requirements

- Reduce token cost in prompt files with zero functional risk
- No file-splitting extraction pattern (model may skip stub instructions
  5%+ of the time — unacceptable for state-changing steps like roadmap
  updates and plan completion)
- All instructions must remain inline in the prompt
- Scope to top 5 prompts only — don't boil the ocean
- Existing Pester tests must continue to pass

## Approaches Considered

### Approach 1: Late-Sequence Extraction (CE Pattern — REJECTED)

Move late-sequence blocks into `references/` files and replace with stubs
that instruct the model to read them at the right time.

**Pros**: Maximum savings (~611 lines, ~9,000 tokens). Proven in CE codebase.
**Cons**: Depends on model reliably following "read file X at Step N"
instructions. If model skips the stub even 5% of the time, state-changing
steps (roadmap updates, plan completion) are silently dropped. CE has a test
harness for behavioral compliance; we don't.
**Effort**: Large
**Recommended?**: No — risk too high for this project.

### Approach 2: Prose Compression (CHOSEN — part of combined)

Edit prompts for conciseness — remove verbose explanations, redundant
phrasing, tutorial-style "why" explanations. Keep all instructions inline.

**Pros**: Zero functional risk. Same logic, fewer tokens. Testable.
**Cons**: Manual editing effort. Moderate savings per file.
**Effort**: Medium
**Estimated savings**: ~400–600 lines across top 5 files

### Approach 3: Conditional Mode Splitting (REJECTED)

Split prompts with mutually exclusive code paths into separate prompt files.

- `cg-setup` (309 lines): Mode A (new project) + Mode B (returning user)
  → split into two prompts so each invocation loads only the relevant path.
- `cg-fix-triage` (189 lines): `--migrate` mode (~33 lines) is a
  completely separate workflow → extract to `/cg-fix-triage-migrate`.

**Pros**: Zero risk. Each invocation loads only what it needs.
**Cons**: VS Code Copilot has no subcommand support — every `.prompt.md`
shows up as a user-facing `/command`. No way to hide dispatch-only prompts.
Adding more commands increases user confusion. Savings are the smallest
part of the plan (~150 lines).
**Effort**: Small
**Recommended?**: No — UX cost outweighs token savings.

### Approach 4: Step 0 Deduplication (CHOSEN — part of combined)

Compress the "Get Bearings" block (~20–25 lines per prompt) to a
standardized minimal form. Keep it duplicated per the design convention
(prompts must work standalone), just shorter and consistent.

**Pros**: ~30–40 lines saved across each of the 5 target files.
**Cons**: Still duplicated — risk of copies drifting over time.
**Effort**: Small

## Decision

Combined Approaches 2 + 4, scoped to the **top 5 prompts only**:

1. `cg-work.prompt.md` (307 lines) — prose compression + Step 0 dedup
2. `cg-setup.prompt.md` (309 lines) — prose compression + Step 0 dedup
3. `cg-plan.prompt.md` (237 lines) — prose compression + Step 0 dedup
4. `cg-review.prompt.md` (226 lines) — prose compression + Step 0 dedup
5. `cg-fix-triage.prompt.md` (189 lines) — prose compression + Step 0 dedup

No new commands. No structural changes. No mode splitting (rejected due to
UX cost of additional user-visible commands).

Estimated combined savings: ~500–700 lines (~7,500–10,500 tokens), or
~17–23% of total prompt line count. Zero functional risk.

## Next Steps

1. `/cg-plan` — Create implementation plan with per-file compression targets
2. Establish a "before/after" line count baseline for each file
3. Implement file by file, running Pester tests after each
4. Verify no behavioral regressions via manual spot-checks
