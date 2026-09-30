---
date: 2026-08-11
depth: light
parent-review: .cg-docs/reviews/2026-08-11-copilot-issue-implementation-pipeline-v2-phase5-review.md
type: verification
findings:
  P1.1: fixed
  P2.1: fixed
  P2.2: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
---

# Verify Review — Phase 5 dispatcher fixes converge (2026-08-11)

## Provenance

`/cg-review mode:verify` run after `/cg-fix-triage` on the Phase 5 dispatcher.
Prior review: `.cg-docs/reviews/2026-08-11-copilot-issue-implementation-pipeline-v2-phase5-review.md`
(32 findings fixed, 3 skipped). Verify agents: `@cg-code-quality`,
`@cg-testing`. Depth forced to `light`.

**Suppression policy** (applied): P0/P1 always reported; P2/P3 suppressed only
when clearly anchored to a finding already listed `fixed` in the prior review;
cross-file breakage always reported; doubt defaulted to report.

## Verification Facts

- Dispatcher suite: `python -m pytest scripts/tests/test_issue_dispatch.py -q`
  → 61 passed (baseline before verify was 55; verify-added tests raised it).
- Combined dispatch + readiness: 61 + 194 = 255 passed.
- Full native-targets gate: 621 passed, 11 skipped (run after fix-triage,
  before verify additions); verify additions re-run against the gate list
  covered by the dispatcher + readiness files above.

## Verification Report

**Review mode**: verification (light)
**Files reviewed**: `scripts/issues/dispatch.py`, `dispatch_client.py`,
`dispatch_project.py` (new), `dispatch_util.py`, `dispatch_cli.py`,
`dispatch_render.py`, `dispatch_contract.py` (new), `gh_process.py`,
`scripts/tests/test_issue_dispatch.py`, `.github/workflows/copilot-dispatch.yml`,
`docs/copilot-dispatch.md`
**Findings**: 6 (P0: 0, P1: 1, P2: 2, P3: 3)

### P1 — CRITICAL

- **[P1.1]** [cg-code-quality] `scripts/issues/dispatch.py` + `dispatch_render.py` + `dispatch_cli.py` — the P1.3 split introduced a hard circular import (`dispatch` ⇄ `dispatch_cli` ⇄ `dispatch_render`), unlike the acyclic readiness graph.
  **Why**: `import issues.dispatch` happened to work only because the facade re-imports sit after every definition (`# noqa: E402`); `import issues.dispatch_cli` / `import issues.dispatch_render` independently raised `ImportError` from a partially initialized module. Any move of the re-exports to module top breaks the primary entry.
  **Fix**: Split the leaf `dispatch_contract.py` (types + constants) and defer `run_dispatch` import inside `main()` exactly like `cli.py:99`, giving an acyclic graph with `dispatch.py` as a pure facade.
  Tag: [safe_auto] — applied (acyclic import verified empirically; see below).

### P2 — IMPORTANT

- **[P2.1]** [cg-testing] `scripts/issues/dispatch_client.py` — `_repo()` (the `gh repo view` call site) is entirely untested: all mutator tests inject `owner=`/`name=`, so the JSON parse, `expect_mapping` wrong-shape guard, `nameWithOwner` ConfigError guard, and the P3.2 `defaultBranchRef → _base_branch` derivation were never exercised.
  **Why**: typed-invalid regression tests are required per remote call site (`.cg-docs/solutions/bugs/2026-08-10-...`); a regression here would silently break exit-code classification and mis-target the Copilot base branch.
  **Fix**: add tests with no `owner`/`name` injection: valid `defaultBranchRef` flows into the assign body `base_branch`; missing `/` → ConfigError; array payload → ApiError.
  Tag: [safe_auto] — applied.

- **[P2.2]** [cg-testing] `scripts/tests/test_issue_dispatch.py` `test_least_privilege_permissions` — evadable: only the text after the first `permissions:` occurrence was scanned, so the job-level permissions block (the one governing the step that exports live secrets) was never checked; the allowlist was a negative scan, not an allowlist.
  **Why**: adding `actions: write`/`checks: write` to the job-level block would pass every assertion while granting a write scope to the job holding both live dispatch secrets.
  **Fix**: scan every `permissions:` block and enforce an allowlist (`contents: read` only).
  Tag: [safe_auto] — applied.

### P3 — MINOR

- **[P3.1]** [cg-testing] `scripts/issues/dispatch_client.py` — the strict-nodes branches added for P3.21 (non-Mapping node → ApiError, wrong-shape content → ApiError) had no regression test.
  **Fix**: add two tests feeding typed-invalid node/content payloads.
  Tag: [safe_auto] — applied.

- **[P3.2]** [cg-testing] `scripts/issues/dispatch_client.py` — P2.3's fix note promised an unwritable-temp regression test but `_write_temp_file`'s `OSError → ApiError` wrap was never exercised.
  **Fix**: monkeypatch `tempfile.NamedTemporaryFile` to raise `OSError` and assert `ApiError`.
  Tag: [safe_auto] — applied.

- **[P3.3]** [cg-code-quality] `dispatch_client.py` (447 lines) still exceeds the <300-lines rule, and `COPILOT_ASSIGN_LOGIN` was duplicated in `dispatch.py` and `dispatch_client.py` (drift hazard for the most security-sensitive literal).
  **Why**: the P1.3 fix only slimmed `dispatch.py`; `dispatch_client` had grown with the new mutation checks.
  **Fix**: split helpers into `dispatch_project.py`/`dispatch_util.py`; single-source `COPILOT_ASSIGN_LOGIN`/`IN_PROGRESS_STATUS` in `dispatch_contract.py`.
  Tag: [safe_auto] — applied (all four leaf modules now ≤ 279 lines; login/status single-sourced).

## Post-verify re-check

- All new modules independently importable: acyclic graph verified via
  `import issues.dispatch_cli`, `import issues.dispatch_render`, etc.
- Line counts: dispatch.py 279, dispatch_client.py 260, dispatch_project.py 234,
  dispatch_render.py 70, dispatch_cli.py 110, dispatch_util.py 74,
  dispatch_contract.py 52.
- Dispatcher suite 61 passed; readiness 194 passed.

## Disposition

All six verify findings fixed in-place during this run and verified by the
61-pass dispatcher suite. No open findings remain; the fix cycle has converged.
