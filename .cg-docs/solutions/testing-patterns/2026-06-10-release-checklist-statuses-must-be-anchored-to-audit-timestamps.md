---
date: 2026-06-10
title: "Release checklist statuses must be anchored to audit-run timestamps"
category: "testing-patterns"
language: "Python/PowerShell/Markdown"
tags: [release-readiness, attestation, audit, checklist, token-optimization, stale-evidence]
root-cause: "Pre-filled 'Passed in Codex' statuses in a release checklist contain no timestamp anchor, so post-commit changes silently invalidate the attestation without any visible signal"
severity: "P1"
plan: ".cg-docs/plans/2026-06-09-token-optimization-phase7-release-validation.md"
reviewed-in: ".cg-docs/reviews/2026-06-09-token-optimization-phase7-release-validation-review-2.md"
related: [".cg-docs/solutions/testing-patterns/2026-06-09-external-validation-must-not-be-marked-passed.md", ".cg-docs/solutions/testing-patterns/2026-06-09-token-optimization-release-validation.md"]
---

# Release Checklist Statuses Must Be Anchored to Audit-Run Timestamps

## Problem

The Phase 7 release checklist had a column of pre-filled statuses like
`"Passed in Codex"` across all automated gates. Each status was static text
committed at checklist creation time, with no reference to *when* the evidence
was collected.

Because `context-audit.json` overwrites its `"generated"` timestamp on every
re-run, the checklist could point to stale evidence indefinitely. A maintainer
who adds a new broad-context-load to a prompt, does **not** re-run the audit,
and then cites the checklist would unknowingly attest to a superseded audit
run. Post-commit regressions would pass release review against the stale
attestation.

The adversarial attack path:

1. Codex runs audit at T1, commits `context-audit.json` with `"generated": "2026-06-09T17:02:00"`.
2. Maintainer adds a new prompt that re-introduces broad context loading.
3. Maintainer does NOT re-run the audit.
4. Checklist still shows `"Passed in Codex, failures 0"` for the guardrail gate.
5. Release declared complete against stale evidence.

## Root Cause

Release checklists that contain evidence summaries ("Passed in Codex") rely on
the reader understanding that the status reflects a specific run at a specific
point in time. Without an explicit timestamp anchor, the status is indistinguishable
from a perpetually-valid assertion — which it is not.

The pattern is particularly risky for checklists that are committed to the repo
(like `context-audit.json`): every re-run overwrites the artifact the checklist
pointed to, invalidating the attestation silently.

## Solution

Anchor each "Passed in Codex" status to the specific audit-run timestamp at the
time of checklist completion:

```markdown
| Guardrail failures are zero | Audit reports `Failures: 0` | Passed in Codex (2026-06-09); re-run if `.github/` files change |
```

Add a header note to the checklist explaining the re-run requirement:

```markdown
> **Re-run requirement**: Statuses in the Release Gates table reflect the audit
> run recorded in `.cg-docs/cost/context-audit.json`. If any `.github/` file
> changes after that run, re-execute the audit and verify `Failures: 0` before
> citing any "Passed in Codex" status for a future release candidate.
```

The timestamp makes stale attestations immediately visible when
`context-audit.json` is regenerated (the file's `"generated"` field changes,
diverging from the date recorded in the status column).

## Prevention

When building a release checklist that records validation evidence:

1. **Name the harness and date in every status cell**: `"Passed in Codex (YYYY-MM-DD)"`,
   not `"Passed in Codex"`. This immediately surfaces stale entries when the
   date in the status column diverges from the run timestamp in the committed
   artifact.

2. **Add a re-run requirement note** near the checklist header: name the specific
   artifact file (e.g., `context-audit.json`) and the condition that triggers a
   mandatory re-run (e.g., any `.github/` file change).

3. **Separate stable gates from time-sensitive gates**: static rules that don't
   change with each run (e.g., "Pester safe runner is required") don't need
   timestamps; automated measurement gates (e.g., "guardrail failures = 0") do.

4. **Treat committed baseline files as time-stamped snapshots**: when using a
   committed JSON file as an audit baseline (`--baseline context-audit.json`),
   ensure the file predates the change set. Never use the same-session output as
   both output and baseline — the comparison shows zero delta and hides
   regressions. Name baselines explicitly: `context-audit-phaseN-baseline.json`.

5. **Complement with harness naming**: this pattern (timestamp anchoring) works
   alongside the harness-naming rule from
   `.cg-docs/solutions/testing-patterns/2026-06-09-external-validation-must-not-be-marked-passed.md`.
   Both rules apply: name which harness ran *and* when it ran.

## Related

- [External validation must not be marked passed from static evidence](.cg-docs/solutions/testing-patterns/2026-06-09-external-validation-must-not-be-marked-passed.md)
- [Token optimization release candidates need end-to-end validation evidence](.cg-docs/solutions/testing-patterns/2026-06-09-token-optimization-release-validation.md)
- [Reviewed warning classifications close token work without hiding risk](.cg-docs/solutions/testing-patterns/2026-06-16-reviewed-warning-classifications-close-token-work.md)
- [Token Optimization Release Candidate Checklist](.cg-docs/cost/token-optimization-release-checklist.md) — the fixed checklist applying this pattern
