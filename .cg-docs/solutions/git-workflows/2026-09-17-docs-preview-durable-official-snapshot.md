---
date: 2026-09-17
title: "Docs previews restore durable official bytes from the protected Pages origin instead of stale build artifacts"
category: "git-workflows"
language: "both"
tags: [docs, deployment, pages, snapshot, preview, provenance]
root-cause: "Preview rebuilds that relied on the original stable build artifact failed after artifact expiry, deep workflow history, or source-branch payload advancement, because official state lived only transiently in the producing run."
severity: "P1"
plan: ".cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md"
reviewed-in: ".cg-docs/reviews/2026-09-16-cg-release-prerelease-automation-phase3-review.md"
---

# Docs Preview Durable Official Snapshot

## Problem

The dev preview refreshed when `release-pages.yml`'s controller deployed the
full site. Pilot review (phase 3, P1.2, P1.4, P1.5) found ordinary previews
broke when the producer artifact expired (retention ~1 day), more than 100
workflow runs intervened, or the source branch's payload advanced — and a
repair that reused main content would break the protected/static-data trust
boundary of the docs chain.

## Root Cause

Official docs bytes existed only transiently in the producing build artifact
and its logs. Any preview path that re-derived official state from history
(artifact lookup, run-window scans, source-branch payloads) was time- and
history-dependent with no durable anchor.

## Solution

- `scripts/legacy-official-snapshot.js` reuses the existing strict docs
  snapshot envelope and static-data format (from `docs-snapshots.js` /
  `snapshot-data.js`) without enabling the disabled async controller or its
  registry. The current protected official Pages job seals
  `cg-official-snapshot.json` (immutable official docs bytes plus
  release/controller provenance) into its existing Pages artifact; the
  existing successful Pages deployment atomically publishes docs and state
  together. No new publisher, state branch, Release asset mutation, token
  scope, or remote configuration write is introduced.
- Previews retrieve the served state from the exact workflow-managed
  repository HTTPS Pages origin returned by GitHub — no custom-domain
  inference, redirects, or credential header — validate its complete strict
  envelope, and authenticate its publisher against the current successful
  `github-pages` environment deployment and the exact protected
  job/run-attempt/controller lineage. Stale served state that does not match
  that current deployment is rejected.
- Previews restore the immutable official bytes as data, compose the new dev
  tree, retain the exact official envelope, update only dev content and the
  publisher tuple, and recheck the fetched state before deployment. They do
  not consult the historical source branch's current payload or current
  production membership.
- The current environment pointer is independent of the original build
  artifact's expiry and of mixed Actions history; an active/pending/failed
  deployment does not replace the last successful pointer.
- New official deployments still run the current-payload/source selection
  checks (P1.3) before sealing new state. Sealing uses the same recovery
  token expression as the initial authority and final recheck (P1.6).
- Safety limit: missing official deployment history in the bounded window,
  expired/deleted producer artifacts, no currently eligible payload-matching
  source, or changed official evidence blocks the preview. There is
  deliberately no fallback to main or an older official artifact.
- Initial seeding requires one authorized protected official Pages
  deployment (plan V13) to establish the durable format, followed by preview
  verification; initial state is never inferred from main.

## Prevention

- Treat official docs bytes as data that must be sealed by the protected
  publisher; any consumer that must survive artifact expiry must read the
  durable sealed state from the verified HTTPS Pages origin, not build logs
  or artifacts.
- Re-authenticate the publisher against the current successful protected
  environment deployment on every preview; reject stale, corrupt, or foreign
  publisher/origin responses.
- Keep snapshot sealing in the same token path as initial authority and
  final recheck; never introduce a separate write authority for state.
- Never fall back to main or older artifacts when evidence is missing —
  block and report.

## Related

- `.cg-docs/solutions/git-workflows/2026-08-13-verified-pages-artifact-and-release-tag-gates.md`
- `.cg-docs/solutions/bugs/2026-08-14-pages-immutable-ref-gate-rejects-dev-series-pre-release-tags.md`
- `.cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md`