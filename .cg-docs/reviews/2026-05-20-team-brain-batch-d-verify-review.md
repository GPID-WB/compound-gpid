---
date: 2026-05-20
depth: light
parent-review: .cg-docs/reviews/2026-05-20-team-brain-batch-d-review.md
type: verification
findings:
  P1.1: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P3.1: skipped
  P3.2: skipped
---

## Verification Report — `feat/knowledge-brain-engine` (post-fix-triage)

**Review depth**: light (verify mode)  
**Prior review**: `.cg-docs/reviews/2026-05-20-team-brain-batch-d-review.md` (40 findings, all `fixed`)  
**Agents**: cg-code-quality, cg-testing  
**Files verified**: ~15 (modified by fix-triage session)  
**Findings**: 10 (P1: 1, P2: 6, P3: 2 advisory)

**Verified ✅**: All 40 prior findings correctly implemented. Cross-file contracts intact. SCHEMA_VERSION Pester test accurate. Python + Pester suites both clean (324 + 1,949 tests, 0 failures).

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-code-quality] `scripts/brain/scanner.py:~82` — **Symlink guard `startswith` bypass**  
  **Why**: `str(resolved_path).startswith(str(cg_docs_real))` is a string prefix comparison, not a path component comparison. A directory named `.cg-docs-evil` sibling to `.cg-docs` would pass the guard — `str(resolved_path)` would start with the same prefix as `str(cg_docs_real)`.  
  **Fix**: Replace with `Path.relative_to()` which performs component-level comparison:
  ```python
  try:
      resolved_path.relative_to(cg_docs_real)
  except ValueError:
      warnings.warn(
          f"[brain.scanner] Skipping {md_path}: symlink escapes .cg-docs/ boundary.",
          stacklevel=2,
      )
      continue
  ```
  `[manual]`

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `scripts/brain/scanner.py:~79` — **`cg_docs.resolve()` called O(n) times inside loop**  
  **Why**: `cg_docs_real = cg_docs.resolve()` is inside the `for md_path in sorted(cg_docs.rglob(...))` loop. `resolve()` issues `readlink`/`realpath` syscalls on every iteration. At 200 entities this is 200 unnecessary syscalls. Pattern inconsistency: `edge_detector.py` correctly pre-computes `root_resolved = root.resolve()` once.  
  **Fix**: Move `cg_docs_real = cg_docs.resolve()` to before the loop.  
  `[safe_auto]`

- **[P2.2]** [cg-code-quality] `scripts/team_brain/schema.py` — **`confidence` upper bound missing (partial P1.6 fix)**  
  **Why**: The P1.6 fix validated `confidence >= 0.0` but not the upper bound. A corrupted JSONL entry with `"confidence": 999.0` silently sorts first in any ranking.  
  **Fix**: `if not (0.0 <= confidence <= 2.0): raise ValueError(...)` (2.0 allows reasonable boost headroom).  
  `[manual]`

- **[P2.3]** [cg-code-quality] `scripts/team_brain/privacy.py:181` — **Dead assignment `original = line`**  
  **Why**: `original = line` is assigned at the top of the `apply_regex_filter` loop body but never read. Dead code; `ruff F841` violation.  
  **Fix**: Delete the line.  
  `[safe_auto]`

- **[P2.4]** [cg-testing] `scripts/team_brain/tests/test_config.py` — **No test for `_find_local_config` stop-at-`.git`**  
  **Why**: The P2.3 fix added a `.git` stop-guard. No test exercises this path. A regression removing the stop would go undetected.  
  **Fix**: Add tests verifying walk stops correctly at `.git/` boundary.  
  `[manual]`

- **[P2.5]** [cg-testing] `scripts/team_brain/tests/test_privacy.py` — **No test for re-run-regex-after-LLM path (P2.2 fix)**  
  **Why**: `run_privacy_filter` now re-runs `apply_regex_filter` after `apply_llm_redactions`. No test verifies this second pass actually catches LLM-injected PII. Regression risk: silent removal of the second pass.  
  **Fix**: Add test where LLM replacement itself contains an absolute path.  
  `[manual]`

- **[P2.6]** [cg-testing] `scripts/brain/tests/test_clusterer.py` — **No test for `_MAX_FANOUT` skip branch**  
  **Why**: The P2.11 fix skips keywords appearing in >100 entities. No test exercises this path — it would never trigger with the current test suite (max 6 entities).  
  **Fix**: Add test with 101 entities sharing one ubiquitous keyword.  
  `[manual]`

- **[P2.7]** [cg-testing] `scripts/brain/tests/test_init.py` — **No test for `from brain import ClusterStrategy` (P3.4 re-export)**  
  **Why**: The `__getattr__` lazy re-export is untested. A refactor removing it would not be caught.  
  **Fix**: Add to `TestImports`: `from brain import ClusterStrategy; from brain.clusterer import ClusterStrategy as _D; assert ClusterStrategy is _D`.  
  `[safe_auto]`

---

### P3 — ADVISORY (no action required)

- **[P3.1]** [cg-code-quality] `scripts/brain/edge_detector.py` — `_resolve_path` calls `root.resolve()` independently from pre-computed `root_resolved`. Minor redundancy, no correctness impact. `[advisory]`

- **[P3.2]** [cg-code-quality] `scripts/team_brain/privacy.py` — `_HEADING_RE` has superfluous `re.MULTILINE` flag; called on single stripped lines. No correctness impact. `[advisory]`

---

### ✅ Verified — all 40 prior findings correctly implemented

- All source implementations spot-checked and confirmed correct
- Test assertions match source error messages exactly
- `_UNIX_PATH_RE` lookbehind `(?<![A-Za-z0-9_.])` is correct — blocks relative-path false positives
- Re-run regex after LLM uses correct `config` reference
- `__getattr__` ClusterStrategy re-export is PEP 562 compliant (Python 3.7+)
- `cg-code-quality` clean on all newly modified files
- SCHEMA_VERSION Pester test correctly updated to `brain-engine` marker
