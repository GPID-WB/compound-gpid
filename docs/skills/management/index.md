# Skill Management

This candidate guide documents the private descriptor-driven skill lifecycle. It
is intentionally absent from public navigation until the complete pre-removal
gate passes.

The [operation descriptors](../../../.github/shared/skill-management/operations/help.json)
define operation identity, role, phase, workflow, contract, tests, and command
page. The [private dispatcher](../../../scripts/cg_skill.py) loads only complete
active descriptors.

## Choose a Path

- [Consumer guide](consumers/index.md)
- [Maintainer guide](maintainers/index.md)
- [Lifecycle and roles](lifecycle.md)
- [Security controls](security.md)
- [Migration guide](migration.md)

## Operations

- [activate](commands/activate.md)
- [audit](commands/audit.md)
- [create](commands/create.md)
- [deactivate](commands/deactivate.md)
- [deprecate](commands/deprecate.md)
- [find](commands/find.md)
- [help](commands/help.md)
- [import](commands/import.md)
- [info](commands/info.md)
- [remove](commands/remove.md)
- [update](commands/update.md)
- [validate](commands/validate.md)

## Consumer Topics

- [Discover and inspect](consumers/discovery.md)
- [Import a project skill](consumers/project-import.md)
- [Activate and deactivate](consumers/activation.md)
- [Understand availability](consumers/availability.md)
- [Remediate findings](consumers/remediation.md)

## Maintainer Topics

- [Create permanent skills](maintainers/creation.md)
- [Vendor imported skills](maintainers/vendoring.md)
- [Manage registry and capabilities](maintainers/registry-capabilities.md)
- [Update imported skills](maintainers/updates.md)
- [Deprecate and remove](maintainers/deprecation-removal.md)
- [Release changes](maintainers/release.md)

## Common Grammar

Common options must appear before the operation:

```text
python scripts/cg_skill.py [--project-root <path>] [--source-root <path>] [--format human|json] <operation> [operation arguments]
```

Consumer is the default role. The dispatcher derives maintainer authority from
the checkout context; a command-line role value cannot grant authority. Mutating
operations plan first and apply only the same digest-bound arguments with
`--apply <64-character-plan-digest>`.

## Result Contract

Human and JSON output use the same deterministic result envelope. Every finding
has a stable code, severity, path, message, and remediation. Exit codes are:

| Result | Code | Meaning |
| --- | ---: | --- |
| `success` | 0 | The read, plan, or apply completed safely. |
| `internal` | 1 | Trusted dispatch or output failed unexpectedly. |
| `usage` | 2 | Operation grammar or typed arguments are invalid. |
| `contract` | 3 | A descriptor, schema, manifest, or result contract failed. |
| `role-context` | 4 | The validated checkout role cannot perform the operation. |
| `security` | 5 | Admission, path, source, or content security blocked the operation. |
| `lifecycle-conflict` | 6 | Current lifecycle state does not permit the requested transition. |
| `stale-plan` | 7 | Inputs or expected bytes changed after planning. |
| `verification` | 8 | Final desired-state verification failed. |

Do not reinterpret a nonzero code as partial success. Follow the returned
remediation and create a new plan after any relevant input changes.
