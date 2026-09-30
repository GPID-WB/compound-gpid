---
date: 2026-08-11
title: "GitHub workflow_dispatch booleans fail open; verify mutation responses, not just return codes"
category: "testing-patterns"
language: "Python"
tags: [github-actions, workflow-dispatch, dry-run, fail-closed, gh-cli, mutation-verification, security, controlled-dispatch]
root-cause: "A workflow_dispatch boolean input compared only for the exact lowercase 'true' string routes every unexpected value (typo, empty, API serialization) to the LIVE path; and mutation clients trusted the gh return code instead of verifying the persisted response, allowing silent false-success."
severity: "P1"
---

# GitHub workflow_dispatch booleans fail open; verify mutation responses, not just return codes

## Problem

Phase 5 of the Copilot issue-implementation pipeline introduced a
`workflow_dispatch`-only dispatcher (`copilot-dispatch.yml` +
`scripts/issues/dispatch.py`) whose live path assigns the Copilot coding agent
and moves Project Status to `In progress`. Two fail-open bugs were found by the
`full`-depth adversarial review:

1. The workflow selected the mode with `if [ "${DRY_RUN}" = "true" ]; then
   --dry-run; else --no-dry-run; fi`. GitHub's API does not strictly validate
   boolean inputs: any value other than the exact lowercase `"true"` (a typo
   `True`/`yes`/`1`, a missing/empty value, or a future serialization change)
   silently selected the **live** assignment path — inverting the documented
   "live requires explicit opt-in" safety invariant.
2. `GhDispatchMutator.assign` ran `POST /assignees` and treated a non-zero
   `gh` return code as the only failure signal — a silent no-op (or a
   wrong-shape response) would still advance Project Status and post a
   "Dispatched" success comment. `set_project_status` likewise treated any
   no-`errors` GraphQL response as success even when `data` was `null`.

## Root Cause

- A shell branch whose safe branch is matched by an exact string and whose
  `else` is the dangerous action is fail-open by construction: the safe path
  must be the default, not an exception.
- `subprocess`/`gh` return codes indicate the transport completed; they do not
  prove the mutation persisted. For GitHub mutations the JSON response body is
  the source of truth (the assign endpoint returns the updated issue with its
  `assignees`; the Project mutation returns the updated item).

## Solution

### 1. Fail closed in the workflow: only "false" selects live

Invert the branch so every value except the exact `"false"` stays on the
dry-run (zero-mutation) path:

```bash
args=(--issue "${ISSUE_NUMBER}")
if [ "${DRY_RUN}" = "false" ]; then
  args+=(--no-dry-run)
else
  args+=(--dry-run)
fi
python scripts/issue_dispatch.py "${args[@]}" --json
```

The CLI-side `argparse` default is also `dry_run=True`, so a caller that passes
no mode flag gets a dry run.

### 2. Verify the assign response body, then verify the mutation success shape

After `POST /assignees`, parse the returned issue and require the requested
login to be present — a missing assignee is an `ApiError` (fail closed, exit 5):

```python
data = expect_mapping(json.loads(out.stdout), "assign response", ApiError)
assignees = data.get("assignees")
if not isinstance(assignees, list) or not any(
    isinstance(item, Mapping) and item.get("login") == login for item in assignees
):
    raise ApiError(f"assignment did not persist: assignee {login!r} not returned")
```

For the Project mutation, classify GraphQL `errors` with the shared helper and
then require the success subtree — a no-errors `null` `data` must not be
reported as `In progress`:

```python
data = expect_mapping(json.loads(stdout), "graphql response", ApiError)
_classify_graphql_errors(data.get("errors"))
updated = data["data"]["updateProjectV2ItemFieldValue"]["projectV2Item"]["id"]
if not isinstance(updated, str) or not updated:
    raise ApiError("Project Status update returned an empty item id")
```

### 3. Keep dispatch modules acyclic and small

The P1.3 module split (orchestration vs render vs CLI) initially re-imported
leaf modules from the facade, creating a cycle (`dispatch` ⇄ `dispatch_cli` ⇄
`dispatch_render`) that broke standalone `import issues.dispatch_cli`. Fix: a
leaf `dispatch_contract.py` holds shared types/constants; `dispatch_cli` defers
`from .dispatch import run_dispatch` into `main()` (mirroring the readiness
`cli.py` pattern); the facade `dispatch.py` is import-after-definition with an
acyclic graph. All `scripts/issues/*.py` modules are now <= 279 lines.

## Prevention

- **Fail-closed defaults for a safety switch**: the dangerous branch (`live`
  assignment, deletions, release actions) must be selected only by an exact,
  explicit opt-in value; everything else follows the safe path. Add a test that
  asserts the workflow stays dry for at least one non-exact value (e.g. `True`).
- **Verify mutations from the response, not return codes**: for every mutation
  whose outcome advances pipeline state, parse and check the JSON body (assignee
  list present, success subtree shape). Add one regression test per remote call
  site that feeds a typed-invalid payload (see the existing typed-invalid gh
  payload solution).
- **Schema-shape discipline on writes**: reuse `expect_mapping` /
  `_classify_graphql_errors` on the mutation path too, so present-but-wrong data
  maps to the documented `ApiError`/`ConfigError` exit codes, never a raw
  traceback (exit 1).
- **Acyclic module split for Python tooling**: shared types/constants go in a
  leaf; cross-module runtime dependencies (`run_dispatch` in `main()`) are
  deferred inside functions; keep every `scripts/issues/*.py` module under 300
  lines.

## Related

- [Typed-invalid gh CLI JSON payloads must map to the API-error exit code, not a crash](.cg-docs/solutions/bugs/2026-08-10-typed-invalid-gh-cli-payloads-crash-exit-code-contract.md)
- [gh CLI fixture JSON keys must match what the client parses](.cg-docs/solutions/testing-patterns/2026-08-10-gh-cli-fixture-json-keys-must-match-client-parsing.md)
- [Python circular import: brain/__init__.py cannot promote lazy sub-module imports to top-level](.cg-docs/solutions/bugs/2026-05-29-python-circular-import-brain-init-requires-lazy-imports.md)
- Review: `.cg-docs/reviews/2026-08-11-copilot-issue-implementation-pipeline-v2-phase5-review.md`
- Docs: `docs/copilot-dispatch.md`, `docs/copilot-readiness.md`
