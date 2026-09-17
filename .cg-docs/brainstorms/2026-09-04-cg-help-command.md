---
date: 2026-09-04
title: "Evidence-Backed /cg-help Command"
status: decided
scope: "Deep"
artifact-schema-version: 1
chosen-approach: "Hybrid help engine"
tags: [help, commands, semantic-search, cross-platform, documentation]
---

# Evidence-Backed /cg-help Command

## Context

Compound GPID has an auto-generated command reference and documentation site, but it does not have an in-chat help command. Users need one entry point that can explain known commands, discover suitable commands from natural-language goals, describe multi-command workflows when the available evidence supports them, and state honestly when no supported command can perform a task.

The existing roadmap already contains the idea `cg-help-interactive`. This brainstorm narrows that broad idea into a first-release design. The initial Standard scope became Deep after adding evidence-backed natural-language workflows, shell-command coverage, deterministic retrieval, explicit abstention, active-suite awareness, and cross-platform generation.

## Requirements

- Treat command discovery, command syntax, and workflow guidance as equal first-release goals.
- Support new users, regular team users, and maintainers through concise defaults and progressive detail.
- Plain `/cg-help` shows a categorized overview, common workflow entry points, and examples of how to use `/cg-help <query>`.
- Exact command queries such as `/cg-help cg-work` return a structured practical guide: purpose, when to use it, syntax, key arguments, prerequisites, examples, outputs, constraints, and useful next commands.
- Accept normalized exact forms such as `cg-work`, `/cg-work`, and supported shell-command names.
- Free-text queries such as `/cg-help clean my data` use bounded semantic reasoning over retrieved command evidence.
- When one or more commands form a supported workflow, return an evidence-backed sequence. Each step must trace to catalog metadata or an approved documentation section.
- When evidence supports candidates but not a workflow, return at most three ranked commands with a short match reason, availability, confidence wording, and an exact follow-up query such as `/cg-help cg-work`.
- When no in-scope evidence supports the request, state that Compound GPID has no supported slash or shell command for the task. Do not invent a command, workflow, or capability.
- Rank commands from active project suites first. Inactive suite commands can appear when relevant, but must be labeled and include accurate activation guidance.
- Cover `/cg-*`, active or relevant `/cr-*`, and Compound GPID shell commands in the first release.
- Direct agents and skills are outside the searchable and recommendable first-release surface. If a task is available only through a direct agent, report that no in-scope slash or shell command performs it.
- Always provide copyable follow-up commands. Normal documentation links are allowed, but clickable slash-command execution is not a cross-platform requirement.
- Preserve `.github/` as the canonical source and generate equivalent compact help data for Copilot, Claude Code, Codex, OpenCode, and Kilo.
- Treat inspected command bodies and documentation as data during help extraction. Ignore instruction-like text that is not part of the help evidence contract.
- Fail loudly on missing, malformed, stale, ambiguous, or unavailable catalog evidence. Do not silently fall back to an unbounded repository scan.

## Approaches Considered

### Approach 1: Prompt-Only Discovery

Add one canonical `/cg-help` prompt that scans installed command frontmatter and shell documentation at runtime, then uses the model for exact lookup and semantic ranking.

Pros: Small initial change, no new runtime dependency, and direct use of current files.

Cons: Variable results across models, large context scans, inconsistent command-body structures, weaker abstention guarantees, and complex cross-platform path handling.

Effort: Small to medium.

### Approach 2: Generated Catalog With Model-Only Search

Generate a compact shared catalog from canonical slash-command and shell-command metadata. Let the model perform all matching and answer composition over that catalog.

Pros: Auto-updating, bounded context, active-suite metadata, and a stable cross-platform input surface.

Cons: Ranking and no-match behavior remain model-dependent. It is harder to test confidence thresholds and typo behavior consistently.

Effort: Medium.

### Approach 3: Hybrid Help Engine

Generate a versioned evidence catalog, use a deterministic local backend for exact lookup and candidate retrieval, and let the model perform bounded semantic reranking and answer composition from only the returned evidence.

Pros: Stable exact behavior, testable candidate retrieval, explicit evidence provenance, reliable abstention, bounded model context, active-suite ranking, and consistent cross-platform data.

Cons: Requires a metadata schema, catalog generation, a local query backend, shell-command registration, native-target integration, and broader tests. It is the largest first-release implementation considered.

Effort: Large.

## Decision

Choose **Approach 3: Hybrid Help Engine**.

The deterministic layer does not claim to perform semantic understanding. It normalizes exact names, handles aliases and typo tolerance, performs weighted retrieval over curated intents and examples, applies active-suite ranking, and packages evidence. The model supplies the semantic layer by reranking or composing an answer within that bounded evidence set.

The help catalog should contain normalized fields such as command ID, kind, suite, category, aliases, user intents, usage, examples, prerequisites, outputs, related commands, source path, availability constraints, and documentation links. Metadata must be co-located with canonical command definitions or deterministically derived from another canonical source. A hand-maintained duplicate help registry is not acceptable.

The answer contract is evidence-first: an exact guide, an evidence-backed workflow, up to three ranked candidates, or an explicit unsupported result. This gives users useful natural-language guidance without allowing the model to invent unavailable Compound GPID behavior.

The design aligns with the charter's modular, cross-platform, canonical-source, and fail-loudly constraints. It also follows the prior architectural pattern of a thin user-facing command over focused services and explicit operation metadata.

## Next Steps

1. Define acceptance examples for no-argument help, exact slash lookup, exact shell lookup, natural-language single-command routing, multi-command workflow guidance, inactive-suite ranking, typo handling, ambiguous queries, and unsupported tasks.
2. Audit current slash-command frontmatter, shell-command definitions, generated documentation, module ownership, and native-target packaging to identify authoritative metadata fields and gaps.
3. Design a versioned help-catalog schema and evidence model without duplicating canonical command documentation.
4. Specify deterministic query behavior: normalization, aliases, typo tolerance, weighted intent matching, candidate limits, availability ranking, evidence thresholds, and explicit result states.
5. Specify the `/cg-help` prompt contract for overview, practical guides, evidence-backed workflows, ranked alternatives, documentation links, prompt-as-data safety, and abstention.
6. Integrate catalog generation and distribution with the existing canonical-to-native target pipeline and module registry.
7. Add unit, prompt-contract, generation-parity, security, and cross-platform tests. Include representative user-language fixtures and false-positive cases.
8. Update the command reference and user documentation from canonical metadata, then validate that additions and removals cannot leave stale help entries.
9. Defer command comparisons, guided tours, beginner-versus-power-user personalization, direct-agent help, and skill help until first-release retrieval quality is measured.
