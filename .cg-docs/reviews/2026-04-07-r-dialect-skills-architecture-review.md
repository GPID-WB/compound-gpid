---
plan: .cg-docs/plans/2026-04-07-r-dialect-skills-architecture.md
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P2.9: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
---

## Review Report

**Review depth**: thorough  
**Branch**: `feat/r-dialect-skills`  
**Files reviewed**: 33 (all changed files between `main` and `feat/r-dialect-skills`)  
**Agents dispatched**: cg-code-quality, cg-testing, cg-documentation, cg-version-control, cg-architecture, cg-reproducibility, cg-performance, cg-data-quality, cg-learnings-researcher  
**Findings**: P1 × 5, P2 × 9, P3 × 6

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-architecture] `.github/agents/cg-code-quality.agent.md:12` — Hardcoded `collapse > data.table > tidyverse` hierarchy defeats the dialect system.  
  **Why**: When `/cg-review` runs on a `r-syntax: "tidyverse"` project, this agent flags correct tidyverse patterns (`filter()`, `if_else()`, dplyr joins) as violations and suggests data.table replacements. Produces actively wrong review feedback.  
  **Fix**: Replace the hardcoded hierarchy with dialect-conditional language: *"Check `compound-gpid.local.md` for `r-syntax`. For `data.table-collapse`: flag `ifelse()` instead of `fifelse()`, missing `:=`. For `tidyverse`: flag `%>%`, `.data$`, old-style `group_by()/ungroup()`. Load dialect skills per `r.instructions.md` before reviewing."*

- **[P1.2]** [cg-architecture] `.github/agents/cg-data-quality.agent.md:12` — Same hardcoded hierarchy leakage.  
  **Why**: Data validation idioms hardcoded to `checkmate` + data.table will be misapplied to tibble-based tidyverse projects. The `r.instructions.md` routing is bypassed entirely by this agent.  
  **Fix**: Same dialect-conditional pattern as P1.1. Replace the hierarchy line with `r-syntax`-conditional guidance.

- **[P1.3]** [cg-architecture] `.github/agents/cg-performance.agent.md:12` — Same hardcoded hierarchy. Section 2 asks "Are `collapse` functions used instead of dplyr?" — wrong question on a tidyverse project.  
  **Why**: Reviewing a tidyverse project with this agent would flag correct `mutate()` + `summarize()` usage as a performance issue. Incorrect results.  
  **Fix**: Same dialect-conditional pattern. Rename "collapse + data.table Optimization" section to "Vectorization and Aggregation (R)" and condition questions on the detected dialect.

- **[P1.4]** [cg-data-quality] `.github/skills/cg-skill-r-tidyverse/references/tidyverse-reference.md:127` — `.by = region` passed inside `across()`, not at the `summarize()` level.  
  **Why**: `across(c(welfare, income), fmean, .by = region)` passes `.by` as a named argument to `fmean()`. The `fmean()` function has no `.by` argument (it uses `g =`), so the grouping is silently ignored — the aggregation runs ungrouped, returning wrong results with no error.  
  **Fix**: Move `.by` to the outer `summarize()` call:
  ```r
  dt |> summarize(across(c(welfare, income), fmean), .by = region)
  ```

- **[P1.5]** [cg-data-quality] `.github/skills/cg-skill-r-collapse/references/collapse-reference.md:268` — Fabricated `%=%` operator that does not exist in collapse.  
  **Why**: `dt %=% list(log_welfare = log(welfare))` — this operator doesn't exist in collapse (arithmetic in-place operators like `%+=%` do exist, but not list-assignment `%=%`). Code following this example errors with `could not find function "%=%"`.  
  **Fix**: Remove the line. The correct pattern is already shown on the line above: `settransform(dt, log_welfare = log(welfare))`.

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-architecture / cg-performance] `.github/instructions/r.instructions.md:18-48` — Router carries 30+ lines of non-routing Package Development, Error Handling, and Style content.  
  **Why**: These rules are injected into context for *every* `.R` file via `applyTo` — including routine analysis scripts with no packages. "A thin router should be 12–15 lines of routing logic only." Creates context bloat and ambiguity about what is canonical.  
  **Fix**: Move Package Development (`@importFrom`, `usethis`, `renv`, `NAMESPACE`) and Error Handling (`rlang::abort`, `cli::cli_abort`) sections to `cg-skill-r-technical`. Move base R Style rules to `cg-skill-r-shared` (which otherwise has no real content). Keep `r.instructions.md` as routing only.

- **[P2.2]** [cg-architecture] `.github/skills/cg-skill-r-testing/SKILL.md:8` — Dialect-blind; explicitly forbids tidyverse in tests.  
  **Why**: Line 8: *"Tidyverse is never used in test code unless annotated as a fallback."* On a tidyverse project, tests naturally use `tibble()` + dplyr. This skill wasn't updated in the dialect refactoring and contradicts the new architecture.  
  **Fix**: Update line 8 to: *"Default examples use data.table + collapse. If your project uses `r-syntax: 'tidyverse'`, test data construction uses `tibble()` and dplyr; statistical assertions still use collapse functions on tibbles."* Update the `description` field similarly.

- **[P2.3]** [cg-architecture / cg-performance] `.github/skills/cg-skill-r-shared/SKILL.md` — Vestigial dead skill; nothing references it after the refactoring.  
  **Why**: The skill body is now only a redirect note saying collapse anti-patterns moved. The `description` field is misleading. It occupies a slot in the skill registry without providing actionable content.  
  **Fix**: Either (a) delete the folder entirely, or (b) repurpose it to hold the base R style rules from `r.instructions.md` (which addresses P2.1 simultaneously). Option (b) is preferred.

- **[P2.4]** [cg-data-quality] `.github/instructions/r.instructions.md:7-9` — No fallback or warning for invalid/unrecognized `r-syntax` values.  
  **Why**: Values like `"base-r"`, `"dplyr"`, or typos silently match neither branch, loading no dialect skill. User gets inconsistent guidance with no warning.  
  **Fix**: Add an explicit catch-all: *"Any other value or field absent → default to `data.table-collapse`. Warn the user the value is not recognized; accepted values are `"data.table-collapse"` and `"tidyverse"`."*

- **[P2.5]** [cg-data-quality] `.github/skills/cg-skill-r-tidyverse/references/tidyverse-reference.md:97` — `flag(welfare, 1)` inside `mutate(.by = country)` without a time variable.  
  **Why**: `flag(welfare, 1)` without `t =` computes a positional lag — correct only if each group is already sorted by time. Unsorted data returns wrong lags silently with no error.  
  **Fix**: Add the time argument: `flag(welfare, 1, t = year)` and note the ordering requirement.

- **[P2.6]** [cg-documentation / cg-code-quality] `docs/reference.md` — Skills table lists only old 3 R skills with stale hierarchy language; Configuration section missing `r-syntax` field documentation.  
  **Why**: The docs are the first place users look for the new dialect routing feature. Missing or wrong entries create immediate confusion.  
  **Fix**: (a) Update Skills table to list all 6 R skills with dialect-neutral descriptions; remove "Preference hierarchy" language. (b) Add a Configuration Fields section documenting `r-syntax: "data.table-collapse"` and `r-syntax: "tidyverse"` with explanations.

- **[P2.7]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No tests for dialect routing or new skill presence.  
  **Why**: The router's logic and new skill files have no automated validation. If a skill directory is accidentally deleted or the routing logic is broken, no test will catch it.  
  **Fix**: Add to `prompt-tools.Tests.ps1`:
  1. Verify `r.instructions.md` exists and references all 6 R skill names
  2. Verify each of the 4 dialect skill directories has a `SKILL.md`
  3. Verify `cg-skill-setup/SKILL.md` contains `r-syntax`, `data.table-collapse`, and `tidyverse`

- **[P2.8]** [cg-reproducibility] `compound-gpid.local.md:6` — `cg-schema-version` is still `"2026-03-25-project-charter"` after the `SCHEMA_VERSION` bump to `2026-04-07-r-syntax-dialect`.  
  **Why**: Schema version tracking is inconsistent. Any future migration tooling would misidentify this config as pre-dialect. The `update.ps1` script stamps `SCHEMA_VERSION` into new projects; the canonical example should match.  
  **Fix**: Update `compound-gpid.local.md` line 6 to `cg-schema-version: "2026-04-07-r-syntax-dialect"`.

- **[P2.9]** [cg-documentation] `README.md` — No mention of R dialect selection feature.  
  **Why**: Per-project R syntax selection (`data.table-collapse` vs `tidyverse`) is a significant new user-facing capability. External coauthors benefit directly from this. The README is the entry point for new users.  
  **Fix**: Add a brief mention in the Key Benefits or Features section, linking to `docs/reference.md` for details.

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `datatable-anti-patterns.md` + `r-technical-anti-patterns.md` — DRY violation: `ifelse()` vs `fifelse()` anti-pattern duplicated in both files with different examples.  
  **Fix**: Use `datatable-anti-patterns.md` as canonical; replace the `r-technical-anti-patterns.md` version with a cross-reference link.

- **[P3.2]** [cg-performance] `.github/skills/cg-skill-r-collapse/references/collapse-reference.md` — Monolithic 402-line reference; entire file loaded whenever any collapse function is mentioned.  
  **Fix**: Split into `collapse-core.md` (~150 lines: FSFs, TRA, GRP, `collap()`, `fwithin`/`fbetween`) and `collapse-advanced.md` (~130 lines: panel operators, `fgroup_by` pipe, S3 dispatch, aliases).

- **[P3.3]** [cg-code-quality] `.github/skills/cg-skill-r-tidyverse/references/tidyverse-reference.md` — Weighted statistics section uses `fmean()` without linking to or cross-referencing `cg-skill-r-collapse`.  
  **Fix**: Add a note: *"Load `cg-skill-r-collapse` for full weighted statistics reference. These functions work identically on tibbles."*

- **[P3.4]** [cg-architecture] `ROADMAP.md` — `cg-skill-r-technical` and `cg-skill-r-analytical` entries still describe their old content (collapse, data.table). Skills are now syntax-neutral.  
  **Fix**: Update entries to match the current `SKILL.md` frontmatter descriptions.

- **[P3.5]** [cg-architecture / cg-data-quality] `compound-gpid.local.md` — No `r-syntax` field despite `language: "both"` (R + Python). Silent default applies.  
  **Fix**: Add `r-syntax: "data.table-collapse"` to make the active dialect explicit at the project level.

- **[P3.6]** [cg-performance] `.github/skills/cg-skill-r-tidyverse/SKILL.md` — `tidyverse-migration.md` listed without a context qualifier; may be loaded unnecessarily for native tidyverse users.  
  **Fix**: Add a qualifier to the reference: *"Load only when translating existing data.table or base R code to tidyverse equivalents."*

---

### ✅ Passed

- **cg-version-control**: Conventional commit format correct, sensitive data absent, `.gitignore` complete, branch naming follows convention, file deletions clean (no orphaned references), schema version bump appropriate.
- **cg-reproducibility**: Routing logic is deterministic; backward compatibility for missing `r-syntax` explicit and documented in 3 places; no new dependencies introduced; relative path depths correct in all new skill files.
- **cg-learnings-researcher**: Architecture aligns with the original brainstorm decision (`2026-04-07-r-syntax-dialect-skills.md`). The 8-location skill consolidation checklist has been followed for `docs/reference.md`, `copilot-instructions.md`, `.cg-docs/solutions/`, and agent files — **except** agent files (see P1.1–P1.3). No broken code fences detected in new files.
