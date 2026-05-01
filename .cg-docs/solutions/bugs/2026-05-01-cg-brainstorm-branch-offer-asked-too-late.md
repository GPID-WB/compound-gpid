---
date: 2026-05-01
title: "cg-brainstorm branch offer asked too late and buried in handoff"
category: "bugs"
type: "bug"
language: "PowerShell"
tags: [cg-brainstorm, branch-offer, step-ordering, ux, prompts]
root-cause: "Branch offer was Step 4.5 (after saving the brainstorm document), bundled implicitly with Step 5 handoff options, where the user had already invested time answering 3–6 clarifying questions on the wrong branch"
severity: "P3"
test-written: "yes"
fix-confirmed: "yes"
---

# cg-brainstorm branch offer asked too late and buried in handoff

## Symptom

When running `/cg-brainstorm`, the prompt asked "would you like to create a new
branch?" only at **Step 4.5**, which fires *after* the brainstorm document was
already saved. By this point the user had answered 3–6 clarifying questions,
chosen an approach, and reviewed the devil's advocate pushback — all on the
wrong (often `main`) branch. The question was also easy to miss because it
appeared in the same conversational turn as the broader "what would you like to
do next?" handoff stream.

## Root Cause

`### Step 4.5: Branch Offer` was placed between Step 4 (Capture Decision) and
Step 5 (Handoff). The design rationale at the time was "offer after the
decision is made so we have a brainstorm title to derive the branch name from."
But this trades naming precision for a worse user experience: the user does the
entire brainstorm on the current branch and only learns they should have been on
a feature branch when the session is almost over.

## Reproduction Test

Added to `tests/prompt-tools.Tests.ps1` as the
`"cg-brainstorm.prompt.md - Branch Offer appears before Step 2"` Describe block
(P1.44):

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

Both `It` blocks failed (returned `-1`) before the fix.

## Fix

**`cg-brainstorm.prompt.md`**

1. Removed `### Step 4.5: Branch Offer` entirely.
2. Added `### Step 1.7: Branch Offer` between Step 1.5 (Scope Assessment) and
   Step 2 (Clarifying Questions). The new step asks the branch question as the
   *very first* thing before any clarifying questions begin.
3. Updated the File Permissions section: `Step 4.5` → `Step 1.7`.
4. The branch name is derived from the user's *initial description* rather than
   the saved brainstorm title. This is slightly less precise but acceptable —
   the user can rename the branch later.
5. Thinking Partner mode skips Step 1.7 silently (non-software tasks don't need branches).

**`tests/prompt-tools.Tests.ps1`**

Replaced the stale
`"cg-brainstorm.prompt.md - Step 4.5 Branch Offer ordering"` Describe block
with a new `"cg-brainstorm.prompt.md - Step 1.7 Branch Offer ordering"` block
that verifies: Step 1.7 > Step 1.5 and Step 2 > Step 1.7.

## Lessons Learned

- **Branch-early, not branch-late**: The branch offer should be the *first*
  question asked in any workflow that will produce committed work. Don't wait
  until the session has produced an artifact — by then the user is invested and
  unlikely to re-do the work on a proper branch.
- **Never bundle the branch offer with the handoff menu**: The handoff step
  presents 4+ options and the branch question gets lost. Isolate it as its own
  named step so the model must ask it as a standalone question.
- **Test step ordering explicitly**: Step-ordering bugs are invisible to content
  tests. Add `IndexOf` ordering assertions whenever a prompt has a step that
  must appear before another.

## Related

- `.cg-docs/solutions/bugs/2026-04-13-cg-work-roadmap-status-never-updated-to-done.md`
  — similar "step executed too late" class of bug.
