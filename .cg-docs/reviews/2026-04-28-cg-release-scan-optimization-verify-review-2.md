---
date: 2026-04-28
depth: light
parent-review: .cg-docs/reviews/2026-04-28-cg-release-scan-optimization-review.md
type: verification
findings:
  P3.1: open
  P3.2: open
---

## Review Report

**Review depth**: light (mode:verify)
**Files reviewed**: 4 (`cg-release.prompt.md`, `.github/agents/cg-release-scanner.agent.md`, `docs/reference.md`, `tests/prompt-tools.Tests.ps1`)
**Findings**: 2 (P0: 0, P1: 0, P2: 0, P3: 2)

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No regression test for `window-days`/`tag-date` hyphen fix in agent
  **Why**: The P3.3(v) fix changed `max(today - window_days, tag_date)` → `max(today - window-days, tag-date)` in `.github/agents/cg-release-scanner.agent.md` line 20. No test guards this spelling — a regression to underscores would pass silently.
  **Fix**: Add to the `cg-release-scanner.agent.md - existence and structure` Describe block (where `$agentContent` is already defined):
  ```powershell
  It "uses window-days (hyphen, not underscore) in window-start description" {
      ($agentContent -match 'window-days') | Should Be $true
  }
  It "uses tag-date (hyphen, not underscore) in window-start description" {
      ($agentContent -match 'tag-date') | Should Be $true
  }
  ```

- **[P3.2]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No regression test for `User-invocable` table header spelling fix
  **Why**: The P3.4(v) fix changed column header `User-invokable` → `User-invocable` in the Release Scanner Agent and Roadmap Agent tables of `docs/reference.md`. The only reference.md test for the scanner checks `cg-release-scanner` presence, not the header spelling. A regression back to `User-invokable` would pass silently.
  **Fix**: Add to the `docs/reference.md - R skills and r-syntax config` Describe block (where `$content` refers to `reference.md`):
  ```powershell
  It "column header uses User-invocable (not User-invokable)" {
      ($content -match 'User-invocable') | Should Be $true
  }
  ```

---

### ✅ Passed

- **cg-code-quality**: All 4 changes verified correct and internally consistent. ✓
  - 8 new test assertion patterns all match actual target file content ✓
  - `window-days`/`tag-date` formula consistent across agent and prompt ✓
  - `User-invocable` uniformly applied in all 4 agent table headers in `docs/reference.md` ✓
  - Removed naming note leaves no orphaned references in `cg-release.prompt.md` ✓
- **Prior verify-review findings** (P2.1–P2.6, P3.1–P3.5): All confirmed converged ✓
- **3 prose occurrences of `user-invokable`** on lines 139, 198, 208 of `docs/reference.md` (in descriptive sentences, not table headers) — consistent with the fix being scoped to table headers only; no action required ✓
- No P0/P1 issues found — the full fix chain has converged ✓
