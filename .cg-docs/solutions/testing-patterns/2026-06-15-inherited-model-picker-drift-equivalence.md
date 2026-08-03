---
date: 2026-06-15
title: "Inherited model-picker prompts need explicit audit equivalence"
category: "testing-patterns"
language: "Python/Markdown"
tags: [model-governance, audit, model-picker, drift, token-optimization, regression-tests]
root-cause: "The model guide documented inherited prompts as 'Copilot model picker' while prompt frontmatter intentionally omitted model:, causing permanent false-positive model-guide drift"
severity: "P1"
plan: ".cg-docs/plans/2026-06-15-model-selection-and-governance-finish.md"
reviewed-in: ".cg-docs/reviews/2026-06-12-goal-driven-execution-verify-review-2.md"
related: [".cg-docs/solutions/testing-patterns/2026-06-08-token-optimization-benchmark-guardrails.md", ".cg-docs/solutions/testing-patterns/2026-06-09-token-optimization-release-validation.md", ".cg-docs/solutions/testing-patterns/2026-06-09-external-validation-must-not-be-marked-passed.md", ".cg-docs/solutions/testing-patterns/2026-08-03-single-command-model-overrides-need-dedicated-roles-and-baseline-audits.md"]
---

# Inherited Model-Picker Prompts Need Explicit Audit Equivalence

## Problem

The OpenAI-first model-governance pass added a durable model catalog and changed
`docs/model-guide.md` to describe each prompt and agent with a target model,
role, and rationale. For inherited prompts, the guide used the human-readable
model value `Copilot model picker`.

That collided with the actual prompt contract: ordinary model-picker prompts
intentionally omit `model:` frontmatter. The audit compared the missing
frontmatter value (`None`, normalized to an empty string) against
`Copilot model picker` and reported those rows as model-guide drift.

This was not just a red-phase mismatch. After the explicit Sonnet/Haiku
assignments are migrated in Phase 2, inherited prompts such as `/cg-plan`,
`/cg-plan-review`, `/cg-brainstorm`, and `/cg-strategy` should still omit
`model:`. Without an equivalence rule, the final "model drift count is zero"
guardrail could never converge.

## Root Cause

The audit treated the docs table as if every row represented an exact YAML
frontmatter value. That assumption is wrong for inherited/model-picker rows:
the docs need a visible phrase for humans, but the executable prompt metadata
must remain absent so GitHub Copilot uses the user's selected model.

In short, the same semantic state had two valid representations:

```text
docs/model-guide.md: Copilot model picker
.github/prompts/cg-plan.prompt.md frontmatter: no model key
```

The parser needed to compare semantics, not raw normalized strings, for this
one intentional exception.

## Solution

Add an explicit semantic equivalence helper and route model-guide drift checks
through it:

```python
def model_guide_matches_declaration(declaration, expected):
    actual = normalize_model_name(declaration.get("model"))
    guide_value = normalize_model_name(expected)
    if actual == guide_value:
        return True
    if declaration.get("model") is None and declaration.get("role") == "inherited":
        return guide_value.lower() in {"copilot model picker", "model picker", "inherited"}
    return False
```

Then use this helper instead of direct string comparison when building
`model_inventory["drift"]`.

Add a regression test with the exact inherited prompt shape:

```python
_write(tmp_path / ".github/prompts/cg-plan.prompt.md", _frontmatter(None))
_write(tmp_path / "docs/model-guide.md", """
### Prompts

| File | Model | Role | Rationale |
| --- | --- | --- | --- |
| cg-plan.prompt.md | Copilot model picker | inherited | Planning inherits the user's chosen model. |
""")
inventory = audit.build_model_inventory(tmp_path, files)
assert inventory["drift"] == []
```

The fix reduced current audit drift from 27 to 21 by removing the six inherited
model-picker false positives. The remaining drift stayed visible as intended:
those rows are explicit current Sonnet/Haiku assignments that should be changed
or validated during Phase 2.

## Prevention

When audit reports compare docs, catalogs, and executable metadata:

1. Identify intentional representation differences before writing drift checks.
   "Missing frontmatter because inherited" is not the same as "missing
   metadata."
2. Give each exception a catalog role or other structured discriminator. Do not
   infer inheritance from filename alone unless that is already the source of
   truth.
3. Add a regression test for every semantic equivalence rule. The test should
   use the production shape, not a simplified fixture that cannot reproduce the
   false positive.
4. Keep target-state drift visible for rows that really need migration. A broad
   "ignore missing vs docs value" exception would hide legitimate model-guide
   drift.
5. Keep runtime validation separate. Static audit can prove that inherited rows
   are modeled consistently; VS Code/Copilot still has to validate actual model
   picker and frontmatter behavior.

## Related

- `.cg-docs/plans/2026-06-15-model-selection-and-governance-finish.md`
- `.cg-docs/reviews/2026-06-12-goal-driven-execution-verify-review-2.md`
- `.github/shared/model-catalog.json`
- `scripts/cg_audit_context.py`
- `scripts/tests/test_audit_context.py`
- `.cg-docs/solutions/testing-patterns/2026-06-08-token-optimization-benchmark-guardrails.md`
- `.cg-docs/solutions/testing-patterns/2026-06-09-token-optimization-release-validation.md`
- `.cg-docs/solutions/testing-patterns/2026-06-09-external-validation-must-not-be-marked-passed.md`
- `.cg-docs/solutions/testing-patterns/2026-08-03-single-command-model-overrides-need-dedicated-roles-and-baseline-audits.md`
