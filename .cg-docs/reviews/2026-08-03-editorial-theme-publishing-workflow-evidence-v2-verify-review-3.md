---
date: 2026-08-08
depth: light
parent-review: .cg-docs/reviews/2026-08-03-editorial-theme-publishing-workflow-evidence-v2-review.md
type: verification
findings:
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
---

## Review Report

**Review mode**: light (verify pass, mode:verify) — fix-convergence pass after fix-triage.
**Files reviewed**: 10 changed paths (generated `.cg-docs/views/**` bodies excluded)
**Findings**: 4 (P0: 0, P1: 0, P2: 0, P3: 4)

### Verification mode context

This is a verify pass following fix-triage (the previous `-verify-review-2.md` had
17 findings, all `open`; fix-triage resolved all 17, and this pass verifies the
converged state of the Stage 2 readiness validator). Per Step 1.7, the most
recent prior review with `fixed` findings is
`2026-08-03-editorial-theme-publishing-workflow-evidence-v2-review.md` (13 fixed).
Per the suppression policy, P2/P3 findings are suppressed only when they target a
function/block explicitly listed as `fixed` in that prior review's `findings:`
map. None of its fixed findings target the Stage 2 validator diff, so suppression
is inert and all findings are reported. No P0/P1 correctness, security, or
data-integrity issue was found; the fix-triage changes did not introduce
regressions.

### P0 — BLOCKING

None.

### P1 — CRITICAL

None.

### P2 — IMPORTANT

None.

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `scripts/issues/readiness.py:667-701` — `get_open_closing_prs` pages through **every** open PR repo-wide and filters by closing keyword in Python.
  **Why**: O(open_prs/100) `gh pr list` subprocess calls with full body transfers on every validation — correct and read-only, but unnecessarily broad and slow for repositories with many open PRs.
  **Fix**: Derive closing PRs from a targeted source (e.g., the GraphQL `issue.closingIssuesReferences` connection scoped to the issue) or add an owner/base-branch filter. Non-blocking.

- **[P3.2]** [cg-code-quality] `scripts/issues/readiness.py:172-199,213-239` — Per-section fence re-tracking can diverge from whole-body tracking on an unclosed fence spanning a section boundary.
  **Why**: `parse_sections` tracks fence state over the whole body while per-section helpers (`_non_fence_lines`, `_verification_commands_nonempty` over section content) re-track from each section's start. Balanced fences are consistent; a fence opened in one section and closed later (or never closed) produces a more permissive interpretation in the isolated helpers.
  **Fix**: Require balanced fences per section, or thread a single fence-state token through both paths. Low priority — the structured contract is not expected to contain cross-section fences.

- **[P3.3]** [cg-testing] `scripts/tests/test_issue_readiness.py:536` — `test_whitespace_only_body_fails_all_contract_rules` name overstates coverage.
  **Why**: The asserted set omits `R015`–`R018`, which also fail on a whitespace-only body; the sibling `test_empty_issue_body...` (line 524) includes them. Holds as written, but the name is inaccurate and inconsistent with the neighbor.
  **Fix**: Add `"R015", "R016", "R017", "R018"` to the `contract_ids` set (optionally noting `R005`, `R012`, `R014` are expected *not* to fail).

- **[P3.4]** [cg-testing] `scripts/tests/test_issue_readiness.py:784` — `test_validation_calls_only_read_methods` redundant `dir()` introspection asserts on the test double, not the code.
  **Why**: Checking `FakeClient` for mutating method names tautologically guards the hand-written double; the real read-only guarantee is verified meaningfully by `test_gh_cli_client_only_issues_read_commands` (records actual `gh` argv pairs).
  **Fix**: Drop the `dir()`/`mutating`-names block (keep the `calls`-recording half).

### ✅ Passed

- `@cg-code-quality`: No P0/P1/P2. Fix-triage changes confirmed correct: `_iter_fence_state` behavior-equivalent across all consumers; per-occurrence `_has_blocking_dependency` negation; checkbox `(?:\s+|$)`; `pr list` pagination (terminates, read-only); `_repo_owner_name` via `_parse_json`; `stderr`-threaded parser; `_section_detail`; docstring security claims hold.
- `@cg-testing`: No P0/P1/P2. Suite hermetic, deterministic, cross-platform clean; 127 passed matches docs claim; new fix-triage tests are meaningful and non-tautological; CI registration correct.

## Validation

- `python -m pytest scripts/tests/test_issue_readiness.py -q` — 127 passed (0.15s).
- No live GitHub interaction in the suite (injected fake clients, monkeypatched subprocess, `tmp_path` fixtures only).
- `.cg-docs/views/**` bodies not read per scope.

Parsed 4 finding IDs. If count differs from total findings above, some IDs may be non-standard.