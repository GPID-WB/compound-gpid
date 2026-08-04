---
date: 2026-08-03
title: "Editorial Theme, Publishing Workflow, and Browser Evidence (Revised)"
status: blocked
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-08-02-completion-dossier-and-curated-artifact-themes.md"
supersedes: ".cg-docs/plans/2026-08-02-editorial-theme-publishing-workflow-evidence.md"
split-from: ".cg-docs/plans/2026-08-02-generic-markdown-publishing-curated-themes.md"
depends-on-plan: ".cg-docs/plans/2026-08-03-generic-markdown-reference-publishing-core-v2.md"
language: "both"
estimated-effort: "medium"
deviation-policy: "ask"
artifact-schema-version: 1
phases: 4
tags: [editorial-theme, html, publishing-skill, playwright, accessibility, cross-platform, reviewed]
---

# Plan: Editorial Theme, Publishing Workflow, and Browser Evidence (Revised)

## Objective

Port the approved editorial visual system from immutable source objects as a
second presentation-only theme, expose explicit theme selection through the
canonical publishing workflow on every supported agent platform, and produce
reproducible automated and attested browser evidence for both themes.

## Context

This revised dependent Plan incorporates all approved `/cg-plan-review`
findings assigned to editorial presentation, agent-platform orchestration, and
browser evidence. It remains blocked until
`.cg-docs/plans/2026-08-03-generic-markdown-reference-publishing-core-v2.md`
is completed with current required evidence. That core owns generic parsing,
strict routing, path/output ownership, provenance schema 2, the mode matrix,
bounded resources, non-clobbering publication, the `reference` renderer, generic
CLI, launchers, and baseline exclusions.

### Review Finding Traceability

This Plan shares the complete ledger in the core v2 Plan. Its direct ownership
is:

| Finding | Accepted revision | Owning step |
|---------|-------------------|-------------|
| P1.2 Browser evidence is self-attested | Produce measured Playwright/Chromium/axe results before validating schema 2; use structured attestation only for manual checks. | Steps 5-6; V5 |
| P1.3 Design source is movable | Verify immutable commit and exact design/template blobs before porting. | Step 1; V1; C2 |
| P1.4 Pester/target gates are invalid or vague | Use registered `prompt-tools` basename, exact durable records, and an enumerated target pytest set. | Step 4; V4 |
| P2.4 Theme semantics are incomplete | Extend the core mode matrix for explicit and recorded editorial states without changing defaults. | Step 2; V3 |
| P2.5 Evidence migration is undefined | Preserve exact schema 1 dispatch and add isolated strict schema 2. | Step 5; V5 |
| P2.6 Evidence assets can enter context | Store binaries under `.cg-docs/views/evidence/**` and prove all model/review/release paths metadata-only. | Step 6; V6; C5 |
| P2.7 Rich editorial components lack source triggers | Style only shared nodes, source tables, and exact `DECISION`/`PROS`/`CONS` markers; defer inferred components. | Step 2; C3 |
| P2.8 Unit/target sequencing is oversized | Depend on the independently released core; finish canonical edits before one target generation pass. | Dependency; Steps 3-4; C1/C6 |
| P3.1 Infrastructure edits are assumed | Treat generator, mappings, shared contracts, and platform infrastructure as test-first and conditional. | Steps 3-4 |

### Immutable Editorial Inputs

| Input | Path at pinned commit | Git object |
|-------|-----------------------|------------|
| Commit | `refactor/modular-compound-gpid` historical source | `52fc749ed484af2246dd7152b032f4dd01e86621` |
| Design system | `.github/skills/cg-skill-standalone-html-brief/references/design-system.md` | `8176439ea8ea60cdb6c541a8fdd6baced3dbc6cf` |
| Editorial template | `.github/skills/cg-skill-standalone-html-brief/assets/editorial-brief-template.html` | `aefb61c65acecc2ec07878191d9a28191fc8aed2` |

Resolve and compare all three objects before mutation. If unavailable or
mismatched, stop; do not reconstruct an approximate design from memory. Freeze
accepted tokens/components in runtime code so runtime never reads Git history.

### Supported Semantics And Theme Modes

- Editorial may style only semantic nodes emitted by the core: headings,
  navigation, paragraphs, lists, tables, code, images, provenance, and exact
  callout markers.
- Tables may receive comparison styling without changing cells. Exact
  `DECISION`, `PROS`, and `CONS` callouts may receive distinct treatments.
- Do not infer selected approaches, pair unrelated blocks, or synthesize
  timelines, diagrams, metrics, architecture, or summaries. Fenced diagrams
  remain code.
- Explicit `--theme editorial` wins in render, enabled automatic, validation,
  and check modes. Bare render/check reuse recorded owned editorial provenance.
  Missing and legacy views use document defaults: strict/generic use
  `reference`; future completion report is reserved for `editorial` without
  adding its parser or workflow here.
- Known old editorial contract versions are stale and rerender with the current
  version. Unknown recorded themes block mutation until an explicit registered
  theme is supplied. Validation-only and disabled automatic do not inspect or
  mutate output.

### Evidence Architecture

- Keep evidence schema 1 behavior and constants isolated and unchanged.
- Schema 2 requires unique `(documentClass, themeName)` cells for technical,
  decision, and editorial fixtures under `reference` and `editorial`.
- Pin Playwright and axe-core in committed `package-lock.json`; record Node,
  Playwright, Chromium, and axe versions.
- The producer opens local standalone HTML with network blocked, measures DOM
  geometry/accessibility/focus/zoom/reduced-motion/provenance, captures five
  viewport screenshots, and prints PDF before writing the manifest.
- Manual-only checks require reviewer, UTC timestamp, cell, check name, result,
  and bounded note; bare booleans are invalid.
- Store binaries under `.cg-docs/views/evidence/curated-themes/**`; store only
  metadata, hashes, measurements, and attestations in `.cg-docs/work-reports/`.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Require completed, current core v2 evidence before implementation. | P2.8 |
| R2 | Verify immutable commit and blob identities before editorial work. | P1.3 |
| R3 | Register `editorial` contract version 1 with exact accepted tokens, typography, geometry, responsive, and print rules. | Brainstorm |
| R4 | Keep themes semantically equivalent and style only deterministic source-backed nodes. | P2.7 |
| R5 | Extend the complete core mode matrix for editorial states. | P2.4 |
| R6 | Add `/cg-render-doc` and publishing skill as deterministic tool orchestration, never bespoke model HTML. | Roadmap |
| R7 | Finish canonical `.github` edits before one target pass and verify all supported platforms. | P2.8; P3.1 |
| R8 | Add a pinned development-only Playwright/Chromium/axe evidence producer. | P1.2 |
| R9 | Preserve schema 1 exactly and add isolated exact schema 2 dispatch. | P2.5 |
| R10 | Keep screenshot/PDF/HTML bodies excluded from every model/review/release input. | P2.6 |
| R11 | Use valid Pester basenames and enumerate all focused target tests. | P1.4 |
| R12 | Document immutable design provenance, themes, workflow, evidence, recovery, platform parity, and dossier boundary. | Brainstorm |

## Phase 1: Immutable Editorial Theme

### 1. Verify and freeze the editorial design inputs

- **Requirements**: R1, R2, R3
- **Files**: new editorial theme module, registry contract, frozen snapshot, theme tests, and developer provenance docs.
- **Details**: Preflight core completion/evidence. Resolve pinned commit and both blobs exactly. Freeze the accepted palette, soft/success/danger/line roles, `1180px` width, radius no greater than `6px`, Georgia display, Trebuchet body/control, and Consolas code stacks. Record supported/deferred components and object IDs; runtime has no Git dependency.
- **Test Scenarios**: completed/incomplete core, exact/missing/mismatched objects, immutable registry, duplicate theme, token snapshot, no external resources.
- **Tests**: exact Git object preflight plus focused theme/design-contract pytest files.
- **Acceptance criteria**: editorial identity is auditable, stable, standalone, and cannot silently drift with a branch.

### 2. Render editorial from shared source-backed semantics

- **Requirements**: R3, R4, R5
- **Files**: editorial theme/components, renderer and strict/generic CLIs, provenance/integration tests.
- **Details**: Add warm paper, grid-textured unframed hero treatment, full-width rhythm, visible borders, restrained hard shadows, multi-accent roles, `980px`/`720px` responsive behavior, and print rules. Style tables and exact editorial callouts only. Extend the core mode matrix without changing defaults. Compare semantic summaries across themes; only CSS/presentation metadata may differ.
- **Test Scenarios**: strict/generic sources in both themes, explicit/recorded editorial, missing/legacy/old/unknown theme, disabled automatic, validation-only, long text, dense tables, all callouts, print/reduced motion, no remote assets/scripts.
- **Tests**: focused theme, renderer, generic renderer, design, accessibility, provenance, CLI, and integration pytest files.
- **Acceptance criteria**: editorial is faithful within supported semantics and cannot alter or omit source meaning.

## Phase 2: Publishing Workflow And Platform Parity

### 3. Add the publishing skill and `/cg-render-doc`

- **Requirements**: R5, R6, R7, R11
- **Files**: canonical publishing skill and reference, new render-doc prompt, shared contract only if focused tests show a gap, prompt/target tests.
- **Details**: Route typed artifacts to `cg-render-artifact` and generic documents to `cg-render-markdown`; direct generic routing still rejects typed roots. Parse explicit theme, check, validation, and constrained output. Agents may recommend but never silently select themes. Treat generator mappings and infrastructure as test-first because canonical prompts/skills are auto-discovered.
- **Test Scenarios**: typed/generic routing, explicit/bare recorded editorial, check/validation, unsafe path/output, recommendation without selection, tool declarations, skill closure.
- **Tests**: focused prompt and target tests, followed by the exact Step 4 gates.
- **Acceptance criteria**: all user workflows invoke deterministic local tools without schema bypass or model-authored HTML.

### 4. Generate platform targets once and verify parity

- **Requirements**: R7, R11
- **Files**: generator/mapping only on focused failure; generated target trees; enumerated target and prompt tests.
- **Details**: Complete all canonical edits first, then generate once. Never hand-edit targets. Verify skill reference closure. Run target mapping, closure, ownership, packaging, documentation, determinism, path-safety, and drift modules explicitly. Run Pester using registered `prompt-tools` basename and inspect exact durable records.
- **Test Scenarios**: auto-discovery, bundled reference, ownership/closure, deterministic bytes, path safety, dirty/stale targets, command/tool parity.
- **Tests**: `pytest -q scripts/tests/test_target_mapping.py scripts/tests/test_target_closure.py scripts/tests/test_target_ownership.py scripts/tests/test_target_packaging.py scripts/tests/test_target_documentation.py scripts/tests/test_target_determinism.py scripts/tests/test_target_path_safety.py scripts/tests/test_target_drift.py`; `execution_subagent`: `. tests\Run-Tests.ps1 -File @('prompt-tools')`, requiring exact filtered identity and passing file record.
- **Acceptance criteria**: every supported platform exposes equivalent behavior and the generated tree is clean after one pass.

## Phase 3: Reproducible Browser Evidence

### 5. Add the locked evidence producer and exact schema 2

- **Requirements**: R8, R9, R10
- **Files**: new `package.json`/lockfile, Playwright evidence script and Node tests, evidence validator, Python evidence tests, fixtures.
- **Details**: Pin development dependencies. Render six document/theme cells with fixed inputs. Capture `390x844`, `768x1024`, `1024x768`, `1440x900`, and `1920x1080`, plus print PDF. Block network during capture and inject local axe only in the test browser. Measure nonblank output, overflow/geometry, navigation/tables, heading order, focus, axe/contrast, zoom, reduced motion, provenance, console errors, and print bytes. Dispatch schemas exactly; reject unknown/mixed fields.
- **Test Scenarios**: deterministic ordering, complete/missing/duplicate cells, stale hashes, missing/false checks, malformed attestations, unknown/mixed schema, unchanged schema 1, blocked network, external resource and console errors.
- **Tests**: `npm ci`; pinned Chromium install; Node evidence tests; focused Python evidence tests.
- **Acceptance criteria**: a locked producer computes evidence before strict validation, with schema 1 compatibility and schema 2 exactness proven.

### 6. Produce evidence and prove binary exclusion

- **Requirements**: R8, R9, R10
- **Files**: schema 2 manifest under work reports; screenshot/PDF assets under views evidence; context/review/release sentinel tests; implementation only where measured failures require repair.
- **Details**: Run capture before validation. Add structured manual print/readability attestations. Prove unique sentinels from binary/text assets never enter Brain, audits, summaries, review, PR, release, or duplicate inputs. Reuse existing views exclusion when it passes; edit infrastructure only on demonstrated failure.
- **Test Scenarios**: all viewports/print, long words/code/tables/images/callouts, zoom/motion/focus/offline, binary sentinels, stale manifest after asset change.
- **Tests**: locked capture command; strict Python manifest validation; focused exclusion tests.
- **Acceptance criteria**: all six cells have current measured/attested evidence and no generated body enters model context.

## Phase 4: Documentation And Final Gate

### 7. Document and verify curated publishing

- **Requirements**: R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12
- **Files**: README and relevant docs, all touched implementation files, generated `tests/last-run.json`.
- **Details**: Document immutable source, supported/deferred semantics, themes/modes, workflow, platform parity, evidence setup/capture/validation/attestation, binary exclusions, recovery, and development-only browser tooling. Keep completion-report generation outside scope. Run docs, enumerated target, Node evidence, capture/validation, all Python, full Pester, diagnostics, drift, and Plan freshness gates.
- **Test Scenarios**: broken docs, stale target/evidence, filtered final Pester, runtime browser import, unavailable object, diagnostics error, report-scope leakage.
- **Tests**: `node scripts/check-docs-site.js`; enumerated target pytest gate; Node evidence tests; locked capture and validation; `pytest -q`; full `. tests\Run-Tests.ps1` through `execution_subagent`; diagnostics; `cg-render-artifact --check .cg-docs/plans/2026-08-03-editorial-theme-publishing-workflow-evidence-v2.md`.
- **Acceptance criteria**: both themes and publishing workflow are documented, platform-equivalent, objectively evidenced, and ready before dossier work.

## Testing Strategy

- Verify immutable Git objects and completed core evidence before mutation.
- Freeze editorial tokens and compare theme-independent semantic summaries.
- Extend the core table-driven mode tests for editorial.
- Finish canonical edits before one generated-target pass and enumerated gate.
- Produce evidence through locked Playwright/Chromium/axe before validation.
- Preserve schema 1 in isolated tests and enforce strict schema 2.
- Keep generated binaries under the excluded views namespace and prove every
  model/review/release path remains metadata-only.
- Run focused checks before broad Python, Node, docs, evidence, and Pester gates.

## Documentation Checklist

- [ ] Record commit and blob identities.
- [ ] Freeze tokens, typography, geometry, responsive, and print rules.
- [ ] List supported/deferred editorial semantic components.
- [ ] Document two-theme modes and recovery.
- [ ] Document render-doc/skill routing and target ownership.
- [ ] Document evidence installation, capture, validation, and attestation.
- [ ] Document schema compatibility and binary exclusions.
- [ ] Document runtime independence and completion-report boundary.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Pinned objects are missing in a shallow/revised clone. | Exact fidelity cannot be verified. | Block; obtain the explicit object or approve a new immutable source. |
| Editorial styling invents groupings. | Themes communicate different facts. | Style shared nodes and exact markers only; defer inferred components. |
| Bare rerender reverts editorial. | Theme choice becomes unstable. | Reuse recorded known theme identity under the core matrix. |
| Browser checks remain self-attested. | Accessibility/layout failures falsely pass. | Require locked capture before validation and structured manual attestation. |
| Browser packages enter runtime. | Offline/runtime guarantees weaken. | Keep Node dependencies development-only and reject runtime imports. |
| Schema 2 invalidates prior evidence. | Completed acceptance becomes unreadable. | Preserve schema 1 code/constants/tests and exact version dispatch. |
| Binaries enter model context. | Token and duplicate-content costs spike. | Store under views evidence and enforce sentinels everywhere. |
| Targets drift after late canonical edits. | Platforms diverge. | Complete canonical edits, generate once, run ownership/closure/drift gates. |

## Out of Scope

- Generic core redesign except focused defects exposed by evidence.
- Inferred timelines, diagrams, metrics, approach selection, or model-authored layouts.
- Completion-report schema, synthesis, correction, or compound integration.
- Bulk/hosted publishing, arbitrary output roots, product PDF format, live
  editing, docs-site restyling, executable source HTML/SVG/JavaScript, remote
  assets, runtime browsers, and Open Design runtime dependency.

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
| V1 | 1 | Pinned commit and blobs match approved immutable identities. | Exact Git object preflight for the three IDs in Context. | yes |
| V2 | 1 | Editorial tokens/source-triggered components are frozen and cross-theme semantic summaries match. | Focused theme, strict/generic renderer, design, and accessibility pytest files. | yes |
| V3 | 1 | Editorial render/automatic/validate/check, legacy, old-version, and unknown states follow the core matrix. | Focused provenance, strict/generic CLI, and integration pytest files. | yes |
| V4 | 2 | Render-doc, publishing skill, canonical assets, and generated targets are equivalent. | Enumerated target pytest command in Step 4 plus exact filtered `prompt-tools` Pester run. | yes |
| V5 | 3 | Locked browser producer computes valid schema 2 evidence; manual checks have structured attestations. | `npm ci`; pinned Chromium install; Node tests; capture command; strict Python evidence validation. | yes |
| V6 | 3 | Screenshot, print, and HTML bodies remain excluded from all model/review/release inputs. | Focused binary sentinel tests across all listed paths. | yes |
| V7 | final | Documentation, Python, and Node regressions pass. | `node scripts/check-docs-site.js`; Node evidence tests; `pytest -q`. | yes |
| V8 | final | Full unfiltered Pester passes safely. | `execution_subagent`: `. tests\Run-Tests.ps1`; require `passed: true`, `failedCount: 0`, `filteredFiles: null`. | yes |
| V9 | final | Diagnostics, targets, evidence, and Plan view are current. | Diagnostics, drift/evidence checks, and `cg-render-artifact --check .cg-docs/plans/2026-08-03-editorial-theme-publishing-workflow-evidence-v2.md`. | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | 1 | Core v2 is completed and current before this Plan mutates theme/platform surfaces. | Plan status, report, and required evidence preflight. |
| C2 | 1 | Editorial inputs are immutable and verified; runtime has no branch dependency. | Exact commit/blob check and frozen theme contract. |
| C3 | 1 | Editorial cannot infer comparisons, decisions, tradeoffs, timelines, or diagrams from prose. | Shared nodes/exact markers only and cross-theme semantic snapshots. |
| C4 | 3 | Browser packages are pinned development-only and absent from runtime imports. | Lockfile/package/static dependency tests. |
| C5 | 3 | Evidence binaries remain under views/evidence and metadata-only to agents. | Binary sentinel tests across all model/review/release paths. |
| C6 | 2 | All canonical edits finish before one target-generation pass. | Target ownership, closure, determinism, and drift. |
| C7 | final | Completion-report implementation remains a separate dependent Plan. | Final diff and scope review. |

### Boundaries

- Allowed: pinned editorial port, two-theme extension, render-doc/skill,
  generated platform targets, development-only Playwright/axe, schema 2 and
  protected evidence, documentation, and final gates.
- Out of scope: generic core redesign, inferred rich components, completion
  reports, executable source content, hosted/product-PDF publishing, and docs
  site restyling.

### Iteration Policy

1. Require completed core v2 before implementation.
2. Verify immutable design objects before porting.
3. Style deterministic source-backed semantics only.
4. Finish canonical edits before generating targets once.
5. Produce browser evidence before validating the manifest.
6. Repair the smallest owning theme/component on evidence failure.
7. Keep browser tooling development-only and binaries outside model context.

### Blocked-Stop Conditions

- Core v2 is incomplete or its evidence is stale/failed.
- Pinned objects are unavailable or mismatched.
- Editorial changes semantic structure or requires prose inference.
- Browser evidence is not reproducible from pinned versions.
- Evidence bodies enter model, Brain, review, or diff inputs.
- A required deviation arises under `ask` without approval.
- Platform parity or any required final gate fails.