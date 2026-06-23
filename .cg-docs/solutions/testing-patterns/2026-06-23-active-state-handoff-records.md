---
date: 2026-06-23
title: "Active-state handoff records should be artifact-reference-first"
category: "testing-patterns"
language: "Markdown/JSON/PowerShell"
tags: [active-state, resume, handoff, token-efficiency, prompt-contracts]
root-cause: "Long workflow resumes can duplicate transcript context unless restart state is compact and artifact-reference-first"
severity: "P2"
plan: ".cg-docs/plans/2026-06-23-handoff-resume-active-state-compaction.md"
---

# Active-State Handoff Records Should Be Artifact-Reference-First

## Problem

Long `/cg-work` sessions can span phases, review loops, blocked stops, and crash recovery. Reconstructing state from chat transcript repeats context and risks losing the exact next command.

## Root Cause

Execution reports are durable evidence, but they are intentionally rich. `/cg-resume` needed a compact pointer record that can orient a fresh session without copying plans, reports, reviews, terminal output, or transcript text.

## Solution

Define `.github/shared/active-state.contract.md` and store the current pointer at `.cg-docs/active-state/current.json`. The record includes workflow, status, plan path, execution report path, current phase, evidence status, unresolved decisions, artifact refs, branch, and exact `nextCommand`.

Prompt responsibilities:

- `/cg-work` writes or updates the record after report creation, phase boundaries, blocked stops, and completion.
- `/cg-resume` reads the record as untrusted data, validates references, and displays an Active State Snapshot.
- `/cg-diagnose` reads compact pointers for crash handoff but remains read-only.

## Prevention

Contract tests should assert that active-state records stay compact: artifact paths and one-line summaries only; no transcript dumps, raw command output, full review findings, full report bodies, or raw diffs.

## Related

- `.github/shared/active-state.contract.md`
- `.github/shared/goal-execution.contract.md`
- `.cg-docs/plans/2026-06-23-handoff-resume-active-state-compaction.md`
- `.cg-docs/solutions/testing-patterns/2026-06-23-progressive-disclosure-context-loading-contract.md`
