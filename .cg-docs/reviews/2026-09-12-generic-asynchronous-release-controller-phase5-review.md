---
date: 2026-09-12
depth: full
type: standard
plan: .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P2.1: fixed
  P2.2: fixed
---

# Phase 5 Review

**Result:** Changes required. V5 and Phase 5 must not be marked complete yet.
**Findings:** 5 (P0: 0, P1: 3, P2: 2, P3: 0). All findings are open.
**Coverage:** 10/10 local reviewer specs emulated sequentially in one dedicated
review session. These were not ten independent agents or sessions.
**Mode:** Embedded `review:auto`, resolved `full`; no implementation or autofix.

## P1 Findings

### P1.1: Valid Publication Inputs Exceed the Journal Transport Limit After Tagging

**[P1.1]** [cg-architecture, cg-testing, cg-adversarial]
`packages/cg-release/src/cg_release/publisher.py:147-149,159-163`;
`packages/cg-release/src/cg_release/github_journal.py:163-178,197`;
`packages/cg-release/src/cg_release/process.py:178-185`.

**Issue:** Publication retains the notes in the seal and then retains them again
in `publication-draft` evidence. A journal transaction base64-encodes both the
whole request record and its event. The record-size check in
`journal_rules.py:30-38` permits almost 64 KiB, but the process boundary limits
the entire encoded GraphQL request to 64 KiB. Thus an allowed record can be
impossible to write through the real transport.

**Proof:** Reused the existing full CLI/control/build/seal/publish test with
6,000 ASCII characters appended to each fixture source changelog. Updated the
fixture blob IDs and trees correctly. This is below the publication notes limit
of 16,384 bytes in `publication_inputs.py:226-232`. For requests over 65,536 bytes,
the fixture called the real `run_process`, which rejected the input before any
subprocess was started. The test failed with `E_PROCESS_ARGUMENT` on a
**67,028-byte `publication-draft` result transaction**. The simulated remote
already contained the exact tag and draft; observed writes were `['tag', 'draft']`.

**Impact:** An ordinary changelog can leave an immutable tag and draft with an
unresolved journal intent. Ordinary resume cannot shrink the append-only record;
fresh recovery seals make it larger. This blocks completion and subsequent
admission. The existing small full-transport fixture passes because its largest
request is only 37,660 bytes, and its fake runner does not enforce production
input limits.

**Fix:** Make the bounded transport envelope compatible with the maximum encoded
journal transaction, including base64 expansion, event duplication, and recovery
growth. Validate the complete transaction before a consequential publication
write. If evidence must be split into immutable referenced records, preserve the
hash chain and read-back guarantees. Do not remove bounds, truncate evidence, or
rewrite an existing tag. Add full-path tests for realistic notes, inventories,
and multiple recovery seals using the real process-input validation boundary.

### P1.2: Removed Artifact Metadata Prevents Exact-Source Rebuild Recovery

**[P1.2]** [cg-reproducibility, cg-testing, cg-adversarial]
`packages/cg-release/src/cg_release/build_stage.py:220-243`;
`packages/cg-release/src/cg_release/publication_stage.py:33-53`;
`packages/cg-release/src/cg_release/publication_rebuild.py:80-90`.

**Issue:** The publication layer recognizes a missing retained artifact as
`E_REBUILD_REQUIRED` and can enter `building`. However, it keeps the old build
ticket, as required for audit history. The next build step finds zero matching
artifacts and raises `E_ARTIFACT` before it can create a replacement ticket.
Only an artifact row that still exists with `expired: true` reaches the existing
replacement path. The same zero-row condition also blocks a pre-tag rebuild.

**Proof:** Reused
`test_phase5_transport.py::test_expired_post_tag_artifact_runs_new_isolated_build_and_new_approval`.
Changed only the expired fixture's artifact listing to the valid response
`{'total_count': 0, 'artifacts': []}`. The existing recovery expectation failed
with `E_ARTIFACT: One exact registered release-assets archive is required.`
The normal test with an `expired: true` row passes.

**Impact:** Retention cleanup or deletion of an Actions artifact can permanently
block the planned recovery after the tag and draft already exist, even though
the exact source, prior build evidence, and owner-expiry proof are retained.
Repeated resume examines the same old ticket and fails again.

**Fix:** Distinguish a verified absent artifact from an ambiguous inventory or
denied read. After the required recovery and owner checks, create a new exact-source
build ticket for absence as well as expiry. Keep the old evidence, require new
registration and approval, and preserve all existing tag and asset bytes. Cover
both pre-tag and post-tag absence; 401/403, duplicate rows, and mismatching
identities must remain hard errors.

### P1.3: Audited Recovery Cannot Replace a Revoked Requester's Authority

**[P1.3]** [cg-adversarial, cg-architecture, cg-testing]
`packages/cg-release/src/cg_release/stranded_recovery.py:123-127,165`;
`packages/cg-release/src/cg_release/authority.py:11-24`;
`packages/cg-release/src/cg_release/publication_inputs.py:179-181`.

**Issue:** The new reviewed recovery path validates a current maintainer and an
exact protected-default directive, but then calls ordinary `authorize_resume`.
That function always requires the original requester to retain write authority.
The new grant is therefore not sufficient to recover a stranded publication when
the original requester's authority was revoked. The later build, resume, and
publication callers also use this ordinary authorization function.

**Contract:** The plan's Approval, Publication, and Recovery contract, lines
498-506, explicitly routes revoked authority to reviewed maintainer recovery
under current policy. Normal resume must stop, but the separate audited path
must be able to carry out that reviewed recovery without altering the tag.

**Proof:** Reused
`test_phase5_transport.py::test_reviewed_recovery_workflow_handles_deleted_source_without_moving_tag`.
When the fixture installs the reviewed recovery commit, changed original
requester 7 from `maintain` to `read`. The current recovering actor 456 remains
`maintain`; the directive, digest, exact tag, and source exception remain valid.
The real controller entry point returned `E_AUTHORITY` instead of recording
`audited-recovery`. No second tag write occurred.

**Impact:** A revoked or departed requester can strand an otherwise recoverable
tag indefinitely. Restoring that user's permissions is not an acceptable substitute
for the planned reviewed recovery authority.

**Fix:** Provide a narrowly scoped, explicit audited authority-replacement path
bound to the verified recovery directive and exact immutable release. Carry it
through build, resume, sealing, and publication checks. Keep the original
requester and all reconfirmers in the approval-exclusion set. Require current
maintainer authority and fresh independent protected approval. Do not weaken
ordinary `authorize_resume` or accept an unreviewed replacement actor.

## P2 Findings

### P2.1: Publication Rechecks Download the Same Build Archive Repeatedly

**[P2.1]** [cg-performance]
`packages/cg-release/src/cg_release/publish_worker.py:168-184`;
`packages/cg-release/src/cg_release/publication_inputs.py:123-153`;
`packages/cg-release/src/cg_release/publisher.py:81,125-129`.

**Issue:** Every pre-effect recheck calls `make_inputs`, which downloads, hashes,
and decompresses the complete build archive again while the Release is not yet
published. These reads are outside `ReadCache`. The original verified bytes are
already held in the same trusted job.

**Proof:** Added an in-memory counter at the existing full-transport fixture's
binary-output boundary. The unchanged successful lifecycle downloaded artifact
51 ten times: twice in control/build processing, once in the seal job, and
**seven times in the protected publication job**. The seal and publication calls
use the same control-role runner, which accounted for eight downloads together.
There was one small build artifact plus the public provenance asset.

**Impact:** Transfer and decompression cost increases with each publication
effect. It consumes the worker's shared 120-second deadline and can interrupt
publication after an irreversible write. This is a measured operation count,
not a measured live latency or speedup claim.

**Fix:** Retain verified immutable archive bytes and inventory within the trusted
job, keyed by exact registered artifact/run/source/digest identity. Continue to
recheck mutable policy, authority, approval, ownership, run state, and remote
publication effects. Reacquire bytes when identity changes or a new recovery job
starts. Add a transfer-count regression without weakening the fresh gates.

### P2.2: Publisher Errors Omit Known Request and Recovery Context

**[P2.2]** [cg-data-quality, cg-testing]
`packages/cg-release/src/cg_release/publish_worker.py:287-295`.

**Issue:** The worker emits only `kind`, `code`, and `message` on failure, even
after it has parsed a request and read its version and checkpoint. The error
event has null request ID, version, step, expected/observed state, elapsed time,
and next action. This differs from the context-preserving CLI error path in
`cli.py:263-279` and from the plan's structured error contract at lines 338-344.

**Proof:** The real publisher error from P1.1 had all these fields set to null,
although it had already created the tag and draft. The error did not tell a
consumer which request had the unresolved publication effect or how to inspect it.

**Impact:** Automated consumers cannot associate the failure with its known
release checkpoint without external log context. The message can also suggest
an ordinary argument problem when an irreversible effect already occurred.

**Fix:** Retain safe request identity, version, last verified checkpoint, elapsed
time, and a reconciliation next action as execution progresses. Include them in
typed errors without extra unbounded recovery reads. Keep unknown outcomes
explicit, and never include credentials, raw API bodies, or inferred success.
Add worker event assertions for pre-write, post-tag, and unknown-write failures.

## Scope and Authority

The exact latest handoff was read from the execution report's
`Phase 5 Implementation Complete 2026-09-12T05:19:08Z` section, lines 2559-2711.
Earlier intermediate handoffs were not used as the current scope. The plan has
`completed-phases: [1, 2, 3, 4]` and `current-phase: 5`.

Authority included Phase 5 Steps 9-10, V5, the publication/recovery design
contracts, project charter and configuration, project/Python instructions, the
local review command, and the review-routing/context-loading/artifact-view
contracts. Python, pytest, Pester safety, Brain query, and Git workflow skills
were applied. The deterministic release/security risk route is `full`.

The review included untracked package source, not only `git diff`. Forty
production modules were inspected, with focused reads for earlier-phase
dependencies rather than a new full review of Phases 1-4.

| Area | Source inspected under `packages/cg-release/src/cg_release/` |
|---|---|
| Approval and publication | `approval.py`, `publish_worker.py`, `publisher.py`, `signing.py`, `publication_approval.py`, `publication_control.py`, `publication_credentials.py`, `publication_inputs.py`, `publication_provenance.py`, `publication_reconcile.py`, `publication_registration.py`, `publication_remote.py`, `publication_rules.py`, `publication_stage.py` |
| Recovery and adoption | `recovery.py`, `recovery_actions.py`, `recovery_audit.py`, `recovery_models.py`, `stranded_recovery.py`, `publication_rebuild.py`, `published_history.py`, `history.py` |
| Journal and trust | `journal.py`, `journal_models.py`, `journal_rules.py`, `journal_checkpoint.py`, `github_journal.py`, `authority.py`, `context.py`, `models.py` |
| Entry points and Phase 4 interfaces | `controller.py`, `stage_router.py`, `runtime.py`, `cli.py`, `build_stage.py`, `build_control.py`, `artifacts.py`, `github.py`, `process.py`, `read_session.py` |

Related scope included `templates/publish.yml`, `templates/controller.yml`,
package metadata and lock usage, the full Phase 5 fake transport, its Phase 4
transport dependency, and the approval, publisher, signing, publication-input,
owner, checkpoint, recovery, retention, and worker tests. The complete package
suite was executed, including installed-wheel and real temporary Git/GPG tests.

Excluded: `.venv`, `dist`, build outputs, bytecode and test/lint caches as review
source; generated view bodies; unrelated existing changes; Phase 6 profile and
reader rollout; Phase 7 documentation, live trials, remote matrix evidence, and
production enablement. The disabled template guards are intentional, not defects.
Future documentation deliverables were not reported as missing Phase 5 work.

## Sequential Reviewer Results

Each role received the same protected-artifact constraint. No role recommended
deleting, replacing, renaming, or moving protected Brain artifacts, charter/config,
roadmap, schema-version files, or `.github/` infrastructure. Related findings
were consolidated once rather than counted again for each role.

### 1. cg-code-quality

No separate code-quality issues found in the reviewed publication, signing,
credential, and recovery modules. Ruff passed on the whole package and benchmark.
Explicit integer checks are appropriate for the strict security boundary; they
were not treated as style errors. Functional defects are recorded separately.

### 2. cg-testing

Found missing behavioral coverage behind P1.1, P1.2, P1.3, and P2.2 in
`test_phase5_transport.py` and its transport/error boundaries. The 683 passing
tests provide useful evidence, but do not refute these additional negative probes.
Cancellation, exact tag, independent approval, and installed-wheel cases ran.

### 3. cg-documentation

No separate Phase 5 documentation defect found in the scoped module comments,
disabled workflow templates, or latest execution handoff. The report correctly
distinguishes offline evidence from live GitHub proof and pending review.
Installation and operational documentation remain explicit Phase 7 deliverables.

### 4. cg-version-control

No separate version-control issue found in the scoped source and templates.
The package and lockfile are untracked implementation work, not omitted review
scope. Root ignore rules cover environments, builds, and bytecode. No actual
credential value was found in the reviewed source; fixture tokens are synthetic.

### 5. cg-reproducibility

P1.2 prevents reconstruction from retained exact-source evidence after artifact
metadata disappears. `build_stage.py` handles only the narrower expired-row case.
The locked Python 3.12 run, temporary Git/GPG fixtures, immutable tag bytes, and
original published-receipt selection otherwise supplied repeatable local evidence.

### 6. cg-performance

P2.1 records repeated transfers of the same archive in `publication_inputs.py`
and `publish_worker.py`. The counter measured actual fake-wire binary operations,
not a manually incremented report field. No live handoff or speedup claim is made.

### 7. cg-architecture

P1.1 is a mismatch between record, transaction, and process limits across the
publication/journal boundary. P1.3 also affects the audited-recovery interface.
Separate trusted sealing, protected publishing, source-free signing, and the
read-only published recovery adapter are present. No new provider was introduced.

### 8. cg-data-quality

P2.2 loses known identity and checkpoint fields at the new publisher error
boundary. P1.1 also shows that downstream encoded-size validation is not compatible
with upstream accepted evidence. Strict recovery models, exact asset hashes,
duplicate inventory rejection, and non-clobber checks were inspected.

### 9. cg-learnings-researcher

Relevant lessons support P1.1 and P2.1: fixtures must match the full runtime
protocol, and resource counts must be measured at the actual I/O boundary.
No additional unique finding is added. Exact immutable publication evidence is
retained as a requirement; the current plan supersedes older main-only rules.

### 10. cg-adversarial

Confirmed P1.1, P1.2, and P1.3 with executable, in-memory fixture variations.
The normal approval, signer, owner, conflict, read-denial, and cancellation tests
also ran. No exploitable P0 issue was confirmed. This does not establish live
GitHub App, environment, ruleset, or signing enforcement.

**Output quality:** 10/10 usable role results, each with named file context and
at least two non-header lines. No missing, empty, or automatically retried role.

## Verification Evidence

| Check | Result |
|---|---|
| `uv run --project packages/cg-release --python 3.12 --locked --offline pytest packages/cg-release/tests -q --tb=short` | Independently executed: 683 passed, zero failed, 184.63 seconds |
| `uv run --project packages/cg-release --python 3.12 --locked --offline ruff check packages/cg-release scripts/benchmark_release.py --output-format concise` | Independently executed: passed |
| `git diff --check` | Passed for tracked changes; does not cover the untracked package |
| Full existing transport tests with the production 65,536-byte input threshold applied in memory | 29 passed; largest request 62,412 bytes |
| Full transport with 6,000 added changelog characters and real `run_process` validation for oversized requests | Failed as described in P1.1; 67,028 bytes, after tag and draft writes in the fake server |
| Existing expired-artifact recovery test with an empty artifact listing | Failed as described in P1.2, `E_ARTIFACT` |
| Existing reviewed recovery test with original requester downgraded to read | Failed as described in P1.3, `E_AUTHORITY` |
| Existing full transport test with a binary-download counter | Passed; ten transfers of the same archive, eight in seal/publication combined |
| Final canonical Pester artifact | Read directly: `2026-09-12T05:24:44Z`, git SHA `b94f585`, total 2,906, passed 2,904, failed 0, skipped 2, `failures: []`, `filteredFiles: null` |
| Native preflight pytest | Implementation handoff reports 52 passed; not independently repeated here |

The supplied Pester cleanup qualification is retained: TestDrive cleanup reported
missing-path/nonempty-directory errors. Successful cleanup is not claimed. The
runner result has no failed assertions; both skips are in `update`, with names
and reasons absent from the artifact. `create-release` passed 95/95 with no skips.
No Pester command was run in this review session.

All added probes used `uv ... python -c` with temporary in-memory monkeypatches
and `pytest.main`, without changing source or test files. They reused these
existing tests:

- `test_phase5_transport.py::test_full_transport_publishes_then_new_preview_uses_journal_history`
- `test_phase5_transport.py::test_expired_post_tag_artifact_runs_new_isolated_build_and_new_approval`
- `test_phase5_transport.py::test_reviewed_recovery_workflow_handles_deleted_source_without_moving_tag`

For P1.1, the fixture extension appended `b'\n' + b'A' * 6000 + b'\n'` to
`CHANGELOG.md`, recomputed its Git blob and containing tree IDs, and updated the
fixture commit tree. At the fake runner boundary, an input longer than 65,536
bytes was passed to real `run_process`; it failed validation before process
execution. For P1.2, expired artifact-list responses became
`{'total_count': 0, 'artifacts': []}`. For P1.3, installation of the existing
reviewed recovery commit set `world.roles[7] = 'read'`, leaving actor 456 unchanged.
No real GitHub mutation or credential access was needed for any reproduction.

The extra probe failures are review evidence for uncovered cases, not failed
reruns of the unchanged suite. No functional recovery counter was reset or
consumed by an implementation repair in this session.

## Brain Sources

The bounded query was:
`cg-index query --intent review --query "release publication recovery signing approval immutable tag transport" --budget 800 --format md`.
It selected the current plan and immutable release-gate solution, with 600 index
warnings. `open-brain` tools were unavailable; the local Brain query and targeted
solution reads were used. No generated view body was read.

- `.cg-docs/solutions/testing-patterns/2026-08-13-release-gate-fixtures-and-derived-evidence-hashes.md`: model the complete external command protocol, not a more permissive fake.
- `.cg-docs/solutions/git-workflows/2026-08-13-verified-pages-artifact-and-release-tag-gates.md`: keep privileged execution separate and bind immutable inputs; its older main-only policy is superseded here.
- `.cg-docs/solutions/bugs/2026-08-26-release-drift-ignore-checks-spawn-thousands-of-git-processes.md`: test resource shape at the process/I/O boundary; do not infer speed from a passing result.
- `.cg-docs/solutions/bugs/2026-08-10-typed-invalid-gh-cli-payloads-crash-exit-code-contract.md`: validate response shape and preserve typed, actionable failures.

## Handoff

Five finding IDs were parsed and entered as open. No finding was fixed, skipped,
or suppressed. Only this consolidated review report was created; implementation,
plans, prior reports, active state, and protected artifacts were not edited.

The remaining phase work is repair and independent verification of these findings.
Retain the passing suite and Pester evidence, but do not use them to mark V5
complete while these reproduced P1 failures remain open. No Phase 6 work, commit,
push, PR, remote setting change, or release operation was performed.

Review-stage advisory: use strong independent boundary and recovery reasoning
with high effort for the repairs and verification. A lower-cost option is useful
only for bounded mechanical checks. These are capability suggestions, not model
or effort assignments; availability varies by platform/date and the user controls
the final selection.
