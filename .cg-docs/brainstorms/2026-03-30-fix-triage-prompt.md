---
date: 2026-03-30
title: "Add /cg-fix-triage prompt for selective review fix application"
status: decided
chosen-approach: "Compound finding IDs with priority-level and individual selection"
tags: [workflow, review, prompts]
---

# Add `/cg-fix-triage` Prompt

## Context

`/cg-review` already saves review reports to `.cg-docs/reviews/` (Step 3.5) and references a `/cg-fix` command that users can invoke in future sessions. However, the actual prompt file never existed. The user wants a prompt that lets them selectively apply review findings — either all at once, by priority level, or by individual finding ID.

## Requirements

- Review reports must include unique, stable finding IDs
- Users need to fix findings in a different session from the review
- Must support: fix all, fix by priority level (P1, P2, P3), fix individual findings
- The naming should be `/cg-fix-triage` (not `/cg-fix`)
- Review reports already live in `.cg-docs/reviews/` with `-review` suffix (existing convention kept)

## Approaches Considered

### Approach 1: Flat Sequential Numbering

Findings get IDs like `#1`, `#2`, `#3` across all priorities. User runs `/cg-fix-triage 1 3`.

**Pros**: Simple, no ambiguity.
**Cons**: Loses priority context in the ID. No way to say "fix all criticals." Numbers shift if report is regenerated.

### Approach 2: Compound Finding IDs (chosen)

Findings get compound IDs: `P1.1`, `P1.2`, `P2.1`, `P3.1`. Users can filter by priority level (`P1`) or by specific ID (`P1.2`).

**Pros**: Natural extension of existing P1/P2/P3 system. Supports both "fix all criticals" and "fix this specific finding." IDs are stable within a priority level.
**Cons**: Slightly more complex argument parsing. IDs are longer.

### Approach 3: Tagged Flat List

Findings get flat IDs (`F1`, `F2`) but are tagged with priority. User can filter by tag or by ID.

**Pros**: Short IDs. Flexible.
**Cons**: Introduces a new `F` prefix that doesn't exist in the system. Breaks the P1/P2/P3 mental model.

## Decision

Approach 2: Compound finding IDs. The `P1.1` format is a natural extension of the existing priority system and supports both broad (priority-level) and precise (individual finding) selection without ambiguity.

## Next Steps

- [x] Update `cg-review.prompt.md` report format to use compound IDs
- [x] Update `cg-review.prompt.md` to reference `/cg-fix-triage`
- [x] Create `cg-fix-triage.prompt.md`
- [x] Update `docs/reference.md`, `docs/workflow.md`, `cg-setup.prompt.md`, `compound-gpid.md`
