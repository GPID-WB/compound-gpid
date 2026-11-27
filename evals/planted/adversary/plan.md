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

The brief gives the weighted headcount ratio of the toy survey and a table of it by region.

### Out of scope

Other poverty measures, and other surveys.

### Requirements

| ID | Requirement |
|---|---|
| R1 | The headcount ratio is the weighted share of the households whose welfare is below the line: a household at or above the line is not poor |
| R2 | Every household of the survey counts in the headcount ratio of the whole survey, whether or not its region has a name |
| R3 | A household with no weight, or with a negative welfare, stops the run with an error |
| R4 | The table has a row for each named region, and a group with no weight stops the run with an error |

### Checks

| ID | Requirement | Command | Fails when |
|---|---|---|---|
| C1 | R1, R2 | `python checks/headcount.py` | the share in output/headcount.csv is not the share of the worked example |
| C2 | R4 | `python checks/table.py` | a named region has no row, or its share is not the share of the worked example |
| C3 | R3 | `python checks/inputs.py` | a household of the survey has no weight, or a negative welfare |

What no check would catch: a share computed on the wrong households.

### Boundaries

- Always: run the checks of the slice.
- Ask first: a new dependency.
- Never: print rows of the survey.

## Data register

| Dataset | Classification | Source | Version | Owner | Permitted use |
|---|---|---|---|---|---|
| data/survey.csv | Public | synthetic | 1 | the team | any |
| data/regions.csv | Public | synthetic | 1 | the team | any |

## Slices

| Slice | What it delivers | Files | Checks | By code or by judgement |
|---|---|---|---|---|
| S1 | the weighted headcount ratio of the whole survey, written to output/headcount.csv | pipeline.py, checks/headcount.py, checks/inputs.py | C1, C3 | by code: pipeline.py |
| S2 | the table by region, written to output/table.csv | pipeline.py, checks/table.py | C2 | by code: pipeline.py |

## Open questions

| ID | About | Question | Recommended answer, with its trade-off | The human's answer |
|---|---|---|---|---|
| none | none | none | none | none |
