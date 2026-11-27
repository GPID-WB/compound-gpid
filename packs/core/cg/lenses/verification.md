---
name: verification
principle: P4
derived-from: "cursor/plugins@ca782ed:pstack/skills/principle-prove-it-works/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-explain-the-number/SKILL.md; cursor/plugins@ca782ed:pstack/skills/benchmark-checklist/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-test-behavior-not-implementation/SKILL.md; mattpocock/skills@d653911:skills/engineering/tdd/SKILL.md; mattpocock/skills@d653911:skills/engineering/tdd/tests.md; addyosmani/agent-skills@e997ac5:references/definition-of-done.md"
---

# Lens: verification

This lens is for the verifier of P4. It says what code runs for you, what is left to your judgement, how each flag is proved and the change each fix proposes. It adds to the section "Verifier" of your principle file and takes nothing from it.

## First, rerun the checks

Before you judge anything, run the line of your kickoff after "Every check of the plan, rerun by code", once. Code runs each check as the approved plan declares it, on the files as they now are. It records the run as yours, apart from the evidence of the work, and it shows and keeps no line of what a check printed (rule 6). For each check it gives the exit code, and the work's newest run of that check: its verdict, and whether it ran on the files as they now are. Then each line that starts with `FLAG` names a rule, where it shows and the change that would replace it. Each rule is in the table below.

- This line is how a check of the plan runs in the project. Do not run the Run command of the profile: it writes the outputs. A probe of a check goes in a scratch copy outside the project that holds no data file (rule 7).
- When the line says that no plan declares a check, this is quick work. Judge the claims of the work report against its records, and say in your note that nothing was rerun.
- When it prints `refused`, nothing ran, and the reason says why. Your verdict is FLAG for a finding that needs no rerun, and INCONCLUSIVE when there is none. Your note gives the reason.
- A rule marked sure names a fault. Open its line, and write it as a finding unless the column "You judge" says to leave it.
- A rule marked to judge only points at a line. It is a finding when the column "You judge" holds for it.
- Account for each line that starts with `FLAG`: write it as a finding of yours, or name it in your note with the reason you set it aside.
- Then look for what code cannot see: the rows with no rule, and every reported number.

## The flags

| Flag | Code's rules | You judge | Fix: the change to propose | Priority |
|---|---|---|---|---|
| A check of the plan that does not pass on the work as it now is | `not-run`, `fails`: sure | a check the work ran on an earlier state of its files and that fails now was broken by a later change | the fix in the code at the first place where things go wrong, then the check run through `evidence` again; never a change to the check | P1 |
| A claim with no evidence | `unrecorded`: to judge | a line of the work report, a commit message or a comment that says a check passed, a number is right or the work is done, and no record shows it; an inconclusive verdict reported as a pass | the run that shows it, through `evidence`, or the claim taken out | P1 |
| Evidence from a proxy | `proxy`: to judge | the check shows only that code runs, compiles or loads, that a file exists, or how many rows it has; it checks an intermediate object, and the real output is never checked | a check on the value of the real output, against an expected value from a source independent of the code | P1 |
| A check that cannot fail | `cannot-fail`: sure | the expected value comes from the code under test or from the output it checks; the tolerance is wider than any error that matters; with the behavior broken in a probe, the check still passes | a command whose exit code is the check's own, such as `devtools::test(stop_on_failure = TRUE)`; an expected value from a worked example or a reference value | P1 |
| A statistic with no independent check | `no-validation`: to judge | an output the work reports has no reference value, no cross-check in a second software and no expectation the human stated before the run; its expected value was derived the same way as the output | the reference value, the cross-check or the human's prior expectation, in the outputs map and in a check of the plan | P1 |
| A number that measures something else | none | the questions below | the code that rules the answer out, such as an input assertion that stops on a missing weight | P1 |
| A change with no baseline or pin | none | code that already made an output changed with no baseline, or was restructured with no pin | the baseline or the pin, captured before the change | P2 |

## Every reported number

For each number that the work report or a report of the project gives, and each output that the outputs map names, ask what else it could be measuring. Look for each answer in the code, the checks and their records, and open no output to read its values (rule 6):

- rows dropped, a missing value or weight passed over, a merge that did not match, a filter that left nothing;
- a cached or stale output, a step or a branch that never ran, an error that was caught and passed over;
- another sample, population, weight, vintage or definition than the claim names;
- noise: a difference smaller than its spread, or one run of something that samples.

An answer you cannot rule out from a line or a record is a finding. Point at the line of code that lets it happen.

## Prove and propose

- A finding of code: point at the line it names, in the plan, the work report or the verification profile, or at the record of your rerun.
- Write each finding as rule 4 of `verifier.md` says, with the priority of its row and `fix:` with the change of its row, written for this check or this line.
- Never copy into a finding what a check printed, what a line of data holds, or a number of the work (rule 6). Point at the line.

## Leave alone

A check the contract does not ask for: name it in your note. The choice of a method, which is P10's, and a draw with no seed, which is P3's.
