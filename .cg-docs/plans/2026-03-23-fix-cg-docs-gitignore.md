---
date: 2026-03-23
title: "Stop gitignoring .cg-docs/ — institutional knowledge must be committed"
status: implemented
brainstorm: ~
language: "both"
estimated-effort: "small"
tags: [gitignore, cg-docs, bug, institutional-knowledge, setup, link]
---

# Plan: Stop Gitignoring `.cg-docs/`

## Context

`.cg-docs/` contains brainstorms, plans, and captured solutions — institutional
knowledge that the entire team should share. The current setup gitignores this
directory, which means:

- Brainstorms written by one team member are invisible to everyone else.
- Plans are not version-controlled and can be lost.
- Captured solutions (the output of `/cg-compound`) never enter the shared
  knowledge base.
- When a new Copilot session starts, the `cg-learnings-researcher` agent cannot
  find solutions that were written on another machine.

**Root cause**: `.cg-docs/` was originally treated as "local thinking artifacts"
analogous to scratch notes. This was a design mistake — these artifacts are the
primary knowledge output of the Compound Engineering workflow and must be shared.

**What stays gitignored**: Only `compound-gpid.local.md` (per-user config:
review depth, personal notes) remains gitignored.

## Scope

This fix touches **two source-of-truth locations** where `.cg-docs/` gets added
to `.gitignore`, plus documentation and tests. No prompt logic, agent behavior,
or skill content changes.

## Implementation Steps

### 1. Remove `.cg-docs/` from `cg-setup.prompt.md` gitignore block

- **File**: `.github/prompts/cg-setup.prompt.md`
- **Section**: Step A5 ("Update `.gitignore`")
- **Change**: Remove the `.cg-docs/` entry and its comment from the gitignore
  block. The block should become:

  ```gitignore
  # Compound GPID local config (user-specific, never commit)
  compound-gpid.local.md
  ```

  Remove these two lines entirely:
  ```gitignore
  # Compound GPID knowledge base (local thinking artifacts, typically not committed)
  .cg-docs/
  ```

- **Acceptance criteria**: Running `/cg-setup` on a new project does NOT add
  `.cg-docs/` to `.gitignore`. It still adds `compound-gpid.local.md`.

### 2. Ensure `link.ps1` does NOT include `.cg-docs/` in gitignore entries

- **File**: `scripts/link.ps1`
- **Section**: Step 5 — the `$cgGitignoreEntries` array and `$cgGitignoreMarker`
- **Change**: Verify that `.cg-docs/` is NOT in the `$cgGitignoreEntries` array.
  Based on current code, the array contains only `.github/` subdirectory entries
  and `copilot-instructions.md`. Confirm this is still the case.

  Also update the `$cgGitignoreMarker` comment string if it mentions
  "knowledge base". The current marker is:
  ```
  # Compound GPID managed items (junctions + copied file - do not commit)
  ```
  This is correct and should NOT reference `.cg-docs/`. Verify no variant of
  the marker (e.g., from an older version) includes "knowledge base".

- **Acceptance criteria**: Running `cg-link` does not add `.cg-docs/` to
  `.gitignore`. Only `.github/` junction entries are gitignored.

### 3. Update the `cg-setup.prompt.md` config file template text

- **File**: `.github/prompts/cg-setup.prompt.md`
- **Section**: Step A3 ("Create `compound-gpid.local.md`")
- **Change**: The template currently says:

  > This file configures Compound GPID for this project. It is gitignored and
  > local to your machine.

  This is correct for `compound-gpid.local.md` — no change needed here. But
  verify that no other comment in the prompt implies `.cg-docs/` is local or
  temporary.

- **Acceptance criteria**: No text in `cg-setup.prompt.md` describes `.cg-docs/`
  as "local", "temporary", "not committed", or "typically not committed".

### 4. Update `cg-skill-setup/SKILL.md` if it references gitignoring `.cg-docs/`

- **File**: `.github/skills/cg-skill-setup/SKILL.md`
- **Change**: Search for any reference to gitignoring `.cg-docs/`. If found,
  remove it. The skill should describe `.cg-docs/` as committed project
  knowledge, not as gitignored local artifacts.
- **Acceptance criteria**: No text in the setup skill implies `.cg-docs/` is
  gitignored or local.

### 5. Update tests that expect `.cg-docs/` in gitignore

- **File**: `tests/link.Tests.ps1`
- **Change**: The test file contains scenarios that include `.cg-docs/` in the
  gitignore block (e.g., the "does not orphan .cg-docs/" test and the
  deduplication test). These tests must be updated:
  - Remove `.cg-docs/` from any `$entries` arrays in test fixtures.
  - Remove or rewrite the "does not orphan .cg-docs/" test — it was testing
    upgrade behavior from a version that gitignored `.cg-docs/`. Replace it
    with a test that verifies `.cg-docs/` is NOT present in the CG gitignore
    block after linking.
  - Add a new test: "does not gitignore .cg-docs/" — after running the
    gitignore logic, assert that `.cg-docs/` does NOT appear in the output.

- **Acceptance criteria**: All tests pass. No test expects `.cg-docs/` in the
  gitignore block. At least one test explicitly verifies `.cg-docs/` is absent.

### 6. Update `docs/reference.md` directory structure description

- **File**: `docs/reference.md`
- **Change**: The directory structure section shows `.cg-docs/` with the comment
  `# Compound GPID knowledge base (committed — institutional memory)`. Verify
  this is accurate. If the comment says anything about being gitignored or
  local, fix it.
- **Acceptance criteria**: `docs/reference.md` describes `.cg-docs/` as
  committed institutional memory.

### 7. Check and update `README.md`

- **File**: `README.md`
- **Change**: Search for any reference to `.cg-docs/` being gitignored. If the
  README describes `.cg-docs/` as local or not committed, update the text to
  clarify it is committed and shared.
- **Acceptance criteria**: README describes `.cg-docs/` accurately.

### 8. Cancel or update the migration plan step that adds `.cg-docs/` to `link.ps1`

- **File**: `.cg-docs/plans/2026-03-05-cg-docs-migration-and-resume.md`
- **Change**: Step 12 of that plan says "Add `.cg-docs/` to `.gitignore` entries
  in `link.ps1`". This step must be marked as **cancelled** with a note:

  > **Cancelled (2026-03-23)**: `.cg-docs/` should NOT be gitignored. It
  > contains institutional knowledge (brainstorms, plans, solutions) that must
  > be committed and shared across the team. Only `compound-gpid.local.md`
  > (per-user config) is gitignored.

  If Step 12 was already implemented, **revert it** by removing `.cg-docs/`
  from the `$cgGitignoreEntries` array in `link.ps1` (covered by Step 2 above).

- **Acceptance criteria**: The old plan no longer instructs anyone to gitignore
  `.cg-docs/`.

### 9. Handle already-linked projects (migration note)

- **No code change** — this is a documentation/communication step.
- **Details**: Projects that were already set up with `/cg-setup` will have
  `.cg-docs/` in their `.gitignore`. After this fix, running `cg-link` again
  will rewrite the CG gitignore block (thanks to the remove-then-rewrite
  pattern), which will drop `.cg-docs/` from the block automatically.

  However, if `.cg-docs/` was added as a standalone line by `/cg-setup` (not
  inside the CG marker block), `cg-link` will not remove it. Users may need
  to manually remove the `.cg-docs/` line from their `.gitignore`.

  Add a note to the `cg-update` output or changelog so users know to check
  their `.gitignore` after updating.

- **Acceptance criteria**: A clear migration note exists for existing projects.

## Testing Strategy

### Automated (Pester)

1. **`link.Tests.ps1`**: Updated tests from Step 5 all pass.
2. **New negative test**: After running the gitignore logic, `.cg-docs/` is NOT
   in the output file.

### Manual

1. **New project**: Run `cg-link` then `/cg-setup` in a fresh project. Verify
   `.gitignore` contains `compound-gpid.local.md` but NOT `.cg-docs/`.
2. **Existing project**: Run `cg-link` in a project that already has `.cg-docs/`
   in its `.gitignore` inside the CG marker block. Verify the block is rewritten
   WITHOUT `.cg-docs/`.
3. **Git status**: After setup, create a brainstorm with `/cg-brainstorm`. Run
   `git status`. Verify the new brainstorm file appears as untracked (ready to
   be committed), not ignored.

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Existing projects have `.cg-docs/` gitignored outside the CG marker block | Medium | Document in migration note; users remove manually |
| Team members accidentally commit large data files inside `.cg-docs/` | Low | `.cg-docs/` only contains markdown files from brainstorms/plans/solutions — no data |
| Merge conflicts on `.cg-docs/` files when multiple people brainstorm | Low | Brainstorm/plan/solution files are date-prefixed and per-topic — different people will create different files, not edit the same one |

## Out of Scope

- Changing what `compound-gpid.local.md` contains (that's Step 2 of the larger
  roadmap — creating `compound-gpid.md` as the shared project file).
- Changing prompt logic or adding new prompts.
- Modifying the `.cg-docs/` directory structure itself.

## Verification — Final Grep

After all changes, run:

```powershell
# In the compound-gpid repo root:
Select-String -Path ".github\prompts\*", ".github\skills\*\*", "scripts\*", "docs\*", "README.md" -Pattern "\.cg-docs/" -Recurse | Where-Object { $_.Line -match "gitignore|ignore|not commit|local thinking" }
```

Expected result: **zero matches** (excluding this plan file and historical
`.cg-docs/` documents that are records-of-fact).
