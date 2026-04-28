---
date: 2026-04-24
plan: .cg-docs/plans/2026-04-23-autopilot-orchestration.md
depth: thorough
findings:
  P1.1: fixed
  P1.2: fixed
  P2.1: skipped
  P2.2: skipped
  P2.3: skipped
  P2.4: skipped
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P3.1: fixed
  P3.2: skipped
  P3.3: skipped
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
  P3.7: fixed
  P3.8: fixed
  P3.9: fixed
  P3.10: skipped
---

## Review Report

**Review depth**: thorough (10 agents)
**Files reviewed**: `scripts/link.ps1`, `scripts/unlink.ps1`, `.github/hooks/hello-hook-guard.ps1`, `.github/agents/cg-hello-hook.agent.md`, `tests/model-assignments.Tests.ps1`, `docs/review-verify.md`, `docs/workflow.md`, `docs/reference.md`, `.gitignore`, `roadmap.json`
**Findings**: 20 (P0: 0, P1: 2, P2: 8, P3: 10)

---

### P0 — BLOCKING

None.

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-architecture + cg-adversarial] `hello-hook-guard.ps1:43,52,62,75` — `[IO.File]::WriteAllText` is blocked in Constrained Language Mode (CLM)
  **Why**: All four write operations use a static .NET method call, which CLM (common in managed enterprise environments like World Bank) blocks at runtime. The `catch { <# logging failure #> }` blocks silently swallow the `MethodInvocationException`. The hook still outputs correct block/allow JSON to stdout (cmdlets work in CLM), but writes no files to disk. Result: A1, A2, A3, and A4 all fail to produce evidence — a false-negative Phase 0 result that is indistinguishable from "hooks are not supported in this environment." The PoC cannot validate its purpose in CLM.
  **Fix**: Replace all four `[IO.File]::WriteAllText(...)` calls with `Set-Content -Path ... -Value ... -Encoding UTF8` (a cmdlet — always CLM-safe). The BOM produced by PS5.1 `-Encoding UTF8` is benign for human-readable JSON log files. Optionally add a startup sentinel: `if ($ExecutionContext.SessionState.LanguageMode -ne 'FullLanguage') { Set-Content -Path (Join-Path $logDir 'poc-hook-clm-warning.txt') -Value 'CLM active — logging degraded' }`.

- **[P1.2]** [cg-architecture] `scripts/link.ps1:45` / `scripts/unlink.ps1:19` — `hooks/` unconditionally distributed to all consumers before Phase 0 completes
  **Why**: `$ManagedDirs = @("prompts", "skills", "agents", "instructions", "hooks")` means every consumer running `cg-link` receives a `.github/hooks/` junction containing `hello-hook-guard.ps1` — explicitly marked `TEMPORARY — delete after Phase 0 validation`. Phase 0 hasn't completed yet. While `cg-hello-hook` is `user-invocable: false`, the junction makes the hook script visible in consumers' `.github/` trees and silently installs unvalidated hook infrastructure before the compound-gpid repo itself has confirmed the hooks API behaves as assumed.
  **Fix**: Two options — **(A) minimal**: remove `"hooks"` from `$ManagedDirs` now; Phase 0 testing runs natively in the compound-gpid repo without a junction. Re-add `"hooks"` when Phase 0 passes and `hello-hook-guard.ps1` is deleted. **(B) opt-in**: keep `"hooks"` in `$ManagedDirs` but gate junction creation on a consumer-side flag (e.g., presence of `CG_ENABLE_HOOKS=1` in env or a key in `compound-gpid.local.md`).

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-testing] `tests/link.Tests.ps1` — `hooks/` junction creation and gitignore entry not covered
  **Why**: `$ManagedDirs` now has 5 entries; `link.Tests.ps1` has `It` blocks and gitignore assertions for only 4. If `"hooks"` is accidentally dropped from the production list, no test catches it.
  **Fix**: Add `It "creates a junction for hooks/"` to the junction context and add `.github/hooks/` to the gitignore entry assertions:
  ```powershell
  ($content -match '\.github/hooks/') | Should Be $true
  ($after | Where-Object { $_ -eq '.github/hooks/' } | Measure-Object).Count | Should Be 1
  ```

- **[P2.2]** [cg-testing] `tests/link.Tests.ps1:~209` — gitignore tests encode the old 4-dir entry set
  **Why**: The "creates .gitignore with CG-specific entries", "does not add duplicate entries when run twice", and "does not gitignore .cg-docs/" tests all hardcode the pre-`hooks` entry array. `.github/hooks/` is not asserted in any of them.
  **Fix**: Add `.github/hooks/` to the `$entries` array and the dedup count assertion.

- **[P2.3]** [cg-testing] `tests/unlink.Tests.ps1:~148` — gitignore cleanup test's simulated block is stale
  **Why**: The "removes the CG managed-items block" test constructs a `.gitignore` block matching the old 4-dir state. After `cg-link` writes the updated block (with `hooks/`), the regex under test doesn't exercise the new entry.
  **Fix**: Add `.github/hooks/` to the test fixture block and assert it is absent after removal.

- **[P2.4]** [cg-architecture] `docs/reference.md` — `hooks/` managed directory absent from user-facing documentation
  **Why**: `hooks/` is now a first-class managed directory alongside `prompts/`, `skills/`, `agents/`, `instructions/`, but appears in zero user-facing docs. Consumers receiving `.github/hooks/` have no way to understand what it is or why it exists.
  **Fix**: Add a `hooks/` entry in `docs/reference.md` — e.g.: "Contains PowerShell scripts invoked by the VS Code Copilot agent hooks API (Phase 0 PoC — subject to change after validation)."

- **[P2.5]** [cg-architecture] `cg-hello-hook.agent.md:9` — `-ExecutionPolicy Bypass` sets risky precedent without Phase 1 remediation plan
  **Why**: The hook command bakes in `-ExecutionPolicy Bypass`, which overrides the machine execution policy (`AllSigned`/`RemoteSigned` in enterprise environments like World Bank). This sets a precedent for future hook scripts. May trigger AppLocker blocks or security audit flags.
  **Fix**: Document the Phase 1 remediation path — either (a) code-sign hook scripts, (b) document that consumers must set their policy to `RemoteSigned`, or (c) add a helper for signing. Add as a Phase 1 acceptance criterion.

- **[P2.6]** [cg-adversarial] `hello-hook-guard.ps1:38` — `($input -join "\`n")` blocks indefinitely if VS Code never closes stdin
  **Why**: The `$input` enumerator blocks until the spawning process closes the stdin pipe. If VS Code has a race condition where it writes the payload but delays closing stdin, the hook hangs — permanently blocking the VS Code extension host Stop event with no error output.
  **Fix**: For Phase 1, add a read timeout. For Phase 0, document in the header: *"Script blocks indefinitely if VS Code does not close stdin — acceptable for PoC."*

- **[P2.7]** [cg-adversarial] `hello-hook-guard.ps1:57` — anti-recursion guard uses case-sensitive property name match
  **Why**: `$hookData.PSObject.Properties.Name -contains 'stop_hook_active'` is an exact-case match. If VS Code sends `"Stop_Hook_Active"` or `"stopHookActive"`, the guard never fires and the hook blocks indefinitely on every subsequent invocation. Since the hooks API shape is Assumption 3 (unverified), this is a realistic failure mode.
  **Fix**: Case-fold the key lookup:
  ```powershell
  $key = $hookData.PSObject.Properties.Name | Where-Object { $_ -ieq 'stop_hook_active' } | Select-Object -First 1
  if ($key) { $stopHookActive = $hookData.$key -eq $true }
  ```

- **[P2.8]** [cg-documentation] `docs/review-verify.md` — Missing "When to use" / "When NOT to use" section
  **Why**: Every workflow step documented in `workflow.md` has explicit "When to use" and "When NOT to use" blocks. `review-verify.md` omits both. The distinction between `mode:verify` and `/cg-review light` requires reading the full mechanics section.
  **Fix**: Add a "When to Use" section after "Why This Exists" covering: run after `/cg-fix-triage` to confirm convergence; when P2/P3 suppression anchored to explicit fixed entries is needed. "When NOT to use": as a substitute for `/cg-review light` when no prior review with `fixed` entries exists; when fix-triage touched statistical functions (use standard/thorough instead).

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `hello-hook-guard.ps1` — No comment explaining intentional omission of `Set-StrictMode`/`$ErrorActionPreference = "Stop"`
  **Fix**: Add near the top: `# NOTE: Set-StrictMode and $ErrorActionPreference = "Stop" are intentionally omitted — hook scripts must fail open; a logging error must never prevent Write-Output.`

- **[P3.2]** [cg-code-quality] `$ManagedDirs` duplicated in `link.ps1` and `unlink.ps1`
  **Why**: Two scripts define identical arrays in lockstep; this release already demonstrates the pattern.
  **Fix**: Add `$CG_MANAGED_DIRS = @(...)` to `scripts/helpers.ps1`; dot-source `helpers.ps1` in `unlink.ps1` and reference `$CG_MANAGED_DIRS` in both. Defer if low priority.

- **[P3.3]** [cg-testing] `tests/unlink.Tests.ps1` — No `hooks/` representative in per-subdirectory junction removal tests
  **Fix**: Add one `It` for `hooks/` alongside the existing `prompts/` test, or add a comment noting the single-representative design is intentional.

- **[P3.4]** [cg-version-control] `.gitignore` — `autopilot-runs` pattern ignores only `*.json`
  **Why**: Future non-JSON artifacts (`.log`, `.txt`) would be accidentally tracked.
  **Fix**: Replace `.cg-docs/autopilot-runs/*.json` with `.cg-docs/autopilot-runs/*` + `!.cg-docs/autopilot-runs/.gitkeep`.

- **[P3.5]** [cg-version-control] No tracked cleanup mechanism for temporary PoC files
  **Why**: `hello-hook-guard.ps1` and `cg-hello-hook.agent.md` are marked `TEMPORARY` but no roadmap entry enforces deletion after validation.
  **Fix**: Add a roadmap item: "Delete Phase 0 PoC hook files after A1–A4 confirmation."

- **[P3.6]** [cg-reproducibility] `hello-hook-guard.ps1:61,75` — Output files overwritten each run; asymmetry with timestamped input logs undocumented
  **Fix**: Add to header comment: *"Output files (`poc-hook-output-*.json`) reflect the most recent invocation only — re-running the PoC overwrites them."*

- **[P3.7]** [cg-documentation] `docs/review-verify.md` — "consecutive" inaccurate in output naming table
  **Fix**: Change "Second consecutive verify pass" → "Second verify pass (when `-verify-review.md` already exists)".

- **[P3.8]** [cg-documentation] `docs/review-verify.md` — Mutual exclusivity section omits user-visible warning text
  **Fix**: Add: *"If both are passed, Copilot warns: 'Cannot combine `mode:autofix` and `mode:verify` — using `mode:verify`.'*"

- **[P3.9]** [cg-documentation] `docs/review-verify.md` — See Also links are unclickable plain text
  **Fix**: Reformat `.cg-docs/solutions/` references as relative markdown links from `docs/`:
  ```md
  - [`2026-04-23-verify-mode-suppression...`](../.cg-docs/solutions/testing-patterns/2026-04-23-verify-mode-suppression-must-be-anchored-to-fixed-finding-scope.md)
  ```

- **[P3.10]** [cg-learnings-researcher] `hello-hook-guard.ps1` source file encoding — non-ASCII bytes in comments could corrupt PS5.1 AST
  **Why**: Per `.cg-docs/solutions/bugs/2026-03-23-ps51-utf8-bom-em-dash-corrupts-ast-silently.md`, PS5.1 reads BOM-less UTF-8 as Windows-1252. The hook is a new PS5.1 execution surface.
  **Fix**: Confirm the file is saved as UTF-8 with BOM (VS Code status bar → "UTF-8 with BOM"), or ensure all comments use ASCII-only characters.

---

### ✅ Passed

- **cg-code-quality**: `$stopHookActive` uses correct PS5.1 `PSObject.Properties.Name -contains` idiom; fail-open design ensures `Write-Output` always reached; `[ordered]@{}` ensures deterministic JSON key order; `$ts` captured once for correlatable log filenames ✅
- **cg-data-quality**: `roadmap.json` fully schema-compliant; `.gitignore` `autopilot-runs/*.json` correctly anchored; `ConvertTo-Json` correctly escapes special chars in exception messages ✅
- **cg-documentation**: `docs/workflow.md` and `docs/reference.md` cross-references accurate; `review-verify.md` suppression table and anti-loop protection match implementation ✅
- **cg-learnings-researcher**: Verify mode suppression anchored correctly to `findings:` map; anti-loop `-verify-review.md` exclusion correct; `$input -join` CLM-safe; no unguarded `Get-Content` encoding regressions ✅
- **cg-performance**: No meaningful performance concerns for a PoC invoked ≤2 times per session ✅
- **cg-reproducibility**: `New-Item -Force` correctly idempotent; `link.ps1`/`unlink.ps1` remain idempotent for `hooks/`; no hardcoded absolute paths ✅
- **cg-version-control**: No credentials or secrets in any new file; `autopilot-runs/` runtime artifacts gitignored; `.cg-docs/` institutional knowledge committable ✅
