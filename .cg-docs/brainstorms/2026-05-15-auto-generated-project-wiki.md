---
date: 2026-05-15
title: "Auto-generated project wiki (created at /cg-setup, updated at /cg-compound)"
status: decided
scope: "Standard"
chosen-approach: "Dedicated Wiki Agent + Template System"
tags: [wiki, documentation, cg-setup, cg-compound, agent, templates]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Auto-Generated Project Wiki

## Context

The roadmap "Ongoing Ideas" milestone includes a feature: "Auto-generated project wiki (created at /cg-setup, updated at /cg-compound)." The goal is to create and continuously maintain a user-readable documentation wiki that serves as the canonical external-facing reference for any project using the plugin — distinct from `.cg-docs/` which is internal compound-gpid knowledge.

## Requirements

### Core Behavior
- **Initialization**: `/cg-setup` creates the wiki based on project charter, scanner results, and project type. Templates vary by type (R package → installation/API/vignettes; research paper → methodology/data/replication; tool → setup/usage/config).
- **Continuous update**: `/cg-compound` automatically updates the wiki whenever a captured solution has user-facing documentation implications.
- **Current-state truth**: The wiki reflects the current state of the repo. Outdated information is removed, not accumulated. Historical knowledge lives in `.cg-docs/`.

### Location and Format
- **Default folder**: `wiki/` (configurable in `compound-gpid.context.md`)
- **Structure**: `wiki/README.md` (landing page with TOC, auto-renders on GitHub), flat `wiki/*.md` pages, `wiki/_wiki.yml` manifest
- **GitHub Wiki conversion**: Structure designed for easy migration to GitHub Wiki (rename README→Home, generate _Sidebar from _wiki.yml)

### Ownership and Update Rules
- **Section markers**: Plugin-managed sections wrapped in `<!-- cg:auto:section-name -->` / `<!-- cg:auto:end -->`. Content outside markers is never touched.
- **Page-level ownership**: Pages are either `auto` (plugin manages entirely) or `manual` (plugin never touches). Tracked in `_wiki.yml`.
- **Hybrid**: Both section-level markers within auto pages AND whole-page manual ownership.

### Conflict Resolution
- **Plugin vs plugin (new info)**: New/improved information from `/cg-compound` replaces old plugin-authored content silently.
- **Plugin vs human**: If new information contradicts user-written content (outside markers or in manual pages), the plugin notifies the user rather than overwriting.

### Update Mode
- **Default**: Auto-generate (no confirmation for plugin-managed sections)
- **Flag**: `/cg-compound --propose-wiki` shows proposed changes before applying
- **Rebuild**: A dedicated command can rebuild pages from scratch (respecting manual ownership)

### Configuration
- Wiki structure customizable via a section in `compound-gpid.context.md` (preferred sections, tone, audience)
- Cross-linking between pages supported
- Table of contents in README.md

## Approaches Considered

### Approach 1: Dedicated Wiki Agent + Template System (CHOSEN)
A new `@cg-wiki` agent handles all wiki operations, invoked by `/cg-setup` (init) and `/cg-compound` (update). Project-type templates define the initial page structure.

**Pros**: Clean separation of concerns; agent has full context; templates extensible; dedicated `/cg-wiki` command for manual operations  
**Cons**: Requires new agent + skill + prompt + templates; moderate effort  
**Effort**: Medium

### Approach 2: Inline in Existing Prompts
Wiki logic embedded in `/cg-setup` and `/cg-compound` steps.

**Pros**: Simpler, fewer files  
**Cons**: Bloats large prompts; scattered logic; no independent rebuild command  
**Effort**: Small

### Approach 3: Script-Based Generator
Deterministic Python/PowerShell script generates wiki pages.

**Pros**: Testable, no LLM variability  
**Cons**: Can't synthesize prose intelligently; loses organic quality  
**Effort**: Medium-Large

## Decision

Approach 1 — full feature, not phased. A dedicated `@cg-wiki` agent with project-type templates, invoked from both `/cg-setup` and `/cg-compound`, plus a standalone `/cg-wiki` command for manual rebuilds and GitHub Wiki conversion.

## Next Steps

1. Design `_wiki.yml` schema (pages, order, ownership, section markers)
2. Create project-type wiki templates (R package, research paper, tool, analysis, dashboard, API)
3. Implement `@cg-wiki` agent (init mode, update mode, rebuild mode, convert mode)
4. Create `/cg-wiki` prompt (manual rebuild, restructure, publish to GitHub Wiki)
5. Add wiki scaffolding step to `/cg-setup` (Step A5.8)
6. Add wiki update step to `/cg-compound` (Step 3c)
7. Define wiki configuration schema for `compound-gpid.context.md`
8. Tests: Pester tests for manifest schema validation, ownership rules, section marker preservation
