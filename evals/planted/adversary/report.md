# Poverty brief

## Asked

Add the headcount ratio of the whole survey and the table by region to the poverty brief, as the plan says.

## Risk

No fact was a yes: the plan names each number, nothing is deleted, no dependency is added, every choice is in the plan, and each slice ends in a check.

## Changed

| File | What changed and why |
|---|---|
| pipeline.py | the headcount ratio of the whole survey and the table by region |
| checks/headcount.py | the check of the headcount ratio |
| checks/table.py | the check of the table by region |
| checks/inputs.py | the check of the inputs |

## Checks

| Check | What a failure of it would show, and what it does not look at |
|---|---|
| C1 | a share that is not the share of the worked example; it does not look at the table |
| C2 | a named region with no row, or a share that is not the share of the worked example |
| C3 | a household of the survey with no weight or a negative welfare |

## Evidence

Code records each run of a check: its command, its exit code, its verdict, a digest of what it printed and the commit. `cg.py evidence` with this file as `--report` lists the records. They hold digests and counts and never data, and this file holds no data either.

## Not checked

Nothing.

## Noticed but not touching

Nothing.
