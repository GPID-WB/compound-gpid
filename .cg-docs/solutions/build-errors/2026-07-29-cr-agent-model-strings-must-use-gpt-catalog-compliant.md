---
date: 2026-07-29
title: "CR agent model strings must use GPT-5.4 — Claude Opus violates catalog policy"
category: "build-errors"
language: "PowerShell"
tags: [model-catalog, agent-frontmatter, claude-opus, gpt, policy, cr-module, model-governance]
root-cause: "CR agents ported from v0.10 carried Claude Sonnet/Opus model strings with a (copilot) suffix not present in model-catalog.json; Opus has policyStatus: user-selected-only and must not appear in agent frontmatter"
severity: "P1"
---

# CR Agent Model Strings Must Use GPT-5.4 — Claude Opus Violates Catalog Policy

## Problem

When the Compound Research (CR) module was ported from the `compound-research`
v0.10.2 branch onto `feat/compound-research-v2` (based on v1.0.3 main), all 9
CR agent files carried model strings from the old branch:

```yaml
model: Claude Sonnet 4.6 (copilot)   # 7 agents
model: Claude Opus 4.6 (copilot)     # 2 agents: cr-mathematical-verification,
                                     #            cr-econometric-reasoning
```

Two violations:
1. **`(copilot)` suffix**: Not present in `model-catalog.json` or any v1.0
   agent. The suffix is unrecognized by model-routing logic and may cause
   silent fallback to a default model.
2. **`Claude Opus 4.6`**: Has `policyStatus: user-selected-only` in the
   catalog. Models with this status must not be hard-coded in agent frontmatter
   — they may only be used when explicitly selected by the user interactively.
   Hard-coding them in an agent file bypasses the policy gate.

## Root Cause

The v0.10 branch pre-dates the v1.0 model catalog and OpenAI-first governance
policy. All model strings from that branch are stale and must be reviewed
against the current catalog before landing on main.

## Solution

Replace all CR agent `model:` fields with `GPT-5.4` (the catalog-compliant
value for review/reasoning agents in v1.0):

```bash
# One-liner for all 9 CR agents:
sed -i '' \
  's/model: Claude Sonnet 4\.6 (copilot)/model: GPT-5.4/g;
   s/model: Claude Opus 4\.6 (copilot)/model: GPT-5.4/g' \
  .github/agents/cr-*.agent.md
```

Also update any test assertions that locked in the old model value:
- Change `($fm -match 'Claude Opus 4\.6')` → `($fm -match 'GPT-5\.4')`
- Strengthen the structural loop assertion from
  `($fm -match '(?m)^\s*model:')` (presence only) to
  `($fm -match '(?m)^\s*model:\s*GPT-5\.4\s*$')` (value check)

## Prevention

**For future branch ports or module migrations:**
1. After porting agent files, always grep for non-catalog model strings:
   ```bash
   grep -rn 'model:' .github/agents/cr-*.agent.md
   ```
2. Verify every model value appears in `.github/shared/model-catalog.json`.
3. Verify no model has `policyStatus: user-selected-only`.
4. The `(copilot)` suffix is never valid in agent frontmatter — strip it if
   present.
5. Default to `GPT-5.4` for review/reasoning agents and `GPT-5.3-Codex` for
   workflow/implementation agents unless there is a documented cross-vendor
   contrast rationale.

**Test governance**: The structural agent loop in `cr-prompts.Tests.ps1`
should assert the specific model value, not just presence:
```powershell
It "[$name] has model: GPT-5.4" {
    ($fm -match '(?m)^\s*model:\s*GPT-5\.4\s*$') | Should -Be $true
}
```
This was strengthened as part of this fix (commit `8148d22`).

## Related

- `.github/shared/model-catalog.json` — authoritative model catalog
- `docs/model-guide.md` — human-readable model assignment guide
- `tests/model-assignments.Tests.ps1` — model governance test (checks format,
  not value — see P2.6 in review 2026-07-29 for rationale)
- `.cg-docs/reviews/2026-07-29-cr-module-migration-to-v1-review.md` — full
  review where P1.1 and P1.2 were identified
- `.cg-docs/solutions/testing-patterns/2026-08-03-single-command-model-overrides-need-dedicated-roles-and-baseline-audits.md` — follow-on pattern for isolated command-level model overrides in the catalog and native target mappings
