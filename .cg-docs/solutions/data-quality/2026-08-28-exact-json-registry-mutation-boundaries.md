---
date: 2026-08-28
title: "Secure registry mutation requires exact JSON and pre-commit output validation"
category: "data-quality"
language: "Python"
tags: [json, decimal, registry, secure-fs, atomic-write, validation, pytest]
root-cause: "Default JSON float decoding, input-only size checks, and post-commit response serialization allowed preserved values or command status to diverge from committed registry state"
severity: "P0"
---

# Secure Registry Mutation Requires Exact JSON and Pre-Commit Output Validation

## Problem

A deterministic JSON registry utility preserved unknown fields structurally but
decoded unknown numbers as binary floats. A value such as
`0.123456789012345678901234567890` was rounded during a later add or remove.
`1e400` became infinity and could make success serialization fail after the
registry mutation committed.

Three related boundaries were incomplete:

- The size limit applied to source bytes, not the larger rendered result.
- Deep JSON and large integer parser paths could escape as raw exceptions.
- Writer-failure tests replaced the secure writer instead of injecting failure
  at its final publication boundary.

## Root Cause

Schema validation alone does not preserve unknown JSON values. `json.loads()`
uses `float` by default, while `json.dumps()` cannot serialize exact
`Decimal` values without an explicit renderer. The command also rendered its
success response after publication, so response validation was not part of the
pre-commit transaction.

Input budgets and mocked storage failures gave incomplete evidence. Formatting
can make valid input larger after rendering, and a mocked writer cannot prove
that the real quarantine and rollback path restores source bytes.

## Solution

Parse every JSON number as `Decimal`, reject non-finite or unsupported values,
and serialize JSON recursively so `Decimal` tokens remain exact:

```python
data = json.loads(
    text,
    object_pairs_hook=reject_duplicate_keys,
    parse_constant=reject_nonfinite_constant,
    parse_float=Decimal,
    parse_int=Decimal,
)
```

Use an iterative tree check before recursive copy or rendering. It enforces a
maximum nesting depth and rejects values outside the JSON type set. Reject raw
URL controls and whitespace before `urlsplit()` because Python versions can
strip them differently.

Before the secure write:

1. Transform and validate the complete registry in memory.
2. Render the complete success line and fail if it is invalid.
3. Render the complete registry and enforce the byte limit on rendered bytes.
4. Bind publication to `ExpectedFileState.from_bytes(source_bytes)`.
5. Emit the prevalidated success line only after publication succeeds.

The regression suite now covers exact high-precision decimals, large finite
exponents and integers, nesting limits, URL controls, rendered-output limits,
subprocess exit streams, and failure injected through `_before_secure_replace`
with the real writer. The native preflight owns the utility test file, so CI
runs the same contract.

Verification passed with 407 focused Python tests, 1,802 native preflight tests,
and 2,723 unfiltered Pester tests. Capability-specific skips remained explicit.

## Prevention

- Treat unknown-field preservation as exact value preservation, not key
  retention only.
- Do not use binary floats when a JSON document will be read and rewritten.
- Validate the final rendered artifact and final response, not only parsed
  input or an intermediate object.
- Put response construction before the commit boundary when response contents
  can fail validation.
- Inject storage failures at the real final boundary and assert exact source
  restoration plus absence of leaked recovery artifacts.
- Add each new security-sensitive suite to the authoritative CI selector, not
  only to local focused commands.

The fix does not resolve the separate review-mode expected-state gap or the
remove-confirmation race recorded in
`.cg-docs/reviews/2026-08-28-compound-gpid-rd-command-review.md`. Do not cite
those skipped findings as solved.

## Related

- `.cg-docs/solutions/bugs/2026-03-19-persistent-state-written-before-validation-causes-corruption.md`
- `.cg-docs/solutions/testing-patterns/2026-06-23-budgeted-knowledge-brain-query.md`
- `.cg-docs/solutions/testing-patterns/2026-07-28-handle-relative-filesystem-mutations-and-real-boundary-tests.md`
- `.cg-docs/solutions/bugs/2026-08-01-secure-publication-rollback-must-not-clobber.md`
- `.cg-docs/plans/2026-08-28-compound-gpid-rd-command.md`
- `.cg-docs/reviews/2026-08-28-compound-gpid-rd-command-review.md`
