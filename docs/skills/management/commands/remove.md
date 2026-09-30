# `cg-skill remove`

Remove only a deprecated inactive skill after grace, migration, and ownership proof.

**Roles:** `consumer`

**Phases:** `plan`, `apply`

## Synopsis

```text
python scripts/cg_skill.py [common options] remove <skill-id> --approver <label> --review-reference <immutable-ref> [--migrations <csv>] [--grace-exception] [--grace-reason <text>] [--apply <plan-digest>]
```

## Options

| Argument | Required | Meaning |
| --- | --- | --- |
| `<skill-id>` | Yes | Deprecated inactive immutable identifier. |
| `--approver <label>` | Yes | Reviewed audit metadata. |
| `--review-reference <immutable-ref>` | Yes | Immutable review reference. |
| `--migrations <csv>` | No | Versioned digest-bound migration records. |
| `--grace-exception` | No | Request an explicitly reviewed emergency exception. |
| `--grace-reason <text>` | With exception | Exact reviewed exception reason. |
| `--apply <plan-digest>` | Apply only | Apply the exact stored plan. |

## Examples

```powershell
python scripts/cg_skill.py --format json remove cg-skill-old --approver maintainer --review-reference 1111111111111111111111111111111111111111
python scripts/cg_skill.py --format json remove cg-skill-old --approver maintainer --review-reference 1111111111111111111111111111111111111111 --apply aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
```

## Lifecycle Effect

Planning requires a valid successor, immutable grace evidence, staged migrations,
and zero final active references. Apply deletes only exact source bytes and
checksum-owned projections. It preserves provenance, migration evidence,
user-owned bytes, and a permanent non-reusable tombstone.

## Results

The result reports grace evidence, tombstone digest, removed paths, and remaining
references. See the [result contract](../index.md#result-contract),
[retirement guide](../maintainers/deprecation-removal.md),
[workflow](../../../../.github/skills/cg-skill-management/workflows/remove.md), and
[operation contract](../../../../.github/shared/skill-management/contracts/remove-v1.schema.json).
