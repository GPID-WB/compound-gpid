---
date: 2026-09-16
title: "cg-release prerelease automation: zero-pause flow under 45 minutes"
status: active
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-09-16-cg-release-prerelease-automation.md"
language: "both"
estimated-effort: "large"
deviation-policy: "ask"
artifact-schema-version: 1
tags: [release, automation, prerelease, cg-release, create-release, preflight-receipt, auto-merge, docs-deployment, pester, latency]
phases: 5
completed-phases: [1, 2, 3, 4]
current-phase: 5
execution-report: ".cg-docs/work-reports/2026-09-17-cg-release-prerelease-automation.md"
---

# Plan: cg-release Prerelease Automation — Zero-Pause Flow Under 45 Minutes

## Objective

Make `/cg-release <tag> --auto-approve` run a four-component prerelease from a
clean dev checkout to a published, attested, evidence-committed state with
zero interactive pauses and exactly one full preflight per commit, using
rebase auto-merge and a gate that runs in parallel with PR CI so the
measured window from payload commit to published+attested stays at or under
45 minutes and the full flow (invocation to evidence merged) stays at or
under 90 minutes — while stable releases keep interactive confirmation and
manual merges, and no publication fallback path exists anywhere.

## Context

The v1.2.0.9018/9019 sessions measured over 3 hours wall-clock per
prerelease: the ~33-minute native preflight ran three to four times per
commit (Step 4 gate, Reserve temp-clone re-run, Finalize re-run, evidence
step), and four-plus human pauses interrupted the flow. Two failure classes
cost hours of rework: the classic branch-protection 404 (fixed by PR #173
ruleset-based authority; the workflow-family audit remains open) and the
docs-contract skew between origin/main's `release-pages.yml` controller and
the tag commit's `release-docs.yml` producer (fixed by PR #172 dual-layout
bridge and #175 lineage sync; nothing detects it pre-tag). A draft race
between a parallel publication and Reserve's reconciliation threw
"Conflicting GitHub Release lookup and list" instead of settling.

The brainstorm (2026-09-16) recorded two maintainer decisions: full docs
deployment moves to stable three-component releases only (Option A — main
leaves the prerelease critical path via one controller-change PR to main),
and the repo-settings change is approved (enable Allow auto-merge; add
required checks to "Protect dev"). The async release controller stays
disabled under `D-2026-09-13-defer-live-rollout`.

The plan review (2026-09-16, `@cg-plan-critic`) re-based the latency design:
with two CI rounds (payload PR ~15-35 min, evidence PR ~15-35 min strictly
after Finalize), a single 45-minute full-flow target is not reachable. The
maintainer approved the overlap design: payload PRs use
`gh pr merge --auto --rebase` so the PR-head SHA becomes the dev tip; the
single full gate runs in parallel with PR CI at that same commit in an
isolated LF clean clone and emits the receipt there; the evidence step
relies on the evidence PR's GitHub-enforced required checks instead of a
second local gate. Targets are segmented: payload commit to
published+attested at or under 45 minutes; invocation to evidence merged at
or under 90 minutes.

Verified implementation facts: `create-release.ps1` requires
`-LegacyOperation Bridge|Recovery` and re-runs the full gate in a temp clone
(lines 348-377); `Get-CgReleaseReservation` (line 544) throws on by-tag/list
disagreement; `cg_pr_preflight.py` has no receipt mechanism (its
`run_native_target` stops on first failure and records per-command exit
codes); repo `allow_auto_merge` is false; "Protect dev" has no required
checks while "Protect main" requires Pester (macos-14, windows-2022), Native
target Python gate (macos-14, windows-2022), and Conventional Commits PR
title; the `/dev/` preview deployment is gated by `pages.yml`'s push path
filter (which excludes `releases/**`), not by `docs-site-build.yml` (whose
`combined-docs-site` artifact has no deploy consumer); five assertion
surfaces constrain the prompt rewrite (`tests/prompt-tools.Tests.ps1`,
`tests/docs-automation.Tests.ps1`, `scripts/tests/test_cg_pr_preflight.py`,
`scripts/tests/test_release_policy.py`,
`scripts/tests/test_release_gate_targets.py`); a receipt written inside the
working tree would trip the strict clean-checkout guard
(`create-release.ps1` lines 287-295), so receipts live outside the working
tree.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Prompt-owned PR automation: payload, main-to-dev sync (stable concern), and evidence PRs created with `gh pr create --body-file`, pushed `--no-follow-tags`, observed with a bounded poll, and merged via GitHub auto-merge — rebase method for the payload PR (preserves the PR-head SHA as the dev tip); stable-tag PRs on main stay manual; never bypass/admin-merge/retry blindly | Brainstorm Req 1; acceptance criteria; review P1.1 (Option A) |
| R2 | `--auto-approve` parsed at a new prompt Step 0.5 before any tool dispatch; valid only for four-component dev prereleases; pre-approves semver, name, notes, payload PR, Reserve, Finalize, automated merges, large-scan continuation, and resume; never weakens any guard; zero pauses | Brainstorm Req 2; acceptance criteria |
| R3 | Durable preflight receipt: `cg_pr_preflight.py --emit-receipt` writes canonical JSON (commit SHA, tree SHA, LF provenance, timestamp, exact command list, per-command exit codes, digest); `create-release.ps1 -PreflightReceipt` skips the ~33-min re-run only on exact commit/tree SHA match, valid digest, and LF-clean-clone provenance; one full gate per commit; segmented latency targets (payload commit to attested <= 45 min; full flow <= 90 min) | Brainstorm Req 3; review P1.1 (Option A), P2.3, P3.2 |
| R4 | Option A docs contract: `release-pages.yml` skips four-component prerelease tags; prerelease Finalize requires only the tag-run `release-docs.yml` build; `pages.yml` push path filter gains `releases/**` so release commits refresh the `/dev/` preview; stable releases keep the pre-tag sync gate (controller/producer contract check + main-tip lineage) with concrete halt remediation | Brainstorm Req 4; maintainer decision (Option A); review P1.2, P1.3 |
| R5 | Failure-mode hardening: Reserve is the only publisher; no `gh release create` / release-API tag creation / Release delete-PATCH anywhere; draft-race bounded read-only reconciliation accepting a settled pair; payload PR only after the publication decision; stranded-payload repair instruction in Step 1a with the exact recovery sequence; no dependence on `release-result.txt` surviving; classic-protection audit of the script and workflow family | Brainstorm Req 5; evidence items 4, 7, 9, 10; review P3.4 |
| R6 | Repo settings (maintainer actions, verified read-only): Allow auto-merge enabled; "Protect dev" gains required checks mirroring main (Pester macos-14/windows-2022, Native target Python gate macos-14/windows-2022, PR title Conventional Commits; 0 approvals) | Brainstorm Req 6; maintainer approval |
| R7 | Root-cause the `test_phase5_transport.py` flake (evidence item 8); fix, or quarantine with a documented reason | Brainstorm; constraints |
| R8 | Tests and parity: co-authored Pester assertions in `create-release.Tests.ps1`; all five prompt-rewrite assertion surfaces (`prompt-tools.Tests.ps1`, `docs-automation.Tests.ps1`, `test_cg_pr_preflight.py`, `test_release_policy.py`, `test_release_gate_targets.py`) kept, re-scoped, or re-derived; targets regenerated via `cg_generate_targets.py --all`; `test_target_drift` green; Pester only through `tests\Run-Tests.ps1` with `tests/last-run.json` | User constraints; review P2.1, P2.2 |
| R9 | Measured before/after wall-clock record committed to `.cg-docs/work-reports/`; stage timings via `-Timing`; segmented targets recorded | Brainstorm Req 3; review P1.1 |

## Implementation Steps

## Phase 1: Preflight receipts

### 1. Add `--emit-receipt` to `cg_pr_preflight.py`
- **Requirements**: R3
- **Files**: `scripts/cg_pr_preflight.py`, `scripts/tests/test_cg_pr_preflight.py`
- **Details**: Add `--emit-receipt <path>` (required explicit path; no
  default) to `_build_parser`. After a `--run-native-target` run where
  `result.exit_code == 0` and every `CommandResult.returncode == 0`, write
  canonical JSON atomically (temp file + replace) to the given path:
  `schema_version: 1`, `commit_sha` (`git rev-parse HEAD^{commit}`),
  `tree_sha` (`git rev-parse HEAD^{tree}`), `line_ending_provenance`
  (`core.autocrlf` and `core.eol` values of the run environment), `timestamp`
  (UTC ISO-8601), `commands` (the exact executed command tuples), `exit_codes`
  (per-command, in order), and `digest` (SHA-256 over the canonical JSON of
  all preceding fields, sorted keys, UTF-8). Emit nothing on selection
  errors, failed commands, or non-`--run-native-target` runs; a failing or
  interrupted gate never produces a receipt. The receipt path is expected
  OUTSIDE the working tree (the prompt uses the system temp directory): an
  untracked in-tree receipt would trip the strict clean-checkout guard in
  Reserve and Finalize (`create-release.ps1` lines 287-295). Receipt
  lifetime: from the gate run through Finalize of the same release.
- **Test Scenarios**: green full gate emits a receipt whose digest validates
  and whose fields match the run (happy); first-failure stop emits no
  receipt (error); `--selection-only` or no `--run-native-target` emits
  nothing (edge); tampered digest/fields fail verification in step 2's
  verifier tests (error).
- **Tests**: extend `scripts/tests/test_cg_pr_preflight.py` (existing
  patterns: direct function calls and `main()` invocations with `argv`).
- **Acceptance criteria**: `python -m pytest scripts/tests/test_cg_pr_preflight.py` green; a real
  `--phase committed --full-gate --run-native-target --emit-receipt` run in
  an isolated LF clone produces a receipt that `create-release.ps1
  -PreflightReceipt` accepts (verified in step 2).

### 2. Add `-PreflightReceipt` to `create-release.ps1`
- **Requirements**: R3, R5
- **Files**: `create-release.ps1`, `tests/create-release.Tests.ps1`
- **Details**: Add an optional `-PreflightReceipt <path>` parameter (both
  phases). In the gate block that currently clones to a temp root and runs
  `cg_pr_preflight.py` (lines 348-377), first attempt receipt verification:
  parse the JSON, require `schema_version == 1`, recompute the digest over
  the canonical field set and require an exact match, require
  `commit_sha == $headCommit` (and that HEAD is the exact current
  `origin/dev` tip, per the existing tag-safety check), require `tree_sha ==
  (git rev-parse "HEAD^{tree}")`, and require the receipt's
  `line_ending_provenance` to record `core.autocrlf=false` and `core.eol=lf`
  (the same conditions the temp-clone re-run enforced; this preserves
  line-ending-sensitive assurance). On full success, skip the temp-clone
  re-run and log "Preflight receipt accepted for <commit>; skipping
  re-run." On any mismatch, malformed file, missing file, or digest failure,
  keep the current behavior (run the full gate) — never fail open, never
  treat an invalid receipt as a pass. Finalize verifies the receipt the same
  way before its own gate use.
- **Test Scenarios**: exact SHA + LF provenance + valid digest skips the
  re-run (happy); wrong commit/tree SHA, tampered digest, missing file,
  malformed JSON, or non-LF provenance each fall through to the full re-run
  (error paths); no `-PreflightReceipt` keeps today's behavior (edge).
- **Tests**: offline-mocked Pester in `tests/create-release.Tests.ps1`
  (mirror the existing "executable two-phase publication with offline mocks"
  Describe style: mock `Invoke-CgReleaseApi` and the git/preflight surface;
  assert the temp-clone preflight is skipped on a valid receipt and executed
  on an invalid one). Add text-presence assertions for the parameter and the
  fail-safe semantics.
- **Acceptance criteria**: `tests\Run-Tests.ps1 -File create-release.Tests.ps1` green
  with all existing assertions plus the new ones; `tests/last-run.json`
  reports `passed: true`.

## Phase 2: create-release.ps1 hardening

### 3. Draft-race bounded read-only reconciliation
- **Requirements**: R5
- **Files**: `create-release.ps1`, `tests/create-release.Tests.ps1`
- **Details**: Replace the immediate throw in
  `Get-CgReleaseReservation` ("Conflicting GitHub Release lookup and list")
  with a bounded reconciliation loop: up to N attempts and a short delay D
  between attempts, defined as script constants with test-injectable
  overrides (e.g. `-RaceAttempts`/`-RaceDelaySeconds` script-scope variables
  the offline tests set to 1 attempt / 0 seconds; production defaults e.g. 5
  attempts / 15 seconds, total bound ~75s). Each attempt re-reads both the
  by-tag lookup and the paginated list. If they settle into agreement (both
  present and consistent, or both absent), return the settled result (the
  EXISTS path handles a settled present pair). If they still disagree after
  the bound, throw the existing error (renamed reason preserved for
  diagnostics). Metadata assertions on a settled pair remain unchanged;
  Finalize stays the authoritative verifier of the final pair state. No
  remote writes anywhere in the loop. Keep at most one real-delay assertion
  in the suite so offline tests do not sleep the full bound.
- **Test Scenarios**: by-tag present + list absent settles to a consistent
  pair within the bound (happy, mirrors evidence item 7); both absent
  settles to null; disagreement persists past the bound throws (error);
  consistent-from-the-start path unchanged (edge); injectable zero-delay
  overrides keep the suite fast (edge).
- **Tests**: offline-mocked Pester: a mock sequence where the first list read
  misses the release and the second finds it, asserting no throw and correct
  return; a mock sequence that never settles, asserting the bounded throw;
  existing static-mock conflict tests (e.g. "rejects same-tag drafts hidden
  from the tag lookup") updated to the injected fast path.
- **Acceptance criteria**: Pester green; the error string
  "Conflicting GitHub Release lookup and list" only appears after the
  bounded wait; the suite adds no meaningful runtime.

### 4. No-fallback hardening and classic-protection audit
- **Requirements**: R5, R8
- **Files**: `create-release.ps1`, `scripts/release-legacy-authority.ps1`,
  `.github/workflows/release-controller*.yml` (audit only; fix only what the
  audit finds), `tests/create-release.Tests.ps1`
- **Details**: Add explicit text-presence Pester assertions that
  `create-release.ps1` and `.github/prompts/cg-release.prompt.md` (once
  rewritten in Phase 4) contain no `gh release create`, no release-API tag
  creation (`POST .../git/refs` or `releases` used for tag creation), and no
  Release delete/PATCH rollback path — and that failure handling routes to
  read-only reconciliation plus `--resume`. Audit the script and workflow
  family (`release-controller*.yml`, `release-legacy-authority.ps1`) for any
  remaining classic `/branches/{branch}/protection` reads beyond the
  documented-and-banned comment; fix any found to use the active rulesets via
  `Get-CgRepositoryRuleset`. Keep the existing no-classic-endpoint guard
  green.
- **Test Scenarios**: text scans find zero fallback commands (happy); the
  banned-endpoint guard stays green after edits (regression); any audited
  workflow endpoint changes keep `test_release_gate_targets.py` /
  `test_release_policy.py` green (edge).
- **Tests**: Pester text-presence assertions; existing ruleset and
  no-classic-endpoint guards; relevant Python tests if workflow files
  change.
- **Acceptance criteria**: audit documented in the work report with a
  pass/fixed list; all guards green.

### 5. Pre-publication docs-contract sync gate (stable releases)
- **Requirements**: R4, R5
- **Files**: `create-release.ps1`, `tests/create-release.Tests.ps1`,
  `scripts/tests/test_release_policy.py` (re-scope)
- **Details**: Add a stable-only pre-tag gate (three-component tags on main;
  prereleases skip it entirely under Option A). It must verify, read-only:
  (a) the tag commit contains origin/main's tip
  (`git merge-base --is-ancestor origin/main <head-commit>`), and (b) the
  artifact contract of the tag commit's `release-docs.yml` is verifiable by
  origin/main's `release-pages.yml` — the layouts the controller accepts
  (`site`/`docs` dual-layout conditions) must cover the layout the producer
  uploads (`docs/` + `.docs-build-metadata.json`). Fetch both files at the
  exact refs and compare the layout expectations (a small YAML/text
  comparison; no execution of workflow content). On mismatch, halt before
  tag creation with a concrete remediation message: "sync the protected
  controller on main first" or "merge main into dev first", stating which
  file and which expectation differs. Reserve runs this gate before the tag
  push for stable tags; the prompt (Phase 4) also runs the same checks
  pre-tag so failure surfaces before Reserve. Because
  `scripts/tests/test_release_policy.py` currently asserts that
  `merge-base --is-ancestor origin/main HEAD` does NOT appear in the prompt
  or the script, re-scope those negative assertions to the prerelease path:
  the lineage check text must exist only inside the stable-only gate
  (guarded by the three/four-component branch), never on the prerelease
  path.
- **Test Scenarios**: in-sync controller/producer passes (happy); stale
  controller layout expectation halts with remediation naming main (error);
  tag commit missing origin/main tip halts with the merge instruction
  (error); four-component prerelease skips the gate (edge).
- **Tests**: offline-mocked Pester with fixture copies of the two workflow
  files (in-sync and stale variants) and branch-topology mocks; re-scoped
  `test_release_policy.py` negative assertions.
- **Acceptance criteria**: Pester green; halts carry the exact remediation
  strings; `test_release_policy.py` green with re-scoped assertions.

## Phase 3: Option A docs contract

### Governing clarification: 2026-09-17

The user clarified: "The only thing I want is that we can ONLY deploy official
releases in deployment branches or default branch (like main). These releases
are of the form x.y.z. Any other pre-release, of the form x.y.z.<build> can be
deployed from any branch, including dev. That's all. Do whatever is needed to
make that the case."

This clarification supersedes the hardcoded main/dev source-branch matrix and
the requirement to merge a main controller PR during Phase 3. Release source
eligibility is separate from the protected default-branch control plane and
from the documentation destination. Stable source branches are the remotely
configured deployment branches plus the current remote default branch;
prerelease source branches may be any verified same-repository remote branch.
Keep exact commit, tag, clean-tree, authority and required-check protections.
Do not introduce a stable-release branch override. Do not enable the disabled
async controller.

Extend step 6 locally to remove the main/dev source restriction in the legacy
publication and tag documentation-build paths. Use explicit source-branch
identity where tag events or detached checkouts cannot determine it; do not
infer authority from a local branch name or source-controlled policy alone.
Use the protected remote policy's `production_branches` for deployment branches
and the remotely discovered default branch. Reject malformed policy and unknown
remote branches. The stable docs-contract comparison must read the exact
protected default controller rather than hardcoded origin/main; source lineage
checks must not force a configured deployment branch to contain the current
default tip merely to select its controller. Preserve conservative artifact
contract verification.

Additional allowed implementation/test surfaces, only as required by this rule:
`scripts/release-legacy-authority.ps1`, `scripts/release-version.js`,
`scripts/legacy-pages.js`, `.github/workflows/release-docs.yml`, and their existing
tests, including `scripts/tests/test_release_policy.py` and
`scripts/tests/test_release_gate_targets.py`. Update policy documentation and
prompt contracts in Phase 4; do not execute Phase 4 in this run. Add executable
tests for stable default/configured branches, rejection of stable feature
branches, acceptance of prerelease feature/dev branches, malformed remote
policy and branch/SHA mismatch. Keep stable full-chain regression coverage.

Option A remains a documentation destination policy: prereleases require their
tag build, not a full-site Pages deployment; the existing `/dev/` preview remains
dev-specific. This does not prohibit publication of prereleases from other
branches or promise a preview site for each branch.

Phase 3 requires executed local tests and independent review. Remote submission
stays at pipeline step9, followed by protected activation and verification. No
commit, push or PR is authorized during this local phase. Record the actual
control-plane activation path and PR URLs at that later stage; default-branch
workflow execution does not mean release source branches must be the default.
No live deployment or whole-plan completion may be claimed before V13 passes.

Phase 3 review repair clarification (2026-09-17): ordinary previews must remain
valid after producer artifact expiry, more than 100 later workflow runs, and
source-branch payload advancement. Reuse the existing strict docs snapshot
envelope and inventory format, but not the disabled async controller's registry
or write credentials. The protected official Pages deployment seals its exact
official bytes into `cg-official-snapshot.json` inside the same deployed site.
Previews retrieve that durable state from the repository's verified HTTPS Pages
origin, authenticate its publisher against the current successful protected Pages
environment deployment, preserve its official snapshot, and replace only dev
content and publisher metadata. Historical snapshot reuse does not run the new
deployment's current-payload selection gate. Only the existing successful official
Pages deployment changes official state; no new publisher, state branch, Release
asset mutation, token scope, or remote configuration write is introduced.

This repair adds `scripts/legacy-official-snapshot.js`, reuses
`scripts/docs-snapshots.js` and `scripts/snapshot-data.js` without enabling the
async controller, and updates existing preview tests. Require positive expiry,
history-independence and branch-advance cases, sequential official-byte
preservation, and negative corrupt/stale/foreign publisher cases. V13 includes an
authorized protected official deployment to seed the durable format and then a
preview verification; never infer missing initial state from main or waive this
activation evidence. The publicly served state contains only already-public docs
bytes and release/controller provenance.

### 6. Controller skip, /dev/ preview filter, prerelease Finalize chain
- **Requirements**: R4
- **Files**: `.github/workflows/release-pages.yml`, `.github/workflows/pages.yml`,
  `create-release.ps1` (Finalize chain), `tests/create-release.Tests.ps1`
- **Details**:
  (a) `release-pages.yml` `deploy` job: add a prerelease-skip condition so
  four-component prerelease tags (classified via `release-version.js
  --legacy-docs-branch` / `parseReleaseTag` semantics, or the tag shape
  carried by `workflow_run.head_branch`) do not deploy the full site; keep
   stable behavior identical. Protected controller activation is deferred to
   pipeline submission/verification under the governing clarification above.
  (b) `/dev/` preview refresh: add `releases/**` to `pages.yml`'s push path
  filter. `pages.yml` ("Deploy documentation site") is the operative
  dev-preview builder: it triggers on dev pushes, uploads
  `legacy-dev-docs`, and its run triggers the `deploy-dev` job in
  `release-pages.yml`. Do NOT edit `docs-site-build.yml` for this purpose —
  its `combined-docs-site` artifact has no deploy consumer. Do not add the
  attestation path (`.github/shared/**`) to the filter: attestation files
  are not docs content.
  (c) `create-release.ps1` Finalize: for four-component prerelease tags,
  require only the successful `release-docs.yml` push run at the tag SHA
  (`-BuildRunId`); do not require a `release-pages.yml` controller run
  (there is none for prereleases under Option A, and
  `Assert-CgLegacyDeployment` would correctly fail — it must not run on the
  prerelease path). Stable tags keep the full chain (build run + controller
  run + existing deployment assertions). The attestation content is
  unchanged — `cg_release_attestation.py` takes only `--root`, `--tag`,
  `--review-reference`, `--check`; the chain check lives in
  `create-release.ps1`, and no attestation schema change is in scope.
  (d) Re-derive existing Finalize Pester assertions: the offline-mock
  fixture uses the four-component tag `v1.2.0.9015`
  (`tests/create-release.Tests.ps1` line 415). The `It` blocks that expect
  prerelease Finalize to require the pages chain — "requires successful
  Pages and leaves the pair intact", "rejects a successful controller from
  another build or workflow", "finalizes the exact successful chain" —
  change to BuildRunId-only expectations. Build a stable-tag fixture
  (extend the existing fixture pattern, e.g. lines 806-819 and 421-428,
  with main-branch lineage mocks, `Protect main` ruleset path, and
  `prerelease=false` metadata) and move the full-chain regression
  expectations onto it.
- **Test Scenarios**: prerelease Finalize succeeds with BuildRunId-only and
  no PagesRunId (happy); prerelease Finalize with a stale/failed build run
  still halts (error); stable Finalize keeps requiring both runs and the
  deploy-job assertions (regression, stable fixture); `pages.yml` filter
  includes `releases/**` (edge).
- **Tests**: offline-mocked Pester for the Finalize chain branch (re-derived
  + new stable fixture); `python -m pytest scripts/tests/test_release_gate_targets.py`
  if workflow references are asserted there; note in the work report that
   workflow activation remains pending until submission/verification.
- **Acceptance criteria**: local Pester and relevant Python/workflow tests green,
   including source-branch policy cases, the re-derived Finalize suite and stable
   fixture; independent review complete. Record remote activation as pending V13,
   not as a passed or waived check.

## Phase 4: Prompt rewrite and target regeneration

### 7. Rewrite `.github/prompts/cg-release.prompt.md`
- **Requirements**: R1, R2, R3, R5
- **Files**: `.github/prompts/cg-release.prompt.md`,
  `tests/prompt-tools.Tests.ps1`, `tests/docs-automation.Tests.ps1`,
  `scripts/tests/test_cg_pr_preflight.py`,
  `scripts/tests/test_release_policy.py`,
  `scripts/tests/test_release_gate_targets.py`, generated targets (via
  regeneration, step 8)
- **Details**: Restructure the legacy process while preserving every guard:
  - **Step 0.5 (new)**: parse `--auto-approve` before any tool dispatch.
    Reject it for three-component stable tags (stable always interactive).
    Record `<auto-approve>` for all later steps.
  - **Step 1a**: add the precise stranded-payload repair instruction when
    the newest payload has no published tag/Release. The exact sequence:
    (1) confirm the payload's target tag has no local or remote annotated
    tag, Release, or attestation; (2) the maintainer decides either to
    complete the release — create the annotated local tag at the merged
    payload commit, then run `/cg-release <tag> --resume` (which requires
    the existing annotated tag) or a fresh Reserve — or to retire the
    payload through a reviewed revert PR; (3) never auto-publish, never
    create the tag on the flow's own initiative.
  - **Step 1d/1f/Step 4 pauses**: under `--auto-approve`, print the warning
    and the semver/name/notes summary and continue; the summary remains the
    publication decision point — under `--auto-approve` that decision is
    pre-approved by the invocation. Without it, all current pauses stay.
  - **Payload PR (after the publication decision only)**: create
    `release/vX.Y.Z.<build>-payload` from the release-branch tip, commit the
    two payload files, push `--no-follow-tags`,
    `gh pr create --body-file`, then `gh pr merge --auto --rebase`
    (prerequisite: R6 settings). The rebase method preserves the PR-head SHA
    as the dev tip when dev has not advanced. Add a bounded observation
    poll of the PR's checks: report status; the poll bound is a named
    constant at or above worst-case CI duration (e.g. 60 minutes); on a
    failed required check, halt and print the PR URL; on poll expiry with
    checks still pending, blocked-stop with the PR URL and a state report;
    never admin-merge, never bypass, never blind-retry.
  - **Sequencing change (overlap design)**: immediately after the payload
    commit exists on the PR branch, run the full gate exactly once at that
    PR-head commit IN PARALLEL with PR CI, in an isolated LF clean clone
    (same temp-clone conditions as today's Reserve re-run:
    `core.autocrlf=false`, `core.eol=lf`), emitting the receipt to the
    system temp directory. After auto-merge completes, fetch and verify
    that `origin/dev` tip equals the gated PR-head SHA: if equal, the
    receipt binds the release commit — proceed; if not equal (dev advanced
    and GitHub rebased), re-run the full gate exactly once at the actual
    dev tip with a fresh receipt — a single conditioned re-execution, not a
    blind retry — and proceed with that receipt. CI covers the PR head; the
    receipt proves the release commit; the tag stays gated on a passing
    receipt. Pass the receipt to Reserve and Finalize via
    `-PreflightReceipt`.
  - **Reserve/Finalize**: unchanged invocation plus `-PreflightReceipt`;
    keep the annotated-tag creation block; keep `release-result.txt` as the
    immediate channel but add: if absent or stale, re-verify the pair state
    read-only (gh API via the script's resume path) instead of failing on
    the missing file.
  - **Docs wait (Step 5.8) and Finalize call (Step 6), prerelease/stable
    branch**: for four-component prereleases, wait only for the successful
    `release-docs.yml` push run at the tag SHA and call Finalize with
    `-BuildRunId <build-id>` only — no `release-pages.yml` controller wait
    and no `-PagesRunId` (none exists under Option A). For stable tags,
    keep the current full chain: wait for the release-docs run AND the
    successful `release-pages.yml` `workflow_run` controller, call Finalize
    with both `-BuildRunId` and `-PagesRunId`. Both arms get contract-test
    assertions.
  - **Evidence step**: after Finalize, run `cg_generate_targets.py --all`,
    commit the canonical attestation and regenerated targets to the
    evidence branch, open the evidence PR with the same automation
    (`--body-file`, `gh pr merge --auto`), and observe its checks with the
    same bounded poll. No separate local full gate at the evidence commit:
    the evidence PR's required checks (R6) provide GitHub-enforced
    verification, and the evidence commit differs from the tag commit only
    in attestation bytes and generated copies. State this explicitly in
    the prompt text (it replaces the current "required Python tests,
    canonical safe Pester, and native preflight" evidence-step block).
  - **Sync detection**: before the tag, detect whether origin/main advanced
    past the commit the release branch contains; under Option A this is a
    stable-release concern (the sync gate from step 5 halts on it); for
    prereleases report it as informational hygiene. When required (stable),
    open and auto-merge the main-to-dev sync PR with the same automation.
  - **Resume**: `--resume <tag> --auto-approve` reconciles and continues
    non-interactively; without the flag, the current confirmation stays.
  - **Rules section**: add the single-writer rules (no fallback, no
    release-API tag creation, no delete/PATCH rollback, bounded draft-race
    reconciliation, payload PR only after publication decision).
  - **Assertion surfaces (five, all listed)**:
    (1) `tests/prompt-tools.Tests.ps1` — keep every guard string; add
    independent-arm assertions for the new text (Step 0.5, stable rejection
    of `--auto-approve`, `--body-file`, `--auto --rebase`, the poll
    halt/expiry text, the receipt pass-through, the stranded-payload
    sequence, the no-fallback rules); test each alternation arm separately
    per the Pester-skill anti-pattern rules.
    (2) `tests/docs-automation.Tests.ps1` — re-derive the order-sensitive
    `IndexOf` sequence for the implemented step order: payload -> validate ->
    commit -> gate+receipt (parallel with PR CI) -> PR auto-merge -> local tag
    and ruleset checks -> Reserve (publishes tag and Release) -> docs wait
    (branch by tag shape) -> Finalize -> evidence PR. Reserve remains the
    executable publication owner and must appear before the docs wait.
    (3) `scripts/tests/test_cg_pr_preflight.py` — keep
    `test_release_prompt_requires_blocking_budget_and_no_blind_retry` green
    (the blocking budget and no-blind-retry language stays in the prompt).
    (4) `scripts/tests/test_release_policy.py` — re-scope the negative
    main-lineage assertions to the prerelease path (the lineage text is
    allowed only inside the stable-only gate).
    (5) `scripts/tests/test_release_gate_targets.py` — re-derive
    `test_release_prompt_requires_gate_before_execute` for the new gate
    position: the authoritative-gate text now sits after the payload-PR
    step; the invariant becomes "the complete native preflight text appears
    before the tag-creation and Reserve steps".
- **Test Scenarios**: all five surfaces green with kept/re-scoped/re-derived
  assertions (happy); every existing guard string still present verbatim
  (regression); prerelease and stable docs-wait arms both asserted
  (branch).
- **Tests**: the five assertion surfaces above, executed per the Testing
  Strategy.
- **Acceptance criteria**: all five surfaces green; every guard list item
  still present verbatim in the prompt.

### 8. Regenerate targets and enforce drift
- **Requirements**: R8
- **Files**: generated trees `.kilo/commands/cg-release.md`, `.claude/`,
  `.agents/`, `.opencode/` equivalents (via script, not hand-edits)
- **Details**: run `python scripts/cg_generate_targets.py --all`; commit the
  regenerated targets together with the canonical prompt change in the same
  PR. Do not weaken drift checks.
- **Test Scenarios**: regeneration produces no unexpected diff beyond the
  prompt change (happy); `test_target_drift.py` green (regression).
- **Tests**: `python -m pytest scripts/tests/test_target_drift.py`
- **Acceptance criteria**: drift test green with regenerated targets
  committed.

## Phase 5: Flake, settings verification, measurement, acceptance

### 9. Root-cause the phase5 transport flake
- **Requirements**: R7
- **Files**: `packages/cg-release/tests/test_phase5_transport.py` (and the
  fake transport helpers it uses)
- **Details**: Time-boxed root-cause of
  `test_lost_response_and_unreadable_observation_remain_unknown_until_fresh_recovery
  [asset-package.whl]` failing once on macos-latest-py3.11 with
  E_PROCESS_ARGUMENT in the shared `prepare()` helper. Suspects: process
  ordering or seed/time-dependent variance in the strict fake transport
  (`world.run`, `world.wall_time` monkeypatching). Approach: audit the
  helper's state-machine steps for order dependence, make any time/seed
  inputs explicit and deterministic, and run the test repeatedly
  (platform-available loops) to confirm stability. If root-cause stays
  inconclusive after the time-box, quarantine with a documented skip marker
  (reason + failure signature + run link) — never a silent skip.
- **Test Scenarios**: repeated runs of the test pass deterministically
  (happy); quarantine, if used, carries the documented reason (error
  fallback).
- **Tests**: `python -m pytest packages/cg-release/tests/test_phase5_transport.py`
  (repeated; platform-dependent) and the package matrix in CI.
- **Acceptance criteria**: fix merged or documented quarantine recorded in
  the work report; the package matrix stops blocking merges on this noise.

### 10. Settings verification, full matrix, measurement, acceptance run
- **Requirements**: R1, R2, R3, R4, R6, R9
- **Files**: `.cg-docs/work-reports/2026-09-16-cg-release-prerelease-automation.md`
- **Details**: (a) Verify read-only via `gh api`: `allow_auto_merge` true;
  "Protect dev" carries the five required checks (exact contexts from
  "Protect main"). These are maintainer UI actions — record who/when in the
  work report; if unavailable, this is a blocked-stop. (b) Run the full
  matrix: `tests\Run-Tests.ps1` (canonical Pester, results from
  `tests/last-run.json`), required Python tests
  (`scripts/tests/`, `packages/cg-release/`), and the native preflight.
  (c) Record stage timings from `-Timing` output and the before/after
  comparison (before: the measured 3h+ / 4-run session data from the
  brainstorm; after: the actual run), segmented per the Option A targets:
  payload commit to published+attested, and invocation to evidence merged.
  (d) Acceptance run: with maintainer authorization, execute
  `/cg-release v1.2.0.9020 --auto-approve` from a clean dev checkout and
  record zero pauses, exactly one full preflight, auto-merged
  payload/evidence PRs, successful docs chain (prerelease path:
  release-docs build; `/dev/` refresh via `pages.yml`), Finalize
  attestation, and the segmented timings: payload commit to
  published+attested at or under 45 minutes; invocation to evidence merged
  at or under 90 minutes.
- **Test Scenarios**: settings verified (happy); missing settings →
  blocked-stop with exact remediation (error); either segmented target
  missed → record the stage breakdown and continue analysis before
  declaring done (edge — outcome not met).
- **Tests**: full Pester suite via `tests\Run-Tests.ps1` + `tests/last-run.json`;
  required Python tests; the measured run itself.
- **Acceptance criteria**: work report contains the verification table, the
  settings record, the segmented timing records, and the acceptance-run
  evidence matching the acceptance criteria.

## Testing Strategy

- Pester: only through `tests\Run-Tests.ps1` (full or `-File`), results read
  from `tests/last-run.json`; never compose raw `Invoke-Pester`; load
  `cg-skill-pester-safety` before any test command; independent-arm regex
  assertions in `prompt-tools.Tests.ps1` (test each alternation arm
  separately).
- Python: `python -m pytest scripts/tests/test_cg_pr_preflight.py`,
  `test_target_drift.py`, `test_release_gate_targets.py`,
  `test_release_policy.py` as touched; `packages/cg-release` matrix for the
  flake.
- Offline-mocked Pester for `create-release.ps1` behavior (receipt skip,
  draft race, sync gate, Finalize chain) following the existing
  "executable two-phase publication with offline mocks" pattern, including
  the new stable-tag fixture.
- All five prompt-rewrite assertion surfaces (`prompt-tools.Tests.ps1`,
  `docs-automation.Tests.ps1`, `test_cg_pr_preflight.py`,
  `test_release_policy.py`, `test_release_gate_targets.py`) run after every
  prompt-revision step in Phase 4.
- The native preflight gate itself validates the final state
  (`--phase committed --full-gate --run-native-target`).
- The acceptance run (V12) is the live end-to-end test under maintainer
  authorization.

## Documentation Checklist

- [ ] Rewritten `cg-release.prompt.md` documents `--auto-approve`, the PR
      automation (rebase method, bounded poll with expiry semantics), the
      receipt flow, the prerelease/stable docs-wait branch, the evidence-step
      required-checks reliance, and the stranded-payload repair sequence
- [ ] `docs/` reference pages covering `/cg-release` updated if they describe
      the flow (check `docs/reference.md` and workflow pages)
- [ ] Work report in `.cg-docs/work-reports/` with before/after segmented
      timings
- [ ] Brainstorm cross-links remain intact (plan frontmatter)
- [ ] No charter update required beyond the optional docs-deployment note
      (surfaced to the maintainer at brainstorm handoff)

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Required-check contexts on dev differ from expected names → auto-merge merges early or never | Medium | High | Verify exact contexts via rulesets API before enabling (V10); the bounded poll also observes checks; halt on unknown check state |
| Main PR for `release-pages.yml` rejected or delayed | Medium | High | Blocked-stop per contract; Option B (automated sync gate) remains the documented fallback design if maintainer reverses |
| Receipt bypass is abused to skip a needed re-run (e.g. dirty tree tricks) | Low | High | Receipt binds commit AND tree SHA AND LF provenance; any mismatch re-runs the gate; fail-safe only; Pester covers tamper cases |
| Dev advances during payload PR → rebase merge rewrites the SHA, invalidating the parallel gate | Medium | Medium | Post-merge verification: if dev tip != gated SHA, one conditioned full re-run at the actual tip with a fresh receipt (never blind); receipt verification in Reserve also fails safe |
| Draft-race bound too short for GitHub list propagation | Medium | Medium | Bounded loop with re-read; persistent disagreement keeps the halt; Finalize re-verifies the settled pair |
| Prompt rewrite breaks existing contract tests or guards | Medium | Medium | All five assertion surfaces listed with keep/re-scope/re-derive decisions (step 7); run them after every prompt-revision step |
| Segmented timing targets missed (45/90 min) due to CI variance | Medium | Medium | Overlap design maximizes parallelism; measure stage timings; record breakdown and continue analysis — outcome requires the targets |
| Flake quarantine masks a real transport bug | Low | Medium | Quarantine only after time-boxed root-cause, with failure signature documented |

## Out of Scope

- Enabling the async release controller (stays disabled under
  `D-2026-09-13-defer-live-rollout`)
- Worktree auto-delete hygiene tooling (tracked as roadmap idea in Ongoing
  Ideas)
- Consumer-project behavior; this prompt is developer-only for compound-gpid
- Stable-release flow redesign beyond keeping it interactive with manual
  merges
- Attestation schema changes (`cg_release_attestation.py` content is
  unchanged; the chain check lives in `create-release.ps1`)
- Attestation for v1.2.0.9018 (permanent documented deviation) or the
  withdrawn v1.2.0.9014
- `.gitignore` changes (receipts live outside the working tree)

## Completion Contract

### Outcome

`/cg-release <tag> --auto-approve` from a clean dev checkout publishes,
attests, and evidence-commits a four-component prerelease with zero
interactive pauses and exactly one full preflight per commit, using the
overlap design (rebase auto-merge; gate parallel with PR CI; evidence
verification via evidence-PR required checks), with the measured window
from payload commit to published+attested at or under 45 minutes and the
full flow from invocation to evidence merged at or under 90 minutes; stable
releases keep interactive confirmation and manual merges; no publication
fallback path exists in the prompt or the script.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | `--emit-receipt` emits valid canonical JSON with digest and LF provenance on a green full gate in an isolated LF clone; failing/interrupted gates emit no receipt | `python -m pytest scripts/tests/test_cg_pr_preflight.py` | yes |
| V2 | 2 | `-PreflightReceipt` skips the temp-clone re-run on exact commit/tree SHA + LF provenance + digest match; invalid/absent receipt keeps current behavior | `tests\Run-Tests.ps1 -File create-release.Tests.ps1` + `tests/last-run.json` | yes |
| V3 | 2 | Draft-race disagreement reconciles read-only within the bound and accepts a settled consistent pair; injectable constants keep the suite fast | offline-mock Pester assertions | yes |
| V4 | 2 | No `gh release create`, release-API tag creation, or Release delete/PATCH surface in prompt or script; classic-protection audit clean | text-presence Pester + audit record in work report | yes |
| V5 | 2 | Stable pre-tag sync gate halts on controller/producer mismatch or missing main-tip lineage with concrete remediation; `test_release_policy.py` negative assertions re-scoped | offline-mock Pester + `python -m pytest scripts/tests/test_release_policy.py` | yes |
| V6 | 3 | Local source-branch policy matches the governing clarification; `release-pages.yml` skips prerelease full-site deployment; `pages.yml` includes `releases/**`; prerelease Finalize accepts BuildRunId-only; stable full-chain fixture and independent review pass | `tests\Run-Tests.ps1` + relevant Python/workflow tests + review ledger | yes |
| V13 | final | Protected source policy and controller/producer changes activated through reviewed submission; record PR URLs, exact deployed revisions and successful branch-policy/docs-chain verification. No activation claimed from local tests | pipeline step9 submission and subsequent remote verification recorded in work report | yes |
| V7 | 4 | Prompt contains Step 0.5 `--auto-approve`, rebase auto-merge automation, bounded poll with expiry semantics, gate-parallel-with-CI receipt flow, prerelease/stable docs-wait branch, evidence-step required-checks reliance, stranded-payload repair sequence, non-interactive resume; all five assertion surfaces green | `tests\Run-Tests.ps1 -File prompt-tools.Tests.ps1`, `tests\Run-Tests.ps1 -File docs-automation.Tests.ps1`, `python -m pytest scripts/tests/test_cg_pr_preflight.py scripts/tests/test_release_policy.py scripts/tests/test_release_gate_targets.py` | yes |
| V8 | 4 | All adapter targets regenerated; no drift | `python scripts/cg_generate_targets.py --all` + `python -m pytest scripts/tests/test_target_drift.py` | yes |
| V9 | 5 | Flake root-caused: deterministic fix merged, or documented quarantine with reason | repeated `packages/cg-release` test runs / quarantine note in work report | yes |
| V10 | 5 | `allow_auto_merge=true` and "Protect dev" carries the five required checks (maintainer UI actions, verified read-only) | `gh api repos/GPID-WB/compound-gpid` + rulesets read, recorded in work report | yes |
| V11 | final | Full test matrix green; measured before/after segmented timing record committed | `.cg-docs/work-reports/2026-09-16-cg-release-prerelease-automation.md` + `tests/last-run.json` | yes |
| V12 | final | One maintainer-authorized prerelease via `--auto-approve`: zero pauses, one full preflight, auto-merged payload/evidence PRs, successful docs chain, attestation; measured payload commit → published+attested ≤ 45 min AND invocation → evidence merged ≤ 90 min | segmented timing records from the actual run in the work report | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | all | Tag immutability; never move/delete a protected tag | script guards + Pester |
| C2 | all | Ruleset verification incl. PR #173 ruleset-based authority unchanged | existing Pester guards stay green |
| C3 | all | Stable three-component releases only from configured deployment branches or remote default; four-component prereleases from any verified same-repository remote branch | executable branch-policy tests + prompt text |
| C4 | all | Payload byte-identity preserved | `generate-whats-new.js` validations |
| C5 | all | `make_latest:"false"` on every reservation | Pester |
| C6 | all | `RELEASE_NOTES.md` stays ephemeral and gitignored | prompt text |
| C7 | all | `gh pr create/edit` uses `--body-file` only | prompt-contract assertions |
| C8 | all | Pester only through `tests\Run-Tests.ps1`, results from `tests/last-run.json`; never raw `Invoke-Pester` | `pester-safety.Tests.ps1` + practice |
| C9 | all | No shared commit/push/PR before pipeline step9; integration targets dev. Any required protected default-controller activation is justified and recorded separately from source-branch eligibility, without bypassing protected checks | submission/activation record and PR list in work report |
| C10 | all | Async controller stays disabled; no enablement anywhere | `.release-controller.json` unchanged |
| C11 | all | v1.2.0.9018 stays published-but-unattested; no attestation created for it or v1.2.0.9014 | existing script guard stays |
| C12 | all | No receipt or transient artifact inside the working tree (clean-checkout guard intact) | Reserve/Finalize clean-tree checks + Pester |

### Boundaries

- Allowed: `.github/prompts/cg-release.prompt.md` plus regenerated adapter
  targets; `scripts/cg_pr_preflight.py`; `create-release.ps1`;
  `scripts/release-legacy-authority.ps1` (audit fixes);
  `.github/workflows/release-pages.yml` and `.github/workflows/pages.yml`
  as specified; `tests/create-release.Tests.ps1`,
  `tests/prompt-tools.Tests.ps1`, `tests/docs-automation.Tests.ps1`,
  `scripts/tests/test_cg_pr_preflight.py`, `test_target_drift.py`,
  `test_release_gate_targets.py`, `test_release_policy.py`,
  `packages/cg-release/tests/test_phase5_transport.py`; receipt files under
  the system temp directory (outside the working tree);
  `.cg-docs/plans|work-reports` artifacts; roadmap writes via `@cg-roadmap`.
- Out of scope: enabling the async release controller; worktree auto-delete
  tooling; consumer projects; stable-flow redesign beyond interactive
  confirmation and manual merges; attestation schema changes; `.gitignore`
  changes; attestation for v1.2.0.9018/9014; `docs-site-build.yml` edits.

### Iteration Policy

1. Deviation policy is `ask` — pause before any deviation and record the
   decision and impact.
2. A failing test is fixed and rerun; skip markers only with a documented
   quarantine.
3. An invalid preflight receipt fails safe: the script re-runs the full
   gate; it never fails open.
4. The flake root-cause is time-boxed; quarantine is a documented last
   resort.
5. The post-merge SHA-mismatch re-run is a single conditioned re-execution
   with a fresh receipt; it is not a blind retry and happens at most once
   per release.

### Blocked-Stop Conditions

- Defaults per `.kilo/shared/goal-execution.contract.md` (safe runner
  unavailable; required evidence failing after recovery; unapprovable
  deviation under `ask`; protected boundary crossing; report write failure;
  static-inspection-only evidence).
- Maintainer repo-settings actions unavailable (blocks V10 and the
  auto-merge design).
- Required protected controller activation is unavailable or rejected (blocks
   V13 and live acceptance, not local Phase 3 verification).
- Required-check contexts on dev do not exist under the expected names
  (auto-merge would not be GitHub-enforced; stop and report instead).
- The bounded poll expires with checks still pending, or a required check
  fails on any automated PR (report the PR URL and state; stop).
