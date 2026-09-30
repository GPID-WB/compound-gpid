---
date: 2026-05-22
title: "Skill/agent forbidden-pattern tables must be kept in sync"
category: "testing-patterns"
language: "both"
tags: [agents, skills, skill-agent-contract, forbidden-patterns, check-list, path-portability, synchronization, P1-mismatch]
root-cause: "Agent check rules and the corresponding skill's Forbidden Patterns table were updated independently — one without the other"
severity: "P1"
---

# Skill/Agent Forbidden-Pattern Tables Must Be Kept in Sync

## Problem

`cr-replication-package.agent.md` Check 6 (Path Portability) was updated to flag
parent-traversal paths (`../`) as P1 violations. The corresponding
`cr-skill-replication-standards/SKILL.md` Section 6 Forbidden Patterns table was
not updated in the same commit.

Result: the skill taught researchers that `../` paths were acceptable; the agent
flagged them as P1. A researcher reading the skill file and correcting their code
would have no reason to remove `../` paths — then the agent would flag them anyway.

The mismatch survived the **thorough** review pass (which caught 12 other findings)
and was only caught in the subsequent **standard** review.

## Root Cause

Agent checks and their corresponding skill sections are maintained in two separate
files. There is no enforced link between them — updating one doesn't signal the
other needs updating. When `../` was added to the agent's forbidden list during a
review-fix pass, the skill documentation was not on the active file set, so the
maintainer didn't think to update it.

## Solution

Keep agent check rules and skill documentation atomically synchronized:

**In `cr-skill-replication-standards/SKILL.md` Section 6**, add the missing row
to the Forbidden Patterns table:

```markdown
| Parent-traversal path | `../data/raw/` or `..\data\raw\` | Non-portable when subscripts are sourced from project root |
```

**General pattern**: whenever an agent check adds a new forbidden pattern, the
corresponding skill's "Forbidden Patterns" (or equivalent) section must receive a
matching row in the same commit.

## Prevention

### Test-first discipline for skill/agent contract changes

Whenever a new forbidden pattern is added to an agent check, write **two** tests in
the same commit:

1. **Agent test** — verifies the agent's check text mentions the new pattern:
   ```powershell
   It "Check 6 forbids parent-traversal paths (../)" {
       ($content -match '\.\./') | Should -Be $true
   }
   ```

2. **Skill test** — verifies the skill's Forbidden Patterns table also includes it:
   ```powershell
   It "SKILL.md Section 6 Forbidden Patterns table includes parent-traversal" {
       ($skillContent -match '\.\./') | Should -Be $true
   }
   ```

If the skill test fails, the PR cannot merge — the mismatch is caught at commit time,
not in a review cycle later.

### Skill/agent invariant

Every row in an agent's "forbidden" or "P0/P1 violations" list that comes from a
skill's reference material **must** appear in the skill's authoritative table. The
agent's check is the *enforcement*; the skill's table is the *documentation*. Both
must agree.

### PR checklist item

Add to any PR that modifies agent check rules:
> - [ ] Updated the corresponding skill's Forbidden Patterns / Required Patterns
>       tables to match the new check rules

## Related

- Agent design convention in `compound-gpid.context.md` — "Path validation is
  mandatory for agent file reads"
- `.cg-docs/solutions/testing-patterns/2026-05-01-fix-triage-prompt-changes-need-co-authored-tests.md`
  — co-authored tests for every fix during triage
- `.cg-docs/reviews/2026-05-22-compound-research-phase7-reproducibility-replication-review-2.md`
  — P1.2 finding where this pattern was discovered
