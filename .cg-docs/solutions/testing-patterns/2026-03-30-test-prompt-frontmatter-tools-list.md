---
date: 2026-03-30
title: "Test prompt frontmatter tools: list to guard against silent write failures"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, prompt-frontmatter, tools, copilot, write, agent-mode, guardrails]
root-cause: "Prompt YAML frontmatter tools: list omitted 'write', silently preventing all file operations during the prompt session without any error"
severity: "P2"
---

# Test Prompt Frontmatter `tools:` List to Guard Against Silent Write Failures

## Problem

VS Code Copilot prompt files support a `tools:` key in their YAML frontmatter
that restricts which tools the agent may use when executing that prompt. If a
prompt's process steps involve writing files (creating reports, applying fixes,
saving output), but `'write'` is absent from the `tools:` list, those steps
silently fail — the agent cannot write, produces no error, and the user is left
with no artifacts.

This is especially insidious because:
- The failure is **silent**: no exception, no error message from the runtime
- The symptom (agent "can't write files") appears only at runtime, not at
  development time when the prompt is being written
- The `tools:` list and the process body are in different parts of the same file
  — it is easy to add a new step without updating the tools declaration

Example: `cg-review.prompt.md` declared:

```yaml
tools: ['agent', 'read', 'search']
```

Step 4 (Triage) told the agent to apply fixes to source files, and a new
Step 3.5 was added to write the review report to `.cg-docs/reviews/`. Neither
could execute because `'write'` was missing.

## Root Cause

The `tools:` key in prompt YAML frontmatter acts as an allowlist. Omitting a
tool is sufficient to block it — there is no warning that the block occurred.

The mental model mismatch: prompt authors think of `tools:` as "optional
enhancement" rather than "required permission declaration". When adding new
steps that write files, updating the `tools:` list is easy to forget.

## Solution

### 1. Use Pester to assert `tools:` contains the right entries

Add tests to `tests/prompt-tools.Tests.ps1` for every prompt that performs
file operations. Parse the YAML frontmatter and assert each required tool:

```powershell
# Helper: extract raw frontmatter string from a .prompt.md file
function Get-Frontmatter {
    param([string]$FilePath)
    $raw = Get-Content $FilePath -Raw -Encoding UTF8
    if ($raw -match '(?s)^---\s*\r?\n(.+?)\r?\n---') { return $Matches[1] }
    return ''
}

# Helper: extract the tools list as an array of strings
function Get-ToolsList {
    param([string]$Frontmatter)
    $line = ($Frontmatter -split '\r?\n' | Where-Object { $_ -match '^\s*tools:' })
    if (-not $line) { return @() }
    $tokens = [regex]::Matches($line, "['""](\w+)['""]") |
              ForEach-Object { $_.Groups[1].Value }
    return $tokens
}

Describe "cg-review.prompt.md - tools frontmatter" {
    $file = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $tools = Get-ToolsList -Frontmatter (Get-Frontmatter -FilePath $file)

    It "includes 'write' so fixes and report output can be saved" {
        $tools | Should Contain 'write'
    }
}
```

### 2. Also assert that process body references match declared tools

For any capability the prompt body describes (writing a file, calling agents,
searching the codebase), add a corresponding content assertion:

```powershell
Describe "cg-review.prompt.md - review file output step" {
    $content = Get-Content $file -Raw -Encoding UTF8

    It "contains a step that writes the review report to .cg-docs/reviews/" {
        ($content -match '\.cg-docs[/\\]reviews') | Should Be $true
    }
}
```

This catches the inverse failure: the `tools:` list declares `'write'` but the
prompt body has no step that actually uses it (dead permission), or the step
was removed but the `tools:` list was not cleaned up.

### 3. Quick reference: which tools map to which operations

| Tool      | Operations |
|-----------|------------|
| `read`    | Reading file contents, listing directories |
| `write`   | Creating files, modifying files, creating directories |
| `search`  | Searching the codebase (grep, semantic search, file search) |
| `agent`   | Invoking sub-agents (e.g., `@cg-code-quality`) |
| `run`     | Running terminal commands |

## Prevention

**Rule**: Before finalizing any prompt, read through every step and verify that
every file-system or tool operation is covered by a declared `tools:` entry.

**Checklist when adding a new step to a prompt:**
- [ ] Does this step read files? → `'read'` must be declared
- [ ] Does this step write or create files? → `'write'` must be declared
- [ ] Does this step search the codebase? → `'search'` must be declared
- [ ] Does this step call a sub-agent? → `'agent'` must be declared
- [ ] Does this step run terminal commands? → `'run'` must be declared
- [ ] Is there a Pester test in `tests/prompt-tools.Tests.ps1` for this requirement?

**Rule**: Add a test in `tests/prompt-tools.Tests.ps1` for every prompt that
declares `tools:`. Treat the frontmatter as a contract — test it like an API.

## Related

- [2026-03-30 cg-review missing write tool (bug)](../bugs/2026-03-30-cg-review-missing-write-tool-disables-file-creation.md)
  — The specific bug this pattern was extracted from.
- [2026-03-02 Prompt file permission guardrails](./2026-03-02-prompt-file-permission-guardrails.md)
  — Complementary pattern: how to scope-limit writes using `## File Permissions`
  prose in the prompt body (for prompts that use default agent mode rather than
  an explicit `tools:` list).
- [2026-03-30 Prompt pipeline contract testing](./2026-03-30-prompt-pipeline-contract-testing.md)
  — Adjacent concern: testing the structural contract between chained prompts
  (output format, file location, cross-reference text) rather than just the
  permission layer.
