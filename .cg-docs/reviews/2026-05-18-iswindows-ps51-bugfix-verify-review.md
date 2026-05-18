---
date: 2026-05-18
depth: light
parent-review: .cg-docs/reviews/2026-05-18-iswindows-ps51-bugfix-review.md
type: verification
findings:
  P3.1: open
---

## Review Report

**Review depth**: light (mode:verify)
**Files reviewed**: 10
**Findings**: 1 (P0: 0, P1: 0, P2: 0, P3: 1)

**Suppressed** (within fixed-finding scope): 2 findings (P3.1-suppressed, P3.2-suppressed — see below)

---

### P0 — BLOCKING
_None._

### P1 — CRITICAL
_None._

### P2 — IMPORTANT
_None._

### P3 — MINOR

- **[P3.1]** [cg-code-quality] `tests/link.Tests.ps1:8`, `tests/unlink.Tests.ps1:8`, `tests/bash-scripts.Tests.ps1:10`, `tests/install.Tests.ps1:8` — Parenthesization in test-file `$OnWindows` is less explicit than production scripts
  **Why**: Production scripts (link.ps1, unlink.ps1) use fully explicit grouping: `(((Test-Path variable:IsWindows) -and $IsWindows) -or ($env:OS -eq "Windows_NT"))`. Test files updated in P3.5 use semi-explicit form: `((Test-Path variable:IsWindows) -and $IsWindows -or $env:OS -eq "Windows_NT")`. Both are correct (operator precedence: `-and` > `-or`), but they're inconsistent without a comment explaining the intentional difference.
  **Fix**: Either match the production form for uniformity, or add a comment in the 4 test files: `# -and binds tighter than -or; grouped explicitly in production scripts for clarity`.

---

### ✅ Passed

- **cg-testing**: No issues found — `Should -Exist` placement correct in all three Describe blocks; helpers.ps1 dot-source mapping is disjoint (no collisions); platform detection evaluates correctly on PS 5.1/PS 7+/macOS.
- **cg-code-quality**: All P2 fixes confirmed correct.

---

### Suppressed findings (within fixed-finding scope)

- **[suppressed, P3]** `tests/helpers.ps1:33` — `$script:OnWindows`/`$script:OnMacOS` have no current consumers among dot-sourcing test files. Suppressed: within scope of P3.4 (fixed) — the helpers.ps1 section is the P3.4 fix itself; forward-declaring for future consumers is the stated intent.
- **[suppressed, P3]** `tests/ps51-compat.Tests.ps1:101` — `#.*$` replacement not string-aware (e.g., `#` inside a URL string). Suppressed: within scope of P2.3 (fixed) — the `#.*$` strip line is the P2.3 implementation; known limitation noted in inline comment.
