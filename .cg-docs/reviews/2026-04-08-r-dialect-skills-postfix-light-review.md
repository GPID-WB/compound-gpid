---
plan: .cg-docs/plans/2026-04-07-r-dialect-skills-architecture.md
findings:
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: skipped
  P3.5: fixed
  P3.6: skipped
  P3.7: fixed
---

## Review Report

**Review depth**: light
**Branch**: `feat/r-dialect-skills`
**Files reviewed**: 45 (all changed files between `main` and `feat/r-dialect-skills`)
**Agents dispatched**: cg-code-quality, cg-testing
**Findings**: P1 × 0, P2 × 5, P3 × 7

---

### P1 — CRITICAL (must fix before merge)

None.

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `.github/copilot-instructions.md:37` — Label says "Six R skills" but 7 are listed (and 8 exist including `cg-skill-r-shared`).
  **Why**: `cg-skill-r-shared` is loaded unconditionally by `r.instructions.md` (line 19) as the base R style reference, making it the 8th R skill. The label is factually wrong, which will confuse users trying to understand the routing architecture.
  **Fix**: Update to: `- **Eight R skills**: R work is covered by eight skills. ...` and append `cg-skill-r-shared` to the end of the description: `` `cg-skill-r-shared` provides universal base R style rules (`<-` assignment, `snake_case`, `TRUE`/`FALSE`) that apply regardless of dialect. ``

- **[P2.2]** [cg-testing] `tests/update.Tests.ps1` (~line 1060) — No test covers multiple release tags pointing to the same HEAD commit.
  **Why**: `git tag --points-at HEAD` can return multiple tags (e.g. if someone creates a tag alias). `update.ps1` takes `$headTags[0]` — correct behavior — but no test documents or validates this. If the selection logic were changed to another index, it would silently go untested.
  **Fix**: Add test: `It "selects first tag when multiple release tags point to HEAD"` — simulate `$headTags = @("v0.4.3", "v0.4.3-alias")` and verify arrow appears on `v0.4.3`.

- **[P2.3]** [cg-testing] `tests/update.Tests.ps1` (~line 1060) — No test documents git-failure path for `git tag --points-at HEAD`.
  **Why**: If git fails (network issues, corrupt repo), `$headTags` is empty and `$installedTag` stays `$null` — correct behavior. But the test suite doesn't document this path, making it invisible to future maintainers.
  **Fix**: Add test: `It "shows no arrow when git tag --points-at HEAD fails"` — simulate empty `$headTags` → `$installedTag = $null` → no arrows in output.

- **[P2.4]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test verifies `applyTo` patterns in `r.instructions.md`.
  **Why**: `r.instructions.md` uses `applyTo: "**/*.R,**/*.r,**/*.Rmd"` — if this field is accidentally removed or misspelled, the entire dialect routing stops working for all R files with no visible error. There is no test asserting this field exists and contains the expected extensions.
  **Fix**: Add `Describe "r.instructions.md - applyTo validation"` with tests for `*.R`, `*.r`, and `*.Rmd` in the `applyTo` frontmatter field.

- **[P2.5]** [cg-testing] `.github/skills/cg-skill-r-testing/SKILL.md`, `cg-skill-r-shared/SKILL.md`, `cg-skill-r-technical/SKILL.md` — Missing `user-invokable: false` frontmatter field while the other four dialect skills carry it.
  **Why**: `cg-skill-r-collapse`, `cg-skill-r-datatable`, `cg-skill-r-tidyverse`, `cg-skill-r-visualization` all have `user-invokable: false`. Omitting it from the remaining three creates inconsistency that could lead to them appearing erroneously in user-invokable skill lists.
  **Fix**: Add `user-invokable: false` to the YAML frontmatter of `cg-skill-r-testing/SKILL.md`, `cg-skill-r-shared/SKILL.md`, and `cg-skill-r-technical/SKILL.md`.

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-testing] `tests/update.Tests.ps1` (~line 1090) — Missing edge case: HEAD at a dev tag in latest mode.
  **Why**: `git tag --points-at HEAD` filtered through `$ReleaseTagPattern` correctly excludes dev tags (`v0.4.3.9000`), leaving `$installedTag = $null` and no arrow. This correct behavior isn't documented by a test case.
  **Fix**: Add test: `It "shows no arrow when HEAD points to a dev tag in latest mode"`.

- **[P3.2]** [cg-testing] `tests/update.Tests.ps1` (~lines 1074–1115) — Tests inline `'^v\d+\.\d+\.\d+$'` instead of sourcing `$ReleaseTagPattern` from the script.
  **Why**: If `$ReleaseTagPattern` in `update.ps1` ever changes, these tests won't catch the divergence. Maintenance burden.
  **Fix**: Add comment `# MUST match $ReleaseTagPattern in scripts/update.ps1` above the inlined pattern in the test, or extract as a shared constant.

- **[P3.3]** [cg-code-quality] `docs/reference.md` — `cg-skill-r-testing` description omits mocking, fixtures, BDD, and snapshot coverage.
  **Why**: The SKILL.md covers `describe()`/`it()`, mocking with `local_mocked_bindings()`, snapshots, and BDD-style testing — none of which appear in the registry description. Maintainers using reference.md won't know when to load this skill.
  **Fix**: Expand description to: `"testthat 3+ patterns: test_that(), describe()/it(), fixtures, mocking (local_mocked_bindings()), snapshots, BDD-style testing. Dialect-aware: data.table test data for collapse/data.table projects, tibble for tidyverse."`

- **[P3.4]** [cg-code-quality] `.github/agents/cg-code-quality.agent.md:16` — `data.table-collapse` written inconsistently across agent files.
  **Why**: Some lines use the exact config value `data.table-collapse` (hyphenated); others use shorthand like "data.table + collapse" or just "collapse". In `compound-gpid.local.md` the field value is `"data.table-collapse"` — agents should match this exactly when referring to the configured dialect to avoid confusion.
  **Fix**: Audit all three agent files for the string. Replace informal shorthands with the canonical value `data.table-collapse` when referring to the `r-syntax` configuration value.

- **[P3.5]** [cg-code-quality] `tests/update.Tests.ps1:1282–1283` — Hardcoded schema version string `"2026-03-05-cg-docs"` repeated without a comment.
  **Why**: Occurs twice in the same describe block with no comment indicating it must match `scripts/update.ps1`. Silent maintenance hazard.
  **Fix**: Add inline comment: `# MUST match $SchemaVersion in scripts/update.ps1`.

- **[P3.6]** [cg-code-quality] `tests/update.Tests.ps1` — DRY: migration test contexts repeat the same setup/assert pattern ~5 times.
  **Why**: Brainstorms, plans, and solutions migration contexts each repeat the same ~15-line pattern. Style issue only — no correctness risk — but increases maintenance cost.
  **Fix**: Low priority. Extract `Test-Migration` helper if the pattern grows further.

- **[P3.7]** [cg-code-quality] `.github/copilot-instructions.md` — `cg-skill-r-shared` not mentioned in the R skills entry at line 37.
  **Why**: Even after fixing the count (P2.1), `cg-skill-r-shared` needs to be described alongside the other seven. It is the universal base R style skill that applies regardless of dialect.
  **Fix**: Add to the end of the existing skills sentence: ``Additionally, `cg-skill-r-shared` provides universal base R style rules that apply regardless of dialect.``

---

### ✅ Passed

- **cg-code-quality**: Agent frontmatter dialect-conditional language is correct and consistent post-fix; `r.instructions.md` routing is clean; README/ROADMAP updated; `docs/reference.md` has all new skills registered; no broken cross-references in skill files; `update.ps1` PowerShell idioms are correct
- **cg-testing**: Core arrow fix (main case + between-releases case) well tested; SKILL.md presence and frontmatter covered in `prompt-tools.Tests.ps1`; no data corruption or security issues
