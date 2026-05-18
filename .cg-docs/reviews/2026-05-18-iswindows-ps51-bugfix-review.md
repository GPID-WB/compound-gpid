---
plan: null
date: 2026-05-18
depth: thorough
mode: autofix
files-reviewed:
  - scripts/link.ps1
  - scripts/unlink.ps1
  - tests/ps51-compat.Tests.ps1
  - tests/link.Tests.ps1
  - tests/unlink.Tests.ps1
findings:
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
  P3.7: skipped
---

## Review Report

**Review depth**: thorough (mode:autofix)
**Files reviewed**: 5
**Findings**: 13 (P0: 0, P1: 0, P2: 6, P3: 7)
**Safe-auto applied**: P2.1, P2.2, P2.5 (+ bonus: 2 stale .cg-docs solution files updated)

---

### P0 — BLOCKING
_None._

### P1 — CRITICAL
_None._

### P2 — IMPORTANT

- **[P2.1]** [cg-documentation] `tests/ps51-compat.Tests.ps1:87-88` — `[safe_auto]` `[fixed]` "Use:" pattern in comment block omits the `$env:OS` fallback
  **Why**: A maintainer copying `(Test-Path variable:IsWindows) -and $IsWindows` verbatim gets an expression that always returns `$false` on PS 5.1 Windows. The fallback `$env:OS -eq "Windows_NT"` is the critical second arm.
  **Fix applied**: Extended the "Use:" snippet to the full canonical expression and added an explanatory line.

- **[P2.2]** [cg-documentation] `tests/link.Tests.ps1:550`, `tests/unlink.Tests.ps1:240` — `[safe_auto]` `[fixed]` "Fix:" snippet in test comments shows only half the expression
  **Why**: Same copy-paste hazard as P2.1 — omitting `$env:OS` arm would create a broken production guard.
  **Fix applied**: Updated both "Fix:" comments to show the full expression.

- **[P2.3]** [cg-adversarial] `tests/ps51-compat.Tests.ps1:103` — `[manual]` Scanner suppressed by inline comment containing guard phrase
  **Why**: A line like `$x = $IsWindows # nb: Test-Path variable:IsWindows` passes the `$line -notmatch 'Test-Path\s+variable:IsWindows'` check because the guard phrase appears in the trailing comment. The violation is silently suppressed even though the code fragment crashes PS 5.1.
  **Fix**: Strip inline comments before the guard check:
  ```powershell
  $codePart = ($line -replace '#.*$', '').Trim()
  if ($codePart -match '\$IsWindows' -and
      $codePart -notmatch 'Test-Path\s+variable:IsWindows' -and
      $line -notmatch '^\s*#') { ... }
  ```

- **[P2.4]** [cg-adversarial] `tests/ps51-compat.Tests.ps1:101` — `[manual]` `${IsWindows}` brace syntax not matched by `\$IsWindows` regex
  **Why**: `${IsWindows}` is valid PowerShell, equivalent to `$IsWindows`, but `'${IsWindows}' -match '\$IsWindows'` returns `$false`. A script using `${IsWindows}` under `Set-StrictMode` would crash PS 5.1 and pass the scanner undetected.
  **Fix**: Broaden the detection pattern:
  ```powershell
  if (($line -match '\$IsWindows|\$\{IsWindows\}') -and ...)
  ```

- **[P2.5]** [cg-architecture] `tests/link.Tests.ps1:7`, `tests/unlink.Tests.ps1:7`, `tests/bash-scripts.Tests.ps1:9`, `tests/install.Tests.ps1:7` — `[safe_auto]` `[fixed]` Misleading "PS 5.1-safe" comment on bare `$IsWindows` access
  **Why**: Four test files labeled their bare `$IsWindows` access as "PS 5.1-safe", which is true only because Pester doesn't set `Set-StrictMode`. A developer reading the comment and copying the pattern into a production script (where `Set-StrictMode -Version Latest` IS set) would reintroduce the exact bug just fixed.
  **Fix applied**: Updated all four to `# PS 5.1 compatible: no Set-StrictMode here, so $IsWindows returns $null rather than throwing`.

- **[P2.6]** [cg-testing] `tests/ps51-compat.Tests.ps1:97` — `[manual]` Silent pass when production script file is missing
  **Why**: `if (-not (Test-Path $filePath)) { return }` inside an `It` block causes Pester 4 to record a **pass** when a file is absent. If a production script is renamed or deleted without updating `$productionScripts`, the scanner is silently disabled for that entry. This pattern appears in all three `Describe` blocks in `ps51-compat.Tests.ps1`.
  **Fix**: Replace with a `Should -Exist` assertion before the scan loop, or emit a warning and keep the return for CI tolerance. Minimal change:
  ```powershell
  if (-not (Test-Path $filePath)) {
      Write-Warning "Expected production script not found: $filePath"
      return
  }
  ```
  Or tighter: `$filePath | Should -Exist`.

---

### P3 — MINOR

- **[P3.1]** [cg-code-quality] [cg-adversarial] `scripts/link.ps1:39`, `scripts/unlink.ps1:24` — `[advisory]` Implicit operator precedence; inner grouping not explicit
  **Why**: The fix is logically correct (`-and` > `-or`), but a future developer who regroups as `A -and (B -or C)` would produce wrong results on PS 5.1 Windows with a misleading error message.
  **Fix** (optional): `((Test-Path variable:IsWindows) -and $IsWindows) -or ($env:OS -eq "Windows_NT")` — parentheses make structure self-documenting.

- **[P3.2]** [cg-code-quality] `tests/ps51-compat.Tests.ps1:104` — `[advisory]` Per-line check constrains valid multi-line guard patterns
  **Why**: A syntactically valid multi-line guard (e.g., `if (Test-Path variable:IsWindows) {` then `$x = $IsWindows` on the next line) would be flagged as a violation because `$IsWindows` appears without `Test-Path` on the same line.
  **Fix**: Add a comment noting the same-line-only requirement is intentional for the current single-line idiom. No code change required unless multi-line patterns are introduced.

- **[P3.3]** [cg-testing] `tests/link.Tests.ps1:551`, `tests/unlink.Tests.ps1:241` — `[advisory]` `Should -Match 'Test-Path\s+variable:IsWindows'` matches comment text
  **Why**: If the guard line were removed but a code comment retained the phrase, the test would pass. Mitigated: the ps51-compat.Tests.ps1 scanner would catch the bare `$IsWindows` re-introduced on the production line. Two-layer protection covers this.
  **Fix**: No change needed. Optionally add a comment noting the dependency on the ps51 scanner.

- **[P3.4]** [cg-architecture] `tests/helpers.ps1` — `[advisory]` Test-layer platform detection duplicated in 4 files
  **Why**: `$script:OnWindows`/`$script:OnMacOS` declared independently in link, unlink, bash-scripts, and install test files. `tests/helpers.ps1` is the natural shared location (already dot-sourced by some test files).
  **Fix**: Add to `tests/helpers.ps1`:
  ```powershell
  $script:OnWindows = ($IsWindows -eq $true -or $env:OS -eq "Windows_NT")
  $script:OnMacOS   = ($IsMacOS   -eq $true)
  ```
  Then verify which of the 4 test files already dot-source helpers.ps1 and remove per-file copies. Verify no test file removes its `$script:OnWindows` before the guard that gates test skipping.

- **[P3.5]** [cg-version-control] `tests/link.Tests.ps1:8`, `tests/unlink.Tests.ps1:8`, `tests/bash-scripts.Tests.ps1:10`, `tests/install.Tests.ps1:8` — `[advisory]` Test-helper `$OnWindows` still uses bare `$IsWindows` (inconsistent with fix)
  **Why**: Safe in practice (no `Set-StrictMode`), but inconsistent with the production pattern. A future addition of `Set-StrictMode` to test scope would crash PS 5.1 at line 8 before any test runs.
  **Fix**: Align in a follow-up commit: `$script:OnWindows = ((Test-Path variable:IsWindows) -and $IsWindows -or $env:OS -eq "Windows_NT")`.

- **[P3.6]** [cg-version-control] `tests/link.Tests.ps1:547`, `tests/unlink.Tests.ps1:237` — `[advisory]` Duplicate assertions with ps51-compat.Tests.ps1
  **Why**: The per-script `It "uses Test-Path variable:IsWindows guard..."` blocks duplicate what the ps51 scanner already covers. Belt-and-suspenders is not harmful, but creates two places to update if the guard pattern changes.
  **Fix**: Add a comment: `# Belt-and-suspenders: ps51-compat.Tests.ps1 also covers this via full-suite scan.`

- **[P3.7]** [cg-version-control] — `[advisory]` Commit message suggestion
  **Why**: Conventional commits format with dual scope is most accurate for this change.
  **Fix**: `fix(link,unlink): guard bare $IsWindows for PS 5.1 strict-mode compatibility`
  Body:
  ```
  $IsWindows is a PS6+ automatic variable. Under Set-StrictMode -Version Latest
  on PS 5.1, accessing it throws 'variable not set'. Guard with:
    (Test-Path variable:IsWindows) -and $IsWindows

  Adds regression guards in link.Tests.ps1, unlink.Tests.ps1, and a new
  Describe block in ps51-compat.Tests.ps1 covering all production scripts.
  ```

---

### Autofix Summary

Applied automatically (`[safe_auto]`):
| Finding | File(s) | Change |
|---|---|---|
| P2.1 | `tests/ps51-compat.Tests.ps1` | Completed "Use:" snippet with full expression + fallback note |
| P2.2 | `tests/link.Tests.ps1`, `tests/unlink.Tests.ps1` | Updated "Fix:" snippet to full expression |
| P2.5 | 4 test files | Replaced misleading "PS 5.1-safe" comment |
| Bonus | `.cg-docs/solutions/bugs/2026-05-13-link-ps1-runs-on-macos-verification-fails.md` | Updated unsafe code sample to guarded pattern |
| Bonus | `.cg-docs/solutions/environment-issues/2026-05-13-join-path-backslash-not-cross-platform.md` | Updated companion-rule snippet to safe pattern |

All 117 tests pass after autofix changes.

---

### Passed
- **cg-performance**: No issues — `Test-Path variable:IsWindows` is a startup probe, overhead negligible.
- **cg-reproducibility**: Fix is deterministic across PS 5.1 Windows, PS 7+ Windows, PS 7+ macOS/Linux.
- **cg-data-quality**: No data operations in changed files.
- **cg-version-control**: No secrets, no gitignore concerns. Changes are a clean single-commit unit.
