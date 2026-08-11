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

Validate each payload's mapping/list shape and field types before access so
present malformed responses become an `ApiError` describing the malformed
response. Preserve `None` only for deliberate absence, such as an issue that
has no project item or a project item with no Status value:

```python
data = self._parse_json(out, "graphql")
if not isinstance(data, dict):
    raise ApiError("malformed graphql response from gh: expected object")
issue = data["data"]["repository"]["issue"]
if issue is None:
    return None
if not isinstance(issue, dict):
    raise ApiError("malformed graphql response from gh: issue is not an object")
```

Applied to all four `gh` consumers in `GhCliClient`: `get_issue`,
`get_open_closing_prs`, `get_project_status` (the GraphQL mapping/list path),
and `_repo_owner_name`. Missing or null issue/project/status values remain
deliberate absence; present wrong-shape values are API errors.

Regression tests cover typed-invalid issue, GraphQL, repository, PR, and
`nameWithOwner` payloads, plus deliberate absent issue/project values.

## Prevention

- **Guard shape, not just syntax**: when a downstream consumer depends on an
  exit-code contract, treat "parses but wrong shape/types" as the same failure
  class as "does not parse" and map it to the documented API error.
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
- Review: `.cg-docs/reviews/2026-08-05-copilot-issue-implementation-pipeline-v2-review.md`
