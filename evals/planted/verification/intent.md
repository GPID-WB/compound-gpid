---
type: intent
schema: 2
title: "Poverty brief"
date: 2026-11-27
status: draft
---

# Poverty brief

The human confirms this intent as it reads below. `cg.py approve` records their reply against this text, so a later change to it needs a new yes.

## Goal

A brief on poverty in the toy survey for the country team: the weighted headcount ratio, a table of it by region, and a bootstrap interval for it.

## Out of scope

Other poverty measures, and other surveys.

## A wrong result

A share that leaves out households, or a table that leaves out a region, with nothing in the brief that says so.

## Facts

| Fact | Source |
|---|---|
| The survey gives each household a region, a welfare value and a weight | `data/survey.csv:1` |
| The poverty line is 3.0 a day | the human |

## Decisions

| ID | Decision | Recommended answer, with its trade-off | The human's answer |
|---|---|---|---|
| D1 | How the interval is computed | A bootstrap of the households, 200 draws; more draws cost more time | "The bootstrap, 200 draws." |

## Assumptions

none

## Approaches considered

| Approach | What it costs | What it risks |
|---|---|---|
| One script that writes every output | one file and its checks | one error reaches every output |
