---
plan: .cg-docs/plans/2026-05-07-python-utility-layer-cg-index.md
date: 2026-05-07
depth: thorough
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: open
  P2.1: fixed
  P2.2: fixed
  P2.3: open
  P2.4: fixed
  P2.5: open
  P2.6: fixed
  P2.7: fixed
  P2.8: open
  P2.9: open
  P2.10: open
  P2.11: open
  P2.12: open
  P2.13: fixed
  P2.14: fixed
  P2.15: fixed
  P2.16: fixed
  P2.17: fixed
  P2.18: fixed
  P2.19: fixed
  P2.20: fixed
  P2.21: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: open
  P3.7: open
---

## Review Report

**Review depth**: thorough
**Files reviewed**: 19 (12 modified tracked + 7 new/untracked)
**Findings**: 31 (P0: 0, P1: 3, P2: 21, P3: 7)

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-adversarial + cg-data-quality + cg-reproducibility] `scripts/cg_index.py`:383 — `sort_key` crashes with unhandled `ValueError` on non-ISO-8601 date strings
  **Why**: `_coerce()` keeps `date: yes`, `date: TBD`, `date: 2024/01/15` as-is. `sort_key` calls `int(d.replace("-",""))` which raises `ValueError` — not caught by the `except OSError` in `main()`. A single mis-typed date field breaks the entire run with a raw traceback.
  **Fix**: Wrap in `try/except ValueError`, fall back to sort position 0.
  **Tag**: [safe_auto]

- **[P1.2]** [cg-adversarial] `.github/agents/cg-learnings-researcher.agent.md`:37 — Tier 3 (direct `.cg-docs/solutions/` scan) missing untrusted-content guard
  **Why**: Tier 1 (DIGEST.md) and Tier 2 (search-index.json) both carry explicit untrusted-content notes. Tier 3 delivers raw solution file body to the model with no guarding — a prompt injection surface when an adversarial file is added to `.cg-docs/solutions/`.
  **Fix**: Add the same untrusted-content note to the Tier 3 section.
  **Tag**: [safe_auto]

- **[P1.3]** [cg-testing] `tests/install.Tests.ps1`:289 — Phase 1 smoke test permanently `-Pending` despite Phase 2 deliverables complete
  **Why**: Comment says "becomes active after Phase 2 delivers cg_index.py." Phase 2 is done. The double-guard means the CMD wrapper's Python-probe logic is never exercised as an end-to-end test.
  **Fix**: Remove `-Pending` guards and add a Python-availability skip guard matching the pattern in `cg-index.Tests.ps1`.
  **Tag**: [manual]

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-data-quality] `scripts/cg_index.py`:145 — Empty-value YAML key (`title:`) starts a block-list and flushes `[]`, making `SolutionEntry.title` return `"[]"`
  **Why**: A key with no value is ambiguous; the parser begins a block-list collection. If no `- item` follows, `result["title"] = []` is stored, the entry passes `if not fm`, and appears in the index with title `"[]"`.
  **Fix**: Only flush non-empty block lists.
  **Tag**: [safe_auto]

- **[P2.2]** [cg-code-quality + cg-data-quality] `scripts/cg_index.py`:75 — `_parse_inline_list` annotated `-> Optional[List[str]]`; should be `Optional[List[Any]]`
  **Why**: `_coerce()` returns `bool`, `int`, or `str`. The return type annotation is incorrect and misleads callers and type checkers.
  **Fix**: Change to `Optional[List[Any]]` and `items: List[Any] = []`.
  **Tag**: [safe_auto]

- **[P2.3]** [cg-adversarial + cg-data-quality] `scripts/cg_index.py`:87 — `_parse_inline_list` regex has ReDoS potential and silently merges items containing apostrophes
  **Why**: The nested lookahead `(?=(?:[^\"']*[\"'][^\"']*[\"'])*[^\"']*$)` treats `"` and `'` as interchangeable; `"it's"` breaks parity and merges adjacent items. At 50 unbalanced items, backtracking grows exponentially.
  **Fix**: Replace with `csv.reader` (stdlib) or a character-by-character quote-tracking split.
  **Tag**: [manual]

- **[P2.4]** [cg-adversarial] `scripts/cg_index.py`:404, 422 — Non-atomic writes via `Path.write_text()` leave corrupt files on process kill
  **Why**: If killed mid-write, `search-index.json` or `DIGEST.md` are left partially written. The next agent read gets invalid JSON or truncated markdown. `install.sh` already uses the correct temp-file + `os.replace()` pattern.
  **Fix**: Write to a temp file in the same directory, then `os.replace(tmp, out_path)`.
  **Tag**: [safe_auto]

- **[P2.5]** [cg-adversarial] `scripts/cg_index.py`:325 — `rglob("*.md")` follows symlinks; out-of-tree symlinks leak absolute paths into `search-index.json`
  **Why**: `relative_to(root)` fails on a symlink target outside `solutions_dir`; the fallback stores the raw absolute path (including username/directory layout) in the committed artifact.
  **Fix**: Resolve both `md_file` and `solutions_dir`, check `is_relative_to` before processing; skip and warn on out-of-tree files.
  **Tag**: [manual]

- **[P2.6]** [cg-reproducibility] `scripts/cg_index.py` — No Python version guard; install scripts accept Python 2.x
  **Why**: `--version` probe matches `Python 2.7.18`. Install succeeds, then `from dataclasses import dataclass` fails with a cryptic `ImportError`. The script claims Python 3.8+.
  **Fix**: Add version guard in `cg_index.py` after module docstring (`sys.version_info < (3, 8)` check). Tighten install script checks separately.
  **Tag**: [safe_auto] for script guard; [manual] for install scripts

- **[P2.7]** [cg-reproducibility + cg-code-quality] `scripts/install.sh`:~250 — heredoc for `bin/cg-index` generates different header than the committed file, causing git noise on every macOS install
  **Why**: Committed: `# bin/cg-index — ... (macOS)`. Generated: `# cg-index — ... (generated by install.sh)`. Every `cg-update` on macOS diffs `bin/cg-index`.
  **Fix**: Align `install.sh` heredoc to exactly match the committed file.
  **Tag**: [safe_auto]

- **[P2.8]** [cg-code-quality] `scripts/install.sh`:~103 — bare `except: pass` in inline Python here-docs silently swallows `KeyboardInterrupt`
  **Why**: Inner cleanup block `except: pass` catches everything. Per `cg-skill-python-best-practices`: never use bare `except:`.
  **Fix**: Replace with `except OSError: pass` in both occurrences.
  **Tag**: [manual]

- **[P2.9]** [cg-version-control] `.gitignore` — No policy decision on whether `DIGEST.md` and `search-index.json` should be tracked or excluded
  **Why**: Both are generated artifacts with a changing `generated:` datestamp, producing noisy diffs on every run. But `.gitignore` has a blanket "`.cg-docs/` is institutional knowledge — do NOT add" comment.
  **Fix**: Decide: (a) track and commit as artifacts (add to pre-commit/release workflow), or (b) add specific exclusions with a note explaining these are derived outputs.
  **Tag**: [manual]

- **[P2.10]** [cg-architecture] `install.ps1`:~161 — `Copy-Item` for `cg-index.cmd` is always a self-copy (no-op)
  **Why**: `$CompoundGpidDir = $PSScriptRoot` makes source and destination identical. The block misleads maintainers about what is happening.
  **Fix**: Replace with an existence check and descriptive comment clarifying the file is already in place.
  **Tag**: [manual]

- **[P2.11]** [cg-learnings-researcher] `tests/cg-index.Tests.ps1` — 16 `Get-Content -Raw` calls missing `-Encoding UTF8`
  **Why**: `cg_index.py` writes with `ensure_ascii=False`. PS5.1 defaults to Windows-1252, silently breaking comparisons on any non-ASCII content. (Past learning: `.cg-docs/solutions/bugs/2026-04-17-ps51-get-content-default-encoding-breaks-equality-check.md`)
  **Tag**: [manual]

- **[P2.12]** [cg-learnings-researcher] `tests/cg-index.Tests.ps1`:366 — `Invoke-PyHelper` builds `sys.path.insert(0, '...')` with single-quote delimiters; breaks on repo paths with apostrophes
  **Why**: Path containing `'` produces a Python syntax error in the generated `.py` file.
  **Fix**: Use raw string delimiter: `$pathLine = 'sys.path.insert(0, r"' + $pyDir + '")'`
  **Tag**: [manual]

- **[P2.13]** [cg-testing] `tests/cg-index.Tests.ps1`:123 — `--index` mode untested with archived/non-active entry
  **Why**: The behavioral contract "index includes all statuses" is unverified. A status filter accidentally added to `build_index()` would go undetected.
  **Fix**: Write a second fixture with `status: archived`; assert `$json.count | Should -Be 2`.
  **Tag**: [safe_auto]

- **[P2.14]** [cg-testing] `tests/cg-index.Tests.ps1`:162 — No test for missing `status` field treated as active in DIGEST
  **Why**: `e.status in ("active", "")` silently includes entries with no `status` field. This path is unverified.
  **Fix**: Add `$script:NoStatusEntry` fixture and assert it appears in DIGEST output.
  **Tag**: [safe_auto]

- **[P2.15]** [cg-testing] `tests/bash-scripts.Tests.ps1`:190 — No test asserting `"shared"` is in `MANAGED_DIRS` in `link.sh`
  **Why**: `scripts/link.sh` was modified to add `"shared"`; no test covers this change.
  **Fix**: Add `It "includes 'shared' in MANAGED_DIRS" { $content | Should -Match '"shared"' }`.
  **Tag**: [safe_auto]

- **[P2.16]** [cg-testing] `tests/cg-index.Tests.ps1`:420 — No test for fenced code block exclusion in `extract_summary`
  **Why**: The `in_fence` state machine in `extract_summary` is untested. A regression could silently include raw code in summaries.
  **Fix**: Add `Invoke-PyHelper2` test with a fenced block in `## Problem`; assert fence markers are absent from summary.
  **Tag**: [safe_auto]

- **[P2.17]** [cg-documentation] `scripts/cg_index.py` — `main()`, `to_index_record()`, `to_digest_block()` missing docstrings
  **Why**: `main()` is the entry point (accepts `argv` override); callers have no documented contract. The two methods define the schema of the two output artifacts.
  **Tag**: [safe_auto]

- **[P2.18]** [cg-documentation] `scripts/install.sh` header omits python3 check; `scripts/unlink.sh` omits python3 requirement
  **Why**: Users reading headers to understand prerequisites will miss the python3 dependency on both scripts.
  **Tag**: [safe_auto]

- **[P2.19]** [cg-testing] `tests/cg-index.Tests.ps1`:134 — `$output` captured in `--index` describe block but never asserted on
  **Why**: Misleads readers and silently captures mixed stdout+stderr without validation.
  **Fix**: Add `$output | Should -Match '\[cg-index\]'` or remove the unused capture.
  **Tag**: [safe_auto]

- **[P2.20]** [cg-testing] `tests/bash-scripts.Tests.ps1`:75 — No test that `install.sh` creates the `cg-index` wrapper
  **Why**: The `cg-index` generation block in `install.sh` is separate from the `for cmd in link unlink update` loop. Accidental deletion would go undetected.
  **Fix**: Add `$content | Should -Match 'cg-index'` to the wrapper-creation test.
  **Tag**: [safe_auto]

- **[P2.21]** [cg-architecture] `scripts/cg_index.py` — `scan_solutions` warns on no-frontmatter but silently produces entries with missing required fields (`title`, `date`)
  **Why**: An entry with frontmatter but no `title` or `date` gets `title = slug` and `date_str = ""` with no warning, sorts last unpredictably, and appears in both index and digest with no signal to the author.
  **Fix**: After `fm = parse_frontmatter(text)`, check for missing required fields and emit `warnings.warn`.
  **Tag**: [safe_auto]

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality + cg-performance] `scripts/cg_index.py`:49-52, 181, 212, 87 — PEP 8 E221 alignment padding on module-level constants; inline regexes not compiled at module level
  **Fix**: Remove alignment spaces; add `_PROBLEM_HEADING_RE` and `_COMMA_SPLIT_RE` as module-level patterns.
  **Tag**: [safe_auto]

- **[P3.2]** [cg-code-quality] `scripts/cg_index.py`:383 — `sort_key` missing return type annotation
  **Fix**: `def sort_key(e: SolutionEntry) -> Tuple[int, str]:`
  **Tag**: [safe_auto]

- **[P3.3]** [cg-code-quality] `scripts/cg_index.py`:313 — Redundant `f""` (no interpolation placeholders)
  **Fix**: Change `f""` to `""`.
  **Tag**: [safe_auto]

- **[P3.4]** [cg-documentation] `scripts/cg_index.py` — `build_arg_parser()`, `_truncate()`, and `SolutionEntry` property docstrings missing
  **Tag**: [safe_auto]

- **[P3.5]** [cg-architecture] `scripts/cg_index.py`:408 — `build_digest` silently promotes no-`status` entries with no warning to author
  **Fix**: Emit `warnings.warn` for entries included due to empty status string.
  **Tag**: [safe_auto]

- **[P3.6]** [cg-architecture] `scripts/cg_index.py` — `scan_solutions` always calls `extract_summary()` even in `--index`-only runs (wasted work for large corpora)
  **Fix**: Add `want_summary: bool = False` parameter or compute summary lazily in `to_digest_block()`.
  **Tag**: [manual]

- **[P3.7]** [cg-testing] `tests/cg-index.Tests.ps1`:357, 399 — `Invoke-PyHelper` and `Invoke-PyHelper2` are functionally identical; temp `.py` files never cleaned up after use
  **Tag**: [advisory]

---

### Advisory notes (filed, not applied)

- [cg-code-quality] `scripts/cg_index.py`: `print()` used for output — intentional (stdlib-only constraint prohibits loguru); add inline comment `# loguru unavailable — stdlib-only script`.
- [cg-version-control] All 17 files unstaged; commit in logical groups per conventional commits convention.
- [cg-adversarial] `bin/cg-index.cmd`: unquoted `%*` allows CMD metacharacter injection in automated callers — low practical risk for interactive use.
- [cg-performance] Frontmatter-strip logic duplicated between `parse_frontmatter` and `extract_summary` — extract a shared `_strip_frontmatter()` helper if Stage 2 adds more consumers.
- [cg-reproducibility] `date.today().isoformat()` makes generated artifacts non-reproducible across calendar days — expected behavior, but tests comparing full output should mock `date.today`.

---

### Passed

- **cg-version-control**: No credentials, secrets, or PII found
- **cg-version-control**: Feature branch `feat/python-utility-layer` in use
- **cg-learnings-researcher**: PS5.1 encoding patterns correctly applied; `print_yellow → >&2` fix from past learning applied; temp-file Python pattern correctly applied
- **cg-architecture**: Clean three-layer design (indexer → wrappers → prompt integration); `SolutionEntry` is a well-designed intermediate representation; untrusted-content notes in `cg-learnings-researcher` are sound
