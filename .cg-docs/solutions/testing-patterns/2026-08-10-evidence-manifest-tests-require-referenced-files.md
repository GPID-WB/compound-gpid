---
date: 2026-08-10
title: "Evidence manifest tests must require referenced files to exist and be non-empty before hashing"
category: "testing-patterns"
language: "JavaScript"
tags: [browser-evidence, manifest, playwright, sha256, silent-skip, test-hardening, fail-loudly, existence-check]
root-cause: "Manifest hash tests wrapped each check in `if (fs.existsSync(...))`, so a manifest referencing missing or empty source, view, PDF, or screenshot files passed silently instead of failing loudly."
severity: "P1"
---

# Evidence manifest tests must require referenced files to exist and be non-empty before hashing

## Problem

The Schema 2 evidence manifest test (`scripts/evidence/tests/manifest.test.js`)
verified that recorded SHA-256 hashes matched actual file content, but each
check was guarded by `if (fs.existsSync(...))`:

```javascript
if (fs.existsSync(sourcePath)) {
  const actualSource = sha256(sourcePath);
  assert.strictEqual(cell.sourceSha256, actualSource, "...source hash mismatch");
}
```

When a manifest referenced a **missing** source, view, or print-preview PDF, the
guard made the hash assertion a no-op and the test passed. The symptom was a
manifest that "looked valid" while its referenced evidence artifacts were
absent — so corrupted or partial evidence could pass validation. A capture
failure could therefore emit (or accept) a manifest that appeared green.

A secondary symptom: the guard was dead code after the sibling hash test was
hardened, and a test named "manifest exists (SKIP if not yet captured)" was
stale — it asserted a failure, never skipped.

## Root Cause

The guarded-assertion anti-pattern: wrapping a validation assertion in an
existence check converts "file is missing" from a failure into a silent pass.
The test author's intent was to avoid throwing on missing files, but the effect
was that missing referenced evidence became indistinguishable from passing
evidence. This collides with the project's core constraint — **fail loudly,
never silently**.

## Solution

Make every referenced artifact a hard requirement: assert existence, assert
non-empty, then hash and compare — unconditionally, with a contextual message:

```javascript
const sourcePath = path.join(PROJECT_ROOT, cell.sourcePath);
assert.ok(
  fs.existsSync(sourcePath),
  `${cell.documentType}/${cell.theme} source must exist`
);
assert.ok(
  fs.statSync(sourcePath).size > 0,
  `${cell.documentType}/${cell.theme} source must not be empty`
);
const actualSource = sha256(sourcePath);
assert.strictEqual(
  cell.sourceSha256,
  actualSource,
  `${cell.documentType}/${cell.theme} source hash mismatch`
);
```

The same pattern was applied to `viewPath`, the print-preview `pdfPath`, and
every viewport `screenshotPath`. The producer (`capture.js`) shares a
byte-identical `sha256` helper, aborts on a missing artifact before writing the
manifest, and writes the manifest only once at the end — so the hardened
assertions encode a real producer invariant: a capture with a missing
referenced file cannot emit a manifest at all.

Two follow-on cleanups that became necessary after hardening:
1. **Remove the now-redundant guard**: the separate "each cell has a non-empty
   print preview artifact" test still carried `if (fs.existsSync(pdfPath))`,
   which could never be false once the hash test mandates PDF existence. Drop
   the guard and assert existence + non-empty unconditionally.
2. **Rename the stale test**: "manifest exists (SKIP if not yet captured)" never
   skipped — it `assert.fail`ed. Renamed to "manifest exists (evidence generated
   by CI capture)" because the suite is CI-gated and evidence is CI-generated.

## Prevention

- **Never guard an assertion with an existence check.** A missing input is a
  test failure with a clear message, not a reason to skip the assertion. Use
  `assert.ok(fs.existsSync(p), "label must exist")` then operate on the file.
- **Assert existence, then non-empty, then content** (hash) in that order — each
  step produces a distinct, debuggable failure instead of an opaque `ENOENT` or
  `hash mismatch`.
- **Make the test encode the producer invariant.** When the producer cannot emit
  an artifact referencing missing files, the test should enforce exactly that —
  no weaker, conditional version.
- **After hardening assertions, audit sibling tests for now-dead guards** and
  stale names. A redundant `if (existsSync)` in a neighboring test is dead code
  the moment a stronger test enforces existence.
- **Reuse the identical hash helper** between producer and test so the
  "hash-match" check is meaningful byte-level drift detection, not a masked by
  normalization.

## Related

- `.cg-docs/solutions/testing-patterns/2026-04-15-prompt-step-silent-skip-antipattern-fallback-required.md` — the silent-skip anti-pattern in prompts (same root: soft fallback instead of loud failure).
- `.cg-docs/solutions/bugs/2026-08-04-evidence-capture-axe-audit-call-site-wiring.md` — last-mile call-site wiring in the same browser evidence workflow.
- `.cg-docs/reviews/2026-08-03-editorial-theme-publishing-workflow-evidence-v2-review.md` (findings P1.3, P2.3) and its verify review `2026-08-03-editorial-theme-publishing-workflow-evidence-v2-verify-review-2.md` (P3.1, P3.3).
