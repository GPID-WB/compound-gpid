---
date: 2026-03-05
title: "Migrate docs/ to .cg-docs/ and add /cg-resume prompt"
status: active
brainstorm: ".cg-docs/brainstorms/2026-03-05-cg-docs-migration-and-resume.md"
language: "both"
estimated-effort: "medium"
tags: [migration, docs, cg-resume, rbuildignore, update-script, breaking-change]
---

# Plan: Migrate docs/ to .cg-docs/ and Add /cg-resume Prompt

## Objective

Move all Compound GPID–managed documentation (brainstorms, plans, solutions) from `docs/` to `.cg-docs/` to avoid collisions with projects that already use `docs/` for their own purposes (pkgdown, Sphinx, MkDocs, etc.). Add automatic migration for existing users, R package `.Rbuildignore` support, and a new `/cg-resume` prompt for picking up interrupted work.

## Context

- **Current state**: All CG-managed brainstorms/plans/solutions live under `docs/` in user projects. The compound-gpid repo itself also stores its own brainstorms/plans/solutions there alongside `docs/manual.md`.
- **Problem**: Many projects use `docs/` for their own documentation, causing namespace collisions.
- **Decision**: Move CG-managed content to `.cg-docs/` (dot-prefix signals "tool-managed"). Keep `docs/manual.md` in `docs/` for the compound-gpid repo itself.
- **User base**: Small (early adopters), so a clean-cut migration is safe.

## Implementation Steps

### 1. Migrate compound-gpid's own folders

- **Details**: Move `docs/brainstorms/`, `docs/plans/`, `docs/solutions/` to `.cg-docs/` in this repo. Keep `docs/manual.md` in place.
- **Acceptance criteria**: `.cg-docs/brainstorms/`, `.cg-docs/plans/`, `.cg-docs/solutions/` exist with all original content. `docs/manual.md` stays. `docs/brainstorms/`, `docs/plans/`, `docs/solutions/` no longer exist.

### 2. Update all prompt files (6 files)

Replace every `docs/brainstorms`, `docs/plans`, `docs/solutions` reference with `.cg-docs/brainstorms`, `.cg-docs/plans`, `.cg-docs/solutions`.

- **Files**:
  - `.github/prompts/cg-brainstorm.prompt.md` — 4 references
  - `.github/prompts/cg-plan.prompt.md` — 6 references
  - `.github/prompts/cg-work.prompt.md` — 1 reference
  - `.github/prompts/cg-compound.prompt.md` — 3 references
  - `.github/prompts/cg-review.prompt.md` — 1 reference (line with 2 occurrences)
  - `.github/prompts/cg-setup.prompt.md` — ~17 references (largest change; also needs `.Rbuildignore` logic)
- **Acceptance criteria**: No remaining `docs/brainstorms`, `docs/plans`, or `docs/solutions` references in any prompt file. All references point to `.cg-docs/`.

### 3. Update cg-setup prompt with .Rbuildignore and .cg-docs/ scaffolding

- **File**: `.github/prompts/cg-setup.prompt.md`
- **Details**:
  - Change `docs/` scaffolding (Steps A4, B1.5) to `.cg-docs/` scaffolding.
  - Update file permissions section: replace `docs/` with `.cg-docs/`.
  - Add `.Rbuildignore` step: after scaffolding `.cg-docs/`, if the user selected "package" project type AND the language is R or both, add `^\.cg-docs$` to `.Rbuildignore` (create the file if needed).
  - Update `.gitignore` step: add `.cg-docs/` entry.
  - In Mode B (returning project), scan `.cg-docs/` instead of `docs/` for existing work.
- **Acceptance criteria**: New projects get `.cg-docs/` scaffolded. R package projects get `.Rbuildignore` entry. Returning projects scan `.cg-docs/`.

### 4. Update agent file (1 file)

- **File**: `.github/agents/cg-learnings-researcher.agent.md` — 8 references
- **Details**: Replace all `docs/solutions/`, `docs/brainstorms/`, `docs/plans/` → `.cg-docs/solutions/`, `.cg-docs/brainstorms/`, `.cg-docs/plans/`.
- **Note**: Only `cg-learnings-researcher` references knowledge directories. The other 8 review agents (`cg-code-quality`, `cg-testing`, `cg-documentation`, `cg-version-control`, `cg-reproducibility`, `cg-performance`, `cg-architecture`, `cg-data-quality`) analyze *project code only* — they have no knowledge of CG-managed directories and do not need updating.
- **Acceptance criteria**: No remaining `docs/` references for brainstorms/plans/solutions.

### 5. Update skill files (6 files)

- **Files**:
  - `.github/skills/cg-skill-setup/SKILL.md` — 5 references
  - `.github/skills/cg-skill-compound-docs/SKILL.md` — 7 references
  - `.github/skills/cg-skill-compound-docs/workflows/capture-solution.md` — 2 references
  - `.github/skills/cg-skill-compound-docs/workflows/search-solutions.md` — 3 references
  - `.github/skills/cg-skill-brainstorming/references/decision-template.md` — 1 reference
  - `.github/skills/cg-skill-git-workflow/workflows/pr-template.md` — 2 references
- **Details**: Replace all `docs/brainstorms`, `docs/plans`, `docs/solutions` → `.cg-docs/brainstorms`, `.cg-docs/plans`, `.cg-docs/solutions`.
- **Acceptance criteria**: No remaining `docs/` references for brainstorms/plans/solutions in any skill file.

### 6. Update copilot-instructions.md

- **File**: `.github/copilot-instructions.md`
- **Details**: Replace `docs/solutions/[category]/` → `.cg-docs/solutions/[category]/`.
- **Acceptance criteria**: Reference points to `.cg-docs/`.

### 7. Update README.md

- **File**: `README.md`
- **Details**:
  - Update the directory structure diagram: change `docs/` tree to show `.cg-docs/` for brainstorms/plans/solutions.
  - Keep reference to `docs/manual.md` as-is (it stays in `docs/`).
  - Update Step 4 description: scaffolds `.cg-docs/` instead of `docs/`.
- **Acceptance criteria**: Structure diagram shows `.cg-docs/`. Manual reference unchanged.

### 8. Update docs/manual.md

- **File**: `docs/manual.md`
- **Details**: Replace all ~9 references to `docs/brainstorms`, `docs/plans`, `docs/solutions` → `.cg-docs/brainstorms`, `.cg-docs/plans`, `.cg-docs/solutions`. Keep `docs/manual.md` self-reference as-is.
- **Acceptance criteria**: All CG-managed path references point to `.cg-docs/`. Manual's own location reference unchanged.

### 9. Update ROADMAP.md

- **File**: `ROADMAP.md`
- **Details**: Replace `docs/solutions/` → `.cg-docs/solutions/` on line 51.
- **Acceptance criteria**: Reference points to `.cg-docs/`.

### 10. Update self-references in migrated .cg-docs/ files

- **Files**: All files now under `.cg-docs/brainstorms/`, `.cg-docs/plans/`, `.cg-docs/solutions/`
- **Details**: Update internal `docs/` references to `.cg-docs/` where they refer to CG-managed paths. Leave historical references (describing what the old structure looked like) as-is where they serve as documentation of the change.
- **Acceptance criteria**: Files in `.cg-docs/` reference `.cg-docs/` paths for current/future use.

### 11. Add migration logic to update.ps1

- **File**: `scripts/update.ps1`
- **Details**: After the git pull and copilot-instructions.md refresh, add a new section that:
  1. Checks if the current directory is a linked project (same guard as copilot-instructions.md refresh).
  2. For each of `brainstorms`, `plans`, `solutions`: checks if `docs/<dir>` exists in the current project.
  3. If any exist: creates `.cg-docs/` if needed, moves each `docs/<dir>` → `.cg-docs/<dir>` using `Move-Item`.
  4. If `docs/` is now empty after migration, removes the empty `docs/` directory.
  5. Prints a clear message: "Migrated docs/{brainstorms,plans,solutions} → .cg-docs/".
  6. If none exist, skip silently (new projects will get `.cg-docs/` from `/cg-setup`).
  7. After migration (or if already migrated), update `compound-gpid.local.md` to set `cg-schema-version` to the current schema version (see Step 11b).
- **Idempotency note**: Running `cg-update` from multiple projects is safe. In each project, `git pull` runs first (returns "Already up to date." after the first run — exit code 0) and then the migration logic fires independently per project. Subsequent runs skip migration because `docs/brainstorms/` no longer exists.
- **Edge cases**:
  - If `.cg-docs/<dir>` already exists (partial migration): merge contents (move individual files, skip if target name already exists, warn user).
  - If `docs/` has other user content (`manual.md`, custom folders): leave it alone, only remove if empty.
- **Acceptance criteria**: Running `cg-update` from a project with `docs/brainstorms/` auto-migrates to `.cg-docs/brainstorms/`. User content in `docs/` is preserved. Multiple runs are idempotent.

### 11b. Add structural schema versioning

- **Files**: new `SCHEMA_VERSION` file in repo root; `compound-gpid.local.md` (added field); `scripts/update.ps1`
- **Details**:
  - Create `SCHEMA_VERSION` in the compound-gpid repo root with content `2026-03-05-cg-docs` (the version name for this migration).
  - Update `update.ps1`: after completing all structural migration steps for the current project, write `cg-schema-version: "2026-03-05-cg-docs"` into the project's `compound-gpid.local.md` (add/update the field).
  - Future structural migrations will bump `SCHEMA_VERSION`, and `update.ps1` will only run migration steps for versions the project hasn't applied yet. This is the foundation for a two-tier update model: prompt/skill/agent changes (non-structural) propagate instantly via junctions; folder-structure changes (structural) are migration-gated per project.
- **Note**: This step also feeds Step 15 — `/cg-resume` reads `cg-schema-version` from local config and compares to the global `SCHEMA_VERSION` to warn the user if their project needs a structural migration.
- **Acceptance criteria**: `SCHEMA_VERSION` file exists in repo root. After `cg-update`, each project's `compound-gpid.local.md` contains `cg-schema-version`. Schema version matches between SCHEMA_VERSION and local config after migration.

### 12. Add .cg-docs/ to .gitignore entries in link.ps1

- **File**: `scripts/link.ps1`
- **Details**: Add `.cg-docs/` to the `$cgGitignoreEntries` array so it gets gitignored when linking a project. This prevents CG-managed docs from being accidentally committed.
- **Acceptance criteria**: After `cg-link`, `.gitignore` includes `.cg-docs/`.

### 13. Add Pester tests for migration logic

- **File**: `tests/update.Tests.ps1`
- **Details**: Add test cases for the new migration logic:
  - Migration moves `docs/brainstorms/` → `.cg-docs/brainstorms/` correctly
  - Migration moves `docs/plans/` → `.cg-docs/plans/` correctly
  - Migration moves `docs/solutions/` → `.cg-docs/solutions/` correctly
  - Migration skips when `docs/brainstorms/` etc. don't exist
  - Migration handles partial state (some dirs already migrated)
  - Migration preserves other `docs/` content (e.g., `docs/manual.md`)
  - Migration is idempotent
  - Empty `docs/` is cleaned up after migration
- **Acceptance criteria**: All migration tests pass.

### 14. Add .Rbuildignore check to cg-review prompt

- **File**: `.github/prompts/cg-review.prompt.md`
- **Details**: In the agent dispatch section, add a note that `@cg-code-quality` should check: if `DESCRIPTION` + `NAMESPACE` or `R/` exist (R package signals) and `.cg-docs/` exists but is not listed in `.Rbuildignore`, flag as P2 finding.
- **Acceptance criteria**: Review prompt includes the `.Rbuildignore` check instruction.

### 15. Create /cg-resume prompt

- **File**: `.github/prompts/cg-resume.prompt.md`
- **Details**: Create a new prompt that:
  1. Reads `compound-gpid.local.md` for project config, including `cg-schema-version`.
  2. **Schema version check**: reads `SCHEMA_VERSION` from the global compound-gpid install (`~/.compound-gpid/SCHEMA_VERSION`) and compares to `cg-schema-version` in local config. If behind, warns: *"Your project structure is outdated. Run `cg-update` from this project's root to apply migrations before continuing."* and stops.
  3. Scans `.cg-docs/plans/` for plans with `status: active` or `status: in-progress` in YAML frontmatter.
  4. Scans `.cg-docs/brainstorms/` for brainstorms with `status: decided` that have no corresponding plan.
  5. Checks recent git log (last 10 commits) for recent work context.
  6. Checks for uncommitted changes (`git status`).
  7. Presents a structured summary of pending work.
  8. Asks the user which item to pick up, or if they want to start something new.
- **File permissions**: Read-only (no file creation or modification).
- **Model**: Claude Sonnet 4.6 (fast context loading, no heavy reasoning needed).
- **Acceptance criteria**: `/cg-resume` is available in Copilot Chat, warns about outdated schema, scans for in-progress work, and presents actionable options.

### 16. Update README.md with /cg-resume

- **File**: `README.md`
- **Details**: Add `/cg-resume` to the workflow table and commands list.
- **Acceptance criteria**: README documents `/cg-resume` alongside other commands.

### 17. Update docs/manual.md with /cg-resume

- **File**: `docs/manual.md`
- **Details**: Add a section for `/cg-resume` explaining when and how to use it.
- **Acceptance criteria**: Manual documents the resume workflow.

## Testing Strategy

- **Pester tests** (Step 13): Unit tests for the migration logic in `update.ps1` using `$TestDrive` to simulate project structures. Include schema version read/write tests.
- **Manual smoke test**: After all changes, run `cg-update` from a project with the old `docs/` structure and verify migration and `cg-schema-version` written to local config.
- **Prompt verification**: Open a linked project and verify `/cg-resume` appears in Copilot Chat. Test both the "schema outdated" warning path and the normal context-loading path.
- **Grep verification**: After all edits, run `grep -r "docs/brainstorms\|docs/plans\|docs/solutions" .github/` to confirm zero remaining old-path references in managed files.

## Documentation Checklist

- [ ] README.md updated with `.cg-docs/` structure and `/cg-resume`
- [ ] docs/manual.md updated with `.cg-docs/` paths and `/cg-resume` section
- [ ] ROADMAP.md path reference updated
- [ ] All prompt file permissions sections reflect `.cg-docs/`
- [ ] copilot-instructions.md references updated

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| User has files in both `docs/<dir>` and `.cg-docs/<dir>` | File conflicts during migration | Merge: move individual files, skip if target name exists, warn user |
| `docs/` contains user content besides brainstorms/plans/solutions | Accidentally deleting user files | Only remove `docs/` if empty after migration; never remove individual files |
| R package user doesn't run `/cg-setup` after migration | Missing `.Rbuildignore` entry | `/cg-review` has defensive P2 check for this |
| User on old Compound GPID version doesn't update | Prompts reference `.cg-docs/` but folders are still at `docs/` | Junction architecture means prompt changes propagate on `cg-update`; migration runs from project dir |

## Out of Scope

- **Cross-project knowledge sharing** — archived in ROADMAP; not addressed here
- **Auto-discovering and migrating all linked projects in one `cg-update` run** — migration only fires when `cg-update` is run from a linked project root; users with multiple projects must run it in each. The `/cg-resume` schema version check will warn them if they haven't done so.
- **Backwards compatibility layer** — no dual-path support; clean cut per brainstorm decision
- **Legacy GPID prompts integration** — tracked in ROADMAP Phase 5; separate effort
