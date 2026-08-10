---
date: 2026-08-10
depth: light
parent-review: .cg-docs/reviews/2026-08-03-editorial-theme-publishing-workflow-evidence-v2-review.md
type: verification
findings:
  P2.1: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: skipped
  P3.4: fixed
  P3.5: fixed
---

## Review Report

**Review mode**: light (verify pass, mode:verify) — convergence pass after two fix-triage cycles.
**Files reviewed**: 10 changed paths (generated `.cg-docs/views/**` bodies excluded)
**Findings**: 6 (P0: 0, P1: 0, P2: 1, P3: 5)

### Verification mode context

This is a verify pass following two fix-triage cycles (17 findings resolved in the
first, 4 P3 polish findings in the second; all marked `fixed` in
`-verify-review-2.md` / `-verify-review-3.md`). Per Step 1.7, the most recent
prior review with `fixed` findings is
`2026-08-03-editorial-theme-publishing-workflow-evidence-v2-review.md` (13 fixed).
Per the suppression policy, P2/P3 findings are suppressed only when they target a
function/block explicitly listed as `fixed` in that prior review's `findings:`
map. None of its fixed findings target the Stage 2 validator diff, so suppression
is inert and all findings are reported. No P0/P1 security or data-integrity issue.

### P0 — BLOCKING

None.

### P1 — CRITICAL

None.

### P2 — IMPORTANT

- **[P2.1]** [cg-code-quality] `scripts/issues/readiness.py:659` (also 691, 714-715, 730) — Typed-invalid (valid JSON, wrong shape) `gh` responses crash with uncaught `ValueError`/`TypeError`/`AttributeError` → raw traceback and exit 1 instead of the documented `ApiError` → exit 4.
  **Why**: `_parse_json` guards only JSON *syntax* errors, not type errors. Empirically confirmed: `"number": "abc"` in `issue view` raises `ValueError`; `get_project_status` raises `AttributeError` if `projectItems.nodes` isn't a list of dicts. None are caught by `validate_readiness` (only `ConfigError`/`ApiError`) or `main()`. This violates the module docstring, the `ApiError` docstring ("malformed response"), and the exit-code table in `docs/copilot-readiness.md` (exit 4 = "malformed response"), and yields exit 1 — indistinguishable from an unrelated crash for a Stage 3 dispatcher relying on the exit-code contract.
  **Fix**: Wrap payload field extraction in a helper (or `try/except (ValueError, TypeError, AttributeError)`) that re-raises as `ApiError(f"malformed {label} response from gh: ...")`, mirroring `_parse_json`.

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `scripts/issues/readiness.py:331-335` (correlate `docs/copilot-readiness.md`) — "cannot be blocked by" is a false-positive blocker, contradicting the doc's "informational prose is not blocking".
  **Why**: Probe: `_has_blocking_dependency(["This cannot be blocked by anything."])` → blocking. The negation regex `\bnot\s+$` matches only exact "not blocked by"; "cannot be blocked by" (semantically not blocked) is flagged. Fail-closed (false NOT READY, never false READY). Doc sentence overstates the behavior.
  **Fix**: Extend negation to also skip "cannot be / can't be / not be … blocked by", or tighten the doc wording.

- **[P3.2]** [cg-code-quality] `docs/copilot-readiness.md` — R002 row attributes "exactly one `**Feature ID:**` line" to `## Roadmap linkage`, but code counts Feature ID lines across the entire body.
  **Why**: `find_feature_id` scans all non-fence lines, not the Roadmap linkage section, so a Feature ID in another section still passes R002. Doc presents a stricter contract than the code enforces — a dispatch-gating doc/code mismatch.
  **Fix**: Reword the row to "the body must contain exactly one … line (matching the tracked marker)", or scope `find_feature_id` to Roadmap linkage if the stricter contract is intended.

- **[P3.3]** [cg-code-quality] `.cg-docs/active-state/current.json` and `.cg-docs/work-reports/2026-08-06-copilot-issue-implementation-pipeline-v2.md` — Stale test counts ("103 focused/deterministic tests") vs. the converged 127 passing tests.
  **Why**: Count claims superseded by the recent hardening/polish additions and contradict `docs/copilot-readiness.md` ("~127"), creating an internal contradiction for reviewers.
  **Fix**: Refresh counts (and re-run the full native-targets invocation) when updating metadata before merge.

- **[P3.4]** [cg-code-quality] `scripts/tests/fixtures/ready_issue.json` ↔ `scripts/issues/readiness.py:823` — Fixture PR items use `headRef`, but the gh client reads `headRefName` for the same field.
  **Why**: If a maintainer copies real `gh pr list --json` output into the offline fixture, `head_ref` silently becomes `""`; no test covers it because the fixture has no PRs. Latent schema trap.
  **Fix**: Rename the fixture key to `headRefName` (matching gh) or document the fixture's `headRef` convention.

- **[P3.5]** [cg-testing] `scripts/tests/test_issue_readiness.py:535-543` — R005/R012/R014 non-failing behavior on empty bodies is documented only in a comment, not asserted.
  **Why**: A future refactor making R012/R014 stricter on empty bodies would pass silently (the NOT-READY verdict is unaffected), masking the regression.
  **Fix**: Add a guard, e.g. `assert _failed_ids(result) & {"R005", "R012", "R014"} == set()`.

### ✅ Passed

- `@cg-code-quality`: No P0/P1. Converged refactor verified correct (fence iterator, negation, pagination, `_parse_json`, `err`-threaded parser, `_section_detail`); recent test/doc edits accurate; security docstring claims hold.
- `@cg-testing`: No P0/P1/P2. Suite hermetic, deterministic, cross-platform clean; 127 passed equals the `~127` doc claim; recent test edits meaningful and non-tautological; CI registration correct; R020/fence doc notes consistent with code.

## Validation

- `python -m pytest scripts/tests/test_issue_readiness.py -q -p no:cacheprovider` — 127 passed (~0.15s).
- Module imports and exit codes 0/2/3/4 verified; no live GitHub interaction in suite.
- `.cg-docs/views/**` bodies not read per scope.

Parsed 6 finding IDs. If count differs from total findings above, some IDs may be non-standard.