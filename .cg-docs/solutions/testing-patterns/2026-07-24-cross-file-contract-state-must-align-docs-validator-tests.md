---
date: 2026-07-24
title: "Cross-file state contracts must align across docs, validators, and behavioral tests"
category: "testing-patterns"
language: "Python/PowerShell/Markdown"
tags: [cross-file-contract, validator, prompt-tools, verify-pass, frontmatter, state-model, wb-report-writing]
root-cause: "The skill docs, deterministic validator, and behavioral Pester checks evolved on different timelines, so terminology and source-pack state values drifted (`approved|not-required` in code vs `approved|unresolved` in docs), letting a documented-valid artifact fail deterministic preflight until a verify pass re-read the whole contract."
severity: "P1"
plan: ".cg-docs/plans/2026-07-23-wb-institutional-report-writing-skill.md"
reviewed-in: ".cg-docs/reviews/2026-07-23-wb-institutional-report-writing-skill-verify-review.md"
related: [".cg-docs/solutions/testing-patterns/2026-04-20-behavioral-pester-tests-for-skill-md-files.md", ".cg-docs/solutions/testing-patterns/2026-04-23-verify-mode-suppression-must-be-anchored-to-fixed-finding-scope.md", ".cg-docs/solutions/testing-patterns/2026-05-01-regex-alternation-masks-coverage-split-into-independent-assertions.md"]
---

# Cross-file State Contracts Must Align Across Docs, Validators, and Behavioral Tests

## Problem

The Phase 1 World Bank report-writing skill shipped with a valid thin router,
shared references, deterministic Python validator, and behavioral Pester tests.
Standard review fixed several gaps, but the follow-up verify pass still found a
real P1 regression: the shared terminology contract no longer agreed across the
files that enforced it.

The concrete mismatch was:

- shared docs described terminology as `approved` or `unresolved`
- `prompt-tools` assertions looked for `approved` and `unresolved`
- the Python validator still accepted `approved` or `not-required`

That meant a source pack that followed the documented contract could still fail
deterministic preflight. The break only surfaced when `/cg-review mode:verify`
re-read the updated docs, validator, and tests together instead of trusting the
earlier fix status.

The same review/fix sequence surfaced a second, related capture lesson: review
body prose can go stale after fix-triage, but review frontmatter remains the
durable machine-readable status contract.

## Root Cause

This was a contract-drift problem, not a single-file bug.

Three independently maintained surfaces carried the same state model:

1. `references/workflows.md` and `references/terminology.md` described the
   allowed source-pack states and preflight rules.
2. `scripts/validate_wb_writing_skill.py` enforced the deterministic artifact
   schema.
3. `tests/prompt-tools.Tests.ps1` guarded the prose contract behaviorally.

Standard review fixed some of these surfaces first, but no single invariant
test asserted that the same state vocabulary existed across all three layers.
As a result, local fixes converged file-by-file while the shared enum drifted.

The stale-body issue had a similar cause: humans read the body summary, but the
workflow logic actually consumes frontmatter. Once fixes changed finding status,
the frontmatter was updated while the narrative body remained historical.

## Solution

Treat shared state vocabularies as a first-class cross-file contract.

For the WB report-writing skill, the fix was to pick one canonical terminology
model and apply it everywhere:

```python
TERMINOLOGY_STATUSES = {"approved", "unresolved"}
```

Then align all dependent artifacts in the same pass:

- update validator constants and validation branches
- update Python fixtures and negative/positive tests
- update shared docs to describe the same states
- update behavioral Pester assertions to require the same wording

The verification loop then becomes meaningful:

1. fix the deterministic enforcement layer
2. fix the documentation and prose guardrails
3. rerun targeted Python tests and behavioral Pester tests
4. run `/cg-review mode:verify` so an independent pass re-reads the whole
   contract surface

For review artifacts, treat frontmatter as the authoritative status ledger:

```yaml
---
findings:
  P1.1: fixed
---
```

If a report body still narrates the original open finding, do not let later
automation infer status from the prose. Use frontmatter for machine decisions.

## Prevention

1. When a review finding changes an allowed enum, status value, or marker
   vocabulary, audit every consumer immediately: docs, validator/schema code,
   fixtures, and behavioral tests.
2. Add at least one invariant-style test that proves the shared vocabulary is
   coherent across layers. File-local branch tests are necessary but not
   sufficient for cross-file contracts.
3. Use verify mode after cross-file fixes. A standard fix-triage pass can miss
   drift when each file looks locally reasonable.
4. In review workflows, treat frontmatter as the durable status source of
   truth; treat report body prose as historical narrative unless it is rewritten
   intentionally.
5. When updating prose-contract tests, split independent expectations into
   separate assertions rather than alternation-heavy regexes, so a stale branch
   cannot mask a live-contract regression.

## Related

- `.cg-docs/solutions/testing-patterns/2026-07-24-positive-validator-fixtures-must-avoid-placeholder-evidence.md`
- `.cg-docs/reviews/2026-07-23-wb-institutional-report-writing-skill-review.md`
- `.cg-docs/reviews/2026-07-23-wb-institutional-report-writing-skill-verify-review.md`
- `.cg-docs/plans/2026-07-23-wb-institutional-report-writing-skill.md`
- `scripts/validate_wb_writing_skill.py`
- `scripts/tests/test_validate_wb_writing_skill.py`
- `tests/prompt-tools.Tests.ps1`
- `.cg-docs/solutions/testing-patterns/2026-04-20-behavioral-pester-tests-for-skill-md-files.md`
- `.cg-docs/solutions/testing-patterns/2026-04-23-verify-mode-suppression-must-be-anchored-to-fixed-finding-scope.md`
- `.cg-docs/solutions/testing-patterns/2026-05-01-regex-alternation-masks-coverage-split-into-independent-assertions.md`