---
date: 2026-06-15
depth: light
parent-review: .cg-docs/reviews/2026-06-12-goal-driven-execution-review.md
type: verification
findings:
  P1.1: fixed
---

## Review Report

**Review mode**: light (verify pass)
**Parent review**: `.cg-docs/reviews/2026-06-12-goal-driven-execution-review.md`
**Files reviewed**: 11 changed or new files
**Findings**: 1 (P0: 0, P1: 1, P2: 0, P3: 0)

### P1 - CRITICAL

- **[P1.1]** [cg-testing] `scripts/cg_audit_context.py:541` - Inherited model-picker prompts are permanently reported as model-guide drift.

  **Issue**: `build_model_inventory()` compares `normalize_model_name(declaration["model"])` against the model-guide value. For inherited prompts, current frontmatter intentionally omits `model:`, so the left side is `""`; the new guide table uses `"Copilot model picker"` for inherited rows, so those rows are always counted as drift. The current generated audit already shows inherited prompts such as `cg-brainstorm.prompt.md`, `cg-ideate.prompt.md`, `cg-plan.prompt.md`, `cg-plan-review.prompt.md`, `cg-review-repos.prompt.md`, and `cg-strategy.prompt.md` in `model_inventory.drift`.

  **Why**: This is not only a red-phase artifact. Even after Phase 2 rewrites explicit Sonnet/Haiku assignments, the inherited prompts are supposed to remain model-picker exceptions, so the final guardrail "no model-guide drift" cannot converge unless the audit treats model-guide values like `Copilot model picker` / `inherited` as equivalent to missing frontmatter for ordinary inherited prompts.

  **Fix**: Add an equivalence helper used by drift detection, for example: if `declaration["model"] is None`, `declaration["role"] == "inherited"`, and the guide value normalizes to `copilot model picker`, `model picker`, or `inherited`, do not append drift. Add a regression test using `cg-plan.prompt.md` with no `model:` and a `docs/model-guide.md` row of `Copilot model picker` that asserts `inventory["drift"] == []`.

### Passed

- **@cg-code-quality**: No additional style, naming, or maintainability findings in the Phase 1 model-catalog/audit changes. The dead `model_catalog_model_lookup({})` branch in `classify_model_tier()` is harmless because catalog classification is performed in `extract_model_declarations()`.
- **@cg-testing**: Python audit tests pass (`73 passed`), context audit generation succeeds, and `git diff --check` is clean. Pester and VS Code/Copilot runtime validation remain external by design.

### Brain/context notes used

- Token-optimization changes need generated benchmark guardrails and tests: `.cg-docs/solutions/testing-patterns/2026-06-08-token-optimization-benchmark-guardrails.md`.
- Release checklist statuses must distinguish Codex evidence from external validation: `.cg-docs/solutions/testing-patterns/2026-06-09-external-validation-must-not-be-marked-passed.md` and `.cg-docs/solutions/testing-patterns/2026-06-10-release-checklist-statuses-must-be-anchored-to-audit-timestamps.md`.
