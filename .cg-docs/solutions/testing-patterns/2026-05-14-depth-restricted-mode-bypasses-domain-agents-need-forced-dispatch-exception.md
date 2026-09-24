---
date: 2026-05-14
title: "Depth-restricted review modes silently bypass domain-specific agents — add forced-dispatch exception for open P0s"
category: "testing-patterns"
language: "both"
tags: [prompt-design, cg-review, mode-verify, domain-agents, cr-research-integrity, bypass, depth-restriction, review-convergence, security]
root-cause: "mode:verify forces light depth (only @cg-code-quality + @cg-testing), which completely bypasses all cr-* research agents. A researcher could mark P0 research-integrity findings as 'fixed' then run a verify pass and get a clean report — without the domain agents ever re-running."
severity: "P0"
---

# Depth-Restricted Review Modes Silently Bypass Domain-Specific Agents

## Problem

`/cg-review mode:verify` was designed to terminate the fix-review cycle: it runs
a `light` depth pass (only `@cg-code-quality` and `@cg-testing`), suppresses
expected P2/P3 re-findings, and reports convergence.

The bypass gap: **mode:verify's light-depth restriction completely omits all
`cr-*` research agents**. A researcher who has an open P0 research-integrity
finding can:

1. Edit the review report frontmatter to mark the finding `fixed`
2. Run `/cg-review mode:verify`
3. Receive a clean "no new issues" pass from the two code-quality agents
4. Merge

No `@cr-research-integrity` check ever ran. The P0 silent research error remains
in the codebase but the review system reports convergence.

This was **P0.1** in the 2026-05-14 thorough review of Compound Research Phase 3.

## Root Cause

The depth-restriction rule (`mode:verify → light → only these agents`) was written
as a blanket override with no exception for domain-specific agents. The implicit
assumption was that all P0-class findings are within the engineering code-quality
domain. This assumption breaks when domain-specific agents (`cr-research-integrity`,
`cr-identification-audit`) own their own P0 finding class.

There are two levels of bypass:
1. The `findings:` frontmatter is written by the human — there is no enforcement
   preventing a researcher from marking a P0 as `fixed` before it's actually fixed.
2. The verify-mode dispatch list is hard-coded — even if the frontmatter is honest
   (`fixed: false → still open`), mode:verify never dispatches the agents that
   would verify the fix.

## Solution

Add a **forced-dispatch exception** to the verify-mode agent dispatch rule:

```markdown
**Verify mode — domain agent exception**: If the prior review file contains any
`P0` finding with a `[cr-*]` agent tag that is still marked `open`, always
dispatch `@cr-research-integrity` in addition to the light-depth agents,
regardless of depth. P0 research-integrity violations cannot be waived by a
verify pass — they must be verified by the domain agent directly.
```

The key invariant: **domain P0s must be re-verified by the domain agent that
owns them before convergence is declared**. The exception fires on:
- Finding status = `open` AND
- Finding has a `[cr-*]` tag in the body

## Pattern

**Wherever a mode enforces depth restrictions, audit whether those restrictions
bypass safety-critical domain agents:**

```
For each depth-restricted mode:
  For each domain with its own P0 finding class:
    Does the mode dispatch that domain's agent?
    If not: is there a forced-dispatch exception for open domain P0s?
    If no exception exists → add one
```

Generalizes beyond `cr-*`: any future domain agent (security, compliance,
statistical correctness) that owns P0 findings needs this exemption in every
depth-restricted mode.

## Prevention

When adding a new domain agent that can emit P0 findings:
1. Search `cg-review.prompt.md` for every depth-restricted mode dispatch list
2. Add the agent to each mode's forced-dispatch exception list (or confirm
   it is already included in the mode's base tier)

Test to add to the mode's dispatch block:
```powershell
It "mode:verify still dispatches @<domain-agent> when open P0 [<domain-tag>] findings exist" {
    ($content -match '<domain agent name> exception') | Should -Be $true
    ($content -match '\[<domain-tag>-\*\]') | Should -Be $true
}
```

## Related

- [`2026-04-23-verify-mode-suppression-must-be-anchored-to-fixed-finding-scope.md`](./2026-04-23-verify-mode-suppression-must-be-anchored-to-fixed-finding-scope.md) — companion: suppression scope must be anchored to the explicit `fixed` map, not agent inference
- [`2026-05-06-cross-prompt-user-journey-must-be-validated-end-to-end.md`](./2026-05-06-cross-prompt-user-journey-must-be-validated-end-to-end.md) — related: user journey validation across prompt chains
