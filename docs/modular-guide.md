# Modular Guide — Technical (`/cg-*`) and Research (`/cr-*`) Suites

## CG or CR: Choose a Workflow

Choose by the question you must answer, not by programming language, whether you
write code, or your level of experience. Both suites require human judgment,
independent verification, and verified lessons.

| Decision | Technical (CG) | Research (CR) |
| --- | --- | --- |
| Main question | Does the implementation meet engineering requirements? | Is the research claim supported by evidence, assumptions, and valid methods? |
| Typical task | Fix a launcher, deliver a feature, maintain a service | Compare surveys, validate a published indicator, specify an estimator |
| Review focus | Behavior, tests, security, maintainability, reproducibility | Provenance, comparability, identification, assumptions, uncertainty, research integrity |
| Example | A quoted project path breaks a launcher | A survey redesign changes who is represented in a poverty estimate |
| Start | [Choose a technical task](workflows/index.md) | [First CR workflow](research/first-workflow.md) |

> [!TECHNICAL] A launcher repair belongs to CG. A passing launcher test shows that the invocation works; it does not establish a statistical claim.

> [!RESEARCH] Statistical specification and published-indicator validation belong to CR, including their implementation code. Research review identifies evidence gaps; it does not certify a claim as true.

### Mixed Work and Bounded Handoffs

A research project can need a separate infrastructure repair. Keep the research
question, assumptions, and integrity gates in the CR plan. Define the technical
repair's inputs, expected behavior, tests, and return evidence in a bounded CG
task when the CG suite is active. Return verified artifacts to the CR workflow
before interpreting results. `/cg-review` does not replace `/cr-review`.

CR composes shared language, testing, and reproducibility capabilities without
depending on the CG suite. Enabling both suites does not merge their review
responsibilities. Rendering and institutional report-writing capabilities have
shared support metadata. Skill Management currently declares `cg` only, and the
registry owns `cg-*` prompts in the Technical suite. A capability-layer module is
not automatically shared, and a badge does not activate a prompt. Check canonical
ownership, capability support, and the resolved project closure rather than the prefix.

### Select the Suite Explicitly

Use one of these configurations in `compound-gpid.local.md`, then follow
[configuration](configuration/index.md) and [installation](installation.md) for
the selected host. These are alternatives, not three successive edits.

```yaml
suites: [cg]
```

```yaml
suites: [cr]
```

```yaml
suites: [cg, cr]
```

The technical default is `[cg]` when the field is absent. `/cg-setup` requires an
eligible technical workflow; selecting CR alone does not make that prompt active.
The [Research Handbook](research/index.md) gives the CR-only activation path.

## Architecture and Configuration

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
| Mixed: research that implements code, tests, and reproduces | `/cr-work` (research conventions apply automatically in implementation mode) | Research — composes technical capabilities |

Concise rule of thumb: **`/cg-*` drives the technical loop; `/cr-*` drives the
research loop.** A research task often *uses* technical capabilities (language
skills, testing, reproducibility) without needing the full technical command
surface.

Researchers who are new to Compound GPID should start with the [Research
Handbook](research/index.md). It explains the research rationale, suite
activation, and first workflow before sending readers to the detailed
references below.

## How suites compose capabilities

Capability packs are reusable pieces of implementation knowledge shared by one
or both suites:

- **Language support** — `cap-language-r`, `cap-language-python`,
  `cap-language-stata`, `cap-language-powershell` (skills + instruction files).
- **Research output** — `cap-research-output` (publication output,
  replication standards, research EDA).
- **Research language support** — `cap-language-research` (LaTeX/math).
- **Other shared capability packs** — Pester safety, git workflow, document
  rendering, World Bank report writing, generic review agents (`cap-review-agents`),
  knowledge capture (`cap-compound-docs`), and public skill lifecycle management
  (`cap-skill-management`).

You do not need to name dependencies. Loading `/cr-work` in a project whose
`suites:` includes `cr` automatically pulls the research suite, kernel, and every
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

The native trees in the Compound GPID source repository are a shared,
all-suite distribution baseline. `cg-link` and `cg-update` share those trees
across linked projects, so they must not rewrite the global tree for one
consumer's local `suites:` choice. Instead, the generated root instructions and
workflow prompts use `suites:` to determine which workflow is eligible in that
project; inactive-suite commands are not treated as active workflow routes.

Maintainers can still produce an isolated filtered tree with
`python scripts/cg_generate_targets.py --all --active-suites cg` (or
`cg,cr`) for packaging or inspection. This option is explicit and does not
change the shared install baseline. Characterization and drift tests enforce
the all-suite baseline, while the context loader
(`.github/shared/context-loading.contract.md`, canonical source; copied to each
platform tree) documents the project-level eligibility rule.

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

The generated targets are `.claude/`, `.agents/`, `.opencode/`, and `.kilo/`;
GitHub Copilot uses the canonical `.github/` source directly. Never edit a
generated target to change module behavior.

> See [Reference](reference.md) for command contracts and configuration fields;
> the module-registry schema is documented in `.github/shared/module-registry.json`.
> See [Skills](skills/index.md) for the skill catalog.
