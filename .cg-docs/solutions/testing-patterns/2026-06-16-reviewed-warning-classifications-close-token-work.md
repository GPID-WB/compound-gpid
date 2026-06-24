---
date: 2026-06-16
title: "Reviewed warning classifications close token work without hiding risk"
category: "testing-patterns"
language: "Python/PowerShell/Markdown"
tags: [token-optimization, warning-classification, context-loading, model-governance, documentation, release-readiness]
root-cause: "A zero-failure audit can still leave ambiguous warnings unless each warning is classified as a fix, accepted maintenance/safety read, or docs-only reference and that classification is tested and reflected in release docs"
severity: "P2"
plan: ".cg-docs/plans/2026-06-16-token-context-optimization-closure.md"
work-report: ".cg-docs/work-reports/2026-06-16-token-context-optimization-closure.md"
related: [".cg-docs/solutions/testing-patterns/2026-06-08-token-optimization-benchmark-guardrails.md", ".cg-docs/solutions/testing-patterns/2026-06-09-token-optimization-release-validation.md", ".cg-docs/solutions/testing-patterns/2026-06-10-release-checklist-statuses-must-be-anchored-to-audit-timestamps.md", ".cg-docs/solutions/testing-patterns/2026-06-22-workflow-telemetry-source-path-tool-extraction.md"]
---

# Reviewed Warning Classifications Close Token Work Without Hiding Risk

## Problem

The Token Optimization & Model Governance milestone had no audit failures after
the OpenAI-first model-governance migration, but #93 and #94 could not honestly
close while the audit still emitted context-loading and token warnings. Treating
all warnings as blockers would force a broad prompt rewrite. Treating all
warnings as harmless would hide real always-on context regressions.

The hard part was distinguishing three cases:

- prompt or agent wording that should be fixed because it broadens ordinary
  runtime context;
- maintenance, safety, roadmap, setup, release, or research reads that are
  intentionally broad and should remain;
- documentation wording that mentions broad artifacts without causing runtime
  loading.

## Root Cause

The audit already separated failures from warnings, but the warning set mixed
runtime risks, safety guardrails, maintenance workflows, generated-report reads,
and docs-only references. Without a reviewed-warning taxonomy, maintainers had
to infer intent from prose each time. That made closure evidence fragile:
remaining warnings could mean either "still risky" or "intentionally accepted."

The same ambiguity appeared in documentation. Older release notes and work
reports still said #93/#94 remained open after later evidence had resolved the
work. If the docs are not updated from the regenerated audit, release guidance
drifts from the actual guardrail state.

## Solution

Extend the deterministic audit so warning triage is generated and tested, then
make documentation cite the regenerated evidence instead of stale prose.

The implemented pattern:

1. Add `reviewed_warnings` to `scripts/cg_audit_context.py`.
2. Classify every current warning as:
   - `fix`: unnecessary broad or always-on context that should be reduced;
   - `accept`: intentional maintenance, safety, roadmap, release, setup, or
     generated-report behavior;
   - `docs-only`: reference documentation that does not imply runtime loading.
3. Keep failures separate from warning classifications. A classified warning
   never downgrades a guardrail failure.
4. Add Python tests for classification behavior, recommendation rendering, and
   explicit `--root` handling.
5. Add `--recommendations` output so `/cg-token-audit` can summarize
   `.cg-docs/cost/token-advice.md` instead of asking the model to inspect broad
   project context directly.
6. Fix only the warnings classified as `fix`, including ordinary prompt broad
   context reads and `/cg-work` size.
7. Regenerate `.cg-docs/cost/context-audit.json`,
   `.cg-docs/cost/context-audit.md`, and `.cg-docs/cost/token-advice.md`.
8. Update docs and release checklists to the final evidence.

Final closure evidence on 2026-06-16:

```text
python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both --recommendations
# failures: 0
# warnings: 22
# reviewed warnings: fix=0, accept=19, docs-only=3
# /cg-work estimated tokens: 4991

python3 -m pytest scripts/tests/test_audit_context.py -q
# 82 passed

. tests\Run-Tests.ps1
# 2194 passed, 0 failed
```

## Prevention

For future token, prompt, context-loading, model-governance, or review-routing
work:

1. Do not aim for "warnings = 0" when warnings include intentional maintenance
   workflows. Aim for "failures = 0 and reviewed warnings `fix = 0`."
2. Add a reviewed-warning classification whenever a new warning category is
   introduced.
3. Test the classification and recommendation output in Python.
4. Regenerate the audit after documentation changes, because docs wording can
   affect broad-context warning tables.
5. Update user-facing docs, release checklists, and follow-up ledgers from the
   regenerated audit counts.
6. Mark historical work reports as superseded when later evidence changes their
   closure status; do not rewrite history as if the earlier run had already
   passed.
7. Keep roadmap and GitHub issue status changes separate from documentation
   updates. Prepare closure evidence in work reports, then route actual status
   writes through `@cg-roadmap` and the issue workflow.

## Related

- `.cg-docs/plans/2026-06-16-token-context-optimization-closure.md`
- `.cg-docs/work-reports/2026-06-16-token-context-optimization-closure.md`
- `.cg-docs/cost/context-audit.md`
- `.cg-docs/cost/token-advice.md`
- `.cg-docs/cost/token-optimization-release-checklist.md`
- `.cg-docs/solutions/testing-patterns/2026-06-08-token-optimization-benchmark-guardrails.md`
- `.cg-docs/solutions/testing-patterns/2026-06-09-token-optimization-release-validation.md`
- `.cg-docs/solutions/testing-patterns/2026-06-10-release-checklist-statuses-must-be-anchored-to-audit-timestamps.md`
- `.cg-docs/solutions/testing-patterns/2026-06-22-workflow-telemetry-source-path-tool-extraction.md`
