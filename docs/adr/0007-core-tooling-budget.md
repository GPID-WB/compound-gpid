# ADR 0007: The budget of the core tooling is 4,000 lines

Date: 2026-11-26. Status: decided by the maintainer on 2026-11-26, during task 2.4 (#227), and passed to the build by the session that runs it.

## Context

`SCOPE.md` capped the core tooling, `packs/core/` without its tests, at 2,500 lines. The number came from the plan (section 6.6), before any of milestone 2 was built. It was an estimate.

It did not hold. Tasks 2.1 to 2.3 moved into code what an agent must not get wrong, and each move followed a failure that was observed at a gate or in a review:

- the artifact schema, after a work report passed as complete with cells left empty, and after two agents read the risk of a change differently at the first gate;
- the reply rule, after replies such as "sounds good", "yes, but" and a question were recorded as a yes;
- what an intent and a plan may leave open, after a plan that still marked a value as pending was called complete at a gate rerun;
- the data rules, after the answers about data were never recorded at the first gate.

After the review of task 2.3, `cg.py` stood at 1,705 lines, with `evidence`, `guard`, `verifiers`, `conformance`, `repro`, `decide`, `index` and `search` still to come. That review listed what the earlier tasks could give back without losing a check: about 50 lines. Task 2.4 then added `evidence` and `guard`, and what holds them, in 335 lines.

## Decision

- **The limit for core tooling is 4,000 lines.** `SCOPE.md` and `tools/check_budgets.py` hold the number. The other budgets stay as they are, and so does the rule that tests are at most 1.5 times the code they cover.
- **The equal deletion is waived this once.** `SCOPE.md` asks that a raised limit comes with a decision record and an equal deletion elsewhere. No deletion of 1,500 lines exists: version 2 already removed the version 1 tree. So this record stands alone. The rule itself stays in force for the next time.
- **The trims are still taken.** Task 2.4 took those the review of task 2.3 listed, except the one that changes the lists of replies and `grilling.md` with them: 29 lines.
- **The limit is looked at again at the end of milestone 2**, when every command of the loop exists and the line count is a measurement.

## Considered and set aside

- Keeping 2,500 and moving commands into packs. The commands still to come are the loop's own, and core never imports from a pack (`SCOPE.md`).
- Splitting `cg.py` into several files. The budget counts lines of tooling, not files, so a split changes nothing in it. Whether one file stays readable is a separate question, for the same review at the end of milestone 2.
- No limit. The limit is what made each task count its lines and give some back.

## Consequences

- The plan's section 6.6 still says 2,500. The plan is left as it was approved, and this record holds the number in force.
- A build session goes on reporting, for each task, the lines it added and the lines it gave back.
