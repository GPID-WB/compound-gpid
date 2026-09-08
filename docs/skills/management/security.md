# Skill Management Security

Skill management treats source acquisition, authority, lifecycle writes, and
destructive cleanup as separate fail-closed controls.

## Acquisition and Quarantine

Imports accept one credential-free public GitHub HTTPS repository, normalized
bundle path, and full commit SHA. Bounded tree and blob traversal verifies sizes,
Git object identities, paths, modes, links, content limits, license, secrets, and
the non-data resource policy before lifecycle state can change.

## Authority and Approval

Consumer is the default role. Canonical mutation requires equal invocation,
project, and source roots in one approved feature-branch checkout. Approver and
review fields are audit metadata, not authorization proof. Project exact-origin
approval cannot grant plugin allowlist authority.

## Provenance and Supply Chain

Provenance is append-only and binds immutable source identity, policy, evidence,
inventory, and content digests. Plans and review evidence are redacted. Imported
content is never executed during admission, generation, validation, or projection.

## Destructive Controls

Apply uses one held lifecycle lock, durable expected-byte journal, and exact
desired-state verification. Removal requires complete references, successor and
grace proof, digest-bound migrations, zero active references, and checksum-owned
paths. Modified and user-owned files are preserved.

Use [audit](commands/audit.md), [remediation](consumers/remediation.md), and the
[lifecycle model](lifecycle.md) for operational checks.
