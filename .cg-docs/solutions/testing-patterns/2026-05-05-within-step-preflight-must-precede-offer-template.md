---
date: 2026-05-05
title: "Within-step pre-flight operations must precede the user-facing offer template"
category: "testing-patterns"
language: "both"
tags: [prompt-design, step-ordering, preflight, derivation, offer-template, branch-offer, ux, sequential-model, cg-plan]
root-cause: "The type derivation rule and uncommitted-changes check appeared after the offer template in Step 0.7 — the model displays the offer (including a placeholder derived value) before evaluating the derivation logic, so the shown branch name and any warnings are wrong"
severity: "P1"
reviewed-in: ".cg-docs/reviews/2026-05-05-branch-creation-from-plan-review.md"
---

# Within-Step Pre-Flight Operations Must Precede the User-Facing Offer Template

## Problem

`cg-plan.prompt.md` Step 0.7 was written in this order:

1. Check current branch
2. **Show the offer template** (`feat/<short-description>`, Yes/No options)
3. Derive the branch type (`feat/` vs `fix/` vs `refactor/`)
4. If accepted: create branch
5. If the repo has uncommitted changes, warn

This order causes two distinct bugs:

**Bug 1 (P1.1 — wrong branch name shown)**: The offer template displays
`` `feat/<short-description-from-request>` `` before the derivation rule
is stated. A model executing linearly shows the user `feat/my-fix`, then
derives `fix/my-fix` as the type, then creates `fix/my-fix`. The user
approved a name they never saw.

**Bug 2 (P1.2 — post-hoc warning)**: The uncommitted-changes warning fires
*after* the user has already said "Yes" to branching. The user gets a
second dialog after the first Yes/No — a confusing post-hoc confirmation
that breaks the expectation of a single interaction.

## Root Cause

Prompt files are executed top-to-bottom. A step's internal text order
determines execution order, not the logical intent. When an offer template
includes a derived value, the derivation rule must appear before the template
or the model will substitute a placeholder before the rule is known.

The pattern is:

```
# ❌ WRONG ORDER — offer shown before derivation
- Offer the user `feat/<short-description>`
- Derive type: feat/fix/refactor

# ❌ WRONG ORDER — warning fires after acceptance
- Offer: Yes/No
- If accepted: create branch
- If uncommitted changes: warn first
```

This is a fine-grained instance of the forward-dependency problem
(see `2026-04-21-prompt-step-forward-dependency-deferred-marker.md`),
but **within a single step** rather than across steps.

## Solution

Reorder so all pre-flight operations precede the user-facing interaction:

```markdown
### Step 0.7: Branch Offer

1. Run guard checks (non-git workspace → skip; Refine path → skip)
2. Determine default branch (dynamic `git symbolic-ref`)
3. Guard: already on feature branch → skip silently
4. Check uncommitted changes → warn if present (before offering)
5. Derive the branch type (feat/fix/refactor/test/docs/chore/data/analysis)
6. Normalize the branch name (spaces→-, strip invalid chars, truncate to 60)
7. THEN show the offer with the fully-derived name
8. If the user accepts: create branch (handle errors)
9. If the user declines: proceed silently
```

The correct canonical order is: **guards → pre-conditions → derive → normalize → offer → handle response**.

## Prevention

### Rule: Offer Template Must Come Last in Its Step

Any prompt step that (a) derives a value and (b) shows that value to the
user must have the derivation rule appear **textually before** the offer
template. Scanning from top to bottom: the first time the offer appears,
all values it displays must already be computed.

### Rule: Pre-Condition Warnings Must Precede the Offer

If a warning might change the user's decision (e.g., "you have uncommitted
changes"), it must appear before the Yes/No question. Post-hoc warnings
create confusing two-prompt interactions.

### Test Pattern

Use `IndexOf` comparisons to enforce within-step ordering:

```powershell
It "Branch type derivation rule appears before the offer block" {
    $derivationIdx = $content.IndexOf('Derive the branch name')
    $offerIdx      = $content.IndexOf('Suggested name:')
    $derivationIdx | Should BeGreaterThan -1
    $offerIdx      | Should BeGreaterThan -1
    $derivationIdx | Should BeLessThan $offerIdx
}

It "Uncommitted-changes check appears before the offer block" {
    $uncommittedIdx = $content.IndexOf('uncommitted changes')
    $offerIdx       = $content.IndexOf('Suggested name:')
    $uncommittedIdx | Should BeGreaterThan -1
    $offerIdx       | Should BeGreaterThan -1
    $uncommittedIdx | Should BeLessThan $offerIdx
}
```

## Related

- [2026-04-21-prompt-step-forward-dependency-deferred-marker.md](2026-04-21-prompt-step-forward-dependency-deferred-marker.md) — cross-step forward dependency (this solution covers within-step)
- [2026-05-01-branch-offer-must-precede-user-investment-steps.md](2026-05-01-branch-offer-must-precede-user-investment-steps.md) — step placement across steps (this solution covers instruction order within a step)
- [2026-04-13-prompt-step-ordering-indexof-tests.md](2026-04-13-prompt-step-ordering-indexof-tests.md) — IndexOf test patterns for step ordering
