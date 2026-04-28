---
date: 2026-04-24
depth: light
parent-review: .cg-docs/reviews/2026-04-23-autopilot-orchestration-review.md
type: verification
findings:
  P1.1: fixed
  P2.1: fixed
  P2.2: fixed
  P3.1: fixed
  P3.2: fixed
---

## Review Report

**Review depth**: light (mode:verify — forced)
**Files reviewed**: `.github/hooks/hello-hook-guard.ps1`, `.github/agents/cg-hello-hook.agent.md`, `scripts/link.ps1`, `scripts/unlink.ps1`, `tests/model-assignments.Tests.ps1`, `.gitignore`
**Findings**: 5 (P0: 0, P1: 1, P2: 2, P3: 2)

### P0 — BLOCKING

None.

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-code-quality] `scripts/unlink.ps1:19` — cross-file breakage from P1.5 fix: `$ManagedDirs` missing `"hooks"`
  **Why**: `link.ps1` (P1.5 fix) now manages `"hooks"` but `unlink.ps1` still has `@("prompts", "skills", "agents", "instructions")`. Running `cg-unlink` leaves a dangling `.github/hooks/` junction in every consumer project. This is a genuine new issue introduced by the P1.5 fix.
  **Fix**: `$ManagedDirs = @("prompts", "skills", "agents", "instructions", "hooks")` in `scripts/unlink.ps1:19`.

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `hello-hook-guard.ps1:21` — A1 criterion still references old non-timestamped filename
  **Why**: Comment reads `A1: poc-hook-input.json exists` but the actual file written is `poc-hook-input-<timestamp>.json` (per P1.3 fix). A PoC validator following A1 literally would look for a file that never exists.
  **Fix**: Update to: `A1: poc-hook-input-<timestamp>.json exists  → hook fires at all`

- **[P2.2]** [cg-code-quality] `hello-hook-guard.ps1:80–87` — `ConvertTo-Json -Depth 3` without `-Compress` emits multi-line JSON
  **Why**: `Write-Output $blockResponse` emits pretty-printed multi-line output. Hook APIs typically parse stdout as a single JSON object; multi-line output risks a parse failure or silent ignore. The allow response correctly uses `"{}"` (single-line). This asymmetry could make A3 produce a false negative with no visible error.
  **Fix**: `} | ConvertTo-Json -Depth 3 -Compress`

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `hello-hook-guard.ps1:55` — catch block discards `$_.Exception.Message`
  **Why**: Error log always writes `{ "error": "malformed stdin JSON" }` without the actual parse error. Makes A2 diagnostics harder when the payload is genuinely malformed.
  **Fix**: `@{ error = "malformed stdin JSON"; detail = $_.Exception.Message }`

- **[P3.2]** [cg-testing] `tests/model-assignments.Tests.ps1:120` — `$agentStems` comment says "All 13 agent file stems" without explaining 13/14 divergence
  **Why**: P3.2's fix updated the sentinel comment but left the `$agentStems` comment unchanged. A developer sees sentinel=14, stems comment=13, no explanation.
  **Fix**: Change to `# All 13 permanent agent file stems must appear in the guide` + `# (cg-hello-hook is excluded -- temporary PoC, not added to model-guide.md)`

### ✅ Passed

- cg-code-quality: All 20 prior fixed findings correctly applied; all try/catch guards in place; CLM-safe `$input` pattern confirmed; `user-invocable: false` confirmed; gitignore pattern correct; timestamped filenames working
- cg-testing: Sentinel/stems list logically consistent (14 files, 13 in guide-sync — correctly excludes PoC); no test correctness regressions; timestamped filename edge cases clean
