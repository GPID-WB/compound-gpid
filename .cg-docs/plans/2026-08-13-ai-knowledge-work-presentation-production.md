---
date: 2026-08-13
title: "AI and the Conditions for Verifiable Knowledge Work Presentation"
status: active
scope: "Standard"
task-type: "Writing"
brainstorm: ".cg-docs/brainstorms/2026-08-13-ai-knowledge-work-presentation.md"
language: "Markdown"
estimated-effort: "medium"
phases: 5
artifact-schema-version: 1
artifact-html: false
deviation-policy: ask
completed-phases: [1, 2, 3, 4, 5]
execution-report: ".cg-docs/work-reports/2026-08-13-ai-knowledge-work-presentation-production.md"
tags: [research, writing, presentation, ai, knowledge-work, evidence, provenance, ai-dqss]
created: 2026-08-13
---
<!-- Created 2026-08-13. -->

# Plan: AI and the Conditions for Verifiable Knowledge Work Presentation

## Objective

Produce one final Markdown manuscript suitable for a 30-minute in-person
presentation and for circulation by email. The manuscript will contain:

- a 12-slide main narrative with timings, slide text, speaker notes, and
  transitions;
- a self-contained email-ready narrative;
- a conceptual explanation of the resource-to-claim-to-composition framework;
- a three-part technical lineage covering the original Compound Research/plugin
  approach, AI-DQSS, and the current `research_evidence` package; and
- appendices with plain-language vocabulary, the repository map, named files,
  implementation examples, source boundaries, and avenues for exploration.
- a derived, locally runnable Reveal.js HTML deck with the 12-slide main
  narrative and speaker notes.

The final artifact will be created at:

`.cg-docs/research/manuscript/2026-08-13-ai-knowledge-work-presentation.md`

The derived presentation will be created at:

`presentation/ai-knowledge-work-presentation.html`

This plan does not create a PowerPoint deck, image assets, application code, a
new literature-search backend, or a roadmap entry. The Reveal.js HTML deck is a
derived delivery surface; the Markdown manuscript remains the authoritative
presentation narrative.

## Context

The task is a **Writing** task in the Communicate stage of the responsible
research lifecycle. Scope, Evidence, and Verify still apply, but there is no
estimator, derivation, causal identification strategy, or new empirical result.

The presentation uses ordinary research practice and answer-first LLM use as
the main comparison baseline. It adopts a strong risk framing while making the
opportunity explicit. Responsibility is assigned to institutions, researchers,
and reviewers to build systems and practices that protect against epistemic
risks while enabling useful AI applications.

A single central caveat checkpoint will state what the framework can and cannot
establish. The main narrative will then proceed without repeating long caveats
everywhere. The future section will offer avenues for exploration, not a
committed product roadmap.

The central conceptual distinction is:

```text
generation may be probabilistic
authority is earned through inspectable evidence and review
```

The technical lineage must distinguish documented facts from interpretation:

1. Compound Research provides the workflow and reasoning-trail foundation.
2. AI-DQSS provides a documented procedural exemplar for staged parsing,
   retrieval, reranking, assessment, citation, and verification.
3. `research_evidence` adapts the useful procedural pattern to a local-first,
   research-specific claim/evidence model with candidate, verification, review,
   approval, and stale-record states.

The missing `Suggestions-For-CR.md` source remains an unresolved lineage gap and
must not be presented as if its contents were inspected.

## Requirements

| ID | Requirement | Source |
|---|---|---|
| R1 | The opening explains why LLMs create an epistemological problem for research and institutional knowledge work, not only a factual-error problem. | Approved brainstorm; scoping memo |
| R2 | The epistemological threats include source detachment, epistemic instability from stochastic generation, selection opacity, and amplified composition. | Approved brainstorm; approved ND-001 and ND-002 |
| R3 | The main framework explains the path from original resource to source unit to candidate evidence and atomic claim to verification and human review to approved record to composition. | CR evidence/provenance skill; current workbench docs |
| R4 | The framework states its limits: source-link verification is not truth verification, causal identification, normative justification, or a guarantee of full model reproducibility. | Approved caveat decision ND-002 |
| R5 | The technical lineage gives separate sections to the original Compound Research/plugin approach, AI-DQSS, and the current package. | Approved baseline decision ND-003 |
| R6 | The AI-DQSS account is accurate, gives credit to the AI for Data team, and does not imply that the current package copies its 13-pillar assessment architecture or model stack. | AI-DQSS `README.md` and `DOCUMENTATION.md`; current workbench brainstorm |
| R7 | The current package account is grounded in its README and source symbols, including local-first processing, deterministic lexical baseline, candidate proposals, typed locators, verification, review, canonical YAML, and stale invalidation. | `research_evidence/README.md`; `claims.py`; `evidence.py`; `schemas.py`; package tests |
| R8 | The document is usable in person and by email: spoken transitions are explicit, timings sum to 30 minutes, and the email narrative does not depend on oral explanation. | User brief; approved brainstorm |
| R9 | The appendix contains actual repository structure, named files, and minimal implementation examples, clearly labeling existing behavior versus future proposals. | User brief; current repository |
| R10 | The source register identifies each substantive factual or methodological presentation claim as directly documented, inferred, proposed, or unresolved. | CR evidence/provenance and research-integrity rules |
| R11 | Source paths are portable where possible. Workspace-relative paths are used for Compound GPID; the external AI-DQSS repository is identified by repository name and relative path rather than a user-specific absolute path in the email-ready narrative. | Repository conventions; evidence provenance |
| R12 | No unsupported metrics, live claims about model variability, or production-readiness claims are introduced. A variability demonstration is optional and requires captured runs and metadata before inclusion. | Research-integrity rules; approved brainstorm |
| R13 | Produce a locally runnable Reveal.js HTML deck that preserves the approved 12-slide sequence, timings, caveat checkpoint, speaker notes, and offline/source-boundary behavior. | User-approved scope expansion, 2026-08-13 |

## Implementation phases

## Phase 1: Freeze evidence and narrative contract

### 1. Freeze evidence and narrative contract

- **Files:**
  - Create `.cg-docs/research/manuscript/2026-08-13-ai-knowledge-work-presentation.md`.
  - Read-only sources: `.cg-docs/brainstorms/2026-08-13-ai-knowledge-work-presentation.md`, `.cg-docs/research/scoping/ai-knowledge-work-presentation.md`, `.cg-docs/research/normative-decisions/ai-knowledge-work-presentation.md`, the CR evidence/provenance skill, the AI-DQSS repository documentation, and the current package README/source.
- **Requirements**: R1, R2, R6, R10, R11, R12
- **Details:**
  - Carry the approved audience, duration, baseline, risk framing, caveat
    checkpoint, shared responsibility, and exploration-oriented conclusion into
    the final manuscript.
  - Build or preserve the source register inside the Markdown document rather
    than adding a second user-facing artifact.
  - Classify each substantive statement as directly documented, inference,
    proposal, or unresolved. Direct statements about AI-DQSS and the package
    must resolve to the cited local repository path and section/symbol.
  - Preserve the unresolved status of `Suggestions-For-CR.md` and do not infer
    its contents.
  - Keep the claim that LLM randomness creates epistemic instability explicitly
    labeled as conceptual framing unless a controlled demonstration is added.
- **Test Scenarios:**
  - Every factual AI-DQSS, Compound Research, and package statement has a
    source-register row.
  - Missing or unavailable source material is marked unresolved rather than
    silently completed.
  - No source-register row labels a proposal as existing implementation.
  - External AI-DQSS references use repository-relative identifiers in the
    email-ready part of the document.
- **Tests**: YAML parse check for provenance and claim records; source-register
  target existence check; `get_errors` on the manuscript and evidence files.
- **Acceptance criteria:** The final manuscript has a complete, honest source
  register and a stable narrative contract before prose polishing begins.

## Phase 2: Write and time the 12-slide main narrative

### 2. Write and time the 12-slide main narrative

- **Files:** `.cg-docs/research/manuscript/2026-08-13-ai-knowledge-work-presentation.md`
- **Requirements**: R1, R2, R3, R4, R8
- **Details:**
  - Use four movements: problem (9 minutes), framework (8 minutes), lineage
    (9 minutes), and next questions (4 minutes).
  - Keep the first seven slides conceptual. Start from ordinary research
    practice and answer-first LLM use rather than from repository architecture.
  - Define epistemological threat once in plain language. Explain source
    detachment, epistemic instability, selection opacity, and amplified
    composition without introducing unnecessary jargon.
  - Include the approved caveat checkpoint as a full slide. State that quote and
    locator verification establish source linkage, not truth, causal validity,
    normative correctness, or complete model reproducibility.
  - Make the resource -> source unit -> candidate evidence -> atomic claim ->
    verification -> human review -> approved record -> composition path the
    conceptual centerpiece.
  - Give each slide one purpose and include a spoken transition to the next
    slide. Keep slide text sparse; place explanatory detail in speaker notes.
  - Present the strong risk framing alongside the opportunity to use AI for
    search, comparison, drafting, and research assistance.
- **Test Scenarios:**
  - Slide timings sum to 30 minutes.
  - The talk can be followed without the appendix.
  - The randomness discussion does not imply that all stochastic outputs are
    false or that a seed guarantees reproducibility.
  - The framework section does not imply that human interpretation is removed.
  - No technical implementation detail appears before the conceptual pipeline
    except what is needed to motivate the problem.
- **Tests**: Python timing assertion over `**Time:**` markers; heading and
  content checks for the 12 slides; `get_errors` on the manuscript.
- **Acceptance criteria:** A presenter can deliver the main narrative in 30
  minutes, and a listener can explain the problem, the framework, the limits,
  and the reason for the technical lineage.

## Phase 3: Add the email narrative and technical appendix

### 3. Add the email narrative and technical appendix

- **Files:** `.cg-docs/research/manuscript/2026-08-13-ai-knowledge-work-presentation.md`
- **Requirements**: R5, R6, R7, R9, R10, R11, R12
- **Details:**
  - Write the email-ready narrative as prose that preserves the complete
    argument, transitions, limits, lineage, and future questions without
    requiring the slide deck or oral commentary.
  - Add a plain-language vocabulary table and the exact caveat-checkpoint text.
  - Add a repository map covering the relevant `.github/`, `.cg-docs/`, and
    `research_evidence/` paths. Keep the map focused on the evidence and
    presentation surfaces rather than reproducing the whole repository.
  - Add named implementation anchors: AI-DQSS citation IDs and staged pipeline;
    `create_claim`, `create_evidence`, candidate proposal validation, typed
    locators, `is_approved_evidence`, deterministic lexical retrieval, and
    source lifecycle/stale invalidation.
  - Use short, accurate code or pseudocode excerpts. Every excerpt must be
    labeled as existing implementation or future proposal.
  - Include a lineage table stating what was adopted from each stage and what
    was not adopted.
  - Include avenues for source discovery and literature-review interface design,
    framed as questions for joint exploration rather than commitments.
  - Preserve the future generative-run metadata example as a proposal. It must
    not be described as already implemented in the current package.
- **Test Scenarios:**
  - Email narrative is understandable without speaker notes.
  - All named local files and symbols exist and match the excerpts.
  - The appendix distinguishes canonical records from derived browser/index
    surfaces and distinguishes candidate from approved evidence.
  - No user-specific absolute filesystem path appears in the email-ready
    narrative.
  - Future source-discovery and interface work is not presented as a completed
    roadmap item.
- **Tests**: Workspace-relative source and symbol existence check; code-fence
  and absolute-path scan; `get_errors` on the manuscript.
- **Acceptance criteria:** The single Markdown file is sufficient to send by
  email and gives a technically informed reader a traceable appendix without
  turning the main talk into a code tour.

## Phase 4: Research-integrity, editorial, and artifact validation

### 4. Research-integrity, editorial, and artifact validation

- **Files:** Final manuscript and its referenced source files; no code changes.
- **Requirements**: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12
- **Details:**
  - Perform a source/provenance pass against the source register and all direct
    factual claims.
  - Perform an editorial pass for plain language, active voice, coherent
    transitions, consistent terms, and audience fit. Use `cr-skill-academic-writing`
    principles while adapting them to a spoken institutional presentation rather
    than a journal article.
  - Check the central caveat checkpoint against every later claim about
    verification, reproducibility, AI-DQSS, and the current workbench.
  - Check that the presentation does not overclaim current package maturity,
    AI-DQSS equivalence, or the effect of stochastic generation.
  - Validate Markdown structure, fenced code blocks, local source links,
    referenced files, dates, and whitespace. Render only if a later presentation
    or email workflow requires a visual artifact; Markdown is the authoritative
    deliverable in this plan.
- **Test Scenarios:**
  - `get_errors` reports no diagnostics for the manuscript and updated register.
  - `git diff --check` reports no whitespace errors.
  - All workspace-relative source targets exist.
  - No `TODO`, `PENDING`, or unresolved decision marker remains in the approved
    manuscript, except the explicitly documented missing `Suggestions-For-CR.md`
    lineage note.
  - No generated prose is presented as evidence, and no claim is promoted from
    proposal to documented implementation without a source.
- **Tests**: `get_errors`; `git diff --check`; `./bin/cg-render-artifact --validate-only`
  on the plan; final manuscript validation checks; explicit presentation-owner
  review recorded in the execution report.
- **Acceptance criteria:** The manuscript is factually traceable, editorially
  coherent, technically bounded, portable enough to email, and ready for
  presentation-owner review.

## Phase 5: Reveal.js HTML presentation

### 5. Produce and browser-verify the Reveal.js HTML presentation

- **Requirements**: R8, R9, R12, R13
- **Files**:
  - `presentation/ai-knowledge-work-presentation.html`
  - `presentation/vendor/reveal.js/reveal.js`
  - `presentation/vendor/reveal.js/reveal.css`
  - `presentation/vendor/reveal.js/notes.js`
  - `package.json`
  - `package-lock.json`
- **Details**:
  - Translate the 12-slide main narrative into a Reveal.js deck while keeping
    the Markdown manuscript authoritative.
  - Use concise slide text, visual hierarchy, diagrams, speaker notes, and the
    approved central caveat checkpoint. Keep appendix material out of the main
    slide flow.
  - Pin Reveal.js as a development dependency and vendor only the runtime files
    required by this deck so the HTML works without a CDN or runtime network
    request.
  - Add a restrained, research-oriented visual system: editorial serif display
    type, readable sans-serif body text, warm paper background, ink/teal/coral
    accents, thin rules, and no decorative gradient blobs or generic dashboard
    cards.
  - Include a small visible derived-artifact/source note and a link back to the
    canonical Markdown manuscript using a relative path.
  - Verify the deck with a local HTTP server and Playwright/Chromium at desktop
    and mobile widths. Confirm the first, framework, lineage, and final slides
    render; navigation works; notes are present; the canvas is nonblank; and no
    external network requests are required.
- **Test Scenarios**:
  - **Happy path**: Deck loads locally, initializes Reveal.js, exposes 12 slides,
    and advances through the main narrative.
  - **Edge case**: Narrow viewport keeps headings, diagrams, tables, and caveat
    text within the slide without overlap or clipping.
  - **Error path**: Missing local Reveal.js asset is reported by the browser
    check rather than silently falling back to a remote CDN.
- **Tests**: `npm install` lock check; local HTTP server smoke test;
  Playwright/Chromium screenshot and DOM assertions; `get_errors`; `git diff
  --check`.
- **Acceptance criteria**: `presentation/ai-knowledge-work-presentation.html`
  opens as a working Reveal.js presentation from the repository, renders the
  approved 12-slide/30-minute narrative, includes speaker notes, uses only
  local runtime assets, and passes desktop/mobile browser checks.

## Testing Strategy

This is a Writing task with a derived HTML presentation surface. The following
gates apply:

| Gate | Status and check |
|---|---|
| P0: fabricated or unverifiable citation | Required. Every direct factual or methodological claim must map to a source-register row with a resolvable source and locator/section. The missing `Suggestions-For-CR.md` note remains explicitly unresolved. |
| P0: uncited substantive claim | Required. Remove, qualify, or source every substantive claim in the final manuscript. Conceptual proposals and future avenues must be labeled as such. |
| P0: stochastic generation | No random code is added. Any optional live demonstration must have captured repeated runs, model/provider/version, settings, seed status, retrieved context, and output artifacts before inclusion. |
| P0: seed enforcement | Not applicable to the manuscript itself. Applies to a live-generation demonstration only; no demonstration is included by default. |
| P0: specification manifest | Not applicable. The plan adds no estimation or model-fitting code. |
| P0: derivation cross-reference | Not applicable. No mathematical derivation is being implemented. |
| P1: identification diagnostic | Not applicable. No causal identification strategy is claimed. |
| P2: reproducibility | Required for document production: dated source list, portable paths, explicit inference/proposal labels, and reproducible validation checks. |
| P2: audience review | Required. Review the talk from both the AI for Data and DRG research perspectives before treating the manuscript as final. |
| P2: presentation runtime | Required. The Reveal.js deck must pass local desktop/mobile browser checks and must not rely on a CDN or runtime network request. |

No Pester or Python test suite is required for this Markdown-only plan unless
implementation code or automated document validation is added later.

## Documentation Checklist

- [ ] Final manuscript has creation date and approved presentation metadata.
- [ ] Main slides include timings, slide text, speaker notes, and transitions.
- [ ] Email narrative is self-contained and uses plain language.
- [ ] Source register distinguishes documented facts, inferences, proposals,
      and unresolved lineage.
- [ ] Appendix paths and code excerpts match the current repository.
- [ ] The central capability/limits caveat is present and consistent with later
      claims.

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Strong risk framing is heard as rejection of AI. | State the opportunity at the opening and assign responsibility to institutions, researchers, and reviewers to enable useful use while protecting knowledge quality. |
| Quote verification is mistaken for truth verification. | Keep the caveat checkpoint explicit and repeat short source-link reminders in the lineage and appendix. |
| AI-DQSS lineage is overstated or treated as a direct clone. | Cite the AI-DQSS purpose and stages separately from the research adaptation, and label the missing `Suggestions-For-CR.md` note unresolved. |
| Stochastic generation is presented as measured evidence without a controlled run. | Treat epistemic instability as conceptual framing unless captured repeated runs and metadata are added. |
| The current package is presented as a complete literature-review product. | State its local-corpus boundary and frame source discovery and interface work as exploration. |

## Out of Scope

- PowerPoint, PDF export, or other non-HTML slide-deck formats.
- New visual assets, screenshots, or a live model demonstration without a
  captured evidence package.
- Internet search, external paper retrieval, external API model execution, or
  a new literature-search backend.
- Changes to `research_evidence/` implementation code or its dependency lock.
- Changes to `roadmap.json`, the project charter, or AI-DQSS source files.

## Completion Contract

### Outcome

The final Markdown manuscript exists at
`.cg-docs/research/manuscript/2026-08-13-ai-knowledge-work-presentation.md`
and contains a source-traceable 30-minute presentation, a self-contained
email narrative, and a technically accurate appendix. The manuscript and its
supporting evidence records are validated, bounded by the approved caveats,
and ready for presentation-owner review. A derived local Reveal.js HTML deck
also exists at `presentation/ai-knowledge-work-presentation.html` and passes
browser checks without runtime network access.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|---|---:|---|---|---|
| V1 | 1 | Source register, provenance ledger, and claim matrix exist and parse; direct lineage claims resolve to documented sources. | `.cg-docs/research/manuscript/2026-08-13-ai-knowledge-work-presentation.md`; `.cg-docs/research/evidence/provenance-ledger.yaml`; `.cg-docs/research/evidence/claim-evidence-matrix.yaml`; YAML parse check | yes |
| V2 | 2 | The main deck has exactly 12 timed slides totaling 30 minutes and contains the approved conceptual sequence. | Python timing assertion over the manuscript plus heading/content checks | yes |
| V3 | 3 | Email narrative and appendix are self-contained; every named local file and implementation symbol exists; future proposals are labeled. | Source-target existence check, `get_errors`, and manuscript inspection | yes |
| V4 | 4 | Markdown, links, caveat boundaries, and unresolved-lineage markers pass final validation without stale or pending decision markers. | `get_errors`; `git diff --check`; `cg-render-artifact --validate-only` on this plan; final manuscript validation script/check | yes |
| V5 | final | Presentation-owner review confirms the narrative is fit for both audiences and accepts any remaining caveats or revisions. | Explicit user review response recorded in the execution report | yes |
| V6 | 5 | Reveal.js HTML deck loads locally, renders the 12-slide narrative at desktop and mobile widths, contains speaker notes, and uses only local runtime assets. | Playwright/Chromium browser evidence and local HTTP smoke test | yes |

### Constraints

| ID | Phase | Constraint | Check |
|---|---:|---|---|
| C1 | 1-4 | Do not modify `roadmap.json`, application code, or the AI-DQSS repository. | Changed-file inspection |
| C2 | 1-4 | Original source documents and documented repository files remain authoritative; generated prose is not evidence. | Source register and provenance review |
| C3 | 1-4 | Do not present quote verification as truth verification, or seeds as guarantees of model determinism. | Caveat consistency review |
| C4 | 1-4 | Do not include a live variability demonstration without captured runs, model metadata, settings, seed status, and outputs. | Demonstration presence/metadata check |
| C5 | 3-4 | Keep user-specific absolute paths out of the email-ready narrative and label external AI-DQSS sources explicitly. | Path scan and source-register review |
| C6 | 4-5 | Do not mark the plan complete from static inspection alone when a required executable check is available. | Execution report evidence table |
| C7 | 5 | The deck must not depend on CDN assets, remote fonts, or runtime network requests. | Browser request log and local asset existence check |

### Boundaries

- In scope: one Markdown manuscript, its source/provenance records, the
  approved presentation narrative, email narrative, appendix, a derived local
  Reveal.js HTML deck, vendored runtime assets, and validation evidence.
- Out of scope: PowerPoint/PDF export, visual asset production beyond the deck's
  CSS/diagrams, a new literature-search service, external API execution, model
  benchmarking, `research_evidence/` code changes, and roadmap edits.
- The missing `Suggestions-For-CR.md` source remains an explicitly unresolved
  lineage note.
- A future source-discovery or literature-interface concept is presented as an
  avenue for exploration, not as a completed product commitment.

### Iteration Policy

1. Execute phases in order; do not begin a later phase while required evidence
   for the prior phase is missing.
2. Apply `deviation-policy: ask`: pause before any scope, source, audience, or
   output change not stated in this plan, record the proposed deviation and
   impact, and obtain explicit user approval.
3. If a source cannot be verified, mark the related claim unresolved or
   abstained and pause rather than inventing metadata, quotations, or locators.
4. Treat direct documentation, interpretation, and future proposal as separate
   statuses throughout the manuscript and evidence records.
5. Keep the Markdown manuscript authoritative; any rendered view is derived and
   must be regenerated or validated from the canonical source.

### Blocked-Stop Conditions

- A required source, locator, or evidence record cannot be verified.
- A required verification command cannot run through the safe local workflow.
- A required evidence item fails after the allowed recovery attempts.
- A required deviation is discovered under `ask` and user approval is
  unavailable.
- A protected boundary would need to be crossed to continue.
- The execution report or active-state pointer cannot be written durably.
- The plan or manuscript would need to claim that `Suggestions-For-CR.md` was
  inspected when the file remains unavailable.
- Completion would require treating static inspection as passed evidence when
  an executable check is available.

## Normative Decisions

This plan commits to the following decisions, all explicitly approved in the
per-study register:

- `ND-ai-knowledge-work-presentation-001`: strong risk framing; responsibility
  is assigned to institutions, researchers, and reviewers to protect against
  risks while enabling useful AI applications.
- `ND-ai-knowledge-work-presentation-002`: one central caveat checkpoint states
  what the framework can and cannot establish.
- `ND-ai-knowledge-work-presentation-003`: ordinary research practice and
  answer-first LLM use are the comparison baseline; the three technical stages
  provide the lineage response.

Register:
`.cg-docs/research/normative-decisions/ai-knowledge-work-presentation.md`

## Plan critique

1. **Task type:** Writing drives the output shape: talk track, email narrative,
   plain-language exposition, and source-backed appendix. No estimator-specific
   method pack is needed.
2. **P0 enforcement:** Evidence provenance, uncited claims, unresolved lineage,
   and stochastic-generation boundaries are explicit in the testing strategy.
3. **Derivation:** No derivation exists or is required because the task does not
   implement a model.
4. **Acceptance criteria:** Timing, source resolution, path portability,
   caveat consistency, and Markdown integrity are directly testable.
5. **Measurement/classification:** Not applicable. No weighting, ranking,
   clustering, thresholds, or vintage comparisons are introduced.

## Handoff

After review and any refinement, the next step is:

1. `/cr-work` to produce the final manuscript and run the validation checks; or
2. `/cg-plan-review` to have the plan challenged before production.

No `roadmap.json` change is required by this plan.
