---
date: 2026-05-06
title: "Implicit output template in agent spec — 'same as X but omit Y' causes non-deterministic rendering"
category: "testing-patterns"
language: "both"
tags: [agent-design, prompt-design, output-template, rendering, determinism, tasks-milestone, cg-roadmap-view]
root-cause: "Describing a view mode as 'Same as <other-view> but omit <fields>' requires the model to perform a mental subtraction from an implied template, creating ambiguity about what is and isn't included — especially for structural elements like headings."
severity: "P3"
fix-confirmed: "no"
reviewed-in: ".cg-docs/reviews/2026-05-06-roadmap-visualization-verify-review.md"
---

# Implicit Output Template in Agent Spec — "Same as X but omit Y" Causes Non-Determinism

## Problem

`cg-roadmap-view.agent.md` specifies the `tasks-milestone` view as:

> Same as `milestone` view but focused on the feature table only (omit
> objective and progress bar).

Every other view mode in the same agent has a **concrete Markdown code block**
showing exactly what the rendered output looks like. The `tasks-milestone` view
has only prose description.

This creates ambiguity: when "omitting" the objective and progress bar, is the
`## 🏁 <milestone-title>` heading also omitted? Or retained? Different model
invocations answer this differently, producing non-deterministic output across
sessions.

Identified as **V-P3.4** in the verify pass of the roadmap-visualization
feature (`2026-05-06-roadmap-visualization-verify-review.md`).

## Root Cause

Prose-based "same as X but subtract Y" specs force the model to:
1. Locate the template for view X in its context window.
2. Mentally enumerate what fields Y refers to.
3. Decide which structural elements (headings, separators) are "content"
   vs. "scaffolding" — a judgment call with no single right answer.

This is a reliable source of hallucinated or inconsistent output when:
- The base view (X) has structural elements (headings, sub-sections) that
  aren't obviously "fields."
- The subtracted elements (Y) are specified ambiguously ("objective section"
  could mean the `**Objective**:` line, or the entire H3 subsection, or a
  prose paragraph).

## Solution

Every view mode in an agent spec must have its **own concrete Markdown code
block** showing exactly what the output looks like for that mode, even if it
closely resembles another view.

**Wrong** (implicit via subtraction):
```markdown
### `tasks-milestone` view
Same as `milestone` view but focused on the feature table only
(omit objective and progress bar).
```

**Right** (explicit concrete template):
````markdown
### `tasks-milestone` view
Output exactly:
```markdown
## 🏁 <milestone-title>

| # | Title | Status | Branch |
|---|-------|--------|--------|
| 1 | <feature-title> | <badge> | <branch or "—"> |
```
Omit the objective block and progress bar. Include the milestone title heading.
````

The rule: **if you find yourself writing "same as X but ..."**, stop and write
the full template for the variant. Copy-paste from X, then explicitly delete
the omitted elements. The resulting spec is unambiguous and directly verifiable.

## Prevention

- **Agent review checklist**: For every output view/mode defined, verify a
  concrete Markdown example block is present — not just prose description.
- **Code review**: Flag any `Same as <view>` or `Like <mode>` language in agent
  output specs as requiring a concrete template.
- **Test coverage**: Pester tests can assert that view mode names are documented
  (`-match 'tasks-milestone'`), but cannot catch implicit templates. Only agent
  spec review catches this class of bug.

## Related

- [`2026-03-30-prompt-pipeline-contract-testing.md`](2026-03-30-prompt-pipeline-contract-testing.md) — general principle that agent output contracts must be explicit and testable
- [`2026-04-08-new-prompt-agent-addition-checklist.md`](2026-04-08-new-prompt-agent-addition-checklist.md) — checklist for new agent files; add "concrete template per view mode" as a required item
