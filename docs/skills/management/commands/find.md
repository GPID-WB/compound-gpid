# `cg-skill find`

Search deterministic canonical and project skill metadata without remote discovery.

**Roles:** `consumer`

**Phases:** `read`

## Synopsis

```text
python scripts/cg_skill.py [common options] find [--id <text>] [--exact] [--capability <id>] [--suite <id>] [--platform <id>] [--available] [--unavailable] [--cost <low|medium|high>] [--owner <id>] [--provenance <text>] [--full]
```

## Options

| Option | Meaning |
| --- | --- |
| `--id <text>` | Filter identifiers. |
| `--exact` | Require exact `--id` equality. |
| `--capability <id>` | Filter by capability. |
| `--suite <id>` | Filter by supported suite. |
| `--platform <id>` | Filter by supported platform. |
| `--available` | Require proven active availability. |
| `--unavailable` | Require proven inactive availability. |
| `--cost <value>` | Filter by activation cost. |
| `--owner <id>` | Filter by owning module. |
| `--provenance <text>` | Filter by provenance identity. |
| `--full` | Include complete inspection fields. |

## Examples

```powershell
python scripts/cg_skill.py --format json find --id cg-skill-python-best-practices --exact --full
python scripts/cg_skill.py --format json find --suite cg --platform kilo --cost low
```

## Lifecycle Effect

Find is read-only. Missing or stale manifests produce prospective rows with
regeneration remediation. Availability filters require a fresh manifest. The
operation never searches global, generated, external, or network locations.

## Results

Records are deterministic and include origin, lifecycle, availability, and
manifest health. See the [result contract](../index.md#result-contract),
[discovery guide](../consumers/discovery.md),
[workflow](../../../../.github/skills/cg-skill-management/workflows/find.md), and
[operation contract](../../../../.github/shared/skill-management/contracts/find-v1.schema.json).
