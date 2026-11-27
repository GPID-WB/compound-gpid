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

The brief gives a table of the weighted headcount ratio by region, beside the ratio of the whole survey.

### Out of scope

Other poverty measures, other surveys, and any change to the ratio of the whole survey.

### Requirements

| ID | Requirement |
|---|---|
| R1 | The table gives the weighted headcount ratio of each region of the survey |
| R2 | The ratio of the whole survey is as it was |

### Checks

| ID | Requirement | Command | Fails when |
|---|---|---|---|
| C1 | R1 | `python checks/table.py` | a region has no row, or its share is not the share of the worked example |
| C2 | R2 | `python checks/headcount.py` | the ratio of the whole survey is not the one the brief gave before |

What no check would catch: a region with too few households for its share to mean much.

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
| S1 | the table by region, written to output/table.csv | pipeline.py, checks/table.py | C1 | by code: pipeline.py |
| S2 | an option to scale the shares of the table, for a use later on | pipeline.py | C1 | by code: pipeline.py |
| S3 | a check in the table's function that the poverty line is not negative | pipeline.py | C1 | by code: pipeline.py |
| S4 | the check of the ratio of the whole survey laid out again, as the new check is | checks/headcount.py | C2 | by code: checks/headcount.py |

## Open questions

| ID | About | Question | Recommended answer, with its trade-off | The human's answer |
|---|---|---|---|---|
| none | none | none | none | none |
