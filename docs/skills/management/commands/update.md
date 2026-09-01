# `cg-skill update`

Compare and apply one imported skill update from a new immutable full SHA.

**Roles:** `consumer`, `maintainer`

**Phases:** `plan`, `apply`

## Synopsis

```text
python scripts/cg_skill.py [common options] update <skill-id> <new-full-sha> --license <id> --approver <label> --review-reference <immutable-ref> [--apply <plan-digest>]
```

## Options

| Argument | Required | Meaning |
| --- | --- | --- |
| `<skill-id>` | Yes | Skill with pinned imported provenance. |
| `<new-full-sha>` | Yes | New exact 40-character commit SHA. |
| `--license <id>` | Yes | Expected approved license identifier. |
| `--approver <label>` | Yes | Reviewed audit metadata. |
| `--review-reference <immutable-ref>` | Yes | Immutable review reference. |
| `--apply <plan-digest>` | Apply only | Apply the exact stored plan. |

## Examples

```powershell
python scripts/cg_skill.py --format json update cg-skill-example 2222222222222222222222222222222222222222 --license MIT --approver maintainer --review-reference 1111111111111111111111111111111111111111
python scripts/cg_skill.py --format json update cg-skill-example 2222222222222222222222222222222222222222 --license MIT --approver maintainer --review-reference 1111111111111111111111111111111111111111 --apply aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
```

## Lifecycle Effect

The repository, source path, origin, identifier, owner, capability, and
eligibility remain fixed. Apply appends deterministic redacted diff and policy
digests to provenance, then verifies all selected targets and projections.

## Results

Status is `planned`, `committed`, `blocked`, or `unchanged`; data includes the
diff and its digest. See the [result contract](../index.md#result-contract),
[update guide](../maintainers/updates.md),
[workflow](../../../../.github/skills/cg-skill-management/workflows/update.md), and
[operation contract](../../../../.github/shared/skill-management/contracts/update-v1.schema.json).
