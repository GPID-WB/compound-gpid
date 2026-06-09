---
date: 2026-06-09
title: "External validation must not be marked passed from static evidence"
category: "testing-patterns"
language: "Python/PowerShell/Markdown"
tags: [validation, release-readiness, pester, codex, vscode, evidence-quality]
root-cause: "A release checklist described an externally required Pester prompt-contract check as passed even though Codex had only run static audit guardrails"
severity: "P2"
plan: ".cg-docs/plans/2026-06-09-token-optimization-phase7-release-validation.md"
reviewed-in: ".cg-docs/reviews/2026-06-09-token-optimization-phase7-release-validation-review.md"
related: [".cg-docs/solutions/testing-patterns/2026-06-09-token-optimization-release-validation.md", ".cg-docs/solutions/testing-patterns/2026-06-08-token-optimization-benchmark-guardrails.md", ".cg-docs/solutions/testing-patterns/2026-04-15-pester-verbose-output-floods-context-long-session.md"]
---

# External Validation Must Not Be Marked Passed from Static Evidence

## Problem

The Phase 7 release checklist correctly separated Codex-side checks from
manual VS Code/PowerShell validation, but one row overstated the evidence:

```text
`/cg-plan` model-context note is present ... Passed through audit guardrails
and prompt tests
```

That was inaccurate. Codex had run Python audit tests and the static context
audit, but had not run Pester prompt-contract tests because no `pwsh` or
`powershell` executable was available on PATH. The checklist could have led a
maintainer to treat external Pester validation as complete.

## Root Cause

Release validation uses multiple evidence types with different harnesses:

- static audit guardrails run in Codex;
- Python audit tests run in Codex;
- Pester prompt-contract tests run in VS Code/PowerShell through the safe
  runner;
- runtime model-picker and routed-dispatch behavior runs in GitHub Copilot /
  VS Code.

The checklist row combined static evidence and external evidence in one status
phrase. Because the behavior under review was a prompt contract, "prompt tests"
looked plausible even though that harness had not run.

## Solution

Change checklist statuses to name the harness that actually ran and leave
external harnesses explicit.

The fixed status became:

```text
Passed in Codex through audit guardrails; Pester prompt-contract tests remain external
```

The review report records the finding as fixed:

```yaml
findings:
  P2.1: fixed
```

This preserves the useful Codex evidence without implying that VS
Code/PowerShell validation has happened.

## Prevention

When documenting release validation:

1. Use evidence-specific statuses: "Passed in Codex", "Passed in
   VS Code/PowerShell", "External validation required", or "Not run".
2. Do not use broad phrases like "tests passed" when only one test harness ran.
3. If PowerShell is unavailable, say exactly that and keep Pester as an
   external requirement.
4. Treat static audit guardrails as evidence for static prompt state, not proof
   of runtime Copilot behavior.
5. In review reports, mark fixed findings in frontmatter only after the
   documentation row itself has been corrected.

## Related

- `.cg-docs/reviews/2026-06-09-token-optimization-phase7-release-validation-review.md`
- `.cg-docs/cost/token-optimization-release-checklist.md`
- `.cg-docs/solutions/testing-patterns/2026-06-09-token-optimization-release-validation.md`
- `.cg-docs/solutions/testing-patterns/2026-06-08-token-optimization-benchmark-guardrails.md`
- `.cg-docs/solutions/testing-patterns/2026-04-15-pester-verbose-output-floods-context-long-session.md`
