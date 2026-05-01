---
date: 2026-05-01
depth: light
parent-review: .cg-docs/reviews/2026-05-01-smart-setup-phase2-revised-review.md
type: verification
findings:
  P3.1: fixed
  P3.2: fixed
---

## Verify Review Report (Pass 2)

**Review depth**: light (mode:verify)
**Files reviewed**: 3 (`.github/prompts/cg-setup.prompt.md`, `.github/prompts/setup-templates.md`, `tests/prompt-tools.Tests.ps1`)
**Prior review**: `.cg-docs/reviews/2026-05-01-smart-setup-phase2-revised-review.md` (21 fixed, 1 skipped)
**First verify pass**: `.cg-docs/reviews/2026-05-01-smart-setup-phase2-revised-verify-review.md` (10 fixed)
**Findings**: 2 (P0: 0, P1: 0, P2: 0, P3: 2)

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` — Injection trigger word "Forget" not independently verified
  **Why**: The regex `(?i)Ignore.*Override|Override.*Forget` only requires the first alternative (`Ignore.*Override`) to match. The current source text (`"Ignore", "Override", or "Forget"`) satisfies `Ignore.*Override`, so the test passes. If "Forget" were removed from the sanitization instruction in `cg-setup.prompt.md` line 62, the test would still pass. The `It` description claims all three words are verified, but only two are effectively tested.
  **Fix**: Replace the single regex with three independent assertions:
  ```powershell
  It "names specific injection trigger words (Ignore, Override, Forget)" {
      ($content -match '(?i)\bIgnore\b') | Should Be $true
      ($content -match '(?i)\bOverride\b') | Should Be $true
      ($content -match '(?i)\bForget\b') | Should Be $true
  }
  ```

- **[P3.2]** [cg-testing] `tests/prompt-tools.Tests.ps1` — `<!-- TODO: Add` blocker string not tested despite being listed in Charter Quality Gate
  **Why**: `setup-templates.md` line 296 lists four exact TODO blocker strings: `<!-- TODO: Describe`, `<!-- TODO: List`, `<!-- TODO: Add`, `<!-- TODO: What`. The "Charter Quality Gate specifies exact TODO blocker strings" `It` block checks only three of them, omitting `<!-- TODO: Add` (the Constraints placeholder). Removing that string from the table would go undetected.
  **Fix**: Add to the existing `It` block:
  ```powershell
  ($content -match '<!-- TODO: Add') | Should Be $true
  ```

---

### ✅ Passed

- **cg-code-quality**: All 2 prose changes verified correct — B0.5 section names match actual headings in setup-templates.md (lines 215, 235); B3 state-handoff correctly directs to B4.7 after B4.
- **cg-testing**: All 12 new test patterns verified against source text — all non-trivially true and correctly scoped. No P0/P1/P2 gaps remain. Two minor P3 gaps above are genuine new issues.

---

Parsed 2 finding IDs: P3.1, P3.2. Count matches total findings above.
