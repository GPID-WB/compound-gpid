---
plan: .cg-docs/plans/2026-05-19-knowledge-brain-engine-batch-a.md
reviewed-by: cg-review (thorough)
agents: [cg-code-quality, cg-testing, cg-documentation, cg-version-control, cg-reproducibility, cg-performance, cg-architecture, cg-data-quality, cg-learnings-researcher, cg-adversarial]
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P2.9: fixed
  P2.10: fixed
  P2.11: fixed
  P2.12: fixed
  P2.13: fixed
  P2.14: advisory
  P2.15: fixed
  P2.16: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: advisory
  P3.5: fixed
  P3.6: fixed
  P3.7: fixed
  P3.8: fixed
  P3.9: fixed
  P3.10: advisory
---

# Code Review — Knowledge Brain Engine (Batch A)

**Date**: 2026-05-19  
**Branch**: feat/knowledge-brain-engine (commits 11b67f8, 7b64a26, c9ba903)  
**Scope**: 19 changed files, +5,122/−275 lines  
**Depth**: thorough (cg-code-quality, cg-testing, cg-documentation, cg-version-control, cg-reproducibility, cg-performance, cg-architecture, cg-data-quality, cg-learnings-researcher, cg-adversarial)  
**Result**: 31 findings (P0: 0 | P1: 5 | P2: 16 | P3: 10)

---

## P0 — BLOCKING

_None._

---

## P1 — CRITICAL (must fix before merge)

### [P1.1] `scripts/brain/scanner.py`:99–101 — `UnicodeDecodeError` not caught in `scan_all()`
**Agents**: cg-data-quality, cg-adversarial, cg-learnings-researcher  
**Tag**: [safe_auto]

`read_text(encoding="utf-8")` raises `UnicodeDecodeError` (a `ValueError` subclass, NOT `OSError`) when any `.cg-docs/` file contains non-UTF-8 bytes (e.g. Windows-1252 em-dash `0x97`, Latin-1 characters from Word exports). The `except OSError` block does not catch it. The exception propagates through `build_brain()` → `main()`, whose outer `except OSError` also misses it — producing an unhandled traceback and exit code 1. A single bad file in any subdirectory disables the entire indexer for every team member. Past learnings (`pester-encoding.md`) document this exact encoding class in the project.

**Fix**:
```python
# scanner.py:100
except (OSError, UnicodeDecodeError) as exc:
```

Also apply the same fix in `cg_index.py:scan_solutions()` (same pattern, same risk).

---

### [P1.2] `scripts/brain/scanner.py`:~139 — `UnicodeDecodeError` not caught in `scan_roadmap()`
**Agent**: cg-data-quality  
**Tag**: [safe_auto]

Same root cause as P1.1. `roadmap_path.read_text(encoding="utf-8")` is wrapped in `except (OSError, json.JSONDecodeError)` — which does not cover `UnicodeDecodeError`. A `roadmap.json` accidentally saved as Latin-1 would crash the pipeline.

**Fix**:
```python
except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
```

---

### [P1.3] `scripts/brain/scanner.py`:114 — Absolute `Path` objects stored as `Entity.path`; BRAIN.md links non-functional, filesystem layout leaked into committed output
**Agents**: cg-adversarial, cg-reproducibility  
**Tag**: [safe_auto]

`root` is always `.resolve()`d (absolute) in `main()`. `cg_docs.rglob("*.md")` yields absolute paths. These are stored as `entity.path` and written verbatim by `_entity_line()` into every `BRAIN-NN.md` and by `_write_brain_json()` into `brain-index.json`. Committed output files contain machine-specific paths like `E:/PovcalNet/01.personal/wb384996/...` that are non-functional in any browser, editor, or GitHub viewer.

**Fix** — in `scan_all()`:
```python
# Change:
path=md_path,
# To:
path=md_path.relative_to(root),
```

The edge detector's `known_paths` construction already handles both absolute and relative paths via `.resolve()` comparison — no further changes needed in `edge_detector.py`.

---

### [P1.4] `scripts/brain/scanner.py`:149 — `AttributeError` when `roadmap.json` is valid JSON but not a dict
**Agent**: cg-data-quality  
**Tag**: [safe_auto]

`data.get("milestones", [])` is called **outside** the `try/except` block. If `roadmap.json` contains `null`, `[]`, or a bare string — all valid JSON — `json.loads()` succeeds but `data.get(...)` raises `AttributeError: 'NoneType' object has no attribute 'get'`, which also escapes the outer `except OSError` handler.

**Fix**: Insert after `data = json.loads(...)`:
```python
if not isinstance(data, dict):
    warnings.warn("[brain.scanner] roadmap.json is not a JSON object — skipping.", stacklevel=2)
    return []
```

---

### [P1.5] `scripts/brain/scanner.py`:~105 — `scan_all()` suppresses all `parse_frontmatter` warnings; violates "fail loudly" constraint
**Agent**: cg-data-quality  
**Tag**: [safe_auto]

The `with warnings.catch_warnings(): warnings.simplefilter("ignore")` block silently discards every diagnostic from `parse_frontmatter` and `extract_summary`, including malformed-frontmatter warnings. Files with corrupt or partial frontmatter are ingested silently with under-populated fields. This directly violates the "fail loudly, never silently" project standard.

**Fix**: Remove the `warnings.catch_warnings()` suppression block entirely. Warnings propagate naturally to the `warnings.catch_warnings(record=True)` wrapper in `cg_index.py::main()`, which already collects and prints them to stderr.

---

## P2 — IMPORTANT (should fix)

### [P2.1] `scripts/brain/renderer.py`:103 — Entity title containing `]` corrupts markdown link syntax
**Agent**: cg-data-quality  
**Tag**: [safe_auto]

`_entity_line()` renders `- **[{title}]({path_str})**`. If a solution title is `"Fix [P1] regression"`, the markdown parser closes the link text at the first `]`, producing broken link syntax in all output files.

**Fix**: `title = title.replace("]", "\\]")` before embedding.

---

### [P2.2] `scripts/brain/utils.py`:~160 — Inline YAML comments silently become part of string values
**Agent**: cg-data-quality  
**Tag**: [safe_auto]

The frontmatter parser does not strip YAML inline comments. `status: active # deprecated` stores `"active # deprecated"`. Downstream comparisons like `e.status in ("active", "")` silently fail.

**Fix**: After extracting `raw_value`:
```python
raw_value = raw_value.split(" #")[0].rstrip()
```

---

### [P2.3] `scripts/brain/utils.py`:~150 — Duplicate frontmatter keys silently overwrite each other
**Agent**: cg-data-quality  
**Tag**: [safe_auto]

`result[key] = ...` is assigned unconditionally. Two `date:` lines (common copy-paste error) silently discard the first value.

**Fix**: Before assigning:
```python
if key in result:
    warnings.warn(f"Duplicate frontmatter key '{key}'", stacklevel=2)
```

---

### [P2.4] `scripts/brain/renderer.py`:600–622 — `_build_topic_file_map()` approximation produces wrong BRAIN.md navigation links
**Agents**: cg-code-quality, cg-architecture, cg-testing  
**Tag**: [manual]

Topic-to-file assignment uses `i * n_files // max(len(topics), 1)` — an even count-based distribution. `_partition_and_write_topic_files()` uses token-based packing. When topics split across file boundaries due to token overflow, the navigation links in BRAIN.md point to the wrong `BRAIN-NN.md` file.

**Fix**: Have `_partition_and_write_topic_files()` return a `Dict[str, str]` mapping `topic.slug → filename` as it processes each topic, eliminating the approximation. See also [P2.12] which covers refactoring this function.

---

### [P2.5] `scripts/brain/tests/test_extractor.py`:79 — `test_heading_stopwords_excluded` contains no assertions
**Agent**: cg-testing  
**Tag**: [safe_auto]

Test body is `pass`. Heading-stopword filtering has no coverage despite appearing in the suite.

**Fix**:
```python
def test_heading_stopwords_excluded(self) -> None:
    scores = _kw_dict("## How To Use The File\n\n")
    for sw in ("how", "the", "use", "file"):
        assert scores.get(sw, 0) == 0, f"Stopword '{sw}' should not be boosted by heading signal"
```

---

### [P2.6] `scripts/brain/utils.py`:314 — `_write_atomic()` has zero unit tests
**Agent**: cg-testing  
**Tag**: [safe_auto]

Every renderer output path calls `_write_atomic`. The function uses `tempfile.NamedTemporaryFile` + `os.replace` — a pattern with known Windows-specific failure modes (temp on different volume). No test verifies correctness, idempotency, or content.

**Fix**: Add `TestWriteAtomic` class to `test_utils.py` (or `test_init.py`):
```python
class TestWriteAtomic:
    def test_creates_file(self, tmp_path):
        p = tmp_path / "out.md"
        _write_atomic(p, "hello")
        assert p.read_text(encoding="utf-8") == "hello"

    def test_overwrites_existing(self, tmp_path):
        p = tmp_path / "out.md"
        _write_atomic(p, "first")
        _write_atomic(p, "second")
        assert p.read_text(encoding="utf-8") == "second"
```

---

### [P2.7] `scripts/brain/utils.py`:223 — `extract_summary()` has no direct unit tests
**Agent**: cg-testing  
**Tag**: [safe_auto]

Existing scanner tests only assert `e.summary != ""`. The `## Problem`-first path, fenced-code-block skipping, and max-words truncation are all untested. A regression returning the full file body would not be caught.

**Fix**:
```python
class TestExtractSummary:
    def test_problem_section_preferred(self):
        text = "---\ntitle: X\n---\n## Overview\nOther stuff.\n## Problem\nThis is the fix.\n"
        assert "fix" in extract_summary(text)

    def test_falls_back_to_first_paragraph(self):
        text = "---\ntitle: X\n---\n\nFirst real paragraph here.\n"
        assert "paragraph" in extract_summary(text)

    def test_truncated_to_max_words(self):
        body = "word " * 200
        text = f"---\ntitle: X\n---\n\n{body}\n"
        assert len(extract_summary(text, max_words=50).split()) <= 51

    def test_skips_fenced_code(self):
        text = "---\ntitle: X\n---\n\n```python\nprint('skip')\n```\n\nReal summary.\n"
        assert "Real summary" in extract_summary(text)
        assert "print" not in extract_summary(text)
```

---

### [P2.8] `scripts/brain/__init__.py`:164 — `build_brain()` has no integration test
**Agent**: cg-testing  
**Tag**: [safe_auto]

Each sub-module is unit-tested in isolation, but `build_brain()` wires them together. Bugs in call order or argument plumbing are not caught.

**Fix**:
```python
class TestBuildBrainIntegration:
    def test_returns_brain_data(self, tmp_path):
        (tmp_path / ".cg-docs/solutions/bugs").mkdir(parents=True)
        (tmp_path / ".cg-docs/solutions/bugs/fix.md").write_text(
            "---\ntitle: My Fix\ndate: 2026-05-01\nstatus: active\n---\n\nFixed the crash.\n",
            encoding="utf-8",
        )
        data = build_brain(root=tmp_path)
        assert isinstance(data, BrainData)
        assert len(data.entities) == 1
        assert data.entities[0].entity_type == "solution"
        assert len(data.entities[0].keywords) > 0

    def test_empty_project_returns_empty_brain(self, tmp_path):
        data = build_brain(root=tmp_path)
        assert data.entities == []
        assert data.topics == []
        assert data.edges == []
```

---

### [P2.9] `scripts/brain/edge_detector.py`:~207 — Brainstorm entities produce `reviews` edges; semantically wrong
**Agent**: cg-testing  
**Tag**: [manual]

`entity.entity_type in ("review", "brainstorm")` causes brainstorms with a `plan:` frontmatter field to emit `reviews`-typed edges. A brainstorm does not *review* a plan — it precedes one. The module docstring edge table lists only `review → plan` as producing `reviews`. Latent: brainstorms rarely carry `plan:` today, but the bug will manifest silently.

**Fix**: Confirm intended edge type. If `references` is correct, change the condition path for `"brainstorm"` to emit `"references"`. Add a regression test.

---

### [P2.10] `scripts/brain/edge_detector.py`:254–259 — `_slug_tokens()` recomputed O(P×F) times in nested loop
**Agent**: cg-performance  
**Tag**: [safe_auto]

`_slug_tokens(feature.slug)` is recomputed inside a loop over all plans (outer) × all features (inner). At 50 plans × 100 features = 5,000 redundant regex split + set-construction operations.

**Fix**: Before the outer loop:
```python
feature_token_list = [(e, _slug_tokens(e.slug)) for e in features]
```

---

### [P2.11] `scripts/cg_index.py`:~155 — `scan_solutions()`, `build_index()`, `build_digest()` have incomplete docstrings
**Agent**: cg-documentation  
**Tag**: [safe_auto]

All three use freeform prose docstrings; missing `Args:`, `Returns:`, and `Example:` sections. Inconsistent with Google-style docstrings throughout the new `brain/` package.

---

### [P2.12] `scripts/brain/renderer.py`:170–285 — `_partition_and_write_topic_files()` is 115 lines with three distinct concerns
**Agents**: cg-code-quality  
**Tag**: [manual]

(1) Fitting topics to token-budget pages, (2) splitting oversized topics at entity boundaries, (3) flushing page buffers to disk files. Split paths are hard to test in isolation. Also the root cause of [P2.4].

**Fix**: Extract `_split_oversized_topic(topic, budget) → List[Topic]` and `_flush_pages_to_files(pages, out_dir) → Dict[str, str]`. The refactoring resolves P2.4 naturally by having `_flush_pages_to_files` return the `{topic_slug → filename}` map.

---

### [P2.13] `scripts/brain/renderer.py`:352 — Misleading comment: `# Negate date string for descending sort`
**Agent**: cg-code-quality  
**Tag**: [safe_auto]

No negation occurs. The comment actively misleads readers. `reverse=True` in the `sorted()` call achieves descending order.

**Fix**: Replace with: `# sentinel "0000-00-00" pushes empty dates to the end; reverse=True gives newest-first`

---

### [P2.14] `scripts/brain/__init__.py`:161 — Lazy sub-module imports inside `build_brain()` body should be module-level
**Agent**: cg-architecture  
**Tag**: [advisory]

Guard comment says these were lazy for incremental development. All five sub-modules now exist. Lazy imports hide `ImportError` until call time and break static analysis.

**Fix**: Move all `from brain.X import Y` calls to the module top-level import block.

---

### [P2.15] `scripts/brain/__init__.py`:18 — Module docstring ASCII art shows `render_brain()` nested inside `build_brain()`; incorrect
**Agent**: cg-architecture  
**Tag**: [manual]

`build_brain()` returns `BrainData`. `cg_index.py` calls `render_brain()` separately. The diagram implies they are coupled, which will confuse Batch B/C/D contributors.

**Fix**: Update ASCII art to show two sibling calls from `cg_index.py --brain` handler.

---

### [P2.16] `scripts/brain/__init__.py`:212 — `date.today()` hardcoded; prevents reproducibility testing
**Agent**: cg-reproducibility  
**Tag**: [safe_auto]

Running the indexer on identical inputs on different calendar days produces different output. Any snapshot or diff-based CI check fails. Tests cannot inject a known date.

**Fix**:
```python
def build_brain(root: Path, generated: str = "") -> BrainData:
    ...
    return BrainData(..., generated=generated or date.today().isoformat())
```

---

## P3 — MINOR

### [P3.1] `scripts/brain/renderer.py`:89 — Magic numbers `120`/`117` for summary truncation
**Agent**: cg-code-quality | **Tag**: [safe_auto]  
**Fix**: `_SUMMARY_MAX_CHARS: int = 120`; use the constant.

### [P3.2] `scripts/brain/utils.py`:76 — Backslash continuation unnecessary inside parentheses
**Agent**: cg-code-quality | **Tag**: [safe_auto]  
**Fix**: Remove backslash; Python continues implicitly.

### [P3.3] `scripts/brain/extractor.py`:48, `edge_detector.py`:42,88 — `frozenset` annotations missing element type
**Agent**: cg-code-quality | **Tag**: [safe_auto]  
**Fix**: `from typing import FrozenSet`; annotate as `FrozenSet[str]`.

### [P3.4] `scripts/brain/utils.py`:344 — `_write_atomic` leading underscore misleading for cross-module shared function
**Agent**: cg-code-quality | **Tag**: [advisory]  
**Fix**: Rename to `write_atomic`; update import sites.

### [P3.5] `scripts/cg_index.py`:378 — `w.message` implicit `str()` coercion in f-string
**Agent**: cg-code-quality | **Tag**: [safe_auto]  
**Fix**: `{w.message!s}` or `str(w.message)`.

### [P3.6] `scripts/brain/scanner.py`:130 — Roadmap features with no `id` silently skipped without warning
**Agent**: cg-code-quality | **Tag**: [safe_auto]  
**Fix**: `warnings.warn(f"[brain.scanner] roadmap feature in milestone '{m_title}' has no 'id'; skipping.", stacklevel=2)` before `continue`.

### [P3.7] `scripts/brain/utils.py`:107 — `# type: ignore[assignment]` suppresses legitimate narrowing gap
**Agent**: cg-code-quality | **Tag**: [safe_auto]  
**Fix**: `if current_list is not None and current_key is not None:` combined guard; remove `# type: ignore`.

### [P3.8] `scripts/brain/clusterer.py`:225 — `frozenset((a, b))` heap-allocated per candidate pair
**Agent**: cg-performance | **Tag**: [safe_auto]  
**Fix**: `pair = (a, b) if a < b else (b, a)`.

### [P3.9] `scripts/brain/clusterer.py`:128 — `_weighted_jaccard` iterates `all_keys` twice
**Agent**: cg-performance | **Tag**: [safe_auto]  
**Fix**: Single-pass loop tracking `total_min` and `total_max` accumulators.

### [P3.10] `scripts/brain/edge_detector.py`:~96 — `_resolve_path()` accepts absolute paths outside project root; UNC paths are SSRF vector on Windows
**Agent**: cg-adversarial | **Tag**: [advisory]  
**Fix**: After resolving, assert result starts with `str(root.resolve())`. Warn or raise if path escapes project.

---

## ✅ Passed (no findings)

- **Version control**: Commit messages follow conventional commits; no secrets, PII, credentials, or data files committed; `.gitignore` covers `__pycache__/`; branch naming correct.
- **Learnings researcher**: All prior failure modes documented in `.cg-docs/solutions/` are correctly addressed — atomic writes, YAML single-quoted values, PS 5.1 `Invoke-PyHelper` pattern, UTF-8 BOM stripping, null coercion, pathlib throughout.
- **Adversarial**: No P0 issues. No exploitable RCE, PII, or data corruption paths found.

---

## Autofix Plan

**Applied automatically** (safe_auto): P1.1, P1.2, P1.3, P1.4, P1.5, P2.1, P2.2, P2.3, P2.5, P2.6, P2.7, P2.8, P2.10, P2.11, P2.13, P2.16, P3.1, P3.2, P3.3, P3.5, P3.6, P3.7, P3.8, P3.9

**Requires manual review**: P2.4, P2.9, P2.12, P2.15

**Advisory only**: P2.14, P3.4, P3.10
