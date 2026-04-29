---
date: 2026-04-29
title: "Smart /cg-setup with project scanner agent"
status: decided
scope: "Deep"
chosen-approach: "Scanner-first, then Integration (Two Phases)"
tags: [onboarding, setup, scanner, charter, quality-gate, agent, skill]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Smart /cg-setup with Project Scanner Agent

## Context

The current `/cg-setup` asks 10 generic questions regardless of what already exists in the project. For existing projects with `pyproject.toml`, `DESCRIPTION`, `README.md`, etc., most of these questions are answerable by scanning the file system. The goal is to make `/cg-setup` intelligent — scan first, draft a charter from what it finds, and only ask about what couldn't be inferred.

This brainstorm covers 4 roadmap features in the Onboarding & Setup milestone:
- **Project scanner agent** (`project-scanner-agent`)
- **Smart /cg-setup for existing projects** (`smart-setup-existing-projects`)
- **Skip high-confidence setup questions** (`skip-irrelevant-setup-questions`)
- **Charter quality gate** (`charter-quality-gate`)

## Requirements

### Scanner Architecture
- **Skill + Agent hybrid (Option C)**: A skill file (`cg-skill-project-scanner/SKILL.md`) holds the signal catalog — what files to look for, what patterns mean, confidence rules. A thin agent (`@cg-project-scanner`) loads the skill and orchestrates file reads, returning structured analysis.
- Rationale: The signal catalog is structured reference knowledge (like R dialect skills). The skill is loadable without agent dispatch for lighter-weight consumption. The agent handles orchestration and is dispatchable by any prompt.

### Signal Catalog (4 tiers)

**Tier 1: Language & Framework Detection** (high confidence → skip the question)

| Signal File | Inference | Confidence |
|---|---|---|
| `DESCRIPTION` + `NAMESPACE` | R package | high |
| `renv.lock` or `.Rprofile` with renv | R, renv managed | high |
| `pyproject.toml` | Python | high |
| `uv.lock` / `poetry.lock` / `requirements.txt` | Python, dep manager variant | high |
| `*.do` or `*.ado` in tree | Stata | high |
| `master.do` or `main.do` | Stata analysis project | medium |
| `reproot.yaml` | Stata + repkit | high |
| `_targets.R` or `_targets/` | R targets pipeline | high |
| `app.R` or `ui.R` + `server.R` | Shiny dashboard | high |
| `plumber.R` or `entrypoint.R` | R API | high |
| FastAPI/Flask in `pyproject.toml` deps | Python API | high |
| `streamlit` in deps | Python dashboard | high |

**Tier 2: Project Type & Convention Signals** (medium confidence → pre-fill but confirm)

| Signal | Inference | Confidence |
|---|---|---|
| `.github/workflows/` present | CI exists | medium |
| `testthat/` or `tests/testthat/` | R testing in place | high |
| `tests/` with `conftest.py` or `test_*.py` | Python testing | high |
| `README.md` present + parseable | Extract project name, objective text | medium |
| Existing `.github/copilot-instructions.md` | Vanilla Copilot user, may have preferences to merge | medium |
| `data/` or `data-raw/` directory | Analysis project (not package/API) | low |

**Tier 3: Charter-Relevant Content** (scan for draft, always confirm)

| Signal | Maps to Charter Section |
|---|---|
| README first paragraph | Objective |
| README "Installation" / "Usage" sections | Key Deliverables |
| Existing `DESCRIPTION` Title/Description fields | Objective + Project Name |
| `.gitignore` patterns | Constraints (what's excluded) |
| Git remote URL | Team/org context |

**Tier 4: Out-of-scope for v1** (note but don't act on)

| Signal | Why defer |
|---|---|
| Git history depth / commit patterns | Expensive to scan, low ROI for charter |
| Code complexity metrics | Needs AST parsing, overkill for setup |
| Dependency vulnerability scan | Different concern (security, not onboarding) |

### Confidence Thresholds

| Level | Behavior |
|---|---|
| **High** | Skip the question entirely, set the value silently |
| **Medium** | Pre-fill the answer and show for confirmation ("I detected Python + FastAPI. Correct?") |
| **Low** | Ask the question normally, mention what was detected ("I found a `data/` directory — is this an analysis project?") |

### Draft-and-Approve UX
- **Hybrid flow**: Scanner runs → `/cg-setup` generates a complete `compound-gpid.md` draft → displays it in a fenced code block → asks: "Approve as-is, or walk through section by section?"
- Power users approve immediately. New users get guided walkthrough per section.

### Charter Quality Gate (Tiered)
- **Errors (block)**: `project-name` missing, `last-reviewed` is not a valid date, `<!-- TODO -->` placeholders still present.
- **Warnings (continue with notice)**: Empty optional sections (Constraints, Current Focus).
- Matches the project's existing P0/P1 (block) vs P2/P3 (advisory) priority system.

## Approaches Considered

### Approach 1: All-at-once (Big Bang)
Build all 4 features in one pass: skill, agent, `/cg-setup` rewrite, quality gate.
- **Pros**: One coherent rewrite, no intermediate states.
- **Cons**: Large changeset, hard to review/test, higher regression risk to Mode B.
- **Not chosen**: Too risky for a prompt that currently works.

### Approach 2: Scanner-first, then Integration (Two Phases) — CHOSEN
**Phase 1**: Build scanner infrastructure — `cg-skill-project-scanner/SKILL.md` with signal catalog, `@cg-project-scanner.agent.md` returning structured analysis. Testable in isolation, no changes to `/cg-setup`.
**Phase 2**: Integrate into `/cg-setup` — rewrite Mode A to dispatch scanner, add hybrid draft-approve flow, add quality gate.
- **Pros**: Phase 1 is self-contained and testable. Scanner can be validated against real projects before wiring into `/cg-setup`. Phase 2 only touches `/cg-setup` once scanner is proven.
- **Cons**: Two plan/work cycles. Phase 1 has no user-visible value alone.

### Approach 3: Incremental Feature Slices (Four Phases)
Ship each feature as its own slice: scanner, integration, question skipping, quality gate.
- **Pros**: Smallest changesets, independently testable.
- **Cons**: Slices 2 and 3 are tightly coupled — artificial to separate. 4 plan/review/work cycles is disproportionate overhead.
- **Not chosen**: Over-sliced.

## Decision

Approach 2 — **Scanner-first, then Integration** — chosen for its balance of testability and cohesion.

- Phase 1 delivers the scanner as a standalone, testable component.
- Phase 2 wires it into the user-facing flow with confidence-based question skipping, hybrid approve, and quality gate.

## Next Steps

1. `/cg-plan` Phase 1 — build `cg-skill-project-scanner/SKILL.md` (signal catalog + confidence rules) and `@cg-project-scanner.agent.md` (thin orchestrator). Test by running `@cg-project-scanner` against the compound-gpid repo itself and at least one consumer project.
2. `/cg-plan` Phase 2 — rewrite `/cg-setup` Mode A to dispatch scanner, implement hybrid draft-approve flow, add tiered quality gate. Preserve Mode B (returning projects) without regressions.
