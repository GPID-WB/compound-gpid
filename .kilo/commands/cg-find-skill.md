---
description: "Discover skills and capabilities from the manifest-backed catalog."
---

# Find Skill

Query the static manifest-backed skill catalog to discover available skills,
their activation requirements, and activation costs.

## Process

1. Read `compound-gpid.local.md` for the current project configuration.
2. Load `.compound-gpid/active-manifest.json`. If missing or stale, stop:
   > "No active manifest found. Run `cg-link` or `cg-update` first to generate the project manifest."
3. Run the catalog query:
   ```
   python scripts/cg_skill_catalog.py --format json [filters]
   ```
4. Present results. Default compact view shows: id, purpose, capability,
   availability, and activation cost.

## Filters

| Flag | Effect |
|------|--------|
| `--id <query>` | Match skill id or purpose substring |
| `--capability <id>` | Filter by capability id |
| `--suite <name>` | Filter by supported suite |
| `--platform <id>` | Filter by supported platform |
| `--available` | Only active/available skills |
| `--unavailable` | Only inactive skills |
| `--cost <level>` | Filter by activation cost (low/medium/high) |
| `--full` | Show all metadata (source path, provenance, eligibility, inactive reason) |

## Capability Routing

When a command needs a specific capability and it is not active, use:

```
python scripts/cg_skill_catalog.py --route <capability-id>
```

This returns a structured hard-stop with:
- The inactive reason
- The authoritative selector/configuration field
- The exact `cg-link` or `cg-update` regeneration action

Do NOT silently fall back to global all-skill source.

## Examples

```
# List all available skills
/cg-find-skill

# Find R-related skills
/cg-find-skill --id r

# Show full metadata for unavailable skills
/cg-find-skill --unavailable --full

# Check if a capability is active
/cg-find-skill --route research-output
```

## Invocation Arguments

User-provided slash-command arguments:

```text
$ARGUMENTS
```
