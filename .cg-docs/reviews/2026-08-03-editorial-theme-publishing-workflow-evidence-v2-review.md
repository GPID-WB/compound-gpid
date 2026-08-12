---
date: 2026-08-04
depth: standard
type: standard
plan: .cg-docs/plans/2026-08-03-editorial-theme-publishing-workflow-evidence-v2.md
findings:
  P0.1: fixed
  P0.2: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: skipped
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: skipped
---

## Review Report

**Review mode**: standard  
**Files reviewed**: 38 changed paths (generated `.cg-docs/views/**` bodies excluded)  
**Findings**: 17 (P0: 2, P1: 3, P2: 8, P3: 4)

### P0 — BLOCKING

- **[P0.1]** `evidence_schema2.py:232-237` — Evidence error counts are not type/range validated or required to be zero.
  **Why**: Negative, string, or nonzero `consoleErrors`/`axeViolations` values can pass strict validation and represent failed evidence as passing.
  **Fix**: Require non-negative integers and reject nonzero counts when `require_all_pass=True`. **[manual]**

- **[P0.2]** `capture.js:375-379` — Axe failures are encoded as `-1`, which the validator can accept.
  **Why**: A capture failure can produce a manifest that appears valid instead of failing loudly.
  **Fix**: Propagate the capture failure or emit a validator-rejected value. **[manual]**

### P1 — CRITICAL

- **[P1.1]** `generate_manifest.py:61-102` — Manifest checks and Playwright provenance are synthesized without executing the checks.
  **Why**: A generated manifest can attest browser/accessibility results that were never captured.
  **Fix**: Make the browser capture the sole attested manifest producer, or mark preflight output as non-attested and reject it in strict validation. **[manual]**

- **[P1.2]** `.cg-docs/views/evidence/curated-themes/evidence-schema2.json` — Checked-in evidence records incomplete/failed checks.
  **Why**: The derived evidence artifact does not demonstrate a passing capture, so it cannot serve as release evidence.
  **Fix**: Regenerate through the real capture path and require all checks to pass before accepting the artifact. **[manual]**

- **[P1.3]** `scripts/evidence/tests/manifest.test.js:167-204` — Manifest tests previously skipped missing source, view, and PDF files.
  **Why**: Missing referenced evidence could pass validation.
  **Fix**: Require referenced files to exist and be non-empty before hashing/checking. **[manual]**

### P2 — IMPORTANT

- **[P2.1]** `pre_render.py:39-60` — Pre-rendering skipped missing fixtures and hardcoded theme version `1`.
  **Why**: Partial evidence could exit successfully and provenance could drift from the theme registry.
  **Fix**: Fail on missing required fixtures, parse each fixture once, and use the registered theme contract version. **[fixed]**

- **[P2.2]** `evidence_schema2.py:79-84` — Timestamp validation checks format but not calendar validity.
  **Why**: Impossible dates can enter provenance while matching the timestamp regex.
  **Fix**: Parse timestamps with strict UTC datetime validation. **[manual]**

- **[P2.3]** `capture.js:407` — Screenshots and PDFs are referenced without hashes.
  **Why**: Referenced browser artifacts can change without manifest tamper detection.
  **Fix**: Add and validate SHA-256 hashes for every screenshot and PDF. **[manual]**

- **[P2.4]** `capture.js:332` — Manual `file://` URL construction was not portable.
  **Why**: POSIX absolute paths and platform-specific escaping can produce incorrect URLs.
  **Fix**: Use Node's `pathToFileURL`. **[fixed]**

- **[P2.5]** `package.json:5-12` — Browser evidence dependencies have no committed lockfile.
  **Why**: Transitive Playwright/Chromium/axe versions can drift between evidence runs.
  **Fix**: Commit a lockfile and use `npm ci` for evidence workflows. **[manual]**

- **[P2.6]** `.github/workflows/tests.yml:29-58` — Node evidence tests are not CI-gated.
  **Why**: Python CI can pass while browser evidence regressions remain undetected.
  **Fix**: Install pinned Node dependencies and run `npm test` in CI. **[manual]**

- **[P2.7]** `cg-render-doc.prompt.md:50-103` — Generated `.cg-docs/views/` sources were not explicitly excluded from publishing routing.
  **Why**: Users could attempt to republish derived outputs rather than canonical Markdown.
  **Fix**: Explicitly exclude generated views from both publishing routes. **[fixed]**

- **[P2.8]** `scripts/evidence/capture.js:281,397` — Axe is reread for every cell and fixed waits add avoidable runtime.
  **Why**: Evidence runs perform repeated I/O and unconditional sleeps.
  **Fix**: Load the axe bundle once and replace fixed waits with readiness/layout-stability checks. **[manual]**

### P3 — MINOR

- **[P3.1]** `capture.js:43,146-147` — Matrix comment and redundant `firstViewportIdentity` assignment were stale/confusing.
  **Fix**: Update the comment and remove the overwritten assignment. **[fixed]**

- **[P3.2]** `evidence_schema2.py:18,223,267` — Unused imports, an inaccurate collection annotation, and duplicate parent traversal reduced clarity.
  **Fix**: Remove unused imports, use `Collection[str]`, and iterate over `Path.parents`. **[fixed]**

- **[P3.3]** `scripts/evidence/pre_render.py:43-51` — Fixture bytes and Markdown parsing were repeated per theme.
  **Fix**: Read/decode and parse once per fixture. **[fixed]**

- **[P3.4]** `.cg-docs/views/**` — Generated derived outputs changed or were added.
  **Why**: These artifacts should be staged only when the release policy requires checked-in evidence.
  **Fix**: Confirm generated-output staging policy before committing. **[advisory]**

### Passed

- `@cg-code-quality`: Review completed; findings recorded above.
- `@cg-testing`: Review completed; findings recorded above.
- `@cg-documentation`: Review completed; no in-scope high-confidence documentation defect beyond routing noted above.
- `@cg-version-control`: No secrets, credentials, PII, or unexpected binaries found; generated-output policy noted above.
- `@cg-reproducibility`: Review completed; findings recorded above.
- `@cg-performance`: Review completed; findings recorded above.
- `@cg-architecture`: Review completed; findings recorded above.
- `@cg-data-quality`: Review completed; findings recorded above.

## Validation

- `python -m pytest scripts/artifact_views/tests/test_evidence_schema2.py scripts/artifact_views/tests/test_themes.py` — 36 passed.
- `npm test` — 19 passed.
- `git diff --check` — passed.

Parsed 17 finding IDs. If count differs from total findings above, some IDs may be non-standard.
