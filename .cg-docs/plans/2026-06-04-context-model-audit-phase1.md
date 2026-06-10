---
date: 2026-06-04
title: "Context and model-governance audit — Phase 1 inventory"
status: planned
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-06-04-context-model-audit-infrastructure.md"
language: "python"
estimated-effort: "medium"
tags: [performance, tokens, model-governance, audit, cost-efficiency, codex]
phases: 3
---

# Plan: Context and Model-Governance Audit — Phase 1 Inventory

## Objective

Build `scripts/cg_audit_context.py` — a stdlib-only Python script that
inventories all context-contributing files in Compound GPID, estimates token
burden using `chars / 4`, counts inter-file references, inventories model
declarations, detects duplicates, and classifies optimization candidates
against predefined thresholds. Outputs both JSON and Markdown reports to
`.cg-docs/cost/`.

## Context

- Roadmap milestone: `token-optimization-model-governance`
- Roadmap feature: `token-audit-context-model`
- Prior art: `cg_index.py` (stdlib-only, argparse, pathlib, same project)
- Implementation harness: **Codex**
- Validation harness: **VS Code Copilot**

## Requirements

| ID  | Requirement | Source |
|-----|-------------|--------|
| R1  | Script at `scripts/cg_audit_context.py` | brainstorm |
| R2  | Python 3.8+, stdlib only, no third-party packages | project convention |
| R3  | Argparse CLI: `--root <path>`, `--output-dir <path>`, `--format json|md|both` | design |
| R4  | Default root: parent of `scripts/` directory | cg_index.py pattern |
| R5  | Default output-dir: `.cg-docs/cost/` | brainstorm |
| R6  | Token estimation: `characters / 4` | brainstorm decision |
| R7  | Scan categories: prompts, agents, skills, instructions, shared, docs, brain, context | brainstorm |
| R8  | Prompt reference matrix: count file refs, agent refs, skill refs, tool mentions, load verbs | brainstorm |
| R9  | Model inventory: parse frontmatter `model:` field from prompts and agents | brainstorm |
| R10 | Cross-reference model declarations against `docs/model-guide.md` table | brainstorm |
| R11 | Duplicate detection: find paragraph blocks (4+ lines) appearing in 3+ files | brainstorm |
| R12 | Threshold classification: immediate / needs-review / acceptable | brainstorm |
| R13 | JSON output: `.cg-docs/cost/context-audit.json` | brainstorm |
| R14 | Markdown output: `.cg-docs/cost/context-audit.md` | brainstorm |
| R15 | Report header states heuristic disclaimer | brainstorm |
| R16 | Exit code 0 on success, 1 on fatal error, 2 on missing root | convention |
| R17 | Reuse `brain.utils.parse_frontmatter()` for YAML parsing | existing utility |
| R18 | Tests in `scripts/tests/test_audit_context.py` using pytest | project convention |

## File Inventory

### Files to create

| File | Purpose |
|------|---------|
| `scripts/cg_audit_context.py` | Main audit script |
| `scripts/tests/__init__.py` | Package marker (if not exists) |
| `scripts/tests/test_audit_context.py` | Pytest test suite |
| `.cg-docs/cost/.gitkeep` | Ensure output directory is committed |

### Files to modify

None. This is additive only.

### Files generated at runtime (gitignored)

| File | Purpose |
|------|---------|
| `.cg-docs/cost/context-audit.json` | Machine-readable audit report |
| `.cg-docs/cost/context-audit.md` | Human-readable audit report |

---

## Phase 1: Core Audit Engine

### 1.1 Script skeleton and CLI

- **Requirements**: R1, R2, R3, R4, R5, R16
- **File**: `scripts/cg_audit_context.py`
- **Details**:
  - Docstring with usage, description, exit codes (match `cg_index.py` style)
  - `argparse` CLI with `--root`, `--output-dir`, `--format`
  - `sys.path` bootstrap for `brain.utils` import (same pattern as `cg_index.py`)
  - `main()` function, `if __name__ == "__main__"` guard
  - Root validation: if `.github/prompts/` doesn't exist under root, exit 2

### 1.2 File scanner and size inventory

- **Requirements**: R6, R7
- **File**: `scripts/cg_audit_context.py`
- **Details**:
  - Define scan categories as a dict of `{category_name: glob_pattern}`:
    ```python
    SCAN_CATEGORIES = {
        "prompts": ".github/prompts/**/*.prompt.md",
        "agents": ".github/agents/**/*.agent.md",
        "skills": ".github/skills/**/SKILL.md",
        "instructions": ".github/instructions/**/*.instructions.md",
        "shared": ".github/shared/**/*",
        "template": ".github/copilot-instructions.template.md",
        "docs": "docs/**/*.md",
        "brain": ".cg-docs/BRAIN*.md",
        "brain_index": ".cg-docs/brain-index.json",
        "context": "compound-gpid.context.md",
        "roadmap": "roadmap.json",
    }
    ```
  - For each file: read content, compute `len(content)` characters and
    `len(content) // 4` estimated tokens
  - Build per-file records: `{path, category, characters, estimated_tokens}`
  - Aggregate category totals

### 1.3 Frontmatter model extraction

- **Requirements**: R9, R10, R17
- **File**: `scripts/cg_audit_context.py`
- **Details**:
  - Import `parse_frontmatter` from `brain.utils`
  - For every prompt and agent file: extract `model:` field from frontmatter
  - Build model inventory: `{path, category, model, model_tier}`
  - Tier classification: map known model strings to `{premium, standard, economy}`:
    - Premium: contains "Opus"
    - Standard: contains "Sonnet"
    - Economy: contains "Haiku"
    - Missing: no `model:` field
  - Cross-reference against `docs/model-guide.md`:
    - Parse the two tables (Prompts / Agents) for declared model per file
    - Flag any file where frontmatter model ≠ model-guide declaration (drift)

### 1.4 Reference counting (Prompt Reference Matrix)

- **Requirements**: R8
- **File**: `scripts/cg_audit_context.py`
- **Details**:
  - For each prompt and agent file, count occurrences of:
    - **File references**: regex for known filenames (`compound-gpid.md`,
      `roadmap.json`, `BRAIN.md`, `brain-index.json`, `context.md`,
      `model-guide.md`, `copilot-instructions`)
    - **Agent references**: regex `@cg-[a-z-]+`
    - **Skill references**: regex `cg-skill-[a-z-]+`
    - **Tool mentions**: regex for `read_file|edit_file|run_in_terminal|
      grep_search|semantic_search`
    - **Load verbs**: regex `must read|load .+skill|consult|dispatch`
  - Build per-file reference record:
    `{path, file_refs: int, agent_refs: int, skill_refs: int, tool_refs: int, load_verbs: int, total_refs: int}`
  - Sort by `total_refs` descending

### 1.5 Duplicate paragraph detection

- **Requirements**: R11
- **File**: `scripts/cg_audit_context.py`
- **Details**:
  - Split each scanned file into paragraph blocks (separated by blank lines)
  - Filter to blocks with 4+ non-empty lines
  - Hash each block (normalize whitespace first)
  - Find hashes appearing in 3+ distinct files
  - Report: `{block_preview (first 80 chars), file_count, total_chars, files[]}`

---

## Phase 2: Threshold Classification and Report Generation

### 2.1 Threshold classifier

- **Requirements**: R12
- **File**: `scripts/cg_audit_context.py`
- **Details**:
  - Define thresholds as constants:
    ```python
    THRESHOLD_INSTRUCTION_IMMEDIATE = 1500
    THRESHOLD_INSTRUCTION_CRITICAL = 3000
    THRESHOLD_PROMPT_IMMEDIATE = 3000
    THRESHOLD_PROMPT_REVIEW = 1500
    THRESHOLD_AGENT_REVIEW = 1500
    THRESHOLD_SKILL_IMMEDIATE = 2000
    THRESHOLD_SKILL_REVIEW = 1200
    THRESHOLD_REFS_IMMEDIATE = 5
    THRESHOLD_DUPLICATE_FILES = 3
    THRESHOLD_DUPLICATE_TOKENS = 1000
    ```
  - Classify each file into: `immediate`, `needs-review`, `acceptable`
  - Apply additional rules:
    - Premium model without escalation condition → immediate
    - Agent with broad tools + premium model → immediate
    - Missing model in high-ref prompt (total_refs ≥ 3) → needs-review
    - Model drift (frontmatter ≠ model-guide) → needs-review

### 2.2 JSON output

- **Requirements**: R13, R15
- **File**: `scripts/cg_audit_context.py`
- **Details**:
  - Output structure:
    ```json
    {
      "generated": "2026-06-04T...",
      "disclaimer": "Token estimates are heuristic (chars/4)...",
      "summary": {
        "total_files": int,
        "total_characters": int,
        "total_estimated_tokens": int,
        "by_category": {...}
      },
      "files": [...],
      "reference_matrix": [...],
      "model_inventory": {
        "declarations": [...],
        "missing": [...],
        "drift": [...],
        "premium_usage": [...]
      },
      "duplicates": [...],
      "optimization_candidates": {
        "immediate": [...],
        "needs_review": [...],
        "acceptable_count": int
      }
    }
    ```
  - Write to `{output_dir}/context-audit.json` with `json.dump(indent=2)`

### 2.3 Markdown output

- **Requirements**: R14, R15
- **File**: `scripts/cg_audit_context.py`
- **Details**:
  - Header with disclaimer and generation timestamp
  - Sections:
    1. **Summary** — total files, total tokens, by-category table
    2. **Top 15 Largest Files** — sorted table
    3. **Prompt Reference Matrix** — table with ref counts per prompt/agent
    4. **Model Inventory** — table of all model declarations
    5. **Missing Model Declarations** — list
    6. **Model Drift** — frontmatter vs model-guide mismatches
    7. **Premium Model Usage** — list with escalation-condition check
    8. **Duplicate Paragraphs** — table with preview and file count
    9. **Immediate Optimization Candidates** — classified list with reasons
    10. **Needs Review** — classified list
  - Write to `{output_dir}/context-audit.md`

---

## Phase 3: Tests and Validation

### 3.1 Unit tests

- **Requirements**: R18
- **File**: `scripts/tests/test_audit_context.py`
- **Details**:
  - Test structure mirrors `scripts/brain/tests/test_scanner.py`
  - Run command: `python -m pytest scripts/tests/test_audit_context.py -v`
  - Test classes:

  **TestTokenEstimation**:
  - `test_empty_file_zero_tokens` — empty string → 0
  - `test_known_length` — 400 chars → 100 tokens
  - `test_unicode_chars_counted` — multi-byte chars counted by char not byte

  **TestFileScanner**:
  - `test_finds_prompt_files` — create temp `.github/prompts/x.prompt.md` → found
  - `test_finds_agent_files` — create temp `.github/agents/x.agent.md` → found
  - `test_categorizes_correctly` — each category maps to correct glob
  - `test_missing_category_dir_no_error` — missing `.github/shared/` → empty list

  **TestModelExtraction**:
  - `test_extracts_model_from_frontmatter` — `model: "Claude Sonnet 4.6"` → extracted
  - `test_missing_model_field` — no model in frontmatter → flagged missing
  - `test_tier_classification` — Opus→premium, Sonnet→standard, Haiku→economy

  **TestReferenceCounting**:
  - `test_counts_agent_refs` — `@cg-roadmap` in content → agent_refs=1
  - `test_counts_skill_refs` — `cg-skill-brain-query` → skill_refs=1
  - `test_counts_file_refs` — `compound-gpid.md` → file_refs=1
  - `test_multiple_refs_summed` — multiple refs → total correct

  **TestDuplicateDetection**:
  - `test_no_duplicates_under_threshold` — block in 2 files → not flagged
  - `test_duplicates_at_threshold` — block in 3 files → flagged
  - `test_short_blocks_ignored` — 3-line block in 5 files → not flagged

  **TestThresholdClassification**:
  - `test_large_instruction_immediate` — 7000 chars instruction → immediate
  - `test_medium_prompt_needs_review` — 4000 chars prompt → needs-review
  - `test_small_file_acceptable` — 2000 chars prompt → acceptable
  - `test_high_refs_immediate` — 6 total refs → immediate
  - `test_premium_no_escalation_immediate` — premium model → immediate

  **TestOutputFormats**:
  - `test_json_output_valid` — output parses as JSON, has required keys
  - `test_markdown_output_has_sections` — output contains expected headers
  - `test_disclaimer_present` — both outputs contain heuristic disclaimer

### 3.2 Integration test (Codex)

- **File**: `scripts/tests/test_audit_context.py`
- **Details**:
  - `TestIntegration::test_full_run_on_real_repo` — run the script against
    the actual repo root, assert JSON output is valid and contains >0 files
  - Mark with `@pytest.mark.integration` so unit tests can run without repo

### 3.3 Validation in VS Code (manual)

After Codex completes implementation:

1. Run from project root:
   ```powershell
   python scripts/cg_audit_context.py --root . --format both
   ```
2. Verify `.cg-docs/cost/context-audit.json` exists and parses cleanly
3. Verify `.cg-docs/cost/context-audit.md` is readable and contains all sections
4. Spot-check: largest prompt should be `/cg-work` or `/cg-plan`
5. Spot-check: model inventory should show 22 prompts + 17 agents = 39 entries
6. Spot-check: `cg-brainstorm.prompt.md` should show Opus (premium tier)
7. Spot-check: reference counts for `/cg-review` should be high (dispatches 10 agents)
8. Run pytest:
   ```powershell
   python -m pytest scripts/tests/test_audit_context.py -v
   ```

---

## Acceptance Criteria

| # | Criterion | Validation |
|---|-----------|------------|
| 1 | Script runs successfully on this repo | Exit code 0, JSON and MD outputs exist |
| 2 | Token estimates are `chars / 4` | Unit test + spot-check |
| 3 | All 7+ scan categories populated | JSON `summary.by_category` has entries |
| 4 | Model inventory covers all 39 prompt+agent files | Count check in JSON |
| 5 | Reference matrix shows top accumulators | Sorted by total_refs |
| 6 | Optimization candidates classified | `immediate` and `needs_review` lists non-empty |
| 7 | No third-party dependencies | Only stdlib imports |
| 8 | All pytest tests pass | `python -m pytest` exit 0 |
| 9 | Markdown report is human-readable | Manual review in VS Code |
| 10 | Duplicate detection finds known duplication | Pester Safety Rules block appears in 2+ files |

---

## Implementation Notes for Codex

- Follow `cg_index.py` patterns exactly: docstring, argparse, sys.path bootstrap,
  `brain.utils` import, `main()` entry point.
- Use `pathlib.Path.glob()` for file discovery. Handle missing directories gracefully.
- Use `brain.utils.parse_frontmatter()` — it returns a dict of frontmatter fields.
  It handles malformed frontmatter by returning an empty dict (not raising).
- For duplicate detection, use `hashlib.md5` on normalized paragraph text (strip
  leading/trailing whitespace per line, collapse multiple spaces).
- The script should be idempotent: running twice produces the same output.
- Keep the script under 500 lines. If it exceeds, split helpers into
  `scripts/audit/__init__.py` + modules (but only if necessary).
- Do NOT modify any existing files. This plan is purely additive.

---

## Roadmap Update

After implementation, update `roadmap.json`:
- Set `token-audit-context-model` status from `idea` to `done`
- Add `"plan": ".cg-docs/plans/2026-06-04-context-model-audit-phase1.md"`
