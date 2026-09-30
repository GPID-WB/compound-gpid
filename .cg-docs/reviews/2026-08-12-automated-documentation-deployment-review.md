---
date: 2026-08-13
depth: full
type: standard
plan: .cg-docs/plans/2026-08-12-automated-documentation-deployment.md
findings:
  P0.1: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: skipped
  P1.5: fixed
  P1.6: fixed
  P1.7: fixed
  P1.8: fixed
  P1.9: fixed
  P1.10: fixed
  P1.11: fixed
  P1.12: fixed
  P1.13: fixed
  P1.14: skipped
  P2.1: open
  P2.2: open
  P2.3: open
  P2.4: open
  P2.5: open
  P2.6: open
  P2.7: open
---

# Review: Automated Documentation Deployment and What's New Page

## Scope

- Documentation generators, validation, release-payload contract, Pages and rebuild workflows.
- Canonical prompts/agent and regenerated native targets.
- Node/Pester/Python coverage and local validation evidence.

## Findings

### P0 - Blocking

- **[P0.1]** `docs/assets/site.js:201,299` - Navigation page IDs are interpolated into `innerHTML` attributes without validation. A crafted `navigation.json` ID can inject an event handler into the public site. Validate page IDs and use DOM APIs/encoded attributes. This is in the effective deployment scope because the new workflow publishes the navigation manifest.

### P1 - Critical

- **[P1.1]** `.github/workflows/pages.yml:8-15,87-104` - Tag and dispatch paths run repository Node code with Pages/OIDC permissions for arbitrary `v*` tags or user-supplied refs. Restrict production deploys to official immutable release tags or full commit SHAs resolved to approved main history; reject dev tags and branch refs before checkout.
- **[P1.2]** `.github/workflows/doc-rebuild.yml:31`; `.github/workflows/pages.yml:41,46,68,78,85,99,110,113,119` - Privileged workflows use mutable action tags. Pin each `uses:` action to a reviewed full commit SHA with a version comment.
- **[P1.3]** `.github/workflows/doc-rebuild.yml:64-70` - Artifact upload omits hidden files by default, dropping build metadata and `.nojekyll`. Enable hidden-file upload and fail when required files are absent.
- **[P1.4]** `.github/workflows/doc-rebuild.yml:6-15` - `releases/**` does not trigger main rebuilds. A payload commit leaves main's generated What's New page stale. Add the path filter.
- **[P1.5]** `scripts/generate-whats-new.js:149-160`; `scripts/rebuild-docs.js:283-295` - Release inputs can use symlinked files/dirs, while fingerprints exclude those link targets. Reject symlinked release inputs and verify containment before reads.
- **[P1.6]** `scripts/rebuild-docs.js:150-173`; `scripts/generate-whats-new.js:259-268` - Marker-like text in fenced or inline code is parsed as a live marker. Use a shared line-oriented parser that ignores fenced examples and accepts only standalone markers.
- **[P1.7]** `scripts/rebuild-docs.js:189-190` - Prompt descriptions are emitted without HTML-sensitive escaping, allowing marker-like frontmatter to poison generated Markdown. Escape HTML-sensitive sequences and add a two-run regression.
- **[P1.8]** `scripts/generate-whats-new.js:75-109` - Release/source URLs can target unrelated GitHub repositories. Require the expected `GPID-WB/compound-gpid` repository and exact tag path.
- **[P1.9]** `scripts/generate-whats-new.js:178-199` - `latest.json` may match an older immutable release instead of the newest. Require it to byte-match the newest `(publishedAt, tag)` payload.
- **[P1.10]** `scripts/rebuild-docs.js:253-260,313-322,434-444` - Metadata adds a runtime timestamp and unsorted file enumeration, so identical builds do not produce byte-identical provenance. Remove or derive the timestamp and sort digests deterministically.
- **[P1.11]** `.github/prompts/cg-release.prompt.md:84` - `<latest-tag>..HEAD --since=<window-start>` can omit post-tag commits with old timestamps; blank-line record separation also makes multiline commit bodies ambiguous. Scan the whole tag range and use explicit record/field separators.
- **[P1.12]** `.github/prompts/cg-release.prompt.md:314-328` - The tag command cannot resume: it fails for both absent and already-correct tags in its prescribed order. Branch explicitly on tag existence, require equality to `HEAD`, then push and verify remote resolution.
- **[P1.13]** `.github/prompts/cg-release.prompt.md:317-360` - A failed tag-site/API publish has no explicit `--resume <tag>` path, so a rerun may prepare a new release instead. Add resume validation and retry only the unfinished deployment/API stage.
- **[P1.14]** `compound-gpid.md:32` - The narrow bot exception lists `.github/` sources but the renderer also consumes release payloads. Do not broaden charter text without approval; either obtain approval or prevent payload-based output from bot commits.

### P2 - Important

- **[P2.1]** `.github/workflows/tests.yml:10-27` - `npm run test:docs-automation` is not a pre-merge CI gate. Add it before browser-evidence work.
- **[P2.2]** `scripts/rebuild-docs.js:51,450-460` - No non-mutating complete-build check covers a stale What's New page. Support `--all --check` and report every stale managed page.
- **[P2.3]** `scripts/generate-whats-new.js:308` - Per-file validation does not enforce filename/tag identity or `latest.json` consistency. Provide release-set validation before durable writes.
- **[P2.4]** `tests/docs-automation.Tests.ps1:25` - Workflow tests use broad substring checks and do not assert job-scoped non-mutation. Scope assertions to each named job and prohibit generation in the artifact-consuming job.
- **[P2.5]** `scripts/check-docs-site.js:92` - New validation paths lack negative fixture coverage, including artifact-root validation. Add fixture-driven validator tests.
- **[P2.6]** `scripts/generate-whats-new.js:149-200`; `scripts/rebuild-docs.js:267-310` - Payload history and fingerprint construction are unbounded in memory. Add payload byte/count limits and incrementally hash sorted canonical inputs.
- **[P2.7]** `docs/development/index.md:109-127` - Schema documentation omits exact field formats/limits and `releaseDate`; align it with the closed implementation contract.

## Passed

- Node documentation suite: 20 tests passed.
- Package-script equivalent passed.
- Site validation passed.
- Focused and full canonical Pester runner passed with zero failures.
- Native pre-commit target gate: 280 passed, 10 skipped.

## Residual Evidence

- The generated-target drift assertion must run after this branch is committed.
- Required V9 GitHub Actions evidence must be collected after merge.
