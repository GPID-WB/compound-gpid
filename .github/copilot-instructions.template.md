<!-- compound-gpid:template — source for copilot-instructions.md, managed by scripts/helpers.ps1.
     Run `cg-update` to regenerate the output file from this template.
     Do not edit .github/copilot-instructions.md directly.
     Template variables substituted at generation time: project-name, project-type, languages, review-depth. -->
# Project Instructions

This project uses [Compound GPID](https://github.com/GPID-WB/compound-gpid),
a structured AI-assisted workflow plugin. Prompts: `.github/prompts/`,
skills: `.github/skills/`.

## Project Identity

- **Name**: {{project-name}}
- **Type**: {{project-type}}
- **Languages**: {{languages}}
- **Review depth**: {{review-depth}}

## Essential Context

- Read `compound-gpid.md` for the project charter (objective, constraints,
  current focus).
- Read `compound-gpid.context.md` for project-specific context and workspace
  notes. If it does not exist, skip silently.
- Check `compound-gpid.local.md` for per-user preferences (language, dialect,
  review depth).

## Essential Rules

- **Fail loudly, never silently** — explicit errors for missing data, null
  weights, and missing artifacts; no silent fallbacks.
- **Commit lockfiles and institutional knowledge** — `renv.lock`,
  `poetry.lock`, `.cg-docs/` must be version-controlled. Never gitignore them.
- **Conventional commits required** — `type(scope): description` format;
  work on branches, not main.

## Workspace

- **Principal folder**: this one ({{project-name}}) — Compound GPID is
  active here.
- For multi-folder workspace details, see `## Workspace Notes` in
  `compound-gpid.context.md` (if it exists).
