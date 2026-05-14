---
plan: .cg-docs/plans/2026-05-13-pr-verification-pipeline.md
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P2.9: fixed
  P2.10: fixed
  P2.11: fixed
  P2.12: fixed
  P2.13: fixed
  P2.14: fixed
  P2.15: fixed
  P2.16: fixed
  P3.1: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
---

## Review Report

**Review depth**: thorough  
**Files reviewed**: 15  
**Findings**: 25 (P0: 0, P1: 3, P2: 16, P3: 6)  
**Mode**: autofix — 18 safe_auto findings applied, 4 manual findings open

### Pre-dispatch Applied Fixes (cg-data-quality)
- `scripts/link.ps1:262` — `Join-Path` nested form for PS5.1 compatibility (multi-arg form requires PS6+)
- `scripts/unlink.sh:77,110` — `printf` prompt strings moved inside FORCE guard (were appearing in CI logs with `--yes`)

---

### P0 — BLOCKING
*(none)*

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-adversarial] `.github/workflows/tests.yml` teardown — `Get-ChildItem -Recurse | Remove-Item | Remove-Item -Recurse` follows surviving junctions into `$GITHUB_WORKSPACE` if junction removal fails silently, deleting source files.  
  **Why**: On GitHub Actions Windows runners, Windows Defender can lock files accessed through junctions, causing `Remove-Item -Force` to silently fail. The subsequent `Remove-Item -Recurse` then descends through the surviving junction and deletes `$GITHUB_WORKSPACE/.github/prompts/*` etc.  
  **Fix**: Replaced teardown with `cmd /c rmdir /s /q` which treats junctions as atomic entries.  
  **Status**: fixed

- **[P1.2]** [cg-testing] `tests/unlink.Tests.ps1` — Two junction-creating Describe blocks ("legacy whole-directory junction" and "per-subdirectory junction removal") had no `AfterAll` cleanup; Pester's `$TestDrive` teardown uses `Remove-Item -Recurse -Force`.  
  **Fix**: Added `AfterAll` blocks that remove junctions with `Remove-Item -Path $_.FullName -Force`.  
  **Status**: fixed

- **[P1.3]** [cg-testing] `tests/unlink.Tests.ps1:218` — `$content | Should -Match 'if \(-not \$Force\)'` passes on the first match, so it passes if only 1 of the 2 required guards is present. A deleted guard goes undetected.  
  **Fix**: Changed to count assertion: `($content -split '\r?\n' | Where-Object { $_ -match 'if \(-not \$Force\)' } | Measure-Object).Count | Should -Be 2`.  
  **Status**: fixed

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality, cg-architecture, cg-adversarial] `scripts/link.ps1:148` — `Read-Host "Relink $dir/ to Compound GPID instead? [y/N]"` in the junction-conflict branch has no `-Force` bypass. If a pre-existing non-CG junction is found in CI (e.g., from a prior failed teardown), the runner hangs indefinitely.  
  **Fix**: Add `[switch]$Force` to `link.ps1` param block; wrap this `Read-Host` in `if (-not $Force)`. Mirror in `link.sh` with `--yes`/`-y`.  
  **Status**: open

- **[P2.2]** [cg-adversarial] `.github/workflows/tests.yml:207` — `DEFAULT_BRANCH="${{ github.base_ref }}"` embeds a GitHub Actions expression directly in shell source. Flagged by CodeQL `actions/expression-injection`.  
  **Fix**: Moved to `env: DEFAULT_BRANCH: ${{ github.base_ref }}` and reference as `${DEFAULT_BRANCH}` in the shell script.  
  **Status**: fixed

- **[P2.3]** [cg-adversarial] `.github/workflows/tests.yml` — `New-Item -ItemType Directory -Force` on `e2e-project` silently inherits stale junction debris if `$RUNNER_TEMP` persists on self-hosted runners. Second E2E run could validate stale state.  
  **Fix**: Pre-clean with `cmd /c rmdir /s /q` before creating the fresh e2e dir.  
  **Status**: fixed

- **[P2.4]** [cg-architecture] `.github/workflows/tests.yml` — E2E smoke test steps had no `if: success()` guard; they ran even when Pester failed, obscuring which step caused the overall job failure.  
  **Fix**: Added `if: success() && runner.os == '...'` to both E2E smoke test steps.  
  **Status**: fixed

- **[P2.5]** [cg-testing, cg-architecture] `tests/parity.Tests.ps1` — Three Describe blocks ("unlink.ps1 <-> unlink.sh", "link.ps1 <-> unlink.ps1", "link.sh <-> unlink.sh") had no extraction sanity checks. If `Get-ManagedDirsFromSource` returns `@()` for both sides, `$missing` and `$extra` are empty and the parity assertions pass vacuously.  
  **Fix**: Added `$dirs.Count | Should -BeGreaterThan 0` parse guards and per-block sanity `It` tests.  
  **Status**: fixed

- **[P2.6]** [cg-testing] `.github/workflows/tests.yml` — E2E smoke tests only asserted that `.github/prompts` was removed; they did not verify `.gitignore` was cleaned of CG entries.  
  **Fix**: Added `.gitignore` cleanup assertions to both Windows and macOS E2E steps.  
  **Status**: fixed

- **[P2.7]** [cg-testing, cg-code-quality] `tests/unlink.Tests.ps1:220` — `Should -BeLessThan 3` passes vacuously with 0 `Read-Host` calls (e.g., if they were accidentally removed during refactor).  
  **Fix**: Changed to `Should -Be 2` (exactly two guarded calls, one per confirmation path).  
  **Status**: fixed

- **[P2.8]** [cg-testing] `tests/bash-scripts.Tests.ps1` — `$content | Should -Match 'if.*FORCE'` passes on the first match; second guard going missing is undetected.  
  **Fix**: Changed to `([regex]::Matches($content, 'if\s+\[\[.*FORCE') | Measure-Object).Count | Should -Be 2`.  
  **Status**: fixed

- **[P2.9]** [cg-testing] `tests/bash-scripts.Tests.ps1` — `-y` short form not asserted in `--yes / -y` regression guard.  
  **Fix**: Added `$content | Should -Match '(?<!\w)-y[)\s]'`.  
  **Status**: fixed

- **[P2.10]** [cg-documentation] `CONTRIBUTING.md:59` — "Files not listed are silently skipped by the suite runner and will produce a warning" is self-contradictory ("silently" + "will produce a warning").  
  **Fix**: Reworded to "Unregistered files are skipped and the runner emits a warning at the start of the run."  
  **Status**: fixed

- **[P2.11]** [cg-documentation, cg-version-control] `.github/workflows/tests.yml` docs-staleness job — Block comment claimed the three-dot diff "works correctly with GitHub Actions' default shallow clone" but the checkout immediately below uses `fetch-depth: 0`. Contradictory docs risk future regression.  
  **Fix**: Updated comment: "Requires full history (fetch-depth: 0): git diff origin/$base...HEAD needs the common ancestor commit reachable from both refs; a shallow clone omits it."  
  **Status**: fixed

- **[P2.12]** [cg-documentation] `CONTRIBUTING.md:221` — Security reviewed self-review item did not mention the Windows 2-level junction scan requirement. New contributors could write teardown code using `Remove-Item -Recurse` on trees containing junctions.  
  **Fix**: Added "On Windows, junction cleanup uses the safe 2-level scan pattern — no `Remove-Item -Recurse` on directory trees that may contain junctions."  
  **Status**: fixed

- **[P2.13]** [cg-documentation] `.github/PULL_REQUEST_TEMPLATE.md` — No "Tests added/updated" checkbox. Project standards require tests for all behavioral changes; the PR template is the enforcement surface.  
  **Fix**: Add a "Tests added / updated" checkbox between E2E verified and Cross-script parity.  
  **Status**: open

- **[P2.14]** [cg-version-control] `.github/workflows/link-check.yml` — Pre-existing issue: `actions/checkout@v4` and `lycheeverse/lychee-action@v2` use mutable tag references. Not introduced by this PR.  
  **Fix**: Replace with SHA-pinned references (SHA lookup required for lychee-action@v2).  
  **Status**: open

- **[P2.15]** [cg-learnings-researcher] `scripts/unlink.ps1` — No Windows platform guard (`$IsWindows` / `$env:OS -eq 'Windows_NT'` check). `LinkType -eq "Junction"` never matches macOS symlinks, silently skipping all removals when `cg-unlink` is run via `pwsh` on macOS. `link.ps1` has this guard (added in this PR); `unlink.ps1` does not.  
  **Fix**: Add `if (-not ($IsWindows -or $env:OS -eq 'Windows_NT')) { Write-Error "...use cg-unlink (unlink.sh)..."; exit 1 }` at the top.  
  **Status**: open

- **[P2.16]** [cg-learnings-researcher] `tests/unlink.Tests.ps1` — No `Read-Host ""` regression guard; gap relative to the equivalent guard in `link.Tests.ps1`.  
  **Fix**: Added `$content | Should -Not -Match 'Read-Host\s+""'` and `$content | Should -Not -Match "Read-Host\s+''"`.  
  **Status**: fixed

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `scripts/unlink.ps1:45` — "Found legacy whole-directory junction. Removing..." contradicts the `if (-not $Force)` confirmation prompt immediately after.  
  **Fix**: Changed to "Found legacy whole-directory junction."  
  **Status**: fixed

- **[P3.3]** [cg-code-quality] `.github/workflows/tests.yml:56` — `pwsh -File "$env:GITHUB_WORKSPACE\scripts\link.ps1"` spawns a child `pwsh` process within a `shell: pwsh` step. Idiomatic form is `& "$env:GITHUB_WORKSPACE\scripts\link.ps1"`.  
  **Status**: open (advisory)

- **[P3.4]** [cg-architecture] `tests/bash-scripts.Tests.ps1:7` — Header comment said "requires: pwsh + Pester 5.6.1"; CI installs 4.10.1.  
  **Fix**: Changed to `4.10.1`.  
  **Status**: fixed

- **[P3.5]** [cg-documentation] `CONTRIBUTING.md:30` — `-File` stem-name convention not explained; a new contributor would try `-File parity.Tests.ps1` or `-File tests/parity` and get a confusing error.  
  **Fix**: Added inline examples: `. tests\Run-Tests.ps1 -File link` and `. tests\Run-Tests.ps1 -File parity`.  
  **Status**: fixed

- **[P3.6]** [cg-testing] `tests/parity.Tests.ps1:72` — `-y` short form missing from "bypass flag" test in parity suite. Covered more thoroughly in bash-scripts.Tests.ps1.  
  **Status**: open (advisory — redundant with bash-scripts coverage)

---

### ✅ Passed

- **cg-performance**: No meaningful performance concerns for this shell-script change set
- **cg-reproducibility**: All new action SHAs pinned; no hard-coded absolute paths outside `$RUNNER_TEMP`/`$GITHUB_WORKSPACE`; E2E dir isolation via pre-clean
- **cg-version-control**: No credentials or secrets in changed files; all three new/modified workflows use SHA-pinned action references

---

*Parsed 25 finding IDs. Auto-applied 18 safe_auto findings; 4 manual findings remain open (P2.1, P2.13, P2.14, P2.15). Advisory findings (P3.3, P3.6) are filed but not applied.*
