---
plan: .cg-docs/plans/2026-05-20-team-brain-batch-d.md
date: 2026-05-20
depth: thorough
branch: feat/knowledge-brain-engine
files-reviewed: 54
agents: cg-code-quality, cg-testing, cg-documentation, cg-version-control, cg-reproducibility, cg-performance, cg-architecture, cg-data-quality, cg-learnings-researcher, cg-adversarial
findings:
  P0.1: fixed
  P0.2: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: fixed
  P1.7: fixed
  P1.8: fixed
  P1.9: fixed
  P1.10: fixed
  P1.11: fixed
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
  P2.15: fixed
  P2.16: fixed
  P2.17: fixed
  P2.18: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
  P3.7: fixed
  P3.8: fixed
  P3.9: fixed
  P3.10: fixed
  P3.11: fixed
  P3.12: fixed
---

## Review Report

**Review depth**: thorough  
**Files reviewed**: 54 (22,718 insertions / 1,584 deletions vs main)  
**Primary scope**: `scripts/brain/` Python engine, `scripts/team_brain/` Phase 1 modules, `scripts/cg_index.py`  
**Findings**: 40 (P0: 2, P1: 11, P2: 18, P3: 12, minus deduplication)  
**Brain consulted**: ✅ All 5 documented Python bugs verified AVOIDED in current code

---

### P0 — BLOCKING (immediate remediation required)

- **[P0.1]** [cg-adversarial] `scripts/team_brain/privacy.py:113` — **ReDoS via wildcard expansion in `_build_url_pattern()`**  
  **Why**: `TEAM-BRAIN.yml` `internal-url-patterns` entries like `*.*.*.*.*.*` expand to nested `.*` groups. Applied to a non-matching URL, Python's backtracking engine explores O(N^K) combinations — hangs indefinitely. User-supplied YAML is the attack surface.  
  **Fix**: Replace `.*` with `[^.]*` in the expansion (single-segment, no-dot wildcard), or reject patterns with more than one `*`:
  ```python
  escaped = re.escape(p).replace(r"\*", r"[^.]*")  # was: ".*"
  ```
  `[manual]`

- **[P0.2]** [cg-data-quality] `scripts/team_brain/schema.py:342` — **`tags` string silently explodes to characters**  
  **Why**: `list("pester")` → `['p','e','s','t','e','r']`. A JSONL line with `"tags": "pester"` (string instead of array) corrupts every downstream keyword score and cross-project pattern search with no error.  
  **Fix**:
  ```python
  raw_tags = data.get("tags", [])
  if not isinstance(raw_tags, list):
      raise ValueError(f"'tags' must be a JSON array, got {type(raw_tags).__name__}: {raw_tags!r}")
  tags = [str(t) for t in raw_tags]
  ```
  `[safe_auto]`

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-adversarial] `scripts/brain/scanner.py:83` — **Symlink following exposes content outside project root**  
  **Why**: `cg_docs.rglob("*.md")` follows symlinks. A symlink `.cg-docs/solutions/secret.md → /etc/hosts` causes the scanner to index `/etc/hosts` into the brain. `md_path.relative_to(cg_docs)` passes because the *link path* is inside `.cg-docs/`.  
  **Fix**: After resolving, verify symlink target is still under `cg_docs`:
  ```python
  resolved = md_path.resolve()
  cg_docs_real = cg_docs.resolve()
  if not str(resolved).startswith(str(cg_docs_real)):
      continue  # skip symlinks escaping the repo
  ```
  `[safe_auto]`

- **[P1.2]** [cg-adversarial] `scripts/team_brain/privacy.py:89` — **Windows forward-slash path bypass in privacy filter**  
  **Why**: `_WIN_PATH_RE = re.compile(r"[A-Z]:\\[^\s]...")` misses `E:/PovcalNet/data/file.dta` (Git Bash, WSL, R's `file.path()` all write forward slashes on Windows).  
  **Fix**: Match both separators:
  ```python
  _WIN_PATH_RE = re.compile(r"[A-Z]:[/\\][^\s\"'\n]+", re.IGNORECASE)
  ```
  `[safe_auto]`

- **[P1.3]** [cg-adversarial] `scripts/team_brain/privacy.py:92` — **Unix non-standard path prefixes bypass privacy filter**  
  **Why**: `_UNIX_PATH_RE` covers only `/home`, `/Users`, `/tmp`, `/var`, `/opt`, `/root`. Paths like `/mnt/data/wb384996/secret.csv`, `/srv/`, `/data/private/`, `/media/` are unredacted.  
  **Fix**: Expand to match all long absolute Unix paths:
  ```python
  _UNIX_PATH_RE = re.compile(r"/[A-Za-z][A-Za-z0-9_\-]*/[^\s\"'\n]{4,}")
  ```
  `[manual]` — verify no false positives on short paths like `/a/b/c`

- **[P1.4]** [cg-adversarial] `scripts/brain/renderer.py:641` — **Non-atomic directory operation: delete-then-write gap**  
  **Why**: `render_brain()` deletes all stale `BRAIN-NN.md` files before writing new ones. A kill between phases leaves an empty directory — no BRAIN content until next successful run. VS Code extension readers see an empty brain mid-operation.  
  **Fix**: Write new files first, then delete only the stale ones (those with a higher index than the new run produces):
  ```python
  # write all new partition files first (already atomic per-file via _write_atomic)
  # then prune stale files
  new_indices = set(range(1, len(topics_by_file) + 1))
  for existing in out_dir.glob("BRAIN-[0-9][0-9].md"):
      idx = int(existing.stem.split("-")[1])
      if idx not in new_indices:
          existing.unlink(missing_ok=True)
  ```
  `[manual]`

- **[P1.5]** [cg-version-control + cg-reproducibility] `.cg-docs/brain-index.json` — **110 of 156 edge targets are absolute machine-specific paths**  
  **Why**: `_resolve_path()` in `edge_detector.py` returns an absolute `Path`; this is serialized verbatim in `edges[].target` in `brain-index.json`. Produces `E:/PovcalNet/01.personal/wb384996/...` — non-functional on any other clone and exposes staff directory structure.  
  **Fix**: In `detect_edges()`, relativize the target before storing in `Edge`:
  ```python
  target_abs = _resolve_path(bval, root)
  if target_abs is not None:
      root_resolved = root.resolve()
      try:
          target_rel = target_abs.relative_to(root_resolved)
      except ValueError:
          target_rel = target_abs
      edges.append(Edge(source=entity.path, target=target_rel, kind=edge_kind))
  ```
  `[safe_auto]` (regenerate `brain-index.json` after fix)

- **[P1.6]** [cg-data-quality] `scripts/team_brain/schema.py:345` — **`confidence` float is not bounds-checked**  
  **Why**: Values like `-0.5` or `99.0` silently corrupt curation ranking. The dataclass docstring states confidence is in base 1.0 with boost — implying domain is [0, 1+].  
  **Fix**:
  ```python
  confidence = float(data.get("confidence", 1.0))
  if confidence < 0.0:
      raise ValueError(f"'confidence' must be ≥ 0.0, got {confidence}")
  ```
  `[safe_auto]`

- **[P1.7]** [cg-data-quality] `scripts/team_brain/schema.py:339` — **`date` field not ISO-validated**  
  **Why**: `"date": "May 2026"` or `"date": ""` is silently accepted and produces incorrect supersession and chronological sorting.  
  **Fix**:
  ```python
  date_str = str(data["date"]).strip()
  if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
      raise ValueError(f"'date' must be ISO format YYYY-MM-DD, got: {date_str!r}")
  ```
  `[safe_auto]`

- **[P1.8]** [cg-data-quality] `scripts/team_brain/schema.py:290` — **`VALID_SCHEDULES` defined but never enforced**  
  **Why**: `schedule: biweekly` silently becomes a `TeamBrainConfig` with an invalid `curation_schedule` string. The constant was added precisely to validate this field but the check is missing.  
  **Fix** (after schedule extraction):
  ```python
  if schedule not in VALID_SCHEDULES:
      raise ValueError(
          f"TEAM-BRAIN.yml: 'curation.schedule' must be one of {list(VALID_SCHEDULES)}, got {schedule!r}"
      )
  ```
  `[safe_auto]`

- **[P1.9]** [cg-data-quality] `scripts/team_brain/schema.py:344` — **`entry-path` has no path traversal guard**  
  **Why**: A JSONL entry with `"entry-path": "../../etc/shadow"` is stored in `PatternEntry.entry_path` and could be used by downstream code to reference files outside the entries directory. The edge detector has `_resolve_path()` for exactly this — the same protection is missing in schema validation.  
  **Fix**:
  ```python
  ep = str(data["entry-path"]).strip()
  if ".." in Path(ep).parts or Path(ep).is_absolute():
      raise ValueError(f"'entry-path' must be a relative path inside entries/, got: {ep!r}")
  ```
  `[safe_auto]`

- **[P1.10]** [cg-testing] `scripts/team_brain/tests/test_privacy.py` — **`private-sections` non-list path untested — silent privacy failure**  
  **Why**: `apply_frontmatter_filter` with `private-sections: "Internal Notes"` (string) warns but silently skips stripping — private content leaks through. No test verifies this contract.  
  **Fix**: Add to `test_privacy.py`:
  ```python
  def test_frontmatter_private_sections_non_list_warns_and_skips():
      content = "---\n---\n## Internal Notes\n\nSecret.\n\n## End\n\nPublic."
      with pytest.warns(UserWarning, match="not a list"):
          filtered, blocked, _ = apply_frontmatter_filter(
              content, {"private-sections": "Internal Notes"}
          )
      assert "Secret" in filtered  # confirm stripping was skipped
  ```
  `[safe_auto]`

- **[P1.11]** [cg-architecture] `scripts/cg_index.py:11` / `scripts/brain/__init__.py` — **`__version__` duplicated in two files**  
  **Why**: Both define `__version__ = "0.2.0"` independently. A version bump will diverge and `cg-index --version` will return the wrong value.  
  **Fix**: Remove `__version__` from `cg_index.py` and import it from `brain`:
  ```python
  from brain import __version__  # already imported in the do_brain branch
  ```
  `[safe_auto]`

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-adversarial] `scripts/brain/scanner.py:98` — **Unbounded file read: memory exhaustion**  
  **Why**: `md_path.read_text()` with no size check. A 500 MB markdown file in `.cg-docs/` exhausts memory; three concurrent processes could OOM the machine.  
  **Fix**: `if md_path.stat().st_size > 10 * 1024 * 1024: warnings.warn(...); continue` `[safe_auto]`

- **[P2.2]** [cg-adversarial] `scripts/team_brain/privacy.py:410` — **LLM replacement strings bypass regex filter**  
  **Why**: `apply_llm_redactions()` applies LLM-supplied `replacement` strings without re-filtering. A jailbroken LLM could return `"replacement": "C:\\Users\\secret.txt"`, injecting an absolute path that the regex layer would otherwise catch.  
  **Fix**: After applying all LLM replacements, re-run `apply_regex_filter()` on the result. `[manual]`

- **[P2.3]** [cg-adversarial] `scripts/team_brain/config.py` — **`_find_local_config()` walks to filesystem root**  
  **Why**: A `compound-gpid.local.md` at an ancestor directory (e.g., `/home/user/`) pointing to `attacker/evil` repo would silently take effect for any nested project.  
  **Fix**: Stop the walk when a `.git/` directory or `compound-gpid.md` is found, not at filesystem root. `[manual]`

- **[P2.4]** [cg-adversarial] `scripts/team_brain/privacy.py:226` — **ATX heading with closing `#` bypasses section stripping**  
  **Why**: `## Internal Notes ##` captures title as `"Internal Notes ##"`, which doesn't match `"Internal Notes"` in `lower_names`. The private section silently leaks.  
  **Fix**: Strip trailing `#` from captured title:
  ```python
  title = m.group(2).strip().rstrip("#").strip().lower()
  ```
  `[safe_auto]`

- **[P2.5]** [cg-data-quality] `scripts/brain/__init__.py:93` — **Scalar `tags: pester` silently dropped in Entity**  
  **Why**: `Entity.tags` checks `isinstance(raw, list)` and returns `[]` for a bare scalar. Any entity with a single unquoted tag loses its keyword signal.  
  **Fix**:
  ```python
  if isinstance(raw, str) and raw.strip():
      return [raw.strip()]
  ```
  `[safe_auto]`

- **[P2.6]** [cg-data-quality] `scripts/team_brain/schema.py:231` — **Bare `#` in URL fragments truncates value**  
  **Why**: `if "#" in value:` fires on `https://github.com/org/repo#readme`, yielding `https://github.com/org/repo`. The correct guard (from `brain/utils.py`) requires a space before `#`.  
  **Fix**: `if " #" in value: value = value.split(" #")[0].rstrip()` `[manual]`

- **[P2.7]** [cg-data-quality] `scripts/team_brain/schema.py:338` — **Empty `id`/`pattern` pass required-field check**  
  **Why**: `"id": ""` has the key present, so it passes the required-fields check, but creates dedup-invisible entries.  
  **Fix**: Add non-empty guards: `if not entry_id: raise ValueError("'id' must be a non-empty string.")` `[safe_auto]`

- **[P2.8]** [cg-reproducibility] `scripts/brain/utils.py:340` — **CRLF line endings on Windows in all output files**  
  **Why**: `os.fdopen(fd, "w", ...)` in `_write_atomic()` uses platform-default newline translation. `BRAIN.md`, `BRAIN-log.md`, `BRAIN-NN.md`, and `brain-index.json` have CRLF on Windows, LF on macOS — byte-identical commits impossible.  
  **Fix**: `os.fdopen(fd, "w", encoding="utf-8", newline="\n")` `[safe_auto]`

- **[P2.9]** [cg-code-quality] `scripts/cg_index.py:498` — **`warnings.catch_warnings` scope too narrow**  
  **Why**: `build_digest()` is called outside the `catch_warnings(record=True)` block; its `warnings.warn()` calls escape unformatted.  
  **Fix**: Widen the `catch_warnings` block to cover all legacy path operations. `[manual]`

- **[P2.10]** [cg-architecture] `scripts/brain/__init__.py` — **No `__all__` — stdlib names leak as public API**  
  **Why**: `from brain import *` would import `date`, `Path`, `Any`, `Dict`, etc.  
  **Fix**: `__all__ = ["Entity", "Topic", "Edge", "BrainData", "build_brain", "__version__"]` `[safe_auto]`

- **[P2.11]** [cg-performance] `scripts/brain/clusterer.py` — **O(d²) inner loop with no fanout cap**  
  **Why**: A keyword appearing in `d` entities creates `d(d−1)/2` pair iterations. At 500 entities, a ubiquitous keyword like `"pester"` generates ~44K iterations alone.  
  **Fix**: Skip high-frequency posting lists (`len(indices) > 100`). `[manual]`

- **[P2.12]** [cg-performance] `scripts/brain/clusterer.py` — **`sum(kw_dict.values())` recomputed on every Jaccard call**  
  **Why**: Each entity participates in O(n) pairs; its sum is recomputed O(n) times. Pre-compute once per entity.  
  **Fix**: `kw_sums = [sum(kd.values()) for kd in kw_dicts]` before the loop; pass into `_weighted_jaccard`. `[safe_auto]`

- **[P2.13]** [cg-testing] `scripts/brain/tests/test_scanner.py` — **Unreadable file path untested**  
  **Why**: The `except (OSError, UnicodeDecodeError)` warning/skip branch in `scan_all()` is unverified; BOM-less Latin-1 files are realistic on Windows.  
  **Fix**: See test code in cg-testing report P2.2. `[safe_auto]`

- **[P2.14]** [cg-testing] `scripts/brain/tests/test_init.py` — **BOM prefix strip untested**  
  **Why**: PowerShell here-strings on Windows write BOM-prefixed files. Without a test, a BOM regression silently breaks all frontmatter parsing.  
  **Fix**: `fm = parse_frontmatter("\ufeff---\ntitle: BOM Test\n---\n")` → `assert fm["title"] == "BOM Test"` `[safe_auto]`

- **[P2.15]** [cg-testing] `scripts/team_brain/tests/test_privacy.py` — **`build_llm_filter_prompt()` has zero tests**  
  **Why**: Any template regression (missing `{content}` placeholder) is invisible. Function is imported but never called in tests.  
  **Fix**: `assert content in build_llm_filter_prompt(content)` `[safe_auto]`

- **[P2.16]** [cg-documentation] `scripts/team_brain/__init__.py` — **Module docstring imports from non-existent `team_brain.push`**  
  **Why**: Running the usage example raises `ImportError`. A developer reads the docstring and gets an incorrect picture of the package state.  
  **Fix**: Add `# Note: Phase 2 — only schema.py, config.py, and privacy.py are implemented.` `[manual]`

- **[P2.17]** [cg-documentation] `scripts/team_brain/privacy.py` — **Layer numbering mismatch in `run_privacy_filter()` inline comments**  
  **Why**: Module docstring assigns layers by role (Regex = layer 1); function body runs `# Layer 2: Frontmatter` first. Contradictory.  
  **Fix**: Rename to `# Step 1: Frontmatter filter` / `# Step 2: Regex filter` / `# Step 3: LLM filter` `[safe_auto]`

- **[P2.18]** [cg-version-control] `SCHEMA_VERSION` — **Not updated to reflect brain engine introduction**  
  **Why**: Contains `2026-05-15-wiki-scope-fields`. The brain engine introduces new output format (`brain-index.json`, `BRAIN-NN.md`). Install/update scripts test against this file.  
  **Fix**: Update to `2026-05-20-brain-engine` and verify `install.ps1`/`update.ps1` references. `[manual]`

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `scripts/team_brain/privacy.py:306` — `warnings.warn()` missing `stacklevel=2`. **Fix**: Add `stacklevel=2`. `[safe_auto]`

- **[P3.2]** [cg-code-quality] `scripts/team_brain/schema.py:365` — `import warnings` inside function body. **Fix**: Move to module-level imports. `[safe_auto]`

- **[P3.3]** [cg-architecture] `scripts/brain/renderer.py:88` — `_sanitize_inline()` doesn't escape `[`. A title like `[Fix] Something` produces nested `[[Fix] Something](path)` in markdown. **Fix**: Add `.replace("[", "\\[")`. `[safe_auto]`

- **[P3.4]** [cg-architecture] `scripts/team_brain/__init__.py` — `ClusterStrategy` Protocol not re-exported from `brain/__init__.py`. Callers must import from internal `brain.clusterer`. **Fix**: Add to `brain/__init__.py` + `__all__`. `[safe_auto]`

- **[P3.5]** [cg-reproducibility] `scripts/team_brain/privacy.py:77` — `FilterResult.summary()` iterates a `set` → non-deterministic LLM type listing. **Fix**: `sorted({...})` instead of `list({...})`. `[safe_auto]`

- **[P3.6]** [cg-performance] `scripts/brain/renderer.py` — `text.split()` allocates full word-list on every `_estimate_tokens()` call. **Fix**: `word_count = text.count(" ") + text.count("\n") + 1`. `[safe_auto]`

- **[P3.7]** [cg-documentation] `scripts/brain/clusterer.py:88` — `_UnionFind.find()`, `.union()`, `.__init__()` have no docstrings. Path compression is non-obvious. **Fix**: Add one-liners. `[safe_auto]`

- **[P3.8]** [cg-documentation] `scripts/team_brain/schema.py` — `load_patterns_from_jsonl()` missing `Example:` block. **Fix**: Add `>>> entries = load_patterns_from_jsonl(Path("patterns/compound-gpid.jsonl"))`. `[safe_auto]`

- **[P3.9]** [cg-testing] `scripts/team_brain/tests/test_schema.py` — `PatternEntry` serialization roundtrip not tested with `superseded_by` set — key name `superseded-by` vs `superseded_by` trap. **Fix**: Add roundtrip test with non-null `superseded_by`. `[safe_auto]`

- **[P3.10]** [cg-testing] `scripts/brain/tests/test_init.py` — Block-list `tags:` syntax and duplicate-key warning paths untested. **Fix**: See cg-testing P2.5 and P2.6 test code. `[safe_auto]`

- **[P3.11]** [cg-version-control] `.cg-docs/reviews/2026-05-19-knowledge-brain-engine-batch-a-review.md` — Contains literal absolute developer path `E:/PovcalNet/01.personal/wb384996/...` in review text. **Fix**: Replace with `<machine-root>/...`. `[safe_auto]`

- **[P3.12]** [cg-performance] `scripts/brain/edge_detector.py:102` — `root.resolve()` called per-invocation inside `_resolve_path()`. Adds ~500–1,500 redundant stat syscalls. **Fix**: Pre-compute `root_resolved = root.resolve()` once in `detect_edges()`. `[safe_auto]`

---

### ✅ Passed / Clean

- **cg-learnings-researcher**: All 5 documented Python brain bugs (sorted reverse, try-except scope, warnings scope, non-atomic write, helper-not-wired) are **AVOIDED** in current code. The solutions in `.cg-docs/solutions/bugs/` directly informed the correct implementations.
- **cg-code-quality**: `brain/` modules (scanner, extractor, clusterer, edge_detector, renderer) are clean — no PEP 8 violations, regexes pre-compiled, no anti-patterns.
- **cg-reproducibility**: Entity ordering, topic ordering, clusterer determinism, and `brain-index.json` entity paths are all reproducible. No random operations.
- **cg-version-control**: No secrets, credentials, or API keys found. Commit messages follow conventional commits. `.gitignore` correctly excludes `tests/last-run.json`, `__pycache__`, `.env`.
- **cg-performance**: For current corpus size (~400 entities), all modules are fast. Bottleneck is clustering (P2.11) which only materialises at 500+ entities.

---

### ⚠️ Merge gate recommendation

**Block merge on**: P0.1, P0.2, P1.1–P1.5 (adversarial + absolute paths), P1.6–P1.9 (schema validation), P1.10 (privacy test gap), P1.11 (__version__)

**Safe to defer**: P2.11 (performance, only affects 500+ entities), P2.16 (docstring), P3.x (all advisory or minor).
