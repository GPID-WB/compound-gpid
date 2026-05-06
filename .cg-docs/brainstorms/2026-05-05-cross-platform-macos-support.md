---
date: 2026-05-05
title: "Cross-platform macOS support for plugin distribution"
status: decided
scope: "Deep"
chosen-approach: "Parallel Shell Scripts + Unified Pester Tests"
tags: [cross-platform, macos, installation, distribution, ci, bash]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Cross-platform macOS support for plugin distribution

## Context

The plugin was originally built assuming all team members are on Windows (see
`2026-03-03-global-install-and-project-setup.md`). The team now includes Mac
users who need to use the plugin seamlessly. The developer (maintainer) works
on both Windows and Mac and needs confidence that changes made on either
platform work correctly on the other.

Current Windows-only mechanisms:
1. Directory junctions (`New-Item -ItemType Junction`)
2. `.cmd` batch wrappers for PATH commands
3. Windows registry for PATH modification
4. PowerShell scripts (`.ps1`) for all operations

## Requirements

1. **Mac consumers**: Must be able to run `cg-link`, `cg-unlink`, `cg-update`,
   and `install` on macOS with zero dependencies (no Homebrew, no pwsh).
2. **No admin rights for consumers**: Nothing should require elevated privileges
   on macOS. Developer (maintainer) may require admin for their own machine.
3. **Parity guarantee**: A single Pester test suite validates behavior on both
   platforms. Developer runs `pwsh` on macOS for testing.
4. **CI matrix**: GitHub Actions runs tests on both `windows-latest` and
   `macos-latest` to catch platform-specific regressions.
5. **Windows untouched**: Existing `.ps1` scripts and `.cmd` wrappers remain
   unchanged — zero regression risk for current Windows users.
6. **Linux deferred**: Not in scope for this iteration; bash scripts would
   likely work on Linux but it's not tested or documented.
7. **Symlinks on macOS**: Use `ln -s` (no admin needed) as the macOS equivalent
   of Windows directory junctions. VS Code/Positron follows both transparently.
8. **`.gitignore` patterns**: Already work for both junctions and symlinks
   (trailing-slash patterns match regardless of link type). No changes needed.
9. **`copilot-instructions.md` refresh**: Mac `cg-update.sh` must support
   regenerating the copied `copilot-instructions.md` from template.
10. **Shell profile modification**: Mac `install.sh` auto-adds `bin/` to PATH
    via `~/.zshrc` or `~/.zprofile` (user's home directory, no admin needed).

## Approaches Considered

### Approach 1: Parallel Shell Scripts + Unified Pester Tests (CHOSEN)

Add `install.sh`, `link.sh`, `unlink.sh`, `update.sh` in `scripts/` alongside
existing `.ps1` files. Add extensionless bash wrappers in `bin/` alongside
`.cmd` files. Adapt Pester tests to be platform-aware.

- **Pros**: Clean separation, zero Windows regression risk, zero Mac
  dependencies, shared test suite validates parity, CI catches drift.
- **Cons**: Two implementations to maintain (~100 lines each), must keep
  behavior in sync (mitigated by shared tests).
- **Effort**: Medium (3–5 days)

### Approach 2: Unified PowerShell Scripts (pwsh required everywhere)

Refactor `.ps1` scripts to detect `$IsWindows`/`$IsMacOS` and branch
internally. Mac users install `pwsh` via Homebrew.

- **Pros**: Single codebase, no sync drift.
- **Cons**: Requires Homebrew + pwsh for all Mac consumers (violates
  zero-dependency constraint), refactoring risks breaking Windows, still
  needs shell wrappers for Mac PATH.
- **Effort**: Medium

## Decision

Approach 1 — Parallel Shell Scripts + Unified Pester Tests. This respects
the zero-dependency constraint for Mac consumers, keeps Windows stable, and
the shared Pester test suite guarantees behavioral parity across platforms.

## Next Steps

1. Create `scripts/install.sh` — macOS installer (symlink test, PATH setup via
   shell profile, create `bin/` bash wrappers).
2. Create `scripts/link.sh` — create symlinks in `.github/` for managed dirs,
   copy `copilot-instructions.md`, update `.gitignore`.
3. Create `scripts/unlink.sh` — remove symlinks from `.github/`.
4. Create `scripts/update.sh` — git pull, refresh `copilot-instructions.md`.
5. Create `bin/cg-link`, `bin/cg-unlink`, `bin/cg-update` (extensionless bash
   wrappers).
6. Adapt Pester tests to be platform-aware (skip junction-specific assertions
   on macOS, test symlink behavior instead).
7. Add `.github/workflows/tests.yml` with matrix: `[windows-latest, macos-latest]`.
8. Update `docs/installation.md` with macOS instructions.
9. Update charter Key Deliverables to reflect dual-platform support.
