---
date: 2026-07-03
title: "Cross-agent native platform trees require a generator, drift tests, and consistent Python resolution"
category: "environment-issues"
language: "Python/PowerShell/Markdown"
tags: [cross-agent, generator, target-mapping, drift-tests, python-detection, claude-code, codex, opencode]
root-cause: "Distributing Compound GPID to multiple agent platforms (Claude Code, Codex, OpenCode) from a single .github/ source requires a generator that emits platform-native trees, drift tests that catch stale outputs, and consistent Python resolution across Windows/macOS."
severity: "P2"
plan: ".cg-docs/plans/2026-07-03-cross-agent-native-platform-targets.md"
---

# Cross-Agent Native Platform Trees Require Generator, Drift Tests, and Consistent Python Resolution

## Problem

Compound GPID's `.github/` assets were designed for GitHub Copilot. Supporting
Claude Code, Codex, and OpenCode required generating native platform trees
(`.claude/`, `.agents/`, `.opencode/`) from the canonical source, committing
them, and distributing via the existing junction/symlink mechanism — without
requiring maintainers to run Python commands manually.

Three sub-problems emerged:

1. **Distribution maintainability**: How to keep generated trees in sync with
   `.github/` edits without manual regeneration.
2. **Cross-platform Python resolution**: PowerShell scripts calling Python
   directly (`python3`) fail on Windows when only `python` or `py` is available.
3. **Release safety**: How to prevent shipping stale generated trees.

## Root Cause

- Generated trees are a product surface, not optional adapters — they must be
  committed and release-validated.
- `install.ps1` and `bin/*.cmd` launchers already had Python detection logic
  (`python3 → python → py` with Windows Store stub rejection), but PowerShell
  scripts (`update.ps1`, `link.ps1`) called `python3` directly.
- Without drift tests, a maintainer who edits `.github/` but forgets to
  regenerate trees would ship stale outputs silently.

## Solution

### 1. Generator + target-mapping schema

- `.github/shared/target-mapping.json` — platform-generic schema with capability
  flags (`supportsNativeCommands`, `supportsMultiVendorModels`, etc.). OpenCode
  fits as another target, not a special case.
- `scripts/cg_generate_targets.py` — reads `.github/` + target-mapping, emits
  native trees. Role-first model policy: canonical roles (`coding`, `review`,
  `reasoning`, `mechanical`, `inherited`) drive platform-specific model mapping
  (`tier` for Claude, `exact` for Codex, `role-only` for OpenCode).

### 2. Workflow integration (no manual Python)

- **`/cg-commit-push-pr`** Step 1.5: detects `.github/` changes in the diff →
  auto-runs the generator → stages regenerated trees alongside source changes.
  Maintainers never type `python3 scripts/...`.
- **`cg-update`**: runs the generator after `git pull` (defense in depth) so the
  global clone's trees stay current even if a maintainer forgot to commit
  regenerated trees.

### 3. Consistent Python resolution

- Added `Resolve-PythonCommand` to `scripts/helpers.ps1` — probes
  `python3 → python → py` with Windows Store stub rejection, matching
  `install.ps1`'s `Test-PythonCandidate` and `bin/*.cmd`'s `where/for-f/findstr`
  pattern.
- `update.ps1` uses `Resolve-PythonCommand` instead of bare `python3`.

### 4. Drift tests + release gate

- `test_target_drift.py` — runs generator in `--dry-run`, compares manifest
  against committed trees. Fails on stale or orphaned files.
- `test_release_gate_targets.py` — wraps drift + platform tests as a release
  gate.
- `/cg-commit-push-pr` Step 1.5 ensures trees are fresh before push.

## Prevention

- **Never call `python3` directly in PowerShell scripts.** Always use
  `Resolve-PythonCommand` from `helpers.ps1`. It mirrors the detection logic
  in `install.ps1` and `bin/*.cmd` launchers.
- **Always regenerate platform trees when `.github/` changes.** The
  `/cg-commit-push-pr` Step 1.5 does this automatically, but the drift test is
  the safety net.
- **Use capability flags, not platform-specific schema forks.** New platforms
  should fit into `target-mapping.json` as another target with different
  capability flags, not a structural schema change.
- **Role-first model policy.** Canonical roles drive platform catalogs. Exact
  model names are asserted only where the platform supports deterministic
  validation. Multi-vendor platforms (OpenCode, Copilot) use role/tier intent,
  not vendor-specific names.

## Related

- `.github/shared/target-mapping.json` — the platform-generic target schema
- `scripts/cg_generate_targets.py` — the generator
- `scripts/helpers.ps1` — `Resolve-PythonCommand` helper
- `.github/prompts/cg-commit-push-pr.prompt.md` — Step 1.5 auto-regeneration
- `scripts/update.ps1` / `scripts/update.sh` — post-pull regeneration
- `.cg-docs/brainstorms/2026-07-03-cross-agent-native-platform-targets.md` —
  approved brainstorm
- `.cg-docs/plans/2026-07-03-cross-agent-native-platform-targets.md` —
  implementation plan
- `.cg-docs/solutions/environment-issues/2026-06-06-codex-claude-code-cg-prompt-dispatch-adapter.md`
  — prior adapter approach (superseded by generated trees)
- `.cg-docs/solutions/environment-issues/2026-06-23-cross-agent-adapters-are-opt-in-source-packages.md`
  — prior adapter packaging (superseded)
- `.cg-docs/solutions/testing-patterns/2026-08-13-release-gate-fixtures-and-derived-evidence-hashes.md`
  — runtime-faithful release fixtures and derived evidence hash validation
