---
date: 2026-05-19
title: "Knowledge Brain Engine — Batch A Design"
status: decided
scope: "Standard"
chosen-approach: "Modular single-pass (hybrid)"
tags: [brain, indexer, topics, relationships, knowledge-graph, cg-index]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Knowledge Brain Engine — Batch A Design

## Context

The `.cg-docs/` folder has grown to 127+ solutions, 51+ plans, 35+ brainstorms,
plus reviews and strategies. The current `DIGEST.md` is a flat solution-only
index with no relationships, no topic organization, and no coverage of plans,
brainstorms, reviews, or strategies. Agents cannot efficiently navigate
accumulated knowledge during sessions.

This brainstorm designs Batch A of the Knowledge Brain strategy
(`.cg-docs/strategy/2026-05-19-knowledge-brain.md`): the engine that indexes
all artifacts, extracts topics, detects relationships, and generates the
multi-file BRAIN output.

## Requirements

### Functional
1. **Full-scope indexing**: Scan all `.cg-docs/` subdirectories (solutions,
   plans, brainstorms, reviews, strategies) plus `roadmap.json` features.
2. **Deep content extraction**: Extract keywords from backtick terms, headings,
   first sentence per section, file references, command references, pattern
   names, and word frequency (stopword-filtered) — not just frontmatter.
3. **Topic clustering**: Auto-cluster artifacts into topics using keyword
   co-occurrence across documents. Topics emerge from data, not manual
   definition. Clustering algorithm is pluggable for future NLP upgrade.
4. **Relationship detection**: Parse explicit frontmatter links (`brainstorm:`,
   `plan:`, `parent-review:`), infer edges from naming conventions (same
   date+slug across directories), and infer `implements` from roadmap feature
   ID matches.
5. **Multi-file output with token cap**: BRAIN.md is the meta-index (~20K token
   cap per file). When corpus exceeds cap, split into topic-partitioned
   sub-files (`BRAIN-01.md`, `BRAIN-02.md`, ...) with cross-references.
6. **Chronological log**: `BRAIN-log.md` — all artifacts ordered by date,
   newest first (Karpathy's `log.md` pattern).
7. **Machine-readable index**: `brain-index.json` — structured data with
   entities, topics, and edges. Replaces `search-index.json`.
8. **Replaces both legacy outputs**: `BRAIN.md` supersedes `DIGEST.md`;
   `brain-index.json` supersedes `search-index.json`.

### Non-functional
- **Stdlib-only Python 3.8+**: No external dependencies. Cross-platform
  (Windows + macOS) with zero changes.
- **Performance**: Full rebuild under 2 seconds for ~200 documents.
- **Token budget**: Each BRAIN file ≤20K tokens. Meta-index routes agents
  to the right sub-brain by topic.
- **Pluggable clustering**: Topic extraction module can be swapped for a
  richer algorithm (e.g., scikit-learn TF-IDF) in a future batch without
  changing the pipeline interface.

### Edge Types (full set from day one)
| Edge type | Source → Target | Detection method |
|---|---|---|
| `decided_from` | plan → brainstorm | Explicit `brainstorm:` field |
| `reviews` | review → plan | Explicit `plan:` field |
| `verifies` | verify-review → review | Explicit `parent-review:` field |
| `implements` | plan → roadmap feature | Filename keyword match to feature ID |
| `resolves` | solution → plan finding | Explicit field (future) |
| `supersedes` | newer → older | Explicit field (future) |
| `references` | any → any | Explicit field (future) + name inference |

### Content Extraction Signals
| Signal | Source | Weight |
|---|---|---|
| Frontmatter tags | `tags: [...]` | High |
| Category (directory) | Parent folder name | Medium |
| Backtick terms | `` `Invoke-Pester` `` in body | High |
| Heading text | `## Problem`, `## Solution` | High |
| Command references | `/cg-brainstorm`, `cg-link` | Medium |
| File references | `.ps1`, `.prompt.md` mentions | Medium |
| Pattern names | "IndexOf guard pattern" | High |
| Keyword frequency | Stopword-filtered word counts | Medium |
| First sentence per section | Paragraph after `##` | Low-Medium |

## Approaches Considered

### Approach 1: Single-pass pipeline
One `cg-index --brain` invocation does everything in a single sequential
pipeline within a single Python file.

**Pros**: Simple mental model, no intermediate state, consistent output.
**Cons**: Monolithic file, harder to swap components, harder to unit test in
isolation.

### Approach 2: Multi-stage with intermediate JSON
Split into explicit stages with intermediate JSON files between each stage.

**Pros**: Each stage independently testable, can re-run partial stages.
**Cons**: Over-engineered for current scale, intermediate file management,
ordering dependencies.

### Approach 3: Modular single-pass (hybrid) ✓
One CLI invocation, internally organized as separate Python modules
(`scanner.py`, `extractor.py`, `clusterer.py`, `edge_detector.py`,
`renderer.py`) that pass data structures in memory.

**Pros**: Clean architecture, unit-testable per module, pluggable clusterer
(NLP upgrade path), single command UX, no intermediate file clutter.
**Cons**: Multiple `.py` files to maintain, import structure.

## Decision

**Chosen: Approach 3 — Modular single-pass (hybrid)**

Reasons:
- Best balance of clean architecture and simple UX
- The pluggable clusterer directly addresses the "future NLP upgrade" design
  goal without requiring any user-facing changes
- Each module is independently testable with pytest
- User sees one command; developer sees clean separation of concerns

## Architecture

```
scripts/
├── cg_index.py          # CLI entry point + legacy --index/--digest (deprecated path)
└── brain/
    ├── __init__.py      # Package init, version
    ├── scanner.py       # Full-scope entity scanner (all .cg-docs/ + roadmap.json)
    ├── extractor.py     # Deep content extraction (backtick terms, headings, keywords)
    ├── clusterer.py     # Topic clustering (pluggable algorithm)
    ├── edge_detector.py # Relationship detection (explicit + inferred)
    └── renderer.py      # Multi-file BRAIN.md + log + JSON output
```

Output files:
```
.cg-docs/
├── BRAIN.md             # Meta-index (routes to sub-brains by topic)
├── BRAIN-01.md          # Topic-partitioned sub-file (≤20K tokens)
├── BRAIN-02.md          # (created only when needed)
├── BRAIN-log.md         # Chronological log (all artifacts by date)
└── brain-index.json     # Machine-readable (entities + topics + edges)
```

## Next Steps

1. `/cg-plan` — Turn this into a phased implementation plan:
   - Phase 1: Scanner module (extend entity scanning to all directories)
   - Phase 2: Extractor module (deep content extraction)
   - Phase 3: Clusterer module (topic detection with pluggable algorithm)
   - Phase 4: Edge detector module (explicit + inferred relationships)
   - Phase 5: Renderer module (multi-file BRAIN output with token cap)
   - Phase 6: CLI integration (new `--brain` flag, deprecate `--index`/`--digest`)
2. Update `cg_index.py` version to 0.2.0 upon completion
3. Update `install.ps1` / `install.sh` if any new bin wrappers needed
4. Add tests for each module (pytest)
