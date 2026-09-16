---
date: 2026-09-13
depth: light
parent-review: .cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase6-review.md
type: verification
findings:
  P1.1: fixed
---

# Pipeline Step 8 Verification

**Status: Failure, changes required.** The requested verification ran to completion. One new P1 prevents review convergence. This is not a failed live rollout or a withdrawal of the approved deferral.

**Review mode:** `mode:verify`, resolved `light`.
**Coverage:** 2/2 required specs, applied sequentially in this session: `cg-code-quality`, then `cg-testing`. No separate reviewer or Agent Manager session was created.
**Files reviewed:** 56 current product, configuration, workflow and test paths, through full files or targeted excerpts. The inventory is below. Plan, historical reviews and evidence are additional context, not part of that count.
**New findings:** 1 (P0: 0, P1: 1, P2: 0, P3: 0).
**This pass:** Fixed 0; skipped 0; remaining 1; incomplete role outputs 0; suppressed candidate findings 0.

## New Finding

### P1 - Critical

**[P1.1]** [cg-testing, cg-code-quality] `packages/cg-release/tests/test_profile_workflow_authority.py:18`; `packages/cg-release/pyproject.toml:17-19`; `scripts/cg_pr_preflight.py:30-35,904-908` - The default locked package gate cannot collect the new authority tests in a clean environment.

**Issue:** The test module imports `yaml` unconditionally. The default `dev` dependency group does not include PyYAML; only the separate `gpid-native` group declares it. The full-package preflight command selects neither that group nor another YAML dependency. The native PR producer installs PyYAML into its outer interpreter at `.github/workflows/tests.yml:248-254`, then executes the isolated controller-package environment through preflight at lines 264-280. The outer installation cannot supply a dependency to that package environment.

**Executed proof:** The following offline command created an isolated locked environment from cached dependencies, without changing the repository's existing environment or source. It exited 2 during collection at line 18 with `ModuleNotFoundError: No module named 'yaml'`; no tests were collected.

```powershell
uv run --isolated --offline --project packages/cg-release --locked python -B -m pytest packages/cg-release/tests/test_profile_workflow_authority.py --collect-only -q --tb=short -p no:cacheprovider
```

The otherwise equivalent isolated collection with `--group gpid-native` collected all 18 cases. A fresh isolated execution with that group then passed all 18 in 2.57 seconds:

```powershell
uv run --isolated --offline --project packages/cg-release --locked --group gpid-native python -B -m pytest packages/cg-release/tests/test_profile_workflow_authority.py -q --tb=short -p no:cacheprovider --basetemp "C:\Users\wb384996\AppData\Local\Temp\3\kilo\s8y-1722-a81f"
```

**Impact:** A fresh checkout cannot complete the advertised default package suite or the ordinary native PR preflight on controller changes. `docs/release-controller.md:295` also advertises the default suite command. This is a current, locally reproduced integration defect, not a complaint that ordinary PR CI has not yet run. The separate six-cell package workflow explicitly installs `--group gpid-native` at `.github/workflows/release-controller-ci.yml:167`; that does not repair the other producer. The retained 994-test run used `--no-sync` in an already provisioned environment, so it does not refute this defect.

**Correction for step 9:** Make every supported full-package test entry point provision the required test dependency. Prefer a default test/development dependency declaration, or consistently select the existing group where that is the intended contract. Keep PyYAML out of generic core runtime dependencies. Update the lock and affected producer/documentation contracts as required. Add a clean locked-environment collection regression; do not skip the authority tests or rely on an existing developer environment. No correction was applied here.

**Escalation:** P1 is a must-fix-before-merge issue. P0/P1 and cross-file breakage cannot be suppressed in verification mode. This new test-to-environment/producer breakage is not a claim that the earlier native receipt validator repair failed.

Parsed 1 distinct new finding ID. Its status is `open`; the count matches the report total. IDs are local to this report.

## Additional Failures

The fresh native selection returned **86 passed, 2 failed** in 24.20 seconds. Both failures are `test_real_shell_preserves_argv_exit_and_does_not_recurse` in `scripts/tests/test_release_controller_launchers.py:26`, for `--legacy-bridge-bash` and `--legacy-recovery-bash`. Each expected exit 37 but received 127 with empty streams and no argv record. A separate run using the recorded package interpreter returned **19 passed, the same 2 failed** in 25.98 seconds.

The failures were investigated without product changes. The temporary probe is `C:/Users/wb384996/AppData/Local/Temp/3/kilo/s8_shell_probe_a81f.py`. Its final fixture root is `C:/Users/wb384996/AppData/Local/Temp/3/kilo/s8d-0bapp0mm`. The probe uses the real launchers and router copied by the existing fixture, plus fake executables. It does not invoke a real legacy publisher.

- The trace reaches the real Python router with the exact legacy arguments.
- Under the actual Bash environment, `shutil.which('pwsh')` resolves the fixture's copied `pwsh.EXE`.
- Direct execution of that copied mock, outside the product router, returns 3758096423 with empty streams, before the fixture dispatcher records argv.
- The original compiled `python.exe` mock returns the expected 37. Adding System32 or the full host PATH does not make the copied mock succeed. A same-assembly companion copy also does not change the result.

The failure is localized to the copied fixture executable on this host. Its underlying cause is not established. No product launcher defect, remote failure or permission bypass is claimed from it, and it is not assigned another source finding ID. **The two failed checks remain failed and unresolved**, not fixed, skipped, suppressed, or covered by the live deferral. Step 9 must assess this qualification before treating the current launcher check as green. Earlier passing launcher evidence remains historical evidence; this report does not rewrite it.

## Route And Scope

Original plan: `.cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`. The current plan records seven completed local phases and remains active. Decision `D-2026-09-13-defer-live-rollout` controls local acceptance; V8 remains pending the later authorized committed gate and ordinary PR CI.

The command was read first at `.kilo/commands/cg-review.md`. Project instructions, charter/configuration, context-loading, review-routing and model-advisory contracts, both reviewer specs, Python instructions/skill/anti-patterns, and PowerShell/CMD guidance were applied. The canonical release-controller integration contract was also read. No Pester command was executed.

The review directory metadata scan selected the existing **Phase 6 standard review** as the parent: it is the latest eligible `-review.md` with fixed entries, using date then filename precedence. The newer Phase 7 standard review has only historical open entries and is ineligible. Its separate verification report confirms closure and was used as supporting evidence, not substituted as the suppression anchor. No parent status was edited. The output filename follows the command's parent-derived naming rule; it does not limit this review to Phase 6.

Both spec passes used the same suppression context: the parent's 34 explicitly fixed entries, with their original descriptions and repair dispositions. P0/P1 and cross-file defects always remain reportable. P2/P3 suppression applies only to the explicitly fixed function/block scope, not all recent work. No cosmetic refactoring of repaired blocks was proposed. Release, permission, publishing, linking and schema risks were recognized, but the verify guard correctly prevented a full-route escalation or additional agent dispatch.

The scope includes untracked package, tests, workflows, launchers and profile product. It is not just the final repair diff. Unrelated pre-existing work, virtual environments, caches and build outputs were excluded as review source. No `.cg-docs/views/**` body or HTML diff was read. Protected infrastructure, knowledge, charter, configuration, roadmap and schema artifacts were preserved.

## Repair History

Historical closure counts are scoped to each phase, not globally unique finding IDs. The total is **71 prior confirmed closures**, preserved with their original evidence limits. This does not claim 71 new independent reproductions in this pass, nor that all current checks pass after the new finding above.

| Phase | Prior Closures | Closure Evidence And Current Coverage |
|---|---:|---|
| 1 | 4 | Original review and repair verification: authorization-key rejection, empty CLI options, preflight provisioning and observed process counts. Current `process.py`/`cli.py` and focused process/contract/CLI tests retain these mechanisms. The newly required YAML test dependency is a later cross-file issue. |
| 2 | 8 | Final `phase2-verify-review-2.md` plus prior closure details: numeric-token preservation, real role envelopes, strict manifest producer/reader agreement, GraphQL routing, notes baseline, confirmation time and bounded capture. Current JSON edit, manifest, source and process boundaries were inspected; repair/manifest/CLI tests passed. |
| 3 | 6 | `phase3-verify-review.md`: current resumer authority, queue fairness, idle-scan/journal retention, real wire integration, human status and missing-time handling. Current queue/journal and transport-level worker tests were checked; focused tests passed. |
| 4 | 3 | `phase4-verify-review.md`: preparation-versus-release checks, atomic build ticket/registration restart, pre-parser ZIP bounds. Current check routing, build stage and archive code were inspected; restart, stage and archive tests passed. |
| 5 | 6 | Original review and final `phase5-verify-review-2.md`: bounded publication envelopes, absent-artifact rebuild, reviewed authority replacement and override reason, job-local archive reuse and error context. Current publication capacity/inputs/effects were inspected; full-path review-repair tests passed. |
| 6 | 42 | Original standard review, first verification, full repair-2 verification and final continuation verification were reconciled. The final report preserves 41 earlier confirmations and closes the finite 15-row continuation audit. Current hook/deployment/dispatch/evidence, snapshot capacity, native receipt, journal replay, workflow and launcher boundaries were checked. Focused authority tests passed, but the new clean-test dependency defect and two fresh fixture failures remain as recorded above. The absorbed draft finding is not counted. |
| 7 | 2 | `2026-09-13-generic-asynchronous-release-controller-phase7-verify-review.md`: finite overflow-safe median and bounded exclusive-output errors. Current five reviewed product blobs match that report; performance/sandbox/documentation tests passed. |

All review names in the table refer to `.cg-docs/reviews/` and the `generic-asynchronous-release-controller` plan family. The final Phase 6 source is `.cg-docs/reviews/2026-09-13-generic-asynchronous-release-controller-phase6-P1.15-continuations-verification.md`. Earlier open maps and blocked reports are retained history, not proof that their later closures or the approved deferral do not exist.

The finite authority audit does not promise atomic permission checks across GitHub calls or prevent changes during an already-started operation. The cold-journal repair still has cumulative flat-directory hashing; no total linear-time or live deadline guarantee is inferred. These original qualifications remain intact.

## Spec Results

### cg-code-quality

Checked current error boundaries, strict input handling, explicit interfaces, immutable state and cross-file producer configuration. Identified the dependency declaration/consumer mismatch consolidated into the new finding. No additional actionable style or refactoring finding was found in the inspected product scope.

Ruff passed for the entire package and benchmark without fixes or cache writes. Structured stdout is a documented protocol, not debug logging. No R package or changed R/Stata code was identified in the scoped implementation, so those language/build checks do not apply.

### cg-testing

Checked repair tests, outer-I/O transport fixtures, negative authorization cases, restart faults, producer selection and exact byte assertions. Independently reproduced the missing clean-environment dependency, with an explicit-group positive control. The 281-test cross-phase selection passed; the native launcher failures are retained separately above.

No test total is treated as proof of live publication, actual approval enforcement, native Unix qualification or complete source review. The callback-wiring test alone is not authority proof; the connected real-authority workflow tests and retained finite continuation probes provide that scoped evidence.

Both role outputs are usable, file-specific and complete for the required light route. No automatic reviewer retry or model switch occurred.

## Executed Checks

| Fresh Check | Result | Qualification |
|---|---|---|
| Cross-phase package selection, 19 test modules | 281 passed; 149.31 seconds; exit 0 | Existing provisioned package environment, `--no-sync`; not clean dependency provisioning or a full gate. |
| Native launchers, producer contracts and preflight tests | 86 passed, 2 failed; 24.20 seconds; exit 1 | Both failures are the Bash legacy mock-executable cases described above. |
| Launcher-only comparison with package interpreter | 19 passed, 2 failed; 25.98 seconds; exit 1 | Same failures; not additional unique coverage. |
| Clean default locked collection | 1 collection error; exit 2 | Reproduces the new finding; no tests collected. |
| Clean explicit-group collection/execution | 18 collected, then 18 passed; 2.57 seconds; exit 0 | Positive dependency control only; no source fix. |
| Node release-version, snapshots, legacy Pages and payload-loader tests | 55 passed; 0 failed/skipped/cancelled; 17.77 seconds; exit 0 | Local Node fixtures, not deployed Pages evidence. |
| Ruff, disabled installation, docs freshness and docs site | Passed | No regeneration or activation; 76 pages and 8 navigation groups. |
| Historical payload/attestation diff | Empty; exit 0 | Tracked local history only, not a remote Release audit. |
| Tracked whitespace | Passed with LF/CRLF advisories | Does not inspect untracked bytes. |

Exact cross-phase command:

```powershell
uv run --offline --project packages/cg-release --locked --no-sync python -B -m pytest packages/cg-release/tests/test_process.py packages/cg-release/tests/test_contracts.py packages/cg-release/tests/test_cli.py packages/cg-release/tests/test_manifest.py packages/cg-release/tests/test_phase2_repairs.py packages/cg-release/tests/test_worker_e2e.py packages/cg-release/tests/test_phase3_review_repairs.py packages/cg-release/tests/test_check_stages.py packages/cg-release/tests/test_phase4_restarts.py packages/cg-release/tests/test_artifacts.py packages/cg-release/tests/test_phase5_review_repairs.py packages/cg-release/tests/test_hook_continuation_wiring.py packages/cg-release/tests/test_hook_authority_boundary.py packages/cg-release/tests/test_journal_cold_work.py packages/cg-release/tests/test_profile_workflow_authority.py packages/cg-release/tests/test_profile_evidence_edits.py packages/cg-release/tests/test_performance.py packages/cg-release/tests/test_sandbox.py packages/cg-release/tests/test_documentation.py -q --tb=short -p no:cacheprovider --basetemp "C:\Users\wb384996\AppData\Local\Temp\3\kilo\s8v-1722-a81f"
```

Other exact test commands:

```powershell
python -B -m pytest scripts/tests/test_release_controller_launchers.py scripts/tests/test_release_producer_contracts.py scripts/tests/test_cg_pr_preflight.py -q --tb=short -p no:cacheprovider --basetemp "C:\Users\wb384996\AppData\Local\Temp\3\kilo\s8n-1722-a81f"
uv run --offline --project packages/cg-release --locked --no-sync python -B -m pytest scripts/tests/test_release_controller_launchers.py -q --tb=short -p no:cacheprovider --basetemp "C:\Users\wb384996\AppData\Local\Temp\3\kilo\s8l-1722-a81f"
node --test --test-reporter=spec scripts/tests/release-version.test.js scripts/tests/docs-snapshots.test.js scripts/tests/legacy-pages.test.js scripts/tests/generate-whats-new.test.js
```

Other checks were `uv run --offline --project packages/cg-release --locked --no-sync ruff check --no-cache packages/cg-release scripts/benchmark_release.py`, the existing package interpreter with `-I -B scripts/release_profile_install.py --check`, `node scripts/rebuild-docs.js --all --check`, `node scripts/check-docs-site.js`, and `git diff --exit-code -- releases .github/shared/skill-management/release-attestations`.

All temporary test roots were new paths below the verified approved Kilo temporary parent. The copied mock failures were investigated only with local fixture executables. No old roots were deleted. The isolated uv probes used the offline cache; no dependency was added to product declarations and no existing package environment was synchronized. No new Pester/full-package/prepare/committed gate was run. Counts overlap and must not be added as unique coverage.

Report read-back confirmed the frontmatter, existing parent target and one open finding. An additional `cg-render-artifact --validate-only` attempt rejected the report because that tool supports only canonical brainstorms and plans, not reviews. No report-validator pass is claimed, and the report was not moved or rendered to bypass that restriction.

## Retained Evidence

Current summary: `.cg-docs/work-reports/release-controller/2026-09-13-phase7-final-evidence.json` at 17:16:58Z. The final package `result.json`, `execution.json`, integrity record and complete 15-line stdout were read. The captured Pester artifact was also read. The final package stdout confirms **994 passed in 1315.28 seconds**; the JUnit and summary record 0 failures/errors/skips. Pester records **2935 passed, 0 failed, 2 skipped**, 21 files, `filteredFiles: null`, at 16:31:31Z.

Fresh `certutil` SHA-256 checks match the retained integrity record:

| Artifact under `2026-09-13-phase7-pkg-165245Z-52219816/` | SHA-256 |
|---|---|
| `result.json` | `e472c55968f540a5bf4c3420c46137bcaa7efe8cdc1f997e0359311f84689f4d` |
| `full-package.xml` | `98aae3f65205beebf52282e55e01a78a2e090999ee052e02ae0bc113d9bdb7d6` |

Fresh before/after Git blob checks match the Phase 7 independent review for `trials.py`, `benchmark_release.py`, `test_performance.py`, `test_sandbox.py` and `docs/release-controller.md`. The full 2743-product-file identity comparison is retained executor evidence, not independently repeated here. HEAD remains `b94f585c8a485dfb03965ca9711fb83257aaa7de`; this is still a dirty candidate, not an exact committed input.

The short temporary-root GPG correction remains an environment correction with no source or assertion change. The historical 993-pass/1-failure package run is not rewritten. The passing replacement and its seven unchanged companion gates remain valid for their recorded environment; the new clean-environment defect narrows what can be inferred from them.

Pester's cleanup diagnostics, unknown individual identities/reasons for two update skips, Windows Bash placeholder, adapter-only Kilo containment and prior Node/Unix platform qualifications remain. Zero failed Pester assertions does not prove successful cleanup. Raw `*.log` files remain subject to the existing ignore rule and need deliberate preservation/review at later evidence staging. No raw prior log, XML, review or JSON evidence was replaced.

## Current File Inventory

Paths in each row share the displayed directory. Comma-separated names denote distinct files. This is the 56-path direct inspection inventory, not a claim to have read every package or generated file.

| Directory | Count | Files |
|---|---:|---|
| `packages/cg-release/src/cg_release/` | 21 | `cli.py`, `process.py`, `build_stage.py`, `github_checks.py`, `queue.py`, `journal.py`, `json_edit.py`, `manifest.py`, `publication_inputs.py`, `publication_capacity.py`, `hook_authority.py`, `profile_deploy.py`, `profile_dispatch.py`, `trials.py`, `source.py`, `artifacts.py`, `publisher.py`, `profile_native.py`, `profile_selection.py`, `profile_evidence.py`, `github_journal.py` |
| `scripts/` | 4 | `benchmark_release.py`, `release-payloads.js`, `cg_pr_preflight.py`, `cg_release_cli.py` |
| `bin/` | 2 | `cg-release`, `cg-release.cmd` |
| Configuration | 2 | `packages/cg-release/pyproject.toml`, `.release-controller.json` |
| `docs/` | 1 | `release-controller.md` |
| `.github/workflows/` | 9 | `release-controller.yml`, `release-controller-build.yml`, `release-controller-ci.yml`, `release-controller-docs.yml`, `release-controller-publish.yml`, `release-controller-bridge.yml`, `pages.yml`, `release-docs.yml`, `tests.yml` |
| `packages/cg-release/tests/` | 13 | `conftest.py`, `test_phase2_repairs.py`, `test_worker_e2e.py`, `test_phase4_restarts.py`, `test_phase5_review_repairs.py`, `test_profile_workflow_authority.py`, `test_hook_continuation_wiring.py`, `test_performance.py`, `test_profile_evidence_lifecycle.py`, `test_profile_evidence_edits.py`, `test_hook_authority_boundary.py`, `test_journal_cold_work.py`, `test_install.py` |
| `scripts/tests/` | 3 | `test_release_producer_contracts.py`, `test_release_controller_launchers.py`, `release_shell_fixture.py` |
| `.github/shared/` | 1 | `release-controller.contract.md` |

## Brain And Handoff

The bounded `cg-index query --intent review --query "release controller publishing tag recovery test evidence verification" --budget 800 --format md` selected the original plan and `.cg-docs/solutions/testing-patterns/2026-08-13-release-gate-fixtures-and-derived-evidence-hashes.md`. The runtime-boundary lesson informed the fresh dependency and shell probes. The query reported index warnings; it is not execution evidence. `open-brain` was unavailable, so the local Brain query and targeted saved project context were used. No memory write was requested or performed.

**Next pipeline action: step 9 `/cg-fix-triage`, targeting this exact report and its open finding.** Also carry the two unresolved local fixture failures into that assessment. Step 9 was not executed, and this report is not permission to skip it or advance to commit/PR operations.

Review-stage model advice: strong independent dependency/producer and regression reasoning, with high effort. An economical code-capable option can assist with the bounded dependency correction once the boundary is understood. These are suggestions only; availability differs by platform and date, and the user chooses the model and effort. No model or effort was changed.

The publisher remains disabled. Bridge delivery, native clean-client qualification, registered release-mode live CI, sandbox/security/approval trials, remote identity proof and live performance remain **deferred, not passed**. Ordinary PR CI and the later authorized committed gate remain **required and pending under V8**. The approved absence of live proof is not a finding. No phase, plan, counter or active-state field was changed. This report is the only manual repository write; no source fix, regeneration, commit, remote operation or new Agent Manager session occurred.
