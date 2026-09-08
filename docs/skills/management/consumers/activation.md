# Activate and Deactivate Skills

[Activate](../commands/activate.md) adds one explicit capability through a
byte-preserving configuration plan. [Deactivate](../commands/deactivate.md)
removes only an explicit selection; it cannot subtract selector-derived or
dependency-required capabilities.

Both operations re-resolve the manifest, generate selected targets, publish
selected host projections, and verify exact desired paths and managed-bundle
inventories. Modified or user-owned projection files block unsafe deletion.

After apply, use [availability](availability.md) and [audit](../commands/audit.md)
to confirm the final state.
