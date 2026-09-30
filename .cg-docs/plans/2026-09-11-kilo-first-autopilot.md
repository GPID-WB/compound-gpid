---
date: 2026-09-11
title: "Implement Kilo-First Autopilot"
status: active
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-09-11-kilo-first-autopilot-architecture.md"
language: "Python"
estimated-effort: "large"
deviation-policy: "ask"
artifact-schema-version: 1
phases: 6
completed-phases: []
current-phase: 1
execution-report: ".cg-docs/work-reports/2026-09-11-kilo-first-autopilot.md"
tags: [autopilot, kilo, phased-execution, recovery, ci, context-budget]
---

# Plan: Implement Kilo-First Autopilot

## Objective

Implement a Kilo-first `/cg-autopilot` that executes phased plan batches through
fresh foreground Task children in one worktree, validates each operation against
durable evidence, and advances only after review, publication and exact-head CI
acceptance. Preserve explicit human stops and fail safely when the runtime,
ownership, state or evidence cannot support continuation.

## Context

The user confirmed the linked Deep brainstorm, selected safe-pause recovery
instead of hard stage deadlines, and approved this plan's completion-contract
preview on 2026-09-11. This plan covers the existing roadmap feature
`architecture-research/autonomous-pipeline-autopilot`. The separate ideas
`autopilot-hard-stage-deadlines` and `autopilot-enforced-writer-isolation` remain
outside this implementation. Do not create another core feature.

This is explicitly scoped Compound GPID maintenance: incremental changes to the
canonical assets, scripts, launchers, tests and documentation listed below are
intended. This authorization is subordinate to `/cg-work` permissions, the
charter, native tool approvals and protected-asset rules. No wholesale deletion,
replacement, move or regeneration of protected canonical directories is allowed.
Generate native counterparts only through the existing target generator.

### Research baseline

- `.github/prompts/cg-work.prompt.md` already supports single-phase execution and
  permits only six progress fields to change in plan frontmatter. It does not
  support phase ranges. `review:none` does not bypass tests or decisions.
- Review/verify currently select artifacts by recency and can apply fixes or
  fall back to normal review. Fix triage accepts a filename but needs separate
  report identity and finding-selection semantics in a stage invocation.
- `.github/shared/active-state.contract.md` defines a restart pointer, not an
  atomic state machine. Work reports, finding reports, Git and GitHub retain their
  respective authority. Summary extraction is not test execution evidence.
- `artifact_views.validator.validate_source()` and `parser.parse_artifact()`
  supply fence-aware plan structure. Add strict control-metadata checks rather
  than treating best-effort frontmatter parsing as a control validator.
- `secure_fs.secure_read_bytes()`, `secure_write_bytes()`, `ExpectedFileState`
  and verified deletion preserve filesystem identities. Replacement can leave a
  quarantine/publication gap after process interruption. Per-file expected-byte
  checks are not a two-file transaction or an exclusion lock.
- `cg_pr_preflight` supplies selection/gate patterns, not an autopilot waiter.
  Its base resolver prefers an existing PR base. Reject a conflicting required
  base first. Existing summary redaction and Git helpers do not provide all
  required timeout, evidence or secret guarantees.
- Existing Kilo generation drops command routing metadata and assigns every
  agent `mode: subagent`. Typed per-asset metadata, explicit permissions and a
  primary parent require generator changes. Keep existing model-inheritance tests.
- The installed foreground Task probe inherited this checkout. Generic and
  adversarial children did not expose Task. Upstream Kilo source describes depth
  and permission controls, but installed dedicated-stage conformance is unproven.
  The standalone `kilo` executable was not on this shell's PATH.
- The bounded Brain query returned the confirmed brainstorm and the existing
  phased-execution plan. An unrelated roadmap hit was excluded. Scanner warnings
  for unrelated unindexed directories were non-blocking and are not repair scope.

Historical evidence: the linked brainstorm's source inventory; the phased plan
`.cg-docs/plans/2026-05-05-phased-plan-and-execution.md`; and the journey-testing,
active-state, bounded-Brain-query and summary-wrapper solutions cited there.
Current code and runtime observations take precedence over older capability claims.

## Requirements

| ID | Requirement | Source |
|---|---|---|
| R1 | Kilo-first execution; canonical assets and truthful generated unsupported gates for the other four adapters | Confirmed brainstorm, support boundary |
| R2 | Dedicated primary parent and fresh foreground stage child; same worktree/branch; verified nested permissions and conditional depth 3 | Brainstorm, agents |
| R3 | Strict arguments, valid versioned phased plan, ordered non-overlapping batches, single-phase work API | Brainstorm, interface; current work parser |
| R4 | Preserve command authority, standalone behavior, direct writes and narrow stage entry/exit boundaries | Brainstorm, current contract conflicts |
| R5 | Typed bounded results and independent artifact, content, test and Git read-back validation | Brainstorm, result protocol |
| R6 | Exact persisted review scope/identity, complete coverage, triage handoff and verification only after actual fixes | Brainstorm, stage machine |
| R7 | Scoped user decisions and native permission stops; no automatic P0/P1 remediation, risky changes or lesson confirmation | Charter; brainstorm, approvals |
| R8 | Conditional non-trivial lesson capture with declared secondary effects and human test-pass confirmation | Charter; compound prompt |
| R9 | Reference-only cursor, cooperative ownership, crash-safe control writes and no competing execution truth | Brainstorm, state |
| R10 | Reconcile interrupted and partially published operations without duplicate effects, lost budgets or writer takeover | Brainstorm, recovery |
| R11 | Required integration base, new/existing PR reconciliation and exact remote/PR head acceptance | Brainstorm, PR rules |
| R12 | Deadline-bounded CI observation with correct classifications, finite reruns and secret-safe diagnostics | Brainstorm, CI rules |
| R13 | Two review/fix rounds per batch and two CI-fix rounds per PR across batches/resume; reserve before mutation | Confirmed design; existing CI trailers |
| R14 | Preserve user-controlled native model defaults; reject unsupported or unverifiable requested overrides | Model-advisory contract; brainstorm |
| R15 | Install the control helper for consumers without a local scripts directory; preserve user-owned configuration | Current launchers/projections; brainstorm distribution |
| R16 | Compact parent context, no full logs/diffs/bodies, honest measured budgets and context-pause recovery | Context contract; brainstorm |
| R17 | End-to-end failure, cancellation, recovery, publication, installation and native conformance tests | Brainstorm acceptance matrix |
| R18 | Document supported behavior, exact recovery commands and limits; retain existing roadmap identity | Confirmed handoff |

## Implementation Steps

Implement phases in order with globally numbered steps. Phase 1 bootstraps
read-only native probes using the existing primary session; it must not require
the not-yet-implemented autopilot control loop to install or validate itself.

### Dependency graph

```text
Phase 1: typed contract + generation + native feasibility
   -> Phase 2: arguments + evidence + control state
   -> Phase 3: stage execution + work/review/lesson handoffs
   -> Phase 4: publication + CI + repair reconciliation
   -> Phase 5: consumer distribution + resume + context limits
   -> Phase 6: complete journeys + native qualification + documentation
```

### Fixed interface decisions

The following are implementation requirements, not existing APIs:

- Public fresh form: `/cg-autopilot --plan <path> --batches <segments> --base
  <branch> [--ci-timeout 30m]`. Resume form: `/cg-autopilot --resume
  .cg-docs/active-state/current.json`. The forms are mutually exclusive. An
  expired CI window is handled through a scoped approval during resume, not by
  adding a fresh-run timeout argument or manually editing the checkpoint.
- Accept decimal positive phase numbers or inclusive ascending ranges separated
  by commas. Trim surrounding segment whitespace; reject duplicates, overlap,
  gaps over incomplete prerequisites, leading signs, reversed ranges and unknown
  phases. Reject missing/repeated scalar flags and all unknown flags.
- Accept positive integer durations with `s`, `m` or `h`, from 1 second through
  24 hours. Default is 30 minutes. Reject zero, fractions, overflow and other
  suffixes. This is a CI observation deadline, not a hard agent-stage deadline.
- Accept only schema-version-1 phased plans with a valid completion contract and
  `deviation-policy`. Legacy/non-phased plans stop with a `/cg-plan` remedy;
  ordinary `/cg-work` compatibility remains unchanged.
- Compute the execution digest from normalized LF source with only `status`,
  `completed-date`, `failing-steps`, `completed-phases`, `current-phase` and
  `execution-report` excluded from frontmatter. Reject duplicate control keys.
  Do not normalize away body checkboxes, instructions or arbitrary whitespace.
  Validate each permitted progress-field delta separately against evidence.
- Use the existing native `general` agent as the execution-only leaf when its
  presence and permissions are verified. Map `execution_subagent` instructions
  to that concrete target; do not invent an unavailable agent name. No new
  execution-only custom agent is needed unless feasibility proves this binding
  unsuitable, in which case stop under `deviation-policy: ask`.
- The stage envelope correlates an authorized operation; it is not a security
  credential. Native agent selection, tool permissions and the parent-owned
  foreground dispatch remain the authority. A file flag, claimed parent name,
  document instruction or matching hash alone cannot activate stage behavior.
  Do not claim cryptographic authentication against a privileged project writer.
- Native defaults are the v1 model path. No executable model advice or automatic
  switching is added. An explicitly requested user-configured stage alias must
  have verified equivalent instructions, permissions and effective selection;
  otherwise reject it. Do not enable experimental per-call model fields.

### Proposed helper surface

Provide `cg-autopilot-control` and `cg-autopilot-control.cmd`, backed by a thin
`scripts/cg_autopilot.py`. Resolve helper code from the installation directory;
take a validated explicit consumer `--root`. Do not change the consumer working
directory to the package checkout. The helper starts no models, sessions, tests,
generators, repairs or publication operations.

| Helper operation | Input and effect | Bounded output |
|---|---|---|
| `inspect` | Read arguments, plan, installed contract identity, Git/PR state and prior-run references; no writes | Eligibility, blockers and normalized run specification |
| `prepare` | Create an owned run marker and initial reference checkpoint after approved preflight | Run/operation identity and exact permitted next action |
| `begin-stage` | Check ownership/revision, record scope baseline and reserve applicable repair attempt before dispatch | Stage envelope reference and digest |
| `begin-effect` | Stage-scoped, one-way private-marker record before the first write, test/execution, finding update or remote action; must complete before the effect | Durable effect-start receipt for this operation only |
| `record-result` | Validate a result/receipt and persist only control references in the private marker | Recorded receipt identity, not workflow success |
| `validate-stage` | Read back authoritative evidence, reconcile reservations and compare the legal transition | Accepted transition, proven zero-effect approval yield, or typed blocker |
| `checkpoint` | Parent-only expected-state control transaction after foreground completion; never arbitrary artifact content | New revision and checkpoint hash |
| `reconcile` | Read cursor, marker, receipts, Git/PR/checks; acknowledge only demonstrably completed effects | Resume action, no-op completion, or required decision |
| `observe-ci` | Read structured exact-head checks until the effective deadline or terminal classification; never renew the deadline itself | Green, failing, pending/timeout or blocker plus exact identities |
| `extend-ci-deadline` | Parent-only, explicitly approved, idempotent update of the private marker after identity/ownership checks; retain the original deadline and all usage | Old/new deadline, approval identity and unchanged usage counters |

Use closed, versioned input/output shapes. Proposed modules under
`scripts/autopilot/`: `contracts.py`, `arguments.py`, `plan.py`, `evidence.py`,
`state.py`, `recovery.py`, `queries.py`, `ci.py`, and `pipeline.py`, with a small
`__init__.py`. Keep each new module/entry script under 300 lines. Prefer functions
and immutable records; do not add a general workflow framework or dependency.
Use stdlib JSON/type validation with explicit semantic checks, existing secure
filesystem operations and artifact parsing. Diagnostics and machine stdout must
be separate; reuse established project error conventions, never raw tracebacks.

### Control records and evidence

The existing `compound-gpid-active-state-v1` fields remain. Its optional
`autopilot` section has its own schema version, run ID, revision, worktree/branch,
required base, plan execution digest, installed command/contract identities,
batch/stage pointer, artifact references, folded attempt IDs and next action.
It remains a restart pointer. Phase completion, findings, publication and CI
success are always derived from their existing authorities.

In a validated autopilot stage, the parent is the only versioned cursor writer.
Replace `/cg-work` active-state writes at report creation, phase completion and
blocked stops with bounded `cursor-update-request` events in its final stage
result. Each request identifies the expected cursor revision, event kind and
existing plan/report references; it cannot supply replacement cursor bytes.
The work child still writes its plan progress and work report directly. After
foreground completion, the parent reads back those artifacts and publishes a
validated request through `checkpoint`, including a blocked cursor when warranted.
If the child is interrupted before returning, retain the pre-dispatch marker and
reconcile the plan/report; never invent the missing event or advance the stage.
Unknown writer state remains blocked without a new versioned cursor write.
The active-state contract's newest-workflow replacement rule does not apply
inside stage execution. Ordinary standalone work retains its current lifecycle;
an interfering external overwrite is detected, not accepted as an autopilot update.

Evidence references contain kind, contained path, byte count, SHA-256, producing
operation ID and applicable content/HEAD identity. Reject self-references,
duplicate keys, unknown versions, malformed types, non-regular/link aliases and
out-of-root paths. Read bounded bytes through `secure_read_bytes()` before
parsing. Use `validate_source()`, not an unchecked pathname read.

Use these initial documented bounds: result JSON 4096 UTF-8 bytes; stage envelope
16384 bytes; checkpoint/private marker 32768 bytes each; at most 16 artifact
references per result. Helper input limits are separate from parent output limits:

| Input kind | Complete-file limit |
|---|---|
| Plan or Markdown report to parse | 2 MiB per file |
| Machine test receipt or structured query response | 8 MiB per file/response |
| File content acquired for a change-manifest hash | 8 MiB per file |
| Combined acquired evidence for one validation operation | 128 MiB |

Read each permitted local document once with `secure_read_bytes(max_bytes=...)`
and validate/hash those same returned bytes. `validate_source()` receives the
complete bounded document. Process files sequentially within the aggregate cap;
do not retain all content in memory. The current secure-read API has no offset or
streaming contract: do not invent chunk reads or add an unchecked read path.
An oversized input stops with `evidence-too-large` and its path/limit, before
parsing or acceptance; do not truncate, silently raise a limit, or split a signed
report into independently accepted pieces. Test exact limits, one byte over,
aggregate exhaustion and replacement during secure acquisition. A streaming
filesystem extension is not part of this plan. Parent packets remain bounded
references, never these complete helper inputs.
Artifact reference paths are not commands. Require
`stage/status/run-id/operation-id/artifacts/head-before/head-after/
change-manifest-hash/tests/next-stage` plus schema version. Status is exactly
`succeeded`, `failed`, `blocked`, or `needs-input`; cancellation is non-success.
Optional decision fields have bounded text and exact advertised option labels.

Pin the batch-start commit and a manifest of staged, unstaged and owned untracked
files, including deletions. Bind tests/reviews to the actual content, not just
HEAD. Exclude only declared generated HTML bodies, the operation's own report
output, and exact declared control/test-output paths from their own content
inputs; record those outputs separately. No directory-wide exemption hides
`.github/`, `.cg-docs/active-state/`, tests or generated code from checking.

Freeze operation-specific test evidence before another run can overwrite a
shared result. Capture command identity, start/end times, scope digest, exit
status and machine-produced result digest. Require a result newer/different than
the pre-run artifact when using `last-run.json`; validate its SHA, filter scope
and actual success. Preserve `accepted-exception` as distinct from `passed`.
Hashes detect inconsistency; they are not proof against a malicious privileged
executor. Static fixture receipts cannot qualify native runtime support.

### Ownership, transactions and budgets

Resolve the private coordination root using `git rev-parse --absolute-git-dir`.
Its run marker holds owner nonce, worktree/run identity, in-flight operation,
pending reservations, deadline and receipt hashes, not phase/finding/CI truth.
Acquire without replacement. Only the matching owner can update or release it.
No lease-only takeover, automatic process killing, rollback or stale-lock deletion.

For each checkpoint change:

1. Expected-byte update the marker with a transaction ID, old and target
   checkpoint digests and the reservations to fold.
2. Validate and publish the checkpoint against its expected previous bytes;
   securely read back the target bytes.
3. Expected-byte acknowledge the target in the marker, retiring only the exact
   reservations demonstrably present in that checkpoint.

Recovery with the old checkpoint does not assume the attempted stage never ran;
reconcile evidence before retry. Recovery with the target checkpoint can finish
acknowledgement idempotently. Other bytes, absent files, quarantines, conflicting
revisions or uncertain ownership block. Preserve recovery files and the error;
do not describe this as cross-file atomic CAS or uninterrupted old-or-new visibility.
Fault-inject the existing secure-write quarantine gap explicitly.

Assign a new operation ID to each actual attempt, separate from logical
batch/stage/phase identity. Reserve before mutation; failed/uncertain attempts
remain charged. A reservation is not automatically a consumed repair round;
apply this exact settlement rule after foreground completion:

| Child outcome | Repair reservation settlement |
|---|---|
| Acknowledged `needs-input` before any effect, independently proven as below | Release the slot with a durable `released-no-effect` record; do not charge a repair round |
| `needs-input` after any fix, finding-status update, test/write or publication effect | Charge the round and preserve partial results; a resumed repair needs a new remaining slot |
| Failed, cancelled, missing/malformed result, uncertain completion or possible surviving writer | Keep the slot charged/pending; no automatic refund |
| Completed mutating repair | Charge once and correlate its evidence/commit with the reservation |

Only the parent can settle a zero-effect release through `validate-stage` and an
expected-state marker update. Require the exact acknowledged child/operation,
all delegated work settled, unchanged HEAD/index/worktree and plan/report status
manifests, unchanged relevant remote/PR identity, and no test or other external
action started. The stage contract requires a durable `begin-effect` receipt
before any such action; its effect-start flag cannot be cleared within the
operation. Validate the marker and available execution receipts, not a child's
free-text claim. Missing or inconsistent accounting blocks a release. Checking
only final file hashes or trusting `mutation-started: false` is insufficient.
This is cooperative protocol evidence, not hostile-executor attestation.
Known control receipts and the decision request itself
are not repair effects. If absence of effects cannot be established, retain the
charge and block; do not infer zero effects from clean Git status alone.

Preserve released reservation IDs and their validation evidence so replay cannot
refund twice. Resume after the answer in a fresh child with a new operation ID,
linked to the prior decision, and reserve again. Multiple proven approval-only
yields do not consume the two repair rounds; partial/uncertain yields do. Release
settlement and answer persistence must survive interruption independently. Native
permission requests still use the runtime's own mechanism and are not semantic
zero-effect approvals.

Deduplicate folded and pending reservations by ID. Two review/fix
rounds apply per batch. Two CI rounds apply per `(GitHub host, repository, PR)`
across batches and sessions. Existing `CI-Fix-Round: <PR>/<round>` trailers
consume slots. New repair commits also carry an `Autopilot-Operation: <id>`
correlation trailer; ambiguous association blocks. Do not erase outstanding
PR reservations by starting a fresh run or changing batches.

### Publication and CI decisions

For source maintenance, run target generation and selected preflight before the
initial batch review and after any triage, lesson or CI repair that changes its
inputs. Reuse the existing publication command's preparation instructions through
an opt-in `prepare-publication` stage envelope: classify source versus consumer,
run only the applicable preparation/generation gates, then return before staging,
commit or push. This stage can inspect a clean already-committed repair and must
not inherit the standalone command's early clean-tree halt. It is a fresh Task,
not duplicated generator logic in the parent. Consumer preparation follows the
project-test route below and never generates Compound GPID source assets.

The order is changed work -> preparation -> initial review, or changed fixes ->
preparation -> eligible review verification. After lesson capture, re-prepare
and validate the new output scope; new substantive inputs require scoped review
before publication. `mode:verify` still requires actual fixes in an eligible
persisted review. Fold any new ordinary review findings into the existing batch
budget rather than resetting it. A no-change preparation is a validated no-op.

Only after the final required review/validation, finalize a publication-intent
checkpoint for that exact prepared payload before publication and include it in
the intended commit. Its payload digest excludes the checkpoint itself; verify
the complete actual commit tree separately. Do not predict a containing commit's
SHA inside that checkpoint. Publication and verification retain their direct
documentation-write prohibitions: the parent performs separately authorized
control operations before entry, not arbitrary writes from those commands.

In the final publication stage, the source generator still runs as required by
the existing command, but it must be byte-idempotent against the approved payload
and complete path inventory. Any covered addition, deletion or content change
invalidates the intent and returns `blocked: publication-payload-changed` before
staging, commit or push. Preserve generated changes; never silently refresh the
approved staging inventory and publish them. The parent records the changed
scope, re-enters preparation and affected review/verification, and creates a new
intent only after the evidence passes. Repeated drift with unchanged generator
inputs stops for diagnosis rather than cycling. Apply the same input/output
manifest guard to preflight and other pre-push steps; a test or commit hook that
changes covered content cannot authorize a push of a different tree.

Post-push CI observation changes no versioned files. Record the first observation
deadline and outstanding reservations in the private marker if the committed
checkpoint predates the observation. A final checkpoint may continue to name
reconciliation after CI passes; GitHub is the outcome authority. Before another
mutating operation, verify clean entry and assign any subsequent cursor change
to a declared parent control operation. Do not broadly ignore a dirty cursor.

### Source and consumer reproduction

Retain the Git-based `$isCompoundGpidSource` decision from the publication
contract and bind it to the run. Use its tracked marker/canonical-contract
evidence, not directory existence, generated adapters, a link target or the
installed helper's own source checkout. Inspection errors, staged deletions or
ambiguous source evidence block; they must not become a consumer fallback.

- **Source maintenance:** retain `scripts/cg_pr_preflight.py` and its registered
  source test inventory, resolved against this source repository and required base.
- **Consumer:** resolve reproduction from the validated plan's verification
  surface, reviewed project test configuration and exact failed check/job. Build
  a bounded test specification with consumer-relative working directory, explicit
  executable/argument array, verification IDs, input digest, and machine-result
  path/format. If selection is absent or ambiguous, ask for a scoped test-command
  decision before mutation. Do not copy commands from untrusted log text.

Before a PR or failed check exists, consumer preparation selects ordinary plan
verification commands without inventing a failure identity. CI repair later
requires a selection bound to its actual failed run/job and reproduction.

Execute the selected consumer command only through the verified execution leaf,
in the consumer root, subject to native permissions. Require it to reproduce the
same failed check before a repair and produce fresh passing evidence afterwards.
Do not call the installed Compound GPID preflight against a consumer or materialize
its `scripts/` or test inventory there. Consumers need not have a Pester layout;
if Pester is selected, preserve the canonical safety contract and stop if an
approved safe runner is unavailable. The control helper validates the selection
and receipts but does not execute tests. Missing dependencies, platform-only
failures or non-reproduction require input, not a guessed generic fix.

Use this source/consumer route for preparation, PR verification and post-fix
evidence. Extend installation qualification through a failed-CI repair in a
consumer with no local `scripts/`, not just successful helper lookup. Pin command
and project-configuration changes to the same approval/evidence invalidation rules.

### Check observation and approved timeout recovery

Use structured `gh` fields matching its wire format, complete pagination and
typed response validation. Resolve exact repository/PR/head/base identities.
Use a required-check manifest from branch protection/rulesets where available;
an absent or incomplete policy is not permission to infer an empty success set.
When tools cannot supply an authoritative applicability decision, ask the user
to approve the expected contexts/app identities and store that scoped policy
reference. Authentication failure is not a policy-choice fallback.

| Observation | Autopilot action |
|---|---|
| All expected applicable contexts present and `SUCCESS`, with no other applicable blocker | Eligible for the final exact-head/base recheck |
| Absent checks, `EXPECTED`, queued, pending, in progress | Bounded observation only |
| `FAILURE`, `TIMED_OUT` | Diagnose through PR verification; no automatic risky/P0/P1 remediation |
| `ACTION_REQUIRED`, `STALE`, unknown applicability, malformed data, auth failure | Block and present the required action |
| `CANCELLED` | Non-success; permit a rerun only under explicit approval and remaining budget |
| `NEUTRAL`, `SKIPPED` | Never success by default; require an explicit applicable/non-applicable policy |
| Head/base changed or evidence belongs to another attempt | Invalidate affected acceptance and reconcile |

Blockers dominate mixed results. Handle repeated runs using explicit context/app
identity and run/attempt ordering; ambiguous duplicates block, not last-list-item
selection. Do not accept one fast passing check while expected checks are absent.
Recheck immediately before dispatching the next batch; do not claim this removes
all races with external actors.

Set the original UTC deadline at the first CI observation for the batch. The
effective deadline initially equals it and is immutable to automatic actions.
Only the explicitly approved extension transition below can change it. Bound every
subprocess/network request by `min(30 seconds, remaining time)`. Poll every
15 seconds while pending, clipping waits to the remaining time. Allow at most
two retries of a read-only transient request and one explicitly approved
infrastructure rerun per batch; neither renews the deadline or a repair budget.
Use monotonic elapsed time during an observation process and persisted UTC
deadline/last-observed time across resume; detected clock rollback blocks.
Unknown process completion is a safe stop, not an excuse to dispatch a new writer.

When observation expires, record `ci-timeout` and keep the normal resume command.
On `/cg-autopilot --resume <cursor>`, reconcile first, then offer a scoped request
to extend observation or remain paused. Approval must specify a positive duration
using the existing 1-second-to-24-hour grammar, the current original/effective
deadline, run/batch, repository/PR/head/base and an approval/request ID. An expired
deadline alone never grants that approval, and no new public bypass flag is added.

The parent invokes `extend-ci-deadline` only after the answer, with expected marker
revision and identity checks and no active/uncertain writer. On first application,
set the new effective deadline to that application time plus the approved duration;
store application/approval times, old/new absolute deadlines, duration, scope hash
and approval reference. Keep the original deadline and extension history. Replay
of the same request ID returns the stored deadline without adding time again;
changed scope, old revision, rollback of the clock or an already-expired proposal
requires a new decision or a safe stop, never silent rebasing of the deadline.
Write this post-push control event only to the private marker and fold its reference
into a later normal checkpoint, preserving clean-tree observation. Repair attempts,
released/charged reservations, reruns, review counts and context usage do not reset.
Extension authorizes waiting only: all manual-CI, evidence, permission and writer
stops remain. Test interruption immediately before/after the marker update and
resume after an extension acknowledgement is lost.

## Phase 1: Contract and Native Bootstrap

### 1. Define the typed stage contract and read-only bootstrap

- **Requirements**: R1, R2, R4, R5, R7, R14
- **Files**: new `.github/shared/autopilot-stage.contract.md`, `.github/prompts/cg-autopilot.prompt.md`, `.github/agents/cg-autopilot.agent.md`, `.github/agents/cg-workflow-stage.agent.md`; `.github/shared/module-registry.json`; new `scripts/tests/test_autopilot_contracts.py`.
- **Details**: Specify the interfaces above, authority precedence and probe-only bootstrap, including parent-only cursor writes, stage cursor-update requests, `begin-effect`, preparation-only publication entry and explicitly approved deadline extension. Keep the new command non-executing until runtime and control preflight are satisfied. Initial stage behavior supports only read-only probes. Parent owns coordination; stage executes one canonical command directly. A forged envelope stops, never falls back to ordinary mutation. Add explicit agent ownership; the shared Markdown contract and prompt already match their existing owner globs.
- **Test Scenarios**: valid read-only bootstrap, unsupported adapter, arbitrary document flag, missing marker/operation, malformed result, undeclared agent, instruction-like report text, child attempting a parent-only control operation.
- **Tests**: new contract tests plus structural checks in `tests/prompt-tools.Tests.ps1`, using the safe execution-child runner.
- **Acceptance criteria**: The source contract defines every stage entry/exit and stop; stubs cannot execute an unvalidated pipeline. No duplicated command instructions or automatic model assignment.

### 2. Emit typed per-asset routing and permissions

- **Requirements**: R1, R2, R14, R17
- **Files**: `.github/shared/target-mapping.json`, `scripts/cg_generate_targets.py`, `scripts/tests/test_target_mapping.py`, `scripts/tests/test_target_kilo.py`, `scripts/tests/test_target_drift.py`, generated counterparts/ownership inventories.
- **Details**: Add a closed per-asset metadata allowlist for command `agent/subtask` and agent `mode/permission`. Emit the Kilo parent as primary with Boolean `subtask: false`; emit the stage as subagent. Parent Task allows only the stage; stage allows exact required specialists/executor. Preserve metadata types and deterministic permission ordering. Keep ordinary commands unchanged and keep non-Kilo entrypoints discoverable but unsupported. No global depth/model/config override. Separate declared eligibility from observed runtime qualification.
- **Test Scenarios**: Boolean versus string, nested permission maps, unknown keys/targets, primary-agent exception to the old all-subagent test, unchanged defaults, each unsupported adapter.
- **Tests**: `python -B -m pytest scripts/tests/test_target_mapping.py scripts/tests/test_target_kilo.py scripts/tests/test_target_drift.py -q`; module ownership/dependency/cross-suite checks.
- **Acceptance criteria**: Generated bytes contain the intended native metadata and all ordinary model-inheritance tests pass. Copilot's direct canonical entry also stops honestly.

### 3. Prove native delegation without self-hosting

- **Requirements**: R2, R7, R14, R17
- **Files**: bootstrap section of `.github/shared/autopilot-stage.contract.md`; `.github/agents/cg-fix-problems.agent.md`; exact Kilo permission overrides in target mapping; new `scripts/tests/test_autopilot_runtime.py`; later work-report evidence.
- **Details**: Use the existing primary session to inspect actual Task fields and installed metadata. Generate/load the new read-only agents through supported runtime reload, with any user-owned depth/permission configuration changed only after separate approval. Probe parent -> stage -> reviewer/general and the conditional stage -> fix-problems -> general path. Record exact agent/Task IDs, directory, branch, declared/effective permissions and available model fields. A text capability claim is not a passing probe. Add only test-execution delegation to fix-problems, not delegation of its direct repairs.
- **Test Scenarios**: depth 1 rejection, depth 2 success/conditional failure, depth 3 success, denied target, absent general executor, wrong agent mode, unavailable fields and unsupported alias.
- **Tests**: offline receipt/permission tests plus an actually executed read-only native probe recorded in the plan-linked work report. Do not use a fixture receipt as V1 proof.
- **Acceptance criteria**: Native graph feasibility is demonstrated on the installed runtime. If it cannot be established, stop before Phase 2 and report the missing capability; do not substitute a plugin, CLI, Agent Manager or same-context execution.

#### Approved Runtime-Acquisition Correction (2026-09-13)

The user's explicit **Approve Local Plugin** decision adopts
`.cg-docs/plans/2026-09-12-autopilot-native-evidence-revision.md` only to correct
the assumption that standard child context exposes trusted native identity and
the plugin exclusion in this Step 3/bootstrap acquisition path. The approved
worktree-local plugin may supply bounded identity/evidence and fail-closed probe
guards; it must not implement or replace native Task, create sessions or run
models. CLI, Agent Manager and same-context substitutes remain excluded.
Production identity checks remain fail-closed, V1 still requires complete actual
native tests, and Phase 2 stays blocked until Phase 1 is complete. Original
Steps 1/2/3 retain 2/2 exhausted attempts each. The separate
`NATIVE-EVIDENCE-REVISION-01` has one initial execution and at most two focused
recoveries total, with its exact inventory, constraints and technical stops in
the linked revision. No other Original plan-body requirement is changed.

#### Approved Permission-Baseline Correction (2026-09-14)

The user-approved exception unit `TASK-DISPATCH-01` (approval turn
`2026-09-14T20:33:52Z`) corrects two live-probe findings from 2026-09-14: the
deny-first Task baselines on the bootstrap parent and stage caused
session-level inherited Task denies to override declared allow exceptions, so
the stage subagent had no effective Task tool; and the candidate leaves
(built-in `general` and `cg-code-quality`) have full native tool access and are
not read-only enforced. The correction: non-denying `ask` Task baselines with
EXACT named allows (parent allows only `cg-workflow-stage`; stage allows only
`cg-code-quality`, `cg-fix-problems` and the new `cg-bootstrap-leaf`;
`cg-fix-problems` keeps its single `general` allow with the same symmetric
`ask` baseline). A new restricted READ-ONLY leaf agent `cg-bootstrap-leaf`
replaces built-in `general`/`cg-code-quality` for read-only probe edges (it has
no Task key, no delegation, and bash access restricted to the contract's four
Git probes). `ask` is approval-gated, never a bypass; no `task: {"*":
"allow"}` is installed anywhere. All other plan constraints are unchanged:
model defaults, root `kilo.json` depth 3, no user/global config or plugin
changes, and V1 remains unqualified until supported reload and fresh probes
(e.g. `phase1-20260914-stage-reviewer-02` and `phase1-20260914-stage-general-03`).

## Phase 2: Deterministic Evidence and Control State

### 4. Implement strict invocation and plan validation

- **Requirements**: R3, R5, R15
- **Files**: new `scripts/cg_autopilot.py`, `scripts/autopilot/__init__.py`, `contracts.py`, `arguments.py`, `plan.py`; new `scripts/tests/test_autopilot_arguments.py`; `scripts/tests/test_autopilot_contracts.py`.
- **Details**: Implement `inspect`, closed packet validation, argument expansion, strict control frontmatter and immutable execution digest. Reuse bounded secure reads and `validate_source()/parse_artifact()`. Validate real phase headings, required evidence structure and completed-prefix consistency; do not trust the convenience `phases` count. Fresh/resume forms cannot silently change identities or bypass an unfinished batch.
- **Test Scenarios**: example batches, singletons, every invalid grammar case, fenced fake headings, duplicate keys, aliases/link escapes, malformed completion metadata, changed body with unchanged progress, valid progress-only delta.
- **Tests**: focused argument/contract tests and existing artifact parser/validator tests under `scripts/artifact_views/tests/`.
- **Acceptance criteria**: Invalid input returns a typed bounded error before writes. Every valid segment expands into the exact single-phase command; supported plan compatibility is explicit.

### 5. Bind changes, reports and test evidence to operations

- **Requirements**: R5, R6, R16, R17
- **Files**: new `scripts/autopilot/evidence.py`; new `scripts/tests/test_autopilot_evidence.py`; existing summary/preflight modules only for narrowly reused functions.
- **Details**: Implement manifest capture and reference verification, exact report/finding identities, test-result freshness and operation-specific frozen receipts. Acquire each complete document through the current secure-read API within the per-kind and aggregate limits, and parse/hash those same bytes; do not add streaming or pathname-read fallbacks. Verify plan-linked work reports rather than newest files. Allocate collision-safe reports ending in `-review.md` or `-verify-review.md`, with explicit report type and parent identity. Define exact self-output exclusions and return only compact verification results.
- **Test Scenarios**: same HEAD/different files, renamed/deleted/untracked inputs, stale or missing runner result, successful summary without test execution, incomplete review, forged success, wrong parent report, exact/over-limit and aggregate input sizes, file replacement during secure acquisition, hard-linked evidence, report collision.
- **Tests**: new evidence tests plus `scripts/tests/test_cg_summary.py` and relevant preflight result tests.
- **Acceptance criteria**: Success text, stale runner artifacts and empty findings without complete coverage cannot advance a stage. Returned evidence is bounded and content-linked.

### 6. Implement owned control transactions and recovery

- **Requirements**: R9, R10, R13, R17
- **Files**: new `scripts/autopilot/state.py`, `recovery.py`; `.github/shared/active-state.contract.md`; new `scripts/tests/test_autopilot_state.py`, `test_autopilot_recovery.py`; existing `scripts/tests/test_secure_fs.py` as regression coverage.
- **Details**: Implement `prepare/begin-stage/begin-effect/record-result/checkpoint/reconcile` around the defined marker/checkpoint protocol. Permit versioned checkpoint changes only through the parent; stage operation rights cover its own private effect/result receipts, not cursor replacement. Keep run-specific and PR-scoped reservations through interruption, with durable zero-effect release and charged/uncertain settlement records. Use expected-byte operations and detect quarantine/publication gaps. Return exact recovery diagnostics without removing another owner's files. Do not modify the global secure filesystem algorithm just to conceal its interruption semantics.
- **Test Scenarios**: crash before/after every marker/checkpoint boundary, old/target/unknown bytes, absent/quarantined state, competing revisions, foreign owner, direct child cursor update, missing acknowledgement, charged failed attempt, released approval-only reservation replay, interrupted effect-start record, reservation folded twice, fresh-run cap bypass.
- **Tests**: new state/recovery tests and `scripts/tests/test_secure_fs.py`, using temporary fixture repositories and injected clocks/failures.
- **Acceptance criteria**: Reconciliation is idempotent, never resets budgets or steals ownership, and preserves recoverable files. CI observation needs no versioned state write. Unknown effects remain blocked.

## Phase 3: Sequential Command Execution and Decisions

### 7. Implement the parent transition loop and decision handoff

- **Requirements**: R2, R4, R5, R7, R13, R14
- **Files**: parent/stage prompt and agents; `.github/shared/autopilot-stage.contract.md`; new `scripts/autopilot/pipeline.py`; new `scripts/tests/test_autopilot_pipeline.py`.
- **Details**: Implement the closed transition table and stage activation, including fresh preparation-only Tasks before the applicable reviews. Dispatch one fresh foreground Task per operation without `task_id` reuse or background writers. Correlate the returned native child ID with the reserved operation, then validate artifacts and cursor-update requests through helpers. The parent never implements repairs or executes arbitrary returned commands. Convert semantic decisions to `needs-input`, preserving exact options and action/content scope; settle a reservation only under the defined zero-effect rule. Require `begin-effect` before a stage's first substantive action. Native permission questions remain native. Approved batches authorize structural continuation only.
- **Test Scenarios**: successful phase progression, failed/cancelled/malformed child, returned child mismatch, attempted parallel writer, forged envelope, automatic approval attempt, stale approval, several zero-effect decision yields, a partial-effect yield, interruption after an answer, same-session resume mistaken for fresh context.
- **Tests**: pipeline state-machine tests with a recording fake dispatcher; negative prompt guards; repeat native permission checks after expanding stage functionality.
- **Acceptance criteria**: No transition bypasses evidence or human gates. The stage cannot become a generic privileged execution route. No unverified model override is accepted.

### 8. Integrate work, persisted review, triage and verification

- **Requirements**: R3, R4, R5, R6, R7, R13
- **Files**: `.github/prompts/cg-work.prompt.md`, `cg-review.prompt.md`, `cg-fix-triage.prompt.md`, `cg-commit-push-pr.prompt.md`; `.github/shared/active-state.contract.md`; `.github/shared/goal-execution.contract.md` only where needed for explicit report permission/identity; `tests/prompt-tools.Tests.ps1`; new `scripts/tests/test_autopilot_handoffs.py`.
- **Details**: Bind work to one explicit plan/phase and return at its boundary without bypassing final evidence/roadmap gates. Replace every stage-mode work cursor write, including report-created and blocked-stop paths, with a request for parent publication; keep direct plan/report writes and all standalone lifecycle writes. Implement the publication command's preparation-only stage here, before handoff tests depend on it: retain source classification/generation and validated ordinary consumer tests, but return before staging/commit/push. Initial review routes normally after preparation and persists directly before its autofix/questions step. Triage consumes exact report hash and eligible findings with a reserved round; apply explicit settlement to approval-only versus partial-effect yields. Regenerate affected source outputs before the exact eligible verify report; never fall back to another review. Preserve the prohibition on following report recipes; independently derived canonical maintenance fixes need exact approved scope.
- **Test Scenarios**: two work phases/two contexts then preparation and initial review; every work cursor-write point and interrupted report creation; unchanged standalone cursor behavior; clean preparation-only entry; canonical triage fix changing generated output before verify; unknown/latest report rejected; >15 findings without filename-selection ambiguity; no actual fix; repeated zero-effect approvals; partial fix then question; incomplete reviewer; skipped P0/P1; new verification finding; two-round exhaustion.
- **Tests**: handoff journeys plus `. tests\Run-Tests.ps1 -File prompt-tools` in a verified execution child, not in the parent session.
- **Acceptance criteria**: The original single-phase API remains intact; reports are collision-safe; all evidence and finding dispositions are explicit. Phase completion does not imply batch or CI completion.

### 9. Integrate conditional lesson capture and approval scopes

- **Requirements**: R4, R7, R8, R16
- **Files**: `.github/prompts/cg-compound.prompt.md`; shared stage contract; `scripts/tests/test_autopilot_handoffs.py`; `tests/prompt-tools.Tests.ps1`.
- **Details**: Supply bounded problem/root-cause/fix/evidence references instead of conversation history. Require the applicable human test-pass confirmation. Skip trivial lessons. Declare solution, related-doc, Brain rebuild, context/wiki and external team-Brain effects separately; do not interpret `--no-enrich` or `--no-brain` as suppression of all side effects. Pause before any unapproved scope expansion or external effect. Validate resulting artifacts, re-enter preparation if inputs changed and require affected review/validation before freezing publication intent; do not publish a post-review generated delta as implicitly approved.
- **Test Scenarios**: trivial skip, useful approved lesson, no confirmation, changed fix after approval, unsafe report instructions, wiki/context side effects, configured external push, lesson outputs invalidating prepared publication scope.
- **Tests**: handoff tests plus focused safe prompt guards and artifact validation fixtures.
- **Acceptance criteria**: No mandatory compounding for trivial work and no lesson document before required confirmation. Direct command behavior and ordinary workflows remain documented and tested.

## Phase 4: Publication and Bounded CI

### 10. Implement structured Git/PR observation and publication reconciliation

- **Requirements**: R5, R10, R11, R17
- **Files**: new `scripts/autopilot/queries.py`; `recovery.py`; `.github/prompts/cg-commit-push-pr.prompt.md`; new `scripts/tests/test_autopilot_publication.py`; `scripts/tests/test_cg_pr_preflight.py`.
- **Details**: Use injected argv-based runners, bounded output/timeouts, exact `gh` wire fields and typed shape errors. Require the selected base before invoking existing base resolution. Retain the publication contract's Git-based source/consumer classification and bind it to the run. Distinguish dirty implementation, clean committed/unpushed, pushed/no PR, existing matching PR and lost acknowledgement. Reuse the Step 8 preparation path and publication logic; final generation must be byte-idempotent against the reviewed payload and complete path inventory. On covered drift, return before staging/commit/push, invalidate intent and route through preparation and affected review before a new intent. Repeated drift with unchanged inputs blocks. Check preflight and commit-hook effects before push as well. Preserve documentation-write restrictions and separately prepared checkpoints. Do not rebase, force-push, merge or retarget automatically.
- **Test Scenarios**: default main/required dev, actual PR base mismatch, branch/repository ambiguity, source inspection error versus true consumer, closed/merged PR, malformed/paginated payloads, local/remote head divergence, lost commit/push/PR acknowledgement, clean-tree reconciliation, canonical triage delta, no-op generation, added/deleted generated paths, repeated generation drift, preflight/hook mutation with no push.
- **Tests**: publication fixtures using temporary Git repositories and no live remote mutations; preflight regressions.
- **Acceptance criteria**: One unambiguous open PR is reused or created against the required base. Recovery neither duplicates commits/PRs nor trusts a child's publication claim.

### 11. Implement deadline-aware check classification and safe diagnostics

- **Requirements**: R5, R11, R12, R13, R16
- **Files**: new `scripts/autopilot/ci.py`; `queries.py`; new `scripts/tests/test_autopilot_ci.py`; recorded-wire fixtures under `scripts/tests/fixtures/autopilot/`.
- **Details**: Implement the CI policy table, required-context identity, complete pagination, original/effective deadlines, clipped request/poll timing and bounded transport retry/rerun policy. Implement the parent-only `extend-ci-deadline` transition in the existing state/recovery modules: explicit scoped approval, idempotent request ID, original deadline/history retained and no reset of usage or other gates. No observer can extend its own deadline. Fetch diagnostic evidence only from exact failed run/job identities, with size limits and redaction before model output. Keep logs out of parent packets and raw logs out of versioned evidence. Emit closed reason codes, identities and counts, not copied arbitrary server messages.
- **Test Scenarios**: absent/EXPECTED/pending, success with missing expected context, mixed failure/manual state, skipped/neutral/cancelled, stale rerun, wrong SHA, duplicate names/apps, auth and wrong-shape JSON, timeout/clock rollback, approved/declined/stale extension, lost extension acknowledgement, unchanged counters and clean tree, uncertain-writer rejection, rerun exhaustion, secret sentinels and oversized logs.
- **Tests**: CI tests with fake clocks/runners and wire-format fixtures; no sleeps or network calls in unit tests.
- **Acceptance criteria**: Only complete applicable exact-head success is eligible. Every observation is finite. No automatic action renews time; an explicit approved extension changes only the effective deadline, never PR repair slots or other usage.

### 12. Integrate PR verification and repair revalidation

- **Requirements**: R4, R6, R7, R10, R11, R12, R13
- **Files**: `.github/prompts/cg-verify-pr.prompt.md`; stage contract; `pipeline.py`, `queries.py`, `evidence.py`, `recovery.py`; publication/CI/pipeline tests; safe prompt guards.
- **Details**: Bind PR verification to exact repository, PR, required base and head and the retained source/consumer route. Source maintenance retains its focused preflight selector; a consumer uses validated plan/project test specifications through the verified execution leaf, never the installed source test inventory. Require exact failed-job reproduction before repair and fresh passing evidence afterwards; missing/ambiguous consumer selection yields `needs-input` before effects. Preserve clean repair entry, targeted staging, CI-Fix-Round trailers and one post-push observation. Use fetched-base ancestry consistently and distinguish Git exits 0, 1 and error. Reserve the PR slot before repair with the defined no-effect/partial-effect settlement. After an already committed/pushed repair, prepare generated/project outputs and review the exact changed scope, reconcile any remaining publication and await current-head checks. Do not duplicate the repair commit/push.
- **Test Scenarios**: source preflight versus consumer tests, consumer without local scripts reproduces/fixes/passes its own failed job, ambiguous commands and missing safe runner, wrong failed-job reproduction, consumer configuration change, first/second repair, third attempt across batches/resume, failure before commit still charged, approval-only versus partial-effect yield, existing trailer without operation ID, clean committed repair preparation/review, conflict/auth/P0/P1 stop, final head/base change.
- **Tests**: combined publication/CI/pipeline journeys and focused safe prompt guards.
- **Acceptance criteria**: The next batch never starts on pending/failing/stale/unverified CI or unresolved blocking findings. Repairs cannot bypass review or create another budget by restarting.

## Phase 5: Consumer Distribution and Context-Safe Resume

### 13. Install the helper and preserve user-owned runtime configuration

- **Requirements**: R1, R2, R14, R15, R17
- **Files**: new `bin/cg-autopilot-control`, `bin/cg-autopilot-control.cmd`; `install.ps1`, `scripts/install.sh`; relevant reporting in `scripts/link.ps1`; `scripts/tests/test_project_projection.py`; new `scripts/tests/test_autopilot_install.py`; relevant existing install/launcher Pester tests.
- **Details**: Follow installed wrapper-relative resolution and version-verified Python detection, including Windows Store-stub rejection. Pass the validated consumer root explicitly and retain its own reproduction/test selection, not the helper checkout's preflight. Verify helper/contract versions and allowlisted code paths. Do not solve installation by adding a directory unit ignored by manifest projections or copying Compound GPID scripts/tests into consumers. Preserve user-owned config bytes and require explicit scoped depth/permission setup; never overwrite global settings or enable broad permissions automatically. Extend installed qualification through the Step 12 consumer repair path.
- **Test Scenarios**: Windows/POSIX wrappers, paths with spaces, consumer without scripts completes failed-CI reproduction/repair/review/publication/green with its own test command, installed source tests are never selected, missing Python/Store stub, wrong helper version, partial install, linked projection, unowned/modified config and unsupported adapter.
- **Tests**: install/projection/launcher tests; load Windows CMD detection and Pester safety skills before working on those files. Verify native tree drift after generation.
- **Acceptance criteria**: A linked consumer can resolve the helper without the source-repository CWD, and unsupported/preserved-blocking configurations fail explicitly without modification.

### 14. Integrate read-only resume and measurable context limits

- **Requirements**: R9, R10, R14, R16, R17
- **Files**: `.github/prompts/cg-resume.prompt.md`, `.github/prompts/resume-templates.md`, `.github/shared/context-loading.contract.md`; `scripts/cg_audit_context.py`; `scripts/tests/test_audit_context.py`; new `scripts/tests/test_autopilot_context.py`; stage/pipeline tests.
- **Details**: Make unfinished autopilot reconciliation take precedence over phase-only suggestions without making `/cg-resume` a writer; it recommends the exact `/cg-autopilot --resume` command. The autopilot parent reconciles an expired window and offers its scoped extension decision; only the separately approved parent helper transition writes the private control event. Register the new workflow in source-budget audits and update exact-count tests. Keep complete stage JSON within 4096 bytes; measure total returned frames including metadata/warnings and budget-check before another dispatch. Start with an 8192-byte per-frame ceiling and a 65536-byte cumulative returned-frame allowance per parent context. Pause rather than truncate or claim fresh-context reset in the same session. Verify or explicitly confirm a fresh primary context before resetting only that context allowance; reservations/usage never reset, and deadline changes require the explicit extension transition.
- **Test Scenarios**: completed phases but unfinished CI, forged next command, stale pointer, wrong owner, expired deadline then approved/declined extension, repeated resume does not add time, read-only `/cg-resume`, oversized final warning/header, repeated compact stages, full-log leakage, unknown model/Auto and same-context resume.
- **Tests**: context/audit/pipeline tests plus representative native frame measurements; source-token estimates alone are not savings evidence.
- **Acceptance criteria**: Resume stays read-only, exact next actions are generated safely, and measured context limits include full returned envelopes. No constant-memory or native pre-delivery truncation claim.

## Phase 6: Qualification and Handoff Documentation

### 15. Prove complete journeys with injected failures

- **Requirements**: R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R17
- **Files**: new `scripts/tests/test_autopilot_journeys.py`; fixtures under `scripts/tests/fixtures/autopilot/`; all focused tests above.
- **Details**: Drive at least two batches through the real control transition functions with a recording dispatcher, temporary local Git remote and exact-wire fake GitHub backend. Inject interruption before/after phase progress, each state write, receipt return, review update, commit, push, PR creation and repair trailer publication. Keep test seams injection-only; no production bypass flags for fake success or unsupported runtime.
- **Test Scenarios**: complete flow with/without findings and lesson, all child failure forms, missing nested Task, all legacy work cursor-write points, lost writes, repeated zero-effect approvals and partial-effect yield, dirty cursor, unknown writer, publication generator drift and re-review, no-local-scripts consumer repair, existing/new PR, wrong base, pending/failure/timeout/approved extension/rerun, lost extension acknowledgement, third CI round, whole-document input limits, changed source/commands/config and context exhaustion.
- **Tests**: full new autopilot pytest set; fixture safety tests verify no live network or destructive operation reaches a real checkout.
- **Acceptance criteria**: Every required transition and stop has an executable negative case. Repeated reconciliation is a no-op or the same blocker, not duplicated work. No silently skipped coverage.

### 16. Qualify installed native behavior and generated adapters

- **Requirements**: R1, R2, R14, R15, R16, R17
- **Files**: runtime/install/context tests and their documented probe protocol; `scripts/cg_pr_preflight.py`; existing module, target and projection tests; plan-linked work evidence.
- **Details**: Repeat conformance against the final installed parent/stage/leaf graph, helper, command hashes and user-approved configuration. Use an explicitly approved disposable consumer for native multi-operation smoke work; do not create a live remote PR solely for testing. Capture actual child IDs, sequential completion, write scope, denial behavior, effective selection when requested and full returned-frame sizes. Qualify each claimed OS; an untested host remains unsupported. Register every new pytest file in `NATIVE_PYTEST_FILES`; register a Pester file only if one is actually added. Preserve existing CI selection authority.
- **Test Scenarios**: final versus bootstrap metadata, changed config invalidating a probe, real nested execution, non-Kilo entry rejection, consumer install/reload, cancellation with uncertain child and hidden model selection.
- **Tests**: actual native smoke artifacts plus full Python, safe Pester, module and preflight regression gates. Mock success cannot satisfy native rows.
- **Acceptance criteria**: The advertised support matrix matches performed qualification. Missing runtime evidence blocks feature completion, even if all offline tests pass.

### 17. Document the operating contract and close evidence

- **Requirements**: R1, R7, R10, R11, R12, R13, R14, R15, R16, R18
- **Files**: `README.md`, `docs/reference.md`, `docs/workflows/index.md`, `docs/configuration/index.md`; canonical command/contract docs and generated counterparts; plan/work-report progress via the normal work workflow.
- **Details**: Document exact fresh/resume examples, required base behavior, scoped approvals, zero-effect versus charged repair rounds, two CI rounds per PR, explicit deadline-extension semantics, preparation/review/publication ordering, parent-only checkpoints, consumer-owned reproduction, complete-file evidence limits, installed-helper setup, conditional nesting and context limits. Explain what locks and receipts do not prove. Include recovery for interrupted/quarantined control state without instructing broad deletion or force operations. Link the two existing advanced ideas without adding features. Run final source/artifact validation and confidence checks.
- **Test Scenarios**: documented command forms accepted/rejected as stated, examples do not use invented flags, generated docs stay in parity, recovery guidance preserves unrelated work.
- **Tests**: documentation/target tests and final command/contract validation.
- **Acceptance criteria**: Documentation matches the qualified behavior. Only verified required evidence allows plan/roadmap completion; no merge, release or automatic user-config change is part of this plan.

## Testing Strategy

Write tests before implementation. New tests are proposed file paths, not claims
that the commands below can run before those files are created. Use injectable
runners, clocks, IDs and failure points. Match actual GitHub CLI field names and
pagination shapes. Assert response shape as well as JSON syntax; catch deliberate
domain errors without hiding unexpected implementation exceptions.

Representative focused commands after the relevant steps exist:

```text
python -B -m pytest scripts/tests/test_autopilot_contracts.py scripts/tests/test_autopilot_arguments.py scripts/tests/test_autopilot_evidence.py -q
python -B -m pytest scripts/tests/test_autopilot_state.py scripts/tests/test_autopilot_recovery.py scripts/tests/test_secure_fs.py -q
python -B -m pytest scripts/tests/test_autopilot_pipeline.py scripts/tests/test_autopilot_handoffs.py -q
python -B -m pytest scripts/tests/test_autopilot_publication.py scripts/tests/test_autopilot_ci.py -q
python -B -m pytest scripts/tests/test_autopilot_runtime.py scripts/tests/test_autopilot_install.py scripts/tests/test_autopilot_context.py scripts/tests/test_autopilot_journeys.py -q
python -B scripts/cg_validate_modules.py --check-ownership
python -B scripts/cg_validate_modules.py --check-dependencies
python -B scripts/cg_validate_modules.py --check-cross-suite
python -B scripts/cg_generate_targets.py --all
python -B -m pytest scripts/tests/test_target_mapping.py scripts/tests/test_target_kilo.py scripts/tests/test_target_drift.py scripts/tests/test_project_projection.py scripts/tests/test_audit_context.py -q
```

Generation is an intentional work-phase mutation; inspect its complete path
inventory and never hand-edit generated output. There is no generator `--check`
flag. Run Pester only through the verified execution child and canonical runner:
`. tests\Run-Tests.ps1 -File prompt-tools` for focused work, and
`. tests\Run-Tests.ps1` for the full gate. Check fresh `tests/last-run.json`;
non-null `filteredFiles` cannot satisfy the full gate. Do not run Pester now as
part of planning or inject its full output into the parent.

Final preflight uses the actual required base:
`python -B scripts/cg_pr_preflight.py --phase prepare --base origin/dev --full-gate --run-native-target`.
If the active integration base differs at execution, obtain/record that explicit
change rather than silently defaulting. Publication itself also requires its
existing committed-phase checks; neither prepare nor selection-only is a substitute.

## Documentation Checklist

- [ ] Fresh/resume syntax, phased prerequisites, strict v1 plan eligibility and helper exit/status contract are documented.
- [ ] Each new function has typed parameters/returns, errors and a docstring example; new modules stay under 300 lines.
- [ ] Kilo depth/permission setup is explicit and user-owned configuration is preserved.
- [ ] Unsupported adapters, OS qualification, model limitations and safe-pause boundaries are stated without false guarantees.
- [ ] Review/CI caps, zero-effect reservation settlement, approved deadline extension, rerun policy and exact-base/head checks are documented.
- [ ] Parent-only cursor writes, quarantine recovery and native permission versus semantic approval are distinct.
- [ ] Generation precedes affected review; final publication cannot push payload drift.
- [ ] Consumer launchers and consumer-owned CI reproduction work without a local Compound GPID scripts/test layout.
- [ ] Complete-file input limits, parent output limits, generated ownership, source budgets and tests remain consistent.
- [ ] The existing core roadmap feature is reused and the two advanced ideas remain deferred.

## Risks & Mitigations

| Risk | Mitigation and decisive test |
|---|---|
| Native nesting or dispatch evidence is unavailable | Bootstrap with existing primary session; require actual graph proof before Phase 2 and repeat final qualification. Do not self-host or silently emulate. |
| Stage metadata is mistaken for authorization | Correlate only native parent-owned operations; preserve all tool/charter permissions. Reject document flags and invalid envelopes. No security credential claim. |
| Quarantine or two-file interruption loses the cursor | Record transaction digests first, detect old/target/unknown states, preserve recovery files and block uncertain cases. Fault-inject every boundary. |
| A marker and cursor become competing truth | Neither stores execution conclusions as authority; reconcile plan/reports/Git/GitHub and deduplicate only control reservations. |
| A work child replaces the parent's cursor | Stage-mode lifecycle points return update requests; only the parent checkpoints after completion and read-back. Test report-created, phase and blocked-stop paths. |
| A post-push cursor update breaks the clean-tree gate | Commit intent before publication, observe CI without versioned writes and test repair/review/publication journeys. |
| Publication generates a new payload after review | Prepare before affected review; final generation/preflight/hook deltas block before push, invalidate intent and require new evidence. |
| Test or review evidence is stale despite matching HEAD | Bind actual content manifest, operation identity, time, exit and machine-result digest; test unchanged-SHA and overwritten-result cases. |
| Evidence exceeds what the secure-read API can acquire | Use explicit complete-file and aggregate limits; parse/hash the same securely read bytes and stop on overflow. No invented chunk API. |
| Another actor or cancelled descendant writes | Cooperative ownership plus content checks; no lease takeover or automatic retry while uncertain. State the non-exclusive threat boundary. |
| Wrong PR base or fast/stale CI is accepted | Explicit required base, expected context/app policy, exact head and complete checks, then recheck before the next writer. |
| Retry or fresh-run entry resets PR limits | Reserve before mutation; correlate pending/folded IDs with PR trailers; test failed-before-commit and cross-batch exhaustion. |
| Approval-only pauses consume repair rounds, or partial repairs are refunded | Release only acknowledged, independently verified zero-effect yields with durable settlement; charge partial/failed/uncertain effects. |
| An expired window has no safe documented recovery | Resume offers an explicit deadline extension; its idempotent private-marker event preserves original time, usage and all other gates. |
| Parent context grows or logs expose secrets | Closed packets, bounded diagnostic acquisition/redaction, real frame budgets and context pause. Never persist raw logs or claim perfect redaction. |
| Helper or CI repair works only in the source checkout | Installed-wrapper-relative code, explicit consumer root, Git-derived source classification and consumer-owned test specification; test a complete no-local-scripts failed-CI repair. |
| Generator changes break existing agents or configuration | Narrow typed per-asset overrides, no model assignments/global depth changes, explicit primary exception, ownership and drift regressions. |

## Out of Scope

- Non-Kilo autonomous execution, Agent Manager stage orchestration, plugins and external model controllers.
- Hard elapsed-time guarantees for whole agent stages, process-tree termination guarantees and enforceable exclusive writer isolation.
- Separate worktrees per stage, automatic conflict resolution/rebase/retargeting, force operations, merging or releases.
- Automatic model selection/escalation, experimental Task field enablement and broad `--auto` approval.
- Automatic edits to user/global runtime configuration or a new general workflow engine/schema framework.
- Unrelated Brain scanner warnings, roadmap restructuring or implementing the two advanced roadmap ideas.

## Completion Contract

### Outcome

The qualified Kilo runtime exposes a usable `/cg-autopilot` with installed control
helpers, fresh sequential stage contexts and verified phase-to-PR journeys. All
unsupported or uncertain cases stop without false completion, and ordinary
commands and generated adapter behavior remain correct.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|---|---|---|---|---|
| V1 | 1 | Typed generation and installed native graph feasibility, including conditional depth 3 | Target/contract tests and actually executed bootstrap probes in the plan-linked work report | yes |
| V2 | 2 | Arguments, whole-document evidence limits, parent-owned transactions, reservation settlement and recovery | Focused argument/evidence/state/recovery/secure-filesystem pytest results | yes |
| V3 | 3 | Work cursor requests, pre-review preparation, exact handoffs and zero-effect/partial-effect decisions | Pipeline/handoff tests, safe prompt guards and direct-write checks | yes |
| V4 | 4 | Payload freeze, source/consumer repair, CI classifications, approved extensions, persistent caps and repair review | Publication/CI/pipeline fixture journeys with injected interruptions | yes |
| V5 | 5 | Installed consumer failed-CI repair, read-only resume/extension handoff and measured context limits | Install/projection/audit/context tests and full-frame measurements | yes |
| V6 | 6 | Complete multi-batch behavior on the supported installed runtime | Journey tests plus final native qualification evidence, not fixture receipts | yes |
| V7 | final | No affected workflow/distribution regressions; all R1-R18 covered | Full safe Pester runner, new and affected pytest suites, module checks, generated drift, PR preflight and artifact validation | yes |

### Constraints

| ID | Phase | Constraint | Check |
|---|---|---|---|
| C1 | final | One pipeline worktree; no overlapping writer or unverified takeover | Ownership, cancellation and same-worktree native tests |
| C2 | final | Preserve standalone semantics and `/cg-work phaseN review:none` | Ordinary-versus-stage branch and handoff tests |
| C3 | final | Existing artifacts remain execution authority; control writes are fail-safe | Transaction/reconciliation and stale-evidence tests |
| C4 | final | Preserve P0/P1, evidence, lesson confirmation, secret and permission gates | Explicit negative cases for each required stop |
| C5 | final | No broad approval, automatic model routing or false adapter support | Native permissions, generated metadata and unsupported-entry tests |
| C6 | final | No hard stage-termination or exclusive-writer claim in v1 | Scope/documentation and uncertain-writer cases |

### Boundaries

- Allowed: incremental maintenance of the exact canonical assets, scripts,
  launchers, tests, documentation and generated counterparts listed in steps;
  future work evidence/control artifacts and isolated fixtures through normal
  `/cg-work` permissions. Roadmap changes go through `cg-roadmap` only.
- Out of scope: implementation during plan creation/review; protected directory
  replacement; global/user config mutation without separate approval; advanced
  supervision/isolation, new runtime support, merges, releases and unrelated work.
- The existing brainstorm and unrelated worktree changes are preserved. Plan
  body revisions require plan-workflow/user authorization, not routine work
  progress writes. All higher-level permission and charter rules still apply.

### Iteration Policy

1. Write failing tests for the selected step, then implement the smallest change.
2. Run focused checks through safe execution paths and record current evidence.
3. After a failed required check, permit at most two focused recovery attempts;
   record each. Exhaustion blocks the completion write and next phase.
4. Under `ask`, obtain approval before a material deviation or added dependency,
   native architecture change or boundary expansion. Never turn a fixture,
   unavailable capability or accepted exception into a passing result.
5. Product runtime budgets are separate: two review/fix rounds per batch and two
   CI-fix rounds per PR, with persistent reservations and no silent renewal.
   Only proven zero-effect approval yields release a reserved slot. Explicit
   deadline extension adds waiting time, not attempts or approval of other actions.
6. Revalidate affected evidence after changes. Required native support, safety
   constraints and exact-head CI claims cannot be made from static inspection or
   an exception that lacks that proof.

### Blocked-Stop Conditions

- Required native Task, depth, permission, agent identity or host qualification
  is missing/unverifiable; do not mark V1/V6 or runtime support passed.
- A required artifact/result is malformed, absent, stale, oversized or unsafe;
  a control revision/owner is uncertain; a writer might still be active.
- A required check cannot run safely or remains failed after the permitted
  recovery attempts; durable work-report evidence cannot be recorded.
- An unresolved P0/P1, risky fix, deviation, evidence exception, lesson-confirmation,
  native permission, conflict, authentication or manual-CI decision needs approval.
- Publication identity/base/head, required-check applicability, deadline or
  persistent attempt accounting cannot be reconciled.
- Completion would need an unapproved protected boundary, false evidence claim,
  unsupported fallback, silent budget reset or unrelated worktree rollback.

## Plan Review Resolution

The initial read-only `/cg-plan-review` returned three P1 and three P2 findings.
The user requested that all findings be addressed. None is accepted as a risk or
deferred. These are plan corrections, not implemented runtime behavior.

| Finding | Plan correction | Implementation and verification anchors |
|---|---|---|
| P1.1: work-child cursor overwrite | Parent-only versioned cursor; child lifecycle points return bounded update requests; interrupted requests reconcile from existing evidence | Control records; Steps 1, 6-8, 15; V2/V3/V6 |
| P1.2: post-review publication generation | Preparation before affected review; final generation must be idempotent; drift stops before staging/push and invalidates intent | Publication decisions; Steps 8-10, 12, 15; V3/V4/V6 |
| P1.3: source-only consumer CI repair | Retained Git source classification; consumer plan/project test specification and verified execution leaf, not Compound GPID preflight | Source and consumer reproduction; Steps 8, 10, 12-13, 15; V4/V5/V6 |
| P2.1: approval-only attempt accounting | Durable zero-effect release with effect-start and independent state evidence; partial/failed/uncertain attempts remain charged | Reservation settlement; Steps 6-8, 12, 15; V2/V3/V4/V6 |
| P2.2: missing timeout-extension recovery | Explicit resume-time approval and idempotent private-marker extension preserving original deadline and all usage | Timeout recovery; Steps 11, 14-15, 17; V4/V5/V6 |
| P2.3: nonexistent chunk-read interface | Bounded complete-file secure reads, per-kind/aggregate caps, same-byte parsing/hashing and overflow/replacement tests | Control records and evidence; Steps 5, 15, 17; V2/V6 |

All six corrections were independently verified on 2026-09-11: six closed,
zero open, and no new P1/P2/P3 findings. Artifact validation and the plan-file
whitespace check passed. The plan is ready for `/cg-work phase1`; native
feasibility, implementation tests and final runtime qualification remain future
work, not completed evidence.

## Planning Handoff

After plan review and corrections, the first implementation command is
`/cg-work phase1 .cg-docs/plans/2026-09-11-kilo-first-autopilot.md`.
No phase has been implemented by creating this plan. Retain `completed-phases: []`
until the work workflow records actual required evidence.

Model advice is non-executable: use strong repository-navigation, decomposition,
testing and validation capability with high reasoning effort for this Deep work.
A more economical option is suitable only for bounded mechanical edits with
verified contracts. Availability differs by platform/date; the user makes the
final selection. This advice must not set frontmatter, dispatch another model
or create retry/model-switch rules.
