---
date: 2026-05-19
trigger: mid-project-new-ideas
milestone: knowledge-brain
status: approved
features-count: 13
batches: 4
---

# Strategy: Knowledge Brain

## Problem Statement

The `.cg-docs/` folder is growing dramatically (127+ solutions, 51+ plans, 35+
brainstorms, reviews, strategies). The agent cannot efficiently navigate all
accumulated knowledge during sessions. No relationships are tracked between
documents. No cross-project knowledge sharing mechanism exists. The current
`DIGEST.md` is a flat solution-only index with no graph structure.

## Vision

A concept-centric knowledge system that:
1. Indexes ALL `.cg-docs/` artifacts (not just solutions)
2. Organizes them by **topics and themes** (not just file-to-file links)
3. Tracks typed relationships between artifacts
4. Produces a single `BRAIN.md` entry point readable in one context window
5. Is consumed by every major command in Step 0 (the read path)
6. Enables cross-project knowledge sharing via a central team brain repo

## Design References

### Karpathy's LLM Wiki
- URL: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Key insights:
  - Three layers: Raw sources (immutable) → Wiki (LLM-maintained) → Schema (instructions)
  - Two navigation files: `index.md` (content catalog) + `log.md` (chronological)
  - "Compile once, keep current" vs RAG's "re-derive on every query"
  - At ~100-300 pages, index alone is sufficient without vector DB
  - Operations: Ingest, Query, Lint

### OmegaWiki
- URL: https://github.com/skyllwt/OmegaWiki
- Key insights:
  - 9 typed entities: papers, concepts, topics, people, ideas, experiments, methods, etc.
  - Knowledge graph: `graph/edges.jsonl` (typed edges with confidence)
  - `context_brief.md` — compressed snapshot fitting one context window
  - `open_questions.md` — tracked knowledge gaps
  - Python CLI with rebuild subcommands
  - Principle: "Every skill reads from and writes back to the wiki. Knowledge compounds."

## Architecture Decisions

### Entity Types
| Entity | Source | Notes |
|---|---|---|
| Solution | `.cg-docs/solutions/` | Already parsed by cg_index.py |
| Plan | `.cg-docs/plans/` | Same frontmatter format |
| Brainstorm | `.cg-docs/brainstorms/` | Same frontmatter format |
| Review | `.cg-docs/reviews/` | Same frontmatter format |
| Strategy | `.cg-docs/strategy/` | Same frontmatter format |
| Feature | `roadmap.json` | Structured JSON, trivial to ingest |

### Graph Structure — Topic-Centric
The brain is organized by TOPICS/THEMES, not just file-to-file edges:
```
Topic: "PowerShell 5.1 compatibility"
├── solutions: ps51-strict-mode-crashes, ps51-encoding-issues, ...
├── plans: ps51-migration-plan
├── patterns: "always test with -Version 5.1 flag"
├── gotchas: "Write-Host behaves differently in PS 5.1 ISE"
└── related topics: "cross-platform scripting", "Pester safety"
```

### Relationship Types (full set from day one)
- `implements` — plan → feature
- `resolves` — solution → plan finding
- `supersedes` — newer artifact → older artifact
- `decided_from` — plan → brainstorm
- `reviews` — review → plan
- `references` — any → any (general citation)

### Retrieval Interface — Single File (BRAIN.md)
One file with three sections:
1. **Topic index** (primary navigation) — each topic with artifacts + takeaways
2. **Entity catalog** (secondary) — organized by entity type
3. **Edge list** (tertiary) — full relationship tracking

Replaces current `DIGEST.md`. Fits in one context window.

### Update Triggers — Option C
- **Automatic**: rebuild on `/cg-compound`
- **Explicit**: `/cg-brain-rebuild` command for on-demand use
- All other commands CONSUME the brain (read path) but don't rebuild it

### Read Path — Consult Brain in Step 0
Every major command gains a "Consult Brain" sub-step:
| Command | Brain usage |
|---|---|
| /cg-brainstorm | Prior explorations? Abandoned approaches and why? |
| /cg-plan | Existing solutions for sub-tasks? Failed plans for similar features? |
| /cg-work | Gotchas/edge cases from similar work? |
| /cg-review | Known mistakes documented before? |
| /cg-fix-triage | Known fix for this finding? |
| /cg-compound | Does this supersede/contradict existing solutions? |

### Team Brain — Solutions + Distilled Patterns (Phase 2)
Only solutions and auto-distilled reusable patterns cross the project boundary.
Plans, brainstorms, and reviews stay project-local (too context-specific).
Privacy filter strips project-specific details before pushing upstream.

## Implementation Batches

### Batch A — The Engine (features 1–4)
Design and build together as one coherent unit. These are the same indexing pass.
- `brain-full-scope-indexer`
- `brain-topic-extraction`
- `brain-relationship-detection`
- `brain-md-generation`

### Batch B — The Triggers (features 5–6)
Quick wiring once engine exists. One short session.
- `brain-rebuild-command`
- `brain-auto-rebuild-on-compound`

### Batch C — The Read Path (features 7–8)
Makes the brain useful. Design consumption patterns together.
- `brain-prompt-integration`
- `brain-query-skill`

### Batch D — Team Brain (features 9–13, Phase 2)
Cross-project knowledge sharing. Sub-batchable.
- `team-brain-repo-schema` (design first)
- `team-brain-push` + `team-brain-pull` (together)
- `team-brain-dedup` + `team-brain-privacy-filter` (together)

## Execution Order

A → B → C → D

Each batch produces a testable increment:
- After A: `cg-index --all` produces a working BRAIN.md ✓
- After B: Brain auto-rebuilds at the right moments ✓
- After C: Agents actually use the brain in their workflows ✓
- After D: Knowledge flows across projects ✓

## How to Execute a Batch

For each batch:
1. `/cg-brainstorm` — describe the entire batch as one design unit
2. `/cg-plan` — reference the brainstorm, produce a phased plan
3. `/cg-work` — implement phase by phase

Example for Batch A:
> `/cg-brainstorm` → "Design the project brain engine per the strategy in
> .cg-docs/strategy/2026-05-19-knowledge-brain.md — Batch A features:
> full-scope indexer, topic extraction, relationship detection, BRAIN.md generation"

## Existing Infrastructure

- `scripts/cg_index.py` v0.1.0: stdlib-only Python 3.8+, regex-based frontmatter
  parsing, currently scans `.cg-docs/solutions/` only
- `.cg-docs/DIGEST.md`: 127 active solutions, flat list, no relationships
- `bin/cg-index` + `bin/cg-index.cmd`: shell wrappers for the indexer

The existing indexer will be extended (not replaced) since its frontmatter
parser and CLI structure are already solid.
