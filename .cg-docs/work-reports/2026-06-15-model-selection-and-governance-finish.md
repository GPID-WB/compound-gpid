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

## Next Phase

Phase 2 should proceed after one of these is true:

1. VS Code/Copilot validates the exact GPT frontmatter strings in the release
   checklist, allowing broad OpenAI frontmatter assignment updates.
2. The implementation switches affected workflows to inherited/manual
   model-picker behavior with explicit runtime instructions and keeps the
   catalog support status as `not-tested`.

The preferred path is option 1 because it matches the user's OpenAI-first
request and keeps coding workflows explicit instead of inheriting the chat-box
model.
