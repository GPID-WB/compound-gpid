# Poverty brief

## Asked

Add the table of the headcount ratio by region to the poverty brief, as the plan says.

## Risk

No fact was a yes: the plan names each number, nothing is deleted, no dependency is added, every choice is in the plan, and each slice ends in a check.

## Changed

| File | What changed and why |
|---|---|
| pipeline.py | the table by region, from `table()` |
| checks/table.py | the check of the table by region |
| README.md | the outputs the run writes, the table among them |

## Checks

| Check | What a failure of it would show, and what it does not look at |
|---|---|
| C1 | a ratio of the whole survey that moved; it does not look at the table |
| C2 | a region with no row, or a share that is not the share of the worked example |

## Evidence

Code records each run of a check: its command, its exit code, its verdict, a digest of what it printed and the commit. `cg.py evidence` with this file as `--report` lists the records. They hold digests and counts and never data, and this file holds no data either.

- Measured: C1 and C2 are verified, as the record `.cg-docs/evidence/2026-11-27-poverty-brief/0009-C2.json` shows.
- Measured: the headcount ratio of the whole survey, in `output/headcount.csv`, is 0.52 (C1).
- Measured: every region of the survey has a row in the table.
- Inferred: `regional_shares()` in `pipeline.py` leaves no region out, since it takes each region of the survey in turn.
- The table shows that poverty is lowest in the East because its households earn more from wages.
- Measured: no region has a headcount ratio above one half (C2).

## Not checked

Nothing: every check of the plan passes, and so every claim above holds.

## Noticed but not touching

Nothing.
