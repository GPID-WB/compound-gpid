---
date: 2026-04-16
title: "Context Layer Restructuring"
status: completed
completed-date: 2026-04-17
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-04-16-context-layer-restructuring.md"
language: "PowerShell + Markdown"
estimated-effort: "large"
tags: [context, copilot-instructions, template, consumer-projects, step-0, multi-folder]
---

# Plan: Context Layer Restructuring

## Objective

Restructure how consumer projects receive Copilot context so that
`copilot-instructions.md` becomes a slim (~40 line), project-specific
generated file instead of a bloated generic copy; introduce
`compound-gpid.context.md` for freeform project knowledge that grows over
time; add multi-folder workspace awareness; and detect stale Current Focus
when milestones complete.

## Context

Today, `cg-link` copies compound-gpid's own ~150-line `copilot-instructions.md`
verbatim into every consumer project. Most of that content (Pester safety
rules, R skill routing, coding standards boilerplate, workflow entry points)
is irrelevant to consumer projects or already available via skills and
instruction files. This wastes premium context window real estate on every
Copilot interaction.

The brainstorm and strategy session (`.cg-docs/strategy/2026-04-16-context-layer-restructuring.md`)
decided on five features (roadmap milestone `context-layer`):

1. Slim generated `copilot-instructions.md` from a template
2. New `compound-gpid.context.md` for growing project knowledge
3. `/cg-compound` proposes context.md additions
4. Multi-folder workspace awareness
5. Auto-detect stale Current Focus on milestone completion

Key design decisions:
- Charter stays read-only for enrichment; growing knowledge goes to context.md
- Single ownership model for context.md (no user/AI sections; topic-based)
- context.md is committed to git (institutional knowledge)
- Loading model: copilot-instructions.md (auto-injected), charter + context.md (Step 0)
- Template generation must work even without charter/local config (placeholder fallbacks)

## Requirements

| ID  | Requirement                                              | Source    |
|-----|----------------------------------------------------------|-----------|
| R1  | Template file with placeholders for project-specific values | brainstorm |
| R2  | Generation function in helpers.ps1 that fills the template | brainstorm |
| R3  | link.ps1 generates copilot-instructions.md instead of copying | brainstorm |
| R4  | update.ps1 regenerates copilot-instructions.md instead of copying | brainstorm |
| R5  | Fallback values when charter/local config don't exist yet | brainstorm |
| R6  | Backward-compatible managed marker preservation | brainstorm |
| R7  | compound-gpid.context.md created by /cg-setup | brainstorm |
| R8  | Step 0 in all prompts reads context.md (line 3) | brainstorm |
| R9  | /cg-compound proposes context.md additions (new Step 5) | brainstorm |
| R10 | /cg-setup asks workspace question and writes to context.md | brainstorm |
| R11 | Multi-folder workspace info lives in context.md (not in generated copilot-instructions.md) | review |
| R12 | /cg-work detects milestone completion and warns about stale focus | brainstorm |
| R13 | /cg-resume cross-checks Current Focus against completed milestones | brainstorm |
| R14 | compound-gpid's OWN copilot-instructions.md is NOT the template | brainstorm |
| R15 | context.md is NOT gitignored | brainstorm |
| R16 | Tests for template generation, prompt updates, and script changes | brainstorm |

## Implementation Steps

### Phase 1 — Foundation: Template + Generation

#### 1.1 Create Template File
- **Requirements**: R1, R14
- **Files**: create `.github/copilot-instructions.template.md`
- **Details**:
  - ~40-line template with `{{project-name}}`, `{{project-type}}`,
    `{{languages}}`, `{{review-depth}}` placeholders
  - Essential Rules section uses static hardcoded constraints
    (e.g., "Fail loudly, never silently. Commit lockfiles and
    institutional knowledge. Conventional commits required.") —
    NOT extracted from the charter body (fragile)
  - Workspace section uses a static single-folder default; multi-folder
    details live in `compound-gpid.context.md` and are loaded by Step 0
  - Follows the target structure from the brainstorm:
    managed marker, Project Identity block, Essential Rules block,
    Workspace block
  - Separate from compound-gpid's own `copilot-instructions.md`
- **Test Scenarios**:
  - ✅ Template file exists and contains expected placeholders
  - 🛑 No placeholder syntax collisions with markdown
  - ❌ Template file is not the same as copilot-instructions.md
- **Acceptance criteria**: Template renders correctly with sample values

#### 1.2 Add Generation Function to helpers.ps1
- **Requirements**: R2, R5, R6
- **Files**: modify `scripts/helpers.ps1`
- **Details**:
  - New function `New-CopilotInstructions` that:
    1. Reads `.github/copilot-instructions.template.md` from the
       compound-gpid install dir
    2. Reads `compound-gpid.md` frontmatter for `project-name`
       (fallback: `"<project-name>"`)
    3. Reads `compound-gpid.local.md` frontmatter for `language`,
       `project-type`, `review-depth`, `r-syntax`
       (fallback: `"<not configured>"` for each)
    4. Fills template placeholders and returns the string
       (Essential Rules and Workspace sections are static in the
       template — no runtime extraction needed)
    5. Prepends the managed marker
  - Function signature: `New-CopilotInstructions -TemplateDir <path> -ProjectRoot <path>`
  - Must handle: missing charter, missing local config, missing template
    (error, not silent)
- **Test Scenarios**:
  - ✅ All config files present → fully populated output
  - ✅ Charter missing → placeholder values, no error
  - ✅ Local config missing → placeholder values, no error
  - 🛑 Template file missing → throw error (not silent)
  - ❌ Output always starts with managed marker
- **Tests**: Unit tests in a new `tests/helpers.Tests.ps1` (or extend
  existing test structure)
- **Acceptance criteria**: Function returns correct markdown for all
  input combinations

#### 1.3 Update link.ps1 — Generate Instead of Copy
- **Requirements**: R3, R6
- **Files**: modify `scripts/link.ps1`
- **Details**:
  - Replace Step 4 (copy copilot-instructions.md with marker) with:
    1. Call `New-CopilotInstructions -TemplateDir $CompoundGpidDir -ProjectRoot $ProjectRoot`
    2. Write result to `.github/copilot-instructions.md`
  - Preserve existing behavior:
    - If file exists with marker → overwrite with generated content
    - If file exists without marker → skip (user-managed)
    - If file does not exist → create with generated content
  - Remove `$CopilotInstructionsSource` variable (no longer copying)
- **Test Scenarios**:
  - ✅ Fresh project → generates copilot-instructions.md with real values
  - ✅ Existing managed file → regenerates with updated values
  - 🛑 User-managed file (no marker) → skipped
  - ❌ Output starts with managed marker
- **Tests**: Update `tests/link.Tests.ps1` copilot-instructions tests
- **Acceptance criteria**: `cg-link` in a consumer project produces a slim,
  project-specific copilot-instructions.md

#### 1.4 Update update.ps1 — Regenerate Instead of Copy
- **Requirements**: R4, R6
- **Files**: modify `scripts/update.ps1`
- **Details**:
  - In the copilot-instructions.md refresh section (after pull),
    replace copy-with-marker logic with:
    1. Check if file has managed marker (same as today)
    2. If yes, call `New-CopilotInstructions -TemplateDir $CompoundGpidDir -ProjectRoot (Get-Location)`
       and overwrite. **Note**: at this point in the script, after
       `Pop-Location` in the finally block, `Get-Location` returns
       the consumer project root — NOT $CompoundGpidDir.
    3. If no, skip (same as today)
  - The `$CopilotInstructionsMarker` variable stays
  - Remove `$CopilotInstructionsSource` reference
  - Must work when called from `cg-link` (internal call with
    `$env:CG_INTERNAL_CALL = "1"`)
- **Test Scenarios**:
  - ✅ Managed file → regenerated after update
  - 🛑 User-managed file → untouched
  - ❌ Internal call from cg-link → skips refresh (link handles it)
- **Tests**: Update `tests/update.Tests.ps1`
- **Acceptance criteria**: `cg-update` in a consumer project regenerates
  copilot-instructions.md from template

#### 1.5 Create context.md Scaffold in /cg-setup
- **Requirements**: R7
- **Files**: modify `.github/prompts/cg-setup.prompt.md`,
  modify `.github/prompts/setup-templates.md`
- **Details**:
  - Mode A (new project): After charter creation (Step A3.5), create
    `compound-gpid.context.md` with section scaffold (Data Sources,
    Domain Rules, Work in Progress, Workspace Notes)
  - Mode B (returning project): In Step B1.1, check if context.md
    exists; if not, offer to create it
  - Add `compound-gpid.context.md` to File Permissions
  - Add context.md template to `setup-templates.md`
- **Test Scenarios**:
  - ✅ Mode A creates context.md alongside charter
  - ✅ Mode B offers to create if missing
  - 🛑 Mode B does not overwrite existing context.md
- **Tests**: Update `tests/prompt-tools.Tests.ps1` for new file
  references
- **Acceptance criteria**: `/cg-setup` creates the context.md scaffold

#### 1.6 Update Step 0 in All Prompts
- **Requirements**: R8
- **Files**: modify 13 prompt files with standard Step 0
- **Details**:
  - Add line 3 to each prompt's Step 0:
    ```
    3. Read `compound-gpid.context.md` for project-specific context
       and workspace notes. If it does not exist, skip silently.
    ```
  - For `cg-strategy.prompt.md` (variant "Prerequisite Check" Step 0):
    insert context.md read as new step 2.5, between "Read local config"
    (step 2) and "Read roadmap.json" (step 3). Renumber: 3→4, 4→5, 5→6.
  - For all other prompts: renumber existing items 3+ to 4+
  - Each prompt gets its own copy (no factoring out — per project
    convention)
  - **Exclusion**: `cg-devtag.prompt.md` has no Step 0 by design (it
    operates on the compound-gpid tool repo itself, not a user project).
    Do not modify it.
- **Prompts to update** (14 files): cg-brainstorm, cg-compound,
  cg-compound-refresh, cg-diagnose, cg-fix-problems, cg-fix-triage,
  cg-fixbug, cg-ideate, cg-plan, cg-plan-review, cg-resume, cg-review,
  cg-work, cg-strategy
- **Test Scenarios**:
  - ✅ All 14 prompts mention `compound-gpid.context.md` in Step 0
  - ❌ No prompt reads context.md before reading charter
  - ✅ Existing "warn if `compound-gpid.md` does not exist" text
    survives in each updated prompt after renumbering
- **Tests**: Add Pester test in `prompt-tools.Tests.ps1` — every prompt
  with Step 0 must reference `compound-gpid.context.md`. Use a
  **hardcoded list** of 14 prompts (not a directory scan) to avoid
  false positives on `cg-devtag.prompt.md`. Also verify the "warn if
  missing" text is preserved.
- **Acceptance criteria**: All 14 prompts load context.md in Step 0;
  existing Step 0 content is intact

### Phase 2 — Enrichment + Workspace

#### 2.1 Add Context Enrichment to /cg-compound
- **Requirements**: R9
- **Files**: modify `.github/prompts/cg-compound.prompt.md`
- **Details**:
  - Insert new Step 5 ("Context Enrichment") between current Step 4
    (Cross-Reference) and current Step 5 (Confirm)
  - Renumber current Step 5 → Step 6
  - New step:
    1. Re-read compound-gpid.context.md
    2. Assess if the solved problem reveals a domain rule, data source,
       or project fact useful for future tasks
    3. If yes, propose specific text for the appropriate section
    4. If approved, insert into the correct section (not append at end)
    5. If context.md doesn't exist, offer to create it
- **Test Scenarios**:
  - ✅ Step 5 exists and mentions context enrichment
  - ✅ Step ordering: Cross-Reference < Context Enrichment < Confirm
- **Tests**: Update `prompt-tools.Tests.ps1`
- **Acceptance criteria**: `/cg-compound` offers context.md additions

#### 2.2 Add Workspace Question to /cg-setup
- **Requirements**: R10
- **Files**: modify `.github/prompts/cg-setup.prompt.md`
- **Details**:
  - Mode A and Mode B: Add optional question about other workspace
    folders
  - Store answers in `## Workspace Notes` section of
    `compound-gpid.context.md` only (NOT in the generated
    copilot-instructions.md — that file has a static single-folder
    default and points readers to context.md for multi-folder details)
  - No changes to the template or `New-CopilotInstructions` needed
- **Test Scenarios**:
  - ✅ Setup asks about workspace folders
  - ✅ Workspace notes written to context.md
  - 🛑 Existing context.md content is preserved when adding workspace notes
- **Tests**: Prompt structure tests in prompt-tools.Tests.ps1
- **Acceptance criteria**: Workspace info stored in context.md

### Phase 3 — Staleness Detection

#### 3.1 Milestone Completion Check in /cg-work
- **Requirements**: R12
- **Files**: modify `.github/prompts/cg-work.prompt.md`
- **Details**:
  - After Step 3.7 (marking feature done), add Step 3.8:
    1. Re-read roadmap.json
    2. Check: is this the last non-done feature in the milestone?
    3. If yes, dispatch `@cg-roadmap` to mark milestone `done`
    4. Warn user that Current Focus may be stale
    5. Offer to suggest new Current Focus text or defer to
       `/cg-strategy`
- **Test Scenarios**:
  - ✅ Step 3.8 exists and mentions milestone completion
  - ✅ Step ordering: 3.7 (feature done) < 3.8 (milestone check)
  - 🛑 Does not modify charter without user approval
- **Tests**: Update `prompt-tools.Tests.ps1`
- **Acceptance criteria**: Completing the last feature triggers a
  staleness warning

#### 3.2 Current Focus Staleness in /cg-resume
- **Requirements**: R13
- **Files**: modify `.github/prompts/cg-resume.prompt.md`
- **Details**:
  - Add as **Step 2f.5** (after the existing charter `last-reviewed`
    staleness check in Step 2f). This reuses the roadmap data already
    loaded in Step 2d and fits the collect-then-present pattern.
  - Cross-check Current Focus text against milestone statuses: if
    Current Focus mentions a milestone name that is status `done`,
    flag it: "Current Focus references '<milestone>' which is already
    done. Consider running `/cg-strategy` to update direction."
  - Do NOT place this in Step 0a (that would read roadmap.json
    redundantly and break the collect-then-present flow).
- **Test Scenarios**:
  - ✅ Prompt mentions roadmap.json cross-check for Current Focus
  - ✅ Check appears after Step 2f (charter staleness), not in Step 0
  - 🛑 Only warns, never auto-modifies charter
- **Tests**: Update `prompt-tools.Tests.ps1`
- **Acceptance criteria**: Stale focus is flagged on resume

### Phase 4 — Testing

#### 4.1 Template Generation Tests
- **Requirements**: R16
- **Files**: create or extend `tests/helpers.Tests.ps1`
- **Details**:
  - Test `New-CopilotInstructions` with all input combinations:
    all present, charter missing, local config missing, both missing
  - Verify managed marker is always present
  - Verify placeholder fallback values
  - Verify template missing → throws
- **Acceptance criteria**: All generation paths covered

#### 4.2 Prompt Structure Tests
- **Requirements**: R16
- **Files**: update `tests/prompt-tools.Tests.ps1`
- **Details**:
  - Every prompt with Step 0 references `compound-gpid.context.md`
    (use hardcoded list of 14 prompts; exclude `cg-devtag`)
  - Existing Step 0 items (e.g., "warn if missing") survive renumbering
  - `cg-compound` has Step 5 (Context Enrichment) before final confirm
  - `cg-work` has Step 3.8 (milestone completion check)
  - `cg-resume` has Current Focus staleness check at Step 2f.5
  - Template file exists and contains expected placeholders
- **Acceptance criteria**: Pester tests pass for all structural checks

#### 4.3 Script Integration Tests
- **Requirements**: R16
- **Files**: update `tests/link.Tests.ps1`, `tests/update.Tests.ps1`
- **Details**:
  - link.ps1 generates (not copies) copilot-instructions.md
  - update.ps1 regenerates (not copies) on managed files
  - Backward compat: user-managed files still skipped
  - `.gitignore` does NOT contain `compound-gpid.context.md` after
    `cg-link` runs (R15 verification)
- **Acceptance criteria**: Existing link/update tests updated and passing

## Testing Strategy

- **Unit tests**: `New-CopilotInstructions` function tested in isolation
  with mock config files (all combinations of present/missing)
- **Structural tests**: Pester regex tests on prompt files for Step 0
  context.md references, new step presence, and step ordering
- **Integration tests**: link.ps1 and update.ps1 end-to-end tests in
  `$TestDrive` with generated copilot-instructions.md validation
- **Backward compatibility**: Verify user-managed (no marker) files are
  never overwritten; verify old managed files are seamlessly upgraded

## Documentation Checklist

- [ ] Update `docs/manual.md` — document context.md and slim
  copilot-instructions.md
- [ ] Update `docs/installation.md` — mention context.md creation
- [x] Inline comments in `New-CopilotInstructions` function
- [x] Template file has header comment explaining its purpose

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Template placeholder syntax conflicts with markdown | Generated file has raw `{{...}}` artifacts | Use distinctive prefix like `{{cg:project-name}}` or validate output in tests |
| Breaking existing consumer projects on upgrade | cg-link/cg-update overwrites with slim version, losing user customizations | Managed marker check already prevents this; only marker-present files are touched |
| Step 0 update across 14 prompts — risk of inconsistency | Some prompts miss the new line | Pester test enforces all prompts reference context.md |
| Multi-folder workspace info in context.md becomes stale | Copilot acts on outdated folder references | context.md is user-editable; user removes stale entries. Step 0 loads latest version each session |

## Out of Scope

- Automatic context.md population via codebase scanning (future: Mode B scanner)
- AI-authored sections in context.md (single ownership model — user approves all additions)
- Dynamic constraint extraction from charter body into copilot-instructions.md
  (Essential Rules uses static hardcoded text; extraction is fragile)
- Multi-folder workspace data in copilot-instructions.md (workspace details
  live in context.md only; copilot-instructions.md has a static single-folder
  default that points to context.md)
- Per-folder copilot-instructions.md in multi-root workspaces (VS Code loads
  from each workspace folder's `.github/` automatically)
- Changes to compound-gpid's OWN copilot-instructions.md content (separate task)
