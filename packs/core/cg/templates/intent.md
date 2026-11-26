---
type: intent
schema: 2
title: "{title}"
date: {date}
status: draft
---

# {heading}

The human confirms this intent as it reads below. `cg.py approve` records their reply against this text, so a later change to it needs a new yes.

## Goal

<what the human wants, in plain words, and who will read or use the output>

## Out of scope

<what this work will not do>

## A wrong result

<what an incorrect output would look like, and what would tell it apart from a correct one>

## Facts

What was looked up, each with where it was found.

| Fact | Source |
|---|---|
| <one thing that is true of the project, the method or the data> | <the file and line, the command, or the documentation that shows it; "the human" only for what they alone know> |

## Decisions

Each one was put to the human. The answer is theirs, and the recommended answer is never written in its place.

| ID | Decision | Recommended answer, with its trade-off | The human's answer |
|---|---|---|---|
| D1 | <one choice that changes the method, the scope, the risk or the output> | <the answer you recommend, and what it costs> | <the human's answer, in their words; "open" until they give it> |

## Assumptions

<each thing taken as true that was neither looked up nor decided, with what changes if it is wrong; or "none">

## Approaches considered

| Approach | What it costs | What it risks |
|---|---|---|
| <one way to reach the goal, in a line or two; the one the human chose is a row under Decisions> | <the work and the dependencies it needs> | <what could go wrong with it> |
