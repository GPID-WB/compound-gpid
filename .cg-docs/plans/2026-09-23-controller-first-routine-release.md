---
date: 2026-09-23
title: "Controller-first routine release with four-part prereleases"
status: blocked
execution-report: ".cg-docs/work-reports/2026-09-23-controller-first-routine-release.md"
current-phase: 1
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-09-23-controller-first-routine-release.md"
language: "both"
estimated-effort: "large"
deviation-policy: "ask"
artifact-schema-version: 1
phases: 5
tags: [release, controller, prerelease, github-actions, ci-cd, cutover, recovery]
---

# Plan: Controller-First Routine Release With Four-Part Prereleases

Superseded on 2026-09-24 by
`.cg-docs/plans/2026-09-24-legacy-first-routine-prerelease.md`. Phase 1
stopped before implementation. Keep its blocked work report as the record of
the rejected exclusive-gateway design, not an instruction to resume cutover.

## Objective

Make bare `/cg-release <tag>` the ONE supported GPID routine release request:
official `vX.Y.Z` only from the verified remote default or configured deployment
branches, and `vX.Y.Z.<build>` prereleases from verified same-repository remote
branches including `dev`. Use the existing asynchronous controller and GitHub
Actions. Prereleases proceed from reviewed exact-source CI to publication without
an extra human publication approval; official releases keep independent approval
and protected Pages deployment. Preserve exact version, source, tag, Release,
artifact and attestation identities and require an enforceable shared cutover
fence. No source work, GitHub setting change, activation or live release is
authorized by approval of this plan alone.

## Context

PR #179 is merged at `48001ab4`. Current `.kilo/commands/cg-release.md:25-49`
dispatches only explicit `plan/start/status/resume` to the controller; legacy
Bridge/Recovery cannot serve routine requests. `packages/cg-release/src/cg_release/
versions.py`, `cli.py` and `models.py` reject four-part versions; `history.py`
does not adopt unrecognized managed refs. `policy.py:200-221` restricts every
source branch to a declared release line, whereas the desired prerelease branch
policy permits any verified branch. The installed `.release-controller.json`
has `enabled: false`, null trust identities, only `main` in its release line,
and no bridge record. It declares `.release-version.json` and a `CHANGELOG.md`
insertion marker, but neither input exists. The install generator repeats these
declarations. The GPID docs profile additionally needs a reviewed stable
snapshot baseline for the first controller prerelease.

Controller `publication_control.py` and its journal CAS protect controller
publishers, not the existing legacy PowerShell writer or a policy change. The
legacy script can push a tag and POST a Release after a read-only cutover check.
Its credential path and the proposed controller publishing App use different
tag-authority models. A journal claim only fences participating writers; it
cannot revoke a previously issued tag or Release token. Repository/App/ruleset
capability and all other writers must be inventoried before this design is
implemented or activated. In particular, tag protection is not proof that
GitHub Release API writes can be restricted to one App. If the shared gateway
cannot be made exclusive for the defined trusted principals, STOP; do not
substitute another authority read or a workflow concurrency group.

Prior work is context, not completed evidence for this plan:
`.cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md` and
`.cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md` remain active
with their own histories. The latter's commit/tree/LF receipt can avoid repeated
native preflight for unchanged inputs but is not remote release authority.
`D-2026-09-13-defer-live-rollout` leaves bridge, clean-client, release-mode CI,
remote controls and timing unproved. Do not claim old V12/V13 live gates passed.
The charter requires explicit failures, reviewed branches, and protected output.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | One explicit GPID bare-tag command routes to the controller; generic `plan/start/status/resume` retain their contract; legacy Bridge/Recovery stay exceptional. | Confirmed brainstorm; `.kilo/commands/cg-release.md` |
| R2 | Four-part tags remain exact, first-class prerelease identities in input, state, policy, metadata, tags, payload, readers and attestation; stable and historical lanes are not silently remapped. | Confirmed brainstorm; `versions.py`, `scripts/release-version.js` |
| R3 | Official sources use only remote default/deployment branches, prerelease sources any verified same-repository remote branch; GPID has no stable override. | Confirmed brainstorm; `policy.py`, protected-default branch policy |
| R4 | A remotely atomic shared owner and enforced credential boundary serialize legacy writes, controller publication and cutover, including interrupted writes. | Confirmed brainstorm; `publication_control.py`, `create-release.ps1` |
| R5 | Reviewed exact commit, required CI, payload, annotated tag, Release, build artifact and final evidence are bound; prerelease auto-publishes without Pages or another human publication approval; official approval/Pages remain distinct. | Confirmed brainstorm; release controller integration contract |
| R6 | Existing help-evidence gate, second evidence PR, native preflight receipt and generated platform targets remain intact. | Confirmed brainstorm; `.github/workflows/tests.yml`, release integration contract |
| R7 | Setup is staged and disabled by default; separate real authority, activation and live-operation approvals precede remote changes; failure or unknown writes recover without destructive rollback. | Confirmed brainstorm; `docs/release-controller.md` |
| R8 | Negative and cross-platform tests and one separately approved live `v1.2.0.9020` acceptance capture honest timing and remote proof; no asserted V12/V13 pass before evidence. | Confirmed brainstorm; existing deferred gates |

## Dependency Graph

`Phase 1: audited contract and conditional gateway feasibility` ->
`Phase 2: atomic owner and version implementation` ->
`Phase 3: CI/CD provenance and command` ->
`Phase 4: local/PR and cross-platform checks` ->
`Phase 5: separately approved setup and cutover` ->
`final: separately approved live acceptance`.
Phase 1 must identify a concrete enforcement route before Phase 2 may implement
publication effects. The actual denied-write proof needs a separately authorized
non-public probe before activation; a read-only inventory does not prove denial.
Every intermediate phase keeps the shipped controller disabled. Remote proofs
cannot be inferred from fixtures, prior PRs, or the
completion of an earlier phase. If remote authorization is withheld, record
later phases as pending rather than marking the plan complete.

## Phase 1: Audit Contract And Prove The Fence Is Feasible

### 1. Inventory Writers And Verify Exclusive Authority

- **Requirements**: R4, R7
- **Files**: `create-release.ps1`, `scripts/release-legacy-authority.ps1`, `packages/cg-release/src/cg_release/{publication_control,publication_rules,github_journal,journal_transport,authority,publication_credentials,publish_worker,publisher}.py`, `.github/workflows/release-controller-publish.yml`, tag/Release workflow producers and disabled templates.
- **Details**: Draw a write-authority inventory for every Git tag, GitHub Release, asset, controller-state and effective-policy write, including humans, Actions default tokens, legacy GCM, Apps and administrative bypass. Distinguish Git ref protection from Release API permissions. Identify the smallest trusted gateway that alone receives effective write credentials, and a CAS mode/owner transition on the protected controller state branch. State the precise remote enforcement settings, issuer/revocation and permitted trusted administrators. The old script must not retain an independently usable write token during cutover. Bridge must be delivered before its creation authority is retired; route any later authorized historical Reserve through the gateway or disable that write while retaining read-only Finalize. A protected policy commit or workflow guard must not be able to become effective outside the same cutover protocol. Obtain read-only capability/protection evidence before committing to one implementation; do not change settings or try a denied write here. List exactly which proposed denials remain unproved until separately authorized sandbox trials in Phase 5.
- **Test Scenarios**: Concurrent legacy and controller claims; administrator/tag bypass or direct Release POST; policy merge during a legacy claim; expired credential with live process; repository feature unavailable.
- **Tests**: Focused read-only settings/principal inventory and a local modeled CAS race harness; record observed capabilities and unproved denial assumptions in the work report. A rejected POST or tag push is a write attempt and must not be run during this read-only phase.
- **Acceptance criteria**: A specific conditional gateway and activation route, with observed repository capabilities and an explicit list of pending denied-write probes, is documented. If read-only evidence already shows direct non-gateway writes or effective activation cannot be denied to the defined operating principals, stop and return for a revised plan. Local modeling is insufficient for activation.

### 2. Freeze The Version, Metadata And Source Contract

- **Requirements**: R1, R2, R3, R5, R6
- **Files**: `packages/cg-release/src/cg_release/{versions,models,history,policy,source,preview,metadata,profile_selection}.py`, `scripts/release_profile_install.py`, `scripts/release_profile_gpid.py`, `scripts/release_version.py`, `scripts/release-version.js`, `.release-controller.json`, current release readers, command sources and generated targets.
- **Details**: Specify strict ASCII `vX.Y.Z.<build>` numeric grammar (no leading zeroes except `0`, bounded length and integer ranges), exact serialized GPID kind/tag/version, stable/pre-release classification and collision rules. Keep strict SemVer for generic mode and existing historical readers. Do not synthesize a SemVer or PEP 440 version; where an adapter cannot represent four parts, reject it rather than silently project. Define how an explicit or uniquely inferred release line is chosen by numeric core for arbitrary verified same-repository prerelease branches, without changing stable source membership; ambiguous lines stop. Document how stable baseline/last published four-part history and latest stable selection interact without declaring a four-part tag a SemVer bump. Resolve actual metadata source path and changelog marker: add reviewed inputs under source implementation later, or choose already supported existing files; update the disabled installer generator and installed policy together. Locate the required prior stable snapshot/baseline and the exact reviewed adoption path, or stop live acceptance if missing. Choose one unambiguous bare-tag to controller request translation; no silent extra flags or implicit approval.
- **Test Scenarios**: Empty/malformed/overlong tag, leading zeroes, numeric overflow, occupied tag, dual-lane history, ambiguous lines, missing metadata/marker, source branch deletion/fork, absent stable baseline.
- **Tests**: Define fixtures for `packages/cg-release/tests/{test_versions,test_policy,test_history}.py`, `scripts/tests/{test_release_version_readers,test_release_controller_profile}.py`, `scripts/tests/release-version.test.js` and help catalog tests.
- **Acceptance criteria**: The written contract names every representation and available source input, cross-lane comparison, stable docs baseline and branch decision before coding; unknown or absent inputs remain explicit blockers.

## Phase 2: Implement Version And Shared Publication Ownership

### 3. Add First-Class GPID Version Handling

- **Requirements**: R1, R2, R3
- **Files**: `packages/cg-release/src/cg_release/{cli,versions,models,policy,preview,source,history,metadata,manifest,profile_selection,profile_build_verify}.py`, `scripts/release_profile_gpid.py`, `scripts/release_profile_install.py`, `.release-controller.json` (disabled values only), active Python/Node/PowerShell release readers and associated tests.
- **Details**: Implement the Phase 1 exact kind and unchanged tag across proposal, persisted record, replay, line, history, global collision and emitted metadata. Do not broadly change generic SemVer behavior. Keep existing four-part payload/tag readers and historical bytes; add comparison/property tests for latest stable and same-core numeric builds. In `profile_build_verify.py`, branch on the explicit GPID kind: classify a four-part release as prerelease without passing it to `parse_version`, and compare candidate versus selected stable only for official SemVer, while still validating capacity against the stable baseline. Resolve real metadata/changelog files and baseline through reviewed source changes, not placeholder values. Enforce stable source policy before preview and again before effects; GPID rejects `--allow-non-deployment-branch` and its reason, while unrelated generic behavior remains unchanged.
- **Test Scenarios**: `v1.2.0.9020` round trip; same-core `9019 < 9020 < v1.2.0`; stable from `dev` refused; four-part prerelease from verified feature branch accepted only with unique line; unrelated repo ref, invalid version, duplicate draft/tag/reservation rejected.
- **Tests**: Focused package tests above, GPID profile and Node/Python reader suites; exact round-trip fixtures for persisted request, manifest, payload and attestation, plus an approval-artifact test with `v1.2.0.9020` and a valid reviewed stable docs baseline. No network or secret-dependent default tests.
- **Acceptance criteria**: All first-class identities preserve original bytes, generic SemVer tests remain green, no historical tag is rewritten, and the disabled installation remains nonpublishing.

### 4. Extend The Journal Claim And Funnel Legacy Effects

- **Requirements**: R4, R7
- **Files**: `packages/cg-release/src/cg_release/{publication_control,publication_rules,journal_checkpoint,journal_transport,github_journal,publish_worker,publisher,recovery,authority}.py`, `create-release.ps1`, `scripts/release-legacy-authority.ps1`, controller/legacy GitHub Actions publishers and focused tests.
- **Details**: Use the existing state-branch `expectedHeadOid` CAS for one repository owner and mode (`legacy`, `cutover-pending`, `controller`, and scoped historical recovery), with a unique claim, generation/fencing identity and durable intent before every external effect. One gateway controls tag/Release/asset write credentials; local PowerShell never races with an independently valid publishing token after activation. While an owner is active, cutover waits; after cutover old Bridge cannot claim. Route permitted historical Recovery Reserve through the same gateway with exact reviewed identity, or fail closed; read-only Finalize stays separate. Check owner generation and fresh authority before each effect; retain claim through uncertain read-back. Claim takeover requires proven terminal run, credential expiry/revocation and reconciled tag/draft/asset/Release effects. A credential still valid outside the gateway is a stop even if journal mode changed. Do not add another lock service, a timed-lease unlock, or rely on Actions concurrency alone.
- **Test Scenarios**: Cutover at every consequential boundary (claim, policy/source check, intent, tag push/read-back, draft creation, asset upload, publish, hook/evidence checkpoint, owner release); lost/ambiguous tag and Release responses; stalled legacy owner; stale credential; competing actor; CAS conflict; resumed stranded exact tag.
- **Tests**: `packages/cg-release/tests/{test_publication_control,test_publication_checkpoints,test_authority,test_recovery,test_worker_e2e}.py`, `tests/create-release.Tests.ps1`, additional targeted fault-injection cases using real journal rules and bounded fake outer services.
- **Acceptance criteria**: For both orderings of legacy/cutover/controller, no second writer can obtain authority; no duplicate public identity occurs. Every unknown remote effect retains its claim/intent and safe recovery path. Negative direct-write probes are required before later activation; local tests alone do not satisfy remote enforcement.

## Phase 3: Wire The One CI/CD Path

### 5. Dispatch Bare Tags And Preserve Existing Command Modes

- **Requirements**: R1, R3, R6
- **Files**: canonical `.github/prompts/cg-release.prompt.md`, `scripts/cg_release_cli.py`, `bin/cg-release`, `bin/cg-release.cmd`, generated `.kilo/commands/cg-release.md` and other native targets via the canonical generator, command/help tests and release docs.
- **Details**: Bare valid tag selects the exact GPID controller request only; distinguish an explicit attached checkout branch from detached HEAD needing a branch. Verify remote origin numeric repository ID, remote ref and exact SHA against protected-default policy; never infer source from tag shape. `plan/start/status/resume` remain argument-preserving generic calls. Do not expose legacy Recovery as a routine fallback or infer an absent installed controller. `--yes` confirms local submission, not publication or policy changes. Regenerate native targets from canonical `.github/` sources; update reviewed command-definition evidence, help catalog and derived docs using existing help-evidence workflow, without redesigning certification.
- **Test Scenarios**: Bare four-part and stable input, empty/unknown flags, detached checkout, fork, moved branch, stable from `dev`, mixed legacy/generic arguments, disabled/uninstalled controller, stale catalog/definition evidence.
- **Tests**: `scripts/tests/test_release_controller_launchers.py`, `scripts/tests/test_release_policy.py`, prompt/help catalog tests, `python scripts/cg_generate_targets.py --all --dry-run` after generation and existing help gate.
- **Acceptance criteria**: One documented bare-tag route is usable only when the controller is actually enabled and qualified; generated targets match canonical source and existing help evidence passes. Disabled paths return a safe actionable error, not a legacy attempt.

### 6. Bind Review, CI, Artifacts And Publication Without Extra Prerelease Pauses

- **Requirements**: R2, R5, R6, R7
- **Files**: `packages/cg-release/src/cg_release/{reviewed_commit,build_evidence,publication_inputs,publication_approval,publication_remote,profile_source,profile_build_verify,profile_docs,profile_docs_verify,profile_attestations,profile_evidence,hooks,hook_authority}.py`, `scripts/release_profile_gpid.py`, `.github/workflows/release-controller-{ci,build,publish,docs}.yml` (keep false guards), existing release and Pages workflows, integration contract and focused tests.
- **Details**: Retain the reviewed preparation PR and bind exact source branch/SHA, reviewed release commit/tree, policy/controller revision, required CI producer/workflow/run/attempt, payload bytes, isolated native build/artifact digest, public annotated tag bytes/object/peeled commit, GitHub Release ID/classification/assets, and second evidence PR/attestation. Reuse existing validated owner-specific evidence and preflight receipts instead of repeating the full native gate for an unchanged commit. Register actual build job/attempt; a successful wrapper with skipped release work is not proof. Route GPID prereleases to a protected credential environment configured for automatic post-CI publish without a second human reviewer; independently review its authorization and job scope. Keep official human publication approval and protected default-ref Pages deploy. The current `profile_docs.py` always calls `verify_deployment`, so for four-part prereleases explicitly satisfy the required `docs` completion hook using the verified immutable release-docs build artifact, exact successful producer run/attempt/job/artifact and a reviewed stable snapshot baseline. Bind its hook `remote_id` to the verified positive build-run identity and `evidence_digest` to the sealed immutable artifact inventory; use existing hook validation and do not fabricate a Pages deployment. Official `docs` hook continues to verify the protected `github-pages` deployment. Optional mutable site composition may continue independently and must not be mislabeled as prerelease deployment proof. No flag may turn a stable tag into prerelease or waive required CI.
- **Test Scenarios**: Failed/skipped/foreign same-name check, altered source or payload, expired/reused artifact, deleted branch, policy drift, incorrect tag object, Release/asset conflict, missing help evidence, prerelease without Pages but with exact successful build and stable baseline, prerelease with a skipped docs producer or missing baseline, official without required approval/Pages, lost publish response and failed post-hook.
- **Tests**: Existing package build/publication/profile suites and `scripts/tests/test_release_controller_profile.py`, `scripts/evidence/tests/release-pages.test.js`, `scripts/tests/test_release_gate_targets.py`; add exact cross-object negative cases. Use isolated fake provider for defaults; remote denial evidence belongs to Phase 5.
- **Acceptance criteria**: Valid prerelease can move CI -> reviewed commit -> publish -> verified immutable `docs` hook -> attested complete without Pages or another chat/human publication approval; official `docs` still requires protected deployment. A published object with missing hooks stays `published`, never false `complete`.

## Phase 4: Validate Disabled Candidate On Every Target

### 7. Run Focused Suites, Generated Output And Cross-Platform CI

- **Requirements**: R2, R3, R4, R5, R6, R8
- **Files**: affected `packages/cg-release/tests/`, `scripts/tests/`, `tests/create-release.Tests.ps1`, `.github/workflows/`, generated platform trees, documentation and work report.
- **Details**: Complete generation BEFORE review; do not publish changed unreviewed output. Run `uv run --project packages/cg-release pytest packages/cg-release/tests -q`, `uv run --project packages/cg-release ruff check packages/cg-release`, `python scripts/release_profile_install.py --check`, `python scripts/cg_generate_targets.py --all --dry-run`, appropriate focused Python/Node suites, renderer and help/catalog verification. Use the canonical safe `tests/Run-Tests.ps1` runner through an isolated execution child and inspect its saved result, not unsafe direct Pester pipelines; report skips, cleanup and host scope. On an approved candidate commit run `python scripts/cg_pr_preflight.py --phase committed --full-gate --run-native-target`; a prepare-mode receipt cannot replace it. Run ordinary PR CI including the six Python/OS package cells and required release checks on Windows/Linux/macOS; do not represent Windows Git Bash as native Unix. Pin Kilo support only to the documented minimum and capabilities, not an exact-version allowlist or upper bound.
- **Test Scenarios**: All specified negative version/cutover/authority/credential cases; faulty symlink or host, stale help catalog, absent marker/baseline, failed/unknown check and build attempt.
- **Tests**: Commands above, safe Pester runner, registered workflow results, targeted generated docs/check artifacts. Do not execute a live publisher as a test.
- **Acceptance criteria**: Reviewed candidate passes exact committed-input gate, ordinary PR CI and all required cross-platform cases; every failure, skip and unsupported host is reported. Publisher remains disabled. Phase 4 does NOT establish old V12/V13, real credential denials or live performance.

## Phase 5: Separately Authorize Setup And Cutover

### 8. Prepare Real Disabled Installation And Qualify Bridge

- **Requirements**: R2, R4, R5, R7
- **Files**: reviewed `.release-controller.json`, `scripts/release_profile_install.py`, real metadata/changelog inputs, trusted workflow templates, bridge qualification workflow and operator guide.
- **Details**: Under separately approved maintainer setup, supply and verify numeric repository ID, controller source and wheel digest, journal root/state history, exact control/publishing App IDs/scopes, registered CI/check identities, signing policy, source/line/history/bootstrap records, stable docs baseline, source files and protected environment/ruleset evidence. Keep `enabled: false` and false workflow guards. `scripts/release_profile_install.py --check` compares the installed files byte-for-byte to a placeholder template: run it on the unchanged generated disabled template in Phase 4, but do NOT use that equality check on a reviewed configured-but-disabled installation or regenerate over it. Validate the configured policy instead with strict controller policy parsing plus verified real remote identities, source files and protected-setting read-back; retain separate template-parity and configured-policy evidence. Deliver and remotely verify the required legacy-format Bridge plus distinct genuine clean Windows/native Unix previous -> bridge -> successor client receipts before retiring its writer; fixtures are not receipts. No secrets in plan, logs or commits. Do not count a synthetic successor as the authorized `v1.2.0.9020` run.
- **Test Scenarios**: Missing App scope or unsupported environment; insufficient tag protection; unrecognized historical Release; missing stable snapshot; failed real clean client; source-free wheel digest mismatch.
- **Tests**: Exact remote read-only settings inventory plus separately authorized sandbox denied-write probes; authorized Bridge qualification runs with separately retained identities; strict configured-policy parsing and identity/read-back checks. Template parity comes from Phase 4 only; no local fixture counts as live proof.
- **Acceptance criteria**: Every real prerequisite has independently reviewed exact evidence; any unavailable setting or receipt keeps the installation disabled and this phase pending.

### 9. Execute Reviewed Atomic Cutover, Not A Flag Flip

- **Requirements**: R3, R4, R5, R7
- **Files**: reviewed protected policy and workflows, state branch journal, publishing and control App/credential settings; do not select exact remote values from this plan.
- **Details**: Before any production enablement, request separate approval for an isolated sandbox repository with its own VERIFIED numeric repository ID, protected default and state branch, reviewed real metadata/baseline, control App, check identities, and installed exact pinned controller wheel/workflow revision. Normal GPID `start` calls `verify_bridge` before admission; therefore the sandbox policy must include its OWN previously published previous/Bridge/successor distributions, authorized Bridge delivery and genuine Windows/native Unix clean-client qualification runs with exact sandbox-bound IDs. Production Bridge evidence cannot be reused under a different repository ID. Only the sandbox policy has `enabled: true`; production `.release-controller.json` and all production workflow guards remain disabled. In the sandbox, use normal `start` admission and reviewed preparation PR to create the exact journal `building` record; its authorized control App runs the normal `build_stage.py` ticket issuer against the enabled sandbox policy, sealing source SHA/tree, policy, controller wheel, lock digests and dispatch nonce. Normal registered release-mode CI and build jobs consume that ticket; their existing registration and artifact verifiers must pass, including the six-cell producer, native docs builder and exact artifact. Disable the sandbox publication job and withhold publishing App credentials: stop the TRIAL request at verified pre-publication state with no tag, Release or asset for that trial. The already published sandbox Bridge prerequisites remain separate authorized history, not trial output. Do not mint a test ticket directly or relax admission/build checks. The literal `false` registration guards currently prevent this, so enable only the reviewed sandbox registration jobs under separate approval; never enable production to run this test. Retain sandbox repository ID, bridge/qualification receipts, policy SHA, exact workflow SHA, run/attempt, job, check producer and artifact identity, and distinguish sandbox qualification from production proof. If sandbox Bridge qualification or normal registration cannot be completed, or if the trial cannot avoid its own public write while matching the essential release-mode contract, stop and revise the plan instead of using the first live prerelease as the test. Then request separate user approval for exact production repository/settings, migration, activation and rollback/recovery procedure. Acquire cutover-pending owner on the production CAS journal; drain/reconcile all legacy owners and effects and prove retired legacy credentials cannot write tags OR Releases using explicitly authorized negative probes (attempted writes, not read-only inspections). Apply approved protection/credential handoff with controls that prevent an effective default-branch or workflow enablement outside this owned transition; read back remote branch, journal, rulesets, environments, App scopes, old and new denied operations. Only then commit effective `controller` mode, enable reviewed policy and workflow guards as authorized, and release the cutover claim. If repository setting changes cannot be made/observed atomically relative to gateway credentials, keep all publishers disabled during that window and do not advertise an enabled routine path. Never rely on read-only policy equality or `concurrency.group` alone.
- **Test Scenarios**: Cutover requested while legacy owns a write, claim loss before tag, stale old credential after policy change, failed policy merge, dropped settings response, false enabled guard, missing sandbox Bridge or clean-client receipt, controller runs before its repository's bridge proof.
- **Tests**: Separately authorized non-public release-mode CI/build success trial, sandbox denial/fault trials, then exact production read-back and recorded state transitions. No local green suite substitutes for remote permission proof.
- **Acceptance criteria**: Actual release-mode CI/build registration, producer cells and immutable artifact verification succeeded before activation without any public object write. Effective old writer cannot publish, and new writer can publish only with the single current claim; exact remote mode/config and denials are retained. On uncertainty, stop with publisher disabled or owned transition retained; never assume automatic rollback or delete a tag. An enabled policy flag alone is not acceptance.

## Testing Strategy

Use deterministic local fixtures for every version/history branch and each CAS
boundary, replacing only outer GitHub transport while exercising real journal
validation. Include positive and negative controls. Separate actual cross-platform
and live remote authorization trials from mock results. Verify all changed
canonical/generated docs and help-evidence catalog; no test should modify
repository settings or create a public tag by default. Pester execution uses the
project's safe runner and records skips and cleanup independently of assertions.

The final acceptance is a separate, explicitly authorized maintainer operation
after Phase 5: verify `v1.2.0.9020` and its source are still unoccupied/current,
submit once from verified `dev`, preserve durable request ID and exact review,
CI, build, tag, Release, asset, attestation and Pages-independent prerelease
evidence. Time tracked handoff to receipt (target <=120 seconds) separately
from queue, review, build, publication, final evidence and recovery. Report
failed/blocked/unknown attempts, not only successes. The historical V12/V13
criteria retain their own evidence definitions; do not mark them passed based
on this plan, local fixtures or a different acceptance label.

## Documentation Checklist

- Update canonical `/cg-release` command, generated targets, usage examples and
  controller operator guide together, preserving cross-adapter parity.
- Document four-part grammar, separate historical/managed identities, branch
  selection and exact disabled/status/resume behavior; explain `--yes` does not
  bypass required checks or official approval.
- Record reviewed metadata files/marker, stable docs baseline, owner recovery,
  effective writer permissions, staged activation/rollback and stop rules.
- Refresh existing help definition evidence and catalog before publication;
  leave help certification architecture and second evidence PR unchanged.

## Risks & Mitigations

| Risk | Mitigation and stop |
|------|---------------------|
| Journal CAS cannot fence a still-valid legacy GCM or administrator Release API credential. | Phase 1 inventories principals and identifies a conditional gateway; separately authorized Phase 5 denied-write probes must prove effective exclusion before activation. If unavailable, stop; no TOCTOU claim. |
| GitHub settings or policy can change outside cutover owner. | Protect effective activation path; disable all writers during unverifiable handoff; remote read-back and denied-operation evidence are required. |
| Four-part identity corrupts SemVer baseline or latest stable selection. | Distinct GPID kind, tests against historical tag fixtures and core/line ambiguities; no hidden projection or rewritten tags. |
| Installed policy references absent metadata/changelog or no stable docs baseline. | Resolve reviewed source inputs and baseline in Phase 1; missing values block live acceptance. |
| A green wrapper or stale preflight receipt masks failed exact build/CI. | Bind registered producer, SHA, tree, run/attempt, artifact digest, LF provenance and exact help evidence; never treat local receipt as remote approval. |
| Real Bridge, Apps, environments or cross-platform evidence is not obtainable. | Keep disabled guards and separate pending remote phases; never treat prior deferral as a pass. |
| Unknown tag/Release response or expired artifact invites duplicate write. | Retain claim and intent; reconcile exact remote objects; rebuild exact source under renewed approval where required, never clobber published bytes. |

## Out of Scope

Replacing the second evidence PR, redesigning Kilo help certification, exact
Kilo-version allowlists/upper bounds, generic controller behavior for other
repositories, a second CI service, routine use of legacy Bridge/Recovery,
automatic settings changes or live publication from `/cg-work` without
separate approval, and retrospective claims that V12/V13 have passed.

## Completion Contract

### Outcome

One controller-backed GPID routine path preserves exact four-part prerelease
and official release identities, enforces one shared publication/cutover owner
and binding CI/CD proof, and completes a separately approved real acceptance
without a routine legacy fallback. Completing local work alone does not meet
the final remote outcome.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Reviewed version, source, metadata/baseline contract and conditional gateway feasibility; actual denied writes stay pending for Phase 5. | Phase 1 contract and read-only capability/principal inventory with explicit unproved denials in execution report | yes |
| V2 | 2 | Exact four-part identity and historic stable/generic regressions, shared CAS fencing and boundary fault injection. | Focused package, reader, Node, legacy Pester results and fault-case matrix | yes |
| V3 | 3 | Bare-tag routing, generated target/help evidence, exact CI/build/payload/tag/Release/attestation binding and stable vs prerelease negative tests. | Command/profile suites, generated-target dry run, catalog/docs gate, fault-case results | yes |
| V4 | 4 | Disabled reviewed candidate passes cross-platform suites, exact committed preflight and required ordinary PR CI; skips and cleanup disclosed. | CI links/sha/cell results, preflight receipt, safe Pester result, generated output check | yes |
| V5 | 5 | Separately approved repository-bound production and sandbox Bridge/setup, successful sandbox trial release-mode CI/build registration without trial publication, denied direct writes, single-owner production cutover and current remote policy/setting read-back. | Exact approvals, sandbox Bridge/clean-client receipts and CI/build run/attempt/job/artifact proof, strict configured-policy validation, production Apps/ruleset/Bridge clean-client identities and cutover journal/remote records | yes |
| V6 | final | Separately approved live `v1.2.0.9020` from verified `dev`, exact public objects and final attestation, complete measured handoff and total timing. | Durable request locator, review/CI/run/commit/tag/Release/asset/attestation IDs and timing report | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | 2 | No stable branch override, unreviewed version translation or generic SemVer regression. | Source/line tests and exact byte comparisons |
| C2 | 3 | Help-evidence and second evidence PR remain required; no prerelease Pages requirement and no official approval bypass. | Help/catalog checks, hook and environment tests |
| C3 | 4 | No hardcoded exact/maximum Kilo version or unreviewed generated output. | Capability/minimum-version tests and generated-target/diff review |
| C4 | 5 | No activation, settings write or release without separate express approval and actual remote denial proof. | Approval record and before/after remote settings/actor results |
| C5 | final | No V12/V13 live-gate claim from local evidence; no duplicate, moved or deleted public objects. | Exact remote provenance and pending-gate ledger |

### Boundaries

- Allowed after separate `/cg-work` approval: scoped controller/GPID version,
  command, fence, GitHub Actions, tests, documentation and reviewed setup changes.
- Requires further separate approval: actual repository settings, bridge
  delivery, controller activation, and the one-time live acceptance release.
- Out of scope: alternate routine publisher, stable override, help redesign,
  second evidence PR replacement, broad platform-version certification.

### Iteration Policy

1. Under `deviation-policy: ask`, stop and seek approval before changing design,
   adding a publisher or dependency, or weakening any required gate.
2. Implement and verify one phase at a time. Preserve previous exact identities
   and logged failures. Never infer a later phase's success from earlier fixtures.
3. Keep disabled until a separately reviewed effective cutover; obtain separate
   user authorization again for remote setup and live release operations.
4. A failed remote effect is reconciled by exact read-back under retained owner;
   recovery resumes missing work only, not rollback by deleting public objects.

### Blocked-Stop Conditions

- No enforceable exclusive gateway or protected effective cutover transition;
  an independently usable old publication credential remains valid.
- Missing real metadata/changelog marker, stable docs baseline, reviewed Bridge
  and clean-client receipts, required App scopes, CI/help evidence or branch rule.
- CAS conflict, unknown remote write, incomplete API inventory, mismatched exact
  tag/Release/asset/source, or failed required test/check/review.
- User approval for implementation, remote settings/activation or live release
  is absent. Do not treat plan approval as any of these approvals.
- Required verification cannot run safely, or a phase/final evidence row cannot
  be supported by an executed check and durable report; mark blocked/pending,
  not passed.
