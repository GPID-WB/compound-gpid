---
date: 2026-08-07
plan: ".cg-docs/plans/2026-08-07-modular-compound-gpid.md"
kind: documentation
status: completed
---

# Compatibility Matrix (V11 / R9)

This matrix documents the six compatibility combinations of the modular Compound
GPID architecture: CG-only, CR-only, mixed, legacy (pre-modular) configuration,
generated-target drift, and context-budget limits.

## Legend

- **suites:** field in `compound-gpid.local.md` selects active suites.
  Absent → `[cg]` (backward compatible). Allowed values: `[cg]`, `[cr]`, `[cg, cr]`.
- Loadable modules = active suites + their transitive dependencies + kernel
  (see `.kilo/shared/context-loading.contract.md` Stage rule and
  `scripts/cg_context_budget.py`).

## Matrix

| # | Combination | Expected installed assets | Expected loaded context | Migration steps |
|---|---|---|---|---|
| CG-only | `suites: [cg]` (or absent → `[cg]`) | `.github/` canonical + 4 non-Copilot platform trees with CG prompts, agents, skills (24), instructions (4), shared contracts; **no `cr-*` assets** | Kernel + `suite-cg` + its capability deps; `cr-*` prompts/agents/skills and `latex`/`math` instructions **not loaded** | Legacy config migrates to `[cg]` automatically (Step 12); no manual steps |
| CR-only | `suites: [cr]` | `.github/` canonical + platform trees with CR prompts, agents, skills, research instructions; **no `cg-*` workflow prompts in generated trees** | Kernel + `suite-cr` + its capability deps (including `cap-research-output`, `cap-language-research`); CG workflow prompts not loaded | Set `suites: [cr]`; CG-only assets remain in canonical `.github/` but are not in the active loadable set |
| Mixed | `suites: [cg, cr]` | Full canonical + all generated trees (1214 files: CG + CR) | Both suites + all shared capability packs + kernel | Set `suites: [cg, cr]` |
| Legacy (pre-modular) | No `suites:` field, no registry in downstream project | Downstream project uses canonical `.github/` as before; generator falls back to `cg-skill-*` glob discovery with deprecation warning (Step 3) | Unchanged from pre-modular behavior | None needed; Step 12 migrates `compound-gpid.local.md` when present; registry absence triggers generator fallback |
| Generated-target drift | Any of the above | Platform trees must equal generator output at HEAD | N/A | Run `python scripts/cg_generate_targets.py --all` after canonical changes; drift gate (`test_target_drift.py`, release gate) fails loudly |
| Context budget | CG-only, CR-only, or mixed | Generator `--active-suites <list>` filters emitted assets; `cg_context_budget.py` produces module-budget manifest | CG-only generation emits 1071 files (identical to pre-modular baseline — no context increase); mixed emits 1214 | Non-modular projects unaffected; modular projects choose the suites they want loaded |

## Examples

CG-only:

```yaml
# compound-gpid.local.md
suites: [cg]
```

Mixed:

```yaml
suites: [cg, cr]
```

## Verification

- Dependencies/ownership: `python scripts/cg_validate_modules.py` (exit 0).
- Cross-suite: `python scripts/cg_validate_modules.py --check-cross-suite`.
- Context budget: `pytest scripts/tests/test_context_budget.py`.
- Migration: `pytest scripts/tests/test_config_migration.py`.
- Drift: `pytest scripts/tests/test_target_drift.py`.
