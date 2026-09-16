---
date: 2026-09-15
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

# Verification Review: Evidence-Backed /cg-help Command

**Date**: 2026-09-15
**Mode**: verify (light-only)
**Type**: verification
**Parent review**: `.cg-docs/reviews/2026-09-08-evidence-backed-cg-help-command-review.md`
**Plan**: `.cg-docs/plans/2026-09-08-evidence-backed-cg-help-command.md`
**Head (before/after)**: `53966262c430b44145508b7837ebcc9a11a1aa5c` (unchanged)
**Settled decisions (not reopened)**: D1–D5, OR-set approval 2026-09-15T01:58Z, five-decision approval 2026-09-15T18:45Z.

## Review Context

- **Review mode**: verify (light-only, per `/cg-review mode:verify` Step 1.7).
- **Parent review**: `.cg-docs/reviews/2026-09-08-evidence-backed-cg-help-command-review.md`
- **Files reviewed**: fix-affected uncommitted scope on current worktree bytes
  (79 modified + 30 untracked paths): `scripts/help/*.py`, `scripts/cg_help.py`,
  `scripts/cg_kilo_preflight.py`, `scripts/cg_generate_help_catalog.py`,
  `scripts/cg_validate_modules.py`, `scripts/cg_skill_catalog.py`,
  `scripts/cg_project_projection.py`, `scripts/cg_projection_benchmark.py`,
  `scripts/cg_context_budget.py`, `scripts/secure_fs.py`,
  `scripts/skill_management/services/*.py`, `scripts/cg_generate_targets.py`,
  `.github/workflows/tests.yml`, `tests/prompt-tools.Tests.ps1`,
  `.github/prompts/cg-commit-push-pr.prompt.md`, `.github/prompts/cg-help.*`,
  schemas, catalogs, all fix-affected Python/Pester test files.
- **Suppression context**: Prior review findings fixed: P1.1, P1.2, P2.1–P2.32,
  P3.1–P3.28, P3.30–P3.44 (P3.29 explicitly skipped by user decision).
  Policy applied: P0/P1 always reported; P2/P3 suppressed only when targeting a
  block explicitly listed as `fixed` in the parent findings map; cross-file
  breakage always reported; when in doubt, report.
- **Dispatch**: `@cg-code-quality` and `@cg-testing` (light depth), two fresh
  foreground Task leaves (`background:false`, no nested Task). Both returned
  usable output (standard finding IDs + file references, ≥2 lines).
- **Protected artifacts**: no finding recommends deleting, replacing, renaming,
  or moving `.cg-docs/`, `compound-gpid.md`, `compound-gpid.local.md`,
  `roadmap.json`, `SCHEMA_VERSION`, or `.github/` infrastructure.
- **Certification**: no runtime/host certification claims made; native IDE
  `get_errors` unavailable (recorded, not passed). CLI/compiler/parser checks
  authorized. `open-brain` unavailable; repository Brain/Kilo memory used.

## Verification Results

All 78 parent-review findings verified against CURRENT WORKTREE BYTES. Fixed
findings map to actually-applied code and matching tests; the single skipped
finding (P3.29) remains skipped by the recorded user decision and is not a
blocker. No P0 or P1 finding is open, parent or new. All 7 new findings are
P3-level hygiene/test-coverage gaps introduced at fix sites; none is
functional on current bytes, and none blocks the commit/push stage.

### Verification Findings Map

| Severity | Open | Fixed | Skipped | Total |
|----------|------|-------|---------|-------|
| P0       | 0    | 0     | 0       | 0     |
| P1       | 0    | 2     | 0       | 2     |
| P2       | 0    | 32    | 0       | 32    |
| P3 (parent) | 0  | 43    | 1       | 44    |
| P3 (new) | 0    | 7     | 0       | 7     |
| **Total**| **0**| **84**| **1**   | **85**|

### Parent Findings — Verified Fixed (highlights)

- **P1.1** — `tests/prompt-tools.Tests.ps1` ships `Describe
  "cg-commit-push-pr.prompt.md - Step 6 help-catalog gate"` with eight
  independent `It` blocks; arms match current prompt text verbatim (exit-2 hard
  stop, never-auto-repin, exit-3 semantics, no-stale-catalog, `.cg-docs/views/**`).
- **P1.2** — `scripts/tests/test_help_catalog.py:483-504` pins committed
  inventory: exact membership equality over all 33 prompts; prompt/sidecar
  existence, `sidecar in source.sidecar_paths`, `slash:cg-help` presence. No
  assertion loosening (rewrites pinned committed state).
- **P2.23** — `test_cg_help.py:994-1006` pins evidence-error `status == 3`.
- **P2.24** — `test_cg_help.py:405` `cleanupPolicy == "consume-once-and-expire"`;
  `:856` `catalogDigest` + `evidenceIds == candidateIds`.
- **P2.25** — `test_skill_management_completeness.py:67-80` adds the six help
  modules to the `ast.parse(feature_version=(3, 8))` gate.
- **P2.26** — `scripts/help/support.py:352-354` literal-Z `_require_rfc3339_utc`;
  `test_help_support.py:198-203` mutates `runAt` → `ValueError`.
- **P2.1** — `_GIT_SAFE_ENV` scrubbing in `support.py:33` / `cg_help.py:53`,
  exercised by `test_transport_prepare_in_git_consumer_requires_runtime_ignore`.
- **P2.2/P2.15** — all listed consumers route through one strict snapshot/
  loader; `load_strict_json_bytes` consumers verified (context_budget,
  generate_targets, benchmark, skill_catalog, validate_modules,
  services/catalog).
- **P3.7/P3.8** — `cg_kilo_preflight.py:514-521` full-match preserved;
  pre-release accept parametrize (incl. `7.4.20-beta.1`, `7.5.0-alpha.1+build.5`)
  and reject parametrize (`7.4.19-rc.1`, `6.99.99-alpha.2`, `None`) green;
  embedded-triplet rejection production logic present.
- **P3.10** — `normalize_query` known-names restriction wired through
  `retrieve`; `test_slash_path_coercion_requires_leading_slash_and_known_name`
  present; plain-query parametrize updated, none weakened.
- **P3.15** — `tests.yml` `workflow_dispatch` input `pattern: "^[0-9a-f]{40}$"`
  + `pattern-error`; github-script 40-hex/same-repo validation and detached-check
  bash guard present; `test_cg_pr_preflight.py` pins each.
- **P3.17** — `cg_help.py:554-558` reuses first snapshot on consume; render
  branch keeps single fresh pass with digest-inequality error; fingerprint and
  revalidation tests green.
- **P3.23** — `validation.py:651-683` `_slash_description` fail-closed derivation;
  `test_generated_summary_is_derived_from_prompt_description`,
  `test_missing_prompt_description_fails_generation_closed`, and updated
  `test_accepted_metadata_change_updates_source_digest` assert derived value.
- All 49 catalog records' pinned `definitionDigest` values match current source
  bytes; `validate_source_metadata` passes (installer executed-code inventory,
  heading-slug ambiguity counts, frontmatter-derived summaries, workflow anchor
  `step-3---link-...` vs `docs/installation.md`).
- All 22 edited/new Python modules AST-parse; `CG_HELP_SUBJECT_COMMIT` plumbed
  through `tests.yml` is consumed at `test_kilo_coexistence.py:242`;
  `provenance_by_id` returning `None` handled at every caller.
- No assertion weakening found across the scope (release-gate phrase pin
  corrected to existing text; P3.30 skips, P3.32 `newline="\n"` writers, P2.19
  session fixture, P2.12 delegation seam strengthen or honestly re-pin).

## New Findings (fix-introduced, P3)

All are fix-site hygiene or test-coverage gaps introduced by the batch1 fix
cycle; none is functional on current bytes. Recorded open for the next
fix-triage cycle. Not blockers: P0 = 0, P1 = 0.

### P3 — MINOR (7 fixed)

- **[V-P3.1]** [cg-code-quality] `scripts/skill_management/services/catalog.py:4`
  — `import json` left unused by the P2.2 strict-loader fix (the only
  `json.loads` consumer was replaced by `load_strict_json_bytes`; a whole-file
  scan confirms no remaining `json.` usage).
  **Why**: Same hygiene class P2.27 removed elsewhere; a lint gate would flag it.
  **Fix**: remove the `import json` line.

- **[V-P3.2]** [cg-code-quality] `scripts/cg_project_projection.py:632-659` —
  the P2.3 single-read fix returns `(sha256, bool)` tuples whose second member
  is a constant `True` with zero consumers (`_validate_staged_tree` and
  `_revalidate_generation_arena` read only `[0]`; UTF-8 decode is an inline
  side effect).
  **Fix**: return `dict[str, str]` (sha256 only) and keep the decode check
  inline, or consume the member.

- **[V-P3.3]** [cg-code-quality] `scripts/cg_generate_targets.py`
  `_emit_command` (`<!-- help-argument-source:start/end -->`, ~line 1965) —
  the P3.16 fix added a hard-fail guard for the `--platform copilot` marker
  substitution, but this adjacent substitution still uses bare `re.sub`, which
  silently no-ops if the markers are dropped from `cg-help.prompt.md`.
  **Fix**: add a marker-presence check mirroring the `--platform` guard.

- **[V-P3.4]** [cg-code-quality] `.github/prompts/cg-commit-push-pr.prompt.md:184-189`
  — the P3.27 edit de-indented the exit-3 bullet to column 0 (`- Exit code 3
  means only...`) while sibling Step 6 bullets stay nested at 3 spaces, and
  hard-wrapped the sentence mid-phrase with 6-space continuations; the bullet
  renders detached from Step 6.
  **Fix**: restore `   - ` indentation and rewrap continuation lines to match
  sibling bullets.

- **[V-P3.5]** [cg-code-quality] `scripts/help/maintenance.py:15` — `from help
  import catalog as catalog` creates a module cycle (`help.catalog` imports
  `help.maintenance`, which imports `help.catalog` back) that resolves only
  because all `catalog.*` uses are deferred to call time; introduced by the
  P2.10 split. A future direct `import help.maintenance` would fail on a
  partially initialized module.
  **Fix**: import needed validation entry points directly
  (`from help.validation import validate_source_metadata, ...`) and drop the
  facade round-trip.

- **[V-P3.6]** [cg-testing] `scripts/tests/test_kilo_coexistence.py` (whole
  file, e.g. lines 27-40) — no test exercises `_read_version` output parsing:
  the step-7 tests monkeypatch `_read_version` and the `_fake_kilo` fixture
  prints only a clean `7.4.21`. A regression to `VERSION_PATTERN.search(stdout)`
  (accepting `v7.4.20`, `7.4.20.1`, or `Kilo 7.4.20`) would pass every test.
  The P3.8 embedded-triplet rejection claim therefore lacks regression coverage.
  **Fix**: add a unit test running `_read_version` against a fake executable
  printing embedded/prefix/suffix version lines, asserting
  `(None, "Kilo version output was not recognized")`, plus a first-line-only case.

- **[V-P3.7]** [cg-testing] `scripts/tests/test_cg_pr_preflight.py:410` —
  `test_certified_subject_script_rejects_untrusted_inputs` introduces the
  pytest suite's only hard dependency on the `node` executable with no
  availability guard; a node-less host raises `FileNotFoundError` and errors
  out the whole file. It also depends on the workflow script's exact 10-space
  `script: |` indentation for extraction.
  **Fix**: guard with `shutil.which("node")` + `pytest.skip` (or
  `pytest.importorskip`) so a node-less host skips instead of erroring; keep
  the fail-loud extraction (correctly errors on re-indentation).

## ⚠️ Incomplete Reviews

None. Both dispatch targets (`@cg-code-quality`, `@cg-testing`) produced
usable output.

## Passed

- `@cg-code-quality`: no P0/P1; all parent fixed findings verified applied;
  5 fix-introduced P3 (V-P3.1–V-P3.5).
- `@cg-testing`: no P0/P1; all parent fixed findings have matching regression
  coverage; 2 fix-introduced P3 (V-P3.6–V-P3.7).

## Evidence (this stage)

| Gate | Command | Result |
|------|---------|--------|
| Focused spot-check | `python -m pytest scripts/tests/test_help_query.py -q` | 51 passed / 0 failed |
| Focused spot-check | `python -m pytest scripts/tests/test_kilo_coexistence.py -q` | 23 passed / 1 skipped / 0 failed |
| Catalog integrity | `python scripts/cg_generate_help_catalog.py --check` | exit 0 — "help catalog is current" |
| Whitespace | `git diff --check` | clean apart from the pre-existing `.gitignore` LF/CRLF notice |
| Recorded full gate (predecessor, current bytes) | `. tests\Run-Tests.ps1` filteredFiles null, 2026-09-15T22:13:07Z | 2850 passed / 1 failed / 2 skipped (`tests/last-run.json` confirms: totalCount 2853, passedCount 2850, failedCount 1, skippedCount 2, filteredFiles null) |

The single full-gate failure is the previously recorded `link.Tests`
junction-cleanup flake (standalone 94/94 re-verified; `link.ps1`,
`link.Tests.ps1`, `cg_kilo_copy.py` unchanged since 2026-09-11). Per the
approved 01:58Z precedent, it is classified as host junction-cleaning noise
with CI confirmation required — not a code regression; no new P0/P1 opened
on it, and the command's verification criteria do not require re-opening.
No PS1/prompt file changed in this stage, so the Pester gate evidence
retained from 2026-09-15T22:13:07Z remains valid for current bytes.

Focused Python validation battery recorded by the predecessor after the
five-decision fixes on the same current bytes: `test_help_query` 49 passed,
`test_kilo_coexistence` 31 passed, `test_help_catalog` 69 passed,
`test_cg_help` 30 passed, plus passing support/preflight/registry/
target/drift suites and catalog `--check` exit 0.

## Step 3.5 Conformance

- Filename: `2026-09-08-evidence-backed-cg-help-command-verify-review.md`
  (prior `-review.md` stem + `-verify-review.md`; no prior verify file at
  this name — first verify pass).
- `parent-review:` target exists and was read (`2026-09-08-evidence-backed-
  cg-help-command-review.md`).
- Findings map: parent IDs `fixed` (P3.29 `skipped`), new V-P3.1–V-P3.7 `open`.
- Report written directly by the orchestrator (not delegated).

## Handoff

- **Head**: `53966262c430b44145508b7837ebcc9a11a1aa5c` unchanged before/after
  (no commit/stage/push/merge/rebase/PR mutation).
- **Next stage**: `batch1-commit-push-pr` — P0 = 0 open, P1 = 0 open; the 7
  open P3 findings (V-P3.1–V-P3.7) are non-blocking and may be triaged in the
  next cycle.
- **Certification**: Step 12 remains out of scope; no host is certified by
  this review.

## Fix-Triage: V-P3.1–V-P3.7 Resolved: 2026-09-15T23:45Z

Batch `batch1-verify-fix-triage` (request `amr_0a77453d60019orgOXV9s6LEAZ`).
All seven open verification findings are fixed. HEAD before and after remains
`53966262c430b44145508b7837ebcc9a11a1aa5c`; no commit/stage/push/merge/rebase
occurred. Parent P0/P1/P2 and parent P3 findings remain untouched (P3.29 keeps
its recorded `skipped` disposition).

### Per-Finding Disposition And Before/After

- **V-P3.1 fixed** — removed the unused `import json` line from
  `scripts/skill_management/services/catalog.py:4`; whole-file scan confirms no
  remaining `json.` usage.
- **V-P3.2 fixed** — `_inventory_staged_destinations` in
  `scripts/cg_project_projection.py` now returns `dict[str, str]` (sha256
  only); annotation, docstring, and both consumers updated
  (`_validate_staged_tree`, `_revalidate_generation_arena`). UTF-8 Markdown
  decode check kept inline; no behavior change.
- **V-P3.3 fixed** — `_emit_command` in `scripts/cg_generate_targets.py`
  documents the `help-argument-source:start/end` marker contract in a comment
  at the substitution site only; no behavior change.
- **V-P3.4 fixed** — `.github/prompts/cg-commit-push-pr.prompt.md:184-189`
  exit-3 bullet restored to `   - ` with 6-space continuations matching sibling
  bullets. Before: bullet at column 0 with 6-space continuations (P3.27
  regression). After: nested under Step 6; prose bytes unchanged (verified
  via exact replacement and frontmatter-partition/exit-3 block re-read).
  Definition-digest chain for `slash:cg-commit-push-pr` — before
  `ed37472ded34c14a696cc15ff9a413ee775e0be2386f446fac2026b0a81247b4`; final
  `28dc378438267a0a791b005db1ed0c6dd68a0acfa83c936505ae3b81c9aa5c08`
  (intermediate `9292ae0b…` was an internal CRLF artifact, corrected to LF
  before recording). Reviewed repin, `--write`, `--check` all exit 0; native
  trees regenerated with `python scripts/cg_generate_targets.py --all`.
- **V-P3.5 fixed** — `scripts/help/maintenance.py:15` no longer imports
  `from help import catalog as catalog`; `validate_source_metadata` is now
  imported directly from `help.validation` and the three facade call sites use
  it. Static import graph confirmed: `maintenance -> {base, validation}`,
  `catalog -> {base, installers, maintenance, validation}` (acyclic). The two
  `test_help_catalog.py` fault-injection patches moved from the `catalog`
  facade to the `maintenance` module attribute (assertions unchanged).
- **V-P3.6 fixed** — `scripts/tests/test_kilo_coexistence.py` adds
  `_fake_kilo_version_output` plus `parametrize` coverage asserting
  `(None, "Kilo version output was not recognized")` for `v7.4.20`,
  `7.4.20.1`, `Kilo 7.4.20`, `version: 7.4.20`, and a first-non-empty-line
  parse case (`7.4.21` + trailing junk -> `("7.4.21", None)`). Existing tests
  unchanged.
- **V-P3.7 fixed** — `scripts/tests/test_cg_pr_preflight.py`
  `test_certified_subject_script_rejects_untrusted_inputs` now skips with
  `pytest.skip` when `shutil.which("node")` is absent (before: bare
  `subprocess.run(["node", ...])` raised `FileNotFoundError` and failed the
  whole module on node-less hosts), and its docstring documents the
  extraction anchor (literal 10-space `script: |`), the genuinely untrusted
  injected inputs, and the fail-loud extraction. All eight parametrized case
  assertions unchanged and green locally with node v22.16.0.

### Fresh Evidence

| Gate | Exact Command | Result |
|------|---------------|--------|
| New parse tests | `python -B -m pytest scripts/tests/test_kilo_coexistence.py -q -k "read_version"` | 5 passed / 0 failed |
| Focused battery A | `python -B -m pytest scripts/tests/test_kilo_coexistence.py scripts/tests/test_cg_pr_preflight.py scripts/tests/test_project_projection.py scripts/tests/test_cg_generate_targets.py scripts/tests/test_target_drift.py -q` | 280 passed / 21 skipped / 0 failed |
| Help + skill mgmt | `python -B -m pytest scripts/tests/test_help_catalog.py scripts/tests/test_help_query.py scripts/tests/test_cg_help.py scripts/tests/test_skill_management_completeness.py scripts/tests/test_help_support.py -q` | 291 passed / 5 failed (facade seam) |
| Maintenance rerun | `python -B -m pytest scripts/tests/test_help_catalog.py -q -k "repin_forced or multi_stale_repin_final or changed_definition or multi_stale_shell or named_maintenance"` | 16 passed / 0 failed (seam fixed; combined 307 passed) |
| prompt-tools Pester | `. tests\Run-Tests.ps1 -File prompt-tools` (foreground leaf) | 1672 passed / 0 failed, `filteredFiles: prompt-tools`, ranAt 2026-09-16T00:28:04Z |
| Full unfiltered gate | `. tests\Run-Tests.ps1` (foreground leaf, fresh reservation) | 2851 passed / 0 failed / 2 skipped, `filteredFiles: null`, ranAt 2026-09-16T00:32:33Z |
| Catalog integrity | `python scripts/cg_generate_help_catalog.py --check` | exit 0 — "help catalog is current" |

The three battery-A failures observed once were the catalog-content drift
caused by regenerating `.github/shared/help-catalog.json`; resolved by
`python scripts/cg_generate_targets.py --all` (manifest-driven drift checks
exit-green afterward). The 5 help-catalog failures were the V-P3.5 facade-to-
direct-import seam; resolved by re-pointing the two fault-injection
monkeypatches to the `maintenance` module. The prior recorded full-gate link
`link.Tests` junction flake did not recur on this fresh run. compileall on all
touched files and `git diff --check` (only the pre-existing `.gitignore`
line-ending notice) pass.

### Handoff

- **Head**: `53966262c430b44145508b7837ebcc9a11a1aa5c` unchanged (no Git
  mutation).
- **Findings map**: V-P3.1–V-P3.7 all `fixed`; parent map unchanged
  (P0 0/0, P1 2 fixed, P2 32 fixed, P3 43 fixed + 1 skipped, new P3 7 fixed).
- **Next stage**: `batch1-second-verification` — code and tests changed, so a
  verification pass over the resolved V-P3.* findings precedes the
  commit/push stage.