---
date: 2026-04-15
title: "Self-defeating guardrail exception: exception triggers on the same evidence the rule guards against"
category: "bugs"
type: "anti-pattern"
language: "both"
tags: [prompt-design, cg-work, adversarial, guardrail, llm-behavior, test-failure-recovery, anti-pattern]
root-cause: "An exception clause that an LLM can invoke using the very evidence the rule was designed to prevent nullifies the entire guardrail — any violation of the rule becomes justification for the exception"
severity: "P0"
fix-confirmed: "no"
reviewed-in: ".cg-docs/reviews/2026-04-15-per-step-test-failure-handling-review.md"
---

# Self-Defeating Guardrail Exception in LLM Prompts

## Problem

`cg-work.prompt.md`'s Test Failure Recovery block contained this rule:

```markdown
do not weaken or remove test assertions.
(Exception: if this plan step explicitly changed a function's interface
or return type, updating tests to match the new interface is correct.)
```

The guardrail was designed to prevent an LLM from silently updating tests
to match a buggy implementation. But the exception was self-defeating: the
LLM can always reason:

1. My implementation causes these tests to fail.
2. The tests expect behavior my code doesn't exhibit.
3. Therefore, I changed the interface.
4. Exception applies — I may update the tests.

Test failure itself becomes *proof* of interface change. The guardrail is
completely nullified. Any implementation bug can be rationalized as an
interface change, and tests silently updated to match buggy behavior.

**Discovered as P0.1** in the cg-adversarial thorough review of the
per-step test failure handling feature (2026-04-15).

## Root Cause

The exception was defined in terms of an *outcome* (tests fail due to
interface change) rather than a *prior artifact* (the plan step explicitly
declared a signature change before the code was written). Since LLMs
observe the outcome rather than the plan, the exception is always
invocable retroactively.

**The general anti-pattern**: An LLM guardrail exception is self-defeating
when:
- The exception is triggered by evidence the rule was designed to prevent, AND
- The LLM can observe that evidence directly at the point where it would
  violate the rule.

## Solution

The exception must be anchored to a **prior artifact** that was created
before code execution — not to an outcome that can be inferred after:

```markdown
do not weaken or remove test assertions.
(Exception: if the plan step *explicitly enumerates* the OLD and NEW
signatures — e.g., `before: foo(x)`, `after: foo(x, y)` — updating only
the assertions that directly reference those changed signatures is correct.
Inference about interface change from test failure alone is prohibited.)
```

This forces the exception trigger to a concrete, pre-existing document
artifact. The LLM cannot create that artifact retroactively (the plan was
written before execution).

## Prevention

When designing LLM guardrails, ask: **"Can the LLM invoke this exception
from the same evidence the rule was designed to prevent?"**

If yes, the exception is self-defeating. Convert it to require:
1. A **prior artifact** (a plan item, schema, explicit spec) created before
   the guarded action was taken, OR
2. An **external check** that cannot be fabricated from behavior alone.

**Checklist for guardrail exceptions**:
- [ ] Is the exception triggered by a pre-existing artifact (plan step, schema,
  spec), not an inferred outcome?
- [ ] Can the triggering evidence be produced retroactively by the LLM from
  the violation it is supposed to prevent?
- [ ] Is there any external check that confirms the exception is genuine?

## Related

- `.cg-docs/solutions/bugs/2026-04-15-per-batch-retry-counter-unbounded-loop.md`
  — companion P0 finding from the same review; both are adversarial prompt
  design anti-patterns
- `.cg-docs/solutions/testing-patterns/2026-03-30-prompt-pipeline-contract-testing.md`
  — testing strategy that catches such prompt logic bugs
- `.cg-docs/solutions/testing-patterns/2026-04-13-dead-step-after-wait-prompt-session-terminator.md`
  — related prompt-design pitfall: unreachable steps after user-wait pauses
- `.cg-docs/solutions/bugs/2026-04-15-loop-early-exit-skips-per-iteration-cleanup.md`
  — related: loop early-exit directive skips per-iteration cleanup steps
- `.cg-docs/solutions/bugs/2026-05-15-circular-error-recovery-command-in-halt-message.md`
  — variant: recovery suggestion in a halt message is itself blocked by the same missing precondition (bootstrap trap)
