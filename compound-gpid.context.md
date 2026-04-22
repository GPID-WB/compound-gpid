# Compound GPID — Project Context

This file captures project-specific conventions, workspace notes, and domain
rules that help Copilot produce accurate outputs across all prompts and sessions.

---

## Prompt Design Conventions

- **Mode-specific step skipping**: Steps depending on in-scope findings (e.g., skill loading) are skipped when a mode flag (`--migrate`) is present. The flag is evaluable at invocation time — no formal arg-parsing step needed.

- **Deferred side-effects come after the primary deliverable**: In interactive prompts, side-effect offers (e.g., "create a git branch", "open a PR") must come after the primary deliverable is created — not before. Creating a branch before writing a document means the document is created on the new branch (which may be wrong) and leaves an empty "orphan" branch if the session is interrupted. Pattern: complete the main output first, then offer optional follow-on actions.

## Testing Conventions

- **IndexOf guard pattern**: Block-scoped prompt tests that extract text via `$content.Substring($start, $end - $start)` must first assert both index values with `$start | Should BeGreaterThan -1` and `$end | Should BeGreaterThan $start`. Without guards, a missing section header throws `ArgumentOutOfRangeException`, obscuring which assertion failed.
