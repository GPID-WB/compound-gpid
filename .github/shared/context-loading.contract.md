# Context Loading Contract

Use this contract for context-heavy workflow prompts.

## Prompt Classes

- **Ordinary prompts**: `/cg-brainstorm`, `/cg-plan`, `/cg-work`, `/cg-review`, `/cg-resume`, and similar user workflows. They should start with minimal bearings and expand context only when the current task needs it.
- **Maintenance prompts**: `/cg-compound`, `/cg-brain-rebuild`, roadmap commands, setup/update flows, and audit/index tooling. They may read or generate larger artifacts when the workflow explicitly requires whole-file semantics.

## Expansion Statement

Before opening a large generated or tactical artifact beyond its default stage, state:

`Context expansion: reading <artifact/section> because <reason>.`

Use the narrowest artifact, section, snippet, or structured field that can answer the question.

## Staged Policy

| Stage | Name | Allowed default reads | Expansion rule |
| --- | --- | --- | --- |
| 0 | Minimal bearings | `compound-gpid.md`; `compound-gpid.local.md` if needed for language/review flags; command arguments | No large generated or tactical artifacts. |
| 1 | Targeted metadata | File lists, YAML frontmatter, titles, status fields, matching snippets from `.cg-docs`; `roadmap.json` only through workflow-relevant fields | State why the metadata is needed. Do not read whole bodies unless selected. |
| 2 | Query-first knowledge | `cg-skill-brain-query`, `.cg-docs/BRAIN.md`, matched `BRAIN-NN.md` topic sections only | State the search directive and matched topic before opening topic files. |
| 3 | Targeted tactical context | Relevant headings/snippets from `compound-gpid.context.md`; roadmap feature/milestone records relevant to the current plan, feature, or status update | State why the specific section or record is needed. Prefer heading search or structured JSON parsing. |
| 4 | Justified full expansion | Full `compound-gpid.context.md`, full `roadmap.json`, full `.cg-docs/BRAIN-log.md`, full `BRAIN-NN.md`, or full `brain-index.json` | Only when the workflow explicitly requires whole-file semantics. State the reason and the expected decision the full read supports. |

## Module-Suite Context Budget (AI-agent compliance)

Before loading a skill or instruction file, check whether its owning module's suite
is declared active in `compound-gpid.local.md`'s `suites:` field. If not active,
skip it. For example, with `suites: [cg]` only, files owned by the research suite
(`cr-*` prompts, agents, skills, and the research instruction files) are not loaded
into routine sessions; the same applies to the technical suite when it is inactive.

- Active suites plus their transitive dependencies plus kernel form the loadable set.
- Generator-level filtering is available as an explicit isolated-build option.
	The linked native trees are shared all-suite distribution baselines, so
	`cg-update` must not filter the global tree for one consumer. The project-level
	`suites:` rule is an instruction/eligibility contract for AI agents and is NOT
	programmatically verifiable by automated tests. Do not claim automated
	verification of this instruction.
- When `suites:` is absent, the default is `[cg]` (backward compatible).

## Manifest-Aware Capability Routing

When a command explicitly requests a capability (by id, task trigger, or
skill reference) and that capability is not active in the project manifest,
use the capability router to produce a structured hard-stop before doing any
work:

```bash
python scripts/cg_skill_catalog.py --route <capability-id>
```

The router returns:
- **inactiveReason**: why the capability is absent (selector mismatch, suite
  ineligibility, or module not in closure)
- **selector**: the authoritative config selector (field/operator/value) when
  the capability is selector-driven
- **remedy**: the exact `compound-gpid.local.md` field change and `cg-update`
  command needed

**Hard-stop behavior**: when the router returns `found: false`, stop before
work. Do NOT:
- Silently fall back to all-skill global source
- Write a transient session projection
- Alter configuration
- Imply that instructions alone enforce selection
- Continue with degraded partial output

**Inactive reference leak detection**: generated targets, catalog rows, and
adapter/config files must not contain references to assets outside the
selected closure. Run the leak check to verify:

```bash
python scripts/cg_skill_catalog.py --check-leaks
```

The stable `/cg-*` and `/cr-*` workflow namespaces are preserved. Skill
discovery and lifecycle management use the action-first `/cg-skill <operation>`
namespace.

## Artifact Rules

- `.cg-docs/BRAIN.md` is the small agent-facing meta-index and may be read by Brain query flows.
- `BRAIN-NN.md` partitions are retrieval artifacts. Open only matched topic sections unless section extraction is impractical.
- `.cg-docs/BRAIN-log.md` is for chronology, staleness audits, or Knowledge Brain maintenance, not ordinary planning/review/work.
- `.cg-docs/brain-index.json` is a tooling retrieval index. Prompt agents must not read it wholesale; scripts may query it or produce targeted summaries.
- `compound-gpid.context.md` is tactical project context. Ordinary prompts should search headings or snippets first. Full reads are allowed for setup/context-curation and `/cg-compound` enrichment when placement or conflict checks require whole-file context.
- `roadmap.json` should be parsed for workflow-relevant structured fields. Full reads are allowed for roadmap commands and `/cg-resume` milestone health or drift checks, but do not carry unrelated records into the working summary.
- `.cg-docs/views/` contains generated derived HTML. Ordinary and maintenance
	workflows must exclude view bodies, full content, and diffs from model
	context, Brain retrieval, duplicate-content inputs, token source totals, and
	release knowledge scans. Path listing, staging, counts, provenance identity,
	and `cg-render-artifact --check <source>` freshness results are allowed.
