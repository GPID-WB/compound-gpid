# Configuration

Run `/cg-setup` after linking a project. Configuration separates personal
preferences, shared project direction, and durable project knowledge so teams
can commit only the appropriate information.

## User configuration

`compound-gpid.local.md` is personal and gitignored. Its YAML frontmatter
contains the supported setup fields:

| Field | Values | Purpose |
|---|---|---|
| `language` | R, Python, Stata, a combination, or `other` | Routes language guidance |
| `r-syntax` | `data.table-collapse` or `tidyverse` | Selects the R manipulation dialect; `collapse` remains available for weighted statistics |
| `project-type` | `package`, `analysis`, `dashboard`, `api`, `tool`, or `other` | Provides project-structure context |
| `review-depth` | `light`, `standard`, or `thorough` | Sets the legacy default; `thorough` maps to `full` review |
| `artifact-html` | `true` or `false` | Enables or suppresses automatic Brainstorm/Plan HTML writes; validation remains mandatory |
| `cg-schema-version` | Date-prefixed schema identifier | Managed by updates; do not edit manually |

`artifact-html: false` affects automatic writes only. It does not affect
`cg-render-artifact <source>`, `--validate-only`, or `--check`, and it can never
disable validation. Emitter flag `--no-html` is the one-run equivalent for the
HTML write, not a project setting.

## Shared project context

`compound-gpid.md` is an optional committed charter with exactly four body
sections: Objective, Key Deliverables, Constraints, and Current Focus. It is a
short strategic source, not a running work log.

`compound-gpid.context.md` is optional committed tactical context. Appropriate
content includes data-source caveats, domain vocabulary, workspace structure,
variable notes, and recurring gotchas. Keep plans, reviews, and solved problems
in `.cg-docs/` rather than duplicating them here.

Do not commit `compound-gpid.local.md`. Do not place credentials, private data,
or raw secrets in any context file.

## Platform selection

The normal command links all supported platforms:

```bash
cg-link
```

Narrow the install only when needed:

```bash
cg-link --platforms copilot
cg-link --platforms claude-code,codex
cg-link --platforms opencode
```

Canonical authoring lives in `.github/`. Committed `.claude/`, `.agents/`, and
`.opencode/` trees are generated targets. Do not repair generated copies by
editing them directly.

## Managed and user-owned content

Directory install units are junctions on Windows and symlinks on macOS. Marker-
managed text files can be regenerated. Strict configuration files that cannot
contain comments use `.compound-gpid/managed-files.json` checksums.

If a target file is user-owned or has changed since it was managed, link and
update operations preserve it and report the conflict. Review the suggested
snippet instead of replacing the file wholesale.

The repository's `adapters/` directory is a superseded compatibility path.
Generated native trees are the current default and should be used for new
installations.

## Detailed references

- [Context Files](../context-files.md) covers lifecycle, charter quality, and platform architecture.
- [Files and Artifacts](../reference/files.md) maps installed and generated paths.
- [Installation Details](../installation.md) covers setup and migration procedures.
- [Complete Reference](../reference.md) defines all configuration fields and schemas.
