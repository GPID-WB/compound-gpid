---
date: 2026-05-01
title: "Smart /cg-setup Phase 2 — Scanner Integration, Quality Gate & Health Check (revised)"
status: completed
completed-date: 2026-05-01
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-04-30-smart-setup-phase2-integration.md"
language: "PowerShell"
estimated-effort: "large"
tags: [onboarding, setup, scanner, charter, quality-gate, health-check, phase2, revised]
---

# Plan: Smart /cg-setup Phase 2 — Scanner Integration, Quality Gate & Health Check (revised)

## Objective

Wire the `@cg-project-scanner` agent (shipped in Phase 1) into the user-facing
`/cg-setup` flow. Rewrite Mode A to scan first, draft a charter from results,
use confidence levels to skip/confirm/ask questions, validate with a quality gate,
bootstrap the roadmap from Current Focus, and add a pre-flight health check.
Mode B gains a quality gate check for existing charters. `cg-link` gets a
`/cg-setup` call-to-action appended to its success message.

> **Revision note**: This plan supersedes `2026-05-01-smart-setup-phase2-integration.md`
> (now status: superseded). Addresses 10 findings from `/cg-plan-review`:
> P1.1 (vanilla migration removed from scope), P1.2 (fallback questions anchored),
> P1.3 (overwrite guard preserved), P2.1 (.Rbuildignore preserved), P2.2 (warning
> kept), P2.3 (deferred-output specified), P2.4 (fallback clarified), P3.1 (all 4
> dirs checked), P3.2 (confidence test added), P3.3 (specific assertion text).

## Context

- Phase 1 shipped: `@cg-project-scanner` and `cg-skill-project-scanner` are
  fully built and tested. The agent returns a structured markdown report with
  sections: Scan Summary, Language Detection, Project Type, Framework & Tooling,
  Charter Draft Content, Setup Recommendations.
- Current `/cg-setup` Mode A asks 7 generic questions regardless of project state.
- `setup-templates.md` is the existing content store — loaded on-demand by the prompt.
- Mode B (returning projects) must not regress.
- The prompt is assigned to Haiku 4.5 — keep orchestration lean.
- Vanilla-copilot migration (R12 from prior plan) is **removed from scope** per
  P1.1: the health check blocks when `.github/prompts/` is absent, and `cg-link`
  already overwrites the file — the detection trigger is structurally unreachable.
  Moved to a future iteration where `cg-link` can flag pre-existing files.

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
| R12 | `cg-link` success message enhanced with `/cg-setup` guidance (additive only) | brainstorm + P2.2 |
| R13 | Mode B unchanged except quality gate insertion after B1.1 | brainstorm |
| R14 | All new template content in `setup-templates.md`, not inline in prompt | brainstorm |
| R15 | Original Q1–Q7 preserved as a named fallback block in Mode A | P1.2 |
| R16 | Charter overwrite guard preserved in Mode A before writing | P1.3 |
| R17 | `.Rbuildignore` update step preserved in Mode A | P2.1 |

## Implementation Steps

### 1. Add Quality Gate Section to `setup-templates.md`

- **Requirements**: R7, R8, R14
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
  - **Remediation instructions**: for each blocker, what question to re-ask the user.
  - **Mode A behavior**: validate draft before writing; if blockers found, loop back
    to the failing section(s) for the user to provide content.
  - **Mode B behavior**: check and store results at B1.1.1 (do not output). At B3,
    append to context summary: blockers as an offer to fix, warnings as a note.
    (Explicit deferred-output instruction per P2.3.)
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
  - Section contains "store results" / "do not output" deferred-output instruction
- **Acceptance criteria**: Section is well-formed, references the P0–P3 priority
  system, includes explicit deferred-output mechanism for Mode B, and can be
  loaded by the prompt at runtime.

### 2. Add Scanner-Based Charter Template to `setup-templates.md`

- **Requirements**: R1, R5, R6, R14
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
  - For any field the scanner reports as `"not detected"`: leave the `<!-- TODO -->`
    placeholder in the draft (the quality gate will catch it).
  - Instructions for rendering the draft in a fenced code block.
  - **Confidence-action mapping table** (per P3.2 — must be present for structural test):
    ```
    | Confidence | Action  | UX behavior |
    |------------|---------|-------------|
    | high       | skip    | Set silently, confirm in summary: "Detected: <value> (<evidence>)" |
    | medium     | confirm | Pre-fill and ask: "I detected <value>. Correct? (yes / change)" |
    | low        | ask     | Show full question menu, mention signal: "I found <signal> — ..." |
    ```
  - Hybrid approve flow UX text:
    ```
    Here's your project charter draft based on what I found:

    <fenced charter>

    **Options:**
    1. **Approve as-is** — Write this charter and continue setup
    2. **Walk through section by section** — Review and edit each section
    3. **Start from scratch** — Ignore scanner results, ask questions manually
       (uses the Fallback: Manual Questions flow)
    ```
  - Section walkthrough mechanics:
    - For each section (Objective, Key Deliverables, Constraints, Current Focus):
      show the inferred content, ask "Approve or edit?", accept freeform replacement.
- **Test Scenarios**:
  - ✅ Template references all scanner output sections
  - ✅ Hybrid flow offers 3 options (approve / walkthrough / scratch)
  - ✅ Confidence-action mapping table present with skip/confirm/ask
  - 🛑 "Start from scratch" explicitly references the fallback block
- **Tests**: Pester test asserting:
  - `setup-templates.md` contains `## Charter from Scanner Results`
  - Section mentions `@cg-project-scanner`
  - Section contains the three options (approve / walk through / scratch)
  - Section contains `| high` and `| skip` and `| confirm` and `| ask` (confidence table)
- **Acceptance criteria**: Template is complete enough that the prompt can render a
  charter from any valid scanner report without improvising structure. Confidence
  table is structurally testable.

### 3. Add Health Check and Roadmap Bootstrap Sections to `setup-templates.md`

- **Requirements**: R10, R11, R14
- **Files**: `.github/prompts/setup-templates.md`
- **Details**:
  **A) Pre-flight Health Check section** (`## Pre-flight Health Check`):
  - Checks to perform (all silent on success):
    - `.github/prompts/` directory exists and contains `*.prompt.md` files
    - `.github/skills/` directory exists
    - `.github/agents/` directory exists
    - `.github/instructions/` directory exists
  - (All 4 managed directories checked — per P3.1.)
  - Failure messages:
    - Prompts missing: "Prompts not visible — the junction may be broken or VS Code
      needs a restart. Re-run `cg-link` from the project root."
    - Skills missing: "Skills directory missing — `cg-link` may have partially failed.
      Re-run `cg-link`."
    - Agents missing: "Agents directory missing — `cg-link` may have partially failed.
      Re-run `cg-link`."
    - Instructions missing: "Instructions directory missing — `cg-link` may have
      partially failed. Re-run `cg-link`."
  - Behavior: any failure → stop setup, show the failing check's error. All pass → proceed silently.
  
  **B) Roadmap Bootstrap section** (`## Roadmap Bootstrap from Charter`):
  - Trigger: charter was written at A4.5 with a non-empty, non-placeholder Current Focus.
  - If charter was NOT written (user skipped all charter questions and A4.5 was
    skipped): create empty `roadmap.json` skeleton (existing behavior). (Per P2.4 —
    this is the only trigger for the empty skeleton. The `<!-- TODO -->` case cannot
    reach here because the quality gate eliminates it.)
  - If charter was written with substantive Current Focus:
    - Create `roadmap.json` with schema + one milestone seeded from Current Focus
    - Milestone: `id` = slugified Current Focus title (first 5 words, lowercase,
      hyphens), `title` = Current Focus text (first sentence), `objective` = full
      Current Focus content, `status` = "in-progress"
    - Include one feature entry: `id` = "initial-focus", `title` = first sentence
      of Current Focus, `status` = "in-progress"
- **Test Scenarios**:
  - ✅ Health check passes when all 4 directories exist
  - ❌ Health check fails when prompts directory missing
  - ❌ Health check fails when agents directory missing
  - ✅ Roadmap bootstrap creates milestone from Current Focus
  - ✅ Roadmap creates empty skeleton when charter was skipped
- **Tests**: Pester tests asserting:
  - `setup-templates.md` contains `## Pre-flight Health Check`
  - `setup-templates.md` contains `## Roadmap Bootstrap from Charter`
  - Health check section mentions `.github/prompts/`, `.github/skills/`,
    `.github/agents/`, `.github/instructions/` (all four)
  - Bootstrap section mentions `roadmap.json` and `Current Focus`
  - Bootstrap section mentions "charter was NOT written" (skip case per P2.4)
- **Acceptance criteria**: Both template sections are self-contained and reference-able
  from the prompt file. Health check covers all 4 managed directories.

### 4. Rewrite Mode A in `cg-setup.prompt.md`

- **Requirements**: R1, R2, R3, R4, R5, R6, R10, R11, R13, R15, R16, R17
- **Files**: `.github/prompts/cg-setup.prompt.md`
- **Details**:
  Replace current Mode A (Steps A1–A6) with the following structure. Preserve
  original Questions 1–7 as a named fallback block at the end of Mode A.

  **A0.5. Pre-flight health check**
  - Reference `## Pre-flight Health Check` from `setup-templates.md`
  - Run checks. If any fail → stop with error message. If all pass → proceed silently.

  **A1. Dispatch scanner**
  - Dispatch `@cg-project-scanner` (no arguments — scan workspace root with all tiers)
  - Receive structured report
  - If scanner dispatch fails or returns empty/error: display
    "Scanner could not analyze this project. Proceeding with manual questions."
    → jump to **Fallback: Manual Questions**.

  **A2. Confidence-based configuration**
  - For Language: use scanner's `Setup Recommendations` table →
    if action = `skip`, set silently and inform: "Detected: <language> (<evidence>)";
    if action = `confirm`, pre-fill and ask;
    if action = `ask`, show full question menu (from Fallback Q1)
  - For Project Type: same logic (from Fallback Q2)
  - For Review Depth: always ask using Fallback Q3 (scanner cannot detect this)
  - Write `compound-gpid.local.md` from confirmed values (using existing template)

  **A3. Render charter draft**
  - Use `## Charter from Scanner Results` template from `setup-templates.md`
  - Map scanner's Charter Draft Content into the charter template
  - For sections with `"not detected"`: insert `<!-- TODO -->` placeholder

  **A3.5. Hybrid approve flow**
  - Display draft in fenced code block
  - Present three options: approve / walk through / start from scratch
  - If "approve": proceed to A4
  - If "walk through": iterate sections with show-and-edit
  - If "start from scratch": jump to **Fallback: Manual Questions** Q4–Q7

  **A4. Quality gate**
  - Reference `## Charter Quality Gate` from `setup-templates.md`
  - Validate the final charter content (post-approve/walkthrough)
  - If blockers: loop back to the failing section for the user to fix
  - If only warnings: note them and proceed

  **A4.5. Write charter** (per P1.3 — overwrite guard preserved)
  - **Overwrite guard**: If `compound-gpid.md` already exists, read its `project-name`
    field and ask: "A project charter already exists for **<project-name>**. Do you
    want to overwrite it? (yes / no)". If no: skip charter write, proceed to A5.
  - Write `compound-gpid.md`
  - Write `compound-gpid.context.md` if not present (existing A3.6 logic)
  - Ask about workspace folders (existing A3.7 logic)

  **A5. Scaffold `.cg-docs/`** (existing logic, preserved)

  **A5.5. Update `.gitignore`** (existing logic, preserved)

  **A5.6. Update `.Rbuildignore`** (existing logic, preserved — per P2.1)
  - If user selected Package and language is R/Both/All: check `.Rbuildignore`
    and append `^\.cg-docs$` if not present.

  **A5.7. Roadmap bootstrap**
  - Reference `## Roadmap Bootstrap from Charter` from `setup-templates.md`
  - If charter was written with substantive Current Focus: seed milestone
  - If charter was skipped: create empty skeleton

  **A6. Print Setup Complete** (existing message from template)

  ---

  **Fallback: Manual Questions** (named block — per P1.2)

  > This block preserves the original Q1–Q7 from the pre-scanner Mode A. It is
  > invoked when: (1) the scanner fails/returns empty, (2) the user selects
  > "Start from scratch" in the hybrid approve flow. Questions are numbered for
  > cross-reference from the scanner-based flow.

  - **Q1 — Language** (same menu as current A2 Question 1)
  - **Q2 — Project type** (same menu as current A2 Question 2)
  - **Q3 — Review depth** (same menu as current A2 Question 3)
  - Write `compound-gpid.local.md` from answers
  - **Q4 — Project name** (required for charter creation)
  - **Q4.5 — Team** (optional, default DECDG / GPID — World Bank)
  - **Q5 — Objective** (optional, skip → placeholder)
  - **Q6 — Key deliverables** (optional, skip → placeholder)
  - **Q7 — Constraints** (optional, skip → placeholder)
  - Proceed to A4 (quality gate) after Q7

  Entry points:
  - Full fallback (scanner failure): start at Q1
  - Partial fallback ("start from scratch" after config): start at Q4

- **Test Scenarios**:
  - ✅ Scanner success path: dispatch → draft → approve → write
  - ✅ Scanner partial results: some fields detected, others `not detected`
  - ✅ Hybrid approve: user selects "approve as-is"
  - ✅ Hybrid walkthrough: user edits one section
  - ✅ Hybrid scratch: falls back to Fallback: Manual Questions
  - 🛑 Scanner failure: graceful fallback to Fallback: Manual Questions
  - ✅ Quality gate passes on valid charter
  - ❌ Quality gate blocks on TODO placeholder → loops to section fix
  - ✅ Overwrite guard fires when charter exists
  - ✅ Roadmap seeded from Current Focus
  - ✅ `.Rbuildignore` updated for R package projects
- **Tests**: Pester tests asserting:
  - `cg-setup.prompt.md` mentions `@cg-project-scanner` dispatch
  - Mode A contains `## Fallback: Manual Questions` or `**Fallback: Manual Questions**`
  - Mode A references `## Charter Quality Gate`
  - Mode A references `## Pre-flight Health Check`
  - Mode A references `## Roadmap Bootstrap from Charter`
  - Mode A contains scanner failure fallback text ("Scanner could not analyze")
  - Mode A contains hybrid approve options text ("Approve as-is")
  - Mode A contains overwrite guard ("already exists")
  - Mode A mentions `.Rbuildignore`
  - Existing Mode B steps (B1–B4.7) remain intact (spot-check B1, B3, B4.7 text)
- **Acceptance criteria**: Mode A flows through scanner → confidence → draft →
  approve → gate → write with explicit fallback paths. All existing protections
  (overwrite guard, .Rbuildignore) preserved. Mode B unchanged except Step 5.

### 5. Add Quality Gate to Mode B in `cg-setup.prompt.md`

- **Requirements**: R9, R13
- **Files**: `.github/prompts/cg-setup.prompt.md`
- **Details**:
  Insert a new step **B1.1.1** (after B1.1 "Read project charter"):
  
  **B1.1.1. Charter quality check**
  - Reference `## Charter Quality Gate` from `setup-templates.md`
  - If `compound-gpid.md` exists:
    - Run the quality gate against the loaded content.
    - **Store results internally. Do NOT output anything at this step.** (Per P2.3.)
    - Results are surfaced later at B3 (context summary).
  - If `compound-gpid.md` does not exist: skip (existing B1.1 behavior handles this).
  
  At **B3** (context summary), append quality gate output:
  - **Blockers found**: After the context summary, present:
    > "⚠️ Your charter has issues that should be fixed:
    > - [list blockers]
    > Would you like to fix them now?"
    If yes: ask the relevant questions and update the charter. If no: note and continue.
  - **Warnings found**: Include in context summary as a note:
    > "Charter note: [list warnings] (advisory — not blocking)."
  - **All clear**: Proceed silently (no output).
  
  The step is purely additive — all existing B1.x and B2+ steps remain untouched.

- **Test Scenarios**:
  - ✅ Mode B with valid charter: no quality gate output
  - ✅ Mode B with TODO placeholder: offers to fix after B3
  - ✅ Mode B with blank `last-reviewed`: notes in summary, doesn't block
  - 🛑 Mode B without charter: quality gate step skipped entirely
- **Tests**: Pester tests asserting:
  - Mode B section contains `B1.1.1` or equivalent heading
  - Mode B contains "Store results" or "Do NOT output" (deferred-output instruction)
  - Mode B references `## Charter Quality Gate`
- **Acceptance criteria**: Mode B gains quality checking with explicit deferred-output
  mechanism. No changes to any other Mode B step.

### 6. Enhance `cg-link` Success Message

- **Requirements**: R12
- **Files**: `scripts/link.ps1`
- **Details**:
  **Additive only** (per P2.2 — keep the managed-directory warning). Insert the
  `/cg-setup` call-to-action into the existing success message block. Specifically:

  After the "Linked!" line and before the "IMPORTANT:" managed-directory warning,
  add:
  ```powershell
  Write-Host "  Next step: run /cg-setup in Copilot Chat to configure." -ForegroundColor DarkGray
  ```

  The final output becomes:
  ```
  Linked!

  Compound GPID prompts are now available in this project.
    Next step: run /cg-setup in Copilot Chat to configure.

  IMPORTANT:
    The following directories are managed by Compound GPID.
    Do not edit files inside them — changes will be lost on cg-update.
    Managed: .github/prompts/  .github/skills/  .github/agents/  .github/instructions/

  IMPORTANT: Restart VS Code / Positron now.
    Copilot must re-index the workspace to see the linked prompts and agents.
    Without a restart, /cg-setup and other prompts will not be available.

  Run in VS Code / Positron Copilot Chat:
    /cg-setup
  ```

  Keep all existing content. Only insert the "Next step" line.

- **Test Scenarios**:
  - ✅ Success message contains "Next step: run /cg-setup in Copilot Chat"
  - ✅ Managed-directory warning preserved
  - ✅ Restart reminder preserved
- **Tests**: Pester assertion that `link.ps1` contains the specific string
  `"run /cg-setup in Copilot Chat to configure"` (per P3.3 — specific text, not
  bare `/cg-setup` token which already exists).
- **Acceptance criteria**: `cg-link` terminal output adds one guidance line without
  removing any existing warnings.

### 7. Update Tests

- **Requirements**: All (verification)
- **Files**: `tests/prompt-tools.Tests.ps1`, `tests/link.Tests.ps1`
- **Details**:
  Add Pester test blocks:

  **In `prompt-tools.Tests.ps1`**:
  ```
  Describe "setup-templates.md - quality gate section"
    - contains "## Charter Quality Gate"
    - mentions "project-name" as blocker
    - mentions "<!-- TODO" as blocker
    - mentions "## Objective" empty as blocker
    - mentions "last-reviewed" as warning
    - contains deferred-output instruction ("store results" or "Do NOT output")

  Describe "setup-templates.md - scanner charter template"
    - contains "## Charter from Scanner Results"
    - mentions "@cg-project-scanner" or "scanner"
    - contains hybrid approve options ("Approve as-is", "Walk through", "Start from scratch")
    - contains confidence-action table ("| high" + "| skip" + "| confirm" + "| ask")

  Describe "setup-templates.md - health check section"
    - contains "## Pre-flight Health Check"
    - mentions ".github/prompts/"
    - mentions ".github/skills/"
    - mentions ".github/agents/"
    - mentions ".github/instructions/"

  Describe "setup-templates.md - roadmap bootstrap section"
    - contains "## Roadmap Bootstrap from Charter"
    - mentions "roadmap.json"
    - mentions "Current Focus"
    - mentions "charter was NOT written" or "charter was skipped" (empty skeleton case)

  Describe "cg-setup.prompt.md - scanner integration (Mode A)"
    - mentions "@cg-project-scanner"
    - contains "Fallback: Manual Questions" (named block per P1.2)
    - references "## Charter Quality Gate"
    - references "## Pre-flight Health Check"
    - references "## Roadmap Bootstrap from Charter"
    - contains fallback text ("Scanner could not analyze")
    - contains hybrid approve text ("Approve as-is")
    - contains overwrite guard ("already exists")
    - mentions ".Rbuildignore"

  Describe "cg-setup.prompt.md - Mode B quality gate"
    - references "## Charter Quality Gate" in Mode B section
    - contains "B1.1.1" or "Charter quality check" heading
    - contains deferred-output instruction ("Store results" / "Do NOT output")
    - preserves existing Mode B steps (B1, B3, B4.7 keywords present)
  ```

  **In `link.Tests.ps1`**:
  ```
  Describe "link.ps1 - setup guidance in success message"
    - contains "run /cg-setup in Copilot Chat to configure"
    - still contains "managed by Compound GPID" (warning preserved)
  ```

- **Test Scenarios**:
  - ✅ All new template sections are findable by test assertions
  - ✅ Prompt file structural assertions pass
  - ✅ Confidence-action mapping table is structurally testable (P3.2)
  - ✅ Link test uses specific text (P3.3)
  - 🛑 Existing tests continue to pass (no regressions)
- **Tests**: Self-referential (this step IS the tests)
- **Acceptance criteria**: Full test suite passes with no regressions. New assertions
  cover all structural requirements including the 3 P3 fixes.

## Testing Strategy

- **Structural tests** (Pester): Verify prompt/template files contain expected
  sections, keywords, and cross-references. This is the primary testing approach
  for prompt files — we can't execute the prompts in CI, but we can assert their
  structure is correct.
- **Confidence mapping test** (P3.2): Verify the confidence-action table
  (high→skip, medium→confirm, low→ask) exists in `setup-templates.md`.
- **Regression tests**: Existing Mode B tests and all other existing tests must
  continue to pass unchanged.
- **Manual verification**: After implementation, run `/cg-setup` against a real
  project to verify the scanner-to-charter pipeline works end-to-end.
- **Link script test**: Verify the new guidance line renders and existing warnings
  are preserved.

## Documentation Checklist

- [ ] `setup-templates.md` — all new sections are self-documenting (they ARE documentation)
- [ ] `cg-setup.prompt.md` — inline comments explaining scanner dispatch, fallback paths, and deferred-output mechanism
- [ ] `docs/reference.md` — update `/cg-setup` description if the UX materially changed
- [ ] `ROADMAP.md` — regenerate after roadmap feature statuses update

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Mode A rewrite breaks Mode B | Users on existing projects can't re-configure | Mode B touched minimally (one new step + deferred output at B3). Test existing B steps structurally. |
| Scanner dispatch fails silently | User gets empty charter | Explicit fallback: if scanner returns error/empty, jump to Fallback: Manual Questions with a note. |
| Prompt grows too large for Haiku 4.5 context | Model truncates or hallucinates | All content in `setup-templates.md` (loaded on-demand). Prompt stays orchestration-only. |
| Quality gate too strict for bootstrapping | New users can't save partial charters | Gate runs post-approve: users explicitly chose to save. Blockers are truly critical (no name = broken downstream). |
| Roadmap bootstrap creates bad milestone | Irrelevant milestone pollutes roadmap | Only seeds if charter was written AND Current Focus is substantive. Empty skeleton when charter skipped. |
| Overwrite guard missed on partial Mode A entry | Existing charter silently lost | Overwrite guard explicitly specified at A4.5 with exact condition from current prompt. |

## Out of Scope

- **`vanilla-copilot-migration`** (roadmap item): removed from this plan per P1.1 — detection trigger is structurally unreachable. Redesign needed at the `cg-link` level in a future iteration.
- **`cg-setup-refresh-mode`** (roadmap item): non-destructive re-configuration is a separate feature.
- **`onboarding-tour-prompt`** (roadmap item): guided workflow walkthrough is post-setup.
- **Scanner skill/agent changes**: Phase 1 is frozen; no modifications to the scanner itself.
- **Mode B scanner dispatch**: Mode B is for returning projects — scanner is for new/unknown projects only.
- **CI/automation for prompt testing**: structural Pester tests are sufficient; no LLM-in-the-loop testing.
