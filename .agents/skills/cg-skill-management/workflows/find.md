# Find Workflow

1. Resolve the validated canonical registry and active-manifest health.
2. Build canonical-only catalog rows through the catalog service.
3. Apply identifier, capability, suite, platform, availability, cost, owner,
   and provenance filters in deterministic order.
4. Label missing or stale state as prospective and include exact regeneration
   remediation. Do not claim active or projected state without a fresh manifest.
5. Return the common result envelope without writing files.
