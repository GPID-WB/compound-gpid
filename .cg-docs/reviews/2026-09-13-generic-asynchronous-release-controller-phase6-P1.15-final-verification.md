---
date: 2026-09-13
type: verification
depth: scoped
status: changes-required
parent-review: .cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase6-repair2-verification.md
handoff: .cg-docs/work-reports/release-controller/2026-09-12-phase6-P1.15-repair.json
validation: .cg-docs/work-reports/release-controller/2026-09-12-phase6-P1.15-validation-233019Z.json
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

# Phase 6 P1.15 Final Scoped Verification

**Verdict: Changes required. P1.15 remains open.** The canonical and installed workflow order is repaired, but the final worker helper still reads repository and default-branch state after it checks human permissions. Eight fresh offline counterexamples reproduce stale authorization at that connected boundary. These are additional proofs of P1.15, not new finding IDs.

The 41 confirmations in the parent report are preserved. This pass confirms no additional repair: **41 confirmed, 1 open, 0 new findings**. It does not repeat or replace the earlier full ten-spec review. No original finding map, handoff, progress counter, phase state, or prior evidence file was changed.

## Remaining Finding

### P1.15: Final Helper Reads Outlast Human Authorization

**[P1]** `packages/cg-release/src/cg_release/hook_authority.py:65-79`, called by `packages/cg-release/src/cg_release/profile_deploy.py:43-45`.

**Issue:** Moving `authorize-deploy` to the last workflow command closes the two reported dev/latest read gaps. However, that command's final `authorize_hooks(..., fresh=True)` call executes these operations:

1. `authorize_record()` checks the applicable requester/resumer or admitted recovery authority.
2. `context.api.get("")` reads repository identity and the default branch name.
3. `context.api.branch(context.default)` reads the protected default branch and its SHA.
4. The helper returns without another human-permission check. `authorize_deployment()` then returns the registered composition.

The repository/default-branch reads are not permission reads. A requester or resumer can lose write authority during either read while repository identity, branch protection, and policy SHA remain unchanged. All current checks then pass. This is a concrete stale-authority window inside the final command, not only the unavoidable interval between a completed authorization check and a later external effect.

Both workflows call this real worker at line 256 and place `actions/deploy-pages` immediately after it at lines 257-258. No later command rechecks the human principal. `profile_worker.py:237-251` writes local step outputs and returns success after authorization; it does not close the gap. The read-only App credential and protected Pages environment do not replace the required human check.

**Fresh proof:** The independent probe uses the existing `test_profile_security.py` worker fixture, the real `Journal`, real registration, real composition evidence append, real `GitHubReads`, and real `authorize_deployment()`. It asserts the exact current five-statement workflow order before it replays the manifest and dev/latest comparisons, then calls the worker. Only the outer GET transport changes a synthetic actor's role while returning the expected repository/branch identity.

| Delayed Final Worker Read | Principal | Canonical Template | Installed Workflow |
|---|---|---|---|
| Repository metadata, `repos/owner/repo` | Requester 456 | Stale authorization reproduced | Stale authorization reproduced |
| Repository metadata, `repos/owner/repo` | Resumer 8 | Stale authorization reproduced | Stale authorization reproduced |
| Protected default, `branches/production` | Requester 456 | Stale authorization reproduced | Stale authorization reproduced |
| Protected default, `branches/production` | Resumer 8 | Stale authorization reproduced | Stale authorization reproduced |

All eight cases returned the expected composition after revocation. Each case asserted that no permission read followed the revocation and that the journal transactions, including event bytes, remained unchanged. An immediate negative control called the real authorization function again and rejected the revoked actor with `E_AUTHORITY` in every case. The recorded accepted GET trace ends with repository metadata and `branches/production`, after both human permission checks.

The probe blocks process creation and socket connections. It does not run `gh`, read credentials, execute Bash, call a Pages action, or deploy content. The composition result and small manifest are seeded at the same boundary as the existing worker test; this is not a full composition or deployment qualification. Admitted recovery follows the same helper order by source inspection, but no new recovery-principal counterexample is claimed in this pass.

**Required correction:** Put the final non-authority freshness reads before the final applicable human-authority check, or repeat that human check after those reads. Keep current-ticket, bound policy, exact run, exact registration, manifest, dev/stable, recovery-grant, and protected-environment checks. Add requester/resumer regression cases for both final helper reads, with the real helper and an outer GET transport. Retain the new workflow-order regressions. No live deployment is needed to verify this correction.

The missing test cases are part of this same P1.15 residual. They are not counted as another P2 or new finding.

## Sequential Review

The two requested specs were loaded and their analyses were completed sequentially in this independent session: code quality first, testing second. No Agent Manager or internal reviewer session was created.

| Order | Spec | Scope And Result |
|---|---|---|
| 1 | `cg-code-quality` | Read the canonical and installed docs workflows, installer, worker, deployment helper, current-ticket checks, run verification, ordinary/recovery authority, and context trust checks. The workflow change is small and correctly generated. The final helper's control flow exposes the existing P1.15 residual. No separate style or quality finding was added. |
| 2 | `cg-testing` | Read the new connected workflow regressions, worker security tests, fixture transport/journal, effective workflow tests, and disabled-profile tests. Ran the 34-test repair selection and eight independent counterexamples. Existing regressions cover earlier boundaries but not the final repository/default read. No second finding ID was added. |

Project instructions, Python guidance, and the Python testing skill were applied. Local project context and the verified Pages artifact lesson were consulted. No open-brain service tool was available; saved project context and the local solution file were used. The older main-only release topology was not treated as the current plan. No memory write was requested or performed.

## Adjacent Preservation

| Control | Current Evidence |
|---|---|
| Canonical/generated order | `packages/cg-release/templates/gpid-docs.yml:250-258` and `.github/workflows/release-controller-docs.yml:250-258` both use strict Bash handling, manifest comparison, dev comparison, latest-stable comparison, then `authorize-deploy`. The read-only installer `--check` passed. |
| Effective failure handling | The authorization step has no `continue-on-error`, skipped-step condition, error suppression, or trailing command. Deployment is the next step and has the default success condition. Existing structural and command-replay tests passed. |
| Queue and upload boundary | Workflow lines 153-168 retain the shared `pages` concurrency group, no cancellation of an in-progress deployment, and `github-pages` environment. Upload precedes the read-only authority token and final step at lines 225-256. |
| Artifact and source separation | Lines 190-224 retain exact-run artifact download, expected manifest digest, complete site inventory hashing, and link/nonregular-file checks. The unprivileged dev job stays separate from the pinned trusted composer and deploy job. |
| Credential and controller boundary | The final worker remains isolated with `-I`; checkout uses the pinned trusted controller and does not persist credentials. The final App token requests read permissions only. The deploy job does not execute dev/release source or obtain the publishing App credential. |
| Current worker guards | `profile_deploy.py:24-44` retains published/current composition, policy digest, exact registered run/request digest, expected manifest, final current ticket, and final helper invocation. `controller.py:24-72` retains exact workflow/run/ref/actor and installed pin verification. |
| Existing revocation repairs | Fresh tests reject requester/resumer revocation during each workflow dev/latest read and during the worker's run read. Their success does not test the later helper reads. |
| Disabled installation and history | The installer check and disabled-profile tests passed. `git diff --exit-code -- releases .github/shared/skill-management/release-attestations` was empty. |

These adjacent checks preserve, but do not independently re-prove, all 41 earlier confirmations. Their IDs, severity qualifications, evidence limits, and the absorbed P1.21 treatment remain as recorded in the unchanged parent report.

## Fresh Local Evidence

All pytest calls used the existing package interpreter, `-B`, `-p no:cacheprovider`, and separate new scratch directories under `C:/Users/wb384996/AppData/Local/Temp/3/kilo/`. No environment installation or full-gate rerun was performed.

| Check | Result | Evidence |
|---|---|---|
| Existing repair selection | 34 passed, 0 failed, 0 skipped; 3.66 seconds | `phase6-p115-independent-existing-20260913.xml` in the scratch directory |
| Independent final-helper counterexamples | 8 reproduced, 0 probe failures, 0 skipped; 1.84 seconds | `phase6-p115-independent-residual-20260913.xml` in the scratch directory; each case includes its exact GET trace and negative-control code |
| Disabled installation | Exit 0 | `packages/cg-release/.venv/Scripts/python.exe -B scripts/release_profile_install.py --check` |
| Protected history | Exit 0, empty diff | `git diff --exit-code -- releases .github/shared/skill-management/release-attestations` |

The 34-test selection was `test_profile_workflow_authority.py`, `test_profile_security.py`, `test_module_bounds.py`, `scripts/tests/test_legacy_pages_security.py`, and `scripts/tests/test_release_controller_profile.py`. Eight passing counterexample assertions mean that the defect was reproduced, not that deployment is safe. Counts overlap retained suites and are not added as unique coverage.

**Critical proof log:** `C:/Users/wb384996/AppData/Local/Temp/3/kilo/phase6-p115-independent-residual-20260913.xml`.

**Independent probe source:** `C:/Users/wb384996/AppData/Local/Temp/3/kilo/test_phase6_p115_final_authority_independent_20260913.py`.

## Retained Gate Evidence

The latest validation was recorded at `2026-09-12T23:58:32Z`, after the repair handoff at `23:13:59Z`. It supersedes the handoff's statement that final gates were pending. It does not supersede independent review. Its source freeze is a declaration for an uncommitted candidate, not a complete cryptographic identity of dirty contents.

| Retained Gate | Latest Result | Limit |
|---|---|---|
| Prepare | 9 selected, 9 executed, 9 passed, 0 failed/unexecuted | Prepare mode, not a reviewed committed-candidate gate |
| Package | 863 passed, 0 failed/errors/skipped | Complete summary and return code inspected at readable prepare lines 327-343 |
| Native | 2,592 passed, 0 failed, 50 skipped, 2 deselected | Retained validation summary; individual skip identities are unavailable from that `-q` result |
| Profile/launchers | 28 passed, 0 failed/skipped | Complete result inspected at readable prepare lines 345-362 |
| Pester | 2,935 passed, 0 failed, 2 skipped; `filteredFiles: null` | Current `tests/last-run.json` still matches `23:30:19Z`; cleanup errors remain, and individual update skip names/reasons are absent |
| Ordinary Node | 106 passed, 0 failed/skipped | Log confirms the portable Windows file-link boundary, not native symlink creation |
| Plan/parity | 56 passed, 0 failed, 8 skipped | Log names the unavailable POSIX execution groups |
| Lint/build | Ruff and wheel/sdist build passed | Readable prepare lines 364-400; not rerun in this review |

Retained logs are under `.cg-docs/work-reports/release-controller/`:

- `2026-09-12-phase6-P1.15-validation-233019Z.json`
- `2026-09-12-phase6-P1.15-prepare-233019Z.json`
- `2026-09-12-phase6-P1.15-prepare-readable-233019Z.json`
- `2026-09-12-phase6-P1.15-prepare-stderr-233019Z.log`
- `2026-09-12-phase6-P1.15-node-233019Z.log`
- `2026-09-12-phase6-P1.15-planparity-233019Z.log`

The retained full Pester output path is `C:/Users/wb384996/.local/share/kilo/tool-output/tool_097f462f1001VUumtZ2TPHrT1O`. This review read the validation and canonical result, not that full Pester stream, and ran no Pester command. Cleanup errors and missing skip details are not relabeled as clean-host proof.

## Phase Boundary

HEAD remains `b94f585c8a485dfb03965ca9711fb83257aaa7de`. This report is the only manual worktree write by this reviewer. The independent probe and generated test reports are outside the worktree. No source or repository test file was edited, no canonical tree was regenerated, and no historical artifact was rewritten. No real remote operation, credential lookup, release, deployment, setting change, commit, push, or PR was performed.

Phase 6 remains incomplete, with P1.15 still open. V6 is not marked complete or external-only; no counter is reset and Phase 7 is not started. The controller remains disabled. Native Unix/Python 3.8 execution, supported-host file-symlink qualification, authorized bridge delivery and clean-client proof, exact source-bound six-cell CI and registered producer evidence, reviewed committed-candidate validation, and real bootstrap/App/journal/protected-setting authority remain external requirements. Local gate success does not replace them.
