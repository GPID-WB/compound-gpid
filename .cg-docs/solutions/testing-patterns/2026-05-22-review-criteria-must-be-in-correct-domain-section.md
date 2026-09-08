---
date: 2026-05-22
title: "Review criteria bullets must be placed in the domain section they belong to, not the adjacent section"
category: "testing-patterns"
language: "both"
tags: [agent-design, skill-design, review-criteria, section-placement, ggsave, figure-caption, table-note, cr-skill-publication-output, content-organization]
root-cause: "A ggsave() criterion was placed in the Section 6 (Table-Note Discipline) Review Criteria callout of cr-skill-publication-output, but ggsave() is a figure output function. It belongs in Section 5 (Figure-Caption Discipline). An agent delegating to Section 6 would receive a figure criterion inside a table-note checklist."
severity: "P1"
---

# Review Criteria Bullets Must Be Placed in the Domain Section They Belong To

## Problem

`cr-skill-publication-output/SKILL.md` was updated with Review Criteria callout
boxes in Sections 5 and 6 (for use by `@cr-academic-writing` Check 6 delegation).
During the update, the `ggsave()` criterion landed in Section 6 (Table-Note
Discipline):

```markdown
## 6. Table-Note Discipline

> **Review criteria** (for `@cr-academic-writing` Check 6):
> - Missing SE type sentence → flag
> - Missing significance level key (`* p < 0.10...`) → flag
> - Variable not defined in notes → flag
> - `ggsave()` called without explicit `width`, `height`, `units` → flag   ← WRONG
```

`ggsave()` is a **figure output function** — it belongs in Section 5 (Figure-Caption
Discipline). A reviewer applying Check 6 and reading Section 6 would encounter
a figure criterion inside a table-note checklist, causing:

1. Misclassified findings: `ggsave` issues flagged as table-note violations
2. Missed criteria: reviewers following Section 5 would not see the `ggsave` check
3. Confusion for humans reading the skill as a reference

## Root Cause

When multi-file edits add criteria to adjacent sections in quick succession, it
is easy to paste a criterion into the wrong `> **Review criteria**` callout block —
especially when both blocks are similar in structure and appear close together.
`ggsave()` was added during the same edit that created both callout boxes.

## Solution

Move the criterion to its domain section:

**Section 5 (Figure-Caption Discipline)**:
```markdown
> **Review criteria** (for `@cr-academic-writing` Check 6):
> - Caption missing the data source → flag
> - Caption not self-contained (requires body text to understand) → flag
> - Caption missing required elements (what is plotted, sample, key takeaway) → flag
> - `ggsave()` called without explicit `width`, `height`, `units` → flag   ← CORRECT
```

**Section 6 (Table-Note Discipline)**:
```markdown
> **Review criteria** (for `@cr-academic-writing` Check 6):
> - Missing SE type sentence → flag
> - Missing significance level key (`* p < 0.10...`) → flag
> - Variable not defined in notes → flag
> - Sample definition absent from notes → flag
> - Fixed effects not disclosed in notes (if applicable) → flag
```

## Prevention

**Rule**: Before adding a review criterion to any `> **Review criteria**` callout,
verify the **domain** of the function or artifact being checked:

- Is this a figure output function (ggplot2, ggsave, figure captions)? → Section 5
- Is this a table annotation function (modelsummary notes, kableExtra footnotes, table variables)? → Section 6
- Ask: "Would a table reviewer checking note completeness care about this?" If no, it does not belong in Section 6.

**Verification step**: After any multi-section edit, read each criteria callout
in isolation and ask "Does every bullet in this box belong to the section
heading above it?"

## Related

- `.cg-docs/solutions/testing-patterns/2026-05-22-multi-task-type-agent-needs-execution-mode-guard.md` — found in the same review session; both are agent/skill design discipline issues.
