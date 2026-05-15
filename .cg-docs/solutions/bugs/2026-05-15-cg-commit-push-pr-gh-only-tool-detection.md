---
date: 2026-05-15
title: "cg-commit-push-pr skipped PR creation when gh not found — VS Code extension never tried"
category: "bugs"
type: "bug"
language: "both"
tags: [cg-commit-push-pr, gh, vscode-extension, pr-creation, tool-detection, fallback, github-pull-request]
root-cause: "Step 1.5 only detected gh CLI; Step 6 skipped entirely when gh was absent, ignoring the VS Code GitHub Pull Request extension"
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
---

# cg-commit-push-pr skipped PR creation when gh not found — VS Code extension never tried

## Symptom

When `gh` CLI was not installed, `/cg-commit-push-pr` set `$ghAvailable = false`, skipped Step 6
entirely, and dumped a manual `gh pr create` command in the handoff — even though the VS Code
GitHub Pull Request extension was installed and fully capable of creating the PR. Users got a
degraded experience with no actionable path to fix it for future runs.

## Root Cause

Step 1.5 used a single boolean (`$ghAvailable`) based solely on `gh` CLI presence. Step 6 was
guarded by `*(Skip this step if $ghAvailable is false)*`. No other tool was checked. The VS Code
GitHub Pull Request extension (`github-pull-request_create_pull_request` tool) was never
considered, despite being the mechanism used for all PR creation in this workspace.

The handoff message for the "no gh" case also gave no next-time setup instructions — it only
listed the manual command again, which still requires `gh`.

## Reproduction Test

Added to `tests/prompt-tools.Tests.ps1` in the `cg-commit-push-pr.prompt.md - structure`
Describe block:

```powershell
It "falls back to VS Code GitHub Pull Request extension when gh CLI is not found" {
    ($content -match 'GitHub Pull Request.*extension|vscode.*github|github-pull-request_create|VS Code.*extension.*PR|extension.*PR.*creation') | Should -Be $true
}

It "gives actionable next-time setup instructions when no PR tool is available" {
    ($content -match 'next.time|to enable.*PR|install.*gh.*next|winget.*GitHub\.cli.*next|for.*future.*runs|next run') | Should -Be $true
}
```

Both failed before fix, both pass after (967/967 total).

## Fix

Replaced the single `$ghAvailable` boolean with a `$prTool` priority chain in Step 1.5:

1. **Priority 1 — `gh` CLI** (`$prTool = "gh"`)
2. **Priority 2 — VS Code GitHub Pull Request extension** (`$prTool = "vscode-extension"`) —
   detected by checking whether `github-pull-request_create_pull_request` tool is available in
   the agent context.
3. **Priority 3 — No tool** (`$prTool = "none"`) — proceed to commit/push, defer PR to handoff.

Step 6 updated to route the PR creation call through the detected tool (both `gh pr create` and
`github-pull-request_create_pull_request` are handled). Step 7 handoff updated with:
- A dedicated "no tool found" case that explains what was tried.
- Actionable **next-time** instructions: install VS Code GitHub Pull Request extension (zero
  config) or `gh` CLI + `gh auth login`.

## Lessons Learned

- **Never design a feature around a single external tool without a fallback.** Any workflow step
  that depends on an optional CLI should have a priority chain of alternatives.
- **"No tool found" messages must give forward-looking setup instructions**, not just repeat the
  command that requires the missing tool.
- **VS Code extension tools are first-class alternatives to CLI tools.** When an agent has access
  to extension-provided tools (e.g., `github-pull-request_create_pull_request`), it should
  prefer them before declaring a capability unavailable.

## Related

- [cg-commit-push-pr always waited for confirmation](./2026-05-15-cg-commit-push-pr-always-waits-for-confirmation.md) — same prompt, earlier fix session.
