# Agents

Agents provide focused analysis or controlled infrastructure behavior. Most are
dispatched by prompts and should not be invoked directly.

## Review agents

| Agent | Focus |
|---|---|
| `cg-code-quality` | Style, linting, duplication, and naming |
| `cg-testing` | Coverage, edge cases, test quality, and test patterns |
| `cg-documentation` | Code documentation, README quality, and explanatory comments |
| `cg-version-control` | Commit hygiene, branching, and secrets |
| `cg-reproducibility` | Lockfiles, paths, seeds, and reproducible execution |
| `cg-performance` | Vectorization, memory, and algorithmic complexity |
| `cg-architecture` | Structure, modularity, boundaries, and dependencies |
| `cg-data-quality` | Inputs, types, missing values, and schema consistency |
| `cg-learnings-researcher` | Relevant prior project solutions in a full review |
| `cg-adversarial` | Edge cases, corruption, race conditions, and security in a full review |

## Workflow and infrastructure agents

| Agent | Used by |
|---|---|
| `cg-plan-critic` | `/cg-plan-review` |
| `cg-project-scanner` | `/cg-setup` and project-analysis steps |
| `cg-release-scanner` | compound-gpid-only `/cg-release` |
| `cg-fix-problems` | `/cg-fix-problems` |
| `cg-roadmap-view` | `/cg-roadmap-view` |
| `cg-wiki` | `/cg-wiki` |
| `cg-roadmap` | Direct roadmap management and workflow-dispatched roadmap writes |

`cg-roadmap` is the documented direct user-facing agent for writing
`roadmap.json`. Other agents are internal specialists even if a particular host
exposes their files in its generated tree.

## Research review agents

Research agents are owned by `suite-cr` and dispatched conditionally by
`/cr-review`; `/cg-review` does not import them.

| Agent | Focus |
|---|---|
| `cr-research-integrity` | P0 silent research errors and integrity gates |
| `cr-provenance-audit` | Claim-evidence traceability and citation provenance |
| `cr-mathematical-verification` | Derivation-to-code consistency |
| `cr-identification-audit` | Causal identification and required diagnostics |
| `cr-econometric-reasoning` | Structural and econometric model logic |
| `cr-ml-methodology` | Leakage, validation, inference, and economic ML interpretation |
| `cr-specification-analysis` | Theory-data implications and specification discipline |
| `cr-measurement-integrity` | Indicators, thresholds, clustering, and comparability |
| `cr-academic-writing` | Economics-paper structure, notation, and citations |
| `cr-publication-output` | Publication tables, figures, captions, and deterministic output |
| `cr-replication-package` | Replication archive completeness and portability |

## Dispatch principle

The review route determines which review agents run. Light review uses a small
set; data-risk, architecture, and full routes add the lenses needed by changed-
file risk. Packaging differs by host, so public capability should be inferred
from the canonical `.github/agents/` source and workflow contracts rather than
counting generated files.

See [Review and Assure](../workflows/assure.md) for route selection and
[Complete Reference](../reference.md) for models and detailed agent contracts.
See the [Modular Guide](../modular-guide.md) for ownership and dependency rules.
