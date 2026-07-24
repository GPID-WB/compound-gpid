---
date: 2026-07-24
title: "Positive validator fixtures must avoid placeholder evidence once validation tightens"
category: "testing-patterns"
language: "Python"
tags: [pytest, fixtures, validator, placeholder-host, source-pack, wb-report-writing, verify-pass]
root-cause: "A shared 'valid' fixture kept using example.org placeholder URLs after the validator started rejecting placeholder hosts, so positive tests encoded data that no longer satisfied the real contract."
severity: "P1"
---

# Positive Validator Fixtures Must Avoid Placeholder Evidence Once Validation Tightens

## Problem

The World Bank report-writing validator was tightened to reject placeholder
hosts like `example.org` in approved source-pack evidence. The production
source-pack JSON files were updated, but the shared pytest helper
`_valid_source_pack()` still returned placeholder terminology and exemplar URLs.

That created a false "valid fixture" contract inside the test suite. When the
verify pass reran `scripts/tests/test_validate_wb_writing_skill.py`, three tests
failed even though the validator itself was behaving correctly:

- `test_validate_source_pack_passes_for_valid_payload`
- `test_validate_source_pack_accepts_unresolved_terminology_status`
- `test_run_validation_all_combines_requested_checks`

The failure was not in the validator branch. It was in the supposedly-valid
test data.

## Root Cause

The positive fixture stopped matching the real input contract after validation
rules tightened.

The validator explicitly rejected placeholder hosts:

```python
def _is_placeholder_host(value: str) -> bool:
    parsed = urlparse(value)
    host = (parsed.netloc or "").lower()
    return host == "example.org" or host.endswith(".example.org")
```

But the shared fixture still emitted values like:

```python
"terminology_sources": ["https://example.org/terms"]
"source": "https://example.org/a"
```

Because several tests reused the same helper, one stale fixture polluted
multiple positive paths at once.

## Solution

Treat shared "valid" fixtures as first-class contract artifacts.

Update the fixture immediately when the validator contract changes so it uses
evidence the validator will actually accept:

```python
"terminology_sources": [
    "https://www.worldbank.org/en/about/unit/decdg",
    "https://www.worldbank.org/en/publication/wdr",
],
"exemplars": [
    {
        "title": "Exemplar A",
        "source": "https://www.worldbank.org/en/research/dime",
    },
    {
        "title": "Exemplar B",
        "source": "https://www.worldbank.org/en/research",
    },
]
```

Then rerun the narrow executable check that exercises the helper directly:

```text
.venv\Scripts\python.exe -m pytest scripts/tests/test_validate_wb_writing_skill.py -q
```

In this case, the result moved from `3 failed, 18 passed` to `21 passed` once
the fixture matched the real validator contract.

## Prevention

1. Whenever a validator tightens what counts as valid input, audit every shared
   positive fixture in the same session.
2. If a helper is named `valid_*`, assume it is part of the contract surface,
   not just test scaffolding.
3. Prefer realistic reviewed URLs or repo-relative paths in positive fixtures;
   reserve placeholder hosts for explicit negative tests only.
4. After changing a shared validator fixture, rerun the narrow test file that
   imports it before trusting broader suite results.
5. Capture this as a distinct check from broad cross-file enum drift: docs,
   validator constants, and behavioral tests can align while a stale positive
   fixture still breaks executable verification.

## Related

- `.cg-docs/solutions/testing-patterns/2026-07-24-cross-file-contract-state-must-align-docs-validator-tests.md`
- `.cg-docs/reviews/2026-07-23-wb-report-writing-technical-methodology-verify-review.md`
- `scripts/validate_wb_writing_skill.py`
- `scripts/tests/test_validate_wb_writing_skill.py`