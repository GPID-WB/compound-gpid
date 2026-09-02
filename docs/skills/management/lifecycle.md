# Skill Lifecycle

Skill management separates source origin, admission, lifecycle, availability,
and manifest health so one status cannot imply another.

## State Model

| Dimension | Values | Meaning |
| --- | --- | --- |
| Origin | `plugin-canonical`, `project-imported` | The authority and store that own the bundle. |
| Admission | `quarantined`, `approved`, `rejected` | The bounded source-review state. |
| Lifecycle | `current`, `deprecated`, `removed` | Immutable identity progression. |
| Availability | `inactive`, `active` | Whether an explicit selected capability is usable. |
| Manifest health | `fresh`, `missing`, `stale`, `invalid` | Whether runtime availability is proven. |

An imported or created skill starts inactive. Activation is a separate explicit
plan. Deprecation blocks new activation but does not silently deactivate current
use. Removal requires inactive deprecated state, a valid successor, grace
evidence, completed migrations, zero active references, and checksum ownership.

## Roles

Consumers can discover, inspect, validate, audit, import project skills, and
manage explicit project selections. Maintainers can also change canonical plugin
assets, but only when invocation root, project root, and canonical source root
are the same approved feature-branch checkout.

Approver labels and review references are audit metadata. They do not grant
authority and do not replace repository review or branch protection.

## Plan and Apply

Every mutation creates a deterministic plan by default. Its digest binds
normalized arguments, resolved role, source and project roots, registries,
configuration, manifest, provenance, references, and bundle inventory.

Apply repeats the same operation arguments with `--apply <digest>`. A held lock,
durable journal, compare-before-replace publication, and exact final verification
make the operation crash-consistent and forward-recoverable. A changed input or
byte invalidates the plan rather than being overwritten.

## Lifecycle Paths

- Project: [import](consumers/project-import.md) -> [activate](consumers/activation.md) -> [update](maintainers/updates.md) -> [deprecate and remove](maintainers/deprecation-removal.md)
- Plugin: [create](maintainers/creation.md) or [vendor](maintainers/vendoring.md) -> [registry review](maintainers/registry-capabilities.md) -> [release](maintainers/release.md)

See [security controls](security.md) before any source acquisition or destructive
operation.
