---
date: 2026-08-04
title: "Evidence capture must pass the bundled axe source at the audit call site"
category: "bugs"
language: "JavaScript"
tags: [browser-evidence, playwright, axe-core, call-site, regression-test, verify-pass]
root-cause: "capture.js loaded the bundled axe source and runAxeAudit required it, but the production call omitted the argument, causing page.evaluate(undefined) to abort the first capture cell."
severity: "P1"
---

# Evidence capture must pass the bundled axe source at the audit call site

## Problem

The browser evidence producer loaded the bundled `axe-core` source and defined
`runAxeAudit(page, axeSource)`, but the capture loop called
`runAxeAudit(page)` instead. The first cell therefore failed before producing an
attested manifest.

## Root Cause

This was a last-mile wiring failure: the dependency was prepared in the caller
and required by the helper, but the call site was not updated when the helper
contract was introduced.

## Solution

Pass the already-loaded source at the production call site:

```javascript
axeResults = await runAxeAudit(page, axeSource);
```

Add a regression test that reads the capture source and asserts the call
contains `axeSource`. This catches the exact omission without requiring a
browser launch.

Validation completed:

- `npm test`: 20 tests passed.
- Canonical PowerShell regression suite: passed with zero failures.

## Prevention

When a helper gains a required argument, re-read every production call site
immediately after editing it. Add a call-site regression assertion before
marking the finding fixed; checking only that the helper and imported
dependency exist can miss a dead or incorrectly wired path.

## Related

- `.cg-docs/solutions/bugs/2026-05-20-fix-helper-written-but-not-wired-into-call-site.md`
  — the same last-mile wiring failure pattern in a different protected path.
- `.cg-docs/reviews/2026-08-03-editorial-theme-publishing-workflow-evidence-v2-verify-review.md`
  — source verification finding P1.4.
