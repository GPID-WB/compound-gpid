# Update an Imported Skill

[Update](../commands/update.md) accepts one existing imported skill and one new
full commit SHA. It reuses the original immutable repository, path, origin,
identifier, and metadata authority.

Review the deterministic path, change-kind, size, and SHA-256 diff. Apply appends
source, approval, policy, evidence, diff, and content digests to provenance. It
does not replace prior provenance history.

Generic mutable update discovery is not available. A specific exact SHA is
required for every comparison.
