---
date: 2026-08-02
title: "Workflow completion dossier and curated artifact themes"
status: decided
scope: "Extended"
artifact-schema-version: 1
chosen-approach: "One initiative, two linked delivery units"
tags: [completion-report, html, themes, artifact-rendering, workflow, provenance, human-review]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Workflow Completion Dossier and Curated Artifact Themes

## Context

Compound GPID already produces canonical Brainstorm, Plan, work, review, fix-triage, and solution artifacts, but no single artifact explains the complete journey from the original problem through implementation, verification, review, resolution, and knowledge capture. The task owner needs one coherent account that explains what happened, why decisions were made, what changed during execution, which problems were found, how they were resolved, and what remains open or correctable.

This extends the decision in `.cg-docs/brainstorms/2026-07-31-dual-audience-workflow-artifact-rendering.md`. Canonical Markdown remains authoritative. HTML remains a deterministic, self-contained, regenerable human view and never becomes a competing source.

The repository also contains two appealing but materially different visual systems:

- The current `main` artifact-view design is restrained, contract-like, and optimized for exact review of Brainstorms and Plans.
- The `refactor/modular-compound-gpid` editorial brief design uses Georgia, Trebuchet MS, and Consolas; warm paper; coral, teal, blue, and yellow accents; full-width bands; diagrams; explicit comparison surfaces; and stronger narrative hierarchy.

The question is not whether to replace one with the other, but whether Compound GPID can support both coherently and select predictable defaults for distinct reading jobs.

## Requirements

- Optimize the completion dossier first for the original task owner to understand and correct the recorded process.
- Create canonical completion-report Markdown as a synthesized, correctable account grounded in persisted workflow artifacts.
- Use recorded facts only. When rationale or evidence was discussed but not persisted, flag the gap rather than infer or silently fill it.
- Preserve source links, provenance, uncertainty, unresolved items, skipped items, and manual follow-up prominently enough to challenge the account.
- Keep the completion dossier concise at the top while retaining detailed evidence and traceability for review and future maintenance.
- Keep canonical source authority and model-assisted synthesis separate from deterministic HTML presentation.
- Support two coherent themes rather than mixing fonts, palettes, layouts, and components case by case.
- Use deterministic artifact-type defaults with an explicit user override.
- Use the restrained reference theme by default for Brainstorms and Plans.
- Use the editorial theme by default for completion dossiers.
- Permit an agent to recommend a theme override, but never let it silently make a non-reproducible aesthetic choice.
- Persist the selected theme in generation inputs or provenance so regeneration is stable.
- Share security, source coverage, provenance, accessibility, responsive behavior, print behavior, freshness checks, and failure semantics across themes.
- Scope the first iteration to workflow artifact views: Brainstorms, Plans, and completion dossiers. Do not restyle the documentation site or all `.cg-docs` artifacts.
- Exclude derived HTML from model context, Knowledge Brain ingestion, and other duplicate-content paths.
- Deliver the work as one product initiative with two separately planned, implemented, reviewed, and verifiable units.

## Approaches Considered

### Approach 1: One Initiative, Two Linked Delivery Units

Build the curated theme and generic publishing foundation first, then build the completion dossier as a dependent unit that reuses it.

**Pros**

- Matches the existing roadmap boundaries between generic Markdown publishing and the completion report.
- Keeps content synthesis and presentation concerns separate.
- Reuses provenance, security, freshness, accessibility, print, and theme-selection behavior.
- Allows each unit to ship, fail, and be validated independently.
- Avoids coupling strict Brainstorm and Plan parsing to completion-report synthesis.

**Cons**

- Requires coordination across two implementation plans or pull requests.
- The completion dossier arrives after the publishing and theme foundation.
- Cross-unit contracts must be explicit to prevent drift.

**Effort**: Large overall, divided into manageable medium-sized units.

**Recommended**: Yes. This preserves one coherent product direction without creating one oversized acceptance surface.

### Approach 2: One Integrated Deep Implementation Plan

Add the theme registry, port both visual systems, define the completion-report schema and generator, and integrate report generation into `/cg-compound` in one plan and branch.

**Pros**

- Makes all architectural decisions in one pass.
- Allows the editorial theme to be designed directly around the dossier.
- Avoids an intermediate publishing-only state.

**Cons**

- Creates a very large blast radius across parsing, rendering, prompts, platform targets, source relationships, and tests.
- Makes failures and regressions harder to localize.
- Risks conflating report correctness with visual acceptance.

**Effort**: Very large.

**Recommended**: No. It is technically feasible but unnecessarily difficult to verify as one task.

### Approach 3: Completion Dossier First, Themes Later

Generate completion-report Markdown first and render it with one existing style, then add curated themes later.

**Pros**

- Tests the dossier's usefulness sooner.
- Delivers the main comprehension and correction value before broader presentation work.
- Reduces the first implementation's design scope.

**Cons**

- The current strict renderer supports Brainstorm and Plan schemas, not arbitrary or completion-report Markdown.
- Likely creates a temporary dossier-specific rendering path.
- Introduces predictable rework when theme support is added.

**Effort**: Medium initially, followed by additional migration work.

**Recommended**: No unless delivery urgency outweighs the expected rework.

## Decision

Choose **One Initiative, Two Linked Delivery Units**.

The first unit extends the existing deterministic publishing architecture with a small curated theme registry and a generic Markdown document path. It preserves two complete visual identities:

- `reference`: the restrained current artifact-view design, default for Brainstorms and Plans.
- `editorial`: the richer standalone editorial brief design, default for completion dossiers.

The renderer selects the documented default from artifact type. Users can override it explicitly, for example with `--theme reference` or `--theme editorial`. The selected theme is recorded so regeneration remains deterministic. Agents may recommend an override but must not silently choose presentation based on subjective judgment.

The second unit defines and generates the canonical completion-report Markdown, integrates explicit and default generation into the workflow, and renders the report through the shared publishing and theme capability. The report synthesizes persisted evidence, identifies evidence gaps, and remains open to correction. It must never present inferred rationale as recorded fact.

This decision combines the ideas at the product and architecture level while separating their implementation gates. The theme foundation is reusable presentation infrastructure; the dossier is a source-governed workflow product built on top of it.

## Devil's Advocate Conclusions

- **Problem validation**: The missing end-to-end account is a real workflow gap. Multiple themes are valuable only where distinct document types have demonstrably different reading jobs; they are not an end in themselves.
- **Simplicity**: The existing `broader-artifact-publishing-formats-and-views` roadmap feature already calls for a small curated theme system. Reuse it rather than embedding theme intelligence in the completion-report command.
- **Decision reversibility**: Theme defaults are reversible because HTML is derived. The completion-report schema and source-linking model are durable contracts and must be versioned carefully.
- **Stakeholder impact**: The task owner needs correction affordances, reviewers need evidence, future maintainers need provenance, and agents need duplicate-content exclusions. Visual polish must not obscure missing evidence.
- **Charter fit**: One model-assisted synthesis of canonical report Markdown can be justified, while routine HTML generation stays local, deterministic, and model-free to align with token-efficiency goals.

## Next Steps

1. Create the first linked plan for the generic Markdown publishing and curated theme foundation, using roadmap feature `broader-artifact-publishing-formats-and-views`.
2. Define the theme contract: stable names, artifact-type defaults, explicit override, provenance, compatibility, fallback and unknown-theme failure behavior, shared semantic components, and visual regression evidence.
3. Port the `main` artifact-view aesthetics as the `reference` theme without weakening existing Brainstorm and Plan fidelity or validation.
4. Port the alternate branch's aesthetics as the `editorial` theme using only its style, typography, palette, layout grammar, responsive behavior, print rules, and presentation components.
5. Keep both themes fully standalone with no external fonts, stylesheets, scripts, runtime network calls, model calls, or Open Design dependency.
6. Validate the theme foundation independently across representative technical, decision, and editorial Markdown documents.
7. After the foundation is accepted, create the second linked plan for roadmap feature `workflow-completion-report-and-html-dossier`.
8. Define a versioned completion-report schema, explicit source-relationship contract, evidence-gap markers, correction workflow, resumable regeneration behavior, and required report sections.
9. Integrate explicit `/cg-completion-report` generation and default end-of-`/cg-compound` generation with a `--no-report` opt-out.
10. Render completion dossiers through the shared publisher with `editorial` as the deterministic default and `reference` as an explicit override.
11. Validate report factual grounding, source coverage, missing-evidence disclosure, correction behavior, duplicate-content exclusions, cross-platform parity, accessibility, responsive behavior, and print output.