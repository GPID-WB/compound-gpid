---
date: 2026-04-28
depth: light
parent-review: .cg-docs/reviews/2026-04-23-autopilot-orchestration-review-3.md
type: verification
findings:
  P1.1: fixed
---

## Review Report

**Review depth**: light (mode:verify — verification pass)
**Prior review**: `2026-04-23-autopilot-orchestration-review-3.md` (16 fixed, 4 skipped)
**Files reviewed**: 12 substantive (`scripts/helpers.ps1`, `scripts/link.ps1`, `scripts/unlink.ps1`, `tests/link.Tests.ps1`, `tests/unlink.Tests.ps1`, `.github/hooks/hello-hook-guard.ps1`, `.github/agents/cg-hello-hook.agent.md`, `.gitignore`, `docs/reference.md`, `docs/review-verify.md`, `docs/workflow.md`, `roadmap.json`)
**Findings**: 1 (P0: 0, P1: 1, P2: 0, P3: 0)

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-code-quality + cg-testing] `tests/link.Tests.ps1:537–560` — guard test passes falsely after `$CG_MANAGED_DIRS` P3.2 refactor.
  **Why**: The test extracted `$ManagedDirs` by regex-scraping `link.ps1` for a literal `@(...)` array. After P3.2, `link.ps1` now contains `$ManagedDirs = $CG_MANAGED_DIRS` — no inline array. The regex returns empty string. `$managedDirs` is empty; `$entries` collapses to `@(".github/copilot-instructions.md")` only. The guard (`Should BeGreaterThan 0`) passes vacuously because `$entries` always has 1 element. All three sync-validation tests pass falsely.
  **Fix**: Re-target extraction at `helpers.ps1` where `$CG_MANAGED_DIRS` is now defined; guard on `$managedDirs` count (not `$entries` count). Applied in fix-triage pass.

---

### ✅ Passed

- **cg-code-quality**: `$CG_MANAGED_DIRS` single-source-of-truth extraction correct; both `link.ps1` and `unlink.ps1` dot-source `helpers.ps1` before referencing `$CG_MANAGED_DIRS`; PowerShell dot-source scoping confirmed correct. `hooks/` correctly absent from the constant. All non-ASCII characters removed from `hello-hook-guard.ps1` — clean ASCII confirmed. No new style or DRY violations.
- **cg-testing**: P3.2 (`$CG_MANAGED_DIRS` extraction), P3.3 (single-representative comment), P3.10 (non-ASCII replacement) all confirmed applied correctly. `model-assignments.Tests.ps1` agent sentinel (14) and stems list (13) are logically consistent with `cg-hello-hook` correctly excluded. `unlink.Tests.ps1` gitignore fixture matches current 4-dir production list. After P1.1 fix: extraction guard correctly checks `$managedDirs` count, not `$entries` count — false-pass eliminated.
