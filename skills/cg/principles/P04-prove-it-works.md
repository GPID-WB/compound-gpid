---
id: P4
name: Prove it works
applies-when: "after each slice and before declaring anything done"
stages: "review"
verifier: verification
status: accepted
derived-from: "docs/philosophy.md (principle 2); cursor/plugins@ca782ed:pstack/skills/principle-prove-it-works/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-test-behavior-not-implementation/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-explain-the-number/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-sequence-verifiable-units/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-fix-root-causes/SKILL.md; cursor/plugins@ca782ed:pstack/skills/benchmark-checklist/SKILL.md; cursor/plugins@ca782ed:pstack/skills/create-verification-skill/SKILL.md; cursor/plugins@ca782ed:pstack/skills/maintain-verification-skill/SKILL.md; cursor/plugins@ca782ed:pstack/skills/figure-it-out/SKILL.md; cursor/plugins@ca782ed:pstack/skills/tdd/SKILL.md; cursor/plugins@ca782ed:pstack/skills/poteto-mode/playbooks/bug-fix.md; cursor/plugins@ca782ed:pstack/skills/poteto-mode/playbooks/refactoring.md; mattpocock/skills@d653911:skills/engineering/tdd/SKILL.md; addyosmani/agent-skills@e997ac5:skills/using-agent-skills/SKILL.md"
---

# P4 Prove it works

Work is proven in two ways, and both are required.

- **Verification:** the work does what the contract says, shown by checks that can fail, run on the real output.
- **Validation:** the result is right for the question, shown against something independent of our code.

**Why.** Generating and checking are different jobs. When the same agent writes the code and the test, a passing test can repeat the code's misunderstanding. A pipeline can do exactly what was specified and still give a wrong estimate. "It runs" and "it looks right" are proxies.

Terms used here are defined in the plugin glossary (`../GLOSSARY.md`): verification, validation, real output, proxy, check, baseline, pin, reference value, cross-check, verdict, evidence.

## In production

### Setup: the verification profile

Each project has a verification profile, written once by setup and kept current:

- **Run:** the one command that produces the outputs from the inputs.
- **Doctor:** one read-only check that the environment is fit to run: package versions, data vintage present, credentials valid.
- **Outputs map:** each important output, where it lives, and what proves it right (a reference value, a cross-check, an input assertion).
- **Evidence:** where proof is kept.

A profile that was never run end to end is a draft. A profile that no longer matches the project is fixed before it is used.

### Plan

- Agree the checks with the human before work. Give each proposed check one line on what it catches and what it misses.
- For a statistic, write down what result is expected and what result would change the decision, before anything runs.
- Before changing existing code, capture the baseline: the current value of the outputs the change may move.
- Before restructuring code whose behavior must stay the same, write the pin.

### Work: verification

- See each check fail before the change and pass after it, where that is possible. Prefer no new check over a bad one: a check that cannot fail, or that mirrors the code, proves nothing.
- Check the real output, in the place its reader will see it: the number in the final table, the function as a package user calls it, the dashboard as it runs. A check on an intermediate object does not cover the final one.
- Finish one slice and pass its check before starting the next.
- For a restructuring, show the outputs are unchanged against the pin: old against new.
- When a check fails, suspect the way you observed before the system. Then fix the first place things went wrong. A check is never weakened to make it pass.

### Work: validation

- Compare against an independent source: a reference value, a published figure, a worked example from the method's documentation, or a cross-check in a second software such as R against Stata. The expected value is never recomputed the way the code computes it.
- Ask the human what they roughly expect before the check runs, then compare.
- Put every reported number through the seven questions:
  1. **What drives it?** Name what the number depends on most.
  2. **Like with like?** Both sides of a comparison use the same sample, weights, vintage and definitions.
  3. **Within bounds?** A share lies between 0 and 1, parts sum to the total, a count does not exceed the population.
  4. **Did anything fail quietly?** Count dropped rows, missing values, warnings and unmatched merges.
  5. **Does it repeat?** A rerun gives the same number; where there is sampling, the spread is reported.
  6. **Does it matter?** The difference is larger than its noise and changes a conclusion.
  7. **Did it happen?** The code ran on the intended data: no empty filter, no stale cached target, no branch that never executed.

### Every stage

- Give each thing checked one verdict: **verified**, **not verified**, or **inconclusive**. Inconclusive is not a pass, and neither is a check run in the wrong place. Say so plainly.

## Evidence it leaves

- One evidence entry per declared check: command, exit code, output digest, commit.
- The failing-then-passing record where one exists; the baseline and the pin comparison where they apply.
- The comparison against a reference value or cross-check for each statistic, and the human's prior expectation.
- A verdict for every check.

## Verifier: `verification`

The verifier runs in a fresh context. A verdict from the agent that wrote the work does not count, and a green automated run is not a verdict.

**Inspect** the contract's checks, the evidence, the work report and the outputs. **Rerun every declared check yourself.**

Flag when:

- a claim of done has no evidence, or rests on a proxy;
- a check still passes when the behavior it protects is broken (break it in a scratch copy and run the check);
- a check ran on an intermediate object and the real output was never checked;
- an expected value was derived the same way as the output;
- a statistic has no validation: no reference value, no cross-check, no prior expectation;
- a reported number fails or skips any of the seven questions;
- existing code changed with no baseline, or was restructured with no pin;
- a check was deleted, skipped or loosened;
- a verdict of inconclusive was reported as a pass.

**Prove a flag** with the command you ran and its output.

**Leave alone:** missing checks for behavior the contract does not cover. Note those under `not-checked`.

## Deterministic checks

- Every check ID in the approved plan has an evidence entry at the current commit.
- `cg.py guard`: the diff does not delete or skip checks or add suppressions.
- Every evidence entry records exit code 0, or is listed as failing.
- The verification profile's doctor passes before any check is trusted.
