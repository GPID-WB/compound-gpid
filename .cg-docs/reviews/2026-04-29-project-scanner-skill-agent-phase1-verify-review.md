---
date: 2026-04-29
depth: light
parent-review: .cg-docs/reviews/2026-04-29-project-scanner-skill-agent-phase1-review.md
type: verification
findings:
  P1.1: fixed
  P1.2: fixed
  P3.1: fixed
  P3.2: fixed
---

## Review Report

**Review depth**: light (verification mode)
**Files reviewed**: 7 (`.github/agents/cg-project-scanner.agent.md`, `.github/skills/cg-skill-project-scanner/SKILL.md`, `tests/prompt-tools.Tests.ps1`, `tests/model-assignments.Tests.ps1`, `docs/model-guide.md`, `docs/reference.md`, `roadmap.json`)
**Findings**: 4 (P0: 0, P1: 2, P2: 0, P3: 2)

> **Note**: Both P1 findings are pre-existing failures that predate the current triage cycle — they are not introduced by any fix in the P1–P3 triage passes. They are reported per the verify suppression policy ("P0/P1: Always report").

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-code-quality] `roadmap.json` — Milestone/feature status mismatches causing pre-existing `roadmap.Tests.ps1` failure  
  **Why**: Milestone `performance` has `status: "done"` but feature `model-split-pattern-reuse` carries `status: "idea"` (schema validator derives milestone status from features → conflict). Milestone `skills-enhancement` has `status: "planned"` but feature `r-dialect-skills-architecture` has `status: "done"` (a done feature inside a planned milestone → conflict). `roadmap.json` is in the changed-file set; cross-file breakage policy requires reporting. This is the cause of the pre-existing `roadmap.Tests.ps1` failure (1 failure, present before this review cycle).  
  **Fix**: For `performance` — either change `model-split-pattern-reuse` to `"done"` (if the idea has been decided upon and work has been done or is deferred-but-complete) or change the milestone status to `"in-progress"`. For `skills-enhancement` — change milestone status from `"planned"` to `"in-progress"` (one feature is already done).

- **[P1.2]** [cg-code-quality] `tests/prompt-tools.Tests.ps1` — `SCHEMA_VERSION` test expects `scope-fields` marker; file contains only the version string  
  **Why**: Test `"SCHEMA_VERSION contains scope-fields marker"` asserts `($schemaContent -match 'scope-fields')` but `SCHEMA_VERSION` contains only `2026-04-28-release-scanner-agent`. This is the cause of the pre-existing `prompt-tools.Tests.ps1` failure. `tests/prompt-tools.Tests.ps1` is in the changed-file set; cross-file breakage policy requires reporting. This failure predates this review cycle and was not introduced by the triage.  
  **Fix**: Either add the `scope-fields` marker to `SCHEMA_VERSION` (e.g., `2026-04-28-release-scanner-agent-scope-fields`) if the corresponding `/cg-setup` scope-fields feature was implemented, or remove/skip the test until the feature ships.

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality + cg-testing] `tests/model-assignments.Tests.ps1:119` — Stale count in comment  
  **Why**: Comment reads `# All 14 agent file stems must appear in the guide` but `$agentStems` now contains 15 entries (including `cg-project-scanner`). The sentinel on line 68 is correctly `15`; only the inline comment is stale.  
  **Fix**: Change `14` → `15` in the comment.

- **[P3.2]** [cg-code-quality] `tests/prompt-tools.Tests.ps1` — `cg-skill-project-scanner` frontmatter context block missing `schema-version:` test  
  **Why**: P2.11 explicitly added `schema-version: "1.0"` to SKILL.md frontmatter as a machine-parseable version anchor; no test guards against accidental removal. `cg-skill-project-scanner` is the only skill with this field.  
  **Fix**: Add inside the `Context "frontmatter fields"` block: `It "has a schema-version: field in frontmatter" { ($frontmatter -match 'schema-version:') | Should Be $true }`.

---

### ✅ Passed

- **cg-code-quality**: All 30 previously-triaged findings (P1.1–P1.5, P2.1–P2.18, P3.2–P3.7) correctly applied in `.github/agents/cg-project-scanner.agent.md`, `.github/skills/cg-skill-project-scanner/SKILL.md`, `docs/model-guide.md`, `docs/reference.md`. No new style, naming, or structural issues introduced by the fixes.
- **cg-testing**: All new Pester assertions use `Should Be` (Pester 3.4 compatible). `Get-ToolsList` helper correctly used for tools exclusion check (P3.5). Confidence threshold regex correctly anchored to table rows (P2.5). Model value test correctly checks `Claude Haiku 4\.5` literal (P2.4). All three output schema sections tested independently (P2.6). `reference.md` scanner coverage test present (P2.7). `model-assignments.Tests.ps1` sentinel and array correct at 15 entries.
