---
date: 2026-05-20
title: "Agent step carve-outs must not contradict the global P0 deferral policy"
category: "testing-patterns"
language: "both"
tags: [agent-design, P0-deferral, compound-research, research-integrity, cr-agents, deferral-policy]
root-cause: "Step 4a said 'do NOT emit P0 here' while the global deferral policy said 'emit directly regardless of dispatch context'. The carve-out made it impossible to surface P0s detected in that step."
severity: "P1"
---

# Agent Step Carve-outs Must Not Contradict the Global P0 Deferral Policy

## Problem

`cr-econometric-reasoning.agent.md` Step 4a contained:

> "If you detect a code-math mismatch, **do NOT emit P0 here**. Cross-reference
> @cr-research-integrity."

The same agent's deferral policy section stated:

> "P0 findings must be emitted **directly**, regardless of which step detects them."

With the carve-out in place, a code-math mismatch found in Step 4a would be deferred to
`@cr-research-integrity` — which the model cannot dispatch. The P0 would never surface.

## Root Cause

The carve-out was written to encourage cross-agent collaboration: `@cr-research-integrity`
is the canonical home for code-math mismatch (Check 6). The intent was good — but agents
cannot dispatch other agents. They can only emit findings. A "defer to @X" instruction
inside a finding step is inert; the P0 disappears silently.

The contradiction was invisible in isolation — the step and the policy section looked
individually reasonable. The bug only manifests at runtime when the step fires and the
carve-out suppresses the finding.

## Solution

Remove the carve-out. Replace with the cross-reference note pattern:

**Before:**
```
If you detect a code-math mismatch, do NOT emit P0 here. Cross-reference @cr-research-integrity.
```

**After:**
```
If you detect a code-math mismatch, emit a P0 finding directly (per P0 deferral policy below)
and add a cross-reference note: "Cross-reference: @cr-research-integrity Check 6 (code-math mismatch)".
```

This preserves the link to the canonical agent without suppressing the finding.

## Prevention

- **Never write "do NOT emit [priority] here"** in an agent step. This creates an
  unconditional suppression at the exact moment that a finding should be reported.
- When a finding legitimately belongs to multiple agents, the pattern is:
  **emit finding + cross-reference note** — not **defer to other agent**.
- After any edit to an agent's step instructions that mentions deferral, scan for
  carve-out language (`do NOT emit`, `skip`, `defer to`, `do not report`) and verify
  each is consistent with the global deferral policy section.
- Agents that contain a global deferral policy should have a Pester test:
  ```powershell
  ($content -match 'P0 deferral policy') | Should Be $true
  ($content -notmatch 'do NOT emit P0') | Should Be $true
  ```

## Related

- `.github/agents/cr-econometric-reasoning.agent.md` — Step 4a carve-out removed (2026-05-20)
- `.github/agents/cr-research-integrity.agent.md` — canonical home for code-math mismatch
- `.cg-docs/solutions/testing-patterns/2026-04-28-prompt-guard-conditions-need-immediate-pester-coverage.md`
