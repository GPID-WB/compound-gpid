---
date: 2026-04-20
title: "Prompt prose compression and Step 0 dedup"
status: completed
completed-date: 2026-04-20
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-04-20-reduce-late-sequence-token-cost.md"
language: "both"
estimated-effort: "medium"
tags: [performance, tokens, prompts, optimization, prose-compression]
---

# Plan: Prompt Prose Compression and Step 0 Dedup

## Objective

Reduce token cost across the 5 largest prompt files by compressing verbose
prose and standardizing the repeated Step 0 "Get Bearings" block. All
instructions stay inline — no extraction, no new commands, no behavioral
dependencies. Target: ~20% line reduction per file while preserving
identical functional behavior.

## Context

Analysis (brainstorm 2026-04-20) found ~611 of 3,029 prompt lines (~20%)
are late-sequence content. The CE-style extraction approach was rejected
(model may skip stub instructions 5%+ of the time). Mode splitting was
rejected (VS Code shows every `.prompt.md` as a user-facing command — no
way to hide dispatch-only prompts).

The chosen approach: prose compression + Step 0 dedup, scoped to the top 5
prompts by line count. Estimated savings: ~500–700 lines (~7,500–10,500
tokens). Zero functional risk.

The 5 targets:

| File | Current lines | Step 0 lines |
|------|-------------:|-------------:|
| `cg-work.prompt.md` | 307 | ~12 |
| `cg-setup.prompt.md` | 309 | 0 (no Step 0 — bootstraps context files) |
| `cg-plan.prompt.md` | 237 | ~14 |
| `cg-review.prompt.md` | 226 | ~12 |
| `cg-fix-triage.prompt.md` | 189 | ~12 |
| **Total** | **1,268** | |

## Requirements

| ID  | Requirement                                             | Source      |
|-----|---------------------------------------------------------|-------------|
| R1  | Compress prose: remove tutorial explanations, merge redundant lines, tighten multi-line blocks to single-line where semantics are preserved | brainstorm |
| R2  | Standardize Step 0 "Get Bearings" to a compact form (~8 lines) across all 5 files | brainstorm |
| R3  | Preserve all functional behavior — every instruction, condition, and output template must survive compression | brainstorm |
| R4  | No new files, no new commands, no structural changes | brainstorm |
| R5  | All existing Pester tests must pass after each file edit | brainstorm |
| R6  | Target ~20% line reduction per file (minimum 15%) | brainstorm |

## Compression Principles

Apply these patterns consistently across all 5 files:

### Step 0 Standard Form (~8 lines)
Replace the current ~12-14 line Step 0 with this compact form:

```markdown
### Step 0: Get Bearings

1. Read `compound-gpid.md` (objective, constraints, current focus). If missing: warn "No project charter found. Run `/cg-setup` to create one."
2. Read `compound-gpid.local.md` (language, project type, review depth).
3. If `compound-gpid.context.md` exists, read it for project-specific context.
```

File-specific additions (e.g., cg-plan's "verify alignment" or cg-work's
skill-loading) go as bullet 4+ rather than as separate sub-blocks.

### Prose Compression Patterns

1. **Merge condition + action**: "If X exists, do Y. If it does not exist,
   skip silently." → "If X exists: do Y. Otherwise skip."
2. **Remove why-explanations**: The model needs *what* to do, not *why*.
   Cut sentences like "This ensures..." or "The reason is...".
3. **Collapse numbered sub-steps**: When a numbered list has single-sentence
   items, merge 2–3 onto one line if they're sequential and simple.
4. **Tighten templates**: Markdown output templates with blank lines between
   fields → remove blank lines, keep structure.
5. **Remove redundant qualifiers**: "in the project root" when the context
   is already clear, "in Copilot Chat" when the context is a prompt.
6. **Shorten agent dispatch instructions**: "dispatch `@cg-roadmap` with:
   'Update feature X in milestone Y to status done'" stays — it's a
   concrete instruction. But surrounding paragraphs explaining when/why
   get compressed.
7. **Never compress**: Exact strings the model must output (quoted user
   messages), YAML frontmatter field names, file paths, finding ID
   formats, test command patterns, or any phrase matched by a
   `Should Match`/`Should Be` assertion in `prompt-tools.Tests.ps1`
   (e.g., `skip silently`, `warn the user`).

## Implementation Steps

### Pre-step: Assertion Scan (mandatory for each file)

Before compressing any file, read all `Describe`/`It` blocks in
`prompt-tools.Tests.ps1` that reference that file. List the exact
strings and regex patterns asserted. Treat these as additional
"Never compress" items for that file.

### 1. Compress cg-work.prompt.md (307 lines → ~245 target)
- **Requirements**: R1, R2, R3, R5, R6
- **File**: `.github/prompts/cg-work.prompt.md`
- **Details**:
  - Run assertion scan (see Pre-step above)
  - Replace Step 0 with standard form (~12 → ~8 lines)
  - Compress Step 1 inline plan logic (~40 lines of conditionals)
  - Compress Step 1.6 Build Test Index (~8 → ~4 lines)
  - Compress Step 2 per-step loop — especially the Test Failure Recovery
    block (~30 lines) and Auto-Fix Diagnostics block (~25 lines)
  - Compress Steps 3–3.8 completion workflow (~100 lines, heaviest target)
  - Compress Step 4 summary template
  - Keep: exact `execution_subagent` query strings, YAML frontmatter
    examples, finding notification format, commit message format
- **Test Scenarios**:
  - ✅ All existing `prompt-tools.Tests.ps1` tests pass
  - ✅ File still contains all key markers tested by Pester (Step 0
    references, roadmap dispatch patterns, execution_subagent patterns)
  - 🛑 Line count is within 240–250 range
- **Acceptance criteria**: File ≤ 250 lines, all Pester tests pass

### 2. Compress cg-setup.prompt.md (309 lines → ~255 target)
- **Requirements**: R1, R3, R5, R6
- **File**: `.github/prompts/cg-setup.prompt.md`
- **Note**: This file has **no Step 0** — it bootstraps the files Step 0
  reads. All savings come from prose compression only.
- **Note**: `prompt-tools.Tests.ps1` has **zero** test coverage for this
  file. The manual correctness checklist below is the primary safety gate.
- **Details**:
  - Run assertion scan (see Pre-step) — expect zero matches; proceed
    with manual checklist below
  - Compress Step 1 detect with compact form
  - Compress Mode A questions — remove per-question explanatory text, keep
    the question prompts and option lists tight
  - Compress A3.5 charter creation — tighten the skip-definition paragraph
    and overwrite-guard logic
  - Compress A3.6, A3.7, A4, A4.5, A5, A5.5, A6 — many of these are
    short steps that can lose 1–2 lines each
  - Compress Mode B — B1.x sub-steps have verbose condition blocks
  - Compress B2–B4.7 — especially B4.5 charter update offer
  - Keep: exact question text, template references, `.gitignore` content
- **Manual correctness checklist** (no Pester coverage — verify by hand):
  - [ ] Mode A questions (A2, Questions 1–3) still present with options
  - [ ] Mode B context summary format intact
  - [ ] Overwrite guards for existing files preserved
  - [ ] `setup-templates.md` references intact
  - [ ] `.gitignore` append block verbatim
  - [ ] All conditional branches (if exists / if not) preserved
- **Test Scenarios**:
  - ✅ Manual checklist above — all items verified
  - 🛑 Line count is within 250–260 range
- **Acceptance criteria**: File ≤ 260 lines, manual checklist passes

### 3. Compress cg-plan.prompt.md (237 lines → ~190 target)
- **Requirements**: R1, R2, R3, R5, R6
- **File**: `.github/prompts/cg-plan.prompt.md`
- **Details**:
  - Run assertion scan (see Pre-step above)
  - Replace Step 0 with standard form + alignment check as bullet 4.
    **Note**: cg-plan has a unique 5th item ("Verify alignment with
    project objective/constraints") not present in other prompts —
    must be preserved. Target ~9–10 lines, not ~8.
  - Compress Step 0.5 prior work check (~20 lines → ~12)
  - Compress Step 1.5 scope assessment — table stays, surrounding prose
    tightens
  - Compress Step 3 plan template — the template itself stays verbatim,
    but the "Write a structured plan covering:" intro and surrounding
    instructions compress
  - Compress Step 4.5 confidence check — table stays, reporting rules
    tighten
  - Compress Step 5 roadmap registration (~35 lines, heavily nested
    conditionals → flatten)
  - Compress Step 6 handoff
  - Keep: plan template verbatim, confidence check table, scope table
- **Test Scenarios**:
  - ✅ All existing plan-related tests pass
  - 🛑 Line count is within 185–195 range
- **Acceptance criteria**: File ≤ 195 lines, all Pester tests pass

### 4. Compress cg-review.prompt.md (226 lines → ~180 target)
- **Requirements**: R1, R2, R3, R5, R6
- **File**: `.github/prompts/cg-review.prompt.md`
- **Details**:
  - Run assertion scan (see Pre-step above)
  - Replace Step 0 with standard form
  - Compress Step 1.5 content-based depth overrides — table stays, rules
    after it tighten
  - Compress Step 2 agent dispatch — the 3-tier agent lists stay, but the
    surrounding instructions (R package check, R skill check, Stata check,
    protected artifacts) compress
  - Compress Step 2.5 subagent output quality check
  - Compress Step 3 collect and prioritize — the output template stays,
    surrounding prose compresses
  - Compress Step 3.5 save review report (~25 lines → ~15)
  - Compress Step 4 triage mode
  - Compress Step 5 summary
  - Keep: agent lists per tier, output template, finding ID format,
    protected artifacts list, auto-escalation table
- **Test Scenarios**:
  - ✅ All existing review-related tests pass (no-tools restriction,
    output step markers, finding ID format)
  - 🛑 Line count is within 175–185 range
- **Acceptance criteria**: File ≤ 185 lines, all Pester tests pass

### 5. Compress cg-fix-triage.prompt.md (189 lines → ~150 target)
- **Requirements**: R1, R2, R3, R5, R6
- **File**: `.github/prompts/cg-fix-triage.prompt.md`
- **Details**:
  - Run assertion scan (see Pre-step above)
  - Replace Step 0 with standard form
  - Compress Step 1 load review report — tighten the 6 numbered sub-steps
  - Compress Step 2 determine scope — the argument-parsing rules tighten,
    large-report notice tightens
  - Compress Step 3 apply fixes — the per-finding loop tightens
  - Compress Step 4 summary template — remove blank lines, tighten
  - Compress Step 5 next steps
  - Compress `--migrate` mode — the companion-plan heuristic explanation
    is verbose
  - Keep: exact argument formats, finding status values, execution_subagent
    query pattern, YAML frontmatter example
- **Test Scenarios**:
  - ✅ All existing fix-triage tests pass
  - 🛑 Line count is within 145–155 range
- **Acceptance criteria**: File ≤ 155 lines, all Pester tests pass

### 6. Run Full Test Suite
- **Requirements**: R5
- **Files**: all test files
- **Details**: Run `. tests\Run-Tests.ps1` via `execution_subagent` and
  verify all tests pass. This is the final gate before commit.
- **Acceptance criteria**: All tests pass, zero regressions

## Testing Strategy

- **Primary**: Existing Pester tests in `tests/prompt-tools.Tests.ps1`
  (2,163 lines) — these check prompt structure, keyword presence, finding
  ID formats, template markers, and frontmatter fields. All must pass
  after each step.
- **Secondary**: Line-count verification after each file edit (measure
  with `(Get-Content <file>).Count`).
- **No new tests needed**: The existing test suite already validates the
  structural properties we're preserving. Prose compression doesn't
  change structure.

## Documentation Checklist
- [ ] No documentation changes needed — prompt files are self-documenting
- [ ] `docs/reference.md` — no changes (command names unchanged)
- [ ] README — no changes

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Over-compression removes a nuance the model needs | Medium | Pester tests catch structural markers. Manual spot-check after each file: verify the compressed text still reads as clear instructions. |
| Compression introduces a semantic difference | Low | Keep all conditional logic, exact strings, and template content unchanged. Only compress surrounding prose. |
| Tests don't cover a removed instruction | Low | Before compressing each section, scan `prompt-tools.Tests.ps1` for assertions that reference that section's content. |

## Out of Scope

- Prompt files beyond the top 5 (11 other prompts remain at current size)
- Agent files (`.agent.md`) — already lean
- Skill files (`SKILL.md`) — already use demand-loaded references
- Late-sequence extraction (rejected in brainstorm)
- Mode splitting / new commands (rejected in brainstorm)
- Any changes to `copilot-instructions.md`, `roadmap.json`, or scripts
