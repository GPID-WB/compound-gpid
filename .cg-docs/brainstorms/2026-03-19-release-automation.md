---
date: 2026-03-19
title: "Release automation via /cg-release prompt"
status: decided
chosen-approach: "Prompt + Generalized Script"
tags: [releases, automation, github-api, semver, cg-release, powershell]
---

# Release automation via /cg-release prompt

## Context

`create-release.ps1` creates a GitHub Release for GPID-WB/compound-gpid via the GitHub API. It currently has the tag (`v0.0.5`), release name, and ~40 lines of release notes hardcoded. Each release requires manually editing the script. The team wants a repeatable `/cg-release` workflow that Copilot can drive end-to-end.

## Requirements

1. **Generalized script**: `create-release.ps1` accepts `-Tag`, `-Name`, `-NotesFile`, `-Draft`, `-Prerelease` parameters. Preserves GCM auth, idempotency check (skip if tag exists), and `release-result.txt` output.
2. **Auto-detect version**: Read latest git tag, analyze commits since that tag using conventional commit types (`feat` → minor, `fix` → patch, breaking → major), suggest next semver tag. User can override.
3. **Curated release notes**: Copilot reads commits + diffs + `.cg-docs/` entries (brainstorms, plans, solutions) dated after last tag to write a human-friendly narrative (not just a commit log).
4. **SCHEMA_VERSION awareness**: If the release includes structural migrations (new folders, renamed paths), prompt the user to bump `SCHEMA_VERSION` before publishing. Include anything related to updating the plugin both in the repo and in the user's system.
5. **Ephemeral notes file**: Draft to `RELEASE_NOTES.md` (gitignored). GitHub Release is the source of truth — no local archive.
6. **Confirmation flow**: Present tag, name, notes preview, and SCHEMA_VERSION status. On user confirmation, execute the script in the terminal.
7. **Full auto-execute**: After confirmation, Copilot runs `create-release.ps1` directly (requires terminal tools).

### Out of scope (v1)

- Multi-repo releases (compound-gpid only)
- Build artifact attachments
- Persistent `CHANGELOG.md` accumulation
- Automatic `SCHEMA_VERSION` bumping (prompt warns; user decides)

## Approaches Considered

### Approach 1: Prompt + Generalized Script (chosen)

A `/cg-release` prompt orchestrates the full flow, calling a parameterized `create-release.ps1`.

- **Script**: dumb executor — takes parameters, authenticates via GCM, creates release, writes result file.
- **Prompt**: smart orchestrator — detects version, analyzes changes, drafts notes, checks SCHEMA_VERSION, confirms, executes.

**Pros**: Clean separation (script is standalone, usable in CI or manually). Fits the existing prompt system. SCHEMA_VERSION check built in.
**Cons**: Prompt file is moderately complex (~100-150 lines). Requires terminal tools for auto-execute.
**Effort**: Small-medium.

### Approach 2: Skill + Prompt

Extract version-detection and changelog-analysis into a `cg-skill-release` skill; thin prompt consumes it.

**Pros**: Reusable by other prompts (e.g., `/cg-resume` showing unreleased changes).
**Cons**: Premature abstraction — only one consumer. More files to maintain.
**Effort**: Medium.

### Approach 3: Prompt Only (no script changes)

Keep `create-release.ps1` hardcoded; prompt rewrites the values each time.

**Pros**: No PowerShell work.
**Cons**: Fragile, un-runnable outside Copilot, violates separation of concerns.
**Effort**: Small.

## Decision

**Approach 1: Prompt + Generalized Script.** Maximum leverage from the existing architecture with clean separation between automation (script) and intelligence (prompt). The script stays useful standalone; the prompt handles the knowledge work.

## Next Steps

1. Refactor `create-release.ps1` to accept parameters (`-Tag`, `-Name`, `-NotesFile`, `-Draft`, `-Prerelease`)
2. Add `RELEASE_NOTES.md` to `.gitignore`
3. Create `.github/prompts/cg-release.prompt.md` with the full orchestration flow
4. Add Pester tests for the parameterized script
5. Test end-to-end with a draft release
