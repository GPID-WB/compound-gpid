> [!CAUTION]
> **⚠️ WORK IN PROGRESS — DO NOT USE IN PRODUCTION**
>
> This project is under active development and is not yet ready for use.
> Prompts, agents, skills, and conventions may change without notice.
> This banner will be removed when the system is stable.

# Compound GPID

A GitHub Copilot plugin for data science teams, built on the [Compound Engineering Philosophy](https://every.to/guides/compound-engineering).

> Each unit of work should make subsequent units easier — not harder.

## Why Compound GPID?

Compound GPID enforces a repeatable **Brainstorm → Plan → Work → Review → Compound** loop that does more than produce code — it produces *knowledge*. Every solved problem is captured as a structured document and fed back into future reviews, so your team compounds its expertise with every task.

**Key benefits:**
- **Consistency** — coding standards, tests, and documentation are enforced on every PR, for R, Python, and Stata.
- **Compounding returns** — the `cg-learnings-researcher` agent cross-references past solutions so the team never solves the same problem twice.
- **Project awareness** -- Optionally create a compound-gpid.md project charter to give Copilot persistent knowledge of your project's objective, deliverables, constraints, and current focus. Every session then starts in context.
- **Zero friction** — one global clone, directory junctions, and three shell commands (`cg-link`, `cg-unlink`, `cg-update`) wire everything into VS Code / Positron automatically.
- **Team-wide** — update once, every linked project gets the new version instantly.
- **Version management** — pin to a specific release for stability, or track `main` for the latest features. Switch at any time with `cg-update v0.2.0` / `cg-update latest`.

## Documentation

**→ [Read the full documentation in `docs/`](docs/manual.md)**

| Page | Contents |
|------|----------|
| [Installation](docs/installation.md) | Install, link, configure, and upgrade from an old version |
| [Versioning](docs/versioning.md) | Version management — pin to a release, browse tags, return to main |
| [Workflow](docs/workflow.md) | The Brainstorm → Plan → Work → Review → Compound loop |
| [Reference](docs/reference.md) | Commands, agents, skills, configuration, file structure |
| [Troubleshooting](docs/troubleshooting.md) | Known issues and step-by-step fixes |

## License

MIT
