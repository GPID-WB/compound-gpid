---
date: 2026-09-13
type: verification
depth: scoped
status: verified-in-scope
parent-review: .cg-docs/reviews/2026-09-13-generic-asynchronous-release-controller-phase6-P1.15-helper-verification.md
prior-full-review: .cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase6-repair2-verification.md
handoff: .cg-docs/work-reports/release-controller/2026-09-12-phase6-handoff.json
repair: .cg-docs/work-reports/release-controller/2026-09-13-phase6-P1.15-continuations-repair.json
validation: .cg-docs/work-reports/release-controller/2026-09-13-phase6-P1.15-continuations-040753Z-validation.json
plan: .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md
phase: 6
phase-complete: false
review-route: [cg-code-quality, cg-testing]
coverage:
  audit-rows-requested: 15
  audit-rows-assessed: 15
  audit-rows-confirmed: 15
  requested-repairs: 1
  confirmed-repairs: 1
  remaining-open: 0
  new-findings: 0
  unverified-repairs: 0
  prior-confirmed-preserved: 41
  total-confirmed: 42
active-severity:
  P0: 0
  P1: 0
  P2: 0
  P3: 0
findings:
  P1.15: fixed
---

# Phase 6 P1.15 Finite Continuation Verification

**Verdict: P1.15 is confirmed fixed within the requested finite audit. No remaining or new finding was identified.** All 15 rows in the continuation repair record were assessed, not only pending registration. Fresh checks used real authority functions and controller/journal paths, with bounded fake provider and storage boundaries. The applicable principals were rejected before the next separately started operation after revocation. Authorized prefixes, exact tickets, and unresolved intents were retained.

**Counts: 1 repair confirmed, 41 prior confirmations preserved, 42 total confirmed, 0 open, 0 new, 0 unverified.** This result does not complete Phase 6, V6, or external qualification. The original finding maps, handoff, counters, phase state, and all earlier reports remain unchanged. Draft P1.21 stays absorbed by P1.13. P1.8 retains its prior P2 severity and P2.12 its prior P1 severity.

## Review Method

The two requested specs were loaded and applied sequentially in this session: `cg-code-quality` first, then `cg-testing`. No child or Agent Manager session was created. Independent file reads were parallel where useful; review analyses and test runs were sequential.

The code-quality pass traced current callers, callback contents, helper ordering, idempotent paths, and bounded journal operations. It found no separate source-quality issue in this scope. The testing pass inspected the regression fixtures, ran the 62-test finite repair matrix, added independent scratch probes at uncovered negative boundaries, and ran 94 adjacent-control tests. Static callback presence was not accepted as sufficient authorization proof.

Project instructions, local configuration, Python guidance, the pytest skill workflow, saved project context, and the local mock-target-drift solution were consulted. No open-brain service tool was available. No project-memory write was requested or made.

## Complete Audit

Row numbers below follow the repair JSON's `audit` array exactly. Source paths are relative to `packages/cg-release/src/cg_release/`. Test paths are relative to `packages/cg-release/tests/`, except the independent scratch file identified below. All test evidence in this table was executed in this review. The retained full package gate supplies additional coverage, not substitute negative proof.

| Row | Path And Current Boundary | Verification Result |
|---|---|---|
| 1 | `profile_worker.register`, `profile_worker.py:93-101` | Confirmed. Pre-reconciliation authority remains; a new check follows dispatch-result save before registration. Existing requester/resumer cases and three independent pending-registration probes preserve the exact dispatch result, ticket, and transaction prefix. Both revoked actors are denied with no registration append; the positive control claims run 55 with the exact ticket digest. |
| 2 | First absence in `profile_dispatch.recover_dispatch`, `profile_dispatch.py:67-82` | Confirmed. Empty inventory precedes authority; uncertain dispatch reconciliation is followed by another check before absence-first. Six existing inventory/dispatch-result cases cover both principals and positives. Independent first-absence cases also cover the no-intent branch. Revocation preserves either the pending intent or the completed uncertain result, with no absence-first write. |
| 3 | Remaining dispatch recovery, `profile_dispatch.py:83-106` | Confirmed. New absence and terminal evidence each have fresh authority. Independent cases cover repeated absence, already-recorded absence, terminal run, pending run, and propagation wait for requester/resumer plus positive controls. Waits remain read-only; four revoked-wait cases return pending without writes and an immediate authority control rejects the actor. Existing two-observation, evicted-run, retry-budget, and absence re-entry tests also pass. |
| 4 | `profile_dispatch.dispatch`, `profile_dispatch.py:121-151` | Confirmed. Checks precede intent, POST, and the separate dispatch-result acknowledgement. Six independent intent-return/POST-return cases plus existing regressions cover both principals and positives. Revocation after intent makes no POST; revocation after accepted POST leaves the durable intent and omits the result. No authorized prefix is undone. |
| 5 | `profile_docs.docs_step`, `profile_docs.py:98-116` | Confirmed. Namespace intent and result receive real callbacks; authority is renewed before composition creation. Six existing namespace cases test both checkpoint completions. Three independent create-to-dispatch cases confirm that a completed composition create does not authorize the next dispatch intent: the created ticket remains, with no dispatch after revocation. |
| 6 | Composition and final deployment, `profile_worker.py:125-140,191-201`; `profile_deploy.py:24-45` | Confirmed in scope. Current-ticket reads precede authority at local materialization and composition-result save. Four existing real-composition negatives cover both principals and both ticket reads. The actual successful lifecycle, final run/metadata/policy/manifest tests, admitted-grant test, and connected canonical/installed workflow replay pass. The bounded credential-free local composition stage is not redefined as multiple privileged remote operations. No Bash or Pages action was executed by the probe. |
| 7 | `profile_evidence_inputs.evidence_inputs`, `profile_evidence_inputs.py:19-79,83-96` | Confirmed. The real `authorize_attempt` checks current record/grant selection, then final human authority. Both input checkpoint operations receive it. Existing inputs-intent negatives preserve intent and deny the result for requester/resumer; positives seal exact inputs. Fresh explicit-base, deleted-source, and preserved-old-evidence lifecycle coverage retains the grant binding. |
| 8 | `profile_evidence.evidence_step`, `profile_evidence.py:103-157` | Confirmed. Base reads precede authority; PR result is separately reauthorized after ensure; both normal and existing-PR binding checkpoints receive the real callback. Existing PR-created, PR-result, and binding-intent negatives pass. Twelve independent interruption/re-entry cases test an actual saved PR result followed by existing-PR read or binding-intent revocation, for ordinary requester, ordinary resumer, and admitted maintainer. All reject the next write, preserve the PR/input prefix, and create no duplicate PR; positive controls finish both binding operations. |
| 9 | `PreparationRemote.write` and merged evidence return, `preparation_remote.py:65-94,168-245`; `profile_evidence.py:158-180` | Confirmed. Each allowlisted POST calls the real freshness callback after intervening object/ref/PR reads. Twelve independent cases revoke after a completed blob, tree, commit, or ref POST and deny the next POST, retaining the PR intent and completed remote prefix. PR-POST-to-result is covered in row 8. Three independent final merged-blob-read cases test the final `authorize_attempt`: revoked principals receive no verified return, while the positive returns exact verified evidence. All are read-only at that final boundary. Eight valid-docs/invalid-evidence controls and the all-nine-output successful lifecycle pass. |
| 10 | Published-owner recovery, `recovery.py:133-161`; `publication_control.py:83-131` | Confirmed. `finish_published` passes real fresh authority into `release_owner`; the helper calls it after its owner/state reads and before its atomic checkpoint. Existing terminal-run/credential-expiry cases use a real interrupted publisher owner. Three independent cases delay the helper's second owner/state read. Requester/resumer revocation prevents owner release and all further writes; the positive releases the owner and can continue hooks. |
| 11 | Hook completion, `recovery.py:86-119,164-172` | Confirmed. Applicable actor is retained; final current-record read precedes callbacks for completion intent and result. Six existing actual-deployment-read/completion-intent cases cover both principals and positives. Revoked cases remain published and do not add `publication-hooks`; an authorized completion succeeds only after actual exact hook verification. |
| 12 | Required-hook sealing, `hook_authority.py:13-41`; `build_stage.py:118-121` | Confirmed. Six independent probes call actual `build_step` from a real pre-seal building state. Requester/resumer revocation during the callback's state read prevents intent; revocation after requirement intent prevents result and later build tickets. Positive controls seal `docs,evidence` and continue. Original requirement/profile-removal and pre-receipt-tag recovery controls also pass. No permission stub is used. |
| 13 | Native source registration, `build_worker.py:143-167`; `build_control.py:41-115` | Confirmed. The actual worker supplies fresh callbacks for dispatch reconciliation and the one-shot claim after current-ticket reads. Four existing late-run/dispatch-result cases and two independent current-ticket-read cases run `build_worker.main`. Revocation denies registration, retains the reconciled dispatch and exact ticket, and emits `E_AUTHORITY`; positive controls register. Direct storage-only helper tests are not treated as authorization proof. |
| 14 | Stranded/source-exception continuations, `stranded_recovery.py:226-279` | Confirmed. Reviewed maintainer checks follow lineage before admission, follow record read before a source-exception grant, and precede the separate audit. Existing admission-to-audit and source-exception read/result cases pass. Independent final-lineage positives/negatives verify no admission after revocation, exact tag identity, and no publication writes. Independent audit-history/retry cases additionally exercise the real maintainer callback, not only its presence. |
| 15 | Restore and recovery audit, `recovery_actions.py:120-170`; `recovery_audit.py:37-85` | Confirmed. Pre-restore authority remains; verified restore read-back cannot authorize the later audit. Existing restore-return negatives preserve the completed non-force restore with no audit. Independent cases revoke after audit history reads and after a valid sibling causes one CAS retry. The next append attempt is denied, the sibling/prefix remains, and positive controls append one audit. Exact existing audit replay makes no new append or callback. Missing/corrupt/divergent and non-force fast-forward controls pass. |

The wiring test has ten parameter groups covering **eleven call expressions**: `profile_evidence.py` has two checkpoint callers. Each supplies a non-constant callback. This count clarifies the repair record's shorthand description of ten sites; it is not another finding.

## Atomicity Limit

The review requires a new applicable authority observation before each separately started continuation operation after intervening reads or a completed operation. It does **not** require atomic permission checks across principals, an atomic transaction between GitHub permission reads and GitHub effects, a permission lease, or an endless check loop.

Reads, CAS attempts, and read-back within an already-started journal operation remain part of that bounded operation. A principal can change after the last observation or during an already-started operation. The tested finite repair does not claim to prevent that. The explicit recovery-audit loop separately renews its callback before each append attempt, as its current contract states. Completed authorized prefixes and unresolved intents remain durable and are not undone.

The final workflow still compares manifest, dev, and latest stable before `authorize-deploy`, then immediately enters the default-success `deploy-pages` step. `hook_authority.py:71-85` still finishes repository/default reads before the final human-authority phase. These repairs remove the observed continuation gaps without promising atomic GitHub authorization.

## Fresh Evidence

All files in this section are under `C:/Users/wb384996/AppData/Local/Temp/3/kilo/`. They were written to distinct paths. The final successful artifacts were read again after the transport-reset notice; completed commands were **not replayed**.

| Selection | Result | Evidence File |
|---|---|---|
| Existing finite repair matrix | 62 passed, 0 failed/errors/skipped; 301.78 seconds | `phase6-finite-existing-20260913-0450.xml` |
| Final independent finite probes | 78 passed, 0 failed/errors/skipped; 307.16 seconds | `phase6-finite-probes-final-20260913-0450.xml` |
| Adjacent authority, workflow, recovery, evidence, and lifecycle controls | 94 passed, 0 failed/errors/skipped, 1 deselected; 414.63 seconds | `phase6-finite-adjacent-20260913-0450.xml` |
| Disabled workflow installation | Exit 0 | `packages/cg-release/.venv/Scripts/python.exe -B scripts/release_profile_install.py --check` |
| Protected payload/attestation history | Exit 0, empty diff | `git diff --exit-code -- releases .github/shared/skill-management/release-attestations` |

**Independent probe source:** `C:/Users/wb384996/AppData/Local/Temp/3/kilo/test_phase6_finite_independent_20260913_0450.py`.

The 78 final independent cases comprise **44 late-revocation denials, 4 read-only revoked waits, and 30 authorized positive cases**. Denial cases check the real authority error and an immediate real-authority negative control, with no control-induced journal change. Native-worker cases also check the structured worker error. Exact transaction prefixes and relevant ticket/intent/result identities are asserted. The JUnit file retains per-case boundary observations; detailed GET/append traces are included for the memory-worker cases. It is not a full provider transcript for every lifecycle case.

The existing matrix selection is `test_hook_save_continuations.py`, `test_hook_checkpoint_continuations.py`, `test_recovery_registration_continuations.py`, `test_hook_continuation_wiring.py`, and `test_module_bounds.py`.

The adjacent selection is `test_hook_authority_boundary.py`, `test_profile_security.py`, `test_profile_workflow_authority.py`, `test_profile_dispatch.py`, `test_profile_evidence_lifecycle.py`, `test_profile_policy_recovery.py`, `test_profile_lifecycle.py::test_real_lifecycle_requires_exact_committed_evidence_and_deployment`, `test_recovery_actions.py`, `test_stranded_recovery.py`, `scripts/tests/test_legacy_pages_security.py`, and `scripts/tests/test_release_controller_profile.py`. Only `test_repeated_actual_refreshes_do_not_grow_release_record` was deselected from this bounded adjacent run; it remains covered by the retained full package gate. No audit row was omitted.

### Preserved Probe Failures

The preliminary lightweight run passed 37 cases, with 31 deselected and 37 JUnit `record_property`/xunit2 warnings. Its XML remains `phase6-finite-light-20260913-0450.xml`. The final run used xunit1 and had no warning summary.

The first lifecycle probe run recorded **26 passed and 5 failed**, with 37 deselected, in `phase6-finite-lifecycle-20260913-0450.xml`. These failures were in the independent harness, not reproduced source defects:

- Four existing-PR cases matched an unencoded `release-controller/` path while the outer boundary used an encoded ref. Both positive controls reported an unfired trigger; the negatives therefore had not revoked authority. The scratch trigger now decodes the observed endpoint before matching.
- One native-ticket negative matched an older historical dispatch result before the new pending dispatch had been reconciled. It correctly rejected earlier than intended. The scratch trigger now uses the latest request event, requires a cleared intent, and excludes the active result operation.

Only the scratch probe was corrected. No repository source/test code changed, and the failed XML remains unchanged. The complete final run covers all corrected cases, adds ordinary-requester binding recovery and create/merged-read boundaries, and passes 78/78. Preliminary runs and overlapping suites are not added as unique coverage.

### Execution Limits

Pytest used the existing package interpreter, `-B`, `-p no:cacheprovider`, and new external `--basetemp`/JUnit paths. Ambient `GH_TOKEN`, `GITHUB_TOKEN`, `GH_ENTERPRISE_TOKEN`, and `GITHUB_ENTERPRISE_TOKEN` were removed from each test process without reading or logging their values. Existing offline fixtures supply their own scoped synthetic credentials.

Independent probes substitute only outer provider/store/process/time boundaries, not authority functions, grants, journal transitions, or verification results. Their test process denies socket connections and nonlocal process commands. Local Git, fixed installed Node helpers, and a no-isolation scratch wheel build are allowed for real lifecycle fixtures. Existing selections also use their inspected fake providers. This is not OS-wide network-denial proof, live Bash/Pages execution, remote credential qualification, or a full distribution/clean-client test.

## Retained Gates

The validation recorded at `2026-09-13T04:47:53Z` supersedes the older handoff's pending-gate statement. The validation, exact prepare analysis, decoded package/profile/lint/build command results, and captured Pester last-run artifact were read. No full gate or Pester command was rerun by this reviewer.

| Gate | Latest Recorded Result | Retained Qualification |
|---|---|---|
| Prepare | 9 selected, 9 executed, 9 passed; 0 failed/unexecuted | Exact argv match in order. Prepare mode, not reviewed committed-candidate validation. |
| Package | 952 passed; 0 failed/errors/skipped | Complete final summary at `continuations-040753Z-prepare-commands.log:102`, not inferred progress. Earlier 951/1 package XML remains unchanged. |
| Native | 2,592 passed, 50 skipped, 2 deselected, 1 warning | Individual skip names/reasons are absent from the exact `-q` result. Unsafe-hard-link exclusion warning remains. |
| Profile/launchers | 28 passed; 0 failed/skipped | Complete summary at decoded command log line 111. |
| Pester | 2,935 passed, 0 failed, 2 skipped; `filteredFiles: null`; 21 files | Captured at `04:11:51Z`. TestDrive `DirectoryNotFoundException` and nonempty-directory cleanup errors remain. Both skips are in `update`; individual names/reasons are absent. |
| Ordinary Node | 106 passed, 0 failed/skipped | Portable Windows file-link Dirent boundary on EPERM, not native file-symlink qualification. |
| Plan/parity | 56 passed, 0 failed, 8 skipped | Named POSIX command-shim/update groups are unavailable on Windows. |
| Modules/lint/build | Three module checks, Ruff, wheel and sdist passed | Complete retained command results; not new independent host qualification. |

The exact validation path is `.cg-docs/work-reports/release-controller/2026-09-13-phase6-P1.15-continuations-040753Z-validation.json`. Referenced gate filenames use the same directory and `2026-09-13-phase6-P1.15-` prefix. Pester's Windows Bash result remains a placeholder. Existing quiet/fixture warnings, intentional missing-target-mapping failure-boundary diagnostic, and mixed CLIXML/raw stderr qualification remain as recorded. This review did not reparse the full Pester stderr. Missing details are not inferred or relabeled as clean-host proof.

## Preservation And Phase

The 41 prior confirmations, their evidence limits, severity qualifications, and deduplication remain as recorded in the unchanged full repair2 report and subsequent scoped reports. They are preserved, not relabeled as 41 newly executed proofs. Adjacent checks confirm current policy/run/ticket/manifest guards, immutable hook requirements, exact canonical/native/ownership evidence, one-shot registration, bounded absence/retry recovery, and disabled workflow parity.

HEAD remains `b94f585c8a485dfb03965ca9711fb83257aaa7de` on `improve-cg-release`. Worktree path states before this report match those inspected at entry. The candidate remains uncommitted; the source freeze and path-state checks are not a complete cryptographic identity of dirty contents.

This distinct report is the reviewer's only manual worktree write. Probe source and reports are outside the worktree. No source or repository test edit, prior evidence overwrite, canonical regeneration, handoff/counter/state edit, real credential lookup, live remote operation, setting/secret change, activation, publication, deployment, commit, push, PR, or new Agent Manager session was performed. The controller remains disabled.

**Phase 6 remains incomplete.** This report closes only P1.15 within the finite audit. It does not mark V6 complete or external-only, reset a counter, or authorize Phase 7. Native Unix/Python 3.8 execution, supported-host file-symlink qualification, authorized bridge delivery and clean-client proof, exact source-bound six-cell CI and registered native/profile producer identities, reviewed committed-candidate validation, and real bootstrap/App/controller/journal/protected-setting authority remain separate requirements.
