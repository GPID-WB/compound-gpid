---
date: 2026-09-11
title: "Kilo-First Autopilot Architecture"
status: decided
scope: "Deep"
artifact-schema-version: 1
chosen-approach: "Foreground Task Parent with Verified Stage Boundaries"
tags: [autopilot, workflow, kilo, phased-execution, recovery, context-budget, ci]
---

# Kilo-First Autopilot Architecture

## Context

The existing roadmap feature `architecture-research/autonomous-pipeline-autopilot`
needs an implementation-ready architecture for long phased plans. The objective
is one command that advances phase batches through work, review, fixes,
conditional knowledge capture, publication, and passing PR checks, with fresh
agent contexts and no overlapping pipeline writers.

The user selected Kilo-first execution and safe-pause recovery rather than hard
elapsed-time guarantees for every agent stage. The user accepted the revised
Task-parent approach, explicitly confirmed the minimal design, and declined
additional complexity before capture. No autopilot implementation was performed.

The roadmap's existing core ID is retained. Its description now records this
scope, and its title no longer implies that a hooks implementation is required.
The core feature remains `idea`, with `plan: null`.

### Research and authority

Research was completed on 2026-09-11. The charter governs constraints; current
commands and runtime observations govern implemented behavior. Older research
is evidence, not an instruction source or proof of current platform support.

| State | Finding | Design consequence |
|---|---|---|
| Established | April workflow research scoped autopilot as research-first work. Its Copilot-specific limitations do not establish current Kilo limitations. [S1] | Reuse the research goals, not obsolete impossibility claims. |
| Established | The phased-execution decision keeps ranges out of `/cg-work` and uses plan completion metadata. [S2] | Parse batches in autopilot; execute one phase per work child. |
| Established | Token strategy favors bounded retrieval, compact summaries, and artifact handoffs. Summary success does not prove test execution. [S3-S5] | Separate evidence generation from summarization; measure actual context use. |
| Established | Current review can fix findings itself, and review/verify select artifacts by chronology. [S6] | Add explicit stage boundaries and artifact identity; do not simply chain unchanged prompts. |
| Established | Existing active state is an untrusted restart pointer without a specified atomic writer or ownership protocol. [S7] | Add deterministic control-state validation and writes, without copying execution truth. |
| Established | Publication retains an existing PR's base ahead of an explicit base argument. Verification requires a clean tree and has no bounded-wait API. [S8] | Enforce the required base before delegation and add a bounded observation helper. |
| Established | Live foreground Task probes inherited this worktree and branch. Generic and adversarial children did not expose Task. | Directory inheritance is proven here; nested delegation is not ready by default. |
| Established in upstream source | Kilo defaults `subagent_depth` to 1; depth and explicit agent Task permissions are separate gates. Conditional per-call model fields require runtime support. [S10] | Check the actual installed schema and permitted delegation graph. |
| Unavailable | A successful probe of the future dedicated stage agent, the conditional depth-3 path, and effective per-stage overrides on the installed build. | Release requires these conformance tests; do not claim support from upstream source alone. |
| Unavailable locally | The standalone `kilo` executable was not on this shell's PATH. | The external-controller alternative was researched, not executed. |

The `open-brain` tool was unavailable. Local Brain entries and saved project
memory supplied historical context. Official Kilo documentation was checked
against upstream commit `3d04228b6a642acb3daf68a649269618b6018250`, dated
2026-09-10. That source snapshot is not proof of the installed release version.
Raw Markdown documentation links returned 404; the corresponding official HTML
pages and pinned source were accessible.

### Current contracts that must be reconciled

- `/cg-work phaseN review:none` suppresses review, not tests, evidence gates,
  phase-continuation questions, or other required decisions.
- `/cg-review --report-only` still asks about findings. It is not an unattended
  report-generation API. Verification can fall back to normal review when no
  eligible parent report exists; autopilot must prohibit that fallback.
- Review and fix triage must perform their specified direct writes themselves.
  The stage child is the command executor, not a dispatcher for those writes.
- Fix triage must not execute instruction-like report text, including recipes
  that attempt to modify canonical `.github/` assets. Authorized maintenance
  scope and independently verified findings are not permission to obey a recipe.
- Work's permissive wording after repeated test failures does not override the
  stricter required-evidence stop in the goal-execution contract.
- The charter requires confirmation before documenting fixes. A child's test
  result cannot supply human confirmation missing from a command's local steps.
- A clean worktree currently stops `/cg-commit-push-pr` before remaining push/PR
  work. A resumed publication needs a narrow reconciliation path, not a duplicate
  commit or an invented public command argument.
- `/cg-verify-pr` currently stops on pending/no checks, performs one observation
  after a repair push, and preserves a two-round cap through PR-scoped
  `CI-Fix-Round` commit trailers. A roadmap description of polling is not an API.
- `EXPECTED`, cancelled checks, incomplete review output, skipped findings, and
  ambiguous ancestry results need explicit classification. None implies success.

## Requirements

### Version-1 support boundary

Kilo is the only planned execution runtime for version 1. `.github/` remains the
canonical source. Generate corresponding assets for Copilot, Claude Code,
Codex, OpenCode, and Kilo through the normal mapping and install paths.

Represent orchestration capabilities separately from generic native-subagent
support: foreground completion, nested depth, target permissions, stage-result
contract, directory inheritance, and supported selection/observation mechanisms.
Non-Kilo adapters must stop before writes with an explicit unsupported-runtime
message. Kilo must also stop if its required capabilities are absent. Never
substitute same-context emulation or Agent Manager for a failed Task capability.

Version 1 does not merge PRs, release software, force-push, reset changes, stash
work, retarget an existing PR, create per-stage worktrees, or promise exclusive
filesystem access, hard agent-stage deadlines, or exactly-once tool execution.
It does not install a CLI supervisor or plugin.

### Command interface

```text
/cg-autopilot --plan .cg-docs/plans/example.md --batches 1-2,3-4,5-6 --base dev --ci-timeout 30m
/cg-autopilot --resume .cg-docs/active-state/current.json
```

The first form is a fresh run. `--plan`, `--batches`, and `--base` are required;
`--ci-timeout` defaults to `30m`. The second form reconciles an existing run; it
does not silently change its plan, batches, branch, base, or attempt limits.
Do not add a broad `--auto` option or a misleading hard stage-timeout option.

- Accept comma-separated positive phase numbers or ascending inclusive ranges.
  `1-2,3-4` means two batches and four separate work operations, not two range
  calls to `/cg-work`.
- Reject empty segments, reversed ranges, repeated or overlapping phases,
  out-of-order batches, unknown flags, missing/repeated scalar flags, malformed
  durations, out-of-plan phases, and skipped incomplete prerequisites.
- Require a valid, project-contained phased plan. Pin its identity and the hash
  of its execution content, distinguishing permitted progress metadata updates
  from a changed design. Changed instructions require reconciliation/approval.
- Check already completed phases against their evidence. A new invocation must
  not bypass an unfinished run's review, publication, CI gate, or attempt cap.
- Treat paths, branch names, report strings, and returned commands as data.
  Validate them and use structured arguments, never shell interpolation of
  arbitrary result text. Construct the next command from the allowed transition.
- Use the supplied integration branch, which can differ from the repository
  default. Both `dev` and `origin/dev` existed during research; `origin/main`
  was the default-branch reference. No new global integration-branch setting is
  required for this interface.

The CI deadline is set when the first CI observation window starts for a batch.
Retries, repairs, reruns, and resume do not silently renew it. It bounds CI
observation, not the wall-clock duration of an entire Task or a hung agent.
An expired deadline blocks the next action; extension requires explicit approval.

### Parent and child agents

Add a dedicated `cg-autopilot` primary agent and a `cg-workflow-stage` subagent.
The Kilo command must route to the parent without an additional subtask wrapper.
Do not make `/cg-work`, or all existing commands, globally `subtask: true`.

The parent selects the next operation, dispatches a fresh foreground Task,
checks compact evidence, asks the user when needed, and calls restricted control
helpers. It never implements fixes or consumes full logs, diffs, or file bodies.
Control helpers parse/validate/update state and observe CI; they do not start
models or form a second agent scheduler.

The child reads the installed, trusted command asset and its referenced
contracts. It executes one allowlisted `/cg-*` command with an explicit stage
envelope: run/operation identity, arguments, permitted scope, artifact references,
remaining budgets, and applicable approvals. It does not copy command bodies
into a new prompt implementation. Record command/contract identities so changed
instructions cannot be silently used during resume.

An opt-in shared stage contract defines exact artifact selection, yield points,
result formatting, and decision handoff. Ordinary invocations retain their
existing interaction model. Direct-write rules remain in force within the child;
required specialist delegation remains inside the verified delegation graph.
Do not treat the envelope as a general override of command or charter constraints.

Require depth 2 for parent -> stage -> reviewer/executor and depth 3 for the
conditional parent -> stage -> fix-problems -> Pester executor path. Configure
explicit Task target rules at each delegating level, not a blanket allowance.
Do not count text-only iteration limits as timeouts. Validate that the generator
actually emits the required agent modes, command routing, and permissions.

All pipeline writes are sequential, including test or generation processes that
write files. Read-only review analysis can use existing independent reviewers,
but a reviewer that runs a mutating test is not a read-only worker. No child may
return while a delegated writer is still active. Do not use background Tasks or
Agent Manager sessions as the stage-completion barrier.

### Model and reasoning selection

Use native Kilo selection by default; do not derive routing from model-advisory
recommendations. The user controls model and reasoning configuration. Optional
user-configured stage-agent aliases can share one stage instruction body.
Validate the required agent behavior and effective selection before accepting
an explicit per-stage selection requirement.

The observed parent Task schema had no model/provider/variant fields. Upstream
source can expose them under an experimental setting, but version 1 must not
assume or enable that setting. Command and agent settings can take precedence
over caller settings. Reject an explicit unsupported or unverifiable override;
never silently ignore it, choose a cheaper model, or switch models on retry.

### Stage state machine

| Stage | Operation and acceptance gate | Next action |
|---|---|---|
| Preflight | Validate run arguments, runtime, plan, branch/base, dirty state, ownership, prior run, and budgets. | First eligible phase, or reconciled pending stage. |
| Work | Fresh `/cg-work phaseN review:none <plan>`; validate phase metadata and current work/test evidence. | Next phase in this batch; otherwise initial review. |
| Initial review | Fresh `/cg-review` under the stage contract; persist the exact scoped report without applying findings in this operation. Require complete coverage. | Block on P0/P1; otherwise triage if findings remain. |
| Fix triage | Fresh `/cg-fix-triage <persisted-review-path>` for approved/eligible findings. Reserve a round before mutation and validate actual fixes. | Verify after fixes; no-fix outcomes must not claim repair verification. |
| Review verification | Fresh `/cg-review mode:verify` bound to the exact eligible parent report. No latest-file selection or normal-review fallback. | Repeat eligible fixes within budget, or lesson decision. |
| Lesson decision | Skip trivial work. Run fresh `/cg-compound` only for a durable non-trivial lesson with required confirmation and bounded evidence references. | Validate all resulting artifacts and proceed to publication. |
| Publication | Fresh `/cg-commit-push-pr --base <required-base>`; reconcile already completed effects on resume. Verify committed/pushed scope and open PR identity. | CI observation. |
| CI observation | Bounded helper reads exact-HEAD checks with request timeouts and a persistent deadline. No unbounded watch or blind fixed-delay success. | PR verification, timeout, or explicit blocker. |
| PR verification | Fresh `/cg-verify-pr` for this PR/head/base. Reuse its repair and PR-scoped round-accounting semantics. | Green validation, or reconcile repair effects and revalidate changed scope. |
| Batch gate | Recheck required evidence, findings, clean publication state, remote/PR head, required base, and passing applicable checks. | Next batch only if all gates hold; otherwise pause. |

Any CI repair invalidates evidence affected by its changes. Review the repair
scope before accepting the batch; use `mode:verify` only for fixed persisted
findings. If PR verification already committed/pushed its repair, reconcile that
publication rather than duplicating its Git logic in the parent. Further changes
require publication and checks for the new head. Neither a repair push nor an
old green result authorizes the next batch.

Use at most two review/fix rounds per batch. Preserve the existing two unique
CI-fix rounds per PR across all batches and sessions; this is not a fresh budget
for every batch. Exhaustion requires a human decision. Bounded read-only
transport retries do not reset workflow budgets, rerun write stages, or turn an
authentication failure into a retry loop.

### Typed result and evidence validation

The result is a bounded protocol object, not authority. Minimum shape:

```yaml
schema-version: 1
run-id: <run identifier>
operation-id: <unique stage attempt>
stage: <stage identifier>
status: succeeded | failed | blocked | needs-input
artifacts: [<project-relative evidence paths>]
head-before: <sha>
head-after: <sha>
change-manifest-hash: <sha256>
tests: <bounded status/counts and current evidence reference>
next-stage: <proposed stage identifier>
```

Conditional fields identify a safe reason code or a decision request with exact
options and the evidence/action scope. Cancellation is a non-success reason,
not permission to advance. Reject malformed, oversized, missing, mismatched,
or unknown-version results. Validate references before opening them. A child's
suggested next command must never be executed as arbitrary input.

Read back the relevant plan frontmatter, current work reports, review finding
metadata and completeness, file/change hashes, Git refs, PR metadata, and check
results. SHA equality alone does not verify uncommitted writes. Test summaries
must reference a fresh successful execution artifact; stale `last-run.json`,
missing output, or summary-command success is insufficient.

Detailed evidence stays outside the parent context. Use redacted, bounded
diagnostics from exact failed run/job identities; do not send full CI logs,
transcripts, diffs, generated HTML, or file bodies. Never persist raw secrets in
versioned evidence. Test final payload size including wrapper metadata and
warnings. Protocol caps are not a native pre-delivery Task size limit, and fresh
children do not make accumulated parent history constant-size. Checkpoint and
pause before unsafe context growth; measure representative long runs before
claiming savings.

### Human approval boundary

- Return `needs-input` before a semantic decision that the child cannot make.
  The parent presents the exact question/options and records the scoped answer.
- Bind approval to the run, proposed action, affected scope, plan/review identity,
  relevant content hash, PR/base/head, and risk. Relevant changes invalidate it;
  unrelated control timestamps must not invalidate a valid content approval.
- Resume through a fresh stage context and revalidated durable references. Do
  not assume a resumed Task ID names the same child or that replay is harmless.
- P0/P1 findings, plan deviations, risky fixes, conflicts, authentication
  failures, manual-action CI, missing evidence, uncertain owners, and exhausted
  budgets stop automatic continuation. Approval of remediation is not approval
  to proceed with an unresolved blocking finding.
- Preserve required confirmation before capturing fixes as lessons. Do not
  synthesize it from test success. If none is available, pause before compounding.
- Native tool permissions remain separate runtime approvals. A workflow answer
  does not bypass them. Do not use broad `--auto`, permission escalation, force
  operations, or blanket approval of future unspecified actions.

### Durable state and clean publication checkpoints

Plan `completed-phases` is implementation-progress authority. Work reports are
execution evidence; review reports govern finding status. Commits and remote
refs govern publication; PR/check metadata governs CI. None of these alone
establishes complete pipeline success.

Extend the existing active-state record at `.cg-docs/active-state/current.json`
with a versioned, compact autopilot control section. Preserve its standard
schema fields and exact `nextCommand`. Store run identity, plan/command/artifact
references and hashes, branch/base, stage/batch cursor, attempt reservations or
counts, deadline, and next action. Do not copy phase bodies, findings, or logs.
The cursor remains a restart pointer that must be checked against authority.

Use deterministic validation, expected-revision checks, and atomic replacement
through the repository's secure filesystem primitives where applicable. Validate
the new content before replacement and read it back. Partial writes, unsafe
paths, revision conflicts, and mismatched ownership fail closed. A timestamp
alone is not a safe ownership or stale-lock test.

Publication boundary:

1. During implementation/review, update the cursor with the other owned changes.
2. Before committing, finalize a recoverable publication-intent checkpoint and
   include it in the intended commit. The checkpoint need not predict the SHA of
   the commit that contains it.
3. After push, keep versioned CI observation read-only. Do not update the cursor
   on every poll and immediately violate verification's clean-tree requirement.
4. Resolve publication/CI after interruption from actual refs and checks. The
   next command can remain a reconciliation command even if CI has since passed.
5. A later mutating stage must pass its clean entry gate before control changes
   join that stage's intended write set. Any stage-only cursor-write permission
   is narrow and explicit; ordinary publication/verify file restrictions remain.

A Git-private coordination marker, resolved through Git rather than assuming
`.git` is a directory, can hold ownership, in-flight operation identity,
unsettled attempt reservations, a deadline, and receipt hashes. It is not an
alternative phase, review, publication, or CI ledger. Fold reconciled control
reservations into the next checkpoint exactly once; do not lose a budget when
an attempt fails before its commit. Reconcile committed CI trailers with pending
reservations by operation identity to avoid either resetting or double counting.

Only the matching owner may update/release its marker. Cooperative locks and
status/hash checks detect some interference; they do not exclude other sessions
or people. On uncertain cancellation, missing acknowledgements, inconsistent
markers, or a possible surviving writer, stop. Do not retry a mutation or steal
ownership because a lease expired. No automatic rollback of unrelated changes.
The checkpoint/marker protocol requires crash and clean-tree journey tests before
implementation can be accepted; prompt wording alone is not a transaction system.

### PR and CI rules

- Require one unambiguous open PR for the current branch/repository, or create a
  new one after validated publication. Reuse the ongoing PR across batches.
- Reject an existing PR whose actual base differs from `--base`, before changing
  anything. Do not let the child silently retain the wrong base or retarget it.
- Reconcile clean-tree runs with committed-but-unpushed work, pushed-but-no-PR
  work, and a PR created before a lost acknowledgement. No duplicate commits or
  PRs. Closed/merged PRs and ambiguous matches require a new human decision.
- Use structured check data, an absolute deadline, and finite per-request
  timeouts. Re-observe status between bounded polling intervals. Do not infer
  readiness from elapsed sleep or use an unbounded `--watch`.
- Missing checks, `EXPECTED`, pending, cancelled, skipped, stale, and
  manual-action states require explicit policy. Never equate no failures with
  complete success. Unknown required-check applicability must block acceptance.
- Check the exact remote/PR head and required base again immediately before the
  next batch. Green checks for another SHA, or before a repair, are not evidence.
- Infrastructure reruns require classified, permitted action and a finite
  budget; they do not renew the deadline or count as proof of a code fix. Auth,
  manual approvals, conflicts, and ambiguous ancestry stop automation.
- Resolve ancestry against the fetched required base consistently. Distinguish
  Git's expected non-ancestor exit result from a command or authentication error.

## Approaches Considered

### Approach 1: Foreground Task Parent with Verified Stage Boundaries

**Summary:** One lightweight primary agent coordinates fresh sequential stage
children in the same checkout.
**Pros:** Uses native foreground completion and the existing command assets.
**Cons:** Needs stage-contract changes, deterministic helpers, verified nesting
and permissions, and safe interruption stops.
**Effort:** Large.
**Recommended:** Yes; fits the selected Kilo-first and safe-pause requirements.

### Approach 2: Fresh CLI Controller

**Summary:** A Python or PowerShell controller starts fresh `kilo run --command`
conversations for operations.
**Pros:** Offers deterministic scheduling and a place for process supervision.
**Cons:** Adds a controller/runtime dependency; headless permissions, JSON event
framing, selection precedence and surviving processes need tests. The CLI was
unavailable locally.
**Effort:** Large.
**Recommended:** No for v1; revisit if hard stage deadlines become required.

### Approach 3: Event-Driven Kilo Plugin

**Summary:** A plugin reacts to session events to coordinate operations.
**Pros:** Integrates lifecycle observation into the Kilo runtime.
**Cons:** `session.idle` is not success; event correlation, replay, cancellation
and durable transitions need implementation.
**Effort:** Large.
**Recommended:** No for v1; it is not needed for the selected guarantees.

### Other evaluated mechanisms

| Mechanism | Summary and pros | Cons and risks | Effort | Recommended |
|---|---|---|---|---|
| Global `/cg-work subtask: true` | Isolates each work invocation with little routing code. | Does not coordinate the pipeline; changes standalone behavior and can add a wrapper depth. | Small but incomplete | No; a routing change is not an orchestrator. |
| Global subtask routing for every command | Makes command invocations separate contexts. | Still lacks dependencies, approvals, evidence checks, or recovery; affects all users and increases nesting. | Medium but incomplete | No. |
| Agent Manager Local sessions | Visible independent sessions sharing a checkout; explicit model options at creation. | Targeted prompts return on acceptance/queueing, not completion. Status or idle alone does not validate the operation. Extra coordination is required. | Large | Defer; not a foreground Task substitute. |

Legacy Kilo workflows are command instructions, not a durable workflow engine.
Agent Manager `replyTo` correlates replies; it does not turn a targeted prompt
into a synchronous call. No stage in this design edits `.kilo/agent-manager.json`.

### Devil's advocate resolution

- Problem validation: long-session/context concerns and the observed nesting gap
  justify investigation, but measured token savings remain an acceptance task.
- Simplicity: retain native Tasks; do not add a plugin or process controller for
  guarantees the user has explicitly deferred.
- Effort and value: the minimum safe feature includes command-contract changes,
  deterministic gates, generation work and failure-path tests, not just a prompt.
- Charter alignment: correctness, explicit failures, scoped approval, secret
  protection and verified lesson capture remain mandatory. Kilo-first execution
  does not excuse false support claims or drift in generated adapters.

## Decision

Select **Foreground Task Parent with Verified Stage Boundaries** for Kilo-first
version 1. Preserve single-phase `/cg-work`, same-worktree sequencing, command
authority and existing human gates. Add the smallest deterministic control
surface needed to validate transitions and recover from durable evidence.

The user explicitly confirmed this design and declined an advanced redesign.
Runtime conformance and the checkpoint transaction are implementation acceptance
gates, not claims that the current unchanged commands are already compatible.

### Acceptance criteria and failure scenarios

| Area | Required evidence before acceptance |
|---|---|
| Arguments and phases | Valid example expands correctly; malformed/duplicate/overlapping/gapped/out-of-range input stops without mutation; completed-phase and resumed-run cases preserve prerequisites. |
| Native execution | Each operation receives a fresh child ID, same worktree/branch and a foreground completion barrier. Denied/missing Task, depth-1/2 limits, conditional depth-3 execution, and incorrect agent modes are tested. |
| Writer safety | Dirty staged/unstaged/untracked inputs, interfering writers, changed branch/HEAD, mutating tests, stale ownership and a surviving cancelled child cannot trigger another writer. No blanket active-state exemption. |
| Child results and writes | Empty/malformed/oversized/mismatched results, lost acknowledgements, partial/missing writes, wrong artifact hashes, stale test files and fabricated success text do not advance state. |
| Review handoff | Exact persisted report reaches triage; initial review does not fix; verify runs only after actual fixes; missing parent report never falls back; incomplete coverage and skipped blockers cannot pass. |
| Decisions | Required decisions reach the parent with exact options; native permissions stay separate; changed scope invalidates approval; a fresh child resumes only after reconciliation. |
| State and recovery | Crash before/after reservation, phase metadata, report write, atomic cursor replacement, commit, push, PR creation and acknowledgement. Resume neither duplicates effects nor resets attempt caps. Unknown owner or torn state pauses. |
| Clean publication | Checkpoint is included before publication; CI observation does not dirty the tree; repair entry and any narrow cursor write set are tested end to end; final green is derivable without a self-referential checkpoint commit. |
| PR behavior | New/existing PR, wrong base, ambiguous/closed/merged PR, clean committed-but-unpushed branch, pushed-but-no-PR and lost PR-creation acknowledgement are covered. |
| CI | Pending/EXPECTED/no checks, failure, cancelled/skipped/manual states, auth/network errors, timeout, rerun, changed head/base and two-fix-round exhaustion across batches/resume are covered. Repairs invalidate affected evidence. |
| Context and secrets | Full final payload stays within its registered budget; representative multi-batch parent/child measurements include metadata; raw CI logs, credentials, generated HTML and file bodies do not enter parent packets. Do not claim native transport enforcement. |
| Models | Native default selection remains user-controlled; explicit aliases/overrides are tested against effective runtime selection; unavailable fields or unsupported reasoning variants fail explicitly. |
| Generation and installs | Canonical ownership, typed command/agent metadata, Kilo primary/subagent routing and permissions, five-adapter unsupported/support gates, installed projections and generated-byte drift are tested. |

Use isolated fixtures and fault injection for deterministic tests; do not claim
prompt assertions prove runtime permission or concurrency behavior. Run real
Kilo smoke tests on the supported installed build for native capabilities. Follow
the repository's Pester safety/execution-child rules rather than running a large
test suite in the parent context. No implementation tests were run in this
brainstorm; only read-only runtime probes and roadmap validation were performed.

### Canonical and generated change surface

- New canonical `.github/prompts/cg-autopilot.prompt.md`, dedicated parent/stage
  agent specs, and a shared opt-in stage/result contract under `.github/shared/`.
- Targeted integration changes to work, review, fix triage, compound, publication,
  PR verification and resume. Resolve their documented conflicts without copying
  entire prompts or changing ordinary invocation behavior unnecessarily.
- Extend the active-state contract and add small deterministic parser, evidence,
  state and CI helpers under `scripts/`, reusing existing secure filesystem and
  summary/preflight infrastructure where its semantics fit.
- Register new agents/capabilities in `.github/shared/module-registry.json`;
  extend `.github/shared/target-mapping.json` and `scripts/cg_generate_targets.py`
  for the required typed metadata and truthful runtime gates. Current generation
  does not preserve all necessary routing/permission fields.
- Regenerate `.kilo/commands/`, `.kilo/agents/` and corresponding Claude, Codex
  and OpenCode assets, shared contracts and ownership/install projections through
  the existing generation paths. Do not author generated files by hand.
- Extend prompt guards, Kilo-target/drift tests, relevant preflight tests, context
  budget registration and end-to-end workflow journeys; add deterministic helper
  tests. Update command documentation with actual support and recovery limits.

### Roadmap follow-ups

The user approved these two new `idea` records in `architecture-research`, both
with `plan: null`:

| ID | Separate scope |
|---|---|
| `autopilot-hard-stage-deadlines` | Research runtime-enforced deadlines, process supervision and descendant-termination checks. Termination is not rollback; do not retry while a prior writer might survive. |
| `autopilot-enforced-writer-isolation` | Research enforceable writer ownership/fencing and runtime-backed interrupted-child reconciliation, with explicit actor/platform coverage. Do not claim advisory locks exclude uncooperative writers. |

Basic writer checks, safe stops, bounded CI, evidence reconciliation and context
regression tests remain core version-1 requirements. Do not defer them to these
ideas. Do not create duplicate model-control, token-benchmark or resume items:
related existing records include `stage-control-knobs`,
`token-benchmark-before-after`, `workflow-context-budget-checks`, and
`workflow-status-resume`. No new plugin or non-Kilo execution feature was added
during this brainstorm.

## Next Steps

1. Run `/cg-plan .cg-docs/brainstorms/2026-09-11-kilo-first-autopilot-architecture.md`.
   Link the resulting plan to `architecture-research/autonomous-pipeline-autopilot`;
   do not create another feature or mark the core planned before that link exists.
2. Start planning with the installed-runtime capability spike and the exact
   checkpoint/ownership/attempt protocol. Preserve an explicit unsupported stop
   until the required native paths are proven.
3. Plan test-first increments for typed command boundaries and generation,
   deterministic state/evidence controls, phase/review execution, publication/CI,
   and interruption/context-budget journeys. Resolve the listed command
   conflicts within their canonical assets.
4. Keep the two advanced ideas outside the version-1 plan. Reassess them only if
   real usage requires guarantees beyond the confirmed safe-pause boundary.

### Evidence references

- [S1] `.cg-docs/strategy/2026-04-13-workflow-automation-research.md`;
  `.cg-docs/competitive-reviews/2026-04-23-gsd-2-full-review.md`.
- [S2] `.cg-docs/brainstorms/2026-05-05-phased-plan-and-execution.md`;
  `.github/prompts/cg-work.prompt.md`; `.github/shared/goal-execution.contract.md`.
- [S3] `.cg-docs/strategy/2026-06-18-token-efficiency-workflow-strategy.md`;
  `.github/shared/context-loading.contract.md`; `.cg-docs/token/TOKEN-BUDGET.md`.
- [S4] `.cg-docs/solutions/testing-patterns/2026-06-23-budgeted-knowledge-brain-query.md`;
  `.cg-docs/solutions/testing-patterns/2026-06-23-command-output-summary-wrappers.md`.
- [S5] `.cg-docs/solutions/testing-patterns/2026-05-06-cross-prompt-user-journey-must-be-validated-end-to-end.md`;
  `.cg-docs/solutions/testing-patterns/2026-06-23-active-state-handoff-records.md`.
- [S6] `.github/prompts/cg-review.prompt.md`;
  `.github/prompts/cg-fix-triage.prompt.md`; `.github/prompts/cg-compound.prompt.md`;
  `.github/agents/cg-fix-problems.agent.md`; `compound-gpid.md`.
- [S7] `.github/shared/active-state.contract.md`;
  `.github/prompts/cg-resume.prompt.md`; `scripts/secure_fs.py`.
- [S8] `.github/prompts/cg-commit-push-pr.prompt.md`;
  `.github/prompts/cg-verify-pr.prompt.md`; `scripts/cg_pr_preflight.py`.
- [S9] `.github/shared/model-advisory.contract.md`;
  `.github/shared/module-registry.json`; `.github/shared/target-mapping.json`;
  `scripts/cg_generate_targets.py`; `scripts/tests/test_target_kilo.py`;
  `scripts/tests/test_target_drift.py`; `roadmap.json`.
- [S10] [Kilo Agent Manager](https://kilo.ai/docs/automate/agent-manager),
  [Agent Manager workflows](https://kilo.ai/docs/automate/agent-manager-workflows),
  [Task tool](https://kilo.ai/docs/automate/tools#task-tool),
  [custom subagents](https://kilo.ai/docs/customize/custom-subagents),
  [permissions](https://kilo.ai/docs/customize/agent-permissions),
  [workflows](https://kilo.ai/docs/customize/workflows),
  [CLI reference](https://kilo.ai/docs/code-with-ai/platforms/cli-reference), and
  [plugin events](https://kilo.ai/docs/automate/extending/plugins#events).
- [S11] Pinned Kilo source at
  [3d04228b6a642acb3daf68a649269618b6018250](https://github.com/Kilo-Org/kilocode/tree/3d04228b6a642acb3daf68a649269618b6018250):
  `packages/opencode/src/tool/task.ts`, `agent/subagent-permissions.ts`,
  `kilocode/tool/task.ts`, `session/prompt.ts`,
  `kilocode/session/workflow-variant.ts`, `permission/index.ts`,
  `cli/cmd/run.ts`, `kilocode/cli/run-drain.ts`, and
  `packages/core/src/v1/config/{config,agent}.ts`.
  Source resolves permission precedence as last matching rule wins. It does not
  substantiate all CLI-overview claims about timeout exit codes or automatic
  question answers; those claims are not part of this design.
