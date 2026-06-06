# Review Routing Contract

Canonical routing contract for `/cg-review` and `/cg-work review:*`.

## Modes

| Mode | Required agents |
|------|------------------|
| `light` | `@cg-code-quality`, `@cg-testing` |
| `standard` | `@cg-code-quality`, `@cg-testing`, `@cg-documentation`, `@cg-version-control`, `@cg-reproducibility`, `@cg-performance`, `@cg-architecture`, `@cg-data-quality` |
| `data-risk` | all `standard` agents, with mandatory emphasis on `@cg-data-quality` and `@cg-reproducibility` |
| `architecture` | all `standard` agents, with mandatory emphasis on `@cg-architecture` and `@cg-performance` |
| `full` | all `standard` agents plus `@cg-learnings-researcher` and `@cg-adversarial` |

## Risk Classes

Risk classes are internal selectors. User-facing output should report the
resolved mode.

| Internal risk class | Resolved mode |
|---------------------|---------------|
| `low` | `light` |
| `normal` | `standard` |
| `data-risk` | `data-risk` |
| `architecture-risk` | `architecture` |
| `security-risk` | `full` |

## Precedence

Resolve routes in this order:

1. verify/report-only guard behavior
2. risk-class routing result
3. explicit user mode
4. line-volume escalation
5. config default

`mode:verify` is light-only and exempt from staged broad routing. `--report-only`
changes triage behavior, not risk classification.

Explicit user modes can raise review depth, but they must not lower review depth
below a mandatory risk-class route. For example, `/cg-review light` on a
security-risk change still resolves to `full`.

## Trigger Taxonomy

| Trigger | Internal risk class |
|---------|---------------------|
| Docs-only, comments-only, small prompt wording, metadata-only, or low-risk tests | `low` |
| Ordinary implementation, prompt, or test changes without high-risk signals | `normal` |
| Statistical, survey, poverty, welfare, weights, joins, aggregation, summary tables, model estimation, reproducibility-sensitive scripts, or pipeline/extract/load scripts | `data-risk` |
| Architecture, dependency, module boundary, performance, memory, concurrency, API contract, or large refactor changes | `architecture-risk` |
| Auth, secrets, credentials, tokens, permissions, release automation, publishing, install/update paths, linking/unlinking paths, schema changes, or destructive filesystem behavior | `security-risk` |

Line volume can raise `light -> standard`. Risk-class modes (`data-risk`,
`architecture`, `full`) take precedence over line-volume upgrades.

## Dedup

Apply additive dedup: if multiple rules request the same agent, dispatch once.
If multiple high-risk classes apply, choose the highest resolved mode by
coverage: `full` > `architecture` / `data-risk` > `standard` > `light`, then
include any mandatory emphasis in the dispatch instructions.
