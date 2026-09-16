---
date: 2026-09-11
depth: full
type: standard
plan: .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
---

# Release Controller Phase 3 Review

## Result

**Final verification, 2026-09-11T23:08:05Z**: All six findings are independently
confirmed fixed in phase3-verify-review.md. Remaining findings: 0; new findings: 0.
The original full review covered 10 specs; repair verification covered two specs
sequentially in a separate session. The finding statuses above record that
verified closure. The dated implementation note and original review below are
historical, not current open findings.

**Implementation update, 2026-09-11T22:54:27Z**: Authorized repair batch 1 has
applied local fixes for all six IDs. The repaired package passes 382 tests;
preflight passes 52 tests and Ruff is clean. Independent repair verification has
not run. The original finding statuses remain open until that verification.
Repair details and qualifications:
`.cg-docs/work-reports/release-controller/2026-09-11-phase3-review-repair-evidence.json`.
The review result and evidence below describe the original review snapshot.

**Status**: Review complete; changes required before Phase 3 completion.
**Review mode**: full, embedded `review:auto`, Phase 3 Steps 5-6 only.
**Coverage**: 10/10 local agent specs emulated sequentially in one review session.
These were not ten independent sessions. No incomplete agent outputs remain.
**Findings**: 6 open findings: P0: 0, P1: 3, P2: 3, P3: 0.
**Implementation edits**: none. No fixes, later workflow commands, commits,
pushes, remote mutations, or phase-completion writes were performed.

## P1 Findings

### P1.1: Manual Reconciliation Bypasses Override Resumer Authority

**[P1.1]** [cg-adversarial] `packages/cg-release/src/cg_release/controller.py:215-216`

**Issue**: The trusted workflow accepts a manual `reconcile` operation from a
current write-only actor, then discards that actor's identity when it calls
`reconcile`. `verify_run` checks that the actor has write/maintain/admin permission
at lines 62-63. However, `reconcile` and `revalidate` check only the original
requester. An unsealed production-branch override can therefore be sealed by a
write-only resuming actor through the workflow input. The public CLI correctly
rejects that actor in `runtime.py:183-189`, but this client-side restriction is
not enforced at the journal-write boundary.

**Trigger and proof**: An offline probe called the real `controller.main` with a
valid `workflow_dispatch` run envelope, actor 456 with role `write`, and a valid
unsealed override request from actor 7 with role `maintain`. The probe supplied
a verified context, immutable source snapshot, and inbox as fixtures. It did not
replace `verify_run`, `actor_role`, `reconcile`, `revalidate`, proposal calculation,
or journal transition validation. Result:

```text
exit: 0
checked_roles: [(456, 'write'), (7, 'maintain'), (7, 'maintain')]
reservations: ['1.0.0']
observed: queued
step: admitted
```

**Impact**: Direct workflow dispatch bypasses the current override-resumer
authority rule. This is an admission/reconciliation defect, not evidence of a
published release or bypass of a future publication environment.

**Fix**: Carry the verified triggering actor and operation mode into manual
reconciliation. Enforce the same current resumer rule as CLI resume before a
consequential journal operation. Keep scheduled/issue wakeup authority distinct
from human recovery authority; do not turn all scheduled scans into maintainer
recovery. Add a direct-workflow negative test for a write-only override resumer.

**Authority**: Plan Trusted Policy and Bootstrap, lines 187-191; Phase 3 Step 6;
the implemented matching CLI boundary at `runtime.py:158-189`.

### P1.2: Deadline Exhaustion Can Starve Later Queue Entries

**[P1.2]** [cg-performance, cg-adversarial] `packages/cg-release/src/cg_release/queue.py:129-144`

**Issue**: `scan` gives each entry the remaining command deadline and catches
every `ControllerError`, including `E_DEADLINE`. It saves the cursor only after
the batch. Once an early entry consumes the deadline, later entry checks and
`advance_cursor` use the same expired reader. The cursor cannot be persisted.
The next scheduled worker begins at the same entry. There is no smaller per-item
budget or reserved time for the durable checkpoint.

**Trigger and proof**: An injected-clock probe used the real `scan`, `Journal`,
and cursor validation with a deadline-aware in-memory store. Entry 1 consumed
the 120-second budget and raised `E_DEADLINE`; entry 2 was otherwise available.
Three fresh worker attempts returned:

```text
E_DEADLINE
E_DEADLINE
E_DEADLINE
visited: [1, 1, 1]
cursor: 0
events: 0
```

The store rejected reads after the deadline, as `GitHubReads.remaining` does.
No real wait or network call was used. This models one repeatedly expensive
request, not a claim that any present GitHub request took 120 seconds.

**Impact**: A request that consistently exhausts its budget can prevent later
requests from reaching admission indefinitely. Durable issue storage prevents
deletion, but does not satisfy the required eventual queue progress.

**Fix**: Give each item a bounded budget that leaves time for a verified cursor
write. Stop the batch before the checkpoint budget is consumed. Persist a typed
item failure and advance fairly when the outcome permits it; retain intent and
reconciliation rules for uncertain writes. Test repeated deadline-heavy entries
followed by a healthy entry, using the real shared-deadline adapter boundary.

**Authority**: Plan lines 287-293 and Step 6 queue survival/fairness contract.

### P1.3: Idle Scheduled Scans Exhaust The Lifetime Journal

**[P1.3]** [cg-architecture, cg-performance] `packages/cg-release/src/cg_release/queue.py:134-144`

**Issue**: Every scan, including an empty inventory, advances the cycle and
appends a journal event. `journal_models.py:9` limits history to 10,000 events.
`git_journal.py:24-32`, used by both stores, rejects every subsequent transaction.
Thus the five-minute schedule in `templates/controller.yml:7-8` consumes the
entire journal even when no release request is submitted.

**Trigger and proof**: An offline probe used the real `GitHubJournalStore`,
`Journal`, `scan`, and `transaction_files` with the existing fake GitHub server.
Only the transaction event limit was reduced from 10,000 to 2 for the boundary
test. Three empty scans produced:

```text
empty scan persisted
empty scan persisted
E_JOURNAL
writes: 2
events: 2
```

At the configured limit and nominal schedule, 10,000 empty scans take about
34.7 days. This is arithmetic, not measured GitHub scheduling evidence. Request
events and manual wakeups consume the limit sooner. The transaction guard does
preserve the existing readable history; the probe did not corrupt it.

**Impact**: A normally running installation eventually loses all ability to
admit requests, record results, retire reservations, or advance its queue.
Retry/resume cannot recover capacity. This is a lifetime capacity limit, not a
temporary per-command deadline. Recreating the root or deleting history would
violate the approved retention and immutability rules.

**Fix**: Do not write an unchanged empty queue checkpoint. Separate bounded
per-command verification work from total retained history, with an append-only
design that can continue after this boundary. Do not silently introduce history
rewrites or automatic compaction. Add empty-scan idempotence and limit-boundary
tests, including continued admission and checkpoint updates.

**Authority**: Plan journal retention at lines 325-334; Steps 5-6 durable journal
and scheduled recovery requirements.

## P2 Findings

### P2.1: Critical Worker Integration Paths Have No End-To-End Test

**[P2.1]** [cg-testing] `packages/cg-release/tests/test_controller.py:14-76`

**Issue**: This file tests run identity, an already sealed request with authority
stubbed out, and deleted-issue inventory. It does not execute `controller.main`
or actual confirmed-input `revalidate`. The successful start test in
`test_runtime.py:19-43` replaces `context_for`, `check_submission`, and the inbox.
The lifecycle tests replace revalidation with a callback. These tests are useful
unit checks, but do not establish that the complete Phase 3 path works together.

**Impact**: Direct workflow authority, immutable-source replay, shared deadline,
and fresh-context failures can pass the 362-test suite. P1.1 and P1.2 demonstrate
two gaps. The report's requirement for fault-injected fake-provider end-to-end
coverage is not met by isolated callback tests.

**Fix**: Add an offline transport-level scenario from confirmed start to receipt,
unsealed worker admission, second-machine status, and manual resume. Run the real
context, role, proposal replay, and journal code, stubbing only external transport,
clock, and environment. Include stale policy/source/role, an external tag race,
direct workflow dispatch, and deadline/checkpoint failures. Keep real bare-Git
CAS tests. Live sandbox or remote matrix execution is not required to fix this
Phase 3 gap.

### P2.2: Human Status Omits Lifecycle State, Version, And Step

**[P2.2]** [cg-documentation, cg-code-quality] `packages/cg-release/src/cg_release/events.py:75-83`

**Issue**: The human output branch renders message, locator, next action, and
proposal fields, but not `observed`, `version`, `step`, or `expected`.
`runtime.status` returns a fixed message for all sealed states at
`runtime.py:119-138`. The word `complete` in the generic message does not state
that the request is complete. Both published and complete records retain
`published: true` in the proposal.

**Proof**: The real renderer produced identical human text for status events
that differed only between `observed='published'` and `observed='complete'`.
The supplied version and checkpoint were also absent. JSON output retains
these fields; this finding concerns the default human interface.

**Impact**: A caller cannot reliably distinguish publication from completion or
identify the current execution step from the default status output.

**Fix**: Render the validated version, observed state, and current step explicitly
in human output, with expected state when relevant. Add human snapshots for
queued, failed, published, and complete status, not only locator display.

### P2.3: Missing Queue Start Is Reported As A Measured Duration

**[P2.3]** [cg-data-quality] `packages/cg-release/src/cg_release/progress.py:46-47`

**Issue**: If the receipt's creation timestamp is absent, `stage_timings` uses
the first journal event as the queue start. This discards the unknown interval
between durable issue creation and admission, while still returning the result
under the unqualified `queue` duration. Missing receipt timestamps are explicitly
accepted by `Receipt` and by the inbox adapter.

**Proof**: A real journal admitted the existing receipt fixture with
`created_at=None`. With `now` injected at exactly 60 seconds after its first
event, `stage_timings` returned `queue: 60.0`, not null. The existing test at
`test_progress.py:25-29` checks only that submission time is null.

**Impact**: Reported queue time can understate the actual wait and can be mistaken
for evidence of the handoff/queue performance target. It is a timing-evidence
defect, not a measured live performance regression.

**Fix**: Keep total queue duration null when its start is unknown. If time since
admission is useful, give it a separate explicit field or lower-bound label.
Add a missing-receipt-time assertion for queue duration.

## Sequential Agent Coverage

All ten passes used the same Phase 3 scope, Python instructions/skill, priority
rules, and protected-artifact constraint. Findings were merged without reducing
P0/P1 strength. No agent recommended deleting, replacing, renaming, or moving
protected project artifacts.

### 1. cg-code-quality

Finding P2.2: the status event producer and human renderer disagree about which
fields communicate lifecycle state. Inspected `cli.py`, `events.py`, `runtime.py`,
process errors, and the new controller/journal modules. No additional actionable
style or lint issue was found; independent Ruff passed.

### 2. cg-testing

Finding P2.1: the principal worker/context/revalidation path is absent from
end-to-end coverage in `test_controller.py`, `test_runtime.py`, and lifecycle
tests. Reviewed admission, queue, authority, transport, fault, install, and real
bare-Git tests. The 362-test pass is valid but does not cover the listed gaps.

### 3. cg-documentation

Finding P2.2: default status output does not communicate the promised state.
Reviewed public docstrings, CLI messages, template comments, and the execution
handoff. Package README, operator backup instructions, and full installation
documentation are Phase 7 scope and are not reported as missing Phase 3 work.

### 4. cg-version-control

No additional issues found in `.gitignore`, package configuration, synthetic
fixtures, and template credential references. Build/environment caches are
excluded. The package and lockfile are untracked work in progress, not a missing
commit finding. No real secret value was identified. Existing release history
and unrelated edits were preserved.

### 5. cg-reproducibility

No additional issues found in `pyproject.toml`, the selected `uv.lock` metadata,
installed-wheel tests, explicit Python selection, and pinned disabled workflow.
The real temporary build/install smoke passed locally. Random submission nonces
are intentional identities, not unseeded analytical results. Other operating
systems, live protections, and remote CI remain unverified here.

### 6. cg-performance

Findings P1.2 and P1.3: the queue has no checkpoint time reserve and idle work
consumes lifetime journal capacity. Reviewed `read_session.py`, `github.py`,
`github_journal.py`, and backlog tests. The bounded immutable cache improves
repeated reads, but a warm 101-request fixture is not a cold-start or lifetime
scaling guarantee. No live speedup was inferred.

### 7. cg-architecture

Finding P1.3: per-command bounds are coupled to a finite lifetime journal.
Reviewed the source package boundaries, separate local/remote stores, trusted
workflow, and no-publication Phase 3 checkpoint. The standalone package layout
and disabled later-stage behavior remain intact; no new dependency or target
GPID runtime requirement was identified.

### 8. cg-data-quality

Finding P2.3: unknown receipt time becomes a queue measurement. Reviewed strict
models, locator canonicalization, nonce/reservation checks, receipt identity,
event replay, cursor shapes, and JSON decoding. No statistical/survey data
operations are present. No silent request loss or credential exposure was
demonstrated in this pass.

### 9. cg-learnings-researcher

Relevant lessons: `.cg-docs/solutions/bugs/2026-08-31-trust-anchor-captured-byte-dispatch.md`
requires authority at the actual operation boundary; this supports P1.1 and P2.1.
`.cg-docs/solutions/testing-patterns/2026-08-17-journal-security-hardening-patterns.md`
requires validation before using journal identifiers. Locators and journal paths
have explicit checks. No additional finding was added from historical material.

### 10. cg-adversarial

Confirmed P1.1 through direct manual worker execution and P1.2 through repeated
deadline loss. Probed the event-limit boundary, human state distinction, and
missing timing inputs as supporting evidence. All probes used synthetic data;
no live exploit, publication, or remote mutation was attempted. No P0 was found.

## Scope And Evidence

The exact handoff was read from the execution report's Phase 3 final section,
lines 1212-1420. Plan Steps 5-6, applicable design contracts, local `cg-review`
instructions, review-routing/context-loading contracts, charter/configuration,
Python instructions, Python review/testing references, and Pester safety were
loaded. All ten named local agent specs were read in the requested order.

Direct source inspection covered 24 production modules under
`packages/cg-release/src/cg_release/`: `abandon`, `admission`, `authority`, `cli`,
`context`, `controller`, `events`, `git_journal`, `github`, `github_journal`,
`inbox`, `journal`, `journal_models`, `journal_rules`, `jsonio`, `lifecycle`,
`models`, `preview`, `process`, `progress`, `queue`, `read_session`, `runtime`,
and `source`. Prior-phase dependencies were inspected for cross-file effects,
not reopened as unresolved prior findings.

Direct test/support inspection covered 20 files: `test_abandon`, `test_admission`,
`test_authority`, `test_concurrency`, `test_controller`, `test_controller_templates`,
`test_inbox_transport`, `test_install`, `test_journal`, `test_lifecycle`,
`test_preview`, `test_process_input`, `test_progress`, `test_queue`,
`test_read_session`, `test_remote_faults`, `test_remote_journal`, `test_runtime`,
`test_status`, and `journal_store`. The complete package suite was executed.

Also inspected package metadata, selected lock metadata, the three bootstrap
templates, controller CI configuration, root ignore rules, active-state handoff,
and current Pester result fields. Build outputs, environments, bytecode, test/lint
caches, generated view bodies, and future Phase 4-7 implementation were excluded.

| Check | Result |
|---|---|
| `uv run --offline --project packages/cg-release --python 3.12 --locked pytest packages/cg-release/tests -q --tb=short -p no:cacheprovider` | 362 passed, 27.96 seconds; includes temporary wheel/sdist/install checks |
| `python -m pytest scripts/tests/test_cg_pr_preflight.py -q --tb=short -p no:cacheprovider` | 52 passed, 0.42 seconds |
| `uv run --offline --project packages/cg-release --python 3.12 --locked ruff check packages/cg-release scripts/benchmark_release.py --no-cache` | Passed |
| `git diff --check` | Passed for tracked changes; not untracked package coverage |
| Current `tests/last-run.json` | `ranAt: 2026-09-11T22:09:18Z`, `gitSha: b94f585`, passed true, total 2906, passed 2904, failed 0, skipped 2, filteredFiles null |
| In-memory review probes | Confirmed direct-dispatch authority gap, deadline starvation, empty-scan capacity use, missing human status fields, and missing-time substitution |
| Review artifact validation | Frontmatter and six open IDs checked manually. `cg-render-artifact --validate-only` does not support `.cg-docs/reviews`; it accepts only plans/brainstorms. No dedicated automated review-schema validation is claimed. |

Pester was not rerun in this review session. The dedicated full-run evidence was
checked against the supplied timestamp. Preserve the two known update-test skips
and TestDrive missing-path/nonempty-directory cleanup caveat. Successful cleanup
is not claimed. No evidence found here invalidates the recorded passing
assertions; those assertions do not resolve the six review findings.

The first one-line deadline probe failed due to PowerShell argument quoting.
It was rerun through Python stdin and produced the result recorded above. This
was a review-harness error, not a product test failure or implementation recovery
attempt. No source was changed for any probe. The lifetime-limit probe reduced
only an in-memory constant; it did not run 10,000 scans.

The bounded Brain query returned the trust-anchor solution and the current plan,
with 596 index warnings. `open-brain` tools were unavailable. The current plan,
not an older main-only policy, supplied the authority rules. Public GitHub secret
API and bot-signing documentation was consulted; it was not live repository
capability evidence and did not establish a separate protocol finding.

## Handoff

All six finding IDs are open. Phase 3 completion remains blocked by P1.1-P1.3.
The passing test evidence and prior Phase 1/2 completion remain historical facts,
not approval of these defects. This review makes no phase-checkpoint changes and
does not reset any recovery counter. Return the findings to the implementation
session for its separately authorized in-scope repair and independent verification.
