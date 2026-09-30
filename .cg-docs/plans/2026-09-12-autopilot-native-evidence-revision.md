---
date: 2026-09-12
title: "Implement Autopilot Native Evidence Revision"
status: blocked
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-09-11-kilo-first-autopilot-architecture.md"
language: "both"
estimated-effort: "medium"
deviation-policy: "strict"
artifact-schema-version: 1
proposal-status: "ready-for-supported-reload-passive-capability"
execution-authorized: true
execution-report: ".cg-docs/work-reports/2026-09-11-kilo-first-autopilot.md"
tags: [autopilot, kilo, native-evidence, implementation, safety]
---

# Plan: Autopilot Native Evidence Revision

## Objective

Implement the smallest supported worktree-local native-evidence plugin for the
unavailable bootstrap identity and independent native Task evidence paths.
On 2026-09-13 the user explicitly selected **Approve Local Plugin**, including
the corresponding bounded Original plan revision, source/runtime changes,
dependency installation, focused tests, policies and generated ownership.
The former planning-only restriction is superseded. This is execution approval,
not a V1 waiver, production authorization or reset of an Original budget.

The initial interface investigation reached the policy-enforcement stop below.
On 2026-09-13T13:56:28Z the user explicitly continued the SAME initial execution
with passive acquisition only. That finding blocks future policy relaxation,
not passive tools. The same initial 1/1 allocation remains open. Recovery 1 passed;
the user explicitly approved **Approve Final Recovery** at 2026-09-13T20:46:11Z.
Recovery 2/2 was reserved before edits, covering the deduplicated FR-01 through
FR-14 packet in the work report. No further repair remains. A failure after this
coherent patch stops for a precise report; the tests-first red baseline is not
another attempt.
Overall pipeline `status: blocked` remains truthful pending actual native proof.

### Current Checkpoint 2026-09-14T12:27:27Z

FR-01 through FR-14 are independently verified closed. The separately approved
`CI-REPORTER-01` exception is **1/1 used, verified and closed**: one explicit TAP
reporter flag, with the exit-status, zero-skip and missing-mandatory-SDK guards
unchanged. On actual temporary Node 24.21.0, focused pytest passed 9/9 and Node
passed 125/125, without failures, skips or cancellations. The previous broader
pytest result remains 261 passed / 1 skipped; it was not rerun for that exception.
Full Pester from the final-recovery execution leaf passed 2921 of 2923 total,
zero failed and two skipped, with `filteredFiles: null` and no cleanup errors.
The work report records the exact leaf IDs, timestamps, HEAD and Node checksums.

The passive capability is **ready for a supported Config/Skills reload after
this turn ends**, not already loaded or native-qualified. Keep the current normal
implementation agent for the first passive `cg_native_identity` call; selecting
`cg-autopilot` is not needed yet. After reload, require actual new registration
of `cg_native_identity` and `cg_native_evidence`, honor their native permission
`ask`, and use the registered zero-argument identity tool through its native SDK
path. Do not emulate missing tools, delegate a fresh bootstrap or enter Phase 2.

This checkpoint authorizes documentation/status updates only. Revision recoveries
remain 2/2, the same initial 1/1 allocation is ready for reload/passive acquisition,
and the reporter exception is closed. No new repair budget, implementation,
policy change, test run, generation or live call is part of this checkpoint.

### Active Passive Subset

This subsection defines the active scope and takes precedence over deferred guards.
Implement only `.github/plugins/cg-native-evidence.js` and small pure helpers
under `.github/plugin-support/cg-native-evidence/`, each under 300 lines;
identity/evidence Node tests plus a pytest driver; exact ownership/generation in
`scripts/cg_generate_targets.py`, `scripts/cg_validate_modules.py`, the module
registry and affected target tests; local SDK installation; and minimal native
`cg_native_identity`/`cg_native_evidence` permission keys for parent/stage.
Generate only exact Kilo plugin/helper counterparts and affected existing
ownership/shared-mapping outputs through the generator after canonical tests and
review. Keep all existing Task rules byte-equivalent and root depth 3 unchanged.

No Task-policy relaxation, dispatch hooks, generic tool guards, aliases, Git
execution, source configuration broadening or production-guard changes in this
subset. Plugin absence/failure adds no authority and does not enable the pipeline.
The admission gap remains unresolved. Tools may run from an ordinary implementation
primary: report actual agents, never force an expected `cg-autopilot` identity.
Observer targets must be independently joined native descendants of the actual
caller in the same worktree; old blocked children of another primary are not
owned merely because the project matches. No native runtime probes or loaded
claim until later supported reload. Original V1 remains unverified.

The final recovery also authorizes central test registration in
`scripts/cg_pr_preflight.py`, native-target CI changes in
`.github/workflows/tests.yml`, a minimal locked test-only SDK fixture under
`scripts/tests/native-sdk/`, and scoped LF rules in `.gitattributes`. No runtime
package is tracked and no global Node setting changes. Native CI uses Node 24.x
and requires actual SDK cases to execute; local optional SDK absence is a visible
pytest skip, while incomplete or mandatory installations fail. The SDK 7.6.2 pin
is a reproducible test fixture only, not a runtime version allowlist or upper bound.

**Distribution boundary:** this capability is worktree-local and available through
manifest generation only. Legacy `installUnits` omit the plugin resources and
are explicitly unsupported for this capability until separate Phase 5 distribution
work. This recovery neither expands legacy linking nor claims consumer support.

`childID` selects the returned path, not the entire query scope. Observation scans
the whole bounded caller Task subtree, including siblings, plus required ancestor
histories. Incomplete sibling evidence can block even a known valid target.

## Context

The authoritative plan remains `.cg-docs/plans/2026-09-11-kilo-first-autopilot.md` (hereafter Original).
Its only body correction is the explicit cross-reference after Step 3, limited
to runtime acquisition and the plugin exclusion. All other Original requirements
remain. The pipeline stays in Phase 1, with no completed phases and V1 unverified.
Original Steps 1, 2 and 3 each retain **2/2 exhausted** recovery attempts.
Diagnostics and product budgets are not alternative funding for this revision.

The linked work report's earlier native checkpoint records R1-R7 review corrections fixed,
Pester 2921 passed / 0 failed / 2 skipped, and no cleanup errors. This is historical
evidence, not a new run or native-graph proof. Supported reload loaded the stage
and exposed read/glob/grep/task. Native children `ses_f6c9ad868ffe5aQEk1ZL84b9xN`
and `ses_f695b19d7ffe1L1kBU5wyZCbXp` stopped `native-identity-unverified`.

Kilo 7.6.2 internally has `ctx.agent` and `ctx.sessionID`; Task creates a child
with `parentID` and `agent`. These are not supplied as caller/current-session
identity in the child model's standard system context. The parent wrapper gives
the immediate child ID/state, not the nested graph. Selecting an agent in the UI
mid-turn takes effect on the next new user submission. That selection issue is
separate from the identity gap; another identical probe is not a remedy.

Charter alignment: explicit failure and evidence before claims. The local Brain index predates this diagnosis.
Its journey-testing lesson requires usable paths between prompts, not individually correct but incompatible guards.
No open-brain tool is available here; local Brain and the current work report supply context.
No Brain write, live runtime probe, endpoint scan or secret inspection occurred
in this revision's initial interface investigation.
Public source inspection is not installed-runtime qualification.

## Requirements

IDs below are local to this revision; Original requirement IDs remain unchanged.

| ID | Requirement | Source |
|---|---|---|
| R1 | Prove a trusted, supported metadata acquisition path before any guard change | Original R2/R5/R17, Step 3; stage contract Read-Only Bootstrap |
| R2 | Separate native enforcement, observer evidence and prompt correlation; do not treat passive acquisition as an authentication waiver | Original R4/R7; stage contract Authority And Support |
| R3 | Prove every claimed edge, mode, effective restriction, depth, settlement, worktree, host OS and execution location; unknowns block | Original R2/R14/R17, V1; stage contract qualification rules |
| R4 | Limit revisions, schema changes and recovery attempts; preserve all other boundaries | Original R1/R9/R13/R15/R16; current user authorization |

## Evidence Research

Public tag `v7.6.2` resolves to commit `3d04228b6a642acb3daf68a649269618b6018250`.
This is version-matched source evidence, not evidence of a reachable endpoint in this extension. Source links are at the end.

| Surface | Actual source/wire contract | Limit of the claim |
|---|---|---|
| Native Task | `ctx.metadata` stores `parentSessionId`, `sessionId`, model and optional background; wrapper is `<task id="..." state="...">` | Only the actual tool boundary proves its immediate result; embedded model text can imitate this markup |
| `GET /session/{sessionID}` | `Session.Info`: `id`, optional `parentID`, `agent`, `permission`, `directory`, `projectID`, optional `workspaceID`, `version`, `time` | Session state is mutable; `version` alone is not active-server identity; no branch/HEAD or complete effective policy attestation |
| `GET /session/{sessionID}/message` | Array of `{info, parts}`; positive `limit`, optional `before`; pagination uses `X-Next-Cursor` and `Link` | Omitted/zero limit reads all messages; never use it. Messages can include sensitive text, not just metadata |
| `GET /session/{sessionID}/message/{messageID}` and `/children` | One message with parts, or child `Session.Info` array | A child list alone does not prove Task dispatch; source also exposes create/fork/import and part-update facilities |
| `GET /agent`, `/path`, `/vcs` | Agent definitions, instance paths, current VCS information | Current mode/policy is not historical turn policy; these do not replace dispatch-time evidence or leaf command results |
| Native permissions | Task checks depth, requests target permission, rejects primary-mode children and derives child restrictions | Broad caller-agent `bash` denies are deliberately not inherited; a read-only stage does not prove a read-only general leaf |

These routes enter the public OpenAPI surface, although group comments call the HttpApi implementation experimental.
Their presence supports a candidate, not a stable evidence SLA. Basic server authentication is conditional;
it is not a read-only observer role. Authenticated APIs can also mutate session/part data.
A GET-only client is a client restriction, not server-side least privilege.
The newly approved local plugin may use its runtime-supplied SDK client, not a
new server, CLI session, Agent Manager route or session-creation API. No deployed
listener or file credential path is assumed. SDK package and plugin installation
approval is worktree-local only; it does not authorize loading unreviewed hooks.

## Threat Boundary

**Retained:** native target/mode/depth and tool restrictions where actually
enforced; exact fresh foreground dispatch owned by the primary; same-worktree
checks; bounded independent read-back; user decisions; all production stops.
The installed runtime, its state store and the approved observer transport are
trusted components. Prompt bodies, files, reports and child summaries are data.

**No caller-authentication loss is approved.** The plugin must join the current
tool context to its exact current assistant message and independently join each
child to its native parent Task part before bootstrap activity. The earlier
permission-plus-observation alternate is not adopted. Hashes, IDs, approval
references and request correlation are not credentials.

Native Task permissions restrict a caller's targets, not which callers can reach
the stage. Instruction-level read-only rules alone are insufficient. Every leaf
must have enforced mutation denial and an exact allowed command/read surface
before dispatch. Broad shell, network, MCP or indirect
delegation access fails that gate, even if a leaf promises to use only Git reads.
Human probe approval does not supply missing technical enforcement.

This design cannot attest against a privileged repository/runtime writer, an API credential holder that can alter
records, or an administrator. It does not provide exclusive writer isolation, process termination guarantees or
cryptographic agent identity. Observer compromise and concurrent configuration changes invalidate proof.
It is not sufficient authority for mutating production stages or parent-only control writes;
those remain disabled and require their original independent gates.

## Implementation Steps

These steps form the approved `NATIVE-EVIDENCE-REVISION-01`, not new pipeline
phases or a renewal of Original Steps 1/2/3.

### 1. Verify the Interface and Enforcement Boundary

- **Requirements**: R1, R2, R3, R4
- **Files**: this revision, Original's bounded cross-reference, linked report and ordinary active-state pointer.
- **Details**: verify the public SDK request seam, exact dispatch-message joins, plugin-load failure behavior and subtree-only enforcement before relaxing native policies. Source v7.6.2 is research provenance, not a runtime allowlist.
- **Tests**: inspect actual source contracts first; any subsequent transport test must use a real SDK-generated Request with factory binding, not a handcrafted status-only client.
- **Acceptance criteria**: identify a supported hard guard, or return the precise technical decision before a large hook layer. No prompt-only fallback, restricted-agent alias or unconfirmed policy API may silently substitute.

### 2. Implement, Validate and Stage the Local Plugin

- **Requirements**: R1, R2, R3, R4
- **Files**: the exact passive inventory below; hard admission remains deferred, not a passive-construction prerequisite.
- **Details**: add failing identity/evidence and transport tests first. Implement self-only identity and descendant-only independent observation, without execution hooks. Keep production disabled. Review canonical code and tests before generation into the autoload directory.
- **Tests**: focused Node tests using the existing Node test runner, focused pytest/module/target/drift checks, and Pester only through the primary-dispatched verified `general` execution leaf.
- **Acceptance criteria**: passing offline checks and reviewed generated inventory permit supported reload later; they do not prove loaded tools or Original V1. No Phase 2 until complete actual native qualification.

### Approved Change Inventory

| Area | Exact bounded inventory | Limits |
|---|---|---|
| Plugin | `.github/plugins/cg-native-evidence.js`; `.github/plugin-support/cg-native-evidence/{wire,transport,records,evidence}.mjs` | Each file under 300 lines; four helpers outside autoload root; one passive plugin, no hooks or identity framework |
| Ownership/generation | `.github/shared/module-registry.json`, `.github/shared/target-mapping.json`, `scripts/cg_generate_targets.py`, `scripts/cg_validate_modules.py` | Exact five-resource ownership by `suite-cg`; only Kilo emits `.kilo/plugins/cg-native-evidence.js` and the four exact `.kilo/plugin-support/cg-native-evidence/*.mjs` counterparts; no broad copy glob or other-worktree installation |
| Bootstrap | No canonical prompt, agent-body or contract-body edit in the passive subset | All existing bootstrap and production guards stay in force; no Git execution or Task substitution |
| Policies | Only parent/stage entries in `.github/shared/target-mapping.json` | Add `cg_native_identity: ask` and `cg_native_evidence: ask`; every Task map stays byte-equivalent; no other permission, `general` replacement or alias |
| Tests | `scripts/tests/cg-native-{evidence,transport,records,sdk}.test.mjs`, `native-evidence-fixture.mjs`, `test_native_evidence.py`, exact assertions in `test_target_kilo.py` | Existing Node runner and pytest only; actual installed SDK uses fake factory transports; no native probes |
| CI/LF | `scripts/cg_pr_preflight.py`, `.github/workflows/tests.yml`, `scripts/tests/native-sdk/{package,package-lock}.json`, `.gitattributes` | Register only touched tests centrally; SDK-only locked fixture with standard TLS/integrity and scripts disabled; Node 24.x CI; no legacy installUnits changes or Git renormalization |
| Dependency | Worktree-local `.kilo/package.json`, lockfile and `node_modules` for `@kilocode/plugin` and its SDK dependency | Supported npm Arborist installation with scripts disabled; no global settings, credentials or other worktrees; never load hooks before validation/review |
| Generated assets | Five Kilo code resources, two Kilo agent permission headers, shared target-mapping copies and affected ownership manifests | Existing generator only, no hand edits; unsupported adapter gates preserved; root `kilo.json` depth 3 and generated `.kilo/kilo.json` unchanged |
| Accounting | This plan, Original's Step 3 cross-reference, `.cg-docs/work-reports/2026-09-11-kilo-first-autopilot.md`, `.cg-docs/active-state/current.json` | Record scoped approval and separate counters; preserve roadmap, brainstorm and report history; no schema migration |

### Required Tool Contract

`cg_native_identity` has zero arguments and always requests native permission
through `context.ask({permission: 'cg_native_identity', patterns: ['self'],
always: [], metadata: {}})`. Visibility is not permission. Match
`context.sessionID/messageID/agent` to the exact current assistant record.
The public tool context has no guaranteed `callID`.

`cg_native_evidence` accepts a child ID only after an independently native-joined
descendant operation of that caller permits it. Join child `parentID` to the
exact parent Task part's `state.metadata.parentSessionId/sessionId`, its
`subagent_type`, assistant agent, `callID`, part ID and message ID. Do not use a
mutable selected parent agent, prompt wrappers, caller-supplied parent IDs,
recency or same-project membership as authority.

Use only supplied SDK `session.get`, `session.message` and positively bounded
`session.messages` reads. Preserve the internally authenticated factory fetch,
including in-process `app.fetch`; a per-request guard must bound success AND
error bodies before SDK buffering. Do not access private SDK internals, replace
the transport with global fetch, fetch config/credentials, follow redirects,
accept arbitrary URLs, enumerate sessions, export transcripts or call model,
session-creation, server/admin or permission-override APIs. Unavailable binding
is a capability rejection. Do not log headers or credential-bearing URLs.

Bounds per observation: 50 messages per page, 20 pages total, 5 sessions,
4 distinct inspected edges across the acquisition, depth 3, 8 MiB per response,
32 MiB aggregate and 100000 parse nodes (keys and values, charged before allocation).
The 51st root message item is rejected before parsing it. Native JSON is parsed
once; SDK stream mode receives only an empty acknowledgement. These byte/node
controls are not an exact heap-memory guarantee.

The cooperative 30-second acquisition deadline starts AFTER `context.ask`
permission waiting. It stops waiting and requests cancellation; it cannot force
an uncooperative operation to terminate or preempt synchronous parsing. Parsing
checks the deadline periodically, and late responses receive best-effort body
cancellation. Capped acquisition is incomplete, not evidence of absence.
Return only normalized safe IDs, agents, states, times and provenance hashes:
4096 bytes for identity/receipts and 8192 for qualification; retain primary caps.

### Deferred Guard Contract

This section is future policy-relaxation work, excluded from the active passive
subset. It remains a prerequisite for full bootstrap qualification, not for
building or testing passive acquisition under unchanged policies.

Exact graph: `cg-autopilot -> cg-workflow-stage`; stage to `cg-code-quality`,
`general` or `cg-fix-problems`; fix to `general`; leaves never delegate.
All Tasks are fresh and foreground. Before Task execution, join the hook's
actual `callID` to the exact dispatch message and ancestor provenance. Reject
explicit-subtask and mention-based permission bypass routes. Never emulate Task.

Bootstrap subtree guards must reject edits, network/MCP and arbitrary shell,
while ordinary code/review/fix sessions retain native behavior. Missing plugin,
missing metadata and registration races cannot enable bootstrap or cause a global
tool denial. An event cache alone must not be described as durable admission.

If implementation becomes feasible, replace the four bootstrap shell Git calls
with one controlled plugin Git-read operation: fixed verified argv/environment,
optional locks disabled, fsmonitor/untracked cache/preload index disabled, no
arbitrary commands, and rejection of submodules/unsafe configuration paths.
This bootstrap-only Git correction must be explicit in the contract and tests;
it is not implemented or qualified now. Do not silently drop leaf execution
proof. Native Read can start LSP/load instructions; its permission string and
byte bounds alone do not provide a hard read-only guarantee.

### Technical Stop: Plugin Presence Is Not a Native Admission Condition

Source investigation on 2026-09-13 found a concrete failure path:

1. `packages/opencode/src/plugin/index.ts` catches an external plugin's
   `applyPlugin` failure and continues with `Effect.void`; the failed plugin has
   no registered tools/hooks. Its `config` hook failures are also ignored.
2. Native Task selection uses static agent/session permission rules. No inspected
   public PluginInput, hook or Task option makes the non-denying Task baseline
   conditional on successful guard installation. A prompt instruction to call
   identity first is not that native prerequisite.
3. `KiloTask.inherited()` explicitly does not inherit broad parent-agent bash
   denials. Thus relaxed Task policies plus a failed/missing plugin do not create
   an enforced read-only `general` leaf. Its ordinary policy remains available.
4. The public before-tool hook has only tool/session/call IDs, not current agent,
   message or ancestry. The processor explicitly buffers metadata before tool
   registration, so a persisted exact-call join cannot be assumed at every hook.
   Reject missing joins; do not infer them from the most recent message.

Synchronous work in `session.created` callbacks can record fresh known children
before creation returns in this source. This is not an awaited async admission
hook: the plugin dispatcher discards callback promises, and the cache is absent
after failed initialization or reload. It cannot supply the missing native
plugin-presence condition. Letting unknown calls run can permit an unclassified
bootstrap leaf; denying all unknown calls can block unrelated ordinary sessions.

The public SDK `requestValidator` receives merged request options in this source,
including the factory fetch. The passive implementation preserves that fetch;
the protected `_client` is not a supported config accessor. No claim is made that
transport preservation is impossible. The blocking decision is future enforcement,
not passive construction. Actual released SDK offline integration now covers
Request construction, factory authentication, success/error bounds and in-process
transport. This is not proof of loaded tools, live binding or native qualification.

Required technical resolution: a confirmed runtime-owned fail-closed admission
condition that binds Task/current-message identity and bootstrap restrictions
before child activity, including plugin-load failure. A new native policy API or
restricted profiles would be a different scoped design and need explicit review
and approval. This revision does not authorize either silently. Preserve existing
policies until that condition exists; do not treat a reload as its substitute.

#### Source-Only Candidate Update 2026-09-14

Diagnosis leaf `ses_f6025160bffeoriMtrvXDJXGVg` found that public types/source
allow the Plugin `config` callback to mutate cached `cfg.agent` before
`Agent.list`, although documentation describes the callback as read-only.
Exceptions from `tool.execute.before` propagate. These are source observations,
not live enforcement evidence. They identify a possible conditional-policy
installation candidate, not an implemented or approved guaranteed mechanism.

Missing-plugin behavior, explicit-subtask bypass, command pre-expansion and
existing-child continuation still prevent a universal admission guarantee.
The dated findings above remain history; they must not be read as a claim that
no relevant interface exists anywhere. No source/policy change, new budget or
closure of the read-only admission gap follows from this candidate.

## Testing Strategy

This matrix defines required live proof, not completed tests. Initial test
results and the interface stop are recorded in the linked report. The requested
red/green passive suite is implemented; the work report separates source tests,
released-SDK offline integration, runtime dependency installation and native proof.

| Claim | Actual native evidence required | Static evidence cannot establish |
|---|---|---|
| Primary -> stage | Real wrapper child ID; parent assistant message/Task part (`id`, `callID`, `sessionID`, `tool`, state); runtime metadata `parentSessionId/sessionId`; matching child `parentID`; dispatch-turn agent | A claimed primary name, current UI selection or wrapper copied into text |
| Stage -> reviewer/general; stage -> fix -> general | Independently GET each caller's Task part and child session; join runtime metadata to `parentID`, exact target input and executing message agent; fresh IDs, complete child inventory | Stage receipt IDs, nested XML/text, child list alone or fixture graph |
| Modes and permissions | Dispatch-time agent definitions/modes, ordered policy sources and session restrictions, native tool exposure and exact allowed/denied target behavior; include each leaf's shell/network limits | `/agent` now or `Session.permission` alone; one allowed edge is not a full effective target map |
| Depth and negative cases | Complete ancestry plus separate approved depth 1 rejection, depth 2 direct success/conditional rejection, depth 3 conditional success; valid target denied by policy | Unknown-agent error, parent-depth claim or configuration value alone |
| Settlement and sequence | Runtime terminal Task states/times for every edge; no pending/running/promoted work, missing descendants or later activity; sibling Task intervals do not overlap; descendant intervals are contained within ancestor Task intervals; each child settles before the next sibling starts and before its ancestor returns | Parent wrapper completion alone, a child's `settled:true`, idle session or clean Git |
| Worktree/branch/HEAD | Session directory/project/workspace joined to approved canonical root; actual leaf Git tool calls/results and independent before/after observation | Directory name alone, Git text in a receipt or protection against external concurrent writers |
| Qualified deployment | Host OS and local-versus-remote execution location for observer, server and every leaf, with identified acquisition sources; support limited to the qualified deployment, all others unsupported | Observer OS alone, assumed co-location or general support inferred from one deployment |
| Freshness and defaults | Exact installed asset/policy source hashes and observation interval; unchanged sources on recheck; native defaults preserved | Hidden model identity, alias equivalence, persistent qualification after runtime/config changes |

Read each field from its identified runtime message/part/session, not from a model's result body.
Preserve acquisition method, runtime version, observer binding, host OS and local-versus-remote execution location for observer/server/leaves, request/response time, record IDs, byte count/hash and field path; do not invent unavailable native fields.
Metadata is runtime-origin only within the stated trusted-runtime boundary. Missing/compacted/deleted records,
fork/import ambiguity, API mutation, partial pagination or changed sources block. Branch/HEAD remains observational, not a lock.

### Schema Scope

Bootstrap-only schema/contract revision is approved if needed by the implemented
tools. Do not invent closed fields before the interface is verified. Add bounded
observer provenance and explicit evidence-source classification; do not insert
`child-caller-authentication: unavailable` as an accepted bypass. Child
observations remain claims until independently joined. No v1 record is rewritten
or upgraded to a pass. Reject mixed versions for qualification; retain v1 history.
Keep production result/envelope, active-state and future cursor schemas unchanged.
No automatic migration or completion update. Final closed fields require review
against actual acquired wire data, not invented native metadata.

## Documentation Checklist

- [x] Historical planning architecture, adversarial and plan-critic reviews completed; both P2 memo corrections independently verified on 2026-09-12 by `ses_f68fdeaebffeQVOHQalb1eHlnY` per user-supplied evidence; execution was not approved at that time.
- [x] Explicit local-plugin approval, exact inventory and unchanged guarantees recorded on 2026-09-13.
- [x] Bounded Original cross-reference and separate initial/recovery ledger recorded without rewriting history.
- [x] New source-verified enforcement stop recorded before policy relaxation or autoload generation.
- [x] Passive red/green tests and same-writer architecture/adversarial review completed; recovery 1 fixed three tested boundary defects.
- [x] Runtime dependency installation resolved by the separately identified leaf using strict TLS and scripts disabled; actual installed SDK tests passed 77 before this patch.
- [x] Node 24.21.0 offline validation completed through the isolated reporter exception; default Node 22.16.0 and global settings are unchanged.
- [ ] Runtime Bun qualification, supported Config/Skills reload and passive live reads completed; no loaded-tool or native success is claimed.
- [ ] Complete actual native qualification recorded; Original V1 is still unverified.
- [x] Document schema validation and whitespace check passed; no HTML rendered.
- [x] Final recovery code generated through the existing generator; focused checks including drift/LF passed (261 pytest passed, 1 existing skip; 125 Node passed against the actual ignored installed SDK, external fixture path unset).
- [x] Supplied pre-patch primary-leaf Pester evidence recorded: full 2921 passed, zero failed, two skipped, filteredFiles null; this does not validate the final patch.
- [x] Final-recovery full Pester completed in leaf `ses_f6352f212ffeU8843kxm0BUoHT`: total 2923, passed 2921, failed 0, skipped 2, filteredFiles null, 2026-09-13T21:33:04Z; this precedes the reporter-only exception and was not rerun for it.
- [x] Final independent verifiers closed FR-01 through FR-14; `cg-testing` session `ses_f64b4a42dffewjzRkmWVjJGqK0` confirmed FR-12's explicit TAP flag and unchanged guards.
- [x] `CI-REPORTER-01` closed 1/1: focused pytest 9 passed and Node 125 passed on actual Node 24.21.0 with mandatory installed SDK and external fixture path unset.

## Risks & Mitigations

| Risk | Required mitigation |
|---|---|
| Observer reads another server or forged/replayed session | Supported extension-to-server/session binding plus dispatch/child joins; missing binding blocks |
| Permission-looking read-only probe reaches writable leaf | Verify effective restrictions before dispatch; prompts/human approval are not enforcement |
| Sensitive messages or API credentials reach model context | Bounded GET-only projection, secret-safe transport, no raw logs/config; no safe path means stop |
| Bootstrap evidence silently authorizes production | Separate approval gates; retain production stops and Original V1/V6 truth conditions |
| Scope grows into an identity service | One bounded observer candidate at most; material dependency requires explicit approval or reject |

## Out of Scope

No new sessions/models from the plugin, credentials, global/user settings,
other-worktree changes, native-denial override, unapproved profiles, large hook
framework, live endpoint scans, commits, pushes, PRs, merges or releases.
No Phase 2 or later implementation. Approved inventory is not authority to
continue through the technical stop or to load unreviewed plugin code.
Keep Kilo-only support, minimum 7.4.20 and capability checks with no upper bound or exact-version allowlist; 7.6.2 is research provenance only. Only the qualified deployment is supported.
Preserve containment, local projection, trust checks, user-controlled models, protected assets, Pester rules and standalone behavior.
Keep the six-phase pipeline and existing five-minute wait policy unchanged;
no wait runs here and neither waiting nor reload renews budgets.

## Completion Contract

### Outcome

A reviewed, explicitly authorized revision either proves bounded native
observation and truthful bootstrap qualification, or records a precise technical
stop. Approval itself establishes neither runtime support nor completion.

### Verification Surface

| ID | Evidence Required | Command/Artifact | Required |
|---|---|---|---|
| V1 | Document shape and whitespace only; not Original V1 | `python -B scripts/render_artifact.py --validate-only .cg-docs/plans/2026-09-12-autopilot-native-evidence-revision.md`; document diff check | yes |
| V2 | Exact implementation approval, interface decision and implementation reviews | This revision and linked report; later scoped review artifacts | yes |
| V3 | Trusted acquisition and every claimed native row above, or explicit rejection with Original V1 still unverified | Future bounded work-report evidence; no fixture substitution | yes |

### Constraints

| ID | Constraint | Check |
|---|---|---|
| C1 | Only the approved inventory may change; technical stop precedes unsafe policy changes | Path/whitespace inspection; all other pre-existing work preserved |
| C2 | No weakened production, platform, config, model, timing or protected-asset boundary | Independent scope review and future exact change inventory |
| C3 | Original Step 1/2/3 attempts remain 2/2 each | Historical report preserved; separate named unit ledger |

### Boundaries

- Completed: approved passive implementation, generation, final independent review, final-recovery Pester and the separately approved reporter exception. Revision repair budgets are exhausted; this turn is checkpoint-only.
- Next: supported Config/Skills reload after the turn, then the first passive native identity acquisition from the current normal implementation agent using actual new tool registration and native permissions.
- Deferred: native qualification, any conditional-policy candidate, fresh bootstrap dispatch and Phase 2. Reload is not native evidence or an admission waiver.
- Human native-UI evidence may support a separately approved manual diagnostic case with IDs, time and source views; screenshots/summaries alone cannot prove missing fields. It is user-dependent, not autonomous qualification, and never substitutes for Original V1 under this proposal.

### Iteration Policy

1. Approved work unit: `NATIVE-EVIDENCE-REVISION-01`. The same initial 1/1 allocation remains open. Recovery 1 passed. The final **2/2** recovery was explicitly approved and reserved before the FR-01 through FR-14 patch. There is no remaining repair budget and no automatic round after a failed gate. Original Steps 1/2/3 remain 2/2 each forever.
2. Reserve and record recovery use before work; failed, cancelled or uncertain attempts remain counted. A repeated probe after failure is an attempt, not a free diagnostic. Approval-only pauses consume no recovery attempt when no execution occurred.
3. No automatic renewal, refund, rollover, new alias unit, or borrowing diagnostics/product budgets. Exhaustion or scope change stops for a new explicit decision. `strict` forbids silent deviations.
4. This turn's Local Plugin approval supersedes the old separate planning-only Gate A/Gate B wording. It does not waive implementation review, supported reload, scoped native probes or the technical stop. Passing checks never resets Original budgets or advances its phase automatically. Initial red tests are not recovery attempts.
5. The user separately approved the exact reporter-only exception `CI-REPORTER-01`; it is 1/1 used, verified and closed. It does not renew revision recoveries, Original attempts, diagnostics or product budgets. No additional corrective work is authorized by this checkpoint.

### Blocked-Stop Conditions

- Unavailable supported observer binding/access, unsafe secrets, incomplete graph/policy/settlement evidence or unapproved dependency.
- Native read-only enforcement cannot be established for every participant before dispatch.
- Missing approval, exhausted unit cap, unsupported schema, unsafe acquisition or contradictory native records.
- Any claimed success would require child self-report, static fixtures, a human exception as autonomous proof, production guard removal or an old-budget reset.

## Approval And History

Current approval, 2026-09-13T13:40:05Z: **Approve Local Plugin**, worktree-local
implementation and corresponding bounded plan revision, including the exact
inventory above and `NATIVE-EVIDENCE-REVISION-01` budget. No additional general
plugin-approval request is needed. The technical stop is a new finding, not an
attempt to enforce superseded memo fields.

Historical planning reviewer outcomes, supplied by the user on 2026-09-12; both P2 memo corrections independently verified fixed, with no structural contradictions or new findings at that time:
- Plan critic `ses_f68fdeaebffeQVOHQalb1eHlnY`: verified timing at line 186 and host/location at lines 119/188/192, including minimum-version policy at line 228; both P2 corrections fixed.
- Architecture `ses_f68fde905ffeR5h45LJs15Fm6z`: P2 host OS/execution-location omission corrected in acquisition, qualification and provenance.
- Adversarial `ses_f68fde8abffeNax57dIBrDpv8O`: no P0-P2 findings; Git side-effect caveat retained as an explicit missing enforcement prerequisite.
Those reviews concerned a non-executing observer proposal, not this implementation
inventory. Their former no-execution/no-budget disposition is superseded by the
2026-09-13 approval. They are not implementation reviews or native V1 evidence.
Human UI summaries, prompt assertions and fixtures still cannot replace actual
native qualification.

## Sources

- Original: `.cg-docs/plans/2026-09-11-kilo-first-autopilot.md`, R2/R4/R5/R7/R14/R17, fixed authority decision, Steps 1/3/7/16 and V1.
- Current contract: `.github/shared/autopilot-stage.contract.md`, Authority And Support, Read-Only Bootstrap, Bootstrap Packet Shapes and disabled Production Entry.
- History: `.cg-docs/work-reports/2026-09-11-kilo-first-autopilot.md`, final native checkpoint (lines 390-448); Brain lesson `.cg-docs/solutions/testing-patterns/2026-05-06-cross-prompt-user-journey-must-be-validated-end-to-end.md`.
- [Kilo v7.6.2 tag binding](https://api.github.com/repos/Kilo-Org/kilocode/git/ref/tags/v7.6.2); all source paths below use commit `3d04228b6a642acb3daf68a649269618b6018250`.
- [Task source](https://github.com/Kilo-Org/kilocode/blob/3d04228b6a642acb3daf68a649269618b6018250/packages/opencode/src/tool/task.ts), `TaskTool.execute`, metadata, `ops.prompt`, `renderOutput`; [permission inheritance](https://github.com/Kilo-Org/kilocode/blob/3d04228b6a642acb3daf68a649269618b6018250/packages/opencode/src/kilocode/tool/task.ts), `KiloTask.inherited`.
- [Session schema/service](https://github.com/Kilo-Org/kilocode/blob/3d04228b6a642acb3daf68a649269618b6018250/packages/opencode/src/session/session.ts), `Info`, `fromRow`, `create`, `children`; [message persistence/read projection](https://github.com/Kilo-Org/kilocode/blob/3d04228b6a642acb3daf68a649269618b6018250/packages/opencode/src/session/message-v2.ts), `page`, `get`, `stripPartMetadata`.
- [HTTP session routes](https://github.com/Kilo-Org/kilocode/blob/3d04228b6a642acb3daf68a649269618b6018250/packages/opencode/src/server/routes/instance/httpapi/groups/session.ts), `SessionPaths`; [handlers](https://github.com/Kilo-Org/kilocode/blob/3d04228b6a642acb3daf68a649269618b6018250/packages/opencode/src/server/routes/instance/httpapi/handlers/session.ts), `messages`, `updatePart`; [public API](https://github.com/Kilo-Org/kilocode/blob/3d04228b6a642acb3daf68a649269618b6018250/packages/opencode/src/server/routes/instance/httpapi/public.ts), `PublicApi`.
- [Instance read routes](https://github.com/Kilo-Org/kilocode/blob/3d04228b6a642acb3daf68a649269618b6018250/packages/opencode/src/server/routes/instance/httpapi/groups/instance.ts); [server auth](https://github.com/Kilo-Org/kilocode/blob/3d04228b6a642acb3daf68a649269618b6018250/packages/opencode/src/server/auth.ts); [authorization middleware](https://github.com/Kilo-Org/kilocode/blob/3d04228b6a642acb3daf68a649269618b6018250/packages/opencode/src/server/routes/instance/httpapi/middleware/authorization.ts).
- [Plugin input/hooks](https://github.com/Kilo-Org/kilocode/blob/3d04228b6a642acb3daf68a649269618b6018250/packages/plugin/src/index.ts); [plugin loading, ignored failures and event dispatch](https://github.com/Kilo-Org/kilocode/blob/3d04228b6a642acb3daf68a649269618b6018250/packages/opencode/src/plugin/index.ts), `applyPlugin`, `Plugin.state`, `trigger`.
- [Tool context](https://github.com/Kilo-Org/kilocode/blob/3d04228b6a642acb3daf68a649269618b6018250/packages/plugin/src/tool.ts); [model-issued before-tool hook](https://github.com/Kilo-Org/kilocode/blob/3d04228b6a642acb3daf68a649269618b6018250/packages/opencode/src/session/tools.ts), `context`, `resolve`; [processor registration/buffering](https://github.com/Kilo-Org/kilocode/blob/3d04228b6a642acb3daf68a649269618b6018250/packages/opencode/src/session/processor.ts), `metadata`, `ensureToolCall`, `handleEvent`.
- [Explicit-subtask/mention paths](https://github.com/Kilo-Org/kilocode/blob/3d04228b6a642acb3daf68a649269618b6018250/packages/opencode/src/session/prompt.ts), `handleSubtask`, `prepare`, `bypassAgentCheck`; [synchronous event notification](https://github.com/Kilo-Org/kilocode/blob/3d04228b6a642acb3daf68a649269618b6018250/packages/core/src/event.ts), `notify`, `observe`.
- [Public SDK request implementation](https://github.com/Kilo-Org/kilocode/blob/3d04228b6a642acb3daf68a649269618b6018250/packages/sdk/js/src/gen/client/client.gen.ts), `beforeRequest`, `request`; [SDK facade](https://github.com/Kilo-Org/kilocode/blob/3d04228b6a642acb3daf68a649269618b6018250/packages/sdk/js/src/gen/sdk.gen.ts), `_HeyApiClient`, `Session`; [factory binding](https://github.com/Kilo-Org/kilocode/blob/3d04228b6a642acb3daf68a649269618b6018250/packages/sdk/js/src/client.ts), `createKiloClient`.
