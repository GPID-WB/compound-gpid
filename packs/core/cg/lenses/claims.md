---
name: claims
principle: P7
derived-from: "docs/philosophy.md (principle 6); cursor/plugins@ca782ed:pstack/skills/blast-radius/SKILL.md; cursor/plugins@ca782ed:pstack/skills/poteto-mode/SKILL.md; addyosmani/agent-skills@e997ac5:skills/source-driven-development/SKILL.md; addyosmani/agent-skills@e997ac5:skills/using-agent-skills/SKILL.md"
---

# Lens: claims

This lens is for the verifier of P7. It says what code has already found, what is left to your judgement, how each flag is proved and the change each fix proposes. It adds to the section "Verifier" of your principle file and takes nothing from it.

## What code found

At the review stage, code has run `cg.py claims` on the work. Its record is the newest file with `"kind": "claims"` in the folder of evidence that your kickoff names. It read the work report against the files of the project, the records of the work and the outputs of the outputs map, and it shows and keeps no number and no line of them. Each entry under `findings` is a rule, where it shows, and the change that would replace it. The rule `not-built` is P1's, and every other rule is yours and in the table below.

- Do not run it again. With no such record, write one finding with no pointer: `claims` has not run on this work.
- A rule marked sure names a fault. Open the line, and write it as a finding unless the column "You judge" says to leave it.
- A rule marked to judge only points at a line. It is a finding when the column "You judge" holds for it.
- Account for each entry of yours: write it as a finding of yours, or name it in your note with the reason you set it aside.
- A claim that a check of the plan passed, or of a success that names no check and no record, is P4's, `unrecorded` and `unbacked`: leave it. Then read each claim for what code cannot see.

## Each claim

A claim is a line of the work report, or of a text written for readers, that says what was done, found or measured. Ask of each how it is known, and open what it points at:

- **measured:** its pointer opens and shows what the line says: the record of that check, the line of code that does what it says, the row of the outputs map;
- **inferred:** the reasoning is written beside it, and it holds: a share does not show a cause, and two points make no trend;
- **guess:** it says so, and nothing is built on it;
- written as fact with no label: it is one of the three, and the line does not say which.

## The flags

| Flag | Code's rules | You judge | Fix: the change to propose | Priority |
|---|---|---|---|---|
| A file or a record named that is not there | `no-such-file`: sure | a file the change deleted, which the line says it deleted | the path as the project holds it, or the claim taken out | P1 |
| A file the Changed table names that the change left as it was | `unchanged`: sure | none | the row taken out | P2 |
| A claim labelled measured with no pointer | `unpointed`: sure | none | the pointer to what shows it, or the label inferred or guess | P1 |
| A function named that does not exist | `undefined`: to judge | no code of the project, of the language or of a package it loads defines it; one that its documentation names, with the page cited in the line: leave it | the name as it is defined, with the page of its documentation | P1 |
| A number in the text that differs from its output | `unmatched`: to judge | the line gives it as a result of that output, and not as a line, a tolerance or a count of draws; code compared it with the output, so open no output | the number as the output holds it, written by code | P1 |
| An inference or a guess written as fact | none | a cause, a trend or a comparison that no pointer shows, with no label or labelled measured | the label inferred with its reasoning, or guess | P1 |
| A pointer that does not show what is claimed | none | the record or the line opens and shows something else, or the opposite | the pointer that shows it, or the claim taken out | P1 |
| Nothing said of what was not checked | none | "Not checked" says nothing, or leaves out what the plan says no check would catch | the list of what was not checked | P2 |

## Prove and propose

- Point at the line of the work report that makes the claim. A finding of code: point at the line it names, or at the record of `claims`.
- Open the pointer of a claim yourself and say in your sentence what it shows; never copy into a finding a number of the work, what a line of data holds or what a check printed (rule 6).
- Write each finding as rule 4 of `verifier.md` says, with the priority of its row and `fix:` with the change of its row, written for this line.

## Leave alone

Claims the human made, under "Asked" or in the plan; a plain statement of what a file contains; whether a check passed, which is P4's; and the choice of a method, which is P10's. Say in your note what you left and why.
