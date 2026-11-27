# Poverty brief

## Asked

Add the table of the headcount ratio by region to the poverty brief, as the plan says.

## Risk

No fact was a yes: the plan names each number, nothing is deleted, no dependency is added, every choice is in the plan, and each slice ends in a check.

## Changed

| File | What changed and why |
|---|---|
| pipeline.py | the table by region, its option and its check of the line |
| checks/table.py | the check of the table |
| checks/headcount.py | laid out again |

## Checks

| Check | What a failure of it would show, and what it does not look at |
|---|---|
| C1 | a region with no row, or a share that is not the share of the worked example |
| C2 | a ratio of the whole survey that moved |

## Evidence

Code records each run of a check: its command, its exit code, its verdict, a digest of what it printed and the commit. `cg.py evidence` with this file as `--report` lists the records. They hold digests and counts and never data, and this file holds no data either.

## Not checked

Nothing.

## Noticed but not touching

Nothing.
