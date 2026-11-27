---
name: domain-lenses
principle: P10
derived-from: "v1:.agents/skills/cg-data-quality.md; v1:.agents/skills/cg-testing.md; cursor/plugins@ca782ed:pstack/skills/principle-explain-the-number/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-boundary-discipline/SKILL.md"
---

# Lens: the general data lens

This lens is for the verifier of P10, `domain-lenses`: it is the general data lens that core carries. It says what code holds, what is left to your judgement, how each flag is proved and the change each fix proposes. It adds to the section "Verifier" of your principle file and takes nothing from it. A lens of an installed pack for a field, such as survey weights or identification, runs as a verifier of its own beside you.

## What code holds

- No rule of code reads a weight, a merge, a filter or a unit: what the data needs is yours to judge.
- At the plan stage `cg.py validate` held the data register to the recorded classifications. Who may read a dataset is P12's, and a check of the plan that fails is P4's: leave both.
- Your kickoff clears no data file (rule 6 of `verifier.md`). You judge the code that loads, joins, filters, weights and aggregates, and never the rows it reads.

## At the plan stage

Read the shape of the data that the plan states below its data register, its requirements and its checks. Flag:

- an estimate whose unit of observation, weights or population the plan does not state;
- a merge, a filter or a missing value whose rule the plan does not state;
- units, currencies, PPP vintages or reference years that the plan mixes or leaves unnamed;
- a constraint of the project, such as weighted welfare or one PPP vintage, that no check of the plan holds.

Point at the line of the plan.

## The flags

| Flag | You judge | Fix: the change to propose | Priority |
|---|---|---|---|
| A statistic without the weights its data needs | a mean, a share, a total or a quantile over survey rows that reads no weight | the weighted form, such as `collapse::fmean(x, w = weight)` or `weighted.mean(x, weight)` | P0 |
| A denominator that leaves part of the population out | a filter, a merge or a drop of missing values before the division removes units the stated population holds | the denominator over every unit of the population, with the rule for the rest stated | P0 |
| A merge that changes the row count | a join on a key that is not unique, or that drops or repeats rows, with no count before and after | an assertion that the key is unique and that the count after the join is the count before, or the rule for rows that do not match | P1 |
| A missing value dropped or filled with no stated rule | `na.rm = TRUE`, `fillna(0)`, `or 0`, `dropna()` or `replace ... if missing()` on a variable the estimate reads | an error that stops on it, or the rule the plan states | P1 |
| Units, vintages or years mixed | two series with another currency, PPP vintage, reference year, or per capita beside per adult equivalent | one unit, named where the data enters and in the output | P1 |
| A type that changes a value | `as.numeric()` on a factor, a string compared with a number, a code read as a number, an integer that overflows | the conversion written out, with an assertion on its result | P1 |
| A value outside its possible range | a negative welfare, a share above 1 or a weight of 0 passed on to the estimate | an input assertion at the line where the data enters | P1 |
| Data that enters with no input assertion | a column read with no check of its presence, its key, its type or its range | `stopifnot()`, `checkmate::assert_*()` or `assert` at the line that reads it | P2 |
| A check of the estimate on the happy path alone | the checks of the plan hold no missing weight, empty group, single row or boundary value that the data can hold | a check on that case, in an amendment | P2 |

## Prove and propose

- Point at the line of code where it happens: the call that drops the weight, the join, the filter.
- To show it happens, run a probe through the line your kickoff gives for a run: one command, `python -B -c "..."` or `Rscript -e "..."`, that calls the project's code on a few rows you build in the command, such as a household with a missing weight, and fails on the fault. It opens no data file, and holds no value or name of a dataset (rule 6). Then the finding points at the record of the probe and names the line of code in its sentence.
- Write each finding as rule 4 of `verifier.md` says, with the priority of its row and `fix:` with the change of its row, written for this line. A silent correctness failure is P0.

## Leave alone

A method, a measure or a filter the human chose in the plan or the contract names; what a lens of a pack for the field covers; speed; and style. Say in your note what you left, why, and which part needs a colleague who knows the field.
