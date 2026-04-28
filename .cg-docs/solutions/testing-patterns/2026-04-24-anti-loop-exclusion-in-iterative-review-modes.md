---
date: 2026-04-24
title: "Anti-loop exclusion: output file types must be excluded from input scan in iterative review modes"
category: "testing-patterns"
language: "both"
tags: [prompt-design, cg-review, mode-verify, anti-loop, review-convergence, scan-exclusion, fix-triage]
root-cause: "A verification mode that reads prior review files and writes verify-review files selects its own prior output as input unless the output suffix is explicitly excluded from the input scan"
severity: "P1"
---

# Anti-Loop Exclusion in Iterative Review Modes

## Problem

`/cg-review mode:verify` scans `.cg-docs/reviews/` for the most recent review
file with at least one `fixed` entry to use as suppression context. The mode
also writes its own output to that same directory with the suffix
`-verify-review.md`.

Without an explicit exclusion, a second `mode:verify` invocation on the same
feature would find the first verify-review as the "most recent with fixed
entries" (because `P3.1: fixed` appears in its frontmatter), use it as the
parent, and write `<stem>-verify-review.md` — overwriting itself with no
meaningful suppression context. On a third pass, the pattern repeats. The loop
is silent: no error is raised, but every pass re-reviews fully-fixed code as
though nothing was ever suppressed.

## Root Cause

The input scan (`files ending in -review.md, with at least one fixed entry,
sorted by date`) was specified without regard for the mode's own output type.
In iterative modes where output and input share a directory and similar naming,
the output becomes a valid input on the next run unless the output suffix is
excluded.

This is a specific case of the general **self-referential scan anti-pattern**:
a process that writes to the same namespace it reads from will, without
exclusion, eventually read its own output.

## Solution

Add an explicit exclusion in the input scan rule:

```
Scan: files ending in `-review.md`
Exclude: files ending in `-verify-review.md`
```

Equivalently in regex terms: `.*-review\.md$` minus `.*-verify-review\.md$`.

The fixed rule in `cg-review.prompt.md` Step 1.7.1:

```markdown
Scan `.cg-docs/reviews/` for `.md` files whose name ends in `-review.md`
but NOT `-verify-review.md`, and whose `findings:` frontmatter contains at
least one `fixed` entry.
```

This ensures verify passes always anchor to a canonical `*-review.md`
produced by a standard review, not to a previous verify output.

## Prevention

Whenever designing a mode that writes output to a directory it also scans for
input, apply the **anti-loop exclusion checklist**:

1. What suffix/pattern does this mode write?
2. Does the input scan include files matching that pattern?
3. If yes: add an explicit exclusion line in the scan specification.
4. Write a Pester test asserting the exclusion is present in the prompt:

```powershell
It "excludes -verify-review.md files from prior review scan" {
    ($content -match '(?s)verify-review\.md.*[Ss]kip|[Ss]kip.*verify-review\.md') |
        Should Be $true
}
```

A second useful test guards the filename counter for consecutive verify passes
(prevents silent overwrite):

```powershell
It "increments counter for consecutive verify passes" {
    ($content -match 'verify-review-2|counter|already exists') |
        Should Be $true
}
```

## Related

- [`.cg-docs/solutions/testing-patterns/2026-04-23-verify-mode-suppression-must-be-anchored-to-fixed-finding-scope.md`](2026-04-23-verify-mode-suppression-must-be-anchored-to-fixed-finding-scope.md) — companion pattern: what to suppress and how to anchor suppression to concrete `fixed` entries rather than agent inference
- [`.cg-docs/solutions/bugs/2026-04-15-self-defeating-guardrail-exception-in-llm-prompts.md`](../bugs/2026-04-15-self-defeating-guardrail-exception-in-llm-prompts.md) — related: guardrails that create exceptions LLMs can exploit are also self-defeating
- [`.cg-docs/solutions/testing-patterns/2026-04-13-prompt-interaction-branch-completeness.md`](2026-04-13-prompt-interaction-branch-completeness.md) — related: testing that all prompt branches are covered
