---
name: determinism
principle: P3
derived-from: "cursor/plugins@ca782ed:pstack/skills/principle-build-the-lever/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-make-operations-idempotent/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-prove-it-works/SKILL.md; mattpocock/skills@d653911:skills/engineering/retro/SKILL.md"
---

# Lens: determinism

This lens is for the verifier of P3. It says what code has already found, what is left to your judgement, how each flag is proved and the code each fix proposes. It adds to the section "Verifier" of your principle file and takes nothing from it.

## What code found

At the review stage, code has run `cg.py repro` on the work. Its record is the newest file with `"kind": "repro"` in the folder of evidence that your kickoff names. It ran the Run command of `.cg-docs/verification.md` twice, compared the digest of each output that the outputs map names, and searched the files of the change. Each entry under `findings` is a rule, where it shows, and the code that would replace it. Each rule is in the table below.

- Do not run `repro`, the Run command or the pipeline: each writes the outputs, and rule 7 of `verifier.md` holds. Your note says what you did not run.
- With no such record, write one finding with no pointer: `repro` has not run on this work.
- A rule marked sure names a fault. Open the line, and write it as a finding unless the column "You judge" says to leave it.
- A rule marked to judge only points at a line. It is a finding when the column "You judge" holds for it.
- Then look for what code cannot see: the rows with no rule, and the column "You judge" of each row.

## At the plan stage

No code has run. Read the slices, the checks and the boundaries of the plan, and `.cg-docs/verification.md`. Flag:

- a slice done by judgement that delivers a table, a figure or a number someone will read;
- a slice done by code that names no tool, or whose tool does not run from the inputs to the outputs;
- a step, a check or a boundary in which a person or the model copies, pastes, types, renames, clicks, exports or reads a number off a screen;
- a slice that samples, bootstraps, simulates or splits, and no seed in the plan;
- outputs to make, and no Run command in the verification profile.

Point at the line of the plan, or of the profile.

## The flags

| Flag | Code's rules | You judge | Fix: the code to propose | Priority |
|---|---|---|---|---|
| An output that no script regenerates | `no-run`, `not-written`, `changed`, `missing`, `once`, `unmapped`, `run-failed`: sure | whether a path of the outputs map is an output; a function lives in code, and no run writes it; a pipeline that keeps a cache, such as `targets` or `make`, writes nothing it holds up to date | the step of the Run command that writes the output from the inputs: a script, a function or a `targets` target; for a cache, a Run command that rebuilds, such as `make -B` | P1 |
| A number typed into prose | `typed-number`: to judge | it is a result an output holds, and not a year, a version, a section number or a tolerance | inline code that reads it from the output, such as `` `r round(ci$low, 3)` ``, or a table that code writes | P1 |
| A step a person does | none | a step in the plan, the README, a report or the work report that copies, pastes, types, renames, clicks or exports | the script that does that step, called from the Run command | P1 |
| A draw with no seed | `unseeded`, and `differs` on an output: sure | a seed set in a file that runs first, which your note names; a seed set inside a function, which seeds no draw outside it | `set.seed(<a seed>)` in R, `numpy.random.default_rng(<a seed>)` in Python, `set seed <a seed>` in Stata, above the first draw | P1 |
| An environment that is not pinned | `unpinned`: sure | an R package declares what it needs in `DESCRIPTION` and pins nothing: leave it | `renv::snapshot()`; `uv init --bare`, then `uv add` for each package the code imports; or `version 18` as the first command of a do-file | P2 |
| A path that holds on one machine only | `home-path`: sure | a path to a drive or a server that only one machine has, which no rule finds | a path from the project root, such as `here::here("data", "survey.csv")`; for data that its rule keeps outside the project, a folder that each machine sets, such as `Sys.getenv("SURVEY_DIR")` | P2 |
| An output that depends on order or on the clock | `differs`: sure; `unsorted`, `clock`: to judge | the order or the time reaches an output that is compared; rows after a join, a set or a `distinct()` with no sort | `arrange()` or `sort_values()` before the write, `sorted()` around a listing, the date passed in as an input | P1 |
| A fetch with no saved copy | `network`: to judge | the run reads the address, and no copy with its date and source | a copy saved in the project, read from there, with its source in the data register | P2 |
| Clerical work asked of the model | none | an instruction that has the model copy, count or transcribe what a command could | the command that does it | P2 |

## Prove and propose

- A finding of code that names a line: point at that line. One that names no line, such as `differs`, `unpinned` or `no-run`: point at the record of `repro`.
- Write each finding as rule 4 of `verifier.md` says, with the priority of its row and `fix:` with the code of its row, written for this file and this line.
- Never copy what the line holds into the finding: a path under a home folder holds a person's name, and a typed number is a value (rule 6).

## Leave alone

Interpretation and the choice of a method, one or two obvious edits, a number in prose that no output holds, a clock that only times a run, and a listing whose order reaches no output. Say in your note what you left and why.
