---
date: 2026-04-20
title: "Behavioral Pester tests for SKILL.md files: guard contracts, not just existence"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, skill, SKILL.md, behavioral-test, describe-block, compound-gpid, fix-triage]
root-cause: "New SKILL.md files shipped without Pester coverage of their behavioral contracts (all-open default, no-delegate rule, empty-result response, YAML template). A standard review pass found 4 untested guarantees that only a behavioral describe block would catch."
severity: "P2"
---

# Behavioral Pester Tests for SKILL.md Files

Surfaced during the 2026-04-20 standard review of the `cg-skill-fix-triage-migrate`
skill (P2.1 in `2026-04-20-prompt-prose-compression-review-2.md`).

---

## Problem

When `cg-skill-fix-triage-migrate/SKILL.md` was added to the project, the Pester
test suite gained only a reference test ("skill is loaded for `--migrate` mode by
name") in the `cg-fix-triage.prompt.md` describe block. The skill's own behavioral
contracts — all-open default, no-delegate rule, "No legacy review files found"
response, and the `prepend` instruction — had no test coverage.

Because behavioral contracts live in prose, they can silently regress: an editor
rewriting the Step 3 report template can accidentally remove the all-open guarantee
without breaking any existing test.

```powershell
# ❌ Only tests existence — behavioral contracts unguarded
Describe "cg-fix-triage.prompt.md - per-finding status tracking" {
    It "loads cg-skill-fix-triage-migrate for --migrate mode by name" { ... }
}
```

---

## Root Cause

The `2026-04-08-new-prompt-agent-addition-checklist.md` covers prompts and agents
but does not include a step for **new skill files**. Skills were treated as pure
reference knowledge with no testable surface, but they contain behavioral rules that
the AI must follow — rules that can silently degrade if left untestedge.

---

## Solution

### Pattern: Skill Behavioral Describe Block

Add a dedicated `Describe` block to `tests/prompt-tools.Tests.ps1` for each skill
that has behavioral contracts:

```powershell
Describe "cg-skill-<name> SKILL.md - behavioral rules" {
    $skillFile = Join-Path $repoRoot ".github\skills\cg-skill-<name>\SKILL.md"
    $content = if (Test-Path $skillFile) { Get-Content $skillFile -Raw -Encoding UTF8 } else { "" }

    It "documents all-open default for findings" {
        ($content -match 'Set all findings to.*open|defaulted to.*open|all findings.*open') | Should Be $true
    }

    It "instructs do NOT delegate to subagent for file writes" {
        ($content -match 'do NOT delegate|NOT delegate') | Should Be $true
    }

    It "has 'No legacy review files found' response for empty scan result" {
        ($content -match 'No legacy review files found') | Should Be $true
    }

    It "instructs prepending full frontmatter block when no frontmatter exists" {
        ($content -match 'prepend') | Should Be $true
    }
}
```

**Key conventions:**
- Use `if (Test-Path $skillFile) { ... } else { "" }` so the test reports
  a failing `Should Be $true` (not a file-not-found crash) when the skill
  is missing
- Name the block `"cg-skill-<name> SKILL.md - behavioral rules"` so it is
  findable in the test output separately from prompt describe blocks
- Each `It` should test a *contract* ("does X") not a phrase ("contains the word X")
  — write the regex to match the *intent*, accepting reasonable paraphrase

---

## What Behavioral Contracts to Test

When writing a new SKILL.md, identify these testable contracts and add an `It`
for each:

| Contract type | Example text to match | Example regex |
|---|---|---|
| Default state for managed objects | "all findings default to open" | `'defaulted to.*open\|all findings.*open'` |
| No-delegate write rule | "write directly — do NOT delegate to a subagent" | `'do NOT delegate\|NOT delegate'` |
| Empty-result / not-found response | "'No legacy review files found'" | `'No legacy review files found'` |
| Frontmatter mutation instruction | "prepend full block" | `'prepend'` |
| Cross-file dependency warning | "relies on review files being named …" | `'relies on\|cross-reference'` |
| Error log message format | "log: No companion plan found" | `'No companion plan found'` |

---

## SKILL.md Authoring Conventions for Testability

These conventions emerged from the same review and make behavioral contracts
easy to match:

1. **State defaults explicitly**: write `"Set all findings to \`open\`"` not
   `"the findings map will be populated"`.
2. **Include explicit YAML templates**: instead of describing the frontmatter
   structure in prose, show a copy-pasteable block:
   ```yaml
   ---
   plan: <path or null>
   findings:
     P1.1: open
     P2.1: open
   ---
   ```
3. **Name the no-delegate rule exactly**: the phrase `do NOT delegate` is
   tested in multiple describe blocks — use that exact phrase so the regex
   `'Do NOT delegate|NOT delegate'` always catches it.
4. **Include the empty-result response verbatim**: write the user-facing
   message as a quoted string (`"No legacy review files found"`) so tests can
   match it exactly.
5. **Add cross-file dependency notes inline**: if the skill relies on a naming
   convention from another file, add a comment like `<!-- relies on review files
   named <plan-stem>-review.md per cg-review.prompt.md Step 3.5 -->`.

---

## New-Skill Checklist Extension

Extend the [new-prompt/agent addition checklist](2026-04-08-new-prompt-agent-addition-checklist.md)
with this step for **new skill files**:

| # | File | What to update |
|---|------|----------------|
| 1 | `docs/reference.md` | Add row to the Skills table with skill name and one-line description |
| 2 | `tests/prompt-tools.Tests.ps1` | Add a `Describe "cg-skill-<name> SKILL.md - behavioral rules"` block (see pattern above) |
| 3 | Calling prompt(s) | Add an `It "loads cg-skill-<name> for <mode> by name"` test to the relevant prompt describe block |
| 4 | `SKILL.md` itself | Follow authoring conventions (explicit YAML templates, no-delegate phrase, empty-result quoted message) |

---

## Prevention

- When a code review surfaces "no tests for this skill's behavioral contracts", add
  the `Describe` block immediately rather than deferring to a dedicated refactor.
- Run `. tests\Run-Tests.ps1 -File prompt-tools` after adding any new skill
  describe block before committing.
- If a SKILL.md is updated (e.g., a step is rewritten), re-check the behavioral
  tests to ensure the regex still matches the updated prose.

---

## Related

- [`2026-04-08-new-prompt-agent-addition-checklist.md`](2026-04-08-new-prompt-agent-addition-checklist.md) — parallel checklist for prompts and agents
- [`2026-04-07-pester-test-quality-patterns.md`](2026-04-07-pester-test-quality-patterns.md) — shared helpers, anchored regex, non-empty value checks
- [`2026-04-15-new-validation-branch-requires-dedicated-test.md`](2026-04-15-new-validation-branch-requires-dedicated-test.md) — every new behavioral branch needs a test
