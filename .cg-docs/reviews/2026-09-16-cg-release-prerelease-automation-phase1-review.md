---
date: 2026-09-17
depth: full
type: standard
plan: .cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md
findings:
  P1.1: fixed
  P2.1: fixed
  P2.2: fixed
---

# Phase 1 Review

## Source And Scope

Parent supplied completed full-route review results from reviewer task
`ses_f530fa096ffed2DDrrKHB2gkZE`: 10/10 required specifications complete,
3 findings (0 P0, 1 P1, 2 P2, 0 P3), all tagged manual. This report preserves
the supplied findings; individual reviewer transcripts remain with the parent.
Scope: Phase 1 receipt producer, consumer, tests, and workflow records only.

## Findings

- **[P1.1] [manual]** `scripts/cg_pr_preflight.py:1218-1239` (reviewed revision): clean Git status and autocrlf/eol configuration do not prove physical LF bytes. Normalized CRLF or assume-unchanged can evade the guard. Own a fresh checkout or validate physical identity and transforms, including intentional CRLF exceptions. Require real Git tests.
- **[P2.1] [manual]** `scripts/cg_pr_preflight.py:1321-1323`, `create-release.ps1:324-332` (reviewed revision): command equality depends on the verifier's Python executable path. Valid evidence from another environment can cause an unnecessary full gate. Define a logical command/interpreter contract without executing the recorded interpreter; test differing paths.
- **[P2.2] [manual]** `scripts/cg_pr_preflight.py:1391-1393,1265-1273,1450-1457` (reviewed revision): concurrent writers can leave an earlier successful receipt after a later gate fails. Enforce exclusive destination ownership or run identity and test deterministic interleaving.

## Repair Authorization And Status

The user explicitly instructed Phase 1 repairs on 2026-09-17. All three are
implemented and independently verified with final runtime evidence. No finding
was ignored, skipped, or downgraded.

- P1.1: receipt-producing runs create and own a fresh LF-configured clone at the selected commit. Real Git regression cases hide CRLF, assume-unchanged and skip-worktree edits in the source; the gate must see original LF bytes and intentional CMD CRLF bytes in a different checkout.
- P2.1: exact logical command order and arguments remain required. One consistent absolute Python path may differ from the verifier path. The receipt keeps original command tuples and digest; the verifier never launches a recorded path.
- P2.2: an exclusive external `.lock` is acquired before receipt invalidation and held through the gate and atomic publication. A colliding invocation cannot start. A later owner invalidates prior success before running. Locks remain after an uncatchable process termination; automatic takeover is forbidden.

## Verification History

The parent subsequently supplied 143 passing Python cases and an unfiltered
Pester result with 3029 passes, zero failures and two update skips. TestDrive
cleanup diagnostics remain qualified in the work report. The reviewer confirmed
the fixture correction and four failure cases. Acceptance then exposed a runner
constraint: no Git config updates. The producer now applies LF settings through
command-local `git -c` flags, including read-only provenance queries, with no
persistent config writes. New focused results and delta verification are pending
for this adjustment; real acceptance remains required before closing findings.

Parent supplied independent static confirmation of all three repairs on
2026-09-17, with no new P0/P1 or cross-file findings. Runtime confirmation remains
pending. The first post-repair Python run found a normalized-CRLF fixture setup
failure before production execution; the fixture was corrected without weakening
the byte-mismatch assertion. Four checkout-preparation failure tests were added
in response to the reviewer's coverage note. Post-repair targeted Pester passed
136 cases with no failures or skips.

Focused Python and Pester repair tests, the current unfiltered Pester boundary
gate, real isolated full-gate receipt acceptance, and independent delta review.
These were historical pending gates; the final closure below supersedes them.

## Final Closure: 2026-09-17

- Latest independent reviewer confirmation: all three findings fixed; final command-local settings adjustment has no new issues.
- Final focused tests: 143 passed, 0 failed, 3 skipped.
- Final unfiltered Pester: 3029 passed, 0 failed, 2 update skips; artifact ranAt `2026-09-17T01:48:32Z`, filteredFiles null. TestDrive cleanup diagnostics are retained in the work report.
- Actual isolated committed gate: 9 commands, all exit 0. Receipt verifier exit 0. PowerShell receipt-check acceptance exit 0, receiptAccepted true, rerun skipped. No live publication.
- Snapshot commit `9eaf1b6ab270ea5fa00f13fde6d7131162ea8bb7`; source and snapshot hashes matched and source hashes were rechecked before closure. Full identities and receipt digest are in `.cg-docs/work-reports/2026-09-17-cg-release-prerelease-automation.md`.
- Full review coverage: 10/10 specifications. Three findings fixed, zero open, zero skipped, zero new issues. Phase 1 review is complete.
