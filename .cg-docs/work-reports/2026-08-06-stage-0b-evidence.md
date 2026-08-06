---
date: 2026-08-06
title: "Stage 0B — Approved pre-pilot repairs evidence note"
type: evidence
plan: ".cg-docs/plans/2026-08-05-copilot-issue-implementation-pipeline-v2.md"
phase: 2
scope: "approved Stage 0B repairs; pilot issue prepared; STOPS before Copilot assignment"
---

# Stage 0B — Approved pre-pilot repairs evidence note

Human approval received (2026-08-06) for the Step 2 gate. Executed, in order:

## 1. Roadmap feature + canonical linkage (via @cg-roadmap)

- Milestone: `workflow-maturity` ("Workflow Maturity", stored status `in-progress`, now 15 features).
- Feature added: `artifact-html-opt-in-default` — "Make automatic artifact HTML publication opt-in by default" — `status: planned`, `plan: null`, concise description (from issue #127).
- Canonical linkage: `github: { repo: "GPID-WB/compound-gpid", issueNumber: 127, issueUrl: "https://github.com/GPID-WB/compound-gpid/issues/127", createdAt: "2026-08-06" }`.
- Marker vs canonical preserved: `compound-gpid-tracked` marker = recovery/duplicate-detection only; `features[].github` = canonical persistence.
- Historical linkage drift NOT repaired (out of scope this phase).

## 2. Issue #127 minimal edits (via `gh`, approved)

- `## Roadmap linkage`: milestone → `workflow-maturity`; canonical linkage → added (`roadmap.json`).
- `Ready for Copilot`: checked 3 of 4 ("execution contract approved", "roadmap feature created and linked", "exact allowed-path closure confirmed"); **Project Status `Backlog`→`Ready` box left unchecked**.
- All other body sections (outcome, acceptance criteria, non-goals, tests, path lists, verification commands, risk, human review, blocked-stop) preserved exactly.

## 3. Read-only verification (post-edit)

- Issue #127: OPEN, unassigned, labels `enhancement`,`cg:roadmap`; on CompoundGPID-progress; Project Status **Backlog**; no open PRs (no linked implementation PR).
- targeted roadmap validation: `Run-Tests.ps1 -File roadmap` → passed, 0 failures.
- Feature entry re-read and confirmed in `roadmap.json` (workflow-maturity).

## 4. Confirmed implementation closure (for Stage 1 reference)

- Core: `scripts/artifact_views/config.py` (sole resolver; config-resolution alone suffices).
- Tests: `scripts/artifact_views/tests/test_config.py`, `test_cli.py`, `test_generic_cli.py`, `test_integration.py`.
- Docs/contracts: `docs/configuration/index.md`, `docs/workflow.md`, `docs/reference.md`, `docs/troubleshooting.md`, `.github/shared/artifact-view.contract.md`.
- Generated targets (regenerate only): `.kilo`/`.claude`/`.agents`/`.opencode` `shared/artifact-view.contract.md`.

## 5. No further mutations

No Copilot assignment, no Project Status change, no labels, no workflows/settings/secrets, no new branches/PRs, no source/test/docs/contract edits, no Stage 1+ execution. The human must open/merge the Stage 0B PR and set issue #127 to Ready before Stage 1.
