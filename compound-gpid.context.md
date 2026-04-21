# Compound GPID — Project Context

This file captures project-specific conventions, workspace notes, and domain
rules that help Copilot produce accurate outputs across all prompts and sessions.

---

## Prompt Design Conventions

- **Plan selection sort key**: All prompts that pick "the most recent plan" use
  the `date:` frontmatter field as the primary sort key; fall back to last-write
  time if `date:` is absent; break ties by alphabetically last filename. This is
  standardized across `cg-work`, `cg-plan`, and `cg-fix-triage`.

- **Skill loading**: Load language skills conditionally — only when in-scope
  findings or changed files reference that file type. If all findings reference
  `.md`, `.json`, or `.ps1` files only, skip language skill loading entirely.
  This avoids misleading the model with irrelevant constraints.
