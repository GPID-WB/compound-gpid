---
date: 2026-06-23
title: "Knowledge Brain Query and Budgeted Retrieval"
status: completed
completed-date: 2026-06-23
scope: "Deep"
brainstorm: null
language: "Python/Markdown"
estimated-effort: "large"
deviation-policy: "autonomous"
tags: [token-efficiency, knowledge-brain, retrieval, cg-index, context-budget]
phases: 4
completed-phases: [1, 2, 3, 4]
roadmap-features:
  - token-efficiency-core-system/phase-1-2-knowledge-brain-query
---

# Plan: Knowledge Brain Query and Budgeted Retrieval

## Objective

Implement Phase 1.2 by turning Knowledge Brain consumption into a bounded `cg-index query` interface that returns targeted, budget-aware context summaries for workflow prompts, while preserving the existing generated Brain artifacts and query-first fallback protocol.

## Context

Phase 1.1 created workflow-level token baseline artifacts and confirmed generated Brain/index artifacts are among the largest context surfaces. Existing `cg-skill-brain-query` already prevents wholesale prompt reads by starting from `.cg-docs/BRAIN.md` and matched `BRAIN-NN.md` topic sections. Phase 1.2 adds a native query layer so agents can ask `cg-index` for a bounded answer and selected snippets instead of manually opening generated Brain partitions by default.

Prior relevant patterns:
- `.cg-docs/plans/2026-06-07-token-optimization-phase5-brain-context-selectivity.md` established staged, query-first Brain loading.
- `.cg-docs/plans/2026-06-22-workflow-token-baseline.md` explicitly deferred `cg-index query` to this feature.
- `.cg-docs/strategy/2026-06-18-token-efficiency-workflow-strategy.md` defines the desired `cg-index query --intent <...> --changed-files ... --budget ...` direction.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Add `cg-index query` for budgeted Knowledge Brain retrieval. | roadmap strategy |
| R2 | Support intents: `brainstorm`, `plan`, `work`, `review`, `compound`, and `resume`. | roadmap strategy |
| R3 | Accept changed-file/path hints and a token budget to rank and bound output. | roadmap strategy |
| R4 | Return short answer, selected artifact paths, selected snippets, confidence, why selected, why excluded, stale/conflict flags, and token estimate. | roadmap strategy |
| R5 | Provide JSON and Markdown output formats for prompts and humans. | roadmap strategy |
| R6 | Prefer stdlib/native generated Brain data; do not introduce vector search, external services, optional retrieval backends, or production writes. | objective hard stops |
| R7 | Update `cg-skill-brain-query` to prefer `cg-index query` when available and fall back to the existing `BRAIN.md` topic-index workflow. | roadmap strategy |
| R8 | Add deterministic query benchmarks against known prior `.cg-docs/` artifacts. | roadmap strategy |
| R9 | Preserve generated Brain artifacts and existing `cg-index --brain`, legacy index/digest, and team-brain push behavior. | existing CLI contract |
| R10 | Keep all token-saving claims as baseline hypotheses unless measured with comparable repo probes. | objective hard stop |

## Phase 1: Query Core

### 1. Add Brain query data model and ranking helpers
- **Requirements**: R1, R3, R4, R6, R8, R10
- **Files**: `scripts/brain/query.py`, `scripts/brain/tests/test_query.py`
- **Details**:
  - Load existing local Brain entities using `brain.build_brain(root)` or the underlying scanner/extractor pipeline; do not read `brain-index.json` wholesale in prompt code.
  - Define allowed intents and their lightweight keyword boosts.
  - Score entities using existing extracted keywords, title/status/date/frontmatter, free-text query terms, and changed-file/path hints.
  - Select snippets from entity summaries and small body excerpts without copying entire artifacts.
  - Estimate output tokens with a documented heuristic and stop adding snippets before the requested budget is exceeded.
  - Return stable dictionaries with `schema_version`, `intent`, `query`, `budget_tokens`, `estimated_tokens`, `answer`, `selected`, `excluded`, `warnings`, and `confidence`.
- **Tests**:
  - Query selects relevant solution/plan artifacts for matching terms.
  - Changed-file hints boost artifacts that mention the same path.
  - Low budget still returns a bounded answer and at least paths/reasons when snippets are trimmed.
  - Missing `.cg-docs/` returns a clear nonzero CLI error, not fabricated results.

### 2. Detect stale and conflicting candidates conservatively
- **Requirements**: R4, R6, R8
- **Files**: `scripts/brain/query.py`, `scripts/brain/tests/test_query.py`
- **Details**:
  - Mark candidates stale when frontmatter status is `abandoned`, `superseded`, or `blocked`, or when a title/status explicitly signals obsolete guidance.
  - Mark potential conflicts when two selected candidates share strong keywords but disagree through status signals or supersession-like wording.
  - Keep flags advisory; do not hide P0/P1 safety-relevant artifacts solely due to staleness.
- **Tests**:
  - Abandoned brainstorm is returned only as stale/negative evidence.
  - Newer active solution outranks older stale candidate on the same keywords.
  - Conflict flags appear without failing the query.

## Phase 2: CLI and Formats

### 3. Add `cg-index query` CLI mode
- **Requirements**: R1, R2, R3, R5, R6, R9
- **Files**: `scripts/cg_index.py`, `scripts/brain/tests/test_query.py`, optional `scripts/tests/test_cg_index_cli.py`
- **Details**:
  - Add subcommand-style parsing for `cg-index query` while preserving existing flags.
  - Accept `--intent`, `--query`, repeated `--changed-file`, `--budget`, `--format json|md`, and `--root`.
  - Validate intent and budget with clear stderr errors and exit code `1`.
  - Default format should be Markdown for humans; JSON should be stable for prompt/tool callers.
  - Do not change `--brain`, `--index`, `--digest`, `--all`, or `--push-entry` behavior.
- **Tests**:
  - Parser accepts valid query invocations.
  - Invalid intent/budget fails clearly.
  - Existing `--brain` and `--version` tests remain compatible.

### 4. Render compact JSON and Markdown outputs
- **Requirements**: R4, R5, R10
- **Files**: `scripts/brain/query.py`, `scripts/brain/tests/test_query.py`
- **Details**:
  - JSON output includes all structured fields for prompt consumption.
  - Markdown output includes a short answer, selected artifacts with reasons, omitted/excluded notes, warnings, and token estimate.
  - Outputs must not include large raw artifact bodies.
  - Include a disclaimer that token estimates are heuristic and retrieval output is selection evidence, not proof of token savings.
- **Tests**:
  - JSON parses cleanly and contains required keys.
  - Markdown includes selected paths and not full source bodies.
  - Budget affects snippet count/length deterministically.

## Phase 3: Skill, Docs, and Benchmarks

### 5. Update Brain query skill and docs
- **Requirements**: R5, R7, R9, R10
- **Files**: `.github/skills/cg-skill-brain-query/SKILL.md`, `tests/prompt-tools.Tests.ps1`, `docs/workflow.md`, `docs/reference.md`
- **Details**:
  - Add a Step 0 preference: if `cg-index query` is available, use it with workflow intent and budget before manual `BRAIN.md` topic traversal.
  - Preserve fallback: if CLI unavailable, fails, or returns insufficient evidence, use the existing `BRAIN.md` topic-index protocol.
  - Keep the rule that prompt agents must not read `brain-index.json` wholesale; Python tooling may query generated indexes or Brain entities.
  - Document a few example commands without promising savings.
- **Tests**:
  - Prompt/skill contract test asserts `cg-index query`, `--intent`, `--budget`, and fallback to `BRAIN.md` remain present.

### 6. Add deterministic query benchmarks
- **Requirements**: R8, R10
- **Files**: `scripts/brain/tests/test_query.py`, optional `.cg-docs/token/` generated baseline update only if audit output schema already supports recording it.
- **Details**:
  - Use fixture `.cg-docs/` artifacts to benchmark known queries for Pester safety, token baseline, and Brain selectivity.
  - Assert selected paths include expected top artifacts and estimated output stays under budget.
  - Do not depend on network, embeddings, or real external services.
- **Tests**:
  - `python3 -m pytest scripts/brain/tests/test_query.py -q`
  - `python3 -m pytest scripts/brain/tests scripts/tests -q`

## Phase 4: Validation, Review, and Roadmap

### 7. Validate integration and regenerate Brain only if needed
- **Requirements**: R6, R8, R9, R10
- **Files**: touched files plus generated Brain artifacts only if `cg-index --brain` output changes due to intentional metadata updates.
- **Details**:
  - Run targeted Python tests for query and existing Brain modules.
  - Run full Python audit/brain/team-brain tests if feasible.
  - Run canonical Pester safe runner through `tests/Run-Tests.ps1`.
  - Run representative `cg-index query` commands in JSON and Markdown modes.
  - Run `cg-index --brain` only if implementation changes indexed source artifacts and generated Brain files need refresh.
- **Tests**:
  - `python3 -m pytest scripts/brain/tests scripts/tests -q`
  - `python3 -m pytest scripts/team_brain/tests -q`
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"`

### 8. Review, fix, compound, and mark roadmap done
- **Requirements**: R7, R8, R9, R10
- **Files**: `.cg-docs/reviews/*`, `.cg-docs/work-reports/*`, `.cg-docs/solutions/*`, `roadmap.json`
- **Details**:
  - Run `/cg-plan-review`, `/cg-work review:auto deviate:auto`, `/cg-fix-triage`, `/cg-review mode:verify`, `/cg-fix-triage`, and `/cg-compound` per the batch objective.
  - Link this plan to `phase-1-2-knowledge-brain-query` through the roadmap manager contract and mark done only after evidence passes.
  - Make a feature-scoped conventional commit.

## Testing Strategy

- Python unit tests for query ranking, budget trimming, stale/conflict flags, CLI parsing, and rendering.
- Existing Brain module tests to guard scanner/extractor/renderer behavior.
- `tests/prompt-tools.Tests.ps1` for skill/prompt contract wording.
- Canonical safe runner for repository Pester validation.
- Representative CLI smoke tests:
  - `python3 scripts/cg_index.py query --root . --intent plan --query "workflow token baseline" --budget 600 --format json`
  - `python3 scripts/cg_index.py query --root . --intent review --query "Pester safe runner" --changed-file tests/Run-Tests.ps1 --budget 600 --format md`

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Query mode becomes an untested search engine rewrite. | Use deterministic keyword scoring over existing Brain entities; no embeddings or services. |
| Output exceeds budget or copies too much source. | Budget snippets before rendering and test low-budget behavior. |
| Skill update breaks fallback for environments without CLI. | Keep existing `BRAIN.md` protocol intact and covered by prompt tests. |
| Existing `cg-index` modes regress. | Add parser/CLI tests and run existing Brain tests. |
| Stale/conflict flags overclaim correctness. | Make flags advisory and evidence-based from metadata/status only. |

## Out of Scope

- Vector search, embeddings, MCP retrieval backends, optional external services, or code-intelligence adapters.
- Command-output summarization wrappers.
- Snapshot/external-research modes.
- Replacing or deleting generated Brain artifacts.
- Any token-saving claim without same-probe measurement.

## Completion Contract

### Outcome

Phase 1.2 is complete when `cg-index query` can return bounded JSON/Markdown Knowledge Brain retrieval results for workflow intents, `cg-skill-brain-query` prefers that interface with a safe fallback, and validation proves the query output is deterministic, budget-aware, and compatible with existing Brain generation.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Query core ranks relevant Brain artifacts and respects token budget. | `python3 -m pytest scripts/brain/tests/test_query.py -q` | yes |
| V2 | 2 | `cg-index query` accepts valid args, rejects invalid args, and renders JSON/Markdown. | CLI tests and representative query commands | yes |
| V3 | 3 | `cg-skill-brain-query` prefers `cg-index query` and preserves `BRAIN.md` fallback/no-wholesale rules. | `tests/prompt-tools.Tests.ps1` through safe runner | yes |
| V4 | 3 | Query benchmarks select expected prior artifacts under budget. | `scripts/brain/tests/test_query.py` benchmark tests | yes |
| V5 | final | Existing Brain generation and legacy `cg-index` modes remain compatible. | `python3 -m pytest scripts/brain/tests -q`; `python3 scripts/cg_index.py --brain --root <tmp fixture or repo>` as appropriate | yes |
| V6 | final | Repository Pester safe runner passes. | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"` | yes |
| V7 | final | No external retrieval backend, vector service, or token-saving claim is introduced. | Diff/review evidence | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | all | Keep retrieval stdlib/native and local. | No new dependency or network calls. |
| C2 | all | Preserve generated Brain artifacts and `cg-index --brain`. | Existing Brain tests and smoke run pass. |
| C3 | all | Preserve manual `BRAIN.md` fallback in the skill. | Prompt/skill test and skill review. |
| C4 | all | Do not implement Phase 1.3+ wrappers/backends/snapshots. | Diff review. |
| C5 | all | Treat token estimates as heuristic and non-savings evidence. | Rendered output/docs wording. |
| C6 | all | Preserve Pester safety. | Safe runner only; no unsafe `Invoke-Pester` recipes. |
| C7 | all | Preserve roadmap write discipline. | Roadmap updates through manager contract after verification. |

### Boundaries

- Allowed: `cg-index query` CLI, local Brain query module, tests, skill/docs updates, generated review/work/solution evidence.
- Out of scope: external search/retrieval, command output summaries, cross-agent adapters, snapshots, deleting generated Brain files.

### Iteration Policy

1. Prefer small deterministic scoring over architectural retrieval abstractions.
2. If query precision is imperfect, improve fixture-backed scoring once before broadening scope.
3. If budgeted output cannot include snippets, return paths/reasons/confidence rather than exceeding budget.
4. Under `deviation-policy: autonomous`, record deviations in the work report and stop only if a hard-stop condition applies.

### Blocked-Stop Conditions

- Query mode requires a new external service, dependency, or backend.
- Existing `cg-index --brain` behavior regresses.
- Safe runner or required Python tests fail and cannot be fixed within scope.
- Skill update removes the manual `BRAIN.md` fallback.
- Completion would require claiming token savings without same-probe evidence.
