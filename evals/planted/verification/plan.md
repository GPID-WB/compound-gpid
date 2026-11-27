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

The brief gives the weighted headcount ratio of the toy survey, a table of it by region, and a bootstrap interval for it.

### Out of scope

Other poverty measures, and other surveys.

### Requirements

| ID | Requirement |
|---|---|
| R1 | The headcount ratio uses the household weights |
| R2 | The table has a share for each region of the survey |
| R3 | The brief gives a bootstrap interval of the headcount ratio |

### Checks

| ID | Requirement | Command | Fails when |
|---|---|---|---|
| C1 | R1 | `python checks/headcount.py` | the share in output/headcount.csv is not the weighted share of the survey |
| C2 | R2 | `python -c "import os; assert os.path.exists('output/table.csv')"` | the table by region is not written |
| C3 | R3 | `python checks/interval.py | sort` | the interval has no width |
| C4 | R2 | `python checks/regions.py` | a region of the survey has no row in the table |
| C5 | R2 | `python checks/bounds.py` | a share of the table lies outside 0 and 1 |

What no check would catch: a share computed on the wrong households.

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
| S2 | the table by region, written to output/table.csv | pipeline.py, checks/regions.py, checks/bounds.py | C2, C4, C5 | by code: pipeline.py |
| S3 | the bootstrap interval, written to output/ci.csv, and a region with fewer than three households left out of the table | pipeline.py, checks/interval.py | C3 | by code: pipeline.py |

## Open questions

| ID | About | Question | Recommended answer, with its trade-off | The human's answer |
|---|---|---|---|---|
| none | none | none | none | none |
