# `cg-skill deprecate`

Deprecate one immutable skill identifier in favor of a same-origin successor.

**Roles:** `consumer`

**Phases:** `plan`, `apply`

## Synopsis

```text
python scripts/cg_skill.py [common options] deprecate <skill-id> <successor-id> --approver <label> --review-reference <immutable-ref> [--apply <plan-digest>]
```

## Options

| Argument | Required | Meaning |
| --- | --- | --- |
| `<skill-id>` | Yes | Current immutable identifier to deprecate. |
| `<successor-id>` | Yes | Current nondeprecated same-origin successor. |
| `--approver <label>` | Yes | Reviewed audit metadata. |
| `--review-reference <immutable-ref>` | Yes | Immutable review reference. |
| `--apply <plan-digest>` | Apply only | Apply the exact stored plan. |

## Examples

```powershell
python scripts/cg_skill.py --format json deprecate cg-skill-old cg-skill-new --approver maintainer --review-reference 1111111111111111111111111111111111111111
python scripts/cg_skill.py --format json deprecate cg-skill-old cg-skill-new --approver maintainer --review-reference 1111111111111111111111111111111111111111 --apply aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
```

## Lifecycle Effect

The successor must be current, nondeprecated, acyclic, and from the same origin.
Apply records the successor and immutable deprecation-record digest. It blocks
new activation; active use remains visible as a migration warning.

## Results

The result reports status, origin, successor, active warning, and deprecation
digest. See the [result contract](../index.md#result-contract),
[retirement guide](../maintainers/deprecation-removal.md),
[workflow](../../../../.github/skills/cg-skill-management/workflows/deprecate.md),
and [operation contract](../../../../.github/shared/skill-management/contracts/deprecate-v1.schema.json).
