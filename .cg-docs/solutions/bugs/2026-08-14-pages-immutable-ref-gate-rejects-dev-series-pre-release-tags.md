---
date: 2026-08-14
title: "Pages immutable-ref gate rejects dev-series pre-release tags (v1.2.0.900x)"
category: "bugs"
type: "bug"
language: "PowerShell"
tags: [pages, github-actions, workflow, immutable-ref, resolver, release-tags, pre-release, dev-series, ci]
root-cause: "The pages.yml resolve-immutable-ref gate accepted only 3-part vX.Y.Z tags or main-lineage SHAs, but the repo's dev-series pre-release tags are 4-part v1.2.0.900x cut from dev, so tag-triggered Pages deployments were rejected before deploy."
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
red-phase-confirmed: "yes"
expected-behavior-source: "user-requirement"
test-gap: "missing-test"
---

# Pages immutable-ref gate rejects dev-series pre-release tags (v1.2.0.900x)

## Symptom

The tag-triggered Pages deployment failed for the pre-release release
`v1.2.0.9004`. Running
[31748306075](https://github.com/GPID-WB/compound-gpid/actions/runs/31748306075)
aborted in the `resolve-immutable-ref` job with:

> `Ref must be an official vX.Y.Z tag or a full commit SHA.`

The repo's pre-release line (`v1.2.0.900x`) is cut from `dev`, so the
documentation site for each pre-release never deployed.

## Expected Behavior Source

**User requirement** — the maintainer will keep cutting `v1.2.0.900x`
pre-releases in this tag format, and each tag-triggered Pages deployment must
succeed instead of failing at the ref gate.

Specifically: the `resolve-immutable-ref` tag pattern must accept the 4-part
`v1.2.0.9004` dev-series format (`vX.Y.Z.<build>`), and the resolved commit must
be accepted when it is an ancestor of `origin/dev` (the release line) as well as
`origin/main`.

## Root Cause

`.github/workflows/pages.yml` `resolve-immutable-ref` was written for the
repo's *stable* `vX.Y.Z` release shape on `main`:

- The tag regex `^v[0-9]+\.[0-9]+\.[0-9]+$` accepts only 3-part tags, so the
  4-part `v1.2.0.9004` was rejected with the "official vX.Y.Z tag" error.
- The ancestry check `git merge-base --is-ancestor "$sha" origin/main` fails for
  dev-cut commits, because pre-releases happen on `dev` (ahead of `main`).

## Reproduction Test

`tests/docs-automation.Tests.ps1` → "Pages exact-artifact deployment contracts":

- `accepts dev-series pre-release tags (v1.2.0.900x) in the immutable-ref
  resolver` — compiles the workflow's actual tag regex and asserts it matches
  both `v1.2.0` and `v1.2.0.9004`, and rejects `v1.2`.
- `requires dev-series pre-release tag commits to resolve on the dev lineage` —
  asserts the resolver performs `is-ancestor` and checks `origin/dev`.

Both failed on the shipped `pages.yml` (`Expected $true, but got $false` for the
4-part tag; `origin/dev` absent), reproducing the release failure exactly.

## Test Gap

**`missing-test`** — the pre-existing contract assertions
(`docs-automation.Tests.ps1` gate-exists checks and `check-docs-site.js`'s
`tags: ["v*.*.*"]` token) verified the gate's *presence* but never fed it a
4-part dev-series tag input or asserted the dev-lineage ancestry path. No test
exercised the tag-shape that the actual release line uses, so the rejection
slipped through and surfaced only on a live tag deployment.

## Fix

`.github/workflows/pages.yml` `resolve-immutable-ref`:

- Widen the tag pattern to `^v[0-9]+\.[0-9]+\.[0-9]+(\.[0-9]+)?$` so both
  `vX.Y.Z` official tags and `vX.Y.Z.<build>` dev-series pre-release tags are
  accepted (error message updated accordingly).
- Add `dev` to the fetched refs (`git fetch origin main dev`) and allow the
  resolved commit to be an ancestor of `origin/main` **or** `origin/dev`,
  matching the repo's actual release topology:

```diff
- if [[ "$ref" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
+ if [[ "$ref" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(\.[0-9]+)?$ ]]; then
  ...
- git fetch origin main
+ git fetch origin main dev
  git cat-file -e "$sha^{commit}"
- git merge-base --is-ancestor "$sha" origin/main
+ git merge-base --is-ancestor "$sha" origin/main \
+   || git merge-base --is-ancestor "$sha" origin/dev \
+   || { echo "Ref commit must be an ancestor of origin/main or origin/dev."; exit 1; }
```

The two reproduction tests now pass (16/16 in `docs-automation`), and the full
Pester suite ran green (2534 passed, 0 failed, 2 skipped) with site validation
passing.

## Lessons Learned

The `missing-test` gap teaches that a workflow contract gate must be tested with
the **actual input shape the production path uses**, not just asserted to exist.
The gate's tag regex lived next to a `tags: ["v*.*.*"]` trigger that plainly
fires on 4-part dev tags, and the repo's established release line (`dev`,
`v1.2.0.900x`) diverged from the gate's `main`/`vX.Y.Z` assumption — the two
views of "what refs are deployable" had drifted. Going forward, contract tests
for a ref resolver should compile and exercise the live regex/ancestry logic
against both official and pre-release tag shapes, mirroring the documented
deployment topology (`docs/development/index.md`).

## Related

- `.cg-docs/solutions/git-workflows/2026-08-13-verified-pages-artifact-and-release-tag-gates.md`
  (design note for the gate itself, documented `vX.Y.Z` — the very gap).
- None other found in `.cg-docs/solutions/bugs/`.
