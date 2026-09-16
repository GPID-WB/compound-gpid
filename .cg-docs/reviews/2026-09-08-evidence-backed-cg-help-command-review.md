---
date: 2026-09-14
depth: full
type: standard
plan: .cg-docs/plans/2026-09-08-evidence-backed-cg-help-command.md
brain-enabled: true
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
  P2.26: fixed
  P2.27: fixed
  P2.28: fixed
  P2.29: fixed
  P2.30: fixed
  P2.31: fixed
  P2.32: fixed
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
  P3.13: fixed
  P3.14: fixed
  P3.15: fixed
  P3.16: fixed
  P3.17: fixed
  P3.18: fixed
  P3.19: fixed
  P3.20: fixed
  P3.21: fixed
  P3.22: fixed
  P3.23: fixed
  P3.24: fixed
  P3.25: fixed
  P3.26: fixed
  P3.27: fixed
  P3.28: fixed
  P3.29: skipped
  P3.30: fixed
  P3.31: fixed
  P3.32: fixed
  P3.33: fixed
  P3.34: fixed
  P3.35: fixed
  P3.36: fixed
  P3.37: fixed
  P3.38: fixed
  P3.39: fixed
  P3.40: fixed
  P3.41: fixed
  P3.42: fixed
  P3.43: fixed
  P3.44: fixed
---

# Review — Evidence-Backed /cg-help Command

**Date**: 2026-09-14
**Mode**: full (auto-routed: security-risk — installers, linkers, schema,
generated targets, workflows; config `review-depth: thorough`; no explicit mode)
**Type**: standard initial review (NOT a verify review)
**Plan**: `.cg-docs/plans/2026-09-08-evidence-backed-cg-help-command.md`
**PR**: #153, base `dev`, head branch wealthy-salmonberry
**Head (before/after)**: `53966262c430b44145508b7837ebcc9a11a1aa5c` (unchanged)
**Prev. decisions**: D1–D5 and all approved plan-phase decisions are final and
not reopened (deferral, model-assignments sentinel 33, per-OS implementation
evidence, single-record repin, definition-source set composition).

## Approval Record

- **2026-09-15T01:58Z**: user decision "Approve all listed (Recommended)" —
  the full OR-set from the batch1-fix-triage handoff is approved: P1.1;
  P2.1–P2.22; P3.1–P3.29 (excluding already-applied P3.30/P3.31/P3.32);
  P3.33–P3.44. Recorded by the parent orchestrator session before batch1
  fix-triage applied the recorded recommended fix for each approved finding.
  Pinned-source/definition changes require the recorded explicit final-source
  review plus named per-record `--repin-definition-digest <id> --reviewed`
  operations through the approved tooling; no bulk repin and no hand-written
  digests. Doc-scope P2.6 applies the recorded sanitization policy to the two
  named files, preserving all evidence pointers and receipts.
- **2026-09-15T18:45Z**: user decision "Approve all listed (Recommended)" —
  the five-decision set from the batch1-fix-triage handoff is approved:
  P3.7 (cg_kilo_preflight accepts SemVer pre-releases per recorded
  semver_migration; P3.8 full-match must stay), P3.10 (restrict slash-path
  coercion in `scripts/help/query.py` to leading-slash plus known command
  names; keep plain-query behaviors), P3.15 (pin the tests.yml
  `workflow_dispatch` `subject_commit` input to a full 40-hex SHA pattern
  with script-step validation), P3.17 (evidence revalidation reuses the first
  query_service snapshot; subject-binding checks kept), P3.23 (sidecar summary
  derived from the prompt frontmatter description at generation; generation
  produces equal summary values; catalog regeneration plus check). Recorded by
  this final-triage child session at 2026-09-15T21:06Z in
  `.cg-docs/active-state/current.json` and applied only after that record;
  HEAD unchanged at `53966262c430b44145508b7837ebcc9a11a1aa5c`.

### Batch1 Fix-Triage — Five-Decision Resolutions (final-triage child, 2026-09-15)

Approval: 2026-09-15T18:45Z (all Recommended, recorded 2026-09-15T21:06Z in
`.cg-docs/active-state/current.json` before any code mutation). Applied and
verified by this child session (~21:06Z–22:15Z) with HEAD unchanged at
`53966262c430b44145508b7837ebcc9a11a1aa5c`.

- **P3.7 — cg_kilo_preflight accepts SemVer pre-releases** (fixed):
  `_VERSION_SUFFIX_PATTERN` was added and shared by `VERSION_PATTERN`
  (reader line pattern, group(1) stays the core triplet; the pre-fix
  duplicate `VERSION_PATTERN` line was removed) and the new
  `_VERSION_FULLMATCH_PATTERN` used by `supported_kilo_version`, which now
  compares only the core major.minor.patch against `MINIMUM_KILO_VERSION`
  (7.4.20) with no upper bound, per the recorded `semver_migration`
  decision. P3.8 full-match behavior is preserved (fullmatch + embedded
  triplet rejection tests remain green). Verification:
  `python -m pytest scripts/tests/test_kilo_coexistence.py` — 31 passed
  (pre-release acceptance cases `7.4.20-beta.1`, `7.4.23-rc.2`,
  `7.5.0-alpha.1+build.5` and rejection `7.4.19-rc.1`, `6.99.99-alpha.2`
  added to the step-7 parametrizes).
- **P3.10 — restrict slash-path coercion** (fixed): `normalize_query` in
  `scripts/help/query.py` gained an optional `known_names` parameter;
  shell-kind coercion now fires only for leading-slash multi-segment paths
  whose basename (after an optional `.cmd` suffix) is a known command name;
  all other path-like text stays a plain query (no backslash→slash
  substitution leaks into returned text; the leading-slash slash-kind
  selector remains for single-segment names). `retrieve` now passes the
  casefolded name/alias set computed from `value["commands"]` and the
  validation-only caller in `cg_help.py` is unaffected (one-argument call).
  Test expectation changes in `scripts/tests/test_help_query.py`
  (before → after, restricted coercion, no assertions weakened):
  - `(r"C:\tools\cg-skill.cmd", "shell", "cg-skill")` → `(None, r"c:\tools\cg-skill.cmd")` (no leading slash ⇒ plain text)
  - `("./bin/cg-skill", "shell", "cg-skill")` → `(None, "./bin/cg-skill")` (no leading slash ⇒ plain text)
  - `("cg-skill.cmd", "shell", "cg-skill")` → `(None, "cg-skill.cmd")` (no leading slash ⇒ plain text)
  - `("/usr/bin/cg-skill", "shell", "cg-skill")` → moved into
    `test_slash_path_coercion_requires_leading_slash_and_known_name`
    (`normalize_query("/usr/bin/cg-skill", known_names={"cg-skill"}) == ("shell", "cg-skill")`)
    plus `(None, "/usr/bin/cg-skill")` for the unknown-name single-argument
    call (kept in the plain-query parametrize).
  Verification: `python -m pytest scripts/tests/test_help_query.py` — 49 passed.
- **P3.15 — pin tests.yml `subject_commit`** (fixed): the
  `workflow_dispatch` input now carries `pattern: "^[0-9a-f]{40}$"` plus a
  `pattern-error`; the script-step 40-hex validation already existed in the
  `kilo-certified-subject` github-script step (verified, recorded
  verified-complete — no duplication, no weakening); the detached-check bash
  guard also already enforces the same shape.
- **P3.17 — evidence revalidation reuses the first snapshot** (fixed): the
  `--consume` candidates branch no longer issues a second full
  `query_service("")` pass; `freshness = result` reuses the first snapshot
  (the same-invocation probe was trivially self-consistent). The render
  branch keeps its subject-binding revalidation with its single fresh pass:
  `freshness["state"] == "error"` or `catalogDigest` inequality vs the
  stored snapshot raises "Catalog or project evidence changed". Manifest
  contradiction (e.g. the recorded activation-drift case) surfaces as an
  error-state result, so definition, catalog, and activation drift remain
  caught; `help/support.validate_host_flow` fingerprint expectations remain
  consistent with the lighter sequence. Verification:
  `python -m pytest scripts/tests/test_cg_help.py` — 30 passed; the
  observed-fingerprint transport test and the revalidation-across-invocation
  test are green.
- **P3.23 — sidecar summary derived from frontmatter description** (fixed):
  `scripts/help/validation.py` gained `_slash_description`, which parses the
  prompt frontmatter with `brain.utils.parse_frontmatter` (stdlib-only) and
  requires a non-empty string `description` (fail-closed otherwise); the
  generated catalog command summary is derived from it (single source of
  truth), re-validated against the command schema, and the sidecar's own
  summary field no longer flows into the generated catalog. The committed
  catalog was regenerated (`python scripts/cg_generate_help_catalog.py
  --write`) and checked (`--check` exit 0); all 33 slash catalog summaries
  now equal their frontmatter descriptions (probe confirmed). The
  `committed_catalog_source_graph` fixture regenerates its baseline catalog
  before strict checking because the archived bytes predate the P3.23
  contract. Test changes: `test_accepted_metadata_change_updates_source_digest`
  now asserts the derived summary equals the parsed description after a
  sidecar metadata edit (before: asserted the sidecar summary text flowed
  through); two new tests
  (`test_generated_summary_is_derived_from_prompt_description`,
  `test_missing_prompt_description_fails_generation_closed`). Verification:
  `python -m pytest scripts/tests/test_help_catalog.py` — 69 passed.
- **Reviewed repins** (authorized single-record refreshes after the two code
  edits above): `shell:cg-help` and `shell:cg-kilo` definitionDigest pins
  went stale because their definition sources include the edited
  `scripts/help/query.py` and `scripts/cg_kilo_preflight.py`; repinned one
  record at a time via
  `python scripts/cg_generate_help_catalog.py --repin-definition-digest shell:cg-help --reviewed`
  and the same for `shell:cg-kilo` (no bulk repin, no hand-written digests,
  no payload reads), then `--write` and `--check` (exit 0).
- **Generated trees**: regenerated via `python scripts/cg_generate_targets.py
  --all` because the adapter trees embed the catalog and shell metadata
  (`test_real_repository_working_tree_matches_current_plan` then passed;
  targets/projection suites green).

Validation battery (all fresh foreground leaves, no nested Task):
`test_help_query` 49 passed, `test_kilo_coexistence` 31 passed,
`test_help_catalog` 69 passed, `test_cg_help` 30 passed, `test_help_support`
passed, `test_cg_pr_preflight` passed, `test_module_registry` passed,
`test_cg_generate_targets` + `test_project_projection` passed,
`test_target_ownership` + `test_target_determinism` + `test_target_drift`
passed (full file counts were streamed per-file; totals above 330).
`git diff --check` exit 0 (only the pre-existing `.gitignore` LF/CRLF notice).
Full canonical unfiltered Pester gate (`. tests\Run-Tests.ps1`, filteredFiles
null) at 2026-09-15T22:13:07Z: 2850 passed / 1 failed — the single failure
is the previously recorded `link.Tests` junction-cleanup flake (passes
standalone 94/94, verified again this session; `link.ps1`/`link.Tests.ps1`/
`cg_kilo_copy.py` unchanged since 2026-09-11), classified as host noise with
CI confirmation required per the 01:58Z decision record.
Findings map: P3 now 0 open (five marked fixed above; P3.29 skipped is
accepted); P0 0/0, P1 0/2, P2 0/22.

## Route Summary

- **Scope determination**: complete changed scope since base `dev` — 106
  committed files (`dev..HEAD`, plan phases 1–3) plus 68 uncommitted paths
  (43 modified + 25 untracked, plan phases 3–5 and installer/metadata
  repairs). Reviewed union: 155 unique paths.
- **Route**: full. Auto-routing applied: security-risk (install/update paths,
  linking paths, schema changes, workflows, generated targets);
  architecture-risk (large generator refactor).
- **Dispatch**: 10 review agents over the uncommitted scope, then the same 10
  over the 87 committed-only files (20 fresh foreground leaves, no nested
  Task): code-quality, testing, documentation, version-control,
  reproducibility, performance, architecture, data-quality,
  learnings-researcher, adversarial.
- **Brain**: consulted (`cg-skill-brain-query`); 9 relevant patterns applied
  during review (PS 5.1 `python -c` trap, source-scanning guards, CI bypass
  flags, cross-script parity, enum-exhaustive classification, try/except
  scope traps, `.cmd` python3 stderr leak, exact-JSON mutation boundaries,
  helper-not-wired). No contradictions; no stale entries used.
- **Certification**: no runtime/host certification claims made; Step 12 of
  the plan remains out of scope. `open-brain` and native `get_errors`
  unavailable — recorded, not passed.

## Files Reviewed

- 155 changed paths vs base `dev` (106 committed + 68 uncommitted; 19 overlap).
- Languages: Python (40+ files incl. 6 in new `scripts/help/`), PowerShell
  5.1 (link.ps1, install.ps1, 5 Pester files), bash (link.sh, bin/cg-help),
  CMD (bin/cg-help.cmd), JSON (catalogs, schemas, sidecars, manifests),
  prompts (cg-help.prompt.md, cg-commit-push-pr.prompt.md + ports), docs.

## Findings Map

| Severity | Open | Fixed | Total |
|----------|------|-------|-------|
| P0       | 0    | 0     | 0     |
| P1       | 1    | 1     | 2     |
| P2       | 22   | 10    | 32    |
| P3       | 44   | 0     | 44    |
| **Total**| **67**| **11**| **78**|

No P0 findings: no silent data corruption, security exposure of secrets,
or gate-defeating defect was found across the complete changed scope.

## Fixed Findings — This Review (command-authorized safe_auto)

Tagging discipline: fixes tagged `[safe_auto]` by the reviewing agents were
verified by the orchestrator against the actual source before application;
three candidates were rejected or deferred because application would require
a user decision (see P3.1, P2.5, P3.2).

| ID | Severity | File | Fix |
|----|----------|------|-----|
| P1.2 | P1 | `scripts/tests/test_help_catalog.py` | Two canonical-metadata tests asserted the deferred state (`cg-help.prompt.md`/`.help.json` do not exist) and an exclusion masking the new sidecar from the strict inventory equality. Both were RED in the worktree (confirmed pre-fix: `2 failed in 1.30s`). Rewritten to pin the committed state: existence + exact inventory membership + `slash:cg-help` presence; inventory equality now covers all 33 prompts. |
| P2.23 | P2 | `scripts/tests/test_cg_help.py:923` | Evidence-error exit category pinned from `status != 0` to `status == 3` (missing/stale/selector), matching the documented CLI contract and `cg_help.py:507-508`. |
| P2.24 | P2 | `scripts/tests/test_cg_help.py:401,773-776` | Envelope contract pinned: `cleanupPolicy == "consume-once-and-expire"` on prepare; `catalogDigest` present and `evidenceIds == candidateIds` on selection. |
| P2.25 | P2 | `scripts/tests/test_skill_management_completeness.py` | Python 3.8 AST gate extended to the six new help modules (`cg_help.py`, `cg_verify_help_support.py`, `help/__init__.py`, `help/catalog.py`, `help/query.py`, `help/support.py`). |
| P2.26 | P2 | `scripts/help/support.py:258` | `runAt` parsing wrapped in `_require_rfc3339_utc` with a literal-Z comment (Python 3.8/3.9 `fromisoformat` trap documented); same ValueError contract. |
| P2.27 | P2 | `scripts/cg_validate_modules.py:41-42` | Removed unused `unicodedata`/`fnmatchcase` imports. |
| P2.28 | P2 | `scripts/cg_generate_help_catalog.py:133` | Redundant `except (HelpCatalogIOError, OSError)` tuple simplified to `except OSError` (subclass listed beside base). |
| P2.29 | P2 | `scripts/cg_skill_catalog.py:355-359` | Third copy of the canonical runtime ref regex replaced by `validator.CANONICAL_RUNTIME_PATH_PATTERN`; local `import re` dropped. |
| P2.30 | P2 | `scripts/cg_skill_catalog.py:343-352` | `asset_is_loadable` computed once per asset (single-partition loop) instead of twice over all assets. |
| P2.31 | P2 | `scripts/cg_skill_catalog.py:330-338,377-386` | Removed two no-op `pass` loops in `check_inventory_leaks` and aligned the docstring (leak coverage now honestly stated; inactive-row detection remains covered by `asset_is_loadable` and the projection oracle). |

**Deferred safe_auto candidates** (not applied; require a decision — see open
findings): P3.1 (query.py token hoist — changing a pinned definition source
requires an approved, reviewed repin), P2.5 (lock lifecycle), P3.2 (atomic
replace cleanup semantics).

## Open Findings

### P1 — Critical (1)

- **[P1.1] [manual] `tests/prompt-tools.Tests.ps1` — the new "Step 6
  help-catalog gate" in `.github/prompts/cg-commit-push-pr.prompt.md:169-196`
  has zero Pester contract assertions** (no `cg_generate_help_catalog`,
  `repin`, `--reviewed`, `preview-definition-digest` mentions in `tests/`).
  **Why**: repo discipline (prompt-pipeline-contract-testing 2026-03-30,
  stale-alternation 2026-05-05, source-scanning guard 2026-05-12) requires
  static per-step guards; a future prompt edit can silently weaken the
  exit-2/3/4 hard stops, the preview→repin-reviewed sequence, the
  never-auto-repin rule, or the post-write `--check`. The Python CLI behavior
  is well covered; the prompt TEXT is not. **Fix**: add `Describe
  "cg-commit-push-pr.prompt.md - Step 6 help-catalog gate"` with independent
  `It` assertions per clause, arms copied verbatim from the prompt
  (alternation-safe). (Reported by cg-testing, cg-learnings-researcher.)

### P2 — Important (22 open)

- **[P2.1] [manual] `scripts/cg_help.py:270-283` and `scripts/help/support.py:36-47`
  — ambient `GIT_*` environment redirects any git subprocess**.
  **Why**: `GIT_DIR`/`GIT_INDEX_FILE` etc. from the invoking host are
  inherited, so an ambient environment can redirect proof-staging probes to a
  foreign repo that trivially satisfies subject ancestry.
  **Fix**: scrub/over-ride `GIT_*` vars for subprocess git calls (strict
  allowlist of prepared env).
- **[P2.2] [manual] `scripts/skill_management/services/catalog.py:134`,
  `scripts/cg_project_projection.py:150,188,393`, `scripts/cg_validate_modules.py:210`,
  `scripts/cg_skill_catalog.py:93`, `scripts/cg_context_budget.py:118` —
  manifest/registry JSON readers accept duplicate keys (last-wins)**.
  **Why**: the help gate rejects the same file via `load_strict_json_bytes`;
  a conflicted/hand-edited manifest resolves differently per consumer.
  **Fix**: route all through one strict loader (duplicate-key rejection, BOM,
  size bound).
- **[P2.3] [manual] `scripts/cg_project_projection.py:654,697-703,1184` —
  staged-tree validation double-read TOCTOU; recovery arena not re-hashed**.
  **Why**: the hash pass and the UTF-8 pass re-read files separately, and the
  generation arena is promoted on trust of the first pass; a concurrent swap
  can plant bytes that crash recovery later materializes.
  **Fix**: single read (hash + UTF-8 decode from one buffer); re-verify arena
  after rename and in `recover_projection`.
- **[P2.4] [manual] `scripts/help/catalog.py:823-835,772` — installer
  inventory parser accepts non-executed text (superset acceptance)**.
  **Why**: comment lines, here-doc bodies, and `if false` branches are
  scanned for `chmod +x`/declaration patterns, so documentation text can
  satisfy the exact-inventory gate for a wrapper the installer never creates.
  **Fix**: split on `\n` only, skip comments/here-docs/guarded branches,
  require same execution level for declaration+chmod.
- **[P2.5] [manual — needs design decision] `scripts/cg_help.py:365-385,464-466`
  — orphan stage locks accumulate; cleanup scan cap can starve**.
  **Why**: a process killed between lock creation and the `finally` leaves a
  `.query.lock`/`.selection.lock` forever; `_cleanup` never adopts or deletes
  locks per the documented invariant ("its name and empty bytes do not prove
  CLI ownership") and stops at the scan cap. Agent tag was `[safe_auto]` but
  the deletion side conflicts with the documented ownership-proof invariant
  and would require a design change (e.g., recording lock identity in the
  signed state record). Not auto-applied; decision required.
  **Fix**: record lock identity at creation; let authenticated retirement of
  an expired record also delete its verified lock; separate scan-cap growth.
- **[P2.6] [manual] `.cg-docs/work-reports/2026-09-09-evidence-backed-cg-help-command.md`
  and `.cg-docs/active-state/current.json` — 39 each of personal absolute
  paths (`C:/Users/wb384996/AppData/Local/Temp/3/kilo/...`) beyond the
  established receipt norm**.
  **Why**: receipts in durable docs reference the operator's personal temp
  volumes; the norm elsewhere is repo-relative or sanitized references.
  **Fix**: decide in fix-triage whether to sanitize/elide (evidence receipts
  intentionally preserved per coordinator; needs a decision before edits).
- **[P2.7] [manual] `scripts/help/catalog.py:646-671` — heading-slug
  evidence check cannot detect ambiguity** (`_heading_ids` returns a set;
  colliding slugs both validate).
  **Why**: violates the fail-loudly-on-ambiguous-evidence contract; a future
  duplicate heading silently pins the wrong section.
  **Fix**: return slug→count mapping; reject referenced slugs with count > 1.
- **[P2.8] [manual] `scripts/cg_projection_benchmark.py:160-164,485` —
  baseline payload embeds `platform.python_version()`/`platform.platform()`,
  breaking byte-comparability promise**.
  **Fix**: move host metadata out of the compared payload or document that
  `platformVersions` breaks it.
- **[P2.9] [manual] `scripts/cg_verify_help_support.py:23` — default
  `--evidence` points to a non-existent file** (`_default_evidence(...)`),
  so the documented no-argument invocation fails.
  **Fix**: default to discovering the latest evidence artifact or require the
  flag with a clear message.
- **[P2.10] [manual] `scripts/help/catalog.py` (1556 lines) — single module
  mixes validation, schema engine, installer parsers, serialization, and
  mutating maintenance (preview/repin with `_atomic_replace`)**.
  **Fix**: split into `help/validation.py`, `help/installers.py`,
  `help/maintenance.py` per module-bound conventions.
- **[P2.11] [manual] `scripts/help/query.py:25` — runtime query module
  imports the build-time catalog module** (`from help import catalog`).
  **Fix**: extract transport/validation contracts into a module both can
  import without the build weight.
- **[P2.12] [manual] `scripts/help/catalog.py:1377-1422` — `_atomic_replace`
  re-implements `secure_fs.secure_write_bytes` semantics**.
  **Fix**: delegate to the secure primitive (or extract and share one).
- **[P2.13] [manual] `scripts/skill_management/services/lifecycle.py:668` —
  dead conditional `root_kind = "project" if project_root == source_root else
  "project"` (identical branches)**; `references.scan_references(staged=...)`
  can never receive `"source"`.
  **Fix**: replace with `root_kind = "project"` plus a comment, or implement
  the intended branch with a test.
- **[P2.14] [manual] `scripts/help/catalog.py:335-352` — `_module_closure` is
  a third copy of the dependsOn BFS** (also in
  `cg_context_budget.transitive_dependencies` and
  `cg_validate_modules._transitive_dependency_closure`), with different
  suite-prefix semantics.
  **Fix**: expose one shared `transitive_closure` in `services.registry`.
- **[P2.15] [manual] Registry loading duplication and trust tiers** —
  `_load_registry` copies in `cg_context_budget.py:113-121`,
  `cg_projection_benchmark.py:167-174`, `cg_skill_catalog.py:119-123` plus
  `cg_generate_targets.py:592-607` with three different strictness levels;
  one artifact accepted at different trust levels per consumer.
  **Fix**: route all through `registry_service.load_registry_snapshot(...)` /
  the strict loader; keep a documented relaxed-injection parameter for tests.
- **[P2.16] [manual] `scripts/cg_skill_catalog.py:401` — `--compact`
  `store_true, default=True` is a no-op** (compact is always the default).
  **Fix**: remove the flag or add a real `--no-compact` counterpart.
- **[P2.17] [manual] `scripts/cg_validate_modules.py:915,971,1013,1039,1055`
  — every aggregate check clears the `_read_asset_text` cache, so the default
  run re-reads the full owned-asset tree ~3×** (~5700 reads per default
  invocation).
  **Fix**: move the single `cache_clear()` to `main()` before the checks.
- **[P2.18] [manual] `scripts/cg_validate_modules.py:826-827,880-881,608`,
  `625`, `1075` — owner matching recomputed independently in four places via
  `module_owns_asset(module, canonical)` over (asset × module × pattern)**.
  **Fix**: compute `owners_by_asset` once and look up in O(1).
- **[P2.19] [manual] `scripts/cg_projection_benchmark.py:274-282` +
  `tests/test_projection_benchmark.py:346-355` — `TestRealRepo` triggers 4
  whole-repo scans + 4 git subprocess spawns per PR (benchmark run twice)**.
  **Fix**: accept pre-scanned files; make the real-repo baseline a session
  fixture.
- **[P2.20] [manual] `scripts/cg_project_projection.py:401-407,386-395` —
  combined registry snapshot loaded twice (and a third raw parse)** in the
  CLI plan/publish path.
  **Fix**: resolve the snapshot once, drop the eager parse.
- **[P2.21] [manual] `scripts/cg_context_budget.py:379,393` — public
  functions `ownership_exclusions`/`asset_is_loadable` lack Args/Returns/
  Example docstrings** (charter rule for every function).
  **Fix**: add sections mirroring `ownership_pattern_matches`.
- **[P2.22] [manual] `scripts/help/catalog.py:823-835` + `772` + related —
  installer inventory superset acceptance also affects
  `parse_windows_installer_inventory` for PowerShell comments/CRLF** (same
  class as P2.4; kept distinct for triage).
  **Fix**: apply the same executed-code-only scanning discipline to both
  parsers.

### P3 — Minor (44 open)

- [P3.1] [safe_auto-deferred] `scripts/help/query.py:132-148,218` — hoist
  `_tokens(text)` out of `_score`. Verified behavior-preserving, but
  `scripts/help/query.py` is a pinned definition source of `shell:cg-help`
  (13-source set); applying requires an approved, reviewed repin (user
  decision). Reverted in this stage; catalog `--check` green again.
- [P3.2] [safe_auto-deferred] `scripts/help/catalog.py:1390-1414` — after a
  successful `os.replace`, temp-unlink OSError reports exit 4 (misleading);
  no parent-dir fsync. Apply in fix-triage (contains success-path semantics).
- [P3.3] [advisory] `scripts/help/query.py:209` — inline scoring literals
  (24/6) deserve named constants.
- [P3.4] [advisory] `scripts/cg_help.py:109` — magic threshold literals
  (24/12) in candidates rendering.
- [P3.5] [advisory] `scripts/help/catalog.py:536-545` — `followUpQueries`
  duplicated in rows and data payload.
- [P3.6] [advisory] `scripts/help/support.py:40` — git stderr spooled
  unbounded.
- [P3.7] [advisory] `scripts/cg_kilo_preflight.py:414` — strict version
  pattern rejects SemVer pre-releases (align with release-controller
  pre-release policy if intended).
- [P3.8] [advisory] `scripts/cg_kilo_preflight.py` — `VERSION_PATTERN`
  searched rather than full-matched (accepts embedded triplets).
- [P3.9] [advisory] `scripts/help/support.py:97-102` — workflow `sourcePath`
  from evidence raw-inserted into text (not resolved/validated).
- [P3.10] [advisory] `scripts/help/query.py:45-49` — slash coercion of query
  text.
- [P3.11] [manual] `scripts/tests/test_cg_help.py` — `_check_ignored`
  non-git/non-repo branches untested.
- [P3.12] [manual] `scripts/help/support.py` — 4 functions missing example
  docstrings (`verify_evidence`/`validate_host_flow`/`validate_probe`/
  `subject_bindings`).
- [P3.13] [manual] `scripts/cg_verify_help_support.py` — `main`/`parse_args`
  summary-only docstrings.
- [P3.14] [advisory] `scripts/cg_kilo_preflight.py:409` — docstring/exit-code
  mismatch potential for cert claim wording.
- [P3.15] [advisory] `.github/workflows/tests.yml` — `workflow_dispatch`
  `subject_commit` input is not pinned to a protected branch/commit shape.
- [P3.16] [advisory] `scripts/cg_generate_targets.py` — marker-based
  substitution silently no-ops when markers are absent.
- [P3.17] [advisory] `scripts/cg_help.py:483-485` — evidence revalidation
  double cost on selection branch.
- [P3.18] [advisory] `scripts/help/support.py` — `git cat-file` per platform
  N+1 probe pattern.
- [P3.19] [advisory] `scripts/help/catalog.py:720-751,1099-1109` — shared
  definition sources re-read per record (lru_cache candidate).
- [P3.20] [advisory] `scripts/help/catalog.py:957,1022` — deferred imports
  without `except ImportError` (raw traceback outside exit contract).
- [P3.21] [advisory] `.gitignore:41-45` — collateral removals of earlier
  runtime patterns (verify no external tooling depends on them).
- [P3.22] [advisory] `.github/shared/module-registry.json` — closure edges
  undocumented (cap-help dependency rationale).
- [P3.23] [advisory] `.github/prompts/*.help.json` (33) — sidecar `summary`
  diverges from frontmatter `description` in 33/33 with no consistency
  contract (define derive-or-validate rule).
- [P3.24] [advisory] `scripts/tests/fixtures/help/*` — 8 of 17 fixtures have
  no committed test consumer at HEAD (guarded only by this PR's uncommitted
  tests).
- [P3.25] [manual] `.github/prompts/cr-*.prompt.md` — `module: research`
  frontmatter key on 5 prompts contradicts the description-only extraction
  contract (decide: remove or amend contract).
- [P3.26] [manual] `scripts/cg_generate_help_catalog.py:27,76` + `scripts/
  cg_validate_modules.py:348` — `main`/`parse_args`/`_validate_module_help`
  docstrings lack Args/Returns/Example.
- [P3.27] [advisory] `.github/prompts/cg-commit-push-pr.prompt.md:184-190` —
  exit-3 → `--write` trigger is implicit; add explicit sentence.
- [P3.28] [manual] `docs/workflow.md:65` — `sourceSection`
  `step-3-link-your-project-once-per-project` won't match the GitHub-rendered
  anchor of `docs/installation.md` (`step-3---link-your-project-once-per-project`)
  for human readers.
- [P3.29] [advisory] `a829609` — BRAIN regeneration folded into a
  `docs(knowledge)` commit (separate `chore:` regen commits are the norm).
- [P3.30] [advisory] `scripts/tests/test_projection_benchmark.py:346-355`,
  `test_context_budget.py:307`, `test_project_manifest.py:451`,
  `test_skill_catalog.py:528` — `TestRealRepo` classes flip on dirty
  worktrees; add skip-if-dirty guard.
- [P3.31] [advisory] `scripts/cg_context_budget.py:522` — `--output`
  `json.dumps` without `sort_keys` (byte-stability).
- [P3.32] [advisory] `scripts/tests/test_skill_management_create.py:75`,
  `test_context_budget.py:19`, `test_projection_benchmark.py:18-20` —
  fixture writers default newline translation (CRLF on Windows).
- [P3.33] [advisory] `scripts/skill_management/services/registry.py:167,855`
  — domain service imports app-layer CLI module (function-local cycle
  registry → validate_modules → context_budget → registry).
- [P3.34] [advisory] `scripts/cg_skill_catalog.py:189-262,484-497` — CLI row
  projection bypasses `services.catalog.public_record` (divergent contracts).
- [P3.35] [advisory] `scripts/skill_management/services/registry.py:334-339`
  — `provenance_by_id` raises `KeyError`; siblings return `None`.
- [P3.36] [advisory] `scripts/help/catalog.py` — module exceeds the ~300-line
  bound (see P2.10).
- [P3.37] [advisory] `scripts/schemas/help_catalog_schema.json` — authoring
  boundary for `.github/shared/` artifacts documented only in the plan; add a
  durable statement.
- [P3.38] [advisory] `.github/prompts/cg-setup.prompt.md:1` — UTF-8 BOM is
  part of the pinned digest; normalize or document as pinned content.
- [P3.39] [advisory] `scripts/help/catalog.py:1355-1369` — rendered catalog
  bytes never size-checked before write (input-limit only).
- [P3.40] [advisory] `scripts/help/catalog.py:957,1022` — deferred room for
  typed ImportError messages (see P3.20; distinct fix site).
- [P3.41] [manual] `scripts/help/catalog.py:127-145,219-297` +
  `scripts/cg_generate_help_catalog.py:117-141` — deeply nested JSON
  (~1000 levels) raises `RecursionError` → undocumented exit 1 + traceback;
  re-enter with depth counter / catch and type.
- [P3.42] [manual] `scripts/help/catalog.py:350-351` — `_module_closure`
  crashes with `TypeError` on a registry whose `dependsOn` is not a list
  (public validator API).
- [P3.43] [advisory] `scripts/cg_projection_benchmark.py:250` — description
  truncated at magic 240 chars.
- [P3.44] [advisory] `scripts/cg_skill_catalog.py:189-191` vs
  `services/catalog.py:553-562` — `COMPACT_FIELDS`/`public_record` compact
  sets use different field names (`available` vs `availability`).

## Verified-Impossible Checks (adversarial)

- CRLF pin mutation on Windows (eol=lf; byte-exact repin).
- Multi-occurrence digest replacement injected through comments/paths
  (count != 1 hard-fails).
- Concurrent `--write`/repin races (mkstemp + os.replace + pre-replace
  digest re-check).
- Digest preimage/`\0`-framing ambiguity; identity NUL/empty rejection.
- Path escape via `_validate_relative_path` + `resolve().relative_to(root)`
  + symlink-leaf rejection; sidecar discovery is disk-glob-driven.
- Symlink/pinned output replacement (`_atomic_replace`/`write_catalog`/
  `check_catalog`).
- Prompt-to-CLI mis-sequencing of Step 6 (preview → human review →
  `--repin --reviewed` → `--write` → `--check==0`; repin without `--reviewed`
  rejected at parse time).
- NaN/Infinity, BOM, nested duplicate keys, surrogates in sidecars/catalog/
  transport.

## Evidence (this stage)

| Gate | Command | Result |
|------|---------|--------|
| Pre-fix red-state confirmation | `pytest test_help_catalog.py::test_canonical_help_metadata_inventory_is_complete_and_strict test_canonical_help_metadata_excludes_deferred_help_prompt_and_sidecar` | 2 failed (AssertionError) — as reported |
| Post-fix | `pytest scripts/tests/test_help_catalog.py` | 65 passed / 0 failed |
| Post-fix | `pytest scripts/tests/test_cg_help.py` | 116 passed / 0 failed |
| Post-fix | `pytest scripts/tests/test_skill_management_completeness.py test_skill_catalog.py test_help_query.py test_help_support.py` | 141 passed / 1 skipped / 0 failed |
| Catalog integrity | `python scripts/cg_generate_help_catalog.py --check` | exit 0 — "help catalog is current" |
| Syntax | `python -m compileall -q` (11 edited files) | exit 0 |
| Whitespace | `git diff --check` | clean (one pre-existing `.gitignore` LF→CRLF warning) |

All runs executed through fresh foreground execution leaves (
`background:false`, no nested Task). Pester was not rerun: no PS1/CMD/prompt
file changed in this stage, so the 2845-test Pester gate is unaffected by the
applied fixes (fix-triage may decide on a focused prompt-tools rerun if any
P1.1 fix lands).

Head `53966262c430b44145508b7837ebcc9a11a1aa5c` unchanged; 43 modified / 25
untracked paths preserved; four additional committed files now carry the
command-authorized safe_auto fixes (cg_skill_catalog.py, cg_validate_modules.py,
cg_generate_help_catalog.py, test_skill_management_completeness.py). No
roadmap edit, no phase-completion write, no commit/stage/push/merge/rebase/PR
mutation.

## Handoff

- **Next stage**: `batch1-fix-triage` — conditional on 67 open actionable
  findings (P1.1 manual; 22 P2 manual/design; 44 P3).
- **Needs decision in triage**: P1.1 (add Pester contract — new tests);
  P2.1–P2.4, P2.7–P2.9 (production hardening, behavior-touching); P2.5
  (design decision on lock ownership proof); P2.6 (doc sanitization vs
  receipt preservation); P3.1 (hoist + approved `--repin-definition-digest
  shell:cg-help --reviewed` pairing); P3.2 (success-path semantics).
- **Already-fixed items must not be re-opened**: P1.2, P2.23–P2.32.
- **Certification**: Step 12 remains out of scope; no host is certified by
  this review.