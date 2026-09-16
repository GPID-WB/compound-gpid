---
date: 2026-09-13
title: "Release controller authority and evidence must stay bound at each continuation"
category: "git-workflows"
language: "Python"
tags: [release-controller, authority, recovery, provenance, deferred-rollout]
root-cause: "Earlier authority checks and local gate success were insufficient evidence for later effects, independent approval, or live rollout"
severity: "P1"
plan: ".cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md"
reviewed-in: ".cg-docs/reviews/2026-09-13-generic-asynchronous-release-controller-phase6-P1.15-continuations-verification.md"
---

# Release Controller Authority And Evidence Boundaries

## Problem

The asynchronous controller has durable intents, remote effects, result records,
and recovery paths. An authority check before one operation did not authorize a
later operation after intervening reads or a completed effect. Phase 6 P1.15
required a finite audit of these continuation boundaries, not a callback-presence
check alone.

Phase 5 also found that reviewed recovery after source deletion and a policy
change could be admitted but fail at approval routing. The original request had
no override reason; the verified recovery directive supplied the new reason.
Changing the original request or bypassing protected approval was not a valid fix.

Local test success presented a separate reporting risk. It could not establish
actual bridge delivery, remote protection enforcement, or the tracked handoff
performance target. These were missing evidence, not solved by more local passes.

## Root Cause

- A completed authorized operation is not a permission lease for its successor.
- Recovery admission, current human authority, and independent protected approval
  are separate checks with separate identities.
- A local checkpoint, fake provider response, source freeze, or HEAD value does
  not prove a live effect or identify every dirty and untracked byte.

## Solution

The verified Phase 6 repair renews applicable human authority before each
separately started continuation operation. Current
`packages/cg-release/src/cg_release/profile_dispatch.py` uses this order:

```text
fresh authority -> durable intent
fresh authority -> dispatch POST
fresh authority -> dispatch-result record
```

Revocation after the intent prevents the POST. Revocation after an accepted POST
preserves the intent but prevents the result record. Recovery must reconcile
that uncertainty; it must not erase the authorized prefix or blindly replay it.
The audit also covered registration, absence records, evidence PR writes,
composition, owner release, hook completion, restore, and recovery audit retries.

In `publication_inputs.make_inputs`, the route uses the original override reason
or, only when a verified grant exists, its directive reason. A recovery grant
still selects the protected override environment. The request and exact tag
object remain unchanged. The requester and recovery reconfirmers remain excluded
from independent approval; current authority does not replace that approval.

### Verified Evidence

- [Phase 5 verification](../../reviews/2026-09-12-generic-asynchronous-release-controller-phase5-verify-review-2.md)
  reports 703 package passes, four full recovery variants, and seven additional
  refusal probes. The changed-policy paths retained one tag write and the exact
  saved tag object. Probe counts overlap the package suite.
- [Phase 6 finite verification](../../reviews/2026-09-13-generic-asynchronous-release-controller-phase6-P1.15-continuations-verification.md)
  assessed all 15 audit rows. Its 62-case repair matrix, 78 independent cases,
  and 94 adjacent checks passed. These used real authority and journal paths
  with bounded fake outer services, not live GitHub enforcement.
- [Step 9 triage](../../reviews/2026-09-13-generic-asynchronous-release-controller-step9-fix-triage.md)
  retains all 71 prior phase closures and adds one tested P1.1 repair. Two fixture
  repairs are not two extra finding IDs. This is not 72 newly independent
  confirmations. Independent step 9 verify-review convergence is not claimed.

### Completion And Deferral

The compact phase-final records are the evidence entry points, not one combined
test run. Phase 1 through Phase 5 records are
`2026-09-11-phase1-final-evidence.json`,
`2026-09-11-phase2-final-evidence.json`,
`2026-09-11-phase3-final-evidence.json`,
`2026-09-12-phase4-final-evidence.json`, and
`2026-09-12-phase5-final-evidence.json` under
`.cg-docs/work-reports/release-controller/`. They retain local/offline scope and
their original test and review qualifications.

The older [Phase 6 blocked record](../../work-reports/release-controller/2026-09-13-phase6-final-evidence.json)
is unchanged history. The later [approved deferral](../../work-reports/release-controller/2026-09-13-phase6-accepted-deferral.json)
records `D-2026-09-13-defer-live-rollout`. Together with the
[Phase 7 final record](../../work-reports/release-controller/2026-09-13-phase7-final-evidence.json),
it permits seven completed local phases while the plan remains active and V8
remains pending. The publisher stays disabled.

Deferred, **not passed**: legacy-channel bridge delivery; actual Windows and
native Unix clean-client receipts; registered source-bound release-mode CI;
sandbox, hostile-source, signing and approval trials; remote object identity;
and live performance. Later rollout needs separate reviewed authority and the
exact receipts listed as D1-D4 in the accepted-deferral record. No local failure
is excused by that deferral. No speedup is established without a comparable
legacy baseline.

### Evidence Limits

- Fresh checks are finite observations, not atomic permission checks across
  principals or an atomic GitHub read/effect transaction. Authority can change
  after the final observation or during an already-started bounded operation.
- Step 9 reports 995 package passes and 2,935 Pester passes, zero failed
  assertions, and two skips. Pester cleanup failed: 615 diagnostic occurrences
  comprise 580 removal errors and 35 missing-path errors. These are not 615
  distinct defects. Individual skip names/reasons remain unknown.
- The expected negative `Target mapping not found` fixture error is separate
  from cleanup and skips. Do not suppress it or count it as an unexpected failure.
- Windows Git Bash, the Pester Bash placeholder, portable Node file-link checks,
  and adapter-only Kilo containment do not qualify native Unix, native Windows
  file symlinks, or live VS Code/Kilo. A direct-child wait does not prove that all
  descendants have finished.
- Preserve failed runs and raw logs. Later evidence changes disposition, not
  historical bytes. Ignored logs and temporary probes are local evidence, not
  automatically committed or approved for publication. Review host metadata
  before any later authorized publication.

## Prevention

- Test late revocation at real callers with both negative and authorized positive
  controls. Keep authority functions real; replace only outer service boundaries.
- Bind recovery and approval to exact request, policy, source, tag, run and actor
  identities. Never rewrite a protected tag to repair a stranded release.
- Track assertion results, cleanup, skips, host scope, source identity and remote
  proof separately. Do not sum overlapping suites as unique coverage.
- Preserve closure IDs and counters. Reporting, approval-only pauses, and fixture
  diagnosis are not grounds to reset or invent product repair attempts.
- Complete and check generated documentation before reviewing or publishing it.
  Changed output must not be presented as previously reviewed output.
- After a separately authorized pipeline step 11 candidate commit, V8 requires
  `python scripts/cg_pr_preflight.py --phase committed --full-gate --run-native-target`.
  Ordinary PR CI, including the six-cell package matrix and stable aggregate,
  remains required and is not covered by the live deferral. Prepare-mode success
  cannot replace this exact committed-input gate.

## Related

- [Immutable trust anchors and captured bytes](../bugs/2026-08-31-trust-anchor-captured-byte-dispatch.md)
- [Default test environments and executable fixtures](../testing-patterns/2026-09-13-clean-default-release-gates-and-executable-fixtures.md)
- [Windows GPG socket path diagnosis](../environment-issues/2026-09-13-windows-gpg-agent-socket-path-budget.md)
- [Integration contract](../../../.github/shared/release-controller.contract.md)
- [Controller operator guide](../../../docs/release-controller.md)
