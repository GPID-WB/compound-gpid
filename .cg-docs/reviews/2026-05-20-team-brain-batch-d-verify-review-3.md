---
date: 2026-05-29
depth: light
parent-review: .cg-docs/reviews/2026-05-20-team-brain-batch-d-review-3.md
type: verification
findings:
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P3.1: advisory
---

## Verify Review — Batch D Review 3 Fix Patches

**Review depth**: light (mode:verify)  
**Parent review**: `.cg-docs/reviews/2026-05-20-team-brain-batch-d-review-3.md`  
**Files reviewed**: 9 (fix-triage patch sites)  
**Agents dispatched**: cg-code-quality, cg-testing  
**Findings**: 5 (P0: 0, P1: 0, P2: 4, P3: 1)

---

### All 14 Prior Fixes — Verified

| Finding | File | Verification |
|---------|------|------|
| P1.1 | `test_push.py` | ✅ `unittest.main()` at final line; 23 classes before it |
| P1.2 | `push.py:_api_request` | ✅ `JSONDecodeError` guard on success path |
| P2.1 | `push.py:_get_remote_file` | ✅ `.get()` + `RuntimeError` on missing sha/content |
| P2.3 | `privacy.py` | ✅ `UserWarning` after loop on unclosed fence |
| P2.4 | `config.py` (×2) | ✅ `" #"` prefix check in both parsers |
| P2.6 | `pull.py` | ✅ `UserWarning` on malformed JSONL |
| P2.7 | `dedup.py` | ✅ `_STOP_WORDS` at module level |
| P2.15 | `test_dedup.py` | ✅ `entry_id` parameter |
| P2.16 | `test_curate.py` | ✅ `entry_id` parameter |
| P2.17 | `utils.py` | ✅ `write_atomic` doctest corrected |
| P3.4 | `clusterer.py` | ✅ `sum_a`/`sum_b` documented |
| P3.5 | `curate.py` | ✅ `import re` at module level |
| P3.6 | `extractor.py` | ✅ `os.path.basename()` in inner loop |
| P3.8 | `clusterer.py` | ✅ runnable `cluster_topics([])` doctest |
| P2.11 | `brain/__init__.py` | ✅ lazy imports preserved with circular-import comment |

---

### P2 — IMPORTANT (new test-coverage gaps)

**[P2.1]** [cg-testing] `scripts/team_brain/tests/test_push.py` — `_api_request` success-path malformed JSON is untested  
**Why**: The P1.2 fix wraps the success-path `json.loads(raw)` in `try/except json.JSONDecodeError`. No test makes `_opener.open()` return a 200 with a non-JSON body to confirm the `{"message": raw[:200]}` fallback fires.  
**Fix**:
```python
def test_api_request_success_path_non_json_body(self) -> None:
    """Success path: 200 response with non-JSON body returns {"message": ...}."""
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.status = 200
    mock_resp.read.return_value = b"not-json {"
    with patch("team_brain.push._opener") as mock_opener:
        mock_opener.open.return_value = mock_resp
        status, data = _api_request("GET", "https://api.github.com/test", "tok")
    self.assertEqual(status, 200)
    self.assertIn("message", data)
    self.assertNotIn("not-json", data.get("message", "")[:5])
```
**Tag**: `[safe_auto]`

**[P2.2]** [cg-testing] `scripts/team_brain/tests/test_push.py` — `_get_remote_file` HTTP-200 missing-field `RuntimeError` path is untested  
**Why**: P2.1 fix adds `RuntimeError` when `sha` or `content` is missing after a 200. `TestGetRemoteFileError` covers HTTP 500 and 404 but not the `(200, {})` case.  
**Fix**:
```python
def test_raises_runtime_error_on_200_missing_sha(self) -> None:
    with patch("team_brain.push._api_request", return_value=(200, {"content": "abc="})):
        with self.assertRaises(RuntimeError):
            _get_remote_file("owner/repo", "path.md", "tok")

def test_raises_runtime_error_on_200_missing_content(self) -> None:
    with patch("team_brain.push._api_request", return_value=(200, {"sha": "abc"})):
        with self.assertRaises(RuntimeError):
            _get_remote_file("owner/repo", "path.md", "tok")
```
**Tag**: `[safe_auto]`

**[P2.3]** [cg-testing] `scripts/team_brain/tests/test_privacy.py` — unclosed code fence `UserWarning` is untested  
**Why**: P2.3 fix emits `UserWarning` when `apply_regex_filter` finds `in_code_fence == True` at end of document. No test passes content with an unclosed ` ``` ` block and asserts the warning fires.  
**Fix**:
```python
def test_unclosed_code_fence_emits_warning(self) -> None:
    content = "Before.\n\n```python\nx = 1\n# no closing fence"
    with self.assertWarns(UserWarning) as cm:
        apply_regex_filter(content)
    self.assertIn("nclosed", str(cm.warning))
```
**Tag**: `[safe_auto]`

**[P2.4]** [cg-testing] `scripts/team_brain/tests/test_pull.py` — malformed JSONL warning untested  
**Why**: P2.6 fix emits `UserWarning` on malformed JSON in `_fetch_project_jsonl`. The existing `test_malformed_jsonl_lines_are_skipped` only asserts `len(entries) == 1` — no `assertWarns` call. Compare with `test_dedup.py:test_malformed_line_warns_and_skips` which uses `self.assertWarns`.  
**Fix**: Wrap the call in `with self.assertWarns(UserWarning):` or add a separate assertion confirming the warning is emitted.  
**Tag**: `[safe_auto]`

---

### P3 — MINOR

**[P3.1]** [cg-code-quality] `scripts/team_brain/config.py:_parse_frontmatter_from_text` — comment stripping before quote unquoting  
**Why**: `" #"` inline comment is stripped before surrounding quotes are removed. `push.py:_parse_frontmatter()` explicitly unquotes first with a comment explaining why (`"My Fix #1"` would otherwise be truncated). Same ordering hazard exists in `config.py:_parse_frontmatter_from_text()` and `_parse_markdown_body_key_block()`. Low practical risk since config values rarely contain `#` within quotes, but is inconsistent with the sibling implementation.  
**Fix**: Mirror `push.py` order — strip surrounding quotes first, then strip `" #"` from the unquoted value.  
**Tag**: `[advisory]`

---

### ✅ Passed

- **cg-code-quality**: All 14 fix-triage patches correctly applied; `brain/__init__.py` lazy-import revert confirmed; no regressions at patch sites.
- **cg-testing**: P1.1, P2.7, P2.15, P2.16, P3.5 fully verified; partial coverage gaps flagged for P1.2, P2.1, P2.3, P2.6 warning paths (code is correct; tests don't yet assert the new behaviours).
