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

The poverty brief of the toy survey gains a table of the weighted headcount ratio by region, for the country team.

## Out of scope

Other poverty measures, and other surveys.

## A wrong result

A table that leaves out a region, or a brief that says more than its numbers show.

## Facts

| Fact | Source |
|---|---|
| The survey gives each household a region, a welfare value and a weight | `data/survey.csv:1` |
| The poverty line is 3.0 a day | the human |

## Decisions

| ID | Decision | Recommended answer, with its trade-off | The human's answer |
|---|---|---|---|
| D1 | Whether the ratio of the whole survey may move | It stays as it is, held by its check; a change to it would need its own plan | "It stays." |

## Assumptions

none

## Approaches considered

| Approach | What it costs | What it risks |
|---|---|---|
| The table in the script that writes the ratio | one file and one check | one error reaches both outputs |
