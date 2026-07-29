---
date: 2026-05-22
plan: 2026-05-22-compound-research-phase6-writing-publication
review-depth: standard
agents: [cg-code-quality, cg-testing, cg-architecture, cg-documentation, cg-version-control, cg-reproducibility, cg-performance, cg-data-quality]
p0-count: 0
p1-count: 1
p2-count: 10
p3-count: 4
status: triaged
---

# Standard Review — Phase 6 Writing & Publication Fixes

**Scope**: Phase 6 review-triage changes (2nd pass standard review)
**Changed files**: 8 files (7 modified, 1 untracked)
- `.github/agents/cr-academic-writing.agent.md`
- `.github/skills/cr-skill-publication-output/SKILL.md`
- `.github/prompts/cr-review.prompt.md`
- `.github/prompts/cr-brainstorm.prompt.md`
- `docs/reference.md`
- `.github/copilot-instructions.md`
- `roadmap.json`
- `tests/cr-prompts.Tests.ps1`
- `.cg-docs/reviews/2026-05-22-compound-research-phase6-writing-publication-review.md` (untracked)

**Stats**: ~154 insertions, ~43 deletions. No R/Python/Stata changes.

---

## P0 — BLOCKING

_None._

---

## P1 — CRITICAL

### [P1.1] `ggsave()` in wrong Review Criteria section
**File**: `.github/skills/cr-skill-publication-output/SKILL.md` Section 6
**Agent**: cg-documentation
**Issue**: The Section 6 (Table-Note Discipline) Review Criteria callout includes a `ggsave()` criterion. `ggsave()` is a figure output function — it belongs in Section 5 (Figure-Caption Discipline). A reviewer using Check 6 delegation to Section 6 will receive a figure criterion inside a table-note checklist, producing misclassified findings.
**Fix**: Move `ggsave()` bullet from Section 6 Review Criteria to Section 5 Review Criteria.

---

## P2 — IMPORTANT

### [P2.1] Alternation pattern in font/size test
**File**: `tests/cr-prompts.Tests.ps1`
**Agent**: cg-testing
**Issue**: The `"contains font/size conventions"` test still uses alternation `(?i)font.*size|size.*convention`, which allows either half to pass independently. A file with only font-name info but no size info would pass.
**Fix**: Split into two `It` blocks: `"contains font conventions"` and `"contains size conventions"`.

### [P2.2] Missing Tables/Figures dispatch test
**File**: `tests/cr-prompts.Tests.ps1`
**Agent**: cg-code-quality
**Issue**: No test verifies that the Tables/Figures dispatch row in `cr-review.prompt.md` routes to both `@cg-documentation` AND `@cr-academic-writing`. The row was updated but the test suite doesn't cover it.
**Fix**: Add two `It` blocks asserting `Tables/Figures.*@cg-documentation` and `Tables/Figures.*@cr-academic-writing` patterns in the cr-review test Describe block.

### [P2.3] Missing brainstorm cross-reference test for cr-skill-publication-output
**File**: `tests/cr-prompts.Tests.ps1`
**Agent**: cg-code-quality
**Issue**: No test verifies that `cr-skill-publication-output` appears in both the Writing row and the Tables/Figures row of `cr-brainstorm.prompt.md`.
**Fix**: Add two `It` blocks checking `cr-skill-publication-output` presence in both brainstorm rows.

### [P2.4] roadmap.json feature ID naming inconsistency
**File**: `roadmap.json`
**Agent**: cg-code-quality
**Issue**: New feature ID is `"cr-publication-output-agent"` but all other feature IDs use the pattern `"cr-<capability>"` without an `-agent` suffix (e.g., `"cr-reproducibility-replication"`, `"cr-integration-docs"`).
**Fix**: Rename to `"cr-publication-output"`.

### [P2.5] No Tables/Figures mode guard in agent
**File**: `.github/agents/cr-academic-writing.agent.md`
**Agent**: cg-architecture
**Issue**: Checks 1–5 and 7 are all Writing-specific (section structure, abstract quality, argument flow, etc.). When the agent is dispatched for a Tables/Figures task, these checks will either no-op or emit spurious findings against code files.
**Fix**: Add a T/F mode guard: if the task type is Tables/Figures, skip Checks 1–5 and 7 and execute only Check 6.

### [P2.6] Section 6 Review Criteria incomplete
**File**: `.github/skills/cr-skill-publication-output/SKILL.md`
**Agent**: cg-documentation
**Issue**: Section 6 Table-Note Discipline Review Criteria is missing two standard checks: (a) sample definition note (what sample does the table cover?), and (b) fixed-effects disclosure (are FE absorbed in the model noted?).
**Fix**: Add both checks to the Section 6 Review Criteria callout.

### [P2.7] `library(here)` missing from here::here() example
**File**: `.github/skills/cr-skill-publication-output/SKILL.md` Section 7
**Agent**: cg-documentation
**Issue**: The new `here::here()` code block uses `here::here()` without a preceding `library(here)` call. Readers unfamiliar with the package may not know to load it.
**Fix**: Add `library(here)` to the code example.

### [P2.8] reference.md skill entry missing scope label
**File**: `docs/reference.md`
**Agent**: cg-documentation
**Issue**: The `cr-skill-publication-output` entry says "Loaded by @cr-academic-writing" but doesn't specify "for Writing and Tables/Figures tasks" — inconsistent with the detail level of neighboring entries.
**Fix**: Append "for Writing and Tables/Figures tasks" to the description.

### [P2.9] Section 5 "2-sentence" criterion ambiguous
**File**: `.github/skills/cr-skill-publication-output/SKILL.md` Section 5
**Agent**: cg-documentation
**Issue**: The Review Criteria requires captions to be "shorter than 2 sentences" but also specifies required elements (what the chart shows, data source, key takeaway). A single dense sentence could satisfy the required-elements check but violate the 2-sentence cap — creating conflicting signals.
**Fix**: Replace "shorter than 2 sentences" with "self-contained (no more than 3 sentences)" or remove the sentence-count criterion entirely.

### [P2.10] Misleading ggsave comment
**File**: `.github/skills/cr-skill-publication-output/SKILL.md` (~line 402)
**Agent**: cg-reproducibility
**Issue**: The comment above the PDF `ggsave()` example says "Explicit dimensions, format, dpi" but the PDF code example intentionally omits `dpi` (correct behavior for PDF). The comment claims dpi is specified when it is not.
**Fix**: Update comment to "Explicit dimensions and format" (PDF is vector; dpi not applicable).

---

## P3 — MINOR

### [P3.1] Agent frontmatter description stale
**File**: `.github/agents/cr-academic-writing.agent.md`
**Agent**: cg-architecture
**Issue**: The frontmatter `description` field still says "Loaded by /cr-review for Writing tasks" but the agent is now also dispatched for Tables/Figures tasks.
**Fix**: Update to "Loaded by /cr-review for Writing and Tables/Figures tasks."

### [P3.2] Pre-existing: tools check has two assertions per It block
**File**: `tests/cr-prompts.Tests.ps1` (~line 404)
**Agent**: cg-testing
**Note**: Pre-existing pattern not introduced by Phase 6 changes. The `$crAgents` structural loop `"[$name] has tools: ['read', 'search'] (no write)"` contains two assertions (`$fm -match "tools:.*'read'"` AND `$fm -notmatch "'write'"`). Violates one-assertion-per-It rule.
**Fix** (optional): Split into two It blocks per agent in the loop.

### [P3.3] Word-count check optional optimization
**File**: `tests/cr-prompts.Tests.ps1`
**Agent**: cg-performance
**Note**: `($content -split '\s+').Count -gt 500` allocates a word array; `$content.Length -gt 3000` (≈500 words × 6 chars) is a faster proxy with ~0 allocation. Total overhead is ~4 ms for both tests — no action required.

### [P3.4] Scope label preamble clarity
**File**: `.github/copilot-instructions.md`
**Agent**: cg-code-quality
**Note**: The `cr-skill-publication-output` scope label `(Writing, Tables/Figures)` accurately describes dispatch. Preamble sentence could be slightly clearer about whether the skill is auto-loaded by the agent or requires explicit task-dispatch. Low priority.

---

## Version Control Note

- The first review file (`.cg-docs/reviews/2026-05-22-compound-research-phase6-writing-publication-review.md`) remains untracked — include in commit
- All 8 changed files form one logical commit on the `compound-research` branch
