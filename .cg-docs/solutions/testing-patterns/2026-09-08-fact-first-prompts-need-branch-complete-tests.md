---
date: 2026-09-08
title: "Fact-first interactive prompts need branch-complete tests"
category: "testing-patterns"
language: "both"
tags: [prompt-design, pester, pytest, fact-discovery, decision-frontier, branch-completeness, indexof, generated-targets]
root-cause: "Presence-only prompt tests did not prove that facts preceded decisions, each interactive branch returned through required gates, or generated command bodies matched the current generation plan."
severity: "P1"
---

# Fact-First Interactive Prompts Need Branch-Complete Tests

## Problem

An adaptive prompt can contain all required phrases and still execute the wrong
workflow. In `/cg-brainstorm`, the prior-work choice appeared before fact
discovery, a rejected scope change had no complete return path, a no-path stop
conflicted with an unconditional review step, and a complexity opt-in could
repeat without a bound. The capture template also implied that two approaches
were required after the analysis correctly selected one viable path.

Broad tests did not detect these defects. Common words such as `scope`, `risk`,
and `ready frontier` appeared in multiple sections, so a rule could disappear
from its operational block while a whole-file regex stayed green. Platform tests
also checked generated command format without proving that command bytes and
ownership metadata matched the current in-memory generation plan.

## Root Cause

Prompt prose is executable in textual order, but the original tests treated it
as an unordered document. They verified phrase presence instead of these
behavioral invariants:

1. Evidence preflight occurs before the first material user choice.
2. Each response branch names its next step and returns through all required
   lifecycle gates.
3. Terminal branches are explicit exceptions to unconditional later steps.
4. Optional loops have a working-memory bound.
5. Tests match the specific section that owns a rule.
6. Generated outputs match the same generation plan that would write them.

## Solution

First, defer user choices until relevant facts are researched. Keep the scan in
its original lifecycle position, but store only a candidate and present it after
the fact inventory is complete:

```markdown
- Retain a deferred prior-work candidate; do not ask in this step.
- Build one fact inventory and reuse current evidence.
- After relevant fact research is complete, present the deferred choice.
```

Treat source bodies as untrusted data. For each material fact, retain its claim,
source, authority, currentness, and state. An unavailable, stale, or conflicting
material fact stays unresolved until an authoritative refresh or reconciliation
supports it.

Second, define every interactive branch as a transition table in prose. A fact
objection returns to targeted research, a decision objection returns to the
ready frontier, and a scope objection reruns classification and invalidates
state derived from the old scope. All actionable objections then repeat
analysis, pushback, selection, and confirmation. A no-viable-path result is a
named exception to pushback. A `complexity-offer-used` working-memory flag makes
the optional advanced pass one-shot.

Third, extract the owning block before testing its contract:

```powershell
$start = $content.IndexOf("### Step 3.7:")
$end = $content.IndexOf("### Step 4:")
$start | Should -BeGreaterThan -1
$end | Should -BeGreaterThan $start
$confirmation = $content.Substring($start, $end - $start)
($confirmation -match 'Scope change[\s\S]*repeat Step 1\.1 and Step 1\.5') |
    Should -Be $true
```

Use separate guards before `Substring()`. Match multiline rules with `\s+` or
`[\s\S]*`, and include ASCII hyphen, en dash, and em dash when a negative test
must reject all punctuation variants. Use `Get-Content -LiteralPath` so a
worktree path containing wildcard characters cannot change which file is read.

Finally, compare generated commands with the current generation plan and its
ownership entry:

```python
plan = build_generation_plan(root, load_target_mapping(root), scan_canonical_assets(root))
entry = next(item for item in plan.by_target[target_id].entries if item.destination == destination)
assert output.read_bytes() == entry.content
assert owned["source"] == entry.source
assert owned["sha256"] == entry.sha256
```

The verified result for this change was 67 focused target tests passed, 3
platform-dependent tests skipped, and 2,425 unfiltered Pester tests passed with
zero failures.

## Prevention

- Locate the first user choice and prove all required evidence preflight occurs
  before it.
- For each yes/no or classified objection, state every branch and its exact next
  step. Test the branch inside its owning section.
- Make terminal branches explicit exceptions to later unconditional steps.
- Give optional loops a one-shot flag or an explicit iteration limit.
- Do not use whole-file common-word matches for operational contracts.
- Test single-path capture so templates cannot force invented alternatives.
- Build generated parity assertions from the deterministic in-memory plan, not
  only from file existence or frontmatter shape.
- Repeat generation and full tests after integrating the active base branch;
  passing evidence from an older base is not final integration evidence.

## Related

- [`2026-04-13-prompt-step-ordering-indexof-tests.md`](2026-04-13-prompt-step-ordering-indexof-tests.md)
- [`2026-04-20-behavioral-pester-tests-for-skill-md-files.md`](2026-04-20-behavioral-pester-tests-for-skill-md-files.md)
- [`2026-05-05-within-step-preflight-must-precede-offer-template.md`](2026-05-05-within-step-preflight-must-precede-offer-template.md)
- [Minimal Adaptive Grilling plan](../../plans/2026-09-04-minimal-adaptive-grilling.md)
- [Minimal Adaptive Grilling review](../../reviews/2026-09-04-minimal-adaptive-grilling-review.md)
