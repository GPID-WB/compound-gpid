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

The brief gives a table of the weighted headcount ratio of the toy survey by region, and its ratio of the whole survey stays as it was.

### Out of scope

Other poverty measures, and other surveys.

### Requirements

| ID | Requirement |
|---|---|
| R1 | The ratio of the whole survey is as it was |
| R2 | The table has a row for each region of the survey, with its weighted share of the households below the line |

### Checks

| ID | Requirement | Command | Fails when |
|---|---|---|---|
| C1 | R1 | `python checks/headcount.py` | the share in output/headcount.csv is not the share of the worked example |
| C2 | R2 | `python checks/table.py` | a region has no row, or its share is not the share of the worked example |

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
| S1 | the table by region, written to output/table.csv, beside the ratio of the whole survey | pipeline.py, checks/table.py, README.md | C1, C2 | by code: pipeline.py |

## Open questions

| ID | About | Question | Recommended answer, with its trade-off | The human's answer |
|---|---|---|---|---|
| none | none | none | none | none |
