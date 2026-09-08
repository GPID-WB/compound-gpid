---
date: 2026-08-17
depth: light
parent-review: .cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-phase5-review.md
type: verification
findings:
  VP0.1: open
  VP0.2: open
  VP1.1: open
  VP1.2: open
  VP1.3: open
  VP1.4: open
  VP1.5: open
  VP1.6: open
  VP1.7: open
  VP1.8: open
---

## Verification Review Report

**Review mode**: verify (light depth)
**Parent review**: `.cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-phase5-review.md`
**Files reviewed**: Phase 5 (vendor policy, import skill, tests, prompt, docs, registry)
**Findings**: 10 (P0: 2, P1: 8)

### Verification Context

This verify pass follows the Phase 5 full review. The prior review `2026-08-13-manifest-driven-skill-loading-review.md` has fixed findings P1.8-P1.12, P2.9-P2.12 (Phase 1-3 implementation). None of those findings touch the Phase 5 files, so suppression has no effect on this pass.

### P0 — BLOCKING (immediate remediation required)

- **[VP0.1]** [cg-code-quality] `scripts/cg_import_skill.py`:173-174 — Tar path traversal allows quarantine escape
  **Why**: `tarfile.extractall()` without member path validation. A crafted `git archive` response can write files outside quarantine via `../` paths.
  **Fix**: Validate every tar member before extraction; reject symlinks/hardlinks and path traversal.

- **[VP0.2]** [cg-testing] `scripts/tests/test_import_skill.py`:567-609 — TestVendorRegistration never calls register_vendor_skill()
  **Why**: Both vendor registration tests simulate output by hand without calling the actual function. Any regression in collision checks, file copy, or registry update goes undetected.
  **Fix**: Mock git dependencies and call `register_vendor_skill()` directly.

### P1 — CRITICAL (must fix before merge)

- **[VP1.1]** [cg-code-quality] `scripts/cg_vendor_policy.py`:184-187 — Regex patterns recompiled per line × per pattern
  **Why**: L×P compilations per file. Compile once before the loop.

- **[VP1.2]** [cg-code-quality] `scripts/cg_vendor_policy.py` vs `scripts/cg_import_skill.py` — Shared constants duplicated (_QUARANTINE_MARKER, registry path)
  **Why**: `_QUARANTINE_MARKER` and `_REGISTRY_PATH` are defined identically in both modules. Single-source violation.
  **Fix**: Define in `cg_vendor_policy.py` and import.

- **[VP1.3]** [cg-code-quality] `scripts/cg_import_skill.py`:150-159 — No `GIT_TERMINAL_PROMPT=0` on git subprocess calls
  **Why**: Git may prompt for credentials against untrusted remotes. Security rule requires no interactive credentials.
  **Fix**: Pass `env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}`.

- **[VP1.4]** [cg-testing] `scripts/tests/test_import_skill.py` — `fetch_to_quarantine()` has zero test coverage
  **Why**: Most security-critical function (shells out to git, extracts archives) with no mocked test.

- **[VP1.5]** [cg-testing] `scripts/tests/test_import_skill.py` — `run_import()` has zero test coverage
  **Why**: Primary orchestrator with no integration test.

- **[VP1.6]** [cg-testing] `scripts/tests/test_import_skill.py` — `is_approved_license()` completely untested
  **Why**: Public function with zero tests.

- **[VP1.7]** [cg-testing] `scripts/tests/test_import_skill.py`:325-342 — Single-file-size limit never triggered in bundle tests
  **Why**: Only bundle-size and file-count violations tested.

- **[VP1.8]** [cg-testing] `scripts/tests/test_import_skill.py`:474-493 — Determinism test relies on wall-clock timing
  **Why**: `generate_review_diff()` embeds timestamps; test passes only because both calls complete within the same second.
  **Fix**: Inject a clock or compare non-temporal portions.

### ✅ Passed

- [cg-code-quality]: Naming conventions consistent, no debug code, no hardcoded secrets
- [cg-testing]: Core admission checks (clean, secrets, injection, executable, binary, symlink) all well-tested
