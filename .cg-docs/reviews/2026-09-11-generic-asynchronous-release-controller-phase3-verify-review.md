---
date: 2026-09-11
depth: light
type: verification
plan: .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md
source-review: .cg-docs/reviews/2026-09-11-generic-asynchronous-release-controller-phase3-review.md
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
---

# Phase 3 Repair Verification

## Result

Confirmed fixed: **6/6**. Original findings still open in this verification: **0**.
New findings: **0** (P0: 0, P1: 0, P2: 0, P3: 0).

This independent verification child applied `cg-code-quality`, then `cg-testing`,
sequentially in one session. These are two emulated spec passes, not two separate
agents or a repeat of the original ten-spec full review. No new actionable issue
was found in the inspected repair and nearby regression paths.

The original review remains an unchanged historical artifact. The fixed statuses
above are this child's independent conclusions. No implementation, plan, active
state, recovery counter, or phase-completion field was changed.

## Inputs And Scope

Read the exact execution handoff and repair section at
`.cg-docs/work-reports/2026-09-11-generic-asynchronous-release-controller.md:1212-1540`,
the complete original Phase 3 review, and
`.cg-docs/work-reports/release-controller/2026-09-11-phase3-review-repair-evidence.json`.
Checked the current plan's authority, queue, and retention contracts at lines
180-334. Loaded project instructions, charter/configuration, both requested agent
specs, Python instructions, Python skill, anti-patterns, and pytest guidance.
`open-brain` tools were unavailable. Current code and the specified handoff, not
historical memory, supplied the repair evidence.

Explicitly read untracked package files rather than relying on tracked diffs.
Production inspection covered `controller.py`, `authority.py`, `runtime.py`,
`context.py`, `queue.py`, `journal.py`, `github_journal.py`, `git_journal.py`,
`verification.py`, `github.py`, `read_session.py`, `lifecycle.py`, `events.py`, and
`progress.py`. Test/support inspection covered `test_worker_e2e.py`,
`worker_transport.py`, `test_phase3_review_repairs.py`, `test_journal_retention.py`,
`test_queue.py`, `test_controller.py`, and `test_remote_faults.py`.
The complete package suite also exercised the other test modules.

## Confirmed Repairs

All paths in this table are relative to `packages/cg-release/`.

| ID | Decision and current source evidence | Executed regression evidence |
|---|---|---|
| P1.1 | Fixed. `src/cg_release/controller.py:230-248` passes the verified manual actor into reconciliation. Lines 84-87 and 126-130 check authority before and after proposal replay. `authority.py:11-30` shares the current requester/resumer checks with CLI resume. `journal.py:93-125,145-164` reruns admission revalidation after a competing CAS rather than replaying an old authorization result. | `test_worker_e2e.py:78-94` rejects a direct write-only override resumer and revocation during replay with zero writes. Lines 57-75 retain authorized manual resume and exact sealed reuse. |
| P1.2 | Fixed for the reported repeated-item starvation. `queue.py:137-157` temporarily narrows the actual API deadline to at most 20 seconds, reserves 40 seconds for checkpoint work, restores the parent deadline in `finally`, and records a typed item deadline. Lines 158-170 checkpoint completed work without skipping unattempted entries. | `test_worker_e2e.py:122-141` runs three scheduled attempts with an expensive first request and reaches the healthy second request. Lines 144-173 check failed checkpoint recovery and a timeout after accepted admission without duplicate admission. |
| P1.3 | Fixed. `queue.py:128-129` makes an unchanged empty scan read-only. `git_journal.py:25-39`, `github_journal.py:74-134`, and `journal.py:28-88` no longer impose the old lifetime event cap. Both stores accept canonical event paths beyond ten digits. `verification.py:11-32` limits each verification attempt without truncating history; cycle, signature, tree, and transition checks remain. | `test_phase3_review_repairs.py:51-67` checks five empty remote scans with zero writes and extended revision paths. `test_journal_retention.py:17-56` replays 10,000 valid retained events, admits and checkpoints at 10,001/10,002, rejects an expired verification attempt, and reads the retained request again with a fresh budget. |
| P2.1 | Fixed. `test_worker_e2e.py:12-17` replaces external process transport, not context, role, proposal, admission, or journal decisions. `worker_transport.py:158-221` supplies HTTP envelopes and separates accepted writes from response timing. | Lines 57-173 of `test_worker_e2e.py` run confirmed start, receipt, real worker admission, a fresh CLI status session without Git discovery, manual resume, policy/source/role changes, external tag collision, direct dispatch, deadline exhaustion, and checkpoint failure. Real bare-Git coverage remains in the passing package suite. |
| P2.2 | Fixed. `events.py:71-86` uses the redacted payload for explicit human version, observed state, step, and expected state, while preserving locator and next-action output. | `test_phase3_review_repairs.py:19-38` separately checks queued, failed, published, and complete human output and all four fields. Existing package output tests also pass. |
| P2.3 | Fixed. `progress.py:34-54` leaves the queue start unknown when the receipt timestamp is absent. Repeated queued events do not manufacture a start time; later state changes can start their own measured intervals. | `test_phase3_review_repairs.py:41-48` verifies null total queue time at 60 seconds after admission without a receipt creation timestamp. The other progress tests pass in the package suite. |

## Sequential Review

### 1. Code Quality

Checked the shared authority function and both call paths, exact proposal replay,
CAS retry callback, fresh mutable reads, queue deadline restoration, empty-scan
return, append-only history validation, and output redaction before rendering.
No new actionable correctness or code-quality finding was identified. Ruff passed.

The manual authority check does not turn scheduled or issue-driven scans into
maintainer recovery. Such scans still validate the original requester before
admission. Sealed reconciliation in Phase 3 returns a verified checkpoint and
does not execute a later stage. The deadline repair does not convert an uncertain
write into proof of absence: signed read-back and later reconciliation remain.

### 2. Testing

Checked fixture isolation, mock boundaries, assertions, timeout injection, and
failure-path coverage. The new worker scenario uses real GitHubReads and its
shared deadline through a fake process transport. It is not a callback-only
admission test. Assertions distinguish rejection before writes, one accepted
admission, separate queue writes, and no duplicate issue or admission on resume.

Nearby regression coverage includes continuous arrivals, more than 100 requests,
interruption before checkpoint, stale cursor rejection, deleted sealed-issue
inventory, lost accepted-write response, and invalid remote writer/signature/
root/event/reservation data. These tests passed with the complete package suite.

## Verification Results

| Check | Result |
|---|---|
| `uv run --offline --project packages/cg-release --python 3.12 --locked pytest packages/cg-release/tests -q --tb=short -p no:cacheprovider` | 382 passed, 0 failed, 32.32 seconds; includes build/install and isolated bare-Git tests |
| `python -m pytest scripts/tests/test_cg_pr_preflight.py -q --tb=short -p no:cacheprovider` | 52 passed, 0 failed, 0.44 seconds |
| `uv run --offline --project packages/cg-release --python 3.12 --locked ruff check packages/cg-release scripts/benchmark_release.py --no-cache` | Passed |
| `git diff --check` | Passed for tracked changes; does not cover untracked package content |
| Dedicated post-repair Pester artifact | `ranAt: 2026-09-11T23:01:57Z`, `gitSha: b94f585`, passed true, total 2906, passed 2904, failed 0, skipped 2, `filteredFiles: null` |

The Pester fields were read directly from `tests/last-run.json` and match the
supplied post-repair gate. Pester was not rerun in this child. Retain the two known
update-test skips and the reported TestDrive missing-path/nonempty-directory
cleanup errors. Passing assertions do not establish successful cleanup.

## Limits And Handoff

- Fake-provider signatures, controls, roles, and clocks are synthetic evidence,
  not proof of a live GitHub installation or enforcement matrix.
- The 10,000-event test establishes core replay and retention beyond the removed
  cap. It does not measure 10,000-event GitHub transport performance. Full remote
  replay still scales with retained history and remains subject to time, response,
  cache, and provider limits. Constant-time or unlimited-capacity reads are not
  claimed.
- The checkpoint reserve prevents one item from consuming the entire command
  budget. It does not guarantee a remote checkpoint during an outage or when
  initial inventory/history reads leave insufficient time. No live queue latency
  or 1-2 minute handoff result is claimed.
- No remote mutation, publication, worktree commit, push, or Phase 4 work was
  performed. Temporary Git fixture commits belong to the isolated test suite.

Return all six independently confirmed IDs to the parent. This report permits
the parent to record their closure under its workflow; it does not itself mark
Phase 3 complete. Preserve completed-phases [1, 2], current-phase 3, and all
existing recovery counters until the parent performs the authorized checkpoint.
