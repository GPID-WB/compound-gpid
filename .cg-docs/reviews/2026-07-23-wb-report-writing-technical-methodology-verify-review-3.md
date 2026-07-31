---
date: 2026-07-31
depth: light
parent-review: .cg-docs/reviews/2026-07-23-wb-report-writing-technical-methodology-review.md
type: verification
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
---

## Review Report

**Review mode**: light (verify)
**Files reviewed**: 171 changed or untracked files
**Findings**: 10 (P0: 0, P1: 6, P2: 4, P3: 0)

**Verification context**: Prior review `.cg-docs/reviews/2026-07-23-wb-report-writing-technical-methodology-review.md` had fixed findings for roadmap state, validator coverage, prompt-tools coverage, and the WB work report. None of the findings below target those explicitly fixed scopes. P0/P1 and cross-file issues were not suppressed.

### P1 - CRITICAL (must fix before merge)

- **[P1.1]** [cg-code-quality / cg-testing] `scripts/cg_audit_context.py:393` - An explicit `model: null` declaration is treated as absent execution metadata.
  **Why**: YAML null is converted to `None`, so the forbidden execution-model audit cannot distinguish inherited configuration from an explicitly present model key. A stale executable key can therefore evade the new inheritance guardrail.
  **Fix**: Check frontmatter key presence separately from its parsed value and add a regression test for `model: null`.

- **[P1.2]** [cg-code-quality / cg-testing] `scripts/cg_audit_context.py:486` - Malformed advisory bundles can pass validation or crash the audit.
  **Why**: An empty object is not validated as a bundle, non-list effort labels can raise during `set()` conversion, and a non-object `source` can raise on `.get()` access. Required source verification provenance is also not enforced.
  **Fix**: Validate the complete payload shape before field access, require source provenance fields, and add malformed-payload tests.

- **[P1.3]** [cg-code-quality / cg-testing] `scripts/cg_audit_context.py:432` - Local advisory overrides do not implement the documented warning-and-fallback contract.
  **Why**: Invalid effort values, unknown example references, and unsupported fields are not validated. Malformed blocks can raise while locating the section, and all local errors are promoted to hard guardrail failures instead of falling through to bundled or capability-only advice.
  **Fix**: Parse and validate the optional block defensively, validate known example references and effort labels, emit visible warnings for malformed optional input, and retain hard failures for executable metadata.

- **[P1.4]** [cg-code-quality / cg-testing] `.github/prompts/cg-plan.prompt.md:28` - Copilot-specific picker prose is copied unchanged into native Claude Code, Codex, and OpenCode commands.
  **Why**: Generated non-Copilot commands tell users to inspect Copilot UI details, contradicting the platform-neutral advisory contract and making generated behavior inconsistent across supported targets.
  **Fix**: Use active-platform-neutral wording in the canonical prompt, update its regression assertion, and regenerate all native targets.

- **[P1.5]** [cg-code-quality / cg-testing] `scripts/link.sh:337` and `scripts/link.ps1` - Existing consumer projects can retain legacy model-mapping artifacts after the execution policy migration.
  **Why**: The current install-unit lists no longer own the old mapping files, but a prior managed-files manifest can still record them. Linking and unlinking do not checksum-guarded-clean those stale paths, so removed execution policy artifacts can survive updates or remain permanently owned.
  **Fix**: Add parity cleanup for the legacy mapping paths in Bash and PowerShell, preserving user-modified files, and test upgrade/unlink behavior with seeded old manifests.

- **[P1.6]** [cg-testing] `.github/workflows/tests.yml:26` - The CI Python gate does not run the new advisory/audit validation tests.
  **Why**: `test_model_advisory.py` and `test_audit_context.py` protect the core migration and provenance rules, but the native-target CI job omits them. A regression can therefore merge with green CI while local focused tests pass.
  **Fix**: Register the affected advisory, audit, and documentation Python tests in the CI and release validation gates.

### P2 - IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality / cg-testing] `scripts/schemas/target_mapping_schema.json:17` - The JSON Schema accepts removed model-mapping fields through unrestricted object properties.
  **Why**: Schema validation can accept stale `modelMappingMode`, `modelMapping`, or other unknown fields even though the Python validator rejects selected legacy fields. This weakens schema-first consumers.
  **Fix**: Add `additionalProperties: false` to the affected mapping objects and add schema-level negative coverage.

- **[P2.2]** [cg-testing] `scripts/tests/test_target_opencode.py:100` and platform target tests - Generated model-inheritance checks are incomplete and asymmetric.
  **Why**: OpenCode checks agents only, while Claude and Codex cover only selected output forms. A generated command, fallback, or platform-specific file can regain executable model metadata without being detected.
  **Fix**: Scan every generated command, agent/subagent, fallback, and relevant generated configuration across all native targets.

- **[P2.3]** [cg-code-quality / cg-testing] `cg-release.prompt.md:3` - The developer-only root release prompt still has an explicit model assignment and is excluded from the migration invariant.
  **Why**: The repository-wide policy says commands and agents inherit user selection, but the only remaining prompt-level assignment is outside `.github/prompts/` and is not covered by the updated tests. This creates a stale exception by omission.
  **Fix**: Remove the model frontmatter from the root developer prompt and add an explicit root-prompt invariant test.

- **[P2.4]** [cg-testing] `scripts/tests/test_target_ownership.py:146` - Ownership tests do not seed legacy mapping artifacts during regeneration.
  **Why**: Clean fixtures prove new manifests, but do not verify that a pre-migration manifest and unchanged legacy mapping files are removed safely. The migration cleanup can regress without a test failure.
  **Fix**: Add a fixture that seeds legacy mapping files and manifest entries, then asserts unchanged files are removed and user-modified files are preserved.

### Passed

- Focused advisory, audit, mapping, OpenCode, and ownership tests: `140 passed`.
- No new P0 findings or cross-file breakage in the generated trees were identified.

### Verification Note

The clean-`HEAD` generated-target drift/release gate remains expected to fail before the requested commit because the intended canonical and generated changes are still uncommitted. It must be rerun after commit; it is not counted as a code finding in this report.
