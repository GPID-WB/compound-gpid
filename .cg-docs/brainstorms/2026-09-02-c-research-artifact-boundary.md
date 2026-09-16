---
date: 2026-09-02
title: "Separate CR Research Outputs from Compound GPID Documentation"
status: decided
scope: "Deep"
artifact-schema-version: 1
chosen-approach: "Canonical path contract plus migration"
tags: [compound-research, file-structure, artifact-boundary, module-activation, migration, research-outputs]
---
<!-- Valid status values: decided, in-progress, abandoned -->
<!-- Created 2026-09-02. -->

# Separate CR Research Outputs from Compound GPID Documentation

## Context

The research suite currently stores study-facing artifacts under
`.cg-docs/research/`. This mixes two different kinds of content:

1. Compound GPID process and knowledge records, such as brainstorms, plans,
   reviews, solutions, the inbox, and shared publishing fixtures.
2. Research outputs tied to a research question or study, such as evidence,
   manuscripts, scoping records, normative decisions, derivations,
   specifications, results, and replication material.

The research suite should make the second category a clear project-level
workspace while preserving the first category as the Compound GPID
workflow/documentation layer. The new boundary must support both human
researchers and CR agents and workflows.

The evidence-fixtures directory is not part of this migration. Repository
history shows that it was introduced by R. Andres Castaneda on 2026-08-04 as
part of the shared editorial-theme and browser-evidence publishing workflow.
It contains synthetic test inputs, not CR research outputs. The inbox is also
not part of the migration: it is a holding area for unprocessed Compound GPID
strategy ideas, not an approved research-output directory.

## Requirements

### Canonical research-output boundary

- Create a root-level `c-research/` directory when the `cr` suite is active.
- Use `c-research/` as the canonical project-level home for every artifact tied
  to a research question or study.
- Organize the directory by artifact type rather than by study slug.
- Support dual use: human researchers may author and inspect records, while CR
  agents and workflows may create, update, verify, and consume them.
- Treat files under `c-research/` as research outputs, not as Compound GPID
  process records.

### Proposed artifact-type layout

```text
c-research/
├── evidence/
├── manuscripts/
├── normative-decisions/
├── scoping/
├── derivations/
├── specifications/
├── results/
├── replication/
├── eda/
├── measurement/
└── vintages/
```

The `eda/`, `measurement/`, and `vintages/` directories are included because
existing CR skills already define outputs in those categories. Additional
research-output types may be added through the same path contract.

### Input and shared-document boundaries

- Research data and other inputs do not belong under `c-research/`.
- A separate root-level `data/` directory is the preferred home for project
  data inputs, subject to existing privacy, size, and version-control rules.
- Source documents, code, and other input materials remain outside
  `c-research/` unless a specific artifact is itself a research output.
- `.cg-docs/` retains Compound GPID process and knowledge records, including
  `brainstorms/`, `plans/`, `reviews/`, `solutions/`, `strategy/`, `archive/`,
  `evidence-fixtures/`, `inbox/`, and generated `views/`.
- `.cg-docs/evidence-fixtures/` remains shared publishing/test infrastructure.
- `.cg-docs/inbox/` remains a holding area for unprocessed strategy ideas.
- Generated `.cg-docs/views/` remain derived publishing artifacts and are not
  moved into `c-research/`.

### Migration and activation

- Move existing canonical `.cg-docs/research/` contents into the matching
  artifact-type directories under `c-research/`.
- Rename the existing singular `manuscript/` directory to `manuscripts/`.
- Update every repository reference to the old path, including CR prompts,
  skills, agents, instructions, scripts, tests, documentation, and generated
  platform targets.
- Regenerate derived platform targets from canonical `.github/` sources rather
  than editing generated copies manually.
- After migration, `.cg-docs/research/` must not remain a second canonical
  research-output location.
- Setup scaffolds `c-research/` only when `cr` is active. Deactivating `cr`
  must not delete an existing research workspace or its artifacts.
- Do not move, rename, or reinterpret evidence fixtures, inbox ideas, shared
  Compound GPID documentation, or generated views.
- Preserve existing uncommitted user work while performing the migration.

## Approaches Considered

### Approach 1: Direct relocation

Move the existing research tree, normalize `manuscript/` to `manuscripts/`,
replace all old path references, update setup behavior, and regenerate targets.

**Pros:** Clean result, no duplicate authority, and a simple conceptual change.

**Cons:** A missed dynamic or generated reference could break a workflow, and
there is no dedicated migration guard beyond ordinary tests.

**Effort:** Large.

### Approach 2: Canonical path contract plus migration (chosen)

Define the artifact-type path contract, inventory all old-path references, move
canonical outputs, update canonical CR sources, regenerate derived targets, and
add tests for path ownership, suite activation, input separation, and the
absence of stale old-path references.

**Pros:** Makes the boundary explicit and durable, catches path drift, supports
future artifact types, and provides an auditable migration gate.

**Cons:** Requires coordinated changes across prompts, skills, agents, setup,
documentation, scripts, tests, and generated targets.

**Effort:** Large.

### Approach 3: Relocation with a temporary compatibility redirect

Move the research outputs and update internal references, but leave a marked
`.cg-docs/research/README.md` redirect or migration manifest for old consumers.

**Pros:** Gives external scripts and users a transition hint.

**Cons:** Preserves ambiguity about ownership, risks a second authority, and
conflicts with the goal that `.cg-docs/` retain only Compound GPID records.

**Effort:** Large.

**Recommended:** No.

## Devil's Advocate

The folder move is necessary for a clear user-facing boundary, but it is not
sufficient enforcement. A workflow could still write a research output into
`.cg-docs/` or place data under `c-research/` unless path-specific tests and
documentation make ownership explicit. The implementation should therefore
validate both positive behavior (CR writes and reads `c-research/`) and
negative behavior (CG records, fixtures, inbox ideas, views, and data remain
outside it).

A second risk is migration drift: this repository contains many generated
platform trees and path references in skills and agents. Canonical sources must
be updated first, generated targets must be regenerated, and a stale-reference
scan must be part of the completion gate. Existing uncommitted presentation
work must remain untouched except where a tracked path reference is genuinely
part of the migration.

The change is aligned with the modular research-suite design. It does not
change the project charter's Compound GPID documentation layer, add a new
research backend, move test fixtures, or make research outputs part of the
technical-only suite.

## Decision

Choose **Approach 2: Canonical path contract plus migration**.

`c-research/` is the canonical, artifact-type-organized output workspace for
projects with the `cr` suite active. `data/` is separate input storage.
`.cg-docs/` remains the canonical home for Compound GPID process and knowledge
records. Existing canonical research outputs will be moved and all references
will be updated. No compatibility research tree will remain under
`.cg-docs/` after migration.

## Next Steps

1. Create an implementation plan that inventories every `.cg-docs/research/`
   reference and maps it to the new artifact-type path.
2. Define the canonical path contract and migration checks before moving files.
3. Update setup scaffolding so `c-research/` is created only for active `cr`
   projects, without deleting it when `cr` is later disabled.
4. Move existing research artifacts, including current manuscripts, evidence,
   normative decisions, and scoping records, while preserving file contents,
   dates, and uncommitted user changes.
5. Update CR canonical prompts, skills, agents, instructions, scripts, tests,
   and documentation; regenerate all derived platform targets.
6. Add validation for stale old paths, forbidden data placement, suite-specific
   scaffolding, and preservation of `evidence-fixtures/`, `inbox/`, and views.
7. Run the focused Python and repository tests, target-generation/parity checks,
   documentation checks, and `git diff --check` before considering the migration
   complete.
