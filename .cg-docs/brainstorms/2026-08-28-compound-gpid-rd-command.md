---
date: 2026-08-28
title: "Rename repository review command and add registry management flags"
status: decided
scope: "Standard"
artifact-schema-version: 1
chosen-approach: "Prompt orchestrator plus deterministic registry utility"
tags: [competitive-analysis, command-design, registry, github, developer-workflow]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Rename Repository Review Command and Add Registry Management Flags

## Context

The existing developer-only `/cg-review-repos` command performs full and delta
reviews of external GitHub repositories. It stores repository state in
`.cg-docs/competitive-reviews/repos.json` and produces implementation-ready
feature cards for Compound GPID maintainers.

The command name should change to `/cg-compound-gpid-rd`, where `rd` means
research-development. Maintainers also need safe command flags to add and remove
repositories without editing `repos.json` manually. This extends the decision in
`.cg-docs/brainstorms/2026-04-21-competitive-repo-review-system.md`; it does not
replace the registry-file and review-prompt architecture.

## Requirements

### Purpose and Users

- Keep the command focused on research of external GitHub repositories for ideas
  that can improve the Compound GPID plugin.
- Keep the command developer-only. It must retain the current guardrail that
  blocks use outside the Compound GPID development repository.
- Describe the repository-only scope clearly because the `rd` name could imply a
  broader research and development system.

### Rename

- Rename `/cg-review-repos` to `/cg-compound-gpid-rd`.
- Remove the old command completely. Do not provide a temporary or permanent
  compatibility alias.
- Rename the canonical prompt and update all live command references, command
  inventories, documentation, tests, audit inputs, and generated platform
  targets.
- Regenerate native platform targets from the canonical `.github/` source. Do not
  edit generated targets as independent sources.
- Keep historical brainstorms, plans, reviews, and solutions unchanged when they
  refer to `/cg-review-repos`.

### Command Modes

The renamed command has four mutually exclusive modes:

1. No mode flag: run the existing delta review.
2. `--full`: run the existing full assessment.
3. `--add <URL>`: add one public GitHub repository to the registry.
4. `--remove <id>`: remove one repository from the registry.

Mode flags must not be combined. Missing values, duplicate mode flags,
unrecognized flags, and conflicting modes must stop with an explicit error. The
current behavior that warns about an unknown flag and continues in delta mode is
not safe for registry mutations and must be removed.

### Add Behavior

- Accept only a public repository URL shaped as
  `https://github.com/<owner>/<repo>`.
- Permit and normalize an optional trailing slash or `.git` suffix.
- Reject non-HTTPS URLs, non-GitHub hosts, credentials, query strings, fragments,
  extra path segments, and malformed owner or repository names.
- Verify that the public repository is accessible before writing the entry. Do
  not analyze features or start a full review in the add invocation.
- Derive `releasesUrl` as `<normalized-url>/releases`.
- Derive a valid, stable `id` from the repository name. If that ID belongs to a
  different URL, derive an owner-qualified ID. Stop if a unique valid ID cannot
  be produced within the registry's 50-character limit.
- Derive a 1-10 character alphanumeric `shortName` from the repository name. Use
  a deterministic suffix when needed to avoid a collision.
- Show the normalized URL and derived fields before the write summary.
- Add the entry with `lastReviewedRelease: null` and no completed-review date.
- If the normalized URL is already registered, stop with an explicit message
  that includes its existing ID. Do not create a duplicate or silently succeed.
- After a successful add, instruct the maintainer to run
  `/cg-compound-gpid-rd --full` to establish the baseline.
- Adding must work when the registry contains an empty `repos` array.

### Remove Behavior

- Resolve the exact, case-sensitive registry `id`.
- If the ID does not exist, stop without changing the file and show the available
  IDs.
- Show the matching ID and URL and require explicit confirmation before mutation.
- Remove only the matching registry entry.
- Preserve all existing assessment and delta-review files as historical records.
- Preserve all root fields, unknown fields, and all fields on remaining entries.
- Removing the final entry is valid. Later review modes must fail clearly and
  instruct the maintainer to use `--add`.

### Deterministic Registry Utility

- Keep web research, feature extraction, and review-file production in the
  renamed prompt.
- Put registry parsing, schema checks, URL normalization, field derivation,
  duplicate checks, removal validation, and JSON writes in a small deterministic
  utility.
- Use a non-interactive confirmation token for removal after the prompt receives
  the maintainer's confirmation. The utility must reject removal when the token
  does not exactly match the requested ID.
- Write `repos.json` atomically through a temporary file in the same directory,
  then replace the original only after complete validation and serialization.
- Preserve unknown registry fields during add and remove operations.
- Fail before mutation if the registry is missing, malformed, has the wrong
  schema version, or fails existing entry validation.
- Do not migrate the schema and do not create a general command framework in this
  iteration.

### Tests and Documentation

- Test normal add and remove flows, URL normalization, duplicate URLs, ID and
  short-name collisions, malformed URLs, missing IDs, rejected confirmation,
  malformed registries, empty registries, and atomic no-change behavior after
  failures.
- Replace the current test that requires exactly three registry entries. Dynamic
  add and remove behavior makes a fixed repository-count sentinel invalid.
- Test mutually exclusive mode parsing and all hard-stop cases in the prompt.
- Test that the old canonical and generated command files are absent and the new
  command files are present.
- Update current user and developer documentation to use the new command and
  explain `--full`, delta, `--add`, and `--remove` modes.

### Out of Scope

- Research sources other than public GitHub repositories.
- Private repository authentication.
- Automatic baseline review during `--add`.
- Deleting historical review files during `--remove`.
- A compatibility alias for `/cg-review-repos`.
- A registry schema migration or a general R&D source framework.
- Automatic roadmap insertion for newly added repositories.

## Approaches Considered

### Approach 1: Prompt-Only Registry Management

Rename the prompt and put URL parsing, ID derivation, collision handling,
confirmation, and JSON mutation instructions directly in it.

**Pros**: Smallest implementation and no new utility.

**Cons**: Persistent mutations remain model-dependent, edge cases are harder to
test, and the already large prompt becomes larger.

**Effort**: Medium.

### Approach 2: Prompt Orchestrator Plus Deterministic Registry Utility

Keep repository research in the renamed prompt and route add and remove
operations through a small tested utility.

**Pros**: Deterministic validation, safe atomic writes, clear collision rules,
focused tests, and less mutation logic in the prompt.

**Cons**: Adds a utility and a new test surface. The prompt must verify that the
utility is available before it requests a mutation.

**Effort**: Medium.

### Approach 3: General R&D Source-Management Framework

Replace the repository registry with a generalized source registry for GitHub
repositories, documents, feeds, and later research inputs.

**Pros**: Supports broader R&D sources in the future.

**Cons**: Exceeds the repository-only need, requires a schema migration, and adds
complexity without current value.

**Effort**: Large.

## Decision

Choose **Approach 2: Prompt orchestrator plus deterministic registry utility**.

The utility must remain narrow. It manages registry state only; it does not fetch
release content, produce feature cards, or perform reviews. This boundary gives
maintainers reliable add and remove operations while preserving the established
prompt-based research workflow.

The approach addresses the main risk of manual JSON editing and aligns with the
project constraint to fail loudly rather than continue after invalid input. The
extra utility is proportional because the command changes persistent tracked
state, but a broader source framework is not justified.

## Next Steps

1. Use `/cg-plan` to map all live rename references and generated targets before
   implementation.
2. Define the utility's exact command-line contract, derivation algorithm,
   confirmation token, exit codes, and atomic-write behavior.
3. Rename the canonical prompt and replace its mode-detection section with the
   four mutually exclusive modes and hard-stop rules.
4. Implement the narrow registry utility without external runtime dependencies.
5. Add utility tests and update prompt, registry, generation, documentation, and
   audit tests.
6. Regenerate all native platform trees from `.github/` and verify that no live
   `/cg-review-repos` references or old generated command files remain.
7. Run targeted tests under the project's Pester safety rules, plus the relevant
   non-Pester utility tests.
