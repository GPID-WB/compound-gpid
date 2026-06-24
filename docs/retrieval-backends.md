# Retrieval Backend Evaluation

Compound GPID currently uses one active retrieval backend:

- `native-brain-query`: `cg-index query` over generated local Brain artifacts.

This backend is local, deterministic, stdlib-only, budget-aware, and does not
call external services.

## Evaluation Registry

Optional retrieval backend candidates are tracked in
`.github/shared/retrieval-backends.json`. The registry is an evaluation artifact, not runtime configuration. Phase 2.2 does not enable a new backend.

Every optional backend must remain:

- `default_enabled: false`
- `requires_explicit_opt_in: true`
- `status: "evaluate-only"` or `status: "deferred"` until a future roadmap item
  explicitly implements it

## Required Gates

Before any optional backend can move beyond evaluation, it needs:

- explicit opt-in
- privacy review
- offline behavior
- dependency review
- token-budget comparison
- deterministic validation
- rollback plan

External or networked retrieval also requires separate approval for credentials,
data handling, and failure modes. No external retrieval backend is approved by
this registry.

## Current Decision

Keep `native-brain-query` as the only active backend. Future work may evaluate a
local SQLite FTS index, a local embedding index, or an external vector service,
but each candidate must pass the gates above and provide measured evidence
before any token-saving or quality claim is made.
