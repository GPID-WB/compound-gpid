# `cg-skill deactivate`

Plan and apply removal of one explicit capability selection.

**Roles:** `consumer`

**Phases:** `plan`, `apply`

## Synopsis

```text
python scripts/cg_skill.py [common options] deactivate <capability> [--apply <plan-digest>]
```

## Options

| Argument | Required | Meaning |
| --- | --- | --- |
| `<capability>` | Yes | One explicitly selected capability identifier. |
| `--apply <plan-digest>` | Apply only | Apply the exact stored plan. |

## Examples

```powershell
python scripts/cg_skill.py --format json deactivate project-skill-example
python scripts/cg_skill.py --format json deactivate project-skill-example --apply aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
```

## Lifecycle Effect

Planning writes no lifecycle state. Apply removes only the explicit selection,
then converges the manifest, targets, and projections. Selector-derived and
dependency-required capabilities are not subtracted. Only checksum-owned stale
projection files can be removed.

## Results

Status is `planned`, `committed`, `no-op`, or `blocked`. See the
[result contract](../index.md#result-contract), [activation guide](../consumers/activation.md),
[workflow](../../../../.github/skills/cg-skill-management/workflows/deactivate.md),
and [operation contract](../../../../.github/shared/skill-management/contracts/deactivate-v1.schema.json).
