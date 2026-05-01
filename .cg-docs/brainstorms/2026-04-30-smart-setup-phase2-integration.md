---
date: 2026-04-30
title: "Smart /cg-setup Phase 2 — Scanner Integration & Quality Gate"
status: decided
scope: "Standard"
chosen-approach: "Bottom-Up (Templates → Gate → Mode A Rewrite → Health Check)"
tags: [onboarding, setup, scanner, charter, quality-gate, health-check, phase2]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Smart /cg-setup Phase 2 — Scanner Integration & Quality Gate

## Context

Phase 1 shipped in v0.7.4: `@cg-project-scanner` is fully built and tested with
a signal catalog skill (`cg-skill-project-scanner`). Phase 2 wires the scanner
into the user-facing `/cg-setup` flow to eliminate redundant questions for
existing projects.

This brainstorm covers 6 features (all in the `onboarding-setup` milestone):
- `smart-setup-existing-projects` — rewrite Mode A to dispatch scanner, draft charter
- `skip-irrelevant-setup-questions` — confidence-based skip/pre-fill/ask
- `charter-quality-gate` — validate charter before writing (both modes)
- `first-run-welcome-health-check` — pre-flight check at start of Mode A
- `vanilla-copilot-migration` (partial) — offer to merge existing `copilot-instructions.md`
- `roadmap-bootstrap-from-charter` — seed initial milestone from Current Focus

Reference: `2026-04-29-smart-setup-project-scanner.md` (Phase 1 architecture decisions).

## Requirements

### Prompt File Strategy
- Keep `cg-setup.prompt.md` as orchestration logic only
- Offload all new content to `setup-templates.md` (new sections):
  - Charter-from-scanner template
  - Quality gate rules (blockers + warnings)
  - Hybrid approve/walkthrough UX text
  - Health-check content/messages

### Mode A Rewrite — Smart Setup Flow
1. **A0.5 Pre-flight health check** (silent on success, blocks on failure):
   - `.github/prompts/` has `*.prompt.md` files → pass silently
   - `.github/skills/` directory exists → pass silently
   - On failure: block with actionable guidance ("junction may be broken, re-run `cg-link`")
2. **A1 Dispatch scanner**: invoke `@cg-project-scanner` → get structured report
3. **A2 Confidence-based question handling**:
   - High confidence → skip (set value silently)
   - Medium confidence → pre-fill and confirm
   - Low confidence → ask normally, mention detected signal
   - Review depth → always ask (not detectable)
4. **A3 Render charter draft**: use scanner's Charter Draft Content to generate
   complete `compound-gpid.md` draft
5. **A3.5 Hybrid approve flow**:
   - Display full draft in fenced code block
   - Ask: "Approve as-is, or walk through section by section?"
   - Approve: write immediately
   - Walk through: show each section, ask "approve or edit?", accept freeform edits
6. **A4 Quality gate**: validate before writing (see rules below)
7. **A5 Scaffold + gitignore** (existing logic, preserved)
8. **A5.5 Roadmap bootstrap**: create `roadmap.json` with initial milestone seeded
   from Current Focus section (not empty skeleton)
9. **A6 Vanilla-copilot merge**: if scanner detected `.github/copilot-instructions.md`
   without `.github/prompts/`, offer to pull preferences into `compound-gpid.context.md`

### Mode B Addition — Quality Gate
- After B1.1 (read charter), run quality gate against existing `compound-gpid.md`
- If blockers found: offer to fix inline (re-pose the question for missing fields)
- If warnings found: note them in context summary

### Quality Gate Rules

| Rule | Priority | Behavior |
|------|----------|----------|
| `project-name` missing in frontmatter | P0 (block) | Must have value before writing |
| `<!-- TODO -->` placeholders present | P1 (block) | All must be resolved |
| `## Objective` section empty | P1 (block) | Must have content |
| `last-reviewed` blank | P2 (warn) | Note, don't block |
| Empty optional sections (Constraints, Key Deliverables, Current Focus) | P3 (warn) | Note, don't block |

### Section Walkthrough Mechanics (Hybrid Flow Path B)
- Show-and-edit approach: display each section from draft, ask "approve or edit?"
- Accept freeform text edits inline
- Do NOT re-ask abstract questions — respect the scanner's work

### `cg-link` Output Enhancement
- Add 2-line summary to terminal output after successful link:
  ```
  ✓ Linked compound-gpid to <project>
    Run /cg-setup in Copilot Chat to configure.
  ```

### Mode B Non-Regression
- Mode B detection unchanged: `compound-gpid.local.md` exists → Mode B
- Mode B flow preserved: B1–B4.7 unchanged except quality gate insertion after B1.1
- Mode B does NOT dispatch the scanner (scanner is for new/unknown projects)

## Approaches Considered

### Approach 1: Bottom-Up (Templates → Gate → Mode A Rewrite → Health Check) — CHOSEN

Build all content/logic pieces first, then wire into the prompt as one rewrite pass.

1. Add new sections to `setup-templates.md`
2. Write quality gate rules as self-contained section
3. Rewrite Mode A: scanner-dispatch flow
4. Add quality gate check to Mode B (after B1.1)
5. Add vanilla-copilot merge offer
6. Update tests

**Pros**: Templates testable before prompt rewrite. Mode B gate added last,
minimizing regression surface.
**Cons**: Prompt rewrite is one big edit.

### Approach 2: Mode-A-First (Incremental)
Rewrite Mode A in stages with fallback to current questions at each step.
**Not chosen**: Intermediate states add complexity without value since this ships as one unit.

### Approach 3: Parallel Tracks
Split prompt work from template/gate work.
**Not chosen**: Single-agent implementation — parallelism is artificial.

## Decision

Approach 1 — **Bottom-Up**. Build the pieces (templates, gate rules), then wire
them into the prompt. One coherent rewrite pass for Mode A, minimal Mode B touch.

## Next Steps

1. `/cg-plan` — Create implementation plan with steps:
   - Add new sections to `setup-templates.md` (charter-from-scanner template, quality gate, hybrid-flow text, health-check text)
   - Enhance `cg-link` output message
   - Rewrite Mode A (A0.5 through A6) in `cg-setup.prompt.md`
   - Add quality gate to Mode B (after B1.1)
   - Add vanilla-copilot merge offer to Mode A
   - Add roadmap bootstrap logic
   - Write/update tests
