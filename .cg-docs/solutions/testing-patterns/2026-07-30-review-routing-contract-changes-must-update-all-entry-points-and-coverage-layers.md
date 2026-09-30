---
date: 2026-07-30
title: "Review routing contract changes must update all entry points and coverage layers"
category: "testing-patterns"
language: "PowerShell/Markdown"
tags: [review-routing, cross-file-contract, cg-work, cr-review, prompt-tools, research-mode, additive-coverage, contract-drift]
root-cause: "The shared review-routing contract, /cg-work handoff surface, and /cr-review shared-agent dispatch logic evolved independently, so adding research-mode semantics in one place left other entry points and regression checks stale."
severity: "P1"
related: [".cg-docs/solutions/testing-patterns/2026-05-14-dispatch-table-must-cover-all-taxonomy-entries.md", ".cg-docs/solutions/testing-patterns/2026-06-08-token-optimization-benchmark-guardrails.md", ".cg-docs/solutions/testing-patterns/2026-07-24-cross-file-contract-state-must-align-docs-validator-tests.md"]
---

# Review Routing Contract Changes Must Update All Entry Points and Coverage Layers

## Problem

The research-route rollout left three different review entry points out of sync:

- `.github/shared/review-routing.contract.md` defined `research` as a first-class route
- `.github/prompts/cg-work.prompt.md` still rejected `review:research` and documented only `light|standard|data-risk|architecture|full`
- `.github/prompts/cr-review.prompt.md` described its own reduced shared `cg-*` dispatch surface instead of consuming the canonical shared route first

That meant the same review policy behaved differently depending on where it was invoked. A user could not explicitly request `review:research` from `/cg-work`, and mixed `research` plus `security-risk` changes could silently lose CR methodology coverage if routing collapsed to `full` alone.

The defect surfaced during `/cg-review` and `/cg-fix-triage` on the CR-module migration work as fixed findings `P1.1`, `P1.2`, and `P2.1` in `.cg-docs/reviews/2026-07-29-cr-module-migration-to-v1-review-2.md`.

## Root Cause

This was a contract-drift problem across prompt surfaces, not a single-file wording bug.

One canonical routing file described the review modes and risk composition, but two separate prompt entry points mirrored that behavior in prose:

1. `/cg-work` needed to parse explicit `review:*` values and hand off correctly.
2. `/cr-review` needed to inherit the canonical shared `standard` `cg-*` route before layering CR-specific agents.
3. `tests/prompt-tools.Tests.ps1` and `tests/cr-prompts.Tests.ps1` needed to guard the alignment behavior.

Because the contract and its consumers were edited on different passes, `research` was added as a route without auditing every downstream entry point and every regression layer that enforced the same behavior.

The second-order failure was precedence semantics: a naive coverage ordering of `full > research` looked reasonable, but `full` and `research` do not subsume the same agent sets. In mixed research plus security-risk diffs, choosing only `full` silently removed CR methodology reviewers.

## Solution

Treat review routing as a cross-file contract with additive semantics where agent coverage differs.

The fix had three parts:

1. Extend `/cg-work` to accept `review:research` everywhere explicit review routes are enumerated.
2. Update the shared routing contract so `research` plus `security-risk` uses composite coverage: `full` plus the CR agent set from `research`.
3. Refactor `/cr-review` prose so it consumes the canonical shared `standard` `cg-*` route first, then layers task-specific CR agents instead of maintaining a divergent reduced shared set.

The corresponding regression coverage must be co-authored in the same fix session:

```powershell
It "accepts explicit routed review values" {
    foreach ($mode in @("review:light", "review:standard", "review:data-risk", "review:architecture", "review:research", "review:full")) {
        ($content -match [regex]::Escape($mode)) | Should -Be $true
    }
}

It "shared contract documents precedence and additive dedup" {
    ($contract -match '(?s)If both `research` and `security-risk` signals apply.*dispatch `full` plus the CR agent set from `research`') | Should -Be $true
}
```

Validation for this fix used targeted Pester suites under Pester 4.10.1:

- `tests/prompt-tools.Tests.ps1`
- `tests/cr-prompts.Tests.ps1`

Passing those targeted suites proved the explicit route, composite-coverage rule, and shared-agent parity were all guarded.

## Prevention

When changing review routing, mode enums, or agent-composition semantics:

1. Audit the canonical contract and every user-facing entry point that mirrors it: `/cg-review`, `/cg-work`, and any specialized review prompt such as `/cr-review`.
2. Do not assume route precedence implies agent-set supersets. If two modes cover different reviewer families, prefer additive composition over winner-take-all ordering.
3. Add co-authored prompt-contract tests in the same session for every new explicit route token and every new composition rule.
4. Verify both the general prompt-contract suite and the specialized prompt suite that owns the affected entry point.
5. Treat review frontmatter status as authoritative after fix-triage; body prose may remain historical narrative unless intentionally rewritten.

## Related

- `.cg-docs/solutions/testing-patterns/2026-05-14-dispatch-table-must-cover-all-taxonomy-entries.md` - dispatch tables that mirror a canonical taxonomy must remain exhaustive
- `.cg-docs/solutions/testing-patterns/2026-06-08-token-optimization-benchmark-guardrails.md` - review routing changes need prompt-visible regression guardrails, not manual audits
- `.cg-docs/solutions/testing-patterns/2026-07-24-cross-file-contract-state-must-align-docs-validator-tests.md` - shared state contracts must stay aligned across docs, validators, and behavioral tests
- `.cg-docs/reviews/2026-07-29-cr-module-migration-to-v1-review-2.md` - source review that exposed and tracked the routing drift findings