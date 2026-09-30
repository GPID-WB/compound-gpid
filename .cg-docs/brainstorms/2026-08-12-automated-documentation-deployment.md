---
date: 2026-08-12
title: "Automated Documentation Deployment and What's New Page"
status: decided
scope: "Deep"
artifact-schema-version: 1
chosen-approach: "Approach 3: Scripts-first with separate doc-rebuild workflow"
tags: [documentation, ci-cd, github-actions, whats-new, wiki-rebuild, pages]
---

# Automated Documentation Deployment and What's New Page

## Context

The Compound GPID documentation site (https://gpid-wb.github.io/compound-gpid/) is deployed via GitHub Actions from `docs/` on pushes to `main`, but there is no automation that keeps documentation current when code changes. Today, `/cg-wiki rebuild` and manual edits to `docs/` Markdown files are the only way to update the site content. Features land in code, releases get tagged, and the docs lag behind.

There is also no mechanism to surface release-level changelog content on the public site. Release notes exist only in GitHub Releases and the ephemeral `RELEASE_NOTES.md` file.

Dual-deployment of the `dev` branch under `/dev/` was considered but deferred as independently scoped.

## Requirements

| Area | Decision |
|------|----------|
| Audience | "What's New" for all users (internal and external); `/dev/` preview deferred |
| Trigger for wiki rebuild | Bot commit to `main` on merge when doc-related files change (.github/prompts/, .github/skills/, .github/agents/, docs/) |
| "What's New" content source | Structured `releases/*.json` payloads written by `/cg-release`, aggregated at deploy time |
| No-op handling | Skip bot commit if wiki rebuild produces no diff (docs already current) |
| Wiki timing | CI rebuild on merge to `main`; `/cg-release` writes release payload only, does not rebuild wiki |
| Bot commit exception | Automated doc rebuilds from reviewed canonical sources are exempt from feature-branch review — they are mechanical renders of canonical data |

## Approaches Considered

### Approach 1: Extend pages.yml (single workflow, all logic inline)

Extend the existing `pages.yml` with wiki-rebuild and What's New generation as pre-deploy steps inside the same workflow.

- **Pros**: One workflow to maintain; all CI logic in one file; no coordination between workflows.
- **Cons**: pages.yml grows significantly; wiki-rebuild job needs `contents: write` permission on the deploy workflow; intertwined merge and release paths.
- **Effort**: Medium
- **Recommended?**: No — conflates rebuild and deploy concerns.

### Approach 2: Separate workflows (dedicated rebuild + deploy)

New `doc-rebuild.yml` handles wiki rebuild + bot commit on merge to `main`. pages.yml extended with release-tag trigger and What's New generation. Deployment logic stays clean.

- **Pros**: Clean separation of permissions; wiki rebuild can fail independently without blocking deploy; independently testable.
- **Cons**: Two workflow files; merge flow triggers chained workflow runs (visible across two logs).
- **Effort**: Medium
- **Recommended?**: Yes — cleanest separation for this project's CI patterns.

### Approach 3: Scripts-first (thin workflows, logic in Node.js)

Add `scripts/rebuild-docs.js` and `scripts/generate-whats-new.js` as authoritative logic. Workflows call scripts. Matches existing `check-docs-site.js` pattern.

- **Pros**: Logic in Node.js — testable locally, lintable. Workflows stay thin. Future changes to generation logic don't require CI YAML edits. Dry-runnable (`--check`, `--dry-run`). Matches existing project patterns.
- **Cons**: Two new scripts plus tests. Upfront work for script scaffolding.
- **Effort**: Medium-Large
- **Recommended?**: Yes — best long-term maintainability.

## Decision

**Approach 3: Scripts-first with separate doc-rebuild workflow.**

Two new Node.js scripts (`scripts/rebuild-docs.js`, `scripts/generate-whats-new.js`) with local test coverage. A new `doc-rebuild.yml` workflow triggers on push to `main` with doc-file path filters, runs `rebuild-docs.js`, and bot-commits changes back to `main`. pages.yml gains a release-tag trigger and calls `generate-whats-new.js` before validation and deployment.

The wiki rebuild for auto-managed sections (`managed: true` in `_wiki.yml`) is deterministic — it scans canonical source directories (`.github/prompts/`, `.github/skills/`, `.github/agents/`) and renders structured Markdown tables. No AI judgment required for these sections, so a Node.js script produces identical output.

Key design properties:
- **Idempotent**: Running the rebuild twice on the same source produces byte-identical output.
- **Validated**: `check-docs-site.js` validates navigation coverage, link integrity, and skills catalog in the same CI pipeline.
- **Self-healing**: If any edge case produces bad output, the next merge to `main` re-runs the rebuild and fixes it.
- **Dry-runnable**: `node scripts/rebuild-docs.js --check` for local diff without committing.

Bot-commit exception documented in `compound-gpid.md`:
> "Bot commits to `main` for automated documentation rebuilds from reviewed canonical sources are exempt from feature-branch review. All bot commits are idempotent renders of canonical data."

## Next Steps

1. Create `scripts/rebuild-docs.js` — wiki rebuild for auto-managed sections in `docs/`
2. Create `scripts/generate-whats-new.js` — aggregate `releases/*.json` into `docs/whats-new.md`
3. Add `docs/whats-new.md` page with `ownership: auto` in `_wiki.yml`
4. Add "What's New" entry to `docs/navigation.json`
5. Create `.github/workflows/doc-rebuild.yml` — triggered on push to `main` with doc-file path filter
6. Extend `.github/workflows/pages.yml` with release-tag trigger and What's New generation step
7. Extend `/cg-release` to write structured `releases/latest.json` payload
8. Add `check-docs-site.js` validation for the new What's New page
9. Add Pester/Node test coverage for new scripts and workflow contracts
10. Document bot-commit exception in `compound-gpid.md` Constraints section