---
plan: ".cg-docs/plans/2026-08-13-manifest-driven-skill-loading.md"
date: 2026-08-17
status: in-progress
active-deviation-policy: ask
---

# Execution Report: Manifest-Driven Skill Loading

## Plan Reference

`.cg-docs/plans/2026-08-13-manifest-driven-skill-loading.md`

## Active Deviation Policy

`ask` (stored value, no runtime override)

## Completed Steps/Phases

- Phase 1 (Steps 1-2): Kilo Isolation -- completed prior session
- Phase 2 (Steps 3-5): Baseline, Strict Schemas, Manifest Resolution -- completed prior session
- Phase 3 (Steps 6-8): Secure Materialized Projection -- completed prior session
- Phase 4 (Steps 9-10): Catalog, Routing, and Projection Observability -- 2026-08-17
- Phase 5 (Steps 11-12): Controlled External Skill Vendoring -- 2026-08-17

## Phase 4 Steps Completed

### Step 9: Static Manifest-Backed Skill Catalog

- Created `scripts/cg_skill_catalog.py` with:
  - `build_catalog()`: generates catalog rows from active manifest + registry + skill frontmatter
  - `filter_catalog()`: composable filters for id, capability, suite, platform, availability, cost, owner, provenance
  - `format_compact()` / `format_full()` / `format_json()`: output formatters
  - `_load_manifest()`: staleness guard that hard-fails on missing/stale/invalid manifest
  - `route_capability()`: manifest-aware capability router (Step 10)
  - `check_inventory_leaks()`: inactive asset reference detection (Step 10)
  - CLI with `--compact`, `--full`, `--route`, `--check-leaks`, `--skip-stale-check`
- Created `scripts/tests/test_skill_catalog.py` with 35 passing tests
- Created `.github/prompts/cg-find-skill.prompt.md` (skill discovery command)
- Created `.kilo/commands/cg-find-skill.md` (Kilo command adapter)
- Created `bin/cg-find-skill` (POSIX wrapper) and `bin/cg-find-skill.cmd` (Windows wrapper)

### Step 10: Manifest-Aware Hard-Stop Routing and Inventory Leak Checks

- Updated `.github/shared/context-loading.contract.md` with:
  - `## Manifest-Aware Capability Routing` section
  - Router interface documentation (`--route`, `--check-leaks`)
  - Hard-stop behavior specification
  - Inactive reference leak detection rules
- Added `test_generated_target_content_has_no_inactive_canonical_references` to `test_target_closure.py`
- Added `TestInactiveAssetExclusion` to `test_context_budget.py` with:
  - `test_inactive_module_assets_excluded_from_loadable_globs`
  - `test_catalog_router_inactive_capability_has_remedy`

## Evidence Table

| ID | Phase | Evidence Required | Command/Artifact | Required | Status |
|----|-------|-------------------|------------------|----------|--------|
| V9.1 | 4 | Skill catalog builds from manifest+registry+frontmatter | `python -m pytest scripts/tests/test_skill_catalog.py -q` | yes | passed (35 tests) |
| V9.2 | 4 | Compact output does not spill full records | `test_compact_format_no_spill` | yes | passed |
| V9.3 | 4 | Stale manifest blocks query | `test_missing_manifest_raises_catalog_error`, `test_structurally_invalid_manifest_raises` | yes | passed |
| V10.1 | 4 | Active capability proceeds, inactive hard-stops | `TestCapabilityRouter` tests | yes | passed |
| V10.2 | 4 | Inactive reference in generated targets fails | `test_generated_target_content_has_no_inactive_canonical_references` | yes | passed |
| V10.3 | 4 | Context-budget inactive assets excluded | `test_inactive_module_assets_excluded_from_loadable_globs` | yes | passed |
| V10.4 | 4 | Router remedy is actionable | `test_catalog_router_inactive_capability_has_remedy` | yes | passed |

## Constraints Check

| ID | Constraint | Check | Result |
|----|------------|-------|--------|
| C1 | Existing tests unbroken | `python -m pytest scripts/tests/test_context_budget.py scripts/tests/test_project_manifest.py scripts/tests/test_module_registry.py -q` | passed (80 tests) |
| C2 | No hardcoded secrets | Manual scan | clean |
| C3 | No silent fallbacks | Catalog/router hard-fail on stale/missing manifest | verified |

## Remaining Uncertainty

- The `--skip-stale-check` flag is a testing convenience; production usage always performs the stale check
- The `cg-find-skill.cmd` frontmatter validation warning from Kilo's schema validator is non-blocking

## Final Status

Phase 5 completed. All evidence passed.

---

## Phase 5 Steps Completed

### Step 11: Reconcile Vendoring Roadmap Contract and Build Quarantined Intake Modes

- **R15 Roadmap reconciliation**: Updated `quarantined-external-skill-vendoring` feature in `roadmap.json`:
  - Changed `/cg-skill-import` to `/cg-import-skill` in description
  - Changed status from `idea` to `active`
  - Linked plan: `.cg-docs/plans/2026-08-13-manifest-driven-skill-loading.md`
- Created `scripts/cg_vendor_policy.py` with:
  - `load_policy()`: loads vendor-policy.json
  - `is_allowed_repository()`: HTTPS allowlist check
  - `is_safe_skill_path()`: path traversal, hidden component, reserved name, Unicode confusable checks
  - `is_allowed_extension()` / `is_blocked_extension()`: file extension enforcement
  - `scan_for_secrets()`: regex-based secret detection with redacted output
  - `scan_for_prompt_injection()`: Markdown instruction injection detection
  - `is_approved_license()`: SPDX license allowlist
  - `check_bundle_limits()`: file count, total size, single file size
  - `run_admission_checks()`: full default-deny admission pipeline
  - `verify_canonical_source_checkout()`: git remote, branch, registry verification
  - `check_identifier_collision()`: normalized collision detection
  - CLI with `--check-all`, `--list-allowed-repos`, `--check-repo`, `--check-license`
- Created `scripts/cg_import_skill.py` with:
  - Two explicit modes: `review` (consumer quarantine) and `vendor` (maintainer canonical write)
  - `parse_import_spec()`: validates full 40-char SHA, no traversal, HTTPS only
  - `fetch_to_quarantine()`: git archive or shallow clone with disabled hooks/submodules/LFS
  - `write_quarantine_meta()`: metadata marker for quarantined bundles
  - `generate_review_diff()`: deterministic, secret-redacted Markdown review evidence
  - `register_vendor_skill()`: copies approved bundle to `.github/skills/`, registers provenance in registry
  - `run_import()`: full workflow orchestrating all steps
  - CLI with `--mode review|vendor`, `--root`, `--quarantine-dir`, `--license`, `--reviewer`, `--approval-ref`
- Created `.github/shared/vendor-policy.json` with:
  - Repository identity allowlist (HTTPS only)
  - Allowed upstream skill roots
  - Bundle size limits (1MB total, 64 files, 256KB per file)
  - Allowed/blocked file extensions (`.md/.json/.yml/.yaml/.txt` allowed; executables blocked)
  - Secret detection patterns (API keys, tokens, passwords, AWS credentials, GitHub PATs)
  - Prompt-injection patterns (instruction overrides, shell execution, eval/exec)
  - Approved SPDX license list
  - Canonical source checkout verification config
- Created `.github/prompts/cg-import-skill.prompt.md` (user-facing command)
- Created `.kilo/commands/cg-import-skill.md` (Kilo command adapter)
- Created `docs/skills/importing.md` (user documentation)
- Updated `.gitignore` with `.compound-gpid/vendor-reviews/`
- Updated `.github/shared/module-registry.json` kernel `ownedAssets` to include `vendor-policy.json`

### Step 12: Add Deterministic Review, Approval, and Canonical Vendor Registration

- `generate_review_diff()` produces deterministic, secret-redacted Markdown with:
  - Source repository, commit SHA, skill path
  - File list with SHA-256 hashes
  - Admission check results (pass/fail, errors, secret findings, injection findings)
  - Provenance metadata
- `register_vendor_skill()` performs:
  - Canonical source checkout verification (registry presence, git remote, approved branch)
  - Identifier collision detection (normalized case-fold, Unicode NFKC)
  - Bundle copy to `.github/skills/`
  - Provenance registration in `module-registry.json` `vendorImports` section
  - Records: source repo, full SHA, upstream path, import date, license, reviewer, approval ref
- Created `scripts/tests/test_import_skill.py` with 52 tests covering:
  - Policy loading, repository identity, path safety, file extensions
  - Secret scanning, prompt-injection scanning, bundle limits
  - Full admission checks (clean, secrets, injection, executable, symlink, binary)
  - Identifier collision detection
  - Review diff generation (sections, hashes, redaction, determinism)
  - Import spec parsing (valid, short SHA, traversal, missing @)
  - Quarantine metadata
  - Canonical source checkout verification
  - Vendor registration with provenance
  - Full quarantine workflow integration

## Phase 5 Evidence Table

| ID | Phase | Evidence Required | Command/Artifact | Required | Status |
|----|-------|-------------------|------------------|----------|--------|
| V11.1 | 5 | Admission rejects prohibited content before mutation | `python -m pytest scripts/tests/test_import_skill.py -q` | yes | passed (51 tests) |
| V11.2 | 5 | Secret scanning detects and redacts API keys, passwords, tokens | `TestSecretScanning` tests | yes | passed |
| V11.3 | 5 | Prompt-injection scanning detects instruction overrides | `TestPromptInjectionScanning` tests | yes | passed |
| V11.4 | 5 | Executable/binary content rejected | `test_bundle_with_executable_fails`, `test_binary_content_rejected` | yes | passed |
| V11.5 | 5 | Path safety: traversal, hidden, reserved, Unicode | `TestPathSafety` tests | yes | passed |
| V11.6 | 5 | Canonical source checkout verification | `TestCanonicalSourceCheckout` tests | yes | passed |
| V12.1 | 5 | Review diff is deterministic and secret-redacted | `TestReviewDiff` tests | yes | passed |
| V12.2 | 5 | Vendor registration records full provenance | `TestVendorRegistration` tests | yes | passed |
| V12.3 | 5 | Identifier collision detection | `TestIdentifierCollision` tests | yes | passed |
| V15 | 5 | Roadmap vendoring feature reconciled to `/cg-import-skill` | targeted `roadmap.json` read | yes | verified: `/cg-skill-import` → `/cg-import-skill`, status `active`, plan linked |

## Phase 5 Constraints Check

| ID | Constraint | Check | Result |
|----|------------|-------|--------|
| C1 | Existing tests unbroken | `python -m pytest scripts/tests/test_skill_catalog.py test_context_budget.py test_project_manifest.py test_module_registry.py test_import_skill.py -q` | passed (168 tests, 2 skipped) |
| C2 | No hardcoded secrets | Manual scan of new files | clean |
| C3 | No silent fallbacks | Admission hard-fails on all prohibited content | verified |
| C7 | Imported content is non-executable, immutable, quarantined, provenance-registered | admission checks + vendor registration tests | verified |
