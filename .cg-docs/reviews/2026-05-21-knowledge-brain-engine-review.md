---
date: "2026-05-21"
branch: "feat/knowledge-brain-engine"
plan: "2026-05-20-team-brain-batch-d"
depth: "thorough"
agents: [cg-code-quality, cg-testing, cg-version-control, cg-architecture, cg-performance, cg-reproducibility, cg-data-quality, cg-adversarial, cg-learnings-researcher, cg-documentation]
findings:
  p0: 5
  p1: 13
  p2: 24
  p3: 18
  total: 60
autofix_applied:
  - CQ-P1.1    # privacy.py build_llm_filter_prompt: str.replace instead of str.format
  - SEC-P0.2   # config.py project_name + repo regex validation (path traversal + metachar)
  - SEC-P1.1   # push.py git credential fill trailing \n + password .strip()
  - SEC-P2.1   # push.py _api_request HTTPS scheme enforcement
  - SEC-P2.2   # config.py repo metacharacter validation
  - REPR-P1.1  # push.py urlopen timeout=30
  - REPR-P2.3  # renderer.py json.dumps sort_keys=True
  - REPR-P2.4  # push.py _upsert_jsonl_line returns (str, bool); caller uses was_replaced
  - DQ-P1.1    # push.py "(no pattern)" sentinel guard
  - DQ-P2.1    # push.py _distill_pattern H2-H6 regex (#{2,6})
  - DQ-P2.2    # schema.py topic/source-project non-empty validation
  - CQ-P2.1    # push.py _upsert_jsonl_line JSONDecodeError warnings.warn
  - CQ-P2.4    # privacy.py apply_llm_redactions replacement: null guard
  - CQ-P3.4    # push.py PushResult.action: Literal[...]
  - DOC-P2.1   # privacy.py module docstring layer order (frontmatter -> regex -> LLM)
  - DOC-P2.2   # push.py module docstring add gh auth token step 4
  - DOC-P3.2   # cg-setup.prompt.md gh auth login --scopes repo
  - ADV-P2.1   # push.py git credential fill password .strip() for Windows \r
findings-tracking:
  "CQ-P1.1": {status: fixed}   # autofix: build_llm_filter_prompt str.replace
  "CQ-P1.2": {status: fixed}   # project_name regex validation (SEC-P0.2 fix)
  "CQ-P2.1": {status: fixed}   # autofix: JSONDecodeError warnings.warn
  "CQ-P2.2": {status: deferred, note: "ARCH-P2.1 manual refactor — duplication intentional across modules"}
  "CQ-P2.3": {status: fixed}   # _split_repo helper extracted in config.py
  "CQ-P2.4": {status: fixed}   # autofix: null replacement guard
  "CQ-P3.1": {status: fixed}   # typing.Dict/List/Optional/Tuple replaced with lowercase builtins
  "CQ-P3.4": {status: fixed}   # autofix: PushResult.action Literal[...]
  "T-P0.1":  {status: fixed}   # test for project_name path traversal added
  "T-P1.1":  {status: fixed}   # _get_remote_file RuntimeError test added
  "T-P1.2":  {status: fixed}   # _put_remote_file RuntimeError test added
  "T-P1.3":  {status: fixed}   # push_entry missing file test added
  "T-P1.4":  {status: fixed}   # push_entry no-frontmatter test added
  "T-P1.5":  {status: fixed}   # get_token subprocess exception test added
  "T-P1.6":  {status: fixed}   # _api_request malformed JSON test added
  "T-P2.1":  {status: fixed}   # _upsert_jsonl_line corrupt-line test added
  "T-P2.2":  {status: fixed}   # _distill_pattern Root Cause fallback test added
  "T-P2.3":  {status: fixed}   # apply_frontmatter_filter no-delimiter test added
  "T-P2.4":  {status: fixed}   # apply_llm_redactions multiple findings + guard tests added
  "T-P2.6":  {status: fixed}   # project-name absent → directory-name default test added
  "T-P2.7":  {status: fixed}   # load_team_brain_local_config frontmatter fallback test added
  "T-P2.8":  {status: fixed}   # enabled: false string coercion test added
  "T-P2.9":  {status: fixed}   # _find_local_config boundary stop tests added
  "SEC-P0.1": {status: fixed}  # _NoRedirectHandler prevents Authorization header forwarding
  "SEC-P1.1": {status: fixed}  # autofix: git credential fill \n\n + password .strip()
  "SEC-P1.2": {status: fixed}  # project_name regex validation (SEC-P0.2 fix)
  "SEC-P1.3": {status: fixed}  # cg-setup.prompt.md: scaffold repo as private: true
  "SEC-P2.1": {status: fixed}  # autofix: HTTPS scheme enforcement
  "SEC-P2.2": {status: fixed}  # autofix: repo metacharacter validation
  "ARCH-P2.1": {status: deferred, note: "Push.py and config.py parsers serve different roles; full merger deferred"}
  "ARCH-P2.2": {status: deferred, note: "push_entry god function split — major refactor, deferred to future batch"}
  "ARCH-P2.3": {status: fixed}  # warnings.warn when strategy + non-default min_cluster_size conflict
  "ARCH-P2.4": {status: fixed}  # renamed _write_atomic → write_atomic (public API)
  "PERF-P2.1": {status: deferred, note: "Parallel GET conflicts with JSONL-first ordering (ADV-P1.3); deferred"}
  "PERF-P2.2": {status: fixed}  # autofix: _upsert_jsonl_line returns (str, bool)
  "REPR-P1.1": {status: fixed}  # autofix: urlopen timeout=30
  "REPR-P1.2": {status: fixed}  # _put_jsonl_with_retry with exponential back-off on 409/422
  "REPR-P2.3": {status: fixed}  # autofix: json.dumps sort_keys=True
  "REPR-P2.4": {status: fixed}  # autofix: _upsert_jsonl_line returns (str, bool)
  "DQ-P0.1":  {status: fixed}  # _CREDENTIAL_RE: \b word boundary + code-fence exclusion
  "DQ-P0.2":  {status: fixed}  # _distill_pattern now uses filter_result.clean_content
  "DQ-P1.1":  {status: fixed}  # autofix: "(no pattern)" sentinel guard
  "DQ-P1.2":  {status: fixed}  # PatternEntry.__post_init__ validates all fields on construction
  "DQ-P1.3":  {status: fixed}  # empty-body guard: returns blocked if filtered body < 50 chars
  "DQ-P2.1":  {status: fixed}  # autofix: _distill_pattern #{2,6} regex
  "DQ-P2.2":  {status: fixed}  # autofix: topic/source-project non-empty validation
  "ADV-P1.1": {status: fixed}  # project_name regex blocks YAML injection (same root fix)
  "ADV-P1.3": {status: fixed}  # JSONL-first write ordering: patterns PUT before entry PUT
  "ADV-P1.4": {status: fixed}  # LLM replacement: HTML/script injection guard + 500-char cap
  "ADV-P2.1": {status: fixed}  # autofix: password .strip() for Windows \r
  "ADV-P2.5": {status: fixed}  # quote-before-comment: unquote before stripping # comment
  "DOC-P2.1": {status: fixed}  # autofix: privacy.py module docstring layer order
  "DOC-P2.2": {status: fixed}  # autofix: push.py module docstring gh auth token step
  "DOC-P3.2": {status: fixed}  # autofix: gh auth login --scopes repo
---

# Review: `feat/knowledge-brain-engine`

**Date**: 2026-05-21  
**Branch**: `feat/knowledge-brain-engine` (PR #42)  
**Plan**: [2026-05-20-team-brain-batch-d](.cg-docs/plans/2026-05-20-team-brain-batch-d.md)  
**Depth**: thorough (10 agents)  
**Scope**: 63 changed files; key new modules: `scripts/brain/`, `scripts/team_brain/`, `scripts/cg_index.py`

---

## Overall Assessment

The brain engine (scanner, extractor, clusterer, edge-detector, renderer) is architecturally sound with good test coverage and correct algorithmic choices. The **team_brain push pipeline** has **5 blocking security/data-integrity issues** that must be fixed before merge:

1. `_distill_pattern` runs on unfiltered body — leaks private data to shared JSONL
2. `_CREDENTIAL_RE` corrupts R/Python/Stata code examples (no word boundary)
3. `Authorization` header forwarded on HTTP redirects (urllib default)
4. `project_name` not validated — path traversal + YAML injection in GitHub API paths
5. `build_llm_filter_prompt` uses `str.format()` — crashes on `{...}` in any document

---

## P0 — Blocking (fix immediately)

### [DQ-P0.1] `[manual]` `privacy.py:117` — `_CREDENTIAL_RE` corrupts code examples

`_CREDENTIAL_RE` has no word boundary and no code-block exclusion. `httr2::req_auth_bearer_token(token = get_token())`, `openai.OpenAI(api_key=os.getenv("KEY"))`, `unnest_tokens(tbl, token = word, ...)` — all get silently replaced with `<REDACTED:credential>`. The commit summary shows only a count; the pushed entry has syntactically invalid code with no audit trail.

**Fix**: Add `\b` word boundary after each keyword; track fenced-code-block state in `apply_regex_filter` and skip lines inside ` ``` ` blocks.

---

### [DQ-P0.2] `[manual]` `push.py:529` — `_distill_pattern` uses unfiltered body

`push_entry` passes the **original** `(frontmatter, body)` to `_distill_pattern` instead of parsing from `filter_result.clean_content`. Any credential in the `root-cause:` field or first sentence of `## Solution` bypasses all three privacy layers and is written verbatim to the shared JSONL `pattern` field.

**Fix**:
```python
clean_fm, clean_body = _parse_frontmatter(filter_result.clean_content)
pattern_text = _distill_pattern(clean_fm, clean_body)
```

---

### [SEC-P0.1] `[manual]` `push.py:275` — `Authorization` header forwarded on HTTP redirects

Python's `urllib.request.HTTPRedirectHandler.redirect_request()` copies all headers (except `content-length`) to redirect targets. A GitHub 301 (renamed/transferred repo) to an attacker-controlled endpoint receives the full token.

**Fix**: Custom no-redirect handler:
```python
class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)

_opener = urllib.request.build_opener(_NoRedirectHandler())
# Replace urlopen(req) with _opener.open(req)
```

---

### [SEC-P0.2] `[safe_auto]` `config.py:248` + `push.py:519` — `project_name` not validated

No sanitization before `f"entries/{project_name}/{filename}"` in GitHub Contents API URL. A value like `../../.github/workflows` overwrites workflow files. Same value in `f'source-project: "{project_name}"'` (push.py:507) is a YAML injection vector.

**Fix** (in `load_team_brain_local_config`, after deriving `project_name`):
```python
import re
if not re.match(r'^[A-Za-z0-9][A-Za-z0-9\-_]*$', project_name):
    raise ValueError(
        f"team-brain.project-name must be alphanumeric with hyphens/underscores, "
        f"got: {project_name!r}"
    )
```

---

### [CQ-P1.1] `[safe_auto]` `privacy.py:build_llm_filter_prompt` — `str.format()` crashes on `{...}` in content

`_LLM_LAYER_PROMPT_TEMPLATE.format(content=content)` expands any `{macro}`, `{0}`, `{{braces}}` in the document body. Stata macros, JSON examples, Pester assertions all crash with `KeyError`.

**Fix**: `return _LLM_LAYER_PROMPT_TEMPLATE.replace("{content}", content, 1)`

---

## P1 — Critical (must fix before merge)

### [SEC-P1.1] `[safe_auto]` `push.py:130` — `git credential fill` missing trailing `\n\n`

The git credential protocol requires a blank line to signal end-of-input. Without it, the subprocess blocks, hits `timeout=5`, raises `TimeoutExpired` (caught silently), and returns `None`. Users with correctly stored credentials get a misleading "No GitHub token found" error.

**Fix**: `input="protocol=https\nhost=github.com\n\n"` (add trailing `\n`)

---

### [ADV-P2.1] `[safe_auto]` `push.py:133` — git credential fill password has `\r` on Windows

`line[len("password="):]` on Windows returns `"ghp_abc\r"`. No `.strip()`. All API calls fail with HTTP 401.

**Fix**: `return line[len("password="):].strip()`

---

### [REPR-P1.1] `[manual]` `push.py:290` — `urlopen` has no timeout

`urllib.request.urlopen(req)` with no timeout hangs indefinitely on GitHub rate-limit backoff or transient network stalls, blocking CI forever.

**Fix**: `with urllib.request.urlopen(req, timeout=30) as resp:`

---

### [REPR-P1.2] `[manual]` `push.py:568` — JSONL SHA race: concurrent pushes lose entries

Two simultaneous `push_entry` calls fetch the same JSONL SHA. The second PUT returns HTTP 422 (stale SHA) and the pattern is permanently lost. No retry, no recovery hint.

**Fix**: Retry with exponential back-off (max 3) on 409/422: re-fetch SHA and re-apply upsert.

---

### [ADV-P1.3] `[manual]` `push.py:570` — Two-phase write: entry committed, JSONL fails → desync

If killed between entry PUT and JSONL PUT (or if JSONL PUT gets a 409 race), the entry exists in the central repo but is never indexed in the JSONL. Re-running creates a duplicate entry commit with a stale JSONL.

**Fix**: JSONL-first ordering (index before entry), or surface the partial-commit state in the RuntimeError with a "re-run to recover" hint.

---

### [ADV-P1.4] `[manual]` `privacy.py:394` — LLM prompt injection via adversarial replacement values

`replacement` from LLM JSON output is applied with no length or content check. A jailbroken LLM can inject XSS payloads, SQL, or a 10MB replacement string. The post-LLM regex pass catches file paths but not arbitrary injected content.

**Fix**: `if len(replacement) > 500 or re.search(r'[<>"&]', replacement): replacement = "<REDACTED:llm>"`

---

### [SEC-P1.3] `[manual]` `cg-setup.prompt.md:A5.9` — New team-brain repo scaffolded as `"private": false`

All solution entries pushed via `/cg-compound` are immediately public, before users understand the privacy filter. World Bank project solutions may contain internal server names or analytical logic that should not be public by default.

**Fix**: Change scaffold to `"private": true` with a note to the user.

---

### [T-P1.1–T-P1.6] `[safe_auto]` Six critical test gaps in `test_push.py`

| ID | Missing test |
|---|---|
| T-P1.1 | `_get_remote_file` RuntimeError on non-200/404 |
| T-P1.2 | `_put_remote_file` RuntimeError on non-200/201 |
| T-P1.3 | `push_entry` missing file → `FileNotFoundError` |
| T-P1.4 | `push_entry` no-frontmatter → `ValueError` end-to-end |
| T-P1.5 | `get_token` subprocess raises `FileNotFoundError` (gh not installed) |
| T-P1.6 | `_api_request` malformed JSON body fallback |

---

## P2 — Important (should fix)

### [SEC-P2.1] `[safe_auto]` `push.py:_api_request` — no HTTPS scheme enforcement

Function accepts any URL. Future callers or test stubs passing `http://` send the token in plaintext.

**Fix**: `if not url.startswith("https://"): raise ValueError(...)`

---

### [SEC-P2.2] `[safe_auto]` `config.py:repo` — URL metacharacters not rejected

`repo: "evil/test?x=1"` produces a malformed GitHub API URL that urllib parses with the query string inlined, going to the wrong endpoint.

**Fix**: `if not re.match(r'^[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+$', repo): raise ValueError(...)`

---

### [REPR-P2.3] `[safe_auto]` `renderer.py:595` — `json.dumps` without `sort_keys=True`

`brain-index.json` key order is insertion-order dependent; future refactors produce spurious git diffs.

**Fix**: `json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)`

---

### [REPR-P2.4] `[safe_auto]` `push.py:573` — commit message action from substring check, not JSON parse

`pattern_entry.id in jsonl_content` is a raw string search — false-positive if ID appears in another entry's `entry_path` field.

**Fix**: Return `(new_content, was_replaced: bool)` from `_upsert_jsonl_line` and use it.

---

### [DQ-P1.1] `[safe_auto]` `push.py:254` — `"(no pattern)"` sentinel pushed unguarded

`_distill_pattern` returns `"(no pattern)"` sentinel; `push_entry` never checks for it. Pushes noise to the shared JSONL.

**Fix**: Guard after `_distill_pattern`: if `pattern_text == "(no pattern)"`, return `PushResult(action="skipped", ...)`.

---

### [DQ-P1.2] `[safe_auto]` `push.py:530` — `PatternEntry` bypasses all schema validation on write path

`push_entry` constructs `PatternEntry(...)` directly, bypassing `parse_pattern_jsonl_line`. Invalid dates (`"May 20 2026"`), empty topics pass through to JSONL.

**Fix**: Add `__post_init__` to `PatternEntry` or validate via a round-trip `parse_pattern_jsonl_line(entry.to_jsonl_line())`.

---

### [DQ-P1.3] `[safe_auto]` `push.py:506` — No empty-body guard after privacy filtering

A document with `private-sections: [Problem, Solution, Root Cause, References]` strips the entire body, pushing an entry with only frontmatter.

**Fix**: Check `len(body_only.strip()) < 50` after filtering; return `PushResult(action="blocked", ...)`.

---

### [DQ-P2.1] `[safe_auto]` `push.py:237` — `_distill_pattern` only matches H2 headings (`##`)

`### Solution` (H3) or deeper falls through to the `title` fallback or `"(no pattern)"`.

**Fix**: Change `##\s*` to `#{2,6}\s*` in the section regex.

---

### [DQ-P2.2] `[safe_auto]` `schema.py:370` — `topic` and `source-project` not validated as non-empty

`"topic": ""` passes all checks and enters the JSONL, polluting pattern search.

**Fix**: Add non-empty strip-and-check for both fields alongside existing `id` and `pattern` checks.

---

### [ADV-P2.5] `[safe_auto]` `push.py:_parse_frontmatter` — inline `#` in quoted values truncated before quote-strip

`title: "My Fix #1"` → `'"My Fix'` (leading quote, truncated). Comment stripping runs before quote stripping.

**Fix**: Strip outer quotes first, then strip trailing ` #...` comment.

---

### [CQ-P2.1] `[safe_auto]` `push.py:_upsert_jsonl_line` — silent `JSONDecodeError: continue` hides corrupt lines

**Fix**: `warnings.warn(f"Skipping malformed JSONL line {i+1}", stacklevel=3)` before `continue`.

---

### [CQ-P2.3] `[safe_auto]` `config.py:TeamBrainLocalConfig` — `repo_owner()`/`repo_name()` duplicate split logic

**Fix**: Extract `_split_repo()` private helper called by both methods.

---

### [CQ-P2.4] `[safe_auto]` `privacy.py:apply_llm_redactions` — `replacement: null` from JSON yields `None`, crashes `str.replace`

**Fix**: `replacement = finding.get("replacement") or "<REDACTED:llm>"`

---

### [ARCH-P2.3] `[safe_auto]` `clusterer.py:304` — `min_cluster_size` silently ignored when custom strategy provided

**Fix**: `warnings.warn` when `strategy is not None and min_cluster_size != 3`.

---

### [ARCH-P2.4] `[safe_auto]` `brain/utils.py` — `_write_atomic` named private but imported as public API by two callers

**Fix**: Rename to `write_atomic` (drop underscore); update `renderer.py` and `cg_index.py`.

---

### [PERF-P2.2] `[safe_auto]` `push.py:549` — commit action flag is substring search; `_upsert_jsonl_line` discards its `replaced` flag

Same root cause as REPR-P2.4. Resolved by returning `(content, was_replaced)` tuple from `_upsert_jsonl_line`.

---

### [DOC-P2.1] `[safe_auto]` `privacy.py:6` — module docstring has wrong layer execution order (regex → frontmatter → LLM vs actual frontmatter → regex → LLM)

**Fix**: Swap items 1 and 2 in the module-level docstring.

---

### [DOC-P2.2] `[safe_auto]` `push.py:5` — module docstring omits `gh auth token` from the 5-step token lookup list

**Fix**: Add step 4 (`gh auth token`) between GH_TOKEN and git credential fill.

---

### [T-P2.1–T-P2.11] Eleven important test gaps

| ID | Missing test |
|---|---|
| T-P2.1 | `_upsert_jsonl_line` corrupt-line skip path |
| T-P2.2 | `_distill_pattern` `## Root Cause` fallback |
| T-P2.3 | `apply_frontmatter_filter` no-delimiter path |
| T-P2.4 | `apply_llm_redactions` multiple findings |
| T-P2.6 | `project-name` absent → directory-name default |
| T-P2.7 | `load_team_brain_local_config` frontmatter fallback |
| T-P2.8 | `enabled: "false"` string coercion |
| T-P2.9 | `_find_local_config` stops at `compound-gpid.md` |
| T-P2.10 | `build_brain` empty workspace |
| T-P2.11 | `_topic_slug`/`_topic_label` empty keyword list |
| T-P0.1* | `project_name` path traversal — no validation, no test *(P0 in testing agent)* |

---

## P3 — Minor / Advisory

| ID | Tag | Location | Issue |
|---|---|---|---|
| CQ-P3.1 | `[safe_auto]` | all `team_brain/*.py` | `typing.Dict/List/Optional` → lowercase builtins + `\|` |
| CQ-P3.4 | `[safe_auto]` | `push.py:47` | `PushResult.action: str` → `Literal[...]` |
| ARCH-P3.2 | `[advisory]` | `brain/__init__.py:33` | `__all__` declares `ClusterStrategy` before it's imported |
| PERF-P2.1 | `[manual]` | `push.py:527` | Sequential GET+PUT → could parallelize with `ThreadPoolExecutor(2)` |
| PERF-P3.1 | `[safe_auto]` | `extractor.py` Signal 4 | `Path(fref).name` → `os.path.basename(fref)` |
| PERF-P3.2 | `[safe_auto]` | `renderer.py:_split_oversized_topic` | `_entity_line()` rendered twice per entity |
| PERF-P3.3 | `[advisory]` | `renderer.py:render_brain` | Stale BRAIN-NN.md cleanup runs before BRAIN.md updated |
| REPR-P3.2 | `[advisory]` | `__init__.py:182` | `scan_roadmap()` entities not sorted → cluster order depends on JSON source order |
| REPR-P3.3 | `[safe_auto]` | `clusterer.py:232` | `entity_paths` in Union-Find order → sort for stability |
| REPR-P3.1 | `[safe_auto]` | `renderer.py:60` | Token estimator overcounts consecutive whitespace; use `len(text.split())` |
| ADV-P2.2 | `[advisory]` | `privacy.py:113` | Multi-line credential bypass (keyword on one line, value on next) |
| ADV-P2.3 | `[advisory]` | `privacy.py:113` | Unicode homoglyph bypass in credential keywords |
| DOC-P3.2 | `[safe_auto]` | `cg-setup.prompt.md:156` | `gh auth login` should be `gh auth login --scopes repo` |
| T-P3.1–T-P3.6 | `[advisory]` | various | Advisory test gaps (Windows absolute path, multi-redaction, etc.) |

---

## Learnings from Brain

The following past solutions are directly applicable and contradict or extend current implementation:

| Past solution | Conflict with current code |
|---|---|
| [path-startswith-bypass](.cg-docs/solutions/bugs/2026-05-20-python-path-startswith-bypass-use-relative-to.md) | Use `Path.relative_to()` not string containment for path guards |
| [python-nonatomic-path-write](.cg-docs/solutions/bugs/2026-05-07-python-nonatomic-path-write-use-mkstemp-replace.md) | `_write_atomic` caveat: `os.replace()` needs same-device on Windows |
| [bare-catch-swallows-errors](.cg-docs/solutions/build-errors/2026-03-19-invoke-restmethod-bare-catch-swallows-non-404-errors.md) | Only suppress 404; re-throw all other HTTP errors |
| [two-phase-injection-guard](.cg-docs/solutions/testing-patterns/2026-04-29-two-phase-injection-guard-for-agent-file-reads.md) | Scan raw bytes before extracting into LLM context |
| [prompt-injection-via-plan-content](.cg-docs/solutions/testing-patterns/2026-05-14-prompt-injection-via-plan-content-in-ai-generated-output.md) | LLM-authored content must not be embedded verbatim in AI output |

---

## Fix Plan

### Tier A — Apply now (safe_auto, high-impact)
1. `SEC-P0.2` — `project_name` regex validation in `config.py`
2. `CQ-P1.1` — `build_llm_filter_prompt` → `str.replace()`
3. `SEC-P1.1` — `git credential fill` trailing `\n`
4. `ADV-P2.1` — `git credential fill` password `.strip()`
5. `REPR-P1.1` → add `timeout=30` to `urlopen`
6. `SEC-P2.1` — HTTPS scheme enforcement in `_api_request`
7. `SEC-P2.2` — `repo` metacharacter validation
8. `REPR-P2.3` — `json.dumps(sort_keys=True)`
9. `DQ-P1.1` — `"(no pattern)"` sentinel guard
10. `DQ-P2.1` — H2-H6 section regex (`#{2,6}`)
11. `DQ-P2.2` — `topic`/`source-project` non-empty validation
12. `CQ-P2.4` — `replacement: null` guard
13. `ADV-P2.5` — `_parse_frontmatter` quote-before-comment
14. `CQ-P2.1` — `JSONDecodeError` warning
15. `REPR-P2.4` / `PERF-P2.2` — `_upsert_jsonl_line` returns `(content, was_replaced)`
16. `DOC-P2.1` — privacy.py module docstring layer order
17. `DOC-P2.2` — push.py module docstring add `gh auth token` step
18. `DOC-P3.2` — `gh auth login --scopes repo`
19. `CQ-P3.4` — `PushResult.action: Literal[...]`
20. `CQ-P3.1` — Remove deprecated `typing.Dict/List/Optional` imports

### Tier B — Manual judgment required (P0/P1)
1. `DQ-P0.1` — `_CREDENTIAL_RE` word boundary + code-block exclusion
2. `DQ-P0.2` — `_distill_pattern` from filtered body
3. `SEC-P0.1` — no-redirect handler in `_api_request`
4. `REPR-P1.2` — JSONL SHA race: exponential back-off retry
5. `ADV-P1.3` — Two-phase write recovery documentation + ordering
6. `ADV-P1.4` — LLM replacement value length/content guard
7. `SEC-P1.3` — Team-brain repo scaffold as private

### Tier C — Tests to add (P1/P2)
Six P1 test gaps (T-P1.1–T-P1.6) and eleven P2 test gaps (T-P2.x) — see list above.
