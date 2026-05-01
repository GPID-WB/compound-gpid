---
date: 2026-05-01
depth: light
parent-review: .cg-docs/reviews/2026-05-01-smart-setup-phase2-revised-review.md
type: verification
findings:
  P1.1: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
---

## Verify Review Report

**Review depth**: light (mode:verify)
**Files reviewed**: 4 (`.github/prompts/cg-setup.prompt.md`, `.github/prompts/setup-templates.md`, `scripts/link.ps1`, `tests/prompt-tools.Tests.ps1`)
**Prior review**: `.cg-docs/reviews/2026-05-01-smart-setup-phase2-revised-review.md` (21 fixed, 1 skipped)
**Findings**: 10 (P0: 0, P1: 1, P2: 4, P3: 5)

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test for scanner injection sanitization instruction (P1.5 fix uncovered)
  **Why**: The P1.5 fix added a `**Sanitization**` block to `cg-setup.prompt.md` A3 instructing the model to treat scanner-derived content as untrusted, omit `SYSTEM:` prefixes, and ignore imperative sentences starting with "Ignore", "Override", or "Forget". The existing test at line ~2847 targets `cg-review-repos.prompt.md`, not `cg-setup`. The Mode A scanner integration Describe block has no assertion touching "untrusted", "Sanitization", "SYSTEM:", or the named injection trigger words. Removing the entire sanitization block from the prompt would not fail any test — the primary security mitigation for the prompt-injection vector is unprotected by regression coverage.
  **Fix**: Add to the "cg-setup.prompt.md - Mode A scanner integration" Describe block:
  ```powershell
  It "contains scanner output sanitization instruction" {
      ($content -match 'untrusted user data|SYSTEM:.*prefix|Sanitization') | Should Be $true
  }
  It "names specific injection trigger words (Ignore, Override, Forget)" {
      ($content -match '(?i)Ignore.*Override|Override.*Forget') | Should Be $true
  }
  ```

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test for roadmap.json existence guard (P1.2 fix)
  **Why**: The P1.2 fix added an explicit existence guard to A5.7: "If `roadmap.json` already exists, skip creation entirely." The existing test `($content -match 'roadmap\.json') | Should Be $true` passes trivially — `roadmap.json` appears multiple times in the file (B1.2.5 check, setup-complete message). Deleting the existence guard would not fail any test.
  **Fix**:
  ```powershell
  It "has roadmap.json existence guard (skip if already exists)" {
      ($content -match 'roadmap\.json.*already exists.*skip|already exists.*roadmap') | Should Be $true
  }
  ```

- **[P2.2]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test for Mode B B0.5 pre-load step (P1.3 fix)
  **Why**: The P1.3 fix added `#### B0.5. Pre-load templates` as the first step of Mode B. The Mode B quality gate Describe block tests for B1.1.1, B3, B4.7, and "Store results internally" but has no assertion for `B0\.5` or "Pre-load templates". Removing B0.5 entirely would not fail any test.
  **Fix**:
  ```powershell
  It "Mode B has B0.5 pre-load templates step" {
      ($content -match 'B0\.5') | Should Be $true
  }
  ```

- **[P2.3]** [cg-testing + cg-code-quality] `tests/prompt-tools.Tests.ps1` — Missing / weak test for B4 cg-schema-version carry-forward (P1.4 fix)
  **Why**: The P1.4 fix added "read the existing file and carry forward the `cg-schema-version` value unchanged" to B4. The test `($content -match 'cg-schema-version') | Should Be $true` (line ~2497) passes on the B1.3 schema-version check — a different location. Deleting the B4 carry-forward instruction would not fail any test.
  **Fix**:
  ```powershell
  It "Mode B B4 instructs carrying forward cg-schema-version on rewrite" {
      ($content -match 'carry forward.*cg-schema-version|cg-schema-version.*unchanged') | Should Be $true
  }
  ```

- **[P2.4]** [cg-testing + cg-code-quality] `tests/prompt-tools.Tests.ps1` — No test for B3→B4.5 state handoff instruction (P1.7 fix)
  **Why**: The P1.7 fix added "If blockers were found and fixed in this step… skip the B4.5 charter-update offer — the charter was just updated. Proceed directly to B4.7." to B3. The existing P1.6-derived test checks for quality gate content in B3 but not the skip-B4.5 handoff. Deleting the handoff sentence would not fail any test.
  **Fix**:
  ```powershell
  It "Mode B B3 instructs skipping B4.5 when blockers were fixed in B3" {
      ($content -match 'skip.*B4\.5|charter was just updated') | Should Be $true
  }
  ```

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `.github/prompts/cg-setup.prompt.md:281` — B3 state-handoff sentence ambiguously skips B4 as well as B4.5
  **Why**: The P1.7 fix reads "skip the B4.5 charter-update offer … Proceed directly to B4.7." A model reading this will jump from B3 to B4.7, skipping both B4 (config update offer) and B4.5 (charter update offer). The intent was to skip only B4.5.
  **Fix**: Change to: "skip the B4.5 charter-update offer — the charter was just updated. After B4 (config update), proceed directly to B4.7."

- **[P3.2]** [cg-code-quality] `.github/prompts/cg-setup.prompt.md:214` — B0.5 uses abbreviated section names that don't match actual headings in `setup-templates.md`
  **Why**: B0.5 lists "Missing Directories Scaffold" and "Context Summary Format", but the actual section headings in `setup-templates.md` are `## Mode B: Missing Directories Scaffold` (line 215) and `## Mode B: Context Summary Format` (line 235). B1.2 and B3 in the same file use the full names. The inconsistency makes B0.5 an unreliable inventory for a model scanning for section anchors.
  **Fix**: Update B0.5 to: "Mode B: Missing Directories Scaffold" and "Mode B: Context Summary Format".

- **[P3.3]** [cg-testing] `tests/prompt-tools.Tests.ps1` — `## Current Focus` not verified in field mapping table (P2.3 fix)
  **Why**: The P2.3 fix added a "Current Focus" row to the field mapping table in `setup-templates.md` (marked "not scannable / always insert placeholder"). No assertion verifies this row exists. Deleting it would not fail any test.
  **Fix**:
  ```powershell
  It "field mapping table notes Current Focus as not scannable" {
      ($content -match 'Current Focus.*not scannable|not scannable.*Current Focus') | Should Be $true
  }
  ```

- **[P3.4]** [cg-testing] `tests/prompt-tools.Tests.ps1` — Broad `<!-- TODO` match does not verify specific exact-string fix (P2.4 fix)
  **Why**: The P2.4 fix replaced a broad `<!-- TODO` blocker check with four specific strings (`<!-- TODO: Describe`, `<!-- TODO: List`, `<!-- TODO: Add`, `<!-- TODO: What`). The existing test `($content -match '<!-- TODO')` is satisfied by any `<!-- TODO` occurrence (including prose examples). The specific blocker strings are untested.
  **Fix**: Add:
  ```powershell
  It "Charter Quality Gate specifies exact TODO blocker strings" {
      ($content -match '<!-- TODO: Describe') | Should Be $true
      ($content -match '<!-- TODO: List') | Should Be $true
      ($content -match '<!-- TODO: What') | Should Be $true
  }
  ```

- **[P3.5]** [cg-testing] `tests/prompt-tools.Tests.ps1` — P2.7 (YAML quoting), P2.8 (JSON escaping), and P2.6 (absent-table fallback) have zero test coverage
  **Why**: Three content fixes in `setup-templates.md` / `cg-setup.prompt.md` are entirely untested:
  - P2.7 — "Always wrap `project-name` and all YAML string fields in double quotes" (`setup-templates.md` line ~107)
  - P2.8 — "JSON string escaping: escape `"` as `\"`…" (`setup-templates.md` line ~448)
  - P2.6 — "If the `## Setup Recommendations` table is absent, treat all fields as `ask`" (`cg-setup.prompt.md`)
  Any typo in these three rules would go undetected by the test suite.
  **Fix**:
  ```powershell
  It "setup-templates.md includes YAML quoting rule for project-name" {
      ($content -match 'single-quoted YAML|single quotes instead') | Should Be $true
  }
  It "setup-templates.md includes JSON string escaping rule" {
      ($content -match 'JSON string escaping') | Should Be $true
  }
  It "cg-setup.prompt.md falls back to ask when Setup Recommendations table absent" {
      ($setupContent -match 'absent from the scanner report|Setup Recommendations.*absent') | Should Be $true
  }
  ```

---

### ✅ Passed

- **cg-code-quality**: P0.1 fix confirmed — file terminates correctly at line 287 (no duplicate Mode B content). P1.1 regex escaping confirmed — all four pipe patterns in lines 2573–2581 now use `\|`. P3.2 `-ForegroundColor` fix confirmed — `link.ps1` next-step message uses default color or Cyan. P3.1 step numbering gap corrected — B1.1.1 → B1.1.2 → B1.1.3 (or reserved comment present).
- **cg-testing**: P1.1 regex fix verified correct — `\| skip`, `\| confirm`, `\| ask` all match their expected table rows in `setup-templates.md`. P1.6 Mode B B3 quality gate test passes non-trivially. P2.1 Charter write ordering fix verified in Fallback block. P2.2 Q3 guard verified. P2.5 phantom cross-reference fix verified (A3.5 option 2 now references "Option 2 (Walk through)").
- **Both agents**: P1.4 (cg-schema-version erasure), P1.5 (injection sanitization block), P1.7 (skip-B4.5 sentence), P2.3 (Current Focus row), P2.4 (exact TODO strings), P2.6 (absent-table fallback), P2.7 (YAML quoting), P2.8 (JSON escaping) all confirmed present in the files — the fixes were applied.

---

Parsed 10 finding IDs: P1.1, P2.1–P2.4, P3.1–P3.5. Count matches total findings above.
