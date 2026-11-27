---
name: simplicity
principle: P6
derived-from: "addyosmani/agent-skills@e997ac5:skills/code-simplification/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-laziness-protocol/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-subtract-before-you-add/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-minimize-reader-load/SKILL.md"
---

# Lens: simplicity

This lens is for the verifier of P6. It says what code has already found, what is left to your judgement, how each flag is proved and the change each fix proposes. It adds to the section "Verifier" of your principle file and takes nothing from it.

## What code found

At the review stage, `cg.py guard` held each slice to the files it lists, and code has run `cg.py scope` on the work. Its record is the newest file with `"kind": "scope"` in the folder of evidence that your kickoff names. It gives the size of the change beside the files the slices list. Each entry under `findings` is a rule, where it shows, and the change that would replace it. Each rule is in the table below.

- `scope` runs nothing and writes only its record: do not run it again. With no such record, write one finding with no pointer: `scope` has not run on this work.
- A rule marked sure names a fault. Open the line, and write it as a finding unless the column "You judge" says to leave it.
- A rule marked to judge only points at a line. It is a finding when the column "You judge" holds for it.
- Account for each entry under `findings`: write it as a finding of yours, or name it in your note with the reason you set it aside.
- Then look for what code cannot see: the rows with no rule, and the column "You judge" of each row.

## At the plan stage

No code has run. Read the goal, the requirements, the slices and the boundaries of the plan, and the code the project already has. Flag:

- a slice that builds what the project, a package it already loads, or the standard library already does;
- a slice, an option or a setting that no requirement asks for;
- a plan that a smaller one would meet: fewer slices, fewer files, one step where it names two;
- a slice that tidies or restructures code that the goal does not touch.

Point at the line of the plan.

## The flags

| Flag | Code's rules | You judge | Fix: the change to propose | Priority |
|---|---|---|---|---|
| A change that only tidies | `reformat`: sure | the plan asked for that layout | the file put back as the commit holds it | P2 |
| Code that nothing calls | `no-caller`: to judge | the package exports it, a test or a person who uses the package calls it, or it is an entry point: leave it | the function taken out | P2 |
| An abstraction with one caller | `one-caller`: to judge | it only forwards, or its name tells a reader nothing the caller does not | its body written at its one caller | P3 |
| An option nobody uses | `unused-argument`: to judge | the body never reads it and no requirement asks for it | the argument taken out of the function and of its calls | P2 |
| A check for a state that cannot occur | none | it tests a value the code itself sets, or one the contract fixes | the check taken out; an input assertion where data enters stays | P3 |
| A file that no slice lists | none: `guard` holds each slice | a file changed after the last slice, or one a slice lists for no requirement | the change undone, or an amendment the human approves | P1 |
| Code that can go | none | with it taken out of a scratch copy, every check of the plan still passes | the code taken out | P2 |
| A smaller design | none | a package the project loads, a setting or the standard library does the same | that package, setting or function | P2 |

## Prove and propose

- Point at the line of the function or of the plan. For code that can go, take it out in a scratch copy outside the project that holds no data file, run the checks of the plan there, and say in your note that they passed. The finding still points at the line (rule 7).
- Write each finding as rule 4 of `verifier.md` says, with the priority of its row and `fix:` with the change of its row, written for this line.

## Leave alone

Complexity the contract requires, an input assertion where data enters (P10 asks for it), a design the human chose in the plan, and matters of taste. Say in your note what you left and why.
