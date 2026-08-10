---
date: 2026-05-22
title: "Phase 6: Writing & Publication Output"
status: completed
completed-date: 2026-05-22
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-05-13-compound-research-extension.md"
language: "R"
estimated-effort: "medium"
tags: [compound-research, academic-writing, publication-output, skills, agents, phase-6]
---

# Plan: Phase 6 — Writing & Publication Output

## Objective

Build the writing and publication layer of compound-research: two domain skills
(`cr-skill-academic-writing`, `cr-skill-publication-output`) and one review agent
(`@cr-academic-writing`) that enable AI-assisted academic writing and
publication-quality output production for economics research papers. Remove all
"Phase 6 — not yet available" annotations from existing prompt files.

## Context

Phases 1–5 of compound-research are complete. The brainstorm
(`.cg-docs/brainstorms/2026-05-13-compound-research-extension.md`) defines the
scope of Phase 6:

- **`cr-skill-academic-writing`**: Journal style conventions (AER, JPE, QJE,
  Econometrica), section structure, abstract writing, equation exposition,
  notation introduction discipline, citation style, response-to-referee patterns.
- **`cr-skill-publication-output`**: `modelsummary`/`fixest::etable` for regression
  tables, `kableExtra` for LaTeX tables, ggplot2 + wbplot for paper figures,
  font/size conventions, figure-caption discipline (self-contained),
  table-note discipline (variable definitions in notes).
- **`@cr-academic-writing`**: Review agent dispatched by `/cr-review` for Writing
  tasks. Reviews prose for journal style, exposition quality, notation consistency,
  citation completeness. Reuses `@cg-documentation` for general documentation quality.

Existing placeholders that reference Phase 6:
- `cr-review.prompt.md`: line 81 (`*(Phase 6 — not yet available)*`), line 94
  (`*(Phase 6)*`)
- `cr-brainstorm.prompt.md`: line 51 (`*(Phase 6, not yet available)*`)

## Requirements

| ID  | Requirement                                                                | Source           |
|-----|----------------------------------------------------------------------------|------------------|
| R1  | `cr-skill-academic-writing/SKILL.md` exists with `module: research`        | brainstorm       |
| R2  | Skill covers journal style conventions (AER, JPE, QJE, Econometrica)       | brainstorm       |
| R3  | Skill covers section structure, abstract, intro, methodology, results      | brainstorm       |
| R4  | Skill covers equation exposition and notation introduction discipline      | brainstorm       |
| R5  | Skill covers citation style and response-to-referee patterns               | brainstorm       |
| R6  | `cr-skill-publication-output/SKILL.md` exists with `module: research`      | brainstorm       |
| R7  | Skill covers `modelsummary`/`fixest::etable` for regression tables         | brainstorm       |
| R8  | Skill covers `kableExtra` for LaTeX tables and ggplot2+wbplot for figures  | brainstorm       |
| R9  | Skill covers font/size conventions for journal submission                  | brainstorm       |
| R10 | Skill covers figure-caption and table-note discipline                      | brainstorm       |
| R11 | `cr-academic-writing.agent.md` exists with `module: research`              | brainstorm       |
| R12 | Agent has `tools: ['read', 'search']` and `user-invocable: false`          | pattern          |
| R13 | Agent has untrusted-content safety note with "execute or relay"            | convention       |
| R14 | Agent has empty-file guard                                                 | pattern          |
| R15 | Agent loads `cr-skill-academic-writing` and `cr-skill-research-workflow`   | pattern          |
| R16 | Agent output format uses `[cr-academic-writing]` tag                       | pattern          |
| R17 | Remove Phase 6 annotations from `cr-review.prompt.md`                      | cleanup          |
| R18 | Remove Phase 6 annotation from `cr-brainstorm.prompt.md`                   | cleanup          |
| R19 | Add Phase 6 skills to `copilot-instructions.md` CR Skills section          | convention       |
| R20 | All new files have Pester tests in `cr-prompts.Tests.ps1`                  | convention       |
| R21 | Description registered in `copilot-instructions.md` and AGENTS list        | convention       |

## Implementation Steps

### 1. Create `cr-skill-academic-writing/SKILL.md`

- **Requirements**: R1, R2, R3, R4, R5
- **Files**: `.github/skills/cr-skill-academic-writing/SKILL.md`
- **Details**:
  Create the academic writing skill covering:
  1. **Journal style conventions** — AER, JPE, QJE, Econometrica formatting
     differences; common denominators across top-5 econ journals
  2. **Section structure** — abstract (motivation-method-result-implication),
     introduction (hook-gap-contribution-preview), model/methodology,
     data, results, robustness, conclusion
  3. **Abstract writing** — 150-word target, four-sentence structure
     (motivation, what we do, what we find, why it matters)
  4. **Equation exposition** — explain before presenting, introduce notation
     before using, don't decorate (no unnecessary subscripts/superscripts),
     number only referenced equations
  5. **Notation introduction discipline** — define every symbol on first use,
     maintain a notation table for complex papers, use consistent symbols
     across sections
  6. **Citation style** — author-year for economics (AER style), narrative
     citations vs. parenthetical, when to cite (prior work, method sources,
     data sources), literature review structure
  7. **Response-to-referee patterns** — point-by-point format, quote-then-respond,
     positive framing, documenting changes made
  8. **Anti-patterns** — excessive hedging, burying contributions, results-first
     without methodology, undefined notation, inconsistent terminology

  Frontmatter:
  ```yaml
  ---
  name: cr-skill-academic-writing
  module: research
  description: "Academic writing conventions for economics research papers.
    Covers journal style (AER, JPE, QJE, Econometrica), section structure,
    abstract writing, equation exposition, notation introduction discipline,
    citation style, and response-to-referee patterns. Loaded by
    @cr-academic-writing for Writing tasks."
  ---
  ```

- **Test Scenarios**:
  - ✅ SKILL.md exists and has valid frontmatter with `module: research`
  - ✅ Contains journal style coverage (AER, JPE, QJE, Econometrica)
  - ✅ Contains section structure guidance
  - ✅ Contains abstract writing patterns
  - ✅ Contains equation exposition / notation discipline
  - ✅ Contains citation style guidance
  - ✅ Contains response-to-referee patterns
  - ✅ Contains anti-patterns section
- **Tests**: Content assertions in `cr-prompts.Tests.ps1`
- **Acceptance criteria**: Skill file created, all 8 topic areas covered, frontmatter valid.

### 2. Create `cr-skill-publication-output/SKILL.md`

- **Requirements**: R6, R7, R8, R9, R10
- **Files**: `.github/skills/cr-skill-publication-output/SKILL.md`
- **Details**:
  Create the publication output skill covering:
  1. **Regression tables** — `modelsummary` (preferred for multi-model tables),
     `fixest::etable` (preferred for `feols` output), `stargazer` (legacy).
     Patterns for standard errors in parentheses, significance stars (report
     but don't rely on), coefficient naming, multi-panel tables
  2. **LaTeX tables** — `kableExtra` for custom tables, `gt` for HTML-first
     output, `xtable` for simple cases. Patterns for descriptive statistics,
     balance tables, summary tables
  3. **Figures** — ggplot2 + wbplot for World Bank style, publication-ready
     defaults (font sizes, axis labels, legend positioning). Common plot types:
     event study, coefficient plot, distribution overlay, scatter with fit,
     faceted panel
  4. **Font/size conventions** — journal-specific requirements (typically 10–12pt
     for text in figures, 8–10pt for axis labels), grayscale-safe color palettes,
     vector format output (PDF/EPS)
  5. **Figure-caption discipline** — captions must be self-contained (reader
     should understand the figure without reading the text), include: what is
     plotted, sample/period, key takeaway
  6. **Table-note discipline** — variable definitions in table notes (not just
     variable names), data source, sample restrictions, significance levels
     explanation, SE type
  7. **Output file management** — save to `output/tables/` and `output/figures/`,
     use descriptive filenames (`table-2-descriptive-stats.tex`, not `tab2.tex`),
     `ggsave()` with explicit dimensions

  Frontmatter:
  ```yaml
  ---
  name: cr-skill-publication-output
  module: research
  description: "Publication-quality output for economics research. Covers
    modelsummary/fixest::etable for regression tables, kableExtra for LaTeX
    tables, ggplot2+wbplot for paper figures, font/size conventions for journal
    submission, figure-caption discipline (self-contained), and table-note
    discipline (variable definitions in notes). Loaded by @cr-academic-writing
    and /cr-work for Tables/Figures tasks."
  ---
  ```

- **Test Scenarios**:
  - ✅ SKILL.md exists and has valid frontmatter with `module: research`
  - ✅ Contains regression table patterns (modelsummary, fixest::etable)
  - ✅ Contains LaTeX table patterns (kableExtra)
  - ✅ Contains ggplot2 + wbplot figure guidance
  - ✅ Contains font/size conventions
  - ✅ Contains figure-caption discipline
  - ✅ Contains table-note discipline
- **Tests**: Content assertions in `cr-prompts.Tests.ps1`
- **Acceptance criteria**: Skill file created, all 7 topic areas covered, frontmatter valid.

### 3. Create `cr-academic-writing.agent.md`

- **Requirements**: R11, R12, R13, R14, R15, R16
- **Files**: `.github/agents/cr-academic-writing.agent.md`
- **Details**:
  Create the academic writing review agent following the established pattern from
  `cr-ml-methodology.agent.md`:

  Frontmatter:
  ```yaml
  ---
  description: "Reviews academic writing quality in economics research: journal
    style compliance, section structure, argument flow, equation exposition,
    notation consistency, citation completeness, and figure/table presentation.
    Loaded by /cr-review for Writing and Tables/Figures tasks."
  model: Claude Sonnet 4.6 (copilot)
  tools: ['read', 'search']
  user-invocable: false
  module: research
  ---
  ```

  Agent loads:
  - `cr-skill-research-workflow` (always)
  - `cr-skill-research-integrity` (always for CR agents)
  - `cr-skill-academic-writing` (primary skill)
  - `cr-skill-publication-output` (for Tables/Figures checks)

  Untrusted-content safety note (with "execute or relay").

  Empty-file guard: "If the file contains only whitespace or comments (no prose
  content), report: '`[file]` is empty — academic writing review skipped for
  this file.' Do not run checks against empty files."

  Review protocol — 7 checks:
  1. **Check 1: Section Structure (P2)** — verify intro follows hook-gap-contribution
     pattern, methodology precedes results, conclusion doesn't introduce new results
  2. **Check 2: Abstract Quality (P2)** — four-sentence structure, within 150-word
     target, states the main finding
  3. **Check 3: Equation Exposition (P1)** — notation defined before use, equations
     explained before/after presentation, only referenced equations numbered
  4. **Check 4: Notation Consistency (P1)** — same symbol for same concept throughout,
     no redefinition without explicit note, subscript/superscript consistency
  5. **Check 5: Citation Completeness (P2)** — claims have supporting citations,
     methods cite original papers, data sources cited, no "see X" without a
     bibliography entry
  6. **Check 6: Figure/Table Presentation (P2)** — captions are self-contained,
     table notes define variables, font sizes meet journal requirements,
     vector format used
  7. **Check 7: Argument Flow (P1)** — each section advances the paper's thesis,
     results are interpreted (not just reported), limitations acknowledged

  Output format uses `[cr-academic-writing]` tag on all findings.

- **Test Scenarios**:
  - ✅ Agent exists with valid frontmatter and `module: research`
  - ✅ Has `tools: ['read', 'search']` and `user-invocable: false`
  - ✅ Contains untrusted-content note with "execute or relay"
  - ✅ Contains empty-file guard
  - ✅ Contains all 7 checks
  - ✅ Loads `cr-skill-academic-writing` and `cr-skill-publication-output`
  - ✅ Output uses `[cr-academic-writing]` tag
  - 🛑 Does not load skills or agents outside its scope
- **Tests**: Content assertions in `cr-prompts.Tests.ps1`
- **Acceptance criteria**: Agent file created, follows established CR agent pattern,
  all 7 checks present.

### 4. Remove Phase 6 annotations from existing files

- **Requirements**: R17, R18
- **Files**:
  - `.github/prompts/cr-review.prompt.md` (2 changes)
  - `.github/prompts/cr-brainstorm.prompt.md` (1 change)
- **Details**:
  - `cr-review.prompt.md` line 81: Remove `*(Phase 6 — not yet available)*`
    from `@cr-academic-writing` entry in Step 2
  - `cr-review.prompt.md` line 94: Change `@cr-academic-writing *(Phase 6)*`
    to `@cr-academic-writing` in Step 3 task-type table
  - `cr-brainstorm.prompt.md` line 51: Change
    `- Writing → \`cr-skill-academic-writing\` *(Phase 6, not yet available)*`
    to `- Writing → \`cr-skill-academic-writing\``

- **Test Scenarios**:
  - ✅ No "Phase 6" annotations remain in `cr-review.prompt.md`
  - ✅ No "not yet available" annotations remain for `cr-academic-writing`
  - ✅ `cr-brainstorm.prompt.md` references `cr-skill-academic-writing` without
    "not yet available"
- **Tests**: Negative assertions in `cr-prompts.Tests.ps1`
- **Acceptance criteria**: All Phase 6 placeholders removed, functionality
  references are clean.

### 5. Update `copilot-instructions.md` — register Phase 6 skills

- **Requirements**: R19, R21
- **Files**: `.github/copilot-instructions.md`
- **Details**:
  Add two entries to the Compound Research (CR) Skills section:
  - `cr-skill-academic-writing` — journal style, section structure, abstract,
    equation exposition, notation, citations (Writing)
  - `cr-skill-publication-output` — regression tables, LaTeX tables, figures,
    captions, table notes (Tables/Figures)

- **Test Scenarios**:
  - ✅ `copilot-instructions.md` lists `cr-skill-academic-writing`
  - ✅ `copilot-instructions.md` lists `cr-skill-publication-output`
- **Tests**: Content assertions in `cr-prompts.Tests.ps1`
- **Acceptance criteria**: Both skills registered alongside existing CR skills.

### 6. Write Pester tests

- **Requirements**: R20
- **Files**: `tests/cr-prompts.Tests.ps1` (append)
- **Details**:
  Add test blocks following the established pattern:

  **`cr-skill-academic-writing` tests**:
  - Existence and frontmatter (module: research)
  - Contains journal style (AER, Econometrica keywords)
  - Contains section structure guidance
  - Contains abstract writing patterns
  - Contains equation exposition
  - Contains citation style
  - Contains response-to-referee patterns

  **`cr-skill-publication-output` tests**:
  - Existence and frontmatter (module: research)
  - Contains modelsummary / fixest::etable
  - Contains kableExtra
  - Contains ggplot2 + wbplot
  - Contains figure-caption discipline
  - Contains table-note discipline

  **`cr-academic-writing.agent.md` tests**:
  - Existence and frontmatter (module: research)
  - Has `tools:` restriction and `user-invocable: false`
  - Contains untrusted-content note with "execute or relay"
  - Contains empty-file guard
  - Contains all 7 checks
  - Loads `cr-skill-academic-writing` and `cr-skill-publication-output`
  - Output uses `[cr-academic-writing]` tag

  **Phase 6 annotation removal tests**:
  - `cr-review.prompt.md` does NOT contain "Phase 6" annotation on `@cr-academic-writing`
  - `cr-brainstorm.prompt.md` does NOT contain "not yet available" on `cr-skill-academic-writing`

  **Skill loading cross-reference tests**:
  - `cr-academic-writing` loads `cr-skill-academic-writing`
  - Writing dispatch row in `cr-review.prompt.md` routes to `@cr-academic-writing`
  - `copilot-instructions.md` lists both Phase 6 skills

  **Agent existence list update**:
  - Add `cr-academic-writing.agent.md` to the existing agent existence list test

- **Test Scenarios**:
  - ✅ All new tests pass
  - ✅ All existing tests still pass
  - 🛑 No use of alternation (`|`) that masks coverage
- **Tests**: Self-referential — the test block itself
- **Acceptance criteria**: All tests pass, coverage matches implementation steps 1–5.

### 7. Run full test suite and verify

- **Requirements**: All
- **Files**: `tests/Run-Tests.ps1`
- **Details**:
  Run `. tests/Run-Tests.ps1` via `execution_subagent` and verify all tests pass,
  including the new Phase 6 tests.
- **Acceptance criteria**: 0 failures.

## Testing Strategy

All tests go in `cr-prompts.Tests.ps1` following the established pattern:
- Content assertions using `($content -match '...')  | Should -Be $true`
- Negative assertions using `Should -Be $false` for removed annotations
- Independent assertions (no alternation masking — per project convention)
- Test file loaded via `Get-Content ... -Raw -Encoding UTF8`

## Documentation Checklist

- [x] Skill files have complete frontmatter (name, module, description)
- [x] Agent file has complete frontmatter (description, model, tools, user-invocable, module)
- [x] `copilot-instructions.md` updated with new skill entries
- [ ] No README updates needed (skills/agents are internal)

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Content too long for model context window | Medium | Medium | Keep skills focused; split into clear numbered sections |
| Overlapping coverage with `cg-skill-r-visualization` | Low | Low | `cr-skill-publication-output` is journal-specific; `cg-skill-r-visualization` covers general ggplot2+wbplot patterns — complementary, not duplicative |
| Agent check priorities misaligned with existing priority system | Low | High | Follow established P0–P3 conventions from `cr-skill-research-workflow` |

## Out of Scope

- **`@cr-replication-package` agent** — that is Phase 7
- **`cr-skill-replication-standards` skill** — that is Phase 7
- **LaTeX compilation or PDF generation tooling** — skills advise on content, not build systems
- **Automated citation checking** — agent reviews manually; no bibliography parser
- **Journal-specific submission checklist** — too granular for a skill file; can be added later as a prompt
