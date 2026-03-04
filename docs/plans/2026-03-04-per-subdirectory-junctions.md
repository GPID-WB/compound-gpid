---
date: 2026-03-04
title: "Per-subdirectory junctions for .github coexistence"
status: active
brainstorm: "docs/brainstorms/2026-03-04-per-subdirectory-junctions.md"
language: "both"
estimated-effort: "medium"
tags: [install, link, unlink, update, .github, junctions, windows, powershell]
---

# Plan: Per-Subdirectory Junctions for .github Coexistence

## Objective

Replace the current whole-directory junction of `.github/` with per-subdirectory junctions (`prompts/`, `skills/`, `agents/`, `instructions/`) and a copied `copilot-instructions.md` with a management marker. This preserves any existing `.github/` content (GitHub Actions workflows, issue templates, CODEOWNERS, etc.) while keeping Compound GPID fully functional.

## Context

Today, `cg-link` replaces the entire `.github/` folder with a junction to `~\.compound-gpid\.github\`. If the user has existing content (workflows, templates), it's moved to `.github.bak`, breaking GitHub features. The brainstorm decided on Approach 2: per-subdirectory junctions + a copied `copilot-instructions.md` with a `<!-- compound-gpid:managed -->` marker.

**Key decisions from brainstorm:**
- Per-subdirectory junctions for `prompts/`, `skills/`, `agents/`, `instructions/`
- Copied `copilot-instructions.md` with marker for opt-out management
- Git-based protection (`git checkout . && git pull` in `cg-update`)
- `cg-link` calls `cg-update` first (in `$env:USERPROFILE\.compound-gpid`)
- Warning message during `cg-link` about managed directories
- Three commands: `cg-link`, `cg-unlink`, `cg-update`
- No more `.github.bak`

**Existing solutions to respect:**
- Pester 3.4 syntax required (no `-Be`, use `Be`; no `BeforeAll`; no `-Output`) — see `docs/solutions/testing-patterns/2026-03-04-pester-3-vs-5-windows-compatibility.md`
- Use `[System.Guid]::NewGuid()` for temp paths, not `$$` — see `docs/solutions/build-errors/2026-03-04-powershell-dollar-dollar-is-not-pid.md`
- Don't redirect git stderr into variables — see `docs/solutions/git-workflows/2026-03-04-git-pull-stderr-swallowed-by-redirect.md`

## Implementation Steps

### 1. Rewrite `scripts/link.ps1`

- **Files**: `scripts/link.ps1`
- **Details**:
  1. Keep the existing validation logic (check `$CompoundGpidDir` exists, check `$SourceGithub` exists).
  2. **Add `cg-update` call first**: Run `scripts/update.ps1` at the start to ensure the global clone is current. Use `Push-Location $CompoundGpidDir` and run the update logic. Handle offline gracefully (try, warn, continue).
  3. **Replace whole-directory junction logic** with per-subdirectory approach:
     - If `.github/` does not exist, create it as a real directory.
     - If `.github/` exists as a junction (legacy `cg-link`), remove it, create a real directory, then proceed.
     - For each of `prompts`, `skills`, `agents`, `instructions`:
       - Check if the target already exists in `.github/`.
       - If it's already a junction pointing to compound-gpid → skip (idempotent).
       - If it's already a junction pointing elsewhere → warn and ask to relink.
       - If it's a real directory → error with clear message ("You have a local `prompts/` directory that conflicts").
       - Otherwise → create the junction.
     - For `copilot-instructions.md`:
       - If it exists and contains `<!-- compound-gpid:managed -->` → overwrite with latest copy.
       - If it exists and does NOT contain the marker → skip with message ("copilot-instructions.md is user-managed, skipping").
       - If it does not exist → copy with marker.
  4. **Remove all `.github.bak` logic** — no more backup/rename.
  5. **Update `.gitignore` management**: Still add `.github` to `.gitignore`. Remove `.github.bak` references. The user's existing `.github/` content is not junction-linked, so it would be committed — but wait, the whole `.github/` is gitignored. This means the user's workflows etc. would also be ignored. **Important design decision**: we should NOT gitignore all of `.github/`. Instead, gitignore only the managed subdirectories and the managed file:
     - `.github/prompts/`
     - `.github/skills/`
     - `.github/agents/`
     - `.github/instructions/`
     - `.github/copilot-instructions.md`
  6. **Print warning message** about managed directories: "The following directories are managed by Compound GPID and should not be edited directly: prompts/, skills/, agents/, instructions/. Run cg-update to refresh."
- **Tests**: See Step 4
- **Acceptance criteria**:
  - Running `cg-link` in a project with no `.github/` creates the directory and all junctions + copied file.
  - Running `cg-link` in a project with an existing `.github/` (containing `workflows/`, etc.) adds junctions alongside existing content.
  - Running `cg-link` twice is idempotent.
  - User's existing `.github/` content is NOT moved, renamed, or deleted.
  - Existing `.github/workflows/`, templates, etc. remain visible and functional.

### 2. Rewrite `scripts/unlink.ps1`

- **Files**: `scripts/unlink.ps1`
- **Details**:
  1. **Handle legacy whole-directory junction**: If `.github/` itself is a junction, remove it (same as today, for backward compatibility). Do NOT offer to restore `.github.bak` — that pattern is removed.
  2. **Handle per-subdirectory junctions**: For each of `prompts`, `skills`, `agents`, `instructions`:
     - If it exists and is a junction → remove it.
     - If it exists and is a real directory → skip with message ("Not a junction, skipping").
  3. **Handle `copilot-instructions.md`**:
     - If it exists and contains `<!-- compound-gpid:managed -->` → delete it.
     - If it exists without the marker → skip ("User-managed, leaving in place").
  4. **Clean up `.github/`**: If `.github/` is now empty after removing junctions, delete the empty directory.
  5. **Remove entries from `.gitignore`**: Remove the specific CG-managed entries (`.github/prompts/`, etc.). Leave other `.gitignore` content untouched.
  6. **Remove all `.github.bak` restore logic**.
- **Tests**: See Step 4
- **Acceptance criteria**:
  - Removes only CG-managed junctions and the marker-tagged file.
  - Leaves user's own `.github/` content untouched.
  - Handles legacy whole-directory junctions gracefully.
  - Idempotent — running twice does not error.

### 3. Update `scripts/update.ps1`

- **Files**: `scripts/update.ps1`
- **Details**:
  1. **Add `git checkout .` before `git pull`**: This discards any accidental local changes in the global clone before pulling.
  2. **After successful pull, re-copy `copilot-instructions.md`**: Scan for linked projects is not feasible, so this only refreshes the global source. Linked projects get junction updates automatically for subdirectories. For `copilot-instructions.md`, the user needs to run `cg-link` again or we need a different mechanism.
     - **Alternative**: `cg-update` only updates the global clone. The next time `cg-link` is run, it re-copies the file. OR: `cg-update` could look for `.github/copilot-instructions.md` in the current directory and refresh it if the marker is present.
     - **Chosen approach**: `cg-update` updates the global clone AND checks the current working directory for a linked project. If `.github/copilot-instructions.md` exists with the marker in the CWD, re-copy it from the updated global source.
  3. Keep the existing logging (before/after hash comparison, commit log).
  4. Keep `--ff-only` and direct git output (no `2>&1` capture per solution doc).
- **Tests**: See Step 4
- **Acceptance criteria**:
  - Accidental changes to global clone are reset before pull.
  - `copilot-instructions.md` in the current project (if linked and marker-present) is refreshed.
  - Offline/failure is handled gracefully with a warning.

### 4. Update tests

- **Files**: `tests/link.Tests.ps1`, `tests/unlink.Tests.ps1` (new), `tests/update.Tests.ps1`
- **Details**:
  - **Use Pester 3.4 syntax** (`Should Be`, not `Should -Be`; no `BeforeAll`; no `-Output`).
  - **`tests/link.Tests.ps1`** — rewrite to test:
    - Junction creation for each subdirectory (not whole-directory).
    - `copilot-instructions.md` copy with marker.
    - Idempotency (running link twice).
    - Existing `.github/` content is preserved (create a `workflows/` dir, run link logic, verify `workflows/` still exists).
    - Legacy whole-directory junction detection and migration.
    - `.gitignore` management (specific entries, not blanket `.github`).
    - Remove `.github.bak` test cases.
  - **`tests/unlink.Tests.ps1`** (new file) — test:
    - Junction removal for each subdirectory.
    - Marker-based `copilot-instructions.md` deletion.
    - User-managed file is left in place.
    - Empty `.github/` cleanup.
    - Legacy junction handling.
  - **`tests/update.Tests.ps1`** — add tests for:
    - `git checkout .` is called before pull (can test the logic flow, not git itself).
    - `copilot-instructions.md` re-copy when marker is present in CWD.
    - Marker-absent file is skipped.
- **Acceptance criteria**: All tests pass with `Invoke-Pester tests/`.

### 5. Update `README.md`

- **Files**: `README.md`
- **Details**:
  - Update the "Step 3: Link your project" section to explain per-subdirectory linking.
  - Remove references to `.github.bak`.
  - Mention that existing `.github/` content is preserved.
  - Document the `copilot-instructions.md` marker behavior.
  - Update the "Updating" section to mention `git checkout .` reset behavior.
- **Acceptance criteria**: README accurately reflects the new behavior.

### 6. Update `install.ps1` (minor)

- **Files**: `install.ps1`
- **Details**:
  - No major changes needed — `install.ps1` registers the aliases and tests junctions.
  - Verify the existing junction test still works (it creates a temp junction, which is unrelated to per-subdirectory linking).
  - Update comments if they reference the old whole-directory approach.
- **Acceptance criteria**: `install.ps1` runs cleanly and registers all three aliases.

## Testing Strategy

- **Unit tests (Pester 3.4)**: Test each logical component in isolation using `$TestDrive` for temp directories.
- **Integration-like tests**: Create realistic `.github/` scenarios (empty, with workflows, with legacy junction) and verify correct behavior.
- **Idempotency tests**: Run link/unlink twice, verify no errors and correct state.
- **Edge cases to cover**:
  - `.github/` does not exist
  - `.github/` exists with user content (workflows, templates)
  - `.github/` is a legacy whole-directory junction
  - `copilot-instructions.md` with marker (managed)
  - `copilot-instructions.md` without marker (user-managed)
  - `copilot-instructions.md` does not exist
  - `.gitignore` does not exist
  - `.gitignore` exists with some CG entries already
  - `.gitignore` exists with none of the CG entries
  - Offline scenario (git pull fails)

## Documentation Checklist

- [ ] Script header comments updated in all modified scripts
- [ ] README.md updated with new behavior
- [ ] Inline comments for marker-detection logic
- [ ] Warning messages are clear and actionable

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| User has a `prompts/` directory in `.github/` that conflicts | Low | High | Detect and error with clear message, don't silently overwrite |
| Legacy whole-directory junction not detected | Low | Medium | Explicit check for `.github/` being a junction before creating subdirectories |
| `.gitignore` parsing edge cases (trailing spaces, comments) | Medium | Low | Use regex matching with anchors, test edge cases |
| `cg-update` in `cg-link` fails (offline) | Medium | Low | Try/catch, warn, continue linking with whatever version is available |
| Marker comment accidentally included in user's custom file | Very Low | Low | Marker is specific enough (`<!-- compound-gpid:managed -->`) to be unlikely |

## Out of Scope

- **Cross-platform support** (macOS/Linux) — this iteration is Windows-only.
- **Manifest file** (Approach 3) — can be added later if the number of managed items grows.
- **Read-only file protection** — decided against in brainstorm; git-based protection is sufficient.
- **Per-project tracking of linked state** — `cg-update` only refreshes CWD, not all linked projects.
- **Merging user and CG `copilot-instructions.md`** — user opts in or out; no content merging.
