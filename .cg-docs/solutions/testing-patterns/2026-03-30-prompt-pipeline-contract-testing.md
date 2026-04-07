---
date: 2026-03-30
title: "Test the interface contract between chained prompts (review -> fix-triage pipeline)"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, prompt-pipeline, compound-ids, cg-review, cg-fix-triage, guardrails, workflow]
root-cause: "A follow-up prompt (/cg-fix-triage) silently breaks if the upstream prompt (/cg-review) changes its output format — compound finding IDs, file location, or /cg-fix-triage mention can all drift without detection"
severity: "P2"
---

# Test the Interface Contract Between Chained Prompts (Review → Fix-Triage Pipeline)

## Problem

When two prompts are designed to work in sequence — the OUTPUT of one prompt
is the INPUT of a follow-up prompt — the interface between them is fragile. If
the upstream prompt silently changes its output format (ID scheme, file path,
or cross-reference text), the downstream prompt breaks with no error: it simply
finds no matching findings, reads the wrong file, or never gets invoked by the
user because the upstream prompt forgot to mention it.

Concretely, the review → fix-triage pipeline has three fragile joints:

1. **File location**: `cg-review.prompt.md` must write reports to
   `.cg-docs/reviews/`. If the path changes, `cg-fix-triage` looks in the
   wrong place and reports "no review files found."

2. **Finding ID format**: `cg-fix-triage` expects compound IDs like `[P1.1]`,
   `[P2.3]`. If `cg-review` switches to flat IDs (`[P1]`, `[#1]`, `[critical-1]`),
   the argument parser in `cg-fix-triage` cannot match individual findings.

3. **Cross-reference text**: If `cg-review` never mentions `/cg-fix-triage` in
   its Next Steps summary, a new user on the team has no idea the follow-up
   prompt exists and manually applies fixes instead.

None of these failures are runtime errors — they are workflow failures that
only surface during actual use, possibly weeks after the upstream prompt was
changed.

## Root Cause

Prompt files are not typed APIs — they are natural-language documents. There is
no compiler that catches contract drift between them. Without explicit tests,
a refactor to one prompt can silently invalidate the downstream prompt's
assumptions.

## Solution

### 1. Define the pipeline contract in Pester

For every prompt that produces output consumed by another prompt, add a
`Describe` block in `tests/prompt-tools.Tests.ps1` that asserts the specific
contract points:

```powershell
# Upstream prompt must write to the agreed-upon location
Describe "cg-review.prompt.md - review file output step" {
    $content = Get-Content (Join-Path $repoRoot ".github\prompts\cg-review.prompt.md") `
                           -Raw -Encoding UTF8

    # Contract point 1: agreed file location
    It "writes the review report to .cg-docs/reviews/ directory in Step 3.5" {
        ($content -match '\.cg-docs[/\\]reviews') | Should Be $true
    }

    # Contract point 2: upstream uses the ID format that downstream parses
    It "uses compound finding IDs like [P1.1], [P2.1], [P3.1] in the output template" {
        ($content -match '\*\*\[P[123]\.\d+\]\*\*') | Should Be $true
    }

    # Contract point 3: upstream refers users to the downstream prompt
    It "includes /cg-fix-triage usage instruction with a compound ID example" {
        ($content -match '/cg-fix-triage.*P\d\.\d') | Should Be $true
    }

    It "mentions /cg-fix-triage so users know how to apply findings" {
        ($content -match '/cg-fix-triage') | Should Be $true
    }
}

# Downstream prompt must reference the agreed-upon location 
Describe "cg-fix-triage.prompt.md - review reports location" {
    $content = Get-Content (Join-Path $repoRoot ".github\prompts\cg-fix-triage.prompt.md") `
                           -Raw -Encoding UTF8

    It "references .cg-docs/reviews/ directory to load saved review reports" {
        ($content -match '\.cg-docs[/\\]reviews') | Should Be $true
    }
}
```

### 2. Use compound finding IDs (P1.1, P2.1) for selective triage

Flat priority labels (`P1`, `P2`, `P3`) do not support mixed-scope targets.
Compound IDs (`P1.1`, `P1.2`, `P2.1`) allow callers to specify:

- **Whole priority**: `/cg-fix-triage P1` — fix all P1 findings
- **Individual finding**: `/cg-fix-triage P1.2 P2.1` — fix exactly those two
- **Mixed scope**: `/cg-fix-triage P1 P2.3` — all P1 plus one specific P2

Output template in `cg-review.prompt.md`:

```markdown
### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [agent-name] `file/path.ext` — short description
  **Why**: ...
  **Fix**: ...

- **[P1.2]** [agent-name] `file/path.ext` — short description
  ...
```

The `**[P1.1]**` bold wrapper makes the ID visually distinct, regex-parseable,
and consistent across all severity levels.

### 3. Guard the downstream prompt's frontmatter

The fix-triage prompt must also have valid frontmatter so VS Code loads it:

```powershell
Describe "cg-fix-triage.prompt.md - frontmatter" {
    $frontmatter = Get-Frontmatter -FilePath (
        Join-Path $repoRoot ".github\prompts\cg-fix-triage.prompt.md"
    )

    It "has a description in frontmatter" {
        $frontmatter | Should Match 'description:'
    }

    It "has a model in frontmatter" {
        $frontmatter | Should Match 'model:'
    }
}
```

## Prevention

- **Every new prompt that reads another prompt's output** needs contract tests
  for the specific structural features it depends on (file path, ID format,
  key phrases).
- **Every new prompt that writes output for another prompt** needs the
  downstream prompt mentioned in its Next Steps section.
- When changing an upstream prompt's output format, run
  `Invoke-Pester tests/prompt-tools.Tests.ps1` first — the contract tests
  will tell you which downstream prompts will break.

## Related

- [2026-03-30-test-prompt-frontmatter-tools-list.md](./2026-03-30-test-prompt-frontmatter-tools-list.md) — guarding the `tools:` permission list in prompt frontmatter (adjacent concern: silent failures at the _permission_ layer rather than the _contract_ layer)
- [2026-03-30-do-not-delegate-file-write-guardrail.md](./2026-03-30-do-not-delegate-file-write-guardrail.md) — guarding against the AI agent delegating file-writing steps to a subagent, causing silent data loss (layer below: _execution_ rather than _permission_ or _contract_)
- [2026-03-02-prompt-file-permission-guardrails.md](./2026-03-02-prompt-file-permission-guardrails.md) — broader guardrails for prompt file structure
- [2026-04-07-pester-test-quality-patterns.md](./2026-04-07-pester-test-quality-patterns.md) — four patterns for higher-quality Pester tests: shared helpers, anchored regex, non-empty value checks, named-criteria guards
