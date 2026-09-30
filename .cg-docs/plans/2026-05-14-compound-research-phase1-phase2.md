---
date: 2026-05-14
title: "Compound Research — Phase 1 (Module System) & Phase 2 (Research Workflow Scaffolding)"
status: completed
completed-date: 2026-05-14
completed-phases: [1, 2]
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-05-13-compound-research-extension.md"
language: "PowerShell, Python, Markdown"
estimated-effort: "large"
phases: 2
tags: [compound-research, module-system, research-workflow, architecture, cr-prompts]
---

# Plan: Compound Research — Phase 1 (Module System) & Phase 2 (Research Workflow Scaffolding)

## Objective

Build the foundation for compound-research: a module-tagging system that lets
projects opt into engineering, research, or both; and the core `/cr-*` prompt
scaffolding that mirrors the existing `/cg-*` workflow loop with a research
task-type classifier. At the end of this plan, a user can enable the research
module, run `/cr-brainstorm`, and get a research-aware brainstorming session
with task-type classification — though the specialized agents and skills
(Phases 3–7) won't exist yet.

## Context

The brainstorm ([2026-05-13-compound-research-extension.md](.cg-docs/brainstorms/2026-05-13-compound-research-extension.md))
decided on Approach 3: Plugin Module System — same repo, lazy-loaded modules.
The roadmap milestone `compound-research` has 8 features (one per phase), all
at status `idea`.

**Current state of the codebase:**
- Prompts have frontmatter: `description:`, `model:`. No `module:` field.
- Agents have: `description:`, `model:`, `tools:`, `user-invocable:`. No `module:`.
- Skills have: `name:`, `description:`. No `module:`.
- Instructions have: `applyTo:`. No `module:`.
- `copilot-instructions.md` is generated from `.github/copilot-instructions.template.md`
  by `New-CopilotInstructions` (in `scripts/helpers.ps1`) and `generate_copilot_instructions()`
  (in `scripts/link.sh`). Both read `compound-gpid.local.md` for substitution values.
- `compound-gpid.local.md` schema: `language`, `r-syntax`, `project-type`, `review-depth`, `created`, `cg-schema-version`.
- `/cg-setup` (via `cg-skill-setup`) creates `compound-gpid.local.md`.

**Key constraint**: All existing tests must continue to pass. Default module
is `engineering` — backward compatible. No existing file's behavior changes
unless the user explicitly enables `research`.

## Requirements

| ID  | Requirement | Source |
|-----|-------------|--------|
| R1  | Every prompt, agent, skill, and instruction file gains a `module:` frontmatter field (`shared`, `engineering`, or `research`) | Brainstorm: Module-tagging convention |
| R2  | `compound-gpid.local.md` schema gains a `modules:` field (list of active modules) | Brainstorm: Non-functional requirements |
| R3  | Default module = `engineering` — projects without explicit `modules:` config work unchanged | Brainstorm: Backward compatibility |
| R4  | `copilot-instructions.template.md` gains a `{{modules}}` section listing active modules | Brainstorm: Modular activation |
| R5  | `cg-link` / `cg-update` read `modules:` from local config and include it in the generated `copilot-instructions.md` | Brainstorm: cg-link integration |
| R6  | `/cg-setup` asks about modules at setup time | Brainstorm: cg-setup integration |
| R7  | `/cr-brainstorm` mirrors `/cg-brainstorm` with a research task-type classifier at Step 1.1 | Brainstorm: Task taxonomy |
| R8  | `/cr-plan` mirrors `/cg-plan` with research-aware context | Brainstorm: Workflow loop |
| R9  | `/cr-work` mirrors `/cg-work` with task-type-aware execution and P0 seed enforcement | Brainstorm: Workflow loop |
| R10 | `/cr-review` mirrors `/cg-review` with orchestration of both `cg-*` and `cr-*` agents | Brainstorm: /cr-review orchestration |
| R11 | `/cr-compound` mirrors `/cg-compound` with research-specific solution categories | Brainstorm: Workflow loop |
| R12 | `.cg-docs/research/` directory layout created during setup | Brainstorm: Directory layout |
| R13 | Research Integrity Priority System (P0–P3) documented in `cr-skill-research-workflow` | Brainstorm: Research integrity |
| R14 | `cr-skill-research-workflow` created as the overarching CR loop skill | Brainstorm: Skills |
| R15 | `cr-skill-research-integrity` created as the P0 silent-error catalog | Brainstorm: Skills |
| R16 | Tests: module frontmatter present and valid on all files; CR prompts have canonical structure | Brainstorm: Testing |
| R17 | All existing tests continue to pass after changes | Constraint: backward compatibility |

## Phase 1: Module System Foundation

### 1. Add `module:` frontmatter to all existing files
- **Requirements**: R1, R17
- **Files**: All files in `.github/prompts/`, `.github/agents/`, `.github/skills/*/SKILL.md`, `.github/instructions/`
- **Details**:
  Add `module: shared` or `module: engineering` to every existing frontmatter block.
  Tagging decisions per file (from brainstorm):

  **Prompts** — `shared`:
  - `cg-brainstorm.prompt.md`, `cg-plan.prompt.md`, `cg-compound.prompt.md`,
    `cg-resume.prompt.md`, `cg-ideate.prompt.md`, `cg-strategy.prompt.md`,
    `cg-plan-review.prompt.md`, `cg-roadmap-view.prompt.md`, `cg-setup.prompt.md`,
    `cg-diagnose.prompt.md`, `cg-compound-refresh.prompt.md`, `cg-devtag.prompt.md`

  **Prompts** — `engineering`:
  - `cg-work.prompt.md`, `cg-review.prompt.md`, `cg-fix-triage.prompt.md`,
    `cg-fixbug.prompt.md`, `cg-fix-problems.prompt.md`, `cg-review-repos.prompt.md`

  **Agents** — `shared`:
  - `cg-code-quality`, `cg-testing`, `cg-reproducibility`, `cg-data-quality`,
    `cg-performance`, `cg-architecture`, `cg-adversarial`, `cg-documentation`,
    `cg-version-control`, `cg-learnings-researcher`, `cg-plan-critic`,
    `cg-roadmap`, `cg-roadmap-view`, `cg-project-scanner`, `cg-release-scanner`

  **Agents** — `engineering`:
  - `cg-fix-problems`

  **Skills** — `shared`:
  - `cg-skill-brainstorming`, `cg-skill-compound-docs`, `cg-skill-git-workflow`,
    `cg-skill-pester-safety`, `cg-skill-setup`, `cg-skill-project-scanner`,
    `cg-skill-r-shared`, `cg-skill-r-collapse`, `cg-skill-r-datatable`,
    `cg-skill-r-tidyverse`, `cg-skill-r-visualization`, `cg-skill-r-testing`,
    `cg-skill-r-analytical`, `cg-skill-python-best-practices`,
    `cg-skill-stata-best-practices`, `cg-skill-stata-testing`

  **Skills** — `engineering`:
  - `cg-skill-r-technical`, `cg-skill-fix-triage-migrate`

  **Instructions** — `shared`:
  - `r.instructions.md`, `python.instructions.md`, `stata.instructions.md`

  The `module:` field is added to existing frontmatter blocks without changing
  any other field or any content below the frontmatter. Position: after
  `description:` (or after `applyTo:` for instructions, after `name:` for skills).

- **Test Scenarios**:
  - ✅ Every `.prompt.md`, `.agent.md`, `SKILL.md`, and instruction `.md` has a `module:` field
  - ✅ Every `module:` value is one of `shared`, `engineering`, `research`
  - 🛑 A file with no frontmatter at all (should not exist, but test handles gracefully)
  - ❌ A `module:` value that is not in the permitted set
- **Tests**: New test block in `prompt-tools.Tests.ps1` — enumerate all managed files,
  extract frontmatter, assert `module:` present and valid.
- **Acceptance criteria**: Every file under `.github/{prompts,agents,skills,instructions}`
  has a valid `module:` field. All existing tests still pass.

### 2. Extend `compound-gpid.local.md` schema with `modules:`
- **Requirements**: R2, R3
- **Files**: `.github/skills/cg-skill-setup/SKILL.md`
- **Details**:
  Add a `modules:` field to the `compound-gpid.local.md` schema in `cg-skill-setup`.
  Format: `modules: "engineering"` (default) or `modules: "engineering, research"` or
  `modules: "research"`. Comma-separated string (not YAML list — keeps frontmatter
  parsing simple with existing `extract_fm_value` regex).

  Update the schema example in `cg-skill-setup/SKILL.md`:
  ```yaml
  modules: "engineering"            # Options: engineering, research, or both (comma-separated)
  ```

  Document: if `modules:` is absent, default to `"engineering"`.

- **Test Scenarios**:
  - ✅ `compound-gpid.local.md` with `modules: "engineering"` is valid
  - ✅ `compound-gpid.local.md` with `modules: "engineering, research"` is valid
  - ✅ `compound-gpid.local.md` without `modules:` defaults to `engineering`
  - 🛑 `modules: "banana"` — invalid module name
- **Tests**: Schema validation test in setup test file or `prompt-tools.Tests.ps1`.
- **Acceptance criteria**: The `cg-skill-setup/SKILL.md` documents the new field.

### 3. Update `/cg-setup` to ask about modules
- **Requirements**: R6, R3
- **Files**: `.github/prompts/cg-setup.prompt.md`, `.github/skills/cg-skill-setup/SKILL.md`
- **Details**:
  Add a new question to the setup flow (after Question 2: Project Type):

  > **Question 2b: Active Modules**
  >
  > What workflows does this project need?
  > 1. **Engineering only** — data pipelines, infrastructure, production code *(default)*
  > 2. **Research only** — economics/econometric research, paper writing, derivations
  > 3. **Both** — engineering and research workflows

  Map answers to `modules:` values:
  - Engineering only → `"engineering"`
  - Research only → `"research"`
  - Both → `"engineering, research"`

  If `modules:` includes `research`, also create the `.cg-docs/research/` directory tree
  (Step R12). Do NOT create it for engineering-only projects.

- **Test Scenarios**:
  - ✅ `/cg-setup` prompt contains module selection question text
  - ✅ The setup skill documents the research directory layout
- **Tests**: Content assertions in `prompt-tools.Tests.ps1`.
- **Acceptance criteria**: The setup flow asks about modules. Engineering-only
  projects see no difference from today.

### 4. Update `copilot-instructions.template.md` with module awareness
- **Requirements**: R4
- **Files**: `.github/copilot-instructions.template.md`
- **Details**:
  Add a `{{modules}}` placeholder and a new section:

  ```markdown
  ## Active Modules

  - **Modules**: {{modules}}
  ```

  This section appears after "Project Identity". When `modules` includes `research`:
  - Copilot sees `research` in the active modules list
  - This triggers loading of `cr-*` prompts/skills/agents when relevant

  The template does NOT conditionally include/exclude content — it simply declares
  the active modules. The filtering happens at the Copilot skill/agent level: each
  `cr-*` prompt's Step 0 checks `compound-gpid.local.md` for `modules:` and only
  proceeds if `research` is in the list. This avoids complex template logic in the
  generation pipeline.

- **Test Scenarios**:
  - ✅ Template contains `{{modules}}` placeholder
  - ✅ Generated output contains the modules value
  - 🛑 Missing `modules:` in local config → defaults to `"engineering"`
- **Tests**: Existing template tests in `helpers.Tests.ps1` extended to check
  `{{modules}}` substitution.
- **Acceptance criteria**: Template contains the new section. Placeholder is substituted.

### 5. Update `New-CopilotInstructions` (PS) and `generate_copilot_instructions` (bash) to read `modules:`
- **Requirements**: R5, R3
- **Files**: `scripts/helpers.ps1`, `scripts/link.sh`
- **Details**:
  **PowerShell** (`New-CopilotInstructions` in `helpers.ps1`):
  - Read `modules:` from `compound-gpid.local.md` frontmatter (same `extract_fm_value` pattern).
  - Default to `"engineering"` if absent.
  - Add `$output = $output.Replace('{{modules}}', $modules)` to the substitution chain.

  **Bash** (`generate_copilot_instructions` in `link.sh`):
  - Read `modules` using existing `extract_fm_value()` Python helper.
  - Default to `"engineering"` if absent.
  - Add `output = output.replace('{{modules}}', modules)` to the substitution chain.

  Guard: validate that `modules` value contains only permitted tokens
  (`engineering`, `research`, commas, spaces). Reject if it contains `{{`.

- **Test Scenarios**:
  - ✅ `modules: "engineering"` → output contains `engineering`
  - ✅ `modules: "engineering, research"` → output contains both
  - ✅ Missing `modules:` → output contains `engineering` (default)
  - ❌ `modules: "{{project-name}}"` → rejected (placeholder guard)
- **Tests**: Extend `helpers.Tests.ps1` unit tests for `New-CopilotInstructions`.
  Bash tests via `bash-scripts.Tests.ps1` if pattern exists.
- **Acceptance criteria**: Both PS and bash generation paths read `modules:` and
  substitute it. Default is `engineering`. Existing projects unaffected.

### 6. Write Phase 1 tests
- **Requirements**: R16, R17
- **Files**: `tests/prompt-tools.Tests.ps1` (extended), `tests/helpers.Tests.ps1` (extended)
- **Details**:
  **Module frontmatter tests** (in `prompt-tools.Tests.ps1`):
  ```
  Describe "All managed files have valid module: frontmatter" {
    - Enumerate all .prompt.md files in .github/prompts/
    - Enumerate all .agent.md files in .github/agents/
    - Enumerate all SKILL.md files in .github/skills/*/
    - Enumerate all .md files in .github/instructions/
    - For each: extract frontmatter, assert module: field exists
    - Assert module: value is one of: shared, engineering, research
  }
  ```

  **Template substitution tests** (in `helpers.Tests.ps1`):
  ```
  Describe "New-CopilotInstructions - modules substitution" {
    - Test with modules: "engineering" → output contains "engineering"
    - Test with modules: "engineering, research" → output contains both
    - Test with no modules: field → defaults to "engineering"
  }
  ```

- **Acceptance criteria**: All new tests pass. All existing tests pass.

## Phase 2: Research Workflow Scaffolding

### 7. Create `cr-skill-research-workflow`
- **Requirements**: R14, R13
- **Files**: `.github/skills/cr-skill-research-workflow/SKILL.md`
- **Details**:
  The overarching skill for the research module. Contains:
  - **Research task taxonomy** — the 8 task types with descriptions and examples:
    Theory/Modeling, Specification Analysis, EDA, Implementation, ML/Prediction,
    Writing, Tables/Figures, Reproducibility
  - **Research Integrity Priority System** (P0–P3) — the full table from the
    brainstorm with categories, examples, and enforcement rules
  - **Active P0 detection mechanisms** — code-math mismatch detector, specification
    search tracker, identification audit, seed enforcement
  - **Verification chain** — always: derivation trail; always in review: symbolic
    checks; offered after review: Monte Carlo simulation
  - **`.cg-docs/research/` directory layout** — derivations/, specifications/,
    results/, manuscript/, replication/
  - **Reasoning trail documentation requirement** — every research artifact must
    record the *why* (theory, data evidence, alternatives considered)
  - **PhD student scaffolding convention** — when a step involves a modeling choice,
    document the decision reasoning at a level appropriate for a PhD student learning
    the methodology

  Frontmatter:
  ```yaml
  ---
  name: cr-skill-research-workflow
  module: research
  description: "Overarching conventions for the compound-research workflow loop.
    Covers research task taxonomy (8 types), Research Integrity Priority System
    (P0–P3), active P0 detection mechanisms, verification chain, .cg-docs/research/
    layout, reasoning-trail documentation, and PhD student scaffolding conventions.
    ALWAYS load for any /cr-* command."
  ---
  ```

- **Test Scenarios**:
  - ✅ SKILL.md exists and has valid frontmatter
  - ✅ Contains all 8 task types
  - ✅ Contains P0–P3 priority table
  - ✅ `module: research`
- **Tests**: In `prompt-tools.Tests.ps1` — content assertions on SKILL.md.
- **Acceptance criteria**: Skill file created, frontmatter valid, content covers
  all required sections.

### 8. Create `cr-skill-research-integrity`
- **Requirements**: R15
- **Files**: `.github/skills/cr-skill-research-integrity/SKILL.md`
- **Details**:
  The P0 silent-error catalog skill. Contains detailed detection patterns and
  remediation guidance for each class of silent research error:

  1. **Code-math mismatch** — detection: compare variable names, functional forms,
     and operations between LaTeX derivation and code implementation. Remediation:
     side-by-side audit, variable mapping table.
  2. **Specification searching** — detection: count estimation runs in manifest vs.
     specifications reported in paper. Remediation: report all specifications or
     explicitly document the selection criterion.
  3. **Identification theater** — detection: claimed strategy (IV/RDD/DiD) without
     matching diagnostic (first-stage F, McCrary, parallel trends). Remediation:
     run the diagnostic; if it fails, revisit the identification strategy.
  4. **Unseeded randomness** — detection: scan code for bootstrap/simulation/CV
     calls without preceding `set.seed()` / `np.random.seed()` / `set seed`.
     Remediation: add explicit seed at the top of every random code block.
  5. **Asymptotic assumption violations** — detection: check sample size against
     estimator requirements (e.g., MLE needs n >> p). Flag when n/p < 10.
  6. **Wrong SE clustering** — detection: check if clustering level matches the
     treatment variation level. Flag mismatch.
  7. **Distributional assumption untested** — detection: if the model assumes a
     distributional form (normal errors, log-normal wages), check whether an
     empirical test was run. Flag if not.

  Frontmatter:
  ```yaml
  ---
  name: cr-skill-research-integrity
  module: research
  description: "Catalog of P0 silent research errors with detection patterns and
    remediation. Covers code-math mismatch, specification searching, identification
    theater, unseeded randomness, asymptotic-assumption violations, wrong SE
    clustering, and untested distributional assumptions. Loaded by @cr-research-integrity
    and /cr-review."
  ---
  ```

- **Test Scenarios**:
  - ✅ SKILL.md exists and has valid frontmatter
  - ✅ Contains all 7 error classes
  - ✅ `module: research`
- **Tests**: Content assertions in `prompt-tools.Tests.ps1`.
- **Acceptance criteria**: Skill file created with all 7 error classes documented.

### 9. Create `/cr-brainstorm`
- **Requirements**: R7
- **Files**: `.github/prompts/cr-brainstorm.prompt.md`
- **Details**:
  Mirrors `/cg-brainstorm` structure (Step 0 through Step 5) with these
  research-specific adaptations:

  **Step 0**: Same Get Bearings (read charter, local, context). Add:
  - Check `modules:` in `compound-gpid.local.md`. If `research` is not in the
    active modules, warn: "Research module is not enabled. Run `/cg-setup` to
    add it, or proceed anyway?"
  - Load `cr-skill-research-workflow` always.

  **Step 1.1 — Research Task Classification** (replaces Software/Thinking Partner):
  Classify the user's request into one of the 8 research task types. Show the
  classification to the user for confirmation:
  > "This looks like a **[Theory/Modeling | Specification Analysis | EDA |
  > Implementation | ML/Prediction | Writing | Tables/Figures | Reproducibility]**
  > task. Confirm or correct?"

  Based on confirmed task type, load the appropriate skill bundle (from the
  brainstorm's task taxonomy table). For Phase 2 (before skills exist),
  state which skills would be loaded and note they're not yet available.

  **Step 1.5 — Scope Assessment**: Same table as `/cg-brainstorm`.

  **Step 1.7 — Branch Offer**: Same as `/cg-brainstorm`.

  **Step 2 — Clarifying Questions**: Adapt question areas by task type:
  - Theory/Modeling: What is the economic model? What is the DGP? What
    identification strategy? What are the key assumptions?
  - Specification Analysis: What theoretical prediction are we testing?
    What data features would confirm/refute it?
  - EDA: What is the research question motivating this exploration?
    What distributional features matter?
  - Implementation: Which derived model are we coding? Where is the derivation?
    What numerical considerations (convergence, starting values)?
  - ML/Prediction: What is the prediction target? What is the economic
    interpretation? What is the sample structure (panel, cross-section)?
  - Writing: Which section? What is the key argument? What journal style?
  - Tables/Figures: What story does this table/figure tell? What format?
  - Reproducibility: What journal's standards? What data is sensitive?

  **Step 3 — Propose Approaches**: Same structure. For Theory/Modeling,
  approaches should compare alternative modeling strategies (parametric vs.
  semi-parametric, MLE vs. GMM, etc.).

  **Step 3.5 — Devil's Advocate**: Same 4-check structure, with
  research-specific adaptations:
  - Problem validation: "Is this research question well-posed? Is there a clear
    null hypothesis?"
  - Simplicity check: "Could a reduced-form approach answer this without the
    structural model?"
  - Effort-value: "Is the full structural model justified by the research
    question, or would a simpler approach suffice for the paper's contribution?"
  - Charter alignment: Same.

  **Steps 4, 5**: Same as `/cg-brainstorm`. Brainstorm saved to `.cg-docs/brainstorms/`.
  Handoff offers `/cr-plan` instead of `/cg-plan`.

  Frontmatter:
  ```yaml
  ---
  description: "Research brainstorm — clarify fuzzy research requirements. Classifies
    task type (theory, EDA, implementation, ML, writing, etc.) and guides methodology
    decisions. Use for economics and econometrics research tasks."
  model: Claude Opus 4.6 (copilot)
  module: research
  ---
  ```

- **Test Scenarios**:
  - ✅ Has valid frontmatter with `module: research`
  - ✅ Contains research task classification step (Step 1.1) with all 8 task types
  - ✅ Contains "Specification Analysis" as a task type
  - ✅ Contains Devil's Advocate step (Step 3.5)
  - ✅ Handoff references `/cr-plan` not `/cg-plan`
  - ✅ Loads `cr-skill-research-workflow`
  - 🛑 No `tools:` restriction (orchestrating prompt)
- **Tests**: Content assertions in a new `cr-prompts.Tests.ps1` test file.
- **Acceptance criteria**: Prompt is structurally complete and mirrors the CG
  brainstorm pattern with research task classification.

### 10. Create `/cr-plan`
- **Requirements**: R8
- **Files**: `.github/prompts/cr-plan.prompt.md`
- **Details**:
  Mirrors `/cg-plan` with research-specific context:

  - Step 0: Same. Check `modules:`.
  - Step 1: Gather context. In addition to brainstorm and directory scan,
    also read `.cg-docs/research/derivations/` if the task is Implementation
    (to understand the math being coded).
  - Step 1.5: Same scope assessment.
  - Step 2: Research. In addition to codebase patterns, also research:
    - Are there derivation files that this implementation must match?
    - What existing specification analysis results inform this work?
    - What seed conventions are established?
  - Step 3: Same plan structure, with research-specific additions:
    - For Implementation tasks: add a "Mathematical Reference" section
      linking to derivation files in `.cg-docs/research/derivations/`.
    - For all tasks: add research integrity checks to the Testing Strategy
      (P0 checks from `cr-skill-research-integrity`).
  - Steps 3.5 through 6: Same as `/cg-plan`. Handoff offers `/cr-work`.

  Frontmatter:
  ```yaml
  ---
  description: "Research plan — structured implementation plan for research tasks.
    Use after /cr-brainstorm to create concrete steps."
  model: Claude Opus 4.6 (copilot)
  module: research
  ---
  ```

- **Test Scenarios**:
  - ✅ Has valid frontmatter with `module: research`
  - ✅ References `.cg-docs/research/derivations/`
  - ✅ Handoff references `/cr-work`
  - ✅ No `tools:` restriction
- **Tests**: In `cr-prompts.Tests.ps1`.
- **Acceptance criteria**: Prompt mirrors CG plan structure with research context.

### 11. Create `/cr-work`
- **Requirements**: R9
- **Files**: `.github/prompts/cr-work.prompt.md`
- **Details**:
  Mirrors `/cg-work` with task-type-aware execution:

  - Step 0: Same. Check `modules:`. Read the plan from `.cg-docs/plans/`.
  - Load `cr-skill-research-workflow` and `cr-skill-research-integrity`.
  - **Seed enforcement** (active during work, not just review): Before
    executing any code that involves randomness, check for explicit seed.
    If missing, halt and add one. This is a P0 enforcement.
  - **Specification logging**: When running estimation code, log the
    specification to `.cg-docs/research/results/manifest.json` (create if
    absent). Format: `{"date": "...", "description": "...", "file": "...", "seed": N}`.
  - **Derivation cross-reference**: When implementing from a derivation,
    load the corresponding `.cg-docs/research/derivations/*.tex` file and
    verify variable naming and functional form consistency.
  - Phased execution support: same as `/cg-work` (`/cr-work phase1`).
  - After completing work, offer: "Run `/cr-review` to check this work?"

  Frontmatter:
  ```yaml
  ---
  description: "Research work — implement a research plan step by step. Supports
    /cr-work [phaseX]. Enforces P0 seed requirements and specification logging."
  model: Claude Sonnet 4.6 (copilot)
  module: research
  ---
  ```

- **Test Scenarios**:
  - ✅ Has valid frontmatter with `module: research`
  - ✅ Contains seed enforcement logic
  - ✅ Contains specification logging to manifest.json
  - ✅ Supports phased execution (`/cr-work phase1`)
  - ✅ References `cr-skill-research-integrity`
- **Tests**: In `cr-prompts.Tests.ps1`.
- **Acceptance criteria**: Prompt implements P0 seed enforcement and spec logging.

### 12. Create `/cr-review`
- **Requirements**: R10
- **Files**: `.github/prompts/cr-review.prompt.md`
- **Details**:
  The choreographer prompt. Orchestrates both shared `cg-*` agents and
  new `cr-*` agents (which won't exist until Phase 3, but the dispatch
  structure must be in place now).

  **Review orchestration** (from brainstorm):
  ```
  Step 1: Dispatch shared agents (always)
    - @cg-code-quality, @cg-testing, @cg-reproducibility, @cg-data-quality,
      @cg-version-control, @cg-documentation

  Step 2: Dispatch CR-specific agents (when they exist)
    - @cr-research-integrity      # P0 silent-error detection
    - @cr-mathematical-verification # symbolic checks (if derivation exists)
    - @cr-identification-audit     # if identification strategy claimed

  Step 3: Dispatch task-type-specific agents (conditional)
    - Theory/Modeling     → @cr-econometric-reasoning, @cg-adversarial
    - Specification Analysis → @cr-specification-analysis
    - ML/Prediction       → @cr-ml-methodology, @cg-performance
    - Writing             → @cr-academic-writing
    - Reproducibility     → @cr-replication-package

  Step 4: Merge findings, sort by priority (P0 → P3)

  Step 5: Offer Monte Carlo verification (if applicable)
  ```

  For Phase 2: Steps 2 and 3 note "Agent not yet available — skip" for
  `cr-*` agents. The shared `cg-*` agents in Step 1 work immediately.
  The structure is in place for Phase 3 to fill in.

  Frontmatter:
  ```yaml
  ---
  description: "Research review — multi-agent code and methodology review.
    Orchestrates cg-* agents (code quality, testing, reproducibility) and
    cr-* agents (research integrity, mathematical verification, identification audit).
    Produces prioritized P0/P1/P2/P3 findings."
  model: Claude Sonnet 4.6 (copilot)
  module: research
  ---
  ```

- **Test Scenarios**:
  - ✅ Has valid frontmatter with `module: research`
  - ✅ References all shared `cg-*` agents by name
  - ✅ References `@cr-research-integrity`, `@cr-mathematical-verification`, `@cr-identification-audit`
  - ✅ Contains P0/P1/P2/P3 priority ordering
  - ✅ Contains Monte Carlo verification offer
  - ✅ No `tools:` restriction (orchestrating prompt)
- **Tests**: In `cr-prompts.Tests.ps1`.
- **Acceptance criteria**: Full orchestration structure documented. Shared agents
  callable immediately; CR agents marked as Phase 3.

### 13. Create `/cr-compound`
- **Requirements**: R11
- **Files**: `.github/prompts/cr-compound.prompt.md`
- **Details**:
  Mirrors `/cg-compound` with research-specific solution categories:
  - Existing categories: `bugs`, `build-errors`, `performance-issues`,
    `testing-patterns`, `data-quality`, `environment-issues`, `git-workflows`
  - New research categories: `identification`, `specification`, `derivation`,
    `ml-methodology`, `reproducibility`

  When capturing a research lesson, the prompt guides the user to select
  from the extended category list. Research categories are created under
  `.cg-docs/solutions/` alongside existing engineering categories.

  Frontmatter:
  ```yaml
  ---
  description: "Research compound — capture a solved research problem for future
    reuse. Extends /cg-compound with research-specific categories: identification,
    specification, derivation, ml-methodology, reproducibility."
  model: Claude Sonnet 4.6 (copilot)
  module: research
  ---
  ```

- **Test Scenarios**:
  - ✅ Has valid frontmatter with `module: research`
  - ✅ Contains all 5 new research categories
  - ✅ Contains all 7 existing engineering categories (inherited)
- **Tests**: In `cr-prompts.Tests.ps1`.
- **Acceptance criteria**: Prompt created with extended category list.

### 14. Create `.cg-docs/research/` directory layout in `/cg-setup`
- **Requirements**: R12
- **Files**: `.github/skills/cg-skill-setup/SKILL.md`
- **Details**:
  When `modules:` includes `research`, `/cg-setup` creates:
  ```
  .cg-docs/research/
  ├── derivations/
  │   └── .gitkeep
  ├── specifications/
  │   └── .gitkeep
  ├── results/
  │   └── .gitkeep
  ├── manuscript/
  │   └── .gitkeep
  └── replication/
      └── .gitkeep
  ```

  Also create the new solution categories:
  ```
  .cg-docs/solutions/identification/.gitkeep
  .cg-docs/solutions/specification/.gitkeep
  .cg-docs/solutions/derivation/.gitkeep
  .cg-docs/solutions/ml-methodology/.gitkeep
  .cg-docs/solutions/reproducibility/.gitkeep
  ```

  Update the directory tree in Step 5 of `cg-skill-setup/SKILL.md` to show
  these as conditional on `modules: research`.

- **Test Scenarios**:
  - ✅ Setup skill documents the research directory layout
  - ✅ Directories are conditional on research module activation
- **Tests**: Content assertions in `prompt-tools.Tests.ps1`.
- **Acceptance criteria**: Setup skill updated. Engineering-only projects don't
  get research directories.

### 15. Write Phase 2 tests
- **Requirements**: R16, R17
- **Files**: `tests/cr-prompts.Tests.ps1` (new file)
- **Details**:
  New test file for all CR prompt structural tests:

  ```
  Describe "CR prompt files - structural checks" {
    # Enumerate all cr-*.prompt.md files
    # For each: valid frontmatter, module: research, no tools: restriction
  }

  Describe "cr-brainstorm.prompt.md - research task classifier" {
    # Contains Step 1.1 with all 8 task types
    # Contains Devil's Advocate
    # Handoff references /cr-plan
  }

  Describe "cr-review.prompt.md - agent orchestration" {
    # References shared cg-* agents
    # References cr-* agents
    # Contains P0-P3 priority ordering
    # Contains Monte Carlo verification offer
  }

  Describe "cr-skill-research-workflow - content" {
    # Contains all 8 task types
    # Contains P0-P3 table
    # module: research
  }

  Describe "cr-skill-research-integrity - content" {
    # Contains all 7 error classes
    # module: research
  }
  ```

- **Acceptance criteria**: All tests pass. All existing tests still pass.

## Testing Strategy

- **Structural tests** (Pester): Frontmatter validation, content assertions,
  cross-reference checks (e.g., `/cr-review` references agents that exist or
  are planned).
- **Generation tests** (Pester): `New-CopilotInstructions` correctly reads and
  substitutes `modules:` with proper defaulting.
- **Backward compatibility**: Run the full existing test suite after every step.
  No existing test may fail.
- **Test file organization**: Phase 1 tests go in existing files
  (`prompt-tools.Tests.ps1`, `helpers.Tests.ps1`). Phase 2 tests go in a new
  `cr-prompts.Tests.ps1` to keep CR-specific tests separate.

## Documentation Checklist

- [ ] `cg-skill-setup/SKILL.md` updated with `modules:` field and research directory layout
- [ ] `copilot-instructions.template.md` updated with `{{modules}}` section
- [ ] Each new CR prompt has inline documentation of its process
- [ ] `cr-skill-research-workflow` documents the full task taxonomy, priority system, and conventions
- [ ] `cr-skill-research-integrity` documents all 7 error classes with detection and remediation

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Adding `module:` to all existing frontmatter breaks parsing | Existing tests fail; prompts/agents/skills stop loading | Test each file type individually. The field is additive — VS Code/Copilot ignores unknown frontmatter fields. Run full test suite after. |
| `{{modules}}` placeholder not substituted → shows raw in generated file | User sees `{{modules}}` in copilot-instructions.md | Same guard as existing placeholders: `extract_fm_value` defaults to `"engineering"`. Template substitution tested in `helpers.Tests.ps1`. |
| CR prompts reference CR agents that don't exist yet (Phase 3) | `/cr-review` tries to dispatch `@cr-research-integrity` and fails | Each CR agent reference includes a guard: "If agent not available, skip and note in review output." Phase 3 fills them in. |
| Module frontmatter field rejected by VS Code Copilot | Prompts/agents stop being recognized | The `module:` field is not a reserved Copilot key. VS Code ignores unknown frontmatter fields (confirmed by existing `user-invocable:` field in agents, which is custom). |
| Large diff on Phase 1 (touching every file) | Review becomes unwieldy | Phase 1 changes are mechanical (one line per file) — easy to batch-review. Test coverage catches any breakage. |

## Out of Scope

- Creating the actual `@cr-*` agents (Phase 3)
- Creating the domain skills: structural econometrics, ML, writing, etc. (Phases 4–7)
- Creating `latex.instructions.md` or `math.instructions.md` (Phase 4)
- Conditional template generation (excluding CR prompts from `copilot-instructions.md` for engineering-only projects) — the template simply declares modules; skill/prompt Step 0 guards handle the filtering
- Updating `docs/reference.md`, `README.md`, or `docs/manual.md` (Phase 8)
- Charter update for new scope (Phase 8)
