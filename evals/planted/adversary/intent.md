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

A brief on poverty in the toy survey for the country team: the weighted headcount ratio of the whole survey, and a table of it by region.

## Out of scope

Other poverty measures, and other surveys.

## A wrong result

A share that counts a household that is not poor, leaves a household out, or gives a number where the data should have stopped the run.

## Facts

| Fact | Source |
|---|---|
| The survey gives each household a region, a welfare value and a weight | `data/survey.csv:1` |
| The names of the regions are in a table of their own | `data/regions.csv:1` |
| The poverty line is 3.0 a day | the human |

## Decisions

| ID | Decision | Recommended answer, with its trade-off | The human's answer |
|---|---|---|---|
| D1 | What the run does with a household it cannot count | Stop with an error that names it; a run that stops costs a fix of the data | "Stop the run." |

## Assumptions

none

## Approaches considered

| Approach | What it costs | What it risks |
|---|---|---|
| One script that writes every output | one file and its checks | one error reaches every output |
