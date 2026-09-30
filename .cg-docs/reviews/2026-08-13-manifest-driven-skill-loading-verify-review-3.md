---
date: 2026-08-28
depth: light
parent-review: .cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-review.md
type: verification
findings:
  P0.1: fixed
  P0.2: fixed
  P0.3: fixed
  P0.4: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: fixed
  P1.7: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P3.1: fixed
---

# Verification Review: Compound GPID R&D Command

**Review mode**: light (`mode:verify`)
**Parent review**: `.cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-review.md`
**Findings**: 18 (P0: 4, P1: 7, P2: 6, P3: 1)

The command-selected parent is unrelated to the current plan. None of its fixed
finding blocks overlaps this change, so no current finding was suppressed.

## P0 - BLOCKING

- **[P0.1]** `.github/prompts/cg-compound-gpid-rd.prompt.md:250` and
  `scripts/cg_compound_gpid_rd_registry.py:388` - Remove confirmation is not
  bound to the displayed URL or pre-confirmation state. A same-ID concurrent
  replacement can be removed before the prompt detects the URL mismatch.
- **[P0.2]** `scripts/cg_compound_gpid_rd_registry.py:333` - Default float
  parsing rounds unknown decimal fields and accepts exponent overflow as
  infinity, violating exact unknown-field preservation.
- **[P0.3]** `scripts/cg_compound_gpid_rd_registry.py:505` - Registry mutation
  commits before success output is serialized and emitted, so the process can
  report failure after changing state.
- **[P0.4]** `.github/prompts/cg-compound-gpid-rd.prompt.md:489` - Full and
  delta metadata updates replace the registry without expected-state
  publication and can overwrite concurrent winners.

## P1 - CRITICAL

- **[P1.1]** `scripts/cg_compound_gpid_rd_registry.py:505` - Rendered mutation
  output is not checked against `MAX_REGISTRY_BYTES` before publication.
- **[P1.2]** `scripts/cg_compound_gpid_rd_registry.py:333` - Deep JSON and large
  integers can escape as uncaught `RecursionError` or `ValueError` tracebacks.
- **[P1.3]** `.github/prompts/cg-compound-gpid-rd.prompt.md:79` - Review-mode
  validation is weaker than deterministic utility validation.
- **[P1.4]** `scripts/cg_compound_gpid_rd_registry.py:630` - Empty releases,
  null-release/date combinations, and future dates pass validation.
- **[P1.5]** `scripts/cg_compound_gpid_rd_registry.py:71` - URL controls and
  whitespace can be stripped by `urlsplit` before validation.
- **[P1.6]** `scripts/cg_pr_preflight.py:40` - The authoritative native CI gate
  omits the new registry utility test suite.
- **[P1.7]** `.github/prompts/cg-compound-gpid-rd.prompt.md:228` - Relative
  utility script paths depend on the terminal working directory.

## P2 - IMPORTANT

- **[P2.1]** `tests/prompt-tools.Tests.ps1:3132` - Several security assertions
  are full-prompt searches that can pass from unrelated sections.
- **[P2.2]** `scripts/tests/test_cg_compound_gpid_rd_registry.py:1451` - Mocked
  writer failures do not prove real rollback at the final secure boundary.
- **[P2.3]** `scripts/tests/test_cg_compound_gpid_rd_registry.py:117` - CLI
  behavior is not tested through a real subprocess.
- **[P2.4]** `scripts/tests/test_cg_generate_targets.py:339` - Adapter parity is
  not compared directly with canonical prompt body bytes.
- **[P2.5]** `.github/prompts/cg-compound-gpid-rd.prompt.md:66` and
  `docs/reference.md:452` - Schema coupling and retained-history descriptions
  conflict with the implemented three-way contract and removal behavior.
- **[P2.6]** `scripts/cg_compound_gpid_rd_registry.py:141` - The public doctest
  continuation is invalid and fails `python -m doctest`.

## P3 - MINOR

- **[P3.1]** `.github/prompts/cg-compound-gpid-rd.prompt.md:252` - Remove
  guidance contains the malformed phrase `a A missing ID`.

## Verification Evidence

- Both verification agents independently reproduced the P0/P1 set.
- Focused Python verification remained green at 352 passed and 5 skipped.
- Existing focused Pester remained green, but P2.1 explains the residual test
  quality risk.
- No files were edited by reviewers.

The review cycle has not converged. Apply `/cg-fix-triage` before commit.
