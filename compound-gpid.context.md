# Compound GPID — Project Context

This file captures project-specific conventions, workspace notes, and domain
rules that help Copilot produce accurate outputs across all prompts and sessions.

---

## Prompt Design Conventions

- **Mode-specific step skipping**: Steps depending on in-scope findings (e.g., skill loading) are skipped when a mode flag (`--migrate`) is present. The flag is evaluable at invocation time — no formal arg-parsing step needed.

- **Deferred side-effects come after the primary deliverable**: In interactive prompts, side-effect offers (e.g., "create a git branch", "open a PR") must come after the primary deliverable is created — not before. Creating a branch before writing a document means the document is created on the new branch (which may be wrong) and leaves an empty "orphan" branch if the session is interrupted. Pattern: complete the main output first, then offer optional follow-on actions.

## Testing Conventions

- **IndexOf guard pattern**: Block-scoped prompt tests that extract text via `$content.Substring($start, $end - $start)` must first assert both index values with `$start | Should BeGreaterThan -1` and `$end | Should BeGreaterThan $start`. Without guards, a missing section header throws `ArgumentOutOfRangeException`, obscuring which assertion failed.

- **Test only current state, never future state**: Pester tests must assert what is true now. Writing a test for a schema marker before the marker is applied creates a persistent pre-existing failure that pollutes every test run until resolved. Either apply the marker in the same commit as the test, or mark it `-Pending` to defer without failing. See `.cg-docs/solutions/testing-patterns/2026-04-29-premature-schema-marker-test-creates-persistent-failure.md`.

- **SCHEMA_VERSION bumps are not additive**: each bump overwrites the file entirely; pending markers from prior deferred review findings are silently lost. Before bumping `SCHEMA_VERSION` for a new feature, check `.cg-docs/solutions/` and `.cg-docs/reviews/` for any deferred markers (e.g., `scope-fields`) that must be included in the same bump.
