---
date: 2026-03-03
title: "Global install with automated junction and per-project setup"
status: superseded
language: "both"
estimated-effort: "medium"
tags: [installation, distribution, team-onboarding, windows, junctions, powershell]
---

# Plan: Global Install with Automated Junction and Per-Project Setup

## Objective

Replace the current manual installation process (clone to `C:\tools\`, manually create junctions) with an automated, no-admin-rights workflow: a one-command global install script, a one-command update script, and an enhanced `/cg-setup` prompt that handles per-project junction creation, scaffolding, and context loading.

## Context

- **Current state**: README tells users to clone to `C:\tools\compound-gpid` and manually run `mklink /J`. The `C:\tools\` directory doesn't exist by default, the instructions are error-prone, and there's no update mechanism.
- **Brainstorm decision**: Approach 1 — Global Clone + Automated Junction Script. Clone to `%USERPROFILE%\.compound-gpid`, provide `install.ps1` and `update.ps1` scripts, enhance `/cg-setup` to be a proper prompt (not just a skill).
- **Known issue**: `cg-skill-setup` is a skill, not a prompt, so `/cg-setup` doesn't work as a slash command (documented in `docs/solutions/environment-issues/2026-03-02-skill-vs-prompt-slash-command.md`). This plan addresses that by creating `cg-setup.prompt.md`.
- **Constraint**: All team members are on Windows. No admin rights required.

## Implementation Steps

### 1. Create `install.ps1` (Global Install Script)

- **Files**: Create `install.ps1` in the repo root.
- **Details**:
  - Define `$InstallDir = Join-Path $env:USERPROFILE ".compound-gpid"`.
  - Check if `$InstallDir` already exists:
    - If yes: run `git pull` inside it and report "Updated existing installation."
    - If no: run `git clone https://github.com/GPID-WB/compound-gpid.git "$InstallDir"`.
  - Verify Git is available (`Get-Command git`); if not, print an error with a download link.
  - Verify junction capability: create a temp junction, test it, remove it. If it fails, print a message about enabling Developer Mode.
  - Print a success summary with:
    - Where compound-gpid was installed.
    - How to use it: "Open your project in VS Code, then run `/cg-setup` in Copilot Chat."
    - How to update: "Run `update.ps1` or `git pull` in `%USERPROFILE%\.compound-gpid`."
  - The script must be runnable via: `powershell -ExecutionPolicy Bypass -File install.ps1` (for users who haven't changed their execution policy).
- **Tests**: Manual testing (PowerShell script — no automated test framework). Test scenarios:
  - Fresh install (no `.compound-gpid` exists).
  - Re-run (`.compound-gpid` already exists — should update).
  - No Git installed (should fail gracefully).
  - Junction creation fails (should warn about Developer Mode).
- **Acceptance criteria**:
  - Running `install.ps1` on a clean machine (with Git) clones the repo to `%USERPROFILE%\.compound-gpid`.
  - Running it again performs `git pull` instead of re-cloning.
  - Clear success/error messages in all scenarios.

### 2. Create `update.ps1` (Global Update Script)

- **Files**: Create `update.ps1` in the repo root.
- **Details**:
  - Define `$InstallDir = Join-Path $env:USERPROFILE ".compound-gpid"`.
  - Check if `$InstallDir` exists; if not, print error: "Compound GPID is not installed. Run install.ps1 first."
  - `Push-Location $InstallDir`
  - Capture current commit hash before pull.
  - Run `git pull --ff-only` (fast-forward only to avoid merge conflicts).
  - Capture new commit hash after pull.
  - If hashes differ: print "Updated from <short-old> to <short-new>". Optionally show `git log --oneline` of new commits.
  - If hashes are the same: print "Already up to date."
  - `Pop-Location`
  - Remind user: "All linked projects will see the updates immediately."
- **Tests**: Manual testing. Scenarios:
  - Not installed (should error).
  - Already up to date.
  - New commits available.
- **Acceptance criteria**:
  - Updates the global clone with one command.
  - Shows what changed (or confirms no changes).
  - Never leaves the user in a broken state (fast-forward only).

### 3. Create `cg-setup.prompt.md` (Per-Project Setup Prompt)

- **Files**: Create `.github/prompts/cg-setup.prompt.md`.
- **Details**:
  This prompt replaces the skill-only setup with a proper slash command. It handles two modes:

  **Mode A — New project (no `.github` junction, no `compound-gpid.local.md`)**:
  1. Detect that `.github/` is not a junction to compound-gpid.
  2. Instruct the user to run the junction command in the terminal (the prompt cannot run `mklink /J` itself — it needs to be run in a terminal):
     ```powershell
     # If .github/ exists already, back it up first
     mklink /J ".github" "$env:USERPROFILE\.compound-gpid\.github"
     ```
  3. After junction is created, proceed with the skill-based setup flow:
     - Ask language preference (R, Python, both).
     - Ask project type (package, analysis, dashboard, API, tool).
     - Ask review depth (light, standard, thorough).
     - Create `compound-gpid.local.md`.
     - Scaffold `docs/` directory structure.
     - Add `compound-gpid.local.md` and `.github` to `.gitignore` if not already there.
  4. Print the "Setup Complete" summary with available commands.

  **Mode B — Returning project (`compound-gpid.local.md` exists)**:
  1. Read `compound-gpid.local.md` — report current config.
  2. Scan `docs/brainstorms/` — list existing brainstorms with dates and titles.
  3. Scan `docs/plans/` — list existing plans with dates, titles, and status.
  4. Scan `docs/solutions/` — list existing solutions by category.
  5. Present a summary: "This project is configured for [language], [project-type], [review-depth]. It has X brainstorms, Y plans, and Z captured solutions."
  6. Ask if the user wants to update any configuration.

  **File Permissions** (following the pattern from `docs/solutions/testing-patterns/2026-03-02-prompt-file-permission-guardrails.md`):
  - May read any file in the workspace.
  - May create `compound-gpid.local.md` in the project root.
  - May create new files and directories under `docs/`.
  - May append to `.gitignore`.
  - Must not modify any other existing files.

- **Tests**: Manual testing. Scenarios:
  - New project with no `.github/` — should guide through junction + full setup.
  - New project with existing `.github/` (non-junction) — should warn and guide backup + junction.
  - Returning project — should read and summarize existing context.
  - Update config flow — should rewrite `compound-gpid.local.md`.
- **Acceptance criteria**:
  - `/cg-setup` is available as a slash command in Copilot Chat.
  - New projects get junction guidance + full scaffolding.
  - Returning projects get a context summary.
  - No files are modified that shouldn't be.

### 4. Update `cg-skill-setup/SKILL.md`

- **Files**: Modify `.github/skills/cg-skill-setup/SKILL.md`.
- **Details**:
  - Add a note at the top: "This skill provides reference configuration knowledge. For interactive setup, use the `/cg-setup` prompt."
  - Keep the existing content (it's still consumed as reference by other prompts/agents).
  - Add a new section documenting the junction-based installation model and the `%USERPROFILE%\.compound-gpid` convention.
- **Tests**: Verify the skill is still loadable by other prompts.
- **Acceptance criteria**:
  - Skill documents the junction model.
  - Existing prompts/agents that reference this skill still work.

### 5. Update `README.md`

- **Files**: Modify `README.md`.
- **Details**:
  Replace the current "Installation" section with:

  **Quick Start (3 steps)**:
  1. **Clone**: `git clone https://github.com/GPID-WB/compound-gpid.git "$env:USERPROFILE\.compound-gpid"`
     Or run: `powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.compound-gpid\install.ps1"`
  2. **Link your project**: From your project root:
     ```powershell
     mklink /J ".github" "$env:USERPROFILE\.compound-gpid\.github"
     ```
  3. **Setup**: Open your project in VS Code, run `/cg-setup` in Copilot Chat.

  **Updating**: `git -C "$env:USERPROFILE\.compound-gpid" pull` or run `update.ps1`.

  Also update:
  - Remove references to `C:\tools\`.
  - Update the "Directory Structure" section to reflect that `.github/` is a junction.
  - Add a note that `.github` should be in the project's `.gitignore`.
  - Fix the known issue from `docs/solutions/environment-issues/`: replace `/cg-setup` skill reference with the new prompt reference.

- **Tests**: Read through updated README for consistency.
- **Acceptance criteria**:
  - No reference to `C:\tools\` remains.
  - Install instructions use `%USERPROFILE%\.compound-gpid`.
  - `/cg-setup` is documented as a prompt (slash command).
  - Update workflow is documented.

### 6. Update `docs/manual.md`

- **Files**: Modify `docs/manual.md`.
- **Details**:
  - Update "Getting Started" section to reflect the new install flow.
  - Update any references to `C:\tools\`.
  - Change the setup instruction from "Load the `cg-skill-setup` skill" to "Run `/cg-setup`".
  - Add a section on "Updating Compound GPID" explaining the `git pull` or `update.ps1` flow.
  - Add `/cg-setup` to the Prompts table.
- **Tests**: Read through for consistency.
- **Acceptance criteria**:
  - Manual accurately reflects the new workflow.
  - No stale references to old install method or skill-based setup.

### 7. Update `.gitignore`

- **Files**: Modify `.gitignore` in compound-gpid repo root.
- **Details**:
  - This is the `.gitignore` for the compound-gpid repo itself, not for user projects.
  - Verify it doesn't ignore `install.ps1` or `update.ps1`.
  - No changes likely needed here, but verify.
- **Acceptance criteria**: New scripts are tracked by Git.

## Testing Strategy

This is primarily a scripting + documentation change. Testing is manual:

1. **Fresh install test**: On a machine without `.compound-gpid`, run `install.ps1`. Verify clone succeeds.
2. **Re-install test**: Run `install.ps1` again. Verify it updates instead of failing.
3. **Junction test**: In a new empty project folder, run `mklink /J ".github" "$env:USERPROFILE\.compound-gpid\.github"`. Verify `.github/prompts/`, `.github/agents/`, `.github/skills/` are visible.
4. **Copilot test**: Open the project in VS Code. Verify `/cg-setup` appears in Copilot Chat autocomplete. Run it, verify it creates `compound-gpid.local.md` and `docs/` folders.
5. **Update test**: Make a trivial change in compound-gpid, commit/push. On another machine (or after resetting), run `update.ps1`. Verify the change is visible in linked projects.
6. **Returning project test**: Open a project that already has `compound-gpid.local.md` and `docs/` with content. Run `/cg-setup`. Verify it reads and summarizes existing context.

## Documentation Checklist

- [ ] `install.ps1` has a comment header explaining what it does
- [ ] `update.ps1` has a comment header explaining what it does
- [ ] `cg-setup.prompt.md` has proper file permissions section
- [ ] README.md installation section is rewritten
- [ ] `docs/manual.md` getting started section is updated
- [ ] Inline comments in scripts explain *why*, not just *what*

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Junction creation fails without Developer Mode | Medium | `install.ps1` tests junction capability and provides clear instructions to enable Developer Mode |
| Project already has `.github/` with its own content | Medium | `/cg-setup` detects this, instructs user to back up, explains the trade-off |
| OneDrive conflicts with junctions | Low | Document known issue; junctions to local paths work fine, but if compound-gpid is inside OneDrive, syncing may behave unexpectedly. Recommend cloning to a non-OneDrive path (default `%USERPROFILE%` is usually outside OneDrive) |
| Git execution policy blocks `install.ps1` | Medium | Document the `powershell -ExecutionPolicy Bypass -File install.ps1` workaround |
| User forgets to add `.github` to project `.gitignore` | Medium | `/cg-setup` prompt handles this automatically |

## Out of Scope

- Cross-platform support (macOS/Linux) — team is Windows-only.
- VS Code extension packaging — deferred to Phase 5 roadmap.
- Multi-root workspace fallback — kept as documented alternative but not implemented now.
- Automatic update notifications — users are notified manually and run `update.ps1`.
- Handling compound-gpid repo cloned inside OneDrive — recommend against it, but don't prevent it.
