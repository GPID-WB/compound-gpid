---
date: 2026-09-12
depth: light
type: verification
parent-review: .cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase5-review.md
plan: .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P2.1: fixed
  P2.2: fixed
  P1.4: fixed
---

# Phase 5 Repair Verification

## Result

Original findings confirmed fixed: **5**. Original findings still open: **0**.
New findings: **1**, P1.4. Total open: **1** (P0: 0, P1: 1, P2: 0, P3: 0).
**Phase 5 and V5 must remain incomplete until P1.4 is repaired and verified.**

Completed `cg-code-quality`, then `cg-testing`, using their local specs
sequentially in this independent verification session. This is two spec passes,
not two independent agent sessions. No incomplete spec output or suppressed
correctness, security, or cross-file finding.

## New Finding

### P1.4: Sealing Discards The Reviewed Recovery Override Reason

**[P1.4]** [cg-testing]
`packages/cg-release/src/cg_release/publication_inputs.py:203-212`.

**Issue:** After validating an audited maintainer recovery grant, `make_inputs`
calls `approval_route` again with only `request.override_reason`. An original
stable release from an eligible production branch has no override reason. If
current policy no longer lists that branch, this call raises `E_BRANCH` before
the following grant-specific override route can take effect.

The preceding authority paths accept the reviewed recovery reason:
`recovery_authority.py:28-35` uses
`request.override_reason or grant.directive.reason`, and
`stranded_recovery.py:166-173` uses the equivalent directive reason during
recovery admission. Thus the audited recovery, manual resume, exact-source
rebuild, and new build registration succeed, but the new publication seal cannot
be created. This is a cross-function recovery contract failure, not an authority
bypass. It does not invalidate the original P1.3 revoked-requester reproduction,
which now passes.

**Executed proof:** A new in-memory test used `BoundedTransport`, the real CLI,
controller, build worker, and publisher entry points. No production function was
replaced other than the existing fake I/O and clock boundaries.

1. Set the initial policy's production branches to `[feature]`. Start stable
   `1.0.0` from `feature`, with no branch override option or reason. Complete
   preparation and build, seal with the normal publish environment, then stop
   before the first asset write. The fake server retains one exact tag and draft.
2. Mark that publisher run terminal and advance the fixture clock beyond its
   credential expiry. Change current policy's production branches to `[main]`,
   remove `feature`, and revoke original requester 7 to `read`.
3. Install the new policy and a valid `source-exception` directive in an exact
   protected-default fixture commit. The directive retains the original request,
   tag object, release SHA/tree, and supplies reason
   `Reviewed stable branch policy recovery`. Recovering maintainer 456 remains
   authorized. Git blob/tree identities are recomputed for the directive.
4. Run the real reviewed recovery entry point and CLI resume. Both succeed.
   Complete replacement build ticket 2, register run 22/artifact 52, and return
   to `awaiting-approval` under current policy.
5. Start publication run 42 and attempt its seal. Expected success fails with
   `E_BRANCH: Stable release needs a production branch or a maintainer override.`
   The error reports `step: publication-registration-2` and
   `observed: awaiting-approval`. The fake tag-write count remains exactly one.

The one additional probe failed in 6.13 seconds. It replaced one collected test
callable through an in-memory pytest plugin; no test file was edited. It reused
`test_phase5_transport.prepare`, `publisher`, `test_worker_e2e.worker`, and
`test_phase5_review_repairs.BoundedTransport`. This is a new negative review
probe, not a failure of the unchanged 701-test suite.

**Impact:** A valid current-policy maintainer recovery can leave an immutable tag
and draft unresolved indefinitely. Further resume attempts encounter the same
old null reason. Rewriting the sealed request or restoring obsolete branch
policy is not an acceptable recovery requirement. The plan's publication and
recovery contract, lines 498-506, requires reviewed maintainer recovery under
current policy without changing the original inputs or tag/assets.

**Fix:** Use the verified recovery directive's reason consistently when computing
the audited publication route. Preserve the original request, ordinary resume
checks, current maintainer checks, and fresh independent override approval. Add
the full-path case above with an originally non-override stable request. Do not
weaken branch policy for ordinary publication or accept an unverified reason.

## Original Findings

### P1.1: Encoded Journal Capacity

**Confirmed fixed for the original failure.** `process.py:12-16,181-199` retains
a finite 262,144-byte input bound. `journal_transport.py:11-49` is the shared
encoder used by real writes in `github_journal.py:140-172` and publication
capacity checks. Individual journal files remain bounded at 65,536 bytes.

`publication_capacity.py:10-99` projects the remaining result evidence and actual
encoded transaction before an irreversible publication effect.
`publisher.py:82-83,127-150` applies that check before writes, and
`publication_control.py:25-46` checks a new tagged-recovery seal before retaining
it. Draft evidence stores a notes digest rather than another complete notes body
at `publisher.py:162-192`; remote matching still checks the exact body.

Executed both bounded full-path cases at `test_phase5_review_repairs.py:74-131`:
6,000 added note characters, four declared artifacts, and two recovery runs;
15,000 added note characters and four artifacts. Transactions exceed the old
65,536-byte bound, complete successfully, and retain exactly one tag write.
The near-capacity refusal at lines 196-216 happens before any tag or Release
write. `test_process_input.py:25-58` checks the new rejection boundary and the
maximum file envelope through real local Git stdin. No limit was removed.

### P1.2: Absent Retained Artifact

**Confirmed fixed.** `artifact_download.py:8-39` distinguishes a complete empty
inventory or verified expiry from denied reads and conflicting identity.
`build_stage.py:218-242` creates a fresh exact-source ticket for absence as well
as expiry. The post-tag route still checks authority, old owner termination and
credential expiry, reconciled publication effects, and immutable source evidence
in `publication_rebuild.py:14-91`.

Executed pre-tag absence and all six conflicting-inventory cases in
`test_phase5_review_repairs.py:176-193,219-262`. Executed both post-tag cases in
`test_phase5_transport.py:180-257`, then repeated them with `BoundedTransport`
instead of the older base fake. Both expiry and zero-row absence complete the
replacement build/registration and fresh approval without a second tag write.
401/403, duplicate names, wrong run, replaced ID, and renamed archive remain
typed hard failures. Prior build and publication evidence remains append-only.

### P1.3: Revoked Original Requester

**Confirmed fixed for the original finding.** `recovery_authority.py:8-35` keeps
ordinary `authorize_resume` when no exact grant exists. A grant instead requires
current maintainer authority and current policy. `stranded_recovery.py:55-98`
binds it to the directive digest, original request, release SHA/tree, and tag.

The grant is used by controller reconciliation, CLI resume, build ticket
creation, build registration, rebuild recovery, and publication input acquisition:
`controller.py:104-115`, `runtime.py:169-188`, `build_stage.py:35-53`,
`build_worker.py:146-147`, `publication_rebuild.py:20-32`, and
`publication_inputs.py:192-212`.

Executed both reviewed deleted-source recovery variants in
`test_phase5_transport.py:403-532`, then repeated both with `BoundedTransport`.
The revoked variant proves ordinary resume fails, reviewed maintainer recovery
succeeds, and a new build/registration/seal/publication completes with requester
7 still revoked and one tag write. P1.4 is the separate newly reproduced branch
policy case omitted by these original fixtures, which start with an override.

Approval exclusions remain distinct from current authority.
`publication_approval.py:11-27` retains all historical ticket reconfirmers,
recovery actors, and human triggers. `publish_worker.py:84-87` retains the
original requester in the seal, and `approval.py:64-85` excludes that requester
and every reconfirmer. The original requester and reconfirmer rejection tests
and `test_recovery_authority_history.py` pass.

### P2.1: Repeated Archive Transfers

**Confirmed fixed.** `publish_worker.py:110-120,171-193` creates one cache per
protected job and still rechecks owner, approval, and current publication inputs.
`publication_inputs.py:84-168` rechecks run/attempt/jobs and artifact metadata
before cache use. Its key includes the sealed build, registration, and complete
current artifact metadata; returned data is a separate mapping.

Executed the transfer-count and cache invalidation cases in
`test_phase5_review_repairs.py:134-148,265-292`: one protected-job archive
transfer, a new transfer in a new job, skipped-job refusal, and re-verification
after digest metadata changes. Three additional bounded fake-wire probes changed
requester authority, protected approval, or protected-default revision immediately
after the tag write. Each stopped before draft creation, with one archive
transfer and the expected typed error. Mutable checks were not replaced by the
byte cache. This is an operation-count result, not measured live latency.

### P2.2: Publisher Error Context

**Confirmed fixed.** `journal.py:21-86` updates diagnostic records only after
complete verified replay. `publication_output.py:31-65` uses those local records
without additional recovery reads. `publish_worker.py:218-219,283-290` retains
parsed identity and emits the contextual typed event.

Executed all three error-context regressions at
`test_phase5_review_repairs.py:151-173`: pre-write read denial and uncertain tag
and draft outcomes. They retain request, version, checkpoint/intent, expected and
last verified state, elapsed time, and reconciliation guidance. The three extra
fresh-gate probes also preserve request/state after a tag write. P1.4's actual
error retains the new run's last verified registration checkpoint. Unknown
outcomes are not reported as successful writes; raw API bodies and credentials
are not added to events.

## Scope And Method

Authority was the latest exact execution-report section, **Phase 5 Review Repair
Cycle 1 Handoff 2026-09-12T06:54:09Z**, lines 2726-2812, including **Exact Final
Handoff** at lines 2776-2808; the original Phase 5 review; and
`.cg-docs/work-reports/release-controller/2026-09-12-phase5-review-repair-1-evidence.json`.
Earlier report sections are historical, not replacement handoffs. The original
review intentionally retains open statuses; the explicit verification request
requires checking all five IDs regardless of those statuses.

Direct inspection covered the five repair scopes and related journal, process,
artifact, authorization, approval, worker, policy, and recovery interfaces named
above, plus their fixtures and targeted tests. The full package suite exercised
other modules without implying a new full review of Phases 1-4. Excluded source
environments, build outputs, caches, unrelated tracked changes, and Phase 6/7
deliverables. No live hosting, protected-environment enforcement, remote matrix,
production enablement, or latency result is claimed.

Applied project/Python instructions and the Python skill and pytest guidance.
Consulted the local solution
`.cg-docs/solutions/testing-patterns/2026-08-13-release-gate-fixtures-and-derived-evidence-hashes.md`:
fixtures must model the actual external command protocol. `open-brain` tools
were unavailable. Protected knowledge, charter/configuration, roadmap, schema,
and workflow infrastructure were preserved.

| Order | Spec | Result |
|---|---|---|
| 1 | cg-code-quality | No separate actionable style, naming, or lint finding in the repaired encoder, capacity, artifact, cache, error, and authority code. Ruff passed. Cross-function behavior was carried into the testing pass. |
| 2 | cg-testing | Confirmed the five original reproductions fixed. Found new P1.4 with an executable bounded fake-wire recovery scenario. No incomplete output or automatic review retry. |

## Executed Evidence

| Check | Result | Qualification |
|---|---|---|
| Complete package pytest | 701 passed, 0 failed, 247.33 seconds | Executed with locked offline Python 3.12; includes installed-wheel and real temporary Git/GPG tests. |
| Original absence/revocation paths with `BoundedTransport` substituted in memory | 4 passed, 27 deselected, 32.67 seconds | Both post-tag retention variants and both reviewed source-recovery variants. |
| New post-tag authority/approval/policy cache probes | 3 passed, 5.86 seconds | Each stopped before draft creation with one archive transfer. |
| New audited branch-policy recovery probe | 1 failed, 6.13 seconds | New P1.4, after successful reviewed recovery and replacement build; not an unchanged-suite failure. |
| Package/benchmark Ruff | Passed | `uv run --offline --project packages/cg-release --python 3.12 --locked ruff check packages/cg-release scripts/benchmark_release.py --output-format concise`. |
| `git diff --check` | Passed | Tracked whitespace only; does not inspect the untracked package. |
| Fresh canonical Pester artifact | 2026-09-12T07:06:28Z; gitSha b94f585; passed true; total 2906; passed 2904; failed 0; skipped 2; failures []; filteredFiles null | Read directly from `tests/last-run.json`; dedicated sibling result, not rerun by this verifier. |
| Native preflight pytest | Repair handoff reports 52 passed | Not independently repeated; no claim of new preflight execution. |

The complete package run used `uv run --offline --project packages/cg-release
--python 3.12 --locked python -c` to call `pytest.main` with
`packages/cg-release/tests -q --tb=short`. Its wrapper set `UV_OFFLINE=true` and
`GIT_ALLOW_PROTOCOL=file`, and installed an audit guard to reject real `gh`,
network Git URLs, and Python socket connections. The extra probes also guarded
real `gh` and socket execution and used bounded fake I/O. Guards did not fire.

**Transport safety:** The unsafe old oversized-input probe was not run.
`BoundedTransport.run` at `test_phase5_review_repairs.py:59-71` replaces `_capture`
while exercising real `run_process` validation for every submitted input body.
Accepted bodies therefore reach only the fake server, never live `gh`.
The maximum-envelope stdin test uses local Git only. Extra probe changes existed
only in process memory; they did not change repository source or test files.

**Pester qualification:** Retain the supplied TestDrive missing-path/nonempty-
directory cleanup caveat. Zero failed assertions does not establish successful
cleanup. Both skips are in `update`; their names and reasons are not in the
artifact. `create-release` passed 95/95 with no skips. No cleanup or Pester command
was attempted here. This 07:06:28Z result supersedes the repair evidence file's
pending post-repair Pester field, not its historical pre-repair record.

## Handoff

Only this new report was manually created. No source/test edits, original-review
edits, plan completion, active-state update, remote operation, commit, push, PR,
or Phase 6 work occurred. Existing worktree changes were preserved.

Return the five confirmed original IDs and new open P1.4 to the parent. The
parent owns original-status reconciliation and any authorized repair. Do not
mark Phase 5/V5 complete while P1.4 remains open. No implementation recovery
counter was reset or consumed by this independent review probe.
