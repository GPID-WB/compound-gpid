# `cg-skill activate`

Plan and apply selection of one explicit capability.

**Roles:** `consumer`

**Phases:** `plan`, `apply`

## Synopsis

```text
python scripts/cg_skill.py [common options] activate <capability> [--apply <plan-digest>]
```

## Options

| Argument | Required | Meaning |
| --- | --- | --- |
| `<capability>` | Yes | One current explicit capability identifier. |
| `--apply <plan-digest>` | Apply only | Apply the exact stored plan. |

## Examples

```powershell
python scripts/cg_skill.py --format json activate project-skill-example
python scripts/cg_skill.py --format json activate project-skill-example --apply aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
```

## Lifecycle Effect

Planning writes no lifecycle state. Apply adds only the explicit selection,
re-resolves the manifest, publishes selected targets and projections, and verifies
their exact desired state. Eligibility selectors can reject selection but cannot
activate a project skill.

## Results

Status is `planned`, `committed`, `no-op`, or `blocked`. See the
[result contract](../index.md#result-contract), [activation guide](../consumers/activation.md),
[workflow](../../../../.github/skills/cg-skill-management/workflows/activate.md),
and [operation contract](../../../../.github/shared/skill-management/contracts/activate-v1.schema.json).
