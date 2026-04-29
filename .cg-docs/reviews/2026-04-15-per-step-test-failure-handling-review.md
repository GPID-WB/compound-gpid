---
plan: .cg-docs/plans/2026-04-15-per-step-test-failure-handling.md
findings:
  P0.1: fixed
  P0.2: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: fixed
  P1.7: fixed
  P2.1: open
  P2.2: open
  P2.3: open
  P2.4: open
  P2.5: open
  P2.6: open
  P2.7: open
  P2.8: open
  P2.9: open
  P2.10: open
  P2.11: open
  P2.12: open
  P2.13: open
  P2.14: open
  P2.15: open
  P2.16: open
  P2.17: open
  P2.18: open
  P3.1: open
  P3.2: open
  P3.3: open
  P3.4: open
  P3.5: open
  P3.6: open
  P3.7: open
  P3.8: open
  P3.9: open
  P3.10: open
  P3.11: open
  P3.12: open
---

## Review Report

**Review depth**: thorough
**Files reviewed**: 7 (5 modified + 2 untracked)
- `.github/prompts/cg-work.prompt.md` (+24/-1)
- `tests/prompt-tools.Tests.ps1` (+37)
- `compound-gpid.md` (+2/-2)
- `roadmap.json` (+16/-16)
- `.cg-docs/archive/charter-history.md` (+4)
- `.cg-docs/plans/2026-04-15-per-step-test-failure-handling.md` (untracked)
- `.cg-docs/strategy/2026-04-15-move-testing-skills-to-skills-enhancement.md` (untracked)

**Agents dispatched**: cg-code-quality, cg-testing, cg-documentation, cg-version-control, cg-reproducibility, cg-performance, cg-architecture, cg-data-quality, cg-learnings-researcher, cg-adversarial

**Findings**: 2 P0 · 7 P1 · 18 P2 · 12 P3 = 39 total

---

### P0 — BLOCKING (immediate remediation required)

- **[P0.1]** [cg-adversarial] `.github/prompts/cg-work.prompt.md`:93 — Exception clause is self-defeating circular logic
  **Why**: The exception reads "if this plan step explicitly changed a function's interface or return type, updating tests to match the new interface is correct." An LLM can always reason: my implementation causes these tests to fail → the tests expect behavior my code doesn't provide → therefore I changed the interface → I may update the tests. Test failure itself becomes proof of interface change. There is no external check; the entire anti-weakening rule is nullified. Any implementation bug can be rationalized as an interface change, and failing tests silently updated to match buggy behavior.
  **Fix**: The exception must require the plan step to explicitly enumerate the OLD and NEW signatures (e.g., `before: foo(x)`, `after: foo(x, y)`). Restrict test updates only to assertions that literally reference those signatures. Add: "Inference about interface change from test failure alone is prohibited."

- **[P0.2]** [cg-adversarial] `.github/prompts/cg-work.prompt.md`:97–99 — 2-attempt counter resets for full-suite regressions, creating an unbounded retry loop
  **Why**: Sub-step 3 says "if the targeted failures are resolved, re-run the full test suite." The 2-attempt counter was scoped to the *targeted* failures. If the full-suite re-run exposes a new failure, the counter for that failure is zero — the LLM starts a new 2-attempt cycle. That fix may again resolve targeted failures but expose another full-suite regression. This recurses indefinitely: targeted fix → full suite reveals regression → new counter → targeted fix → full suite reveals regression...
  **Fix**: Make the counter global per plan step, not per failure batch: "Total fix attempts across all Test Failure Recovery, including full-suite regressions: 2. After 2 attempts total, emit the notification and continue."

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-documentation] `compound-gpid.md`:53 — `Current Focus` is stale: lists "per-step test enforcement" as remaining but it was just completed
  **Why**: `.cg-docs/plans/2026-04-15-per-step-test-failure-handling.md` has `status: completed`. Agent prompts that read `compound-gpid.md` (Step 0 of every workflow prompt) will believe this work is still outstanding, producing misleading output from `/cg-work`, `/cg-plan`, and `/cg-ideate`.
  **Fix**: Remove "per-step test enforcement" from "remaining". Suggested: *"remaining: honest pushback mode and side-idea capture."*

- **[P1.2]** [cg-version-control] `main` branch — uncommitted changes sitting directly on `main` after merge of v0.6.4
  **Why**: The project charter is explicit: "work on branches, not main." HEAD is at `f11dfba` (the v0.6.4 merge commit). All 7 modifications are currently unprotected — an accidental `git checkout .` would erase them entirely.
  **Fix**: `git checkout -b feat/per-step-test-failure-recovery` before staging anything.

- **[P1.3]** [cg-version-control] `.cg-docs/plans/2026-04-15-per-step-test-failure-handling.md` and `.cg-docs/strategy/2026-04-15-move-testing-skills-to-skills-enhancement.md` — untracked, never staged
  **Why**: The charter constraint: "Always commit... the entire `.cg-docs/` directory must be version-controlled." The plan file documents the rationale for the 2-round bounded-retry design. The strategy doc records the reasoning for the Quality Loop / Skills Enhancement feature move, directly explaining the `roadmap.json` diff. Neither will survive a branch cleanup.
  **Fix**: `git add .cg-docs/plans/2026-04-15-per-step-test-failure-handling.md .cg-docs/strategy/2026-04-15-move-testing-skills-to-skills-enhancement.md`

- **[P1.4]** [cg-architecture + cg-adversarial] `.github/prompts/cg-work.prompt.md`:107 — "Continue to the next plan step" hard-skips Step 4.1 (Auto-Fix Diagnostics), Validate, Commit, and Report
  **Why**: When Test Failure Recovery exhausts 2 attempts, it says "Continue to the next plan step." "Next plan step" means the next iteration of the outer for-each loop (plan step N+1), which skips `get_errors`, `@cg-fix-problems`, Validate, Commit, and Report for the current plan step. Code with live diagnostic errors advances without cleanup. Silent accumulation of errors.
  **Fix**: Change to "Skip further test retry and continue to **Auto-Fix Diagnostics** (below)." The skip should only bypass additional test retries, not the rest of the per-step sub-sequence.

- **[P1.5]** [cg-adversarial] `.github/prompts/cg-work.prompt.md`:117 — Double-notification guard bleeds across plan steps
  **Why**: Sub-item 5 reads "If the Test Failure Recovery block above already notified the user about exhausted fix attempts **in this step**..." The phrase "in this step" is ambiguous. If plan step 1 triggered exhaustion, and plan step 2 reaches Step 4.1 sub-item 5, the LLM searches its context for any prior TFR notification and finds step 1's. It silently skips step 2's notification. A plan step with quietly failing tests and no diagnostic errors produces no user-visible signal at all.
  **Fix**: Bind the guard to a per-step logical condition that can be re-derived rather than recalled: "If the 2-attempt limit was exhausted in Test Failure Recovery for this same plan step (i.e., 'N test(s) still failing after 2 fix attempts' was already printed for this step), skip this surface."

- **[P1.6]** [cg-adversarial] `.github/prompts/cg-work.prompt.md`:93 — "Do not weaken or remove" rule permits silent expected-value replacement
  **Why**: The rule forbids weakening assertions (e.g., `expect_equal` → `expect_lte`) and removing them. It does not forbid changing the *expected value* while keeping the same assertion form. An LLM can replace `expect_equal(result, 5)` with `expect_equal(result, 3)` matching the new buggy return value — the assertion is equally strong in form, just adjusted to match wrong output. Tests go green, bug ships.
  **Fix**: Add explicitly: "Do not change expected values in assertions to match new implementation output unless the plan step names the exact return values that are expected to change."

- **[P1.7]** [cg-adversarial + cg-code-quality] `.github/prompts/cg-work.prompt.md`:99 — No else-branch when full-suite regression is detected
  **Why**: Sub-step 3: "If the full suite passes, continue normally." There is no `else` clause. If the full-suite re-run reveals a regression, the instructions are silent. The LLM will likely ignore the failure and "continue normally" (instruction completion bias), or enter ad-hoc reasoning with no consistent outcome. Regressions introduced by the targeted fix are detected but then silently swallowed.
  **Fix**: Add explicitly: "If the full suite fails (new regressions from the fix), emit the standard failure notification (using the format from sub-step 4) attributing the failures to the fix, and continue to Auto-Fix Diagnostics."

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-architecture] `.github/prompts/cg-work.prompt.md`:131 — Step 4.1.5 double-notification skip-guard is dead logic if P1.4 is resolved as "skip Step 4.1 on exhaustion"
  **Why**: If TFR exhaustion causes Step 4.1 to be skipped entirely (per the P1.4 fix), the guard in sub-item 5 can never be reached. The guard creates false documentation confidence: a reviewer sees it and believes double-notification is handled when it's structurally unreachable. If instead P1.4 is resolved to keep Step 4.1 running after TFR, the guard stays live. The resolution of P1.4 determines whether this guard should exist.
  **Fix**: Resolve P1.4 first. If Step 4.1 is kept: update the guard per P1.5's fix. If Step 4.1 is skipped on TFR exhaustion: remove the guard entirely.

- **[P2.2]** [cg-architecture] `.github/prompts/cg-work.prompt.md`:122 — Step 4.1 sub-item 3: "re-run both the previously-failing tests" — referent undefined in passing case
  **Why**: By the time Step 4.1 runs, if TFR succeeded (no failures), there are no "previously-failing tests" to re-run. The phrase imports a concept from TFR into the diagnostics layer without establishing what it means when no failures exist. It may cause the agent to waste effort searching for a prior failing set.
  **Fix**: Replace "re-run both the previously-failing tests AND the full test suite" with simply "re-run the full test suite for all files touched by this step."

- **[P2.3]** [cg-architecture] `.github/prompts/cg-work.prompt.md`:84 — Test Failure Recovery lists R/Python/Stata frameworks but omits PowerShell/Pester; no fallback for unknown runners
  **Why**: Item 4 lists `testthat`, `pytest`, `assert`/do-files — but this is a PowerShell/Pester project and Pester is not mentioned. For any project using an unlisted framework, "Re-run the tests" has no concrete command. Pester has documented crash-risk patterns (VS Code context overflow) that TFR aggressively ignores.
  **Fix**: Add `PowerShell: use Pester with `. tests\Run-Tests.ps1` or `Invoke-Pester <file> -Quiet` — never `Invoke-Pester tests/` (crashes VS Code)` to the framework list. Add: "If no test framework is identified, skip all TFR loop iterations and surface: 'Test framework not identified — manual verification required.'"

- **[P2.4]** [cg-architecture] `.github/prompts/cg-work.prompt.md`:112 — 2 TFR attempts + 2 Step 4.1 rounds can compound to 4 independent mutations on the same file
  **Why**: TFR makes up to 2 code edits targeting logic failures. Step 4.1 then dispatches `@cg-fix-problems` for up to 2 rounds of diagnostic-driven edits on the same files. If test failure and diagnostic error share a root cause, 4 independent fixes are applied without a human checkpoint. The user receives a TFR exhaustion notice at attempt 2, then code is modified again by `@cg-fix-problems` at attempts 3–4 with no connecting narrative.
  **Fix**: Add note in Step 4.1 sub-item 1: "If Test Failure Recovery already attempted fixes on these files in this step, note this in the dispatch to `@cg-fix-problems` so it avoids re-applying the same fixes."

- **[P2.5]** [cg-documentation] `.github/prompts/cg-work.prompt.md`:104 — "modules touched by this step" not anchored to Step 1.6 index; phrase too narrow (misses transitive dependents)
  **Why**: Step 1.6 builds an explicit module→test-file index. Recovery rule 3 bypasses that anchor with a vague new phrase. Additionally, "touched" means "directly edited" to an LLM, missing transitive dependents (a utility function used by 10 other modules is touched; those 10 are not). Regressions in transitive dependents go undetected until Step 3's final quality checklist.
  **Fix**: Change to "re-run the full project test suite (per the Step 1.6 index)" to be consistent and exhaustive.

- **[P2.6]** [cg-documentation] `.github/prompts/cg-work.prompt.md`:97 — Interface-change exception scope too broad
  **Why**: "Updating tests to match the new interface is correct" permits any assertion touching the changed function to be rewritten. A function whose return type changes may still have pre-existing assertions on unrelated side-effects that should stay intact.
  **Fix**: Tighten to: "updating *only the assertions that directly verify the changed signature or return type* is correct."

- **[P2.7]** [cg-documentation] `.github/prompts/cg-work.prompt.md`:131 — Skip-guard relies on LLM retaining a boolean flag across two separate prose blocks within the same step
  **Why**: The skip-guard in Step 4.1.5 is a behavioral memory requirement. In long-context runs, the LLM may not reliably track whether the notification was already emitted. Per P1.5's fix, convert to a re-derivable logical condition that does not require memory across blocks.
  **Fix**: See P1.5 fix. Same change resolves both.

- **[P2.8]** [cg-documentation] `.github/prompts/cg-work.prompt.md`:104 — "targeted failures" undefined noun phrase
  **Why**: Rules 1 and 2 say "make a targeted fix." Rule 3 then says "if the targeted failures are resolved" — "targeted failures" appears nowhere earlier and a reader must infer it means "the tests that were failing at the start of this sub-block."
  **Fix**: Rewrite as "If the originally-failing tests now pass…"

- **[P2.9]** [cg-testing] `tests/prompt-tools.Tests.ps1`:1669 — Missing coverage for R3 (continue-normally path)
  **Why**: R3 requires the prompt to instruct continuing normally when tests pass. The phrase "If the full suite passes, continue normally" is never tested. If that line were deleted, all 7 tests would still pass.
  **Fix**:
  ```powershell
  It "instructs continuing normally when the full suite passes" {
      ($content -match 'full suite passes.*continue normally|continue normally') | Should Be $true
  }
  ```

- **[P2.10]** [cg-testing] `tests/prompt-tools.Tests.ps1`:1669 — Missing coverage for R7 (notification template structure)
  **Why**: R7 requires the notification to include `<test-file>::<test-name>` and `<last error message>`. Neither is tested. If the detail lines were removed, test 2 ("still failing after 2 fix attempts") would still pass.
  **Fix**:
  ```powershell
  It "notification template includes test-file::test-name format" {
      ($content -match '<test-file>::<test-name>') | Should Be $true
  }
  It "notification template includes last error message placeholder" {
      ($content -match '<last error message>') | Should Be $true
  }
  ```

- **[P2.11]** [cg-testing + cg-reproducibility] `tests/prompt-tools.Tests.ps1`:1685 — Test 5 first regex alternative is dead code (cross-line `.` mismatch)
  **Why**: Production text splits the phrase across lines: `re-run the **full test suite** for all` / `modules touched by this step to catch regressions`. `full test suite.*catch regressions` requires both tokens on the same line but `.` doesn't match `\n`. Test passes only via the second alternative `regressions introduced by the fix`. "full test suite" language could be removed from the prompt without the test catching it.
  **Fix**:
  ```powershell
  It "requires full-suite re-run after targeted fixes resolve to catch regressions" {
      ($content -match '(?s)full test suite.*catch regressions|regressions introduced by the fix') | Should Be $true
  }
  ```

- **[P2.12]** [cg-testing + cg-reproducibility + cg-code-quality] `tests/prompt-tools.Tests.ps1`:1697 — Test 6 first regex alternative is dead code (cross-line `already notified.*skip this surface`)
  **Why**: "already notified" and "skip this surface" are on separate lines. Without `(?s)`, `.` won't cross the newline. The test passes only because `avoid\s+double.notification` works via `\s+` bridging the line break. This means removing the conditional logic while keeping "avoid double-notification" would pass silently.
  **Fix**:
  ```powershell
  It "includes double-notification skip-guard for Step 4.1 sub-item 5" {
      ($content -match '(?s)already notified.*skip this surface|avoid\s+double.notification') | Should Be $true
  }
  ```

- **[P2.13]** [cg-learnings-researcher] `.github/prompts/cg-work.prompt.md`:107 — Notification has no documented response branches
  **Prior art**: `.cg-docs/solutions/testing-patterns/2026-04-13-prompt-interaction-branch-completeness.md`
  **Why**: The guard states the trigger and notification but leaves the response path implicit. The fix-triage `[yes/batch]` bug shows that an LLM receiving an unspecified response branch fills the gap incorrectly — likely by silently continuing as if the user approved.
  **Fix**: After the notification, add: "Wait for the user's response. If the user says `stop`: halt immediately. If the user says `continue` (or makes no explicit response): proceed with the remaining steps, carrying forward the list of unfixed tests."

- **[P2.14]** [cg-learnings-researcher + cg-adversarial] `.github/prompts/cg-work.prompt.md` — Pester re-runs inside Test Failure Recovery must mandate `-Quiet` / `Run-Tests.ps1`
  **Prior art**: `.cg-docs/solutions/testing-patterns/2026-04-15-pester-verbose-output-floods-context-long-session.md`
  **Why**: Running `Invoke-Pester tests\prompt-tools.Tests.ps1` without `-Quiet` in a long `/cg-work` session floods the agent context with 300+ output lines and crashes VS Code. A cg-work session with inline fix attempts and regression re-runs is a comparably long context. The recovery block's "Re-run the tests" instruction does not constrain the command form.
  **Fix**: Add to the re-run instruction: "PowerShell/Pester: use `. tests\Run-Tests.ps1` for full-suite runs or `Invoke-Pester <file> -Quiet` for single-file runs. Never use `Invoke-Pester tests/`."

- **[P2.15]** [cg-learnings-researcher] `tests/prompt-tools.Tests.ps1` — No step-ordering test for the full-suite re-run position
  **Prior art**: `.cg-docs/solutions/testing-patterns/2026-04-13-prompt-step-ordering-indexof-tests.md`
  **Why**: The full-suite re-run (rule 3) must appear before the user-wait pause in Step 4. Without a positional test, a future edit could move the re-run after the wait (making it dead code after session termination), as happened with the roadmap-status-update bug.
  **Fix**: Add an IndexOf-based assertion:
  ```powershell
  It "full-suite re-run appears before user-wait pause" {
      $rrunIdx = $content.IndexOf('full test suite')
      $waitIdx = $content.IndexOf('Wait for the user')
      $rrunIdx | Should BeLessThan $waitIdx
  }
  ```

- **[P2.16]** [cg-adversarial] `.github/prompts/cg-work.prompt.md`:99 — "modules touched by this step" is too narrow; misses transitive dependents
  **Why**: "Touched" is interpreted as "files I directly edited." A utility function used by 10 other modules is "touched"; those modules are not. If the fix breaks the shared utility's contract, dependent modules will have regressions that the targeted re-run never catches. They surface only at Step 3's final quality checklist, potentially many steps later.
  **Fix**: See P2.5 — change to "run the full project test suite" to ensure transitive dependencies are covered. Partially resolved by fixing P2.5.

- **[P2.17]** [cg-data-quality] `roadmap.json`:quality-loop — Two `idea` features (`honest-pushback-in-brainstorm-strategy`, `side-idea-capture-in-brainstorm`) are now outside the narrowed quality-loop objective scope
  **Why**: The `quality-loop` objective was narrowed to "validated testing patterns for R," but these two ideas describe conversational workflow improvements unrelated to testing. Their presence will keep `quality-loop` in `in-progress` indefinitely under the derived-status rules. The milestone cannot reach `done` without completing or relocating them.
  **Fix**: Migrate both ideas to a more appropriate milestone (e.g., a new `ux-improvements` milestone), or update the quality-loop objective to explicitly scope them in.

- **[P2.18]** [cg-version-control] `roadmap.json` / commit structure — Roadmap feature restructure mixed with functional feature commit
  **Why**: The `roadmap.json` +16/-16 diff (moving `testing-skill-python` and `testing-skill-stata` from Quality Loop to Skills Enhancement) originated from a separate `/cg-strategy` session. Mixing them means `git revert` of the feature would also undo the roadmap reorganization.
  **Fix**: Split into two commits: (1) `feat(roadmap): move python/stata testing skills to Skills Enhancement` (roadmap.json + strategy doc), then (2) `feat(cg-work): add per-step test failure recovery with 2-attempt cap` (all remaining files).

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `.github/prompts/cg-work.prompt.md`:89 — British spelling "Analyse" inconsistent with codebase convention
  **Why**: Every other prompt uses American English (`cg-fixbug.prompt.md`: "Analyze the failing test", `cg-review.prompt.md`: "analyze code changes"). This is the only instance of British spelling.
  **Fix**: `Analyse` → `Analyze`.

- **[P3.2]** [cg-documentation] `.github/prompts/cg-work.prompt.md` — "modules touched by this step" (TFR) vs "files touched by this step" / "files changed in this step" (Step 4.1) — inconsistent terminology
  **Why**: "Module" carries language-specific connotations differing from "file." An AI following the prompt precisely may apply different scoping logic in the two recovery paths.
  **Fix**: Standardize to "files touched by this step" throughout the Test Failure Recovery block (partially resolved by P2.5 fix).

- **[P3.3]** [cg-documentation] `.cg-docs/plans/2026-04-15-per-step-test-failure-handling.md`:1 — `brainstorm: null` should be omitted
  **Why**: Other plan files omit optional fields when not applicable. An explicit `null` suggests there is a brainstorm doc that wasn't linked, which may confuse `/cg-resume` or frontmatter search tooling.
  **Fix**: Remove the `brainstorm:` key entirely.

- **[P3.4]** [cg-architecture] `.github/prompts/cg-work.prompt.md` — `**Auto-Fix Diagnostics** (Step 4.1)` uses a bold-header format that looks like a section heading rather than a per-step sub-task
  **Why**: Items 1–7 use numbered list format. Step 4.1 uses a bold prose header at zero indentation making it ambiguous whether it runs once globally or per-step. The `4.1` decimal also conflicts with the non-decimal numbering of inner items.
  **Fix**: Either fold into the numbered list as item 4.a, or rename: `**Auto-Fix Diagnostics** (runs after each test phase, within Step 2)`

- **[P3.5]** [cg-testing] `tests/prompt-tools.Tests.ps1` — Missing test for `N test(s)` count placeholder (R2 partial coverage)
  **Why**: R2 specifies "notify with count." If the wording were changed to a fixed string ("Some tests still failing"), the count requirement would be silently violated.
  **Fix**:
  ```powershell
  It "notification template uses variable count placeholder (N test(s))" {
      ($content -match 'N test\(s\)') | Should Be $true
  }
  ```

- **[P3.6]** [cg-testing] `tests/prompt-tools.Tests.ps1` — Missing test for R1 sequential two-attempt structure ("one more targeted fix attempt")
  **Why**: Test 1 only confirms the number "2" appears. The explicit "one more targeted fix attempt" instruction (step 2 of the recovery block) is untested.
  **Fix**:
  ```powershell
  It "describes sequential two-attempt structure ('one more targeted fix attempt')" {
      ($content -match 'one more targeted fix attempt') | Should Be $true
  }
  ```

- **[P3.7]** [cg-testing] `tests/prompt-tools.Tests.ps1`:1697 — Test 6 uses `\s+` to span a line break without explanation
  **Why**: `avoid\s+double.notification` works because `\s` matches `\r\n`, but future maintainers may assume `.` is doing the work and incorrectly simplify to `avoid.*double.notification`.
  **Fix**: Add an inline comment: `# \s+ intentionally spans the CRLF line break between 'avoid' and 'double-notification' in the prompt`

- **[P3.8]** [cg-reproducibility] `tests/prompt-tools.Tests.ps1`:1669 — No file-existence guard before `Get-Content` in new `Describe` block
  **Why**: If `cg-work.prompt.md` is missing, all 7 `It` blocks throw an unhandled `Get-Content` exception rather than reporting clean named failures. Earlier `Describe` blocks for high-use prompts include an `It "exists"` check.
  **Fix**: Add a guard `It "exists" { Test-Path $promptFile | Should Be $true }` at the top of the block, or accept the reliance on the earlier existence check as the convention.

- **[P3.9]** [cg-data-quality] `tests/roadmap.Tests.ps1` — Schema validates plan path format but not file existence for `done` features
  **Why**: `Test-RoadmapSchema` checks the path string against a regex but never calls `Test-Path`. If a plan file is moved or renamed, the feature continues to pass schema validation while pointing to a broken reference.
  **Fix**: Add `Test-Path (Join-Path $repoRoot $f.plan)` check for features where `status -eq 'done'` and `plan -ne $null`.

- **[P3.10]** [cg-version-control] `.gitignore` — No VS Code allowlist pattern
  **Why**: `.vscode/settings.json` is intentionally committed (carries Pester safety settings). But `.gitignore` has no entry for `.vscode/`, so future per-user editor files (e.g., `launch.json` with hardcoded paths) would be silently tracked.
  **Fix**:
  ```gitignore
  # VS Code — only committed files are tasks.json and settings.json
  .vscode/*
  !.vscode/tasks.json
  !.vscode/settings.json
  ```

- **[P3.11]** [cg-learnings-researcher] `.github/prompts/cg-work.prompt.md` — Boundary between TFR inline fixes and `@cg-fix-problems` auto-mode is not explicitly documented in the prompt
  **Prior art**: `.cg-docs/brainstorms/2026-04-10-fix-problems-agent-and-prompt.md`
  **Why**: The cg-fix-problems brainstorm explicitly separates diagnostics (Problems panel) from test failures (test runner output). The `Do NOT dispatch @cg-fix-problems` line covers the negative case but doesn't state why, which may confuse future editors.
  **Fix**: Minor clarification: "Do NOT dispatch `@cg-fix-problems` for test failures — that agent handles VS Code Problems-panel diagnostics only (detected via `get_errors`). Test runner output is handled here."

- **[P3.12]** [cg-learnings-researcher] `.github/prompts/cg-work.prompt.md` — "Failure investigation mode" is the documented trigger for dangerous `2>&1 |` Pester patterns
  **Prior art**: `.cg-docs/solutions/testing-patterns/2026-04-09-pester-2amp1-pipe-failure-debugging-trigger.md`
  **Why**: TFR is a formalized failure-investigation entry point that puts the agent in the state that triggers the forbidden `2>&1 | Select-String` pattern (crashed VS Code 14+ times). The prompt does not pre-emptively warn against it.
  **Fix**: Add inline: "When inspecting Pester failures, use the two-phase safe pattern: `$r = Invoke-Pester <file> -PassThru -Quiet; if ($r.FailedCount -gt 0) { Invoke-Pester <file> }`. Never use `2>&1 | Select-String`."

---

### ✅ Passed

- **cg-performance**: No issues found. The 24-line prompt addition is ~450 tokens (~5–8% increase); the 7 new tests add one `Get-Content` call and 7 simple regex matches — all within acceptable bounds.
- **cg-data-quality**: JSON structurally valid; all required fields present; `per-step-test-enforcement-in-cg-work` plan path passes schema regex and plan file exists on disk; milestone derived statuses are consistent. Minor improvements noted above (P3.9).
