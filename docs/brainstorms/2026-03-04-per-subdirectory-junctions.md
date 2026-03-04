---
date: 2026-03-04
title: "Per-subdirectory junctions to preserve existing .github content"
status: decided
chosen-approach: "Junctions + Copied File with Marker (Pragmatic)"
tags: [install, link, .github, junctions, windows]
---

# Per-Subdirectory Junctions to Preserve Existing .github Content

## Context

When a user runs `cg-link` in a project that already has a `.github/` folder (containing GitHub Actions workflows, issue/PR templates, CODEOWNERS, FUNDING.yml, etc.), the current implementation replaces the entire directory with a junction to the shared compound-gpid `.github/`. The user's existing content is moved to `.github.bak`, which effectively hides it from GitHub and other tools that depend on `.github/`.

This is a real problem because `.github/` is a special directory used by GitHub for workflows, templates, and configuration. Replacing it wholesale breaks those features.

## Requirements

1. **Preserve existing `.github/` content** — workflows, templates, CODEOWNERS, and any other user files must remain untouched.
2. **Compound GPID subdirectories must be visible** inside `.github/` — `prompts/`, `skills/`, `agents/`, `instructions/`, and `copilot-instructions.md` must be accessible at `.github/` for VS Code/Copilot to find them.
3. **No `.github.bak`** — stop creating backup directories; the problem should not exist.
4. **Protection against accidental edits** — since junctions are transparent, edits through them modify the shared global source. Use git-based protection (the global clone is a git repo) plus a warning message during `cg-link`.
5. **`cg-update` resets and refreshes** — runs `git checkout . && git pull` in the global clone to discard accidental changes and fetch the latest version.
6. **`cg-link` runs `cg-update` first** — ensures the global clone is up-to-date before linking (pull done in `$env:USERPROFILE\.compound-gpid`, not the project directory).
7. **Marker-based management of `copilot-instructions.md`** — a marker comment (`<!-- compound-gpid:managed -->`) at the top of the file controls whether `cg-update` replaces it:
   - Marker present → `cg-update` replaces with the latest version.
   - Marker absent/modified → `cg-update` skips, allowing user customization.
   - `cg-unlink` only deletes the file if the marker is present.
8. **Three commands only**: `cg-link`, `cg-unlink`, `cg-update`.

## Approaches Considered

### Approach 1: Junctions + File Symlink (Simple)

Create directory junctions for each subdirectory and a file symlink for `copilot-instructions.md`.

**Pros:**
- Simplest implementation
- All links are live — changes in the global clone are instantly visible
- No extra metadata files

**Cons:**
- File symlinks on Windows require Developer Mode or admin — some older Win10 configurations handle them differently than directory junctions
- `cg-unlink` must iterate and inspect each item
- New subdirectories added upstream require re-running `cg-link`

**Effort:** Small
**Recommended:** No — file symlink adds potential friction on Windows.

### Approach 2: Junctions + Copied File with Marker (Pragmatic)

Directory junctions for subdirectories (`prompts/`, `skills/`, `agents/`, `instructions/`), but **copy** `copilot-instructions.md` with a marker comment so it's identifiable and replaceable.

**Behavior matrix for `copilot-instructions.md`:**

| Scenario | Marker present? | `cg-update` action |
|---|---|---|
| Fresh copy from `cg-link` | Yes | Replaces with latest |
| User edits content, keeps marker | Yes | Replaces with latest |
| User removes/changes marker | No | Skips (user-managed) |
| File doesn't exist | N/A | Copies fresh with marker |

**Pros:**
- Avoids file symlink issues on Windows entirely
- Marker makes management unambiguous
- Works on all Windows configurations that support junctions
- User can opt out by removing the marker to take ownership of the file

**Cons:**
- `copilot-instructions.md` is a copy, not live — requires `cg-update` to refresh
- Slightly more logic in `cg-update` (must re-copy the file)
- Marker relies on the user not accidentally removing the comment

**Effort:** Small
**Recommended:** Yes

### Approach 3: Junctions + Manifest File (Future-Proof)

Same as Approach 2, but adds a `.github/.cg-manifest` file listing all managed entries.

**Pros:**
- Explicit tracking — `cg-unlink` is perfectly reliable
- Future-proof for new subdirectories or files

**Cons:**
- Extra file in `.github/`
- Over-engineered for 5 managed items
- Can be added later if needed

**Effort:** Medium
**Recommended:** No

## Decision

**Approach 2: Junctions + Copied File with Marker** was chosen. It is the pragmatic sweet spot:

- Directory junctions for `prompts/`, `skills/`, `agents/`, `instructions/` — live, transparent, no copy needed.
- Copied `copilot-instructions.md` with `<!-- compound-gpid:managed -->` marker — avoids Windows file symlink issues, gives users a clean opt-out mechanism.
- Git-based protection for the global clone — `cg-update` runs `git checkout . && git pull`.
- Warning message during `cg-link` reminding users not to edit managed directories.
- `cg-link` calls `cg-update` first to ensure freshness.

## Next Steps

1. **Modify `scripts/link.ps1`**: Replace whole-directory junction with per-subdirectory junctions + copied `copilot-instructions.md` with marker.
2. **Modify `scripts/unlink.ps1`**: Remove individual junctions and marker-tagged `copilot-instructions.md` instead of removing a single junction. Offer to leave user-managed `copilot-instructions.md`.
3. **Modify `scripts/update.ps1`**: Add `git checkout .` before `git pull`. After pulling, re-copy `copilot-instructions.md` in any linked projects (or just in the global clone — linked projects get junction updates automatically).
4. **Modify `install.ps1`**: No backup logic changes needed (backup was in `link.ps1`).
5. **Update tests**: Adapt `link.Tests.ps1` and `update.Tests.ps1` for per-subdirectory behavior.
6. **Update `README.md`**: Reflect new behavior (no more `.github.bak`, per-subdirectory linking).
7. **Remove `.github.bak` references** from `.gitignore` additions in `link.ps1`.
