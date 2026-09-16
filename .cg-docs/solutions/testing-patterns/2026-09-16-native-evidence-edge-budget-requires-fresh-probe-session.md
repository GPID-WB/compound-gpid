---
date: 2026-09-16
title: "Bounded native-evidence edge budget requires a fresh low-edge session for clean probes"
category: "testing-patterns"
language: "both"
tags: [kilo, native-evidence, plugin, edge-budget, probe-hygiene, session, autopilot, bounded-observer]
root-cause: "The bounded native-evidence observer enforces one four-edge Task inspection budget per acquisition, so sessions that already dispatched several Task edges can only produce blocked edge-limit receipts"
severity: "P2"
status: "confirmed-by-human"
plan: ".cg-docs/plans/2026-09-12-autopilot-native-evidence-revision.md"
related: [".cg-docs/solutions/bugs/2026-09-16-kilo-deny-first-task-baseline-blocks-subagent-dispatch.md"]
---

# Bounded Native-Evidence Edge Budget Requires a Fresh Low-Edge Session for Clean Probes

## Problem

Native bootstrap probes intermittently returned `blocked: edge-limit` or
`blocked: native-identity-unverified` receipts while the parent's own
`cg_native_identity` call stayed healthy. Repeated attempts in the same session
failed identically, looking like a permission or metadata defect:

- Child `ses_f5ed7494effeJwc3SPTIbAS6RK`: `cg_native_identity` returned
  `blocked: edge-limit` while its parent identity read was healthy (report
  "Live Passive Identity Observed 2026-09-14T18:24:51Z").
- Probe `phase1-20260914-stage-general-03`: attempt 2 receipt
  `native-identity-unverified`, child identity blocked `edge-limit` (report
  "Fresh Probe Outcomes 2026-09-15T14:00:44Z").
- Probe `phase1-20260915-stage-fix-general-02`: blocked
  `native-identity-unverified` after three actual attempts, no effects —
  dispatch #5 in that session tripped the cap (report "Phase 6 Step 16 Final
  Native Conformance Round 2026-09-16T02:37:36Z").

## Root Cause

The bounded observer is working as designed. All scanned native Task parts
share one four-edge inspected budget per acquisition, including siblings:
`LIMITS = Object.freeze({ page: 50, pages: 20, sessions: 5, edges: 4,
depth: 3, ... })` at
`.github/plugin-support/cg-native-evidence/transport.mjs:3`, enforced
fail-closed by `requireEvidence(inspected.size < reader.limits.edges,
'edge-limit')` at `.github/plugin-support/cg-native-evidence/records.mjs:74`
(documented at `records.mjs:18`; FR-09 "one distinct inspected-edge budget
across ancestors/descendants"). A long-running session whose own subtree
already contains more than four Task edges cannot produce clean positive edge
evidence; every new child identity traversal trips the shared cap. This is not
a runtime defect, permission failure, or metadata readiness problem.

## Solution

Operational fix, no code change:

- Run each native graph probe in a FRESH dedicated `cg-autopilot` session
  (new session ID) so the subtree edge count starts at zero.
- Make the deepest or most expensive probe the FIRST dispatch of the session.
- Use a fresh probe-id per attempt; never reuse or resume a task_id from a
  failed or transport-interrupted attempt (disqualified by the contract).
- Distinguish `edge-limit` from real failures: read the parent's
  `cg_native_identity` immediately after — observed/healthy parent identity
  with the same scope hash plus child `edge-limit` means the cap, not a
  permission defect. Also note `qualification: unverified` on
  `cg_native_identity` is EVIDENCE-ONLY semantics, not an identity failure.

## Evidence

- Final closure probe `phase1-20260916-stage-fix-general-01` SUCCEEDED
  (conditional depth 3, status `succeeded`, reason `null`, three settled
  `allowed` observations) as the first dispatch of fresh session
  `ses_f5624a8d3ffeVWBBXQSxda2ipb` (report "Step 16 Final Native Conformance
  Closure 2026-09-16T12:46:05Z").
- Offline guard: `scripts/tests/test_native_evidence.py` (9 passed, 0 failed,
  0 skipped under actual Node 24.21.0 and installed SDK 7.6.2); full Node
  suite 125 passed / 0 failed / 0 skipped.

## Confirmation

Status `confirmed-by-human`: the blocked edge-limit receipts and the
successful fresh-session probe were recovered from user-driven dedicated
`cg-autopilot` sessions and recorded as user-reported native evidence in
`.cg-docs/work-reports/2026-09-11-kilo-first-autopilot.md`; the parent/user
drove each probe and supplied the receipts.

## Prevention

- Treat the edge budget as a scarce shared resource: one session, at most four
  inspected Task edges across all acquisitions; plan probe order accordingly.
- Never retry a blocked edge-limit receipt in the same session expecting a
  different result — it is deterministic given the subtree size.
- Record the session ID and dispatch ordinal of every probe; "third probe in
  session, dispatch #5" is exactly the signature that tripped the cap.
- Keep the bound fail-closed: do not raise `LIMITS.edges` without a new
  reviewed approval; the cap is a safety property, not a tuning knob.

## Related

- `.cg-docs/solutions/bugs/2026-09-16-kilo-deny-first-task-baseline-blocks-subagent-dispatch.md`
- `.cg-docs/work-reports/2026-09-11-kilo-first-autopilot.md`
- `.cg-docs/plans/2026-09-12-autopilot-native-evidence-revision.md`
