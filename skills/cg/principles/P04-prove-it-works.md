---
id: P4
name: Prove it works
applies-when: "after each slice and before declaring anything done"
stages: "review"
verifier: verification
status: draft
derived-from: "docs/philosophy.md (principle 2); cursor/plugins@ca782ed:pstack/skills/principle-prove-it-works/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-test-behavior-not-implementation/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-explain-the-number/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-sequence-verifiable-units/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-fix-root-causes/SKILL.md; mattpocock/skills@d653911:skills/engineering/tdd/SKILL.md; addyosmani/agent-skills@e997ac5:skills/using-agent-skills/SKILL.md"
---

# P4 Prove it works

Verify every result on the real thing, with a check that can fail, from a source independent of the code that produced it.

**Why.** Generating and verifying are different jobs. When the same agent writes the code and the test, a passing test can repeat the code's misunderstanding. "It runs" and "it looks right" are not evidence.

## In production

- **Agree the checks first.** No check is written at a point the human has not confirmed. Give each proposed check one line on what it catches and what it misses.
- **Red before green.** Where possible, see the check fail before the change and pass after it.
- **Check the real artifact:** the actual pipeline output, the actual number, the actual file. A file's existence, a clean compile or the agent's own report is a proxy.
- **Take expected values from an independent source:** a reference value, a worked example, a published figure, or the same computation in a second software such as R against Stata. Never recompute the expected value the way the code does.
- **Predict, then check.** For a statistic, ask the human what they roughly expect before the check runs.
- **Explain the number.** Before trusting a result, list what else it could be measuring (dropped rows, a wrong subsample, missing weights, cached output, code that never ran) and rule each out.
- **One slice, one check.** Do not start the next slice until the current one passes.
- **When a check fails,** suspect the way you observed before the system, then fix the first place things went wrong. Never weaken a check to make it pass.

## Evidence it leaves

- One evidence entry per declared check: command, exit code, output digest, commit.
- The red-then-green record where one exists.
- The cross-check or reference comparison for each statistic.

## Verifier: `verification`

**Inspect** the plan's checks, the evidence entries, the work report and the outputs. **Rerun every declared check yourself.**

Flag when:

- a claim of done has no evidence, or evidence from a proxy;
- a check still passes when the behavior it guards is broken (break the behavior in a scratch copy and run it);
- an expected value was derived the same way as the result;
- a statistic has no independent check;
- a test was deleted, skipped or loosened;
- a reported number is unexplained: nothing rules out the other things it could be measuring.

**Prove a flag** with the command you ran and its output.

**Leave alone:** missing tests for behavior the contract does not cover; note those under `not-checked`.

## Deterministic checks

- Every check ID in the approved plan has an evidence entry at the current commit.
- `cg.py guard`: the diff does not delete or skip tests or add suppressions.
- Every evidence entry records exit code 0, or is listed as failing.
