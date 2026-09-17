---
date: 2026-09-16
depth: light
parent-review: .cg-docs/reviews/2026-09-08-evidence-backed-cg-help-command-review.md
type: verification
findings:
  P1.1: fixed
  P1.2: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P2.9: fixed
  P2.10: fixed
  P2.11: fixed
  P2.12: fixed
  P2.13: fixed
  P2.14: fixed
  P2.15: fixed
  P2.16: fixed
  P2.17: fixed
  P2.18: fixed
  P2.19: fixed
  P2.20: fixed
  P2.21: fixed
  P2.22: fixed
  P2.23: fixed
  P2.24: fixed
  P2.25: fixed
  P2.26: fixed
  P2.27: fixed
  P2.28: fixed
  P2.29: fixed
  P2.30: fixed
  P2.31: fixed
  P2.32: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
  P3.7: fixed
  P3.8: fixed
  P3.9: fixed
  P3.10: fixed
  P3.11: fixed
  P3.12: fixed
  P3.13: fixed
  P3.14: fixed
  P3.15: fixed
  P3.16: fixed
  P3.17: fixed
  P3.18: fixed
  P3.19: fixed
  P3.20: fixed
  P3.21: fixed
  P3.22: fixed
  P3.23: fixed
  P3.24: fixed
  P3.25: fixed
  P3.26: fixed
  P3.27: fixed
  P3.28: fixed
  P3.29: skipped
  P3.30: fixed
  P3.31: fixed
  P3.32: fixed
  P3.33: fixed
  P3.34: fixed
  P3.35: fixed
  P3.36: fixed
  P3.37: fixed
  P3.38: fixed
  P3.39: fixed
  P3.40: fixed
  P3.41: fixed
  P3.42: fixed
  P3.43: fixed
  P3.44: fixed
  V-P3.1: fixed
  V-P3.2: fixed
  V-P3.3: fixed
  V-P3.4: fixed
  V-P3.5: fixed
  V-P3.6: fixed
  V-P3.7: fixed
---

# Verification Review 2: Evidence-Backed /cg-help Command

**Date**: 2026-09-16
**Mode**: verify (light-only)
**Type**: verification
**Parent review**: `.cg-docs/reviews/2026-09-08-evidence-backed-cg-help-command-review.md`
**Predecessor verify**: `.cg-docs/reviews/2026-09-08-evidence-backed-cg-help-command-verify-review.md` (cycle 1)
**Head (before/after)**: `53966262c430b44145508b7837ebcc9a11a1aa5c` (unchanged)
**Settled decisions (not reopened)**: D1–D5, OR-set approval 2026-09-15T01:58Z, five-decision approval 2026-09-15T18:45Z, V-P3.1–V-P3.7 fix record 2026-09-15T23:45Z.

## Review Context

- **Scope**: second verification of the fix cycle per pipeline convergence rule, on
  CURRENT WORKTREE BYTES (no commit between cycles; HEAD unchanged).
- **Suppression context** (per Step 1.7): prior review file
  `.cg-docs/reviews/2026-09-08-evidence-backed-cg-help-command-review.md`;
  resolved findings: P1.1, P1.2, P2.1–P2.32, P3.1–P3.28, P3.30–P3.44
  (P3.29 explicitly skipped). V-P3.1–V-P3.7 fixed by the fix-triage record in
  the cycle-1 verify file. Policy applied: P0/P1 always reported; P2/P3
  suppressed only when targeting a block explicitly listed as `fixed`;
  cross-file breakage always reported; when in doubt, report.
- **Dispatch**: `@cg-code-quality` and `@cg-testing` (light depth), two fresh
  foreground Task leaves (`background:false`, no nested Task). Both returned
  usable output.
- **Protected artifacts**: no finding recommends deleting, replacing, renaming,
  or moving `.cg-docs/`, `compound-gpid.md`, `compound-gpid.local.md`,
  `roadmap.json`, `SCHEMA_VERSION`, or `.github/` infrastructure.
- **Certification**: no runtime/host certification claims made; `open-brain`
  unavailable (recorded, not passed). Repository Brain topic index consulted;
  no stale or contradictory entries relevant to the seven fix sites.

## Verification Results

All 7 verification findings from cycle 1 are CONFIRMED FIXED on current bytes.
No new P0 or P1 finding, parent or new. The complete findings map for the
second cycle has P0 = 0 open and P1 = 0 open; convergence holds.

### V-P3.1 .. V-P3.7 — Verified Fixed (current bytes)

- **V-P3.1 fixed** — `scripts/skill_management/services/catalog.py`: no
  `import json` remains; module imports (lines 1–15) are dataclasses/pathlib/
  typing/services; the only `json`-named lines are string literals and the
  lazy `from help.catalog import load_strict_json_bytes` (line 133); no `json.`
  usage anywhere. Whole-file scan confirms.
- **V-P3.2 fixed** — `scripts/cg_project_projection.py:632-634`
  `_inventory_staged_destinations` annotated `-> dict[str, str]`, docstring
  updated, body `inventory: dict[str, str] = {}`, UTF-8 Markdown decode check
  kept inline (lines 653–657); both consumers (`_validate_staged_tree` line
  669, arena re-hash line 1263) only use key membership/`.get()`; test consumer
  `test_project_projection.py:75` compatible. Cross-file breakage: none.
- **V-P3.3 fixed** — `scripts/cg_generate_targets.py:1968-1973` comment above
  the `re.sub` site (line 1974) documents the
  `<!-- help-argument-source:start/end -->` marker contract (markers must stay
  in the canonical prompt; the emitted invocation-tail file must carry the
  block). No behavior change.
- **V-P3.4 fixed** — `.github/prompts/cg-commit-push-pr.prompt.md:184-189`
  exit-3 bullet nested at `   - ` under Step 6 (line 169) with 6-space
  continuations, matching sibling bullets (exit-2 line 175, write gate line
  190, recheck line 194); prose bytes unchanged; digest chain for
  `slash:cg-commit-push-pr` refreshed via reviewed repin to
  `28dc378438267a0a791b005db1ed0c6dd68a0acfa83c936505ae3b81c9aa5c08`,
  catalog `--check` exit 0 (this stage).
- **V-P3.5 fixed** — `scripts/help/maintenance.py:30-36` imports
  `validate_source_metadata` (and `_read_source_bytes`, `_source_path`,
  `compute_definition_digest`, `validate_catalog`) directly from
  `help.validation`; no `from help import catalog as catalog` alias remains
  anywhere in `scripts/`. Import graph acyclic: `maintenance -> {base,
  validation}`, `catalog -> {base, installers, maintenance, validation}`;
  all 7 facade re-exports (lines 68–76) still resolve. Test seams:
  `test_help_catalog.py:738,1075` monkeypatch the live
  `maintenance.validate_source_metadata` attribute; assertions unchanged.
- **V-P3.6 fixed** — `scripts/tests/test_kilo_coexistence.py` adds
  `_fake_kilo_version_output` (lines 105–121, POSIX+Windows correct) and
  parametrize coverage (line 124): rejects `v7.4.20` / `7.4.20.1` /
  `Kilo 7.4.20` / `version: 7.4.20` with
  `(None, "Kilo version output was not recognized")` (lines 125–129) and a
  first-non-empty-line parse case (`7.4.21` + trailing junk → `("7.4.21",
  None)`, lines 132–136). Matches production `_read_version`
  (`cg_kilo_preflight.py:509-521` first-non-empty-line + fullmatch); a
  `.search` regression would fail all four reject cases. Existing tests
  unchanged. This stage: 5 passed / 0 failed.
- **V-P3.7 fixed** — `scripts/tests/test_cg_pr_preflight.py:393-395` guards
  with `shutil.which("node") is None → pytest.skip` before any
  `subprocess.run(["node", ...])`; docstring (lines 382–392) documents the
  literal 10-space `script: |` extraction anchor (live at
  `.github/workflows/tests.yml:110`), the genuinely untrusted injected
  inputs, and fail-loud extraction on re-indentation. All eight parametrized
  assertions unchanged (lines 380, 425–429).

## Verification Findings Map (cycle 2)

| Severity | Open | Fixed | Skipped | Total |
|----------|------|-------|---------|-------|
| P0       | 0    | 0     | 0       | 0     |
| P1       | 0    | 2     | 0       | 2     |
| P2       | 0    | 32    | 0       | 32    |
| P3 (parent) | 0  | 43    | 1       | 44    |
| P3 (new V-P3.*) | 0 | 7    | 0       | 7     |
| **Total**| **0**| **84**| **1**   | **85**|

Required-to-pass criterion met: P0 = 0 open, P1 = 0 open.

## Incomplete Reviews

None. Both dispatch targets (`@cg-code-quality`, `@cg-testing`) produced
usable output.

## Passed

- `@cg-code-quality`: V-P3.1–V-P3.5 verified applied with matching
  documentation on current bytes; no new findings; no cross-file breakage.
- `@cg-testing`: V-P3.6/V-P3.7 verified applied with matching assertions and
  the V-P3.5 seam re-pointing verified effective; no new findings.

## Evidence (this stage)

| Gate | Command | Result |
|------|---------|--------|
| Focused parse tests (this stage) | `python -B -m pytest scripts/tests/test_kilo_coexistence.py -q -k "read_version"` | 5 passed / 0 failed |
| Catalog integrity (this stage) | `python scripts/cg_generate_help_catalog.py --check` | exit 0 — "help catalog is current" |
| Recorded full gate (predecessor fix-triage, current bytes) | `. tests\Run-Tests.ps1` filteredFiles null, 2026-09-16T00:32:33Z | 2851 passed / 0 failed / 2 skipped (`tests/last-run.json` is that PASSING artifact) |
| Recorded prompt-tools gate (current bytes) | `. tests\Run-Tests.ps1 -File prompt-tools`, 2026-09-16T00:28:04Z | 1672 passed / 0 failed |
| Recorded catalog check (fix-triage) | `python scripts/cg_generate_help_catalog.py --check` | exit 0 |
| Recorded focused Python battery (fix-triage) | `pytest test_kilo_coexistence test_cg_pr_preflight test_project_projection test_cg_generate_targets test_target_drift` | 280 passed / 21 skipped / 0 failed |
| Recorded focused Python battery (fix-triage) | `pytest test_help_catalog test_help_query test_cg_help test_skill_management_completeness test_help_support` | 307 passed / 0 failed (after seam re-point) |
| Recorded compileall + diff-check (fix-triage) | `python -m compileall -q` + `git diff --check` | exit 0, clean (pre-existing `.gitignore` notice only) |

The earlier recorded `link.Tests` junction flake did not recur in the
2026-09-16T00:32:33Z gate. No PS1 file changed in this stage; retained gate
evidence remains valid for current bytes.

## Step 3.5 Conformance

- Filename: `2026-09-08-evidence-backed-cg-help-command-verify-review-2.md`
  (cycle-1 verify file `...-verify-review.md` existed, so the command's
  counter rule applies; the peer-suggested `...-verify-2-review.md` variant is
  superseded by the command's prescribed `-verify-review-2.md` counter form).
- `parent-review:` target exists and was read (standard review file).
- Findings map: parent IDs `fixed` (P3.29 `skipped`), V-P3.1–V-P3.7 `fixed`.
- Report written directly by the orchestrator (not delegated).

## Handoff

- **Head**: `53966262c430b44145508b7837ebcc9a11a1aa5c` unchanged before/after
  (no commit/stage/push/merge/rebase/PR mutation; report file added only).
- **Findings map**: P0 0 open, P1 0 open; all parent and V-P3.* findings fixed
  (P3.29 skipped); no unresolved manual findings. Convergence criteria met.
- **Next stage**: `batch1-commit-push-pr`.
- **Certification**: Step 12 remains out of scope; no host is certified by
  this review.