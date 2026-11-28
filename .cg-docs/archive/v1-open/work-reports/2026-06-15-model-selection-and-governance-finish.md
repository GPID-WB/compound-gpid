---
date: 2026-06-15
plan: ".cg-docs/plans/2026-06-15-model-selection-and-governance-finish.md"
status: in-progress
completed-phases: [1]
current-phase: 2
generator-model: unknown
generator-vendor: unknown
generator-source: model-picker
---

# Work Report: Model Selection and Governance Finish

## Summary

Implemented Phase 1 guardrails for the OpenAI-first model-governance milestone:

- added `.github/shared/model-catalog.json` as the durable source of truth for
  model names, vendor/family/role metadata, frontmatter support status, and
  prompt/agent assignments;
- replaced `docs/model-guide.md` with the OpenAI-first policy, inherited
  model-picker exceptions, frontmatter support matrix, and parseable
  `### Prompts` / `### Agents` assignment tables;
- extended `scripts/cg_audit_context.py` to enrich model declarations with
  catalog metadata and report OpenAI-first, Haiku-role, Sonnet-role, stale-name,
  support-gap, and missing-assignment checks;
- added Python tests for catalog enrichment and model-guide assignment parsing;
- updated `tests/model-assignments.Tests.ps1` comments to point at
  `. tests\Run-Tests.ps1` rather than direct `Invoke-Pester`;
- updated the release checklist with external GPT frontmatter validation gates.

## Evidence

| Check | Result | Notes |
| --- | --- | --- |
| Catalog JSON syntax | Passed | `python3 -m json.tool .github/shared/model-catalog.json >/dev/null` |
| Python audit tests | Passed | `python3 -m pytest scripts/tests/test_audit_context.py` -> 73 passed |
| Context/model audit generation | Passed | `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both` |
| Diff hygiene | Passed | `git diff --check` |
| Pester safe runner | External | Must be run in VS Code/PowerShell via `. tests\Run-Tests.ps1` |
| Copilot exact GPT frontmatter validation | External/blocking for Phase 2 | `GPT-5.3-Codex`, `GPT-5.4`, `GPT-5.5`, `GPT-5 mini`, and `GPT-5.4 mini` are visible in the picker but still recorded as `not-tested` for YAML frontmatter support |

## Current Audit State

The audit now classifies every prompt and agent with a catalog role:

- missing catalog assignments: 0
- invalid catalog roles: 0
- stale model names: 0

It also intentionally reports current policy violations from the existing
Sonnet/Haiku defaults before Phase 2 model changes:

- OpenAI-first violations: 19
- Haiku role violations: 2
- Sonnet role violations: 19
- preferred model support gaps: 21
- model-guide drift: 27

These are expected red-phase findings. Phase 2 should only rewrite broad
frontmatter after VS Code/Copilot confirms exact GPT model strings are accepted
in prompt/agent YAML, or after the workflow chooses an explicit inherited/manual
model-picker fallback.

## Deviations

- Runtime deviation policy was treated as autonomous because the user invoked
  `/cg-work review:auto deviate:auto`, even though the plan frontmatter stores
  `deviation-policy: "ask"`.
- Did not dispatch `@cg-roadmap`; Phase 1 made no roadmap status writes.
- Did not close #92, #93, or #94 because final validation has not happened.

## 2026-06-16 Continuation: OpenAI Frontmatter Migration

Manual VS Code/Copilot validation confirmed that these exact prompt/agent
frontmatter strings are accepted and reflected in the Copilot model selector:

- `GPT-5.3-Codex`
- `GPT-5.4`
- `GPT-5.5`
- `GPT-5 mini`
- `GPT-5.4 mini`

After that validation, production prompt and agent frontmatter was synced to
`.github/shared/model-catalog.json`. Coding and fixing workflows now use
`GPT-5.3-Codex`; review/reasoning workflows use `GPT-5.4`; inherited prompts
continue to omit `model:`; Haiku remains only on mechanical workflows.

Updated evidence:

| Check | Result | Notes |
| --- | --- | --- |
| Exact OpenAI frontmatter validation | Passed | Manual VS Code/Copilot canary prompts, user-validated 2026-06-16 |
| Catalog JSON syntax | Passed | `python3 -m json.tool .github/shared/model-catalog.json >/dev/null` |
| Python audit tests | Passed | `python3 -m pytest scripts/tests/test_audit_context.py` -> 74 passed |
| Context/model audit generation | Passed | `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both` |
| Model policy guardrails | Passed | model drift 0; OpenAI-first violations 0; Haiku role violations 0; Sonnet role violations 0; failures 0 |
| Prompt/model Pester tests | Passed | `Invoke-Pester tests/model-assignments.Tests.ps1 -Quiet`; `Invoke-Pester tests/prompt-tools.Tests.ps1 -Quiet` |
| Full safe Pester runner | Passed | `. tests\Run-Tests.ps1` -> 2170 passed, 0 failed |
| Diff hygiene | Passed | `git diff --check` |

Issue #92 now has closure evidence for the model-governance portion: exact
OpenAI frontmatter support, prompt/agent matrix sync, docs/reference sync, and
audit/Pester guardrails all pass. GitHub issue #92 was closed on 2026-06-16
with an evidence comment, and the matching roadmap feature was marked `done`.

This report was superseded on 2026-06-16 by
`.cg-docs/work-reports/2026-06-16-token-context-optimization-closure.md`.
That later closure work prepared #93/#94 evidence: final audit failures are
zero, reviewed warnings are `fix=0`, `accept=19`, `docs-only=3`, and `/cg-work`
is below the 5,000-token audit threshold.

## Next Phase

Phase 4 decided the remaining #93/#94 scope in the 2026-06-16 closure work:

1. fix ordinary prompt broad-read warnings where the audit classified them as
   `fix`;
2. keep maintenance/safety and docs-only warnings as accepted rationale;
3. add `/cg-token-audit` as a thin deterministic advisory entrypoint.

Roadmap and GitHub issue updates still need to be performed through
`@cg-roadmap` / the issue workflow.
