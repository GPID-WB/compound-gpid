# `cg-skill help`

List complete private operations or inspect one exact operation descriptor.

**Roles:** `consumer`

**Phases:** `read`

## Synopsis

```text
python scripts/cg_skill.py [common options] help [<operation>]
```

## Options

This operation has no named options. The optional `<operation>` positional value
limits output to one exact operation.

## Examples

```powershell
python scripts/cg_skill.py --format json help
python scripts/cg_skill.py --format json help import
```

## Lifecycle Effect

Help is read-only. It is descriptor-derived and cannot advertise an operation
until its workflow, handler, contract, tests, and focused documentation page are
complete.

## Results

Operations appear in lexical order with exact roles, phases, workflow paths, and
documentation paths. See the [result contract](../index.md#result-contract),
[discovery guide](../consumers/discovery.md),
[workflow](../../../../.github/skills/cg-skill-management/workflows/help.md), and
[operation contract](../../../../.github/shared/skill-management/contracts/help-v1.schema.json).
