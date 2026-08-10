---
date: 2026-08-10
title: "Typed-invalid gh CLI JSON payloads must map to the API-error exit code, not a crash"
category: "bugs"
language: "Python"
tags: [gh-cli, exit-codes, json, error-handling, subprocess, api-error, malformed-response]
root-cause: "JSON syntax errors were guarded, but valid-JSON/wrong-shape payloads raised uncaught ValueError/TypeError/AttributeError during field extraction, bypassing the documented exit-code contract."
severity: "P2"
---

# Typed-invalid gh CLI JSON payloads must map to the API-error exit code, not a crash

## Problem

The Compound GPID issue readiness validator (`scripts/issues/readiness.py`)
documents an exit-code contract: 0 = ready, 2 = not ready, 3 = configuration
error, 4 = API/network error (including "malformed response"). When `gh`
returned **valid JSON with the wrong shape** — a payload that parses but has
unexpected types — the validator crashed with a raw traceback and Python's
exit code 1 instead of `ApiError` → exit 4.

Confirmed symptoms:

- `gh issue view` returning `"number": "abc"` → `ValueError` from
  `int(data.get("number", ...))`, uncaught.
- `gh repo view` returning a JSON array (`[1, 2]`) instead of an object →
  `AttributeError` on `.get(...)`.
- GraphQL `projectItems.nodes` not being a list of dicts → `TypeError` /
  `AttributeError` during iteration in `get_project_status`.

For a Stage 3 dispatcher consuming the validator, exit 1 is indistinguishable
from an unrelated crash and silently breaks the contract.

## Root Cause

`_parse_json` only guarded `json.JSONDecodeError` — a **syntax** guard. The
**type-shape** of the parsed object was never validated, and field extraction
(`int(...)`, `.get(...)`, iteration) happened outside any error boundary.
`validate_readiness` / `main()` catch only `ConfigError` and `ApiError`, so
`ValueError`, `TypeError`, and `AttributeError` escaped to the interpreter.

## Solution

Wrap each payload's field-extraction block so that any
`(ValueError, TypeError, AttributeError)` becomes an `ApiError` describing the
malformed response — mirroring `_parse_json`:

```python
data = self._parse_json(out, "issue")
try:
    return IssueRecord(
        number=int(data.get("number", issue_number)),
        title=data.get("title", "") or "",
        ...
    )
except (ValueError, TypeError, AttributeError) as error:
    raise ApiError(f"malformed issue response from gh: {error}") from error
```

Applied to all four `gh` consumers in `GhCliClient`: `get_issue`,
`get_open_closing_prs`, `get_project_status` (the `nodes` loop), and
`_repo_owner_name`. Note: the `KeyError`-for-missing-project path in
`get_project_status` intentionally still returns `None` — that is a *valid*
"issue not in any project" outcome, not a malformed response.

Regression tests were added per client method
(`test_gh_cli_typed_invalid_issue_payload_raises_api_error`,
`test_gh_cli_typed_invalid_repo_payload_raises_api_error`,
`test_gh_cli_typed_invalid_pr_payload_raises_api_error`).

## Prevention

- **Guard shape, not just syntax**: when a downstream consumer depends on an
  exit-code contract, treat "parses but wrong shape/types" as the same failure
  class as "does not parse". Catch `(ValueError, TypeError, AttributeError)`
  at the extraction boundary and map to the documented API error.
- **Never let a JSON-driven CLI tool crash with exit 1** when the error
  category has a documented exit code; a consumer that branches on exit codes
  cannot distinguish a crash from a protocol failure.
- **Keep the deliberate-absence path distinct**: distinguish "field missing by
  design (return default/None)" from "field present but garbage (raise
  ApiError)" — see `get_project_status` returning `None` when the issue is not
  in any project.
- Add one regression test per remote call site that feeds a wrong-shape
  payload; a single "malformed JSON" test does not cover typed-invalid input.

## Related

- [New validation branch added without a test for the new code path](.cg-docs/solutions/testing-patterns/2026-04-15-new-validation-branch-requires-dedicated-test.md)
- [PS 5.1: ConvertFrom-Json returns bare PSCustomObject for single-element arrays](.cg-docs/solutions/bugs/2026-03-30-ps51-convertfrom-json-single-element-array-coercion.md)
- [gh CLI fixture JSON keys must match what the client parses](.cg-docs/solutions/testing-patterns/2026-08-10-gh-cli-fixture-json-keys-must-match-client-parsing.md)
- Contract documentation: `docs/copilot-readiness.md` (exit-code table, R020 notes)
- Review: `.cg-docs/reviews/2026-08-03-editorial-theme-publishing-workflow-evidence-v2-verify-review-4.md`