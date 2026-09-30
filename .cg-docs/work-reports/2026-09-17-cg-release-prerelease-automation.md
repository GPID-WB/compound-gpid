# Work Report: Prerelease Automation

## Plan Reference

`.cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md`

## Active Deviation Policy

`ask`; no runtime override. Latest execution scope: Phase 3 only, under the user's
explicit source-policy clarification and authorized review repairs. Earlier Phase
1/2 run sections remain historical evidence.

## Run: 2026-09-17

- Plan validation passed: `python scripts/render_artifact.py --validate-only .cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md`.
- The roadmap-manager specification was loaded and applied in this thread. Only the matched feature status changed from planned to active. Its milestone remains in-progress.
- Preexisting changes: modified `roadmap.json`; untracked plan and brainstorm for this feature. Preserve these changes.
- Brain consultation: `cg-index query --intent work --query "release preflight receipt clean clone line endings Pester" --budget 800 --format md` succeeded. Apply the authoritative command-list and committed-versus-prepare distinctions from `.cg-docs/solutions/git-workflows/2026-08-21-pr-ci-preflight-native-target-kilo-capability-gates.md`.
- Open-brain tools are unavailable in this session. Saved project memory and the local Brain query were inspected instead.

## Completed Steps/Phases

Phases 1, 2 and local Phase 3 completed on 2026-09-17. The final closure below
records Phase 3's clarified V6 gate. Phases 4 and 5 are not started; required V13
remote activation and verification remain pending.
Earlier pending statements below are historical checkpoints; final evidence governs.

### Red Baseline (Parent Evidence)

- Python: `python -m pytest scripts/tests/test_cg_pr_preflight.py -q --tb=short`: 78 total, 66 passed, 12 failed in 1.64 seconds. All new receipt cases failed on unsupported `--emit-receipt` (argparse exit 2). No unrelated failures.
- Pester: `tests/Run-Tests.ps1 -File create-release.Tests.ps1` rejected the filename. The runner registry uses the filter `create-release`; the dedicated runner recovered with `. tests\Run-Tests.ps1 -File create-release`.
- Pester artifact: gitSha `8bc05e51`, ranAt `2026-09-17T00:07:29Z`, passed false; 123 total, 120 passed, 3 failed, 0 skipped; filteredFiles `create-release`. All three new receipt cases failed because `PreflightReceipt` was absent. No unrelated failures.
- Red phase confirmed for both Phase 1 steps. No production code was changed before this baseline.

### Implementation

- Python emits compact, sorted-key UTF-8 JSON plus a SHA-256 digest through a flushed temporary file and atomic replacement. Only a complete successful committed full gate in a clean LF checkout can emit evidence; commit/tree/config and cleanliness are checked before and after execution.
- Receipt output stays outside the checkout. A new gate invalidates the previous receipt at the supplied external path before execution. Failed and interrupted gates do not leave stale success evidence.
- Added a read-only `--verify-receipt` interface in the same preflight module. It owns canonical JSON and the authoritative command list so PowerShell does not duplicate either. It rejects malformed/oversized/duplicate-key JSON, invalid schema, changed identity, non-LF provenance, nonzero or non-integer exit codes, incomplete command lists, invalid timestamps, and digest mismatch.
- Both release phases call the verifier after the existing clean-checkout, tag, lineage and payload guards. Missing or invalid receipts retain the isolated full-gate path. The digest is a local corruption check, not a signature or remote authorization.
- Expanded Python negative cases and offline Pester coverage. Pester uses the real Python verifier against local fixture receipts; native full-gate and HTTP calls remain mocked.

### Focused Green Evidence (Parent Evidence)

- Python: `python -m pytest scripts/tests/test_cg_pr_preflight.py scripts/tests/test_release_policy.py scripts/tests/test_release_gate_targets.py -q --tb=short`: 130 passed, 0 failed, 3 skipped in 64.51 seconds. The execution tool reported success; a separate numeric exit code was not supplied.
- Pester: `. tests\Run-Tests.ps1 -File create-release`: 135 passed, 0 failed, 0 skipped. Artifact gitSha `8bc05e51`, ranAt `2026-09-17T00:16:35Z`, passed true, failFast false, filteredFiles `create-release`, failures empty. The execution tool reported success; a separate numeric exit code was not supplied.
- This is targeted evidence, not the unfiltered Phase 1 boundary gate.
- `git diff --check` passed in the implementation thread.
- Review routing resolved to full: release automation and a receipt schema are security-risk triggers. All ten route agents are required; their findings remain pending.

## Deviations

- Approved runner substitution, 2026-09-17: the user explicitly approved a dedicated `task` subagent in place of unavailable `execution_subagent`. The primary thread will dispatch it. This implementation thread sends RUNNER_REQUEST with exact commands and consumes returned evidence. Pester safety must be loaded; use only `tests/Run-Tests.ps1`, without pipelines; read `tests/last-run.json`; return bounded summaries. No elevation or system installation is permitted.
- The plan lists receipt verification as step 2 inside Phase 1 but labels V2 as Phase 2. Follow the actual Phase 1 step membership and require V2 evidence before Phase 1 completion. The plan body is unchanged.
- The user approved a disposable snapshot commit in an isolated temporary clone on 2026-09-17. No shared-worktree commit, shared-ref change, push or PR is authorized.
- The user clarified that normal project-local uv environment/dependency synchronization is permitted without elevation. System installation and global configuration changes remain prohibited.

## Review Repair Round 1

- Parent-supplied full Pester evidence before repairs: `. tests\Run-Tests.ps1` passed; gitSha `8bc05e51`, ranAt `2026-09-17T01:21:51Z`, total 3030, passed 3028, failed 0, skipped 2 (both update), filteredFiles null, failures empty, no skipped files. Console reported temporary-directory cleanup errors; these were not recorded as test failures. Preserve this qualification.
- Full review completed all 10 required specifications. Three manual findings remain open for verification: P1.1 physical LF evidence, P2.1 interpreter-path coupling, P2.2 concurrent receipt writers. Report: `.cg-docs/reviews/2026-09-16-cg-release-prerelease-automation-phase1-review.md`.
- User authorized in-scope repairs. P1.1 now uses a producer-owned fresh LF clone at the exact commit, preserving committed CRLF attributes for CMD. P2.1 uses exact logical commands with one consistent absolute recorded Python path, never executed during verification. P2.2 uses exclusive destination ownership from before invalidation through publication.
- Added real Git tests for normalized CRLF, assume-unchanged and skip-worktree source edits; interpreter-path and argument substitution tests; deterministic overlapping-run and later-failed-run coverage; and a PowerShell differing-interpreter receipt case.
- A caught failure or interrupt releases the lock. An uncatchable process termination leaves `<receipt>.lock`; use a fresh receipt path, or remove the stale lock only after confirming no owner is running. No automatic stale-lock recovery is implemented.
- Pre-repair focused and full-suite evidence is retained as historical evidence, not proof of the repaired files. Post-repair runner and delta-review results are pending.

## Repair Round 1 Results And Fixture Correction

- Parent-supplied Python result: 138 passed, 1 failed, 3 skipped in 74.52 seconds. `test_receipt_gate_owns_fresh_checkout_with_actual_lf_bytes[normalized-crlf]` failed at fixture setup because Git reported `M code.py`, before production receipt execution. The fixture now uses `git add code.py` to refresh the normalized index/stat entry, explicitly asserts the index blob still equals HEAD, and separately asserts physical CRLF remains. This preserves the intended clean-status/CRLF mismatch rather than weakening its assertion.
- Parent-supplied Pester: create-release 136 passed, 0 failed, 0 skipped; gitSha `8bc05e51`, ranAt `2026-09-17T01:30:56Z`, filteredFiles `create-release`. No cleanup errors. Quiet deprecation and undeclared-file warnings were reported.
- Independent static delta review confirms all three repairs, with no new P0/P1 or cross-file findings. Runtime verification remains pending. Reviewer noted missing clone/config/checkout failure injection; four focused failure-path cases now assert no gate execution, no stale receipt, lock release and temporary-clone cleanup.
- This is a test-fixture correction and added coverage only; production code is unchanged from repair round 1. Required rerun evidence remains pending.

## Command-Local Git Settings Adjustment

- Parent-supplied focused Python result after the fixture correction: 143 passed, 0 failed, 3 skipped in 78.24 seconds.
- Parent-supplied unfiltered Pester result: gitSha `8bc05e51`, ranAt `2026-09-17T01:39:18Z`, passed true, total 3031, passed 3029, failed 0, skipped 2 (update), filteredFiles null, failures empty; create-release contributed 136 passes. Pester 4.10.1 emitted TestDrive cleanup errors for missing paths and nonempty directories under a temporary fresh-manifest-kilo-project skill tree. These console errors are retained as a qualification; no test failures were recorded.
- Reviewer confirmed the corrected fixture and four preparation-failure cases; all three findings are fixed subject to real acceptance evidence.
- Acceptance stopped before cloning because the producer's clone-local `git config` writes were not permitted. Replaced these writes with `git -c core.autocrlf=false -c core.eol=lf` for clone, checkout, and read-only provenance/identity queries. Receipt provenance records these effective command-local checkout settings. Fresh producer ownership and intentional `.gitattributes` CMD CRLF behavior remain unchanged.
- Real Git tests now use command-local settings and assert the producer did not persist either setting in its clone config. The two configuration-write failure cases now inject failures in read-only provenance queries; clone and checkout failure cases remain.
- Disposable temporary snapshot commits and normal project-local uv environment/dependency synchronization remain explicitly approved. No global/shared configuration changes, system installations, elevation, shared-worktree commits, pushes or PRs are authorized.
- This production adjustment requires new focused evidence, delta review and final acceptance; earlier passing results remain historical.

## Accepted Exceptions

None. The runner substitution does not waive test evidence.

## Evidence Table

| ID | Status | Evidence |
| --- | --- | --- |
| V1 | passed | Final focused tests and real 9-command committed gate with canonical receipt; identities recorded below |
| V2 | passed | 136 create-release cases; real emitted receipt accepted by the isolated PowerShell receipt block without a rerun |
| V3-V10 | not started | Later phases; outside this run |
| V11-V12 | not started | Whole-plan final gates; outside this run |
| Phase 1 boundary | passed | 3029 Pester passes, no failures, 2 update skips; full review 10/10, all 3 findings fixed |

## Constraints Check

| Constraints | Status |
| --- | --- |
| C1-C7 | Regression tests passed; no live publication, tag mutation, credential operation, or prompt change |
| C8 | Approved dedicated-task runner required; no Pester run in implementation thread |
| C9 | No PR; dev-only user restriction overrides any later main-PR instruction |
| C10-C11 | No controller enablement or historical attestation changes |
| C12 | Passed: acceptance receipt outside snapshot, clean before/after, no remaining receipt lock |

## Final Evidence: 2026-09-17

- Parent-supplied focused tests: 143 passed, 0 failed, 3 skipped in 78.47 seconds.
- Parent-supplied unfiltered Pester artifact: gitSha `8bc05e51`, ranAt `2026-09-17T01:48:32Z`, total 3031, passed 3029, failed 0, skipped 2 (update), filteredFiles null, failures empty. The create-release suite has 136 passing cases. TestDrive cleanup diagnostics for missing/nonempty temporary directories remain a qualification, not a recorded assertion failure.
- Full route reviewed all 10 specifications. Reviewer confirmed P1.1, P2.1, P2.2 fixed and the final command-local configuration adjustment clean. No open findings or new issues remain.
- Real acceptance: one complete committed native gate, 9 commands, all exit 0, 2065.99 seconds. Receipt verifier exit 0 in 0.157 seconds. Isolated PowerShell acceptance exit 0 in 0.375 seconds, `receiptAccepted=True`, with the accepted/skipping-re-run message. No live Reserve or Finalize was invoked.
- The acceptance harness initially had AST-selection and PSScriptRoot scope errors. These were corrected before successful execution of snapshot `create-release.ps1` lines 354-372 with fixture variables in scope. No product failure occurred.
- Source HEAD: `8bc05e515de45aa5c2b66a4c84107edce0c6a0ea`.
- Approved disposable snapshot commit: `9eaf1b6ab270ea5fa00f13fde6d7131162ea8bb7`; tree: `5db91e396a6ea3009b59212ecd38f4ce640f4731`. Snapshot clean before and after the gate.
- Snapshot: `C:\Users\wb384996\AppData\Local\Temp\3\kilo\phase1-c9c68270a1a14daea12b5d887c927a2b`.
- External receipt: `C:\Users\wb384996\AppData\Local\Temp\3\kilo\phase1-c9c68270a1a14daea12b5d887c927a2b.receipt.json`.
- Receipt schema 1; timestamp `2026-09-17T02:25:00.507121+00:00`; digest `9e8a1cb0f6af5f11540b4ee1435ff077c5d034ab61016350eba386db4bdac86a`; 9 integer zero exit codes; exact snapshot commit/tree; canonical validation passed; receipt lock absent.
- Snapshot patch SHA-256: `54d9b55007c2fb1ab6e647339d2c5c543410bf323d8a9409d18cb0138a421731`.
- Source and snapshot file hashes matched. Rechecked the four source hashes in the implementation thread before completion; all matched the parent acceptance evidence.
- Completion metadata validation passed: plan renderer `--validate-only`, `python -m json.tool` for both current and Phase 1 active-state records, and `git diff --check`. Completion was written crash-safely: append `completed-phases: [1]`, re-read and confirm, then set `current-phase: 2`; plan status remains active.

| File | SHA-256 |
| --- | --- |
| `scripts/cg_pr_preflight.py` | `3e0801a2ba8659960b01b4627f4ccff293e060efafcb2fdbcedbe5f98822097c` |
| `scripts/tests/test_cg_pr_preflight.py` | `95ab7b5bb776505ad3845314354eb922f09c75596fdcc123979bebd7f82f0e55` |
| `create-release.ps1` | `12cf14ad25e32b93fd63cafd622af8c10cef51e55c9459b63e9b1fdf1ee91f4b` |
| `tests/create-release.Tests.ps1` | `e3ff22b18950625131b22434efb5f5dc1d6f4dfb3bdb6d50ef2b347bc03841b4` |

## Remaining Uncertainty

- No unresolved Phase 1 gate. The final gate exercised the changed code in an approved disposable snapshot, not the unchanged source HEAD.
- No live publication was attempted. Later-phase documentation, automation, settings and timing outcomes remain outside this run.
- Pester cleanup diagnostics and reported skips are preserved above. No claim is made that cleanup was error-free.
- Editor `get_errors` is unavailable in this tool surface. Executed Python/Pester/full-native gates and independent review provide the recorded verification; no editor diagnostic result is claimed.

## Final Status

Completed: Phase 1 only. Plan remains active; completed-phases is [1]. Next phase
is 2, not started. Roadmap feature remains active. No shared-worktree commit,
push, PR, main-branch action, or subsequent pipeline command was performed.

Next authorized phase command, for the parent to schedule separately:
`/cg-work phase2 review:auto .cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md`.
Use dedicated task runners, command-local Git settings, and dev-only integration.

## Phase 2 Resume: 2026-09-17

- Scope: Phase 2 only, steps 3-5. Active deviation policy remains `ask`. Phase 1 completion and evidence above remain unchanged.
- Plan validation passed again with `python scripts/render_artifact.py --validate-only .cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md` before mutation.
- Approved deviation carried forward: the parent dispatches a dedicated task runner instead of unavailable `execution_subagent`. This thread has neither tool and sends RUNNER_REQUEST. No evidence waiver, elevation, global setup, snapshot commit, shared commit, push or PR is authorized in this phase. Project-local dependency setup remains allowed. Integration targets dev only.
- Open-brain tools remain unavailable. Budgeted local Brain query for release draft race, rulesets and docs lineage returned older release plans, but no applicable hardening lesson. Current approved plan and current source take precedence.
- Test index: `tests/create-release.Tests.ps1` covers all three steps; `scripts/tests/test_release_policy.py` covers prerelease lineage; `scripts/tests/test_release_gate_targets.py` provides workflow regression coverage.
- Added red-baseline tests for bounded reconciliation, exact-ref stable docs checks, stale controller, missing main ancestry, unreadable workflow, changed producer paths/metadata, and prerelease isolation. Added no-fallback and classic-endpoint audit guards. Existing behavior tests and Phase 1 tests are preserved.
- No production implementation changed yet. The mandatory red baseline needs parent runner evidence before implementation starts. The runner filter is `create-release`, not the filename `create-release.Tests.ps1` (confirmed during Phase 1).
- Initial audit: `release-legacy-authority.ps1` uses `Get-CgRepositoryRuleset`; its classic endpoint text is a documented banned comment. No endpoint call was found in the workflow family. Executed test evidence is still required; V3-V5 and Phase 2 completion remain pending.

### Phase 2 Runner Handoff: Red Baseline

Run `. tests\Run-Tests.ps1 -File create-release` from the shared worktree, without extra flags or a pipeline. Read `tests/last-run.json`; return identity, counts, filteredFiles, failures and any cleanup diagnostics. Do not change code or run a release. Resume this implementation thread with that evidence. Do not advance to Phase 3.

### Phase 2 Red Baseline: Parent Evidence

- Command: `. tests\Run-Tests.ps1 -File create-release`.
- Artifact: gitSha `8bc05e51`, ranAt `2026-09-17T02:37:07Z`, passed false, total 151, passed 140, failed 11, skipped 0, filteredFiles `create-release`.
- Red phase confirmed: the stable docs lineage call was absent; stale controller, missing main ancestry, unreadable workflow and three producer-drift cases did not halt. Reservation presence/absence races threw immediately; bounded retry and sleep counts were 1 instead of 3 and 0 instead of 2. No unrelated failure was reported.
- No cleanup errors. Quiet deprecation and undeclared-file warnings remain recorded. No production code changed before this baseline.

### Phase 2 Implementation Ready: 2026-09-17

- Step 3: `Get-CgReleaseReservation` now has bounded `RaceAttempts` (default/max 5) and `RaceDelaySeconds` (default/max 15; tests use 0). Every attempt reads the by-tag lookup and complete paginated list. Present, absent, ID and publication-field disagreement can settle; a consistent pair still passes the existing strict metadata assertions. Invalid responses and API errors fail closed. Sleep occurs only between attempts, at most four times (60 seconds total configured sleep, excluding API latency). The loop has no remote writes. Exhaustion preserves conflict diagnostics and supplies the read-only `/cg-release --resume` route.
- Step 4: added script/prompt no-fallback guards and a nonempty workflow-family classic-endpoint scan. The single existing Release POST remains after exact remote-tag read-back; no new tag API, Release rollback, alternative publisher or prompt rewrite was introduced.
- Step 5: `Assert-CgStableDocsContract` is called only in stable Reserve, after refreshed main lineage and before tag publication. It verifies origin/main ancestry, reads producer and controller at their exact commit SHAs, and recognizes the current reviewed upload/extraction/metadata layout as text. It verifies both isolated artifacts, hidden metadata inclusion, the controller extraction root, and the isolated docs/site selection. Unknown or conditional producer upload layouts halt with the file name and concrete main-sync remediation. No workflow content is executed. This is a conservative current-layout recognizer, not a general YAML or JavaScript semantic validator; format/contract changes require reviewed updates.
- Re-scoped `test_release_policy.py` so main-tip ancestry is permitted only inside the stable gate, whose only production call is guarded by `-not $isPrereleaseTag` in Reserve and precedes the tag push. Prerelease behavior and Finalize's current full chain are unchanged; Phase 3 has not started.
- Expanded offline tests for settled ID/draft disagreement, immediate absence, one-attempt override, controller metadata/extraction/selection drift, and nonempty audit scope. All sleeps in the full offline fixture are mocked; no new real-delay tests were added.
- PowerShell parser checks passed for production and test files. `git diff --check` passed. These are static checks, not green runtime evidence. Editor `get_errors` remains unavailable.

### Phase 2 Classic-Protection Audit

| Surface | Result | Change |
| --- | --- | --- |
| `create-release.ps1` | Uses active rulesets; no classic protection read | No audit repair needed |
| `scripts/release-legacy-authority.ps1` | Uses `Get-CgRepositoryRuleset`; classic endpoint appears only in the documented banned comment | Unchanged |
| `.github/workflows/release-controller.yml` | No classic endpoint read | Unchanged |
| `.github/workflows/release-controller-bridge.yml` | No classic endpoint read | Unchanged |
| `.github/workflows/release-controller-build.yml` | No classic endpoint read | Unchanged |
| `.github/workflows/release-controller-ci.yml` | No classic endpoint read | Unchanged |
| `.github/workflows/release-controller-docs.yml` | No classic endpoint read | Unchanged |
| `.github/workflows/release-controller-publish.yml` | No classic endpoint read | Unchanged |

The initial glob search omitted hidden-directory entries. The audit above uses explicit directory and file reads of all six workflows; the Pester guard also requires a nonempty workflow list. No async controller enablement changed.

### Phase 2 Runner And Review Requests

Parent dedicated runner, shared worktree, Pester safety loaded:

1. Run `. tests\Run-Tests.ps1 -File create-release`, without extra flags or a pipeline. Read `tests/last-run.json` and return identity, counts, filteredFiles, all failure summaries and cleanup diagnostics.
2. Run `python -m pytest scripts/tests/test_cg_pr_preflight.py scripts/tests/test_release_policy.py scripts/tests/test_release_gate_targets.py -q --tb=short`. Return exit code, counts, duration, skips and bounded failure details. This retains Phase 1 receipt regression coverage.
3. If focused tests pass, run `. tests\Run-Tests.ps1`, without flags or a pipeline. Read `tests/last-run.json`; require `filteredFiles: null`. Preserve any cleanup diagnostics separately from assertion results. Do not run focused Pester concurrently with the full suite because both write the same artifact.

Parent review request: resolve `review:auto` to `full` for release-automation/security risk under `.kilo/shared/review-routing.contract.md`. Load the ten specs in `.kilo/agents/`: `cg-code-quality.md`, `cg-testing.md`, `cg-documentation.md`, `cg-version-control.md`, `cg-reproducibility.md`, `cg-performance.md`, `cg-architecture.md`, `cg-data-quality.md`, `cg-learnings-researcher.md`, `cg-adversarial.md`. Review the Phase 2 changes in `create-release.ps1`, `tests/create-release.Tests.ps1`, `scripts/tests/test_release_policy.py`, and this report/active-state metadata. Focus on read-only reconciliation, bounded attempts and sleep, unchanged strict metadata checks, exact-ref stable-only docs verification, no-fallback publication, and Phase 1 preservation. The uncommitted diff also contains accepted Phase 1 changes; use its review ledger as baseline rather than attributing them to Phase 2. Return P0-P3 findings with file/line references and evidence gaps. Do not mutate protected assets or apply fixes; parent owns review dispatch and ledger capture.

Model advisory: implementation-to-review requires strong code and configuration review, evidence checks and adversarial reasoning; high effort is advised. Capability guidance is a suggestion only; availability varies, and the user controls the model and effort. No model change is requested.

### Phase 2 Current Status

Blocked on executed focused/full-suite evidence and full-route review, not on runner availability. V2 needs regression confirmation; V3-V5 are implemented but not yet verified. No accepted evidence exception. `completed-phases: [1]` and `current-phase: 2` remain unchanged. No shared commit, snapshot commit, push, PR, main integration or later phase was performed.

### Phase 2 Review Repair Round 1: 2026-09-17

- Parent focused Pester evidence: gitSha `8bc05e51`, ranAt `2026-09-17T02:45:44Z`, total 159, passed 158, failed 1, skipped 0, filteredFiles `create-release`, failFast false. `throws the conflict only after the requested bound without remote writes` expected zero non-Get calls but counted three. No cleanup errors. Full boundary gate was not run.
- Parent focused Python: 143 passed, 3 skipped, 0 failed. This predates the repairs below and remains historical evidence.
- Full review completed 10/10 specifications with P1.1 (manual, incomplete stable controller recognizer) and P2.1 (safe_auto, invalid/unsafe resume guidance). Parent reviewer: `ses_f52bf40bbffeMlCyfowYj1ayAA`; runner: `ses_f52c730a8ffeHW5Uqz9O241K6n`. Findings and verification state are recorded in `.cg-docs/reviews/2026-09-16-cg-release-prerelease-automation-phase2-review.md`.
- User authorized in-scope repairs. P1.1 now requires whole dev/release extraction steps with exact artifact IDs, paths and conditional availability; matching source checkout paths; full import/compose/move operations; final Pages site/ upload; and extraction-to-composition order. Added before-write failure fixtures for changed paths, missing/skipped dev download/composition/upload, and premature composition. The gate remains a conservative text recognizer, not an arbitrary YAML/code interpreter.
- P2.1 now separates initial read-only inspection from the separately authorized legacy resume command. Both explicit selectors are shown; the message states that resume requires confirmation and may run Reserve or Finalize. The earlier report's read-only resume wording is superseded by this correction.
- The single Pester failure was a mock parameter-filter issue: omitted Method is recorded as null, not the declared Get default. The assertion now counts only explicit non-Get methods. A mocked Post control proves this filter detects a write. Production reconciliation semantics are unchanged.
- Production and test PowerShell parser checks passed after repair; `git diff --check` passed. Both findings remain open pending executed tests and independent delta review. No accepted evidence exception and no Phase 2 completion write.

### Phase 2 Repair Verification Requests

Dedicated runner: rerun `. tests\Run-Tests.ps1 -File create-release`, then `python -m pytest scripts/tests/test_cg_pr_preflight.py scripts/tests/test_release_policy.py scripts/tests/test_release_gate_targets.py -q --tb=short`. If both pass, run `. tests\Run-Tests.ps1` unfiltered. Use the approved task substitution, load Pester safety, avoid concurrent Pester runs and return exact identities, counts, failures, filteredFiles and cleanup diagnostics. No live publication or Git mutation is requested.

Independent reviewer: verify P1.1, P2.1 and the mock-filter correction against the Phase 2 ledger, using the completed full-route review as baseline. Inspect the expanded `Assert-CgStableDocsContract`, recovery error and new tests. Confirm the original two counterexamples now halt before tag push/Release POST, check conditional availability and path/order agreement, and check for new regressions or scope expansion. Return finding statuses and any new P0-P3 issues; do not apply fixes or advance the pipeline.

## Phase 2 Final Evidence And Closure: 2026-09-17

Phase 2 steps 3-5 are complete. Earlier pending statements are historical
checkpoints and are superseded by this final evidence. Phase 1 remains complete;
Phase 3 has not started.

- Focused Pester: 176 total, 176 passed, 0 failed, 0 skipped; gitSha `8bc05e51`, ranAt `2026-09-17T02:54:56Z`, filteredFiles `create-release`, failFast false, failures empty.
- Focused Python: 143 passed, 0 failed, 3 skipped in 78.01 seconds. Command: `python -m pytest scripts/tests/test_cg_pr_preflight.py scripts/tests/test_release_policy.py scripts/tests/test_release_gate_targets.py -q --tb=short`.
- Full Pester: 3071 total, 3069 passed, 0 failed, 2 skipped (update); gitSha `8bc05e51`, ranAt `2026-09-17T03:00:47Z`, passed true, filteredFiles null, failFast false, failures empty. No files were omitted from the full runner result.
- Preserved Pester artifacts: `C:\Users\wb384996\AppData\Local\Temp\3\kilo\phase2-focused-20260917T025456Z.json` and `C:\Users\wb384996\AppData\Local\Temp\3\kilo\phase2-full-20260917T030047Z.json`. This thread read both summaries and confirmed the supplied identities/counts.
- Full-suite TestDrive cleanup diagnostics concern missing/nonempty temporary skill paths, as in Phase 1. No assertion failure was recorded. Preserve this qualification; no claim of error-free cleanup is made. Critical log: `C:\Users\wb384996\.local\share\kilo\tool-output\tool_0ad4dbc3d001JOKJsRR9p6tdUQ`.
- Full review covered 10/10 specifications. Independent delta review confirmed P1.1, P2.1 and the filter correction fixed; no new P0/P1 or cross-file finding was reported. Both ledger findings are now fixed. No finding was skipped, downgraded or accepted without repair.

### Phase 2 Verification Surface

| ID | Status | Final evidence |
| --- | --- | --- |
| V2 | passed | Receipt regression cases included in 176 passing create-release tests; focused Python receipt suite also passed |
| V3 | passed | Executed bounded reconciliation cases cover settled present/absent pairs, field disagreement, retry limits, sleeps and read-only methods |
| V4 | passed | Executed no-fallback and nonempty workflow-family audit guards; eight audit surfaces recorded above |
| V5 | passed | Executed stable-only docs gate fixtures, including repaired dev extraction/composition cases; re-scoped Python lineage contracts passed |
| Phase 2 boundary | passed | Unfiltered full Pester passed; 10/10 review completed, two findings fixed |
| V6-V10 | not started | Later-phase evidence; outside this execution |
| V11-V12 | not started | Whole-plan matrix/live acceptance and timing; outside this execution |

### Phase 2 Constraints And Limits

- C1-C8 and C10-C12: passing regression/guard tests; no tag mutation, publication, rollback, authority weakening, payload change, controller enablement, attestation change or in-tree receipt added by this phase.
- C9: no PR or integration action; the current user instruction remains dev-only. Reading main lineage is allowed; this phase did not modify main or any workflow.
- Approved dedicated-task runner substitution remains recorded. No elevated setup, global configuration changes, shared commit or additional disposable snapshot commit occurred.
- No accepted evidence exception. No remaining Phase 2 blocker. Three Python skips, two existing update skips and cleanup diagnostics remain explicit qualifications.
- The stable docs gate deliberately recognizes the reviewed current workflow layout and fails closed on unrecognized changes; it does not execute workflow content or claim general YAML/JavaScript semantic validation.
- Editor diagnostics are unavailable. Runtime tests, PowerShell parser checks and independent review supply verification; no editor diagnostic result is claimed.

### Phase 2 Completion Metadata

The plan remains active. Completion is recorded crash-safely: append Phase 2 to
`completed-phases`, read it back, then advance informational `current-phase` to 3.
The next-command pointer is a parent handoff only, not execution authorization in
this thread. No Phase 3 or later command was run. Metadata validation results are
recorded below after execution.

- Completion metadata validation passed: `python scripts/render_artifact.py --validate-only .cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md`, `python -m json.tool .cg-docs/active-state/current.json`, and `git diff --check`.
- Confirmed `completed-phases: [1, 2]` by re-reading before changing `current-phase` to 3. Plan status remains active; active state is a handoff. Phase 3 is only the next-phase pointer and was not started.
- Final status: Success, Phase 2 only. All required Phase 2 evidence and review gates are met. No commit, push or PR was performed.

## Phase 3 Resume: 2026-09-17

- Scope: Phase 3 only, plan step 6. Phase 1/2 evidence and unrelated shared changes remain intact. Plan validation passed before mutation. Active deviation policy remains `ask`.
- Loaded the work command, context-loading, goal-execution, artifact-view and active-state contracts, PowerShell instructions, Pester safety and Brain query skills. Open-brain tools are unavailable. The bounded local Brain query returned an older general release plan, not an applicable docs-chain lesson; current source and this approved plan govern.
- Added a BuildRunId-only fixture option and prerelease success/failure tests. Moved existing controller/deployment and historical manual-recovery regression cases to the existing stable fixture. No production code changed before the required red baseline.
- Test index: `tests/create-release.Tests.ps1` for executable Finalize and stable authority checks; `scripts/tests/test_release_gate_targets.py` and `scripts/tests/test_release_policy.py` for workflow/release regression checks. Full Pester remains the phase boundary gate.
- Required V6 includes a merged main controller PR. The current user instruction prohibits all main integration and defers shared commits/push/PR until step9. No PR will be opened. This evidence remains missing, not waived; Phase 3 cannot be marked complete without the required evidence or an explicit accepted exception.
- Approved dedicated-task runner substitution continues. This thread has no nested task or execution_subagent tool. The parent must run the red baseline and return evidence before production implementation, then dispatch green/full tests and independent review. This is a runner handoff, not a claim that implementation is complete.

### Phase 3 RUNNER_REQUEST: Red Baseline

In the shared current worktree, load `cg-skill-pester-safety`, then run `. tests\Run-Tests.ps1 -File create-release` with no other flags or pipeline. Read `tests/last-run.json` and return gitSha, ranAt, passed, totalCount, passedCount, failedCount, skipped count, filteredFiles, failure names/messages and cleanup diagnostics. Do not run another Pester job concurrently. No installs, global config, Git mutation or live release command. Resume this implementation thread with the result; do not advance to Phase 4.

Expected new red case: `finalizes a prerelease with only the exact build and no deployment reads` currently fails because the implementation still requires a successful release-pages controller. Stable fixture regression cases must remain green. Review dispatch follows production implementation, not this red-only checkpoint.

### Phase 3 Policy Reconciliation: 2026-09-17

- The user explicitly clarified stable source eligibility as deployment branches or the default branch, and four-component prerelease eligibility as any branch, including dev. This authorizes necessary source-policy changes, not a remote-check bypass or an evidence waiver.
- Current code does not satisfy that rule: `create-release.ps1` assigns main/dev from tag shape (lines 145-146) and enforces that branch's remote lineage (lines 421, 781). `release-docs.yml` uses `release-version.js --legacy-docs-branch` and checks ancestor membership (lines 33-36); that helper returns only main/dev (line 41). A Finalize-only edit would therefore be insufficient for feature-branch prereleases.
- The existing stable contract reads origin/main (create-release lines 241-255). In contrast, `Assert-CgLegacyAuthority` already discovers and verifies the remote default and reads its exact policy commit (release-legacy-authority lines 35-73). Reuse protected remote authority for source policy; do not trust the source branch's editable policy. `production_branches` is the existing configuration vocabulary, currently [main]. Stable eligibility must include the remote default as well.
- The disabled async controller is not the active legacy path. Its `policy.py` lines 250-266 have a maintainer override and use default only when production_branches is empty. Do not claim that implementation already meets the user's ONLY restriction, and do not enable it. Any future enablement must enforce the clarified rule as well.
- Option A controls the full-site Pages destination, not permission to publish a prerelease. `pages.yml` lines 6 and 46-54 restrict the separate preview producer to dev. The clarified source rule does not require one preview per source branch or prerelease replacement of the official full site. Keep Option A and the dev preview; allow prerelease tag builds/publication from verified source branches.
- Authorized plan amendment recorded in Phase 3: expand source-policy and build-path scope, retain local full-suite/review V6, and move protected remote activation evidence to required final V13. This is an explicit scheduling change, not a waiver. No actual remote deployment is claimed. Phase 1/2 historical completion remains unchanged, but their main-only contract will be revised under Phase 3.
- No policy ambiguity requires a new user choice. Implementation must bind an explicit same-repository source branch where detached/tag context is insufficient, use current protected remote configuration/default authority, reject malformed or unknown branch data, and preserve immutable SHA and required-check guards.
- No production edits have been made at this checkpoint. The existing RUNNER_REQUEST remains ready: return the prepared Finalize red baseline first, then resume this thread to add source-policy red cases and implement Phase 3. No direct Pester, shared commit, push, PR, or Phase 4 execution occurred.

### Phase 3 Finalize Red Evidence And First Implementation

- Parent red baseline: gitSha `8bc05e51`, ranAt `2026-09-17T15:09:21Z`, total 178, passed 177, failed 1, skipped 0, filteredFiles `create-release`, passed false. The sole failure was `finalizes a prerelease with only the exact build and no deployment reads`: a successful release-pages.yml controller run named Deploy docs from 10 was required. No cleanup errors reported. This confirms the required failing baseline for the Finalize branch.
- Implemented that branch in `create-release.ps1`: four-component Finalize validates the exact successful build and retains fresh authority, tag/Release read-back and final attestation checks, but does not query Pages or call `Assert-CgLegacyDeployment`. Stable Finalize retains the complete controller/job/deployment chain and historical recovery bindings. Help text now distinguishes build evidence from stable deployment evidence. Runtime confirmation is pending.
- Added 15 source-policy Pester cases: feature/dev/default prereleases, stable configured/default branches, forbidden stable feature source, detached explicit-source requirement, missing remote branch, incorrect tip/lineage, and four malformed policy cases. Fixtures expose remote policy and source branch state without changing default behavior. Production source selection is deliberately unchanged until these tests run red.
- Added five Node tests in `scripts/tests/release-version.test.js` for the intended shared docs source-policy validator `assertReleaseSource`: stable configured/default branches, prerelease branches, invalid policy/ref inputs, safe absent-policy handling, and rejection of controller-owned identities. This pure validator is not remote lineage proof; workflow/API integration must separately establish canonical repository and branch/SHA identity.

### Phase 3 RUNNER_REQUEST: Source Policy Red And Finalize Regression

Parent dedicated runner, shared worktree:

1. Load Pester safety and run `. tests\Run-Tests.ps1 -File create-release` without extra flags/pipeline. Read `tests/last-run.json`; return identities, counts, filteredFiles, each failure summary and cleanup diagnostics. The prior Finalize red case should now pass; the new source-policy cases should fail because production has no SourceBranch interface or detached-source requirement yet.
2. Run `node --test scripts/tests/release-version.test.js`; return exit status, counts and bounded failures. The five new source-policy tests should fail because `assertReleaseSource` is not implemented. Existing three tests should pass.
3. Resume this implementation thread with both results. No full-suite or independent full review yet: source-policy production and workflow changes are still pending. No live release, shared Git mutation, installation or elevation is needed.

### Phase 3 REVIEW_REQUEST: After Implementation And Focused Green

Parent must dispatch independent full-route review after source-policy and workflow implementation, not at this intermediate checkpoint. Resolved mode is full because release automation and branch authorization are security-risk triggers. Load all ten specs from `.kilo/agents/`: cg-code-quality, cg-testing, cg-documentation, cg-version-control, cg-reproducibility, cg-performance, cg-architecture, cg-data-quality, cg-learnings-researcher, cg-adversarial. Review only Phase 3 deltas relative to the accepted Phase 1/2 ledger baseline. Required focus: stable configured/default-only source eligibility; prerelease any verified same-repository branch; protected remote policy trust and refresh; exact branch/commit/tag binding; no stable branch override; docs control plane versus source/destination separation; prerelease no deployment reads; stable historical and full-chain regression; V6 local evidence and V13 deferred activation. Preserve all protected assets and report P0-P3 findings with file/line evidence. Do not implement fixes, waive evidence, or advance to Phase 4.

- Static checks passed at this checkpoint: PowerShell parser for production/test files, `node --check scripts/tests/release-version.test.js`, and `git diff --check`. Git emitted its configured LF-to-CRLF warning for the Node test file; no whitespace error. No runtime pass is inferred from these checks. Editor diagnostics remain unavailable.

### Phase 3 Source Policy Red Evidence: 2026-09-17

- Parent Pester evidence: gitSha `8bc05e51`, ranAt `2026-09-17T15:16:07Z`, total 193, passed 178, failed 15, skipped 0, filteredFiles `create-release`, passed false, failFast false. Fourteen new cases failed on missing SourceBranch; the detached-source case did not throw. The earlier Finalize failure is resolved. No unrelated failure, cleanup error or timeout was reported.
- Parent Node evidence: total 8, passed 3, failed 5, skipped 0. All five new cases failed because `assertReleaseSource` was not a function. Existing cases passed. Numeric process exit codes were not separately exposed. Source-policy red phase confirmed before implementation.

### Phase 3 Production Implementation Ready

- `create-release.ps1` accepts `-SourceBranch`, otherwise reads the attached branch. Detached checkouts require explicit identity. Branch names are validated as Git refs before use; canonical origin, exact new-tag tip, resumed-tag ancestry and immutable tag checks remain. Ref read-back now validates both the returned SHA and full ref name. Source lineage is refreshed before the Release POST and final attestation as well.
- `release-legacy-authority.ps1` reads deployment source policy only from the exact protected remote default commit already verified by the authority gate. Stable eligibility is the union of `production_branches` and the current remote default. Missing optional production policy permits only default for stable tags; malformed/null/string arrays, invalid names and duplicate production keys fail closed. Prereleases have no source allowlist. Every publication/attestation authority recheck includes this source policy; no stable branch override was added.
- Stable docs verification reads the exact protected default controller commit, independent of the selected source branch. It no longer requires deployment source ancestry from origin/main. Existing conservative artifact extraction/composition recognition is preserved. Remediation names the actual protected branch. A protected-controller change between contract verification and publication stops the attempt.
- `release-version.js` supplies a shared source eligibility validator and a bounded, GET-only remote resolver for tag-build and deployment workflows. A tag event has no original branch name: the resolver selects a permitted remote branch containing the exact commit, or verifies an explicit `RELEASE_SOURCE_BRANCH`. It does not infer source from version shape, trust the tag checkout's policy, or claim to recover the tag creator's checkout branch. Repository ID/name/fork status, protected default policy commit, candidate ref/SHA, comparison ancestry, and fresh source/default identities are checked. Prerelease enumeration is capped at 20 pages of 100 branches; exceeding the bound requires an explicit candidate.
- `release-docs.yml` uses that resolver before its existing exact tag/fetched-source lineage and payload checks. It remains contents-read-only. The protected release Pages controller uses the same resolver and rechecks its selected source before deployment. Its new read-only classifier runs protected code, passes tags as inert environment/argv data, and skips full-site deployment for four-component tags, including manual recovery attempts. The protected Pages helper independently rejects prerelease full-site deployment.
- `pages.yml` adds only `releases/**` to the existing dev-preview push paths. No `.github/shared/**` path, per-feature preview site, `docs-site-build.yml` change, controller enablement, attestation schema change, or source-policy override was introduced.
- Re-derived obsolete main/dev branch assertions and main-tip ancestry assertions to the approved rule. Stable fixture controller reads now bind the protected default SHA. Added branch-policy revocation-before-POST, unsafe refs, remote resolver trust/ancestry/race/bound tests, real CLI classification tests, and Pages guard tests. Historical full-site recovery tests now use stable tags. `tests/docs-automation.Tests.ps1` changes are limited to workflow/source/classification contracts; Phase 4 prompt-order and prompt text remain untouched.
- Existing `legacyDocsBranch` reader API remains for existing callers, but neither changed workflow uses its main/dev return value for source authorization. The disabled async controller remains unchanged and is not claimed to satisfy the new ONLY restriction if enabled in future.
- Static verification passed: production/helper/test PowerShell parses; Node syntax checks for both production scripts and their tests; `git diff --check`. Git's configured LF-to-CRLF warnings for Node files remain noted. Runtime verification is pending; no green or remote deployment claim is made.

### Phase 3 RUNNER_REQUEST: Focused Green

Parent dedicated runner in the shared worktree, Pester safety loaded:

1. Run `. tests\Run-Tests.ps1 -File create-release` without other flags/pipeline. Preserve/read `tests/last-run.json` before the next Pester command; return identity, counts, filteredFiles, all failure summaries and cleanup diagnostics.
2. Run `. tests\Run-Tests.ps1 -File docs-automation` with the same safety and artifact rules. These are confirmed runner registry names, not filenames. Never overlap the two Pester jobs.
3. Run `node --test scripts/tests/release-version.test.js scripts/tests/legacy-pages.test.js scripts/evidence/tests/release-pages.test.js`. Return exit status, counts, durations and bounded failures.
4. Run `python -m pytest scripts/tests/test_cg_pr_preflight.py scripts/tests/test_release_policy.py scripts/tests/test_release_gate_targets.py -q --tb=short`. Return exit status, counts, duration, skip reasons and bounded failures. This retains Phase 1 receipt regression coverage.

Node/Python may run independently of Pester, but do not start a full Pester suite concurrently. No live release, installation, elevation, global configuration change or shared Git mutation. Return evidence to this thread for recovery and review preparation. Full-suite boundary and independent full-route review remain required after focused green; V13 remains required after step9 activation. Phase 3 is not complete and Phase 4 is not started.

### Phase 3 Focused Results And Review Repair Round 1

- Parent focused evidence: create-release 199 passed, zero failures/skips, gitSha `8bc05e51`, ranAt `2026-09-17T15:33:55Z`; docs-automation 24 passed, zero failures/skips, same gitSha, ranAt `2026-09-17T15:34:27Z`. Both filtered runs, not a full-suite boundary. Python 144 passed, 3 skipped, zero failures. Node 37 total, 36 passed, one failure at `scripts/evidence/tests/release-pages.test.js:149` due to its obsolete legacy-docs-branch assertion.
- Full review 10/10 completed by parent reviewer `ses_f500045e6ffeO3eQZ2tY87ZkFl`, with three P1 manual findings. Ledger: `.cg-docs/reviews/2026-09-16-cg-release-prerelease-automation-phase3-review.md`. User authorized these repairs; all findings remain open pending tests and independent delta review.
- P1.1 repair: prerelease Finalize now checks the exact run attempt's successful build job, exact SHA/run/attempt, all required build/upload steps in order, artifact run/SHA/name/digest/expiry and artifact creation within the successful job interval. A successful wrapper with skipped/missing build or stale/missing artifact cannot attest. Added fourteen negative cases and an exact retry success case; no Pages requirement.
- P1.2 repair: dev preview no longer checks out moving main content. A GET-only official-snapshot gate finds successful protected official deploy jobs in a bounded 100-run window, orders by deployment completion, checks controller ancestry and the exact stable build/artifact, and resolves its eligible source. The workflow downloads that artifact, imports verified docs into the exact official source SHA, composes dev, and rechecks the official tuple before deployment. Added remote selection and failure cases plus a stable-deploy -> dev-preview test that compares every official output byte. The source directory name sources/main is retained as a composition input label, not branch authority.
- Preview safety limit: missing official deployment history in the bounded window, expired/deleted producer artifacts, no currently eligible payload-matching source, or changed official evidence blocks preview. There is deliberately no fallback to main or an older official artifact. Existing producer artifact retention is one day; activation must account for this availability limit. No claim is made that these remote prerequisites currently exist or that V13 passed.
- P1.3 repair: source resolution verifies immutable tag payload/latest equality and candidate latest bytes at the exact branch tip before selection. It can skip an advanced default with newer prerelease payload and select a matching configured deployment branch. Explicit source mismatch still fails. Added ambiguous automatic selection and skew/absence cases.
- Corrected the failing Node contract by re-deriving it to --resolve-source and executable stable/configured/default and feature-prerelease policy checks. Existing protected controller, exact build/tag/SHA, branch ancestry, newest-payload and before-deployment recheck invariants remain asserted.
- Updated workflow contract tests for exact official checkout/download and two official-snapshot checks. No prompt rewrite, async enablement, attestation schema change, shared Git mutation or next phase was performed.

### Phase 3 Repair Verification Requests

RUNNER_REQUEST: use the same four focused commands in the preceding request, with Pester safety, sequential Pester jobs and separate last-run artifacts. Return identities, counts, filteredFiles, failure summaries, skip reasons and cleanup diagnostics. All results above predate these repairs. If every focused command passes, the unfiltered `. tests\Run-Tests.ps1` boundary remains required; do not overlap it with another Pester command.

REVIEW_REQUEST: independent delta review against the Phase 3 full-route ledger. Verify P1.1 exact job/attempt/artifact proof and skipped-wrapper counterexample; P1.2 stable deploy/2.x -> dev update preservation, protected history selection, archive/source binding, missing/expired evidence behavior and post-upload recheck; P1.3 ambiguous default/deployment candidates with different current payload bytes. Check the re-derived Node invariant rather than removing it. Return finding statuses and new P0-P3 issues. Do not close findings solely from static inspection, waive V13, apply fixes, or advance Phase 4.

### Phase 3 Round 1 Evidence And Durability Repairs

- Parent focused evidence after round 1: create-release 214 passes; docs-automation 24 passes; Node 42 passes; Python 144 passes and 3 skips. These results predate the durability repair below.
- Parent full Pester: 3109 total, 3106 passed, 1 failed, 2 skipped; gitSha `8bc05e51`, ranAt `2026-09-17T16:00:51Z`, filteredFiles null. Failure: `docs-preview` still asserted a main checkout in `checks out main as content and uses protected default code as controller`. The test is now re-derived around protected code plus authenticated official static data, preserving the trust boundary. Missing/nonempty TestDrive cleanup errors remain a separate qualification.
- Reviewer confirmed P1.1 and P1.3 static fixes, now backed by passing focused runtime cases. P1.2's original overwrite was prevented with passing sequential preservation evidence, but reviewer added P1.4 (ephemeral artifact/history dependency) and P1.5 (historical snapshot incorrectly subject to current-payload freshness). The original three findings are fixed; new P1.4/P1.5 remain open. The earlier report's one-day qualification was insufficient and is superseded by this repair.

### Durable Strategy And Authority

- Inspected `scripts/docs-snapshots.js`, `scripts/snapshot-data.js`, disabled `.github/workflows/release-controller-docs.yml`, and the package's snapshot/selection surfaces. An existing strict snapshot envelope already binds all docs bytes, paths, SHA, tag, run identity and digest. Its remote registry belongs to the disabled async controller and needs separate protected write authority; it is not enabled or reused.
- Added `scripts/legacy-official-snapshot.js` to reuse only the existing static-data format. The current protected official Pages job seals `cg-official-snapshot.json` into its existing Pages artifact. The existing successful Pages deployment atomically publishes the docs and state together. There is no new publisher, state branch, Release asset write, token scope, Git commit or remote configuration change.
- The file contains only already-public official docs bytes and provenance. Previews retrieve it from the exact workflow-managed repository HTTPS Pages origin returned by GitHub (no custom-domain inference, redirects or credential header), validate its complete strict snapshot envelope, and authenticate its publisher against the current successful github-pages environment deployment and exact protected job/run attempt/controller lineage. Stale served state that does not match that current deployment is rejected.
- The current environment pointer is independent of the original stable build's artifact expiry and of mixed Actions history. An active preview/pending or failed deployment does not replace the last successful pointer. There is no lookup of the original build artifact or search for the old official workflow. Current publisher metadata is verified directly, not by retaining old build logs or artifacts.
- Previews restore the immutable official bytes as data, compose the new dev tree, retain the exact official envelope, update only the publisher tuple, and recheck the fetched state before deployment. They do not consult the historical source branch's current payload or current production membership. New official deployment still uses the P1.3 current-payload/source checks before sealing new official state.
- Plan amendment records this repair-specific scope and seeding requirement under the user's broad implementation and repair authorization. This is a local implementation change, not inferred protected remote write approval. Initial V13 activation requires one authorized protected official Pages deployment to seed the durable format, followed by preview verification. No bootstrap from unverified main bytes or remote deployment has been performed.

### Round 2 Coverage And Requests

- Updated the stable contract recognizer to require the durable sealing step before upload; added missing/skipped seal cases. Re-derived docs-preview, docs-automation and Python workflow checks to preserve protected code/static-data separation without a main checkout.
- Added a positive durable read case with old artifacts expired, more than 100 unrelated runs, and source payload advanced; assertions prohibit old-build/artifact/history/source-payload reads. Added corrupt, stale, foreign publisher/origin, and pending/failed deployment cases. The sequential test exercises actual seal, restore, compose, stamp and recheck functions, proves preparation does not publish state, compares every official docs byte and immutable official envelope, and verifies subsequent preview reuse.
- Syntax checks passed for the new helper, dispatch, Node tests and re-derived Pester test; amended plan validation passed. Runtime reruns and independent delta review remain pending. No Phase 4 execution or completion write.

RUNNER_REQUEST: load Pester safety; run `. tests\Run-Tests.ps1 -File create-release`, `. tests\Run-Tests.ps1 -File docs-automation`, and `. tests\Run-Tests.ps1 -File docs-preview` separately, preserving/reading last-run.json after each. Run `node --test scripts/tests/release-version.test.js scripts/tests/legacy-pages.test.js scripts/evidence/tests/release-pages.test.js scripts/tests/docs-snapshots.test.js`. Run the same focused Python command recorded above. Return exact identities/counts, failures, skips, exits where available and cleanup diagnostics. If all focused checks pass, run unfiltered `. tests\Run-Tests.ps1` with no concurrent Pester job. No installation, elevation, global changes or live publication.

REVIEW_REQUEST: independently verify P1.4/P1.5 against the Phase 3 ledger and inspect the new served-state trust boundary. Focus on exact repository origin, credential-free bounded HTTPS retrieval, current environment-deployment/job/run binding, stale response rejection, immutable official bytes, unchanged new-release freshness, bootstrap/activation limits, and absence of new remote write authority. Verify the positive expiry/history/branch-advance and sequential tests. Preserve P1.1-P1.3 regression checks. Findings remain open until runtime and delta review agree; V13 is not waived.

### Recovery Token Repair And Remaining Preview Assertion

- Parent focused Pester, gitSha `8bc05e51`: create-release 216 passed, ranAt `2026-09-17T16:23:24Z`; docs-automation 24 passed, ranAt `2026-09-17T16:23:49Z`; docs-preview 9 passed, 1 failed, ranAt `2026-09-17T16:24:16Z`. Failure was only the remaining obsolete `--main-root sources/main --dev-root sources/dev` assertion. No cleanup errors; full Pester not run. Node 67 passed; Python 144 passed and 3 skipped.
- Reviewer confirmed P1.2/P1.4/P1.5 static resolution with runtime regressions now passing. Those findings are fixed. New P1.6 safe_auto: sealing used github.token during recovery, but its authority check requires the already-issued recovery App token's administration-read permission. User authorized the repair.
- Sealing now explicitly uses the same `${{ steps.recovery-authority.outputs.token || github.token }}` expression as initial authority and final recheck. No new token, permission, remote action or publisher. The stable controller recognizer requires the token expression. Added a Pester negative case for token removal and a Python parsed-workflow test covering initial/seal/final propagation and the existing manual-recovery token configuration.
- Re-derived the remaining docs-preview root assertion to official-source plus sources/dev, preserving its authenticated data, protected code, exact dev artifact/source and combined verification checks. No production snapshot algorithm changed in this repair.
- P1.6 remains open for verification. Phase 3 remains incomplete; Phase 4 has not started. V13 is still required after step9.

RUNNER_REQUEST: load Pester safety; run `. tests\Run-Tests.ps1 -File create-release` and `. tests\Run-Tests.ps1 -File docs-preview` separately, preserving each last-run.json. Run `python -m pytest scripts/tests/test_release_policy.py -q --tb=short`. If all focused checks pass, run unfiltered `. tests\Run-Tests.ps1` with no concurrent Pester job. Return artifact identity, counts, filteredFiles, failures, skips, exits where available and cleanup diagnostics. The unchanged snapshot Node implementation retains its 67-pass evidence; the new token contract is covered by focused Python/Pester.

REVIEW_REQUEST: independent P1.6 delta review. Verify existing recovery token propagation into sealing, routine github.token fallback, no privilege expansion, the matching fail-closed recognizer and negative test, and the re-derived docs-preview root assertion. Return finding closure/new findings without applying changes or advancing Phase 4.

## Phase 3 Final Local Closure: 2026-09-17

**Status: Success, Phase 3 only.** The clarified local V6 verification surface is
complete. Earlier intermediate requests, failures and pending findings above are
historical; the final evidence here governs local Phase 3 completion.

### Final Evidence

- Final focused Pester: create-release 217 passed, 0 failed, 0 skipped, gitSha `8bc05e51`, ranAt `2026-09-17T16:31:24Z`; docs-preview 10 passed, 0 failed, ranAt `2026-09-17T16:31:44Z`. These were filtered runs, not the boundary gate.
- Final focused Python release policy: 15 passed, 0 failed, 0 skipped. Retained unchanged coverage: docs-automation 24 passes; four Node files 67 passes; combined Python 144 passes and 3 skips. Counts describe separate runs, not an aggregate.
- Full Pester boundary: 3112 total, 3110 passed, 0 failed, 2 skipped in update; gitSha `8bc05e51`, ranAt `2026-09-17T16:36:46Z`, passed true, filteredFiles null, failFast false, failures empty. Read `tests/last-run.json` in this implementation thread and confirmed its identity and counts against the parent evidence.
- Cleanup qualification: the full suite reported missing/nonempty temporary freshmanifest TestDrive directories. This remains documented separately from the zero assertion failures. The final focused runs had no cleanup errors.
- Independent full-route review: 10/10 specifications complete. Parent reviewer confirmed P1.6 fixed with no new P0/P1 or cross-file findings. P1.1-P1.6 are all fixed; zero open Phase 3 findings. Ledger: `.cg-docs/reviews/2026-09-16-cg-release-prerelease-automation-phase3-review.md`.

### Completed Scope

- Stable source eligibility is configured deployment branches plus the remote default; prerelease source eligibility is any verified same-repository branch. Protected controller authority is independent of source selection.
- Prerelease Finalize requires exact successful build-attempt/job/step/artifact evidence without Pages. Stable Finalize retains the protected deployment chain. New deployment resolves matching source ancestry and current payload bytes.
- Dev preview refreshes on releases/** and preserves authenticated durable official bytes from the current protected Pages deployment. Historical preservation does not depend on expired original build artifacts, a mixed-run history window or the source branch's current payload. Snapshot seeding and preview publication use the existing Pages publisher and permissions; recovery sealing carries the existing recovery token.
- The plan remains active. Completed phases are [1, 2, 3]; informational current-phase and next-command point to Phase 4 for a later invocation, not execution or approval to start it now. No roadmap completion is written.

### Gates And Limits

| Gate | Status | Evidence or remaining action |
|---|---|---|
| V6 | passed locally | Executed focused checks, full unfiltered Pester boundary and independent full-route/delta review above |
| V13 | pending, required | Actual authorized protected controller/source-policy activation, official durable-state seeding and preview verification after step9 submission |
| Later phases | not started | Phase 4 and Phase 5 remain outside this execution |

No live release policy or Pages change is claimed active. No shared commit, push,
PR, remote configuration write or deployment was performed. Existing Phase 1/2
and unrelated worktree changes are preserved. This closure does not complete the
whole plan or waive any final-stage gate.

### Closure Metadata Validation

- Wrote completed-phases [1, 2, 3] first, re-read and confirmed it, then moved the informational current-phase pointer to 4. Status remains active; Phase 4 was not executed.
- Plan artifact validation, handoff JSON parsing and git diff --check passed. Git emitted existing LF-to-CRLF warnings only.
- The artifact renderer rejected the review path because it supports only brainstorms/plans, not because the ledger metadata was malformed. Re-read the ledger frontmatter and parsed those exact fields with PyYAML; confirmed full/standard review metadata, the correct plan pointer and exactly six fixed findings. No review artifact was moved or rewritten to bypass the renderer's path contract.

## Phase 4 Resume: Tests First, 2026-09-17

- Scope: pipeline step4, Phase 4 only (plan steps 7-8). The user's source-policy clarification governs over obsolete main/dev mapping and controller ancestry instructions. Phases [1, 2, 3] remain complete; V13 remains required after step9, including official snapshot seeding and preview verification.
- Plan validation passed before edits. Loaded command, context/goal/artifact/active-state/review contracts, Pester safety, PowerShell instructions and Brain query skill. Open-brain tools are unavailable. Budgeted local Brain query returned this plan and older general release material, with no additional applicable lesson.
- Inspected canonical prompt and current source/receipt/Finalize implementations. SourceBranch is mandatory for detached checkouts; the receipt producer owns fresh LF checkout creation with command-local settings; prerelease Finalize checks exact successful build-attempt/job/steps/artifact rather than Pages. The rewrite must preserve generic argument dispatch and explicit legacy selectors; auto approval does not enable the disabled controller or grant missing legacy authority.
- Added eight independent contract tests in tests/prompt-tools.Tests.ps1 before implementation. They cover approval parsing before dispatch, clarified source policy, per-call source/receipt arguments, receipt ownership and conditioned rerun, bounded PR automation, stranded payload recovery, separate Finalize arms, and evidence/resume guards. Existing tests and all prior changes are preserved.
- Test index for the rewrite: tests/prompt-tools.Tests.ps1, tests/docs-automation.Tests.ps1, scripts/tests/test_cg_pr_preflight.py, scripts/tests/test_release_policy.py, scripts/tests/test_release_gate_targets.py; target parity uses scripts/tests/test_target_drift.py. Existing order and obsolete prompt-policy assertions will be re-derived only after red evidence, not removed to hide failures.
- No production prompt, generated target or catalog pin changed yet. Required failing baseline is pending parent execution. This thread has no nested task tool; the approved dedicated parent runner is the handoff, not an evidence waiver. Full review is required after implementation; do not review this red-only checkpoint as completed Phase 4.

### Phase 4 RUNNER_REQUEST: Red Baseline

In the current shared worktree, load cg-skill-pester-safety. Run `. tests\Run-Tests.ps1 -File prompt-tools` with no other flags or pipeline. Preserve/read tests/last-run.json immediately; return gitSha, ranAt, passed, totalCount, passedCount, failedCount, skipped counts, filteredFiles, failure names/messages and cleanup diagnostics. Then run `. tests\Run-Tests.ps1 -File docs-automation` under the same rules for the unchanged sequencing baseline. Never overlap Pester jobs. Return evidence to this implementation thread before the canonical prompt rewrite. No release execution, Git mutation, configuration mutation, system installation or Phase 5 work.

### Phase 4 Review Gate

After implementation and focused tests, parent dispatches full review with all ten specifications from .kilo/agents: cg-code-quality, cg-testing, cg-documentation, cg-version-control, cg-reproducibility, cg-performance, cg-architecture, cg-data-quality, cg-learnings-researcher, cg-adversarial. Focus on authority and source separation, approval scope, PR/gate sequencing, immutable SHA receipts, bounded failure handling, two Finalize arms, resume, evidence-only PR checks, generated parity and catalog pins. Preserve protected assets; return P0-P3 findings and evidence gaps. V7, V8, full unfiltered Pester boundary and full review remain pending. No completion metadata advance, shared commit/push/PR or Phase 5 is authorized here.

### Phase 4 Red Evidence And Implementation

- Parent red evidence: prompt-tools 1746 total, 1738 passed, 8 failed, 0 skipped; gitSha 8bc05e51, ranAt 2026-09-17T16:47:43Z, failFast false, filteredFiles prompt-tools. All eight new prerelease automation cases failed as expected. docs-automation 24 passed, ranAt 2026-09-17T16:48:48Z, same gitSha, filteredFiles docs-automation. No cleanup errors. Artifacts: C:\Users\wb384996\AppData\Local\Temp\7\kilo\prompt-tools-20260917T164743Z.json and docs-automation-20260917T164848Z.json. Red phase confirmed before canonical prompt edits.
- Rewrote the canonical release prompt: parse legacy auto approval before tool dispatch while preserving generic argv dispatch and explicit legacy authority; verify source branches under protected remote policy; retain interactive/manual stable behavior; record a publication decision before payload PR creation; run the producer-owned LF receipt gate at the committed payload while remote CI runs; use bounded rebase auto-merge observation and at most one conditioned SHA-mismatch gate; pass source/receipt into both publication phases; distinguish prerelease build-only and stable Pages evidence; reconcile missing result files without assuming success; preserve immutable resume and single-publisher rules.
- The clarified branch policy supersedes the plan's obsolete main-to-dev sync and default ancestry instructions. The prompt instead checks the exact protected controller contract for stable releases without requiring source ancestry from default. Prerelease eligibility does not imply auto-merge settings exist: automation checks actual destination enforcement and stops if missing. No automatic controller repair or remote settings write is added.
- Re-derived the docs sequencing contract to payload -> validation -> commit -> receipt gate -> merge -> tag -> Reserve -> docs wait -> Finalize -> evidence PR. This preserves the executable Reserve-before-docs invariant; the plan's contradictory prose ordering is not followed. Updated Python policy tests across all adapters and the gate-before-tag/Reserve assertion. Existing preflight blocking-budget/no-blind-retry test is unchanged and remains required.
- Added practical legacy usage and rollout limits to docs/reference.md. Generated all adapter trees with `python scripts/cg_generate_targets.py --all`; the tracked generated delta is the four release commands plus their ownership manifests. No command-definition digest catalog/repin surface was found in this checkout; no hand-edited pin or catalog change. Generator success does not substitute for drift tests.
- Static whitespace check passed with existing Node LF-to-CRLF warnings. No runtime green result, full-review result, remote activation or Phase 4 completion is claimed. No shared commit, push, PR, system install, Git config mutation or Phase 5 work occurred. Earlier phase changes remain intact.

### Phase 4 Round 1 Evidence And Wording-Only Review Repairs: 2026-09-17

- Parent focused Pester: prompt-tools 1746 passed, docs-automation 24 passed, create-release 217 passed; gitSha 8bc05e51, failFast false, filteredFiles per file. Artifacts preserved: prompt-tools-phase4-20260917T165938Z.json, docs-automation-phase4-20260917T170037Z.json, create-release-phase4-20260917T170205Z.json.
- Parent focused Python: 162 passed, 2 failed, 3 skipped in 106.9 seconds. Failures were both drift-test members from `scripts/tests/test_target_drift.py::TestNoDrift`: `test_generated_trees_are_not_stale` (generated trees stale) and `test_generated_skill_bundles_recursively_match_canonical_files` (incomplete bundle `.kilo/skills/cg-skill-stata-testing`).
- Root cause of the bundle mismatch: a stale editor backup file `.kilo/skills/cg-skill-stata-testing/references/.anti-patterns.md.4883404421c247648e6eb9aa4f449645.previous` existed inside the generated skill bundle but not in the canonical `.github/skills` source. Removed only that stale file; no canonical or generated manifest content was hand-edited.
- Ran the authorized generator again: `python scripts/cg_generate_targets.py --all` wrote 1502 files. The generated `cg-skill-stata-testing` bundle now matches the canonical file set exactly. Full drift suite: 19 passed in 40.03 seconds. Both drift failures are cleared.
- Full review completed 10/10, no P0/P1/P2. Three P3 advisories (manual) were confirmed, all fail-closed and already disclosed:
  1. Plan body stale prose ordering: the plan text contrasted implemented tag -> docs -> Reserve ordering; the implementation preserves executable Reserve-before-docs. Updated the plan's step-7 assertion-surface prose to the implemented payload -> validate -> commit -> gate+receipt -> PR auto-merge -> local tag/rulesets -> Reserve -> docs wait -> Finalize -> evidence PR order, stating Reserve remains the executable publication owner before the docs wait. No assertion semantics changed.
  2. Prompt Step 5.6 fresh receipt path vs Step 7 generic placeholder ambiguity: renamed the uniquely allocated path to `<gated-receipt-path>` in the Step 5 gate command and added an explicit sentence binding that exact path to Reserve, Finalize and resume calls; `<receipt-path>` now always refers to that exact path.
  3. Step 0.5 should explicitly reject `--auto-approve` in generic mode: added the sentence rejecting `--auto-approve` in generic mode alongside the existing explicit-selector requirement. No authority, flag or guard behavior changed.
- Existing independent-arm prompt contract tests still cover these strings; no test changes were needed for the wording-only repairs. No shared commit, push, PR, Git config mutation, system install or Phase 5 work occurred. V7/V8 remain pending the updated focused/full-suite re-run and review confirmation; V13 remains after step9.

### Phase 4 P2 Anchor Update: 2026-09-17

- Reviewer P2: mechanical anchor update required after the `<gated-receipt-path>` rename. Two test anchors still referenced the obsolete `<receipt-path>` placeholder:
  - `tests/prompt-tools.Tests.ps1` line 4635: `Should -Match '--emit-receipt <receipt-path>'` -> `'--emit-receipt <gated-receipt-path>'`.
  - `scripts/tests/test_release_gate_targets.py` line 165: `content.index('--run-native-target --emit-receipt <receipt-path>')` -> `'--run-native-target --emit-receipt <gated-receipt-path>'`.
- Both updated. Semantic intent (producer-owned receipt isolation and gate-before-tag order) is preserved and not weakened; the anchors now match the canonical prompt and the regenerated adapter commands.
- The canonical prompt is unchanged by this repair, so no target regeneration was needed and none was run. These are test-only edits.
- No shared commit, push, PR, Git config mutation, system install or Phase 5 work occurred. V7/V8 remain pending the focused/full-suite re-run and review confirmation; V13 remains after step9.

### Phase 4 RUNNER_REQUEST: Focused Re-Verification After Wording Repairs

Re-run every focused surface because the canonical prompt and regenerated targets changed since the last green evidence. Parent dedicated runner in the shared worktree, with cg-skill-pester-safety loaded; no concurrent Pester jobs:

1. Run `. tests\Run-Tests.ps1 -File prompt-tools` and preserve/read tests/last-run.json.
2. Run `. tests\Run-Tests.ps1 -File docs-automation` separately and preserve/read its artifact.
3. Run `. tests\Run-Tests.ps1 -File create-release` separately for the publication guard regression and preserve/read its artifact.
4. Run `python -m pytest scripts/tests/test_cg_pr_preflight.py scripts/tests/test_release_policy.py scripts/tests/test_release_gate_targets.py scripts/tests/test_target_drift.py -q --tb=short`. This must now pass both drift members (`test_generated_trees_are_not_stale`, `test_generated_skill_bundles_recursively_match_canonical_files`).
5. If all focused checks pass, run unfiltered `. tests\Run-Tests.ps1` and preserve/read its artifact; require filteredFiles null for the phase boundary.

No extra Pester flags or pipeline. Return process exit where available, artifact identity, exact counts, skips, filteredFiles, bounded failure details and cleanup diagnostics. Preserve each artifact before the next Pester job overwrites last-run.json. Do not run a release, edit generated files by hand or advance the phase.

### Phase 4 REVIEW_REQUEST: Full Route (Re-confirmation)

Parent dedicated runner in the shared worktree, with cg-skill-pester-safety loaded:

1. Run `. tests\Run-Tests.ps1 -File prompt-tools` and preserve/read tests/last-run.json.
2. Run `. tests\Run-Tests.ps1 -File docs-automation` separately and preserve/read its artifact.
3. Run `. tests\Run-Tests.ps1 -File create-release` separately for the publication guard regression and preserve/read its artifact.
4. Run `python -m pytest scripts/tests/test_cg_pr_preflight.py scripts/tests/test_release_policy.py scripts/tests/test_release_gate_targets.py scripts/tests/test_target_drift.py -q --tb=short`.
5. If all focused checks pass, run unfiltered `. tests\Run-Tests.ps1` and preserve/read its artifact; require filteredFiles null for the phase boundary.

No extra Pester flags or pipeline; never overlap Pester jobs. Return process exit where available, artifact identity, exact counts, skips, filteredFiles, bounded failure details and cleanup diagnostics. Preserve results before another Pester job overwrites last-run.json. Do not run a release or advance the phase.

### Phase 4 REVIEW_REQUEST: Full Route

Parent independent reviewer: load all ten specs listed above and review Phase 4 canonical prompt, re-derived tests, docs/reference.md, generated release commands/manifests and work-report metadata. Use accepted Phase 1-3 ledgers as baseline; do not attribute their unchanged implementation to Phase 4. Inspect current create-release.ps1, receipt producer and protected source policy to check actual semantics. Focus on generic/legacy dispatch separation, exact-tag approval scope, source trust, receipt ownership and commit binding, SHA rewrite handling, required-check coverage on any source, no bypass/fallback, bounded auto-merge uncertainty, Reserve-before-docs order, both Finalize arms, resume after source advancement, evidence-only PR scope, all guard preservation and V13 rollout limits. Return all ten coverage statuses, P0-P3 findings with file/line evidence, and remaining test/evidence gaps. Confirm the three P3 wording repairs landed consistently and introduced no new issue. Do not apply fixes, weaken assertions, mutate protected assets or execute Phase 5. V7/V8 and Phase 4 closure remain pending tests and review.

## Phase 4 Final Local Closure: 2026-09-17

**Status: Success, Phase 4 only.** Steps 7-8 are complete. The final evidence
below governs local Phase 4 completion. Earlier intermediate requests, failures,
repairs and pending statements above are historical checkpoints.

### Final Evidence

- Parent focused Pester, gitSha `8bc05e51`: prompt-tools 1746 passed; docs-automation 24 passed; create-release 217 passed. All three filtered runs, each failFast false. Artifacts preserved: prompt-tools-phase4c-20260917T181952Z.json, docs-automation-phase4c-20260917T182033Z.json, create-release-phase4c-20260917T182135Z.json.
- Parent focused Python: 167 total, 164 passed, 0 failed, 3 skipped. This retained receipt regression and included all four release-policy/gate/drift surfaces; both previously failing drift members are green.
- Full Pester boundary: 3120 total, 3118 passed, 0 failed, 2 skipped (update); gitSha `8bc05e51`, ranAt 2026-09-17T18:28:18Z, passed true, filteredFiles null, failures empty. Artifact preserved: full-suite-phase4c-20260917T182818Z.json. link 94/94, unlink 33/33. Console Remove-Item noise from TestDrive teardown is a qualification only, not an assertion failure.
- Independent full-route review: 10/10 specifications complete. The only findings ever reported were three P3 readability/plan-prose advisories; all three were repaired (declared generic-mode flag rejection; receipt anchor binding `<gated-receipt-path>`; plan ordering prose) and verified. No P0-P2 finding was open at any point after repairs. Reviewer confirmed the two P2 anchor updates in tests/prompt-tools.Tests.ps1 and scripts/tests/test_release_gate_targets.py preserve semantics and parity, with no new findings.
- Manifest parity: 1502 generated files, 0 mismatches. Drift suite green.

### Completed Scope

- Canonical `.github/prompts/cg-release.prompt.md` rewritten to the clarified branch policy: explicit legacy selectors plus Step 0.5 approval parsing before dispatch with generic-mode rejection of `--auto-approve`; stable `x.y.z` sources restricted to protected remote `production_branches`/default; prerelease `x.y.z.<build>` allowed from any verified same-repository branch including dev; producer-owned LF receipt gate at the exact payload commit with a uniquely bound `<gated-receipt-path>`; bounded rebase auto-merge observation; at most one conditioned SHA-mismatch gate; per-call `-SourceBranch`/`-PreflightReceipt`; prerelease build-only and stable Pages Finalize arms; read-only result reconciliation; immutable resume and no-fallback rules retained.
- All five prompt-rewrite assertion surfaces re-derived and green; docs/reference.md legacy usage paragraph added; all adapter target commands and manifests regenerated via `python scripts/cg_generate_targets.py --all` with no drift.
- Plan and review ledgers, active state, work report updated; phase-owned review ledger captured.

### Gates And Limits

| Gate | Status | Evidence or remaining action |
|---|---|---|
| V7 | passed | Step 0.5 approval parsing; verified-source automation; bounded poll; receipt flow; prerelease/stable docs-wait branch; evidence required-checks reliance; stranded-payload repair; non-interactive resume; all five assertion surfaces green |
| V8 | passed | 1502 regenerated adapter files; drift suite green; ownership manifests 0 mismatch |
| Full Pester boundary | passed | 3118 passed, 0 failed, filteredFiles null, failures empty |
| Full review | passed | 10/10; three P3 advisories repaired and verified; no open findings |
| V13 | pending, required | Actual authorized protected controller/source-policy activation, official durable-state seeding and preview verification after step9 submission |
| Phase 5 | not started | flake root-cause, settings verification, measurement and acceptance remain outside this execution |

No live release policy or Pages change is claimed active. No shared commit, push,
PR, remote configuration write, deployment or system mutation was performed.
Existing Phase 1-3 and unrelated worktree changes are preserved. This closure
does not complete the whole plan or waive any final-stage gate.

### Closure Metadata Validation

- Wrote `completed-phases: [1, 2, 3, 4]` first, re-read and confirmed it, then moved the informational `current-phase` pointer to 5. Plan status remains active; Phase 5 was not executed.
- Plan artifact validation, handoff JSON parsing and `git diff --check` results recorded below.

## Phase 5 Resume: Flake Root-Cause, Settings Verification, Requests: 2026-09-17

**Status: In progress; Phase 5 not complete. No release, remote write, shared
commit/push/PR or completion metadata advance occurred.**

### Step 9 R7: Flake root-cause audit and documented quarantine

- Failure signature: `test_lost_response_and_unreadable_observation_remain_unknown_until_fresh_recovery [asset-package.whl]` failed once on macos-latest-py3.11 with `E_PROCESS_ARGUMENT` inside the shared `prepare()` helper (strict fake transport matrix in `release-controller-ci.yml`: os `[ubuntu-24.04, windows-latest, macos-latest]`, python `['3.11', '3.12']`).
- Audit result: `E_PROCESS_ARGUMENT` is raised only by the real `process.run_process`/`profile_process._capture` validation. In `prepare()` every GH/Git call is monkeypatched to `world.run` except `apply_edits` (reached via controller `advance` -> `prepare_step`), which executes real `git` in a `TemporaryDirectory` while mixing the strict fake clocks (`world.now` fixed start 0.0, `world.wall_time` fixed 1789171200) with a real `time.monotonic()` deadline created inside `build_worker.main`. That real-subprocess boundary is the only plausible source of `E_PROCESS_ARGUMENT` inside `prepare()`; it is order/environment dependent and was not reproducible on win32 in this environment.
- Determinism audit: fake transport time/seed inputs are already explicit and fixed (`world.now` 0.0, `wall_time` 1789171200, no randomness). No seed/time nondeterminism was found in the fake wire itself; the residual variance lives at the real `apply_edits` git boundary, so no test-side determinism change could remove it without changing production preparation semantics.
- Time-box conclusion: root-cause inconclusive after the audit; plan-mandated outcome applied: documented quarantine in
  `packages/cg-release/tests/test_phase5_transport.py` with a `@pytest.mark.skip(reason=...)` carrying the failure signature, the suspected real-process boundary, and this work-report reference. Never a silent skip.
- V9 status: passed. Runner confirmed the quarantine is stable and the package matrix stops blocking merges: transport 29 passed, 4 quarantined skips, 0 failed, 152.32 seconds, exit 0, win32, Python 3.12.

### Step 10 R6/V10: Settings verification (read-only)

- Read-only `gh api` verification performed 2026-09-17:
  - `repos/GPID-WB/compound-gpid`: `allow_auto_merge: false` (R6 requires true).
  - Rulesets: "Protect dev" (id 21338685, branch, active) present but carries only `deletion` and `non_fast_forward` rules; no `required_status_checks` and no PR review rule found. "Protect main", "Protect release tags", "Restrict release tag creation" also present.
  - Conclusion: R6 prerequisites are not satisfied; maintainer repo-settings actions are required and were not performed (no remote configuration mutation). Per the plan this is a blocked-stop for V10 and for the auto-merge design: "Required-check contexts on dev do not exist under the expected names (auto-merge would not be GitHub-enforced; stop and report instead)."
- V10 status: blocked-stop, requires authorized maintainer repo settings (Allow auto-merge; Protect dev gains the five required checks mirroring main). Superseded by the re-verification below after the maintainer action; retained as a historical checkpoint, not current status.

### Step 10 V10: PASS evidence after maintainer settings action

- The maintainer performed the required repo-settings action on 2026-09-17 at approximately 21:41Z/22:07Z (Allow auto-merge + the missing fifth required check on "Protect dev").
- Read-only re-verification via `gh api` performed 2026-09-17:
  - `repos/GPID-WB/compound-gpid`: `allow_auto_merge: true` (R6 satisfied).
  - Ruleset "Protect dev" (id 21338685, target branch, enforcement active, refs/heads/dev) now carries `deletion` and `non_fast_forward`, plus `required_status_checks` with exactly five contexts, all integration 15368, `strict_required_status_checks_policy: true`:
    1. Pester on macos-14
    2. Pester on windows-2022
    3. Native target Python gate on macos-14
    4. Native target Python gate on windows-2022
    5. PR title follows Conventional Commits
    and a `pull_request` rule with 0 required approvals and merge/squash/rebase allowed.
  - Ruleset `updated_at` was `2026-09-17T17:41:02-04:00` or later; latest verified `updated_at` `2026-09-17T18:07:26.021-04:00` (2026-09-17T22:07:26Z), consistent with the maintainer's final check addition at approximately 22:07Z.
- V10 status: passed. All five required contexts exist under the expected names and the repo allows auto-merge, so auto-merge is GitHub-enforced; no claims of V11/V12, completion metadata, or live execution are made.

### Phase 5 RUNNER_REQUEST: Focused Evidence

Parent dedicated runner in the shared worktree (local deps permitted; no release, no shared commit/push/PR, no remote config mutation):

1. Package transport quarantine stability + attempted reproduction:
   - Run: `python -m pytest packages/cg-release/tests/test_phase5_transport.py -q --tb=short` (expected: 4 skipped with the documented R7 reason, rest green).
   - Reproduction attempt without the quarantine is out of scope until the runner infrastructure has the package uv environment; if the uv env is available, optionally run the quarantined test directly against the pre-quarantine commit for comparison, but do not mutate the test file.
2. Package full matrix (if uv env available): `python -m pytest packages/cg-release/tests -q --tb=short`.
3. Full Pester boundary, unfiltered: `. tests\Run-Tests.ps1` with cg-skill-pester-safety loaded; preserve/read tests/last-run.json; require filteredFiles null and list skip names (expect the 2 known update skips).
4. Python source-policy/receipt/gate/drift surfaces: `python -m pytest scripts/tests/test_cg_pr_preflight.py scripts/tests/test_release_policy.py scripts/tests/test_release_gate_targets.py scripts/tests/test_target_drift.py -q --tb=short`.
5. Return process exit where available, artifact identities, exact counts, skips (names), filteredFiles, bounded failure details and cleanup diagnostics. Do not modify files, run a release, or advance the phase.

### Phase 5 REVIEW_REQUEST: Full Route

Parent independent reviewer (all ten specs from .kilo/agents): review the Phase 5 quarantine delta only (`packages/cg-release/tests/test_phase5_transport.py` skip marker), the V10 blocked-stop evidence recorded above, and this work-report section. Confirm: the quarantine reason is complete and non-silent; no production behavior changed; no assertion was weakened; V10 blocked-stop classification matches the plan; no completion metadata is claimed. Do not apply fixes or execute Phase 5 remainder.

### Phase 5 Full-Matrix Evidence And Workflow Contract Repair: 2026-09-17

- Full Pester boundary (V11): `. tests\Run-Tests.ps1` unfiltered with Pester
  safety loaded. Artifact: gitSha `8bc05e51`, ranAt `2026-09-17T22:16:03Z`,
  total 3118, passed 3118, failed 0, skipped 2 (both update), filteredFiles
  null, failFast false, failures empty; exit code 0; duration 6m14s. The
  immediately preceding full-suite artifact was preserved before this run,
  SHA-256 `66EFBBEE2858FC5B4EE1124C8BBB841C0D58733905BE19100EAB3E9C4B1C3E13`
  (copies at `C:\Users\wb384996\AppData\Local\Temp\7\kilo\full-suite-phase4c-20260917T182818Z.json`
  and `...\last-run-preserved-20260917.json`, verified identical). Full-suite
  TestDrive cleanup diagnostics remain a separate console qualification, never
  an assertion failure.
- scripts/tests base Python run: 2945 passed, 7 failed, 61 skipped in 662
  seconds. The seven failures included obsolete workflow-contract assertions in
  `scripts/tests/test_legacy_pages_security.py` that predated the Phase 3/4
  workflow changes.
- Workflow contract repair (re-derived pinned Pages contract, no assertion
  removed to hide a failure):
  - Protected checkout plus no `--all` over all jobs: each job carries exactly
    one root checkout pinned to `${{ github.sha }}` with
    `persist-credentials: false`, and no job runs `rebuild-docs.js --all`.
  - `deploy` and `deploy-dev` remain the only `deploy-pages` users and keep
    `steps[-2]` as the fresh authority/snapshot recheck step and `steps[-1]`
    as `actions/deploy-pages@`.
  - New classify-job protected-gate test
    (`test_legacy_classify_gate_runs_protected_code_without_deployment_permissions`)
    pins the `classify` job: no deployment permissions or surface (permissions
    contents: read and actions: read only; no `environment`; no
    `deploy-pages`/`download-artifact`/`upload-pages-artifact` steps; no
    `legacy-pages.js` execution), the classification step
    (`node scripts/release-version.js --full-site-tag`) as the final step,
    `jobs['deploy']['needs'] == 'classify'`, and the deploy `if` conditioned
    on `needs.classify.outputs.full_site == 'true'`.
  - `scripts/evidence/tests/release-pages.test.js` anchors re-derived from the
    obsolete `--legacy-docs-branch` assertions to `--resolve-source` and the
    shared `assertReleaseSource` validator.
  - After the repair `scripts/tests/test_legacy_pages_security.py` passes 5/5.
- Full scripts/tests rerun after the repair: 2947 passed, 61 skipped, 6 failed.
  All six failures are `ModuleNotFoundError: No module named 'semver'` in
  `scripts/tests/test_release_controller_profile.py` — an environment artifact
  of the base Python environment (the dependency lives in the cg-release uv
  environment); the same module passes 7/7 under `uv` in `packages/cg-release`
  in 0.37 seconds. No production or workflow change is implicated.
- Package matrix under uv:
  `python -m pytest packages/cg-release/tests -q --tb=short`: 1010 passed,
  0 failed, 5 skipped (4 with the documented R7 quarantine reason and 1 symlink
  skip) in 1379 seconds, exit 0.
- Native preflight: not re-run in Phase 5. The Phase 1 snapshot acceptance
  evidence (one complete committed nine-command native gate, all exit 0,
  receipt verifier and isolated PowerShell acceptance) remains the governing
  native-gate coverage; the full-matrix Pester/Python surfaces above
  re-exercise the same preflight commands.

## Phase 5 Final Evidence And Closure: 2026-09-17

**Status: The Phase 5 local verification surface is final. The whole-plan final
gate V12 remains pending. No release, remote write, shared commit/push/PR,
deployment or completion metadata advance occurred.**

Earlier intermediate requests, pending statements and the V10 blocked-stop
checkpoint in this section are historical and are superseded by the final
evidence here.

### Final Evidence

- V9: passed (recorded above). The R7 flake root-cause audit concluded with a
  documented quarantine marker in `packages/cg-release/tests/test_phase5_transport.py`;
  the focused rerun passed 29, skipped 4, failed 0 in 152.32 seconds, exit 0,
  win32, Python 3.12, and the full package matrix below confirms quarantine
  stability (4 R7 skips).
- V10: passed (recorded above). Maintainer repo-settings action on 2026-09-17
  (approximately 21:41Z/22:07Z); read-only `gh api` re-verification confirms
  `allow_auto_merge: true` and "Protect dev" (ruleset id 21338685) carries
  exactly the five required checks (Pester macos-14/windows-2022, Native
  target Python gate macos-14/windows-2022, PR title follows Conventional
  Commits; integration 15368; strict required-checks policy true; pull_request
  0 approvals, merge/squash/rebase), latest verified `updated_at`
  `2026-09-17T18:07:26.021-04:00`.
- V11: passed. Full matrix green per the evidence above: unfiltered Pester
  3118 passed, 0 failed, 2 update skips, exit 0, 6m14s (gitSha `8bc05e51`,
  ranAt `2026-09-17T22:16:03Z`, pre-artifact preserved with SHA-256);
  `scripts/tests` after the contract repair 2947 passed, 61 skipped with the
  only six failures being the semver environment artifact (7/7 under uv in
  0.37s); `packages/cg-release` uv matrix 1010 passed, 0 failed, 5 skipped in
  1379 seconds. Native preflight coverage references the Phase 1 snapshot
  acceptance evidence; it was not re-run.
- V12: pending, required. Maintainer-authorized live acceptance run
  `/cg-release v1.2.0.9020 --auto-approve` from a clean dev checkout with the
  segmented timing record, NOT executed. This remains the whole-plan final
  gate; V11 evidence does not substitute for it.
- V13: pending, required. Protected controller/source-policy activation,
  official durable-state seeding and preview verification after step9
  submission; unchanged from the Phase 3/4 closures.
- R9: the after-side measurement (payload commit to published+attested at or
  under 45 minutes; invocation to evidence merged at or under 90 minutes) is
  part of the V12 acceptance run and remains pending with it; the before-side
  session data remains recorded in the brainstorm.
- No independent full-route review outcome for the Phase 5 delta is claimed;
  none was supplied. The evidence above is executed results, not review
  outcomes.

### Gates And Limits

| Gate | Status | Evidence or remaining action |
|---|---|---|
| V9 | passed | Documented R7 quarantine; focused and full matrix runs stable (4 R7 skips), no failures |
| V10 | passed | Read-only `gh api` verification after the maintainer action; five required checks present, auto-merge allowed |
| V11 | passed | Full matrix evidence above: Pester 3118/0/2 update skips exit 0 6m14s; scripts/tests 2947 passed with only the semver env-artifact failures (7/7 under uv); package uv matrix 1010 passed, 0 failed, 5 skipped |
| V12 | pending, required | `/cg-release v1.2.0.9020 --auto-approve` acceptance run, not executed; whole-plan final gate |
| V13 | pending, required | Step 9 submission and protected activation, not executed |

No whole-plan completion is claimed. Plan frontmatter intentionally remains
`completed-phases: [1, 2, 3, 4]` and `current-phase: 5`; the plan stays active
until V12/V13 clear. Timestamps in the report, active state and review ledgers
are 2026-09-17.

### Closure Metadata Validation

- Plan artifact validation passed:
  `python scripts/render_artifact.py --validate-only .cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md`.
- Active-state JSON re-read and parsed with `python -m json.tool`; `currentPhase`
  remains 5; `completed-phases` remains [1, 2, 3, 4]; evidence statuses updated:
  V9, V10 and V11 passed; V12 pending; V13 pending. No completion-5 write.
- `git diff --check` passed.
- No shared commit, push, PR, remote configuration write, deployment, system
  install or Git config mutation was performed. Existing Phase 1-4 and
  unrelated worktree changes are preserved.

## Deploy Gate Contract Fix: 2026-09-18 (User-Approved Deviation)

- **Approved deviation**: the user explicitly approved updating
  `scripts/check-docs-site.js` and `scripts/tests/check-docs-site.test.js` to the
  durable-official-snapshot `deploy-dev` contract and including both files in the
  PR. The PR to dev was blocked because the gate still demanded the obsolete
  Phase 1/2 tokens (`ref: main`, `path: sources/main`, `--main-root sources/main`,
  `branches/main`), while Phase 3 rewrote `deploy-dev` to restore-official /
  stamp-preview / recheck-official with no main checkout.
- Re-derived the `deploy-dev` assertions to the reviewed Phase 3 workflow
  (`.github/workflows/release-pages.yml`):
  - `ref: ${{ steps.authority.outputs.release_sha }}` with `path: sources/dev`
    remains the exact dev SHA binding (exact-run archive digest and authority
    artifact id were already asserted by the shared per-job token set).
  - Official snapshot root is now `official-source` via
    `node scripts/legacy-pages.js restore-official official-source official-state.json`
    (durable `cg-official-snapshot.json` bytes restored from the current
    protected Pages deployment, then carried through `official-state.json`).
  - Composition root is `--main-root official-source --dev-root sources/dev`
    with `import-dev sources/dev dev-artifact` unchanged.
  - Preview stamping requires
    `node scripts/legacy-pages.js stamp-preview official-state.json combined-artifact`.
  - Post-upload pre-deploy recheck requires
    `node scripts/legacy-pages.js recheck-official official-state.json` in
    addition to the existing fresh `legacy-pages.js check` and the dev-branch
    tip check (`branches/dev" --jq .commit.sha)`, `branches/main` assert dropped).
  - New negative guard: `deploy-dev` must not contain `ref: main`,
    `sources/main` or `branches/main` ("never a moving main checkout").
  - The release `deploy` job now also must keep
    `node scripts/legacy-pages.js seal-official release-source release-artifact`,
    because it produces the durable official snapshot that `deploy-dev`
    restores; removing the seal breaks the P1.2/P1.4/P1.5 preview chain.
  - Every preserved guard is unchanged: protected controller checkout
    (`ref: ${{ github.sha }}`, `persist-credentials: false`), no
    `rebuild-docs.js --all` or mutable-source execution, `legacy-pages.js check`
    before download and again after upload before `deploy-pages`,
    `archive "$ARTIFACT_ID" "$ARTIFACT_DIGEST"` digest verification, and
    upload-before-deploy ordering.
- Updated `scripts/tests/check-docs-site.test.js`:
  - Repaired three anchors that no longer matched the Phase 3 workflow
    (`- name: Deploy development preview to GitHub Pages` + `uses:
    actions/deploy-pages@` for the dev deploy variant; deploy-job-unique
    checkout block for the mutable-controller variant; the full post-upload
    recheck body for the missing-cutover variant).
  - Added negative cases: missing restore-official, missing seal-official on the
    release deploy, missing stamp-preview, missing recheck-official, stale
    `ref: main` dev checkout, and wrong composition root
    (`--main-root sources/main`).
- Evidence (this thread, shared worktree):
  - `node --test scripts/tests/check-docs-site.test.js`: 26 passed, 0 failed,
    0 skipped in ~6s (baseline before the fix: 12 passed, 8 failed).
  - `node scripts/check-docs-site.js`: exit 0,
    "Documentation site check passed (76 navigable Markdown pages, 8 groups,
    complete skills catalog)". Baseline before the fix:
    "deploy-dev must reference ref: main." and nonzero exit.
  - Regression `node --test scripts/tests/legacy-pages.test.js
    scripts/tests/release-version.test.js scripts/evidence/tests/release-pages.test.js
    scripts/tests/docs-snapshots.test.js`: 67 passed, 0 failed, 0 skipped.
  - `python -m pytest scripts/tests/test_release_gate_targets.py
    scripts/tests/test_legacy_pages_security.py -q --tb=short`: 13 passed,
    3 skipped (known skips), 0 failed in 98.63s. Neither file references
    `check-docs-site`; run as a release-pages.yml contract regression guard.
- RUNNER_REQUEST (parent, Pester safety loaded; never run Pester in this
  thread): `tests/docs-automation.Tests.ps1` and `tests/docs-preview.Tests.ps1`
  reference `scripts/check-docs-site.js` (docs-automation path filter line 22
  and pages.yml gate invocation at line 39; docs-preview re-derived workflow
  assertions). Run `. tests\Run-Tests.ps1 -File docs-automation` and
  `. tests\Run-Tests.ps1 -File docs-preview` separately, preserving
  `tests/last-run.json` between runs, and return identities, counts,
  filteredFiles, failures and cleanup diagnostics.
- No commit, push or PR was performed; no remote writes; no main-branch action.
  The changed gate files are ready for the step9 commit/push/PR.
