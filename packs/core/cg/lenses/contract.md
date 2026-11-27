---
name: contract
principle: P1
derived-from: "docs/philosophy.md (principle 1); addyosmani/agent-skills@e997ac5:skills/spec-driven-development/SKILL.md; mattpocock/skills@d653911:skills/engineering/to-spec/SKILL.md; mattpocock/skills@d653911:skills/productivity/grilling/SKILL.md"
---

# Lens: contract

This lens is for the verifier of P1. It says what code holds of the contract, what is left to your judgement, how each flag is proved and the change each fix proposes. It adds to the section "Verifier" of your principle file and takes nothing from it.

## What code holds

The contract is what the human approved: the plan's Goal, Out of scope, Requirements, Checks and Boundaries, built on the intent they decided. The line "The contract" of your kickoff says whether they approved the plan as it now reads; when they did not, that is your first finding.

- At the plan stage the playbook ran `cg.py validate` before you: each requirement has a check and each check a requirement, a command in one pair of backticks and an outcome that means failure, a slice runs every check, and nothing is left open. Do not run it. Judge what it cannot read: what the words say, against the intent.
- At the review stage code has run `cg.py claims` on the work. Its record is the newest file with `"kind": "claims"` in the folder of evidence that your kickoff names. Each entry under `findings` with the rule `not-built` is yours, and every other rule is P7's. With no such record, write one finding with no pointer: `claims` has not run on this work. Do not run it again.
- A rule marked sure names a fault. Open its line, and write it as a finding unless the column "You judge" says to leave it.
- Account for each `not-built`: write it as a finding of yours, or name it in your note with the reason you set it aside.
- A check that does not pass is P4's, and a file that no slice lists is P6's: leave both. Then look for what code cannot see.

## At the plan stage

Read the intent the plan is built on, then the contract. Flag:

- a requirement or a "Fails when" that is a matter of opinion, such as "reads well" or "looks right";
- a check that names a requirement and would still pass with it broken, such as a count of rows for a requirement on the weights;
- the wrong result that the intent names, and no check that fails on it;
- a fact, a decision or a part of the goal of the intent that the contract leaves out or changes, such as another poverty line;
- a slice that delivers what no requirement asks for.

Point at the line of the plan, and name in the sentence the line of the intent it breaks.

## The flags

| Flag | Code's rules | You judge | Fix: the change to propose | Priority |
|---|---|---|---|---|
| Something the contract names that was not built | `not-built`: sure | the plan names it as a file the work reads, deletes or leaves alone | the file built as the plan names it, or an amendment the human approves that takes it out | P1 |
| The plan changed since the human's yes | the line "The contract" of the kickoff | the plan as it reads is not the text they approved | the amendment, a dated line the human approves | P1 |
| A requirement built otherwise than the contract says | none | a value, a rule or a group in the code that differs from the requirement or the intent: another line, a group left out, another number of draws | the code changed to what the contract says, or an amendment the human approves | P1 |
| Something built that the contract does not name | none | an output, a measure or an option that no requirement asks for, or that Out of scope names | the code taken out, or an amendment the human approves | P1 |
| A check that does not hold its requirement | none: `validate` holds the IDs | the check passes with the requirement broken, or fails on something else | a check that fails when the requirement is not met, in an amendment | P1 |
| A pass condition that is a matter of opinion | none | "Fails when" names no outcome that someone can observe: an exit code, a value, a count | the outcome that means failure, in an amendment | P2 |

## Prove and propose

- At the review stage, point at the line of code where the work leaves the contract, and name in the sentence the line of the plan or of the intent it leaves. A finding of code: point at the line of the plan it names, or at the record of `claims`.
- For what the contract names and the work never built, point at the line of the plan that names it.
- Write each finding as rule 4 of `verifier.md` says, with the priority of its row and `fix:` with the change of its row, written for this line.

## Leave alone

Wording you would put otherwise, detail the human chose to leave open in the plan, what the plan defers under Out of scope, and the choice of a method, which is P10's. Say in your note what you left and why.
