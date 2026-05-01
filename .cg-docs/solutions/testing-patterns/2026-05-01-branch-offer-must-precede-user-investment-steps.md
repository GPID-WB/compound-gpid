---
date: 2026-05-01
title: "Branch offer must precede user-investment steps in interactive prompts"
category: "testing-patterns"
language: "PowerShell"
tags: [cg-brainstorm, branch-offer, step-ordering, indexof, prompt-design, ux, user-investment]
root-cause: "Git branch selection was deferred to after the brainstorm was saved (Step 4.5), by which point the user had already invested 3-6 questions worth of work on the wrong branch; the question was also buried in the multi-option handoff turn"
severity: "P3"
---

# Branch Offer Must Precede User-Investment Steps in Interactive Prompts

## Problem

`/cg-brainstorm` asked "would you like to create a new branch?" at **Step 4.5**
— after the brainstorm document was saved. By that point the user had already:

1. Answered 3–6 clarifying questions  
2. Chosen an approach from the proposed options  
3. Responded to the devil's advocate pushback  

All of this happened on whatever branch they were on when they invoked the
prompt (often `main`). The question was also easy to miss because it was
bundled inside the same conversational turn as the broader handoff menu.

## Root Cause

The step was placed late under the rationale "we need a brainstorm title to
derive a good branch name from." This is correct but incomplete — a
**slightly imprecise branch name** is a far smaller cost than **all work
done on the wrong branch**.

Additionally, conflating the branch question with the multi-option handoff
menu reduces its visibility. The model skips or buries it because it is
competing with 4+ other options in the same output.

## Solution

### Prompt change

Move the branch offer to **Step 1.7** — immediately after scope assessment
(Step 1.5) and before any clarifying questions (Step 2). Derive the branch
name from the user's *initial description* rather than the saved brainstorm
title.

```markdown
### Step 1.7: Branch Offer

Before asking any clarifying questions, offer to create a new git branch for
this work:

> "Before we start, would you like to work on a new branch?
> Suggested name: `feat/<short-description-from-your-request>`
>
> 1. **Yes** — I'll create the branch now
> 2. **No** — Stay on the current branch"
```

The branch question is now **isolated as its own step** so the model must ask
it as a standalone question — it cannot be suppressed by competing options.

### Test for ordering

```powershell
Describe "cg-brainstorm.prompt.md - Branch Offer appears before Step 2" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "has a Branch Offer step between Step 1.5 and Step 2 (Step 1.7)" {
        $branchOfferIdx = $content.IndexOf('### Step 1.7:')
        $branchOfferIdx | Should BeGreaterThan -1
    }

    It "Branch Offer (Step 1.7) appears before Step 2 Clarifying Questions" {
        $branchOfferIdx = $content.IndexOf('### Step 1.7:')
        $step2Idx       = $content.IndexOf('### Step 2:')
        $branchOfferIdx | Should BeGreaterThan -1
        $step2Idx       | Should BeGreaterThan $branchOfferIdx
    }
}
```

## Prevention

### Rule: Branch selection is workspace configuration, not a side-effect

The general rule "deferred side-effects come after the primary deliverable"
applies to *augmentation actions* (open a PR, add to the roadmap, update the
charter). It does **not** apply to **workspace-configuration questions** —
questions whose answer determines the environment in which all subsequent work
will be performed.

| Question type | Example | When to ask |
|---|---|---|
| Workspace configuration | "Which branch should this work go on?" | **Before any work begins** |
| Side-effect offer | "Should I open a PR?" / "Add to roadmap?" | After the deliverable is created |

Branch selection is workspace configuration. Ask it first.

### Rule: User-action steps must be isolated, never bundled

A branch question buried inside a multi-option handoff menu competes with 4+
other options and gets skipped or missed by the model. Give it its own named
step so the model is forced to ask it as a standalone question.

```markdown
# ❌ FRAGILE — branch offer competes with 4 other options
> What would you like to do next?
> 1. /cg-plan
> 2. Update charter
> 3. /cg-brainstorm again
> 4. /cg-work
> 5. Create a branch?

# ✅ ISOLATED — dedicated step, asked before any other questions
### Step 1.7: Branch Offer
Before asking any clarifying questions, offer to create a new git branch...
```

### Rule: Use IndexOf ordering tests for every user-action step

Any step that asks the user a question or performs a git/file operation must
have an `IndexOf` ordering test asserting it appears at the expected position.
Content-presence tests (`-match '### Step 1.7'`) confirm the step exists but
say nothing about whether it will execute.

## Related

- `.cg-docs/solutions/testing-patterns/2026-04-13-prompt-step-ordering-indexof-tests.md`
  — general `IndexOf` technique for ordering assertions
- `.cg-docs/solutions/bugs/2026-04-13-cg-work-roadmap-status-never-updated-to-done.md`
  — original dead-step-after-wait bug; same class (step in wrong position)
- `.cg-docs/solutions/bugs/2026-05-01-cg-brainstorm-branch-offer-asked-too-late.md`
  — the full bug report with reproduction test and fix
