---
date: 2026-08-02
title: "Use GPT-5.6 Luna for /cr-work"
status: decided
scope: "Lightweight"
chosen-approach: "Dedicated research-execution role (Approach 2)"
tags: [compound-research, cr-work, model-governance, gpt-5-6-luna, native-targets]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Use GPT-5.6 Luna for /cr-work

## Context

The `/cr-work` command implements research plans for the Compound Research module, but its canonical prompt currently selects `GPT-5.3-Codex`, a model optimized for coding tasks. World Bank researchers, economists, and developers implementing research plans would benefit from a research-oriented model with better token efficiency. The canonical prompt also has no corresponding assignment in the shared model catalog, so generated native command projections do not consistently carry its model choice.

The requested change applies only to `/cr-work`. No other agent or model assignment should change.

## Requirements

- Set the canonical `/cr-work` prompt to `GPT-5.6 Luna`.
- Incorporate the assignment across the plugin's relevant governance and generated-target surfaces.
- Add the model and its support/validation status to the shared model catalog.
- Assign a dedicated `research-execution` role only to `/cr-work`.
- Map that role to `GPT-5.6 Luna` for Codex-native output and the existing Claude Sonnet tier for Claude-native output. OpenCode remains inherited because its target is role-only.
- Regenerate native projections and update focused tests so the canonical assignment, catalog entry, role mappings, and generated `/cr-work` outputs remain synchronized.
- Validate the exact `GPT-5.6 Luna` label in GitHub Copilot where practical, without requiring interactive validation of every platform.
- If Luna is unavailable, emit a validation or generation warning and use the existing Claude Sonnet 4.6 fallback mapping where the target supports it.
- Do not change `/cr-review`, global model defaults, the runtime fallback architecture, or any model assignment outside `/cr-work`.

## Approaches Considered

### Approach 1: Canonical prompt assignment only

Set `model: GPT-5.6 Luna` in the canonical prompt, record the preference in the catalog, and regenerate existing outputs.

- Pros: smallest implementation.
- Cons: native targets are role-based and would not reliably receive the exact model; this does not fully incorporate the change across the plugin.
- Effort: small.

### Approach 2: Dedicated `research-execution` role (CHOSEN)

Give only `/cr-work` a new catalog role, map that role per native target, and regenerate the committed projections.

- Pros: uses the existing role-based generator, keeps all other assignments unchanged, provides an auditable command-specific mapping, and supports target-appropriate fallbacks.
- Cons: requires catalog, target-mapping, generated-output, and focused-test updates; GitHub Copilot static frontmatter cannot perform a runtime fallback.
- Effort: medium.

### Approach 3: Per-command platform override

Extend the catalog and generator with explicit per-target model and fallback fields for `/cr-work`.

- Pros: most precise representation of command-specific cross-platform behavior.
- Cons: expands shared generation logic for one command and increases regression surface; runtime fallback would still be unavailable without a separate engine.
- Effort: medium-to-large.

## Decision

Use **Approach 2: Dedicated `research-execution` role**. It delivers the requested command-specific model change across canonical and generated plugin surfaces while preserving every other agent and model assignment. The existing role-based generator already supports target-specific mappings, so a new role is more proportionate than introducing per-command override machinery.

The fallback contract is limited by the platform: validation or generation should warn when `GPT-5.6 Luna` is unavailable, and Claude-native output may use the catalog's existing Sonnet mapping. GitHub Copilot cannot guarantee a runtime warning-then-fallback path from static prompt frontmatter, and adding a runtime fallback engine is out of scope.

## Next Steps

1. Add the exact `GPT-5.6 Luna` model assignment to `.github/prompts/cr-work.prompt.md`.
2. Add the model metadata and a `research-execution` assignment for `/cr-work` to `.github/shared/model-catalog.json`.
3. Add only the new role's target mappings to `.github/shared/target-mapping.json`, preserving all existing mappings.
4. Regenerate the committed `.agents/`, `.claude/`, and `.opencode/` projections and their manifests.
5. Add focused tests for the canonical model, catalog assignment, target mappings, generated command projections, and non-regression of other assignments.
6. Validate the model label and generator output, then run the relevant single-file test checks.
