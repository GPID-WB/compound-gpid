---
date: 2026-09-03
created: 2026-09-03
title: "User-facing Compound Research Handbook and Isolated Dev Preview"
status: active
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-09-03-cr-research-handbook-and-dev-preview.md"
language: "both"
estimated-effort: "large"
deviation-policy: "ask"
execution-report: ".cg-docs/work-reports/2026-09-03-cr-research-handbook-and-dev-preview.md"
completed-phases: [1, 2, 3, 4]
current-phase: 5
artifact-schema-version: 1
phases: 5
tags: [compound-research, documentation, handbook, onboarding, github-pages, dev-preview, research-workflow, provenance]
---
<!-- Created 2026-09-03. -->

# Plan: User-facing Compound Research Handbook and Isolated Dev Preview

## Objective

Give World Bank researchers who are somewhat new to Compound GPID a short,
research-first path to a successful Compound Research workflow. The handbook
will explain why CR exists, how to activate and use it, and what evidence and
judgment remain with the researcher. The documentation site will also expose a
continuously updated `dev` preview at `/dev/` without allowing that preview to
replace stable production documentation at the site root.

## Context

The approved brainstorm chooses a dedicated CR handbook section with shared CG
entry points. It prioritizes onboarding over exhaustive reference material and
uses the Kenya extreme-precipitation task as one deliberately short worked
example. The conceptual material is informed by the AI-for-knowledge-work and
AI-and-research presentations: generated answers are proposals, while reusable
research claims should retain source, evidence, locator, verification, and
review context.

The current repository already has:

- A static documentation shell in `docs/index.html` and `docs/assets/site.js`
  with relative assets, hash-based routes, a navigation manifest, and a
  Markdown renderer.
- `docs/navigation.json` as the public route manifest and
  `scripts/check-docs-site.js` as the navigation, link, skills-catalog, and
  site-shell validator.
- `scripts/rebuild-docs.js --all` producing a complete `docs/` build and
  `.docs-build-metadata.json`, with `doc-rebuild.yml` rebuilding main-only
  managed content and `pages.yml` deploying its verified artifact.
- Separate release build and deployment workflows in `release-docs.yml` and
  `release-pages.yml` that must be updated because a release deployment also
  replaces the entire Pages artifact.
- Existing exact-artifact and immutable-ref safeguards captured in
  [the verified Pages solution](../solutions/git-workflows/2026-08-13-verified-pages-artifact-and-release-tag-gates.md).

The documentation work is on `feat/cr-documentation`, created from
`origin/dev`. The previous automated documentation plan explicitly deferred
`/dev/`; the approved 2026-09-03 brainstorm supersedes that boundary.

The safe deployment shape is one combined artifact, not independent root and
subdirectory deployments. Each successful build assembles stable documentation
at the artifact root and development documentation beneath `dev/`. A single
Pages controller downloads and verifies the complete artifact before deploying
it. The unprivileged build job may execute the `dev` source to construct the
preview, but the privileged Pages job only verifies metadata and bytes using
trusted controller code from `main`; it never executes `dev` code or mutates a
downloaded artifact.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Provide a compact CR handbook section for World Bank researchers somewhat new to Compound GPID. | approved brainstorm |
| R2 | Explain why CR exists: source-to-claim traceability, epistemic uncertainty, selection opacity, amplified composition, human responsibility, and the boundary between generated proposals and accepted research knowledge. | AI-and-research presentation material; brainstorm |
| R3 | Explain prerequisites and research-suite activation with `suites: [cr]` or `suites: [cg, cr]`, including what a user should do when setup or dependencies are missing. | user request; current modular config |
| R4 | Guide a newcomer through `/cr-brainstorm`, `/cr-plan`, `/cr-work`, `/cr-review`, and `/cr-compound`, naming inputs, outputs, researcher decisions, and verification gates. | brainstorm; current CR prompts |
| R5 | Include one short Kenya extreme-precipitation workflow example covering activation, task framing, credible rainfall evidence, the definition decision, checked outputs, and review handoff without reproducing a full climate tutorial. | user request; local show-and-tell project |
| R6 | Explain the CR lifecycle `Scope -> Evidence -> Theory -> Method -> Execute -> Verify -> Communicate -> Maintain`, task types, routing, and human checkpoints. | practitioner-tour presentation material; current CR workflow |
| R7 | Explain evidence, provenance, Proof Carrying Claim in plain language, normative decisions, research-integrity boundaries, and what CR cannot establish alone. | presentation material; CR skills |
| R8 | Present CG and CR as first-class modules of one modular Compound GPID product and link the new handbook from existing CG entry points. | user request; charter; modular guide |
| R9 | Represent every new public page in `docs/navigation.json`, preserve existing link conventions, and pass navigation, link, accessibility-shell, and skills-catalog validation. | `docs/navigation.json`; `scripts/check-docs-site.js` |
| R10 | Publish a continuously updated preview at `https://gpid-wb.github.io/compound-gpid/dev/` from the `dev` branch; per-PR previews are not required. | user request |
| R11 | Keep stable production documentation at `/` sourced from `main`, and make every Pages deployment publish both the stable root and `/dev/` subtree in one complete artifact. | user request; GitHub Pages replacement semantics |
| R12 | Reject stale, incomplete, malformed, colliding, or digest-mismatched combined artifacts before Pages upload; preserve stable root when dev changes and preserve `/dev/` when main or release changes. | charter fail-loudly constraint; verified Pages solution |
| R13 | Do not execute mutable `dev` code with `pages: write` or `id-token: write`, do not rebuild or mutate a downloaded artifact in the privileged controller, and keep actions SHA-pinned with least privilege. | verified Pages solution; security boundary |
| R14 | Keep main managed-documentation rebuilds and release/tag validation correct while adding the combined site build; release deployment must also preserve `/dev/`. | existing `doc-rebuild.yml`, `release-docs.yml`, `release-pages.yml` |
| R15 | Add focused automated coverage for handbook routes, combined artifact construction, path isolation, source freshness, workflow permissions/order, release preservation, and runtime behavior under `/dev/`. | project testing requirements |
| R16 | Avoid new static-site frameworks, per-PR previews, exhaustive CR skill chapters, broad CG redesign, full climate tutorial, runtime GitHub API content, and external local data/code in the repository. | approved brainstorm; user scope decision |

## Implementation Steps

## Phase 1: Build the CR Handbook and Shared Entry Points

### 1. Define the CR handbook information architecture
- **Requirements**: R1, R8, R9
- **Files**: `docs/research/index.md`, `docs/navigation.json`, `docs/getting-started/index.md`, `docs/modular-guide.md`, `docs/workflows/index.md`, `docs/reference/commands.md`, `docs/skills/index.md`, `docs/skills/research.md`, `README.md`
- **Details**:
  - Create a focused `docs/research/` section with six public routes:
    `research`, `research-philosophy`, `research-first-workflow`,
    `research-short-example`, `research-lifecycle`, and
    `research-evidence-boundaries`.
  - Make `docs/research/index.md` the Start Here page. Use the existing
    navigation groups and progressive-disclosure style rather than creating a
    second handbook shell.
  - Add a dedicated Research Handbook navigation group or an equivalent
    clearly labeled sequence. Keep route IDs globally unique and descriptions
    useful to a newcomer scanning the site.
  - Add links from Getting Started, the Modular Guide, workflow overview,
    commands, and research skills pages. Update the README documentation
    table or research entry only where it makes the new route discoverable.
  - Keep command and skill details in their existing reference pages. The new
    pages should explain when to follow a link, not copy complete command
    contracts or skill bodies.
- **Test Scenarios**: all new route IDs are unique; all new Markdown files are in navigation; existing required routes remain unchanged; no new page is orphaned.
- **Tests**: `node scripts/check-docs-site.js`; focused navigation/link assertions added in Step 9.
- **Acceptance criteria**: a newcomer can find the CR handbook from the home page, Getting Started, or Modular Guide and see a clear ordered sequence without losing the existing CG route.

### 2. Draft the onboarding and philosophy chapters
- **Requirements**: R1, R2, R3, R7
- **Files**: `docs/research/index.md`, `docs/research/philosophy.md`
- **Details**:
  - Start Here must state the intended audience, what CR supports, what it
    does not replace, minimal installation/configuration prerequisites, and
    how to select `suites: [cr]` or `suites: [cg, cr]` in
    `compound-gpid.local.md`.
  - Show the first safe action and expected result. Include a compact
    recovery table or route for missing configuration, inactive CR capability,
    missing data/dependencies, and an unclear research question.
  - Explain the philosophy in ordinary research terms: resource -> evidence ->
    claim -> composition; source detachment; instability; hidden selection;
    fluent composition; and the human decision boundary.
  - Introduce Proof Carrying Claim only after explaining the plain-language
    idea that an important claim should carry the evidence and checks needed to
    inspect it. State that provenance supports traceability, not truth by
    itself, and that seeds/settings do not guarantee cross-provider identity.
  - Use the presentation materials as source guidance, but write handbook
    prose rather than reproducing the deck or its slide sequence.
- **Test Scenarios**: activation examples contain valid suite syntax; philosophy names the researcher responsibility boundary; no claim implies that CR proves truth or replaces expert review; pages remain concise.
- **Tests**: content-contract tests; `node scripts/check-docs-site.js`.
- **Acceptance criteria**: a reader who has not used `/cg-*` can explain why CR exists, activate it, identify the first command, and recover from the common onboarding blockers.

### 3. Draft the first workflow, short example, lifecycle, and boundaries chapters
- **Requirements**: R4, R5, R6, R7, R16
- **Files**: `docs/research/first-workflow.md`, `docs/research/short-example.md`, `docs/research/lifecycle.md`, `docs/research/evidence-boundaries.md`
- **Details**:
  - First Workflow should present the five CR commands in order. For each,
    answer only: what it is for, what it leaves behind, and what the researcher
    still decides. Include the handoff from each stage and a short blocked-path
    route.
  - Short Example should use the Kenya task with coordinates and the 2020 to
    present period. Show only the important stages: activate CR, classify or
    scope the question, identify a credible daily rainfall source, make the
    extreme-precipitation definition explicit, calculate location-level
    results, create maps/charts, and send the result through review. Make clear
    that the example is an illustrative workflow shape, not a completed
    climate finding.
  - Use the local show-and-tell project as source material for terminology and
    shape, but do not copy its data, scripts, generated images, absolute paths,
    or a full methods tutorial into the repository.
  - Lifecycle should distinguish lifecycle stages from task types and show how
    classification routes skills/review without deciding research quality.
  - Evidence and Boundaries should cover source records, claim support,
    verification, normative choices, research-integrity gates, and limitations.
- **Test Scenarios**: all five command names appear in order; the example includes activation and a review handoff; no local absolute path or large data asset is copied; the page remains a short orientation rather than a climate textbook.
- **Tests**: content-scope assertions; link/site validation; final manual review against the approved presentation and local example.
- **Acceptance criteria**: a newcomer can follow the documented route from suite activation to a small research output and knows what remains to be checked by a human.

### 4. Integrate the modular CG/CR story without redesigning the CG handbook
- **Requirements**: R8, R9, R16
- **Files**: `docs/getting-started/index.md`, `docs/modular-guide.md`, `docs/workflows/index.md`, `docs/reference/commands.md`, `docs/skills/index.md`, `docs/skills/research.md`, `docs/development/index.md`, `README.md`
- **Details**:
  - State consistently that CG and CR are two user-facing suites over a shared
    kernel and capability layer. Explain the practical rule: CG drives
    technical delivery; CR drives research work and can compose technical
    capabilities for implementation.
  - Link to the CR Start Here page at the first place a researcher chooses a
    route. Keep existing CG guidance intact and avoid rewriting unrelated
    handbook sections.
  - Add a maintainer note that public handbook content is manual source prose,
    while command tables and other declared managed regions remain generated
    from canonical sources.
  - Document the intended local preview URL and the distinction between stable
    root and development subtree in the development page, without presenting
    the preview as a release.
- **Test Scenarios**: CG-only, CR-only, and mixed suite explanations remain accurate; all new cross-links resolve; no generated native target is edited.
- **Tests**: `node scripts/check-docs-site.js`; Markdown link checks; final diff review.
- **Acceptance criteria**: existing CG users can understand the new modular boundary in one short guide and reach the CR handbook without a broad CG redesign.

## Phase 2: Define and Implement the Combined Documentation Artifact

### 5. Implement deterministic root-plus-preview site assembly
- **Requirements**: R10, R11, R12, R13, R14
- **Files**: `scripts/assemble-docs-site.js`, `scripts/rebuild-docs.js` if a shared fingerprint helper or CLI extension is required, `scripts/tests/assemble-docs-site.test.js`
- **Details**:
  - Define a versioned combined metadata schema containing the stable source
    branch/ref and SHA, dev source branch/ref and SHA, canonical-input
    fingerprints for both sources, the assembled site file list, and SHA-256
    digests for every published file.
  - Accept separately built stable and dev documentation roots and write one
    output tree: stable files at the output root, dev files beneath `dev/`.
    Reject traversal, symlinks, missing required roots, duplicate output paths,
    unexpected metadata, and any attempt to place dev files over stable files.
  - Apply a deterministic, visible development-preview marker to the copied
    `/dev/index.html` and identify the channel in metadata. Preserve relative
    `assets/`, `navigation.json`, and Markdown paths so the current site shell
    works at both `/` and `/dev/` without a second framework.
  - Keep the output writer atomic and no-write in verification mode. Verification
    must compare the complete file list and every digest, then compare the
    recorded canonical-input fingerprints with current source inputs using
    trusted code from the deployment controller.
  - Keep stable and dev source builds separate. The assembly script may run in
    an unprivileged builder, but the Pages controller must only call its
    verification path from the trusted checked-out `main` controller.
- **Test Scenarios**: deterministic two-run output; root and `dev/` trees coexist; dev cannot overwrite root; symlink/traversal/collision/missing-metadata failures; changed stable or dev fingerprint is rejected; metadata and published digests match exactly.
- **Tests**: `node --test scripts/tests/assemble-docs-site.test.js`; fixture-based negative tests.
- **Acceptance criteria**: the script can produce and verify one complete artifact whose root and `/dev/` contents have unambiguous source and digest provenance.

### 6. Extend site validation and runtime handling for two documentation roots
- **Requirements**: R5, R9, R10, R12, R15
- **Files**: `scripts/check-docs-site.js`, `docs/index.html` only if a reusable channel marker is needed, `docs/assets/site.js` only if runtime tests disprove relative-path behavior, `scripts/tests/check-docs-site.test.js`, `scripts/tests/docs-preview-runtime.test.js`
- **Details**:
  - Add an explicit validation-root option or equivalent environment contract so
    the same validator can validate a site tree against its matching source
    checkout. Preserve the current default behavior for the stable root.
  - Validate the stable and dev trees independently during the unprivileged
    build, including navigation coverage, internal Markdown links, required
    shell files, skills catalog, and level-one headings. Validate the combined
    output's required root and `/dev/` structure separately.
  - Confirm that the existing relative asset and hash-routing design works at
    `/dev/`. Do not add base-path string manipulation unless an HTTP smoke test
    demonstrates a real failure. If a change is needed, make it explicit and
    backward-compatible for root hosting.
  - Require the dev marker, correct route manifests, and no accidental links
    from stable pages into preview-only material unless intentionally documented.
- **Test Scenarios**: stable and dev sites pass independently; missing `/dev/index.html`, broken `/dev/navigation.json`, bad dev Markdown link, or absent marker fails; browser loads CSS, JavaScript, navigation, a page route, and search from `/dev/`.
- **Tests**: `node scripts/check-docs-site.js` against each tree; `node --test scripts/tests/check-docs-site.test.js scripts/tests/docs-preview-runtime.test.js`.
- **Acceptance criteria**: static validation and HTTP/browser smoke checks prove that the same site shell works at both URL depths and that the preview is visibly distinct.

## Phase 3: Wire Branch Builds and One Protected Pages Controller

### 7. Add an unprivileged combined-site build workflow
- **Requirements**: R10, R11, R12, R13, R14
- **Files**: `.github/workflows/docs-site-build.yml`, `.github/workflows/doc-rebuild.yml`, `scripts/assemble-docs-site.js`
- **Details**:
  - Add a workflow that runs for relevant documentation-input changes on
    `dev` and after a successful `Rebuild documentation` run on `main`. The
    relevant inputs include `docs/**`, canonical prompts/skills/agents, the
    documentation scripts, and the related workflow files. Avoid triggering a
    separate build for unrelated application code.
  - Check out or fetch exact `main` and `dev` source refs in separate working
    directories. Record both source SHAs before building and reject ambiguous
    refs. Build each documentation tree in an unprivileged job; the dev source
    may be executed only here, never in a Pages-permission job.
  - Rebuild managed content in temporary workspaces, validate each source tree,
    assemble the combined output, validate the combined structure, and upload
    exactly one short-retention combined artifact plus its hidden metadata.
  - For a main-triggered build, ensure the source checkout includes the
    post-rebuild state produced by `doc-rebuild.yml`; for a dev-triggered build,
    use current main for the stable root and current dev for the preview. A
    source-input fingerprint, rather than an unrelated code-only commit, should
    determine whether the artifact is stale.
  - Keep `doc-rebuild.yml` responsible for the main-only deterministic managed
    rebuild and narrow docs bot commit. Stop treating its single-root artifact
    as the Pages deployment input; update or remove only obsolete upload steps
    after the combined artifact path is covered by tests.
- **Test Scenarios**: dev documentation change produces a combined artifact; main bot rebuild produces a combined artifact; no-op main rebuild still permits a combined build; failed source validation produces no deployable artifact; unrelated code change does not cause unnecessary docs build.
- **Tests**: workflow contract tests in `tests/docs-automation.Tests.ps1` and `tests/docs-preview.Tests.ps1`; Node assembly tests.
- **Acceptance criteria**: every relevant main or dev documentation change can produce a complete, provenance-bearing combined artifact without Pages permissions.

### 8. Refactor main Pages deployment to consume only the combined artifact
- **Requirements**: R10, R11, R12, R13, R14
- **Files**: `.github/workflows/pages.yml`, `scripts/assemble-docs-site.js`, `tests/docs-automation.Tests.ps1`, `tests/docs-preview.Tests.ps1`
- **Details**:
  - Change `pages.yml` to trigger only after a successful combined-site build.
    Download by exact workflow-run ID and verify the complete combined metadata,
    file list, and digests before any Pages upload.
  - Check out current `main` only for trusted verification and fetch the current
    `dev` ref as data. Compare the artifact's stable and dev canonical-input
    fingerprints with the current approved inputs. Skip stale artifacts rather
    than deploying them.
  - Require both the stable root and `/dev/` subtree, reject any path outside
    the expected site root, and upload the unchanged combined site exactly once.
    The controller must not call a source rebuild, generate release notes, or
    mutate the downloaded tree.
  - Preserve SHA-pinned actions, `pages: write` and `id-token: write` only in
    the deployment job, `contents: read`, and a single serialized `pages`
    concurrency group. Do not create a second dev Pages deployment.
- **Test Scenarios**: successful combined artifact deploys; stale main or dev fingerprint skips; missing dev subtree, digest mismatch, or path collision blocks; Pages upload occurs after verification; privileged job contains no dev checkout execution or write-mode rebuild.
- **Tests**: focused Pester workflow contracts; `node --test scripts/tests/assemble-docs-site.test.js`; site validation.
- **Acceptance criteria**: the main Pages path publishes stable root plus `/dev/` from one exact artifact and cannot deploy a dev-only or stale artifact.

### 9. Preserve the preview through release and tag deployments
- **Requirements**: R11, R12, R13, R14
- **Files**: `.github/workflows/release-docs.yml`, `.github/workflows/release-pages.yml`, `tests/docs-automation.Tests.ps1`, `tests/docs-preview.Tests.ps1`, `.github/prompts/cg-release.prompt.md` only if the combined release artifact changes an existing handoff contract
- **Details**:
  - Keep the release builder unprivileged and immutable-tag validated. Build the
    tagged stable release tree and a separately built current `dev` preview,
    then assemble and upload one combined release artifact.
  - Preserve the existing tag lineage, durable release payload, latest-release,
    and action-pinning gates. The release-pages controller must verify the
    release artifact and current dev fingerprint before uploading it.
  - Ensure a release deployment cannot erase `/dev/`, and a dev update cannot
    change the stable release root. If current dev changes during release
    preparation, fail closed or require a fresh combined build rather than
    silently deploying an old preview.
  - Keep `/cg-release` ordering unchanged unless the combined artifact requires
    a precise documentation of the new wait/verification state. Release API
    publication must remain after successful tag-site deployment.
- **Test Scenarios**: stable and four-component prerelease tag paths preserve `/dev/`; current dev staleness blocks; release payload and tag gates still run before API publication; release-pages never executes tagged or dev source with Pages credentials.
- **Tests**: existing release contract tests plus new combined-artifact assertions in the focused Pester files.
- **Acceptance criteria**: every supported release deployment publishes a complete root-plus-preview artifact without weakening immutable release controls.

## Phase 4: Add Regression Coverage and Local Preview Checks

### 10. Add handbook and combined-artifact regression tests
- **Requirements**: R1, R3, R4, R5, R6, R7, R9, R12, R15, R16
- **Files**: `scripts/tests/check-docs-site.test.js`, `scripts/tests/docs-preview-runtime.test.js`, `scripts/tests/assemble-docs-site.test.js`, `tests/docs-preview.Tests.ps1`, `tests/Run-Tests.ps1`, existing `tests/docs-automation.Tests.ps1`
- **Details**:
  - Add content-contract assertions for the six CR routes, valid suite
    activation syntax, all five commands in order, lifecycle stages, PCC and
    responsibility boundaries, Kenya coordinates/date range, short-example
    scope, and no external absolute paths.
  - Add Node fixtures for deterministic assembly, source metadata, digest
    verification, missing roots, symlink rejection, traversal, output
    collisions, stale fingerprints, marker injection, and no-write failure.
  - Add Pester contracts for dev branch triggers, combined artifact naming,
    source/ref checks, permissions, action SHA pinning, exact workflow-run
    consumption, stale gates, root/dev path isolation, and release preservation.
  - Register any new Pester file in the canonical runner. Do not change the
    safe invocation behavior or add a directory-level `Invoke-Pester` call.
- **Test Scenarios**: each new negative condition fails loudly; each new Pester file is discovered; content tests fail if a future edit turns the short example into an exhaustive tutorial or drops activation/recovery guidance.
- **Tests**: `node --test scripts/tests/assemble-docs-site.test.js scripts/tests/check-docs-site.test.js scripts/tests/docs-preview-runtime.test.js`; registered focused Pester files.
- **Acceptance criteria**: the highest-risk content, artifact, and workflow contracts are executable locally without credentials or a live Pages deployment.

### 11. Validate the site over HTTP at both deployment paths
- **Requirements**: R9, R10, R12, R15
- **Files**: `scripts/tests/docs-preview-runtime.test.js`, `scripts/evidence/` only if existing browser harness reuse is necessary, documentation validation outputs
- **Details**:
  - Build a temporary combined site fixture and serve it over HTTP, not via
    `file://`. Use the existing Playwright dependency and a minimal local
    server harness.
  - Verify root and `/dev/` index loading, relative CSS/JavaScript, navigation
    fetches, representative handbook routes, internal Markdown link conversion,
    search, and the visible development marker.
  - Keep this a smoke test for route and shell behavior. Do not capture or
    commit screenshots, local data, or browser artifacts as public handbook
    content unless an existing evidence contract explicitly requires them.
- **Test Scenarios**: root works; `/dev/` works; missing asset or navigation file produces the expected unavailable state; browser never requests root `navigation.json` while rendering the preview.
- **Tests**: `node --test scripts/tests/docs-preview-runtime.test.js`.
- **Acceptance criteria**: the requested preview URL shape is proven locally with the same interactive site behavior as the stable root.

## Phase 5: Complete Gates and Verify the Public Preview

### 12. Run final repository and deployment verification
- **Requirements**: R9, R10, R11, R12, R13, R14, R15, R16
- **Files**: all touched files; `.cg-docs/work-reports/` only through the normal work workflow after implementation
- **Details**:
  - Run the documentation validator, focused Node tests, modular registry and
    target checks if any canonical `.github/` assets changed, and the full
    project test runner at the end. Use the repository's safe Pester workflow
    and inspect `tests/last-run.json` rather than parsing unsafe terminal
    pipelines.
  - Review the final diff for credentials, data, absolute local paths,
    accidental generated-target edits, broad handbook duplication, and changes
    outside the approved artifact boundary.
  - Push the feature branch and merge the implementation into `dev` through the
    normal PR process. Confirm the dev workflow builds and deploys the current
    combined artifact, then inspect
    `https://gpid-wb.github.io/compound-gpid/dev/` for the handbook routes and
    visible preview marker.
  - Confirm the stable root remains unchanged except for intended main content,
    and record CI evidence that a later main/release deployment retains `/dev/`.
  - Do not mark the work complete on local tests alone: the final state requires
    a successful relevant GitHub Actions run and a reachable preview URL, or a
    clearly reported external repository-settings blocker.
- **Test Scenarios**: all local gates pass; a dev documentation change reaches `/dev/`; root stable content remains present; release/main workflow contracts retain both trees; stale runs do not deploy.
- **Tests**: `node scripts/check-docs-site.js`; focused Node tests; `python -m pytest scripts/tests -q`; canonical Pester runner and `tests/last-run.json`; GitHub Actions run evidence; HTTP check of the preview URL.
- **Acceptance criteria**: the handbook is discoverable and usable, the preview is continuously updated from `dev`, and no tested deployment path can replace stable materials with a dev-only or incomplete artifact.

## Testing Strategy

- **Documentation contracts**: validate navigation coverage, required headings,
  internal links, route IDs, activation examples, command order, lifecycle
  language, and concise example boundaries.
- **Build behavior**: use dependency-free Node tests with temporary fixture
  trees to prove deterministic assembly, source metadata, symlink/traversal
  rejection, path disjointness, no-write verification, and digest integrity.
- **Workflow contracts**: use Pester string/ordering/permission assertions for
  branch triggers, artifact names, workflow-run gates, stale handling,
  action-SHA pinning, least privilege, and the absence of independent dev
  deployment paths.
- **Browser behavior**: use existing Playwright tooling against a local HTTP
  server to test both root and `/dev/` relative paths, navigation, search, and
  representative CR pages.
- **Repository gates**: run `node scripts/check-docs-site.js`, focused Node
  tests, relevant Python tests, target parity only if canonical `.github/`
  sources change, and the canonical safe Pester runner at the end. No test
  requires GitHub credentials, a live release, or a live Pages deployment.

## Documentation Checklist

- [ ] Six CR handbook routes have creation-date comments and clear newcomer-facing headings.
- [ ] Start Here documents prerequisites, `suites:` activation, first action, expected artifacts, and recovery paths.
- [ ] Philosophy uses the presentation's resource-to-claim framing without copying the slide deck.
- [ ] First Workflow explains the five CR commands and researcher decisions without duplicating complete references.
- [ ] Short Example uses the Kenya precipitation-risk task, stays compact, and contains no local absolute paths, data, or copied scripts.
- [ ] Lifecycle and Evidence/Boundaries explain task types, PCC, provenance, normative decisions, and limitations.
- [ ] Getting Started, Modular Guide, workflow, commands, skills, README, and development pages link the new route appropriately.
- [ ] `docs/navigation.json` contains every new page exactly once.
- [ ] Development documentation explains the stable root plus `/dev/` artifact model and recovery behavior.
- [ ] No changes are made to protected charter body content.

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| A dev-only Pages deployment replaces the stable root or a release deployment deletes `/dev/`. | High | P0 | Use one complete combined artifact for main and release paths; require root and `/dev/` trees and test path disjointness before upload. |
| A combined artifact is stale because main or dev advances during the build. | Medium | High | Record source SHAs and canonical-input fingerprints; compare current approved inputs in the protected controller and skip stale artifacts. |
| Mutable dev code executes with Pages credentials. | Medium | P0 | Execute dev source only in an unprivileged builder; privileged controller checks out trusted main and performs verification only. |
| Pages uploads a modified or partial downloaded artifact. | Medium | P0 | Verify complete file list and SHA-256 digests, prohibit rebuild/mutation after download, then upload the exact unchanged site tree. |
| Relative assets or hash routes break beneath `/dev/`. | Medium | High | Preserve the existing relative layout, add HTTP browser smoke tests, and change `site.js` only if a demonstrated failure requires it. |
| New CR pages become another scattered reference layer or overwhelm newcomers. | Medium | Medium | Keep six focused routes, answer only the approved onboarding questions, and link to existing detailed command/skill references. |
| The Kenya example leaks local data, scripts, or absolute paths. | Low | High | Treat the external show-and-tell folder as source material only; add content/path assertions and inspect the final diff. |
| Release or main workflow contracts are weakened while adding the preview. | Medium | High | Extend existing exact-artifact and immutable-release tests; require release workflows to publish the combined artifact and retain current gates. |
| New tests are not run by the canonical runner or Pester invocation crashes the host. | Medium | Medium | Register focused files, preserve Pester 4.10.1 safety rules, and use the canonical runner once at the end. |
| GitHub Pages repository settings cannot support the requested project URL or deployment controller. | Low | High | Verify repository Pages configuration in final CI; stop and report the exact settings blocker rather than silently using a second site. |

## Out of Scope

- Per-pull-request preview environments.
- A full extreme-precipitation or climate-analysis tutorial.
- Exhaustive first-release documentation for every CR skill and reference file.
- A separate CR website, static-site framework, or independent Pages project.
- A broad redesign of the existing CG handbook or a second navigation shell.
- Runtime GitHub API retrieval for documentation content.
- Two independent Pages deployments intended to overlay root and `/dev/`.
- Changes to the project charter body, release semantics, or the narrow
  documentation bot-commit exception.
- Copying data, generated charts, scripts, screenshots, or absolute paths from
  the external Kenya show-and-tell project into this repository.
- Hand-editing generated `.claude/`, `.agents/`, `.opencode/`, or `.kilo/`
  targets.

## Completion Contract

### Outcome

The public handbook contains a compact CR onboarding route with philosophy,
activation, first workflow, Kenya example, lifecycle, and evidence/boundaries
chapters. A continuously updated Pages artifact contains stable `main`
documentation at `/` and current relevant `dev` documentation at `/dev/`, with
both source provenance and complete file digests verified before deployment.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Six CR routes, shared entry points, navigation coverage, and resolved links. | `node scripts/check-docs-site.js` and focused content tests | yes |
| V2 | 1 | Start Here gives valid activation, prerequisites, expected outputs, and recovery routes. | Documentation contract tests and rendered page review | yes |
| V3 | 1 | Kenya example is short, includes activation and review handoff, and contains no external local assets or full tutorial. | Content-scope tests and final diff inspection | yes |
| V4 | 2 | Combined artifact is deterministic, root/dev paths are disjoint, dev marker exists, and metadata covers source inputs and all files. | `node --test scripts/tests/assemble-docs-site.test.js` | yes |
| V5 | 2 | Stable and dev shells, navigation, links, relative assets, hash routes, and search work under both URL depths. | `node --test scripts/tests/check-docs-site.test.js scripts/tests/docs-preview-runtime.test.js` | yes |
| V6 | 3 | Main/dev source build is unprivileged as required and only one protected controller deploys the complete combined artifact. | `tests/docs-automation.Tests.ps1` and `tests/docs-preview.Tests.ps1` | yes |
| V7 | 3 | Stale fingerprints, missing trees, path collisions, missing metadata, digest mismatch, and incomplete artifacts fail before upload. | Negative Node/Pester fixtures | yes |
| V8 | 3 | Release and prerelease deployment preserve `/dev/` and retain immutable release gates. | Release workflow contract tests and CI evidence | yes |
| V9 | 4 | New Pester files are registered and all focused checks pass without credentials. | `tests/last-run.json` plus Node test output | yes |
| V10 | final | Dev update reaches the public preview while stable root remains intact through main/release paths. | GitHub Actions URLs and `https://gpid-wb.github.io/compound-gpid/dev/` | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | 1 | Handbook uses progressive disclosure and remains compact; detailed reference material is linked, not duplicated. | Content review and scope assertions |
| C2 | 1 | Existing CG handbook navigation and modular language remain accurate. | Site validator and targeted link tests |
| C3 | 2 | Stable files are at artifact root, dev files are beneath `dev/`, and no output path overlaps. | Assembly manifest and collision fixtures |
| C4 | 2 | Metadata and SHA-256 digests cover both source inputs and every published file. | Assembly verification tests |
| C5 | 3 | Pages permissions are confined to the protected controller; no dev code executes there. | Workflow permissions/order tests |
| C6 | 3 | Main, release, and prerelease paths all publish one complete combined artifact. | Workflow contract tests |
| C7 | 3 | Stale or incomplete artifacts fail closed; no downloaded artifact is regenerated or mutated. | Freshness, digest, and no-mutation tests |
| C8 | 4 | No secrets, data, absolute external paths, generated-target edits, or new framework dependencies enter the change. | Final diff and dependency review |
| C9 | 4 | Pester safety rules and canonical runner registration remain intact. | Runner check and `tests/last-run.json` |

### Boundaries

- Allowed: six `docs/research/` handbook pages, targeted CG handbook links,
  navigation updates, deterministic Node assembly/verification, compatible
  validator extensions, combined build and Pages workflow changes, release
  workflow updates, focused tests, and maintainer documentation.
- Out of scope: per-PR previews, exhaustive skill chapters, full climate
  tutorial, independent root/dev deployments, a second site framework, runtime
  API content, charter changes, release-semver changes, and external local
  example assets.

### Iteration Policy

1. Finalize page purposes and content contracts before changing deployment
   workflows.
2. Implement combined-artifact fixtures and path-isolation verification before
   wiring the Pages controller.
3. Preserve the current relative site shell unless HTTP tests demonstrate a
   real `/dev/` failure; do not add speculative base-path logic.
4. Keep build jobs unprivileged when executing dev source and keep the protected
   controller verification-only.
5. Run focused Node/site checks after each implementation slice; run the
   canonical Pester suite only after all workflow edits are complete.
6. Regenerate native targets only if canonical `.github/` assets change; never
   hand-edit generated copies.
7. Under `deviation-policy: ask`, pause before widening permissions, changing
   the artifact boundary, adding a dependency, changing release order, or
   expanding the chapter set.

### Blocked-Stop Conditions

- A single complete Pages artifact cannot safely contain both stable root and
  `/dev/` content.
- The controller cannot verify source freshness, metadata, complete file lists,
  and digests before upload.
- Any privileged job would execute mutable dev code, rebuild downloaded files,
  or deploy a partial overlay.
- Main or release deployment would erase `/dev/`, or dev deployment would alter
  stable root content.
- Relative assets, navigation, search, or Markdown routes fail at `/dev/` and
  no minimal compatible repair is available.
- Required Node, Python, Pester-safe, or CI evidence fails without a clear local
  repair or explicitly approved exception.
- Pages repository settings prevent the requested public URL.
- The implementation would require protected charter changes, a broader bot
  exception, per-PR previews, or an out-of-scope tutorial/framework.
