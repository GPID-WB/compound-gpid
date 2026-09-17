---
date: 2026-09-17
title: "Build documentation from one validated snapshot and refresh native evidence"
category: "testing-patterns"
language: "both"
tags: [documentation, provenance, native-help, regression-tests]
root-cause: "Separate reads split validated facts, while later bound-source edits invalidate historical host evidence."
severity: "P2"
plan: .cg-docs/plans/2026-09-16-documentation-ia-ux-redesign.md
reviewed-in: .cg-docs/reviews/2026-09-16-documentation-ia-ux-redesign-review.md
---

# Build Documentation From One Validated Snapshot

## Problem

A documentation projection reopened the help catalog after its Python writer
validated and rendered the tables. A file change between those reads produced
different command facts and documentation from one nominal build. Separately,
final review changed a documentation writer included in the native help evidence
inventory, making the earlier successful Kilo proof stale.

## Root Cause

Validating a pathname does not validate future reads of that path. Source-bound
certification also covers its declared inventory, including helper code that
does not directly change host behavior. A previous successful run cannot prove
unchanged runtime behavior after that inventory changes.

## Solution

`scripts/help/documentation.py::expected_bundle` generates expected catalog
bytes, compares one secure read against them, and renders both catalog facts and
documents from that same validated value. `--stdout-docs` returns a single
catalog/documents envelope. The Node projection never reopens the catalog.
The regression mutates the catalog after the Python subprocess returns and
requires the projection to retain the validated snapshot.

Native help probes run in a detached checkout at an exact committed subject.
The observer checks received query fingerprints, fixed shell operations and
unchanged displayed Markdown. The current combined support artifact is assembled
only from successful real probe receipts and exact Git-object source bindings.
The strict verifier rejects changed bound paths, bytes and evidence anchors.

After the writer correction, fresh probes exposed model progress prose in the
user-visible result. The approved prompt repair explicitly prohibits commentary
before and between tools; it does not discard text in the observer or relax the
comparison. The three-flow test passed on
`4358ca4f46881d1373109be6f712b02ed1bc72ee` in 134.79 seconds. This is evidence for
the recorded Kilo 7.4.20/macOS/model configuration, not all hosts or models.

Verification commands:

```sh
python3 scripts/cg_generate_help_catalog.py --check-docs
python3 scripts/cg_verify_help_support.py --evidence .cg-docs/work-reports/2026-09-17-docs-help-support.json
npm run test:docs-automation
```

The final docs suite passed 199 tests. The focused adapter/generation suite
passed 261 tests; the canonical Pester runner passed 3,008 with zero failures
and three Windows-only skips. See the work report for native host pins, earlier
failed runs and final publication gates.

## Prevention

- Pass the validated value across process boundaries instead of reading again.
- Test a mutation at the boundary, rather than only checking stable fixtures.
- Recreate native proof after any declared sensitive input changes; do not reuse
  an older pass because the edit appears unrelated to runtime behavior.
- Keep negative evidence checks and exact-response assertions intact. Prompt
  repairs belong in the canonical source and generated adapters together.
- Preserve externally owned help sections and all prose outside their markers.

## Related

- [Cross-file contract alignment](2026-07-24-cross-file-contract-state-must-align-docs-validator-tests.md)
- [Wiki ownership notifications](../bugs/2026-05-19-cg-compound-wiki-update-silently-skipped-all-manual-pages.md)
- [Execution report](../../work-reports/2026-09-16-documentation-ia-ux-redesign.md)
