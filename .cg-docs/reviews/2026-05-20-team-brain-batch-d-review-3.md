---
plan: .cg-docs/plans/2026-05-20-team-brain-batch-d.md
findings:
  P1.1: fixed
  P1.2: fixed
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
  P2.11: skipped
  P2.12: fixed
  P2.13: fixed
  P2.14: fixed
  P2.15: fixed
  P2.16: fixed
  P2.17: fixed
  P3.1: advisory
  P3.2: fixed
  P3.3: advisory
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
  P3.7: fixed
  P3.8: fixed
  P3.9: fixed
  P3.10: advisory
  P3.11: advisory
  P3.12: advisory
  P3.13: fixed
---

## Review Report

**Review depth**: thorough  
**Files reviewed**: 88 (focused on 27 Python source/test modules + `.github/` prompts)  
**Findings**: 32 (P0: 0, P1: 2, P2: 17, P3: 13)

---

### ⚠️ Incomplete Reviews
- `@cg-adversarial` did not produce usable output. Consider re-running `/cg-review thorough` with a higher model tier, or invoke `@cg-adversarial` directly on `push.py`, `pull.py`, and `privacy.py`.

---

### P0 — BLOCKING
*None found.*

---

### P1 — CRITICAL (must fix before merge)

**[P1.1]** [cg-testing] `scripts/team_brain/tests/test_push.py:445` — 11 test classes defined **after** `unittest.main()` are silently skipped on direct execution  
**Why**: Classes from `TestProjectNameValidation` onward (11 classes, ~300 lines) are never registered when running `python test_push.py` directly. This includes `test_traversal_rejected` — the critical path-traversal prevention test. All classes run under pytest, but CI that uses pytest would mask the gap.  
**Fix**: Move `if __name__ == "__main__": unittest.main()` to the very last line of the file.  
**Tag**: `[safe_auto]`

**[P1.2]** [cg-data-quality] `scripts/team_brain/push.py:295` — `_api_request` success path has no `json.JSONDecodeError` guard  
**Why**: `json.loads(resp.read().decode("utf-8"))` on the happy path raises unhandled `json.JSONDecodeError` if GitHub returns a non-JSON 2xx body (HTML maintenance page on 502/503 that urllib reports as success). The error path already handles it; the success path does not.  
**Fix**:
```python
with _opener.open(req, timeout=30) as resp:
    raw = resp.read().decode("utf-8")
    try:
        return resp.status, json.loads(raw)
    except json.JSONDecodeError:
        return resp.status, {"message": raw[:200]}
```
**Tag**: `[safe_auto]`

---

### P2 — IMPORTANT (should fix)

**[P2.1]** [cg-data-quality] `scripts/team_brain/push.py:333` — `_get_remote_file` accesses `data["sha"]` and `data["content"]` by bare key after HTTP 200  
**Why**: GitHub returns HTTP 200 with different schema for files >1 MB (no `"content"` key). Also returns 200 without those keys for directory paths. Both raise `KeyError` with no user message.  
**Fix**: Use `.get()` with explicit error for missing keys; document the 1 MB size constraint.  
**Tag**: `[safe_auto]`

**[P2.2]** [cg-data-quality] `scripts/team_brain/privacy.py:120` — `_CREDENTIAL_RE` has false positives for type annotations and `None` defaults  
**Why**: Pattern matches `token: str`, `token = None`, `api_key: Optional[str]` — common in Python documentation. This corrupts legitimate content being pushed to the team brain.  
**Fix**: Add negative lookahead for known non-secret values (`None`, `NULL`, `str`, `int`, `bool`, `Optional`).  
**Tag**: `[manual]`

**[P2.3]** [cg-data-quality] `scripts/team_brain/privacy.py:162` — Unclosed code fence silently suppresses ALL credential detection for remainder of document  
**Why**: If a solution file has an unclosed `` ``` `` fence, `in_code_fence` stays `True` and real credentials in subsequent prose are never redacted.  
**Fix**: Add end-of-document warning: `if in_code_fence: warnings.warn("[privacy] Unclosed code fence...")`  
**Tag**: `[safe_auto]`

**[P2.4]** [cg-data-quality] `scripts/team_brain/config.py:181` — Inline comment stripping uses `index("#")` (first `#`) instead of `" #"` (space-before-`#`)  
**Why**: Silently truncates values like `repo: "GPID-WB/team-brain#issue-tracker"`. `schema.py` correctly uses `" #"` split; `config.py` does not match.  
**Fix**: Change `str.index("#")` to `" #"` prefix check, matching `schema.py` pattern.  
**Tag**: `[safe_auto]`

**[P2.5]** [cg-data-quality] `scripts/team_brain/dedup.py:159` — No per-file size limit on JSONL parsing  
**Why**: `read_text(...).splitlines()` is unbounded; `scanner.py` has a 10 MB guard but JSONL parsers do not. Adversarially large remote JSONL could exhaust memory.  
**Fix**: Add `if jsonl_path.stat().st_size > 20 * 1024 * 1024: warnings.warn(...); continue` before reading.  
**Tag**: `[manual]`

**[P2.6]** [cg-data-quality] `scripts/team_brain/pull.py:355` — Malformed JSONL lines silently dropped with no warning  
**Why**: `except json.JSONDecodeError: continue` discards corrupt lines without logging. `dedup.py` emits `UserWarning` for the same case; `pull.py` is inconsistent.  
**Fix**: `warnings.warn(f"[pull] Malformed JSON in {project_name}.jsonl line {n} — skipping: {exc}", UserWarning)`  
**Tag**: `[safe_auto]`

**[P2.7]** [cg-code-quality] `scripts/team_brain/dedup.py:103` — `_STOP_WORDS` frozenset constructed inside `_tokenize()` on every call (O(n²) hot path)  
**Why**: Every call allocates a new identical frozenset. `_tokenize` is called twice per pair in the O(n²) loop — 9,900+ superfluous allocations at n=100.  
**Fix**: Hoist `_STOP_WORDS: frozenset[str] = frozenset({...})` to module level.  
**Tag**: `[safe_auto]`

**[P2.8]** [cg-performance] `scripts/team_brain/dedup.py:324` — Pattern text re-tokenized O(n²) instead of O(n)  
**Why**: `_tokenize(a.get("pattern", ""))` called fresh every pair. Pre-tokenizing all entries once before the loop cuts tokenization from O(n²) to O(n).  
**Fix**: Build `pattern_tokens: list[Set[str]]` before the loop; index by position inside the loop.  
**Tag**: `[manual]`

**[P2.9]** [cg-architecture] `scripts/team_brain/push.py:176` — `_parse_frontmatter` duplicated from `brain.utils.parse_frontmatter`  
**Why**: Two divergent implementations: `push.py`'s lacks BOM stripping and null coercion rules added to `brain.utils`. Divergence is silent.  
**Fix**: Extract `parse_frontmatter_with_body()` to `scripts/parsing_utils.py`; both packages import from it.  
**Tag**: `[manual]`

**[P2.10]** [cg-architecture] `scripts/cg_index.py` — 459 lines, exceeds 300-line guideline; mixes legacy and new responsibilities  
**Why**: Contains deprecated `SolutionEntry`, `scan_solutions()`, `build_index()`, `build_digest()` alongside new `build_brain()` integration.  
**Fix**: Move legacy code to `scripts/brain/legacy.py`; keep `cg_index.py` as thin CLI dispatcher.  
**Tag**: `[manual]`

**[P2.11]** [cg-architecture] `scripts/brain/__init__.py:196` — lazy sub-module imports inside `build_brain()` should be top-level  
**Why**: Intra-function imports hide `ImportError` until runtime; prevent type checker resolution; no longer justified since all modules are implemented.  
**Fix**: Move `from brain.scanner import ...` etc. to module top level.  
**Note**: ⚠️ Attempted and reverted — sub-modules import `Entity` from the `brain` package creating a circular import. The lazy imports are architecturally necessary until data classes are extracted to `brain._types`. Leave open for a dedicated refactor.  
**Tag**: `[manual]`

**[P2.12]** [cg-reproducibility] `scripts/team_brain/push.py:590` — `_date.today()` hard-coded in `push_entry()`, no injection point  
**Why**: Every push on a different day produces different content/SHA; replay testing requires monkey-patching.  
**Fix**: Add `_today: str | None = None` parameter; use `_today or _date.today().isoformat()`.  
**Tag**: `[manual]`

**[P2.13]** [cg-reproducibility] `scripts/team_brain/curate.py:51` — `sys.path.insert` in production code inside `_import_dedup()`  
**Why**: Runtime `sys.path` mutation in application logic; path string comparison for deduplication is brittle.  
**Fix**: Remove the `sys.path` fallback; exit with clear error on `ImportError`.  
**Tag**: `[manual]`

**[P2.14]** [cg-reproducibility] `scripts/team_brain/tests/` — `sys.path.insert(0, ...)` duplicated in 5 test files; no local `conftest.py`  
**Fix**: Add `scripts/team_brain/tests/conftest.py`; remove per-file boilerplate.  
**Tag**: `[manual]`

**[P2.15]** [cg-testing] `scripts/team_brain/tests/test_dedup.py:52` — `_make_entry` f-string uses `{id}` (builtin) instead of `{entry_id}`  
**Why**: Produces `"entries/proj-a/<built-in function id>.md"` — garbage path. Tests pass only because no assertion checks `entry-path` value.  
**Fix**: Change to `f"entries/{project}/{entry_id}.md"`.  
**Tag**: `[safe_auto]`

**[P2.16]** [cg-testing] `scripts/team_brain/tests/test_curate.py:46` — Same `{id}` builtin capture in `_make_entry`  
**Fix**: Change to `f"entries/{project}/{entry_id}.md"`.  
**Tag**: `[safe_auto]`

**[P2.17]** [cg-documentation] `scripts/brain/utils.py:340` — `write_atomic()` Example calls `_write_atomic()` (undefined — name changed when promoted to public)  
**Why**: Running the doctest raises `NameError`.  
**Fix**: Change `_write_atomic(...)` to `write_atomic(...)`.  
**Tag**: `[safe_auto]`

---

### P3 — MINOR (nice to have)

**[P3.1]** [cg-learnings-researcher] `scripts/team_brain/actions/rebuild-index.yml:141` — inline CI script uses non-atomic `output_path.write_text()`  
**Why**: Contradicts documented `write_atomic` standard; runner crash mid-write truncates index.  
**Tag**: `[advisory]`

**[P3.2]** [cg-reproducibility] `scripts/brain/clusterer.py:249` — implicit insertion-order tie-breaking in `sorted_pairs` and `_top_keywords_for_cluster`  
**Fix**: Add alphabetical tiebreaker: `key=lambda kv: (-kv[1], kv[0])`.  
**Tag**: `[manual]`

**[P3.3]** [cg-data-quality] `scripts/team_brain/schema.py:304` — `schema-version` value never validated against `SCHEMA_VERSION`  
**Fix**: Add `warnings.warn(...)` when value doesn't match expected version.  
**Tag**: `[advisory]`

**[P3.4]** [cg-code-quality] `scripts/brain/clusterer.py:121` — `_weighted_jaccard` `Args:` missing `sum_a`/`sum_b` documentation  
**Fix**: Document purpose of optional pre-computed sums.  
**Tag**: `[safe_auto]`

**[P3.5]** [cg-code-quality] `scripts/team_brain/curate.py:75` — `import re` deferred inside `_parse_team_brain_yml()` function body  
**Fix**: Move to module-level imports.  
**Tag**: `[safe_auto]`

**[P3.6]** [cg-performance] `scripts/brain/extractor.py:320` — `Path(fref).name` in inner loop; use `os.path.basename(fref)` instead  
**Tag**: `[safe_auto]`

**[P3.7]** [cg-documentation] `docs/reference.md:20` — `cg-brain-init` command absent from Shell Commands table  
**Fix**: Add row for `cg-brain-init --repo owner/repo --manager username`.  
**Tag**: `[manual]`

**[P3.8]** [cg-documentation] `scripts/brain/clusterer.py:355` — `cluster_topics()` Example is non-runnable placeholder  
**Fix**: Replace with `>>> cluster_topics([])` returning `[]`.  
**Tag**: `[safe_auto]`

**[P3.9]** [cg-documentation] `docs/team-brain-schema.md` — `private:` and `private-sections:` fields not documented for authors  
**Fix**: Add Privacy Fields section describing the two opt-out fields.  
**Tag**: `[manual]`

**[P3.10]** [cg-architecture] `scripts/team_brain/curate.py:46` — `_import_dedup()` lazy-import architectural concern  
**Tag**: `[advisory]`

**[P3.11]** [cg-reproducibility] `scripts/brain/__init__.py:220` — `generated: str = ""` empty-string sentinel undocumented  
**Fix**: Change to `generated: str | None = None`.  
**Tag**: `[advisory]`

**[P3.12]** [cg-version-control] Two commits lack conventional scope (`chore: bump SCHEMA_VERSION`, `docs: add team-brain schema`)  
**Tag**: `[advisory]`

**[P3.13]** [cg-testing] `scripts/brain/tests/test_init.py` — `_parse_inline_list` missing direct unit tests for `None` return and empty list  
**Tag**: `[manual]`

---

### ✅ Passed
- cg-code-quality: All security fixes verified (path traversal, redirect block, credential regex word boundaries); error handling uses typed exceptions throughout; consistent naming and constants
- cg-testing: 14/15 test modules fully adequate; `brain/` tests completely isolated; all 8 documented past bugs have passing regression tests
- cg-architecture: Clean `brain/` ↔ `team_brain/` boundary; `_NoRedirectHandler` correctly blocks Authorization header forwarding; `ClusterStrategy` protocol justified
- cg-version-control: No credentials, no PII, no data files; institutional knowledge artifacts correctly committed; 40/42 commits follow conventional format
- cg-reproducibility: All paths use `pathlib.Path`; deterministic scan order; 1-hour cache with `refresh=` bypass; `write_atomic` used for all brain outputs
- cg-learnings-researcher: All 9 past documented bugs VERIFIED fixed in current code
