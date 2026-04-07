---
plan: .cg-docs/plans/2026-04-06-testing-skill-r.md
findings:
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P3.1: fixed
  P3.2: skipped
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
---

## Review Report

**Review depth**: light
**Files reviewed**: 15 (10 modified, 5 new)
**Findings**: 0 P1 · 4 P2 · 5 P3

### P1 — CRITICAL (must fix before merge)

_None._

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `.github/skills/cg-skill-r-technical/SKILL.md` — Footer cross-reference mentions `set_collapse` as part of the collapse API, but `set_collapse(mask = ...)` is explicitly prohibited in the same file.
  **Why**: Contradictory documentation: the footer sends readers to a reference that includes a prohibited function by name, creating confusion about whether it's safe to use.
  **Fix**: Remove `set_collapse` from the footer listing — change `"global options, \`set_collapse\`, \`use.g.names\`..."` to `"global options, \`use.g.names\`..."`, keeping the prohibition in the body clear.

- **[P2.2]** [cg-code-quality] `.github/skills/cg-skill-r-testing/references/advanced.md` — Version floor comments are inconsistent: `local_mocked_s3_method()` has an inline `# Requires testthat ≥ 3.2.2` comment, but `snapshot_review()` (requires 3.3.0+) and other version-gated functions have no such annotation.
  **Why**: Developers scanning the file may use version-gated functions without realizing the requirement, causing silent test failures on older testthat installs.
  **Fix**: Add version floor annotations to all version-dependent functions in advanced.md, or add a single compatibility table at the top of the file listing `function → minimum testthat version`.

- **[P2.3]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No tests verify that all 6 files of the new `cg-skill-r-testing` skill exist at the correct paths.
  **Why**: The implementation plan explicitly called for a structural check: "All 6 files exist in the correct paths." Without this test, a broken installation (e.g., missing `references/bdd.md`) would pass the test suite silently.
  **Fix**: Add a Pester `Describe` block verifying the existence of:
  ```
  .github/skills/cg-skill-r-testing/SKILL.md
  .github/skills/cg-skill-r-testing/references/bdd.md
  .github/skills/cg-skill-r-testing/references/mocking.md
  .github/skills/cg-skill-r-testing/references/fixtures.md
  .github/skills/cg-skill-r-testing/references/snapshots.md
  .github/skills/cg-skill-r-testing/references/advanced.md
  ```

- **[P2.4]** [cg-testing] `tests/roadmap.Tests.ps1` — No test verifies that plan files referenced by `done` features in `roadmap.json` actually exist on disk.
  **Why**: `roadmap.json` now requires `plan` to be non-null for done features (constraint added and tested), but a stale or incorrect path would pass the constraint test. If the plan file is deleted or renamed, no test catches the broken reference.
  **Fix**: Add a test case:
  ```powershell
  It "plan files referenced in done features exist on disk" {
      $doneFeatures = $milestones.features | Where-Object { $_.status -eq "done" -and $null -ne $_.plan }
      foreach ($f in $doneFeatures) {
          Test-Path (Join-Path $repoRoot $f.plan) | Should -BeTrue -Because "done feature '$($f.id)' references '$($f.plan)'"
      }
  }
  ```

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-testing] `.github/skills/cg-skill-r-testing/references/mocking.md` — The version requirement for `local_mocked_s3_method()` (testthat ≥ 3.2.2) is noted in an inline comment but is not visible in the section header or a callout box. Developers skimming the section may miss it.
  **Why**: Inline comments in code examples are easy to overlook; a visible callout improves discoverability.
  **Fix**: Add a blockquote callout at the start of the "S3 Method Mocking" section: `> **Requires testthat ≥ 3.2.2.** Available since testthat 3.2.2.`

- **[P3.2]** [cg-code-quality] `.cg-docs/reviews/2026-04-06-testing-skill-r-review.md` — YAML frontmatter lists `P2.9: skipped` and `P2.11: skipped`, but neither finding appears in the report body, making it impossible to understand what was skipped or why.
  **Why**: Skipped findings should be traceable; if their text is missing from the report body, future reviewers cannot assess whether they should be revisited.
  **Fix**: Either add brief entries for P2.9 and P2.11 under the P2 section (even if short) with a `~~Skipped:~~` note and rationale, or document the rationale in the frontmatter as a comment.

- **[P3.3]** [cg-code-quality] `.github/agents/cg-testing.agent.md` — References `references/testing-apis.md` without the parent skill path, making it ambiguous which skill the file belongs to.
  **Why**: Minor ambiguity that could cause confusion if both `cg-skill-r-technical` and `cg-skill-r-testing` have similar reference filenames in the future.
  **Fix**: Use the full path: `cg-skill-r-technical/references/testing-apis.md`.

- **[P3.4]** [cg-code-quality] `tests/roadmap.Tests.ps1` — The schema test does not validate that all `plan` field values match the expected pattern `^\.cg-docs\/(brainstorms|plans|reviews|solutions)\/.*\.md$`.
  **Why**: A typo in a plan path (e.g., `.cg-doc/` instead of `.cg-docs/`) would pass existing tests but silently break the reference.
  **Fix**: Add a regex assertion to the schema validation loop:
  ```powershell
  if ($null -ne $f.plan -and $f.plan -notmatch '^\.cg-docs/(brainstorms|plans|reviews|solutions)/.*\.md$') {
      $errors += "Feature '$($f.id)': plan path '$($f.plan)' does not match expected pattern"
  }
  ```

- **[P3.5]** [cg-testing] `tests/` — No tests validate that markdown cross-references within skill files resolve to existing files (e.g., links from `cg-skill-r-testing/SKILL.md` to `cg-skill-r-technical/references/testing-apis.md`).
  **Why**: Manual review found and fixed one broken cross-reference (P2.10 in prior thorough review). Without an automated check, future edits could re-introduce dangling links.
  **Fix**: Add a test that parses all `[text](../path)` links in SKILL.md and reference files, resolves relative paths, and asserts those files exist. This is an enhancement — low blocking priority.

### ✅ Passed

- **cg-code-quality**: All P1 and P2 findings from the prior thorough review are confirmed fixed; cross-references between skill files are correct; DRY patterns in testing-testthat.md (now a redirect stub) and the new SKILL.md are clean; PowerShell test structure is consistent; roadmap.json field naming is consistent
- **cg-testing**: Fabricated functions (`local_mocked_r6_class`, `skip_unless_r`) removed; `fmean()` named vector fix (`ignore_attr = TRUE`) confirmed; roadmap done→plan constraint added and tested; SKILL.md frontmatter validation added to prompt-tools.Tests.ps1; plan document marked completed
