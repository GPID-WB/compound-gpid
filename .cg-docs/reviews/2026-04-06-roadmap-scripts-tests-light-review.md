---
plan: null
findings:
  P1.1: fixed
  P1.2: fixed
  P2.1: skipped
  P2.2: skipped
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P2.9: fixed
  P3.1: fixed
---

## Review Report

**Review depth**: light
**Files reviewed**: 20
**Findings**: 2 P1, 9 P2, 1 P3

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-testing] `tests/roadmap.Tests.ps1` — `roadmap.json` never validated against schema
  **Why**: `Test-RoadmapSchema` helper function is thoroughly unit-tested, but no test loads the actual `roadmap.json` from the repository and validates it. The actual data file is never verified to pass the rules it claims to follow.
  **Fix**: Add a Describe block that loads `roadmap.json`, parses it, runs `Test-RoadmapSchema`, and asserts zero errors.

- **[P1.2]** [cg-testing] `roadmap.json` — Milestone `quality-loop` status violates derived status rule
  **Why**: The milestone has 6 "idea" + 1 "done" feature, which should derive to "in-progress" (per cascade logic: any-done = in-progress), but status is set to "planned". This would be caught immediately by a test added in P1.1.
  **Fix**: Update `roadmap.json` milestone `quality-loop` status from `"planned"` to `"in-progress"`.

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `scripts/link.ps1:37`, `scripts/update.ps1:47` — DRY violation: install location error message duplicated
  **Why**: The validation error message for missing `$CompoundGpidDir` appears identically in both files. Each file has a comment acknowledging the duplication ("Adding a new environment? Update this message and the matching one in scripts/update.ps1").
  **Fix**: Extract the error message as a shared constant or dot-sourced helper so updates happen in one place.

- **[P2.2]** [cg-code-quality] `tests/charter.Tests.ps1:24` — Inconsistent YAML frontmatter parsing regex
  **Why**: `charter.Tests.ps1` uses `(?s)^---\r?\n(.*?)\r?\n---` while `prompt-tools.Tests.ps1` uses the more robust `(?s)^---\s*\r?\n(.+?)\r?\n---` (handles optional trailing whitespace after `---`, requires at least one character with `.+?`). Divergence can cause subtle parsing differences.
  **Fix**: Update `charter.Tests.ps1` to use `(?s)^---\s*\r?\n(.+?)\r?\n---`, or call the shared `Get-Frontmatter` helper already defined in `prompt-tools.Tests.ps1`.

- **[P2.3]** [cg-testing] `tests/link.Tests.ps1` — Missing test for legacy `.cg-docs` gitignore cleanup (Step 5b)
  **Why**: `link.ps1` has explicit cleanup logic to remove stale `# Compound GPID knowledge base` markers and `.cg-docs/` entries left from older versions. No test verifies this or handles edge cases (marker without entry, entry without marker).
  **Fix**: Add a Context block testing marker+entry removal, including partial-presence edge cases.

- **[P2.4]** [cg-testing] `tests/link.Tests.ps1` — Missing test for `.gitignore` update idempotency
  **Why**: `link.ps1` updates `.gitignore` with CG-managed entries. Tests don't verify that duplicate runs don't create duplicate blocks, Windows `\r\n` line endings are handled correctly, or user content is preserved alongside the CG block.
  **Fix**: Add a test that runs the gitignore write twice and asserts exactly one CG-managed block is present.

- **[P2.5]** [cg-testing] `tests/link.Tests.ps1` — Missing test for `update.ps1` call failure handling
  **Why**: `link.ps1` calls `update.ps1` in a try/catch with a warning fallback. Tests don't verify that linking continues when `update.ps1` throws, or the case where it exits non-zero but doesn't throw.
  **Fix**: Add a test simulating `update.ps1` failure that confirms the rest of the link logic still completes.

- **[P2.6]** [cg-testing] `tests/link.Tests.ps1` — Missing test for junction accessibility verification (Step 6)
  **Why**: `link.ps1` Step 6 verifies `cg-setup.prompt.md` is accessible through the junction, only emitting a warning on failure. No test verifies the check works or triggers correctly.
  **Fix**: Add a test asserting verification fails gracefully when `cg-setup.prompt.md` is absent from the target directory.

- **[P2.7]** [cg-testing] `tests/update.Tests.ps1` — Missing test for `--fix` repair partial failure handling
  **Why**: `update.ps1 --fix` runs `git clean -fd`, `git checkout .`, and `git pull` in sequence. Tests don't verify partial success states (e.g., clean succeeds but checkout fails).
  **Fix**: Add tests simulating per-step failures to verify recovery behavior for each step.

- **[P2.8]** [cg-testing] `tests/update.Tests.ps1` — Missing test for `.cg-version` file parsing edge cases
  **Why**: `update.ps1` reads `.cg-version` and validates format with `$VersionAcceptPattern`. Tests don't cover: multi-line file, leading/trailing whitespace, empty file (should default to "latest"), or garbage input like `"v0.2.0 some comment"`.
  **Fix**: Add tests for each edge case: multi-line, whitespace-padded, empty, and invalid content.

- **[P2.9]** [cg-testing] `tests/update.Tests.ps1` — Missing test for `--list` mode dev tag filtering
  **Why**: `update.ps1 --list` should show only 3-component release tags (e.g., `v0.2.0`) and hide 4-component dev tags (e.g., `v0.2.0.9000`). Tests don't verify dev tags are filtered, sorting is correct, or current version indication is accurate.
  **Fix**: Add a test asserting that 4-component tags are excluded from `--list` output.

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `docs/reference.md:25` — Imprecise `/cg-resume` description
  **Why**: The reference table says "Load context and pick up interrupted work" but the prompt also performs schema version checks, warns about migrations, and scans for stale plans.
  **Fix**: Update to: "Load context, check schema version, scan pending work, and resume interrupted sessions."

### ✅ Passed

- cg-code-quality: No security issues, hardcoded credentials, or magic numbers found
- cg-code-quality: Prompts, documentation, and script structure are well-organized with consistent naming conventions
- cg-testing: `charter.Tests.ps1` and `prompt-tools.Tests.ps1` cover their domains solidly
