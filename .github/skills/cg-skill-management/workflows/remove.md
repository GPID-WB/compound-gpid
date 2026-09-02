# Remove Workflow

1. Require deprecated, inactive state, a valid successor, and immutable plugin
   release or project revision grace evidence.
2. Load only versioned, reviewed migration records. Bind each whole-file edit to
   its exact current SHA-256 digest.
3. Stage migration edits, registry and provenance changes, exact source and
   checksum-owned projection deletions, then rescan the final staged state.
4. Require zero active references. Preserve migration and historical references,
   modified destinations, user-owned files, provenance, and the ID tombstone.
5. Publish all exact bytes through the common lifecycle transaction.
