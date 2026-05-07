---
date: 2026-05-06
title: "Fix applied as HTML comment not executed — prompt instruction must be prose, not markup"
category: "testing-patterns"
language: "both"
tags: [prompt-design, fix-triage, html-comment, executable-instruction, silent-failure, agent-design, cg-ideate]
root-cause: "During fix-triage, the P2.15 fix for cg-ideate was written as an HTML comment (<!-- ... -->) instead of an executable prose instruction. HTML comments are stripped from LLM context or ignored as markup — the model never acts on them."
severity: "P2"
fix-confirmed: "no"
reviewed-in: ".cg-docs/reviews/2026-05-06-roadmap-visualization-verify-review.md"
---

# Fix Applied as HTML Comment Not Executed — Prompt Instruction Must Be Prose

## Problem

During fix-triage for the roadmap-visualization review, finding P2.15 required
migrating `cg-ideate.prompt.md` to dispatch `@cg-roadmap-view` for the
roadmap-add flow (Step 5, option 3). The applied fix was:

```markdown
<!-- For display of the roadmap to the user, dispatch @cg-roadmap-view. -->
- Option 3: @cg-roadmap (to track without immediate action)
```

The verify pass (V-P2.1) found that **`cg-ideate` still had no `@cg-roadmap-view`
dispatch**. The HTML comment served as a note-to-self for the developer but was
invisible to the model executing the prompt. The user landing on option 3 still
picks a milestone blindly — the bug was not fixed.

Every other prompt that received the same P2.15 fix (`cg-plan-review`,
`cg-brainstorm`) had the instruction written as executable prose and
worked correctly.

## Root Cause

HTML comments (`<!-- ... -->`) in Markdown prompt files are:
1. **Not rendered** by Markdown parsers — they appear only in raw source.
2. **Stripped or deprioritized** by many LLM context processors.
3. **Never parsed as instructions** — even when visible in context, a comment
   is treated as informational annotation, not a directive the model should act on.

A fix note like `<!-- dispatch @cg-roadmap-view here -->` is structurally
identical to a TODO comment in source code: it describes intent, it does not
implement it.

## Solution

Every fix to a `.prompt.md` or `.agent.md` file must be written as executable
prose — a numbered step item, a bullet instruction, or a condition clause that
the model will encounter and act on at runtime.

**Wrong** (comment as fix placeholder):
```markdown
<!-- For display of the roadmap to the user, dispatch @cg-roadmap-view. -->
- Option 3: @cg-roadmap (to track without immediate action)
```

**Right** (executable instruction):
```markdown
- Option 3: Add to roadmap. Dispatch `@cg-roadmap-view` with `view: summary`
  to show current milestones, then ask which milestone to assign this idea to.
  Then dispatch `@cg-roadmap` with the chosen milestone and idea.
```

Comments may still serve as design rationale or maintenance notes for human
readers. They must be accompanied by — never substituted for — the actual
instruction.

## Prevention

- **Fix-triage checklist**: After applying a fix to a `.prompt.md` / `.agent.md`
  file, verify the fix text appears outside of `<!-- ... -->` delimiters.
- **Verify pass**: The `mode:verify` pattern in `/cg-review` catches this class
  of incomplete fix. Run it after every fix-triage cycle.
- **Co-authored tests**: See `2026-05-01-fix-triage-prompt-changes-need-co-authored-tests.md`.
  A test that checks `($content -match '@cg-roadmap-view')` would immediately
  expose this gap.

## Related

- [`2026-05-01-fix-triage-prompt-changes-need-co-authored-tests.md`](2026-05-01-fix-triage-prompt-changes-need-co-authored-tests.md) — every prompt fix needs an immediate Pester assertion
- [`2026-04-23-verify-mode-suppression-must-be-anchored-to-fixed-finding-scope.md`](../testing-patterns/2026-04-23-verify-mode-suppression-must-be-anchored-to-fixed-finding-scope.md) — verify pass correctly re-surfaced the incomplete fix as V-P2.1
