---
date: 2026-09-13
type: verification
depth: scoped
status: changes-required
parent-review: .cg-docs/reviews/2026-09-13-generic-asynchronous-release-controller-phase6-P1.15-final-verification.md
prior-full-review: .cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase6-repair2-verification.md
handoff: .cg-docs/work-reports/release-controller/2026-09-12-phase6-handoff.json
repair: .cg-docs/work-reports/release-controller/2026-09-13-phase6-P1.15-helper-repair.json
validation: .cg-docs/work-reports/release-controller/2026-09-13-phase6-P1.15-helper-010024Z-validation.json
plan: .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md
phase: 6
phase-complete: false
review-route: [cg-code-quality, cg-testing]
coverage:
  requested-repairs: 1
  confirmed-repairs: 0
  remaining-open: 1
  new-findings: 0
  unverified-repairs: 0
  prior-confirmed-preserved: 41
  total-confirmed: 41
active-severity:
  P0: 0
  P1: 1
  P2: 0
  P3: 0
findings:
  P1.15: open
---

# Phase 6 P1.15 Shared Helper Verification

**Verdict: Changes required.** The shared helper correction and the stated composition, evidence-base, and dispatch-intent ordering changes are confirmed within the tested boundaries. P1.15 remains open because the pending-dispatch registration path performs a second journal operation without rechecking authority after the first operation. Two fresh offline counterexamples reproduce this for the requester and resumer. This is another boundary of P1.15, not a new finding ID.

**Counts: 41 confirmed, 1 open, 0 new findings.** The 41 prior confirmations are preserved, not independently re-proved by this scoped pass. No original finding map, handoff, counter, phase state, or prior evidence file was changed. Phase 6 remains incomplete.

## Remaining Finding

### P1.15: Pending Dispatch Reconciliation Outlasts Registration Authority

**[P1]** `packages/cg-release/src/cg_release/profile_worker.py:93-100`.

**Issue:** When a composition has a durable dispatch intent, `register()` executes this sequence:

1. At line 93, call the corrected `authorize_hooks(..., fresh=True)`.
2. At lines 94-97, validate the existing intent and save its dispatch result with `store.save(item, "dispatch", payload)`.
3. At lines 98-100, call `store.save(item, "registration", ...)`, with no human-authority check between the two saves.
4. Return the sealed ticket as successful registration.

Each `save()` is a separate authenticated journal operation. `composition_journal.py:157-220` performs state acquisition, validation, CAS append, and read-back. The second save cannot use the first save as a human-permission grant. A requester or resumer can lose authority during dispatch-result reconciliation while the ticket, policy, repository, and run remain valid. Registration is then appended using the earlier permission result.

This branch handles a real pending-intent state. For example, GitHub can accept a workflow dispatch before the dispatch caller records its result. `profile_dispatch.py:119-148` seals intent before POST and records dispatch afterwards; `register()` explicitly supports reconciling that intent. The probe creates this valid state through the real `CompositionJournal.intent()`, rather than inserting an invalid journal record.

**Fresh proof:** An independent scratch probe uses the existing GET-only worker fixture, real `Journal`, real `CompositionJournal.intent()` and both `save()` calls, real `GitHubReads`, and real `register()`. It changes only outer provider/storage boundaries. After the dispatch-result append returns, the storage wrapper changes the selected synthetic actor's role to `read`. The dispatch save completes, then the separate registration save begins. No permission read occurs after revocation and before registration.

| Case | Observed Result | Control |
|---|---|---|
| Requester 456 revoked during dispatch-result save | Registration accepted; dispatch and registration results appended | Immediate real helper call rejects with `E_AUTHORITY` |
| Resumer 8 revoked during dispatch-result save | Registration accepted; dispatch and registration results appended | Immediate real helper call rejects with `E_AUTHORITY` |
| No revocation | Pending intent reconciled and exact registration accepted | Real helper continues to authorize |

Both counterexamples assert that the original transaction prefix, including event bytes, is unchanged and that exactly two results are added. They assert the exact registration run and ticket digest. Their recorded call traces end with dispatch append return, revocation, registration append entry, and registration append return, with no intervening permission GET. An immediate negative control changes no journal bytes.

The production registration step is connected to the dependent dev-preview job at `packages/cg-release/templates/gpid-docs.yml:65-72`. This proves acceptance and a journal write at the wrong registration boundary, not an unauthorized Pages deployment. Later composition and deployment authority checks remain and can reject a revoked actor. No Bash step, source job, or Pages action was executed by the independent probe.

**Required correction:** Keep the pre-reconciliation authority check. After reconciling a pending dispatch, repeat the corrected helper immediately before the separate registration save. Preserve the exact ticket object, policy/run/intent validation, CAS checks, and prior dispatch evidence. Add requester/resumer negative tests for the pending-intent branch, with an authorized positive control. The existing registration metadata/run tests start without a pending dispatch intent, so they do not cover this branch.

This missing negative coverage belongs to P1.15. It is not counted as a separate testing finding.

## Atomicity Limit

GitHub identity reads, permission reads for different principals, journal CAS operations, and later external effects are separate observations and operations. This report does not require atomic authorization across them. It makes no guarantee against a change after the last observation, during another principal's check, or inside one already-started CAS operation.

The remaining issue is narrower: a complete dispatch-result save is followed by a separate registration save, with no renewed authority check between those operation calls. Adding that finite boundary check does not require an impossible atomic GitHub transaction or an endless permission-check loop. The helper documentation at `hook_authority.py:48-55` correctly states the non-atomic limit.

## Sequential Review

The requested specs were loaded and applied in order, sequentially in this independent session. No Agent Manager or internal reviewer session was created.

| Order | Spec | Completed Scope |
|---|---|---|
| 1 | `cg-code-quality` | Read shared helper, ordinary/recovery authorization, exact grant validation, deployment worker, registration, composition, evidence attempt/base callback, dispatch, journal operations, preparation writes, and canonical/installed workflow boundaries. Confirmed the helper ordering correction and identified the two-save registration branch for a bounded probe. No separate style finding. |
| 2 | `cg-testing` | Read the changed regressions, fixtures and transport boundaries, recovery admission, connected workflow replay, current-ticket interleaving, and retained gate records. Ran the 62-test scoped selection, then 11 independent probe assertions. Confirmed helper rejection and reproduced the registration residual. |

Project instructions, local configuration, Python guidance, and the Python testing workflow were applied. Saved project context and the local mock-target-drift solution were consulted. No open-brain service tool was available. No memory write was requested or performed. This is not a repeat of the earlier ten-spec review.

## Boundary Coverage

Package source paths below are relative to `packages/cg-release/src/cg_release/`. Test paths are relative to `packages/cg-release/tests/` unless stated otherwise.

| Boundary | Result And Evidence |
|---|---|
| Final helper repository/default reads | Confirmed. `hook_authority.py:68-82` finishes repository ID/default name and protected-default SHA checks before `authorize_record()`. Four independent deployment negatives and four independent registration negatives revoke requester/resumer during either final metadata read and reject with `E_AUTHORITY`, leaving all transactions unchanged. |
| Ordinary authority and optional freshness | Confirmed in scope. `authority.py:11-31,55-82` still validates immutable user identity and current write/maintain/admin authority. Fresh `test_hook_authority_boundary.py:44-54` covers both `fresh=False` and `fresh=True`, including the permission-read tail. No authority cache was added. |
| Policy mismatch guards | Confirmed. Fresh cases at `test_hook_authority_boundary.py:57-85` reject changed repository ID, default branch, protection, and policy SHA without journal writes. Bound policy and enabled checks remain at `hook_authority.py:57-62`. |
| Admitted recovery authority | Confirmed for both metadata reads. Fresh cases at `test_hook_authority_boundary.py:88-109` use actual recovery admission and reject the grant principal after repository/default reads. `stranded_recovery.py:55-98` retains exact request, policy, source/tree, tag and grant authority checks; `recovery_authority.py:8-35` repeats the applicable human phase. These two cases use the larger local lifecycle fixture, not a newly seeded grant or a real remote. |
| Deployment ticket/run/manifest | Confirmed in scope. `profile_deploy.py:24-45` retains the exact registered composition, manifest digest, run/installation trust, then final current-ticket and helper checks. Fresh run-read revocation and manifest/policy tests pass. No non-authority provider read follows the final helper return. |
| Workflow dev/latest and failure propagation | Preserved and tested. Both workflow copies at lines 250-258 compare manifest, dev, and latest stable before `authorize-deploy`, with strict shell handling and immediate default-success `deploy-pages`. Fresh connected replay covers both copies and both principals, including final-helper metadata delays. This is command-order replay, not Bash or Pages execution. |
| Registration without pending intent | Confirmed in scope. Metadata/run revocation and current-ticket storage interleaving negatives pass. `register()` keeps the original exact composition object and matching registration digest. |
| Registration with pending intent | Not closed. The separate dispatch-result save at `profile_worker.py:97` precedes registration at lines 98-100 without a renewed authority check. Two independent counterexamples and one authorized control are recorded above. |
| Composition ticket reads | Confirmed for both changed boundaries. `profile_worker.py:137-139,198-200` now reads the current ticket before final authority, both before local output creation and before composition-result save. Four fresh requester/resumer cases at `test_hook_authority_boundary.py:140-200` reject revocation during either ticket read. First-boundary failures create no output; neither boundary appends a composition result. |
| Evidence base and attempt reads | Confirmed in scope. `profile_evidence.py:103-109` checks the base before `authorize_attempt()`. `profile_evidence_inputs.py:80-87` reads the current record/grant selection before final helper authority. Two fresh base-read negatives reject before PR intent. `PreparationRemote.write()` at `preparation_remote.py:65-94` calls the same freshness callback before each allowlisted POST, after the necessary object/PR reads. |
| Dispatch intent then POST | Confirmed for the correction. `profile_dispatch.py:119-124` keeps pre-intent authority and repeats it after durable intent before POST. Two fresh negatives preserve the authorized intent and issue no dispatch. Bounded discovery/retry code and existing absence/terminal evidence remain; the whole recovery suite was retained from the package gate, not rerun here. |
| Protected deployment and installation | Preserved. Queue serialization, `github-pages` approval environment, pinned trusted worker, read-only final App token, complete site inventory and source separation remain. Fresh installer `--check` and disabled-profile tests pass. `.release-controller.json:3` remains `enabled: false`. |
| Historical releases and attestations | Preserved. Fresh `git diff --exit-code -- releases .github/shared/skill-management/release-attestations` returns exit 0 with an empty diff. |

The other 41 finding confirmations, their prior severity qualifications, and the absorbed P1.21 treatment remain as recorded in the unchanged full parent report. Adjacent checks above do not turn these into 41 newly executed proofs.

## Fresh Evidence

Both pytest runs used the existing package interpreter, `-B`, `-p no:cacheprovider`, and separate new scratch directories under `C:/Users/wb384996/AppData/Local/Temp/3/kilo/`. No full gate or Pester command was rerun.

| Check | Result | Evidence |
|---|---|---|
| Existing scoped selection | 62 passed, 0 failed, 0 skipped; 112.87 seconds | `phase6-helper-independent-existing-20260913-014138.xml` in the scratch directory |
| Independent helper and caller probes | 11 assertions passed, 0 failures/skips; 2.16 seconds | `phase6-helper-independent-probe-20260913-014138.xml` in the scratch directory |
| Disabled installation | Exit 0 | `packages/cg-release/.venv/Scripts/python.exe -B scripts/release_profile_install.py --check` |
| Protected history | Exit 0, empty diff | Read-only Git command recorded above |

The 62-test selection comprises `test_profile_workflow_authority.py`, `test_hook_authority_boundary.py`, `test_profile_security.py`, `test_module_bounds.py`, `scripts/tests/test_legacy_pages_security.py`, and `scripts/tests/test_release_controller_profile.py`.

The 11 independent assertions are eight repaired-boundary rejection cases, one authorized registration control, and two successful reproductions of the remaining defect. Passing counterexample assertions do not mean that registration is safe. Counts overlap retained suites and are not added as unique coverage.

**Independent probe source:** `C:/Users/wb384996/AppData/Local/Temp/3/kilo/test_phase6_helper_independent_20260913_014138.py`.

**Critical proof and exact call traces:** `C:/Users/wb384996/AppData/Local/Temp/3/kilo/phase6-helper-independent-probe-20260913-014138.xml`.

The independent probe blocks process creation and socket connections. It does not invoke `gh`, obtain credentials, or substitute an authorization function. The existing workflow-memory tests also block processes and sockets. The larger existing recovery/composition/evidence tests use real local Git/Node and a scratch wheel with fake provider I/O. This is not an OS-wide network-denial claim or remote qualification. Test fixture outputs are outside the worktree.

## Retained Gates

The latest validation was recorded at `2026-09-13T01:38:01Z`, after the helper repair freeze at `00:50:17Z`. It supersedes the handoff's pending-gate statement. It does not replace independent review or close P1.15. The candidate is uncommitted; the freeze is a declaration, not a complete cryptographic identity of dirty contents.

| Gate | Latest Recorded Result | Qualification |
|---|---|---|
| Prepare | 9 selected, 9 executed, 9 passed; 0 failed/unexecuted | Exact selected/executed argv match in order. Prepare mode, not reviewed committed-candidate validation. |
| Package | 891 passed; 0 failed/errors/skipped | Complete final summary and return code inspected in `2026-09-13-phase6-P1.15-helper-010024Z-prepare-commands.log:84-103`; not inferred from progress marks. |
| Native | 2,592 passed; 0 failed, 50 skipped, 2 deselected | Individual skip names/reasons are unavailable from the recorded `-q` result. The unsafe-hard-link exclusion warning remains. |
| Profile/launchers | 28 passed; 0 failed/skipped | Complete final summary and return code inspected in the same decoded log at lines 105-112. |
| Pester | 2,935 passed; 0 failed, 2 skipped; `filteredFiles: null` | Captured canonical result at `01:05:35Z` inspected. TestDrive cleanup errors remain; both skips belong to `update`, but individual names/reasons are absent. |
| Ordinary Node | 106 passed; 0 failed/skipped | Portable Windows file-link Dirent boundary on EPERM, not native file-symlink qualification. |
| Plan/parity | 56 passed; 0 failed, 8 skipped | Recorded POSIX-only command-shim/update groups remain unavailable on Windows. |
| Module/lint/build | Three module checks, Ruff, wheel and sdist passed | Retained analysis and decoded command log inspected; no new full gate was run. |

All evidence filenames in this section are under `.cg-docs/work-reports/release-controller/`. The validation, prepare analysis, complete package/profile/lint/build decoded results, and captured Pester last-run artifact were read. This reviewer did not reparse the full mixed Pester stderr or rerun its tests.

Pester's `DirectoryNotFoundException` and nonempty-directory cleanup errors are not relabeled as clean-host proof. Its Windows Bash result is a placeholder. The existing `-Quiet`/fixture warnings remain. The retained validator identifies the missing-target-mapping diagnostic as an intentional failure-boundary test and preserves the malformed mixed CLIXML/raw stderr; its auxiliary XML parse failure was not a gate failure. Missing skip details are not inferred. These qualifications, native Unix/Python 3.8 limits, portable-link limits, and overlapping test counts all remain.

## Phase Boundary

HEAD remains `b94f585c8a485dfb03965ca9711fb83257aaa7de`. This distinct report is the reviewer's only manual worktree write. The probe and new pytest reports are outside the worktree. No source or repository test file, canonical/generated workflow, prior report, handoff, counter, phase state, or historical artifact was manually edited.

No real remote operation, credential lookup, publication, deployment, setting change, activation, commit, push, or PR was performed. Phase 6 is not complete; V6 is not marked complete or external-only, no counter is reset, and Phase 7 is not started. The controller remains disabled.

Native Unix/Python 3.8 execution, supported-host file-symlink qualification, authorized bridge delivery and clean-client proof, exact source-bound six-cell CI and registered producer evidence, reviewed committed-candidate validation, and real bootstrap/App/journal/protected-setting authority remain external requirements. Passing local gates and the repaired final helper do not replace them.
