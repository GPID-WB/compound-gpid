---
date: 2026-03-03
title: "Global install with automated junction and per-project setup"
status: decided
chosen-approach: "Global Clone + Automated Junction Script"
tags: [installation, distribution, team-onboarding, windows, junctions]
---

# Global Install and Per-Project Setup

## Context

The current installation instructions require cloning to `C:\tools\compound-gpid` (a folder that doesn't exist by default) and manually creating a directory junction per project. This is error-prone and hard to maintain across a team. The team needs:

1. **Easy install**: One-time setup on each team member's machine.
2. **Easy updates**: `git pull` once and all projects see changes immediately.
3. **Minimal per-project setup**: A single `/cg-setup` command to initialize a project or contextualize Copilot for an existing one.
4. **No admin rights**: Must work without elevated privileges.
5. **Windows-only**: All team members are on Windows.

Additionally, when a user opens a project that already uses compound-gpid, Copilot should be contextualized with everything done so far (existing brainstorms, plans, solutions, and config).

## Requirements

- All team members are on Windows.
- No admin rights required (Developer Mode or standard user junctions).
- Global install: clone once, available across all projects.
- Per-project init via `/cg-setup` prompt:
  - New project: creates `compound-gpid.local.md`, scaffolds `docs/` folders, creates `.github` junction.
  - Existing project: reads existing config and `docs/` to contextualize Copilot.
- Updates: `git pull` in the global clone propagates instantly to all linked projects.
- Team members should be able to follow clear instructions to run a PowerShell script.

## Approaches Considered

### Approach 1: Global Clone + Automated Junction Script (Chosen)

Clone once to `%USERPROFILE%\.compound-gpid`. Provide:
- `install.ps1` — one-time global setup (clones repo, verifies junction capability).
- Enhanced `/cg-setup` prompt — detects junction, creates it if missing, scaffolds project, reads existing context.
- `update.ps1` — convenience script to `git pull` the global clone.

**Pros**:
- Junctions are instant, zero-copy, no admin rights needed (Developer Mode).
- Updates propagate to all projects simultaneously — no per-project update step.
- Simple mental model: "install once, init per project, update globally."
- No new infrastructure (junctions are native Windows).

**Cons**:
- Requires a lightweight per-project init (one command via `/cg-setup`).
- If `.github/` already exists in a project, needs careful merging/conflict handling.
- Junction makes `.github/` shared — the project can't have its own `.github/` content alongside compound-gpid's content (unless compound-gpid absorbs it).

**Effort**: Small

### Approach 2: Multi-Root Workspace (Fallback)

Add `compound-gpid` as a second folder in each VS Code workspace. Copilot picks up prompts/agents/skills from the second folder.

**Pros**:
- No junctions or filesystem tricks.
- Project's own `.github/` is unaffected.
- Clean separation of plugin vs project files.

**Cons**:
- Multi-root workspaces have UX quirks.
- Uncertain whether Copilot discovers `.github/prompts/` from a second workspace folder — could be a dealbreaker.
- Requires `.code-workspace` files.
- Search results show compound-gpid internals (noise).

**Effort**: Small (if Copilot supports it) / infeasible (if it doesn't)

### Approach 3: VS Code Extension

Package as a proper VS Code extension with marketplace distribution.

**Pros**:
- Truly global, built-in update mechanism, most polished UX.

**Cons**:
- Large effort, evolving APIs, overkill for a small team.

**Effort**: Large

## Decision

**Approach 1: Global Clone + Automated Junction Script** was chosen for its simplicity, reliability, and zero-cost update propagation. Approach 2 is the fallback if junctions prove problematic.

## Next Steps

1. Create `install.ps1` script that:
   - Clones repo to `%USERPROFILE%\.compound-gpid` (or pulls if already exists).
   - Verifies junction capability.
   - Prints success message with next steps.

2. Create `update.ps1` script that:
   - Runs `git pull` in `%USERPROFILE%\.compound-gpid`.
   - Reports what changed.

3. Enhance `/cg-setup` prompt to:
   - Detect whether `.github/` junction exists; create it if not.
   - Handle existing `.github/` folder conflicts gracefully.
   - Scaffold `docs/` folders for new projects.
   - Create `compound-gpid.local.md` for new projects (interactive config).
   - Read existing `compound-gpid.local.md` and `docs/` for returning projects to contextualize Copilot.

4. Update `README.md` with new installation instructions (but do NOT modify in this brainstorm—defer to `/cg-plan`).

5. Add `.github` to the project-level `.gitignore` template (since it's a junction to an external repo).
