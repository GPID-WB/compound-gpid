---
date: 2026-09-12
depth: light
type: verification
parent-review: .cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase5-verify-review.md
plan: .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P2.1: fixed
  P2.2: fixed
  P1.4: fixed
---

# Phase 5 Repair Verification 2

## Result

**P1.4 is confirmed fixed. No new findings or remaining scoped blockers.**
Preserved the five prior confirmed IDs: P1.1, P1.2, P1.3, P2.1, and P2.2.
Total confirmed fixed: 6. Total open: 0 (P0: 0, P1: 0, P2: 0, P3: 0).

Applied `cg-code-quality`, then `cg-testing`, sequentially in this independent
verification session. These are two local spec passes, not two independent agent
sessions. Both passes are complete. No source or test file was edited.

## P1.4 Confirmation

`packages/cg-release/src/cg_release/publication_inputs.py:189-211` first obtains
the verified recovery grant. It now passes the original override reason, or the
verified directive reason when the original reason is absent, to `approval_route`.
The audited route still requires the protected override environment. Without a
grant, ordinary publication receives no new fallback reason.

The reason now agrees with recovery admission at `stranded_recovery.py:166-173`
and current authority checks at `recovery_authority.py:8-35`. Grant validation at
`stranded_recovery.py:55-98` still binds the directive digest, original request,
current policy, release SHA/tree, tag object ID, and current maintainer. Recovery
admission reads the exact protected-default directive at
`recovery_actions.py:176-208` and checks its supplied digest.

The original request remains unchanged. The new seal retains its null
`override_reason` and separately binds the recovery digest, actor, and run at
`publication_inputs.py:274-278`. Current authority is not a replacement for
independent approval: `publish_worker.py:73-89,100-124,171-193`,
`publication_approval.py:11-27,30-93`, and `approval.py:64-85` retain the original
requester and all reconfirmers in the exclusion set and recheck exact approval.

Executed all four variants of
`test_phase5_transport.py::test_reviewed_recovery_workflow_handles_deleted_source_without_moving_tag`
in the full suite, then repeated all four with `BoundedTransport`.
The two `policy_changed=True` cases at lines 403-593 reproduce the P1.4 scenario:

1. Start stable `1.0.0` from initially eligible `feature`, without an override
   option or reason. Seal under the normal publication environment.
2. Stop after the fake server has the exact tag and draft. Mark the old run
   terminal and advance the fixture clock beyond credential expiry.
3. Change current production policy to `main`, delete `feature`, and either keep
   requester 7 authorized or revoke that requester to `read`.
4. Confirm ordinary resume fails with `E_STALE_POLICY` before a grant. Execute
   reviewed maintainer recovery and resume, create replacement build ticket 2,
   register run 22/artifact 52, and return to `awaiting-approval`.
5. Create seal 42 under the protected override environment and complete publication
   with independent reviewer 999. The request and saved exact tag object remain
   unchanged, the original reason remains null, requester 7 and recovery actor
   456 remain excluded, and the total tag-write count remains one.

Both changed-policy cases now pass sealing and publication. The two unchanged-
policy recovery variants also pass. No policy or authority check was removed.

## Nearby Refusal Probes

Seven additional in-memory probes reused the real CLI, controller, build worker,
and publisher through the changed-policy, revoked-requester recovery scenario.
Every world was a `BoundedTransport`. Only fake input/output boundaries, fixture
state, and test entry wrappers were changed; production validators were not
replaced.

| Probe | Result |
|---|---|
| Revoke maintainer 456 immediately before seal 42 | `E_AUTHORITY`; stopped at `publication-registration-2` |
| Revoke maintainer 456 after seal 42, before protected publication | `E_AUTHORITY`; retained `publication-seal-42` context |
| Make original requester 7 the only permitted approving reviewer | `E_APPROVAL`; requester exclusion still applies despite environment permission |
| Make recovery actor 456 the only permitted approving reviewer | `E_APPROVAL`; recovery reconfirmer exclusion still applies |
| Remove approvals for run 42 while keeping prior run evidence | `E_APPROVAL`; no reuse of earlier approval |
| Supply normal-environment approval instead of override approval for run 42 | `E_APPROVAL`; exact protected environment required |
| Submit an incorrect, well-formed recovery directive digest | `E_RECOVERY_AUTHORITY`; audited recovery not admitted |

Each final probe asserted no additional publication write, unchanged fake tag,
Release, and asset state, and exactly one prior tag write. Publisher refusals
retained request identity, checkpoint, and last verified state. These checks
support the nearby authority, approval, immutable publication, and error-context
contracts; they do not establish live GitHub enforcement.

## Prior Confirmations

The following statuses are carried forward from the first independent Phase 5
verification. Their package regressions also passed in this session. This narrow
pass does not claim a second full source audit of all five repairs.

| ID | Preserved status and regression evidence |
|---|---|
| P1.1 | Fixed; bounded notes/inventory/recovery envelopes, pre-write capacity refusal, and local Git stdin limits passed |
| P1.2 | Fixed; pre-tag absence, both post-tag retention variants, and conflicting or denied artifact inventory cases passed |
| P1.3 | Fixed; both requester-authority variants and the new changed-policy variants passed; ordinary pre-grant refusal remains |
| P2.1 | Fixed; one protected-job archive download, job-local cache, and stale gate/digest rejection tests passed |
| P2.2 | Fixed; pre-write and uncertain tag/draft error-context regressions passed; new publisher refusal probes retained context |

## Coverage And Authority

Read the original Phase 5 review and first Phase 5 verification report in full.
Used the exact execution report section **Phase 5 Review Repair Cycle 2 Handoff
2026-09-12T07:49:07Z**, lines 2824-2910, including **Independent Handoff** at
lines 2887-2906. Also read
`.cg-docs/work-reports/release-controller/2026-09-12-phase5-review-repair-2-evidence.json`.
Earlier handoffs and test results remain historical evidence, not current scope.

Direct source inspection covered `publication_inputs.py`, `recovery_authority.py`,
`stranded_recovery.py`, `recovery_actions.py`, `recovery_models.py`, `policy.py`,
`authority.py`, `publication_approval.py`, `approval.py`, and `publish_worker.py`.
Inspected the full recovery tests, bounded transport, base transport, and relevant
publication-input, worker, stranded-recovery, and approval-history fixtures.
The plan's approval and recovery contract at lines 464-506 remained authoritative.

| Order | Spec | Outcome |
|---|---|---|
| 1 | cg-code-quality | No actionable style, naming, duplication, or error-handling finding in the scoped repair and adjacent interfaces. Ruff passed. |
| 2 | cg-testing | Confirmed P1.4 through full-path execution and checked seven additional refusal cases. No new actionable coverage or correctness finding. |

Applied project instructions, project configuration and charter, Python
instructions, and the Python skill's anti-pattern and pytest guidance. The local
Brain lesson
`.cg-docs/solutions/testing-patterns/2026-08-13-release-gate-fixtures-and-derived-evidence-hashes.md`
supports complete wire-protocol fixtures and correct derived identities.
`open-brain` tools were unavailable; the local solution was read directly.

Excluded a new full review of Phases 1-4, unrelated worktree changes, Phase 6/7
deliverables, generated views, build/cache directories as source, live remote
trials, production enablement, and latency claims. Protected project artifacts
were preserved.

## Test Evidence

| Check | Result | Qualification |
|---|---|---|
| Independent complete package pytest | **703 passed**, 0 failed, 267.34 seconds | Locked offline Python 3.12; unchanged suite, including installed-wheel and temporary local Git/GPG tests |
| Four recovery variants plus seven extra bounded refusal probes | **11 passed**, 0 failed, 64.37 seconds | In-memory pytest plugin; all four worlds used bounded transport |
| Package and benchmark Ruff | Passed | `uv run --offline --project packages/cg-release --python 3.12 --locked ruff check packages/cg-release scripts/benchmark_release.py --no-cache --output-format concise` |
| `git diff --check` | Passed | Tracked whitespace only; does not inspect the untracked package |
| Fresh canonical Pester artifact | `2026-09-12T07:56:31Z`; gitSha `b94f585`; total 2906; **2904 passed**, 0 failed, 2 skipped; `passed: true`, `failures: []`, `filteredFiles: null` | Read directly from `tests/last-run.json`; not rerun in this verifier |
| Native preflight pytest | Cycle 2 handoff reports 52 passed | Not independently repeated in this scoped verification |

The package run used `uv run --offline --project packages/cg-release --python 3.12
--locked python -B -c` to invoke `pytest.main` with
`packages/cg-release/tests -q --tb=short -p no:cacheprovider` and a unique temporary
base under the approved Kilo temp directory. Process-local controls set
`UV_OFFLINE=true` and `GIT_ALLOW_PROTOCOL=file`. An audit guard rejected real
`gh`, network Git URLs, Python socket connections, and `os.system`. The successful
suite and final probe run each reported zero network-guard blocks.

**Transport safety:** The unsafe old over-65,536-byte probe was not run.
`BoundedTransport.run`, `test_phase5_review_repairs.py:59-71`, exercises real
process-input validation with `_capture` stubbed before every submitted body.
Accepted bodies reach only the fake server, never live `gh`. Local Git/GPG test
operations used temporary fixtures, not real remote repositories.

**Verifier harness corrections:** The first suite attempt produced 593 passes,
78 failures, and 32 errors in 23.25 seconds because the added audit wrapper did
not handle a null executable field in Windows subprocess audit events. Corrected
only the in-memory wrapper to derive the executable from the command line, then
obtained the 703-test pass above. The first extra-probe run produced 7 passes and
4 failures in 66.35 seconds: two expected a later recovery error instead of the
existing earlier `actor_role` error `E_AUTHORITY`; two changed every environment
subresource instead of only the environment object and reached `E_PROTECTIONS`.
Narrowed those fake endpoint mutations and used the exact existing authority
error. The final 11 checks passed with unchanged no-write assertions. These are
verifier harness corrections, not product repairs or suppressed product failures.
No source, existing test assertion, or recovery counter was changed.

**Pester qualification:** Retain the supplied known TestDrive missing-path and
nonempty-directory cleanup caveat. Zero failed assertions does not establish
successful cleanup. Both skips are in `update`; names and reasons are absent
from the artifact. `create-release` passed 95/95 with no skips. No Pester or
cleanup command was attempted here. This fresh result supersedes the cycle 2
evidence file's pending post-repair Pester field, not its historical prior result.

## Handoff

Only this report was manually created. Earlier reviews, implementation, tests,
plan completion fields, active state, and protected artifacts were not edited.
No commit, push, PR, live GitHub write, remote setting change, or later-phase work
occurred.

Return P1.4 as confirmed fixed and retain the five prior fixed IDs. There is no
remaining blocker from this scoped verification. The parent owns status
reconciliation and Phase 5/V5 completion after all required gates; this report
does not change the phase or start Phase 6.
