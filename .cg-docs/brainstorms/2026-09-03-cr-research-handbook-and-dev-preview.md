---
date: 2026-09-03
title: "User-facing Compound Research Handbook and Isolated Dev Preview"
status: decided
scope: "Deep"
artifact-schema-version: 1
chosen-approach: "Dedicated CR handbook section with shared entry points and isolated dev preview"
tags: [compound-research, documentation, handbook, onboarding, github-pages, dev-preview, research-workflow, provenance]
---
<!-- Created 2026-09-03. -->

# User-facing Compound Research Handbook and Isolated Dev Preview

## Context

Compound GPID already has a strong user-facing handbook for the technical
(`cg`) module, but the research (`cr`) module is currently explained mainly
through the Modular Guide, command reference, skill catalog, and implementation
artifacts. World Bank researchers who are new to Compound GPID need a clear,
research-first path that explains both why CR exists and how to use it
successfully.

The first release should prioritize a first successful CR workflow. It should
use the existing AI-for-knowledge-work and AI-and-research presentation material
as conceptual input, especially its explanation of source detachment,
epistemic instability, selection opacity, amplified composition, Proof Carrying
Claim, human checkpoints, and the research lifecycle. The presentation should
inform the handbook's narrative, not be copied wholesale into it.

The short worked example will be:

> Assess the risk of extreme precipitation at a project site in Kenya
> (Latitude: -1.2921, Longitude: 36.8219). Get credible daily rainfall data
> from 2020 to present, define "extreme precipitation" based on a common
> practice, and calculate extreme precipitation by location. Produce materials
> to help dissemination of the findings, such as maps and charts.

A prior solution exists in the local `AI-work/DECDA Show & Tell - 11 Aug 2026`
folder. It should be used to make the example concrete and credible, while the
handbook keeps the example short and does not become a climate-analysis
manual.

The documentation work is being developed on `feat/cr-documentation`, created
from `origin/dev`.

## Requirements

### Audience and onboarding outcome

- Primary audience: World Bank researchers who know applied poverty,
  inequality, welfare, or related research but are somewhat new to Compound
  GPID.
- Use research language first and introduce repository, configuration, and
  command concepts gradually.
- Lead a newcomer from prerequisites and research-suite activation through a
  proportionate first CR loop: `/cr-brainstorm`, `/cr-plan`, `/cr-work`,
  `/cr-review`, and `/cr-compound`.
- Make clear what the researcher should have at each stage, what can block
  progress, and the shortest recovery path. Avoid a handbook journey that
  ends with an unexplained command, missing setup, or unavailable dependency.

### Handbook content

Add a focused research handbook section, linked from existing CG entry points,
with a compact chapter sequence:

1. **Start here**: what CR is, who it is for, prerequisites, suite activation
   in `compound-gpid.local.md`, and the first command to run.
2. **Why CR exists**: the philosophy of responsible AI-assisted research,
   source-to-claim traceability, uncertainty, human responsibility, and the
   boundary between a generated proposal and approved research knowledge.
3. **Your first CR workflow**: the five research commands, their inputs and
   outputs, the researcher decision at each stage, and the verification gates.
4. **Short workflow example**: activate the research module and walk through
   the important parts of the Kenya precipitation-risk task. Show the question,
   provisional task framing, evidence and method choices, a compact output path,
   and what remains for review. Link to the prior solution where appropriate;
   do not reproduce every script, chart, or climate-method detail.
5. **Research lifecycle and task types**: explain
   `Scope -> Evidence -> Theory -> Method -> Execute -> Verify -> Communicate
   -> Maintain`, the task taxonomy, and how classification routes guidance and
   review without replacing researcher judgment.
6. **Evidence, review, and boundaries**: explain provenance, Proof Carrying
   Claim in plain language, normative decisions, research-integrity gates, and
   what CR cannot establish by itself.

Detailed command contracts and individual skill guidance remain in the existing
reference pages. The new section should link to them rather than duplicate
them.

### CG handbook integration

- Update the CG handbook's modular explanation so the technical and research
  modules are presented as first-class parts of one product.
- Add clear links from Getting Started, the Modular Guide, workflow overview,
  commands, and skills navigation where appropriate.
- Preserve the handbook's existing conventions for page length, progressive
  disclosure, navigation, link style, and reference depth.
- Update `docs/navigation.json`; every new page must be represented in the
  public navigation manifest and pass site validation.

### Dev handbook deployment

- Maintain one continuously updated public preview at:
  `https://gpid-wb.github.io/compound-gpid/dev/`.
- Build the preview from the `dev` branch. Per-pull-request preview
  environments are out of scope.
- Keep stable production documentation at the site root sourced from `main`.
- Prevent a dev-only deployment artifact from replacing the stable root. The
  deployment design must publish a complete, validated combined artifact in
  which the root is the stable `main` site and `/dev/` is the current `dev`
  site.
- Ensure a production deployment cannot silently delete or roll back `/dev/`,
  and a dev deployment cannot mutate or contaminate stable root content.
- Serialize or otherwise coordinate main and dev deployments, verify source
  branch and artifact identity, and fail loudly on stale, incomplete, or
  malformed artifacts.
- Validate links, navigation, path prefixes, and the visible distinction
  between stable and development documentation.
- Do not add a second documentation framework unless the existing static site
  architecture cannot satisfy these guarantees.

### Presentation material to use

Use the prior AI-for-knowledge-work/research material to shape the explanation:

- The AI-and-research practitioner tour's workflow-first bridge from `cg` to
  `cr`, its five-command explanation, task classification, research lifecycle,
  Proof Carrying Claim, normative decisions, and Kenya-style measurement
  example.
- The longer AI knowledge-work presentation's explanation of the movement from
  resource to claim to composition and the distinction between generated
  answers and inspectable research objects.
- The local Kenya show-and-tell project for the short practical example.

Relevant repository history includes the presentation and manuscript material
on `feat/cr-ml-skill-redesign`; the local show-and-tell folder is outside this
repository and is source material only.

## Approaches Considered

### Approach 1: Extend the current pages

Add a CR start page, philosophy material, and the Kenya example beside the
existing Modular Guide, Getting Started, and Research Skills pages, with a dev
workflow publishing a branch build under `/dev/`.

- **Pros**: Smallest documentation change; reuses the existing structure and
  validators.
- **Cons**: The CR story remains scattered, and a branch-only Pages artifact
  creates a direct risk of replacing the stable root.
- **Effort**: Medium.
- **Recommended**: No.

### Approach 2: Dedicated CR handbook section with shared entry points and
isolated dev preview

Create a focused `docs/research/` handbook area and link it from the existing
CG handbook. Keep detailed commands and skills in the reference layer. Publish
a single complete Pages artifact containing stable documentation at `/` and the
current development handbook under `/dev/`; source the root only from `main`
and the preview only from `dev`.

- **Pros**: Gives newcomers one coherent route; preserves the conceptual
  research story; avoids duplicating the reference catalog; fits the current
  static site and validation model; satisfies the requested URL while making
  the production boundary explicit.
- **Cons**: Requires several focused pages, cross-links, deployment coordination,
  and artifact tests for two source branches.
- **Effort**: Large.
- **Recommended**: **Yes.**

### Approach 3: Independent CR handbook or site

Maintain a separate documentation tree or Pages project for CR and link to it
from the CG site.

- **Pros**: Maximum separation between technical and research documentation.
- **Cons**: Duplicates navigation, styling, validation, and deployment
  maintenance; does not naturally provide the requested `/dev/` path on the
  existing site; weakens the unified Compound GPID story.
- **Effort**: Large.
- **Recommended**: No.

## Decision

Choose **Approach 2: Dedicated CR handbook section with shared entry points and
isolated dev preview**.

The handbook is an onboarding product first and a reference expansion second.
A newcomer should be able to understand the purpose of CR, activate the
research suite, complete a small but real workflow, recognize what artifacts
were produced, and know where to go when a step is blocked. The Kenya example
will demonstrate the shape of that experience without pretending that a short
handbook chapter is a complete precipitation-risk study.

The conceptual spine comes from the presentation material: an AI-generated
answer is a proposal; a reusable research claim should carry its source,
evidence, locator, verification, and review state. CR places generation inside
a lifecycle that keeps evidence, judgment, and responsibility visible. The
handbook should state this plainly and avoid implying that provenance proves
truth, that task classification proves quality, or that reproducibility settings
guarantee identical model output across environments.

The dev site is a safety-critical part of the feature. GitHub Pages deployments
replace the published site artifact, so a workflow that deploys only the `dev`
tree could erase or replace stable materials. The implementation must instead
construct and validate a combined site artifact, with stable `main` content at
the root and `dev` content beneath `/dev/`, then deploy that exact artifact.
The main and dev paths need explicit source, freshness, digest, path, and
concurrency checks. A successful dev build must not be treated as permission to
rewrite root content, and a main build must preserve the current dev preview.

## Next Steps

1. Design the `docs/research/` information architecture and assign each page a
   clear onboarding purpose, owner, and link to existing reference material.
2. Draft the Start Here, philosophy, first workflow, short Kenya example,
   lifecycle/task-types, and evidence/boundaries chapters using the handbook's
   existing progressive-disclosure conventions.
3. Update CG entry points and `docs/navigation.json` without duplicating the
   complete command or skill references.
4. Define the combined Pages artifact contract: root from `main`, `/dev/` from
   `dev`, source and freshness metadata, path-prefix validation, digest checks,
   and serialized deployment behavior.
5. Add focused tests for navigation, links, onboarding prerequisites, branch
   isolation, artifact completeness, stale-source rejection, and preservation
   of stable root content.
6. Validate the static site locally over HTTP and verify the deployed preview
   path after CI is available. Keep per-PR previews and a full climate tutorial
   out of scope.

## Explicitly Out of Scope

- Per-pull-request preview environments.
- A full climate or extreme-precipitation methods tutorial.
- Deep documentation of every CR skill in the first release.
- A separate documentation framework or independent CR website.
- A broad redesign of the existing CG handbook.
- Treating the presentation deck itself as the handbook or duplicating its
  complete slide narrative.

## Devil's Advocate

- **Problem validation**: The onboarding gap is explicit, and the current CR
  material is distributed across reference pages rather than arranged as a
  first-use journey. The presentation work also demonstrates that users need
  the conceptual bridge, not only command names.
- **Simplicity check**: Expanding the Modular Guide alone could provide some
  value. A dedicated section is justified only if it stays compact and routes
  users onward to existing references instead of becoming a second encyclopedia.
- **Effort-value check**: The highest-value first release is the six-chapter
  path, a short worked example, cross-links, and protected combined deployment.
  Per-PR previews, exhaustive skill documentation, and a full climate tutorial
  would add substantial work without improving the first successful workflow
  proportionately.
- **Charter alignment**: The decision supports the modular architecture,
  research lifecycle, provenance requirements, and fail-loudly constraint. It
  preserves the production documentation boundary and does not require a
  change to the charter's objective or constraints.
