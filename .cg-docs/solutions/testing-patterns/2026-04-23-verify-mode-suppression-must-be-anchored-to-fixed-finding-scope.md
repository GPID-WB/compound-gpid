---
date: 2026-04-23
title: "Verify-mode suppression must be anchored to fixed-finding scope, not agent-inferred consequence code"
category: "testing-patterns"
language: "both"
tags: [prompt-design, cg-review, mode-verify, suppression-policy, review-loop, fix-triage, convergence, fixed-finding-scope]
root-cause: "Vague suppression wording ('expected fix-consequence P2/P3') lets the review agent suppress findings it infers as consequential rather than anchoring suppression to the explicit findings: map from the prior review"
severity: "P1"
---

# Verify-Mode Suppression Must Be Anchored to Fixed-Finding Scope

## Problem

`/cg-review mode:verify` was designed to suppress expected P2/P3 re-findings
after a fix-triage cycle so the quality loop terminates. The original suppression
policy wording was:

> "Suppress expected fix-consequence P2/P3 findings (those that are a direct
> consequence of the changes made to address prior findings)"

This is dangerous. An AI review agent reading "direct consequence of the changes
made to address prior findings" has no objective anchor. It can:

- Suppress a genuine new P2 by inferring it is "related to" a prior fix
- Over-suppress findings in adjacent code that wasn't explicitly touched
- Produce inconsistent results across sessions (inference varies by context window)

The practical result: a verify pass that claims convergence even when new
genuine issues exist, defeating the entire purpose of the mode.

## Root Cause

Suppression policy was written from the *human reader's* perspective
("I'll know it when I see it") rather than the *agent's* perspective
(needs an objective, verifiable anchor). The agent has access to two
concrete artifacts at verify time:

1. The prior review file's `findings:` frontmatter map (explicit, fixed IDs)
2. The changed files (explicit diff scope)

The original wording referenced neither — it asked the agent to reason about
"consequence", which is unbounded inference.

## Solution

Rewrite suppression policy to anchor on the explicit `findings:` map:

```
Suppression policy:
- P0/P1: Always report. Never suppress.
- P2/P3 on fixed-finding scope: Suppress only if the finding targets a
  function or block explicitly listed as `fixed` in the prior review's
  `findings:` map.
- Cross-file breakage: Always report.
- When in doubt, report.
```

The key phrase is **"explicitly listed as `fixed` in the prior review's
`findings:` map"**. The agent can read the prior review frontmatter and
check whether a finding ID appears there with status `fixed`. If not, the
finding is not suppressed — even if the agent believes it is "related" to
prior work.

This makes suppression deterministic:
- A finding is suppressed if and only if it targets a scope that was
  explicitly fixed per the prior review's findings map.
- Cross-file breakage is never suppressed (structural guard).
- P0/P1 are never suppressed (severity guard).

## Prevention

### Pattern: Write suppression policies from the agent's perspective

When any prompt step involves conditional suppression or skipping, always
ask: "What objective artifact can the agent check to evaluate this condition?"

| ❌ Vague (agent infers) | ✅ Anchored (agent checks artifact) |
|---|---|
| "Suppress fix-consequence findings" | "Suppress findings targeting IDs listed as `fixed` in `findings:` map" |
| "Skip if already addressed" | "Skip if finding ID appears in `fixed:` section of prior review frontmatter" |
| "Ignore redundant findings" | "Suppress only P2/P3 within the explicit scope of the fixed finding" |

### Pattern: Verification file naming and frontmatter

A verify-review file should record its suppression evidence for auditability:

```yaml
---
date: YYYY-MM-DD
depth: light
parent-review: .cg-docs/reviews/<prior-review-stem>-review.md
type: verification
findings:
  <any new finding IDs>: open
---
```

The `parent-review:` field makes the suppression anchor explicit and
machine-readable for future passes.

### Pattern: Prompt cross-reference hygiene

When prompt steps are restructured (renumbered, split, merged), internal
cross-references like `see Step 1.2` drift. Use descriptive anchors instead:

```
❌ see Step 1.2
✅ see Step 1, item 3 (argument parsing)
```

Write Pester tests asserting that specific argument-parsing text exists at
the referenced location, not just that the cross-reference string is present.

## Related

- [`2026-04-15-prompt-step-silent-skip-antipattern-fallback-required.md`](./2026-04-15-prompt-step-silent-skip-antipattern-fallback-required.md) — same root cause: prompts must provide objectively evaluable conditions, not agent-inferred ones
- [`2026-04-21-prompt-step-forward-dependency-deferred-marker.md`](./2026-04-21-prompt-step-forward-dependency-deferred-marker.md) — related: prompt steps need explicit, checkable conditions for execution ordering
- [`2026-04-15-pester-dotall-flag-required-for-multiline-regex.md`](./2026-04-15-pester-dotall-flag-required-for-multiline-regex.md) — used in verify-mode tests: `(?s)Step 1.7.*suppression` patterns require `(?s)` dotall flag
- [`2026-04-24-anti-loop-exclusion-in-iterative-review-modes.md`](./2026-04-24-anti-loop-exclusion-in-iterative-review-modes.md) — companion pattern: the scan must exclude its own output file type or the mode loops on itself
- [`2026-07-24-cross-file-contract-state-must-align-docs-validator-tests.md`](./2026-07-24-cross-file-contract-state-must-align-docs-validator-tests.md) — verify mode caught a real docs/validator/test state-model drift after standard review fixes were applied
