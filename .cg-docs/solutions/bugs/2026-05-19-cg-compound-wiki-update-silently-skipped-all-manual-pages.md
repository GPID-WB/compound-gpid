---
date: 2026-05-19
title: "/cg-compound wiki update silently skipped — all docs/_wiki.yml pages were manual-ownership"
category: "bugs"
type: "bug"
language: "n/a"
tags: [cg-compound, cg-wiki, wiki, ownership, manual, auto, reference, docs, notifications]
root-cause: "docs/_wiki.yml registered all 9 pages as ownership: manual, so @cg-wiki could never write to any page; compounded by /cg-compound Step 3c having no instruction to surface the resulting manual-update notifications to the user"
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
---

# `/cg-compound` Wiki Update Silently Skipped — All `docs/_wiki.yml` Pages Were Manual-Ownership

## Symptom

Running `/cg-compound` after a feature that added new command flags and changed
user-visible behavior (e.g., `command-default-behaviors` — new `--no-branch`,
`--no-phases`, `--report-only`, `--no-enrich` flags) produced no wiki updates and
no notifications. `docs/reference.md` was never updated to reflect the new flags,
and the user received no indication that any docs page needed attention.

## Root Cause

Two compounding issues:

**1. `docs/_wiki.yml` — all 9 pages `ownership: "manual"`**

Per the wiki skill's ownership rules, `manual` pages are **never written** by the
plugin — the agent can only produce a "Relevant update — update it manually"
notification. When `/cg-compound` dispatched `@cg-wiki update` after trigger
criteria fired (criterion #2: added CLI flags), the wiki agent found all pages
were `manual` and produced notifications internally — but nothing was written.

**2. `/cg-compound` Step 3c — manual-page notifications swallowed**

The report step in Step 3c only covered successful writes (`"Wiki updated:
wiki/<page>.md"`). There was no instruction to echo the wiki agent's "update
manually" notifications back to the user. So even the notification path was
silently discarded.

The combined effect: trigger criteria fired → `@cg-wiki` dispatched → all pages
found to be `manual` → notifications generated but swallowed → user sees silence.

## Reproduction Test

Added to `tests/wiki.Tests.ps1`:

```powershell
Describe "docs/_wiki.yml - reference.md is auto-ownership for command-reference updates" {
    It "docs/_wiki.yml has at least one auto-ownership page" { ... }
    It "reference.md entry has ownership: auto" { ... }
}

Describe "docs/reference.md - contains cg:auto section markers for plugin-managed content" {
    It "docs/reference.md contains at least one cg:auto opening marker" { ... }
    It "docs/reference.md contains cg:auto:end closing marker" { ... }
}

Describe "cg-compound.prompt.md - Step 3c surfaces manual-page notifications to user" {
    It "Step 3c instructs agent to notify user when relevant pages are manual-ownership" { ... }
}
```

All 5 assertions failed before the fix.

## Fix

### 1. `docs/_wiki.yml` — change `reference.md` to `ownership: "auto"`

```yaml
- id: "reference"
  file: "reference.md"
  title: "Reference"
  ownership: "auto"
  order: 3
  sections:
    - id: "commands"
      managed: true
```

`reference.md` is the canonical command reference — it tracks all `/cg-*` prompt
flags and descriptions. It is the page most likely to need updates when `/cg-compound`
captures a solution involving new CLI flags. Making it `auto` allows `@cg-wiki` to
rewrite the `commands` section automatically.

### 2. `docs/reference.md` — add `cg:auto:commands` section markers

Wrapped the main commands table (`## Copilot Chat Prompts`) in markers:

```markdown
<!-- cg:auto:commands -->
| Prompt | Model | Purpose |
...
| `/cg-verify-pr [--propose]` | ... |
<!-- cg:auto:end -->
```

The `### Plugin Development` subsection and prose notes (`> **Model selection**:` etc.)
are outside the markers and remain user-owned — the plugin never touches them.

### 3. `cg-compound.prompt.md` Step 3c — surface manual-page notifications

Replaced the single `4. Report: "Wiki updated"` step with two steps:

```markdown
4. After the dispatch, surface any **manual-ownership notifications** from `@cg-wiki`
   to the user verbatim — do not swallow them silently:
   > "Relevant update for `<folder>/<page>.md` — this page is `manual` ownership.
   > Update it manually."
5. Report: "Wiki updated: <folder>/<page>.md — <brief description of change>."
   (Only for `auto` pages where `@cg-wiki` actually wrote content.)
```

## Lessons Learned

**`manual` ownership means "never touch" — including notifications**: When a project
initializes its wiki from hand-authored docs, every page defaults to `manual`. This is
correct for protecting prose, but the command reference page that tracks CLI flags is
exactly the content the plugin should own. Review ownership settings after `init` and
move command/API reference pages to `auto` with section markers.

**Agent dispatch results must be surfaced explicitly**: When a prompt dispatches a
subagent and the subagent produces notifications rather than writes (e.g., because all
pages are `manual`), those notifications will be silently discarded unless the parent
prompt explicitly says "echo any notifications from the subagent to the user." Never
assume subagent output automatically flows to the user.

**Pattern for new projects**: After running `/cg-wiki init`, check `_wiki.yml` and
set the command/API reference page to `ownership: "auto"` with an appropriate section
ID, then add `<!-- cg:auto:<id> -->` / `<!-- cg:auto:end -->` markers to that page.

## Related

- [2026-05-18-compound-gpid-repo-not-wired-as-wiki-consumer.md](2026-05-18-compound-gpid-repo-not-wired-as-wiki-consumer.md) — prior bug: the wiki folder was not configured at all. This bug is the follow-on: folder was configured, but all pages were `manual`.
