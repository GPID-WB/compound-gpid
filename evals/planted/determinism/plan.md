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

The brief gives the weighted headcount ratio of the toy survey, a 95 percent bootstrap interval for it, and a table of the headcount ratio by region.

### Out of scope

Other poverty measures, and other surveys.

### Requirements

| ID | Requirement |
|---|---|
| R1 | The headcount ratio uses the household weights |
| R2 | The brief gives a 95 percent bootstrap interval |
| R3 | The brief has a table of the headcount ratio by region |

### Checks

| ID | Requirement | Command | Fails when |
|---|---|---|---|
| C1 | R1 | `python -c "import csv; assert abs(float(list(csv.DictReader(open('output/headcount.csv')))[0]['headcount']) - 44 / 127) < 1e-6"` | the share differs from 44/127 by more than 1e-6 |
| C2 | R2 | `python -c "import csv; row = list(csv.DictReader(open('output/ci.csv')))[0]; assert float(row['low']) < float(row['high'])"` | the interval has no width |
| C3 | R3 | `python -c "import csv; assert len(list(csv.reader(open('output/table.csv')))) == 5"` | the table does not have a header and four regions |

What no check would catch: a regional share typed with a wrong digit.

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
| S1 | the weighted headcount ratio, written to output/headcount.csv | pipeline.py | C1 | by code: pipeline.py |
| S2 | the bootstrap interval, from 500 draws of the households, written to output/ci.csv | pipeline.py | C2 | by code: pipeline.py |
| S3 | the table by region: the agent reads each regional share off the console and types it into output/table.csv and into report.qmd | output/table.csv, report.qmd | C3 | by judgement |
| S4 | the brief: the analyst copies the interval from output/ci.csv into brief.docx and saves it under today's date | brief.docx | C2 | by judgement |

## Open questions

| ID | About | Question | Recommended answer, with its trade-off | The human's answer |
|---|---|---|---|---|
| none | none | none | none | none |
