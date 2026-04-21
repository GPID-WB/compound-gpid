---
date: 2026-04-13
title: "Prompt step-ordering tests using IndexOf position comparisons"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, prompt-design, indexof, step-ordering, regression, cg-work, position-assertion]
root-cause: "Prompt step ordering cannot be verified by content presence alone — a step can exist but be in the wrong position (e.g., after a user-wait pause), causing silent workflow failures"
severity: "P2"
---

# Prompt Step-Ordering Tests Using IndexOf Position Comparisons

## Problem

Content-presence tests (`$content -match 'status done'`) verify that a phrase
exists in a prompt file but say nothing about **where** it appears. In prompt
workflows, position matters: a step that exists but appears after a
"Wait for the user" pause is dead code.

Example regression: `cg-work.prompt.md` had its roadmap-update dispatch in
Step 5 (after the summary wait). Content tests passed — the phrase was present.
The step never ran because it was unreachable.

## Root Cause

Prompt files are linear instruction sets. The LLM follows them top-to-bottom
and stops at session boundaries (user-wait pauses). A step at the wrong
position is functionally absent even if its text is present.

## Solution

Use `String.IndexOf()` character-offset comparisons to assert relative ordering
of key phrases:

```powershell
Describe "cg-work.prompt.md - roadmap done update before summary wait" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "'to status done.' dispatch phrase is present" {
        $content.IndexOf("to status done.") | Should BeGreaterThan -1
    }

    It "'Wait for the user's response before proceeding' phrase is present" {
        $content.IndexOf("Wait for the user's response before proceeding") | Should BeGreaterThan -1
    }

    It "dispatch appears BEFORE the user-wait pause" {
        $waitPos = $content.IndexOf("Wait for the user's response before proceeding")
        $donePos = $content.IndexOf("to status done.")
        $donePos | Should BeLessThan $waitPos
    }

    It "Step 3.7 appears between Step 3.5 and Step 4" {
        $step35Pos = $content.IndexOf("### Step 3.5:")
        $step37Pos = $content.IndexOf("### Step 3.7:")
        $step4Pos  = $content.IndexOf("### Step 4:")
        $step35Pos | Should BeGreaterThan -1
        $step37Pos | Should BeGreaterThan -1
        $step4Pos  | Should BeGreaterThan -1
        $step37Pos | Should BeGreaterThan $step35Pos
        $step37Pos | Should BeLessThan $step4Pos
    }
}
```

### Key design rules for IndexOf-based ordering tests

**1. Use the most specific unique phrase as the search anchor.**

Generic phrases produce false-matches:
```powershell
# ❌ FRAGILE — also matches "Wait for the user's choice" in Step 2 error handler
$waitPos = $content.IndexOf("Wait for the user")

# ✅ RELIABLE — unique phrase that only appears at the session-ending wait
$waitPos = $content.IndexOf("Wait for the user's response before proceeding")
```

**2. Use the full unique dispatch sentence, not a two-word fragment.**

```powershell
# ❌ FRAGILE — also matches any prose guard like "skip if already status done"
$donePos = $content.IndexOf("status done")

# ✅ RELIABLE — specific to the @cg-roadmap dispatch instruction
$donePos = $content.IndexOf("to status done.")
```

**3. Split presence and ordering into separate It blocks.**

```powershell
# ❌ OPAQUE — failure says "-1 is not less than 206", not "phrase not found"
It "dispatch before wait" {
    $donePos = $content.IndexOf("to status done.")
    $waitPos = $content.IndexOf("Wait for the user's response before proceeding")
    $donePos | Should BeLessThan $waitPos   # fails if either phrase is missing
}

# ✅ CLEAR — distinct failure messages for distinct failure modes
It "'to status done.' is present" {
    $content.IndexOf("to status done.") | Should BeGreaterThan -1
}
It "'Wait for...' is present" {
    $content.IndexOf("Wait for the user's response before proceeding") | Should BeGreaterThan -1
}
It "dispatch is before wait" {
    $content.IndexOf("to status done.") | Should BeLessThan `
        $content.IndexOf("Wait for the user's response before proceeding")
}
```

**4. Add a step-number structural test alongside the lexical test.**

Lexical ordering (A before B) does not guarantee structural correctness (A is
in step X, B is in step Y). Add a step-heading position test:

```powershell
It "Step 3.7 sits between Step 3.5 and Step 4" {
    $s35 = $content.IndexOf("### Step 3.5:")
    $s37 = $content.IndexOf("### Step 3.7:")
    $s4  = $content.IndexOf("### Step 4:")
    $s37 | Should BeGreaterThan $s35
    $s37 | Should BeLessThan $s4
}
```

## Prevention

Add an `IndexOf`-ordering `It` block whenever:
- A prompt step must execute before a user-wait pause
- Two prompt steps must appear in a specific order
- A dispatch or file-write instruction must appear in a particular step by heading

Template to copy:
```powershell
# ---------------------------------------------------------------------------
# P?.? — <description of invariant being tested>
# ---------------------------------------------------------------------------
Describe "<prompt-file> - <invariant name>" {
    $promptFile = Join-Path $repoRoot ".github\prompts\<prompt-file>.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "'<phrase-A>' is present in the prompt" {
        $content.IndexOf("<phrase-A>") | Should BeGreaterThan -1
    }

    It "'<phrase-B>' is present in the prompt" {
        $content.IndexOf("<phrase-B>") | Should BeGreaterThan -1
    }

    It "<phrase-A> appears before <phrase-B>" {
        $posA = $content.IndexOf("<phrase-A>")
        $posB = $content.IndexOf("<phrase-B>")
        $posA | Should BeLessThan $posB
    }
}
```

## Related

- `.cg-docs/solutions/testing-patterns/2026-04-13-dead-step-after-wait-prompt-session-terminator.md` — the anti-pattern these tests guard against
- `.cg-docs/solutions/testing-patterns/2026-03-30-prompt-pipeline-contract-testing.md` — complementary: testing interface contracts between chained prompts
- `.cg-docs/solutions/testing-patterns/2026-04-21-prompt-step-forward-dependency-deferred-marker.md` — when a step appears before its dependency step (forward dependency); same IndexOf guard pattern applies
- `tests/prompt-tools.Tests.ps1` — canonical location for all prompt contract and ordering tests

## Addendum: Guard `IndexOf` values before `Substring` (2026-04-21)

When using `IndexOf` to extract a text block via `Substring`, guard both
index values before calling `Substring`. Without guards, a missing section
header throws `ArgumentOutOfRangeException`, obscuring which assertion failed:

```powershell
# ❌ FRAGILE — unhandled exception if either header is missing
$step35Block = $content.Substring($step35Start, $step37Start - $step35Start)

# ✅ CLEAR — two guard assertions produce a specific failure message
$step35Start | Should BeGreaterThan -1
$step37Start | Should BeGreaterThan $step35Start
$step35Block = $content.Substring($step35Start, $step37Start - $step35Start)
```
