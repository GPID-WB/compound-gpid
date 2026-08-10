---
date: 2026-07-31
depth: research
type: standard
plan: .cg-docs/plans/2026-07-30-cr-scoping-normative-gates.md
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P2.1: fixed
---

## Review Report

**Review mode**: research
**Files reviewed**: 28
**Findings**: 5 (P0: 0, P1: 4, P2: 1, P3: 0)

### P1 - CRITICAL (must fix before merge)
- **[P1.1]** [cg-code-quality] .github/prompts/cr-plan.prompt.md:63 - `/cr-plan` frontmatter cannot encode `Research Scoping`
  **Why**: The canonical CR taxonomy is now 10 task types, but the saved plan template still enumerates only 9 and omits `Research Scoping`. Plans generated from this prompt cannot represent a supported task type, which risks downstream misrouting in `/cr-work` and `/cr-review`.
  **Fix**: Add `Research Scoping` to the `task-type:` enum in the YAML template and keep prompt/test taxonomy assertions aligned with the 10-type workflow.

- **[P1.2]** [cg-architecture] .github/shared/review-routing.contract.md:13 - Shared `research` routing omits the new CR review agents
  **Why**: The shared routing contract for `/cg-review` and `/cg-work review:*` still dispatches `research` mode without `@cr-provenance-audit` and `@cr-measurement-integrity`, even though the current CR docs and authored review surfaces treat both as first-class review agents. Generic research reviews can therefore under-dispatch provenance and measurement integrity coverage.
  **Fix**: Add the missing agents to the shared `research` route and sync the consuming prompt/docs/tests that mirror this registry.

- **[P1.3]** [cg-data-quality] .cg-docs/active-state/current.json:4 - Active-state points the completed CR execution at the wrong workflow
  **Why**: `cr-work.prompt.md` says CR execution state should record `workflow: "/cr-work"`, but the committed active-state pointer stores `/cg-work` while referencing CR-only plan/report artifacts and `nextCommand: "/cr-review"`. That weakens resume and handoff routing.
  **Fix**: Record `/cr-work` for CR execution states and keep the active-state writer aligned with the CR handoff contract.

- **[P1.4]** [cg-testing] tests/Run-Tests.ps1:297 - Top-level test artifact counters overstate full-pass evidence
  **Why**: The runner artifact writes `totalCount = passedCount + failedCount`, ignoring non-passed/non-failed cases. The committed `tests/last-run.json` shows per-file mismatches (`cr-prompts` 620 total / 619 passed / 0 failed; `update` 138 total / 136 passed / 0 failed), yet the top-level artifact and downstream reports claim `2990/2990 passed, 0 failures`. That turns a reporting bug into overstated validation evidence.
  **Fix**: Persist explicit skipped or unaccounted counts from per-file totals, derive top-level totals from per-file `TotalCount`, and downgrade work-report/active-state language until the artifact math is reconciled.

### P2 - IMPORTANT (should fix)
- **[P2.1]** [cg-documentation] docs/reference.md:326 - Canonical reference is not yet synced to the shipped CR surface
  **Why**: The main reference page still lacks a discoverable `/cr-*` command section and the review-agent table omits `cr-replication-package`, even though CR routing and instructions expose those surfaces. That leaves user-facing docs behind the implemented CR expansion and makes `V5` broader than the page currently supports.
  **Fix**: Add a CR commands subsection to `docs/reference.md` and include the missing `cr-replication-package` review agent row so the public reference matches the current workflow.

### ✅ Passed
- `cr-ml-methodology`: No issues found

> Review report saved to `.cg-docs/reviews/2026-07-30-cr-scoping-normative-gates-review.md`. Use `/cg-fix-triage` in a future session to apply findings by ID (for example `/cg-fix-triage P1.2 P2.1`) or by priority level (for example `/cg-fix-triage P1`).