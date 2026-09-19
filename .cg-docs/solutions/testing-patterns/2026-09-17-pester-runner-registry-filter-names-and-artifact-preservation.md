---
date: 2026-09-17
title: "Pester runs use runner registry filter names and preserved last-run artifacts between jobs"
category: "testing-patterns"
language: "both"
tags: [pester, run-tests, last-run-json, artifact-preservation, runner-registry]
root-cause: "tests/Run-Tests.ps1 filters by registered runner names, not filenames, and every Pester job overwrites tests/last-run.json, so filename-based commands fail and evidence is lost unless preserved before the next job."
severity: "P2"
plan: ".cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md"
---

# Pester Runner Registry Filter Names And Artifact Preservation

## Problem

`tests/Run-Tests.ps1 -File create-release.Tests.ps1` rejected the filename at
the very first phase baseline (2026-09-17). Later phases ran many filtered and
full-suite Pester jobs back to back; without a preservation step, each job
silently overwrote the previous run's `tests/last-run.json`, destroying the
evidence trail the workflow needed.

## Root Cause

The runner registry keys commands by short filter names (for example
`create-release`, `prompt-tools`, `docs-automation`, `docs-preview`), not by
the test filenames. Assumptions that `-File` accepts a filename are wrong.
Additionally, `last-run.json` is a single mutable artifact shared by every
Pester job — the canonical-runner design relies on the caller preserving
copies.

## Solution

The safe-run protocol used throughout the 2026-09-17 phases:

- Every Pester execution goes through `tests\Run-Tests.ps1` — the canonical
  runner — never a raw `Invoke-Pester`. This is constraint C8 of the
  prerelease plan and is asserted separately by `pester-safety.Tests.ps1`.
- Use the registered filter name: `. tests\Run-Tests.ps1 -File create-release`
  (confirmed registry names: `create-release`, `prompt-tools`,
  `docs-automation`, `docs-preview`). No extra flags, no pipeline.
- Read `tests/last-run.json` immediately after each run and return identity
  and counts: gitSha, ranAt, passed, total/passed/failed/skipped,
  `filteredFiles`, failFast, failure summaries, cleanup diagnostics.
- Preserve the artifact (copy the JSON to a dated name) before the next
  Pester job overwrites it. Never run two Pester jobs concurrently — both
  write the same artifact.
- The full-suite boundary gate requires `filteredFiles: null`; the two
  known `update` skips are expected and separate from failures.
- TestDrive cleanup diagnostics (missing/nonempty temporary directories)
  are recorded as a console qualification, never as assertion failures.

## Prevention

- Load `cg-skill-pester-safety` before writing any Pester terminal command;
  it contains the pre-flight checklist for all of the above.
- When a phase needs multiple Pester jobs, sequence them and state the
  preservation step in the runner request ("preserve/read last-run.json
  after each job, never overlap jobs").
- Treat `test/update` skips, quiet deprecation warnings, and undeclared-file
  warnings as known noise unless they change in kind.

## Related

- `.cg-docs/solutions/testing-patterns/2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md`
- `.cg-docs/solutions/testing-patterns/2026-04-17-canonical-run-tests-json-artifact-decouples-test-results-from-agent-context.md`
- `.cg-docs/solutions/testing-patterns/2026-09-17-dedicated-task-runner-substitution-for-execution-subagent.md`
- `.cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md`