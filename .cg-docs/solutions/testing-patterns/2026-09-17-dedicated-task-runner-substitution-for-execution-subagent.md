---
date: 2026-09-17
title: "Dedicated task-runner substitution keeps executed evidence flowing when execution_subagent is unavailable"
category: "testing-patterns"
language: "both"
tags: [task-runner, execution-subagent, run-tests, pester, evidence-handoff, release-automation]
root-cause: "Long release-automation sessions require executed test evidence, but the editor-provided execution_subagent was unavailable in the active tool surface, so evidence could only come from a separately approved dedicated runner subagent."
severity: "P2"
plan: ".cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md"
---

# Dedicated Task-Runner Substitution For execution_subagent

## Problem

During the 2026-09-17 prerelease-automation phases, the implementation thread
had neither `execution_subagent` nor a nested task tool. Every Pester and
Python evidence gate had to be executed elsewhere, and the evidence had to
reach the implementation thread without being fabricated, summarized out of
existence, or treated as a waiver.

## Root Cause

The documented Pester safety rules and the canonical-runner JSON pattern
assume an `execution_subagent` surface. When that surface is unavailable,
there is no default protocol for "run these exact commands and return the
evidence" — the agent can stall, or worse, accept prior results as current
evidence.

## Solution

The user explicitly approved a dedicated `task` subagent in place of the
unavailable `execution_subagent`. The parent dispatches a `RUNNER_REQUEST`
with the exact commands and no latitude, and the runner returns only executed
evidence:

- Pester safety is loaded before any command; only `tests\Run-Tests.ps1`
  (or its `. tests\...` invocation form) is used, with no extra flags and no
  pipeline.
- The runner reads `tests/last-run.json` and returns identity (gitSha,
  ranAt), counts (total/passed/failed/skipped), `filteredFiles`,
  `failFast`, failure summaries, and cleanup diagnostics.
- Runner registry filter names are used (`-File create-release`), never
  filenames stirred with assumptions.
- Two Pester jobs are never overlapped because both write the same artifact.
- The runner preserves each artifact (copy of `tests/last-run.json`) before
  the next Pester job overwrites it.
- No elevation, no global configuration change, no Git mutation, no live
  release command, and no evidence waiver are authorized in the handoff.
- The implementation thread resumes only on the returned evidence; the
  parent owns review dispatch and ledger capture.

The same pattern carried review requests: `REVIEW_REQUEST` to an independent
reviewer with the exact review ledger and focus list, returning finding
statuses rather than fixes.

## Prevention

- Record the approved substitution at the start of the phase (deviation
  record), including the rule that substitution never waives test evidence.
- Always frame red baselines before production implementation: the runner
  returns the failing baseline, then implementation starts.
- Keep handoffs exact: command lists, artifact read order, and "do not
  advance to the next phase" boundaries are written into the request.
- Distinguish focused evidence (filtered runs, per-suite artifacts) from the
  full-suite boundary gate (`filteredFiles: null` required), and preserve
  both kinds explicitly.
- Never accept parent-recounted numbers without artifact identity; the
  implementation thread re-reads `tests/last-run.json` when possible and
  confirms identity and counts against the runner evidence.

## Related

- `.cg-docs/solutions/testing-patterns/2026-09-17-pester-runner-registry-filter-names-and-artifact-preservation.md`
- `.cg-docs/solutions/testing-patterns/2026-04-17-canonical-run-tests-json-artifact-decouples-test-results-from-agent-context.md`
- `.cg-docs/solutions/testing-patterns/2026-04-15-pester-verbose-output-floods-context-long-session.md`
- `.cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md`