---
date: 2026-08-13
title: "Verified Pages artifacts and immutable release-tag gates"
category: "git-workflows"
language: "both"
tags: [github-actions, github-pages, artifact-provenance, immutable-ref, release-tag, action-pinning, documentation]
root-cause: "A Pages deployment path accepted mutable refs and action tags, while rebuild metadata and release inputs were not fully verified before privileged publication steps."
severity: "P0"
---

# Verified Pages Artifacts and Immutable Release-Tag Gates

## Problem

An automated documentation workflow needs two independent guarantees:

1. The Pages deploy job must publish exactly the successful documentation build
   artifact, not regenerate or silently replace it.
2. Tag/manual release deployments must not execute repository code with Pages
   credentials from a mutable branch, dev tag, or arbitrary user input.

Without both controls, an old or unreviewed ref can publish content, a mutable
GitHub Action tag can run privileged code, or a missing metadata file can make
artifact provenance unverifiable.

## Root Cause

The initial workflow treated a tag or dispatch `ref` as immutable because the
input was named that way. It also used action major tags and uploaded hidden
metadata files without explicitly opting into hidden-file artifact upload.
Separately, generated content relied on marker parsing and payload validation
that accepted example markers, symlinked inputs, unrelated release URLs, and a
stale `latest.json` convenience copy.

## Solution

Use a three-part publication contract:

1. Rebuild on `main` from approved canonical inputs, validate the complete
   `docs/` tree, commit only `docs/`, and upload `docs/` plus the metadata file
   with hidden files explicitly included.
2. Deploy the completed main rebuild through `workflow_run`: download by exact
   run ID, verify every file digest, recompute the normalized canonical-input
   fingerprint on current `main`, and upload the downloaded tree unchanged.
3. Put tag/manual resolution in an unprivileged job. Accept only an official
   `vX.Y.Z` tag or a full commit SHA that is an ancestor of `origin/main`; pass
   the resolved SHA to the later Pages-permission job.

Supporting generator controls:

- Pin all privileged actions to reviewed commit SHAs.
- Treat only standalone `cg:auto` markers outside fenced examples as managed.
- Reject symlinked release inputs, require exact repository/tag URLs, require
  `latest.json` to byte-match the newest immutable payload, and keep the
  complete build check non-mutating.
- Emit Git log records with explicit field and record separators so multiline
  release messages preserve `BREAKING CHANGE` footers.
- Resume a partial release only after validating the existing payload, exact
  pushed tag, and tag deployment; never create another immutable payload or
  tag during resume.

## Prevention

1. Never treat a tag-shaped string or dispatch input as immutable until it is
   resolved to a commit and checked against the approved history.
2. Any job with `contents: write`, `pages: write`, or `id-token: write` uses
   SHA-pinned actions and performs only the smallest required work.
3. Artifact provenance must fail closed when metadata or a digest is absent.
4. Test workflow contracts, malformed payloads, fake markers, URL ownership,
   stale latest payloads, and no-write complete checks before relying on CI.
5. Keep release payload rendering on the immutable release-tag path when the
   charter authorizes docs bot writes only from reviewed canonical `.github/`
   sources; do not widen that exception without explicit approval.

## Related

- `.cg-docs/plans/2026-08-12-automated-documentation-deployment.md`
- `.cg-docs/reviews/2026-08-12-automated-documentation-deployment-review.md`
- `.cg-docs/solutions/git-workflows/2026-08-11-merge-generated-brain-files-and-additive-ci-conflicts.md`
- `.cg-docs/solutions/testing-patterns/2026-07-31-review-artifacts-must-use-machine-readable-finding-maps-and-stable-validation-evidence.md`
