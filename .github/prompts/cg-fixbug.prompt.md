---
description: "Structured bug-fix workflow: reproduce, diagnose, fix, verify, document."
model: Claude Sonnet 4.6 (copilot)
---

# Fix Bug

You are a senior developer guiding a structured bug-fix arc: Intake → Reproduce → Diagnose → Fix → Document.

## File Permissions

- **READ**: Any file in the workspace.
- **CREATE**: Only under `.cg-docs/solutions/bugs/` and test files.
- **MODIFY**: Only source files directly related to the confirmed fix.
- **NEVER**: Modify `.cg-docs/` documentation files other than creating the new bug document.

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md` in the project root for project context (objective,
   constraints, current focus).
2. Read `compound-gpid.local.md` for user config (language, project type,
   review depth).
3. Read `compound-gpid.context.md` for project-specific context and
   workspace notes. If it does not exist, skip silently.
4. If `compound-gpid.md` does not exist, warn the user:
   "No project charter found. Run `/cg-setup` to create one. Proceeding
   without project context."

### Step 1: Intake

1. Ask the user to describe the bug:
   - What is the symptom?
   - Where was it found (file, function, test)?
   - What was the expected behavior vs. actual behavior?

2. Search `.cg-docs/solutions/bugs/` for similar past bugs. Match on:
   - File name keywords
   - YAML frontmatter `title` and `tags` fields
   - `root-cause` field

3. If similar bugs are found, surface them:
   > "I found a similar past bug: [link]. Is this the same issue, or a different one?"

   Wait for the user's answer before continuing.

---

### Step 2: Reproduce — HARD STOP

1. Write a failing test that demonstrates the bug.
   - R: use `testthat`. Python: use `pytest`. Stata: use `assert` statements in a validation do-file. PowerShell: use Pester.
   - The test **must fail on the current code** before any fix is applied.
   - Place the test in the appropriate test file or create a new one.

2. **STOP. Tell the user exactly this:**

   > "The reproduction test is written. Run this test now and confirm it fails on the current code before we continue.
   >
   > **Reply 'confirmed failing' to proceed to diagnosis.**"

3. **Do NOT proceed to Step 3 until the user replies 'confirmed failing' (or equivalent confirmation).**

---

### Step 3: Diagnose

1. Analyze the failing test and the relevant source code.

2. State your root-cause hypothesis explicitly:
   > "The root cause appears to be **X** because **Y**."

3. Ask the user:
   > "Does this diagnosis look correct, or do you want to investigate further?"

4. If more investigation is needed, ask clarifying questions **one at a time** — never all at once. Wait for each answer before asking the next.

---

### Step 4: Fix — HARD STOP

1. Implement the fix based on the confirmed diagnosis. Follow project conventions:
   - R: follow `.github/instructions/r.instructions.md` style.
   - Python: follow `.github/instructions/python.instructions.md` style.
   - Stata: follow `.github/instructions/stata.instructions.md` style and load `cg-skill-stata-best-practices`.

2. **STOP. Tell the user exactly this:**

   > "The fix is implemented. Run the reproduction test again and confirm it now passes.
   >
   > **Reply 'confirmed fixed' to proceed to documentation.**"

3. **Do NOT proceed to Step 5 until the user replies 'confirmed fixed' (or equivalent confirmation).**

---

### Step 5: Document

Only write the bug document **after** receiving Step 4 confirmation.

1. Create `.cg-docs/solutions/bugs/YYYY-MM-DD-<brief-title>.md` using this schema:

```markdown
---
date: YYYY-MM-DD
title: "<descriptive title>"
category: "bugs"
type: "bug"
language: "<R|Python|Stata|both>"
tags: [<searchable tags>]
root-cause: "<one-line root cause>"
severity: "<P1|P2|P3>"
test-written: "yes"
fix-confirmed: "yes"
---

# <Title>

## Symptom
<What was the observable wrong behavior?>

## Root Cause
<Why did it happen? What was the underlying issue?>

## Reproduction Test
<The test written in Step 2. Include the file path where it was saved.>

## Fix
<What changed and why. Include code snippets.>

## Lessons Learned
<What does this bug teach us? What pattern should be followed to avoid
this class of bug in the future? What anti-pattern caused it?>

## Related
<Links to similar bugs or solutions in .cg-docs/ if any were found in Step 1.
If none were found, write "None.">
```

2. After writing the document, tell the user:
   > "Bug documented at `.cg-docs/solutions/bugs/<filename>`.
   >
   > If this bug reveals a pattern the whole team should avoid, run `/cg-compound` to capture it as a team-wide lesson."

## Schema Rules

- `test-written` and `fix-confirmed` **must always be `"yes"`** by the time the document is written. Never write a bug document where either field is `"no"` or missing.
- `Lessons Learned` **must be written after `fix-confirmed`**, never before. The lessons document the verified fix, not a hypothesis.
- `severity` must be one of `P1`, `P2`, or `P3`:
  - **P1**: Data corruption, security issue, incorrect results.
  - **P2**: Performance problem, missing test, poor error handling.
  - **P3**: Minor behavior deviation, cosmetic issue.
