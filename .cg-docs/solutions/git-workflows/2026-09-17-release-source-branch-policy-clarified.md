---
date: 2026-09-17
title: "Stable releases deploy only from configured deployment branches or the remote default; prereleases use any verified branch"
category: "git-workflows"
language: "both"
tags: [release, source-branch, branch-policy, production-branches, prerelease]
root-cause: "Hardcoded main/dev source mapping and origin/main lineage checks could neither authorize feature-branch prereleases nor keep stable releases bound to the remotely configured deployment policy."
severity: "P1"
plan: ".cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md"
reviewed-in: ".cg-docs/reviews/2026-09-16-cg-release-prerelease-automation-phase3-review.md"
---

# Release Source-Branch Policy: Official x.y.z From Deployment Branches Or Default; Prerelease x.y.z.N From Any Verified Branch

## Problem

`create-release.ps1` assigned main/dev from tag shape and enforced that
branch's remote lineage; `release-docs.yml` used a helper that returned only
main/dev and checked ancestor membership. That meant feature-branch
prereleases were impossible, while the user's single requirement was: only
official `x.y.z` releases may deploy from deployment branches or the default
branch; prereleases of the form `x.y.z.<build>` may come from any branch,
including dev.

## Root Cause

Source eligibility was encoded as a hardcoded two-branch matrix instead of
the remotely configured deployment policy. Tag events also carry no original
branch name, so authority could not be inferred from the version shape or a
local branch name.

## Solution

- Stable eligibility is the union of the protected remote policy's
  `production_branches` (currently `[main]`) and the current remote default
  branch. Prereleases have no source allowlist beyond "a verified
  same-repository remote branch".
- Trust only the exact protected remote default commit already verified by
  the authority gate — never the source branch's editable policy. Missing
  optional production policy permits only the default for stable tags;
  malformed/null/string arrays, invalid names and duplicate production keys
  fail closed. No stable-release branch override exists.
- Detached checkouts require an explicit `-SourceBranch`; branch names are
  validated as Git refs before use; canonical origin, exact new-tag tip,
  resumed-tag ancestry and immutable tag checks remain.
- `release-version.js` supplies a shared validator (`assertReleaseSource`)
  and a bounded, GET-only remote resolver for tag-build and deployment
  workflows: it selects a permitted remote branch containing the exact
  commit, or verifies an explicit `RELEASE_SOURCE_BRANCH` input. It does not
  infer source from version shape or trust the tag checkout's policy.
  Prerelease enumeration is capped (20 pages of 100 branches); exceeding the
  bound requires an explicit candidate.
- Source policy is refreshed before the Release POST and before final
  attestation; a protected-controller change between contract verification
  and publication stops the attempt.
- Source eligibility is separate from the docs control plane and from the
  docs destination (Option A): prereleases still require their own tag build,
  not a full-site Pages deployment, and the `/dev/` preview remains
  dev-specific.

## Prevention

- Encode source eligibility in shared validators with executable tests
  (stable configured/default branches pass; stable feature branches and
  malformed policy reject; prerelease feature/dev branches pass), never in
  per-script branch-name matrices.
- Keep the version-shape legacy helper for classification only; never use
  its main/dev return value for source authorization.
- Recheck remote policy state read-only at every authority boundary —
  eligibility decided once is not a lease for later publication.
- Any future enablement of the async controller must enforce the same
  clarified rule.

## Related

- `.cg-docs/solutions/git-workflows/2026-09-13-release-controller-authority-and-evidence-boundaries.md`
- `.cg-docs/solutions/git-workflows/2026-09-17-preflight-receipt-commit-tree-lf-provenance.md`
- `.cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md`