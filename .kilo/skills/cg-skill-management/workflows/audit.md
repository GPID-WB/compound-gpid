# Audit Workflow

1. Load the complete validated canonical and project snapshots without writing.
2. Run common validation for provenance, selectors, lifecycle, manifest health,
   desired targets, projection containment, and operation completeness.
3. If reference audit is selected, scan active, migration, and historical roots
   once and return deterministic source-neutral reference records.
4. Never query mutable remote state or discover updates. Exact candidate
   comparison remains part of `update <id> <new-full-sha>` only.
