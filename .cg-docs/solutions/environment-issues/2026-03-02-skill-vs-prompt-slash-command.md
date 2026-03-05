---
date: 2026-03-02
title: "Skills are not slash-command prompts — avoid advertising them as /skill-name"
category: "environment-issues"
language: "both"
tags: [prompts, skills, copilot, ux, naming, slash-commands]
root-cause: "Skills (SKILL.md files in .github/skills/) are reference knowledge loaded by prompts/agents, not slash-command prompts — they cannot be invoked with /skill-name in Copilot Chat"
severity: "P2"
---

# Skills Are Not Slash-Command Prompts

## Problem

Documentation (README, manual) instructed users to run `/cg-setup` in Copilot
Chat to configure their project. However, there is no `.github/prompts/cg-setup.prompt.md`
file — the setup entry point is `.github/skills/cg-skill-setup/SKILL.md`, which
is a **skill**, not a prompt.

Typing `/cg-setup` in Copilot Chat produces no result or an error because Copilot
only resolves `/name` commands to `.prompt.md` files in `.github/prompts/`.

## Root Cause

The distinction between skills and prompts was not reflected in user-facing
documentation:

- **Prompts** (`.github/prompts/*.prompt.md`) are invokable as `/name` in chat.
- **Skills** (`.github/skills/*/SKILL.md`) are reference knowledge loaded by
  prompts and agents. They are not directly invokable as slash commands.

The setup workflow was implemented as a skill (so it could be loaded by other
prompts as a reference) but was documented as if it were a prompt.

## Solution

Two valid fixes:

**Option A (chosen):** Update documentation to accurately describe setup as a
skill, not a slash command. Users load it directly in chat by referencing the
skill, not via `/cg-setup`.

Update any reference from:
```
Run `/cg-setup` in Copilot Chat.
```
To:
```
Load the `cg-skill-setup` skill in Copilot Chat — this is a skill, not a
slash-command prompt.
```

**Option B (alternative):** Create `.github/prompts/cg-setup.prompt.md` that
delegates to the skill. This creates a slash-command entry point that internally
loads and runs the skill. Adds a file but improves UX.

## Prevention

When documenting a workflow entry point, verify which type it is before writing
instructions:

- If it lives in `.github/prompts/` → it is a prompt → document as `/cg-name`
- If it lives in `.github/skills/` → it is a skill → document as "load the
  `cg-skill-name` skill"

When reviewing documentation PRs, check that every `/slash-command` reference
corresponds to an actual `.prompt.md` file in `.github/prompts/`.

## Related

- `docs/plans/2026-03-02-rename-prefix-and-documentation.md` — the plan that
  introduced the naming conventions
- `docs/manual.md` — updated to correctly describe setup as a skill
