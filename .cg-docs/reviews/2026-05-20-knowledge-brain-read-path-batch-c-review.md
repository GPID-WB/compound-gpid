---
date: 2026-05-20
depth: thorough
plan: .cg-docs/plans/2026-05-20-knowledge-brain-read-path-batch-c.md
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
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
  P2.14: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
---

## Review Report

**Review depth**: thorough  
**Files reviewed**: 54 (42 committed + 12 uncommitted working-tree changes)  
**Branch**: `feat/knowledge-brain-engine` (PR #42)  
**Findings**: 24 (P0: 0, P1: 4, P2: 14, P3: 6)

---

### P0 — BLOCKING

*None.*

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [adversarial+data-quality] `scripts/brain/edge_detector.py` — **`_resolve_path()` has no project-root containment check — frontmatter paths can escape via `../../../` and appear verbatim in `brain-index.json`**  
  **Why**: LLM-authored frontmatter (`plan: ../../../../.env`) resolves to absolute filesystem paths outside the repo. Those paths are stored in `edges[].target` in `brain-index.json`. An agent consuming the JSON may attempt to read the path as a project artifact (confused-deputy attack). Leaks username-containing paths on all platforms.  
  **Fix** `[manual]`:
  ```python
  def _resolve_path(val: str, root: Path) -> Optional[Path]:
      p = Path(val)
      resolved = p if p.is_absolute() else (root / p).resolve()
      try:
          resolved.relative_to(root.resolve())
      except ValueError:
          warnings.warn(
              f"[brain.edge_detector] Frontmatter path '{val}' escapes project root — edge discarded.",
              stacklevel=2,
          )
          return None
      return resolved
  ```
  Callers must null-check the return value.

- **[P1.2]** [adversarial] `scripts/brain/renderer.py` — **`path_str` is not URL-encoded in `_entity_line()` → HTML attribute injection in BRAIN.md**  
  **Why**: `path_str = str(entity.path).replace("\\", "/")` is inserted directly into a CommonMark link URL `[title](path_str)`. A `path_str` containing ` "title"` or `)` injects a `title=""` attribute into the rendered `<a>` tag. Feature IDs from `roadmap.json` (e.g., a feature ID `foo "inject"`) travel through this path without escaping.  
  **Fix** `[manual]`:
  ```python
  from urllib.parse import quote
  path_str = quote(str(entity.path).replace("\\", "/"), safe="/#-_.")
  ```

- **[P1.3]** [data-quality] `scripts/brain/scanner.py` — **`scan_roadmap()` calls `.get()` on milestone/feature items without checking they're dicts → `AttributeError` crash on malformed JSON**  
  **Why**: The `json.loads()` try/except only wraps parsing. If `roadmap.json` contains `"milestones": [1, "string"]` or `"features": [null]`, calling `.get()` on an `int`/`str`/`None` raises `AttributeError`. `cg_index.py::main()` catches only `OSError`, so this propagates as an unhandled traceback.  
  **Fix** `[safe_auto]`: Add `isinstance(milestone, dict)` and `isinstance(feature, dict)` guards before `.get()` calls in both loops, with `warnings.warn(...)` and `continue`.

- **[P1.4]** [code-quality] `scripts/brain/renderer.py` — **Stale `BRAIN-NN.md` partition files accumulate across re-runs**  
  **Why**: `render_brain()` never removes old partition files from prior runs. If the corpus shrinks from 5 topics to 3, `BRAIN-04.md` and `BRAIN-05.md` persist. `BRAIN.md`'s topic index won't link them, but `file_search("BRAIN-*.md")` or a glob will find stale content, confusing both users and agents.  
  **Fix** `[manual]`: At the start of `render_brain()`, before writing, remove stale partition files:
  ```python
  for stale in out_dir.glob("BRAIN-[0-9][0-9].md"):
      try:
          stale.unlink()
      except OSError:
          pass
  ```

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [adversarial] `scripts/brain/utils.py` — **`_COMMA_SPLIT_RE` has O(N²) backtracking on adversarial inline-list values**  
  **Why**: The nested-lookahead regex `r",(?=(?:[^\"']*[\"'][^\"']*[\"'])*[^\"']*$)"` has O(K×N) cost per comma on strings with K unmatched quotes. Adversarially crafted `tags: [a'a'a'...(200 quotes)...]` in any `.cg-docs/` file can hang the indexer.  
  **Fix** `[safe_auto]`: Replace with `csv.reader` for O(N) parsing: `next(csv.reader(io.StringIO(inner), skipinitialspace=True), [])`.

- **[P2.2]** [code-quality+documentation] `.github/prompts/cg-brain-rebuild.prompt.md` — **Typo: "past earnings" should be "past learnings"**  
  **Fix** `[safe_auto]`.

- **[P2.3]** [code-quality+architecture] `scripts/brain/__init__.py`, `scripts/brain/renderer.py`, `scripts/cg_index.py` — **`schema_version` `"0.2.0"` hardcoded in three independent locations**  
  **Why**: A version bump requires three edits; a missed edit produces a `brain-index.json` with a stale schema version.  
  **Fix** `[safe_auto]`: In `renderer.py`, import `from brain import __version__ as _BRAIN_VERSION` and use `"schema_version": _BRAIN_VERSION`.

- **[P2.4]** [data-quality] `scripts/brain/renderer.py` — **`_entity_line()` only escapes `]` in titles; `(` and `)` are unescaped, and status/date fields are not sanitized**  
  **Why**: Characters `(`, `)` in title text corrupt the markdown link structure. `status` and `date` from frontmatter are inserted raw into italic/code spans.  
  **Fix** `[safe_auto]`: Add `_sanitize_inline()` helper that strips newlines; add `(` and `)` to title escaping.

- **[P2.5]** [data-quality] `scripts/brain/scanner.py` — **`scan_all()` silently indexes entities with empty frontmatter (no warning)**  
  **Why**: `scan_solutions()` warns; `scan_all()` does not. A truncated plan file appears in BRAIN.md with only its slug.  
  **Fix** `[safe_auto]`: Add `warnings.warn(...)` when `parse_frontmatter()` returns `{}` and a `---` block was detected.

- **[P2.6]** [data-quality] `scripts/brain/edge_detector.py` — **Slug-collision `references` edges emitted silently with no warning**  
  **Why**: Two unrelated files with the same stem get a `references` edge with no feedback.  
  **Fix** `[safe_auto]`: Add `warnings.warn(...)` when `len(slug_entities) >= 2`.

- **[P2.7]** [architecture] `scripts/brain/clusterer.py` — **`min_cluster_size` is silently ignored when a custom `strategy` is provided**  
  **Why**: Breaks the extensibility contract.  
  **Fix** `[safe_auto]`: Add docstring note: "When a custom strategy is provided, `min_cluster_size` is intentionally not forwarded."

- **[P2.8]** [architecture] `scripts/brain/__init__.py` — **`Entity.text` (raw file content) retained in memory after extraction**  
  **Why**: At 1000 entities × 5 KB each, this wastes ~5 MB of heap throughout the cluster/edge/render stages.  
  **Fix** `[safe_auto]`: Zero out after extraction loop: `entity.text = ""`.

- **[P2.9]** [testing] `scripts/brain/tests/test_extractor.py` — **Tautological assertion `kw == kw.lower() or kw == kw` always passes**  
  **Fix** `[safe_auto]`: Change to `assert kw == kw.lower(), f"Keyword '{kw}' is not lowercase"`.

- **[P2.10]** [documentation] `scripts/brain/__init__.py` — **`build_brain()` `generated` parameter missing from `Args:` docstring**  
  **Fix** `[safe_auto]`.

- **[P2.11]** [documentation] `README.md` — **Brain system not mentioned in README feature list**  
  **Fix** `[manual]`: Add bullet describing `cg-index --brain` and `/cg-brain-rebuild`.

- **[P2.12]** [documentation] `.github/prompts/cg-compound-refresh.prompt.md` — **Step 7 runs `cg-index --brain` but never reports entity/topic/edge counts back to user**  
  **Fix** `[manual]`: Add parse-and-echo step after `cg-index --brain`, mirroring `/cg-brain-rebuild` Step 2 secondary verification.

- **[P2.13]** [reproducibility] `scripts/brain/tests/test_init.py` — **Midnight race condition in `test_generated_defaults_to_today`**  
  **Why**: Two `date.today()` calls bracket the test — at midnight they return different dates.  
  **Fix** `[safe_auto]`: Assert `re.match(r"\d{4}-\d{2}-\d{2}$", data.generated)` instead.

- **[P2.14]** [code-quality] `scripts/brain/scanner.py` — **Unknown `.cg-docs/` subdirectories silently skipped with no warning**  
  **Why**: A directory name typo (`.cg-docs/solution/` vs `solutions/`) produces zero indexed entities with no feedback.  
  **Fix** `[manual]`: Emit `warnings.warn(...)` for top-level dirs not in `_DIR_TO_TYPE` (excluding `archive`).

---

### P3 — MINOR (nice to have)

- **[P3.1]** [architecture] `scripts/brain/clusterer.py` — Topic slug collision not detected — two topics with identical top-3 keywords produce the same slug, silently corrupting BRAIN.md navigation links `[advisory]`

- **[P3.2]** [reproducibility] `scripts/brain/clusterer.py` — Equal-size topics sorted by Union-Find root index (non-deterministic) → diff noise in committed BRAIN.md. Fix: add `t.slug` as tie-breaker in `topics.sort()` `[advisory]`

- **[P3.3]** [testing] `scripts/brain/tests/test_edge_detector.py` — `_resolve_path()` has no unit tests for relative paths, absolute paths, and paths that escape root `[advisory]`

- **[P3.4]** [testing] `tests/prompt-tools.Tests.ps1` — "Recognized:" string test covers only 2 of 6 prompts; `test_related_entities_cluster_together` assertion `len >= 1` is too weak `[advisory]`

- **[P3.5]** [testing] `tests/cg-index.Tests.ps1` — `--brain` file-existence tests never inspect BRAIN.md content; no test with `roadmap.json` present `[advisory]`

- **[P3.6]** [performance] `scripts/brain/clusterer.py` — `_weighted_jaccard` iterates the full keyword union (up to 100 per call); an intersection-only variant with pre-cached sums is ~10× faster at N=1000 `[advisory]`

---

### ✅ Passed

- **cg-code-quality**: Named constants for all magic numbers; `Entity.tags` property handles non-list values; atomic write safety; `scan_roadmap` missing-id warning; `--no-brain` flag consistent across all 6 prompts
- **cg-testing**: Comprehensive Python test suite (7 modules, all public APIs covered); Pester tests use `(?i)Consult Brain` regex (not step-number-based); all 1938 Pester tests pass
- **cg-version-control**: No secrets; BRAIN artifacts correctly committed per policy; Python bytecode gitignored; branch/commit naming conventions correct
- **cg-reproducibility**: All algorithms deterministic; `conftest.py` sys.path correct; `_write_atomic` safe; relative paths only in production; entity scan order stable
- **cg-architecture**: Module boundaries excellent; brain/legacy separation clean; no circular imports; `BrainData` abstraction correct; edge detection null-guard complete
- **cg-documentation**: All Python functions have `Args`/`Returns`/`Example`; brain sub-modules set a high documentation bar; `docs/reference.md` and `docs/model-guide.md` updated; `cg-skill-brain-query` SKILL.md is self-contained
- **Brain gotchas verified fixed**: `build_brain()` correctly inside `warnings.catch_warnings()` block; legacy file cleanup correctly outside the try block with per-file error handling; two-pass stable sort used in `_write_brain_log`
