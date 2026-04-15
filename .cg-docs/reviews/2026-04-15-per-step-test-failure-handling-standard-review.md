---
plan: .cg-docs/plans/2026-04-15-per-step-test-failure-handling.md
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: fixed
  P2.1: fixed
  P2.2: skipped
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P2.9: fixed
  P2.10: skipped
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: skipped
  P3.6: skipped
  P3.7: fixed
  P3.8: fixed
  P3.9: fixed
---

## Review Report

**Review depth**: standard (auto-escalated from `light` — 65 non-test lines changed ≥ 50)
**Files reviewed**: 7 (5 modified + 2 untracked)
- `.github/prompts/cg-work.prompt.md` (+24/-1)
- `tests/prompt-tools.Tests.ps1` (+37)
- `compound-gpid.md` (+2/-2)
- `roadmap.json` (+16/-16)
- `.cg-docs/archive/charter-history.md` (+4)
- `.cg-docs/plans/2026-04-15-per-step-test-failure-handling.md` (untracked)
- `.cg-docs/strategy/2026-04-15-move-testing-skills-to-skills-enhancement.md` (untracked)

**Agents dispatched**: cg-code-quality, cg-testing, cg-documentation, cg-version-control, cg-reproducibility, cg-performance, cg-architecture, cg-data-quality

**Findings**: 0 P0 · 6 P1 · 10 P2 · 9 P3 = 25 total

---

### P0 — BLOCKING

None.

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-architecture] `.github/prompts/cg-work.prompt.md`:105 — "Continue to the next plan step" on TFR exhaustion silently bypasses Step 4.1, Validate, Commit, and Report
  **Why**: "Next plan step" means the outer `For each step in the plan` loop's next iteration — skipping `get_errors`, `@cg-fix-problems`, Validate, Commit checkpoint, and per-step Report for the current plan step entirely. Code with live diagnostic errors advances unexamined.
  **Fix**: Replace "Continue to the next plan step" with "Continue to **Auto-Fix Diagnostics** (Step 4.1) below" so that the remainder of the current plan step still executes.

- **[P1.2]** [cg-architecture] `.github/prompts/cg-work.prompt.md`:136–141 — Double-notification skip-guard in Step 4.1 item 5 is unreachable dead code
  **Why**: The guard fires only when (a) TFR sent an exhaustion notification AND (b) Step 4.1 is executing. From P1.1, TFR exhaustion causes an outer-loop jump that skips Step 4.1 entirely. The two preconditions are mutually exclusive — no path reaches item 5 after TFR exhaustion. The `Otherwise surface to the user` branch fires unconditionally when Step 4.1.5 is reached.
  **Fix**: Resolve P1.1 first. If TFR exhaustion is changed to fall through to Step 4.1, the guard becomes reachable and correct without further changes.

- **[P1.3]** [cg-documentation] `.github/prompts/cg-work.prompt.md`:Step2.4-TFR-step3 — "modules touched by this step" is undefined
  **Why**: The AI has no anchor — it could interpret this as (a) files changed in this step, (b) files that import those files, (c) all test files from the Step 1.6 index, or (d) the whole project. The Step 1.6 test index exists but is not referenced here.
  **Fix**: Replace "for all modules touched by this step" with "for all test files mapped to the files changed in this step (reference the Step 1.6 index)".

- **[P1.4]** [cg-documentation] `compound-gpid.md`:Current Focus — lists "per-step test enforcement" as remaining but `roadmap.json` shows it `done`
  **Why**: The Current Focus text reads "remaining: per-step test enforcement, honest pushback mode, and side-idea capture." The roadmap entry `per-step-test-enforcement-in-cg-work` has `status: done` and the plan has `status: completed`. Every prompt's Step 0 reads `compound-gpid.md` and will report this work as still outstanding.
  **Fix**: Move "per-step test enforcement" to the done list: "…R testing skill, and per-step test enforcement are done; remaining: honest pushback mode and side-idea capture."

- **[P1.5]** [cg-version-control] `main` branch — all changes are uncommitted directly on `main` after the v0.6.4 release tag
  **Why**: Charter: "work on branches, not main." The release tag is HEAD. All 7 files are unprotected — an accidental `git checkout .` erases them.
  **Fix**: `git checkout -b feat/per-step-test-failure-handling` before staging anything.

- **[P1.6]** [cg-version-control] `.cg-docs/plans/`, `.cg-docs/reviews/`, `.cg-docs/strategy/` files are untracked
  **Why**: Charter: "the entire `.cg-docs/` directory must be version-controlled." The plan file is referenced by `roadmap.json:32`. Losing it breaks traceability.
  **Fix**: `git add .cg-docs/plans/2026-04-15-per-step-test-failure-handling.md .cg-docs/reviews/ .cg-docs/strategy/2026-04-15-move-testing-skills-to-skills-enhancement.md`

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `.github/prompts/cg-work.prompt.md`:99 — No branch for when the full-suite re-run reveals regressions
  **Why**: TFR step 3 says "If the full suite passes, continue normally" but gives no instruction for when the full suite *fails* with a new regression introduced by the targeted fix. The AI is left in undefined state and likely silently continues.
  **Fix**: Add an else-branch: "If the full suite fails on regressions (tests not in the original failing set), emit the standard 'N test(s) still failing' notification and continue to Auto-Fix Diagnostics."

- **[P2.2]** [cg-architecture] `.github/prompts/cg-work.prompt.md`:87–109 — TFR runs before `get_errors`, so compile/type errors waste TFR fix rounds
  **Why**: Sequence is Test → TFR → Step 4.1 (`get_errors`). A missing import or type mismatch surfaces as a test failure first. TFR applies 2 targeted code fixes against a symptom that `@cg-fix-problems` is purpose-built to handle. Only after TFR is exhausted does `get_errors` run.
  **Fix**: Call `get_errors` first within item 4; dispatch `@cg-fix-problems` if errors exist before running tests. TFR then operates only on a diagnostically-clean baseline.

- **[P2.3]** [cg-architecture] `.github/prompts/cg-work.prompt.md`:119–122 — After `@cg-fix-problems` modifies code, Step 4.1's test re-run has no failure handler
  **Why**: Step 4.1 item 3 re-runs tests after the agent patches code. If the agent introduced a regression, neither TFR nor any other clause handles it — execution falls through to Validate potentially passing failing tests.
  **Fix**: Add: "If the re-run reveals new failures not present before the diagnostic-fix pass, apply one TFR-style targeted fix (not re-entering the full 2-round loop). If still failing, notify the user before Validate."

- **[P2.4]** [cg-documentation] `.github/prompts/cg-work.prompt.md`:Auto-Fix-Diagnostics-label — `(Step 4.1)` conflicts with top-level `### Step 4: Summary`
  **Why**: The file has a top-level `### Step 4: Summary`. The label "Step 4.1" inside the per-step loop causes an AI to search for a section heading named "Step 4.1" rather than the inline **Auto-Fix Diagnostics** block immediately below.
  **Fix**: Rename the label: `**Auto-Fix Diagnostics** (the block below)` and update all `(Step 4.1)` cross-references accordingly.

- **[P2.5]** [cg-documentation] `.github/prompts/cg-work.prompt.md`:Step4.1.5-skip-guard — Skip-guard relies on implicit session state, bleeds across plan steps
  **Why**: "If the **Test Failure Recovery** block *in this step* already notified the user" — "in this step" is ambiguous. When step 2 reaches Step 4.1.5, the AI may find step 1's TFR notification in context and incorrectly suppress step 2's surface.
  **Fix**: Add explicit scoping: "If **Test Failure Recovery step 4** was triggered for the **current plan step** (i.e., the 'N test(s) still failing after 2 fix attempts' notice was printed for this same step)…"

- **[P2.6]** [cg-testing + cg-reproducibility] `tests/prompt-tools.Tests.ps1`:1685 — Dead first alternative in `"requires full-suite re-run"` test
  **Why**: `'full test suite.*catch regressions'` spans a line break in the prompt (`**full test suite** for all\n modules touched…`). Without `(?s)`, `.` does not cross `\n`. The test passes only via the second alternative `regressions introduced by the fix`. If "regressions introduced by the fix" is rephrased, the "full test suite" requirement goes undetected.
  **Fix**:
  ```powershell
  ($content -match '(?s)full test suite.*catch regressions|regressions introduced by the fix') | Should Be $true
  ```

- **[P2.7]** [cg-testing + cg-reproducibility] `tests/prompt-tools.Tests.ps1`:1697 — Dead first alternative + regex wildcard in `"double-notification skip-guard"` test
  **Why**: `'already notified.*skip this surface'` spans lines 122–123; `.` won't cross `\n`. Test passes via `avoid\s+double.notification` only. Additionally, the `.` in `double.notification` is a wildcard, not a literal hyphen — it would match `doubleXnotification`.
  **Fix**:
  ```powershell
  ($content -match '(?s)already notified.*skip this surface|avoid\s+double-notification') | Should Be $true
  ```
  (Use `double-notification` with a literal hyphen, not `double.notification`.)

- **[P2.8]** [cg-reproducibility] `tests/prompt-tools.Tests.ps1`:1683 — Multi-hop `.*` without `(?s)` in `"Do NOT dispatch"` test
  **Why**: `'Do NOT dispatch.*@cg-fix-problems.*test fail'` has two `.*` hops. If a markdown editor reflows the line at the backtick boundary, both hops fail and the test starts reporting false negatives (the safeguard text is still present but the test fails).
  **Fix**:
  ```powershell
  ($content -match '(?s)Do NOT dispatch.*@cg-fix-problems.*test fail') | Should Be $true
  ```

- **[P2.9]** [cg-documentation] `.github/prompts/cg-work.prompt.md`:TFR-heading — "`get_errors` diagnostic layer" jargon front-loaded without explanation
  **Why**: An AI reading TFR for the first time encounters "`get_errors` diagnostic layer" before that concept is introduced (it appears paragraphs later in Auto-Fix Diagnostics).
  **Fix**: Change the parenthetical to: "(functional tests only — `get_errors` compile/lint errors are handled separately in the **Auto-Fix Diagnostics** block below)".

- **[P2.10]** [cg-version-control] All 8 files — Roadmap restructure mixed with feature commit
  **Why**: `roadmap.json` / `compound-gpid.md` / strategy doc represent a separate `/cg-strategy` decision; mixing them with the prompt feature commit means `git revert` of the feature also reverts the milestone reorganization.
  **Fix**: Split into two commits: (1) `feat(roadmap): move python/stata testing skills to Skills Enhancement` · (2) `feat(cg-work): add bounded retry on per-step test failures`.

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `.github/prompts/cg-work.prompt.md`: "Do NOT dispatch" paragraph — trailing whitespace
  **Why**: The diff shows trailing spaces after "handles" mid-sentence. Two or more trailing spaces create a Markdown hard `<br>`.
  **Fix**: Remove the trailing whitespace on that line.

- **[P3.2]** [cg-testing] `tests/prompt-tools.Tests.ps1`:1669 — Tests 1 and 2 are near-duplicates with no independent coverage
  **Why**: `'2 fix attempts'` (Test 1) is a substring of `'still failing after 2 fix attempts'` (Test 2). Any change that kills Test 2 also kills Test 1; they don't independently guard different things.
  **Fix**: Replace Test 1 with a more specific assertion pinning the cap to the protocol steps: `($content -match '\d+\.\s+If tests are still failing after 2 fix attempts') | Should Be $true`

- **[P3.3]** [cg-testing] `tests/prompt-tools.Tests.ps1` — Exception clause (interface-change exemption) not covered
  **Why**: The exception in TFR step 1 ("if this plan step explicitly changed a function's interface or return type, updating tests is correct") is the only carve-out in the anti-weakening rule — a high-value regression target with no test.
  **Fix**:
  ```powershell
  It "permits test updates when function interface explicitly changed" {
      ($content -match 'interface or return type|updating tests to match the new interface') | Should Be $true
  }
  ```

- **[P3.4]** [cg-testing] `tests/prompt-tools.Tests.ps1` — Notification template body format not verified
  **Why**: Test 2 checks the opening phrase but not "Review before merging" or the `<test-file>::<test-name>` per-test format.
  **Fix**:
  ```powershell
  It "notification template includes 'Review before merging'" {
      ($content -match 'Review before merging') | Should Be $true
  }
  It "notification template shows per-test enumeration format" {
      ($content -match '<test-file>::<test-name>') | Should Be $true
  }
  ```

- **[P3.5]** [cg-reproducibility] `compound-gpid.md`:4 — `last-reviewed` date manually maintained with no test coverage
  **Why**: `last-reviewed: "2026-04-15"` is updated by convention; a stale date produces no test failure.
  **Fix**: If recency matters, add a Pester assertion that `last-reviewed` is within N days of the file's last commit date.

- **[P3.6]** [cg-performance] `tests/prompt-tools.Tests.ps1` — `cg-work.prompt.md` is now loaded by 6 independent `Get-Content` calls
  **Why**: Each `Describe "cg-work.prompt.md - …"` block calls `Get-Content` independently (Pester 3.4 has no cross-Describe `BeforeAll`). Currently fine with OS disk caching, but grows with each new Describe block.
  **Fix**: No action needed now. If blocks exceed ~10, lift a single `$cgWorkContent` to script scope.

- **[P3.7]** [cg-version-control] `.gitignore` — no comment explaining intentional `.vscode/` tracking
  **Why**: `.vscode/settings.json` and `.vscode/tasks.json` are intentionally committed (Pester safety settings + shared test runner task). No comment documents this as deliberate.
  **Fix**: Add `# .vscode/ is intentionally tracked — tasks.json provides shared safe Pester runner` to `.gitignore`.

- **[P3.8]** [cg-architecture] `.github/prompts/cg-work.prompt.md` — "next plan step" used with two different scopes
  **Why**: At TFR step 4 it means the outer loop's next iteration; at Step 4.1 item 4's `[continue/stop]` prompt it means "proceed to item 5 (Validate)." Same phrase, different semantic levels.
  **Fix**: In Step 4.1 item 4, use "proceed to Validate" instead of "continue to next step" to distinguish inner from outer loop navigation.

- **[P3.9]** [cg-data-quality] `tests/roadmap.Tests.ps1` — Cross-milestone feature ID uniqueness not validated
  **Why**: `$featureIds` is reset inside the `foreach ($m in $milestones)` loop, so uniqueness is only checked per-milestone. A feature ID could appear in two milestones and pass schema validation silently.
  **Fix**: Declare `$allFeatureIds = @{}` before the loop; accumulate all feature IDs across milestones; error on collision.

---

### ✅ Passed

- **cg-performance**: No significant issues — +450 tokens is well within acceptable bounds; `Get-Content` calls are OS-cache-absorbed; no pathological regex patterns.
- **cg-data-quality**: JSON valid; all required fields present; IDs unique; derived milestone statuses correct; plan path passes schema regex and file exists on disk.
