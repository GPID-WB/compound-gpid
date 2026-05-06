---
date: 2026-05-05
depth: light
parent-review: .cg-docs/reviews/2026-05-05-cross-platform-macos-support-review.md
type: verification
findings:
  P1.1: fixed
  P2.1: fixed
  P3.1: fixed
---

## Review Report

**Review depth**: light (verification pass)
**Files reviewed**: 10 (staged changes after P1–P3 fix-triage)
**Findings**: 3 (P0: 0, P1: 1, P2: 1, P3: 1)
**Agents**: cg-code-quality, cg-testing
**Parent review**: `.cg-docs/reviews/2026-05-05-cross-platform-macos-support-review.md`

---

### P0 — BLOCKING

None.

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-code-quality / cg-testing] `scripts/install.sh`:54–55 — `detect_profile()` warning lines write to **stdout** inside a command substitution, corrupting `PROFILE_FILE`
  **Why**: `print_yellow` uses `printf '...\n' "$1"` with no `>&2` redirect. `detect_profile()` is called as `PROFILE_FILE="$(detect_profile)"` — any stdout from the function is captured into the variable. For unrecognized shells (fish, nushell, tcsh), the two `print_yellow` warning lines are captured before the `echo "$HOME/.bashrc"` line, producing a multi-line ANSI-escape-polluted path as `PROFILE_FILE`. Every subsequent operation using `$PROFILE_FILE` (`grep -qF`, `>>`) silently targets a junk path — the PATH block is never written to the real shell profile. Install appears to succeed but does nothing useful. This regression was introduced by the P3.8 fix.
  **Fix**: Add `>&2` to both `print_yellow` calls in the `else` branch:
  ```bash
      else
          print_yellow "Warning: unrecognized shell '$shell_name'. Defaulting to ~/.bashrc." >&2
          print_yellow "  You may need to manually add the PATH block to your shell profile." >&2
          echo "$HOME/.bashrc"
      fi
  ```

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-testing] `tests/bash-scripts.Tests.ps1`:~347 — No test assertion for `*.yaml eol=lf` (P3.6 partially uncovered)
  **Why**: `.gitattributes` was updated with both `*.yml text eol=lf` and `*.yaml text eol=lf`, but only the `*.yml` rule has a corresponding test assertion. A regression dropping the `*.yaml` line would go undetected.
  **Fix**: Add one assertion in the `.gitattributes` Describe block, after the existing `*.yml` assertion:
  ```powershell
  It ".gitattributes sets eol=lf for *.yaml files" {
      $content | Should Match "\*\.yaml.*eol=lf"
  }
  ```

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-testing] `tests/bash-scripts.Tests.ps1`:~383 — Idempotency test does not assert P3.15 `$HOME`-relative PATH entry content
  **Why**: The test only checks `$markerCount | Should Be 1`. The new P3.15 behavior (PATH entry uses `$HOME/<rel>` form) is never verified — a revert to absolute path form would go undetected.
  **Fix**: Add in the `try` block after reading `$profileContent`:
  ```powershell
  # Verify PATH entry uses $HOME-relative form (P3.15)
  $profileContent | Should Match 'export PATH=.*\$HOME/'
  ```

---

### ✅ Passed

- cg-code-quality: P3.14 git log guard correctly applied (`[[ -n "$BEFORE" && ... ]]`)
- cg-code-quality: P3.15 PATH_ENTRY construction correct (`$HOME/<rel>` with guard)
- cg-code-quality: P3.11 `$(< )` replacements verified — no `$(cat ` remaining in 3 scripts
- cg-code-quality: P3.4 `bin/cg-*` glob correctly covers all 3 wrappers; `.cmd` rule order correct
- cg-code-quality: P3.12 `permissions: contents: read` placement valid in GitHub Actions YAML
- cg-code-quality: P2.15 COMPOUND_GPID_DIR sandbox correctly isolates installs to temp dir
- cg-code-quality: P2.16 HOME/SHELL restore in `finally` block confirmed
- cg-testing: P3.1 `bin/cg-\*.*eol=lf` glob assertion verified correct
- cg-testing: P3.2 `'bash-scripts'` membership assertion verified present
- cg-testing: No stale `cg-link.*eol=lf` assertions causing regression from glob change
