---
plan: ".cg-docs/plans/2026-05-22-compound-research-phase7-reproducibility-replication.md"
date: 2026-05-22
depth: standard
agents:
  - cg-code-quality
  - cg-testing
  - cg-version-control
  - cg-architecture
  - cg-documentation
  - cg-reproducibility
  - cg-performance
  - cg-data-quality
findings:
  P1.1: fixed
  P1.2: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P3.1: fixed
---

# Standard Review — Phase 7 Reproducibility & Replication Package

Second review pass (standard depth) run after thorough review fixes were applied.
All 12 findings from the first review confirmed resolved.

## Summary

| Priority | Count | Status |
|----------|-------|--------|
| P0 | 0 | — |
| P1 | 2 | fixed |
| P2 | 4 | fixed |
| P3 | 1 | fixed |
| **Total** | **7** | **all fixed** |

Test suite: **2,341 / 2,341** passing after fixes.

---

## Findings

### P1.1 — `docs/model-guide.md` drift-protection note stale count

**Agent**: cg-documentation, cg-architecture  
**File**: `docs/model-guide.md`, line 8  
**Issue**: Drift-protection note read "validate all **39** files" while the header (line 3) already said 48. The mismatch created conflicting guidance about the authoritative file count.  
**Fix**: Updated note to "validate all **48** files".

---

### P1.2 — `cr-skill-replication-standards/SKILL.md` Section 6 missing `../`

**Agent**: cg-documentation, cg-architecture  
**File**: `.github/skills/cr-skill-replication-standards/SKILL.md`, Section 6 Forbidden Patterns table  
**Issue**: The agent's Check 6 explicitly forbids parent-traversal paths (`../`) as P1 violations, but the corresponding skill documentation did not include this pattern in its Forbidden Patterns table. Skill/agent contract mismatch.  
**Fix**: Added row to Forbidden Patterns table: `| Parent-traversal path | \`../data/raw/\` or \`..\\\data\\\raw\\\` | Non-portable when subscripts are sourced from project root |`

---

### P2.1 — `docs/reference.md` model selection callout stale count

**Agent**: cg-architecture  
**File**: `docs/reference.md`, line 76  
**Issue**: Model selection callout read "for all **39** prompt and agent files" — should be 48.  
**Fix**: Updated to "for all **48** prompt and agent files".

---

### P2.2 — `cr-replication-package.agent.md` injection guard missing case-insensitive qualifier

**Agent**: cg-architecture  
**File**: `.github/agents/cr-replication-package.agent.md`  
**Issue**: Injection guard pattern list lacked `(case-insensitive)` qualifier present in `cr-academic-writing.agent.md`. Guard was functionally correct for case-exact matches but inconsistent with the established convention.  
**Fix**: Changed "patterns: `SYSTEM`" to "patterns, case-insensitive: `SYSTEM`".

---

### P2.3 — `docs/reference.md` new agent row used em-dash separator

**Agent**: cg-architecture  
**File**: `docs/reference.md`, line 173  
**Issue**: The `cr-replication-package` row used em-dash (`—`) as separator between lead phrase and detail list; all other agent rows in the table use colon (`:`). Also improved wording: "vs manifest.json" → "cross-referenced with manifest.json", added "(no absolute paths)" qualifier to path portability entry.  
**Fix**: Changed to colon separator and improved wording for consistency.

---

### P2.4 — `tests/cr-prompts.Tests.ps1` duplicate `cr-review.prompt.md` read

**Agent**: cg-performance  
**File**: `tests/cr-prompts.Tests.ps1`, lines 2090 and 2171  
**Issue**: `cr-review.prompt.md` was read via `Get-Content` in two separate `Describe` blocks ("Phase 7 prompt cleanup - cr-review" and "Phase 7 dispatch journey"). The dispatch journey `It` block also contained a duplicate positive assertion already present in the cleanup block.  
**Fix**: Removed the standalone "Phase 7 dispatch journey" `Describe` block. Moved the unique negative assertion (`Reproducibility.*Phase 7`) into the cleanup `Describe` as a new `It "Reproducibility dispatch row has no Phase 7 qualifier"` block. Net test count unchanged.

---

### P3.1 — `tests/cr-prompts.Tests.ps1` redundant assertion in dispatch journey

**Agent**: cg-performance  
**File**: `tests/cr-prompts.Tests.ps1`  
**Issue**: The removed dispatch journey `It` block contained a positive assertion (`Reproducibility.*cr-replication-package`) identical to one already in the cleanup block.  
**Fix**: Resolved by the P2.4 merge — duplicate assertion eliminated.

---

## Agents with no findings

| Agent | Result |
|-------|--------|
| cg-code-quality | 1 pre-existing P2 (DRY in task-type patterns, predates Phase 7, not actionable here) |
| cg-version-control | No issues |
| cg-reproducibility | No issues — all test paths use `$repoRoot`/`Join-Path`, skill examples seeded with `set.seed(42)`, agent is read-only |
| cg-data-quality | No issues — all frontmatter schemas valid, roadmap JSON valid, plan dates ISO 8601, 12/12 review findings confirmed fixed |
