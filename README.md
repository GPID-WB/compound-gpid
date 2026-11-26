# Compound GPID

> [!WARNING]
> This is branch `v2`, where Compound GPID 2.0 is being built. It installs (see `docs/install-block.md`), and the guide `/cg` can set up a project, think an idea through with you (`/cg brainstorm`), write the plan you approve (`/cg plan`), do the work of that plan slice by slice (`/cg work`) and do quick work. Reviews and sign-off come later in milestone 2, so it is not ready for real work yet.
> Version 1 is on branch `main` and frozen on branch `v1`; its install instructions are in the README there.

Compound GPID helps analysts (economists, researchers and data scientists, and the people who build their packages, pipelines and dashboards) use a coding agent and still own and understand what gets built.

Version 2 is a hub of packs. Everyone installs the core pack; language, research and other packs are added when needed. Every pack is a set of skill folders in the open Agent Skills format, so the same files work in GitHub Copilot, Claude Code, Codex and Kilo, and no coding agent is the base.

## What is here

| Path | What it is |
|---|---|
| `packs/` | One folder per pack. `packs/core/cg/` is the core pack's lead skill: the guide, its playbooks, the principles and the plugin glossary. |
| `.claude-plugin/marketplace.json` | The pack index, read by `install.py`. It is also a valid Claude Code marketplace, but that is not a supported way to install. |
| `install.py`, `docs/install-block.md` | The installer, and the one install text. |
| `tools/` | Checks run in CI, and the version sync. |
| `docs/adr/` | Decision records: hosts, sources, packs, no base host, artifacts. |
| `docs/v2/HANDOFF.md` | Where the build stands and what comes next. |
| `SCOPE.md`, `.out-of-scope/` | What belongs in core, the size budgets, and ideas already set aside. |
| `.cg-docs/` | This project's own plans, reviews and solutions, from version 1 on. |
| `spike/` | The host test kit used for ADR 0001. |

The documentation pages under `docs/` other than `adr/` and `v2/` still describe version 1. They are reviewed in task 7.5.

## Credits

Compound GPID builds on Every's Compound Engineering and adapts ideas from addyosmani/agent-skills, mattpocock/skills and cursor/plugins (pstack). See `docs/adr/0002-sources.md` and `THIRD_PARTY_NOTICES`.

## License

MIT, see `LICENSE`. Text adapted from other projects keeps its own notice in `THIRD_PARTY_NOTICES`.
