# Deactivate Workflow

1. Resolve one explicitly selected capability.
2. Remove only that explicit selection from the top-level inline `capabilities` value.
3. Block if selectors or module dependencies still require the capability.
4. Re-resolve the exact manifest and desired projections.
5. Delete only checksum-owned stale projection files through the common held-lock journal.

Modified or user-owned bytes are preserved and block apply.
