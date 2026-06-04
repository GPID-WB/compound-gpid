---
date: 2026-05-19
title: "Knowledge Brain Engine — Batch A"
status: complete
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-05-19-knowledge-brain-engine-batch-a.md"
language: "Python"
estimated-effort: "large"
tags: [brain, indexer, topics, relationships, knowledge-graph, cg-index, python]
phases: 2
completed-phases: [1, 2]
---

# Plan: Knowledge Brain Engine — Batch A

## Objective

Extend `cg_index.py` into a modular brain engine that indexes all `.cg-docs/`
artifacts (solutions, plans, brainstorms, reviews, strategies) plus roadmap
features, extracts deep content keywords, auto-clusters artifacts into topics,
detects typed relationships, and generates a multi-file BRAIN output system
that replaces both `DIGEST.md` and `search-index.json`.

## Context

- `cg_index.py` v0.1.0 exists: stdlib-only Python 3.8+, regex frontmatter
  parser, scans only `.cg-docs/solutions/`, produces `search-index.json` and
  `DIGEST.md`.
- Strategy approved: `.cg-docs/strategy/2026-05-19-knowledge-brain.md`
- Brainstorm decided: Approach 3 (modular single-pass), stdlib-only, deep
  content extraction, multi-file with 20K token cap, cross-file meta-index,
  chronological log, pluggable clusterer.
- Existing explicit relationship fields in frontmatter: `plan.brainstorm`
  (always), `review.plan` (~40%), `review.parent-review` (verify reviews),
  `solution.plan`/`solution.brainstorm` (rare ~5%).
- Atomic write pattern already in `cg_index.py` (`_write_atomic` via
  `mkstemp` + `os.replace`).

## Requirements

| ID  | Requirement                                                        | Source      |
|-----|--------------------------------------------------------------------|-------------|
| R1  | Scan all `.cg-docs/` subdirectories (solutions, plans, brainstorms, reviews, strategies) | brainstorm |
| R2  | Ingest `roadmap.json` features as entities                         | brainstorm  |
| R3  | Extract deep content keywords: backtick terms, headings, command refs, file refs, pattern names, keyword frequency | brainstorm |
| R4  | Auto-cluster artifacts into topics by keyword co-occurrence        | brainstorm  |
| R5  | Topic clustering algorithm must be pluggable (swappable module)    | brainstorm  |
| R6  | Detect relationships from explicit frontmatter (`brainstorm:`, `plan:`, `parent-review:`) | brainstorm |
| R7  | Infer edges from naming conventions (same date+slug across dirs)   | brainstorm  |
| R8  | Infer `implements` edges from roadmap feature ID keyword match     | brainstorm  |
| R9  | Support full edge type set: `decided_from`, `reviews`, `verifies`, `implements`, `resolves`, `supersedes`, `references` | brainstorm |
| R10 | Generate multi-file BRAIN output with 20K token cap per file       | brainstorm  |
| R11 | `BRAIN.md` is meta-index routing agents to topic-partitioned sub-files | brainstorm |
| R12 | `BRAIN-log.md` is chronological log (all artifacts by date, newest first) | brainstorm |
| R13 | `brain-index.json` is machine-readable structured output (entities, topics, edges) | brainstorm |
| R14 | Replaces `DIGEST.md` and `search-index.json` (supersedes legacy outputs) | brainstorm |
| R15 | Stdlib-only Python 3.8+, cross-platform (Windows + macOS)         | brainstorm  |
| R16 | Full rebuild under 2 seconds for ~200 documents                   | brainstorm  |
| R17 | Superseded/abandoned artifacts included with status markers (not pruned) | brainstorm |
| R18 | Modular architecture: scanner, extractor, clusterer, edge_detector, renderer | brainstorm |

## Phase 1: Core Engine (scanner + extractor + clusterer + edge detector)

### 1. Create `scripts/brain/` package structure and pytest infrastructure

- **Requirements**: R18, R15
- **Files**: `scripts/brain/__init__.py`, `scripts/brain/utils.py`, `scripts/conftest.py`, `scripts/brain/tests/__init__.py`
- **Details**:
  - Create `scripts/brain/` directory with `__init__.py`
  - `__init__.py` exports version `__version__ = "0.2.0"` and a `build_brain(root: Path) -> BrainData` orchestrator function
  - Define `BrainData` dataclass: holds entities, topics, edges, and metadata
  - Define `Entity` dataclass: `path`, `entity_type` (solution/plan/brainstorm/review/strategy/feature), `frontmatter`, `keywords`, `summary`
  - Define `Topic` dataclass: `slug`, `label`, `keywords`, `entity_paths`
  - Define `Edge` dataclass: `source`, `target`, `edge_type`
  - Create `scripts/brain/utils.py`: promote `parse_frontmatter()`, `_write_atomic()`,
    `extract_summary()`, and `_coerce()` from `cg_index.py` into this shared module.
    `cg_index.py` imports from `brain.utils` (backward-compat: legacy mode still works).
    This decouples the brain package from importing the CLI script directly.
  - **Null handling in `_coerce()`** [P1.2 fix]: Add null/tilde detection — return
    `None` for values matching `^(null|~|none)$` (case-insensitive). This prevents
    YAML `brainstorm: ~` and `brainstorm: null` from being treated as path strings.
  - Create `scripts/conftest.py`: inserts `scripts/` into `sys.path` so pytest
    discovers the `brain` package when run from the repo root.
  - Create `scripts/brain/tests/__init__.py` (test package marker).
  - **Pytest invocation**: `python -m pytest scripts/brain/tests/ -v` from repo root.
    No `requirements-dev.txt` needed — pytest is assumed available in the dev
    Python environment (same as the existing Python 3.8+ requirement).
  - Document in `scripts/brain/tests/README.md`: how to run tests, fixture patterns.
- **Test Scenarios**:
  - ✅ Package imports correctly: `python -m pytest scripts/brain/tests/` from repo root
  - ✅ Dataclasses instantiate with required fields
  - ✅ `_coerce("null")` returns `None`; `_coerce("~")` returns `None`
  - ✅ `parse_frontmatter` importable from `brain.utils`
- **Tests**: Unit test for imports, dataclass construction, and null coercion
- **Acceptance criteria**: `python -m pytest scripts/brain/tests/test_init.py -v` passes from repo root

### 2. Implement `scripts/brain/scanner.py` — full-scope entity scanner

- **Requirements**: R1, R2, R15, R17
- **Files**: `scripts/brain/scanner.py`
- **Details**:
  - `scan_all(root: Path) -> List[Entity]` — main entry point
  - Scan directories: all use recursive glob (`rglob("*.md")`) to handle
    potential future subdirectories consistently:
    `solutions/**/*.md`, `plans/**/*.md`, `brainstorms/**/*.md`,
    `reviews/**/*.md`, `strategy/**/*.md` (all under `.cg-docs/`)
  - Import `parse_frontmatter()` from `brain.utils` (promoted in Step 1)
  - For each markdown file: parse frontmatter, extract entity type from
    parent directory, compute relative path
  - `scan_roadmap(root: Path) -> List[Entity]` — parse `roadmap.json`,
    create one Entity per feature (entity_type="feature", path=virtual
    `roadmap.json#<feature-id>`, frontmatter synthesized from JSON fields)
  - Include all statuses (active, superseded, abandoned) — mark in entity
  - Skip non-`.md` files (e.g., `.gitkeep`)
  - Warn on parse failures (missing frontmatter), don't abort
- **Test Scenarios**:
  - ✅ Scans all 5 subdirectories + roadmap features
  - ✅ Entities have correct `entity_type` based on parent dir
  - 🛑 File with no frontmatter: warning emitted, file skipped
  - 🛑 `roadmap.json` missing: features list empty, no error
  - 🛑 `.gitkeep` files ignored
  - ❌ `.cg-docs/` missing: returns empty list with warning
- **Tests**: Fixture-based tests with temp directories containing sample files
- **Acceptance criteria**: Returns correct entity count from a fixture tree with all 6 entity types

### 3. Implement `scripts/brain/extractor.py` — deep content extraction

- **Requirements**: R3, R15
- **Files**: `scripts/brain/extractor.py`
- **Details**:
  - `extract_keywords(entity: Entity, text: str) -> List[str]` — main entry
  - Extraction signals (each as a private helper):
    - `_extract_backtick_terms(text)` — regex for `` `...` `` (single backtick only, not code fences)
    - `_extract_headings(text)` — regex for `^#{1,6}\s+(.*)` lines
    - `_extract_command_refs(text)` — regex for `/cg-\w+` and `cg-\w+` patterns
    - `_extract_file_refs(text)` — regex for `\w+\.(py|ps1|sh|md|json|R|do|ado)` patterns
    - `_extract_pattern_names(text)` — regex for quoted or title-cased multi-word phrases
    - `_extract_frequency_keywords(text)` — word frequency after stopword removal, top N
  - Stopword list: hardcoded English stopwords (~150 words) + markdown syntax words (`the`, `is`, `a`, `to`, `and`, `of`, `in`, `for`, `this`, `that`, `with`, `from`, `are`, `was`, `be`, etc.)
  - Keyword normalization: lowercase, strip punctuation, deduplicate
  - Weight signals: backtick terms and heading words scored 3x, command/file refs 2x, frequency keywords 1x
  - Output: sorted list of (keyword, weight) tuples, stored on Entity
  - For roadmap features (no body text): extract keywords from title + description fields
- **Test Scenarios**:
  - ✅ Backtick terms extracted: `` `Invoke-Pester` `` → `invoke-pester`
  - ✅ Headings extracted: `## Problem Statement` → `problem`, `statement`
  - ✅ Command refs: `/cg-brainstorm` → `cg-brainstorm`
  - ✅ File refs: `cg_index.py` → `cg_index.py`
  - 🛑 Code fences (triple backtick) not treated as terms
  - 🛑 Very short words (≤2 chars) excluded from frequency keywords
  - ❌ Empty text: returns empty keyword list
- **Tests**: Unit tests with sample markdown snippets
- **Acceptance criteria**: Given a real solution file, produces ≥10 meaningful keywords including backtick terms and heading words

### 4. Implement `scripts/brain/clusterer.py` — topic extraction

- **Requirements**: R4, R5, R15
- **Files**: `scripts/brain/clusterer.py`
- **Details**:
  - `cluster_topics(entities: List[Entity], min_cluster_size: int = 3) -> List[Topic]` — main entry
  - Algorithm (pluggable — encapsulated in a `ClusterStrategy` protocol):
    1. Build keyword-to-entity mapping (inverted index)
    2. For each pair of entities: compute keyword overlap score (weighted Jaccard)
    3. Greedy agglomerative clustering: start with highest-overlap pairs,
       merge into topics until overlap drops below threshold
    4. Label each topic: top 3 keywords by combined weight across constituent entities
    5. Assign a slug: `kebab-case` of the top 2-3 keywords
  - Minimum cluster size: configurable (default 3 entities)
  - Unclustered entities: assigned to a catch-all "misc" topic
  - `ClusterStrategy` protocol: any callable with signature
    `(entities: List[Entity]) -> List[Topic]` — enables future swap to
    TF-IDF or embedding-based clustering
  - **No topic deduplication in Batch A** — deferred to future clusterer
    upgrade (the pluggable strategy is the designed extension point for
    improving cluster quality) [P3.2 fix]
- **Test Scenarios**:
  - ✅ 5 entities sharing "pester", "powershell", "testing" → one topic
  - ✅ 2 unrelated entities → no cluster (under min_cluster_size), go to misc
  - ✅ Topic slug derived from top keywords
  - 🛑 Entity with no keywords: excluded from clustering, goes to misc
  - 🛑 All entities identical keywords: single topic containing all
  - ❌ Empty entity list: returns empty topic list
- **Tests**: Unit tests with synthetic entities having controlled keyword sets
- **Acceptance criteria**: Given 10 entities with 3 clear keyword clusters, produces 3 topics + 1 misc

### 5. Implement `scripts/brain/edge_detector.py` — relationship detection

- **Requirements**: R6, R7, R8, R9, R15
- **Files**: `scripts/brain/edge_detector.py`
- **Details**:
  - `detect_edges(entities: List[Entity], root: Path) -> List[Edge]`
  - **Null-guard** [P1.2 fix]: Before processing any relationship field, check
    `if value is None or value in ("", "null", "~", "none"): skip`. This
    handles the 6+ plan files in the real corpus that use `brainstorm: ~` or
    `brainstorm: null`. The `_coerce()` fix in Step 1 returns `None` for these
    values; this guard is defense-in-depth.
  - **Explicit edges** (from frontmatter):
    - `brainstorm:` field in plans → `decided_from` edge
    - `plan:` field in reviews → `reviews` edge
    - `parent-review:` field in verify reviews → `verifies` edge
    - `plan:`/`brainstorm:` in solutions → `references` edge
  - **Inferred edges** (name-based):
    - Same date+slug (e.g., `2026-05-15-wiki` in both `brainstorms/` and
      `plans/`) → `decided_from` edge (plan → brainstorm)
    - Same date+slug across `plans/` and `reviews/` → `reviews` edge
  - **Roadmap edges** [P1.3 fix]: Use minimum Jaccard coefficient (≥0.4)
    between plan slug tokens and feature ID tokens (after splitting on `-`
    and filtering out stopwords: "cg", "and", "the", "for", "in"). Jaccard =
    |intersection| / |union|. This replaces the flawed "3+ token overlap"
    rule — it handles variable-length IDs correctly and avoids false positives
    from short common words.
  - **Future-ready**: `resolves` and `supersedes` edges parsed from
    frontmatter if present (fields don't exist today but engine is ready)
  - Edge deduplication: same source+target+type = one edge
- **Test Scenarios**:
  - ✅ Plan with `brainstorm: ".cg-docs/brainstorms/foo.md"` → `decided_from` edge
  - ✅ Plan with `brainstorm: ~` or `brainstorm: null` → no edge produced (null-guard)
  - ✅ Same-slug inference: `plans/2026-05-15-wiki.md` + `brainstorms/2026-05-15-wiki.md` → edge
  - ✅ Roadmap match: plan slug `auto-generated-project-wiki` vs feature `wiki-auto-generation`
    → tokens after stopword filter: {"auto","generated","project","wiki"} vs {"wiki","auto","generation"}
    → intersection={"auto","wiki"}, union={"auto","generated","project","wiki","generation"}
    → Jaccard=2/5=0.4 → meets threshold → `implements` edge
  - 🛑 Self-referencing path: ignored (no self-edges)
  - 🛑 Target path doesn't resolve to an entity: edge created with `target_missing=True` marker
  - ❌ No frontmatter reference fields: only inferred edges produced
- **Tests**: Fixture entities with known frontmatter fields + naming patterns
- **Acceptance criteria**: Given a plan with explicit `brainstorm:` field and a naming match, produces both explicit and inferred edges without duplicates

## Phase 2: Output Generation + CLI Integration

### 6. Implement `scripts/brain/renderer.py` — multi-file output

- **Requirements**: R10, R11, R12, R13, R14, R16, R17
- **Files**: `scripts/brain/renderer.py`
- **Details**:
  - `render_brain(data: BrainData, out_dir: Path, token_cap: int = 20000) -> List[Path]`
  - **Token estimation** [P3.3 fix]: count words × 1.6 (conservative ratio for
    code-heavy markdown with backtick terms, YAML, and command names). If
    estimated tokens for a generated file exceed the cap by >10%, emit a
    warning in the file header: `<!-- WARNING: estimated ~N tokens, exceeds cap -->`
  - **BRAIN.md** (meta-index):
    - Header with generation date, entity count, topic count, edge count
    - Topic directory: for each topic → slug, label, artifact count, file reference
    - If all topics fit under cap: include full topic detail inline
    - If over cap: topic summaries only, with `→ See BRAIN-01.md` pointers
  - **BRAIN-NN.md** (topic-partitioned sub-files):
    - Created only when corpus exceeds single-file cap
    - Each sub-file: one or more topics with full artifact listings
    - Packing: fill each file up to cap, splitting at topic boundaries
    - **Oversized topic rule** [P2.2 fix]: When a single topic exceeds the
      token cap, split at entity boundaries within that topic. Add a
      continuation header in the next file: `### <topic-label> (continued from BRAIN-NN.md)`.
      The meta-index lists both files for that topic.
    - Cross-references: each sub-file header lists other sub-files and their topics
  - **BRAIN-log.md** (chronological):
    - All entities sorted by date descending
    - Format: `YYYY-MM-DD | type | title | path | topic-slug`
    - Always a single file (log entries are one-liners, very compact)
  - **brain-index.json** (machine-readable):
    - Schema: `{ schemaVersion, generated, entities: [...], topics: [...], edges: [...] }`
    - Entities: slug, title, date, entity_type, status, tags, keywords (top 10), path
    - Topics: slug, label, keywords, entity_paths
    - Edges: source_path, target_path, edge_type
  - All writes use `_write_atomic` pattern (from `brain.utils`)
  - **Does NOT delete legacy files** [P2.1 fix] — legacy cleanup is the
    caller's responsibility (see Step 7). The renderer only creates new files.
- **Test Scenarios**:
  - ✅ Small corpus (< 20K tokens): single BRAIN.md with inline topics
  - ✅ Large corpus (> 20K tokens): BRAIN.md + BRAIN-01.md + BRAIN-02.md
  - ✅ Oversized topic: split at entity boundary with continuation header
  - ✅ BRAIN-log.md sorted newest-first
  - ✅ brain-index.json valid JSON with all three sections
  - 🛑 Token estimate exceeds cap by >10%: warning comment in file header
  - 🛑 Zero entities: produces minimal BRAIN.md with "no artifacts found" message
  - ❌ Unwritable output dir: raises OSError (caught by CLI)
- **Tests**: Generate from fixture data, verify file count, JSON validity, token estimates
- **Acceptance criteria**: Given 20 fixture entities across 3 topics, produces valid BRAIN.md (with topic index), BRAIN-log.md, and brain-index.json

### 7. CLI integration — new `--brain` flag and legacy deprecation

- **Requirements**: R14, R15, R18
- **Files**: `scripts/cg_index.py`
- **Details**:
  - Add `--brain` flag: runs the full brain pipeline (scan → extract → cluster → detect edges → render)
  - **`--all` behavior change** [P2.4 fix]: After this change, `--all` means
    `--brain` only (not `--brain + --index + --digest`). The `--all` flag gets
    the same deprecation warning as `--index`/`--digest`:
    `[cg-index] WARNING: --all is deprecated. Use --brain (now the default).`
    This matches the brainstorm decision that BRAIN replaces both legacy outputs.
  - Deprecate `--index` and `--digest`: still work but print
    `[cg-index] WARNING: --index/--digest are deprecated. Use --brain.`
    and produce legacy output for backward compat
  - `--brain` is the new default when no mode flag is given
  - Import from `brain` package: `from brain import build_brain`
  - Pass `--root` through to `build_brain(root)`
  - Version bump: `__version__ = "0.2.0"`
  - Exit codes unchanged: 0 success, 1 fatal error
  - **Legacy cleanup** [P2.1 fix]: Delete `DIGEST.md` and `search-index.json`
    ONLY after `render_brain()` returns successfully (all BRAIN files written).
    Sequenced in `main()` as: (1) call `build_brain()`, (2) call `render_brain()`,
    (3) if no exception: delete legacy files. If render fails, legacy files
    remain intact.
- **Test Scenarios**:
  - ✅ `cg-index --brain --root <fixture>` produces BRAIN.md + brain-index.json + BRAIN-log.md
  - ✅ `cg-index` (no flags) defaults to `--brain`
  - ✅ `cg-index --all` prints deprecation warning + runs brain pipeline
  - ✅ `cg-index --digest` prints deprecation warning + produces DIGEST.md
  - ✅ `cg-index --version` prints `0.2.0`
  - ✅ Legacy files deleted ONLY after successful brain generation
  - 🛑 Render fails mid-write: legacy DIGEST.md/search-index.json preserved
  - 🛑 `.cg-docs/` missing: exit 1 with error message
  - ❌ Import error (brain package not found): clear error message
- **Tests**: Subprocess invocation tests (matching existing `cg-index.Tests.ps1` pattern)
- **Acceptance criteria**: `cg-index --brain --root .` from project root produces all 3+ brain files

### 8. Update bin wrappers and install scripts

- **Requirements**: R15
- **Files**: `bin/cg-index`, `bin/cg-index.cmd`
- **Details**:
  - No changes needed to wrappers (they already pass all args through to `cg_index.py`)
  - Verify wrappers still work with new `--brain` flag
  - No new bin commands needed (same `cg-index` entry point)
  - `install.ps1` and `install.sh` unchanged (no new deps)
- **Test Scenarios**:
  - ✅ `cg-index --brain` via bin wrapper works on Windows
  - ✅ `cg-index --brain` via bin wrapper works on macOS/bash
- **Tests**: Existing parity tests cover wrapper structure
- **Acceptance criteria**: `cg-index --brain` works via both `bin/cg-index.cmd` and `bin/cg-index`

## Testing Strategy

- **Unit tests** (pytest): `scripts/brain/tests/` — one test module per brain
  module (test_scanner.py, test_extractor.py, test_clusterer.py,
  test_edge_detector.py, test_renderer.py). Fixture-based, no external deps
  beyond pytest itself.
- **Pytest infrastructure**: `scripts/conftest.py` adds `scripts/` to `sys.path`.
  Invocation: `python -m pytest scripts/brain/tests/ -v` from repo root.
  Pytest is assumed available in the dev Python environment (not pip-installed
  by the project — same as Python 3.8+ being a prerequisite).
- **Integration tests**: Pester tests in `tests/cg-index.Tests.ps1` for CLI
  behavior (subprocess invocation pattern, matching existing test structure).
  New Describe block for `--brain` mode.
- **Fixture data**: Self-contained temp directory trees with sample markdown
  files covering all entity types. Include fixtures with `brainstorm: null`
  and `brainstorm: ~` to verify null-guard (P1.2 regression).
- **Performance assertion**: Full brain build on real `.cg-docs/` completes
  under 2 seconds (wall-clock assertion in integration test)

## Documentation Checklist

- [ ] Module docstrings for all `scripts/brain/*.py` files
- [ ] Function docstrings with parameters, returns, examples
- [ ] `--brain` flag documented in `cg_index.py` module docstring
- [ ] `docs/reference.md` updated with new `cg-index --brain` usage
- [ ] Inline comments for clustering algorithm and token estimation logic

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Topic quality too coarse without NLP | Medium | Medium | Pluggable clusterer — swap algorithm later without pipeline changes |
| 20K token cap too small for meta-index | Low | Low | Cap is configurable; `words × 1.6` conservative ratio; runtime warning on overflow |
| Keyword extraction too noisy (false positives) | Medium | Medium | Weighted scoring; backtick terms >> frequency words; tunable threshold |
| Legacy output removal breaks downstream | Low | High | Deletion sequenced AFTER successful render in `main()`; render failure preserves legacy files |
| YAML null/tilde in frontmatter fields | Confirmed | Medium | `_coerce()` returns None for null/~/none; null-guard in edge detector |
| Oversized topic exceeds file cap | Low | Low | Split at entity boundary with continuation header; warning comment in file |

## Out of Scope

- NLP library dependencies (deferred to future batch with venv infrastructure)
- `/cg-brain-rebuild` command (Batch B)
- Auto-rebuild on `/cg-compound` (Batch B)
- Prompt integration / "Consult Brain" step (Batch C)
- `cg-skill-brain-query` (Batch C)
- Team brain / cross-project sharing (Batch D)
- Vector embeddings or semantic search
- Manual topic curation UI
