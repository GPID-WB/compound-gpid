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
- **Consistency** — coding standards, tests, and documentation are enforced on every PR, for both R and Python.
- **Compounding returns** — the `cg-learnings-researcher` agent cross-references past solutions so the team never solves the same problem twice.
- **Zero friction** — one global clone, directory junctions, and three shell commands (`cg-link`, `cg-unlink`, `cg-update`) wire everything into VS Code / Positron automatically.
- **Team-wide** — update once, every linked project gets the new version instantly.

## Documentation

**→ [Read the full documentation in the Wiki](https://github.com/GPID-WB/compound-gpid/wiki)**

| Wiki Page | Contents |
|-----------|---------|
| [Installation](https://github.com/GPID-WB/compound-gpid/wiki/Installation) | Install, link, configure, and upgrade from an old version |
| [Workflow](https://github.com/GPID-WB/compound-gpid/wiki/Workflow) | The Brainstorm → Plan → Work → Review → Compound loop |
| [Reference](https://github.com/GPID-WB/compound-gpid/wiki/Reference) | Commands, agents, skills, configuration, file structure |
| [Troubleshooting](https://github.com/GPID-WB/compound-gpid/wiki/Troubleshooting) | Known issues and step-by-step fixes |

> The wiki is the primary documentation. The `docs/` folder in this repo mirrors the same content for offline reference.

## License

MIT
