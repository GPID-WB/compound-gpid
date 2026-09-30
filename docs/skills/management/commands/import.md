# `cg-skill import`

Plan and apply one inactive skill import from an exact public GitHub source.

**Roles:** `consumer`

**Phases:** `plan`, `apply`

## Synopsis

```text
python scripts/cg_skill.py [common options] import <repository> <bundle-path> <full-sha> --license <id> [--scope project|plugin] [--suites <csv>] [--platforms <csv>] [--owner <module>] [--capability <id>] [--activation-cost <low|medium|high>] [--triggers <csv>] [--selectors <json>] [--approver <label>] [--review-reference <immutable-ref>] [--apply <plan-digest>]
```

## Options

| Argument | Required | Meaning |
| --- | --- | --- |
| `<repository>` | Yes | Credential-free public GitHub HTTPS origin. |
| `<bundle-path>` | Yes | Normalized repository-relative bundle path. |
| `<full-sha>` | Yes | Exact 40-character commit SHA. |
| `--license <id>` | Yes | Expected approved license identifier. |
| `--scope project|plugin` | No | Defaults to project; plugin requires maintainer context. |
| `--suites <csv>` | Plugin | Supported suites. |
| `--platforms <csv>` | Plugin | Supported platforms. |
| `--owner <module>` | Plugin | Canonical module owner. |
| `--capability <id>` | Plugin | Canonical capability identifier. |
| `--activation-cost <value>` | Plugin | `low`, `medium`, or `high`. |
| `--triggers <csv>` | Plugin | Stable task triggers. |
| `--selectors <json>` | Plugin | Eligibility selectors. |
| `--approver <label>` | Plugin | Reviewed audit metadata. |
| `--review-reference <immutable-ref>` | Plugin | Immutable review reference. |
| `--apply <plan-digest>` | Apply only | Apply the exact stored plan. |

## Examples

```powershell
python scripts/cg_skill.py --format json import https://github.com/example/skills skills/example 1111111111111111111111111111111111111111 --license MIT
python scripts/cg_skill.py --format json import https://github.com/example/skills skills/example 1111111111111111111111111111111111111111 --license MIT --apply aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
```

## Lifecycle Effect

Planning writes only confined quarantine and redacted evidence. Project apply
adds an inactive project record and cannot change canonical plugin assets.
Plugin scope requires a separate allowlisted maintainer plan. Import never
activates the skill.

## Results

The result reports status, skill ID, and review-evidence path. See the
[result contract](../index.md#result-contract), [project import guide](../consumers/project-import.md),
[workflow](../../../../.github/skills/cg-skill-management/workflows/import.md), and
[operation contract](../../../../.github/shared/skill-management/contracts/import-v1.schema.json).
