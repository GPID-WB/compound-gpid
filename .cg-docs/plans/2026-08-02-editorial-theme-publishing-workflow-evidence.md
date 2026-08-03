---
date: 2026-08-02
title: "Editorial Theme, Publishing Workflow, and Browser Evidence"
status: blocked
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-08-02-completion-dossier-and-curated-artifact-themes.md"
split-from: ".cg-docs/plans/2026-08-02-generic-markdown-publishing-curated-themes.md"
depends-on-plan: ".cg-docs/plans/2026-08-02-generic-markdown-reference-publishing-core.md"
language: "both"
estimated-effort: "medium"
deviation-policy: "ask"
artifact-schema-version: 1
phases: 4
tags: [editorial-theme, html, publishing-skill, playwright, accessibility, cross-platform]
---

# Plan: Editorial Theme, Publishing Workflow, and Browser Evidence

## Objective

Port the approved editorial visual system from immutable source objects as a
second presentation-only theme, expose explicit theme selection through the
canonical publishing workflow on every supported agent platform, and produce
reproducible automated and attested browser evidence for both themes.

## Context

This is the second replacement unit created after review of
`.cg-docs/plans/2026-08-02-generic-markdown-publishing-curated-themes.md`. It is
blocked until
`.cg-docs/plans/2026-08-02-generic-markdown-reference-publishing-core.md` is
completed with current required evidence. That dependency supplies the generic
document model, trusted semantic markup, `reference` theme, provenance schema
2, mode matrix, destination ownership, safe resources, non-clobbering writer,
generic CLI, launchers, and context exclusions. This Plan must consume those
contracts rather than redesign them.

### Immutable Editorial Inputs

The visual source is pinned to Git commit
`52fc749ed484af2246dd7152b032f4dd01e86621` on the historical
`refactor/modular-compound-gpid` line:

| Input | Path at pinned commit | Git blob |
|-------|-----------------------|----------|
| Design system | `.github/skills/cg-skill-standalone-html-brief/references/design-system.md` | `8176439ea8ea60cdb6c541a8fdd6baced3dbc6cf` |
| Editorial template | `.github/skills/cg-skill-standalone-html-brief/assets/editorial-brief-template.html` | `aefb61c65acecc2ec07878191d9a28191fc8aed2` |

Implementation preflight must resolve the commit and both blobs exactly with
Git object reads. A moved branch name is irrelevant after the object check. If
the commit or either blob is unavailable or mismatched, implementation stops;
the agent must not recreate an "approximately similar" design from memory.
The accepted tokens and supported component rules are then frozen in the
repository theme contract so runtime has no Git-branch dependency.

### Supported Editorial Semantics

The editorial theme may style only semantic nodes emitted by the completed
core:

- headings, full-width section rhythm, navigation, paragraphs, lists, tables,
  code, images, provenance, and generic callouts;
- exact `DECISION`, `PROS`, and `CONS` callout markers may receive decision-band
  and tradeoff treatments;
- source tables may receive explicit comparison-table treatment without
  changing their cells or interpreting a recommendation;
- fenced diagram languages remain visible code; timelines, architecture
  diagrams, metrics, approach selection, paired callout grouping, and other
  source-specific compositions are not inferred in version 1.

This narrows the alternate template's component catalog to deterministic
source-backed structures. A future schema may add explicit timeline or diagram
nodes; this Plan must not infer them from headings or prose.

### Extended Theme Mode Matrix

The completed core matrix remains controlling. This Plan adds `editorial`
theme contract version 1 and these cases:

- Explicit `--theme editorial` wins for render, automatic generation when
  enabled, validation-only, and check.
- Bare render, automatic, and check reuse `editorial` from valid owned
  provenance schema 2; they do not revert to `reference`.
- Missing output and legacy schema 1 use the document-type default:
  Brainstorm, Plan, and generic document use `reference`; the registry reserves
  completion report for `editorial` without adding a report parser or workflow.
- A recorded known theme with an older contract version is stale and rerenders
  with the current version of the same theme.
- A recorded unknown theme is stale for check and blocks mutation until the
  user supplies a registered explicit theme.
- Validation-only never consults existing output. HTML-disabled automatic mode
  validates an explicit theme but does not inspect or mutate output bytes.

### Evidence Architecture

The current evidence schema 1 validator remains byte-for-byte behaviorally
compatible for the completed Brainstorm/Plan record. This Plan adds exact
schema 2 dispatch rather than changing shared constants:

- schema 1 retains its two artifact kinds, three viewports, Open Design
  identity, fields, and checks;
- schema 2 requires unique `(documentClass, themeName)` cells for technical,
  decision, and editorial fixtures under both `reference` and `editorial`;
- schema 2 records source/view/screenshot/print hashes, provenance identity,
  Node, Playwright, Chromium, and axe-core versions, automated measurements,
  and bounded manual attestations;
- unknown versions and cross-version fields fail.

Add a pinned development-only Node harness using `package.json` and committed
`package-lock.json`, Playwright Chromium, and axe-core. The producer opens local
standalone HTML, computes DOM geometry and accessibility results, captures
screenshots and print PDFs, and writes the schema 2 manifest. It must run before
the Python validator. It may use the network only during explicit dependency
or browser installation, never during evidence capture or publisher runtime.

Automated checks include offline load, nonblank output, page overflow, bounded
element geometry, reachable navigation/tables, first-viewport identity,
sequential headings, keyboard focus order, visible focus, axe violations and
contrast, 200 percent zoom, reduced-motion behavior, complete provenance, and
print-PDF production. Print readability and any judgment not reducible to a
stable measurement require an attestation with reviewer, UTC timestamp,
fixture/theme identity, check name, result, and bounded note; a bare boolean is
invalid.

Screenshots and print artifacts live under
`.cg-docs/views/evidence/curated-themes/**`, so existing generated-view body and
diff exclusions apply. The metadata-only manifest lives under
`.cg-docs/work-reports/`. Binary sentinels must prove audit, summary, review,
commit/PR, release, Brain, and duplicate-content surfaces never load evidence
asset bodies.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Require the completed core Plan and verify its current required evidence before implementation. | Review P2.8 |
| R2 | Verify the pinned editorial commit and blob identities before extracting or changing theme code. | Review P1.3 |
| R3 | Register stable `editorial` theme contract version 1 with the exact approved core tokens, typography, geometry, responsive, and print rules. | Brainstorm: Decision; pinned design inputs |
| R4 | Keep both themes presentation-only and semantically equivalent; style only deterministic source-backed nodes and defer unsupported rich components. | Review P2.7 |
| R5 | Extend the completed mode matrix for explicit, recorded, default, legacy, old-version, unknown, validation-only, and HTML-disabled editorial cases. | Review P2.4 |
| R6 | Add `/cg-render-doc` and `cg-skill-markdown-publishing` as orchestration for deterministic repository tooling, never model-authored bespoke HTML. | Roadmap feature |
| R7 | Keep `.github/` canonical, finish all canonical prompt/skill/shared edits before one generated-target pass, and verify Copilot, Claude Code, Codex, and OpenCode parity. | Review P2.8 and P3.1 |
| R8 | Add a pinned Playwright/Chromium/axe-core development harness that produces measured browser evidence before validation. | Review P1.2 |
| R9 | Define evidence schema 2 exactly while preserving schema 1 dispatch unchanged and rejecting unknown/mixed versions. | Review P2.5 |
| R10 | Store binary evidence under the excluded views namespace and prove every model/review/release path remains metadata-only. | Review P2.6 |
| R11 | Use valid canonical Pester basenames and enumerate target Python modules in focused gates. | Review P1.4 |
| R12 | Document immutable design provenance, themes, workflow, browser evidence, recovery, platform behavior, and the separate completion-report boundary. | Brainstorm: Requirements |

## Phase 1: Immutable Editorial Theme

### 1. Verify and freeze the editorial design inputs

- **Requirements**: R1, R2, R3
- **Files**:
  - `scripts/artifact_views/themes/editorial.py` (new)
  - `scripts/artifact_views/themes/contract.py`
  - `scripts/artifact_views/tests/snapshots/design-contract-editorial.json` (new)
  - `scripts/artifact_views/tests/test_themes.py`
  - developer documentation for theme provenance
- **Details**:
  - Preflight the completed core Plan status, execution report, and required
    evidence before any implementation mutation.
  - Resolve the pinned commit and both blobs with `git cat-file`/`git rev-parse`.
    Compare exact IDs above and stop on absence or mismatch.
  - Freeze editorial version 1 with the approved tokens: ink `#181816`, paper
    `#fbfbf8`, coral `#e94f2d`, teal `#087c70`, blue `#2856c7`, yellow
    `#f2c84b`, documented soft/success/danger/line values, `1180px` content
    width, and radius no greater than `6px`.
  - Use Georgia display, Trebuchet MS body/control, and Consolas code stacks with
    system fallbacks and no external fonts.
  - Record commit, blob IDs, supported source-backed components, and explicitly
    deferred components in the frozen contract and documentation. Runtime
    modules contain the accepted design and never read Git history.
- **Test Scenarios**: exact object preflight; missing/mismatched object;
  immutable registry; duplicate theme; frozen token snapshot; no external
  resource tokens; core dependency incomplete.
- **Tests**: Git object preflight command; `pytest -q scripts/artifact_views/tests/test_themes.py scripts/artifact_views/tests/test_design_contract.py`
- **Acceptance criteria**: the exact accepted source is auditable and the
  runtime editorial contract is stable, standalone, and independent of the
  branch name.

### 2. Render editorial presentation from shared semantic nodes

- **Requirements**: R3, R4, R5
- **Files**:
  - `scripts/artifact_views/themes/editorial.py` (new)
  - `scripts/artifact_views/themes/components.py`
  - `scripts/artifact_views/renderer.py`
  - `scripts/artifact_views/cli.py`
  - `scripts/artifact_views/publishing_cli.py`
  - renderer, theme, accessibility, provenance, CLI, and integration tests
- **Details**:
  - Add warm paper, grid-textured unframed hero treatment, full-width section
    rhythm, visible borders, restrained hard shadows, multi-accent roles,
    editorial typography, responsive `980px`/`720px` behavior, and print rules.
  - Style source tables as comparison surfaces without changing cells. Style
    `DECISION`, `PROS`, and `CONS` callouts distinctly without inferring a
    selected approach or pairing unrelated blocks.
  - Do not render timelines, architecture diagrams, invented metrics, or
    source-specific summaries. Fenced diagrams remain code.
  - Add `editorial` to the completed registry and mode matrix. Preserve
    `reference` defaults for strict and generic documents and reserve the future
    completion-report default without implementing that document type.
  - Compare semantic DOM summaries across themes: landmarks, heading order,
    source owners, links, tables, callout identities, and provenance fields must
    match; only approved presentation metadata and CSS differ.
- **Test Scenarios**: strict and generic sources in both themes; explicit and
  recorded editorial; missing/legacy/old/unknown theme; HTML-disabled and
  validation-only modes; long titles/words; dense tables; every callout;
  responsive and print contract tokens; no remote assets or scripts.
- **Tests**: `pytest -q scripts/artifact_views/tests/test_themes.py scripts/artifact_views/tests/test_renderer.py scripts/artifact_views/tests/test_generic_renderer.py scripts/artifact_views/tests/test_design_contract.py scripts/artifact_views/tests/test_accessibility.py scripts/artifact_views/tests/test_provenance.py scripts/artifact_views/tests/test_cli.py scripts/artifact_views/tests/test_publishing_cli.py scripts/artifact_views/tests/test_integration.py scripts/artifact_views/tests/test_publishing_integration.py`
- **Acceptance criteria**: editorial is visually faithful within the supported
  semantic vocabulary and cannot alter or omit canonical source meaning.

## Phase 2: Publishing Workflow And Platform Parity

### 3. Add the publishing skill and `/cg-render-doc`

- **Requirements**: R5, R6, R7, R11
- **Files**:
  - `.github/skills/cg-skill-markdown-publishing/SKILL.md` (new)
  - `.github/skills/cg-skill-markdown-publishing/references/theme-contract.md` (new)
  - `.github/prompts/cg-render-doc.prompt.md` (new)
  - `.github/shared/artifact-view.contract.md` only if the completed core does
    not already expose the two-theme orchestration requirements
  - prompt and target tests
- **Details**:
  - Route Brainstorms and Plans to `cg-render-artifact`; route other accepted
    Markdown to `cg-render-markdown`. The generic command still rejects typed
    roots directly.
  - Parse explicit `--theme reference|editorial`, `--check`, `--validate-only`,
    and constrained `--output`. Do not ask a model to compose or rewrite HTML.
  - An agent may explain theme differences and recommend an exact user-visible
    option, but cannot silently select or persist a subjective theme.
  - Document source authority, defaults, recorded-theme regeneration, unknown
    theme recovery, resource restrictions, and context exclusions in the skill.
  - Treat generator mapping and shared infrastructure as test-first and
    conditional because canonical prompts/skills are auto-discovered.
- **Test Scenarios**: typed/generic routing; explicit themes; bare recorded
  editorial rerender; check and validation-only; unsafe source/output;
  recommendation without silent selection; prompt tools and skill bundle.
- **Tests**: focused prompt and target Python tests; safe Pester command in Step
  4 after all canonical content is stable.
- **Acceptance criteria**: the user workflow invokes deterministic local tools
  with explicit presentation choice and no schema bypass or bespoke model HTML.

### 4. Generate all platform targets once and verify parity

- **Requirements**: R7, R11
- **Files**:
  - `scripts/cg_generate_targets.py` and target mapping only if focused tests
    prove auto-discovery insufficient
  - generated `.claude/`, `.agents/`, and `.opencode/` targets
  - `scripts/tests/test_target_mapping.py`
  - `scripts/tests/test_target_closure.py`
  - `scripts/tests/test_target_ownership.py`
  - `scripts/tests/test_target_packaging.py`
  - `scripts/tests/test_target_documentation.py`
  - `scripts/tests/test_target_determinism.py`
  - `scripts/tests/test_target_path_safety.py`
  - `scripts/tests/test_target_drift.py`
  - `tests/prompt-tools.Tests.ps1`
- **Details**:
  - Finish every canonical `.github` prompt, skill, reference, and shared
    contract edit before generation.
  - Generate targets once from canonical sources; never hand-edit generated
    copies. Verify the new skill's bundled reference closure.
  - Enumerate the complete focused Python target gate rather than saying
    "target tests" generically.
  - Run Pester with the registered basename `prompt-tools`, not a filename.
    Inspect the durable artifact for exact filtered identity and per-file pass.
- **Test Scenarios**: canonical auto-discovery; bundled reference; target
  ownership and closure; deterministic bytes; path safety; stale/dirty target;
  command and tool parity on all supported targets.
- **Tests**: `pytest -q scripts/tests/test_target_mapping.py scripts/tests/test_target_closure.py scripts/tests/test_target_ownership.py scripts/tests/test_target_packaging.py scripts/tests/test_target_documentation.py scripts/tests/test_target_determinism.py scripts/tests/test_target_path_safety.py scripts/tests/test_target_drift.py`; `execution_subagent` runs `. tests\Run-Tests.ps1 -File @('prompt-tools')`, requiring `passed: true`, `failedCount: 0`, `filteredFiles: ['prompt-tools']`, and a passing file record.
- **Acceptance criteria**: all canonical and generated platforms expose the same
  deterministic workflow and the generated tree is clean after a single pass.

## Phase 3: Reproducible Browser Evidence

### 5. Add the pinned evidence producer and exact schema 2

- **Requirements**: R8, R9, R10
- **Files**:
  - `package.json` (new)
  - `package-lock.json` (new)
  - `scripts/capture_artifact_view_evidence.js` (new)
  - `scripts/tests-js/artifact-view-evidence.test.js` (new)
  - `scripts/artifact_views/evidence.py`
  - `scripts/validate_artifact_view_evidence.py`
  - `scripts/artifact_views/tests/test_evidence.py`
  - `scripts/artifact_views/tests/fixtures/publishing/` (new)
- **Details**:
  - Pin Playwright and axe-core as development dependencies through the lockfile
    and record Node, package, and installed Chromium versions in every manifest.
  - Add `npm` scripts for evidence unit tests and capture. Evidence capture must
    run with network disabled after local dependency/browser installation.
  - Render technical, decision, and editorial Markdown fixtures with both
    themes using fixed source and generation inputs.
  - Use Playwright to open each local HTML, execute measured checks, capture
    `390x844`, `768x1024`, `1024x768`, `1440x900`, and `1920x1080`
    screenshots, and print a PDF. Inject the locally installed axe script into
    the browser only; never add it to published HTML.
  - Define schema 2 in separate validation functions and constants. Require six
    unique document/theme cells, exact viewport sets, file hashes, provenance,
    producer versions, measured results, and structured manual attestations.
    Leave schema 1 code and accepted fields unchanged; dispatch by exact
    integer version and reject unknown/mixed data.
  - Fail capture on browser console errors, network requests, blank output,
    page overflow, invalid geometry, inaccessible focus/navigation, axe
    violations, provenance mismatch, or missing print bytes.
- **Test Scenarios**: deterministic manifest ordering; all six cells; missing or
  duplicate cell; stale hash; missing viewport/check; false measurement;
  malformed/manual bare boolean; unknown schema; mixed schema fields; unchanged
  schema 1 fixture; blocked network; external resource attempt; console error.
- **Tests**: `npm ci`; pinned Playwright Chromium installation; `npm run test:artifact-evidence`; focused Python evidence tests.
- **Acceptance criteria**: a named, locked command computes browser evidence
  before validation, and schema 1 compatibility plus schema 2 strictness are
  executable rather than self-attested.

### 6. Produce evidence and prove binary context exclusion

- **Requirements**: R8, R9, R10
- **Files**:
  - `.cg-docs/work-reports/2026-08-02-curated-artifact-themes.design-evidence.json` (new)
  - `.cg-docs/views/evidence/curated-themes/**` (generated screenshots and print PDFs)
  - context, summary, review, PR, release, Brain, and duplicate-content tests
  - implementation files only where measured evidence reveals a defect
- **Details**:
  - Run the locked evidence producer first, then the Python manifest validator
    with all required automated and manual results enforced.
  - Perform bounded manual print/readability review for each theme and document
    class and record structured reviewer attestations; do not use anonymous
    booleans.
  - Add unique binary/text sentinels to evidence assets and prove no body or
    diff reaches model-facing scans or agents. Existing `.cg-docs/views/**`
    exclusions should pass; edit infrastructure only on a demonstrated gap.
  - Keep only paths, hashes, statuses, producer identities, measurements, and
    bounded attestations in the work-report manifest.
  - Repair the smallest owning theme or shared component on failure and rerun
    affected capture cells before validation.
- **Test Scenarios**: all viewports and print; long words/code/tables/images;
  callouts and source comparisons; 200 percent zoom; reduced motion; keyboard
  focus; offline capture; evidence binary sentinel in every model/review/release
  path; stale manifest after any asset change.
- **Tests**: locked capture command; `python scripts/validate_artifact_view_evidence.py --evidence .cg-docs/work-reports/2026-08-02-curated-artifact-themes.design-evidence.json --require-all-pass`; focused context-exclusion tests.
- **Acceptance criteria**: measured and attested evidence is current for all six
  cells, and no screenshot, PDF, or generated HTML body enters model context.

## Phase 4: Documentation And Final Gate

### 7. Document and verify the complete curated publishing workflow

- **Requirements**: R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12
- **Files**:
  - `README.md`
  - `docs/configuration/index.md`
  - `docs/development/index.md`
  - `docs/installation.md`
  - `docs/reference.md`
  - `docs/reference/commands.md`
  - `docs/workflow.md`
  - `docs/context-files.md`
  - `docs/troubleshooting.md`
  - `docs/navigation.json`
  - all files touched by this Plan
  - `tests/last-run.json` (generated result)
- **Details**:
  - Document pinned design provenance, supported/deferred editorial semantics,
    both themes, complete mode behavior, `/cg-render-doc`, skill behavior,
    platform parity, evidence setup/capture/validation, manual attestation,
    binary exclusions, and recovery.
  - State that browser packages are development-only and publisher runtime
    remains dependency-free and network-free.
  - Keep completion-report schema, generation, and `/cg-compound` integration
    explicitly outside this Plan despite the reserved default.
  - Run docs validation, the exact focused target gate, evidence producer and
    validator, all Python tests, Node evidence tests, and the full unfiltered
    Pester suite through `execution_subagent`.
  - Check diagnostics, target drift, evidence freshness, and this Plan's current
    derived view. Review the diff for inferred editorial semantics, model-authored
    HTML, runtime browser imports, binary body leakage, or premature dossier
    implementation.
- **Test Scenarios**: broken docs link; stale target; stale evidence; filtered
  final Pester artifact; diagnostics error; runtime Playwright/axe import;
  unavailable design object; out-of-scope report code.
- **Tests**: `node scripts/check-docs-site.js`; exact focused target pytest gate;
  `npm run test:artifact-evidence`; locked evidence capture and validation;
  `pytest -q`; `execution_subagent` run of `. tests\Run-Tests.ps1` requiring
  `passed: true`, `failedCount: 0`, `filteredFiles: null`; VS Code diagnostics;
  `cg-render-artifact --check .cg-docs/plans/2026-08-02-editorial-theme-publishing-workflow-evidence.md`.
- **Acceptance criteria**: both themes and the publishing workflow are
  documented, platform-equivalent, objectively evidenced, diagnostics-clean,
  and independently releasable before completion-report work starts.

## Testing Strategy

- Verify immutable Git object identities before any design implementation.
- Freeze editorial tokens and compare theme-independent semantic summaries.
- Extend the completed core's table-driven mode tests rather than adding
  theme-specific conditionals without coverage.
- Finish all canonical `.github` changes before one generation pass and run an
  enumerated target gate.
- Use locked Playwright Chromium plus axe-core to compute evidence; validate the
  manifest only after capture.
- Preserve schema 1 in isolated code and tests while adding strict schema 2
  dispatch.
- Keep screenshot/PDF/HTML bodies in the excluded views namespace and prove
  every model-facing path remains metadata-only.
- Run focused tests before broad Python, Node, documentation, evidence, and
  canonical Pester gates.

## Documentation Checklist

- [ ] Record the editorial commit and both blob identities.
- [ ] Freeze exact tokens, typography, geometry, responsive, and print rules.
- [ ] List supported and deferred editorial semantic components.
- [ ] Document two-theme mode behavior and recovery.
- [ ] Document `/cg-render-doc` and publishing skill routing.
- [ ] Document canonical/generated platform ownership.
- [ ] Document locked evidence installation, capture, validation, and attestation.
- [ ] Document schema 1 compatibility and schema 2 identity.
- [ ] Document evidence asset body/diff exclusions.
- [ ] Document runtime independence from Node, browsers, Git history, models, and network.
- [ ] Preserve the completion-report delivery boundary.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Pinned Git objects disappear from a shallow or rewritten clone. | Exact editorial fidelity cannot be verified. | Make object availability a blocked stop; fetch the explicit commit outside the implementation workflow or revise the Plan with a newly approved immutable source. |
| Editorial styling invents semantic groupings. | Two themes could communicate different facts. | Style only shared nodes and exact callout markers; defer timelines, diagrams, metrics, and inferred pairing. |
| Bare rerender reverts an editorial view. | Theme selection becomes unstable. | Reuse recorded known theme identity according to the completed mode matrix and test every mode. |
| Browser checks remain self-attested. | Overlap, accessibility, and print regressions could falsely pass. | Require locked evidence production before validation and structured attestation only for irreducibly manual checks. |
| Playwright becomes a runtime dependency. | Publisher installation grows and offline guarantees weaken. | Keep Node packages in development-only scripts/tests; statically reject runtime imports and document separate setup. |
| Evidence schema changes invalidate the completed record. | Prior acceptance evidence becomes unreadable. | Preserve schema 1 code/constants/tests and dispatch schema 2 through isolated exact validation. |
| Evidence binaries enter model context. | Token cost and duplicate-content noise increase sharply. | Store assets under `.cg-docs/views/evidence/**` and enforce binary sentinels across every model/review/release path. |
| Generated targets drift after late canonical edits. | Supported platforms receive inconsistent workflows. | Complete canonical edits first, generate once, and run ownership, closure, determinism, and drift gates. |

## Out of Scope

- Changes to the completed generic parser, path ownership, secure writer, or
  resource contracts except focused defect repairs exposed by evidence.
- Inferred timelines, architecture diagrams, metrics, approach selection, or
  model-authored document layouts.
- Completion-report schema, synthesis, correction, `/cg-completion-report`, or
  `/cg-compound` integration.
- Historical bulk publishing, arbitrary output roots, hosted publishing,
  product PDF generation, live editing, or documentation-site restyling.
- Executable source HTML, SVG, JavaScript, remote assets, runtime browser calls,
  or Open Design runtime dependency.

## Completion Contract

### Outcome

The accepted editorial design is reproducibly ported from immutable source
objects as a second presentation-only theme. Users can explicitly select it
through `/cg-render-doc` on every supported agent platform, and automated
browser evidence proves both themes remain semantically equivalent, accessible,
responsive, printable, offline, and current.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Editorial source commit and both blob hashes match the approved immutable identities. | Git object preflight against commit `52fc749ed484af2246dd7152b032f4dd01e86621`, design blob `8176439ea8ea60cdb6c541a8fdd6baced3dbc6cf`, and template blob `aefb61c65acecc2ec07878191d9a28191fc8aed2`. | yes |
| V2 | 1 | Editorial tokens and only source-triggered components are frozen; cross-theme semantic summaries are identical. | `pytest -q scripts/artifact_views/tests/test_themes.py scripts/artifact_views/tests/test_renderer.py scripts/artifact_views/tests/test_generic_renderer.py scripts/artifact_views/tests/test_design_contract.py scripts/artifact_views/tests/test_accessibility.py` | yes |
| V3 | 1 | Two-theme render, automatic, validation, check, legacy, old-version, and unknown cases follow the complete mode matrix. | `pytest -q scripts/artifact_views/tests/test_provenance.py scripts/artifact_views/tests/test_cli.py scripts/artifact_views/tests/test_publishing_cli.py scripts/artifact_views/tests/test_integration.py scripts/artifact_views/tests/test_publishing_integration.py` | yes |
| V4 | 2 | `/cg-render-doc`, publishing skill, canonical assets, and generated targets are equivalent. | Enumerated target pytest modules from Step 4 plus `execution_subagent` run of `. tests\Run-Tests.ps1 -File @('prompt-tools')`; exact filtered result required. | yes |
| V5 | 3 | A locked Playwright/Chromium/axe producer computes browser results and emits valid schema 2 evidence; manual-only checks carry structured attestation. | `npm ci`; pinned Chromium installation; `npm run test:artifact-evidence`; locked capture command; `python scripts/validate_artifact_view_evidence.py --evidence .cg-docs/work-reports/2026-08-02-curated-artifact-themes.design-evidence.json --require-all-pass`. | yes |
| V6 | 3 | Screenshot, print, and generated HTML bodies remain excluded from every model/review/release input. | Focused context, summary, Brain, review, commit/PR, release, and duplicate-content sentinel tests. | yes |
| V7 | final | Documentation plus all Python and Node regressions pass. | `node scripts/check-docs-site.js`; `npm run test:artifact-evidence`; `pytest -q`. | yes |
| V8 | final | Full unfiltered Pester passes safely. | `execution_subagent`: run `. tests\Run-Tests.ps1`; require `passed: true`, `failedCount: 0`, and `filteredFiles: null`. | yes |
| V9 | final | Diagnostics are clear, targets/evidence are current, and the replacement Plan view is current. | VS Code diagnostics, target drift check, evidence validator, and `cg-render-artifact --check .cg-docs/plans/2026-08-02-editorial-theme-publishing-workflow-evidence.md`. | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | 1 | The core Plan is completed and current before this Plan changes theme or platform surfaces. | Plan status, execution report, and required evidence preflight. |
| C2 | 1 | Editorial inputs are immutable and verified before porting; runtime has no branch dependency. | Commit/blob preflight and frozen theme contract. |
| C3 | 1 | Editorial styling cannot infer comparisons, decisions, tradeoffs, timelines, or diagrams from prose. | Only shared nodes and exact callout markers trigger variants; cross-theme semantic snapshots match. |
| C4 | 3 | Browser and axe packages are pinned development-only dependencies and never enter publisher runtime imports. | Lockfile, package, static dependency, and runtime isolation tests. |
| C5 | 3 | Screenshots and print artifacts live under `.cg-docs/views/evidence/**`, remain metadata-only to agents, and never enter Brain or model context. | Binary sentinel tests across all model/review/release paths. |
| C6 | 2 | All canonical `.github` edits finish before one generated-target pass. | Target ownership, closure, determinism, and drift tests. |
| C7 | final | Completion-report schema and workflow integration remain a separate dependent Plan. | Final diff and scope review. |

### Boundaries

- Allowed: pinned editorial port, explicit two-theme mode extension,
  `/cg-render-doc`, publishing skill, generated platform targets,
  Playwright/axe development harness, evidence schema 2 and protected assets,
  documentation, and release gates.
- Out of scope: generic core redesign, model-authored layout, inferred rich
  components, completion-report generation, executable Markdown HTML/SVG/
  JavaScript, hosted publishing, product PDF format, and docs-site restyling.

### Iteration Policy

1. Require the completed core Plan before implementation.
2. Verify immutable design objects before extracting tokens or components.
3. Narrow editorial behavior to deterministic source-backed semantics.
4. Finish canonical prompt, skill, and shared changes before generating targets
   once.
5. Produce browser evidence before validating its manifest.
6. Fix the smallest owning theme or component when evidence fails.
7. Keep browser tooling development-only and generated evidence out of model
   context.

### Blocked-Stop Conditions

- The core Plan is incomplete or its required evidence is stale or failed.
- Pinned design objects are unavailable or hash-mismatched.
- Editorial output changes source ownership or semantic structure.
- A promised visual component requires prose inference.
- Browser evidence cannot be reproduced from the pinned lockfile and tool
  versions.
- Evidence assets enter model, Brain, review, or diff bodies.
- A required deviation arises under `ask` and approval is unavailable.
- Generated platform parity or any required final gate fails.