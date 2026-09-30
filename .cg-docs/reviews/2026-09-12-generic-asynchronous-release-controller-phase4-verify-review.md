---
date: 2026-09-12
depth: light
type: verification
parent-review: .cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase4-review.md
plan: .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md
findings:
  P1.1: fixed
  P1.2: fixed
  P2.1: fixed
---

# Phase 4 Repair Verification

## Result

Verified fixed: **3** (P1.1, P1.2, P2.1). Remaining open: **0**. New findings: **0** at every priority. No incomplete review scopes.

Completed `cg-code-quality`, then `cg-testing`, using the local specs sequentially in this independent verification session. This is two spec passes, not two independent agent sessions. No implementation edits, original-review edits, phase advancement, remote writes, commit, or publication occurred. This report is the only manually created file.

Authority: the execution report's **Phase 4 Review Repair Cycle 1 Handoff 2026-09-12T01:50:16Z**, lines 2086-2231, especially **Exact Next Verification Handoff**, lines 2195-2217; the original Phase 4 review; and `2026-09-12-phase4-review-repair-1-evidence.json`. Plan Steps 7-8 and V4 define the phase boundary. Earlier execution sections are historical, not replacement handoffs. The original review deliberately retains open statuses pending this independent result; those statuses do not prevent the explicitly requested verification.

## Verified Findings

### P1.1: Generic Build PR Gate

**Fixed.** `packages/cg-release/src/cg_release/models.py:94-100` requires an explicit check stage. `policy.py:110-113` rejects policies with no preparation check. `github_checks.py:44-46` excludes only release-only gates from preparation verification; it retains producer, workflow, SHA, completion, and nonempty-result checks.

The release path does not apply that exclusion: `build_stage.py:47-76,113-125,267-277` creates tickets for every required workflow, binds the complete check policy into the reuse digest, and requires complete workflow and artifact evidence before approval. `build_evidence.py:106-158` retains registered identity, matrix, job, runner, and success checks. Template instructions at `templates/build.yml:1-4` now state the two roles explicitly.

Executed `test_phase4_generic.py:83-141` through the full package run. It starts with the real CLI and durable admission, creates the preparation PR, binds its reviewed commit, registers separate generic and CI runs, and reaches `awaiting-approval`. Its PR inventory contains only ordinary CI; it does not inject a completed review binding or fabricate a dispatch-only PR check. Final evidence retains both workflows, with only the generic run providing assets. Stage-negative tests and existing producer/substitution tests also pass. This is offline provider evidence, not execution of installed Actions workflows.

### P1.2: Interrupted Tickets And Registration

**Fixed for the repaired protocol.** `prepare_stage.py:22-31` routes build tickets to the atomic helper. `journal_checkpoint.py:19-42` commits the whole ticket or claim in one transaction and rejects stale records, existing intents, and consumed operations. `journal_rules.py:168-209` limits this path to typed, sequential build tickets and exact-ticket-bound registrations in pre-publication build states. Existing evidence remains append-only. External dispatch and publication cannot use this shortcut.

`build_control.py:81-107` reconciles a matching dispatch intent before its atomic registration claim. A committed claim cannot grant source outputs twice. `journal.py:115-130` reads back uncertain append outcomes. A new invocation after process death observes either no ticket/claim or the complete committed record, not a digest-only half-record.

Executed all six before/after provider-commit restart cases in `test_phase4_restarts.py:91-194`. These inject `BaseException` process loss outside the ordinary recoverable-error path. Initial and replacement tickets resume without conflicting nonces; replacement retains prior verified evidence. Registration loss before commit permits the first claim; loss after commit preserves the claim and denies duplicate outputs. A failed registered run does not automatically retry. Explicit authorized resume creates a fresh ticket without changing the old registration.

The retry boundary at `build_stage.py:157-204` checks the actual attempt and registered run identity before replacement. `controller.py:173-211` supplies a resuming actor only on the manual reconciliation route, and `make_ticket()` rechecks authority. Publication-started state is rejected by atomic transition validation. Existing dispatch-unknown, duplicate-registration, identity, reuse, and journal tests remain green.

Five additional in-memory probes passed using the real `Journal`, `atomic_build_checkpoint`, and existing valid fixtures: reject wrong registration nonce, release SHA, and build digest without changing the record; reconcile a lost registration append response with exactly one revision; reject an identical second claim without another revision. No production function was replaced in these probes.

Old opaque intents remain unchanged and fail closed, as tested by `test_atomic_checkpoints.py:67-74`. This repair prevents new partial ticket/registration records. It does not migrate an old live journal or claim recovery of arbitrary historical opaque state; the unreleased implementation handoff explicitly makes the same distinction.

### P2.1: ZIP Allocation Bound

**Fixed.** `artifacts.py:54-106` binds the physical central-directory range to the end record, rejects split-volume and ZIP64 override forms, and walks actual central-directory headers with checked lengths and an entry counter before constructing `ZipFile` at line 108. The limit is the lesser of the policy count and declared inventory length. A forged smaller end-record count cannot bypass this walk.

Executed `test_artifacts.py:107-169`: forged counts, misleading directory offsets, ZIP64 override, and honest excess counts all reject before the parser constructor is called. Valid archive verification and existing run, digest, retention, path, symlink, size, and inventory rejection tests also pass. Byte and decompression limits remain in place. No memory-exhaustion trial or live archive-service compatibility claim is made.

## Spec Results

| Order | Spec | Result |
|---|---|---|
| 1 | cg-code-quality | No new actionable finding in the repaired policy, checkpoint, registration, build-evidence, or archive code. Checked module interactions, fail-closed errors, append-only behavior, and template instructions. Ruff passed. |
| 2 | cg-testing | All three repairs verified with full-package execution, targeted test inspection, and five additional atomic probes. No new coverage or nearby regression finding. |

Direct inspection covered every source and test file listed in the repair evidence scope, plus `journal.py`, `controller.py`, `phase4_transport.py`, `test_build_control.py`, and `test_build_stage.py`. The full package run exercised the remaining tests, including installed-wheel and workflow-security cases; that execution is not a claim of direct inspection of every test file. Excluded environments, caches, build outputs, unrelated tracked changes, and future Phase 5-7 requirements.

Applied the Python skill and language instructions. Consulted the local solution `.cg-docs/solutions/testing-patterns/2026-08-13-release-gate-fixtures-and-derived-evidence-hashes.md`: fixtures must exercise the runtime protocol rather than substitute a completed gate. `open-brain` tools were unavailable. Both specs retained P0/P1 and cross-file reporting without suppression, and preserved the protected-artifact constraint. No deletion or replacement of protected knowledge, charter, configuration, roadmap, schema, or workflow infrastructure is recommended.

## Executed Evidence

| Check | Result | Qualification |
|---|---|---|
| `uv run --offline --project packages/cg-release --python 3.12 --locked pytest packages/cg-release/tests -q --tb=short` | 507 passed, 0 failed, 51.49 seconds | Executed in this verifier; includes installed-wheel tests. Local Windows/Python 3.12 only. |
| `python -m pytest scripts/tests/test_cg_pr_preflight.py -q --tb=short` | 52 passed, 0 failed, 0.56 seconds | Executed in this verifier. |
| `uv run --offline --project packages/cg-release --python 3.12 --locked ruff check packages/cg-release scripts/benchmark_release.py --output-format concise` | Passed | Executed in this verifier; not a type-check or IDE-diagnostic result. |
| Additional atomic registration probes | 5 passed | In-memory journal; no remote effects or implementation edits. |
| `git diff --check` | Passed | Tracked whitespace only; does not check untracked package content. |
| `tests/last-run.json` | 2026-09-12T02:00:08Z; gitSha b94f585; passed true; total 2906; passed 2904; failed 0; skipped 2; filteredFiles null | Read directly. Dedicated sibling Pester result, not rerun by this verifier. Supersedes the repair artifact's pending Pester field. |

Retain the reported Pester TestDrive missing-path/nonempty-directory cleanup caveat. Zero failed assertions does not establish successful temporary-directory cleanup. The aggregate result does not identify the two skipped tests or their reasons. No evidence found that this qualification invalidates the executed Phase 4 package checks. No cleanup was attempted.

## V4 Recommendation

The three reported repair blockers are resolved. Recommend that the parent accept this verification and the refreshed unfiltered Pester gate for the local Phase 4 completion decision. Only the parent may complete V4 and update phase metadata; this verifier does neither.

Live six-cell Actions runs, protected approvals, hostile-source secret-boundary trials, publication, and latency evidence remain later authorized gates. Local fixtures and passing tests do not establish those outcomes. No Phase 5 action is authorized or performed by this report.
