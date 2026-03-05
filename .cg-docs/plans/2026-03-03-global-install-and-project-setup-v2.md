---
date: 2026-03-03
title: "Global install with PowerShell aliases and per-project setup"
status: active
brainstorm: "docs/brainstorms/2026-03-03-global-install-and-project-setup.md"
language: "both"
estimated-effort: "medium"
tags: [installation, distribution, team-onboarding, windows, junctions, powershell]
supersedes: "docs/plans/2026-03-03-global-install-and-project-setup.md"
---

# Plan: Global Install with PowerShell Aliases and Per-Project Setup

## Objective

Replace the current manual installation process with an automated, no-admin-rights workflow:
- One-time global install: clone + run `install.ps1` (registers `cg-*` aliases in PowerShell profile).
- Per-project linking: `cg-link` from any project folder (creates `.github` junction).
- Per-project setup: `/cg-setup` in Copilot Chat (config + scaffolding + context loading).
- Global update: `cg-update` from anywhere.

## Context

- **Current state**: README tells users to clone to `C:\tools\compound-gpid` and manually run `mklink /J`. Fragile and error-prone.
- **Brainstorm decision**: Global clone + automated junction. See `docs/brainstorms/2026-03-03-global-install-and-project-setup.md`.
- **Key insight**: VS Code / Copilot only discovers `.github/prompts/`, `.github/agents/`, `.github/skills/` inside the open workspace folder. A directory junction makes the global clone's `.github/` appear inside the project. `/cg-setup` only becomes available AFTER the junction exists.
- **Known issue**: `cg-skill-setup` is a skill, not a prompt — `/cg-setup` doesn't work as a slash command today. This plan creates the prompt. See `docs/solutions/environment-issues/2026-03-02-skill-vs-prompt-slash-command.md`.

## User Flow (Final)

```
# === ONE-TIME INSTALL (copy-paste 2 lines from README) ===
git clone https://github.com/GPID-WB/compound-gpid.git "$env:USERPROFILE\.compound-gpid"
& "$env:USERPROFILE\.compound-gpid\install.ps1"
# Restart terminal (or run: . $PROFILE)

# === PER-PROJECT (from project root) ===
cg-link          # creates .github junction → enables all Copilot prompts
                 # then run /cg-setup in Copilot Chat for config + scaffolding

# === UPDATING (from anywhere, at any time) ===
cg-update        # git pull; all linked projects see changes immediately

# === DISCONNECT (optional) ===
cg-unlink        # removes the .github junction
```

## Implementation Steps

### 1. Create `scripts/` directory with PowerShell scripts

- **Files**: Create `scripts/link.ps1`, `scripts/unlink.ps1`, `scripts/update.ps1`
- **Details**:

  **`scripts/link.ps1`**:
  - Check if `.github` already exists in the current directory.
    - If it's already a junction pointing to compound-gpid: print "Already linked." and exit.
    - If it's a regular directory: warn the user, offer to back it up to `.github.bak`, then create the junction.
    - If it doesn't exist: create the junction.
  - Run: `cmd /c mklink /J ".github" "$env:USERPROFILE\.compound-gpid\.github"`
  - Verify the junction works (test that `.github\prompts` exists via the junction).
  - Add `.github` to `.gitignore` if not already there.
  - Print success: "Linked! Run /cg-setup in Copilot Chat to configure this project."

  **`scripts/unlink.ps1`**:
  - Check if `.github` is a junction (not a regular directory).
  - If it is: remove the junction (`cmd /c rmdir ".github"` — this removes the junction without deleting the target).
  - If `.github.bak` exists: offer to restore it.
  - Print success: "Unlinked. Compound GPID prompts are no longer available in this project."

  **`scripts/update.ps1`**:
  - Check `$env:USERPROFILE\.compound-gpid` exists; if not, error.
  - `Push-Location "$env:USERPROFILE\.compound-gpid"`
  - Capture current commit: `$before = git rev-parse --short HEAD`
  - Run `git pull --ff-only`
  - Capture new commit: `$after = git rev-parse --short HEAD`
  - If different: show `git log --oneline $before..$after` and print "Updated. All linked projects see the changes immediately."
  - If same: print "Already up to date."
  - `Pop-Location`

- **Acceptance criteria**:
  - `cg-link` creates a working junction from any project folder.
  - `cg-unlink` cleanly removes junction without deleting compound-gpid files.
  - `cg-update` pulls latest and reports changes.
  - Existing `.github/` directories are handled gracefully (backed up).
  - `.gitignore` is updated automatically by `cg-link`.

### 2. Create `install.ps1` (Global Install Script)

- **Files**: Create `install.ps1` in the repo root.
- **Details**:
  - This script is run AFTER cloning (since the user needs the repo to have this file).
  - Verify Git is available (`Get-Command git`); if not, error with download link.
  - Verify junction capability: create a temp junction in `$env:TEMP`, test, remove. If fails: print instructions to enable Developer Mode.
  - Register `cg-*` functions in the user's PowerShell profile (`$PROFILE`):
    - Check if `$PROFILE` file exists; create it if not (`New-Item -Force`).
    - Check if compound-gpid block already exists in profile (idempotent — don't add twice).
    - Append a clearly delimited block:
      ```powershell
      # --- Compound GPID (added by install.ps1) ---
      function cg-link { & "$env:USERPROFILE\.compound-gpid\scripts\link.ps1" @args }
      function cg-unlink { & "$env:USERPROFILE\.compound-gpid\scripts\unlink.ps1" @args }
      function cg-update { & "$env:USERPROFILE\.compound-gpid\scripts\update.ps1" @args }
      # --- End Compound GPID ---
      ```
  - Print success summary:
    ```
    Compound GPID installed successfully!
    
    Location: C:\Users\<you>\.compound-gpid
    
    IMPORTANT: Restart your terminal (or run `. $PROFILE`) for commands to take effect.
    
    Available commands:
      cg-link    — Link current project (run from project root)
      cg-update  — Update Compound GPID (run from anywhere)
      cg-unlink  — Unlink current project (run from project root)
    
    Quick start:
      1. cd to your project folder
      2. Run: cg-link
      3. Open VS Code, run /cg-setup in Copilot Chat
    ```
  - The script must be runnable via: `powershell -ExecutionPolicy Bypass -File install.ps1`

- **Acceptance criteria**:
  - Running `install.ps1` registers functions in `$PROFILE`.
  - Running it again doesn't duplicate the profile block (idempotent).
  - Clear error if Git is missing.
  - Clear error if junctions aren't supported.
  - Clear success message with next steps.

### 3. Create `cg-setup.prompt.md` (Per-Project Setup Prompt)

- **Files**: Create `.github/prompts/cg-setup.prompt.md`
- **Details**:
  This prompt handles two modes:

  **Mode A — New project (no `compound-gpid.local.md`)**:
  1. Verify `.github/` junction exists (check for `.github/prompts/cg-setup.prompt.md` — if the prompt is running, the junction is already there).
  2. Ask language preference (R, Python, both).
  3. Ask project type (package, analysis, dashboard, API, tool).
  4. Ask review depth (light, standard, thorough).
  5. Create `compound-gpid.local.md` in the project root.
  6. Scaffold `docs/` directory structure (brainstorms, plans, solutions with subcategories).
  7. Add `compound-gpid.local.md` to `.gitignore` if not already there.
  8. Print "Setup Complete" summary with available commands.

  **Mode B — Returning project (`compound-gpid.local.md` exists)**:
  1. Read `compound-gpid.local.md` — report current config.
  2. Scan `docs/brainstorms/` — list existing brainstorms with dates and titles.
  3. Scan `docs/plans/` — list existing plans with dates, titles, and status.
  4. Scan `docs/solutions/` — list existing solutions by category.
  5. Present a summary: "This project is configured for [language], [project-type], [review-depth]. It has X brainstorms, Y plans, and Z captured solutions."
  6. Ask if the user wants to update any configuration or start working.

  **File Permissions**:
  - You may read any file in the workspace.
  - You may create `compound-gpid.local.md` in the project root.
  - You may create new files and directories under `docs/`.
  - You may append to `.gitignore`.
  - You must not modify any other existing files.

- **Acceptance criteria**:
  - `/cg-setup` is available as a slash command in Copilot Chat (after junction exists).
  - New projects get full scaffolding + config.
  - Returning projects get a context summary.

### 4. Update `cg-skill-setup/SKILL.md`

- **Files**: Modify `.github/skills/cg-skill-setup/SKILL.md`
- **Details**:
  - Add a note at the top: "This skill provides reference configuration knowledge. For interactive setup, use the `/cg-setup` prompt."
  - Add a section documenting the junction-based installation model.
  - Keep existing config schema content (still used as reference by other prompts/agents).
- **Acceptance criteria**:
  - Skill references the new prompt.
  - Existing prompts/agents that reference this skill still work.

### 5. Update `README.md`

- **Files**: Modify `README.md`
- **Details**:
  Replace the "Installation" section with the new flow:

  ```markdown
  ## Installation

  ### Step 1: Clone (one-time)
  git clone https://github.com/GPID-WB/compound-gpid.git "$env:USERPROFILE\.compound-gpid"

  ### Step 2: Install (one-time)
  & "$env:USERPROFILE\.compound-gpid\install.ps1"
  # Restart your terminal (or run: . $PROFILE)

  ### Step 3: Link your project (per-project)
  cd C:\path\to\your-project
  cg-link

  ### Step 4: Configure (per-project)
  # In VS Code Copilot Chat:
  /cg-setup

  ## Updating
  cg-update
  ```

  Also update:
  - Remove all references to `C:\tools\`.
  - Update "Directory Structure" to show `.github/` as junction.
  - Add `.github` to the `.gitignore` guidance.
  - Reference `/cg-setup` as a prompt, not a skill.
  - Add `cg-link`, `cg-unlink`, `cg-update` to the commands table.

- **Acceptance criteria**:
  - No reference to `C:\tools\` remains.
  - Install instructions use the 4-step flow.
  - All commands documented.

### 6. Update `docs/manual.md`

- **Files**: Modify `docs/manual.md`
- **Details**:
  - Update "Getting Started" to reflect 4-step flow.
  - Change setup instruction from "Load the `cg-skill-setup` skill" to "Run `/cg-setup`".
  - Add a "Updating Compound GPID" section.
  - Add `/cg-setup` to the Prompts table.
  - Add a "PowerShell Commands" section documenting `cg-link`, `cg-update`, `cg-unlink`.
- **Acceptance criteria**:
  - Manual accurately reflects the new workflow.
  - No stale references.

### 7. Verify `.gitignore` and repo structure

- **Files**: Check `.gitignore`, verify `scripts/` and `install.ps1` are tracked.
- **Details**:
  - Ensure `install.ps1` and `scripts/*.ps1` are not gitignored.
  - Verify directory structure is clean.
- **Acceptance criteria**: All new files are tracked by Git.

## Testing Strategy

Manual testing in a **separate project folder** (not compound-gpid itself):

1. **Fresh install**: Clone compound-gpid, run `install.ps1`, restart terminal. Verify `cg-link`, `cg-update`, `cg-unlink` are available.
2. **Link test**: `cd` to a test project, run `cg-link`. Verify `.github/` junction works (prompts visible in VS Code).
3. **Copilot test**: Open the test project in VS Code. Verify `/cg-setup` appears. Run it, verify config and `docs/` scaffolding.
4. **Update test**: Modify something in compound-gpid repo, run `cg-update`. Verify change visible in linked project.
5. **Unlink test**: Run `cg-unlink`. Verify `.github/` junction removed, project unaffected.
6. **Idempotency**: Run `install.ps1` twice — profile not duplicated. Run `cg-link` twice — no error.
7. **Existing `.github/`**: Test on project with existing `.github/` directory — verify backup and warning.
8. **Re-setup**: Open a previously configured project, run `/cg-setup`. Verify it reads existing context.

## Documentation Checklist

- [ ] `install.ps1` has comment header explaining purpose and usage
- [ ] `scripts/link.ps1` has comment header
- [ ] `scripts/unlink.ps1` has comment header
- [ ] `scripts/update.ps1` has comment header
- [ ] `cg-setup.prompt.md` has File Permissions section
- [ ] README.md installation section rewritten
- [ ] `docs/manual.md` getting started section updated
- [ ] All scripts have inline comments explaining *why*

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Junction fails without Developer Mode | Medium | `install.ps1` tests capability upfront, provides clear Developer Mode instructions |
| `$PROFILE` doesn't exist | Medium | `install.ps1` creates it with `New-Item -Force` |
| PowerShell execution policy blocks scripts | Medium | Document `powershell -ExecutionPolicy Bypass -File install.ps1`; aliases in `$PROFILE` are functions (not scripts) so they bypass policy |
| Project has existing `.github/` | Medium | `cg-link` detects, warns, backs up to `.github.bak` |
| OneDrive conflicts with junctions | Low | Default install path (`%USERPROFILE%\.compound-gpid`) is typically outside OneDrive sync folders |
| User forgets to restart terminal after install | High | Clear message in `install.ps1` output; also print `. $PROFILE` command they can run immediately |

## Out of Scope

- Cross-platform support (macOS/Linux) — team is Windows-only.
- VS Code extension packaging — deferred to Phase 5 roadmap.
- Automatic update notifications — users notified manually.
- Handling compound-gpid inside OneDrive — recommend against, don't prevent.
- Uninstall script — can be added later if needed.
