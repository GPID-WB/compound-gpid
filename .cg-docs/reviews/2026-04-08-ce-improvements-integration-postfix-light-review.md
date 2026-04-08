---
plan: .cg-docs/plans/2026-04-08-ce-improvements-integration.md
findings:
  P1.1: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P3.1: fixed
---

## Review Report

**Review depth**: light (post fix-triage verification)
**Files reviewed**: 14 (fix-triage commit: `fix(prompts): apply phase 2 review findings (P0-P3)`)
**Findings**: 0 P0 · 1 P1 · 4 P2 · 1 P3

---

### P0 — BLOCKING (immediate remediation required)

_None._

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-testing] `tests/prompt-tools.Tests.ps1`:210 — Workflow Entry Points test missing `/cg-compound-refresh` and `/cg-ideate`
  **Why**: `copilot-instructions.md` lines 66 and 72 include both entries in the Workflow Entry Points table. The `Describe "copilot-instructions.md - Workflow Entry Points"` block tests 9 entries (ending at `/cg-compound`) but never checks the two new prompts. If either entry is accidentally removed from the instructions table, the gap goes undetected.
  **Fix**: Add two `It` blocks after the `/cg-compound` check at line 210:
  ```powershell
  It "references /cg-compound-refresh in Workflow Entry Points" {
      ($section -match '/cg-compound-refresh') | Should Be $true
  }

  It "references /cg-ideate in Workflow Entry Points" {
      ($section -match '/cg-ideate') | Should Be $true
  }
  ```

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `.github/prompts/cg-compound-refresh.prompt.md`:93,142 — Incomplete `Delete` → `Archive` rename
  **Why**: The classification table was updated (line 74: `**Archive**`) but two downstream references still say "Delete": line 93 (example audit table row) and line 142 (rules section: "If unsure whether to Delete vs. Replace"). Both should use "Archive" to match the renamed classification and the "Never hard-delete" rule on line 139.
  **Fix**:
  - Line 93: change `Delete` → `Archive` in the example table row
  - Line 142: change `Delete vs. Replace` → `Archive vs. Replace`

- **[P2.2]** [cg-code-quality] `.github/skills/cg-skill-r-testing/SKILL.md`:79 — Missed link-format migration for `bdd.md` reference
  **Why**: Three inline "See [references/…](...)" links were migrated to "Read `references/…` in this directory" format in this commit (lines 334, 339, 342). Line 79 uses the same old format — `See [references/bdd.md](references/bdd.md)` — and was missed.
  **Fix**: Change line 79 to:
  ```markdown
  Read `references/bdd.md` in this directory for nesting, test-first workflow, and mixing both styles.
  ```
  (The hyperlink at line 368 is in the formal Cross-References table — leave it as-is.)

- **[P2.3]** [cg-code-quality] `.github/copilot-instructions.md`:126 — Thorough review depth description omits `cg-adversarial`
  **Why**: `cg-adversarial` was added as a thorough-only agent in `cg-review.prompt.md` and `docs/reference.md`. The `copilot-instructions.md` Review Depth Tiers section only mentions `cg-learnings-researcher` for thorough depth, leaving users unaware of the adversarial pass.
  **Fix**: Update line 126:
  ```markdown
  - **thorough**: Runs all 8 review agents + `cg-learnings-researcher` to cross-reference past solutions and `cg-adversarial` for adversarial edge-case analysis. Use for major features and refactors.
  ```

- **[P2.4]** [cg-testing] `tests/prompt-tools.Tests.ps1`:452–490 — New prompts lack symmetric frontmatter coverage
  **Why**: `cg-compound-refresh` and `cg-ideate` each get one assertion (`tools:` restriction). Comparable orchestrating prompts like `cg-strategy` (lines 243–260) and `cg-fix-triage` (lines 104–160) also test file existence and required frontmatter fields (`description:`, `model:`). Missing coverage means a broken frontmatter in either new prompt goes undetected.
  **Fix**: Add file-existence and frontmatter `Describe` blocks for both prompts, following the same pattern as the existing `cg-strategy.prompt.md` and `cg-fix-triage.prompt.md` test blocks.

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-testing] `tests/prompt-tools.Tests.ps1`:462,479 — Tool-restriction regex unanchored
  **Why**: Both new `Describe` blocks use `($frontmatter -notmatch 'tools:')`. A comment like `# tools: disabled` in the frontmatter body would pass this check while the YAML pattern remains correct. Risk is low (comments are rare in frontmatter), but anchoring clarifies intent.
  **Fix**: (Optional) Change to `($frontmatter -notmatch '(?m)^\s*tools:')` in both new blocks to match only at line-start, consistent with YAML key semantics.

---

### ✅ Passed

- **cg-code-quality**: No P0 or P1 issues found. Path fixes (`setup-templates.md`, `resume-templates.md`), count sentinel updates (22→25), table reordering, classification rename (main occurrence), and output-format realignment in `cg-adversarial.agent.md` all applied correctly.
- **cg-testing**: Count sentinels correct (14 prompt stems, 11 agent stems). `roadmap.Tests.ps1` `Join-Path` fix is correct. `cg-adversarial` is covered by the dynamic agent loop in `model-assignments.Tests.ps1`. All 756 tests passing.
