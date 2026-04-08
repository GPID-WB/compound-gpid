---
date: 2026-04-08
title: "Cross-cutting enumeration propagation: quality gate inversion and the full-audit pattern"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, prompt-pipeline, severity-tier, P0, enumeration, cross-cutting, quality-gate, audit, regression-tests]
root-cause: "Adding a new value to a shared enum (P0 severity tier) to 8 agent output templates without auditing all downstream consumers — the quality gate that validates agent output was checking for P1/P2/P3 entries only, so a P0-only response would be misclassified as 'unusable output'"
severity: "P1"
---

# Cross-Cutting Enumeration Propagation: Quality Gate Inversion and the Full-Audit Pattern

Surfaced during Phase 1 of the CE-improvements integration (2026-04-08).
Applies to any change that adds a new value to an enumeration used across
multiple pipeline components.

---

## Problem

After adding a P0 severity tier to all 8 review agent output templates
(`**[P0|P1|P2|P3]**`), the pipeline silently contained a **quality gate
inversion**: the Step 2.5 subagent output quality check in `cg-review.prompt.md`
validated output by checking for `**[P1.`, `**[P2.`, or `**[P3.` entries.

An agent returning *only* P0 findings (e.g., `cg-version-control` finding
committed credentials) would fail the quality check — the worst-possible
inversion. The pipeline would log the most critical finding of all as
*unusable output*.

Additional gaps discovered by the follow-up light review:

| Component | Gap |
|-----------|-----|
| `cg-fix-triage.prompt.md` — Step 2 | Priority-level example showed `(e.g., P1, P2, P3)` — P0 undiscoverable |
| `cg-fix-triage.prompt.md` — Step 3 | Apply order: `P1 first, then P2, then P3` — P0 had no guaranteed first-fix semantics |
| `cg-compound.prompt.md` — severity field | Template showed `"<P1\|P2\|P3>"` — no valid option for blocking findings |
| `cg-review.prompt.md` — Step 3.5 | YAML frontmatter example omitted `P0.1: open` |
| `compound-gpid.md` — Constraints | Still described the 3-tier system |
| `copilot-instructions.md` — Priority System | P0 wording diverged from agent files ("affecting published outputs" qualifier) |
| `cg-skill-compound-docs/solution-schema.md` | `severity: "P1"  # P1 \| P2 \| P3` |
| `cg-skill-compound-docs/capture-solution.md` | "Set severity based on impact (P1/P2/P3)" |
| `docs/reference.md` | No standalone Priority Levels table |
| `solution-schema.md` — category field | `bugs` missing from required fields table |

9 gaps across 8 files — all introduced by a single cross-cutting change.

---

## Root Cause

**Enumeration values are implicit contracts spread across every file that
references them.** There is no single source of truth enforced at parse time.
When a new value is added to the "live" producers (agent output templates),
every downstream consumer — quality gates, fix-triage ordering, templates,
docs, skill references, schema docs — must be audited and updated manually.

The most dangerous gap is the **quality gate inversion**: the component whose
job is to *validate* pipeline output was not updated to accept the new value,
so it would reject the very output type it should have flagged as highest
priority.

---

## Solution

### 1. Core change first, audit second

Commit the change to producers first (agents, output templates). Do NOT try
to find all consumers speculatively — you will miss some.

```
feat(review): add P0 blocking severity tier to review pipeline
```

### 2. Immediately run `/cg-review light`

After the core commit, run a light review before any further work. The
review agents will scan all changed files and surface every consumer that
was not updated:

```
/cg-review light
```

The light review (cg-code-quality + cg-testing) caught all 9 gaps in one pass.

### 3. Fix all gaps via fix-triage

Save the review report and apply all findings:

```
/cg-fix-triage
```

### 4. Add regression tests for each critical behaviour

For each gap that was fixed, add a Pester `It` block that guards the
corrected behaviour. This prevents silent reversion:

```powershell
# Guard: quality gate must accept P0 findings
It "Presence criterion includes P0 entry pattern" {
    ($content -match [regex]::Escape('**[P0.')) | Should Be $true
}

# Guard: apply order must list P0 first
It "Step 3 apply order lists P0 first before P1" {
    ($content -match 'P0 first') | Should Be $true
}

# Guard: severity template must include P0 option
It "severity field template includes P0 option" {
    ($content -match '<P0\|P1\|P2\|P3>') | Should Be $true
}

# Guard: reference docs must have the priority table
It "contains Priority Levels table with P0 BLOCKING entry" {
    ($content -match 'P0.*BLOCKING') | Should Be $true
}
```

Final test count after all guards: 308/308 ✅

---

## Prevention

### Anti-pattern: quality gate inversion
When a pipeline stage validates its inputs (or outputs) by checking for
specific enum values, that gate **must** be updated in the same commit as
the enum change. The gate is the most critical consumer because a missed
update inverts its purpose — it rejects what it should accept.

**Checklist when adding a new enumeration value to a pipeline:**

- [ ] All producer templates updated (agent output format, schema fields)
- [ ] All quality gates updated (pattern-matching validators, presence checks)
- [ ] All ordering/priority lists updated (fix ordering, triage priority)
- [ ] All documentation templates updated (YAML examples, format snippets)
- [ ] All reference docs updated (tables, guides, skill references)
- [ ] All project-level definitions updated (charter, instructions, config)
- [ ] Regression tests added for each updated component

### Workflow pattern: commit + light review + fix-triage
Rather than trying to find all consumers speculatively before committing,
use the review pipeline itself as the audit tool:

1. `feat(scope): core change` — add the new value to producers
2. `/cg-review light` — let agents find all missing consumers
3. `/cg-fix-triage` — apply all findings systematically
4. Add regression tests for guarded behaviours
5. `fix(scope): propagate new value to all consumers + add regression tests`

This sequence is more reliable than manual enumeration of consumers because
it leverages agents that read the actual file contents.

---

## Related

- [Prompt pipeline contract testing](2026-03-30-prompt-pipeline-contract-testing.md) — interface contracts between chained prompts (cg-review → cg-fix-triage)
- [Four Pester test quality patterns](2026-04-07-pester-test-quality-patterns.md) — regression test design for prompt validation
- [Do-not-delegate file write guardrail](2026-03-30-do-not-delegate-file-write-guardrail.md) — related pipeline trust boundary pattern
