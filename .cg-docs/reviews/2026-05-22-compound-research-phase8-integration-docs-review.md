---
date: 2026-05-22
plan: .cg-docs/plans/2026-05-22-compound-research-phase8-integration-docs.md
commit: c3b4d02
depth: thorough
agents: [cg-code-quality, cg-testing, cg-documentation, cg-version-control, cg-reproducibility, cg-performance, cg-architecture, cg-data-quality, cg-learnings-researcher, cg-adversarial]
findings:
  P1-ADV-01: resolved
  P1-ARCH-01: resolved
  P1-ARCH-02: resolved
  P1-ARCH-03: resolved
  P1-ARCH-04: resolved
  P2-CQ-01: resolved
  P2-ARCH-01: resolved
  P2-ARCH-02: resolved
  P2-ARCH-03: resolved
  P2-ARCH-04: resolved
  P2-DOC-01: resolved
  P2-ADV-01: resolved
  P2-ADV-02: resolved
  P2-DQ-03: resolved
  P2-VC-01: deferred
  P3-CQ-01: resolved
  P3-PERF-01: resolved
  TEST-01-04: deferred
---

# Review: Phase 8 Integration Polish & Documentation

**Commit**: `c3b4d02` — `docs(compound-research): Phase 8 integration polish & documentation`  
**Files reviewed**: 9 (README.md, compound-gpid.md, docs/context-files.md, docs/manual.md,
docs/workflow.md, roadmap.json, .cg-docs/plans/…phase8…md,
.cg-docs/solutions/testing-patterns/…skill-agent-sync.md, .cg-docs/DIGEST.md)  
**Depth**: Thorough — all 8 standard agents + `@cg-learnings-researcher` + `@cg-adversarial`  
**Tests at commit**: 2,341 / 2,341 passing

---

## P1 — BLOCKING

### [P1-ADV-01] `scripts/update.sh` — `{{modules}}` not substituted on macOS/Linux
**Source**: `@cg-adversarial` (confirmed by file read)  
**File**: `scripts/update.sh` lines ~100–122 (the Python heredoc in `generate_copilot_instructions`)  
**Issue**: The Python block reads and substitutes only four variables (`project-name`,
`project-type`, `languages`, `review-depth`). It does **not** read `modules` from
`compound-gpid.local.md` and does not call `.replace('{{modules}}', ...)`. When a user
follows the new `## Research Workflow` → "Enabling the research module" instructions and
runs `cg-update`, the generated `copilot-instructions.md` will contain the literal string
`{{modules}}` in the Active Modules section. `helpers.ps1` (Windows) handles this
correctly; only the Bash/macOS path is broken.  
**Impact**: Every Copilot session on macOS/Linux after `cg-update` sees `Modules:
{{modules}}` — the research module appears unconfigured. `/cr-*` commands may not be
activated by the instruction context.  
**Fix**: Add `modules` extraction + substitution to `update.sh`'s Python heredoc, mirroring
the pattern in `link.sh` lines 96–137.

---

### [P1-ARCH-01] `docs/workflow.md` line 507 — Theory/Modeling dispatch row incorrect
**Source**: `@cg-architecture` + `@cg-adversarial` (confirmed against `cr-review.prompt.md` line 89)  
**Issue**: Docs say `@cr-mathematical-verification`, `@cr-econometric-reasoning`.  
Actual (`cr-review.prompt.md` Step 3): `@cr-identification-audit`, `@cr-econometric-reasoning`, `@cg-adversarial`.  
`@cr-mathematical-verification` is dispatched file-presence-conditionally (Step 2, when
`.cg-docs/research/derivations/` contains `.tex`/`.md` files), not as Theory/Modeling-specific.  
**Fix**: Correct row to `@cr-identification-audit`, `@cr-econometric-reasoning`, `@cg-adversarial`.
Add a separate paragraph explaining `@cr-mathematical-verification` (file-presence conditional).

---

### [P1-ARCH-02] `docs/workflow.md` line 508 — Specification Analysis dispatch row incorrect
**Source**: `@cg-architecture` (confirmed against `cr-review.prompt.md` line 90)  
**Issue**: Docs say `@cr-specification-analysis`, `@cr-identification-audit`.  
Actual: `@cr-specification-analysis` only. `@cr-identification-audit` is triggered by a
separate code-pattern override (feols/ivreg/rdrobust/DiD in reviewed files), not as a
Specification Analysis task-type dispatch.  
**Fix**: Change row to `@cr-specification-analysis` only. Note the identification override
separately.

---

### [P1-ARCH-03] `docs/workflow.md` lines ~510-511 — EDA and Implementation rows incorrect
**Source**: `@cg-architecture` + `@cg-adversarial` (confirmed against `cr-review.prompt.md` lines 91-97)  
**Issue**:  
- EDA docs: `@cr-research-integrity` → Actual: `@cg-performance`, `@cg-data-quality`  
- Implementation docs: `@cr-research-integrity`, `@cr-mathematical-verification` → Actual: `@cg-performance`, `@cr-ml-methodology`, `@cr-specification-analysis`  
`@cr-research-integrity` is unconditionally dispatched for ALL task types (Step 2), not
EDA-specific. Listing it in these rows contradicts the "always dispatched" note that follows the table.  
**Fix**: Remove `@cr-research-integrity` from both rows. Correct EDA to `@cg-performance`,
`@cg-data-quality`. Correct Implementation to `@cg-performance`, `@cr-ml-methodology`,
`@cr-specification-analysis`.

---

### [P1-ARCH-04] `docs/workflow.md` — `@cr-mathematical-verification` dispatch mechanism misrepresented
**Source**: `@cg-architecture` (confirmed against `cr-review.prompt.md` lines 66-72)  
**Issue**: The table implies `@cr-mathematical-verification` is Theory/Modeling-specific. It is
actually dispatched in Step 2 (file-presence conditional: runs if
`.cg-docs/research/derivations/` contains `.tex` or `.md`) regardless of task type.  
**Impact**: Two failure modes: (1) Theory/Modeling without derivation files won't get the
agent, contradicting docs. (2) Any task type with derivation files (EDA, ML) will get it
unexpectedly.  
**Fix**: Remove from the task-type dispatch table. Add a note after the table:
`@cr-mathematical-verification` is dispatched when `.cg-docs/research/derivations/` contains
`.tex` or `.md` files, regardless of task type.

---

## P2 — IMPORTANT

### [P2-CQ-01] `compound-gpid.md` — Current Focus uses present tense for completed Phase 8
**Source**: `@cg-code-quality` + `@cg-reproducibility` (confirmed)  
**File**: `compound-gpid.md` `## Current Focus` section  
**Issue**: "Phase 8 (integration polish & documentation) **is the final step** before
merging to main" — present tense implies Phase 8 is still pending, but it is complete
(`completed-date: 2026-05-22` in roadmap.json).  
**Fix**: Update to past tense. Suggested text:
> Compound Research milestone — **Phases 1–8 complete** (module system, research workflow
> scaffolding, core CR agents, structural econometrics skills, ML-in-economics, academic
> writing & publication output, reproducibility/replication, and integration polish &
> documentation). Phase 9 (dedicated Tables/Figures agent) remains as planned future work.
> Engineering milestones (Workflow Maturity, Skills Enhancement) continue in parallel.

---

### [P2-ARCH-01] `docs/workflow.md` line 505 — "architecture" should be "version-control"
**Source**: `@cg-architecture` (confirmed against `cr-review.prompt.md` lines 45-51)  
**Issue**: "6 shared `cg-*` quality agents (code quality, testing, **architecture**,
documentation, reproducibility, data quality)" — `@cg-architecture` is not dispatched by
`cr-review.prompt.md`. The actual 6th agent is `@cg-version-control`.  
**Fix**: Change "architecture" to "version control".

---

### [P2-ARCH-02] `docs/workflow.md` — ML/Prediction row missing `@cg-performance`
**Source**: `@cg-architecture` (confirmed against `cr-review.prompt.md` line 93: `@cr-ml-methodology, @cr-specification-analysis, @cg-performance`)  
**Fix**: Add `@cg-performance` to the ML/Prediction row.

---

### [P2-ARCH-03] `docs/workflow.md` — Tables/Figures row missing `@cg-documentation`
**Source**: `@cg-architecture` (confirmed against `cr-review.prompt.md` line 95: `@cg-documentation, @cr-academic-writing`)  
**Fix**: Add `@cg-documentation` to the Tables/Figures row.

---

### [P2-ARCH-04] `docs/workflow.md` — `@cg-adversarial` for Theory/Modeling undocumented
**Source**: `@cg-architecture` (confirmed against `cr-review.prompt.md` line 89)  
**Note**: Fixed by [P1-ARCH-01] correction — the corrected Theory/Modeling row will include
`@cg-adversarial`.

---

### [P2-DOC-01] `README.md` — Redundant "enable" description in research module bullet
**Source**: `@cg-documentation`  
**File**: `README.md` Key Benefits research bullet  
**Issue**: "enable `/cr-*` commands via `modules: "engineering, research"` in your local
config... Requires the `research` module to be enabled." — states the same enabling
requirement twice.  
**Fix**: Remove redundant second sentence. Rewrite as a single sentence covering both the
activation mechanism and the research capabilities.

---

### [P2-ADV-01] `docs/workflow.md` — `set.seed()` confusingly listed under "Unseeded randomness"
**Source**: `@cg-adversarial`  
**Issue**: The P0 enforcement bullet reads: "**Unseeded randomness** — any `sample()`,
`rnorm()`, `set.seed()` without a documented seed in a seed registry." A researcher doing a
P0 self-check who sees `set.seed(42)` but no formal seed registry could read this as their
`set.seed()` call being the P0 violation and remove it — eliminating reproducibility.  
**Fix**: Clarify: flag `sample()`/`rnorm()` **without** a preceding `set.seed()` as P0.
Seed calls without a registry entry are a separate (P1) concern. Rephrase to distinguish
the random call (the crime) from the missing seed (the evidence).

---

### [P2-ADV-02] `docs/workflow.md` — No warning about YAML list notation for modules
**Source**: `@cg-adversarial`  
**Issue**: Documentation shows `modules: "engineering, research"` but gives no warning about
the natural YAML multi-value syntax (`modules: [engineering, research]`) which fails with an
error in `link.sh`/`helpers.ps1`. The YAML block-sequence form (`- engineering` on next
line) is not caught by either script.  
**Fix**: Add a callout to the "Enabling the research module" section:
> ⚠️ Use a quoted string — YAML list notation (`modules: [engineering, research]`) is not
> supported and will cause `cg-link`/`cg-update` to exit with an error.

---

### [P2-DQ-03] `.cg-docs/DIGEST.md` — Header claims 119 but filesystem has 120 solutions
**Source**: `@cg-data-quality` (confirmed: `find .cg-docs/solutions -name "*.md" | wc -l` = 120)  
**Fix**: Regenerate DIGEST or update the count header to `120 active solutions`.

---

### [P2-VC-01] `.cg-docs/DIGEST.md` — Auto-generated file committed without automation guard
**Source**: `@cg-version-control`  
**Issue**: DIGEST.md is regenerated by `cg-index.py --digest` but committed manually. On
parallel branches where different solutions are added, the DIGEST will produce merge
conflicts.  
**Note**: This is a workflow/process concern rather than a single-commit fix. See
`.cg-docs/brainstorms/2026-05-07-python-utility-layer-cg-index.md` for the planned
automation. No immediate action required for this commit; track as roadmap item.

---

## P3 — MINOR

### [P3-CQ-01] `docs/context-files.md` — "Five template variables" after "Three Files" heading could briefly confuse
**Source**: `@cg-code-quality`  
**Issue**: Section heading "The Three Files at a Glance" immediately precedes prose about
"five template variables" — readers may wonder why there are 5 variables for 3 files.  
**Note**: These are distinct counts (3 files generated, 5 placeholder variables). A
parenthetical clarification would help. Low priority.

### [P3-PERF-01] `docs/workflow.md` — Research loop omits `/cg-plan-review` step
**Source**: `@cg-performance`  
**Issue**: The engineering loop documents `/cg-plan-review` between plan and work. The
research loop omits it, even though Theory/Modeling and Specification Analysis tasks benefit
most from plan-review before implementation.  
**Fix**: Add a note recommending `/cg-plan-review` for Standard/Deep research tasks before
`/cr-work`.

---

## Test Gap Findings (P1 per `@cg-testing`)

The following test gaps are not bugs in the committed code but represent missing contract
tests for new documentation surfaces. Separate from the priority matrix above.

- **[TEST-01]** No test verifying 8 task types stay in sync between `docs/workflow.md` and
  `cr-brainstorm.prompt.md` / `cr-skill-research-workflow`
- **[TEST-02]** No test verifying the dispatch table in `docs/workflow.md` matches
  `cr-review.prompt.md` Step 3
- **[TEST-03]** No test verifying `{{modules}}` is documented in `docs/context-files.md`
  AND present in `copilot-instructions.template.md`
- **[TEST-04]** No test verifying research loop steps are documented in `docs/manual.md`
  Quick orientation section

---

## Findings Summary

| ID | Priority | File | Source | Status |
|----|----------|------|--------|--------|
| P1-ADV-01 | P1 | scripts/update.sh | adversarial | open |
| P1-ARCH-01 | P1 | docs/workflow.md | architecture | open |
| P1-ARCH-02 | P1 | docs/workflow.md | architecture | open |
| P1-ARCH-03 | P1 | docs/workflow.md | architecture | open |
| P1-ARCH-04 | P1 | docs/workflow.md | architecture | open |
| P2-CQ-01 | P2 | compound-gpid.md | code-quality | open |
| P2-ARCH-01 | P2 | docs/workflow.md | architecture | open |
| P2-ARCH-02 | P2 | docs/workflow.md | architecture | open |
| P2-ARCH-03 | P2 | docs/workflow.md | architecture | open |
| P2-ARCH-04 | P2 | docs/workflow.md | (fixed by P1-ARCH-01) | open |
| P2-DOC-01 | P2 | README.md | documentation | open |
| P2-ADV-01 | P2 | docs/workflow.md | adversarial | open |
| P2-ADV-02 | P2 | docs/workflow.md | adversarial | open |
| P2-DQ-03 | P2 | .cg-docs/DIGEST.md | data-quality | open |
| P2-VC-01 | P2 | .cg-docs/DIGEST.md | version-control | process |
| P3-CQ-01 | P3 | docs/context-files.md | code-quality | open |
| P3-PERF-01 | P3 | docs/workflow.md | performance | open |
| TEST-01–04 | P1 | (new test files) | testing | open |
