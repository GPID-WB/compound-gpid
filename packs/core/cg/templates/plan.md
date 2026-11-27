---
type: plan
schema: 2
title: "{title}"
date: {date}
status: draft
intent: {intent}
---

# {heading}

The human approves this plan as it reads below. `cg.py approve` records their reply against this text, so a later change is an amendment, a dated line under `## Amendments`, and needs a new approval.

## Contract

### Goal

<what will be true when the work is done, in terms someone can measure>

### Out of scope

<what this work will not do, and what is deferred>

### Requirements

| ID | Requirement |
|---|---|
| R1 | <one thing the work must do> |

### Checks

Every requirement has a check, and every check can fail. A Command cell holds one command, written in full, in one pair of backticks: code runs it as it stands, and its exit code is the check's. The exit code of a pipe or of `;` is the last command's.

| ID | Requirement | Command | Fails when |
|---|---|---|---|
| C1 | R1 | <the command, as it will be run, in one pair of backticks> | <the outcome that means the requirement is not met> |

What no check would catch: <what could still be wrong while every check passes, or "nothing known">

### Boundaries

- Always: <what the agent does without asking>
- Ask first: <what needs the human's yes each time>
- Never: <what the agent does not do in this work>

## Data register

| Dataset | Classification | Source | Version | Owner | Permitted use |
|---|---|---|---|---|---|
| <path of a dataset the work reads or produces, or "none"> | <its classification, as recorded: the level on the `data` line of status> | <where it comes from> | <its version or date> | <who owns it> | <what the work may do with it> |

Shape of the data: <for each dataset, the unit of observation, the key and the columns that matter; for each estimate, the unit of observation, the weights and the population it covers; or "no dataset">

## Slices

| Slice | What it delivers | Files | Checks | By code or by judgement |
|---|---|---|---|---|
| S1 | <a small piece that ends in a check> | <the files it may touch> | C1 | <by code, with the tool that does it; or by judgement> |

## Open questions

What only the human can decide inside this plan, each put to them with a recommended answer. The answer is theirs, in their words. Where an answer is still to come, its place in the plan names the question's ID in brackets. A plan that asks nothing has one row that says "none" in each cell.

| ID | About | Question | Recommended answer, with its trade-off | The human's answer |
|---|---|---|---|---|
| Q1 | <the part of the plan it is about: a check ID, a boundary or a dataset> | <one choice inside the plan that only the human can make> | <the answer you recommend, and what it costs> | <the human's answer, in their words; "open" until they give it> |
