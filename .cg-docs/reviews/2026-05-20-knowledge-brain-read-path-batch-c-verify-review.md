---
date: 2026-05-20
depth: light
parent-review: .cg-docs/reviews/2026-05-20-knowledge-brain-read-path-batch-c-review.md
type: verification
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P2.1: fixed
  P2.2: fixed
  P3.1: fixed
  P3.2: fixed
---

## Review Report

**Review depth**: light (forced by `mode:verify`)
**Files reviewed**: 10 (scripts/brain/renderer.py, edge_detector.py, scanner.py, clusterer.py, tests/test_edge_detector.py, tests/test_clusterer.py, tests/test_scanner.py, tests/test_renderer.py, tests/cg-index.Tests.ps1, tests/prompt-tools.Tests.ps1)
**Findings**: 7 (P0: 0, P1: 3, P2: 2, P3: 2)
**Agents**: cg-code-quality, cg-testing

---

### P1 — CRITICAL (convergence failures — prior fixes not wired in)

- **[P1.1]** [cg-code-quality + cg-testing] `scripts/brain/renderer.py:123` — `_entity_line()` builds `path_str` without calling `quote()` — prior finding P1.2 (URL encoding) did not converge
  **Why**: `from urllib.parse import quote` was added (line 38) as part of the P1.2 fix but `_entity_line()` still does `path_str = str(entity.path).replace("\\", "/")` — `quote()` is never called. Paths containing `(`, `)`, spaces, or `%` produce broken markdown links (e.g. `.cg-docs/plans/fix(v2).md` terminates the URL at the first `)`).
  **Fix**: Replace the path_str line with:
  ```python
  path_str = quote(str(entity.path).replace("\\", "/"), safe="/#-_.")
  ```
  Also add a test in `test_renderer.py` asserting that a path with special characters is percent-encoded in the rendered output.

- **[P1.2]** [cg-code-quality + cg-testing] `scripts/brain/renderer.py:122` — `_entity_line()` sanitizes title with `.replace("]", "\\]")` only, not via `_sanitize_inline()` — prior finding P2.4 (markdown injection) did not converge
  **Why**: `_sanitize_inline()` (escapes `]`, `(`, `)`, strips newlines) was defined at line 78 as the P2.4 fix, but `_entity_line()` was never updated to call it — it only escapes `]` manually. A title like `"Fix for (bug)"` still has unescaped `(` and `)` that corrupt the markdown link. `_sanitize_inline` is effectively dead code.
  **Fix**: Replace:
  ```python
  title = (entity.title or entity.slug).replace("]", "\\]")
  ```
  with:
  ```python
  title = _sanitize_inline(entity.title or entity.slug)
  ```
  Also add tests for `_sanitize_inline` in `test_renderer.py` (parens, brackets, newlines).

- **[P1.3]** [cg-code-quality] `scripts/brain/edge_detector.py:100` — `_resolve_path()` passes unresolved `Path` for absolute inputs, making the traversal guard lexical-only — prior finding P1.1 (path traversal) is partially incomplete
  **Why**: `resolved = p if p.is_absolute() else (root / p).resolve()` skips `.resolve()` for absolute paths. A path like `/project/root/../../../etc/passwd` has parts starting with `('/', 'project', 'root', '..', ...)` — `relative_to(root.resolve())` checks parts as a prefix, finds a match, and returns the unresolved path without filtering. Only relative traversal is caught.
  **Fix**: Apply `.resolve()` to absolute paths too:
  ```python
  resolved = p.resolve() if p.is_absolute() else (root / p).resolve()
  ```
  Add a test: `_resolve_path("/project/root/../../../etc/passwd", tmp_path)` must return `None`.

---

### P2 — IMPORTANT (should fix — test coverage gaps)

- **[P2.1]** [cg-testing] `scripts/brain/tests/test_edge_detector.py` — null-guard at `_resolve_path()` call site in `detect_edges()` is not integration-tested
  **Why**: `TestResolvePath` tests the helper in isolation. No test passes a traversal path (e.g. `brainstorm: "../../../../etc/passwd"`) as a frontmatter value and asserts `detect_edges()` returns zero edges. If the `if target is not None:` guard were removed, isolation tests would still pass.
  **Fix**: Add a test to `TestDecidedFromEdges`:
  ```python
  def test_traversal_path_in_frontmatter_produces_no_edge(self, tmp_path):
      plan = Entity(path=tmp_path / ".cg-docs/plans/plan.md", entity_type="plan",
                    frontmatter={"brainstorm": "../../../../etc/passwd"})
      edges = detect_edges([plan], root=tmp_path)
      assert edges == []
  ```

- **[P2.2]** [cg-testing] `scripts/brain/tests/test_scanner.py` — `test_unknown_top_dir_is_skipped` asserts empty return but does not verify the `UserWarning` is emitted
  **Why**: The P2.14 fix added `warnings.warn(...)` for unknown `.cg-docs/` subdirs, but the test only checks `entities == []`. A regression removing the warning call would pass silently.
  **Fix**: Add a companion test or extend the existing one:
  ```python
  def test_unknown_top_dir_emits_warning(self, tmp_path):
      import warnings as _w
      (tmp_path / ".cg-docs/misc").mkdir(parents=True)
      (tmp_path / ".cg-docs/misc/foo.md").write_text("---\ntitle: Foo\n---\n")
      with _w.catch_warnings(record=True) as caught:
          _w.simplefilter("always")
          scan_all(tmp_path)
      assert any("Unknown .cg-docs/ subdirectory" in str(w.message) for w in caught)
  ```

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-testing] `scripts/brain/tests/test_edge_detector.py` — slug collision warning (inferred edges path) is not tested
  **Why**: The P3.1 fix added `warnings.warn(...)` when same-slug entities produce an edge, but no test asserts the warning. A regression removing it would pass.
  **Fix**: Add to `TestSameSlugInferredEdges`:
  ```python
  def test_slug_collision_emits_warning(self, tmp_path):
      import warnings as _w
      slug = "2026-05-19-feature-x"
      plan = Entity(path=tmp_path / f".cg-docs/plans/{slug}.md", entity_type="plan", frontmatter={})
      bs = Entity(path=tmp_path / f".cg-docs/brainstorms/{slug}.md", entity_type="brainstorm", frontmatter={})
      with _w.catch_warnings(record=True) as caught:
          _w.simplefilter("always")
          detect_edges([plan, bs], root=tmp_path)
      assert any("Slug collision" in str(w.message) for w in caught)
  ```

- **[P3.2]** [cg-testing] `scripts/brain/tests/test_clusterer.py` — no determinism test for equal-size clusters
  **Why**: The P3.2 fix added a slug tie-breaker to the sort key, but no test verifies that two clusters of identical entity count produce the same ordering on repeated calls.
  **Fix**: Add a test that calls `cluster_topics()` twice on the same data and asserts `[t.slug for t in run1] == [t.slug for t in run2]`.

---

### ✅ Passed

- **cg-code-quality**: `scanner.py` (P2.14 unknown-subdir logic correct), `clusterer.py` (P3.2 sort key, P3.1 slug collision arithmetic, P3.6 Jaccard identity all correct), `cg-compound-refresh.prompt.md` (P2.12 count reporting step present), `README.md` (P2.11 brain bullet added), `tests/prompt-tools.Tests.ps1` (6 new `It` blocks structurally correct), `tests/cg-index.Tests.ps1` (P3.5 BOM-safe `WriteAllText` pattern correct)
- **cg-code-quality**: `scripts/cg_index.py` — `build_brain()` and `render_brain()` are both inside the `with warnings.catch_warnings(record=True)` block ✅ (known gotcha verified — no warning swallowing)
- **cg-testing**: `test_edge_detector.py::TestResolvePath` — all 5 isolation tests present and sound; `catch_warnings` scope is correct ✅
- **cg-testing**: `test_clusterer.py` — strengthened cluster separation test (pester vs python not mixed) is in place ✅; `TestWeightedJaccard` verifies correct numeric results with `pytest.approx` ✅
- **cg-testing**: `test_init.py` — P2.9 tautological assertion fixed; P2.13 midnight race resolved ✅

Parsed 7 finding IDs.
