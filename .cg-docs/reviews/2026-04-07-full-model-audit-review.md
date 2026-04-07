---
plan: ".cg-docs/plans/2026-04-07-full-model-audit.md"
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
  P2.9: fixed
  P2.10: fixed
  P2.11: fixed
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
**Branch**: `audit_models`  
**Files reviewed**: 10  
**Agents**: cg-code-quality, cg-testing, cg-documentation, cg-version-control, cg-architecture, cg-performance, cg-reproducibility, cg-data-quality, cg-learnings-researcher  
**Findings**: 2 P1 · 11 P2 · 10 P3

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-testing] `tests/prompt-tools.Tests.ps1:503-552` — Model assignment tests use hardcoded file lists; new files won't be caught  
  **Why**: The `$promptCases` and `$agentCases` arrays are static. Adding a new prompt or agent file without updating the test leaves it silently unvalidated. The test count stays at 22 forever.  
  **Fix**: Replace hardcoded arrays with dynamic discovery via `Get-ChildItem` on `.github/prompts` and `.github/agents`, then assert each discovered file has a `model:` frontmatter key. Add count sentinel assertions (`Should Be 12` and `Should Be 10`) to catch unexpected additions.

- **[P1.2]** [cg-testing] `tests/prompt-tools.Tests.ps1:515-552` — No file existence check before `Get-Frontmatter` calls in model tests  
  **Why**: If a path is misspelled, `Get-Content` throws a scope-level exception, causing the entire `Describe` block to error rather than a clean test failure. Root cause is obscured.  
  **Fix**: Add `Test-Path $filePath | Should Be $true` as the first assertion in each `It` block before calling `Get-Frontmatter`.

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `tests/prompt-tools.Tests.ps1:503-552` — DRY violation: two near-identical `Describe` blocks for prompt and agent model tests  
  **Why**: Both blocks use identical structure (build array → foreach → extract frontmatter → assert match). Copy-paste increases maintenance burden.  
  **Fix**: Extract a shared helper or combine into one parameterized `Describe "Model assignments"` sweep. (Note: resolving P1.1 with dynamic discovery would naturally eliminate this duplication.)

- **[P2.2]** [cg-architecture + cg-reproducibility] `docs/model-guide.md:7` — False single-source-of-truth claim; three-way duplication  
  **Why**: The guide states "A Pester test validates all 22 files against this guide" — but the tests validate against their own inline constants, not the guide. The guide and tests can silently diverge with no detection.  
  **Fix**: Either (a) correct the claim to "tests validate against inline constants in `prompt-tools.Tests.ps1`; update both files together," or (b) extract the 22 assignments to `.github/model-assignments.json` and have both the tests and guide reference it. Option (a) is a one-line fix; option (b) creates a true single source of truth.

- **[P2.3]** [cg-architecture] `tests/prompt-tools.Tests.ps1` — Test file scope has outgrown its name; model tests warrant extraction  
  **Why**: `prompt-tools.Tests.ps1` now covers 5 distinct concerns: tool restrictions, review step content, findings frontmatter, SKILL.md structure, and model tier assignments. The 22 new model tests are conceptually separate.  
  **Fix**: Extract the two `Describe "Model assignments - ..."` blocks into `tests/model-assignments.Tests.ps1`. The `Get-Frontmatter` helper can be duplicated (4 lines) or moved to a shared `tests/helpers.ps1`.

- **[P2.4]** [cg-testing + cg-data-quality] `tests/prompt-tools.Tests.ps1:520-552` — `Get-Frontmatter` model match not anchored to `model:` key  
  **Why**: `$frontmatter -match [regex]::Escape($expectedModel)` passes if the model string appears *anywhere* in the frontmatter block — including in a `description:` field. A file with the wrong `model:` value but the right model name in its description would silently pass.  
  **Fix**: Anchor to the YAML key: `($frontmatter -match "(?m)^\s*model:\s*" + [regex]::Escape($expectedModel)) | Should Be $true`

- **[P2.5]** [cg-testing] `tests/prompt-tools.Tests.ps1:479-491` — Step 2.5 tests check keyword presence only; behavioral intent not validated  
  **Why**: The three Step 2.5 tests verify that the strings `"Subagent Output Quality Check"`, `"Incomplete Reviews"`, and `"NOT retry"` exist somewhere in the file. They don't verify the text is in the right context.  
  **Fix**: Add structural anchors: e.g., `($content -match 'empty.*garbled|garbled.*empty')` to confirm the quality criteria are present; `($content -match '@<agent-name>')` to confirm the warning template is present.

- **[P2.6]** [cg-testing] `docs/model-guide.md` — No Pester tests validate the guide's structure or sync with frontmatter  
  **Why**: The guide documents 22 assignments in a reference table. If the guide is manually edited and diverges from actual frontmatter, there is no automated detection.  
  **Fix**: Add a `Describe "docs/model-guide.md"` block to `tests/prompt-tools.Tests.ps1` (or the new `model-assignments.Tests.ps1`) testing: file exists, table references all 12 prompt files by stem, table references all 10 agent files by stem.

- **[P2.7]** [cg-documentation] `docs/reference.md:127` — Model Guide link is buried at the end of the Review Agents section  
  **Why**: The guide covers all 22 files across the entire system but is only referenced as a small note after the agent tables. Users browsing `reference.md` may miss it.  
  **Fix**: Add a reference near the top of the document (e.g., after the Prompts table) or create a "Key Guides" sub-section with a more visible link: "**Model selection**: See [Model Guide](model-guide.md) for tier assignments, decision criteria, and override guidance."

- **[P2.8]** [cg-documentation] `docs/model-guide.md` — Borderline Candidates section lacks current status  
  **Why**: The section says candidates are "pending empirical validation" but doesn't state whether testing has started, what the current recommendation is, or when results will be documented.  
  **Fix**: Add a `**Current status**` line: "Testing scheduled for a future session. Until then, use these files normally — their current tiers are safe; they may be downgraded if empirical testing approves."

- **[P2.9]** [cg-documentation] `.github/prompts/cg-review.prompt.md:Step 2.5` — "Usable output" criteria are subjective  
  **Why**: The step asks to check if output is "empty, garbled, or clearly off-topic" without concrete thresholds.  
  **Fix**: Replace with operational criteria: at least one `**[P1|P2|P3]**` entry OR an explicit "no issues found" statement; findings must reference changed files by name; fewer than 2 lines of non-header output counts as incomplete.

- **[P2.10]** [cg-documentation] `.cg-docs/solutions/performance-issues/2026-04-07-model-audit-classification.md` — Missing brainstorm cross-reference  
  **Why**: The solution links to the plan but not to the brainstorm where the hybrid approach was chosen. Users reading the solution can't trace the decision rationale.  
  **Fix**: Add `brainstorm: ".cg-docs/brainstorms/2026-04-07-full-model-audit.md"` to YAML frontmatter and add a "Decision Rationale" opening paragraph linking to the brainstorm.

- **[P2.11]** [cg-reproducibility] `docs/model-guide.md` + all frontmatter files — Model name strings not version-pinned  
  **Why**: `Claude Haiku 4.5 (copilot)` is a display name, not a stable API identifier. If Copilot renames models or upgrades Haiku 4.5 → 4.6, all frontmatter and tests silently reference the old name.  
  **Fix**: Add a "Version Mapping" section to the model guide documenting which Anthropic API version each Copilot display name maps to, and establish a 6-month re-audit cadence or a trigger-based refresh policy.

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `docs/model-guide.md:7` — Drift protection note doesn't specify which Pester describe blocks to look for  
  **Fix**: Update to: "...the 'Model assignments — prompt files' and 'Model assignments — agent files' describe blocks in `tests/prompt-tools.Tests.ps1`..."

- **[P3.2]** [cg-testing] `tests/prompt-tools.Tests.ps1:520-552` — Test failure messages lack diagnostic context  
  **Fix**: Add `-Because` clause: `Should Match $expectedModel -Because "$($case.File) model tier should be $($case.Tier)"`, or use `Should Match` instead of `| Should Be $true` for better output.

- **[P3.3]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No edge case tests for malformed frontmatter  
  **Fix** (optional): Add a sanity check `Describe "Prompt/agent files - frontmatter delimiters"` verifying both `---` delimiters are present in all 22 files.

- **[P3.4]** [cg-performance] `tests/prompt-tools.Tests.ps1:~382-411` — Pre-existing: duplicate `Describe "SKILL.md files - required frontmatter"` block causes redundant reads (not introduced by this PR)  
  **Fix**: Remove the second duplicate block; the first already covers both `name:` and `description:`.

- **[P3.5]** [cg-documentation] `docs/model-guide.md` — Token cost section lacks link to canonical pricing  
  **Fix**: Add: "For current Claude pricing, see [Anthropic pricing](https://www.anthropic.com/pricing/claude)."

- **[P3.6]** [cg-reproducibility] `docs/model-guide.md` — No maintenance cadence documented  
  **Fix**: Add an "Audit Maintenance" section: last validated date (2026-04-07), next validation due (2026-10-07), and triggers for early re-audit (model sunset, Copilot announcements, empirical test results).

- **[P3.7]** [cg-reproducibility] `.github/prompts/cg-setup.prompt.md`, `.github/prompts/cg-devtag.prompt.md` — No inline comment explaining Haiku downgrade  
  **Fix**: Add a comment in each file header: `# Model: Haiku 4.5 — configuration task; reasoning=2, creativity=1. See docs/model-guide.md (2026-04-07 audit).`

- **[P3.8]** [cg-data-quality] `tests/prompt-tools.Tests.ps1` — Model matching is case-insensitive (PowerShell default)  
  **Why**: `claude haiku 4.5 (copilot)` would pass a test expecting `Claude Haiku 4.5 (copilot)`.  
  **Fix**: Apply `(?-i)` flag or use `-cmatch` for case-sensitive comparison.

- **[P3.9]** [cg-data-quality] `.cg-docs/` document frontmatter — Status enum values undefined/inconsistent  
  **Why**: Brainstorm uses `decided`, plan uses `completed`, solution uses `applied`; no canonical schema.  
  **Fix**: Document the intended enum per document type (brainstorm: `open|decided|abandoned`; plan: `draft|active|completed|abandoned`; solution: `draft|applied`) in anticipation of the `evals` milestone schema validation feature.

- **[P3.10]** [cg-data-quality] `.cg-docs/plans/2026-04-07-full-model-audit.md:6` — `language: "both"` is non-standard  
  **Fix**: Change to `language: "PowerShell"` since all changed files are `.md` prompt/agent files or PowerShell tests.

---

### ✅ Passed

- **cg-version-control**: Commit messages follow conventional commits; no secrets or credentials; `.cg-docs/` artifacts correctly committed; 2-commit structure (feat + chore) is appropriate.
- **cg-performance**: 22 new file reads are negligible (<15 ms); lazy regex is correct choice; Step 2.5 adds zero latency (inline instructions only).
- **cg-architecture** (partial): Step 2.5 preserves `cg-review.prompt.md` single responsibility; `docs/model-guide.md` location in `docs/` is correct.
- **cg-data-quality** (partial): `roadmap.json` schema is fully compliant; prompt frontmatters have all required fields.
- **cg-reproducibility** (partial): `$repoRoot` path resolution is portable (`$PSScriptRoot` with env override); test execution is deterministic (static array, no randomness).
- **cg-learnings-researcher**: No conflicts with past solutions. Confirms that: dual-location documentation pattern, parametrised Pester tests, and `.cg-docs/` as institutional memory are all being applied correctly.
