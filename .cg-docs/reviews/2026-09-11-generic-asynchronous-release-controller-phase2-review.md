---
date: 2026-09-11
depth: full
type: standard
plan: .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md
findings:
  P0.1: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P2.1: fixed
  P2.2: fixed
  P1.5: fixed
---

# Phase 2 Review Report

## Status

Review and independent repair verification complete; all eight findings are fixed.
Embedded `/cg-work phase2 review:auto`, resolved mode **full**.
Coverage: **10/10 specs**, emulated sequentially in one dedicated review session,
not ten independent sessions. Incomplete outputs: **0**.
Initial findings: **7 (P0: 1, P1: 4, P2: 2, P3: 0)**, all open when reviewed.
All seven original findings and follow-up P1.5 are independently verified fixed.
The final verification is recorded in phase2-verify-review-2.md; historical repair
sections below retain their original local-evidence qualifications.
No implementation edits, repairs, completion updates, commits, or remote mutations.
Phase 1 review and verification reports remain unchanged.

## Scope And Authority

The exact scope is the execution report's Phase 2 handoff, lines 769-806, and
the selected plan's Steps 3-4, lines 586-604. Relevant design contracts include
trusted policy, CLI/version resolution, pure metadata edits, and read deadlines.
The project charter/configuration, project and Python instructions, local
`cg-review` prompt, context-loading and review-routing contracts were read.
Python best-practices, its review anti-pattern reference, Pester safety, and
Brain-query skills were loaded and applied to the sequential reviews.

Primary coverage comprises 24 files, including the untracked package sources:

- `packages/cg-release/src/cg_release/`: `policy.py`, `versions.py`, `github.py`,
  `history.py`, `source_blobs.py`, `source.py`, `notes.py`, `preview.py`,
  `metadata.py`, `cli.py`, `events.py`, `models.py`, and `process.py`.
- `packages/cg-release/tests/`: `test_policy.py`, `test_versions.py`,
  `test_github_reads.py`, `test_history.py`, `test_source.py`, `test_notes.py`,
  `test_preview.py`, `test_metadata.py`, `test_cli.py`, `test_contracts.py`, and
  `test_install.py`.
- Supporting context: package configuration and fixtures, timing implementation
  and test references, root ignore rules, current test evidence, and the selected
  plan/work report. Existing Phase 1 dependencies were checked for cross-file
  effects, not subjected to a second Phase 1 acceptance review.

Excluded: environments, distributions, build trees, caches, generated view bodies,
unrelated changes, and implementation/evidence requirements of Phases 3-7.
Every spec retained the protected-artifact constraint: do not recommend deleting,
replacing, renaming, or moving brainstorms, solutions, archives, charter/config,
`roadmap.json`, `SCHEMA_VERSION`, or `.github/` infrastructure.

## P0 Findings

### P0.1: JSON Version Edits Silently Change Unrelated Numbers

**Agents:** cg-data-quality; corroborated by cg-adversarial and cg-code-quality.

**Evidence:** `packages/cg-release/src/cg_release/github.py:38` and
`packages/cg-release/src/cg_release/metadata.py:96-123,248-253`.

The generic JSON decoder converts all fractional/exponent numbers to binary
floats. The version adapter then serializes the entire document. Unrelated
numeric values can change even though only the declared version field is meant
to change. This violates the plan's explicit unrelated-value preservation rule
at line 396 and its declared-edit boundary.

**Executed proof:** Passing `{"version":"1.0.0","threshold":1e-1000}` through
the existing test helper into `proposed_edits` returned a successful, hashed
`Edit` with `"version": "1.5.0"` and `"threshold": 0.0`. No error was raised.
Ordinary high-precision decimal literals can also lose digits. The severity is
P0 under the mandatory silent-data-corruption rule. The demonstrated corruption
is in the validated in-memory edit output; no source file or release was changed.

**Related error boundary:** A second probe used the valid JSON numeric literal
`1e400` in a snapshot and invoked `cli.main(... --json)`. It raised an uncaught
`ValueError` during serialization, with a traceback instead of the contracted
JSON error event. This is recorded under the same numeric round-trip defect,
not counted twice.

**Fix:** Preserve numeric values exactly when editing the declared JSON field,
or reject unsupported numeric representations before returning an edit set.
Do not silently normalize them through binary floats. Convert unsupported-data
failures into redacted `ControllerError` events. Add regressions for long decimal
literals, underflow, overflow, and unchanged unrelated nested values through the
public edit-set and CLI boundaries.

## P1 Findings

### P1.1: Real Maintainers Lose Override Eligibility

**Agents:** cg-testing; corroborated by cg-learnings-researcher and cg-adversarial.

**Evidence:** `packages/cg-release/src/cg_release/source.py:134-146,197` and
`packages/cg-release/src/cg_release/policy.py:234-244`;
`packages/cg-release/tests/test_source.py:80-81` and `test_policy.py:65-80`.

GitHub's permissions endpoint exposes a legacy `permission` field: `maintain`
maps to `write`, while `role_name` carries the assigned role. Acquisition ignores
`role_name` and passes `permission` into the approval policy. Thus a real
maintainer is classified as a writer and cannot use the explicitly supported
production-branch override. The unit test calls `approval_route` with the string
`maintain` directly, so it does not detect the transport mismatch.

**Executed proof:** Injecting `permission='write', role_name='maintain',
user={'id': 7}` into the acquisition fixture produced `Snapshot.role == 'write'`.
An explicit bounded override reason then failed with the maintainer-authority
error. This is a false denial, not proof of unauthorized publication.

**Fix:** Resolve the current effective role from verified REST role/capability
fields, bound to the authenticated numeric actor ID. Handle custom or unknown
roles explicitly; do not promote an unknown role by name alone. Test actual
maintainer, ordinary writer, administrator, triage, and unknown-role envelopes
through acquisition and proposal creation.

**Protocol source:** GitHub REST documentation, fetched 2026-09-11:
<https://docs.github.com/en/rest/collaborators/collaborators#get-repository-permissions-for-a-user>.

### P1.2: Existing Manifest Content Is Never Validated

**Agents:** cg-data-quality; corroborated by cg-architecture and cg-adversarial.

**Evidence:** `packages/cg-release/src/cg_release/metadata.py:222-234,270-282` and
`packages/cg-release/src/cg_release/source.py:168-172`.

Acquisition reads an existing `.release-manifest.json`, but `proposed_edits`
uses its bytes only to compute an input digest. It does not parse or validate
them before returning a replacement schema-v1 manifest. Malformed JSON, an
unknown schema version, or an incompatible existing manifest therefore becomes
a successful edit proposal instead of an explicit unsupported-schema failure.
Phase 2 owns this pure parser/validation requirement; it is not deferred PR logic.

**Executed proof:** Adding `SourceBlob(b'not JSON')` at
`.release-manifest.json` in the standard snapshot still produced a successful
three-edit proposal. No implementation write was performed.

**Fix:** Strictly validate an existing manifest's supported schema and field
shapes before proposing replacement. Distinguish permitted absence, a supported
prior release manifest, and byte-idempotent reapplication from malformed or
unsupported content. Retain the preview-only request identity and do not invent
Phase 3 admission semantics. Add negative manifest fixtures and reapplication
regressions.

### P1.3: GraphQL Query Encoding Breaks Enterprise Host Routing

**Agents:** cg-reproducibility; corroborated by cg-testing and cg-adversarial.

**Evidence:** `packages/cg-release/src/cg_release/github.py:126-143,250` and
`packages/cg-release/tests/test_github_reads.py:115-151`.

The reader passes `graphql?query=...` as the `gh api` endpoint. GitHub CLI selects
its GraphQL host route only when the endpoint is exactly `graphql`. Other
relative endpoints use the REST prefix. On github.com both constructions happen
to reach `/graphql`. On GitHub Enterprise Server, this construction instead
targets `/api/v3/graphql`, while the GraphQL endpoint is `/api/graphql`.
The reader accepts an explicit Enterprise hostname, but its tag inventory cannot
complete there. Current tests return a successful body without testing this
endpoint distinction.

**Proof basis:** Static call tracing against the upstream GitHub CLI transport
and host-routing source, fetched 2026-09-11. No live Enterprise request was made.

**Fix:** Pass the exact `graphql` endpoint with a separately encoded query field
and explicit GET method, so `gh` chooses the correct host route. Preserve the
GET-only contract and bounded pagination. Test emitted argv and both public and
Enterprise URL routing without a live service.

**Protocol sources:**
<https://raw.githubusercontent.com/cli/cli/trunk/pkg/cmd/api/http.go> and
<https://raw.githubusercontent.com/cli/cli/trunk/internal/ghinstance/host.go>.
These fetched upstream sources are protocol evidence, not a claim that a specific
installed GitHub CLI version was independently exercised against Enterprise.

### P1.4: Stable Patch Notes Use A Future Prerelease Baseline

**Agents:** cg-adversarial; corroborated by cg-reproducibility and cg-data-quality.

**Evidence:** `packages/cg-release/src/cg_release/source.py:173-183`,
`packages/cg-release/src/cg_release/notes.py:28-46`, and
`packages/cg-release/src/cg_release/versions.py:111-138`.

Notes select the maximum version from all history in eligible lines before the
proposal resolves its version. The version resolver deliberately uses the stable
baseline for a stable core bump and excludes higher-core future prereleases from
the relevant comparison. These two baseline rules disagree.

**Trigger:** One line contains stable `1.4.2` and `1.5.0-rc.1` published from a
feature branch. A patch on the stable branch correctly resolves to `1.4.3`, but
notes compare against the RC commit. If that RC is not an ancestor of the stable
branch, the valid patch is rejected as diverged/behind. Even if it is an ancestor,
the notes can omit changes since the actual stable baseline.

**Executed proof:** An acquisition fixture containing those two adopted versions
and `--bump patch --branch main` passed the RC commit, not the stable commit, to
the notes reader. The divergence rejection follows directly from the inspected
notes status guard. No live history or branch was changed.

**Fix:** Select one release line and resolve the proposal's relevant baseline
before computing its commit inventory. Use the matching adopted commit for that
proposal. Add an integration regression with a higher-core RC on another branch
in the same line and a valid stable patch, plus promotion/RC continuation cases.

## P2 Findings

### P2.1: Confirmation Timing And Shared-Deadline Acceptance Lack Evidence

**Agents:** cg-testing; corroborated by cg-performance and cg-documentation.

**Evidence:** `packages/cg-release/src/cg_release/cli.py:113-152,157-162`,
`packages/cg-release/tests/test_cli.py:14-77`, and
`packages/cg-release/tests/test_timing.py:159-160`.

The interactive CLI measures a wait only to extend its deadline, then discards
the duration. It never records or emits a confirmation timing result. Merely
listing `confirmation` in `TimingRecorder.STAGES` does not measure the actual
CLI wait. The plan requires separate confirmation accounting, and the Phase 2
acceptance scenarios explicitly include shared command deadlines.

The CLI tests use fixed snapshots without advancing an injected clock. They do
not prove that acquisition plus recheck share the total budget, a lower policy
timeout is honored, or only human wait is excluded. The reader's expired-before-
first-call test does not cover those CLI boundaries. This is missing Phase 2
measurement/acceptance evidence, not a claim that a specific deadline overrun
has already been reproduced.

**Fix:** Connect the real confirmation interval to the existing timing contract
through an explicit supported measurement path. Add injected-clock CLI tests for
acceptance, decline/interruption, long human wait, pre-confirmation expiry, and
recheck expiry. Record observed intervals separately from submission, which must
remain unavailable in Phase 2. Do not claim measured handoff speed from these tests.

### P2.2: Response Size Is Checked Only After Full Buffering

**Agents:** cg-performance; corroborated by cg-adversarial.

**Evidence:** `packages/cg-release/src/cg_release/process.py:57-83` and
`packages/cg-release/src/cg_release/source_blobs.py:105-125`.

`subprocess.run(capture_output=True)` buffers all stdout and stderr before the
four-MiB stdout check. The new limit does not bound acquisition memory, and stderr
has no corresponding bound. A declared blob is fetched before its API size is
checked; a large source-controlled blob can consume substantially more memory
than the supported one-MiB metadata limit before rejection. A process timeout is
not a byte limit.

**Proof basis:** Static process-boundary inspection; no large-memory stress test
was run. Impact is excess memory and process failure during supposedly bounded
read acquisition, not demonstrated credential exposure.

**Fix:** Bound stdout and stderr while collecting them and terminate/reap the
process on overflow. Retain typed, redacted errors and argv-only execution.
Where available, check declared tree sizes before blob retrieval as an additional
guard, not a replacement for bounded transport capture. Add a small-limit test
producer that proves rejection while output is still being produced.

## Sequential Spec Results

### 1. cg-code-quality

Completed against the 13 primary source modules using the Python skill.
The JSON decode/serialize path contributes to P0.1; no separate style finding.
Ruff passed; no debug-output or bare-except defect found in this scope.

### 2. cg-testing

Completed against all 11 primary test files and their implementation boundaries.
P1.1 and P2.1 identify real protocol coverage and acceptance-evidence gaps.
The passing suite does not cover the negative JSON/manifest probes or notes
baseline mismatch recorded in the consolidated findings.

### 3. cg-documentation

Completed against source docstrings, CLI output, and the Phase 2 work report.
No separate documentation defect found; disabled submission and the journal
prerequisite are described accurately. P2.1 limits claims about measured timing.
Future installation/publication documentation was not imposed on this phase.

### 4. cg-version-control

No issues found in the Phase 2 source/test scope and `.gitignore` context.
The branch is `improve-cg-release`, not a production branch; source/tests are
untracked and were included. No commit was requested, so untracked status is
not itself a finding. Builds, environments, and caches remain excluded.

### 5. cg-reproducibility

Completed against immutable source acquisition, deterministic proposal/notes,
package configuration, and installed-wheel test behavior.
P1.3 and P1.4 identify host-dependent routing and inconsistent baseline behavior.
No new undeclared Python dependency or target-project GPID dependency found.

### 6. cg-performance

Completed against `github.py`, `source_blobs.py`, `process.py`, `notes.py`, and
the CLI timing path. P2.2 identifies the post-buffer resource-limit defect;
P2.1 records absent confirmation measurement. No live speedup is inferred.

### 7. cg-architecture

Completed against provider acquisition, pure edits, proposal calculation, and
disabled submission boundaries. No separate module-split finding.
P1.2 is the pure-validation boundary gap; the shared edit-set design otherwise
keeps writes out of Phase 2. Missing future journal/publisher code is not a defect.

### 8. cg-data-quality

Completed against schemas, version/projection history, declared paths, JSON,
TOML, DCF, changelog, and manifest output. P0.1 and P1.2 are confirmed defects;
P1.4 is a cross-file baseline inconsistency. No statistical code is in scope.

### 9. cg-learnings-researcher

Completed using the bounded Brain query and targeted solution/brainstorm reads.
The exact-wire-fixture lesson corroborates P1.1/P1.3; the typed-error lesson
corroborates the overflow case in P0.1. No additional independent finding.
The older main-only publication rule was not applied over this plan's branch rules.

### 10. cg-adversarial

Completed with synthetic, in-memory probes and external protocol source checks.
Confirmed P0.1, P1.1, P1.2, and the baseline selection in P1.4; corroborated
P1.3/P2.2 by static boundary tracing. No mutation or real credential probe ran.

## Verification And Qualifications

- Fresh reviewer run: `uv run --project packages/cg-release --python 3.12 --locked
  pytest packages/cg-release/tests -q --tb=short -p no:cacheprovider`:
  **204 passed in 7.66 seconds**, including real build/install tests.
- Fresh reviewer run: `uv run --project packages/cg-release --python 3.12 --locked
  ruff check packages/cg-release/src packages/cg-release/tests --output-format
  concise --no-cache`: passed.
- `git diff --check`: passed. This covers tracked diffs, not untracked package
  files; package lint/test evidence is reported separately.
- Report frontmatter and seven open IDs were checked against the local review
  report contract. `cg-render-artifact --validate-only` cannot validate reviews:
  it accepts only brainstorm/plan sources and rejected this review path. No
  renderer validation success is claimed; the required report was not moved.
- Read `tests/last-run.json`: `ranAt=2026-09-11T19:18:59Z`, `gitSha=b94f585`,
  `passed=true`, total 2906, passed 2904, failed 0, skipped 2,
  `filteredFiles=null`. The user supplied the known TestDrive cleanup caveat.
  No Pester command ran in this review session. Successful temporary-directory
  cleanup is not claimed, and the passing result does not refute Python findings.
- All defect probes used synthetic fixtures/in-memory data. One initial Python
  probe had a PowerShell quoting error; the corrected probe ran successfully.
  That command-construction error is not a product test failure.
- External reads fetched public protocol documentation/source only. No target
  GitHub repository API call, Enterprise trial, publication, or remote matrix
  execution was performed. Other OS/interpreter evidence is not inferred.

## Phase Boundary Assessment

The existing journal prerequisite is correctly fail-closed for this phase:
an existing state branch produces `E_STATE_UNAVAILABLE`, while enabled policy
without state requires a journal. This is not treated as proof of empty
reservations or as missing Phase 3 implementation.

`request_id: preview-not-submitted` is correctly limited to preview edit data.
Signing fingerprints and approval environment names are requirements, not proof
of key availability, approval, or protected-environment enforcement. Those
checks remain in later phases. `plan` and the implemented `start` path contain
reads and pure calculations only; submission/status/resume remain explicitly
disabled. No preview or confirmation is called a durable receipt.

The no-write boundary limits the immediate effect of P0.1/P1.2 but does not
make an incorrect validated edit set acceptable. V2 remains blocked pending
repair and independent verification. Parent handling should preserve all seven
open finding identities and the recorded evidence qualifications.

## Brain Sources

- `.cg-docs/solutions/git-workflows/2026-08-13-verified-pages-artifact-and-release-tag-gates.md`:
  bind data to exact immutable identities; do not import its superseded main-only rule.
- `.cg-docs/solutions/testing-patterns/2026-08-10-gh-cli-fixture-json-keys-must-match-client-parsing.md`:
  use actual external protocol fields instead of convenient mocked roles.
- `.cg-docs/solutions/bugs/2026-08-10-typed-invalid-gh-cli-payloads-crash-exit-code-contract.md`:
  guard response shapes and preserve typed CLI failures.
- The selected 2026-09-11 brainstorm's CLI, preview, metadata, and version sections
  supplied design context, not implementation evidence.

`open-brain` tools were unavailable. The bounded local `cg-index query` succeeded
with 593 index warnings; no Brain files or saved project memory were changed.

## Authorized Repair 2026-09-11T19:44:13Z

The user authorized repair of all seven findings at 2026-09-11T19:30:02Z.
This section records implementation-child results, not an independent verification
pass. Original observations and priorities above remain the review history.
The seven statuses are `fixed` with local regression evidence; independent
confirmation remains pending and Phase 2 is not marked complete.

| Finding | Repair | Regression evidence |
|---|---|---|
| P0.1 | json_edit.py validates the complete JSON document, locates the declared string token, and replaces only that token. Numeric lexemes never become floats and all other bytes remain unchanged. Invalid input raises a typed metadata error. | test_phase2_repairs.py: underflow, overflow, long decimal, signed zero, nested/escaped keys, array indices, and CLI success/error cases |
| P1.1 | source.py resolves a standard role_name only when its legacy permission field agrees and the response user ID matches the authenticated numeric actor ID. Custom, unknown, missing, and contradictory roles fail explicitly. | Real-wire role envelopes through acquisition and proposal: maintain/write, admin/admin, writer, triage, read, unknown/custom, missing role, and contradictory admin/read |
| P1.2 | manifest.py defines and validates strict schema-v1 prior/preview manifests before replacement: required shapes, duplicate/unknown fields, canonical version/tag, paths, outputs, and supported projections. Absence stays permitted. | Malformed JSON, unknown schema, duplicate keys, wrong types, missing/unknown fields, unsafe paths, supported prior manifest, and existing byte-idempotent reapplication test |
| P1.3 | github.py passes the exact graphql endpoint, a separate --raw-field query argument, and explicit GET. Host routing occurs before query encoding. | Public/Enterprise argv and documented routing-key regression; existing 101-ref cursor pagination remains tested |
| P1.4 | versions.py supplies a shared baseline selector. Acquisition selects one line and resolves the proposal before notes; base bumps use the stable baseline, while explicit promotion/RC continuation use their relevant adopted version. | Stable 1.4.2 plus future 1.5.0-rc.1: patch notes use the stable commit; promotion and RC continuation use the RC commit |
| P2.1 | CLI uses TimingRecorder around actual interactive input and emits a confirmation timing event. Reads and rechecks share an injected monotonic clock; only the measured human interval extends the deadline. | test_cli.py: accept, decline, EOF/interrupt, 500-second synthetic wait, lower policy timeout, expiry before confirmation and during recheck; no submission timing/receipt |
| P2.2 | process.py collects each pipe in a bounded buffer and kills/reaps on overflow. Stderr has the same limit as stdout. source_blobs.py rejects an excessive advertised tree size before blob retrieval. | test_bounded_capture.py: live stdout/stderr producers exceed a 512-byte bound, are terminated/reaped before their 30-second wait completes, and return E_RESPONSE_SIZE; normal dual-stream/nonzero output, timeout cleanup, and pre-download rejection also pass |

### Executed Repair Checks

- Negative baseline before implementation: 27 failed, 8 passed. These were
  expected regressions/new measurement interfaces, not failed green attempts.
- First repaired targeted pass: 35 passed.
- First full repaired package pass: 239 passed, including installed-wheel checks.
- Added four focused cases for escaped JSON pointers, typed CLI JSON failures,
  and pre-download tree-size rejection; timing cases moved into test_cli.py.
- Final full package command:
  `uv run --project packages/cg-release --python 3.12 --locked pytest packages/cg-release/tests -q --tb=short`:
  **243 passed in 8.04 seconds**, including build/install tests and real bounded
  output producers. No failed post-repair functional run occurred.
- `python -m pytest scripts/tests/test_cg_pr_preflight.py -q --tb=short`:
  **52 passed in 0.41 seconds**.
- `uv run --project packages/cg-release --python 3.12 --locked ruff check packages/cg-release scripts/benchmark_release.py --output-format concise`:
  passed. Formatting and one import-order correction completed.
- `git diff --check`: passed for tracked changes. No committed-candidate claim.

### Qualifications And Verification Scope

No live GitHub/Enterprise calls or remote changes occurred. Enterprise routing
is tested through the exact documented gh endpoint/argv contract, not a live
Enterprise deployment. Producer tests use small limits and temporary subprocesses;
they do not claim a cross-platform process-tree supervision guarantee. Human
timing tests use injected clocks, not measured submission performance.

The earlier full Pester result at 2026-09-11T19:18:59Z is preserved: 2904 passed,
0 failed, 2 skipped, filteredFiles null, with the known TestDrive cleanup caveat.
That run preceded these repairs. A refreshed dedicated safe gate and a separate
finding-verification child remain pending. Existing functional recovery counters
are unchanged; one authorized review-repair implementation pass is recorded
separately, with no failed post-repair functional run.

Verification must check all seven finding IDs and any cross-file regressions,
with P0/P1 always reportable. Scope includes json_edit.py, manifest.py, metadata.py,
source.py, versions.py, github.py, cli.py, process.py, source_blobs.py, and affected
tests. Confirm that the changed test process spies still check argv rejection,
shell=False, explicit cwd, typed timeout/errors, and disabled status/resume.
No weakening of the underlying behavior assertions is intended or authorized.

## P1.5 Repair 2026-09-11T20:01:42Z

The independent report
`.cg-docs/reviews/2026-09-11-generic-asynchronous-release-controller-phase2-verify-review.md`
confirmed all seven original findings fixed and found P1.5, generated manifests
that failed their own reader on reapplication. That independent report remains
unchanged. P1.5 is added to this parent tracker as locally fixed, not yet verified.

The user authorized this scoped correction at 2026-09-11T19:58:15Z.

- `policy.py`: reject duplicate and case-aliased build artifact paths, not only
  duplicate artifact names. Enforce the existing 255-character schema limit on
  complete branch/tag names through safe_ref, including prefix plus version.
- `metadata.py`: validate the exact generated manifest bytes with the same
  validate_manifest reader before adding that manifest or returning any edit set.
- `manifest.py`: retain strict schema validation and use a diagnostic applicable
  to both existing and generated bytes. No reader constraint was weakened.
- `test_manifest.py`: policy and public-proposal rejection for both path alias
  forms and 256/260-character tags; accepted 254/255-character tags with distinct
  output paths validate and reapply all returned edit bytes identically. Direct
  producer tests also reject malformed generated fields before returning a set.

Executed red baseline: 11 failed, 2 passed. First green targeted run: 13 passed.
Full locked Python 3.12 package run: **256 passed in 7.77 seconds**, including
build/install tests. Preflight regression: **52 passed in 0.40 seconds**. Ruff
and tracked whitespace checks passed. Failed post-repair functional runs: 0.

This is authorized Phase 2 review-repair pass 2 (one pass for P1.5). Existing
functional recovery counts and earlier repair history are unchanged. Latest
supplied Pester evidence, checked in tests/last-run.json, is 2026-09-11T19:51:46Z:
2904 passed, 0 failed, 2 skipped, filteredFiles null, with the known TestDrive
cleanup caveat. It preceded this correction and is not claimed as a fresh gate.

Next independent verification should focus on P1.5 and cross-file regressions in
the three changed production files plus test_manifest.py. Preserve the seven
original confirmations, but always report new P0/P1 or cross-file defects. No
Phase 2 completion, Phase 3, commit, push, or remote operation is claimed here.
