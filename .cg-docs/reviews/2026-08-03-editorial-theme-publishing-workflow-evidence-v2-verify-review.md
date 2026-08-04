---
date: 2026-08-04
depth: light
parent-review: .cg-docs/reviews/2026-08-03-editorial-theme-publishing-workflow-evidence-v2-review.md
type: verification
findings:
  P1.2: skipped
  P1.3: skipped
  P1.4: fixed
  P1.5: skipped
  P2.3: skipped
  P2.5: skipped
  P2.6: skipped
  P2.8: skipped
  P2.9: skipped
  P2.10: skipped
  P3.4: skipped
---

## Review Report

**Review mode**: light (verification)  
**Prior review**: `.cg-docs/reviews/2026-08-03-editorial-theme-publishing-workflow-evidence-v2-review.md`  
**Files reviewed**: 38 changed paths; generated `.cg-docs/views/**` bodies excluded  
**Suppression policy**: P0/P1 and cross-file breakage always reported; P2/P3 suppressed only for blocks explicitly covered by fixed findings.

### P0 — BLOCKING

No new P0 findings.

### P1 — CRITICAL

- **[P1.2]** `.cg-docs/views/evidence/curated-themes/evidence-schema2.json` — The evidence artifact remains incomplete/failed and is not a passing attested capture.
  **Why**: The generated evidence cannot support a release claim until it is produced by the real browser capture path with all checks passing.
  **Fix**: Regenerate through Playwright capture and require strict validation before accepting the artifact.

- **[P1.3]** `scripts/evidence/tests/manifest.test.js:167-204` — Hash and file checks remain conditional on `fs.existsSync`.
  **Why**: Missing source, view, or PDF files can still bypass the checks and allow the test to pass.
  **Fix**: Fail explicitly when every referenced file is absent; then hash and validate each required artifact.

- **[P1.4]** `scripts/evidence/capture.js:366` — `runAxeAudit` is called without its required `axeSource` argument.
  **Why**: `page.evaluate(undefined)` throws on the first cell, so the capture path aborts and never writes an attested manifest.
  **Fix**: Call `runAxeAudit(page, axeSource)`.

- **[P1.5]** `.github/workflows/tests.yml:65-81` — The new schema-2 validator test file is not included in the CI Python gate.
  **Why**: Regressions in `evidence_schema2.py` can pass CI despite the new tests existing and passing locally.
  **Fix**: Add `scripts/artifact_views/tests/test_evidence_schema2.py` to the pytest command.

### P2 — IMPORTANT

- **[P2.3]** `scripts/evidence/capture.js:407` — Screenshot and PDF references still lack content hashes.
  **Why**: Referenced browser artifacts can change without manifest tamper detection.
  **Fix**: Emit and validate SHA-256 hashes for every screenshot and PDF.

- **[P2.5]** `package.json:5-12`, `.github/workflows/tests.yml:21` — Browser evidence dependencies are not installed reproducibly.
  **Why**: No committed lockfile is present and CI uses `npm install`, allowing transitive versions to drift.
  **Fix**: Commit `package-lock.json` and use `npm ci`.

- **[P2.6]** `.github/workflows/tests.yml:10-24` — The browser-evidence CI gate cannot reliably run from a clean checkout.
  **Why**: The pending evidence inputs/package are not yet part of the tracked checkout, and the manifest-dependent tests fail when the manifest is absent.
  **Fix**: Ensure required package and release evidence inputs are intentionally committed or make the workflow explicitly capture/gate them before running manifest tests.

- **[P2.8]** `scripts/evidence/capture.js:281,397` — Axe is reread per cell and fixed waits remain in the capture path.
  **Why**: Evidence generation performs avoidable repeated I/O and unconditional sleeps.
  **Fix**: Load the axe bundle once and replace fixed waits with readiness/layout-stability checks.

- **[P2.9]** `.github/workflows/tests.yml:17` — `actions/setup-node@v4` is floating while neighboring actions are SHA-pinned.
  **Why**: A mutable tag weakens the workflow’s supply-chain reproducibility.
  **Fix**: Pin setup-node to a full commit SHA.

- **[P2.10]** `.agents/skills/cg-skill-render-doc/workflows/render-document.md: routing rule 2` (and the corresponding `.claude`, `.github`, and `.opencode` copies) — The skill workflow omits the `.cg-docs/views/` exclusion.
  **Why**: An agent loading the skill without the command prompt can route generated views to the canonical Markdown publisher, contradicting the fixed prompt-level contract.
  **Fix**: Add “excluding `.cg-docs/views/` generated outputs” to rule 2 in all four copies.

### P3 — MINOR

- **[P3.4]** `.cg-docs/views/**` (path/count only) — Generated derived outputs remain subject to an unresolved staging-policy decision.
  **Why**: The review intentionally excludes generated bodies, but whether these outputs belong in the release commit is still not established.
  **Fix**: Confirm the generated-output staging policy before committing; do not treat generated views as canonical review evidence.

### Passed

- `@cg-code-quality`: Fixed P0.1, P0.2, P1.1, P2.1, P2.4, P2.7, P3.1, P3.2, and P3.3 spot-checked; no new P0.
- `@cg-testing`: Findings above; prior P2.2 calendar validation appears implemented and covered by tests.
- Generated `.cg-docs/views/**` bodies were not read or used as review authority.

Parsed 11 finding IDs.
