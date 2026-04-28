---
date: 2026-04-28
depth: light
parent-review: .cg-docs/reviews/2026-04-28-cg-release-scan-optimization-review.md
type: verification
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
---

## Review Report

**Review depth**: light (mode:verify)
**Files reviewed**: 4 (`cg-release.prompt.md`, `.github/agents/cg-release-scanner.agent.md`, `docs/reference.md`, `tests/prompt-tools.Tests.ps1`)
**Findings**: 11 (P0: 0, P1: 0, P2: 6, P3: 5)

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test for the `window-start >= today` warning
  **Why**: Step 1c of `cg-release.prompt.md` specifies a guard warning when `window-start >= today`, but no test asserts this text exists.
  **Fix**: Add `It "warns when window-start is on or after today (zero-doc-context guard)" { ($content -match 'window-start.*today|All.*cg-docs.*entries will be excluded') | Should Be $true }` to the `cg-release.prompt.md - dispatches cg-release-scanner` Describe block.

- **[P2.2]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test for the `--since` ISO-date-after-today fallback guard
  **Why**: The Arguments section of `cg-release.prompt.md` specifies "if the parsed date is after today, warn the user and fall back to the 60-day default." No test verifies this behavior is documented.
  **Fix**: Add `It "warns and falls back when --since ISO date is in the future" { ($content -match 'after today.*fall back|parsed.*after today') | Should Be $true }`.

- **[P2.3]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test for the 500-line commit log guard
  **Why**: Step 1d specifies a user warning when the commit log exceeds 500 lines. This guard exists to prevent silent context truncation — untested.
  **Fix**: Add `It "warns when commit log exceeds 500 lines" { ($content -match '500 lines|exceeds 500') | Should Be $true }`.

- **[P2.4]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test for the shallow-clone fallback
  **Why**: Step 1b specifies a warning and fallback when `git log -1` returns empty output. Untested.
  **Fix**: Add `It "warns on shallow clone and falls back to window-days formula" { ($content -match 'shallow clone') | Should Be $true }`.

- **[P2.5]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test for the `release-result.txt` catch-all
  **Why**: Step 5 specifies: "If `release-result.txt` is absent, or starts with neither `CREATED|` nor `EXISTS|`: > Release script may have failed…". No test covers this path.
  **Fix**: Add `It "catch-all when release-result.txt is absent or unrecognized" { ($content -match 'may have failed|release-result\.txt.*absent|neither.*CREATED') | Should Be $true }`.

- **[P2.6]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test for `Highest impact: none` empty-log path in scanner agent
  **Why**: The scanner agent specifies "write in Suggested Semver Impact: `Highest impact: none — no commits found.`" as the safe empty-log response. This primary exit path has no test.
  **Fix**: In the `cg-release-scanner.agent.md - existence and structure` Describe block, add: `$agentContent = Get-Content $agentFile -Raw -Encoding UTF8; It "documents Highest impact: none for empty commit log" { ($agentContent -match 'Highest impact: none') | Should Be $true }`.

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test verifying `docs/reference.md` lists `cg-release-scanner`
  **Why**: `reference.md` was changed in this fix session; a regression guard ensures accidental removal is caught.
  **Fix**: Add `It "reference.md documents @cg-release-scanner agent" { ($refContent -match 'cg-release-scanner') | Should Be $true }` to the existing `docs/reference.md - R skills and r-syntax config` Describe block (reusing the `$refContent` variable already defined there).

- **[P3.2]** [cg-testing] `tests/prompt-tools.Tests.ps1` — P2.8 dispatch test doesn't cover the halt condition
  **Why**: The P1.4 fix added a halt guard ("If the agent response is empty or does not contain `## Scan Summary`: halt and report…"). The dispatch Describe block currently only checks `@cg-release-scanner` presence.
  **Fix**: Add `It "documents halt condition when scanner returns no output" { ($content -match 'no output|does not contain.*Scan Summary|Scanner returned no output') | Should Be $true }`.

- **[P3.3]** [cg-code-quality] `.github/agents/cg-release-scanner.agent.md`:20 — `window_days` and `tag_date` (underscores) still present in agent Inputs description
  **Why**: P3.5 renamed `window_days` → `window-days` in `cg-release.prompt.md` but missed the parenthetical formula in the scanner agent's `window-start` input description: `(pre-computed by the prompt as \`max(today - window_days, tag_date)\`)`.
  **Fix**: Change `max(today - window_days, tag_date)` → `max(today - window-days, tag-date)` in `.github/agents/cg-release-scanner.agent.md` line 20.

- **[P3.4]** [cg-code-quality] `docs/reference.md`:~204 — `User-invokable` (k) vs `User-invocable` (c) intra-file inconsistency
  **Why**: The new Release Scanner Agent table uses `User-invokable` but the adjacent Plan Review Agent table (and the actual `user-invocable:` frontmatter key throughout the project) uses `User-invocable`.
  **Fix**: Change `User-invokable` → `User-invocable` in the Release Scanner Agent table header in `docs/reference.md`.

- **[P3.5]** [cg-code-quality] `cg-release.prompt.md` — naming-note `> Note: \`window-days\` uses hyphens...` interrupts Step 1c prose flow
  **Why**: This is a meta-comment on naming convention inserted mid-algorithm. It interrupts the logical flow after the `window-start >= today` guard and before Step 1d.
  **Fix**: Move the note to the Arguments section (after the `--since` bullet list, before the Precedence rule) where `window-days` is first introduced, or remove it since the naming is now self-evident.

---

### ✅ Passed

- `cg-release.prompt.md`: No remaining `window_days` instances (P3.5 confirmed clean) ✓
- `cg-release.prompt.md`: `--since` future-date guard correctly placed and unambiguous ✓
- `cg-release.prompt.md`: `window-start >= today` warning logically correct and well-placed ✓
- `cg-release.prompt.md`: `<proposed-name>` derivation rule in Step 4 confirmation block is clear ✓
- `cg-release-scanner.agent.md`: `Semver Impact` capitalization consistent in table header and output section ✓
- `cg-release-scanner.agent.md`: No DRY violations or confusing duplications ✓
- `docs/reference.md`: Release Scanner Agent section content accurate and description matches agent behavior ✓
- `tests/prompt-tools.Tests.ps1`: New Describe blocks follow Pester 3 style (script-scope variables, `Should Be $true`, `Get-Frontmatter` helper reuse) ✓
- P2.7 test assertions match actual agent frontmatter content ✓
- P2.8 dispatch reference test asserts correct literal string ✓
- No P0/P1 issues found — prior critical and blocking fixes all converged ✓
