# Model Guide - Compound GPID

<!-- Created 2026-09-02. -->

## The Decision Belongs To The User

Compound GPID does not choose, switch, retry, or constrain the model or
reasoning effort used by a workflow. Commands and agents inherit the selection
provided by the active platform picker or configuration wherever that platform
supports inheritance.

The guidance below is advisory. The available model picker or configuration is
authoritative, examples may be unavailable, and the user decides what to use.
Availability can differ by platform and date. Static documentation cannot prove
runtime availability or identify the hidden model behind Copilot Auto.

## How To Read The Advice

- Start with the capability profile for the process stage.
- Choose an effort level available on the current platform: `low`, `medium`,
  `high`, `xhigh`, or `max`.
- Use the strong option when correctness, tool use, or independent reasoning is
  important.
- Consider the economical option only after successful completion and evidence
  needs are covered, and only when the work is bounded.
- Treat named examples as dated, best-effort references rather than guarantees.
- If no named example is available, use capability-only guidance and the current
  platform selection.

## Process-Stage Guide

| Stage | Capability profile | Strong option | Economical option |
|-------|--------------------|---------------|-------------------|
| Discovery and strategy | Scope assessment, alternatives, project context, and roadmap reasoning | High-effort reasoning-capable selection | Medium-effort selection for bounded exploration |
| Planning | Repository navigation, decomposition, dependency awareness, and test planning | Strong repository-navigation selection with high effort | Balanced selection with medium effort |
| Implementation | Code generation, tool use, test-driven iteration, and narrow diffs | Reliable coding selection with high effort | Balanced selection for bounded changes |
| Review | Independent critical reasoning, evidence checking, risk classification, and adversarial comparison | Independent reasoning-capable selection with high effort | Cross-family review selection when available |
| Fix triage | Finding-specific diagnosis, minimal safe fixes, regression awareness, and status tracking | Code-aware diagnosis selection with high effort | Mechanical selection for narrow fixes |
| Compounding and documentation | Faithful synthesis, provenance preservation, concise explanation, and safe knowledge capture | Faithful synthesis selection with medium effort | Mechanical selection for straightforward records |

The `/cg-plan` to `/cg-work`, `/cg-work` to `/cg-review`,
`/cg-review` to `/cg-fix-triage`, and fix-triage to documentation transitions
use the shared contract at `.github/shared/model-advisory.contract.md`. Those
handoffs emit recommendations only; they do not perform model or effort
routing.

## Named Examples And Provenance

The bundled examples are dated and availability-unverified. They make capability
profiles concrete, not guarantees that a particular account or platform exposes
them. Before using a named example, check the current platform picker or
configuration. If it is absent or its status is unclear, fall back to the
capability profile and choose an available option yourself.

The advisory examples are stored in `.github/shared/model-advisory-examples.json`.
They are data for guidance only and must never become executable prompt or agent
metadata.

## Auto, Unknown, And Cross-Family Review

When Copilot Auto is selected, you must not infer or name the hidden underlying model.
If the generator family is unknown, say that an independent review from another
family could be useful if available, without claiming that a different family
was used. When the family is known, the user may choose a different family for
contrast. No cross-family review is automatic.

## Local Advisory Preferences

Users may keep optional advisory preferences in `compound-gpid.local.md`:

```yaml
model-advisory:
  enabled: true
  examples:
    planning:
      strong: "example-id"
      economical: "example-id"
  preferences:
    effort: "high"
    notes: "Advisory context only."
```

Local values affect advisory wording only. Invalid, stale, or unsupported values
fall through to bundled examples and then capability-only guidance. They do not
change platform configuration or execution.

## Availability And Validation Boundaries

The advisory source order is:

1. Reliable runtime or platform facts observed through a supported mechanism.
2. Valid local advisory preferences.
3. Bundled dated examples with verification and availability labels.
4. Capability-only guidance.

Runtime model availability discovery is intentionally deferred until a supported
platform exposes a reliable mechanism. The context audit validates static
inheritance, advisory schema, provenance, effort vocabulary, user-control
language, and fallback behavior. It does not claim runtime model availability,
provider identity, or successful platform dispatch.

For release validation, run:

```bash
python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both --recommendations
```

Then confirm the platform picker and generated native trees separately. Static
checks and a model response are not substitutes for executed test evidence.