---
date: 2026-07-30
title: "User-selected execution with advisory model and effort routing"
status: decided
scope: "Deep"
chosen-approach: "Decoupled advisory router"
tags: [model-routing, model-picker, reasoning-effort, cross-platform, token-efficiency]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# User-Selected Execution with Advisory Model and Effort Routing

## Context

Compound GPID currently assigns specific models to many commands and agents and
propagates that policy through a model catalog, generated platform mappings,
documentation, audits, and tests. This policy is difficult to maintain as model
catalogs change and prevents users from selecting models that may be more
capable for their tasks.

GitHub Copilot cannot reliably let one agent assess a task and then dispatch a
second agent with a dynamically selected model and reasoning effort. Similar
model-routing assumptions also vary across Claude Code, Codex, and OpenCode.
Execution policy should therefore defer to the model selected by the user on
every supported platform.

The prior brainstorm, `.cg-docs/brainstorms/2026-04-07-full-model-audit.md`,
established explicit model assignments. This decision replaces that execution
policy while retaining model selection as optional user guidance.

## Requirements

- Remove model-specific execution assignments from all Compound GPID commands
  and agents on GitHub Copilot, Claude Code, Codex, and OpenCode.
- Remove generated model mappings and validation rules that enforce particular
  models or vendors.
- Ensure commands and agents inherit the model and reasoning configuration
  selected by the user wherever the platform supports inheritance.
- Keep model selection advisory only. Recommendations must never switch models,
  set reasoning effort, or constrain which model the user may select.
- Add recommendations at these initial workflow transitions:
  - `/cg-plan` to implementation.
  - `/cg-work` to review.
  - `/cg-review` to fix triage.
  - `/cg-fix-triage` to compounding or documentation.
- Make capability profiles the durable recommendation format, with exact model
  names included as best-effort examples.
- Resolve model availability through a layered fallback:
  1. Runtime or platform introspection when reliable.
  2. User-maintained local configuration.
  3. Bundled examples with platform, observation date, and an explicit
     availability-unverified label.
  4. Capability-only recommendations.
- Recommend both model capability and reasoning effort. Effort labels may
  include `low`, `medium`, `high`, `xhigh`, and `max` when supported.
- Optimize recommendations first for effective task completion and then for
  token efficiency. Offer more than one option when useful, including a strong
  default and a more economical alternative.
- Treat cross-family review as a primary criterion on platforms such as GitHub
  Copilot and OpenCode. When the current model vendor cannot be detected,
  provide conditional guidance instead of guessing.
- Keep recommendation logic centralized so the four handoffs do not drift.
- Do not assume that the newest models are available. Unverified examples must
  be labeled clearly.

## Approaches Considered

### Approach 1: Capability Guidance Only

Remove all model assignments and mappings, then add generic capability and
effort recommendations to the four handoffs. This minimizes maintenance and
works across platforms, but it provides no concrete model examples or
platform-aware availability guidance.

### Approach 2: Decoupled Advisory Router

Make execution inherit the user's selection while a shared advisory component
recommends capability profiles, reasoning effort, conditional cross-family
review, and optional model examples from layered availability sources. This
preserves user control and useful specificity without coupling execution to a
volatile model catalog. Its trade-off is additional design and testing for the
shared recommendation contract and platform capability sources.

### Approach 3: Live Model Registry

Build platform adapters or an external registry that continually discovers and
ranks current models. This could improve freshness but depends on unstable APIs,
introduces network and trust concerns, and is disproportionate to the immediate
need.

## Decision

Choose **Approach 2: Decoupled Advisory Router**, implemented incrementally.

The first implementation will remove model-specific execution policy, define
shared capability and effort profiles, add advisory output to the four agreed
handoffs, support local configuration and clearly labeled bundled examples,
and provide conditional cross-family review guidance. Runtime introspection is
deferred until a supported platform exposes a reliable discovery mechanism.

This approach delivers user autonomy and reduces model-policy churn while still
helping users choose effective, token-efficient models and reasoning effort for
the next workflow stage.

## Next Steps

1. Inventory every canonical model assignment, mapping, audit, test,
   documentation reference, and generated artifact affected by the policy.
2. Specify one shared advisory contract covering task profiles, effort levels,
   alternatives, availability provenance, cross-family review, and fallback
   behavior.
3. Decide whether the existing model catalog should be removed or replaced by
   a smaller advisory-examples schema with no execution assignments.
4. Update the canonical `.github/` sources and target generator so all platforms
   inherit user selections and no generated target applies model routing.
5. Add advisory recommendations to `/cg-plan`, `/cg-work`, `/cg-review`, and
   `/cg-fix-triage` through the shared contract.
6. Update context audits, Python tests, Pester prompt contracts, model guidance,
   token-audit output, and generated-target parity tests.
7. Regenerate `.claude/`, `.agents/`, and `.opencode/` from the canonical source
   and verify drift, inheritance behavior, and recommendation labeling.
8. Track reliable runtime model introspection as a separate future enhancement.
