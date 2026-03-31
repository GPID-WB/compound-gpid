---
date: 2026-03-30
title: "cg-review missing 'write' tool disables file creation during review sessions"
category: "bugs"
type: "bug"
language: "both"
tags: [cg-review, prompt-frontmatter, tools, write, copilot, file-creation]
root-cause: "cg-review.prompt.md declared tools: ['agent', 'read', 'search'] omitting 'write', which blocked all file-creation operations during /cg-review sessions"
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
---

# cg-review missing 'write' tool disables file creation during review sessions

## Symptom

When running `/cg-review`, the Copilot agent was unable to write any files. This
affected two capabilities:

1. **Triage fixes**: When the user selected "Fix" for a finding, the agent could
   not modify source files to apply the fix.
2. **Review report output**: The desired feature of saving the assembled review
   report to `.cg-docs/reviews/` was impossible because the `write` tool was
   not available.

Users observed that the agent appeared to try to write files but silently failed
or reported it could not do so, with no clear explanation.

## Root Cause

`cg-review.prompt.md` had the following frontmatter:

```yaml
tools: ['agent', 'read', 'search']
```

In VS Code Copilot, the `tools:` key in a prompt's YAML frontmatter restricts
which tools are available to the agent executing that prompt. The `'write'` tool
was omitted, so any file-creation or file-modification operation was blocked for
the duration of a `/cg-review` session.

Additionally, the prompt had no step instructing the agent to persist the review
report to disk — so even if `write` were available, the report would never be
saved.

## Reproduction Test

File: `tests/prompt-tools.Tests.ps1`

The test parses the YAML frontmatter of `cg-review.prompt.md` and asserts:
- `'write'` is present in the `tools:` array
- The prompt body contains a reference to `.cg-docs/reviews/`

Both assertions failed before the fix was applied, verified directly:

```powershell
$f = Get-Content ".github\prompts\cg-review.prompt.md" -Raw
$f -match "'write'"        # False (BUG)
$f -match "\.cg-docs/reviews"  # False (MISSING FEATURE)
```

## Fix

Two changes to `.github/prompts/cg-review.prompt.md`:

**1. Add `'write'` to the tools frontmatter:**

```yaml
# Before
tools: ['agent', 'read', 'search']

# After
tools: ['agent', 'read', 'search', 'write']
```

**2. Add Step 3.5 — Save Review Report** (between Step 3 and Step 4):

The new step instructs the agent to:
- Identify the most recently modified plan in `.cg-docs/plans/`
- Derive the review filename as `<plan-stem>-review.md`
- Write the full prioritized report to `.cg-docs/reviews/<stem>-review.md`
- Inform the user of the saved path

The `.cg-docs/reviews/` directory was also created and tracked with a `.gitkeep`.

## Lessons Learned

- **Prompt `tools:` lists must include every operation the agent is instructed
  to perform.** If a prompt has a step that writes files (triage fixes, report
  output), `'write'` must be in the `tools:` list — otherwise the step silently
  cannot execute.
- **Audit `tools:` after adding new steps.** Any time a prompt gains a step that
  creates, modifies, or deletes a file, immediately verify that `'write'` (or
  the appropriate tool) is declared in the frontmatter.
- **Test prompt frontmatter like you test code.** The `tests/prompt-tools.Tests.ps1`
  fixture now guards this contract. New prompts that gain file-writing steps
  should have corresponding tests added there.

## Related

None.
