# Modular Guide — Technical (`/cg-*`) and Research (`/cr-*`) Suites

Compound GPID is a modular plugin. The canonical `.github/` tree is organized
into **modules** across three layers — **kernel**, **capability packs**, and
**suites** — so every asset has one owner, dependencies stay acyclic and
cross-suite-safe, and you can pick which workflows you load.

This guide is task-oriented: start from "I want to do X" and follow the shortest
path. It explains suite selection, how suites compose capabilities, module
preferences, extension rules for maintainers, and migration from the legacy
single-suite package.

## Choosing a suite: `/cg-*` vs `/cr-*`

| I want to… | Use | Suite |
|---|---|---|
| Develop code, fix bugs, manage infrastructure, or run a technical workflow | `/cg-work`, `/cg-plan`, `/cg-review`, `/cg-fixbug`, … | Technical (`cg`) |
| Run a research workflow: scoping, identification, measurement, econometrics, replication, publication output | `/cr-work`, `/cr-plan`, `/cr-review`, `/cr-compound`, … | Research (`cr`) |
| Mixed: research that implements code, tests, and reproduces | `/cr-work` (it loads R/Python/Stata skills automatically) | Research — composes technical capabilities |

Concise rule of thumb: **`/cg-*` drives the technical loop; `/cr-*` drives the
research loop.** A research task often *uses* technical capabilities (language
skills, testing, reproducibility) without needing the full technical command
surface.

## How suites compose capabilities

Capability packs are reusable pieces of implementation knowledge shared by one
or both suites:

- **Language support** — `cap-language-r`, `cap-language-python`,
  `cap-language-stata`, `cap-language-powershell` (skills + instruction files).
- **Research output** — `cap-research-output` (publication output,
  replication standards, research EDA).
- **Research language support** — `cap-language-research` (LaTeX/math).
- **Other shared capability packs** — Pester safety, git workflow, document
  rendering, World Bank report writing.

You do not need to name dependencies. Loading `/cr-work` in a project with
`suites: [cg, cr]` automatically pulls the research suite, kernel, and every
capability it depends on. Skills like `cr-skill-publication-output` and
`r.instructions.md` are available without you referencing module ids.

## Module preferences

The `suites:` field in `compound-gpid.local.md` selects which workflows are
active. Preferences:

| Configuration | Behavior |
|---|---|
| `suites: [cg]` (or absent) | Technical-only. CR prompts/skills and LaTeX/math instructions are **not loaded** into routine sessions. Context = kernel + `cg` + shared capabilities. |
| `suites: [cr]` | Research-only. CG workflow prompts are not in the active loadable set. |
| `suites: [cg, cr]` | Mixed. Both suites plus shared capabilities. |

Example:

```yaml
# compound-gpid.local.md
suites: [cg, cr]
```

Generator-level enforcement: `python scripts/cg_generate_targets.py --all --active-suites cg`
emits only CG + shared assets (1071 files in main), while `--active-suites cg,cr`
emits the full 1214-file tree. The context loader (`.kilo/shared/context-loading.contract.md`)
follows the same rule at instruction level.

## Migration from the legacy single-suite package

- Legacy configs without a `suites:` field are read as `[cg]` — no behavior change.
- `python scripts/cg_migrate_config.py` adds `suites: [cg]` idempotently and
  non-destructively; re-running is a no-op and existing frontmatter is preserved.
- The module registry (`module-registry.json`) is data, not a code fork: existing
  `cg-skill-*` identifiers keep working via the registry; user-facing `/cg-*` and
  `/cr-*` names are stable.

## Extension rules for maintainers

Adding a capability pack or a future suite is data in `.github/shared/module-registry.json`:

1. Add a module with `layer: capability` (or `suite`), a unique `id`, a
   `description`, `ownedAssets` globs under `.github/`, and `dependsOn` only on
   lower layers (kernel for capabilities; kernel/capabilities for suites).
2. Never create an empty module without a reason — an empty module is a warning.
3. Run the validator: `python scripts/cg_validate_modules.py --check-ownership
   --check-dependencies --check-cross-suite`. Every canonical asset must be
   owned by exactly one module; the dependency graph must be acyclic; suites may
   not depend on suites; capabilities may not depend on suites.
4. If a shared capability is used by both suites, keep it as a capability pack
   and depend on it from each suite (never reference another suite's assets
   directly).
5. Regenerate: `python scripts/cg_generate_targets.py --all`, then run the drift
   gate (`pytest scripts/tests/test_target_drift.py`).

> See [Reference](reference.md) for command contracts and the module-registry
> schema. See [Skills](skills/index.md) for the skill catalog.
