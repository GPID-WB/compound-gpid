---
date: 2026-05-29
depth: light
parent-review: .cg-docs/reviews/2026-05-20-team-brain-batch-d-review-2.md
plan: .cg-docs/plans/2026-05-20-team-brain-batch-d.md
type: verification
branch: feat/knowledge-brain-engine
agents: cg-code-quality, cg-testing
findings:
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
---

## Review Report

**Review depth**: light (verify pass)  
**Parent review**: `2026-05-20-team-brain-batch-d-review-2.md` (22 fixed, 1 skipped)  
**Files reviewed**: `pull.py`, `distiller.py`, `__init__.py`, `test_pull.py`, `test_distiller.py`, `cg-skill-brain-query/SKILL.md`  
**Findings**: 8 (P0: 0, P1: 0, P2: 4, P3: 4)  
**All P0/P1 from parent review confirmed correctly applied.**

---

### ✅ Confirmed Fixed (no regressions)

- **P0.1**: `distiller.py` — `isinstance(rc_val, str)` / `isinstance(title_val, str)` null guards ✓
- **P0.2**: `pull.py` + `SKILL.md` — security note present, block-quote instruction in place ✓
- **P1.1–P1.4**: `pull.py` — `try/except (ValueError, TypeError)` around `float()`, `tags or []` guard, non-string `pattern_text` guard, `math.isfinite` check ✓
- **P1.5**: `pull.py` — `except (OSError, ValueError)` + `utf-8-sig` on all cache reads ✓
- **P1.6**: `__init__.py` — `load_team_brain_local_config` name corrected in docstring ✓
- **P2.2–P2.6**: `pull.py` / `distiller.py` — atomic writes, empty pattern skip, module-level regex, `task_kw_set` hoisted, docstrings ✓
- **P3.1–P3.4**: `pull.py` — unused `field` removed, `i` removed from enumerate, XDG priority order corrected ✓

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `scripts/team_brain/pull.py` — `refresh=True` not propagated to `_fetch_project_jsonl`.  
  **Why**: `pull_from_team_brain(kws, config, refresh=True)` correctly passes `refresh` to `_fetch_team_brain_index`, but calls `_fetch_project_jsonl(config, project_name)` with no `refresh` argument. The JSONL cache ignores `refresh=True` and uses the 1-hour TTL unconditionally. A caller gets a freshly-fetched index but stale pattern entries — silent inconsistency. The function's docstring contains a phantom `refresh: If True, bypass cache...` parameter that was never implemented.  
  **Fix**: Add `refresh: bool = False` to `_fetch_project_jsonl` and skip `_is_cache_fresh` when `True`; pass `refresh=refresh` from the call site in `pull_from_team_brain`. `[safe_auto]`

- **[P2.2]** [cg-code-quality + cg-testing] `scripts/team_brain/tests/test_pull.py` — `TestPullEdgeCases` (P2.8 fix) placed after `if __name__ == "__main__": unittest.main()`.  
  **Why**: When run directly (`python test_pull.py`), `unittest.main()` executes before the class is defined — all seven edge-case tests are silently skipped. Under pytest (CI) they are discovered normally. This is a new defect introduced by the P2.8 placement.  
  **Fix**: Move `class TestPullEdgeCases` above the `if __name__ == "__main__":` guard. `[safe_auto]`

- **[P2.3]** [cg-testing] `scripts/team_brain/tests/test_pull.py` — `test_malformed_jsonl_lines_are_skipped` not cache-isolated.  
  **Why**: The test patches `_fetch_remote_raw` but does not mock `_is_cache_fresh` or redirect `_cache_dir`. If a fresh `compound-gpid.jsonl` exists in the developer's real cache directory (from a prior manual run), the cache branch fires, `_fetch_remote_raw` is never called, and the assertion `assertEqual(len(entries), 1)` targets whatever is cached. The test passes or fails based on filesystem state.  
  **Fix**: Add `patch("team_brain.pull._is_cache_fresh", return_value=False)` context to force the remote-fetch branch. `[safe_auto]`

- **[P2.4]** [cg-testing] `scripts/team_brain/tests/test_pull.py` — `test_inf_confidence_clamped_to_one` wraps its security assertion in `if result.patterns:`.  
  **Why**: If the entry fails to match (e.g., future scoring-threshold change), the `if` is `False`, the test passes with zero assertions, and the clamping invariant is never verified. This is an adversarial-resistance test — the assertion must be unconditional.  
  **Fix**:
  ```python
  self.assertGreaterEqual(len(result.patterns), 1, "inf-confidence entry must still match")
  self.assertFalse(any(p.confidence == float("inf") for p in result.patterns))
  ```
  `[safe_auto]`

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `scripts/team_brain/pull.py` — `_fetch_project_jsonl` docstring has a phantom `refresh:` parameter in the `Args:` block.  
  **Why**: The `Args:` section documents `refresh: If True, bypass cache and fetch from remote.` but the function signature is `(config, project_name)` — no `refresh` argument. Stale artifact from the P2.3 caching fix. Resolved by implementing P2.1 (add the parameter). If P2.1 is deferred, remove the docstring line as a standalone fix.  
  **Fix**: Remove the `refresh:` line (or implement the parameter per P2.1). `[safe_auto]`

- **[P3.2]** [cg-code-quality + cg-testing] `scripts/team_brain/tests/test_distiller.py` — `TestDistillerReviewFindings` (P3.6 fix) placed after `if __name__ == "__main__": unittest.main()`.  
  **Why**: Same as P2.2 — the six new null-guard and skipping tests are invisible when the file is run directly. Pytest discovers them normally.  
  **Fix**: Move `class TestDistillerReviewFindings` above the `if __name__ == "__main__":` block. `[safe_auto]`

- **[P3.3]** [cg-code-quality] `scripts/team_brain/__init__.py:35` — module docstring calls `push_to_team_brain()` which does not exist.  
  **Why**: P1.6 corrected the `load_team_brain_local_config` import name but left the push call using a phantom alias. `push_to_team_brain(entry_path, pattern, config)` is never defined anywhere in the package — the actual entry point is `push_entry(entry_path, config)` in `push.py`. Anyone following the example will get a `NameError`.  
  **Fix**: Change the import to `from team_brain.push import push_entry` and the call to `push_entry(entry_path, config)`. `[safe_auto]`

- **[P3.4]** [cg-testing] `scripts/team_brain/tests/test_distiller.py` — `TestDistillerReviewFindings.test_empty_fallback_source` duplicates `TestDistillPattern.test_fallback_when_empty`.  
  **Why**: Both assert `pattern_text == "(no pattern)"` and `source == "fallback"` on `distill_pattern({}, "")`. The only new assertion in the P3.6 test is `assertIsNone(result.prompt)`.  
  **Fix**: Remove `test_empty_fallback_source` and add `assertIsNone(result.prompt)` to the existing `test_fallback_when_empty`, or rename it to `test_fallback_source_has_no_prompt` and remove the redundant assertions. `[advisory]`

---

### ✅ Passed

- **cg-version-control**: No new secrets, credentials, or auth code introduced.
- **cg-data-quality**: Entry validation guards (P1.1–P1.4) confirmed correctly applied.
- **cg-reproducibility**: All test mocks correctly isolate network calls.
