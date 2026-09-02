# Deprecate and Remove Skills

[Deprecate](../commands/deprecate.md) preserves the immutable identifier and
records a valid same-origin successor. Existing active use receives a migration
warning, while new activation is blocked.

[Remove](../commands/remove.md) requires deprecated inactive state, a successor,
immutable grace evidence, digest-bound migration edits, and a final zero-reference
rescan. It deletes only exact source bytes and checksum-owned projections, then
writes a permanent tombstone. User-owned or modified files are never deleted.

Plugin grace uses pinned release attestation data. Project grace uses a later
descendant project revision. See [release](release.md) and [migration](../migration.md).
