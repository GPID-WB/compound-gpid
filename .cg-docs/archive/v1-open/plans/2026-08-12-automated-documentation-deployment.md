---
date: 2026-08-12
title: "Automated Documentation Deployment and What's New Page"
status: active
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-08-12-automated-documentation-deployment.md"
language: "both"
estimated-effort: "large"
deviation-policy: "ask"
artifact-schema-version: 1
execution-report: ".cg-docs/work-reports/2026-08-13-automated-documentation-deployment.md"
phases: 5
tags: [documentation, ci-cd, github-actions, whats-new, wiki-rebuild, pages, release]
---

# Plan: Automated Documentation Deployment and What's New Page

## Objective

Keep the public documentation site current from reviewed canonical sources and
publish a deterministic, release-backed "What's New" page. Canonical source
changes on `main` must rebuild only managed documentation sections, commit only
real changes, and deploy the exact rebuilt artifact without relying on a bot
push to trigger a second workflow.

## Context

- `docs/reference.md` is an existing auto-managed wiki page. Its
  `shell-commands` and `commands` sections are bounded by `cg:auto` markers and
  declared in `docs/_wiki.yml`.
- The current Pages workflow validates and deploys `docs/` on pushes to `main`,
  but it does not rebuild generated documentation or include release history.
- Canonical prompts, skills, and agents are authored under `.github/`; `.kilo/`,
  `.claude/`, `.agents/`, and `.opencode/` are generated projections and must
  not be edited directly.
- A workflow push using `GITHUB_TOKEN` does not provide a safe implicit trigger
  for a separate Pages workflow. The deployment workflow must consume the
  rebuilt `docs/` artifact from the completed rebuild run, rather than assuming
  the bot commit will launch a new Pages run.
- `create-release.ps1` requires a clean checkout for its isolated release
  preflight. Release payloads therefore must be committed and tagged before the
  GitHub Release API call, not left as uncommitted files created mid-release.
- The charter already contains the approved, narrow bot-commit exception for
  deterministic documentation renders. This work must verify that wording, not
  broaden it to arbitrary bot edits.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Rebuild all supported canonical-source `cg:auto` sections deterministically from `.github/` source files. | brainstorm |
| R2 | Preserve all manual pages and user-owned text outside managed markers; fail loudly for malformed markers or unknown managed generators. | wiki contract, brainstorm |
| R3 | Provide a local write mode and a no-write `--check` mode that reports exactly which managed files would change. | brainstorm |
| R4 | Add a navigable, auto-managed `docs/whats-new.md` page and declare its ownership in `docs/_wiki.yml`. | brainstorm |
| R5 | Define a validated, versioned release-payload contract and make `/cg-release` create tracked `releases/<tag>.json` plus `releases/latest.json` before tagging and publishing. | brainstorm |
| R6 | Generate the What's New managed section from release payloads in stable newest-first order, without duplicate `latest.json` content or raw untrusted Markdown injection. | brainstorm |
| R7 | Add a least-privilege rebuild workflow on `main` for canonical documentation inputs, with idempotent no-op handling and an auditable bot commit. | brainstorm |
| R8 | Deploy the exact rebuilt documentation artifact after a successful rebuild and separately support release-tag deployment without stale-content races. | brainstorm, GitHub Actions behavior |
| R9 | Extend site validation so the What's New route, ownership markers, release-page structure, and deployment workflow contracts fail loudly on drift. | project testing requirements |
| R10 | Cover script logic, malformed input, no-op behavior, workflow contracts, and release-prompt sequencing with focused automated tests. | project testing requirements |
| R11 | Regenerate and verify every native platform target after canonical `.github/` changes; never hand-edit generated copies. | `compound-gpid.context.md` |
| R12 | Preserve the charter's narrow deterministic-docs bot-commit exception and document the operational behavior for maintainers. | brainstorm, charter |

## Implementation Steps

## Phase 1: Define Contracts and Page Ownership

### 1. Define the documentation and release-payload contracts
- **Requirements**: R1, R2, R5, R6, R12
- **Files**: `docs/_wiki.yml`, `docs/whats-new.md`, `docs/navigation.json`, `docs/development/index.md`, `releases/.gitkeep`, `compound-gpid.md` (verification only unless the approved bot exception is absent or materially inconsistent)
- **Details**:
  - Add a `whats-new` page entry to the wiki manifest with `ownership: "auto"`, a `release-notes` managed section, and a plain `whats-new.md` filename that satisfies the wiki path rules.
  - Add a `What's New` route to the audience-appropriate navigation group with complete title and description metadata. The route must be unique and every Markdown page must remain represented exactly once.
  - Create the initial page with one level-one heading and a paired `<!-- cg:auto:release-notes -->` / `<!-- cg:auto:end -->` section. Its initial placeholder must be valid before the first release payload exists.
  - Document the release payload schema in maintainer documentation. Use tracked immutable files named `releases/v<major>.<minor>.<patch>[.<dev>].json`; `releases/latest.json` is a byte-for-byte current-release convenience copy and is never rendered as a second release.
  - Require payload fields: `schemaVersion: 1`, `tag`, `publishedAt` in UTC ISO-8601 form, `name`, `url`, and a non-empty `sections` array. Each section has a controlled `kind` (`new`, `fixed`, or `internal`), a bounded plain-text title, and bounded plain-text entries. Reject invalid tags, duplicate tags, malformed dates, unknown fields that alter rendering semantics, control characters, invalid GitHub release URLs, and excessive record sizes.
  - Render no more than the 20 newest immutable payloads, newest first by `publishedAt` then tag, and include a GitHub Releases link for older history. This keeps the page bounded while retaining every versioned source payload in the repository.
  - Verify that the existing charter constraint remains narrowly limited to deterministic docs renders from reviewed canonical sources. Do not change other charter body content as part of this work.
- **Test Scenarios**: valid page and manifest registration; empty release directory renders an explicit empty state; duplicate navigation ID fails; malformed release payload is rejected; manual text outside the marker remains untouched.
- **Tests**: focused Node contract tests added in Step 2; `node scripts/check-docs-site.js` after Steps 2 and 4; focused Pester assertions added in Step 8.
- **Acceptance criteria**: the route, manifest entry, marker pair, schema documentation, and empty-state behavior are explicit and compatible with the existing wiki and navigation contracts.

### 2. Establish isolated fixtures and a Node test entry point
- **Requirements**: R2, R3, R6, R9, R10
- **Files**: `scripts/tests/rebuild-docs.test.js`, `scripts/tests/generate-whats-new.test.js`, `scripts/tests/fixtures/docs-automation/**`, `package.json`
- **Details**:
  - Use Node's built-in `node:test` and `node:assert/strict`; do not add a YAML or Markdown-rendering package for these deterministic scripts.
  - Build small, temporary fixture repositories that contain only the relevant `_wiki.yml`, marker-delimited Markdown, canonical source samples, navigation manifest, and release payload files. Tests must never write the working repository's real `docs/` or `releases/` directories.
  - Add an explicit script such as `test:docs-automation` that executes only the new Node test files. Do not fold these unit tests into the browser-evidence `npm test` command, which requires Playwright assets and a captured evidence manifest.
  - Test the command-line exit contract: `--check` exits zero when current, exits nonzero without mutation when stale, and names the stale file paths; write mode mutates only allowed managed regions.
- **Test Scenarios**: idempotent second rebuild; manual ownership skipped; missing close marker; nested marker; unknown managed section; invalid release JSON; `latest.json` deduplication; stable ordering ties; escaping of table delimiters and line breaks.
- **Tests**: `node --test scripts/tests/rebuild-docs.test.js scripts/tests/generate-whats-new.test.js`; package-script equivalent.
- **Acceptance criteria**: all tests run without browser dependencies and demonstrate no production-file mutation.

## Phase 2: Implement Deterministic Generation

### 3. Implement the canonical documentation rebuild script
- **Requirements**: R1, R2, R3, R7, R9
- **Files**: `scripts/rebuild-docs.js`, `docs/reference.md`, `docs/_wiki.yml`
- **Details**:
  - Implement a dependency-free Node CLI with `--root <path>`, default write mode, and `--check` no-write mode. Resolve every path beneath the supplied repository root and reject traversal, symlink escapes, unknown files, or writes outside `docs/`.
  - Parse only the manifest subset needed for the established ownership contract. Validate the wiki schema version, page filenames, unique page IDs/orders, each selected `ownership: "auto"` page, and each paired marker before any write.
  - Use an explicit generator registry rather than evaluating source text: regenerate `commands` only from canonical `.github/prompts/cg-*.prompt.md` frontmatter and command names, and regenerate `research-commands` only from `.github/prompts/cr-*.prompt.md`. Keep technical and research tables separate, preserve a documented deterministic order, and never rewrite the manual shell-command table or surrounding reference prose.
  - Treat `release-notes` as owned by the separate release generator, not as a prompt-derived section. Fail for any other declared managed section without an explicit owner to prevent silent documentation drift.
  - Replace only marker interiors, preserve all text before, between, and after marker pairs byte-for-byte, and write only when bytes differ. A second run on unchanged inputs must produce no diff.
  - Add `--all` for the complete deployable site build. It calls the separately testable What's New generation logic, validates the combined documentation tree, and writes an out-of-tree build metadata file containing a version, canonical-input fingerprint, and per-file digest for the completed `docs/` output. The canonical-input fingerprint includes prompt/skill/agent source files, releases, the three documentation scripts, relevant documentation workflow files, and documentation source text with every managed marker interior normalized away; it therefore remains stable after a permitted bot render but changes for a newer source revision.
  - Add a no-write fingerprint verification mode used by Pages. It recomputes canonical inputs on current `main`, compares them with downloaded build metadata, and reports a stale run before Pages receives the artifact.
  - Keep the public prose generated by the script concise, escape Markdown table content derived from frontmatter, and fail if required canonical metadata is missing rather than inventing a description.
- **Test Scenarios**: canonical prompt addition/removal updates only the matching technical or research table; no diff produces no write; malformed YAML-like manifest content fails before writes; source descriptions containing pipes/newlines are safely rendered; shell-command and non-command reference prose is preserved; a newer canonical input fails metadata freshness verification.
- **Tests**: Node rebuild script suite from Step 2; `node scripts/rebuild-docs.js --check`; `node --check scripts/rebuild-docs.js`.
- **Acceptance criteria**: the script is deterministic, bounded to its two prompt-table markers, provides useful dry-run and freshness output, and can construct one fingerprinted complete deployment tree without touching user-owned reference prose.

### 4. Implement the What's New generator and validation hooks
- **Requirements**: R4, R5, R6, R9
- **Files**: `scripts/generate-whats-new.js`, `docs/whats-new.md`, `scripts/check-docs-site.js`
- **Details**:
  - Implement a dependency-free Node CLI with `--root <path>`, `--check`, write mode, and `--validate-payload <relative-path>`. The payload-validation mode is the release workflow's machine-checkable guard before any release payload commit.
  - Read only `releases/*.json`, exclude `.gitkeep`, deduplicate `latest.json` against its immutable versioned record, validate every included payload before rendering, and render a stable newest-first release history inside the `release-notes` marker pair. Link every entry to its validated pushed-tag `sourceUrl`, not to a presumed completed Release API resource.
  - Render payload text as plain Markdown content after escaping table delimiters, line breaks, HTML-sensitive sequences, and link labels. Never render arbitrary payload text as executable HTML or accept external URLs other than the expected GitHub release URL shape.
  - Render a deterministic empty state when no release payload is present. `--check` must report a stale page without writing it.
  - Extend `check-docs-site.js` to require the What's New navigation route and file, the expected heading and marker pair, the split Technical/Research command markers, and the complete-build artifact handoff and freshness contract. Keep existing navigation, link, skill-catalog, accessibility-shell, and Pages-action validation intact.
- **Test Scenarios**: two immutable releases plus matching `latest.json` render exactly twice, not three times; each valid scanner kind renders in its expected group; invalid `latest.json` or unknown kind fails; payload text with Markdown/HTML characters is rendered inertly; older releases are consistently capped; no-payload state passes site validation.
- **Tests**: Node What's New suite; `node scripts/generate-whats-new.js --check`; `node scripts/check-docs-site.js`; `node --check scripts/generate-whats-new.js`.
- **Acceptance criteria**: the public page has deterministic, safe, release-backed content and every invalid input fails before a site artifact can be deployed.

## Phase 3: Wire Release and Deployment Workflows

### 5. Add the main-branch documentation rebuild workflow
- **Requirements**: R1, R3, R7, R8, R9, R12
- **Files**: `.github/workflows/doc-rebuild.yml`, `.github/workflows/pages.yml`
- **Details**:
  - Create `doc-rebuild.yml` for pushes to `main` that affect only charter-approved canonical documentation inputs: `.github/prompts/**`, `.github/skills/**`, `.github/agents/**`, `docs/**`, or the documentation scripts/workflows. Release payload changes intentionally use the separate tag deployment path and do not authorize bot documentation commits.
  - Use the minimum job permissions: `contents: write` only for the rebuild job, with no Pages or identity-token permission. Check out the triggering main commit, run `rebuild-docs.js --all` to construct the complete tree including What's New, run static documentation validation, compute build metadata, and inspect the resulting diff.
  - If `docs/` is unchanged, report a no-op and still upload the validated complete `docs/` directory plus build metadata as a short-retention artifact. If it changed, commit only `docs/` with a conventional bot identity/message that states it is a deterministic render from the approved canonical inputs, then push to `main`; never stage or commit unrelated working-tree paths.
  - Upload the complete post-build `docs/` directory and build metadata from every successful run. They are the exact deployment input and provenance for the Pages workflow, including a no-op run. The workflow must run complete-build validation before upload; Pages must not regenerate or mutate any downloaded file.
  - Refactor `pages.yml` so its main-branch deployment path is a `workflow_run` trigger for a successful `doc-rebuild.yml` run on `main`. The Pages job downloads the exact completed artifact and metadata from that run, checks out current `main` only to recompute the normalized canonical-input fingerprint, and skips the deployment if the run is stale. If current `main` differs only by the approved idempotent docs bot commit, the normalized fingerprint remains equal and deployment proceeds. It verifies all downloaded file digests, runs validation-only site checks, uploads the unchanged `docs/` tree, and deploys.
  - Preserve `workflow_dispatch` and add an explicit `push.tags: ["v*"]` path. Tag/manual paths run `rebuild-docs.js --all` from the immutable checked-out tag, validate and upload that completed tree directly, and do not use a main-branch freshness check or bot commit. Use a shared Pages concurrency group with explicit latest-source behavior: stale `main` artifact runs are skipped by the fingerprint check; immutable tag/manual deploys are not treated as stale.
  - Pin or retain action references according to the repository's established workflow policy and keep Pages permissions scoped to the deploy job (`pages: write`, `id-token: write`, `contents: read`, plus only the artifact-read access required by `workflow_run`).
- **Test Scenarios**: canonical source change writes a changed complete docs artifact; unchanged source produces no bot commit; bot-created docs output is available to Pages even when its `GITHUB_TOKEN` push does not trigger `push` workflows; an older rebuild completing after a newer canonical main commit is skipped; failed rebuild never deploys; tag path builds and deploys the tag's validated documentation.
- **Tests**: focused workflow-contract Pester tests from Step 8; static YAML/action-string checks in `check-docs-site.js`; GitHub Actions run validation after merge.
- **Acceptance criteria**: deployment always uses an unmodified, complete, validated, digest-verified post-build artifact; stale main runs are skipped; and no-op runs, bot pushes, tags, and deployment concurrency have explicit behavior.

### 6. Extend `/cg-release` with a tracked-payload release sequence
- **Requirements**: R5, R6, R8, R10, R12
- **Files**: `.github/prompts/cg-release.prompt.md`, `.github/agents/cg-release-scanner.agent.md` if its output schema needs structured section fields, `tests/prompt-tools.Tests.ps1` or a focused release contract test
- **Details**:
  - Preserve the current release scanner's human-readable notes path, but require its new `## Release Payload` fenced JSON block to use the exact `kind: new|fixed|internal`, title, and bounded plain-text entries contract in Step 1. Do not derive the payload by scraping rendered `RELEASE_NOTES.md` or translate ambiguous categories in `/cg-release`.
  - Before creating a GitHub Release, require a clean, up-to-date `main` checkout and derive both `releases/<tag>.json` and `releases/latest.json` from the confirmed scanner block. Fill `releaseDate` from the release preparation date and `sourceUrl` from the known pushed-tag URL. Validate both files with `generate-whats-new.js --validate-payload` and reject an unknown scanner kind before writing either file.
  - After explicit release confirmation, stage only the two release payloads, commit them with a documented conventional release-preparation message, create or verify that `<tag>` resolves to that exact clean commit, push `main` and the tag, then invoke the tag path in `pages.yml` to build and deploy the exact tag checkout before calling `create-release.ps1`.
  - Keep `RELEASE_NOTES.md` ephemeral and gitignored. The release payload is the durable site source; the GitHub Release remains the public release record.
  - Halt safely on a non-fast-forward main, existing tag pointing to another commit, existing immutable payload with different bytes, payload validation failure, push failure, failed tag-site deployment, or failed release API call. Report which durable state succeeded so a maintainer can resume without overwriting a release record.
  - Do not invoke `/cg-wiki` or rebuild documentation from `/cg-release`; the `main` push and the tag trigger provide the separate deterministic site path.
- **Test Scenarios**: fresh release maps each scanner payload kind into matching JSON before tag/API publication; rerun with byte-identical payload is idempotent; different existing immutable payload blocks; missing/malformed scanner block or unknown kind blocks; tag deployment failure blocks release API publication; GitHub API failure leaves the committed/tagged source state clearly recoverable.
- **Tests**: focused Pester structural/ordering assertions; generator payload validation tests; existing `create-release.Tests.ps1` updated only where its established contract changes.
- **Acceptance criteria**: every deployable release has a committed, validated JSON source before its tag and API publication, and release execution cannot silently publish an untracked What's New entry.

## Phase 4: Add Regression Coverage and Native Parity

### 7. Add focused documentation-automation tests and register them safely
- **Requirements**: R2, R3, R6, R7, R8, R9, R10
- **Files**: `tests/docs-automation.Tests.ps1`, `tests/Run-Tests.ps1`, `tests/prompt-tools.Tests.ps1`, `tests/wiki.Tests.ps1`, `scripts/tests/rebuild-docs.test.js`, `scripts/tests/generate-whats-new.test.js`
- **Details**:
  - Add a registered Pester file that checks the canonical workflow contracts: approved canonical path filters, least privilege, `git diff --quiet` no-op decision, docs-only staging, complete-build validation before artifact upload, artifact/download digest identity, `workflow_run` success/branch gate, normalized-fingerprint stale-main skip, tag trigger, and no downloaded-artifact mutation before Pages upload.
  - Assert the release prompt's order: require scanner `Release Payload` JSON with exact valid kinds, validate payload, commit only durable release payloads, create/verify the exact tag, push main/tag, wait for tag-site deployment success, then call `create-release.ps1`. Assert that it never dispatches a wiki rebuild or derives kinds from prose.
  - Extend wiki tests for the marker migration and What's New manifest entry/marker, and extend prompt/site tests for the required routes, complete-build metadata, stale-run guard, and generator contract.
  - Register `docs-automation` in `tests/Run-Tests.ps1` so the canonical safe runner cannot silently skip it. Do not alter Pester invocation behavior or safety rules.
  - Keep behavioral generator coverage in Node tests and contract-level workflow/prompt coverage in Pester; no test may require credentials, a Pages deployment, or a live GitHub Release.
- **Test Scenarios**: new test file is registered; a future path-filter regression fails; bot staging broadens beyond `docs/` and fails; Pages mutates a downloaded artifact and fails; a stale main rebuild run is rejected; release API call moves before tag-site deployment and fails; malformed/unknown-kind payload fixture fails without writing a page.
- **Tests**: `node --test scripts/tests/rebuild-docs.test.js scripts/tests/generate-whats-new.test.js`; canonical Pester runner with only the registered affected files, using the project-safe execution mechanism; `node scripts/check-docs-site.js`.
- **Acceptance criteria**: the essential behavior is enforced locally without GitHub credentials, and every new Pester file is in the canonical runner registry.

### 8. Regenerate native targets and validate cross-platform contracts
- **Requirements**: R10, R11
- **Files**: generated `.claude/**`, `.agents/**`, `.opencode/**`, `.kilo/**` projections created only by `scripts/cg_generate_targets.py`; relevant Python target tests
- **Details**:
  - Regenerate all native trees from canonical `.github/` sources only after the canonical prompt/agent changes are finalized. Do not manually repair any generated prompt, agent, or adapter.
  - Confirm that each generated `/cg-release` command carries the same release-payload ordering and that target manifests remain complete.
  - Run the scoped target-mapping, target-generation, target-path-safety, packaging, ownership, closure, determinism, drift, and per-platform target tests that cover the changed canonical assets.
- **Test Scenarios**: canonical `cg-release` change appears in every generated target; no generated-only change survives a regeneration; drift test detects a missing projection.
- **Tests**: `python scripts/cg_generate_targets.py --all --dry-run`; regenerate with `python scripts/cg_generate_targets.py --all`; relevant `python -m pytest scripts/tests/test_target_*.py -q` subset including drift and Kilo coverage.
- **Acceptance criteria**: canonical and all generated native command trees are synchronized and the generator reports no drift.

## Phase 5: Verify and Hand Off

### 9. Run the complete documentation validation matrix
- **Requirements**: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12
- **Files**: all changed files; `tests/last-run.json` as generated test evidence only
- **Details**:
  - Run syntax checks for both Node scripts, focused Node unit tests, complete-build/fingerprint checks, and `node scripts/check-docs-site.js` from a clean worktree state after generation.
  - Run the registered affected Pester files using the canonical safe runner, following `cg-skill-pester-safety`; record the resulting artifact rather than parsing unsafe command output.
  - Run the relevant Python native-target gate after regeneration. If practical in the repository CI environment, add a workflow-dispatch smoke run or verify the first merge run: one changed canonical source, one no-op rerun, one stale-run skip, and one release-payload/tag path.
  - Inspect the final diff to confirm no release payload test fixture, credentials, generated browser evidence, or unrelated user change is staged by the new bot workflow.
- **Test Scenarios**: full local validation passes; fixture roots never appear in production output; workflow test asserts docs-only staging and unchanged downloaded-artifact deployment; release payloads are deterministic across two generator runs; a stale metadata fingerprint blocks deployment.
- **Tests**: Node syntax, focused Node tests, site validation, safe focused Pester runner, scoped Python target gate, and CI workflow evidence.
- **Acceptance criteria**: every required verification item has executed evidence, and no known failure can be resolved by static inspection alone.

### 10. Register the plan and document operational ownership
- **Requirements**: R8, R11, R12
- **Files**: `roadmap.json` through `@cg-roadmap`; `docs/development/index.md`; relevant reference documentation if new maintainer commands/options need a public home
- **Details**:
  - Through `@cg-roadmap`, link this plan to the existing `automated-documentation-deployment-and-whats-new-page` feature and set it to `planned` before implementation, then let `/cg-work` move it through active and done states only after required evidence passes.
  - Document the maintainer operational sequence: canonical source merge -> deterministic rebuild artifact -> Pages deploy; release preparation -> validated payload commit/tag -> release/tag deploy. State that manual edits outside `cg:auto` markers remain user-owned and that release JSON is the canonical public-release source for the page.
  - Document no-op, validation failure, bot commit, and release API recovery behavior without widening the charter exception.
- **Test Scenarios**: roadmap points to the saved plan; maintainer instructions name the local dry-run, payload validation, and site validation commands; no documentation tells users to edit generated native targets.
- **Tests**: targeted roadmap read after agent dispatch; documentation-link validation through `node scripts/check-docs-site.js`; target drift verification from Step 8.
- **Acceptance criteria**: the roadmap, operations documentation, canonical/generated ownership model, and recovery instructions all agree.

## Testing Strategy

- Node unit tests use temporary fixtures and cover pure parsing, replacement, validation, idempotency, ordering, escaping, and no-write behavior.
- Pester tests enforce canonical workflow, release-prompt, manifest, marker, and runner-registration contracts. They run only through the project-safe canonical runner.
- Site validation checks navigation coverage, internal links, public page structure, required routes, and the workflow wiring that guards deployments.
- Python target tests enforce canonical-to-native target parity after `.github/` changes.
- GitHub Actions provides final integration evidence for a changed rebuild, no-op rebuild, artifact handoff, and tag-triggered deployment; no local test publishes a release or deploys Pages.

## Documentation Checklist

- [ ] `docs/whats-new.md` explains the generated release history and empty state.
- [ ] `docs/navigation.json` exposes What's New with audience-appropriate metadata.
- [ ] `docs/_wiki.yml` declares the split prompt-table ownership and release-generated marker.
- [ ] `docs/development/index.md` documents local rebuild, payload validation, and deployment flow.
- [ ] `/cg-release` documents the scanner-kind mapping, durable payload-before-tag/site-deploy/API sequence, and recovery states.
- [ ] The existing charter bot-commit exception is verified as narrow and accurate.
- [ ] Generated native-target copies are regenerated, not hand-authored.

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Bot `GITHUB_TOKEN` push does not trigger a separate Pages push workflow | High | High | Deploy the complete post-build `docs/` artifact through a successful, main-only `workflow_run`; never depend on the bot push event. |
| A bot workflow stages an unrelated file | Low | High | Stage only `docs/`, assert that path in Pester contracts, and inspect the diff before the commit. |
| Rebuild overwrites research or hand-authored reference documentation | Medium | High | Migrate the oversized marker first, generate only isolated CG/CR command markers, preserve all other bytes, and fixture-test malformed/nested markers. |
| Renderer has no authoritative shell-command source | High | High | Remove shell-command markers and keep the existing table manual until a separately scoped canonical metadata feature exists. |
| Invalid or hostile release text corrupts public Markdown | Medium | High | Strict payload schema, bounded plain-text fields, escaping, allowed URL validation, and fail-before-write behavior. |
| Scanner categories cannot produce valid release payloads | Medium | High | Require an exact `Release Payload` JSON block with `new|fixed|internal` kinds and reject unknown/missing kinds. |
| Release payload is not in the tag or public site before API publication | Medium | High | Require durable payload commit, exact tag verification, pushed tag-site deployment success, then GitHub Release API publication. |
| `latest.json` duplicates a versioned release | Medium | Medium | Deduplicate by immutable tag/content and test both versioned and latest inputs. |
| Older main rebuild completes after a newer one | Medium | High | Compare normalized canonical-input fingerprints before deploying; skip stale main runs while treating immutable tags independently. |
| Pages mutates the claimed exact rebuild artifact | Medium | High | Build and validate all generated content in doc-rebuild, upload digests, and prohibit Pages from regenerating downloaded files. |
| New Pester tests are silently omitted | Medium | Medium | Register the new test stem in `tests/Run-Tests.ps1` and assert registration. |
| Generated platform trees drift from canonical prompts | Medium | Medium | Regenerate only with `cg_generate_targets.py` and run the drift/per-platform target tests. |
| No public payload exists before the first release | High | Low | Ship a valid deterministic empty state and validate it in local and CI checks. |

## Out of Scope

- Publishing a separate `/dev/` documentation site or preview deployment.
- Fetching GitHub Releases dynamically in browser JavaScript or treating the GitHub API as the documentation source of truth.
- AI-driven wiki regeneration in CI; the workflow uses deterministic Node scripts only.
- Automating the hand-authored shell-command table or introducing a new shell-command metadata catalog.
- Replacing the existing release-note prose workflow, changing release semver policy, or broadening the documentation bot's authority beyond reviewed canonical renders.
- Introducing a general YAML, Markdown, or static-site framework dependency for the two scripts.
- Editing generated native platform trees by hand.

## Completion Contract

### Outcome

Merges to `main` deterministically rebuild only the isolated Technical and
Research command tables plus the generated What's New page, then deploy the
exact validated, digest-verified complete artifact. Releases publish a safe,
versioned source payload whose validated pushed tag is deployed before the
GitHub Release API is called; manual documentation remains protected, and no
workflow relies on an implicit bot-push trigger.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Marker migration preserves all non-table reference content; What's New page, navigation, manifest ownership, marker pairs, scanner mapping, and empty state are valid. | `node scripts/check-docs-site.js` plus focused fixture tests | yes |
| V2 | 2 | Rebuild is deterministic, changes only isolated CG/CR prompt tables, preserves manual regions, and `--check` is non-mutating. | `node --test scripts/tests/rebuild-docs.test.js`; two consecutive rebuild checks | yes |
| V3 | 2 | Release payloads validate exact scanner kinds, deduplicate `latest.json`, render stable escaped content, and fail on malformed input. | `node --test scripts/tests/generate-whats-new.test.js`; `node scripts/generate-whats-new.js --validate-payload <fixture>` | yes |
| V4 | 3 | Rebuild workflow has approved input filters, docs-only staging, no-op behavior, complete-build validation, metadata/digest artifact upload, and least privilege. | Pester workflow-contract tests and reviewed `doc-rebuild.yml` | yes |
| V5 | 3 | Pages deploys the unmodified successful build artifact only after stale-main fingerprint checks, and tag/manual paths build complete immutable trees. | Pester workflow-contract tests and `node scripts/check-docs-site.js` | yes |
| V6 | 3 | `/cg-release` validates scanner payload kinds and creates durable payloads before exact commit/tag/push, tag-site deployment, and release API execution. | Pester release-contract tests and payload validation command | yes |
| V7 | 4 | Native targets are regenerated from canonical sources with no parity drift. | `python scripts/cg_generate_targets.py --all --dry-run`; scoped target pytest gate | yes |
| V8 | 5 | Affected Pester files run through the canonical safe runner and pass. | `tests/last-run.json` produced by the canonical safe runner | yes |
| V9 | final | Successful CI runs prove changed rebuild, no-op rebuild, stale-main skip, unmodified artifact handoff, and release/tag deployment behavior. | GitHub Actions run URLs/logs and deployed site result | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | 2 | Scripts never modify text outside the isolated CG/CR prompt markers, What's New marker, or `docs/`. | Fixture byte-preservation tests and resolved-path guards |
| C2 | 2 | Invalid manifest, marker, source metadata, or payload causes an explicit failure with no partial output. | Negative Node fixtures and no-write assertions |
| C3 | 3 | Bot commits contain only deterministic `docs/` output from reviewed canonical sources. | Workflow docs-only staging contract and final diff review |
| C4 | 3 | Pages never deploys a failed or stale main rebuild, assumes a `GITHUB_TOKEN` bot push triggers a workflow, or mutates downloaded build bytes. | `workflow_run` conclusion/branch/fingerprint gates and digest-verified artifact contract |
| C5 | 3 | GitHub Release publication occurs only after the exact durable payload commit/tag is pushed and its tag site deployment has succeeded. | Release-prompt ordering assertions and `create-release.ps1` clean-preflight behavior |
| C6 | 4 | `.github/` remains canonical; generated targets are changed only by the generator. | Generator output plus target-drift tests |
| C7 | 5 | Pester safety rules are never weakened or bypassed. | Canonical runner usage and `tests/last-run.json` evidence |

### Boundaries

- Allowed: canonical `.github/` prompt/agent changes, deterministic Node scripts, isolated prompt-table marker migration, documentation files, release JSON payloads, GitHub Actions workflows, tests, generator-produced target updates, and the existing roadmap feature link through `@cg-roadmap`.
- Out of scope: `/dev/` hosting, runtime GitHub API content, arbitrary bot edits, release-semver redesign, new framework dependencies, and direct generated-target edits.

### Iteration Policy

1. Implement the schema and fixture contracts before mutating deployment workflows.
2. Complete and test the reference marker migration before enabling a write-mode rebuild; keep the shell-command table manual unless a separately approved canonical source is introduced.
3. Keep Node generation deterministic and dependency-free; if a manifest feature cannot be parsed safely, fail with a precise error rather than adding heuristic recovery.
4. Run focused Node checks after each script, then complete-build, site, fingerprint, and workflow-contract validation after workflow changes.
5. Regenerate native targets only after canonical `.github/` sources stabilize; treat a generator drift failure as a required correction, not a manual generated-file edit.
6. If a workflow integration behavior cannot be proven locally, preserve the static contract evidence and require the first GitHub Actions run before marking final completion.
7. Under `deviation-policy: ask`, pause for approval before changing the payload schema, widening bot write scope, changing release tag order, automating manual shell-command content, or adding a dependency not specified here.

### Blocked-Stop Conditions

- A managed section lacks a recognized deterministic generator or valid marker pair, or the marker migration cannot preserve the existing reference prose.
- A release payload lacks a valid scanner-defined kind, is invalid, differs from an existing immutable versioned payload, or cannot be committed/tagged exactly as validated.
- The rebuild workflow would need to stage outside `docs/` or use broader permissions than specified.
- The Pages workflow cannot download/digest-verify the exact successful complete artifact, cannot establish main-run freshness, or would deploy after a failed rebuild.
- Required Node, Pester-safe-runner, target-parity, or CI evidence fails without an explicitly approved exception.
- A necessary change would broaden the charter's bot-commit exception, alter protected charter body content without approval, or require a `/dev/` deployment.
