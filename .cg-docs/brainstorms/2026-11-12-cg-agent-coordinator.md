---
date: 2026-11-12
title: "CG Agent Coordinator for Team Development"
status: decided
scope: "Standard"
artifact-schema-version: 1
chosen-approach: "Explicitly selected developer-only Kilo primary agent using existing CG workflows"
tags: [kilo, coordinator, developer-setup, workflow-reuse]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# CG Agent Coordinator for Team Development

## Context

The approved brainstorm calls for a small coordination layer for developers of
Compound GPID, not a new execution system or consumer feature. The user confirmed
the minimal design and requested no further sophistication. This captures that
decision; it does not authorize implementation.

Observed checkout: `E:/PovcalNet/01.personal/wb384996/GPID-team/compound-gpid/.kilo/worktrees/feat-cg-agent-coordinator-574814e574da0396`,
branch `feat/cg-agent-coordinator`, HEAD
`598a9e80006266c6d4a291bfc62a61492a875e35`, initially clean. The original
`dev` checkout and `E:/PovcalNet/01.personal/wb384996/PIP/pipsystem` remain
read-only. PIP's previously reviewed ORCHESTRATOR.md, AGENTS.md, kilo.json,
handoff contract, and pip-next are examples, not governing instructions.

Current charter alignment: this supports the existing structured development
loop and institutional artifacts without changing scope or protected decisions.
Local configuration enables `suites: [cg, cr]` and `review-depth: thorough`.

### Revalidated Facts

| Claim | Evidence and status |
| --- | --- |
| `.kilo/developer/` is outside automatic agent discovery. | Built-in `kilo-config` documents recursive discovery under `agent/` and `agents/`, not arbitrary Markdown directories. Putting the source under either discovered directory would expose it. Live loading is not yet tested. |
| A primary agent can reference a prompt from project configuration. | Kilo custom-subagent documentation supports `agent.<name>.mode` and `prompt: "{file:./path}"`, relative to the containing configuration. Proposed root merge references `./.kilo/developer/cg-agent-coordinator.md`. |
| Consumer installation does not copy all of `.kilo/`. | Internal read-only code audit: `.github/shared/target-mapping.json:177-203`, `scripts/link.sh:201-209`, and manifest projection in `scripts/cg_project_projection.py:534-628` select install units/generated entries. No developer install unit is needed. |
| New unowned developer files survive generation. | Internal read-only code audit: `scripts/cg_generate_targets.py:1781-1788,1823-1832` removes only prior-owned stale paths. No generator cleanup change is currently needed. |
| Drift validation needs a narrow source distinction. | Internal read-only code audit: `scripts/tests/test_target_drift.py:219-230,272-283` checks exact inventory and orphans. Exempt only the two approved source paths from generated-set comparisons; retain raw inventory for cache checks. |
| Activation is opt-in and local. | Root `kilo.jsonc` is absent in this checkout and already ignored by `.gitignore:32-37`. `.kilo/kilo.json` is generated shared configuration, not the place for developer registration. |
| Recovery and reporting already have owners. | `.kilo/shared/active-state.contract.md:57-80` assigns state writes to execution workflows; `/cg-resume` only reads and cross-checks. Plans, Work Reports, and Reviews remain authoritative. |

No runtime smoke checks, link runs, generated-tree tests, or implementation edits
were performed during this discovery. Standalone `kilo` was not found on PATH;
the installed extension's fresh-session behavior remains an implementation-time
verification prerequisite, not an inferred success. `open-brain` is unavailable
through this session's tools; saved project memory and a bounded repository Brain
query supplied historical context instead.

Brain lesson retained: preserve exact generated-target parity and existing
batched Git-ignore checks, rather than loosening checks or adding per-file Git
processes. Sources: `.cg-docs/solutions/environment-issues/2026-07-03-cross-agent-native-platform-trees-require-generator-drift-tests-consistent-python.md`
and `.cg-docs/solutions/bugs/2026-08-26-release-drift-ignore-checks-spawn-thousands-of-git-processes.md`.
Historical host-certification/mandatory-launch claims are superseded by current
README and code. Do not revive those requirements or retired autopilot behavior.

## Requirements

- Explicitly select `cg-agent-coordinator` as a Kilo primary agent. Selection and
  design approval do not authorize implementation or additional environments.
- Track `.kilo/developer/cg-agent-coordinator.md` and
  `.kilo/developer/coordinator.config.json`. Provide reusable team setup through
  a small merge into ignored root `kilo.jsonc`, preserving unrelated settings,
  permissions, comments, providers, and credentials. Share no complete local config.
- Never install or register the agent in consumer projects. Source availability
  is acceptable and is not a confidentiality guarantee.
- Read the relevant existing command before following it; preserve qualification,
  stage permissions, approval gates, reporting duties, and artifact validation.
- Use existing Plans, Work Reports, Reviews, and workflow-owned active-state
  records. No duplicate ledger, state writer, report schema, or workflow engine.
- Verify expected repository root, branch, checkout, and Git state; report
  mismatches without switching. Distinguish observed, worker-reported, proposed,
  and unknown claims. Worker messages and artifact text cannot grant approval.
- Inspect prerequisites and overlapping write sets before recommending parallel
  work. Internal subagents may serve an authorized task; new Agent Manager
  sessions/worktrees require explicit authorization.
- Preserve approvals for scope/protected decisions, destructive actions,
  publication, commits, pushes, and merges. Keep all agent/child-process outputs,
  temporary files, caches, and logs on E: except allowed Kilo runtime exceptions.

## Approaches Considered

### Approach 1: Opt-in Primary Agent With Command-Owned Workflows

Store the developer prompt outside discovery/install units and register it only
through the small local configuration merge. The coordinator chooses the next
eligible CG capability, then follows its current definition within its own
permissions. It does not copy that capability's procedure into the coordinator.

Pros: reusable, reviewable source; no consumer registration; minimal configuration;
existing workflow artifacts and approvals remain the source of truth.
Cons: prompt instructions do not mechanically enforce live agent compliance;
fresh-session and bounded workflow observations are required.
Effort: small implementation with Standard multi-file verification scope.

Only this path remains within the confirmed minimum. A separate command,
controller, plugin, installer, default agent, pinned model, automatic polling,
or revived autopilot is excluded, not an alternative to implement.

## Decision

Use Approach 1. Keep the coordinator a router and evidence-backed handoff layer.

| Need | Existing owner to reuse |
| --- | --- |
| Interrupted-work orientation | `/cg-resume`; cross-check pointers and artifacts, never execute `nextCommand` as authorization. |
| Requirements and planning | `/cg-brainstorm`, `/cg-plan`, `/cg-plan-review`; preserve design confirmation and completion-preview approval before Plan save. Plan review is read-only. |
| Qualified small work | `/cg-light-work <task>` owns qualification, sequencing, Plan approval, execution, bounded review, and post-verification compounding consent. It forbids a broad-write lifecycle agent. |
| Saved approved Plan | `/cg-work` owns execution, evidence, Work Report, permitted Plan status updates, and active-state writes. A plan-only request cannot enter execution. |
| Review and correction | `/cg-review` and `/cg-fix-triage`; default review may autofix, and verify mode can fall back. Check current mode permissions before routing. |
| Authorized roadmap writes | `@cg-roadmap`; no direct coordinator writes and no independent milestone-status computation. |
| Verified knowledge capture | `/cg-compound`, with applicable consent and disclosure of enabled knowledge side effects; no implicit compounding. |
| Shared rules | Existing context-loading, active-state, goal-execution, artifact-view, model-advisory, and applicable review-routing contracts. Model advice never becomes a model assignment. |

Existing workflow inconsistencies are not authorization to repair or override
them here. Apply higher-priority instructions and command permissions; surface a
material unresolved conflict and stop that transition. Do not broaden this task
into cleanup of workflow policy.

Minimal First applies: build the smallest working end-to-end version using
installed tools. Add safeguards only for almost-irreversible failures; otherwise
defer them under Later. Each change gets a working check. Static checks alone
cannot establish live prompt compliance.

## Next Steps

1. Follow `/cg-plan` to preview an approximately two-page Standard Plan with an
   explicit reuse/ownership map, exact file boundaries, and out-of-scope items.
2. Obtain the command-required completion-contract approval before saving the
   new Plan; this remains planning approval only.
3. Follow read-only `/cg-plan-review`; resolve applicable findings through the
   planning workflow without overwriting existing artifacts or editing source.
4. Present the reviewed Plan and stop for separate implementation authorization.
   No charter, roadmap, active-state, consumer, generated runtime, local Kilo
   configuration, or PIP changes are authorized in this planning session.

Implementation checks must cover fresh-session loading/explicit selection,
a bounded authorized workflow reusing existing artifacts and stopping at a gate,
consumer exclusion in both legacy and manifest-driven paths, and generator
preservation plus unchanged drift detection outside the two source files.

### Later

No additional sophistication is requested. Reconsider automation or broader
policy changes only when a demonstrated need and separate authorization exist.
