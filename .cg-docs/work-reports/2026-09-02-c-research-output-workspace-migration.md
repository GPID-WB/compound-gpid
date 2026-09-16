---
created: "2026-09-02"
plan: ".cg-docs/plans/2026-09-02-c-research-output-workspace-migration.md"
status: completed
---

# Execution Report: Root-Level c-research Output Workspace and Migration

- Plan reference: `.cg-docs/plans/2026-09-02-c-research-output-workspace-migration.md`
- Active deviation policy: `ask` (no runtime override)
- Run started: 2026-09-02
- Branch: `research/ai-knowledge-work-presentation`

## Completed Steps/Phases

- Step 1: complete (2026-09-02)
- Step 2: complete (2026-09-02)
- Phase 1: complete (2026-09-02)
- Step 3: complete (2026-09-02)
- Step 4: complete (2026-09-02)
- Phase 2: complete (2026-09-02)
- Step 5: complete (2026-09-02)
- Phase 3: complete (2026-09-02)
- Step 6: complete (2026-09-02)
- Step 7: complete (2026-09-02)
- Phase 4: complete (2026-09-02)
- Step 8: complete (2026-09-02)
- Step 9: complete (2026-09-02)
- Phase 5: complete (2026-09-02)
- Step 10: complete (2026-09-02)
- Phase 6: complete (2026-09-02)
- Phase 7: complete (2026-09-02)

## Deviations

- D1: User selected reconciliation of the pre-existing model-routing changes
  before target regeneration. The target mapping and related tests were aligned
  with the committed advisory-only contract; Kilo support was restored and no
  model-mapping artifacts were generated. Impact: unrelated model-guide and
  model-assignment work remains outside this migration's scope.

## Accepted Exceptions

None recorded.

## Evidence Table

| ID | Phase | Evidence | Status | Artifact |
|---|---:|---|---|---|
| V1 | 1 | Canonical layout and ownership contract lists every supported output type and separates outputs from `data/` inputs | passed | `c-research/README.md` and `test_research_layout.py`: 8 passed |
| V2 | 1 | Migration inventory detects all operational old paths, classifies historical paths, and reports deterministic moves/conflicts | passed | `test_research_layout.py`: 29 passed; real check is `up-to-date` with only historical and migration-tool references |
| V3 | 2 | Setup creates the complete `c-research/` scaffold only for active `cr` and never deletes an existing tree | passed | Setup contracts in `prompt-tools`: new assertions passed |
| V4 | 2 | Both update scripts invoke the same idempotent, conflict-safe structural migration | passed | Update hooks run the shared migrator across linked and native-target-only projects; behavioral updater regression passed |
| V5 | 3 | Existing research files move to correct destinations with unchanged bytes/frontmatter and no duplicate old tree | passed | Deck-matching 21-slide manuscript is canonical; 16-slide draft is retained as a superseded alternate; legacy root absent |
| V6 | 4 | All live CR prompts, skills, agents, instructions, scripts, package docs, and ignore rules use new paths | passed for active sources | Active source scan: zero legacy/singular paths; evidence docs test passed |
| V7 | 4 | Evidence workbench canonical state is rooted at `c-research/evidence/` with offline/security behavior unchanged | passed | Full evidence package: 122 passed with one dependency deprecation warning |
| V8 | 5 | Documentation and generic Brain retain Compound records while excluding root-level research outputs | passed | Final Brain rebuild: 727 entities, 5 topics, 316 edges; exclusion check passed; scanner suite 40 passed; docs/path tests passed; known non-fatal slug/frontmatter warnings recorded |
| V9 | 5 | Generated Claude, Codex, OpenCode, and Kilo targets match updated canonical CR sources | passed | Generator wrote 1,222 files; target drift, closure, ownership, mapping, documentation, Kilo, and characterization checks pass |
| V10 | 6 | Boundary tests reject data placement, misplaced shared records, stale operational paths, conflicts, and lost files | passed | Strict migration classification, race fixtures, stale-path checks, and updater behavior tests pass |
| V11 | final | Existing shared fixtures, inbox, and generated views remain present and outside the migration | passed | Protected directories remain present and untouched; legacy research root absent |
| V12 | final | Required Python, evidence, docs, generated-target, Brain, safe Pester, and whitespace checks execute successfully | passed | Repository Python: 890 passed, 1 skipped; evidence: 122 passed; safe Pester: 2,446 passed, 0 failed, 3 skipped; migration `up-to-date`; diagnostics and diff check pass |

## Constraints Check

| ID | Phase | Constraint | Status | Evidence |
|---|---:|---|---|---|
| C1 | 1-3 | `c-research/` is output-only and `data/` is never a migration destination | passed | Path contract tests: 13 passed |
| C2 | 1-5 | `.cg-docs/` remains the Compound GPID process/knowledge layer | passed | Updated file maps and Brain scanner exclusion tests |
| C3 | 2 | Scaffolding is conditional on active `cr`; disabling `cr` is non-destructive | passed | Setup prompt/template contract tests |
| C4 | 2-3 | Migration is idempotent, conflict-safe, symlink-safe, and preserves bytes/frontmatter | passed | Migration tests: 29 passed, including no-follow ancestor, dangling-link, source-change, destination-race, and recovery cases |
| C5 | 3-5 | No second canonical `.cg-docs/research/` tree remains after verified migration | passed | Real repository check: `up-to-date`; legacy root absent and no operational references |
| C6 | 4-5 | CR workflows read/write `c-research/`; generic Brain remains `.cg-docs/`-only | passed | Active CR path scan, runtime root test, and Brain scanner suite |
| C7 | 4-5 | Generated targets come from canonical `.github/` sources | passed for current worktree | Reconciled advisory-only mapping; generator emitted all five targets from canonical sources |
| C8 | all | Shared fixtures, inbox ideas, generated views, and unrelated user changes are preserved | passed | Protected fixtures/inbox/views preserved; roadmap entities and context safety rules reconciled without unrelated loss |
| C9 | 4-7 | Evidence offline, original-authority, transaction, and P0 research-integrity behavior does not regress | passed | Full evidence suite 122 passed with one dependency deprecation warning |
| C10 | final | Completion is based on executed evidence, not static inspection alone | passed | Required Python, evidence, target, migration, Brain, Pester, diagnostics, and whitespace checks executed successfully |

## Remaining Uncertainty

- Full safe Pester run is green: 2,446 of 2,449 tests passed, with 0 failures
  and 3 environment-appropriate skips.
- Target drift now compares the generated worktree against canonical sources;
  the drift suite passes without requiring a commit during this worktree run.
- The 21-slide practitioner-tour manuscript matches the 21-slide presentation
  and is canonical. The former 16-slide draft is retained under an explicit
  superseded alternate filename.
- Existing presentation changes were preserved and the deck/source lineage was
  reconciled.
- The repository does not provide a Node runtime, so the separate JavaScript
  docs-site validator was not run; all available documentation and artifact
  contract checks passed.

## Final Status

`completed`
