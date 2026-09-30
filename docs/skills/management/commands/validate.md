# `cg-skill validate`

Validate one skill or the complete combined canonical and project skill set.

**Roles:** `consumer`

**Phases:** `read`

## Synopsis

```text
python scripts/cg_skill.py [common options] validate [<skill-id> | --all]
```

## Options

| Argument | Required | Meaning |
| --- | --- | --- |
| `<skill-id>` | Conditional | Validate one exact immutable identifier. |
| `--all` | Conditional | Validate all combined registry skills. |

Use exactly one selection form.

## Examples

```powershell
python scripts/cg_skill.py --format json validate cg-skill-python-best-practices
python scripts/cg_skill.py --format json validate --all
```

## Lifecycle Effect

Validate is read-only. It checks descriptors, contracts, frontmatter, atomic
bundle inventory, links, ownership, capabilities, project records, provenance,
manifest health, targets, projections, references, and containment.

## Results

The result includes manifest health, validated IDs, descriptor operations, and
stable findings. See the [result contract](../index.md#result-contract),
[remediation guide](../consumers/remediation.md),
[workflow](../../../../.github/skills/cg-skill-management/workflows/validate.md),
and [operation contract](../../../../.github/shared/skill-management/contracts/validate-v1.schema.json).
