---
date: 2026-06-06
depth: architecture
type: standard
plan: .cg-docs/plans/2026-06-06-cg-plan-work-context-slimming-phase4.md
review_mode: architecture
autofix: true
findings:
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
  P3.1: fixed
---

# Compound GPID Phase 4 Context Slimming Review

Review of the Phase 4 `/cg-plan` and `/cg-work` context slimming implementation.

## Findings

### P1.1 Fixed - `docs/reference.md` contradicted model-governance policy

`docs/reference.md` still documented ordinary workflow prompts as using `Claude Opus 4.6`, including `/cg-plan`, `/cg-plan-review`, and related commands. That contradicted Phase 2 model-governance policy and the regenerated audit classification that ordinary prompts inherit the GitHub Copilot model picker.

Autofix applied:

- Updated ordinary prompt rows in `docs/reference.md` to `Copilot model picker`.
- Added `tests/model-assignments.Tests.ps1` coverage so the reference table cannot regress to hard-coded premium defaults for ordinary prompts.
- Regenerated `.cg-docs/cost/context-audit.json` and `.cg-docs/cost/context-audit.md`.

Status: fixed.

### P3.1 Fixed - duplicate `/cg-plan` model-context test block

`tests/prompt-tools.Tests.ps1` had two separate `/cg-plan` model-context test blocks covering the same policy surface.

Autofix applied:

- Removed the later duplicate block.
- Kept the canonical `cg-plan.prompt.md - model-context note` coverage.

Status: fixed.

### P1.2 Fixed - `/cg-work` over-blocked plugin maintenance

Oracle follow-up found that `/cg-work` rejected any plan directive modifying `.github/` or `.cg-docs/` infrastructure, which could block legitimate Compound GPID maintenance. The guard now blocks destructive protected-asset operations while allowing explicit content edits when a plan targets Compound GPID maintenance.

Status: fixed.

### P1.3 Fixed - `/cg-work` contradicted Pester safety

Oracle follow-up found that `/cg-work` prohibited direct `Invoke-Pester` while also giving a direct file-level `Invoke-Pester` recipe. The prompt now routes failure inspection through the safe runner and `tests/last-run.json`, with prompt tests guarding against direct file-level recipes.

Status: fixed.

### P1.4 Fixed - review routing precedence could ignore explicit escalation

Oracle follow-up found that review routing precedence could be read as risk-class routing overriding explicit user mode selection. The routing contract and `/cg-review` now resolve exactly one route: verify/report-only guard behavior first, then explicit user mode, then auto risk-class routing, line-volume escalation, and config default. Auto routing applies only when no explicit mode is requested.

Status: fixed.

### P1.5 Fixed - verify fallback could skip normal routing

Oracle follow-up found that `mode:verify` could skip normal routing before Step 1.7 discovered no prior fixed review. `/cg-review` now requires Step 1.7 to run first for verify mode and continue normal routing when verify is disabled.

Status: fixed.

### P1.6 Fixed - normal review reports lacked date/depth/type frontmatter

Oracle follow-up found that verify-mode review selection sorted by `date:` while normal report frontmatter did not require `date:`. `/cg-review` now requires standard review reports to include `date`, `depth`, and `type: standard`.

Status: fixed.

### P1.7 Fixed - phases could be marked complete with failing tests

Oracle follow-up found that `/cg-work` could append `completed-phases` even when `failing-steps` remained. Step 2.5 now blocks completion when the full-suite gate fails, is partial, or in-phase `failing-steps` remain.

Status: fixed.

### P2.1 Fixed - audit did not flag standard-model hard-codes on ordinary prompts

Oracle follow-up found that ordinary prompts hard-coding a standard model could escape the premium-only audit checks. The audit now reports `ordinary_model_picker_violations` and promotes them to immediate optimization candidates.

Status: fixed.

### P2.2 Fixed - model guide contradicted standard-pinned operational prompts

Oracle follow-up found that `docs/model-guide.md` said no prompts retained explicit model assignments while `/cg-work` and `/cg-review` intentionally pin Sonnet. The guide now distinguishes ordinary model-picker prompts from standard-pinned operational prompts.

Status: fixed.

### P2.3 Fixed - legacy prompt-tools model assertions conflicted with model governance

Oracle follow-up found stale prompt-tools tests expecting `model:` frontmatter in ordinary prompts and stale model-guide per-prompt table expectations. The tests now assert model-picker inheritance for ordinary prompts and category-level model-guide governance.

Status: fixed.

## Validation

- `python3 -m pytest scripts/tests/test_audit_context.py` - passed, 55 tests.
- `python3 scripts/cg_audit_context.py --root . --format both` - passed, regenerated JSON and Markdown audit artifacts.
- `git diff --check` - passed.
- Static reference-table check for ordinary prompt model cells - passed.

Skipped:

- Pester prompt/model tests were not run because no PowerShell executable is available in this Codex environment (`pwsh`, `powershell`, and `pwsh-preview` were absent).

## Residual Risk

No remaining local review findings after autofix and Oracle follow-up fixes. Manual VS Code/Copilot validation is still required for command behavior and model picker display because this environment cannot execute Copilot prompt workflows directly.
