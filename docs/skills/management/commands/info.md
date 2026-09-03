# `cg-skill info`

Inspect one canonical or project skill by its exact immutable identifier.

**Roles:** `consumer`

**Phases:** `read`

## Synopsis

```text
python scripts/cg_skill.py [common options] info <skill-id>
```

## Options

This operation has no named options. `<skill-id>` is one required exact
immutable identifier.

## Examples

```powershell
python scripts/cg_skill.py --format json info cg-skill-python-best-practices
```

## Lifecycle Effect

Info is read-only and never falls back to a global skill directory. A missing or
stale manifest can produce prospective metadata but cannot prove availability.

## Results

The result includes purpose, owner, capability, source, provenance, selectors,
supported suites and platforms, lifecycle, and availability context. See the
[result contract](../index.md#result-contract), [discovery guide](../consumers/discovery.md),
[workflow](../../../../.github/skills/cg-skill-management/workflows/info.md), and
[operation contract](../../../../.github/shared/skill-management/contracts/info-v1.schema.json).
