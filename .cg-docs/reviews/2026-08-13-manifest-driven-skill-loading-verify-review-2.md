---
date: 2026-08-14
depth: light
parent-review: .cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-review.md
type: verification
findings:
  P1.1: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
---

## Review Report

**Review mode**: verify (light-only)
**Files reviewed**: Phase 2 diff (registry v2 + capability resolution + strict
config parser + manifest/baseline tooling + tests + docs)
**Findings**: 11 (P0: 0, P1: 1, P2: 4, P3: 6) — all resolved by `/cg-fix-triage`.
**Prior verify review**: `.cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-verify-review.md`
(Phase 1) — this Phase 2 verify supersedes the sub-matrix that overlaps it, so
it is recorded under the `-2` name per workflow counter rules.

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-code-quality] `.github/shared/module-registry.json` (all 12 `capabilities[].supportedPlatforms`) ↔ `scripts/cg_project_manifest.py` — capability records declared platform `"claude"`, but the canonical platform id in `.github/shared/target-mapping.json` (and `docs/configuration.md`) is `"claude-code"`.
  **Why**: `_platform_eligibility` compares against the canonical id set, so every capability reported `ineligiblePlatforms: ["claude-code"]` and `platformEligibility.allEligible = False` on the default manifest.
  **Fix**: change `"claude"` → `"claude-code"` in all capability records (JSON fix). — **fixed**

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality / cg-testing] `scripts/cg_validate_modules.py` (`_derived_capability_ids_for`) — `str.removeprefix("suite-")` requires Python 3.9+, but the module enforces "Python 3.8+, stdlib only".
  **Fix**: use 3.8-safe slicing. — **fixed**
- **[P2.2]** [cg-code-quality] `scripts/cg_context_budget.py` `main()` — config read unguarded (crash on invalid UTF-8/permissions).
  **Fix**: wrap in `try/except (OSError, UnicodeDecodeError)` and return 1. — **fixed**
- **[P2.3]** [cg-code-quality] `scripts/cg_project_manifest.py` `resolve_active_manifest` — did not enforce a non-supported `config-schema-version`.
  **Fix**: reject values not equal to the supported `"2"`. — **fixed**
- **[P2.4]** [cg-testing] `scripts/tests/test_projection_benchmark.py` `test_oracle_flags_inactive_skill_leak` — negative-path assertion was absence-of-success.
  **Fix**: extract the check and assert it is present with `ok is False`. — **fixed**

### P3 — MINOR (nice to have)

- **[P3.1]** `scripts/parsing_utils.py` — dead `_ in item` branch removed. — **fixed**
- **[P3.2]** `scripts/cg_context_budget.py` — reuse shared `_strip_yaml_comment` import. — **fixed**
- **[P3.3]** `scripts/cg_context_budget.py` — drop unused `config` parameter on `explicit_capability_module_ids`. — **fixed**
- **[P3.4]** `scripts/cg_projection_benchmark.py` — align `_git_revision` docstring with the deterministic sentinel. — **fixed**
- **[P3.5]** `scripts/cg_context_budget.py` — document `filtered_manifest` v2 contract change. — **fixed**
- **[P3.6]** `scripts/parsing_utils.py` — compute physical line offsets instead of assuming the delimiter is on line 1. — **fixed**

### ✅ Passed

- [cg-code-quality] No P0; suppression policy applied; no protected-artifact modifications.
- [cg-testing] Phase 2 test batch executed (139 passed); all requested edge cases green; no cross-file breakage.

## Triage Guidance

All findings were applied by `/cg-fix-triage` and marked `fixed`. Re-verified:
Phase 2 test batch 139 passed; real-repo registry/manifest validate; baseline
regenerated; canonical safe Pester full-suite gate 2520 passed / 0 failed.
