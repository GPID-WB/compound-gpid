# Configuration

Run `/cg-setup` after linking a project. Configuration separates personal
preferences, shared project direction, and durable project knowledge so teams
can commit only the appropriate information.

## User configuration

`compound-gpid.local.md` is committed team-shared configuration (keep it out of `.gitignore` so every
worktree, clone, and team member receives it without manual copying). Its YAML frontmatter
contains the supported setup fields:

| Field | Values | Purpose |
|---|---|---|
| `language` | R, Python, Stata, a combination, or `other` | Routes language guidance |
| `r-syntax` | `data.table-collapse` or `tidyverse` | Selects the R manipulation dialect; `collapse` remains available for weighted statistics |
| `project-type` | `package`, `analysis`, `dashboard`, `api`, `tool`, or `other` | Provides project-structure context |
| `review-depth` | `light`, `standard`, or `thorough` | Sets the legacy default; `thorough` maps to `full` review |
| `suites` | `[cg]` (default/absent), `[cr]`, `[cg, cr]` | Active suites for the modular architecture; selects which workflow prompts/skills load into routine sessions |
| `artifact-html` | `true` or `false` | Explicitly enables automatic Brainstorm/Plan and generic Markdown HTML writes; validation remains mandatory |
| `cg-schema-version` | Date-prefixed schema identifier | Managed by updates; do not edit manually |

Automatic HTML publication is opt-in. Missing `compound-gpid.local.md`, a
missing `artifact-html` field, and `artifact-html: false` all disable automatic
writes. Invalid values emit a warning and also default to disabled.

`artifact-html: true` affects automatic writes only. It does not affect
`cg-render-artifact <source>`, `--validate-only`, or `--check`, and it can never
disable validation. Emitter flag `--no-html` is the one-run equivalent for the
HTML write, not a project setting.

For `cg-publish-markdown --automatic`, the same setting suppresses output
inspection and mutation while source, path, resource, and theme validation
still run. Explicit generic render, `--validate-only`, and `--check` remain
available.

## Shared project context

`compound-gpid.md` is an optional committed charter with exactly four body
sections: Objective, Key Deliverables, Constraints, and Current Focus. It is a
short strategic source, not a running work log.

`compound-gpid.context.md` is optional committed tactical context. Appropriate
content includes data-source caveats, domain vocabulary, workspace structure,
variable notes, and recurring gotchas. Keep plans, reviews, and solved problems
in `.cg-docs/` rather than duplicating them here.

Do keep `compound-gpid.local.md` version-controlled (committed, not in `.gitignore`).
Do not place credentials, private data,
or raw secrets in any context file.

## Modular architecture

`.github/shared/module-registry.json` assigns every canonical prompt, agent,
skill, instruction, and shared contract to exactly one module. Modules form
three layers:

The `cg` suite includes the public `skill-management` capability. Use
`/cg-skill help` to inspect lifecycle operations. Project skills stay inactive
until their explicit capability is selected and the manifest is regenerated.

| Layer | Responsibility |
|---|---|
| Kernel | Lifecycle contracts, context loading, target mapping, and core infrastructure |
| Capability packs | Reusable language, testing, rendering, review, knowledge, and research-output support |
| Suites | Independent user-facing command surfaces: technical `suite-cg` and research `suite-cr` |

Active suites plus their transitive capability dependencies and the kernel form
the loadable set. Suites never depend directly on one another. Research work may
reuse technical capability packs without importing the `/cg-*` command suite.

Validate registry ownership and boundaries with:

```bash
python scripts/cg_validate_modules.py --check-ownership --check-dependencies --check-cross-suite
```

See the [Modular Guide](../modular-guide.md).

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
cg-link --platforms kilo
```

Canonical authoring lives in `.github/`. Committed `.claude/`, `.agents/`, `.opencode/`, and `.kilo/` trees are generated targets. Do not repair generated copies by editing them directly.

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

## Kilo autopilot requirements

`/cg-autopilot` is the only command that needs a specific runtime. It requires
Kilo with the dedicated primary `cg-autopilot` agent installed and natively
selected; document flags, envelopes, or copied tool lists never substitute for
actual native selection. The parent coordinates and validates child results but
never implements fixes or runs tests itself, so the primary session must have
a foreground Task tool available for stage children and at most three
conditional-nesting levels with full input validation at each level.

Requirements are explicit and scoped:

- One dedicated primary agent (`cg-autopilot`) with its own model-assignment
  and permission settings; existing user-owned configuration is preserved and
  never rewritten by setup.
- Parent context budgets (8192 bytes per returned frame, 65536 cumulative
  bytes per primary context) pause before another dispatch; they never
  truncate and never reset within the same session.
- The control helper `cg-autopilot-control` is installed with the other shell
  commands; `inspect` is its only enabled operation today. See the [Autopilot
  (Kilo) Operating Contract](../reference.md) for the full fresh/resume
  syntax, scoped approvals, repair rounds, and recovery behavior.
- Production execution is not enabled: the command is probe-only and returns
  `blocked: bootstrap-only` for fresh/resume pipeline arguments until native
  qualification completes. Unsupported adapters, missing qualification, and
  safe-pause boundaries are reported as typed blockers, never worked around.

No user or global Kilo configuration is modified by the autopilot contract;
runtime containment, capability, and trust checks follow the ordinary Kilo
installation policy.

## Detailed references

- [Context Files](../context-files.md) covers lifecycle, charter quality, and platform architecture.
- [Files and Artifacts](../reference/files.md) maps installed and generated paths.
- [Installation Details](../installation.md) covers setup and migration procedures.
- [Complete Reference](../reference.md) defines all configuration fields and schemas.
