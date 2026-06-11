---
date: 2026-06-06
plan: .cg-docs/plans/2026-06-05-cg-review-token-cost-phase3.md
depth: architecture
branch: codex/context-model-audit-phase1
findings:
  P1.1: fixed
  P1.2: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: skipped
  P2.6: skipped
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
  P2.19: fixed
  P2.20: fixed
  P2.21: fixed
  P2.22: fixed
  P2.23: fixed
  P2.24: fixed
  P2.25: fixed
  P2.26: skipped
  P2.27: skipped
  P2.28: skipped
  P2.29: fixed
  P2.30: fixed
  P3.1: advisory
  P3.2: advisory
  P3.3: advisory
  P3.4: fixed
  P3.5: fixed
  P3.6: advisory
  P3.7: fixed
  P3.8: advisory
  P3.9: fixed
  P3.10: advisory
  P3.11: advisory
  P3.12: advisory
  P3.13: fixed
  P3.14: advisory
  P3.15: advisory
  P3.16: fixed
  P3.17: fixed
  P3.18: fixed
  P3.19: fixed
  P3.20: advisory
  P3.21: advisory
  P3.22: fixed
  P3.23: fixed
  P3.24: advisory
  P3.25: fixed
---

## Review Report

**Review mode**: architecture (auto-escalated from normal: new Python module with cross-module imports)
**Files reviewed**: 14 changed files (19 total including artifacts), branch `codex/context-model-audit-phase1` vs `main`
**Agents dispatched**: cg-code-quality, cg-testing, cg-documentation, cg-version-control, cg-reproducibility, cg-performance, cg-architecture, cg-data-quality
**Findings**: 57 (P0: 0, P1: 2, P2: 30, P3: 25)

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-documentation] `scripts/cg_audit_context.py:189` — `parse_model_guide()` is silently broken; drift detection always returns `{}`
  **Why**: The rewritten `docs/model-guide.md` no longer contains `### Prompts` / `### Agents` H3 headers with per-file assignment tables. `parse_model_guide()` depends on those headers and silently returns `{}` when they are absent. As a result, `build_model_inventory()` computes `drift = []` unconditionally — the "Model Drift" section of every audit report will permanently show "None" regardless of actual drift.
  **Fix**: Either (a) restore an H3-keyed assignment table in `docs/model-guide.md` for non-ordinary prompts, or (b) rework `parse_model_guide()` to derive expected models from `ORDINARY_MODEL_PICKER_PROMPTS` and frontmatter directly (no guide cross-check). Update the docstring to reflect whichever path is chosen. `[manual]`

- **[P1.2]** [cg-testing] `scripts/tests/test_audit_context.py:281` — `test_disclaimer_present` uses `Path.cwd()` making the test CWD-fragile
  **Why**: `audit.build_report(Path.cwd())` resolves differently depending on the directory from which pytest is invoked. If run from `scripts/` or any subdirectory, it may scan zero files or a completely different tree. The integration test at line 290 correctly uses `Path(__file__).resolve().parents[2]`; this test does not.
  **Fix**: Replace `Path.cwd()` with `Path(__file__).resolve().parents[2]` to anchor to the repo root regardless of invocation directory. `[safe_auto]`

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-data-quality] `scripts/cg_audit_context.py:383` — `chars` compared against token threshold; false-positive review flags
  **Why**: `chars >= THRESHOLD_PROMPT_IMMEDIATE` uses raw character counts against a *token* threshold (3000). A 3000-character file has ≈750 tokens — well below the 1500-token review threshold — yet triggers a "prompt size exceeds review threshold" flag. Every prompt in the 3000–5999 char / <1500 token range receives a false-positive review classification in the JSON/Markdown output.
  **Fix**: Replace `chars >= THRESHOLD_PROMPT_IMMEDIATE` with `tokens >= THRESHOLD_PROMPT_REVIEW` (the token-based gate already on the right side of the `or`). `[safe_auto]`

- **[P2.2]** [cg-data-quality] `scripts/cg_audit_context.py:205` — Model guide separator filter only matches 6-dash strings; standard `---` rows pass through as filenames
  **Why**: `if … cells[0] in ("File", "------"):` — after splitting a standard Markdown separator row `| --- | --- |`, the first cell is `"---"`, not `"------"`. The separator passes the filter and `guide["---"] = cells[1].strip()` inserts a garbage entry into the model dict, silently corrupting drift detection.
  **Fix**: `if len(cells) < 2 or cells[0] in ("File",) or cells[0].startswith("---") or cells[0].startswith(":---"):` `[safe_auto]`

- **[P2.3]** [cg-data-quality] `scripts/cg_audit_context.py:176` — `tools` field is polymorphic (`null | string | string[]`) with no schema normalization
  **Why**: `fm.get("tools")` returns `None`, a `list[str]`, or a bare `str` depending on the YAML value. The output JSON contains both `null` and `["read", "search"]` for the same field. Downstream consumers must defensively handle three types for a single field with no documented schema.
  **Fix**: Normalize at emission time: `list[str]` passthrough, `str` → `[str]`, `None` → `None`. Document `null` as "tools not declared in frontmatter." `[manual]`

- **[P2.4]** [cg-architecture] `scripts/cg_audit_context.py:512` — `write_outputs` uses non-atomic writes; partial files on crash
  **Why**: `json_path.write_text(...)` and `md_path.write_text(...)` write in-place. A crash or keyboard interrupt mid-write leaves a silently corrupt output file. `brain.utils` already exports `write_atomic()` (temp-file + rename pattern) available from the existing import.
  **Fix**: Import `write_atomic` from `brain.utils` and replace both `write_text` calls in `write_outputs` with `write_atomic(path, content)`. `[safe_auto]`

- **[P2.5]** [cg-architecture] `scripts/cg_audit_context.py:92` — `ORDINARY_MODEL_PICKER_PROMPTS` hardcoded allowlist will silently drift as the prompt library grows
  **Why**: When a new prompt intentionally omits `model:`, it will be incorrectly classified as `"missing"` until a developer manually updates this constant. The set will silently drift out of date.
  **Fix**: Introduce an optional `model-picker: true` frontmatter field. In `extract_model_declarations`, check `fm.get("model-picker") is True` instead of path membership. The existing constant can remain as a transitional allowlist with a comment marking it for removal once frontmatter is backfilled. `[manual]`

- **[P2.6]** [cg-architecture + cg-performance] `scripts/cg_audit_context.py:128,167,256,293,313` — Same prompt/agent files read from disk up to 5× per audit run
  **Why**: `scan_files`, `extract_model_declarations`, `build_reference_matrix`, `build_dispatch_burden`, and `detect_duplicates` each call `path.read_text()` independently. ~250 disk reads where 50 suffice; scales linearly as the corpus grows.
  **Fix**: In `scan_files`, add `"content": content` to each record. Downstream functions already receive the file record dict — they can access `file_record["content"]` instead of calling `path.read_text()`. `[manual]`

- **[P2.7]** [cg-architecture] `scripts/cg_audit_context.py:128` — `UnicodeDecodeError` during file read swallows path context; aborts entire audit run
  **Why**: When `path.read_text(encoding="utf-8-sig")` raises `UnicodeDecodeError`, the exception propagates to `main()`'s handler which prints `ERROR: {exc}` with no filename. The operator cannot identify which file triggered the failure, and the entire audit aborts.
  **Fix**: Wrap each `read_text` call in its loop body with a localized `try/except UnicodeDecodeError as exc: warnings.warn(f"Skipping {path}: {exc}"); continue`. `[safe_auto]`

- **[P2.8]** [cg-architecture + cg-code-quality + cg-data-quality] `scripts/cg_audit_context.py:512` — `write_outputs` silently no-ops on invalid `fmt` values
  **Why**: `argparse` validates `--format` in `main()`, but `write_outputs` is a public function. `write_outputs(report, out, "xml")` silently returns `[]` and writes nothing — no error raised, exit code 0.
  **Fix**: Add as first line: `if fmt not in ("json", "md", "both"): raise ValueError(f"Unknown format {fmt!r}")`. Also change the parameter type annotation to `Literal["json", "md", "both"]`. `[safe_auto]`

- **[P2.9]** [cg-code-quality] `scripts/cg_audit_context.py:35` — Legacy `typing` module aliases used despite `from __future__ import annotations`
  **Why**: `from __future__ import annotations` (line 18) makes all annotations strings at runtime, so builtin generics work as annotations on Python 3.8. Using `Dict`, `List`, `Tuple`, `Optional`, `Sequence`, `Iterable` from `typing` is deprecated since 3.9 and generates warnings in 3.12+.
  **Fix**: Replace `Dict[str, Any]` → `dict[str, Any]`, `List[...]` → `list[...]`, `Tuple[...]` → `tuple[...]`, `Optional[str]` → `str | None`. Keep only `Any`, `Sequence`, `Iterable` from `typing`. `[safe_auto]`

- **[P2.10]** [cg-code-quality] `scripts/cg_audit_context.py:384` — f-string with no interpolation
  **Why**: `f"prompt size exceeds review threshold"` contains no `{…}` expressions. `ruff` RUF010 flags this.
  **Fix**: Drop the `f` prefix: `"prompt size exceeds review threshold"` `[safe_auto]`

- **[P2.11]** [cg-code-quality + cg-reproducibility] `scripts/cg_audit_context.py:316` — `hashlib.md5()` without `usedforsecurity=False` fails in FIPS environments
  **Why**: `hashlib.md5(data)` raises `ValueError: [digital envelope routines] unsupported` on FIPS-compliant Linux hosts (common in World Bank/government cloud environments). `usedforsecurity=False` is Python 3.9+; this tool targets 3.8+.
  **Fix**: Replace with `hashlib.sha256(normalized.encode("utf-8")).hexdigest()`. SHA-256 is always available, FIPS-safe, and no slower for this use case. `[manual]`

- **[P2.12]** [cg-documentation] `scripts/cg_audit_context.py:104–541` — 18 of 21 public functions have no docstring
  **Why**: Project standard requires every public function to have a docstring with Args, Returns, and at least one Example. Functions without docstrings include all primary entry points and builder/render functions.
  **Affected**: `rel_path`, `classify_model_tier`, `normalize_model_name`, `extract_model_declarations`, `build_model_inventory`, `count_references`, `build_reference_matrix`, `build_dispatch_burden`, `iter_paragraph_blocks`, `normalize_block`, `detect_duplicates`, `classify_optimization_candidates`, `build_report`, `markdown_table`, `render_markdown`, `write_outputs`, `build_arg_parser`, `main`
  **Fix**: Add Google-style docstrings to each. For `main` and `write_outputs` include Args/Returns/Raises/Example; for internal builders Args/Returns suffice. `[safe_auto]`

- **[P2.13]** [cg-documentation] `scripts/cg_audit_context.py:99,111,189,260` — 4 functions have docstrings missing Args/Returns/Examples
  **Why**: One-line summaries alone do not meet the standard. Affected: `estimate_tokens` (L99), `scan_files` (L111), `parse_model_guide` (L189), `count_dispatch_burden` (L260).
  **Fix**: Expand each to include `Args`, `Returns`, and at least one `Example` block. `[safe_auto]`

- **[P2.14]** [cg-documentation] `docs/reference.md:84,166` — Two callouts describe model-guide as having per-file assignment tables that were removed in this PR
  **Why**: Line 84: _"See Model Guide for tier assignments … and **override guidance for all 37 prompt and agent files**."_ Line 166: _"For model assignment rationale, tier criteria, and override guidance, see Model Guide."_ Neither the per-file tables, tier criteria with numeric scores, per-file override guidance, nor the "37" file count remain in the rewritten model-guide.
  **Fix**: Update L84 to: `"See [Model Guide](model-guide.md) for model selection guidance and escalation criteria."` Update L166 similarly. `[safe_auto]`

- **[P2.15]** [cg-documentation] `README.md` — `cg-audit-context` CLI tool absent from all user-facing documentation
  **Why**: The module docstring documents the tool's invocation but there is no mention in `README.md`, `docs/reference.md`, or `docs/installation.md`. Users scanning the repo cannot discover the tool.
  **Fix**: Add a brief entry to `docs/reference.md` in the CLI tools section: `| scripts/cg_audit_context.py | Context and model-governance audit. Inventories context files, estimates token burden, detects model drift and duplicate blocks. Run: python scripts/cg_audit_context.py [--root PATH] [--output-dir PATH] [--format json|md|both] |` `[safe_auto]`

- **[P2.16]** [cg-testing] `scripts/tests/test_audit_context.py` — `parse_model_guide()` has zero tests
  **Why**: This function drives all drift detection. If the table format deviates from expected, `parse_model_guide()` silently returns `{}`, and `drift` is always `[]`. The failure is invisible. Branches needed: missing file → `{}`, valid H3 table row → populated dict, separator row → skipped.
  **Fix**: Add `TestModelGuideParser` with: (a) non-existent file returns `{}`, (b) valid `### Prompts` table row parses filename → model, (c) separator rows are ignored. `[safe_auto]`

- **[P2.17]** [cg-testing] `scripts/tests/test_audit_context.py` — `main()` exit codes 1 and 2 untested
  **Why**: Exit code 2 (non-Compound-GPID root) and exit code 1 (`OSError`/`UnicodeDecodeError` during `build_report`) are the CLI's documented contract but have no tests. The integration test covers only exit code 0.
  **Fix**: Add `TestMainCLI`: `test_invalid_root_exit_code_2` (pass `tmp_path` without `.github/prompts/`, assert return `== 2`), `test_oserror_exit_code_1` (monkeypatch `build_report` to raise `OSError`, assert `== 1`). `[safe_auto]`

- **[P2.18]** [cg-testing] `scripts/tests/test_audit_context.py` — `normalize_model_name()` untested; drift detection silently broken by "(copilot)" suffix mismatch
  **Why**: `build_model_inventory()` calls `normalize_model_name()` on both frontmatter and model-guide values before comparing. A regression in the suffix pattern produces false-positive drift entries silently.
  **Fix**: Add tests: `normalize_model_name("Claude Sonnet 4.6 (copilot)") == "Claude Sonnet 4.6"`, case-insensitive, `None` → `""`, no-op passthrough. `[safe_auto]`

- **[P2.19]** [cg-testing] `scripts/tests/test_audit_context.py` — `_has_broad_tools()` and the broad-tools classification branch untested
  **Why**: `classify_optimization_candidates()` fires `"agent has broad tools and premium model"` only when `_has_broad_tools()` returns `True`. No test passes a `tools=` value, making all branches of `_has_broad_tools` and the broad-tools escalation path dead in the test suite.
  **Fix**: Add `TestBroadTools`: `_has_broad_tools(None) is False`, `_has_broad_tools(["read", "edit_file"]) is True`, `_has_broad_tools(["read"]) is False`, `_has_broad_tools("*") is True`. Add a threshold classification test with `tools=["edit_file"]` on an agent record. `[safe_auto]`

- **[P2.20]** [cg-testing] `scripts/tests/test_audit_context.py` — Duplicate-block escalation path dead in test suite
  **Why**: Lines ~405–409 push entries to `immediate` when a duplicate block crosses `THRESHOLD_DUPLICATE_FILES` (3) and `THRESHOLD_DUPLICATE_TOKENS` (1000). `_classify_one()` always passes `[]` as `duplicates`. The `"duplicates"` category and token-threshold guard are entirely untested.
  **Fix**: Add a test that constructs `{"file_count": 4, "estimated_tokens": 1200, "files": [...]}` and passes it as `duplicates=` to `classify_optimization_candidates()`, asserting `result["immediate"]` contains `category == "duplicates"`. Also test the under-threshold case. `[safe_auto]`

- **[P2.21]** [cg-testing] `scripts/tests/test_audit_context.py` — Drift path in `classify_optimization_candidates()` dead in test suite
  **Why**: The `if path in drift_paths` branch adds `"model guide drift"` to `reasons_review`. No test passes a non-empty `model_inventory["drift"]` list, making drift-flagging silently uncovered.
  **Fix**: Add a test: pass `model_inventory={"declarations": [...], "missing": [], "drift": [{"path": ".github/prompts/x.prompt.md", ...}], "premium_usage": []}` with a matching file record, assert `result["needs_review"][0]["reason"]` contains `"model guide drift"`. `[safe_auto]`

- **[P2.22]** [cg-testing] `scripts/tests/test_audit_context.py` — `count_dispatch_burden()` "limited" and "none" burden levels untested
  **Why**: `count_dispatch_burden()` has four `burden_level` values. Only `"conditional"` and `"broad"` are tested. `"limited"` (1–7 unconditional dispatch refs) and `"none"` (0 refs) have no tests.
  **Fix**: Add `test_limited_burden` (3 `@cg-*` refs, no routing keywords → `burden_level == "limited"`) and `test_no_refs_none_burden` (empty content → `burden_level == "none"`). `[safe_auto]`

- **[P2.23]** [cg-testing] `scripts/tests/test_audit_context.py` — `write_outputs(fmt="md")` path untested in isolation
  **Why**: No test exercises `fmt="md"` alone — the `"md"` branch of `write_outputs()` is only partially covered by the `fmt="both"` test.
  **Fix**: Add `test_md_output_written`: call `write_outputs(report, tmp_path, "md")`, assert `len(paths) == 1`, `paths[0].name == "context-audit.md"`, `"## Summary" in paths[0].read_text()`. `[safe_auto]`

- **[P2.24]** [cg-testing] `tests/model-assignments.Tests.ps1:91` — Agent model-assignments Describe block is an empty stub with no assertions
  **Why**: Line 91 is a comment header `# Model assignments - agent files` with no Describe block. Agent files in `.github/agents/` have no Pester coverage. The Python audit script (`extract_model_declarations`) explicitly processes agent files — it is inconsistent for the Pester layer to skip the same governance check.
  **Fix**: Add `Describe "Model assignments - agent files"` block mirroring the prompts block: discover via `Get-ChildItem`, assert a count sentinel, assert each file has `model:\s+\S+` in frontmatter. `[manual]`

- **[P2.25]** [cg-testing] `tests/model-assignments.Tests.ps1:70` — Redundant second `Describe` block duplicates ordinary-prompt checks
  **Why**: The first `Describe "Model assignments - prompt files"` already iterates all prompt files and checks `model:` absence for ordinary prompts. The second `Describe "Model governance - ordinary prompts"` re-checks the same six files, creating 12 assertions for the same logic. Maintenance risk: two lists to update when prompts change.
  **Fix**: Remove the second `Describe "Model governance - ordinary prompts"` block; all coverage is already present in the first `foreach`. `[manual]`

- **[P2.26]** [cg-version-control] commit history — 3/6 commits on this branch violate conventional commits format
  **Why**: `"add report"`, `"update audit"`, and `"plan and brainstorm"` carry no `type(scope):` prefix. Per project conventions the format is `type(scope): description`.
  **Fix**: Interactive rebase before merge: `git rebase -i main` → reword the three offending commits to e.g. `chore(cost): add initial context audit reports`, `chore(audit): update audit output`, `docs(planning): add brainstorm and plan artifacts`. `[manual]`

- **[P2.27]** [cg-reproducibility] `scripts/cg_audit_context.py:428` — `datetime.now()` embeds non-deterministic timestamp in every committed artifact
  **Why**: `build_report()` stamps `"generated": datetime.now().isoformat(...)` unconditionally. Every run produces a different JSON/Markdown even when no project files changed, guaranteeing a perpetual one-line diff in every PR that re-runs the audit.
  **Fix**: Accept an optional `generated: Optional[str] = None` parameter in `build_report()` (defaulting to `datetime.now()` only when `None`) so callers and tests can inject a fixed timestamp. `[advisory]`

- **[P2.28]** [cg-reproducibility] `.cg-docs/cost/` — Generated artifacts committed without a documented regeneration policy
  **Why**: No documentation establishes when `.cg-docs/cost/context-audit.*` should be regenerated and committed (e.g., only on scheduled CI, only on release). Combined with P2.27, this creates persistent review noise.
  **Fix**: Add a note in `docs/reference.md` or the script's docstring stating that `.cg-docs/cost/context-audit.*` should only be committed when intentionally refreshing the audit snapshot, not on every branch. `[advisory]`

- **[P2.29]** [cg-code-quality + cg-architecture] `scripts/cg_audit_context.py:160` — PEP 8 E302: only one blank line before `normalize_model_name` and `extract_model_declarations`
  **Why**: Both functions have only one blank line before them. PEP 8 requires two blank lines between top-level function definitions. `ruff`/`flake8` will flag E302.
  **Fix**: Insert a second blank line before each definition. `[safe_auto]`

- **[P2.30]** [cg-code-quality] `scripts/cg_audit_context.py:114` — `seen: set` is unparameterized
  **Why**: `seen: set = set()` gives type checkers no information about element type. Should be `set[Path]`.
  **Fix**: `seen: set[Path] = set()` `[safe_auto]`

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `scripts/cg_audit_context.py:546` — `print()` used for CLI output (intentional constraint)
  **Why**: Project standard is `loguru`; `print()` is prohibited. The module docstring explicitly states "stdlib only (no third-party packages)" — this is an intentional design constraint. The pre-import guard at line 23 is legitimately pre-import.
  **Fix**: When the stdlib constraint is lifted, replace `main()`'s `print()` calls with `logger.error()` / `logger.info()`. `[advisory]`

- **[P3.2]** [cg-code-quality] `scripts/cg_audit_context.py:446` — `render_markdown` is ~65 lines, exceeds 30-line guideline
  **Why**: Project standard: functions should be kept under 30 lines. This function builds every report section in a single linear body.
  **Fix**: Extract per-section helpers (e.g., `_render_model_section`, `_render_dispatch_section`) each returning `list[str]`, and have `render_markdown` call them in sequence. `[advisory]`

- **[P3.3]** [cg-code-quality] `pytest.ini` — missing `testpaths` directive
  **Why**: Without `testpaths`, running `pytest` from the repo root will discover all directories including PowerShell `.Tests.ps1` files and fixture text files.
  **Fix**: Add `testpaths = scripts/tests scripts/brain/tests scripts/team_brain/tests` to `pytest.ini`. `[advisory]`

- **[P3.4]** [cg-testing] `scripts/tests/test_audit_context.py:91` — `classify_model_tier()` "unknown" return value untested
  **Why**: `classify_model_tier("GPT-4")` returns `"unknown"`. Only three of four branches tested.
  **Fix**: Add `assert audit.classify_model_tier("GPT-4o") == "unknown"` and `assert audit.classify_model_tier("") == "unknown"`. `[safe_auto]`

- **[P3.5]** [cg-testing] `scripts/tests/test_audit_context.py:107` — `tool_refs` and `load_verbs` not individually asserted in `TestReferenceCounting`
  **Why**: `test_multiple_refs_summed` asserts on `total_refs == 6` but not on `tool_refs` or `load_verbs` individually. A broken regex would reduce total_refs but no focused test names the broken counter.
  **Fix**: Add `test_counts_tool_refs`: `count_references("x", "run_in_terminal foo")["tool_refs"] == 1`, and `test_counts_load_verbs`: `count_references("x", "must read the charter")["load_verbs"] == 1`. `[safe_auto]`

- **[P3.6]** [cg-testing] `scripts/tests/test_audit_context.py` — `rel_path()` `ValueError` fallback branch untested
  **Why**: The `ValueError` catch in `rel_path()` fires when a file is not under `root` (e.g., symlink resolving outside the tree). No test exercises this path.
  **Fix**: Add `test_rel_path_outside_root`: `audit.rel_path(Path("/tmp/other/file.md"), Path("/home/user/repo"))` returns `"/tmp/other/file.md"`. `[advisory]`

- **[P3.7]** [cg-testing] `pytest.ini` — No `pythonpath = scripts`; import relies on conftest side-effect
  **Why**: `import cg_audit_context as audit` works only because `scripts/conftest.py` inserts `scripts/` into `sys.path` at collection time. With `--import-mode=importlib` this fails with a non-obvious `ModuleNotFoundError`.
  **Fix**: Add `pythonpath = scripts` to `pytest.ini` (requires pytest ≥ 7). `[safe_auto]`

- **[P3.8]** [cg-testing] `tests/model-assignments.Tests.ps1:48` — Count sentinel failure has no file-list diagnostic
  **Why**: When `Should -Be 23` fails, the error is `Expected 23 but got 24` with no indication of which file is new. Developer must diff manually.
  **Fix**: Add `$promptFiles | ForEach-Object { Write-Host $_.Name }` inside a `BeforeAll` block so the test output lists all discovered files when the count check fails. `[advisory]`

- **[P3.9]** [cg-code-quality + cg-testing] `scripts/tests/test_audit_context.py:10` — `from typing import Optional` imported with `from __future__ import annotations` active
  **Why**: With `from __future__ import annotations`, `Optional[str]` in annotations can be written as `str | None` without any import. The `Optional` import is residual.
  **Fix**: Remove `from typing import Optional`; change `Optional[str]` annotations to `str | None`. `[safe_auto]`

- **[P3.10]** [cg-documentation] `docs/model-guide.md` — No reference to Pester tests or audit tool that enforce governance rules
  **Why**: The old model-guide had an explicit "Drift protection" callout pointing to `tests/model-assignments.Tests.ps1`. The rewrite removed it. A developer reading governance principles has no indication they are machine-enforced.
  **Fix**: Add: `**Enforcement**: \`tests/model-assignments.Tests.ps1\` validates ordinary prompt model-picker behavior. Run \`python scripts/cg_audit_context.py\` to audit token burden and model drift.` `[advisory]`

- **[P3.11]** [cg-documentation] `docs/model-guide.md` — No changelog/migration note for `model:` key removal across 6 prompts
  **Why**: `cg-brainstorm`, `cg-ideate`, `cg-plan`, `cg-plan-review`, `cg-review-repos`, `cg-strategy` previously hardcoded `Claude Opus 4.6 (copilot)`. Users who have scripted around the `model:` frontmatter key will be surprised.
  **Fix**: Add a note to `docs/model-guide.md` or `CONTRIBUTING.md` recording this as an intentional governance change. `[advisory]`

- **[P3.12]** [cg-version-control] `.cg-docs/cost/context-audit.json` — 44 KB regenerated artifact committed; will accumulate diffs over time
  **Why**: Regenerated on every audit run; produces a large noisy diff in every PR that re-runs the audit. Project policy prohibits adding `.cg-docs/` to `.gitignore`.
  **Fix**: Document in `.cg-docs/cost/README.md` (or the script docstring) that these files are regenerated artifacts and should only be committed when intentionally refreshing the audit snapshot. `[advisory]`

- **[P3.13]** [cg-reproducibility] `scripts/cg_audit_context.py:517` — `json.dumps` missing `sort_keys=True`
  **Why**: Ordering relies on Python 3.7+ dict insertion-order stability — correct now, but fragile if any future contributor introduces an unordered dict construction.
  **Fix**: Add `sort_keys=True` to `json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True)`. `[safe_auto]`

- **[P3.14]** [cg-reproducibility] `scripts/cg_audit_context.py:103` — `rel_path()` fallback silently emits absolute machine-specific path
  **Why**: If the ValueError fallback fires (symlink outside root), `path.as_posix()` returns an absolute OS path in the committed JSON, making it machine-specific.
  **Fix**: Return a sentinel prefix: `return "(external)" + path.as_posix()` with a `warnings.warn`. `[advisory]`

- **[P3.15]** [cg-reproducibility] `scripts/tests/` — No `conftest.py` in `scripts/tests/`; sys.path setup is implicit
  **Why**: Import resolution relies on `scripts/conftest.py` being discovered by pytest traversal. With isolated test runs this can fail without an obvious error.
  **Fix**: Add a one-line `scripts/tests/conftest.py` re-exporting the path setup, or document the required invocation pattern. `[advisory]`

- **[P3.16]** [cg-performance] `scripts/cg_audit_context.py:159` — `re.sub` pattern recompiled on every `normalize_model_name` call
  **Why**: Python re-cache is finite; explicit pre-compilation is idiomatic when a pattern is called in a loop.
  **Fix**: Add `_COPILOT_SUFFIX_RE = re.compile(r"\s*\(copilot\)\s*$", re.IGNORECASE)` at module level; use in `normalize_model_name`. `[safe_auto]`

- **[P3.17]** [cg-performance] `scripts/cg_audit_context.py:298` — `re.split` pattern recompiled on every `iter_paragraph_blocks` call
  **Why**: Same as P3.16; called per-file in `detect_duplicates`.
  **Fix**: Add `_PARAGRAPH_SEP_RE = re.compile(r"\n\s*\n")` at module level; use in `iter_paragraph_blocks`. `[safe_auto]`

- **[P3.18]** [cg-performance] `scripts/cg_audit_context.py:430` — Two separate `sum()` passes over `files` list
  **Why**: `total_characters` and `total_estimated_tokens` are computed in separate generator expressions iterating the same list.
  **Fix**: Compute both in a single pass or use two comprehensions but note this is purely stylistic at the current scale. `[safe_auto]`

- **[P3.19]** [cg-performance] `scripts/cg_audit_context.py:318` — Full normalized block text stored in memory; only 80 chars ever used for preview
  **Why**: `blocks.setdefault(digest, {"block": normalized, ...})` stores the entire normalized block. The only consumer uses `entry["block"][:80]`.
  **Fix**: `"block": normalized[:80]` at the `setdefault` call site. `[safe_auto]`

- **[P3.20]** [cg-performance] `scripts/cg_audit_context.py:517` — `json.dumps` materializes full serialized string in memory before writing
  **Why**: For current scale (~50–100 files), the ~few hundred KB overhead is negligible. Advisory for future growth.
  **Fix**: Replace with `json.dump(report, fp, ...)` using an open file handle. `[advisory]`

- **[P3.21]** [cg-data-quality] `scripts/cg_audit_context.py:102` — `estimated_tokens = 0` for 1–3 char files; floor effect undocumented
  **Why**: Integer floor division means files with 1–3 characters produce `estimated_tokens = 0`, which looks like a processing error.
  **Fix**: Add to docstring: "Returns 0 for strings shorter than 4 characters (integer floor division)." `[advisory]`

- **[P3.22]** [cg-data-quality] `scripts/cg_audit_context.py:338` — `duplicates[*].estimated_tokens` is total redundant cost, not per-block size; semantics undocumented
  **Why**: `total_chars` accumulates block_size × num_occurrences. The field name `estimated_tokens` has different semantics than `files[*].estimated_tokens`, which is per-file size.
  **Fix**: Rename to `total_redundant_tokens` and add a comment explaining the accumulation semantics. `[manual]`

- **[P3.23]** [cg-data-quality] `scripts/cg_audit_context.py:416` — `"(duplicate block)"` sentinel in `classified_paths` undercounts `acceptable_count` by 1
  **Why**: `add()` inserts the string `"(duplicate block)"` into `classified_paths`. Multiple qualifying duplicate blocks all share this same sentinel, so only one slot is occupied but it's not a real file path, causing `acceptable_count` to be 1 lower than the true count.
  **Fix**: Exclude the sentinel from `classified_paths`: `if path != "(duplicate block)": classified_paths.add(path)`. `[safe_auto]`

- **[P3.24]** [cg-data-quality] `scripts/cg_audit_context.py:102` — Token heuristic uses Unicode code points, not UTF-8 bytes; undisclosed
  **Why**: Python `len(text)` counts code points. For ASCII-dominant content (this project's files) the heuristic is reliable. For CJK-heavy files, tokens could be underestimated by up to 3×. The DISCLAIMER doesn't clarify "chars."
  **Fix**: Clarify DISCLAIMER: "chars = Python len() = Unicode code points, not UTF-8 bytes." `[advisory]`

- **[P3.25]** [cg-architecture] `scripts/cg_audit_context.py:14` — "stdlib only" docstring claim is misleading; `brain.utils` dependency not mentioned
  **Why**: The module docstring states "stdlib only (no third-party packages)" but line 40 imports `from brain.utils import parse_frontmatter` — a project-local package. Running the script outside the `scripts/` directory tree without path setup fails with `ImportError`.
  **Fix**: Amend to: "Requirements: Python 3.8+, stdlib only (no third-party packages); requires `scripts/brain/` from this repository." `[safe_auto]`

---

### ✅ Passed

- **cg-version-control**: No secrets, credentials, or hardcoded absolute paths in `cg_audit_context.py`; `.gitignore` change (EOF newline fix) is correct; `roadmap.json` is valid JSON with structurally correct changes; `pytest.ini` changes are safe for version control.
- **cg-reproducibility**: No absolute paths hardcoded in source; all glob results sorted (`sorted(root.glob(...))`); duplicate detection uses `sorted(entry["files"])` — stable ordering across platforms; no random operations.
- **cg-performance**: `detect_duplicates` is O(total_chars) — no O(n²) patterns. The only performance concern is repeated disk I/O (P2.6).
- **cg-data-quality**: No NaN/Inf in numeric fields; no negative `estimated_tokens` possible (integer floor division on `len()`); no silent PII exposure.
