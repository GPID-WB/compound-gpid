---
date: 2026-09-02
title: "Root-Level c-research Output Workspace and Migration"
status: completed
completed-date: 2026-09-02
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-09-02-c-research-artifact-boundary.md"
language: "Python/Markdown/PowerShell"
estimated-effort: large
deviation-policy: "ask"
artifact-schema-version: 1
phases: 7
execution-report: ".cg-docs/work-reports/2026-09-02-c-research-output-workspace-migration.md"
completed-phases: [1, 2, 3, 4, 5, 6, 7]
current-phase: 7
tags: [compound-research, file-structure, artifact-boundary, module-activation, migration, research-outputs]
---
<!-- Created 2026-09-02. -->

# Plan: Root-Level c-research Output Workspace and Migration

## Objective

Separate project-level research outputs from Compound GPID process and knowledge
records. Introduce a root-level, artifact-type-organized `c-research/`
workspace for active CR projects, migrate existing canonical research outputs
from `.cg-docs/research/`, and update every operational path, setup rule,
validation surface, and generated target that depends on the old location.

## Context

Compound Research currently writes study-facing outputs under
`.cg-docs/research/`, while `.cg-docs/` is also the home for Compound GPID
brainstorms, plans, reviews, solutions, strategy records, work reports, and
generated views. This makes the ownership boundary unclear for both human
researchers and CR agents.

The approved boundary is:

```text
project/
├── data/                 # inputs; separate from research outputs
├── c-research/           # canonical CR research outputs
│   ├── evidence/
│   ├── manuscripts/
│   ├── normative-decisions/
│   ├── scoping/
│   ├── derivations/
│   ├── specifications/
│   ├── results/
│   ├── replication/
│   ├── eda/
│   ├── measurement/
│   └── vintages/
└── .cg-docs/             # Compound GPID process and knowledge records
    ├── brainstorms/
    ├── plans/
    ├── reviews/
    ├── solutions/
    ├── strategy/
    ├── archive/
    ├── work-reports/
    ├── evidence-fixtures/
    ├── inbox/
    └── views/
```

The `data/` directory is separate input storage and is not created or migrated
by this plan. Source documents, code, and other inputs remain outside
`c-research/` unless a particular file is itself a research output.

`.cg-docs/evidence-fixtures/` is shared publishing/test infrastructure added by
Andres Castaneda in the editorial-theme evidence workflow; it is not a CR
research artifact and must not move. `.cg-docs/inbox/` remains a holding area
for unprocessed Compound GPID strategy ideas. Generated `.cg-docs/views/`
remain derived publishing outputs in their existing location.

The generic Brain scanner reads `.cg-docs/` entity directories only. This plan
keeps that behavior: CR workflows read `c-research/` directly, while the
Compound GPID process Brain continues to index process and knowledge records
rather than study outputs. No second research Brain is introduced here.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | `c-research/` is the canonical project-level home for every CR artifact tied to a research question or study. | Approved brainstorm |
| R2 | The workspace is organized by artifact type: evidence, manuscripts, normative decisions, scoping, derivations, specifications, results, replication, EDA, measurement, and vintages. | Approved brainstorm |
| R3 | Research outputs are separate from inputs; `data/` remains outside `c-research/`, and this plan does not create or migrate data. | User decision |
| R4 | `.cg-docs/` retains Compound GPID process and knowledge records, including brainstorms, plans, reviews, solutions, strategy, archive, work reports, fixtures, inbox, and views. | Approved brainstorm |
| R5 | `.cg-docs/evidence-fixtures/`, `.cg-docs/inbox/`, and `.cg-docs/views/` are preserved in place and retain their current ownership. | User decision; fixture provenance check |
| R6 | Existing canonical `.cg-docs/research/` outputs move to the matching `c-research/` directories; `manuscript/` becomes `manuscripts/`. | Approved brainstorm |
| R7 | All operational references are updated across canonical CR prompts, skills, agents, instructions, scripts, package documentation, tests, and project documentation. | Approved brainstorm |
| R8 | Setup creates the `c-research/` scaffold only when the `cr` suite is active and never deletes an existing research workspace when `cr` is later disabled. | Approved brainstorm; modular suite contract |
| R9 | The generic Compound Brain remains `.cg-docs/`-only; `c-research/` is not silently indexed as Compound process knowledge. | Approved architecture decision; scanner behavior |
| R10 | Generated Claude, Codex, OpenCode, and Kilo targets are regenerated from canonical `.github/` sources after path changes. | Project instructions |
| R11 | The local evidence workbench moves its canonical evidence root to `c-research/evidence/` without changing its offline, provenance, transaction, or original-authority guarantees. | Approved brainstorm; evidence-workbench contract |
| R12 | Migration is fail-closed on destination conflicts, unknown source content, stale operational references, or boundary violations, and preserves existing user changes. | Charter constraints; approved brainstorm |

## Implementation Steps

## Phase 1: Path Contract and Inventory

### 1. Define the canonical research-output path contract

- **Requirements**: R1, R2, R3, R4, R5, R8, R9
- **Files:** `c-research/README.md` (new), `docs/reference/files.md`,
  `docs/reference.md`, `docs/workflow.md`, targeted path-contract tests.
- **Details:**
  - Document the ownership boundary and artifact-type layout in a concise
    root-level `c-research/README.md`.
  - State that `c-research/` contains outputs only; `data/` and other source
    inputs are separate; no data is scaffolded or migrated by the plugin.
  - Define the complete supported directory set, including `eda/`,
    `measurement/`, and `vintages/` already referenced by CR skills.
  - State that `.cg-docs/` remains the Compound GPID process/knowledge layer,
    including `evidence-fixtures/`, `inbox/`, and derived `views/`.
  - State that CR workflows consume `c-research/` directly and that the generic
    Brain scans `.cg-docs/` only.
  - Add a machine-checkable path contract used by later migration and boundary
    tests; do not duplicate path rules in unrelated code when a shared test
    helper can express them.
- **Test Scenarios:** complete layout; missing optional directory; data path
  accidentally nested below `c-research/`; shared fixture/inbox/view paths
  classified as non-research; `c-research/` absent for a CG-only project.
- **Tests**: new or extended `scripts/tests/test_research_layout.py` and
  targeted documentation tests.
- **Acceptance criteria:** The canonical layout and ownership rules are
  documented once, all required artifact types are named, and tests can assert
  the output/input/shared-record boundary.

### 2. Inventory live, historical, generated, and runtime path references

- **Requirements**: R6, R7, R9, R10, R11, R12
- **Files:** `scripts/cg_migrate_research_layout.py` (new), migration fixtures,
  `scripts/tests/test_research_layout.py`, reference inventory output kept in
  the execution report.
- **Details:**
  - Add a standard-library Python migration helper with `--root` and `--check`
    modes, following the idempotent/fail-loud pattern of
    `scripts/cg_migrate_config.py`.
  - Inventory `.cg-docs/research/` files and classify each source path by the
    destination artifact type. Map `manuscript/` to `manuscripts/`.
  - Scan repository text for `.cg-docs/research/` references and classify them
    as operational source, generated target, historical record, derived view,
    fixture, or unrelated text.
  - Define an explicit allowlist for historical plan/brainstorm/review records
    where the old path is part of historical evidence. Operational source,
    generated target, documentation, test, and runtime references must be
    updated; historical references must not be rewritten merely to alter the
    historical record.
  - Reject unknown top-level source directories, destination collisions with
    different bytes, symlink escapes, and files that cannot be mapped without a
    human decision.
  - Make check mode report the planned moves and unresolved references without
    mutating files.
- **Test Scenarios:** clean migration inventory; already migrated tree; unknown
  source child; identical destination; conflicting destination; symlink escape;
  historical old-path reference; operational old-path reference.
- **Tests**: `python3 -m pytest scripts/tests/test_research_layout.py -q`.
- **Acceptance criteria:** Check mode produces a deterministic path map, detects
  every live old-path reference, and fails closed for ambiguous or conflicting
  input.

## Phase 2: Suite-Aware Scaffolding and Migration Hook

### 3. Update setup scaffolding for active `cr`

- **Requirements**: R1, R2, R3, R4, R5, R8
- **Files:** `.github/prompts/cg-setup.prompt.md`,
  `.github/prompts/setup-templates.md`, `.github/skills/cg-skill-setup/SKILL.md`,
  setup/Pester contract tests.
- **Details:**
  - Expand setup file permissions so setup may create the project-root
    `c-research/` directory and its artifact-type subdirectories, while
    retaining the prohibition on unrelated root mutations.
  - Replace the conditional `.cg-docs/research/` scaffold with the full
    `c-research/` scaffold when `suites:` includes `cr`.
  - Keep the base `.cg-docs/` scaffold limited to Compound GPID process and
    knowledge directories. Do not move `evidence-fixtures/`, `inbox/`, or
    `views/` into the research scaffold.
  - In returning-project mode, create missing `c-research/` directories only
    when `cr` is active and do not delete an existing `c-research/` tree when
    `cr` is inactive.
  - Use the current `suites:` configuration terminology consistently in the
    new behavior; preserve backward-compatible handling where an older config
    lacks the field.
  - Document that `data/` is user/project-owned input storage and is not
    created by setup.
- **Test Scenarios:** new CG-only setup; new CR-only setup; mixed setup;
  returning CR project with missing directories; returning CG-only project;
  existing `c-research/` while CR is disabled; existing shared fixture/inbox.
- **Tests**: targeted setup assertions in `tests/prompt-tools.Tests.ps1`,
  `tests/roadmap.Tests.ps1`, and any setup-template test blocks.
- **Acceptance criteria:** Setup creates exactly the research-output scaffold
  for active CR projects, never deletes an existing research workspace, and
  leaves the shared `.cg-docs/` directories unchanged.

### 4. Integrate the migration with structural updates on both platforms

- **Requirements**: R6, R8, R10, R12
- **Files:** `scripts/update.ps1`, `scripts/update.sh`,
  `scripts/cg_migrate_research_layout.py`, `tests/update.Tests.ps1`,
  `tests/bash-scripts.Tests.ps1`, migration fixtures.
- **Details:**
  - Invoke the shared migration helper from the existing structural-migration
    path in both update scripts when run from a project root.
  - Keep shell-specific behavior limited to invoking the same Python contract;
    preserve parity between PowerShell and Bash.
  - Run the migration only for an existing project with the old tree or a
    detectable path migration need. A project with no old tree remains a no-op.
  - Preserve the existing update behavior for global-install files, version
    pinning, generated instructions, and unrelated structural migrations.
  - Report moved, skipped-identical, and blocked-conflict outcomes clearly.
  - Never use destructive cleanup when a destination differs or source content
    is unknown. Leave the old source intact and return a failure requiring
    resolution.
- **Test Scenarios:** old tree moved; no-op after migration; conflict blocks;
  old tree absent; both scripts invoke equivalent migration behavior; unrelated
  `docs/ -> .cg-docs/` migration still works.
- **Tests**: focused update and Bash script tests; direct migration-helper
  pytest tests.
- **Acceptance criteria:** `cg-update` applies the same checked migration on
  macOS and Windows, is idempotent, and never silently overwrites content.

## Phase 3: Canonical Output Migration

### 5. Move existing research outputs without changing content

- **Requirements**: R2, R3, R4, R5, R6, R12
- **Files:** existing `.cg-docs/research/**` canonical files; new
  `c-research/**` destinations; migration manifest/test fixtures.
- **Details:**
  - Run the migration helper in checked mode and review the complete move map
    before applying it.
  - Move `evidence/` to `c-research/evidence/`, `manuscript/` to
    `c-research/manuscripts/`, `normative-decisions/` to
    `c-research/normative-decisions/`, and `scoping/` to `c-research/scoping/`.
  - Create the remaining artifact-type directories (`derivations/`,
    `specifications/`, `results/`, `replication/`, `eda/`, `measurement/`, and
    `vintages/`) as empty scaffold directories where no current files exist.
  - Preserve bytes, UTF-8 content, frontmatter, creation dates, file names, and
    relative links. Record source/destination hashes in the execution report
    or migration evidence rather than adding a second authoritative manifest.
  - Move only canonical research outputs. Do not move `.cg-docs/brainstorms/`,
    `.cg-docs/plans/`, `.cg-docs/reviews/`, `.cg-docs/solutions/`,
    `.cg-docs/evidence-fixtures/`, `.cg-docs/inbox/`, `.cg-docs/views/`, or the
    `research_evidence/` Python package.
  - Remove the old `.cg-docs/research/` tree only after all mapped files have
    been verified at their destinations and no unknown content remains.
- **Test Scenarios:** every existing file; singular-to-plural manuscript path;
  empty new artifact directories; byte/hash preservation; source and
  destination collision; user-modified source; untracked current manuscript;
  old tree contains unknown file.
- **Tests**: migration helper tests plus a repository-level content/hash check.
- **Acceptance criteria:** All existing canonical research files exist only at
  their new artifact-type paths, with unchanged content and no second
  `.cg-docs/research/` authority.

## Phase 4: CR Sources and Evidence Runtime

### 6. Update canonical CR prompts, skills, agents, and instructions

- **Requirements**: R1, R2, R4, R7, R8, R9, R11
- **Files:**
  `.github/prompts/cr-brainstorm.prompt.md`,
  `.github/prompts/cr-plan.prompt.md`,
  `.github/prompts/cr-work.prompt.md`,
  `.github/prompts/cr-review.prompt.md`,
  `.github/prompts/cr-compound.prompt.md` where paths occur,
  `.github/skills/cr-skill-*.*/SKILL.md` path references,
  `.github/agents/cr-*.agent.md` path references,
  `.github/instructions/math.instructions.md`,
  `scripts/brain/scanner.py` only if contract tests expose a needed boundary fix.
- **Details:**
  - Replace operational `.cg-docs/research/` paths with the corresponding
    `c-research/` path, including evidence, scoping, normative decisions,
    derivations, specifications, results, replication, EDA, measurement, and
    vintage records.
  - Keep CR brainstorm, plan, review, and compound solution outputs in their
    existing `.cg-docs/` locations because those are Compound GPID process or
    reusable-knowledge records, not study outputs.
  - Update CR file-permission and output instructions so agents can write
    research outputs under `c-research/` but cannot reinterpret `data/` as an
    output directory.
  - Update the mathematical instruction `applyTo` glob to the new derivation
    location.
  - Preserve untrusted-content warnings, normative gates, evidence authority,
    P0 checks, and task taxonomy while changing only path ownership and related
    wording.
  - Preserve the generic Brain scanner's `.cg-docs/` scope. If a code change is
    unnecessary, prove that with a regression test rather than adding a second
    scanner path.
- **Test Scenarios:** each CR artifact type; CR brainstorm output versus
  scoping output; CR plan references derivations/specifications; work writes
  results/evidence; review detects evidence/measurement scope; math instruction
  matches only `c-research/derivations/`; generic Brain excludes `c-research/`.
- **Tests**: focused CR prompt/skill contract tests, scanner regression tests,
  and stale-reference inventory tests.
- **Acceptance criteria:** Every active CR source points to `c-research/` for
  research outputs and to `.cg-docs/` for process/knowledge records, with no
  semantic regression in research-integrity enforcement.

### 7. Move the evidence workbench canonical root

- **Requirements**: R3, R6, R7, R11, R12
- **Files:** `research_evidence/README.md`,
  `research_evidence/src/research_evidence/config.py`,
  `research_evidence/src/research_evidence/transactions.py`,
  `research_evidence/tests/test_runtime_contract.py`,
  `research_evidence/tests/test_transactions.py`,
  `scripts/tests/test_research_evidence_docs.py`, `.gitignore`.
- **Details:**
  - Change runtime settings so the canonical evidence root is
    `project_root / "c-research" / "evidence"`.
  - Update transaction examples, package README layout, canonical/derived
    state documentation, and the ignore rules for derived evidence state.
  - Keep original source authority paths, local-only processing, loopback
    binding, model-cache policy, transaction journaling, and security behavior
    unchanged.
  - Ensure the evidence package can create `c-research/evidence/` on demand
    without creating or moving `data/`.
  - Update tests to assert the new root and retain the existing path-safety and
    no-network guarantees.
- **Test Scenarios:** valid project/resources settings; evidence root missing;
  evidence root symlink; existing old evidence root; canonical YAML and derived
  index paths; offline runtime; transaction recovery.
- **Tests**: `uv run --project research_evidence pytest research_evidence/tests -q`
  plus focused evidence documentation tests.
- **Acceptance criteria:** The workbench persists canonical evidence and
  derived evidence state below `c-research/evidence/`, and all existing
  evidence/security tests remain green.

## Phase 5: Documentation, Brain, and Generated Targets

### 8. Update project documentation and derived knowledge artifacts

- **Requirements**: R1, R2, R3, R4, R5, R9, R11
- **Files:** `README.md` only if it contains an operational path claim,
  `docs/reference/files.md`, `docs/reference.md`, `docs/workflow.md`,
  `research_evidence/README.md`, `.cg-docs/BRAIN.md`, `.cg-docs/BRAIN-*.md`,
  `.cg-docs/BRAIN-log.md`, `.cg-docs/brain-index.json` (regenerated).
- **Details:**
  - Replace active documentation claims that research outputs live under
    `.cg-docs/research/` with the new boundary and artifact-type layout.
  - Explicitly preserve the descriptions of `.cg-docs/evidence-fixtures/` and
    `.cg-docs/inbox/` as shared test infrastructure and unprocessed strategy
    holding area.
  - Run the Brain/index rebuild after migration. Confirm the generic Brain
    drops moved research-output entities and retains Compound GPID process and
    knowledge entities.
  - Do not hand-edit generated Brain files; use the canonical index/rebuild
    command and record warnings or unresolved classifications.
  - Do not load or rewrite generated HTML view bodies. Refresh only a view whose
    canonical source genuinely changed, and keep all views under `.cg-docs/views/`.
- **Test Scenarios:** moved research artifacts absent from generic Brain;
  brainstorm/plan/solution records remain indexed; evidence fixtures and inbox
  remain excluded or classified according to their existing policy; generated
  view paths remain unchanged.
- **Tests**: targeted documentation tests; `bin/cg-index --brain` (or
  the repository's canonical Brain rebuild command); Brain scanner tests.
- **Acceptance criteria:** Documentation and generated Brain outputs describe the
  new ownership boundary without moving shared process artifacts or view files.

### 9. Regenerate native platform targets and verify parity

- **Requirements**: R7, R10
- **Files:** generated `.claude/`, `.agents/`, `.opencode/`, and `.kilo/` CR
  prompts, skills, agents, and instructions; target/parity tests.
- **Details:**
  - Regenerate from updated canonical `.github/` sources with the supported
    target generator; do not hand-edit generated copies.
  - Verify each generated CR target contains the new paths and preserves module
    metadata, tool declarations, model mappings, and platform adapters.
  - Check that CG-only generated targets do not gain CR-only research content
    beyond the existing suite dependency rules.
  - Record any generator or parity failure as a blocked stop rather than
    patching one platform tree independently.
- **Tests**: `python3 scripts/cg_generate_targets.py --all`,
  target ownership/closure/drift/parity tests, and generated-target tests.
- **Acceptance criteria:** Generated native targets are deterministic and
  semantically aligned with canonical `.github/` CR sources.

## Phase 6: Boundary and Regression Tests

### 10. Add executable boundary and migration regression coverage

- **Requirements**: R1, R2, R3, R4, R5, R6, R8, R9, R11, R12
- **Files:** `scripts/tests/test_research_layout.py`,
  `scripts/tests/test_research_evidence_docs.py`, `scripts/brain/tests/test_scanner.py`,
  `tests/prompt-tools.Tests.ps1`, `tests/update.Tests.ps1`,
  `tests/bash-scripts.Tests.ps1`, relevant CR prompt tests, and minimal fixtures.
- **Details:**
  - Add positive tests for each artifact-type destination and CR-active
    scaffolding.
  - Add negative tests proving data, source inputs, Compound GPID records,
    evidence fixtures, inbox ideas, and generated views are not placed in or
    treated as `c-research/` outputs.
  - Add a stale-reference test with an explicit historical-reference allowlist;
    operational old paths must fail the test.
  - Add byte/hash preservation and conflict tests for migration.
  - Add suite matrix tests for absent, `cg`, `cr`, and `cg, cr` configurations.
  - Ensure fixture data used to prove valid paths is substantive and cannot pass
    by placeholder content.
- **Tests**: focused migration, boundary, suite-matrix, Brain, and publishing
  fixture tests listed above.
- **Test Scenarios:** normal migration; idempotent rerun; partial migration;
  conflict; unknown file; symlink; all suite combinations; Brain exclusion;
  evidence root; generated target parity.
- **Acceptance criteria:** The test suite fails on stale operational paths,
  misplaced inputs, lost files, duplicate authorities, or incorrect suite
  scaffolding.

## Phase 7: Final Verification and Handoff

### 11. Execute the complete validation chain

- **Requirements**: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12
- **Files:** no new source files; execution report for this plan.
- **Details:**
  - Run focused migration, setup, CR-path, evidence-workbench, Brain, and
    generated-target tests first.
  - Run the repository Python tests affected by the migration.
  - Run the canonical safe Pester runner and read `tests/last-run.json`; do not
    invoke Pester as a directory or through unsafe output pipelines.
  - Run documentation and artifact freshness checks for the new plan and any
    changed canonical Markdown sources.
  - Run `git diff --check` and inspect the final path inventory, including
    uncommitted presentation files that predate this plan.
  - Record actual commands, pass/fail status, unresolved warnings, and any
    accepted exception in the execution report. Do not infer completion from
    static grep alone.
- **Tests**:
  - `python3 -m pytest scripts/tests/test_research_layout.py scripts/tests/test_research_evidence_docs.py scripts/brain/tests/test_scanner.py -q`
  - `uv run --project research_evidence pytest research_evidence/tests -q`
  - `python3 scripts/cg_generate_targets.py --all`
  - affected target/parity and documentation tests
  - canonical safe Pester runner through `tests/Run-Tests.ps1`
  - `git diff --check`
- **Acceptance criteria:** Required checks pass, the execution report contains
  evidence for every required verification row, and no unrelated user work is
  reverted or overwritten.

## Testing Strategy

- **Migration correctness:** use temporary repositories with identical,
  conflicting, missing, symlinked, and unknown source files; compare SHA-256
  bytes and frontmatter before/after.
- **Path contract:** assert every supported artifact type has the expected
  destination and that `data/` is never a destination.
- **Suite activation:** test new and returning projects under `cg`, `cr`, and
  mixed suite configurations; creation is conditional, deletion is never
  automatic.
- **CR workflow contracts:** test every operational old-path replacement in
  canonical prompts, skills, agents, instructions, and runtime docs.
- **Brain boundary:** test that `.cg-docs/` process records remain indexable and
  root-level `c-research/` outputs are not ingested by the generic scanner.
- **Generated targets:** regenerate all native targets and run ownership,
  closure, drift, and parity checks.
- **Evidence runtime:** run the full package suite and verify canonical evidence
  root, transaction recovery, offline enforcement, path safety, and original
  authority behavior.
- **Regression safety:** preserve existing publishing fixtures and views; run
  focused publishing evidence tests if path inventory or documentation changes
  touch their references.
- **Repository checks:** use `git diff --check`, affected Python tests, and the
  canonical safe Pester runner. Never use an unsafe Pester invocation.

## Documentation Checklist

- [ ] `c-research/README.md` documents output-only ownership, artifact types,
      separate `data/` inputs, human/agent dual use, and migration boundary.
- [ ] `docs/reference/files.md`, `docs/reference.md`, and `docs/workflow.md`
      describe `c-research/` and retain the `.cg-docs/` process map.
- [ ] Setup documentation describes conditional `cr` scaffolding and the
      non-destructive behavior when `cr` is disabled.
- [ ] CR prompts, skills, agents, and math instructions use operational
      `c-research/` paths.
- [ ] Evidence workbench README and runtime examples use
      `c-research/evidence/`.
- [ ] `.gitignore` ignores derived evidence state under the new root without
      ignoring canonical research outputs.
- [ ] Generic Brain documentation explains why `c-research/` is not scanned by
      the Compound process index.
- [ ] Existing shared fixture, inbox, and view documentation remains accurate.
- [ ] Every created file has the 2026-09-02 creation date in frontmatter or a
      header.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| A destination path collides with an existing user file | Compare bytes first; identical files are idempotent, differing files block the migration. |
| Untracked or modified presentation work is overwritten | Inventory status before moving; move only `.cg-docs/research/` files and preserve unrelated changes. |
| A research output is accidentally left under `.cg-docs/` | Operational stale-reference and source-inventory tests; remove the old tree only after verification. |
| A Compound GPID record is moved as if it were research output | Explicit allowlist for `.cg-docs/` process directories and boundary-preservation tests. |
| `data/` becomes an accidental output location | Path-contract tests reject data/input destinations and documentation states data is separate. |
| CR-only content leaks into CG-only contexts | Suite-aware setup and generated-target/module closure tests. |
| Generated native targets drift from canonical sources | Regenerate all targets and run ownership/parity/drift tests. |
| Historical plans become misleading or are rewritten | Classify historical references and preserve historical records; update only operational references. |
| Brain rebuild drops useful process knowledge or retains stale research entities | Rebuild after migration and compare expected retained entity classes with scanner tests. |
| Evidence workbench security/provenance changes during path migration | Change only the evidence-root setting and examples; run the complete package security and transaction suite. |
| Update scripts diverge across Windows and macOS | Both scripts invoke one shared Python migration helper; parity tests cover the invocation contract. |
| Missing path reference is hidden in a generated or ignored artifact | Scan canonical sources and generated target trees separately; exclude only documented historical/view/venv cases. |

## Out of Scope

- Moving `.cg-docs/evidence-fixtures/`, `.cg-docs/inbox/`, `.cg-docs/views/`,
  or any Compound GPID brainstorm, plan, review, strategy, solution, archive,
  or work-report record.
- Moving or renaming the `research_evidence/` Python package itself.
- Creating, moving, versioning, or documenting project data beyond stating that
  `data/` is separate input storage.
- Adding internet search, external-paper discovery, citation retrieval,
  citation-manager integration, hosted collaboration, or a new research
  backend.
- Creating a second Brain/index for `c-research/` outputs.
- Rewriting historical plan/brainstorm/review content solely to remove old path
  language.
- Refactoring unrelated module-registry, model-routing, or publishing behavior.

## Completion Contract

### Outcome

All canonical CR research outputs live under the root-level, artifact-type-
organized `c-research/` workspace. CR workflows and the local evidence
workbench read and write that workspace; `data/` remains separate, `.cg-docs/`
retains Compound GPID process/knowledge records, and shared publishing
fixtures, inbox content, and generated views remain in place.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|---|---:|---|---|---|
| V1 | 1 | Canonical layout and ownership contract lists every supported output type and separates outputs from `data/` inputs | `c-research/README.md`, `docs/reference/files.md`, targeted contract test | yes |
| V2 | 1 | Migration inventory detects all operational old paths, classifies historical paths, and reports deterministic moves/conflicts | `scripts/cg_migrate_research_layout.py --check <root>` plus migration tests | yes |
| V3 | 2 | Setup creates the complete `c-research/` scaffold only for active `cr` and never deletes an existing tree | Setup prompt/template tests and suite matrix fixtures | yes |
| V4 | 2 | Both update scripts invoke the same idempotent, conflict-safe structural migration | Focused `update.Tests.ps1`, `bash-scripts.Tests.ps1`, and migration helper tests | yes |
| V5 | 3 | Existing research files move to correct destinations with unchanged bytes/frontmatter and no duplicate old tree | Migration manifest/execution report plus content/hash tests | yes |
| V6 | 4 | All live CR prompts, skills, agents, instructions, scripts, package docs, and ignore rules use new paths | Stale-reference inventory test; zero unallowlisted operational `.cg-docs/research` matches | yes |
| V7 | 4 | Evidence workbench canonical state is rooted at `c-research/evidence/` with offline/security behavior unchanged | Package runtime/transaction tests and documentation tests | yes |
| V8 | 5 | Documentation and generic Brain retain Compound records while excluding root-level research outputs | Brain rebuild artifact and scanner regression tests | yes |
| V9 | 5 | Generated Claude, Codex, OpenCode, and Kilo targets match updated canonical CR sources | `python3 scripts/cg_generate_targets.py --all`; target/parity/drift tests | yes |
| V10 | 6 | Boundary tests reject data placement, misplaced shared records, stale operational paths, conflicts, and lost files | Focused Python/Pester boundary suites | yes |
| V11 | final | Existing shared fixtures, inbox, and generated views remain present and outside the migration | Filesystem/content preservation tests and targeted inventory | yes |
| V12 | final | Required Python, evidence, docs, generated-target, Brain, safe Pester, and whitespace checks execute successfully | Test outputs, `tests/last-run.json`, execution report, `git diff --check` | yes |

### Constraints

| ID | Phase | Constraint | Check |
|---|---:|---|---|
| C1 | 1-3 | `c-research/` is output-only and `data/` is never a migration destination | Path-contract and forbidden-destination tests |
| C2 | 1-5 | `.cg-docs/` remains the Compound GPID process/knowledge layer | Ownership documentation and scanner tests |
| C3 | 2 | Scaffolding is conditional on active `cr`; disabling `cr` is non-destructive | Setup suite matrix |
| C4 | 2-3 | Migration is idempotent, conflict-safe, symlink-safe, and preserves bytes/frontmatter | Migration helper tests and hash evidence |
| C5 | 3-5 | No second canonical `.cg-docs/research/` tree remains after verified migration | Source inventory and stale-path test |
| C6 | 4-5 | CR workflows read/write `c-research/`; generic Brain remains `.cg-docs/`-only | Prompt/skill/agent tests and scanner regression |
| C7 | 4-5 | Generated targets come from canonical `.github/` sources | Generator ownership/parity/drift checks |
| C8 | all | Shared fixtures, inbox ideas, generated views, and unrelated user changes are preserved | Boundary preservation and final diff review |
| C9 | 4-7 | Evidence offline, original-authority, transaction, and P0 research-integrity behavior does not regress | Full `research_evidence` suite and CR contract tests |
| C10 | final | Completion is based on executed evidence, not static inspection alone | Execution report and required command outputs |

### Boundaries

- **Allowed:** root-level `c-research/` output directories; migration of current
  `.cg-docs/research/` canonical files; CR prompts, skills, agents,
  instructions, runtime evidence paths, setup scaffolding, update scripts,
  documentation, tests, Brain rebuild, and generated native targets.
- **Out of scope:** data and source-input migration; Compound GPID process and
  knowledge records; evidence fixtures; inbox ideas; generated views; the
  research Python package location; external search or new research services.
- **Historical references:** may remain only when they are part of an immutable
  historical artifact and are listed in the explicit allowlist. They do not
  authorize the old path for new output.

### Iteration Policy

1. Inventory the old tree and all path references before mutating files.
2. Keep source files intact until destination hashes and conflict checks pass.
3. Apply the canonical path contract before updating dependent workflow text.
4. Update canonical `.github/` sources before regenerating native targets.
5. Preserve historical Compound GPID records and generated view locations.
6. Treat unresolved path ownership, destination conflicts, unknown source files,
   or suite semantics as ask-before-deviating decisions under `ask` policy.
7. Run focused validation after each phase and require all final evidence before
   linking the plan as done.

### Blocked-Stop Conditions

- A destination exists with different bytes or would overwrite user work.
- An unknown file, directory, symlink, or path reference cannot be classified
  safely.
- The migration would touch `evidence-fixtures/`, `inbox/`, `views/`, data,
  source inputs, or Compound GPID process records.
- A live operational `.cg-docs/research/` reference remains unresolved.
- CR-only content leaks into CG-only setup or generated targets.
- The generic Brain begins indexing `c-research/` without an explicitly approved
  separate research-index design.
- Evidence runtime security, provenance, transaction recovery, or offline
  behavior regresses.
- A required executable validation cannot run through the safe runner.
- Generated targets drift or the execution report cannot be durably updated.
- Completion would require treating static inspection as executed evidence.

### Deviation Policy

`ask`
