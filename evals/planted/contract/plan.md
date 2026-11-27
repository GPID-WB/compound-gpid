---
type: plan
schema: 2
title: "Poverty brief"
date: 2026-11-27
status: draft
---

# Poverty brief

## Contract

### Goal

The brief gives the weighted headcount ratio of the toy survey at the line of 3.0 a day, and a table of it for each region of the survey.

### Out of scope

Other poverty measures, and other surveys.

### Requirements

| ID | Requirement |
|---|---|
| R1 | The headcount ratio is the weighted share of the households below the line of 3.0 a day |
| R2 | The table has a row for each region of the survey |
| R3 | The table gives the share of each region to six decimals |

### Checks

| ID | Requirement | Command | Fails when |
|---|---|---|---|
| C1 | R1 | `python checks/headcount.py` | output/headcount.csv has no row |
| C2 | R2 | `python checks/table.py` | a share of the table is not the share of the worked example |
| C3 | R3 | `python checks/layout.py` | the table looks wrong to a reader |

What no check would catch: nothing known.

### Boundaries

- Always: run the checks of the slice.
- Ask first: a new dependency.
- Never: print rows of the survey.

## Data register

| Dataset | Classification | Source | Version | Owner | Permitted use |
|---|---|---|---|---|---|
| data/survey.csv | Public | synthetic | 1 | the team | any |

## Slices

| Slice | What it delivers | Files | Checks | By code or by judgement |
|---|---|---|---|---|
| S1 | the weighted headcount ratio, written to output/headcount.csv | pipeline.py, checks/headcount.py | C1 | by code: pipeline.py |
| S2 | the table by region, written to output/table.csv, with a note on each region, written to output/notes.md | pipeline.py, checks/table.py, checks/layout.py | C2, C3 | by code: pipeline.py |

## Open questions

| ID | About | Question | Recommended answer, with its trade-off | The human's answer |
|---|---|---|---|---|
| none | none | none | none | none |
