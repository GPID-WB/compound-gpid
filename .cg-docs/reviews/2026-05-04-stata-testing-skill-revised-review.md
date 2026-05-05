---
plan: .cg-docs/plans/2026-05-04-stata-testing-skill-revised.md
date: 2026-05-04
depth: thorough
findings:
  P0.1: fixed
  P0.2: fixed
  P0.3: fixed
  P0.4: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: fixed
  P1.7: fixed
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
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
  P3.7: fixed
  P3.8: fixed
  P3.9: fixed
  P3.10: fixed
---

## Review Report

**Review depth**: thorough  
**Files reviewed**: 16 (`.github/skills/cg-skill-stata-testing/SKILL.md` + 6 reference files, `.github/instructions/stata.instructions.md`, `.github/copilot-instructions.md`, `tests/prompt-tools.Tests.ps1`, `docs/reference.md`, `roadmap.json`, `.cg-docs/` plans/brainstorm)  
**Findings**: 35 (P0: 4, P1: 7, P2: 14, P3: 10)  
**Agents**: cg-code-quality, cg-testing, cg-documentation, cg-version-control, cg-reproducibility, cg-performance, cg-architecture, cg-data-quality, cg-learnings-researcher, cg-adversarial

---

### P0 — BLOCKING (immediate remediation required)

- **[P0.1]** [cg-code-quality / cg-adversarial] `.github/skills/cg-skill-stata-testing/references/data-validation.md:16` + `references/test-scaffolding.md:54` — `assert expr, "string message"` is invalid Stata syntax; the `, "..."` token causes `r(198): invalid syntax` and the test file halts.  
  **Why**: Stata's `assert` has no message option; the comma is parsed as the start of an option list. Any agent copying this pattern ships broken code. Affects two files.  
  **Fix** (data-validation.md): Remove the string; wrap with explicit `display as error` + `error 9`:
  ```stata
  assert dup_flag == 0
  ```
  **Fix** (test-scaffolding.md): Remove the message option:
  ```stata
  if `tests_failed' > 0 display as error "Some poverty-line tests failed — see above"
  assert `tests_failed' == 0
  ```

- **[P0.2]** [cg-code-quality / cg-adversarial] `.github/skills/cg-skill-stata-testing/references/data-validation.md:74` — `assert e(balanced) == "strongly balanced"` reads `e()` after `xtset`, but `xtset` is not an estimation command and stores nothing in `e()`. The assertion unconditionally fails for every dataset — balanced or not.  
  **Why**: `e(balanced)` is `""` (empty string) after `xtset`; `"" == "strongly balanced"` is `0`. Every run fails. The comment "after xtset, inspect macro" is actively misleading.  
  **Fix**: Use `r(balanced)` from `xtset`, or promote the `xtdescribe` alternative already in the same block:
  ```stata
  xtset country_code year
  assert r(balanced) == "strongly balanced"
  ```

- **[P0.3]** [cg-code-quality / cg-adversarial / cg-data-quality / cg-reproducibility] `.github/skills/cg-skill-stata-testing/references/result-verification.md:169` — `assert reldif(_b[treatment], _b[treatment]) < 0.20` compares a value with itself; `reldif(x, x)` is always exactly 0. The assertion can never fail — the cross-specification stability check is permanently bypassed.  
  **Why**: After `estimates restore spec2`, both arguments to `reldif()` are `spec2`'s `_b[treatment]`. Spec1's coefficient was never stored in a local. An estimate that shifts from 0.03 to 0.90 between specifications passes silently.  
  **Fix**: Store spec1's value before restoring spec2:
  ```stata
  estimates restore spec1
  local b_spec1 = _b[treatment]
  
  estimates restore spec2
  assert reldif(`b_spec1', _b[treatment]) < 0.20
  ```

- **[P0.4]** [cg-code-quality / cg-adversarial / cg-reproducibility] `.github/skills/cg-skill-stata-testing/references/test-scaffolding.md:118-121` — The `assert_soft` program's `c_local` counter always resets to 1, never accumulates. A suite with N failures reports `tests_failed = 1` regardless of N.  
  **Why**: Inside the program, `` `tests_failed' `` is evaluated in the program's own local scope (where it is undefined, expanding to `""`). `"" + 1 = 1` in Stata. Every failure call sets the counter to `1` not `N+1`. The final `assert \`tests_failed' == 0` fires (correctly failing), but the displayed count is always wrong.  
  **Fix**: Pass counter variable names as arguments so `c_local` can read from the caller via double-dereference:
  ```stata
  program define assert_soft
      args condition label tf_var tp_var
      capture assert `condition'
      if _rc {
          di as error "FAIL: `label'"
          c_local `tf_var' = ``tf_var'' + 1
      }
      else {
          c_local `tp_var' = ``tp_var'' + 1
      }
  end
  
  // Call:
  assert_soft "inrange(welfare, 0, 1)" "welfare non-negative" tests_failed tests_passed
  ```

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-adversarial / cg-data-quality] `.github/skills/cg-skill-stata-testing/references/data-validation.md:173,178` — `assert weight > 0` and `assert welfare >= 0` both silently pass when the variable is missing (`.`), because Stata treats `.` as positive infinity in numeric comparisons (`.` > any number evaluates to `1`).  
  **Why**: Missing survey weights and missing welfare are the most dangerous data quality issues in poverty analysis — they produce silently incorrect poverty rates with no warning or error. The current assertions provide false confidence.  
  **Fix**: Always gate non-negative checks with an explicit missing check:
  ```stata
  assert !missing(weight)
  assert weight > 0
  
  assert !missing(welfare)
  assert welfare >= 0
  ```

- **[P1.2]** [cg-code-quality] `.github/skills/cg-skill-stata-testing/references/data-validation.md:78` — `assert r(min) == r(max)` after `quietly xtdescribe` — `xtdescribe` stores `r(T_min)` and `r(T_max)`, not `r(min)` and `r(max)`. Both sides resolve to `.` (missing), so `assert . == .` passes unconditionally — the panel balance check never detects imbalance.  
  **Why**: Non-existent stored results evaluate to missing; `.` equals `.` in Stata comparisons, so a trivially-always-true assertion is produced.  
  **Fix**:
  ```stata
  quietly xtdescribe
  assert r(T_min) == r(T_max)    // all panels have the same time span
  ```

- **[P1.3]** [cg-reproducibility] `.github/skills/cg-skill-stata-testing/references/reproducibility-reprun.md:52` — `repscan using "analysis/main.do"` uses the `using` keyword, which is not part of the `repscan` API. This produces a Stata syntax error.  
  **Why**: The repkit documentation shows `repscan "path/to/analysis.do"` without `using`. Code generated from this pattern fails on run.  
  **Fix**: Remove `using`:
  ```stata
  repscan "analysis/main.do"
  ```

- **[P1.4]** [cg-reproducibility] `.github/skills/cg-skill-stata-testing/references/reproducibility-reprun.md:68` and `references/anti-patterns.md:110` — `reproot, project("my_project") roots("C:/Users/me/projects" "D:/work")` passes absolute filesystem paths as root identifiers. The `roots()` option takes **root name IDs** (e.g., `"code"`, `"data"`), not actual paths.  
  **Why**: Actual paths live in the machine-local `reproot-env.yaml`. Passing absolute paths produces invalid global macro names and silently fails — no error, no root macros set, all downstream `${code}` references break.  
  **Fix**: Replace with root name identifiers:
  ```stata
  reproot, project("my_project") roots("code" "data")
  ```
  Add a note directing users to configure `reproot-env.yaml` with `reproot_setup`.

- **[P1.5]** [cg-data-quality] `.github/skills/cg-skill-stata-testing/references/workflow-examples.md:258` — In the DiD pre-trends test, `pre_period = (year < treatment_year)` is a deterministic linear combination of the year dummies in `i.year`. Stata drops it due to perfect collinearity, making the interaction `1.treated#1.pre_period` undefined. The `test` command then either errors or tests a zero-constrained coefficient — not parallel trends.  
  **Why**: The model specification `i.treated##i.pre_period i.year` contains collinear terms. The resulting test is meaningless and gives a false sense of having verified the parallel trends assumption.  
  **Fix**: Keep only pre-treatment periods and test year × treated interactions:
  ```stata
  preserve
  keep if year < `treatment_year'
  regress outcome i.treated##i.year controls, vce(cluster district_id)
  testparm i.treated#i.year
  local p_pretrend = r(p)
  capture assert `p_pretrend' > 0.05
  restore
  ```

- **[P1.6]** [cg-adversarial] `.github/skills/cg-skill-stata-testing/references/workflow-examples.md` (Example 3) — No warning about the critical difference between `svy, subpop(if urban == 1): mean welfare` (correct) and `svy: mean welfare if urban == 1` (incorrect, produces understated standard errors).  
  **Why**: In complex survey designs, variance estimation requires the full PSU/strata structure. Conditioning with `if` before `svy:` discards cross-stratum information, producing SEs that are too small. For World Bank poverty reports this means confidence intervals on rural/urban headcount rates are falsely narrow.  
  **Fix**: Add to `anti-patterns.md` as Anti-Pattern 9:
  ```stata
  * ❌ Wrong — subgroup with `if` gives incorrect variance
  svy: mean welfare if urban == 1
  
  * ✅ Correct — use subpop() to preserve full design
  svy, subpop(if urban == 1): mean welfare
  ```

- **[P1.7]** [cg-reproducibility / cg-documentation] `.github/skills/cg-skill-stata-testing/references/workflow-examples.md:131` — `gen welfare_ppp = welfare_lcu / ppp_2017 / 365` divides by 365 without any comment documenting that `welfare_lcu` must be **annual** LCU consumption. If `welfare_lcu` is already daily (GPID surveys vary in periodicity), dividing by 365 produces values ~365× too small — every household appears below the poverty line, with no error.  
  **Why**: GPID welfare aggregates can be daily, monthly, or annual depending on the survey. A silent unit mismatch would produce a completely wrong poverty rate.  
  **Fix**: Add a comment and a plausibility sanity check:
  ```stata
  * welfare_lcu must be ANNUAL (LCU per year); / ppp_2017 converts to 2017 USD; / 365 to daily
  gen welfare_ppp = welfare_lcu / ppp_2017 / 365
  assert welfare_ppp < 500 if !missing(welfare_ppp)    // plausibility: < $500/day
  ```

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-version-control] `.github/skills/cg-skill-stata-testing/references/anti-patterns.md:104` and `references/reproducibility-reprun.md:79` — Real World Bank employee ID `wb384996` appears in two negative-example code blocks.  
  **Why**: Even in an `❌ wrong` example block, a real username leaked into a shared, potentially public skill file.  
  **Fix**: Replace `wb384996` with a generic placeholder (`analyst` or `username`) in both files.

- **[P2.2]** [cg-testing] `tests/prompt-tools.Tests.ps1` (end of file) — No test verifies that `copilot-instructions.md` globally registers `cg-skill-stata-testing`.  
  **Why**: The PR adds the skill to `copilot-instructions.md` but the test suite has no regression protection. A future edit could silently remove it.  
  **Fix**: Add a new `Describe` block after the existing stata-testing blocks:
  ```powershell
  Describe "copilot-instructions.md - cg-skill-stata-testing registration" {
      $instrFile = Join-Path $repoRoot ".github\copilot-instructions.md"
      $content = if (Test-Path $instrFile) { Get-Content $instrFile -Raw -Encoding UTF8 } else { "" }
  
      It "copilot-instructions.md registers cg-skill-stata-testing" {
          ($content -match 'cg-skill-stata-testing') | Should Be $true
      }
  }
  ```

- **[P2.3]** [cg-code-quality / cg-architecture] `.github/skills/cg-skill-stata-testing/SKILL.md:1` — Missing `user-invokable: false` in SKILL.md frontmatter. The structural peer `cg-skill-r-testing` has this field.  
  **Why**: Without it, the skill may surface incorrectly in the skill picker UI; inconsistency with the established pattern.  
  **Fix**: Add `user-invokable: false` after the `name:` field.

- **[P2.4]** [cg-architecture] `.github/skills/cg-skill-stata-testing/SKILL.md:1` — The frontmatter `description:` trigger phrase says **"test blocks"** but `stata.instructions.md` and `copilot-instructions.md` say **"assertion patterns, or reproducibility checks"**. The frontmatter is the authoritative load-trigger signal for agents reading skill metadata.  
  **Why**: An agent scanning skill descriptions and seeing a standalone `assert` block or `reprun` question may decide the skill is irrelevant if it only sees "test blocks".  
  **Fix**: Align the frontmatter description trigger: *"Load when writing, reviewing, or debugging assertion blocks, data validation, result verification, test scaffolding, or reproducibility checks in `.do`/`.ado` files."*

- **[P2.5]** [cg-documentation / cg-data-quality] `.github/skills/cg-skill-stata-testing/references/result-verification.md:93` — FGT return names `r(head_count)`, `r(poverty_gap)`, `r(poverty_severity)` are specific to a community package, but no package name is documented. Different packages (`dasp`, `apoverty`, `povdeco`) use different names. An agent applying this with the wrong package gets silent wrong assertions (non-existent scalars resolve to `.`).  
  **Why**: Package-specific return names without documentation create portability failures.  
  **Fix**: Add a header comment identifying the required package and its return names.

- **[P2.6]** [cg-documentation] `.github/skills/cg-skill-stata-testing/references/workflow-examples.md:264-265` — `gen pre_period = (year < \`treatment_year')` references `\`treatment_year'` which is never defined in the setup block. Evaluates to `(year < )` and silently generates a zero variable.  
  **Why**: The example is not self-contained; following it literally produces wrong indicator variables with no error.  
  **Fix**: Add `local treatment_year = 2018 // adjust as needed` to the SETUP section of Example 4.

- **[P2.7]** [cg-adversarial] `.github/skills/cg-skill-stata-testing/references/data-validation.md:30` — `assert inrange(welfare_ppp, 0, .)` has ambiguous behavior across Stata versions when the upper bound is `.` (missing). In some versions `inrange(z, a, .)` returns 0 for all observations (treating `.` as missing per `inrange` docs), causing the assertion to always fail.  
  **Why**: Portability trap; `assert welfare_ppp >= 0 & !missing(welfare_ppp)` is unambiguous.  
  **Fix**: Replace `inrange(x, 0, .)` with `assert x >= 0 & !missing(x)` throughout.

- **[P2.8]** [cg-adversarial] `.github/skills/cg-skill-stata-testing/references/result-verification.md:139` — `reldif < 0.20` tolerance (20%) is too loose for poverty statistics. For a headcount of 0.45, this allows ±9 percentage points between specifications to pass silently.  
  **Why**: World Bank poverty publications require highly stable estimates across robustness checks. A 20% relative tolerance hides meaningful instability.  
  **Fix**: Document domain-appropriate tolerances and require a justification comment; default to `< 0.05` for welfare statistics.

- **[P2.9]** [cg-learnings-researcher] `.github/skills/cg-skill-stata-testing/references/data-validation.md` — Missing pre-FGT validation block requiring **strictly positive welfare** (`welfare > 0`). Per `.cg-docs/solutions/data-quality/2026-03-18-zero-negative-welfare-inflates-fgt-beyond-1.md`, `welfare = 0` produces `gap = 1` and `welfare < 0` produces `gap > 1` — both invalid. Current guidance only checks `welfare >= 0`.  
  **Why**: The existing solution documents that zero/negative welfare silently inflates FGT beyond its valid range.  
  **Fix**: Add a "Pre-FGT Validation Block" subsection with the four-assertion compound guard and cross-reference to the solution file.

- **[P2.10]** [cg-performance] `.github/skills/cg-skill-stata-testing/references/workflow-examples.md:22` — All four workflow examples use `use "${root_data}/processed/survey_clean.dta", clear` (full production dataset) for tests of mathematical properties (FGT ∈ [0,1], sign checks). No example uses synthetic minimal test data.  
  **Why**: On a GPID household survey with millions of observations, running the full estimation pipeline every test run discourages frequent testing. Mathematical invariants hold on any valid sample.  
  **Fix**: Add a "Test Data Strategy" section to `test-scaffolding.md` distinguishing unit tests (50–500 synthetic obs) from integration tests (full production data), and show constructing synthetic test data with `set obs 500; gen welfare = runiform()`.

- **[P2.11]** [cg-reproducibility] `.github/skills/cg-skill-stata-testing/references/reproducibility-reprun.md:145` — `// reprun halts on non-reproducible output` is unverified. If `reprun` exits cleanly (rc=0) regardless of mismatches and only prints a report, the loop always prints `"PASS: ... is reproducible"` even for failing files.  
  **Why**: `reprun` is documented to produce a SMCL mismatch report but the exit code behavior is not confirmed in the skill reference. False-green signals on non-reproducible scripts.  
  **Fix**: Use `capture reprun "\`script'"` and check `_rc`, or add a note that the batch-runner pattern should be verified against the installed repkit version.

- **[P2.12]** [cg-reproducibility] `.github/skills/cg-skill-stata-testing/references/reproducibility-reprun.md:106` — The cache-reading pattern reads only the first value from a three-value cache file, then closes. `se_treatment` and `n_obs` are never read or compared.  
  **Why**: A script where the coefficient is stable but N or SE changed (a real panel-cleaning regression failure mode) would pass the cache check silently.  
  **Fix**: Use a `while` loop to read all lines, or switch to the CSV-based `import delimited` approach to load all cached values at once.

- **[P2.13]** [cg-adversarial] `.github/skills/cg-skill-stata-testing/references/result-verification.md:120` — `assert e(N) == _N` (no observations dropped unexpectedly) produces false alarms in any regression with missing covariates — which is standard listwise deletion in real survey data.  
  **Why**: Any observation with a missing covariate value is legitimately dropped by Stata. The assertion fires routinely on valid data, causing agents to remove it (defeating its purpose).  
  **Fix**: Assert a minimum-retention threshold with justification:
  ```stata
  * At least 90% of observations retained after listwise deletion
  assert e(N) >= _N * 0.90
  ```

- **[P2.14]** [cg-adversarial] `.github/skills/cg-skill-stata-testing/references/anti-patterns.md` (Anti-pattern 8 "corrected" example) — The corrected pattern tests that `replace` was effective rather than testing the generation logic:
  ```stata
  count if welfare_ppp > 999
  assert r(N) == 0    // replace above should have removed all > 999
  ```
  **Why**: If the generation formula is wrong (e.g., wrong PPP field), values exceed 999, get capped by `replace`, and this assertion passes — hiding the root cause.  
  **Fix**: Test the generated values **before** any capping replace, using a temporary calculation:
  ```stata
  preserve
      gen welfare_ppp_test = welfare_lcu / ppp_2017
      assert welfare_ppp_test >= 0
  restore
  ```

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` — `BeLessThan 101` allows exactly 100 lines but the description says "SKILL.md is **under 100 lines**" (implies < 100).  
  **Fix**: Either `Should BeLessThan 100` or update the label to "100 lines or fewer".

- **[P3.2]** [cg-testing] `tests/prompt-tools.Tests.ps1` — `($content -match 'when writing')` asserts conditional trigger language for stata-testing but would pass if "when writing" appeared anywhere in the file unrelated to the skill.  
  **Fix**: Tighten to `($content -match 'cg-skill-stata-testing.*when writing|when writing.*cg-skill-stata-testing')`.

- **[P3.3]** [cg-code-quality] All reference files — Code examples use `*` for regular inline comments (`* Assert…`), contradicting `stata.instructions.md` which reserves `*` exclusively for section delimiter lines and requires `//` as the default comment style.  
  **Why**: Code generated from the skill will replicate the non-standard pattern.  
  **Fix**: Convert example comments from `*` to `//` in the reference files (or note the convention in an introductory comment).

- **[P3.4]** [cg-reproducibility / cg-data-quality] `.github/skills/cg-skill-stata-testing/references/workflow-examples.md:219` — `assert inrange(deff, 1, 20)` — DEFF < 1 is valid for calibrated weights or systematic sampling (not rare for World Bank surveys with post-stratification). Lower bound of 1 produces false failures.  
  **Fix**: `assert inrange(deff, 0.5, 30)` or document the assumption.

- **[P3.5]** [cg-learnings-researcher] `.github/skills/cg-skill-stata-testing/references/data-validation.md` (Survey Design Checks) — No proactive singleton PSU assertion. The `singleunit(centered)` option silently handles it; an explicit assertion forces the analyst to decide.  
  **Fix**: Add `bysort strata: assert _N >= 2, "Stratum has only 1 PSU"` before `svyset` with a note that `singleunit(centered)` is available for confirmed certainty strata.

- **[P3.6]** [cg-performance] `tests/prompt-tools.Tests.ps1` — Inside `Describe "cg-skill-stata-testing - skill file structure"`, `SKILL.md` is read from disk 3 separate times. Other `Describe` blocks hoist `$content` once at the block scope.  
  **Fix**: Hoist `$skillContent` and `$skillLineCount` to the top of the `Describe` block.

- **[P3.7]** [cg-architecture] `.github/copilot-instructions.md` — R skills have an "Eight R skills" orientation paragraph. With two Stata skills now in the catalog, there's no equivalent boundary description.  
  **Fix**: Add a sentence: *"Stata skills: `cg-skill-stata-best-practices` covers all general coding, repkit API, and community packages; `cg-skill-stata-testing` is an additive layer for assertion patterns, data validation, result verification, and reprun testing workflows."*

- **[P3.8]** [cg-data-quality] `references/anti-patterns.md` vs `references/workflow-examples.md` — PPP formula inconsistency: `workflow-examples.md` uses `welfare_lcu / ppp_2017 / 365` (correct for annual surveys); some `anti-patterns.md` examples use `welfare / ppp_2017` without `/365`.  
  **Fix**: Add a comment in `anti-patterns.md` where `/ppp_2017` appears without `/365`: `* welfare_lcu here is already daily — annual surveys additionally require / 365`.

- **[P3.9]** [cg-data-quality] `.github/skills/cg-skill-stata-testing/references/workflow-examples.md:219` — `local deff = e(deff)` silently takes element `[1,1]` of the `e(deff)` matrix; for multi-variable `svy: mean`, only the first variable's DEFF is checked.  
  **Fix**: `local deff = e(deff)[1,1]` with a comment.

- **[P3.10]** [cg-reproducibility] `.github/skills/cg-skill-stata-testing/references/reproducibility-reprun.md:24` — Column header listed as `**Seed RNG**`; actual reprun output column is `**Seed RNG State**`. Routing table entry for `reproducibility-reprun.md` implies the file has full repkit API, but it explicitly defers to `cg-skill-stata-best-practices`.  
  **Fix**: Update table header to match reprun actual output; narrow the routing description to "reprun/reproot/repscan *testing patterns* (full API → cg-skill-stata-best-practices)".

---

### ✅ Passed

- **cg-testing**: Test blocks follow Pester 3.4 syntax throughout (`Should Be`, `Should BeLessThan` — no Pester 5 flags). No `Substring` calls requiring IndexOf guards. `anti-patterns.md` cross-reference assertion is factually correct.
- **cg-version-control**: All 7 commits follow `type(scope): description` format. Commit sequence tells a coherent story. Branch name `feat/stata-testing-skill` is appropriate. No API keys or credentials.
- **cg-architecture**: Routing table completeness ✓ (all 7 reference files listed). `docs/reference.md` placement ✓. `stata.instructions.md` routing ✓. Cross-reference paths ✓. Skill boundary clear ✓.
- **cg-documentation**: Routing table rows accurately describe file content. All 7 reference files have clear structure with fenced code blocks. `workflow-examples.md` covers all 4 required examples (FGT, PPP, survey estimates, DiD). SKILL.md cross-references present ✓.
- **cg-learnings-researcher**: All 6 brainstorm areas covered. No missing scope from the brainstorm. No contradictions with past solutions (modulo the `welfare > 0` strictness in P2.9).
