---
date: 2026-06-23
title: "Snapshot and external-research modes need opt-in gates before implementation"
category: "testing-patterns"
language: "JSON/Python/Markdown"
tags: [snapshot, external-research, opt-in, copyright, privacy, token-efficiency]
root-cause: "Mode registries can be mistaken for runtime configuration unless default-disabled status and external-research gates are tested"
severity: "P2"
plan: ".cg-docs/plans/2026-06-23-snapshot-external-research-modes.md"
---

# Snapshot and External-Research Modes Need Opt-In Gates Before Implementation

## Problem

Snapshot and external-research modes are useful future ideas, but they carry
different risks from local workflow execution: large transcript captures,
copyright-sensitive source copying, network failures, privacy exposure, and
reproducibility gaps.

## Root Cause

Without an explicit registry and tests, a future contributor could add a mode
name or docs note that looks like approval. Agents may then treat the mode as
available even though no runtime implementation or validation exists.

## Solution

Represent candidate modes in `.github/shared/snapshot-research-modes.json`:

- current mode: `local-workflow`
- snapshot candidate: `evaluate-only`, `default_enabled: false`
- external-research candidate: `deferred`, `default_enabled: false`,
  `network_required: true`

Add tests that verify only local workflow mode is enabled and that external
research requires attribution, privacy, copyright-safe summary,
reproducibility, token-budget, and rollback gates.

## Prevention

Do not implement browser automation, web search, external source fetching, or
snapshot capture in the same change that introduces the registry. A future mode
needs its own roadmap item, validation evidence, and explicit user opt-in.

## Related

- `.github/shared/snapshot-research-modes.json`
- `docs/snapshot-external-research.md`
- `.github/shared/retrieval-backends.json`
