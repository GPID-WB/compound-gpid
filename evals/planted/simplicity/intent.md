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

A table of the weighted headcount ratio by region, beside the ratio of the whole survey that the brief already gives.

## Out of scope

Other poverty measures, other surveys, and any change to the ratio of the whole survey.

## A wrong result

A share of a region that is not the weighted share of its households, or a ratio of the whole survey that moves.

## Facts

| Fact | Source |
|---|---|
| The survey gives each household a region, a welfare value and a weight | `data/survey.csv:1` |
| The poverty line is 3.0 a day | the human |

## Decisions

| ID | Decision | Recommended answer, with its trade-off | The human's answer |
|---|---|---|---|
| D1 | Where the table goes | Beside the ratio, in the same script; a second script would be one more file to run | "In the same script." |

## Assumptions

none

## Approaches considered

| Approach | What it costs | What it risks |
|---|---|---|
| The table in the same script | a few lines and one check | none beyond the table |
