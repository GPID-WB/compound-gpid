---
date: 2026-08-11
depth: full
type: standard
plan: ".cg-docs/plans/2026-08-05-copilot-issue-implementation-pipeline-v2.md"
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
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
  P3.17: skipped
  P3.18: skipped
  P3.19: fixed
  P3.20: fixed
  P3.21: fixed
  P3.22: skipped
---

# Review Evidence — Phase 5 (Stage 3) Copilot dispatcher

## Provenance

Full-depth review (`/cg-review full`) of the Phase 5 implementation at working
HEAD on branch `issue-implementation-phase5`, 2026-08-11. Ten agents dispatched:
`@cg-code-quality`, `@cg-testing`, `@cg-documentation`, `@cg-version-control`,
`@cg-reproducibility`, `@cg-performance`, `@cg-architecture`, `@cg-data-quality`,
`@cg-learnings-researcher`, `@cg-adversarial`. Changed files:
`.github/workflows/copilot-dispatch.yml`, `scripts/issues/dispatch.py`,
`scripts/issues/dispatch_client.py`, `scripts/issue_dispatch.py`,
`scripts/tests/test_issue_dispatch.py`, `.github/workflows/tests.yml`,
`docs/copilot-dispatch.md`, `docs/copilot-readiness.md`,
`docs/navigation.json`, plus `.cg-docs/` plan metadata.

## Review Report

**Review mode**: full
**Files reviewed**: 11 changed paths
**Findings**: 33 (P0: 0, P1: 3, P2: 8, P3: 22)

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-code-quality][cg-architecture] `scripts/issues/dispatch.py:343` — CLI usage errors exit code 2, colliding with `EXIT_NOT_READY`.
  **Why**: plain `argparse.ArgumentParser.error()` exits 2, which is simultaneously the documented "validation_failure" code; a malformed invocation (missing/non-int `--issue`) is indistinguishable from "issue not ready". The readiness sibling solved this via `_ReadinessArgumentParser` (exit 3 = config).
  **Fix**: reuse `_ReadinessArgumentParser` from `issues.cli` (or an identical `_DispatchArgumentParser`) so usage errors exit `EXIT_CONFIG` (3); assert `exc.value.code == EXIT_CONFIG` in the CLI test.
  Tag: [safe_auto] — applied.

- **[P1.2]** [cg-adversarial][cg-reproducibility][cg-architecture] `.github/workflows/copilot-dispatch.yml:66-72` — `dry_run` input fails open: any value other than the exact lowercase string `"true"` triggers a **live** dispatch.
  **Why**: `if [ "${DRY_RUN}" = "true" ]; then --dry-run; else --no-dry-run; fi`. A typo (`True`, `yes`, `1`) or a missing/empty value silently routes to `--no-dry-run` — the live assignment path. The safety invariant is "live requires explicit opt-in".
  **Fix**: invert the default direction — only the exact value `"false"` selects live, everything else stays dry-run.
  Tag: [safe_auto] — applied.

- **[P1.3]** [cg-architecture][cg-code-quality] `scripts/issues/dispatch.py` (413 lines), `scripts/issues/dispatch_client.py` (341 lines) — modules exceed the repo's <300-lines-per-module rule and bundle orchestration + render + CLI responsibilities that the readiness sibling keeps separated.
  **Why**: The Stage 2 refactor (plan review P1.3) explicitly split readiness into `orchestration.py`/`render.py`/`cli.py`; the dispatcher is its natural sibling and regresses that structure. `dispatch.py` mixes the orchestration state machine, result contract, render layer, and CLI; `_emit` is near-verbatim from `cli.py`.
  **Fix**: Split into `orchestration`/`render`/`cli` responsibilities (or extract render + CLI into modules), keeping `dispatch.py` as a thin facade so `issue_dispatch.py`, tests, and the workflow continue to import unchanged.
  Tag: [manual]

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-adversarial][cg-architecture] `scripts/issues/dispatch.py:183-260` — TOCTOU: no post-assignment state re-read before the Project Status mutation.
  **Why**: the second validation closes pre-assign races, but assign success is judged by REST returncode only; a silent assign no-op or a state change between revalidation and assign would still advance the project and post a "Dispatched" success comment.
  **Fix**: after `mutator.assign` succeeds, re-read assignees and fail closed to `EXIT_ASSIGN_FAILED` (leaving Project untouched) if `COPILOT_ASSIGN_LOGIN` is absent, or parse the assign response's returned assignee list.
  Tag: [manual]

- **[P2.2]** [cg-adversarial][cg-data-quality] `scripts/issues/dispatch_client.py:241-246` — `set_project_status` treats any no-`errors` response as success and never verifies the mutation result.
  **Why**: a GraphQL response `{"data": null}` (or the target field `null`) with no `errors` passes as success; `run_dispatch` then claims "Project Status set to 'In progress'" and exits 0. Silent false-success in a control plane.
  **Fix**: require the success shape — parse `data["data"]["updateProjectV2ItemFieldValue"]` and raise `ApiError` when missing/`None`/wrong-shape (mirror `_classify_graphql_errors` + explicit null guard).
  Tag: [manual]

- **[P2.3]** [cg-adversarial] `scripts/issues/dispatch_client.py:193-208, 313-324` and `dispatch.py:203-260` — unexpected `OSError` in temp-file create/write/unlink escapes `run_dispatch`'s `(ApiError, ConfigError)` handlers → raw traceback exit 1, no structured output, no audit comment.
  **Why**: `tempfile.NamedTemporaryFile`/`handle.write`/`Path.unlink` raise `OSError` (disk full, permission), not `ApiError`/`ConfigError`; violates the documented exit-code contract and kills the audit trail exactly in partial/crash states where it is needed.
  **Fix**: wrap temp-file creation/write/unlink in `try/except OSError → ApiError`; make the `finally` unlink best-effort; add an unwritable-temp regression test.
  Tag: [safe_auto] — applied.

- **[P2.4]** [cg-adversarial] `scripts/issues/dispatch_client.py:52-63, 263-300` — `_resolve_item_id` resolves the project item through the repository/issue GraphQL node, contradicting the documented least-privilege `PROJECT_SYNC_TOKEN` ("project write").
  **Why**: a project-write-only token lacks repo/issue read, so `_ITEM_QUERY` fails with an auth/scope error and `set_project_status` always exits 6 under the documented credential setup.
  **Fix**: resolve the item via the project node (`node(id: projectId) { items { nodes { id content { ... on Issue { number } } } } }`), filtering by issue number client-side, requiring only project access.
  Tag: [manual]

- **[P2.5]** [cg-data-quality][cg-code-quality] `scripts/issues/dispatch_client.py:245, 280-285` — mutation-path GraphQL errors are not classified with the established `_classify_graphql_errors`; `_resolve_item_id` never inspects `errors`.
  **Why**: a genuine GraphQL rejection (scope, schema) collapses to a blanket `ApiError` (exit 4) or a misleading "malformed ... missing projectItems nodes" instead of the documented `ConfigError`/exit 3, so the same failure class has two exit semantics.
  **Fix**: call `_classify_graphql_errors(data.get("errors"))` in `_resolve_item_id` and `set_project_status`; split the mapping-vs-errors checks onto separate lines.
  Tag: [safe_auto] — applied.

- **[P2.6]** [cg-testing] `scripts/tests/test_issue_dispatch.py` — the `mutator.comment` failure path is untested on all four call sites.
  **Why**: `fail_comment` exists on `FakeMutator` but is never used; the required "audit-comment ordering and partial-failure reporting" is only half-covered.
  **Fix**: add four tests (success, assign-fail, project-fail, idempotent-noop) with `fail_comment=ApiError(...)`, asserting `comment:failed` markers in `mutation_log` and exit-code behavior.
  Tag: [safe_auto] — applied.

- **[P2.7]** [cg-testing] `scripts/tests/test_issue_dispatch.py` — config-vs-api error branches on the second validation are untested.
  **Why**: `FakeReadClient.raise_error` fails the first read, so the revalidation `EXIT_CONFIG`/`EXIT_API` branch is dead under the current suite.
  **Fix**: add a `raise_after` fake control (first pass ready, second pass raises `ConfigError`/`ApiError`), two tests asserting fail-closed with zero mutations and the second error's exit code.
  Tag: [safe_auto] — applied.

- **[P2.8]** [cg-testing] `scripts/tests/test_issue_dispatch.py:624-644` — secret-isolation and constraint tests bypass GitHub's most permissive aliases.
  **Why**: scan is `glob("*.yml")` only (a `.yaml` PR workflow invisible); substring matches are case-sensitive (GitHub secret names are case-insensitive); a second dispatch workflow file is exempt if it does not reference the exact tokens.
  **Fix**: glob `*.yml` AND `*.yaml`; normalize secret references case-insensitively (also lowercase `copilot_assign_token`/`project_sync_token`); assert every dispatch-secret reference lives only in `copilot-dispatch.yml`.
  Tag: [safe_auto] — applied.

- **[P2.9]** [cg-testing]/[cg-code-quality] `scripts/tests/test_issue_dispatch.py` — `main()`'s `--no-dry-run` live path is not exercised through the CLI.
  **Why**: only parser flag flip is tested; the guaranteed live path (assign/project/comment recorded through `main`) is unverified end-to-end via the CLI.
  **Fix**: add a `main(["--issue","9002","--no-dry-run"], read_client=..., mutator=...)` test asserting `["assign","project","comment"]` and `EXIT_READY`; drop unused `capsys`.
  Tag: [safe_auto] — applied.

- **[P2.10]** [cg-code-quality] `scripts/issues/dispatch.py:334` — `build_parser(*, stderr=...)` accepts but never uses `stderr`; usage errors go to `sys.stderr`, not the injectable stream.
  **Why**: dead parameter plus a testability gap; the readiness parser wires its error stream.
  **Fix**: implement `stderr` wiring in the parser subclass (store and use it in `error()`), forward from `build_parser`.
  Tag: [manual]

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-adversarial][cg-performance][cg-data-quality] `scripts/issues/dispatch_client.py:52-63,248-300` — `_ITEM_QUERY` declares an unused `$projectTitle` parameter, and `_resolve_item_id` scans `first:50` with no `pageInfo` guard.
  **Why**: the sibling readiness query guards truncated scans (`pageInfo.hasNextPage`); a full 50-node scan that misses the target produces a misleading ConfigError.
  **Fix**: add `pageInfo { hasNextPage }` and fail closed (`ApiError`) when the target is not found and `hasNextPage` is true; drop the dead `$projectTitle` or use the shared `PROJECT_TITLE` constant.
  Tag: [safe_auto] — applied.

- **[P3.2]** [cg-adversarial][cg-architecture] `scripts/issues/dispatch_client.py:189` — assign body hardcodes `"base_branch": "main"` while the workflow/checkout uses `github.event.repository.default_branch`.
  **Why**: the two "default branch" sources can diverge on a rename, silently mis-targeting the Copilot agent's base branch.
  **Fix**: derive the base branch from a single source of truth (e.g., pass `github.event.repository.default_branch` through, falling back to `main`).
  Tag: [advisory]

- **[P3.3]** [cg-code-quality] `scripts/issues/dispatch.py:55` — `EXIT_REASONS_DISPATCH` re-declares the four readiness reasons instead of extending `EXIT_REASONS`.
  **Why**: drift risk in the shared JSON `exitReason` schema.
  **Fix**: `EXIT_REASONS_DISPATCH = {**EXIT_REASONS, ...}` importing from `.contract`.
  Tag: [safe_auto] — applied.

- **[P3.4]** [cg-code-quality] `scripts/issues/dispatch.py:137` — duplicated config/api early-return and audit-comment write blocks within `run_dispatch`.
  **Why**: ~30 duplicated lines; primary driver of the 300-line overflow (see P1.3).
  **Fix**: extract `_error_dispatch_result` and a `_try_audit_comment` helper.
  Tag: [safe_auto] — applied (light extraction).

- **[P3.5]** [cg-code-quality][cg-documentation] `render_json` (one-line docstring), `render_human`/`build_parser`/`main` (missing Example) — docstring completeness vs sibling `render.py`/`cli.py`.
  **Why**: the module convention documents Args/Returns/Example on every public function.
  **Fix**: add full docstrings.
  Tag: [safe_auto] — applied.

- **[P3.6]** [cg-code-quality] `scripts/issues/dispatch_client.py:148` — `_repo()` reimplements repo resolution and JSON shape guards already present in `gh_client._repo_owner_name` / `client_utils.expect_mapping`.
  **Why**: fabricated duplication and a fourth `json.loads` site.
  **Fix**: reuse `expect_mapping` and a shared resolve-repo helper.
  Tag: [manual]

- **[P3.7]** [cg-code-quality] `scripts/issues/dispatch_client.py:66` — `_default_mutation_runner` duplicates `_default_run_gh` exception translation and hardcodes the 60s timeout.
  **Why**: a JSON/CLI tool must keep one documented timeout/translation source.
  **Fix**: delegate to `_default_run_gh` with an optional `env`/`token` parameter using `GH_TIMEOUT_SECONDS`.
  Tag: [safe_auto] — applied.

- **[P3.8]** [cg-code-quality][cg-architecture] `scripts/issues/dispatch_client.py:193,313` — temp-file write+`finally` unlink duplicated in `assign()`/`comment()`.
  **Why**: ~12 duplicated lines with a drift-prone cleanup guarantee (see P2.3).
  **Fix**: extract `_write_temp_file(text, suffix)` helper/context manager.
  Tag: [safe_auto] — applied.

- **[P3.9]** [cg-code-quality][cg-data-quality] `scripts/issues/dispatch_client.py:270,294` — magic literal `"CompoundGPID-progress"` (twice) and `"In progress"` status in `_PROJECT_STATUS_OPTION_IDS` instead of `PROJECT_TITLE` / `IN_PROGRESS_STATUS` constants.
  **Why**: project-identity/status strings duplicated across modules invite silent drift.
  **Fix**: import and use `PROJECT_TITLE` and `IN_PROGRESS_STATUS`.
  Tag: [safe_auto] — applied.

- **[P3.10]** [cg-code-quality][cg-testing] `scripts/tests/test_issue_dispatch.py:461,473` — dead `capsys` fixture params; redundant duplicate assertion in `test_assign_called_with_exact_login`.
  **Why**: dead parameters signal the output stream is not asserted; the same literal is pinned twice.
  **Fix**: assert on `capsys.readouterr()` in the main test or drop; keep a single login assertion.
  Tag: [safe_auto] — applied.

- **[P3.11]** [cg-testing] `scripts/tests/test_issue_dispatch.py` — exit codes 5/6/7 asserted only against constants imported from the unit under test; literals never pinned.
  **Why**: if `EXIT_ASSIGN_FAILED`/`EXIT_PROJECT_UPDATE_FAILED`/`EXIT_RECHECK_FAILED` were accidentally collapsed, every test would still pass.
  **Fix**: pin the literals (assert `EXIT_ASSIGN_FAILED == 5`, `EXIT_PROJECT_UPDATE_FAILED == 6`, `EXIT_RECHECK_FAILED == 7`, or use numeric literals in the failure tests).
  Tag: [safe_auto] — applied.

- **[P3.12]** [cg-testing] `scripts/tests/test_issue_dispatch.py:596-604` — concurrency/permission static assertions evadable (group prefix-superset rename; other `*: write` scopes).
  **Why**: `"group: copilot-dispatch"` substring passes for `copilot-dispatch-prod`; only two write scopes are blocked.
  **Fix**: stricter line-level concurrency assert and an explicit allowed-scope allowlist for `permissions:`.
  Tag: [advisory]

- **[P3.13]** [cg-documentation] `scripts/issues/dispatch_client.py:327` — `DispatchMutator` protocol methods lack docstrings; class uses "Args:" where the sibling dataclass uses "Attributes:".
  **Why**: protocol is the surface `run_dispatch` depends on and should document itself.
  **Fix**: add brief docstrings; align style.
  Tag: [advisory]

- **[P3.14]** [cg-documentation] `docs/copilot-dispatch.md` — no machine-readable JSON schema documented although the workflow always runs `--json`.
  **Why**: operators consume the JSON payload but the exact reason strings/fields are only in code; the readiness sibling documents its JSON result.
  **Fix**: add a "JSON result" section with a worked example and reason-string mapping.
  Tag: [advisory]

- **[P3.15]** [cg-documentation] `docs/copilot-dispatch.md:88` — exit-code row 2 doesn't note the already-dispatched overlap with row 0.
  **Why**: an issue not-ready solely because Copilot is already assigned returns exit 0 (idempotent no-op), not 2; the table alone could mis-map it.
  **Fix**: add a parenthetical/footnote linking to guarantees item 6.
  Tag: [advisory]

- **[P3.16]** [cg-version-control][cg-reproducibility] `scripts/issues/dispatch_client.py:32-36` — deployment-specific Project node/field/option IDs frozen in source with no override path.
  **Why**: a fork/recreated Project fails with opaque errors; opaque IDs in a public repo invite misreading as sensitive values.
  **Fix**: inject via environment (fail-closed) or document them as verified deployment-specific constants on the dispatch page.
  Tag: [advisory]

- **[P3.17]** [cg-reproducibility] `scripts/issues/dispatch.py:351-358` — `--dry-run` is an inert always-true flag; only `--no-dry-run` drives behavior.
  **Why**: brittle; a maintainer "fixing" the redundancy could invert semantics and enable live dispatch by default.
  **Fix**: use an explicit opt-in pair (`argparse.BooleanOptionalAction`) so the default stays provably safe.
  Tag: [advisory]

- **[P3.18]** [cg-architecture] `.github/workflows/copilot-dispatch.yml:61-65` + `_repo()` — both secrets exported unconditionally (including dry-run), and `_repo()` resolves repo metadata with the assign credential even on the project path.
  **Why**: the "never combined in a single command" boundary holds only inside Python's per-command selection, not at process scope; a future env-dumping step would expose both.
  **Fix**: split dry-run validation (no secrets) from live dispatch steps, or scope secret env to the live branch; make `_repo()` credential-neutral.
  Tag: [advisory]

- **[P3.19]** [cg-data-quality] `scripts/issues/dispatch.py:350` — `--issue type=int` accepts `0` and negatives; `run_dispatch` performs no positivity check.
  **Why**: issue numbers are strictly positive; `--issue 0` flows into a live `gh issue view 0` misclassified as ConfigError.
  **Fix**: reject non-positive `issue_number` at the top of `run_dispatch`/parser.
  Tag: [advisory]

- **[P3.20]** [cg-data-quality] `scripts/issues/dispatch_client.py:172` — `assign()` trusts its `login` argument; the "anything else must never be assigned" invariant is enforced only at the caller.
  **Why**: defense-in-depth should enforce the constant at the single credential-holding boundary.
  **Fix**: `if login != COPILOT_ASSIGN_LOGIN: raise ConfigError(...)` at the top of `assign`.
  Tag: [advisory]

- **[P3.21]** [cg-data-quality] `scripts/issues/dispatch_client.py:288` — `_resolve_item_id` silently skips non-Mapping nodes and non-Mapping/null `project` objects.
  **Why**: present-garbage treated as deliberate absence, producing a plausible-but-wrong ConfigError.
  **Fix**: `expect_mapping` on each node/project; only `project: null`/missing is a deliberate skip.
  Tag: [advisory]

- **[P3.22]** [cg-version-control] branch `issue-implementation-phase5` lacks a `type/` prefix (accepted de-facto — matches the repo's phase-branch scheme `issue-implementation-phase-4`, etc.). No action.
  Tag: [advisory]

### ✅ Passed / Verified Clean

- [cg-adversarial] argv-safe/`--input`/`--body-file` isolation; no command injection; no secret leakage in argv/log/comment; dry-run zero-mutation verified across all branches; typed-invalid reads map to ApiError not crash; exit-code 5/6/7 mutually exclusive.
- [cg-version-control] zero secret literal in any changed file; `.gitignore` adequate for temp files; clean PR/commit split; no lockfile churn; protected artifacts untouched.
- [cg-performance] `_repo()` caches correctly (one `gh repo view` total); temp-file I/O negligible; second validation cost bounded and intentional.
- [cg-reproducibility] tests hermetic/order-independent; cross-platform safe; Python/actions SHA-pinned; no absolute paths; no seeds needed.

## Autofix disposition (Step 4)

`safe_auto` findings applied and verified (see `findings:` frontmatter → `fixed`):
P1.1, P1.2, P2.3, P2.5, P2.6, P2.7, P2.8, P2.9, P2.10, P3.1, P3.3, P3.4,
P3.5, P3.7, P3.8, P3.9, P3.10, P3.11.

Note: P2.10 (dead `build_parser` `stderr` parameter) was resolved by P1.1 —
reusing `_ReadinessArgumentParser` wires the injectable stderr stream, so it is
marked fixed rather than left open/manual.

`/cg-fix-triage` pass (same session) additionally applied the manual/advisory
findings where the change was concrete and low-risk, and recorded the three
accepted advisories as `skipped`:

- Applied in fix-triage: **P1.3** (split dispatch into orchestration +
  `dispatch_render` + `dispatch_cli`, facade re-exports), **P2.1** (verify the
  assign response contains `copilot-swe-agent[bot]`, fail closed to exit 5 on a
  silent no-op), **P2.2** (verify the Project mutation success shape before
  declaring `In progress`), **P2.4** (resolve the project item via the project
  node so `PROJECT_SYNC_TOKEN` needs no repo/issue read), **P3.2** (base branch
  derived from the repo's default branch, not a hardcoded literal), **P3.6**
  (reuse `expect_mapping`), **P3.12** (harden concurrency/permission static
  asserts), **P3.13** (protocol method docstrings), **P3.14/P3.15/P3.16**
  (dispatch docs: JSON schema, exit-code overlap note, deployment IDs
  documented), **P3.17/P3.18/P3.22** recorded as skipped (accepted advisories:
  inert `--dry-run` flag kept as the safe default and test-locked; secret env
  scope follows the workflow input; branch naming matches the repo's established
  phase-branch scheme).

Validation after fix-triage: dispatcher suite 77 passed; readiness 194 passed;
docs-site passed.
