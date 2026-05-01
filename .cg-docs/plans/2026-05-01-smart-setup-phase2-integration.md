---
date: 2026-05-01
title: "Smart /cg-setup Phase 2 — Scanner Integration, Quality Gate & Health Check"
status: superseded
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-04-30-smart-setup-phase2-integration.md"
language: "PowerShell"
estimated-effort: "large"
tags: [onboarding, setup, scanner, charter, quality-gate, health-check, phase2]
---

# Plan: Smart /cg-setup Phase 2 — Scanner Integration, Quality Gate & Health Check

## Objective

Wire the `@cg-project-scanner` agent (shipped in Phase 1) into the user-facing
`/cg-setup` flow. Rewrite Mode A to scan first, draft a charter from results,
use confidence levels to skip/confirm/ask questions, validate with a quality gate,
bootstrap the roadmap from Current Focus, offer vanilla-copilot migration, and
add a pre-flight health check. Mode B gains a quality gate check for existing
charters. `cg-link` gets an improved success message.

## Context

- Phase 1 shipped: `@cg-project-scanner` and `cg-skill-project-scanner` are
  fully built and tested. The agent returns a structured markdown report with
  sections: Scan Summary, Language Detection, Project Type, Framework & Tooling,
  Charter Draft Content, Setup Recommendations.
- Current `/cg-setup` Mode A asks 7 generic questions regardless of project state.
- `setup-templates.md` is the existing content store — loaded on-demand by the prompt.
- Mode B (returning projects) must not regress.
- The prompt is assigned to Haiku 4.5 — keep orchestration lean.

## Requirements

| ID  | Requirement | Source |
|-----|-------------|--------|
| R1  | Mode A dispatches `@cg-project-scanner` and uses its structured output | brainstorm |
| R2  | High-confidence scanner results skip the question silently | brainstorm |
| R3  | Medium-confidence results pre-fill and confirm | brainstorm |
| R4  | Low-confidence results ask normally, mention detected signal | brainstorm |
| R5  | Full charter draft displayed in fenced code block for approve/walkthrough | brainstorm |
| R6  | Walkthrough = show-and-edit per section (not re-asking questions) | brainstorm |
| R7  | Quality gate blocks on: missing `project-name`, `<!-- TODO -->`, empty Objective | brainstorm |
| R8  | Quality gate warns on: blank `last-reviewed`, empty optional sections | brainstorm |
| R9  | Quality gate runs in both Mode A (pre-write) and Mode B (post-read) | brainstorm |
| R10 | Pre-flight health check (A0.5): silent on success, blocks on failure | brainstorm |
| R11 | Roadmap bootstrap: seed initial milestone from Current Focus (not empty skeleton) | brainstorm |
| R12 | Vanilla-copilot merge: offer to pull preferences from existing `copilot-instructions.md` | brainstorm |
| R13 | `cg-link` success message enhanced with `/cg-setup` guidance | brainstorm |
| R14 | Mode B unchanged except quality gate insertion after B1.1 | brainstorm |
| R15 | All new template content in `setup-templates.md`, not inline in prompt | brainstorm |

## Implementation Steps

### 1. Add Quality Gate Section to `setup-templates.md`

- **Requirements**: R7, R8, R15
- **Files**: `.github/prompts/setup-templates.md`
- **Details**:
  Add a new `## Charter Quality Gate` section defining:
  - **Blockers (P0/P1 — halt and require fix)**:
    - `project-name` missing or empty in frontmatter
    - `<!-- TODO` placeholder(s) remaining anywhere in the charter body
    - `## Objective` section is empty (no non-whitespace content after the heading before the next `##`)
  - **Warnings (P2/P3 — note but proceed)**:
    - `last-reviewed` field blank or missing
    - Empty optional sections: Constraints, Key Deliverables, Current Focus
  - **Remediation instructions**: for each blocker, what question to ask the user.
  - **Mode A behavior**: validate draft before writing; if blockers found, loop back to walkthrough for the failing section.
  - **Mode B behavior**: after reading charter, report blockers → offer inline fix; report warnings → include in context summary.
- **Test Scenarios**:
  - ✅ Gate passes: charter with all fields populated
  - 🛑 Gate blocks: charter with `<!-- TODO -->` in Objective
  - 🛑 Gate blocks: charter missing `project-name` in frontmatter
  - ❌ Gate blocks: empty Objective (heading present, no content)
  - ✅ Gate warns only: `last-reviewed` blank, otherwise valid
- **Tests**: Pester test in `prompt-tools.Tests.ps1` asserting:
  - `setup-templates.md` contains `## Charter Quality Gate` section
  - Section mentions `project-name`, `<!-- TODO`, `## Objective` as blockers
  - Section mentions `last-reviewed` as warning
- **Acceptance criteria**: Section is well-formed, references the P0–P3 priority system, and can be loaded by the prompt at runtime.

### 2. Add Scanner-Based Charter Template to `setup-templates.md`

- **Requirements**: R1, R5, R6, R15
- **Files**: `.github/prompts/setup-templates.md`
- **Details**:
  Add a new `## Charter from Scanner Results` section containing:
  - Template showing how to map scanner output fields to charter sections:
    - `Charter Draft Content > Project Name` → frontmatter `project-name`
    - `Charter Draft Content > Objective` → `## Objective`
    - `Charter Draft Content > Key Deliverables` → `## Key Deliverables`
    - `Charter Draft Content > Constraints` → `## Constraints`
    - `Setup Recommendations > Language` → `compound-gpid.local.md` language field
    - `Setup Recommendations > Project type` → `compound-gpid.local.md` project-type field
  - Instructions for rendering the draft in a fenced code block
  - Hybrid approve flow UX text:
    ```
    Here's your project charter draft based on what I found:
    
    <fenced charter>
    
    **Options:**
    1. **Approve as-is** — Write this charter and continue setup
    2. **Walk through section by section** — Review and edit each section
    3. **Start from scratch** — Ignore scanner results, ask questions manually
    ```
  - Section walkthrough mechanics:
    - For each section (Objective, Key Deliverables, Constraints, Current Focus):
      show the inferred content, ask "Approve or edit?", accept freeform replacement.
- **Test Scenarios**:
  - ✅ Template references all scanner output sections
  - ✅ Hybrid flow offers 3 options (approve / walkthrough / scratch)
  - 🛑 "Start from scratch" falls back to current Mode A question flow
- **Tests**: Pester test asserting:
  - `setup-templates.md` contains `## Charter from Scanner Results`
  - Section mentions `@cg-project-scanner`
  - Section contains the three options (approve / walk through / scratch)
- **Acceptance criteria**: Template is complete enough that the prompt can render a charter from any valid scanner report without improvising structure.

### 3. Add Health Check and Roadmap Bootstrap Sections to `setup-templates.md`

- **Requirements**: R10, R11, R13, R15
- **Files**: `.github/prompts/setup-templates.md`
- **Details**:
  **A) Pre-flight Health Check section** (`## Pre-flight Health Check`):
  - Checks to perform (all silent on success):
    - `.github/prompts/` directory exists and contains `*.prompt.md` files
    - `.github/skills/` directory exists
  - Failure messages:
    - Prompts missing: "Prompts not visible — the junction may be broken or VS Code needs a restart. Re-run `cg-link` from the project root."
    - Skills missing: "Skills directory missing — `cg-link` may have partially failed. Re-run `cg-link`."
  - Behavior: any failure → stop setup, show error. All pass → proceed silently.
  
  **B) Roadmap Bootstrap section** (`## Roadmap Bootstrap from Charter`):
  - After charter is written with a non-empty Current Focus:
    - Create `roadmap.json` with schema + one milestone seeded from Current Focus
    - Milestone: `id` = slugified Current Focus title, `title` = Current Focus text (first sentence), `objective` = full Current Focus content, `status` = "in-progress"
    - Include one feature entry: `id` = "initial-focus", `title` = first sentence of Current Focus, `status` = "in-progress"
  - If Current Focus is empty/placeholder: fall back to empty skeleton (existing behavior)
  
  **C) Vanilla-Copilot Migration section** (`## Vanilla Copilot Migration Offer`):
  - Trigger: scanner report contains `.github/copilot-instructions.md` as Tier 2 signal (vanilla Copilot user detected)
  - Behavior: read the file, present key lines to user, ask:
    ```
    I found an existing copilot-instructions.md with custom preferences.
    Would you like to incorporate these into your project context?
    1. Yes — merge relevant preferences into compound-gpid.context.md
    2. No — start fresh (the file will be overwritten by Compound GPID)
    ```
  - If yes: append extracted preferences to `## Domain Rules` in `compound-gpid.context.md`
  - Path safety: only offer when `.github/prompts/` is NOT present (true vanilla user). If both exist, it's already a CG project — skip.
- **Test Scenarios**:
  - ✅ Health check passes when both directories exist
  - ❌ Health check fails when prompts directory missing
  - ✅ Roadmap bootstrap creates milestone from Current Focus
  - ✅ Roadmap falls back to empty skeleton when Current Focus is placeholder
  - ✅ Vanilla migration offered when copilot-instructions.md exists without prompts/
  - 🛑 Vanilla migration NOT offered when prompts/ already exists
- **Tests**: Pester tests asserting:
  - `setup-templates.md` contains `## Pre-flight Health Check`
  - `setup-templates.md` contains `## Roadmap Bootstrap from Charter`
  - `setup-templates.md` contains `## Vanilla Copilot Migration Offer`
  - Health check section mentions `.github/prompts/` and `.github/skills/`
  - Bootstrap section mentions `roadmap.json` and `Current Focus`
- **Acceptance criteria**: All three template sections are self-contained and reference-able from the prompt file.

### 4. Rewrite Mode A in `cg-setup.prompt.md`

- **Requirements**: R1, R2, R3, R4, R5, R6, R10, R11, R12, R14
- **Files**: `.github/prompts/cg-setup.prompt.md`
- **Details**:
  Replace current Mode A (Steps A1–A6) with:

  **A0.5. Pre-flight health check**
  - Reference `## Pre-flight Health Check` from `setup-templates.md`
  - Run checks. If any fail → stop with error message. If all pass → proceed silently.

  **A1. Dispatch scanner**
  - Dispatch `@cg-project-scanner` (no arguments — scan workspace root with all tiers)
  - Receive structured report

  **A2. Confidence-based configuration**
  - For Language: use scanner's `Setup Recommendations` → if `skip`, set silently and tell user ("Detected: Python (pyproject.toml found)"); if `confirm`, pre-fill and ask; if `ask`, show full question menu
  - For Project Type: same logic
  - For Review Depth: always ask (scanner cannot detect this)
  - Write `compound-gpid.local.md` from confirmed values

  **A3. Render charter draft**
  - Use `## Charter from Scanner Results` template from `setup-templates.md`
  - Map scanner's Charter Draft Content into the charter template
  - For sections with `"not detected"`: leave the `<!-- TODO -->` placeholder

  **A3.5. Hybrid approve flow**
  - Display draft in fenced code block
  - Present three options: approve / walk through / start from scratch
  - If "approve": proceed to A4
  - If "walk through": iterate sections with show-and-edit
  - If "start from scratch": fall back to Questions 4–7 from original Mode A (preserved as fallback)

  **A4. Quality gate**
  - Reference `## Charter Quality Gate` from `setup-templates.md`
  - Validate the final charter content (post-approve/walkthrough)
  - If blockers: loop back to the failing section for the user to fix
  - If only warnings: note them and proceed

  **A4.5. Write charter**
  - Write `compound-gpid.md` (same file permissions as current Mode A)
  - Write `compound-gpid.context.md` if not present (existing A3.6 logic)

  **A5. Vanilla-copilot migration** (conditional)
  - Reference `## Vanilla Copilot Migration Offer` from `setup-templates.md`
  - Only if scanner detected vanilla copilot file
  - Offer merge or skip

  **A5.5. Scaffold `.cg-docs/`** (existing logic, preserved)
  
  **A5.6. Update `.gitignore`** (existing logic, preserved)

  **A5.7. Roadmap bootstrap**
  - Reference `## Roadmap Bootstrap from Charter` from `setup-templates.md`
  - If Current Focus is substantive: seed milestone
  - If empty/placeholder: create empty skeleton

  **A6. Print Setup Complete** (existing message from template)

  **Fallback**: If scanner dispatch fails (agent returns error or empty report),
  fall back gracefully to the existing question flow (original A2–A6) with a note:
  "Scanner could not analyze this project. Proceeding with manual questions."

- **Test Scenarios**:
  - ✅ Scanner success path: dispatch → draft → approve → write
  - ✅ Scanner partial results: some fields detected, others `not detected`
  - ✅ Hybrid approve: user selects "approve as-is"
  - ✅ Hybrid walkthrough: user edits one section
  - ✅ Hybrid scratch: falls back to original questions
  - 🛑 Scanner failure: graceful fallback to manual questions
  - ✅ Quality gate passes on valid charter
  - ❌ Quality gate blocks on TODO placeholder
  - ✅ Roadmap seeded from Current Focus
- **Tests**: Pester tests asserting:
  - `cg-setup.prompt.md` mentions `@cg-project-scanner` dispatch
  - Mode A references `## Charter Quality Gate`
  - Mode A references `## Pre-flight Health Check`
  - Mode A references `## Roadmap Bootstrap from Charter`
  - Mode A contains fallback to manual questions
  - Mode A contains hybrid approve options text
  - Existing Mode B steps (B1–B4.7) remain intact
- **Acceptance criteria**: Mode A flows through scanner → confidence → draft → approve → gate → write without improvisation. Mode B is unchanged except Step 5.

### 5. Add Quality Gate to Mode B in `cg-setup.prompt.md`

- **Requirements**: R9, R14
- **Files**: `.github/prompts/cg-setup.prompt.md`
- **Details**:
  Insert a new step **B1.1.1** (after B1.1 "Read project charter"):
  
  **B1.1.1. Charter quality check**
  - Reference `## Charter Quality Gate` from `setup-templates.md`
  - If `compound-gpid.md` exists:
    - Run the quality gate against the loaded content
    - **Blockers found**: after the context summary (B3), present:
      > "Your charter has issues that should be fixed:
      > - [list blockers]
      > Would you like to fix them now?"
      If yes: ask the relevant questions (e.g., "What is this project's objective?") and update the charter.
    - **Warnings found**: include in context summary as a note:
      > "Charter note: <list warnings> (these are advisory, not blocking)."
    - **All clear**: proceed silently.
  - If `compound-gpid.md` does not exist: skip (existing B1.1 behavior handles this).
  
  The step is purely additive — all existing B1.x and B2+ steps remain untouched.

- **Test Scenarios**:
  - ✅ Mode B with valid charter: no quality gate output
  - ✅ Mode B with TODO placeholder: offers to fix
  - ✅ Mode B with blank `last-reviewed`: notes in summary, doesn't block
  - 🛑 Mode B without charter: quality gate step skipped entirely
- **Tests**: Pester tests asserting:
  - Mode B section contains `B1.1.1` or quality gate reference
  - Mode B references `## Charter Quality Gate`
- **Acceptance criteria**: Mode B gains quality checking without changing any existing step behavior.

### 6. Enhance `cg-link` Success Message

- **Requirements**: R13
- **Files**: `scripts/link.ps1`
- **Details**:
  Replace the current success output block (lines ~254–271) with:
  ```powershell
  Write-Host ""
  Write-Host ([char]0x2713 + " Linked compound-gpid to this project.") -ForegroundColor Green
  Write-Host "  Run /cg-setup in Copilot Chat to configure." -ForegroundColor DarkGray
  Write-Host ""
  Write-Host "IMPORTANT:" -ForegroundColor Yellow
  Write-Host "  Restart VS Code / Positron now." -ForegroundColor Yellow
  Write-Host "  Copilot must re-index the workspace to see the linked prompts." -ForegroundColor Yellow
  Write-Host ""
  ```
  This replaces the verbose existing message with a concise 2-line confirmation
  followed by the critical restart notice. The managed-directory warning is
  redundant with `.gitignore` enforcement — remove it.

- **Test Scenarios**:
  - ✅ Success message contains checkmark and `/cg-setup` reference
  - ✅ Restart reminder preserved
  - 🛑 No managed-directory warning (removed as redundant)
- **Tests**: Existing `link.Tests.ps1` patterns. Add assertion that script
  contains the `/cg-setup` guidance string.
- **Acceptance criteria**: `cg-link` terminal output is shorter and directs user to next step.

### 7. Update Tests

- **Requirements**: All (verification)
- **Files**: `tests/prompt-tools.Tests.ps1`, `tests/link.Tests.ps1`
- **Details**:
  Add Pester test blocks:

  **In `prompt-tools.Tests.ps1`**:
  - `Describe "setup-templates.md - quality gate section"` — asserts section exists, mentions all blocker/warning rules
  - `Describe "setup-templates.md - scanner charter template"` — asserts section exists, mentions scanner output fields
  - `Describe "setup-templates.md - health check section"` — asserts section exists
  - `Describe "setup-templates.md - roadmap bootstrap section"` — asserts section exists
  - `Describe "setup-templates.md - vanilla copilot migration"` — asserts section exists
  - `Describe "cg-setup.prompt.md - scanner integration"` — asserts Mode A dispatches scanner, has fallback, has hybrid approve, references quality gate
  - `Describe "cg-setup.prompt.md - Mode B quality gate"` — asserts Mode B references quality gate

  **In `link.Tests.ps1`**:
  - `Describe "link.ps1 - success message"` — asserts script contains `/cg-setup` string

- **Test Scenarios**:
  - ✅ All new template sections are findable by test assertions
  - ✅ Prompt file structural assertions pass
  - 🛑 Existing tests continue to pass (no regressions)
- **Tests**: Self-referential (this step IS the tests)
- **Acceptance criteria**: Full test suite passes with no regressions. New assertions cover all structural requirements.

## Testing Strategy

- **Structural tests** (Pester): Verify prompt/template files contain expected sections, keywords, and cross-references. This is the primary testing approach for prompt files — we can't execute the prompts in CI, but we can assert their structure is correct.
- **Regression tests**: Existing Mode B tests must continue to pass unchanged.
- **Manual verification**: After implementation, run `/cg-setup` against a real project (or the compound-gpid repo itself) to verify the scanner-to-charter pipeline works end-to-end.
- **Link script test**: Verify the new success message renders correctly.

## Documentation Checklist

- [ ] `setup-templates.md` — all new sections are self-documenting (they ARE documentation)
- [ ] `cg-setup.prompt.md` — inline comments explaining scanner dispatch and fallback logic
- [ ] `docs/reference.md` — update `/cg-setup` description if the UX materially changed
- [ ] `ROADMAP.md` — regenerate after roadmap feature statuses update

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Mode A rewrite breaks Mode B | Users on existing projects can't re-configure | Mode B touched minimally (one new step). Test existing B steps structurally. |
| Scanner dispatch fails silently | User gets empty charter | Explicit fallback: if scanner returns error/empty, switch to manual questions. |
| Prompt grows too large for Haiku 4.5 context | Model truncates or hallucinates | All content in `setup-templates.md` (loaded on-demand). Prompt stays orchestration-only. |
| Quality gate too strict for bootstrapping | New users can't save partial charters | Gate runs post-approve: users explicitly chose to save. Blockers are truly critical (no name = broken downstream). |
| Roadmap bootstrap creates bad milestone | Irrelevant milestone pollutes roadmap | Only seeds if Current Focus is substantive (not a placeholder). User can edit via `@cg-roadmap`. |

## Out of Scope

- **`cg-setup-refresh-mode`** (roadmap item): non-destructive re-configuration is a separate feature
- **`onboarding-tour-prompt`** (roadmap item): guided workflow walkthrough is post-setup
- **Scanner skill/agent changes**: Phase 1 is frozen; no modifications to the scanner itself
- **Mode B scanner dispatch**: Mode B is for returning projects — scanner is for new/unknown projects only
- **CI/automation for prompt testing**: structural Pester tests are sufficient; no LLM-in-the-loop testing
- **Full vanilla-copilot-migration**: we offer to merge preferences; we don't build a comprehensive instruction parser
