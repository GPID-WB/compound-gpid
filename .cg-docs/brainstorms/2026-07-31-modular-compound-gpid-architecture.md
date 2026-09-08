---
date: 2026-07-31
title: "Modular Compound GPID architecture for technical and research suites"
status: decided
scope: "Deep"
chosen-approach: "Layered registry over the canonical .github tree"
tags: [architecture, modularity, compound-research, technical-suite, capability-packs, routing, packaging, migration]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Modular Compound GPID Architecture for Technical and Research Suites

## Context

Compound GPID currently combines product infrastructure, reusable technical
knowledge, and user-facing technical workflows under the `cg-*` namespace. The
`origin/feat/compound-research-v2` branch adds a substantial research suite
under `cr-*`: 11 research agents, 5 research prompts, 14 research skills, 2 new
instruction domains, and integrations with existing CG workflows and shared
contracts. Relative to `main`, the branch changes 305 files, including generated
Claude Code, Codex, and OpenCode targets.

A May 2026 brainstorm had already chosen a single-repository module system with
`shared`, `engineering`, and `research` tags. This session deliberately reopened
that decision. The newer branch demonstrates that the research behavior is
valuable, but it also exposes incomplete architectural boundaries. For example,
the canonical target generator still discovers skills through a hard-coded
`.github/skills/cg-skill-*` glob even though the branch contains generated
`cr-skill-*` trees.

The revamp's primary goal is maintainability: core maintainers must be able to
improve a shared capability or one suite without silently breaking another.
User experience may involve a modest learning curve if the manual and help
system make suite selection and composition clear.

## Requirements

### Product and Governance

- Keep a single repository, a single installation path, and one product version
  and release train.
- Optimize for core maintainers. A public third-party plugin API and marketplace
  are not required in this revamp.
- Preserve stable user workflows, especially `/cg-*`, the compound lifecycle,
  `.cg-docs/`, and installation behavior.
- Permit a versioned, automated migration of project configuration and internal
  manifests.
- Treat the research branch as a behavioral specification: preserve validated
  research capabilities, task taxonomy, and research-integrity safeguards while
  refactoring ownership and orchestration.

### User-Facing Suites

- Keep explicit suite commands rather than relying on an opaque universal
  router.
- Retain `cg-*` as the general technical suite and `cr-*` as the research and
  analytical suite.
- Let a suite compose reusable capabilities automatically. Users should not
  need to know dependency names.
- Support soft project preferences such as technical-only or
  technical-plus-research. Preferences shape setup, help, recommendations, and
  default guidance; every explicitly invoked installed command remains usable.
- Make the CG-versus-CR choice understandable through concise help, examples,
  and task-oriented documentation.

### Architecture and Safety

- Separate the product into three layers: a small platform kernel, reusable
  capability packs, and user-facing suites.
- Give every canonical prompt, agent, skill, instruction, and shared contract
  exactly one declared owner.
- Prevent direct suite-to-suite dependencies. Both CG and CR must consume
  reusable implementation knowledge through capability packs.
- Keep `.github/` as the canonical runtime source in the first revamp. Continue
  generating committed native platform trees from it.
- Make canonical asset discovery namespace-agnostic. Adding a registered suite
  or capability must not require another hard-coded prefix branch in the
  generator.
- Validate ownership, dependency closure, acyclic dependencies, forbidden
  cross-suite references, generated-target parity, and compatibility in CI.
- Treat context size as an architecture constraint. Inactive suites may be
  installed, but their domain instructions and skills must not be loaded into
  routine sessions by default.

### Scope and Risk Priorities

- Deliver the architecture foundation and migrate the technical and research
  suites in the first revamp.
- Design for future writing, presentation, dashboard, and application suites,
  but do not implement them in this iteration.
- Prevent these failure modes most aggressively:
  1. A shared change silently breaks a suite.
  2. Additional modules inflate routine context and instruction load.
  3. Users cannot tell which suite should own a task.

## Approaches Considered

### Approach 1: Layered Registry Over the Canonical Tree

Keep `.github/` canonical and introduce a validated architecture registry for
three layers:

1. **Kernel**: configuration and schema migration, lifecycle contracts, context
   loading, active state, Knowledge Brain and roadmap integration, model and
   review routing contracts, canonical generation, installation, release, and
   architecture validation.
2. **Capability packs**: reusable implementation knowledge such as language
   support, testing, reproducibility, data quality, visualization, and
   publication-output primitives.
3. **Suites**: user-facing intent and orchestration. The technical suite owns
   `cg-*`; the research suite owns `cr-*` and its domain-specific integrity,
   identification, measurement, econometric, and academic-writing behavior.

Suite manifests declare required capabilities. Capabilities may depend on the
kernel and, where justified, other capabilities, but never on a suite. A suite
may not depend directly on another suite. Registry validation and contract tests
turn these rules into release gates.

**Pros**:

- Enforces ownership and dependency boundaries without replacing the current
  canonical runtime and packaging model.
- Lets shared improvements reach both suites through explicit capability packs.
- Supports incremental migration and rollback.
- Keeps one release compatibility matrix.
- Provides most of the isolation value of physical packages at lower cost.

**Cons**:

- Boundaries are logical rather than visible as top-level source directories.
- The registry, dependency validator, and compatibility tests become
  load-bearing infrastructure.
- Capability granularity and neutral internal naming require careful design.

**Effort**: Large.

### Approach 2: Physically Modular Source Packages

Move canonical content into source packages such as `packages/kernel/`,
`packages/capabilities/testing/`, `packages/suites/technical/`, and
`packages/suites/research/`. Generate `.github/` and all native platform trees
from those packages.

**Pros**:

- Makes ownership and module contents immediately visible in the filesystem.
- Gives future modules a clean package template.
- Allows directory boundaries to reinforce dependency rules.

**Cons**:

- Makes `.github/` a second generated layer and replaces a recently hardened
  canonical-to-native packaging model.
- Requires broad changes to paths, references, tests, adapters, install logic,
  and contributor workflows.
- Greatly increases migration, rollback, and generated-drift risk.
- Is disproportionate while only two suites need migration.

**Effort**: Very large.

### Approach 3: Parallel Suites With a Broad Shared Bucket

Complete the branch's existing `shared | engineering | research` tagging model,
keep parallel CG and CR commands, and allow CR workflows to reuse CG-owned
agents and skills directly.

**Pros**:

- Closest to the current research branch.
- Fastest route to shipping the research suite.
- Requires the least immediate restructuring.

**Cons**:

- Encourages a growing, weakly defined `shared` bucket.
- Leaves CR coupled to technical-suite ownership.
- Does not make dependency closure or ownership reliably enforceable.
- Scales through conditionals as new suites appear.
- Does not adequately prevent shared changes from breaking a suite.

**Effort**: Medium.

## Decision

Choose **Approach 1: Layered Registry Over the Canonical Tree**.

This approach best satisfies the maintainability goal. It preserves the
recently established `.github/` canonical-source model and the stable `/cg-*`
surface while adding enforceable ownership and dependency boundaries. It also
allows research workflows to use coding, testing, visualization, and
reproducibility capabilities without making the research suite depend on the
technical suite.

Approach 3 may be used only as a temporary migration state while assets are
classified. Approach 2 remains a possible later evolution if the logical
registry proves difficult to maintain, but physical relocation is not justified
in the first revamp.

### Target Dependency Rules

1. Kernel code and contracts do not depend on capability packs or suites.
2. Capability packs may depend on the kernel and declared capability packs.
3. Suites may depend on the kernel and declared capability packs.
4. Suites do not depend on other suites.
5. Every asset has one owner, and every runtime reference resolves through the
   declared dependency graph.
6. Platform adapters and generated targets are projections of the same
   canonical registry, not separate module implementations.

### Compatibility Position

- Existing `/cg-*` commands remain the technical suite's stable interface.
- Existing `.cg-docs/` artifacts and the compound lifecycle remain shared
  product infrastructure.
- CR behavior is preserved while its direct dependencies on CG-owned behavior
  are replaced with capability-pack dependencies.
- Existing shared `cg-skill-*` identifiers may require compatibility aliases if
  neutral capability identifiers are introduced. The exact naming and
  deprecation policy belongs in the implementation plan.
- Project module configuration may move to a new schema, but migration must be
  automated, idempotent, and backward compatible for a defined transition
  period.

## Next Steps

1. Use `/cg-plan` to produce a phased, Deep-scope implementation plan on
   `refactor/modular-compound-gpid`.
2. Inventory every canonical asset and classify it as kernel, capability-pack,
   technical-suite, or research-suite content. Record ambiguous ownership for
   explicit resolution rather than defaulting it to `shared`.
3. Define the minimal registry schema, capability granularity, neutral internal
   identifiers, compatibility aliases, and dependency validation rules.
4. Add characterization tests for current CG workflows and selected CR branch
   behavior before moving or refactoring orchestration.
5. Make canonical generation prefix-agnostic and prove complete CG/CR parity
   across Copilot, Claude Code, Codex, and OpenCode.
6. Migrate main's assets first, then import CR intellectual content by suite and
   capability instead of merging the research branch wholesale.
7. Prove one mixed `/cr-work` path can use research reasoning, R or Python
   implementation, testing, reproducibility, and publication output without a
   direct dependency on the technical suite.
8. Add a compatibility matrix covering CG-only preferences, CR-only
   preferences, mixed projects, legacy configuration, generated-target drift,
   and context-budget limits.
9. Write a task-oriented manual that explains suite selection, capability
   composition, module preferences, extension rules for maintainers, and
   migration from the current package.
10. Update the project charter only after approving the corresponding expansion
    of Key Deliverables and Current Focus.

### Planning Questions Still Open

- Where should the registry live, and should ownership be centralized,
  distributed in per-pack manifests, or represented by a validated combination?
- What is the smallest useful capability-pack granularity without creating a
  dependency graph that is harder to maintain than the current shared layer?
- Which currently `cg-*` skills are genuinely technical-suite assets, and which
  are neutral capabilities that need aliases or eventual renaming?
- Which CR branch tests and artifacts form the minimum behavioral baseline for
  migration?
- What measurable context budget should CG-only, CR-only, and mixed sessions
  satisfy?