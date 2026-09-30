---
date: 2026-09-16
title: "cg-release prerelease automation: zero-pause flow under 45 minutes"
status: decided
scope: "Deep"
artifact-schema-version: 1
chosen-approach: "Prompt-automated prerelease pipeline with preflight receipts, GitHub-enforced auto-merge, and stable-only full docs deployment"
tags: [release, automation, prerelease, cg-release, create-release, preflight-receipt, auto-merge, docs-deployment, latency, pester]
---

# cg-release Prerelease Automation: Zero-Pause Flow Under 45 Minutes

## Context

The v1.2.0.9018/9019 release sessions (2026-09-15/16) measured the prerelease
pipeline at over 3 hours wall-clock with four-plus interactive pauses. Measured
problems, all observed first-hand:

1. The native preflight (~33 minutes) ran three to four times against the same
   commit: at the Step 4 summary gate, inside `create-release.ps1` Reserve,
   inside Finalize, and again in the evidence step.
2. Interactive pauses: semver confirmation (Step 1f), publication summary
   (Step 4), resume confirmation, and every PR merge.
3. The payload PR cycle is manual: branch, push `--no-follow-tags`,
   `gh pr create`, wait for CI, ask the maintainer to merge, fetch, verify tip.
   Same again for the evidence PR, plus a routine main-to-dev lineage sync PR.
4. `Assert-CgLegacyAuthority` read the classic `/branches/main/protection`
   endpoint, which returns 404 on ruleset-protected repos. Fixed by PR #173
   (ruleset-based authority). The workflow family audit for remaining
   classic-protection assumptions is still open.
5. That 404 forced a `gh release create` fallback that produced a lightweight
   remote tag with `target_commitish="dev"` - permanently unattestable and
   unfixable (protected tag). Correction required v1.2.0.9019, a payload PR, a
   main-to-dev sync PR (#175), and hours of rework. Reserve fallbacks must be
   impossible.
6. Docs contract skew: origin/main's `release-pages.yml` controller was stale
   relative to the tag commit's `release-docs.yml` producer (layout `site/` ->
   `docs/`); v1.2.0.9018 deployment failed with ENOENT. Fixed by PR #172
   (dual-layout bridge) and #175 (lineage sync). Nothing detects this skew
   before publication.
7. Publication draft race: while Reserve's 33-minute preflight ran, a parallel
   publication of the same tag went live. The by-tag lookup found it, the
   paginated list did not, and Reserve threw "Conflicting GitHub Release lookup
   and list". Finalize later verified the final pair and succeeded.
8. One CI flake: `packages/cg-release/tests/test_phase5_transport.py::
   test_lost_response_and_unreadable_observation_remain_unknown_until_fresh_recovery
   [asset-package.whl]` failed once on macos-latest-py3.11 (E_PROCESS_ARGUMENT
   in the shared `prepare()` helper) while passing in four other runs.
9. Sequencing hazard: the payload PR was opened before the publication
   decision. A payload merged without its tag blocks the next release
   (Step 1a halts on the newest payload having no published tag/Release).
10. Hygiene: merged worktrees with uncommitted WIP must never be auto-deleted
    (tracked as a separate roadmap idea); `release-result.txt` is a transient
    local channel - the durable records are the GitHub pair, the committed
    payload, and the committed attestation.

Verified facts at brainstorm time: `create-release.ps1` requires
`-LegacyOperation Bridge|Recovery`; Reserve re-runs the full gate in a temp
clone (lines 348-377) with no receipt mechanism; the draft race throws at
`Get-CgReleaseReservation` (line 544); the PR #173 ruleset fix and its
no-classic-endpoint Pester guard are in place; repo `allow_auto_merge` is
false; ruleset "Protect dev" carries no required status checks while
"Protect main" requires Pester (macos-14, windows-2022), Native target Python
gate (macos-14, windows-2022), and Conventional Commits PR title;
`release-docs.yml` runs the tag commit's own workflow file (not main-resident)
while `release-pages.yml` is the main-resident controller; `releases/**` is not
in the dev-preview path filters; the async release controller stays disabled
under `D-2026-09-13-defer-live-rollout`.

## Requirements

1. **Automate the PR cycle in the prompt.** After the two-file payload commit,
   the prompt itself creates `release/vX.Y.Z.<build>-payload` from the
   release-branch tip, pushes with `--no-follow-tags`, opens the PR with
   `gh pr create --body-file`, observes required checks with a bounded poll
   that only reports and halts on failure with the PR URL, and enables GitHub
   auto-merge (`gh pr merge --auto --merge`). Never bypass, never admin-merge,
   never retry blindly. Apply the same automation to the post-Finalize
   evidence PR and to the main-to-dev sync PR when a sync is required. For
   stable tags on main, open PRs but keep the merge manual.
2. **Add `--auto-approve` (non-interactive mode).** Parsed at a new Step 0.5
   before any tool dispatch. Valid only when the derived tag is a
   four-component prerelease released from dev; rejected for three-component
   stable tags on main (stable releases always keep interactive confirmation
   before Reserve). It pre-approves the semver suggestion, the release name,
   the notes, the payload PR creation, Reserve, Finalize, the automated
   merges, the Step 1d large-scan continuation, and resume. It must never
   skip or weaken: the dev-repo guardrail, clean-tree and tip checks, payload
   schema validation, validate-release-set, ruleset verification, the
   preflight gate itself, annotated-tag identity, `make_latest:"false"`, the
   docs-chain success gates, or protected-branch rules. `/cg-release <tag>
   --auto-approve` from a clean dev checkout must reach a published,
   attested, evidence-committed prerelease with zero interactive pauses.
3. **Kill the redundant preflight runs.** `cg_pr_preflight.py` gains
   `--emit-receipt <path>` writing canonical JSON: commit SHA, tree SHA,
   timestamp, exact command list, per-command exit codes, and a digest over
   those fields. `create-release.ps1` accepts `-PreflightReceipt <path>` in
   Reserve and Finalize: on commit/tree SHA equality with the exact release
   commit and a valid digest, skip the ~33-minute re-run; otherwise keep the
   current behavior. The prompt runs the full gate exactly once per commit
   (Step 4 for the tag commit; a fresh gate for the evidence commit) and
   passes the receipt to Reserve and Finalize. Target: full prerelease under
   45 minutes wall-clock including CI, with the Step 4 gate overlapped
   against payload-PR CI. Record stage timings (`-Timing` exists) and publish
   a measured before/after record in `.cg-docs/work-reports/`.
4. **Docs contract decision (approved Option A).** Full Pages deployment is
   gated to stable three-component releases only. One PR to main (the
   documented contract-mandated exception) makes `release-pages.yml` ignore
   four-component prerelease tags. Prerelease Finalize requires the
   successful tag-run `release-docs.yml` producer build (self-consistent, not
   main-resident) and no main-resident deployment. Add `releases/**` to the
   dev-preview path filters so release commits refresh the `/dev/` site,
   which serves prerelease docs. The pre-publication sync gate
   (controller/producer contract check plus main-tip lineage: the tag commit
   must contain origin/main) applies to stable releases; prereleases no
   longer require the main tip because the main-resident chain leaves their
   path. Halt with concrete remediation instead of publishing a tag whose
   deployment is guaranteed to fail.
5. **Failure-mode hardening (single-writer semantics).** Reserve is the only
   legal publisher. On Reserve or tag-push failure: halt, reconcile
   read-only, report the exact tag/Release pair state, and direct the user
   to `--resume`. No `gh release create` fallback, no release-API tag
   creation, no delete/PATCH of a Release as rollback, anywhere in the
   prompt or the script. Handle the draft race: when the by-tag lookup and
   the release list disagree, re-reconcile read-only with a bounded wait and
   accept a settled consistent pair (EXISTS path); Finalize remains the
   authoritative verifier. Do not open the payload PR until the publication
   decision is confirmed. Step 1a gets a precise stranded-payload repair
   instruction. Add Pester text-presence assertions for these rules. Do not
   depend on `release-result.txt` surviving; re-verify pair state when it is
   absent. Audit the script and workflow family for remaining
   classic-protection assumptions.
6. **Repo settings (maintainer-approved).** Enable Allow auto-merge; add
   required status checks to "Protect dev" mirroring main's set (Pester on
   macos-14 and windows-2022, Native target Python gate on macos-14 and
   windows-2022, PR title follows Conventional Commits; approving reviews
   stay 0). GitHub's own enforcement then blocks red merges; auto-merge
   relies on it.

## Approaches Considered

### Approach 1: Prompt-automated prerelease pipeline with receipts, GitHub-enforced auto-merge, and stable-only full docs deployment (selected)

Automate the legacy prompt flow end-to-end: prompt-owned PR automation with
GitHub auto-merge as the merge authority, a durable preflight receipt so the
full gate runs exactly once per commit, `--auto-approve` scoped to
four-component dev prereleases, single-writer hardening with draft-race
reconciliation, and Option A docs gating that removes main from the
prerelease critical path.

Pros: meets every acceptance criterion; removes the measured 2 hours of
redundant preflight; removes all human round-trips for prereleases; removes
the docs-skew failure class for prereleases entirely; GitHub enforces merge
safety instead of the prompt. Cons: large cross-cutting effort (prompt,
script, preflight runner, tests, one PR to main); prerelease root-site docs
appear only at the next stable release; repo-settings change affects all dev
PRs.

### Approach 2: Keep the controller for every prerelease; guard instead of remove (rejected)

Same pipeline automation, but keep the main-resident controller in every
prerelease path: add the pre-tag controller/producer contract check plus
automated main-to-dev sync, and let the prompt poll CI and merge without repo
settings changes.

Pros: no PR to main now; the public root site updates on every prerelease;
Finalize chain unchanged. Cons: main stays in the prerelease critical path
and a main problem can still block a prerelease; the skew class remains real
(merely caught pre-tag); prompt-polled merges are not GitHub-enforced and can
race; the 45-minute target is harder.

## Decision

Approach 1. The maintainer approved Option A for docs deployment and the two
repo-settings changes. The async release controller (`packages/cg-release`)
stays disabled under `D-2026-09-13-defer-live-rollout`; the prompt automation
must remain compatible with it and must not enable it.

Defaults applied (disclosed, not asked): flake handling is root-cause first
with a documented quarantine only as last resort; `--auto-approve` also
auto-accepts the Step 1d large-scan continuation (warning still printed);
`--resume <tag> --auto-approve` is non-interactive; the evidence commit gets
its own fresh full-gate receipt; the prompt reads `release-result.txt` as the
immediate channel but re-verifies pair state when it is absent.

## Next Steps

Hand off to `/cg-plan` with these concrete actions:

1. Rewrite `.github/prompts/cg-release.prompt.md`: new Step 0.5 argument
   parsing (`--auto-approve`), prompt-owned payload/sync/evidence PR
   automation, pre-tag sync gate for stable releases, stranded-payload
   repair instruction in Step 1a, non-interactive resume under
   `--auto-approve`, and the Option A prerelease Finalize chain. Then
   regenerate all adapter targets (`python scripts/cg_generate_targets.py
   --all`) and keep `test_target_drift` green.
2. `scripts/cg_pr_preflight.py`: add `--emit-receipt` plus tests.
3. `create-release.ps1`: add `-PreflightReceipt` (commit/tree SHA and digest
   verification, skip re-run on valid receipt), draft-race bounded
   read-only reconciliation, no-fallback hardening; update
   `tests/create-release.Tests.ps1` (currently 120 passing) with co-authored
   Pester assertions; run Pester only through `tests\Run-Tests.ps1` with
   `cg-skill-pester-safety` loaded.
4. `release-pages.yml` controller change on main (prerelease-tag skip) and
   `docs-site-build.yml` path-filter addition (`releases/**`).
5. Maintainer settings actions: enable Allow auto-merge; add required checks
   to "Protect dev".
6. Root-cause the item 8 flake in `test_phase5_transport.py`; fix or
   quarantine with a documented reason.
7. Measure and record before/after wall-clock in `.cg-docs/work-reports/`.
8. All PRs target dev, merged only on green required checks; the
   release-pages.yml controller change is the one main exception.
9. Acceptance: `/cg-release v1.2.0.9020 --auto-approve` from a clean dev
   checkout - zero pauses, exactly one full preflight, automated
   payload/sync/evidence PRs auto-merging on green required checks,
   successful docs chain, Finalize attestation, measured wall-clock under
   45 minutes; stable releases keep interactive confirmation and manual
   merges; all tests green (canonical Pester, required Python tests, native
   preflight).

Constraints that stay inviolable: tag immutability; ruleset verification
including the PR #173 ruleset-based authority checks; the branch/tag matrix
(three-component on main, four-component prereleases on dev); payload
byte-identity; protected-branch PR requirements; the durable publication
contract (payload, tag, Release, attestation); the RELEASE_NOTES.md-is-
ephemeral rule; `gh pr create/edit` with `--body-file`; v1.2.0.9018 remains
published but unattested - a permanent documented deviation like the
withdrawn v1.2.0.9014.