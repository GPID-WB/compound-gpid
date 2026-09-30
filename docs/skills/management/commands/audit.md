# `cg-skill audit`

Audit lifecycle metadata, provenance, references, manifests, targets, and exact projections.

**Roles:** `consumer`

**Phases:** `read`

## Synopsis

```text
python scripts/cg_skill.py [common options] audit [<skill-id>] [--provenance] [--references]
```

## Options

| Argument | Required | Meaning |
| --- | --- | --- |
| `<skill-id>` | No | Limit the audit to one immutable identifier. |
| `--provenance` | No | Include provenance checks. |
| `--references` | No | Include classified reference results. |

With no filter, audit runs both audit groups.

## Examples

```powershell
python scripts/cg_skill.py --format json audit --provenance --references
python scripts/cg_skill.py --format json audit cg-skill-python-best-practices --references
```

## Lifecycle Effect

Audit is read-only and performs no mutable remote update discovery. Reference
output classifies active, migration, and historical records with stable paths,
lines, findings, and remediation.

## Results

The result includes manifest health, audited IDs, filters, reference digest, and
classified references. See the [result contract](../index.md#result-contract),
[remediation guide](../consumers/remediation.md),
[workflow](../../../../.github/skills/cg-skill-management/workflows/audit.md), and
[operation contract](../../../../.github/shared/skill-management/contracts/audit-v1.schema.json).
