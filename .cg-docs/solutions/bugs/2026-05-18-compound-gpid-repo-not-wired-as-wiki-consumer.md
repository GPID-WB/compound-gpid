---
date: 2026-05-18
title: "compound-gpid repo not wired as its own wiki consumer — docs/ folder ignored by /cg-wiki and /cg-compound"
category: "bugs"
type: "bug"
language: "both"
tags: [cg-wiki, cg-compound, wiki-configuration, context-md, docs, bootstrap, self-referential]
root-cause: "compound-gpid.context.md had no ## Wiki Configuration section, so /cg-wiki and /cg-compound defaulted to a non-existent wiki/ folder, silently skipping the docs/ folder that already served as the project's user-facing documentation"
severity: "P3"
test-written: "yes"
fix-confirmed: "yes"
---

# compound-gpid Repo Not Wired as Its Own Wiki Consumer

## Symptom

Running `/cg-wiki` or `/cg-compound` (after a user-facing change) in the
compound-gpid repo either reported "no manifest found" or silently skipped
the wiki update step — even though `docs/` contains 9 hand-authored
documentation pages that serve as the project's canonical user reference.

`/cg-wiki init` would have bootstrapped a `wiki/` folder that didn't exist
and wasn't wanted. `docs/` was never touched by the wiki system.

## Root Cause

The wiki feature was built as infrastructure for *consumer projects* (projects
that use the Compound GPID plugin). When implementing the feature, the plugin
repo itself was never configured as a consumer. `compound-gpid.context.md` had
no `## Wiki Configuration` section, so all wiki-aware prompts defaulted to
`folder: wiki` — a folder that doesn't exist in this repo.

The pre-existing `docs/` folder, which plays the exact role the wiki system was
designed for, was invisible to `/cg-wiki` and `/cg-compound`. Additionally,
`docs/workflow.md` had no mention of `/cg-wiki` at all, making the feature
undiscoverable from the main workflow reference.

## Reproduction Test

Added to `tests/wiki.Tests.ps1`:

```powershell
Describe "compound-gpid.context.md - wiki configuration for this repo" {
    It "has a ## Wiki Configuration section" { ... }
    It "declares docs/ as the wiki folder" { ... }
}

Describe "docs/_wiki.yml - manifest exists for docs/ folder" {
    It "docs/_wiki.yml exists (wiki initialized against docs/)" { ... }
}

Describe "docs/workflow.md - /cg-wiki is documented in the workflow loop" {
    It "mentions /cg-wiki in the workflow" { ... }
}
```

All 4 assertions failed before the fix.

## Fix

### 1. `compound-gpid.context.md` — add `## Wiki Configuration`

```markdown
## Wiki Configuration

<!-- folder: docs -->
<!-- audience: plugin users (developers integrating Compound GPID into their projects) -->
<!-- tone: technical, concise -->
```

This points all wiki-aware prompts (`/cg-wiki`, `/cg-compound`) at `docs/`
instead of the default `wiki/`.

### 2. `docs/_wiki.yml` — created manifest

Created `docs/_wiki.yml` with all 9 existing pages registered as
`ownership: "manual"` — the plugin will never auto-overwrite hand-authored
content. `schemaVersion: "compound-gpid-wiki-v1"`, `lastUpdated: "2026-05-18"`.

### 3. `docs/workflow.md` — added `/cg-wiki` section

- Updated the workflow loop diagram to include `Wiki` after `Compound`
- Added a new `### 6b. Wiki (/cg-wiki)` section documenting all subcommands,
  when to use them, and how they integrate with `/cg-compound`
- Renumbered former `6b. Compound Refresh` to `6c`

## Lessons Learned

**The builder of a tool must also configure it for their own project.** When
building infrastructure for consumer projects, it is easy to overlook
self-application — especially when the builder's project already has an
equivalent artifact (`docs/`) that predates the new feature.

**Pattern**: after implementing any feature that requires project-level
configuration (`## Wiki Configuration`, `roadmap.json`, etc.), immediately
check if the compound-gpid repo itself needs to be configured as a consumer.
Add a Pester test that asserts the configuration exists — this makes the gap
immediately visible rather than silently wrong.

**`manual` ownership is the safe default for existing content.** When
bootstrapping a wiki against pages that already exist and are hand-authored,
register them all as `manual`. This gives the wiki system awareness of the
pages without any risk of overwriting content. Ownership can be changed to
`auto` selectively later.

## Related

- [2026-05-15-cg-wiki-no-user-facing-init-path-for-existing-projects.md](2026-05-15-cg-wiki-no-user-facing-init-path-for-existing-projects.md) — the prior bug that added `/cg-wiki init`; this bug is the natural follow-on (now that `init` exists, the repo needed to be configured to use it)
