---
description: "Render a workflow artifact or generic Markdown document to curated HTML. Routes typed artifacts to cg-render-artifact and generic documents to cg-publish-markdown. Supports --theme selection (reference or editorial)."
---

# Render Doc

You render one project-contained Markdown source to curated HTML using the
deterministic two-theme publishing pipeline.

## File Permissions

- You may read any file in the workspace.
- You may run `cg-render-artifact` and `cg-publish-markdown` to render, check,
  or validate documents.
- You must NOT modify source files, generated views, or theme modules.
- You must NOT generate HTML directly — always use the deterministic CLI tools.

## When to Use

Use `/cg-render-doc` when the user asks to:
- Render a plan, brainstorm, or generic Markdown document to HTML
- Check whether a rendered view is current or stale
- Validate a document without writing output
- Select a specific theme (`reference` or `editorial`) for rendering

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md` (objective, constraints, current focus). If missing,
   warn: "No project charter found. Run `/cg-setup` to create one. Proceeding
   without project context."
2. Read `compound-gpid.local.md` (language, project type, review depth).
3. Load `cg-skill-render-doc` for the publishing workflow, theme reference, and
   CLI reference.

### Step 1: Parse the Request

Identify from the user's request:

1. **Source path**: The Markdown file to render. If ambiguous, ask.
2. **Mode**: render (default), check, validate-only, or automatic.
3. **Theme**: `reference` (default), `editorial`, or unspecified.
4. **Output path** (generic only): Optional custom output path.

### Step 2: Route to the Correct Tool

1. If the source is under `.cg-docs/brainstorms/` or `.cg-docs/plans/`:
   use `cg-render-artifact`.
2. If the source is any other `.md` file in the project, excluding
   `.cg-docs/views/` generated outputs:
   use `cg-publish-markdown`.
3. Never use `cg-publish-markdown` on typed artifact roots — the CLI rejects
   them with exit code 2.

### Step 3: Resolve the Theme

1. If the user explicitly requests `editorial`, pass `--theme editorial`.
2. If the user explicitly requests `reference`, pass `--theme reference`
   (or omit — it's the default).
3. If the user does not specify a theme:
   - For a new render: omit `--theme` (uses document-type default: `reference`).
   - For a re-render: the CLI reuses the recorded theme from existing provenance.
4. **Never silently select `editorial`**. If the user seems unsure, recommend
   but ask: "The editorial theme uses a warm paper palette with Georgia/Trebuchet
   typography. Would you like to use it, or stick with the default reference theme?"

### Step 4: Execute

Run the appropriate command with the resolved flags. Report the result to the
user:

- **Render success**: Show the output path.
- **Check**: Report `current`, `stale`, or `missing` with the path.
- **Validate-only**: Confirm validation passed.
- **Failure**: Show the error message and the recovery command printed by the CLI.

### Step 5: Recovery Guidance

If the command fails:
1. Read the error message and recovery command from the CLI output.
2. Explain the failure in plain language.
3. Provide the exact recovery command.
4. Do not attempt to fix source files or theme modules — those are out of scope
   for this prompt.

## Theme Reference

| Theme | Default For | Key Characteristics |
|-------|-------------|---------------------|
| `reference` | All document types | Clean minimal style, Iowan Old Style + Avenir Next, single accent |
| `editorial` | None (explicit only) | Warm paper palette, Georgia + Trebuchet, multi-accent (coral, teal, blue, yellow) |

Both themes produce semantically identical HTML — only CSS presentation differs.
See `cg-skill-render-doc` references for full design contracts.

## Constraints

- Never generate HTML directly — always use the deterministic CLI.
- Never modify theme modules, renderers, or the publishing pipeline.
- Never pass `--theme editorial` without user confirmation.
- Never use `cg-publish-markdown` on `.cg-docs/brainstorms/` or `.cg-docs/plans/` sources.
- Never use either publishing command on `.cg-docs/views/` generated outputs.
- Output paths are always under `.cg-docs/views/` — never outside the project.