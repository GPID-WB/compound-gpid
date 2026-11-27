# ADR 0010: The verification verifier: how it reruns the checks, what code holds of P4, and its lens

Date: 2026-11-27. Status: proposed in task 2.7 (#230) as the working version. It waits for the maintainer's acceptance. Before 2.0 it changes by amending this record.

## Context

The issue asks that the verifier of P4 reruns every declared check itself; flags claims with no evidence, evidence from a proxy, checks that cannot fail and statistics with no independent check; asks of every reported number what else it could be measuring; and catches its planted violations. Section 4.3 of the plan gives the proxies ("it compiles", "the file exists") and the independent checks (a second software, a reference value, a prediction the human made beforehand). The question about a number is pstack's `principle-explain-the-number`.

Three things stood in the way of "reruns every declared check itself". Rule 7 of `verifier.md` lets a verifier leave nothing in the project but the record of a run. `cg.py evidence <check ID>` records a run as the work's own evidence and prints all that the check printed, which can hold rows of a dataset (P12). And the kickoff clears no data file, while a declared check may read one (an open point of item 40 in the handoff).

As in ADR 0009, each flag was split in two: the part a rule can find, which code finds with a test, and the part that needs judgement, which the lens names (mattpocock's `retro`).

## Decision

### How the verifier reruns a declared check

- **Through `cg.py evidence --rerun --report <work report>`.** With no check ID it runs every check of the plan, and with one it runs that check. Each command is the one the approved plan declares for it, run on the files as they now are, in the project, through the shell, as `evidence` runs it. It refuses as `evidence <check ID>` does: no plan, a plan not approved as it now reads, a Command cell that is not one text in backticks, or a stop that waits for the human. Code runs nothing then, and the lens has the verifier say why.
- **The record is the verifier's.** One record of `"kind": "rerun"` in the evidence of the work report. For each check it holds the exit code, a digest and two counts of what the check printed, and the work's newest run of that check: its record, its exit code, its verdict, whether it printed the same bytes, and whether it ran on the files as they now are. Then the findings of code, the files the runs made by a digest of each name, the commit and the state of the change. `runs`, `unproven`, `guard` and `validate` read only records of `"kind": "check"`, so a verifier's run never stands for the work's evidence and never completes the work: the work's records stay as they were. `cg.py conformance` takes a record of a rerun of this work as proof, as it takes the record of a check or of `repro` (ADR 0008).
- **Nothing a check printed is shown or kept (P12).** The rerun prints the exit code of each check and the comparison, never the output. This is stricter than `evidence`, which shows the agent that does the work all that a check printed, so that it can read it against "Fails when".
- **Data.** A declared check reads what the plan's data register lists, which the human approved with the plan, and the verifier sees an exit code and a digest of what it read. A probe of the verifier's own goes in a scratch copy outside the project that holds no data file (the lens). So a verifier reruns code that reads a data file only as a check the human approved.
- **Rule 7 holds.** The record of the rerun is the record of a run. A check that writes files into the project leaves them, and `guard` names each one `written` by the rerun, as it does for a check of the work (ADR 0009).
- **The line is in the kickoff.** `templates/kickoff.md` gained one line: "Every check of the plan, rerun by code", followed by the line code fills in. At the plan stage it says "none at this stage", and on quick work "none: no plan declares a check for this work". Every verifier at the review stage of work on a plan gets it. Only the verification lens asks for it.
- **Considered and set aside.** `evidence <check ID>` as it is: the verifier's run would become the work's newest record of the check and could complete the work, it is labelled `declared` like the work's, and it shows all that a check printed. A run by the work playbook before the verifiers, as `repro` is run: then the verifier does not rerun the checks itself, which the issue asks. Reading the work's records only: a record is the author's claim (rule 2 of `verifier.md`). A line in the lens that the verifier builds from the kickoff's line for a run: the agent would edit a command line, where every other line code prints runs as written. The line only in the kickoff of the verification verifier: dispatch would then name a verifier in code, where it is computed from the principle files.

### What code holds, and what stays by judgement

| Flag | What code finds (a rule of the rerun) | What stays by judgement |
|---|---|---|
| A check that does not pass on the work as it now is | `not-run`: no run of the check in the work's evidence, as the plan now declares it; `fails`: the rerun ends with an exit code other than 0, and the record says whether the work's run was on an earlier state of its files | whether a later change broke it, and where |
| A claim with no evidence | `unrecorded`: a line of the work report that names a check and a word of success, with no word of negation, while that check has no verified run | a claim in other words, in a commit message or a comment; an inconclusive verdict reported as a pass |
| Evidence from a proxy | `proxy`: a command that only shows that a file exists, that code compiles, builds or collects its tests, or that is the Run command of the profile | a check on an intermediate object; a count of rows |
| A check that cannot fail | `cannot-fail`: a command whose exit code its shape sets: `\|\| true`, `; echo`, a pipe into a filter such as `sort` or `tail`, `--exit-zero`, `python -O`, and the defaults of `devtools::test()` and `rcmdcheck::rcmdcheck()`, which exit with 0 when a test fails | an expected value from the code under test or from the output it checks; a tolerance wider than any error that matters; a check that still passes with the behavior broken |
| A statistic with no independent check | `no-validation`: an output of the outputs map with nothing under "What proves it right" | whether the work reports that output; an expected value derived the same way as the output |
| A number that measures something else | nothing | the questions of the lens: dropped rows, a stale output, another sample or definition, noise |

Each rule carries the change that would replace what it finds, and the rerun prints it beside the finding.

**A run older than the files it covers** is found too: the record of a check holds the state of the files of its slice, and code computes that state again for the files and the commit of the slice in force when the check ran. It is shown for each check, and it is a finding only with `fails`. The rerun is on the files as they now are, so it settles what an earlier run left open: as a finding alone it would flag every check of an early slice whose files a later slice changed, though the check still passes.

### The lens

`packs/core/cg/lenses/verification.md`, 53 of its 60 lines, in the shape of the determinism lens (ADR 0009): rerun the checks first, with what code shows and what to do when it refuses; a table of the flags, each with code's rules, marked sure or to judge, what the verifier judges, the change to propose and a priority; what else every reported number could be measuring, from pstack's `principle-explain-the-number` and the questions of its `benchmark-checklist` rewritten for statistics (the seven questions of P4 hold the rest); how to prove and propose; and what to leave alone. A test holds the lens to every rule code writes, to a fix in every row, and to the line of the kickoff.

### The planted cases

`evals/planted/verification/` follows `evals/planted/determinism/`, with three more files: `intent.md`, `report.md` and, under `work` in `expected.json`, each slice with the checks the work ran and what the files held then. The runner builds the work as it went: the intent and the plan approved, each slice started, the files put back as they were then, the Run command run and the slice's checks recorded. Nine cases: six with a rule of code (a check that never ran, one that fails now on a change after its run, one that cannot fail, one on a proxy, a claim with no record, a statistic with nothing that proves it right), and three by judgement (an expected value computed by the code under test, a headcount that leaves out the households with no weight, a claim of validation with no record). `tests/core/test_verification.py` holds code's part in CI. `run_planted.py --verifier verification` gives the lens the same work through a coding agent, judges the verdict block with one finding for each case, and asks that a record of a rerun made in the verifier's turn holds every check of the plan. Step W of the gate asks the same of the gate's work. The build agent ran the runner with `--dry-run` only.

### Also built in this task

- `cg.py repro` refuses to write over an output that no commit holds (ADR 0009, "Changes").
- A `requirements.txt` or an `environment.yml` that pins every package is a pin (ADR 0009, "Changes").
- `cg.py status --guide --playbook work` names quick work when no plan is approved as it now reads, with a `next` line that says so (gate rerun 22: an agent asked for a change took the row of the guide for the work, read that the work playbook needs an approved plan, and changed nothing). The guide's row says it in one clause. `--playbook plan` and `--playbook brainstorm` are as they were.

## Consequences

- `cg.py` went from 2,626 to 2,757 of its 4,000 lines: 91 for the rerun, its rules, the kickoff's line and the proof; 17 for the refusal of `repro`; 16 for the pins; 7 for the status.
- The close of work on a plan runs every check once more, in the verifier's turn.
- Every kickoff has one more line, which only one verifier is asked to run.
- A FLAG of the rerun blocks nothing. Its findings go to the human through the verifier.

## Changes

- 2026-11-27, review of task 2.7 (#230). `unrecorded` takes a word of negation only when it stands at most three words before the word of success, so a claim with a negation elsewhere in its line is found. `cannot-fail` also finds `testthat::test_file()` without `stop_on_failure = TRUE`, `try()`, and a `tryCatch()` that stops nothing, which exit with 0 when a test fails (measured with testthat 3.3; `devtools::check()` run by `Rscript` errors on a warning, so it can fail). `proxy` also finds a check that only loads code or searches a test or code file, and no longer a file test followed by `&&` or `;`. An approved plan changed since its yes sends a request for its work to the work playbook, as an in-progress one does, and that playbook sends the human to `/cg plan`. The lens has the verifier account for each line of code that starts with `FLAG`, and read no output for its values. The runner leaves out the byte code that a rerun makes Python write, and a finding catches a case only when it names ten lines at most, or a record that is there.

- 2026-11-27, task 2.8 (#231), V18 of the review of task 2.7: the kickoff says, on the line after the rerun line, that only the verifier `verification` runs it, once, and that any other verifier leaves it and reads the record of that rerun when there is one. Nothing in code changed: the line is still in every kickoff at the review stage of work on a plan.

- 2026-11-27, task 2.8 (#231), second half, from the first run of the lens (ADR 0012): the rule `unbacked` names a claim of success or of validation that names no check of the plan and no record of a run of this work, beside `unrecorded`, with one pattern for both that now holds the words of validation (matches, agrees, reproduces, validated). Both read only the lines the agent wrote: none of the template's own text and none under "## Asked". The lens has the verifier trace each reported number to the line that computes it, and name each filter, merge, weight and unit on the way. The planted claim of validation is now found by code.

## Open

- Whether `validate` applies the rule `cannot-fail` to a plan's commands at the plan stage, before the human approves the plan. It was not built: it would change what `approve` takes, which every gate has passed, and P4 has no verifier at the plan stage.
- The rules are lists. Known misses: a Stata do-file run in batch mode, whose exit code may not show an error (not tried here); a pipe into `grep`; a claim of success in other words, such as "C3 is fine", or in another language; a proof cell of the outputs map that says in words that nothing independent was found. Known false alarms: a pipe inside a quoted string, a pipe under `pipefail`, `rcmdcheck()` with `RCMDCHECK_ERROR_ON` set.
- Whether a run on an earlier state of its files is a finding of its own when the rerun passes.
- Quick work has no plan, so its verifier reruns nothing. Its self-review is as earlier gates passed it.
