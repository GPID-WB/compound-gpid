# `cg-skill create`

Plan and create one inactive permanent canonical skill scaffold.

**Roles:** `maintainer`

**Phases:** `plan`, `apply`

## Synopsis

```text
python scripts/cg_skill.py [common options] create <skill-id> --scope permanent --description <text> --owner <module> --capability <id> --suites <csv> --platforms <csv> --activation-cost <low|medium|high> --triggers <csv> --selectors <json> --approver <label> --review-reference <immutable-ref> [--references <csv>] [--workflows <csv>] [--examples <csv>] [--resources <csv>] [--resource-classes <json>] [--apply <plan-digest>]
```

## Options

| Argument | Required | Meaning |
| --- | --- | --- |
| `<skill-id>` | Yes | New immutable skill identifier. |
| `--scope permanent` | Yes | Restrict creation to permanent plugin scope. |
| `--description <text>` | Yes | Quoted ASCII-safe frontmatter description. |
| `--owner <module>` | Yes | Exact canonical module owner. |
| `--capability <id>` | Yes | Explicit capability identifier. |
| `--suites <csv>` | Yes | Supported suite identifiers. |
| `--platforms <csv>` | Yes | Supported platform identifiers. |
| `--activation-cost <value>` | Yes | `low`, `medium`, or `high`. |
| `--triggers <csv>` | Yes | Stable task triggers. |
| `--selectors <json>` | Yes | Eligibility selectors. |
| `--approver <label>` | Yes | Reviewed audit metadata. |
| `--review-reference <immutable-ref>` | Yes | Immutable review reference. |
| `--references <csv>` | No | Focused reference files to scaffold. |
| `--workflows <csv>` | No | Focused workflow files to scaffold. |
| `--examples <csv>` | No | Focused example files to scaffold. |
| `--resources <csv>` | No | Approved non-data resources to scaffold. |
| `--resource-classes <json>` | Conditional | Exact classes for opaque resources. |
| `--apply <plan-digest>` | Apply only | Apply the exact stored plan. |

## Examples

```powershell
python scripts/cg_skill.py --format json create cg-skill-example --scope permanent --description "Example focused skill." --owner cap-example --capability example --suites cg --platforms copilot,kilo --activation-cost low --triggers example --selectors "[]" --approver maintainer --review-reference 1111111111111111111111111111111111111111
python scripts/cg_skill.py --format json create cg-skill-example --scope permanent --description "Example focused skill." --owner cap-example --capability example --suites cg --platforms copilot,kilo --activation-cost low --triggers example --selectors "[]" --approver maintainer --review-reference 1111111111111111111111111111111111111111 --apply aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
```

## Lifecycle Effect

Planning validates frontmatter, ownership, capability metadata, resource classes,
and collisions without publishing state. Apply writes canonical source,
provenance, registry, manifest, targets, and projections through one transaction.
The new capability remains inactive.

## Results

Status is `planned`, `committed`, or `blocked`; availability is always `inactive`.
See the [result contract](../index.md#result-contract), [creation guide](../maintainers/creation.md),
[workflow](../../../../.github/skills/cg-skill-management/workflows/create.md), and
[operation contract](../../../../.github/shared/skill-management/contracts/create-v1.schema.json).
