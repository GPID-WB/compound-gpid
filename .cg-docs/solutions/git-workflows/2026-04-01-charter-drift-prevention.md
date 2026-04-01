---
date: 2026-04-01
title: "Charter drift prevention: four-section rule + archive-on-removal + staleness nudge"
category: "git-workflows"
language: "both"
tags: [charter, compound-gpid.md, staleness, archive, cg-resume, structural-rule, drift, last-reviewed, frontmatter]
root-cause: "No structural constraint, staleness signal, or archive mechanism existed for compound-gpid.md, so content accumulated, became unfocused, and went unreviewed."
severity: "P2"
---

# Charter Drift Prevention

## Problem

`compound-gpid.md` is read at the start of every Copilot session via "Step 0:
Get Bearings" — it is the shared source of truth for project context, constraints,
and current focus. Without any maintenance mechanism, it drifts in predictable ways:

- **Section sprawl**: Architecture notes, roadmap items, historical decisions, and
  meeting summaries accumulate in whatever section is nearby, making the charter
  increasingly long and unfocused.
- **Stale focus**: The "Current Focus" section stops being updated when no prompt
  enforces it, so Copilot operates on outdated priorities session after session.
- **Deleted history**: When content is removed to keep the charter lean, it is
  simply deleted — no institutional trace remains.
- **No structural invariant**: Without a tested constraint, reviewers and prompts
  cannot programmatically verify charter health.

## Root Cause

The charter was treated as a living free-form document with no conventions beyond
what `/cg-setup` seeded. The original template included six sections (Objective,
Key Deliverables, Constraints, Architecture Notes, Current Focus, Roadmap,
Related Resources) with no enforcement — content migrated between sections
arbitrarily, sections were added informally, and no machine-readable signal existed
to indicate when the charter had last been reviewed.

## Solution

Three complementary mechanisms were implemented (Approach C):

### 1. Four-Section Structural Rule

`compound-gpid.md` contains exactly these four sections — no more, no fewer:

| Section | Purpose |
|---|---|
| `## Objective` | 1–3 sentences. What is this project? Who is it for? |
| `## Key Deliverables` | Bulleted list of concrete outputs. |
| `## Constraints` | Hard rules Copilot must always respect. |
| `## Current Focus` | What the team is working on RIGHT NOW. 1–2 sentences. Update frequently. |

Content that doesn't fit these four categories goes elsewhere:
- Architecture notes → `copilot-instructions.md` or a skill file
- Historical decisions → `.cg-docs/brainstorms/`
- Removed charter content → `.cg-docs/archive/charter-history.md`
- Roadmap / milestones → `roadmap.json`

The rule is enforced with Pester tests (`tests/charter.Tests.ps1`):

```powershell
# Count all level-2 headings in the body
$sectionCount = @($body -split '\r?\n' | Where-Object { $_ -match '^##\s+\S' }).Count
$sectionCount | Should Be 4

# Deprecated sections must not appear
($body -match '(?m)^## Architecture Notes') | Should Be $false
($body -match '(?m)^## Roadmap')            | Should Be $false
($body -match '(?m)^## Related Resources')  | Should Be $false
```

### 2. `last-reviewed` Frontmatter + Staleness Nudge

The charter YAML frontmatter gains a `last-reviewed` field:

```yaml
---
project-name: "<name>"
created: "YYYY-MM-DD"
last-reviewed: "YYYY-MM-DD"
---
```

`/cg-resume` step 2f checks this field at session start and surfaces a nudge
if more than 30 days have elapsed without a review:

```markdown
# Step 2f — Charter Staleness Check
Read the `last-reviewed` field from `compound-gpid.md`. If today's date is
more than 30 days beyond that value, surface a warning:

  > **Charter may be stale** — last reviewed <date> (<N> days ago).
  > Before resuming, consider whether `compound-gpid.md` still reflects
  > current project priorities. Update the `last-reviewed` date after any
  > meaningful review.

Do not block work — this is a nudge, not a hard stop.
```

The `last-reviewed` date is the only frontmatter field that may be
auto-updated by prompts without explicit user approval of the body content.

Tests validate format and guard against future dates:

```powershell
It "last-reviewed is a valid YYYY-MM-DD date" {
    $match = [regex]::Match($yamlBlock, 'last-reviewed\s*:\s*["''"]?(\d{4}-\d{2}-\d{2})["''"]?')
    $match.Success | Should Be $true
}

It "last-reviewed is not set to a future date" {
    ($dateValue -le (Get-Date -Format 'yyyy-MM-dd')) | Should Be $true
}
```

### 3. Archive-on-Removal

When content is removed from `compound-gpid.md`, it is appended to
`.cg-docs/archive/charter-history.md` with a datestamp rather than deleted.
This protects historical decisions while keeping the charter lean:

```markdown
<!-- archived 2026-04-01 — removed from ## Constraints -->
- Architecture notes go in skill files or copilot-instructions.md, not the charter.
```

The archive directory is scaffolded with a `.gitkeep` so git tracks it from setup,
and tests verify it exists:

```powershell
Describe ".cg-docs/archive/ - scaffold present" {
    It ".cg-docs/archive/ directory exists" { ... }
    It ".cg-docs/archive/ is tracked via .gitkeep" { ... }
}
```

## Prevention

Apply the same three-mechanism pattern to any shared committed document that
multiple AI sessions will read:

1. **Structural rule** — define allowed sections; test with regex section-count assertions
2. **`last-reviewed` frontmatter** — add to any document that should be reviewed periodically; check in the session-resume prompt
3. **Archive-on-removal** — never hard-delete content from shared docs; append to a dated archive file

For the charter specifically: the "Do not modify" rule for AI prompts applies to
the **body content** only. The `last-reviewed` frontmatter field may be updated
automatically when a review is confirmed.

## Related

- [testing-patterns/2026-03-30-do-not-delegate-file-write-guardrail.md](../testing-patterns/2026-03-30-do-not-delegate-file-write-guardrail.md) — pattern for protecting files from unintended AI writes
- [git-workflows/2026-03-23-cg-docs-must-not-be-gitignored.md](./2026-03-23-cg-docs-must-not-be-gitignored.md) — archive/ and .cg-docs/ directories must be committed, not gitignored
