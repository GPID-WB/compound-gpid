---
date: 2026-05-05
depth: light
parent-review: .cg-docs/reviews/2026-05-05-phased-plan-and-execution-thorough-review.md
type: verification
findings:
  P2.v1: fixed
  P3.v1: fixed
  P3.v2: fixed
  P3.v3: fixed
  P3.v4: fixed
  P3.v5: fixed
  P3.v6: fixed
---

## Review Report

**Review depth**: light (verify mode)
**Parent review**: `2026-05-05-phased-plan-and-execution-thorough-review.md`
**Files reviewed**: 12
**Findings**: 7 (P0: 0, P1: 0, P2: 1, P3: 6)

---

### P2 — IMPORTANT (should fix)

- **[P2.v1]** [cg-code-quality] `cg-resume.prompt.md:95` — **All-phases-complete message contradicts cg-work halt behavior**
  **Why**: `cg-resume` Step 2a says: *"All M phases completed. Run `/cg-work` to proceed to final quality checks."* But `cg-work.prompt.md:64` dispatch row "Phased | none" halts when all phases are complete: *"Nothing to run."* A user following cg-resume's instruction will run `/cg-work`, hit the halt, and never reach Step 3 quality checks. The feature contracts disagree.
  **Fix**: Update cg-resume line 95 to one of: (a) *"All M phases completed. Final quality checks ran at the end of the last phase."* (since Step 3 ran automatically when phase M completed); or (b) *"All M phases completed. To re-run the final phase and its quality checks: `/cg-work phaseM`."* Either removes the broken suggestion to run `/cg-work` with no argument.

---

### P3 — MINOR (nice to have)

- **[P3.v1]** [cg-code-quality] `cg-work.prompt.md:64` — **"All N phases are already complete" uses undefined variable N in no-arg context**
  **Why**: The "Phased | none" row (no phase argument given) uses variable `N` in its halt message. N is defined as the phase argument — which is absent in this row. The total-phase count variable used throughout the file and in cg-resume is `M`. This makes the message inconsistent with all surrounding prose.
  **Fix**: Change to `"All M phases are already complete. Nothing to run."`.

- **[P3.v2]** [cg-code-quality] `docs/reference.md:366` — **`phases` field "Read by" column says `/cg-resume (hint only)` but cg-resume explicitly ignores it**
  **Why**: `cg-resume` Step 2a states: *"M = authoritative header count; do not use the `phases:` frontmatter hint as the source of truth for M."* The field is never consulted at runtime. Listing `/cg-resume (hint only)` implies the field has runtime significance in cg-resume, which is inaccurate.
  **Fix**: Change the "Read by" cell to `(not read at runtime — informational only for human readers)`.

- **[P3.v3]** [cg-testing] `tests/prompt-tools.Tests.ps1` ~line 3856 — **`$step2aBlock` Substring extraction lacks individual IndexOf guard It blocks**
  **Why**: `compound-gpid.context.md` requires Substring-based extractions to assert both index values with dedicated It blocks (`$start | Should BeGreaterThan -1`, `$end | Should BeGreaterThan $start`). P3.4 added a `"Step 2a section exists"` guard that tests the derived `$step2aBlock` but not the raw index values — if either anchor heading is renamed, the error message is "Expected string to not be empty" rather than identifying which index failed.
  **Fix**: Add before content assertions:
  ```powershell
  It "Step 2a section start anchor found" { $step2aStart | Should BeGreaterThan -1 }
  It "Step 2b section start is after Step 2a" { $step2bStart | Should BeGreaterThan $step2aStart }
  ```

- **[P3.v4]** [cg-testing] `tests/prompt-tools.Tests.ps1` ~line 3817 — **`$permBlock` Substring extraction lacks individual IndexOf guard It blocks**
  **Why**: Same pattern as P3.v3 — P3.5 added `"File Permissions section exists"` but tests the derived `$permBlock`, not `$permStart` and `$permEnd` individually.
  **Fix**: Add:
  ```powershell
  It "File Permissions section start anchor found" { $permStart | Should BeGreaterThan -1 }
  It "Process section start anchor found (end of perm block)" { $permEnd | Should BeGreaterThan $permStart }
  ```

- **[P3.v5]** [cg-testing] `tests/prompt-tools.Tests.ps1:3695` — **Dead alternation branch `Phase \d+ does not exist` in out-of-bounds test**
  **Why**: P3.3 aimed to tighten the pattern to `'Phase \d+ does not exist'` but the result is `'Phase N does not exist|Phase \d+ does not exist'`. The prompt source (`cg-work.prompt.md:72`) uses the literal template `"Phase N does not exist"` where N is a letter, not a digit. So `Phase \d+` never matches — the test passes only via the first branch. The dead second branch provides no coverage.
  **Fix**: Either (a) drop the second branch and use `'Phase N does not exist'` alone; or (b) update the prompt to emit a numeric example like `"Phase 3 does not exist"` and use only `'Phase \d+ does not exist'`.

- **[P3.v6]** [cg-testing] `tests/prompt-tools.Tests.ps1` ~line 3872 — **Dead middle branch `not positive integer.*discard` in sanitization test**
  **Why**: The pattern `'discard.*not positive integer|not positive integer.*discard|deduplicate'` — the prompt reads "discard any entries that are not positive integers", so `discard` precedes `not positive integers`. The middle branch `not positive integer.*discard` (reversed order) never matches. Test passes via branch 1 or 3.
  **Fix**: Remove the dead middle branch. Use `'discard.*not positive integer|deduplicate'`.

---

### ✅ Passed

- **cg-code-quality**: No new `[plan_file]` references. YAML frontmatter field names (`completed-phases`, `current-phase`, `phases`) consistent across all prompt files and docs. Internal cg-plan↔cg-work format contract holds. roadmap.json schema well-formed. No stale step-number cross-references. No redundancy.
- **cg-testing**: New Describe blocks structurally sound. Test specificity adequate. All P3-session prompt/doc changes have corresponding test coverage.

---

*Parsed 7 finding IDs: P2.v1, P3.v1–P3.v6.*
