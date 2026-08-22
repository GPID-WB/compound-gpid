---
date: 2026-08-21
title: "Prevent PR CI reruns with native-target and Kilo capability preflights"
status: active
scope: "Deep"
brainstorm: null
language: "both"
estimated-effort: "large"
deviation-policy: "ask"
artifact-schema-version: 1
execution-report: ".cg-docs/work-reports/2026-08-21-pr-ci-preflight-and-kilo-capability-gates.md"
completed-phases: [1, 2, 3, 4, 5]
current-phase: 6
tags: [ci, pull-requests, preflight, native-targets, kilo, capability-gates, drift, pester]
phases: 6
---

# Plan: Prevent PR CI Reruns With Native-Target And Kilo Capability Preflights

## Objective

Make `/cg-commit-push-pr` and `/cg-verify-pr` stop release-critical
native-target, module-closure, Kilo-host, PR-base, and CI-fix-round errors
before they cause avoidable remote CI reruns. Missing or uncertified Kilo hosts
must remain explicit capability outcomes, never evidence of Kilo integration or
generic linker failure.

## Context

PR #141 exposed gaps between local workflow guidance and the required CI path:

1. A local Python cache could appear in generated skill inventory/ownership
   context even though its bytecode was not a committed product artifact.
2. Active-suite filtering could diverge between emitted assets and validation
   roots.
3. Generic CI paths could imply Kilo behavior on runners without a certified
   Kilo host.
4. `/cg-verify-pr` could use a latest matching workflow run rather than the
   failed check's precise job, while its trailer policy was stronger than its
   worktree isolation.
5. PR base branch handling could default to `origin/HEAD` rather than using the
   actual PR base.

Current foundations reduce the implementation scope:

- `scripts/cg_generate_targets.py` already creates structured generation plans,
  excludes `__pycache__` directories, generates committed native targets, and
  enforces ownership-manifest drift checks.
- `.github/workflows/tests.yml` already runs a native Python gate on Windows
  and macOS plus separate module, Pester, and generic E2E gates.
- `scripts/cg_kilo_preflight.py` has authoritative typed Kilo outcomes,
  containment evidence, supported host versions, and the certified `cg-kilo`
  launcher.
- `tests/Run-Tests.ps1` is the sole safe Pester runner; new Pester files must
  be registered there and results are consumed from `tests/last-run.json`.

Relevant prior knowledge:

- Native trees are generated, committed product surfaces; generator, ownership,
  drift, and CI gates must fail closed. Source:
  `.cg-docs/plans/2026-07-27-canonical-native-packaging-foundation.md`.
- Kilo coexistence needs executed certified-host inventory evidence; host
  absence is not proof of functional correctness. Source:
  `.cg-docs/solutions/environment-issues/2026-08-14-kilo-contained-launch-and-no-follow-copy.md`.
- Every Kilo-reachable compatibility skill path must be project-contained and
  checksum-managed. Source:
  `.cg-docs/solutions/bugs/2026-08-20-kilo-cross-adapter-skill-autodiscovery.md`.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Add one Python 3.8+ stdlib-only PR preflight that owns impact classification and the authoritative native-target Python command. It supports prepare/committed phases, resolved base, changed-file or Git-derived changes, JSON/text output, selection-only behavior, and native-run execution. | PR #141 follow-up; plan review P1.1 |
| R2 | The preflight must run or emit all required module dependency, cross-suite, and ownership validation checks in addition to the native pytest command; CI must not retain a divergent duplicate list. | plan review P1.1 |
| R3 | `__pycache__` and `*.pyc` never enter generated skill bundles, ownership manifests, or committed generated trees. Tracked or manifest-referenced cache paths fail; correctly excluded untracked local cache paths are reported without failing. | PR #141 failure; native packaging contract |
| R4 | Active-suite closure applies identically to emitted skill bundles and validation/projection roots: CG-only excludes CR-only assets, CG+CR includes registered CR assets, and unregistered assets fail ownership validation. | PR #141 failure; module-registry contract |
| R5 | Generic Windows/macOS link/unlink and E2E paths remain host-independent. They report Kilo as not applicable when absent and never claim certified Kilo behavior from a missing host. | Kilo coexistence solution |
| R6 | Reuse `cg_kilo_preflight.py` status values and evidence rather than inventing another Kilo vocabulary. Deterministic Kilo coexistence and copy tests are mandatory native-target coverage; real certified-host evidence is opt-in and visibly reported. | plan review P1.2; Kilo preflight contract |
| R7 | Both PR workflows resolve one base branch: existing PR `baseRefName`, then explicit `--base` where accepted, then default branch. Every base-sensitive Git, preflight, and PR-create operation uses it in both `gh` and VS Code extension paths. | PR #141 failure; plan review P2.2 |
| R8 | `/cg-verify-pr` resolves each failed GitHub Actions check from its `detailsUrl` to the exact run and job, retrieves that job's failed log, and uses an explicit manual route for non-Actions or unparseable URLs. | plan review P1.3 |
| R9 | Auto-fix halts on pre-existing staged, unstaged, or untracked worktree changes. A verification pass creates at most one targeted `fix(ci)` commit with a unique `CI-Fix-Round: <PR>/<N>` trailer. | plan review P1.4 |
| R10 | Canonical prompt, shared contract, generator, script, CI, or registry changes regenerate and commit `.agents/`, `.claude/`, `.kilo/`, and `.opencode/`; committed drift runs at `HEAD` before push. | native packaging contract |
| R11 | Tests cover prompt ordering and behavior independently, register any new Pester file in `tests/Run-Tests.ps1`, and run Pester only through the safe runner with `tests/last-run.json` evidence. | project Pester safety rules |
| R12 | A configured certified-host integration job performs real `cg-kilo` preflight/launch evidence. An always-runnable capability-report job writes a neutral not-applicable summary when runner/version configuration is absent. | plan review P2.1 |
| R13 | CI provides event-specific base/change context to preflight: PRs fetch and pass the actual base revision; pushes pass the prior revision when available or use an explicit full-gate fallback. Missing or shallow history must fail selection visibly rather than compare the wrong revision. | formal plan review P1.2 |
| R14 | The mandatory native runner executes only deterministic Kilo tests. Real embedded-host tests marked `integration` run only in the trusted certified-host job. | formal plan review P2.1 |
| R15 | Manifest-driven project projection uses the same active-suite closure as generator output; CG-only, CG+CR, and unowned-asset fixtures prove membership parity across both paths. | formal plan review P2.2 |
| R16 | The certified-host job runs only for protected-branch pushes or manual dispatch explicitly limited to the protected default branch. It uses a protected environment with maintainer approval, explicitly checks out that trusted ref, never executes pull-request code, and compares the observed executable SHA-256 to a reviewed expected value. | formal plan review P1.1, P2.3; re-review P1.1 |

## Implementation Steps

## Phase 1: Authoritative Preflight Contract

### 1. Add the shared CI-impact selector and runner

- **Requirements**: R1, R2, R3, R10, R11, R13, R14
- **Files**:
  - `scripts/cg_pr_preflight.py` (new)
  - `scripts/tests/test_cg_pr_preflight.py` (new)
  - `scripts/tests/test_target_drift.py`
- **Details**:
  - Implement pure, stdlib-only functions for changed-file classification,
    base resolution inputs, native-target selection, module-gate selection,
    cache-artifact reporting, and structured results.
  - Support `--phase prepare|committed`, `--base <branch>`, repeated
    `--changed-file <path>`, Git-derived changes, `--format text|json`,
    selection-only output, and `--run-native-target` execution.
  - Make the native runner invoke `sys.executable -m pytest` with one canonical
    ordered file list and `-m "not integration"` for the generic mandatory
    path. It must also execute `cg_validate_modules.py`
    dependency, cross-suite, and ownership checks, preserving existing hard
    failures rather than replacing them with ownership-only pytest coverage.
  - Return registered Pester file-group identifiers when needed; never invoke
    Pester or `tests/Run-Tests.ps1` itself.
  - Report all cache hits with paths and provenance; fail only when tracked or
    ownership-manifest-referenced cache artifacts are found.
- **Test Scenarios**: canonical source change; generated-tree-only change;
  Kilo/link change; no-impact change; explicit and Git-derived files; PR base
  SHA/ref; push-before SHA; new-branch/zero-before full-gate fallback; shallow
  or missing Git history; text/JSON output; prepare versus committed behavior;
  module command failure; cache fatal/nonfatal distinctions; integration-marker
  exclusion; no Pester subprocess invocation.
- **Tests**: `python -m pytest scripts/tests/test_cg_pr_preflight.py scripts/tests/test_target_drift.py -q`
- **Acceptance criteria**: One successful preflight result identifies the exact
  Python and module gates needed by local workflows and CI, without duplicate
  test-list ownership or unsafe Pester execution.

### 2. Delegate native CI to the preflight without dropping existing gates

- **Requirements**: R1, R2, R6, R10, R13, R14
- **Files**:
  - `.github/workflows/tests.yml`
  - `scripts/tests/test_cg_pr_preflight.py`
  - `tests/prompt-tools.Tests.ps1`
- **Details**:
  - Replace the inline native pytest file list with the preflight's
    `--run-native-target` mode on both matrix platforms. Keep the runner's
    generic test marker as `not integration` so an incidental editor-host
    installation cannot convert a mandatory runner into real-host coverage.
  - For pull requests, configure checkout/history and pass the actual
    `github.event.pull_request.base.sha` (or an explicitly fetched equivalent)
    to preflight. For pushes, pass `github.event.before` when it is a usable
    revision; for branch creation, zero SHA, or unavailable history, invoke the
    preflight's explicit full-gate fallback. Do not infer `origin/HEAD`.
  - Retain the separate Pester suite, generic E2E, backend race evidence, and
    artifact uploads. Transfer the existing module dependency, cross-suite, and
    ownership gate to the preflight runner or make the workflow call a
    preflight-emitted module gate so each remains mandatory and visible.
  - Include deterministic cases from `test_kilo_coexistence.py`,
    `test_kilo_copy.py`, and `test_cg_pr_preflight.py` in the authoritative
    native command. Reserve the existing `@pytest.mark.integration` embedded
    host case for the certified-host job.
  - Add static contract tests that prove the workflow delegates to preflight,
    does not keep a second authoritative native list, and retains all three
    module validation modes.
- **Test Scenarios**: workflow delegates exact runner; all module checks present;
  Kilo deterministic tests present and integration tests absent; PR base revision
  fetched/passed; push full-gate fallback; Pester/E2E/race gates retained;
  nonzero preflight exits fail the job.
- **Tests**: `python -m pytest scripts/tests/test_cg_pr_preflight.py -q`; focused `prompt-tools` via safe Pester runner
- **Acceptance criteria**: CI and local preflight use the same native target
  command and module validation set, with no lost gate.

## Phase 2: Generator, Registry, And Drift Hygiene

### 3. Enforce cache artifact hygiene across inventory and drift

- **Requirements**: R3, R10
- **Files**:
  - `scripts/cg_generate_targets.py`
  - `scripts/tests/test_cg_generate_targets.py`
  - `scripts/tests/test_target_drift.py`
  - `scripts/tests/test_cg_pr_preflight.py`
- **Details**:
  - Preserve the existing `__pycache__` directory exclusion and add explicit
    rejection for `*.pyc` regular files in `_inventory_skill_bundle` so a cache
    file cannot bypass the directory rule.
  - Test nested cache paths, cache-containing prior manifest fixtures, and
    committed-drift behavior. Keep a correctly excluded untracked local cache
    nonfatal, but surface it in preflight output for diagnosis.
  - Do not alter the existing deterministic manifest or safe stale-cleanup
    ownership contract.
- **Test Scenarios**: nested `__pycache__`; nested `.pyc`; malformed manifest
  containing cache; tracked cache file; excluded untracked cache; regenerated
  bundle and manifest contain neither cache form.
- **Tests**: `python -m pytest scripts/tests/test_cg_generate_targets.py scripts/tests/test_target_drift.py scripts/tests/test_cg_pr_preflight.py -q`
- **Acceptance criteria**: Cache files cannot be emitted or committed through a
  generated target, while local interpreter noise does not create a false
  release-blocking failure.

### 4. Prove active-suite and ownership closure parity

- **Requirements**: R4, R10, R15
- **Files**:
  - `scripts/tests/test_cg_generate_targets.py`
  - `scripts/tests/test_context_budget.py`
  - `scripts/tests/test_module_registry.py`
  - `scripts/cg_project_projection.py`
  - `scripts/tests/test_project_projection.py`
- **Details**:
  - Add fixture-level tests around `scan_canonical_assets`,
    `cg_context_budget`, `cg_validate_modules`, and the manifest-driven
    `cg_project_projection` closure path.
  - Prove CG-only active suites emit and validate only their closure; CG+CR
    emits registered CR skill bundles; and a present but unregistered CR skill
    fails ownership validation before generation can endorse it.
  - Build matching active-manifest fixtures and compare generator versus
    projection membership for CG-only and CG+CR. Ensure an unowned canonical
    asset fails before either path can publish it.
  - Change generator or validation code only if those tests expose a real
    mismatch; do not redesign module registry semantics.
- **Test Scenarios**: CG-only closure; CG+CR closure; registered CR skill;
  unregistered CR skill; generator/projection membership mismatch; stale or
  malformed active manifest; unknown suite; missing registry while filtering.
- **Tests**: `python -m pytest scripts/tests/test_cg_generate_targets.py scripts/tests/test_context_budget.py scripts/tests/test_module_registry.py scripts/tests/test_project_projection.py -q`
- **Acceptance criteria**: Projection, validation, and generated bundle
  membership agree for each selected suite closure.

## Phase 3: Kilo Capability Boundary

### 5. Adapt authoritative Kilo results for workflow decisions

- **Requirements**: R5, R6, R11, R14
- **Files**:
  - `scripts/cg_pr_preflight.py`
  - `scripts/tests/test_cg_pr_preflight.py`
  - `scripts/tests/test_kilo_coexistence.py`
  - `scripts/tests/test_kilo_copy.py`
- **Details**:
  - Add a small adapter in the PR preflight that consumes bounded JSON from
    `cg_kilo_preflight.py` and maps existing status values to workflow outcomes:
    generic-not-applicable, certified-ready, or blocking configuration/content/
    containment failure.
  - Preserve source status, exit code, version, executable hash, certified
    launcher requirement, and inventory evidence. Unknown or malformed results
    fail visibly rather than defaulting to a safe-looking state.
  - Keep deterministic fake-host containment and checksum-copy tests mandatory
    under the native runner. Preserve `@pytest.mark.integration` on the real
    embedded-host test and use real hosts only as additional certified evidence.
- **Test Scenarios**: missing executable; unsupported version; local projection
  missing/invalid; local content invalid; containment failure; certified success;
  no-coexistence success; malformed JSON; unknown status.
- **Tests**: `python -m pytest -m "not integration" scripts/tests/test_cg_pr_preflight.py scripts/tests/test_kilo_coexistence.py scripts/tests/test_kilo_copy.py -q`
- **Acceptance criteria**: Every workflow-facing Kilo outcome can be traced to
  an existing preflight status and evidence record, with no silent mapping.

### 6. Separate generic E2E from certified-host integration evidence

- **Requirements**: R5, R6, R12, R14, R16
- **Files**:
  - `.github/workflows/tests.yml`
  - `tests/link.Tests.ps1`
  - `tests/unlink.Tests.ps1`
  - `tests/parity.Tests.ps1`
  - `scripts/tests/test_kilo_coexistence.py`
  - `scripts/tests/test_kilo_copy.py`
- **Details**:
  - Preserve generic Windows/macOS E2E invocation with
    `copilot,claude-code,codex,opencode`; make it consume and report a declared
    Kilo capability result, not probe for a host implicitly.
  - Keep generic assertions confined to host-independent links, cleanup, and
    explicit not-applicable reporting. Move certified-only mirror and legacy
    migration expectations to deterministic Python coverage or the certified job.
  - Add an always-runnable capability-report job that writes a neutral summary
    when `vars.CG_KILO_CERTIFIED_RUNNER`,
    `vars.CG_KILO_CERTIFIED_VERSION`, or
    `vars.CG_KILO_CERTIFIED_SHA256` is absent. It must also state that generic
    CI did not run real-host integration.
  - Add an opt-in self-hosted certified integration job guarded by all three
    values and a machine-checkable trusted-event boundary: a protected-branch
    `push`, or `workflow_dispatch` only when its requested ref equals the
    protected default branch. Never run it for `pull_request`, including
    internal pull requests. Attach a protected environment that requires
    maintainer approval and explicitly check out the protected default branch
    rather than a caller-supplied or event-head ref. The job must compare the
    observed preflight-reported executable SHA-256 with the reviewed expected
    SHA-256 in the protected repository variable before `cg-kilo` launch,
    verify the configured version, capture inventory evidence, and report
    failures as host-integration failures rather than generic linker failures.
- **Test Scenarios**: host absent; certificate configuration absent; configured
  certified host; unsupported version; missing/mismatched expected hash;
  untrusted PR excluded; unprotected/default-mismatched dispatch excluded;
  protected push and protected-default dispatch allowed; protected-environment
  approval; trusted-ref checkout; generic E2E without Kilo; deterministic
  containment/copy regression; visible not-applicable summary.
- **Tests**: preflight-owned native runner; focused `link,unlink,parity` Pester
  files via `tests/Run-Tests.ps1`; workflow structural tests
- **Acceptance criteria**: Generic CI never requires a Kilo executable, while
  deterministic Kilo behavior remains mandatory and real-host coverage has an
  explicit, auditable opt-in contract.

## Phase 4: Commit, Push, And PR Base Selection

### 7. Route commit/push preparation through base-aware preflight

- **Requirements**: R1, R2, R5, R7, R10, R11
- **Files**:
  - `.github/prompts/cg-commit-push-pr.prompt.md`
  - `tests/prompt-tools.Tests.ps1`
  - `docs/workflow.md`
  - `docs/reference.md`
- **Details**:
  - Add `--base <branch>` and resolve `$baseBranch` before generation or
    staging: existing PR base from `gh` or the VS Code PR extension, then
    explicit `--base`, then default branch.
  - If the selected PR tool cannot resolve or create against the required base,
    halt with an actionable `gh` route instead of silently using a different
    base.
  - Pass `$baseBranch` to changed-file comparison, merge-base, prepare and
    committed preflight modes, `gh pr create --base`, and extension creation
    parameters.
  - Replace the hard-coded local gate list and direct post-commit drift command
    with preflight output. A missing mandatory selected runtime blocks before
    staging or push; Kilo not-applicable is reported without blocking generic
    behavior.
- **Test Scenarios**: existing PR base; explicit base; default fallback;
  extension base support/unavailable route; preflight-before-staging; committed
  preflight-before-push; missing runtime; Kilo not applicable; generated target
  refresh.
- **Tests**: focused `prompt-tools` via `tests/Run-Tests.ps1 -File prompt-tools`
- **Acceptance criteria**: Commit/push behavior uses one explicit base branch
  on every supported PR path and cannot push locally rejected generated-target
  changes.

## Phase 5: Exact PR Failure Diagnosis And Safe Repair

### 8. Diagnose the exact failed Actions job and protect user work

- **Requirements**: R5, R6, R7, R8, R9, R11
- **Files**:
  - `.github/prompts/cg-verify-pr.prompt.md`
  - `tests/prompt-tools.Tests.ps1`
  - `docs/workflow.md`
- **Details**:
  - Request `detailsUrl` with PR check data. Parse only recognized GitHub
    Actions URLs containing both run and job IDs; retrieve failed output with
    `gh run view <run-id> --job <job-id> --log-failed`.
  - For missing, non-Actions, or unparseable URLs, preserve a manual diagnosis
    route and do not fall back to `gh run list --limit 1`.
  - Resolve `baseRefName` before fetch, merge-base, rebase, changed-file
    comparison, preflight, or trailer history. Use the Kilo capability adapter
    for preflight failures and route host-dependent certified-job failures to
    the certified-host remediation path.
  - Before any auto-fix, run `git status --porcelain`; halt if it reports any
    pre-existing staged, unstaged, or untracked changes. After a clean baseline,
    require exact focused local reproduction selected by preflight except for an
    externally confirmed host-dependent certified integration failure.
  - Retain two-round PR-scoped trailer logic, select unique trailers only in
    `$mergeBase..HEAD`, stage only files changed after the clean baseline, and
    create exactly one `fix(ci)` commit with `CI-Fix-Round: <PR>/<N>` per pass.
  - Report the precise run/job IDs before and after push so stale logs cannot
    drive a later invocation.
- **Test Scenarios**: two jobs in one run; unrelated latest run; absent/non-Actions
  details URL; dirty index/worktree/untracked file; clean targeted fix; duplicate
  trailer; historical unrelated trailer; host-dependent Kilo job; rebase against
  non-default PR base.
- **Tests**: focused `prompt-tools` via `tests/Run-Tests.ps1 -File prompt-tools`
- **Acceptance criteria**: Auto-fix cannot commit user work and diagnoses only
  the failed job that triggered the repair decision.

## Phase 6: Regeneration, Validation, And Knowledge Capture

### 9. Complete parity, documentation, and final evidence

- **Requirements**: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R16
- **Files**:
  - `.agents/` (generated)
  - `.claude/` (generated)
  - `.kilo/` (generated)
  - `.opencode/` (generated)
  - `tests/Run-Tests.ps1` (only if a new Pester file requires registration)
  - `docs/workflow.md`
  - `docs/reference.md`
  - `.cg-docs/solutions/git-workflows/` (post-green only)
- **Details**:
  - Add independent prompt assertions for preflight-before-staging, committed
    gate-before-push, base precedence, exact job log syntax, non-Actions route,
    dirty-worktree stop, Kilo outcome reporting, one trailer-bearing commit,
    no latest-run fallback, and safe-runner instructions.
  - Regenerate every native target after canonical edits. Run prepare and
    committed preflight phases with the implementation PR base, execute the
    native runner, and run focused Pester only through `tests/Run-Tests.ps1`.
  - Read `tests/last-run.json` summary fields rather than injecting full Pester
    output into the work session. Commit intended changes, then run committed
    drift against `HEAD` before push.
  - Update docs only for the `--base` behavior, capability outcomes, and the
    certified-host job contract. After remote CI is green, use `/cg-compound`
    to record one verified solution; do not create it earlier.
- **Test Scenarios**: regenerated native parity; clean second generation;
  required Python suite; Pester summary artifact; committed drift; CI matrix;
  certified-runner absent/configured evidence; trusted-event boundary; expected
  hash match/mismatch; post-green solution capture.
- **Tests**:
  - `python scripts/cg_generate_targets.py --all`
  - `python scripts/cg_pr_preflight.py --phase prepare --base <pr-base> --run-native-target`
  - `. tests/Run-Tests.ps1 -File prompt-tools,link,unlink,parity`
  - `python scripts/cg_pr_preflight.py --phase committed --base <pr-base> --format json`
- **Acceptance criteria**: Required local and remote evidence is green, generated
  trees match committed canonical sources, and institutional learning is captured
  only after verification.

## Testing Strategy

- Use `pytest` `tmp_path` fixtures, bounded subprocess fakes, and synthetic
  manifests for preflight, cache, closure, Git, workflow, and Kilo cases.
- The preflight owns the canonical native command, including deterministic Kilo
  coexistence/copy tests and all three module validation modes. It excludes
  `integration`-marked real-host tests from generic CI.
- Test prompt ordering with independent `IndexOf` positions and separate
  assertions; do not use alternation where sibling text could cause a vacuous
  pass.
- Treat Kilo host absence as not-applicable only for real-host integration;
  deterministic Kilo correctness remains required.
- Derive CI comparison inputs from event data, never `origin/HEAD`: PR base SHA
  or fetched ref for pull requests, push-before SHA when available, otherwise
  an explicit full-gate fallback.
- Run Pester last, only through `tests/Run-Tests.ps1 -File <registered names>`.
  Read `tests/last-run.json` for bounded evidence.
- Test all error paths for nonzero exits, exact manual routes, no unintended
  staging, and preservation of user content.

## Documentation Checklist

- [ ] Document `--base` precedence and extension/`gh` behavior for commit/push.
- [ ] Document exact Actions job diagnosis and manual route for non-Actions checks.
- [ ] Document Kilo capability outcomes and that missing host is not integration proof.
- [ ] Document certified-host variables, protected-event boundary, reviewed SHA-256 prerequisite, and evidence output.
- [ ] Preserve safe Pester runner guidance and `tests/last-run.json` consumption.
- [ ] Confirm generated platform prompt trees include all canonical workflow changes.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Preflight and CI test commands diverge. | A local pass still fails CI. | Make `--run-native-target` the sole native runner and test workflow delegation. |
| Module dependency/cross-suite checks are accidentally dropped. | Invalid registry closure reaches generated targets. | Execute all three validator modes through the authoritative runner and test each. |
| Cache detection blocks harmless local interpreter output. | Developers cannot run normal local tests. | Fail only on tracked or manifest-referenced cache paths; report excluded untracked cache nonfatally. |
| Missing Kilo host hides containment regressions. | Generic CI appears green without Kilo correctness evidence. | Keep deterministic coexistence/copy tests required; show visible certified-host not-applicable evidence. |
| An embedded Kilo host appears on a generic runner. | Mandatory CI becomes host-dependent or claims real-host coverage. | Exclude `integration`-marked cases from the native runner; run them only in the certified job. |
| A self-hosted host runs untrusted PR code. | A fork or unprotected internal branch can execute arbitrary repository code on persistent infrastructure. | Restrict certified integration to protected pushes or dispatch at the protected default ref, require protected-environment approval, and explicitly check out that ref; never `pull_request`. |
| CI compares against an unavailable or wrong base revision. | Change selection is wrong or fails unpredictably on shallow checkouts. | Fetch/pass PR base explicitly; use push-before revision or explicit full-gate fallback. |
| Projection and generator closures drift. | A consumer projection exposes assets that source generation excludes. | Compare active-manifest projection and generator membership under CG-only, CG+CR, and unowned fixtures. |
| Certified host identity is only version-checked. | A substituted executable can be treated as certified. | Compare preflight SHA-256 against a reviewed protected expected-hash variable. |
| Actions URL parsing selects an unrelated job. | Auto-fix commits address the wrong failure. | Require run and job IDs, use `--job`, and halt to a manual route for unrecognized URLs. |
| Auto-fix stages user work. | Unrelated changes are pushed in `fix(ci)` commits. | Hard-stop on a dirty worktree before repair and stage only post-baseline paths. |
| Branch base differs from default. | Incorrect diff/rebase/PR target and misleading CI repair history. | Resolve PR base first; cover `gh` and extension paths or halt when unavailable. |
| Conditional certified job is skipped invisibly. | No auditable record of missing integration coverage. | Always run a lightweight capability-report job; gate only self-hosted integration execution. |
| Canonical edits leave generated targets stale. | Platform behavior diverges. | Regenerate all targets and run committed drift at `HEAD` before push. |

## Out of Scope

- Changing Kilo upstream discovery behavior or certifying a new Kilo release.
- Redesigning non-Kilo link/unlink behavior or consumer managed-copy ownership.
- Replacing the project-wide Pester suite with Python selection logic.
- Parsing arbitrary third-party CI check URLs beyond the explicit manual route.
- Creating solution artifacts before the implementation and remote CI are green.
- Building a general GitHub Actions framework unrelated to these preflight gates.

## Completion Contract

### Outcome

`/cg-commit-push-pr` and `/cg-verify-pr` apply one CI-equivalent native-target
preflight, use the actual PR base and failed Actions job, preserve user changes,
and distinguish Kilo host availability from functional correctness. Generated
targets remain committed, drift-checked, and safely testable.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Preflight owns the native pytest selection plus dependency, cross-suite, and ownership gates; CI delegates with a PR base or explicit push full-gate fallback. | `python scripts/cg_pr_preflight.py --phase prepare --base <pr-base> --run-native-target`; workflow contract tests | yes |
| V2 | 2 | Cache and suite-closure fixtures prove inventory, manifests, drift, generator, projection, and validation agree. | Focused generator, drift, context-budget, registry, projection, and preflight pytest suites | yes |
| V3 | 3 | Deterministic Kilo coexistence/copy tests run in required CI without integration-marked host tests; generic E2E reports host absence as not applicable; certified job has protected-event, protected-environment, trusted-checkout, and hash-verification contracts. | Preflight-owned native runner; `tests/Run-Tests.ps1 -File link,unlink,parity`; workflow contract tests | yes |
| V4 | 4 | Commit/push prompt resolves and applies the one base branch across local preflight, merge-base, and PR creation for `gh` and extension paths. | `tests/Run-Tests.ps1 -File prompt-tools`; `tests/last-run.json` | yes |
| V5 | 5 | Verify prompt retrieves exact Actions job logs, blocks dirty worktrees, classifies Kilo outcomes, and creates at most one trailer-bearing CI fix commit. | `tests/Run-Tests.ps1 -File prompt-tools`; `tests/last-run.json` | yes |
| V6 | 6 | All native trees regenerate; committed drift passes at `HEAD`; required local gates and remote CI are green before solution capture. | Generator; committed preflight JSON; `tests/last-run.json`; CI results | yes |
| V7 | final | Execution evidence is recorded for every required row or an explicit approved exception. | `.cg-docs/work-reports/YYYY-MM-DD-pr-ci-preflight-and-kilo-capability-gates.md` | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | 1 | The preflight is Python 3.8+ stdlib-only and never directly invokes Pester. | Import/subprocess fixtures and source inspection test. |
| C2 | 1 | Module dependency, cross-suite, and ownership checks remain mandatory, and CI receives correct PR/push comparison context. | Preflight and workflow contract tests. |
| C3 | 2 | Generated output and ownership manifests contain no cache artifacts. | Inventory, manifest, and committed drift fixtures. |
| C4 | 3 | Existing `cg_kilo_preflight.py` status vocabulary remains authoritative; missing host is not integration proof; only protected events at a trusted checkout may run real hosts. | Capability mapping and workflow evidence tests. |
| C5 | 4 | An explicit base cannot be silently ignored by a supported PR tool path. | Prompt contract tests for `gh` and extension behavior. |
| C6 | 5 | Auto-fix never stages pre-existing user changes. | Dirty-worktree and selected-path staging tests. |
| C7 | final | Canonical workflow changes regenerate and commit every managed native tree. | `test_target_drift.py` against `HEAD`. |

### Boundaries

- Allowed: canonical CI, prompt, generator, test, workflow, and documentation
  changes; native-target regeneration; post-green verified solution capture.
- Out of scope: upstream Kilo changes; new Kilo certification; non-Kilo linker
  redesign; arbitrary third-party check parsing; pre-verification solution
  artifacts; general GitHub Actions infrastructure.

### Iteration Policy

1. Implement and verify each phase before starting the next.
2. Keep the preflight-owned native command and module gates authoritative; do not
   reintroduce duplicate CI lists.
3. Run Pester only through `tests/Run-Tests.ps1 -File <registered names>` and
   record its bounded JSON result.
4. Under `deviation-policy: ask`, pause before changing a requirement, phase
   boundary, Kilo support claim, CI failure policy, or listed integration path.
5. Mark a phase complete only after every required verification row for that
   phase passes; mark the plan complete only after all final evidence passes.

### Blocked-Stop Conditions

- The preflight, module gate, generator, drift gate, or required test cannot run
  successfully through its approved mechanism.
- A Kilo outcome is unknown, malformed, or requires a new status vocabulary.
- The exact failed Actions job cannot be resolved and the explicit manual route
  cannot supply sufficient diagnosis.
- Auto-fix finds pre-existing worktree changes or needs to stage a path outside
  its post-baseline fix set.
- A required change crosses a stated boundary or requires a deviation without
  user approval.
- Remote CI remains failed after allowed focused recovery.
