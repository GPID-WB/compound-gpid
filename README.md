> [!NOTE]
> **⚠️ WORK IN PROGRESS**
>
> Core workflows (brainstorm, plan, work, review, fix-triage, compound) are stable.
> Advanced features (release automation, context layer) are still evolving.
> Prompts, agents, skills, and conventions may change without notice.

# Compound GPID

A GitHub Copilot plugin for data science teams, built on the [Compound Engineering Philosophy](https://every.to/guides/compound-engineering).

> **Runtime scope**: Compound GPID supports GitHub Copilot, Claude Code, Codex,
> OpenCode, and Kilo. `.github/` is the canonical source; native platform trees
> (`.claude/`, `.agents/`, `.opencode/`, `.kilo/`) are generated from it and distributed
> through per-platform install units. `cg-link` links all supported platforms by
> default; use `cg-link --platforms copilot` or another comma-separated list to
> narrow the install.

Native targets package each canonical skill as an **atomic skill bundle**. A
bundle contains `SKILL.md` plus all nested regular files and **includes them by default**;
it is not a `SKILL.md`-only copy. Executable resources are copied as opaque
bytes with their executable bit recorded and are never executed during
generation. See [Generated Native Platform Trees](docs/context-files.md#generated-native-platform-trees)
for ownership, recovery, and verification guarantees.

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
- **Modular suites** — a validated registry separates the kernel, reusable capability packs, the technical `/cg-*` suite, and the research `/cr-*` suite. Projects select `suites: [cg]`, `[cr]`, or `[cg, cr]` without creating cross-suite dependencies.
- **Cross-platform** — native support for GitHub Copilot, Claude Code, Codex, OpenCode, and Kilo from a single `.github/` source. Generated platform trees are committed, release-validated, and distributed through merge-safe per-platform install units. `cg-link` links all platforms by default.
- **Zero friction** — one global clone, per-subdirectory symlinks (junctions on Windows, symlinks on macOS), and shell commands (`cg-link`, `cg-unlink`, `cg-update`, `cg-index`, `cg-brain-init`, `cg-publish-markdown`, `cg-token-audit`) wire everything into VS Code / Positron automatically.
- **Secure document views** — `cg-publish-markdown` turns one project-contained generic Markdown file into a deterministic, self-contained `reference` HTML view while preserving strict Brainstorm/Plan validation and excluding generated bodies from model context.
- **Token guidance** — `/cg-token-audit` runs deterministic context/model analysis and returns compact advice on context size, review depth, and model selection without changing project files.
- **Team-wide** — update once, every linked project gets the new version instantly.
- **Version management** — pin to a specific release for stability, or track `main` for the latest features. Switch at any time with `cg-update v0.2.0` / `cg-update latest`.

## Documentation

**→ [Open the documentation site](https://gpid-wb.github.io/compound-gpid/)** or start with
[Getting Started](docs/getting-started/index.md).

| Page | Contents |
|------|----------|
| [Getting Started](docs/getting-started/index.md) | Understand the project, install/configure it, and complete a first workflow |
| [Why Compound GPID?](docs/why-compound-gpid.md) | Institutional focus, upstream inspiration, differences, and tradeoffs |
| [Workflows](docs/workflows/index.md) | Task-oriented paths from strategy through verified knowledge capture |
| [Skills](docs/skills/index.md) | Canonical analytical, technical, testing, and institutional skill catalog |
| [Configuration](docs/configuration/index.md) | Context files, platform targets, settings, and managed content |
| [Modular Guide](docs/modular-guide.md) | Suite selection, capability composition, registry ownership, and extension rules |
| [Governance](docs/governance/index.md) | Data safeguards, review gates, operating constraints, and limitations |
| [Reference](docs/reference.md) | Complete commands, agents, schemas, configuration, and file structure |
| [Help](docs/help/index.md) | Recovery routes and complete troubleshooting links |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local test setup, cross-platform
requirements, commit conventions, and the PR workflow.

## License

MIT
