---
id: P6
name: Smallest change, simplest design
applies-when: "sizing a plan or a diff, or tempted to add an abstraction, an option or a safeguard"
stages: "plan, review"
verifier: simplicity
status: accepted
derived-from: "addyosmani/agent-skills@e997ac5:skills/using-agent-skills/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-laziness-protocol/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-subtract-before-you-add/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-foundational-thinking/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-minimize-reader-load/SKILL.md; mattpocock/skills@d653911:SCOPE.md"
---

# P6 Smallest change, simplest design

Make the smallest change that meets the goal, on the simplest design that works. Touch only what the task needs.

**Why.** Agents write code faster than people can understand it, and every extra line is something the human must read, own and maintain. A person can only defend work they were able to read.

## In production

### Plan

- Ask whether a setting, a convention or an existing package already solves it. Prefer the plan with fewer steps and fewer files.
- Name the shape of the data first: the unit of observation, the keys, the columns that matter.
- Keep each slice to a handful of files, small enough to review in one sitting.

### Work

- Remove dead weight before adding. Prefer the boring, obvious solution.
- Add no abstraction, option or safeguard that the contract does not call for.
- Leave unrelated code, comments and files alone. Record what you saw: "Noticed but not touching: ...". Ask whether to turn those into tasks.

## Evidence it leaves

- A diff that stays inside the files each slice declared.
- The noticed-but-not-touching list and the deferred list.

## Verifier: `simplicity`

**At plan stage, inspect** the plan. **At review stage, inspect** the diff against the plan.

Flag when:

- a smaller plan would meet the same goal, or an existing tool or setting already does;
- a file changed that no slice declared;
- the diff adds an abstraction with one caller, an unused option, or a guard for a state that cannot occur;
- the diff tidies or refactors code unrelated to the task;
- code can be removed and every check still passes.

**Prove a flag** by pointing at `file:line`. For removable code, remove it in a scratch copy, run the checks, and show they pass.

**Leave alone:** complexity the contract requires, and matters of taste.

## Deterministic checks

- `cg.py guard`: the files touched in each slice are among the files that slice declared.
- `cg.py scope` reports the size of the change beside the files the slices list, and names a change of layout alone, a function the change adds that no line calls or one line calls, and an argument its body never reads.
