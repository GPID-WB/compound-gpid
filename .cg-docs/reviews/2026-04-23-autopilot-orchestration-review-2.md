---
date: 2026-04-24
plan: .cg-docs/plans/2026-04-23-autopilot-orchestration.md
depth: standard
findings:
  P1.1: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: skipped
  P2.8: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
  P3.7: skipped
---

## Review Report

**Review depth**: standard (auto-escalated from `light`: `scripts/link.ps1` in `scripts/` → added `@cg-data-quality`; ≥ 50 non-test new lines → escalated to standard)
**Files reviewed**: 7 code/config files, 5 doc artifacts
**Findings**: 16 (P0: 0, P1: 1, P2: 8, P3: 7)

### P0 — BLOCKING

None.

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-architecture] `scripts/unlink.ps1:19` — `$ManagedDirs` missing `"hooks"` while `link.ps1` has it
  **Why**: `cg-link` creates a `.github/hooks/` junction; `cg-unlink` does not remove it (it only iterates its own `$ManagedDirs`). This leaves a dangling junction silently corrupting consumer project `.github/` layouts.
  **Fix**: `$ManagedDirs = @("prompts", "skills", "agents", "instructions", "hooks")` in `scripts/unlink.ps1:19`.

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `hello-hook-guard.ps1:55–58` — parse error catch discards exception details
  **Why**: Error log writes only `{ "error": "malformed stdin JSON" }` — the reason is lost. This is the primary A2 diagnostic artifact; missing details makes debugging hook payload failures harder.
  **Fix**: `@{ error = "malformed stdin JSON"; details = $_.Exception.Message }`

- **[P2.2]** [cg-code-quality] `hello-hook-guard.ps1:80–87` — `ConvertTo-Json` without `-Compress` emits multi-line JSON
  **Why**: PS5.1 default produces pretty-printed output. If VS Code parses hook stdout line-by-line, the block response silently fails — while `$allowOutput = "{}"` passes. This asymmetry would make A3 produce a false negative result.
  **Fix**: `} | ConvertTo-Json -Depth 2 -Compress`

- **[P2.3]** [cg-testing] `hello-hook-guard.ps1:15` — A1 validation criterion references stale filename
  **Why**: Header comment states `A1: poc-hook-input.json exists` but actual filename is `poc-hook-input-<timestamp>.json`. A validator following A1 literally looks for a file that never exists.
  **Fix**: Update to: `A1: poc-hook-input-<timestamp>.json exists in autopilot-runs/`

- **[P2.4]** [cg-reproducibility] `hello-hook-guard.ps1:44,53` — `Set-Content -Encoding UTF8` writes BOM in PS5.1
  **Why**: PS5.1's `-Encoding UTF8` prepends a 3-byte BOM (`EF BB BF`). Any downstream tool reading the JSON log files (Python `json.load`, `ConvertFrom-Json` in some environments) may fail or silently mangle results.
  **Fix**: Replace both `Set-Content` calls with `[IO.File]::WriteAllText($path, $content, [Text.Encoding]::UTF8)`.

- **[P2.5]** [cg-reproducibility] `hello-hook-guard.ps1` — two independent `Get-Date` calls create non-correlatable log filenames
  **Why**: On the parse-error path, `poc-hook-input-<t1>.json` and `poc-hook-input-error-<t2>.json` get different millisecond timestamps and can't be matched against each other.
  **Fix**: Capture once after `$logDir`: `$ts = Get-Date -Format 'yyyyMMdd-HHmmss-fff'`, then use `$ts` in all filenames.

- **[P2.6]** [cg-documentation] `scripts/link.ps1:4` — header comment still lists only 4 managed directories
  **Why**: Comment reads `(prompts/, skills/, agents/, instructions/)` — `hooks/` was added to `$ManagedDirs` but not to the header. Stale docs mislead readers about what `cg-link` manages.
  **Fix**: Update to `(prompts/, skills/, agents/, instructions/, hooks/)`.

- **[P2.7]** [cg-version-control] `.cg-docs/` knowledge files are entirely untracked — not staged
  **Why**: `.cg-docs/brainstorms/2026-04-23-autopilot-orchestration.md`, `.cg-docs/plans/2026-04-23-autopilot-orchestration.md`, `.cg-docs/reviews/2026-04-23-autopilot-orchestration-review.md`, `.cg-docs/autopilot-runs/.gitkeep`, and the three `competitive-reviews/2026-04-23-*.md` files are all untracked. Per project convention, `.cg-docs/` is fully version-controlled institutional knowledge.
  **Fix**: `git add .cg-docs/`

- **[P2.8]** [cg-data-quality] `hello-hook-guard.ps1:77–83` — `hookSpecificOutput` block response schema is Assumption 3 (unverified)
  **Why**: The exact JSON structure (`hookSpecificOutput.decision = "block"`) is cited in the plan as an unconfirmed assumption. If VS Code expects a different shape, A3 fails silently — the hook outputs JSON but VS Code allows the stop anyway, producing a false negative PoC result with no error.
  **Fix**: Add inline comment: `# Assumption 3: hookSpecificOutput.decision=block schema — verify if A3 fails`. No code change needed unless A3 fails.

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `cg-hello-hook.agent.md:8` — `windows:` hook key is likely unrecognized by VS Code
  **Why**: `windows:` is not a documented VS Code Copilot hook frontmatter field. Forward-slash paths work on Windows PowerShell. If VS Code rejects unknown hook keys, this could silently break hook registration.
  **Fix**: Remove the `windows:` line; keep only `command: "powershell -ExecutionPolicy Bypass -File .github/hooks/hello-hook-guard.ps1"`.

- **[P3.2]** [cg-code-quality] `tests/model-assignments.Tests.ps1:120` — `$agentStems` comment doesn't explain intentional 13/14 divergence
  **Why**: The discovery sentinel says 14 but the guide-sync list has 13 (correctly excludes the temporary agent). The comment says "All 13 agent file stems" without explaining why. Future readers may add `cg-hello-hook` to the guide unnecessarily.
  **Fix**: Change to: `# 13 permanent agents -- cg-hello-hook is intentionally excluded (TEMPORARY PoC)`

- **[P3.3]** [cg-documentation] `hello-hook-guard.ps1` — `P2.x` inline comment convention is unexplained
  **Why**: Notes use `# P2.2:`, `# P2.3:`, `# P2.1:`, `# P2.6:` with no definition. Readers can't tell if these are priority codes, phase-2 issue numbers, or review finding references.
  **Fix**: Add near the first occurrence: `# P2.x: inline notes reference Phase 2 follow-up items tracked in the plan`

- **[P3.4]** [cg-performance] `hello-hook-guard.ps1:35–37` — `Test-Path` + `New-Item -Force` is redundant
  **Why**: `New-Item -ItemType Directory -Force` is idempotent and silently succeeds if the directory exists. The preceding `Test-Path` guard is a redundant filesystem stat.
  **Fix**: Remove the `if (-not (Test-Path ...))` guard; use `New-Item -ItemType Directory -Path $logDir -Force | Out-Null` directly.

- **[P3.5]** [cg-data-quality] `hello-hook-guard.ps1:57` — empty-payload fail-open behavior undocumented
  **Why**: When `$rawInput` is empty (no stdin), the script falls through to the block path. Intentional for A3/A4 but looks like a bug to future readers.
  **Fix**: Add comment: `# Empty payload treated as first-stop (block) — intentional fail-open`

- **[P3.6]** [cg-data-quality] `hello-hook-guard.ps1:80` — `ConvertTo-Json -Depth 3` overstates nesting level
  **Why**: The block response has depth 2 (`hookSpecificOutput` → fields). `-Depth 3` is harmless but incorrect.
  **Fix**: Use `-Depth 2` (already included in P2.2 fix above — address together).

- **[P3.7]** [cg-architecture] `hooks/` is now unconditionally linked for all consumer projects
  **Why**: Every `cg-link` consumer gets `.github/hooks/` even without autopilot intent. Acceptable for Phase 0 PoC since hooks are agent-scoped (only fire for `@cg-hello-hook`). Phase 1 should consider an opt-in.
  **Fix**: No change now. Add to Phase 1 decision checkpoint in plan: consider `cg-link --enable-autopilot` or a `compound-gpid.local.md` opt-in key.

### ✅ Passed

- cg-code-quality: `roadmap.json`, `repos.json`, `.gitignore`, test sentinel structure — valid JSON/schema, no DRY violations
- cg-testing: Sentinel revert comment is unambiguous; no Pester tests needed for PoC hook (API-contract unknowns can't be unit-tested in isolation)
- cg-documentation: Agent frontmatter (`user-invocable: false`, deletion markers, A1–A4 cross-referencing) sufficient for independent validation
- cg-version-control: No credentials, tokens, or sensitive data; `.gitignore` scope correct
- cg-reproducibility: No hardcoded absolute paths; `$PSScriptRoot`-based path correct for compound-gpid repo context
- cg-performance: No blocking performance concerns for a PoC invoked 1–2 times
- cg-data-quality: `repos.json` dates valid ISO 8601; `roadmap.json` schema-compliant; `stop_hook_active` boolean check (`-eq $true`) correctly robust against `null`, string `"true"`, and missing field
