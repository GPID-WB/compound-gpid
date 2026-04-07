---
plan: .cg-docs/plans/2026-04-06-testing-skill-r.md
findings:
  P1.1: fixed
  P1.2: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P2.9: skipped
  P2.10: fixed
  P2.11: skipped
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
  P3.7: fixed
  P3.8: skipped
---

## Review Report

**Review depth**: thorough
**Files reviewed**: 12 (5 modified, 7 new)
**Findings**: 2 P1, 11 P2, 8 P3

### Files Reviewed
- `.github/skills/cg-skill-r-testing/SKILL.md` (new)
- `.github/skills/cg-skill-r-testing/references/fixtures.md` (new)
- `.github/skills/cg-skill-r-testing/references/mocking.md` (new)
- `.github/skills/cg-skill-r-testing/references/snapshots.md` (new)
- `.github/skills/cg-skill-r-testing/references/bdd.md` (new)
- `.github/skills/cg-skill-r-testing/references/advanced.md` (new)
- `.github/skills/cg-skill-r-technical/references/testing-apis.md` (new)
- `.github/agents/cg-testing.agent.md` (modified)
- `.github/copilot-instructions.md` (modified)
- `.github/skills/cg-skill-r-technical/SKILL.md` (modified)
- `.github/skills/cg-skill-r-technical/references/testing-testthat.md` (modified)
- `roadmap.json` (modified)

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-data-quality] `.github/skills/cg-skill-r-testing/references/mocking.md:75` — `local_mocked_r6_class()` is a fabricated function that does not exist in testthat
  **Why**: There is no `local_mocked_r6_class()` in any version of testthat. Any developer following this example will get a "could not find function" error at runtime. This is incorrect guidance in an AI skill reference that will be used to generate test code.
  **Fix**: Remove the R6 method mocking section entirely. Replace with the correct idiom: dependency injection (pass the R6 instance as a parameter) or subclassing with `R6::R6Class(inherit = Database)`. If mocking an R6 class constructor is needed, use `local_mocked_bindings(Database = MockDB, .package = "yourpkg")`.

- **[P1.2]** [cg-data-quality] `.github/skills/cg-skill-r-testing/references/advanced.md:32` — `skip_unless_r()` does not exist in testthat; annotation "testthat 3.3.0+" references a non-existent version
  **Why**: No function `skip_unless_r()` exists in any released version of testthat. Additionally, the annotation claims it's available in "testthat 3.3.0+" — but testthat 3.3.0 has not been released (latest is 3.2.x as of April 2026). This row in the skip-functions table will cause broken tests.
  **Fix**: Remove the `skip_unless_r` table row. Replace with the correct idiom: `skip_if(getRversion() < numeric_version("4.2.0"), "requires R >= 4.2.0")`.

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-data-quality] `.github/skills/cg-skill-r-testing/SKILL.md:224` — `fmean(centered, g = dt$g)` returns a **named** vector; comparing to unnamed `c(0, 0)` breaks `expect_equal()`
  **Why**: `fmean(x, g = character_vector)` returns a named numeric vector (names = group levels, e.g., `c(a = 0, b = 0)`). `c(0, 0)` is unnamed. `expect_equal()` reports "names for target but not for current" and fails. Developers following this pattern will get false test failures on correct code.
  **Fix**: Either `unname(fmean(centered, g = dt$g))` or add `ignore_attr = TRUE`:
  ```r
  expect_equal(fmean(centered, g = dt$g), c(0, 0), tolerance = 1e-10, ignore_attr = TRUE)
  ```

- **[P2.2]** [cg-data-quality] `.github/skills/cg-skill-r-testing/references/mocking.md:57` — `local_mocked_s3_method()` requires testthat ≥ 3.2.2; no version floor documented
  **Why**: This function was introduced in testthat 3.2.2. Projects pinned to 3.0.x or 3.1.x will silently fail with "could not find function". A skill claiming "testthat 3+" compatibility must document these version floors.
  **Fix**: Add an inline comment: `# requires testthat >= 3.2.2` or a callout at the top of the S3 mocking section.

- **[P2.3]** [cg-architecture] `.github/skills/cg-skill-r-technical/SKILL.md:3` — `testthat` still listed in the skill's frontmatter `description:` after testing content was moved to `cg-skill-r-testing`
  **Why**: Agents match skills by scanning description text. With `testthat` in `cg-skill-r-technical`'s description, agents querying "write testthat tests" may load the wrong skill. This creates ambiguous routing between the two R skills.
  **Fix**: Remove `testthat` from the description. The technical skill still has the testing-apis.md reference for plumber/httr2 — scope the description accordingly: replace `"testthat, roxygen2, package development"` with `"roxygen2, package development, plumber API testing"`.

- **[P2.4]** [cg-code-quality + cg-architecture] `.github/skills/cg-skill-r-technical/references/testing-testthat.md` — file claims "redirect only" but retains ~80 lines of live code patterns
  **Why**: The file declares "This file is kept as a redirect only. All content is now in `cg-skill-r-testing`." — yet immediately follows with substantial code (test_that examples, assertions table, collapse testing patterns, data.table section). This contradiction could cause an AI to stop here believing it has complete testing patterns, rather than loading `cg-skill-r-testing`. The risk is silent skill under-loading.
  **Fix**: Strip all code content, keeping only the redirect header and the two pointer lines. Alternatively delete the file and remove the broken reference from `cg-skill-r-technical/SKILL.md`.

- **[P2.5]** [cg-documentation] `.github/skills/cg-skill-r-analytical/SKILL.md:65` — stale cross-reference points to `cg-skill-r-technical/references/testing-testthat.md` which is now deprecated
  **Why**: The analytical skill still directs economists to the old redirect file when they need testthat guidance. An economist reading this cross-reference will land on the stub, not the comprehensive `cg-skill-r-testing`. This is the only entry point for economists into R testing guidance.
  **Fix**: Replace line 65 with:
  ```
  > For comprehensive testthat patterns including collapse output testing, load `cg-skill-r-testing`.
  ```

- **[P2.6]** [cg-performance] `.github/skills/cg-skill-r-testing/references/fixtures.md:125` + `references/advanced.md:109` — `expect_valid_fgt()` defined with conflicting signatures in two files
  **Why**: `fixtures.md` defines `expect_valid_fgt(result)` checking all four FGT columns simultaneously; `advanced.md` defines `expect_valid_fgt(result, alpha = 0L)` checking only `paste0("fgt", alpha)`. Same function name, different interfaces — an AI loading both files gets contradictory definitions and may generate the wrong call.
  **Fix**: Remove `expect_valid_fgt` and `expect_valid_survey` from `fixtures.md` (lines ~116–131). Replace with a distinct, simpler example (e.g., `expect_positive_weights()`). The `advanced.md` version is canonical (more capable, parameterised `alpha`).

- **[P2.7]** [cg-testing] `tests/roadmap.Tests.ps1` — no constraint that features with `status = "done"` must have a non-null `plan`
  **Why**: The roadmap schema currently allows a feature to be marked "done" with `plan = null`. This is semantically incorrect (a completed feature should document its plan). The gap could allow future changes to mark features done without linking their plans, losing traceability.
  **Fix**: Add a schema rule in the `Test-RoadmapSchema` function:
  ```powershell
  if ($f.status -eq "done" -and $null -eq $f.plan) {
      $errors += "Feature '$($f.id)': status is 'done' but plan is null"
  }
  ```
  And add a corresponding test case.

- **[P2.8]** [cg-testing] `tests/prompt-tools.Tests.ps1` — no automated validation for SKILL.md frontmatter
  **Why**: Prompt file frontmatter is validated (description, model) but SKILL.md files have no tests. The new `cg-skill-r-testing` has valid frontmatter (`name:`, `description:`), but there's no guard against future SKILL.md files missing required fields.
  **Fix**: Add a `Describe "skill files - required frontmatter"` block that iterates `Get-ChildItem ".github\skills\*\SKILL.md"` and asserts `name:` and `description:` are present.

- **[P2.9]** [cg-version-control] Working tree — all changes are uncommitted directly on `main`; project convention requires feature branches
  **Why**: Per `copilot-instructions.md` → Version Control: "Use feature branches off main. Name them `type/short-description`." All 12 files are modified/untracked on main with no feature branch. If interrupted, changes have no PR context.
  **Fix**: Create a feature branch before committing:
  ```bash
  git checkout -b feat/r-testing-skill
  git add .
  git commit -m "feat(testing): add cg-skill-r-testing skill with 5 reference files"
  ```

- **[P2.10]** [cg-reproducibility] `.github/skills/cg-skill-r-testing/SKILL.md:420` — relative path `references/testing-apis.md` is ambiguous; does not resolve from `cg-skill-r-testing/`
  **Why**: The cross-reference reads: `see \`references/testing-apis.md\`` — this looks like a relative path from the current skill, but `testing-apis.md` lives in `cg-skill-r-technical/references/`, not `cg-skill-r-testing/references/`. A developer clicking this link will get a 404.
  **Fix**: Use an explicit relative path:
  ```markdown
  see [references/testing-apis.md](../cg-skill-r-technical/references/testing-apis.md)
  ```

- **[P2.11]** [cg-code-quality] `.github/skills/cg-skill-r-testing/references/` — reference files use bare names (`fixtures.md`, `mocking.md`, `bdd.md`, `snapshots.md`, `advanced.md`) inconsistent with naming conventions in other skills
  **Why**: All other skills use descriptive prefixed names: `collapse-reference.md`, `r-technical-anti-patterns.md`, `renv-reference.md`, `testing-apis.md`. Bare single-word names reduce discoverability and could conflict with identically-named files if files are ever bulk-copied or cross-referenced.
  **Fix**: Rename to `testing-fixtures.md`, `testing-mocking.md`, `testing-bdd.md`, `testing-snapshots.md`, `testing-advanced.md`. Update all `[references/...]` links in `SKILL.md` accordingly.

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-data-quality] `.github/skills/cg-skill-r-testing/SKILL.md:145,321` — `expect_contains()` requires testthat ≥ 3.2.0; no version note
  **Why**: `expect_contains(x, y)` was added in testthat 3.2.0. On 3.0.x/3.1.x it fails with "could not find function". The skill bills itself as "testthat 3+" so projects on 3.0.x may hit silent breakage.
  **Fix**: Add `# requires testthat >= 3.2.0` inline comment, or replace with the backward-compatible: `expect_true(all(required_cols %in% result_cols))`.

- **[P3.2]** [cg-data-quality] `.github/skills/cg-skill-r-testing/references/mocking.md:100–115` — httr2 mock uses `local_mocked_bindings(req_perform = …)` while `testing-apis.md` uses `httr2::with_mocked_responses()`
  **Why**: Two different strategies for the same task across two files within the same skill ecosystem. `httr2::with_mocked_responses()` (httr2 ≥ 1.0.0) is the purpose-built mock API and more stable across httr2 refactors. Split guidance confuses developers choosing between files.
  **Fix**: Standardize on `httr2::with_mocked_responses()` in `mocking.md` for the httr2 example, matching `testing-apis.md`. Reserve `local_mocked_bindings` for non-httr2 network calls.

- **[P3.3]** [cg-documentation] `.cg-docs/solutions/testing-patterns/2026-03-18-plumber-make-req-helper-for-unit-tests.md:86,95` — references non-existent path `cg-skill-r-technical/workflows/testing-testthat.md`
  **Why**: The solution doc says the pattern now lives in `workflows/testing-testthat.md` — no such path exists. The make_req content actually moved to `references/testing-apis.md`. This is in a past solution doc, so lower urgency.
  **Fix**: Update both references to point to `cg-skill-r-technical/references/testing-apis.md`.

- **[P3.4]** [cg-performance] `.github/skills/cg-skill-r-testing/references/advanced.md` — "File System Discipline" section duplicated from `references/fixtures.md`
  **Why**: Both files advise the same rule (always use `withr::local_tempfile()`, never write to CWD). An AI loading both files during a CRAN + fixtures task processes identical prose twice, wasting context budget.
  **Fix**: In `advanced.md`, replace the section with a one-line callout: `> See [fixtures.md — File System Discipline](fixtures.md#file-system-discipline) for the temp-dir pattern.`

- **[P3.5]** [cg-architecture] `.github/agents/cg-architecture.agent.md` — not updated to mention `cg-skill-r-testing` when reviewing test directory structure
  **Why**: The testing agent was updated to load `cg-skill-r-testing`, but `cg-architecture.agent.md` still only references `cg-skill-r-technical` and `cg-skill-r-analytical`. When reviewing test architecture (fixture placement, helper organization), the architecture agent has no instruction to load the testing skill.
  **Fix**: Add to the R expertise line: "Load `cg-skill-r-testing` when reviewing test directory structure or fixture organization."

- **[P3.6]** [cg-architecture] `.github/copilot-instructions.md` — no guidance for dual-skill loading when writing API tests
  **Why**: Instructions say "Load `cg-skill-r-testing` when writing, reviewing, or debugging R tests" — correct, but incomplete. The new `testing-apis.md` pattern requires *both* skills simultaneously (plumber/httr2 domain from `cg-skill-r-technical` + test patterns from `cg-skill-r-testing`). Users invoking the skill directly won't know.
  **Fix**: Add a parenthetical: "Load `cg-skill-r-testing` when writing, reviewing, or debugging R tests (also load `cg-skill-r-technical` if tests cover plumber endpoints or httr2 clients)."

- **[P3.7]** [cg-testing] `tests/roadmap.Tests.ps1` — no positive test case for `status = "done"` + valid plan string
  **Why**: Related to P2.7. Even without enforcing the constraint, a positive test case would document the expected valid state explicitly.
  **Fix**: Add a positive test: feature with `status = "done"` and `plan = ".cg-docs/plans/…"` should produce zero errors from `Test-RoadmapSchema`.

- **[P3.8]** [cg-version-control] Uncommitted changes mix multiple logical concerns without clear commit boundary
  **Why**: The 12 changed files span: new skill (8 files), agent update (1), instructions update (1), skill-technical update (2), roadmap (1), brainstorm/plan (2). A single monolithic commit loses granularity for bisect/revert.
  **Fix**: Consider 2–3 focused commits: (1) new skill + reference migration, (2) agent + instructions updates, (3) roadmap + cg-docs artifacts.

---

### ✅ Passed
- **cg-data-quality**: All collapse API signatures correct (`fmean(x, w = weights)`, `collap()`, `GRP()`, `fwithin()`, `TRA = "replace"`); math in weighted-mean examples verified accurate
- **cg-data-quality**: `roadmap.json` new feature object (`skill-description-consistency-audit`) has all required fields; `"status": "idea"` + `"plan": null` is consistent with all other idea-status features
- **cg-performance**: No tidyverse patterns found in any example code — all use data.table/collapse correctly
- **cg-performance**: All 6 skill files are under 450 lines; total load cost ~1840 lines if all loaded simultaneously; SKILL.md is self-sufficient without reference files
- **cg-performance**: Reference files cover distinct topics with minimal cross-pollution
- **cg-reproducibility**: All data-generating examples use `set.seed(seed)` with deterministic defaults; `test_path()` used consistently for fixture access
- **cg-reproducibility**: Plan completion date (`2026-04-06`) matches today's date
- **cg-documentation**: SKILL.md covers all required sections (setup, file organization, test structure, running tests, core expectations, design principles, common patterns, snapshots, mocking, fixtures, BDD); all 5 reference files present and titled
- **cg-documentation**: `cg-testing.agent.md` correctly loads `cg-skill-r-testing` as first R skill
- **cg-documentation**: `testing-apis.md` self-documents its placement rationale; `cg-skill-r-testing` description correctly says "Load alongside cg-skill-r-technical for plumber/httr2"
- **cg-version-control**: No sensitive data, credentials, or API keys in any new file; `.cg-docs/` correctly NOT gitignored; no lockfile changes expected for documentation-only work
- **cg-reproducibility**: Cross-references to `cg-skill-r-technical` and `cg-skill-r-analytical` are correctly spelled and linked (except P2.10 path issue)
- **cg-architecture**: `testing-apis.md` placement in `cg-skill-r-technical/references/` is well-justified; `cg-skill-r-testing` skill registration is complete and discoverable
