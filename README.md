> [!NOTE]
> **⚠️ WORK IN PROGRESS**
>
> Core workflows (brainstorm, plan, work, review, fix-triage, compound) are stable.
> Advanced features (release automation, context layer) are still evolving.
> Prompts, agents, skills, and conventions may change without notice.

# Compound GPID

A GitHub Copilot plugin for data science teams, built on the [Compound Engineering Philosophy](https://every.to/guides/compound-engineering).

> **Runtime scope**: Compound GPID supports GitHub Copilot, Claude Code, Codex,
> and OpenCode. `.github/` is the canonical source; native platform trees
> (`.claude/`, `.agents/`, `.opencode/`) are generated from it and distributed
> through per-platform install units. `cg-link` links all supported platforms by
> default; use `cg-link --platforms copilot` or another comma-separated list to
> narrow the install.

> Each unit of work should make subsequent units easier — not harder.

## Why Compound GPID?

Compound GPID enforces a repeatable **Brainstorm → Plan → Work → Review → Fix Triage → Compound** loop that does more than produce code — it produces *knowledge*. Every solved problem is captured as a structured document and fed back into future reviews, so your team compounds its expertise with every task.

**Key benefits:**
- **Consistency** — coding standards, tests, and documentation are enforced on every PR, for R, Python, and Stata.
- **Compounding returns** — the `cg-learnings-researcher` agent cross-references past solutions so the team never solves the same problem twice.
- **Project awareness** -- Optionally create a compound-gpid.md project charter to give Copilot persistent knowledge of your project's objective, deliverables, constraints, and current focus. Every session then starts in context.
- **R dialect selection** — set `r-syntax: "tidyverse"` in your local config to have all R assistance use tidyverse/dplyr patterns instead of data.table/collapse. Ideal for projects with external coauthors who only know the tidyverse. See [docs/reference.md](docs/reference.md) for details.
- **Knowledge brain** — `cg-index --brain` and `/cg-brain-rebuild` build a structured knowledge brain (`BRAIN.md`, `BRAIN-NN.md`, `BRAIN-log.md`, `brain-index.json`) by clustering `.cg-docs/` artifacts into topics and mapping typed relationships between artifacts — so every session can surface relevant past work automatically.
- **Roadmap tracking** — `@cg-roadmap` manages a `roadmap.json` milestone and feature tracker. Brainstorm, Plan, and Work prompts hook into it automatically: brainstorms register feature ideas, plans link to features, and work marks them active — so your roadmap stays current without manual updates.
- **Cross-platform** — native support for GitHub Copilot, Claude Code, Codex, and OpenCode from a single `.github/` source. Generated platform trees are committed, release-validated, and distributed through merge-safe per-platform install units. `cg-link` links all platforms by default.
- **Zero friction** — one global clone, per-subdirectory symlinks (junctions on Windows, symlinks on macOS), and shell commands (`cg-link`, `cg-unlink`, `cg-update`, `cg-index`, `cg-brain-init`, `cg-token-audit`) wire everything into VS Code / Positron automatically.
- **Token guidance** — `/cg-token-audit` runs deterministic context/model analysis and returns compact advice on context size, review depth, and model selection without changing project files.
- **Team-wide** — update once, every linked project gets the new version instantly.
- **Version management** — pin to a specific release for stability, or track `main` for the latest features. Switch at any time with `cg-update v0.2.0` / `cg-update latest`.

## Documentation

**→ [Read the full documentation in `docs/`](docs/manual.md)**

| Page | Contents |
|------|----------|
| [Installation](docs/installation.md) | Install, link, configure, and upgrade from an old version |
| [Workflow](docs/workflow.md) | The Brainstorm → Plan → Work → Review → Compound loop |
| [Reference](docs/reference.md) | Commands, agents, skills, configuration, file structure |
| [Context Files](docs/context-files.md) | Copilot context files plus the Codex / Claude Code adapter note |
| [Model Guide](docs/model-guide.md) | Model-picker policy, token/context guidance, escalation guidance, and audit guardrails |
| [Team Brain Schema](docs/team-brain-schema.md) | Team Brain repository schema and local configuration |
| [Versioning](docs/versioning.md) | Version management — pin to a release, browse tags, return to main |
| [Troubleshooting](docs/troubleshooting.md) | Known issues and step-by-step fixes |
| [Competitive Reviews](docs/competitive-reviews.md) | Maintainer guide for `/cg-review-repos` workflows |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local test setup, cross-platform
requirements, commit conventions, and the PR workflow.

## License

MIT
