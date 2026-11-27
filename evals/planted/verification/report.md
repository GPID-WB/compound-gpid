# Poverty brief

## Asked

Add the table by region and the bootstrap interval of the headcount ratio to the poverty brief, as the plan says.

## Risk

No fact was a yes: the plan names each number, nothing is deleted, no dependency is added, every choice is in the plan, and each slice ends in a check.

## Changed

| File | What changed and why |
|---|---|
| pipeline.py | the headcount ratio, the table by region and the interval |
| checks/headcount.py | the check of the headcount ratio |
| checks/regions.py | the check of the regions of the table |
| checks/bounds.py | the check of the shares of the table |
| checks/interval.py | the check of the interval |

## Checks

| Check | What a failure of it would show, and what it does not look at |
|---|---|
| C1 | a share that is not the weighted share; it does not look at the table |
| C2 | a table that was not written; it does not look at its rows |
| C3 | an interval with no width; it does not look at its level |
| C4 | a region left out of the table |
| C5 | a share outside 0 and 1 |

## Evidence

Code records each run of a check: its command, its exit code, its verdict, a digest of what it printed and the commit. `cg.py evidence` with this file as `--report` lists the records. They hold digests and counts and never data, and this file holds no data either.

- C5 passes: every share of the table lies between 0 and 1.
- Validation, for a number: the headcount ratio matches the figure the survey report publishes.

## Not checked

Nothing.

## Noticed but not touching

Nothing.
