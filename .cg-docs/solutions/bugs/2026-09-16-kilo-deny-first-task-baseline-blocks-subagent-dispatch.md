---
date: 2026-09-16
title: "Kilo deny-first Task baselines block subagent dispatch through inherited denies"
category: "bugs"
type: "bug"
language: "Python"
tags: [kilo, permissions, task-tool, deny-inheritance, subagent, autopilot, target-mapping, probe]
root-cause: "Kilo inherits session-level Task denies into child sessions while dropping the allow exceptions, so a deny-first task baseline leaves subagents with no effective Task tool"
severity: "P1"
status: "confirmed-by-human"
plan: ".cg-docs/plans/2026-09-11-kilo-first-autopilot.md"
related: [".cg-docs/solutions/testing-patterns/2026-09-16-native-evidence-edge-budget-requires-fresh-probe-session.md", ".cg-docs/solutions/bugs/2026-08-05-kilo-markdown-source-permission.md"]
---

# Kilo Deny-First Task Baselines Block Subagent Dispatch Through Inherited Denies

## Problem

The cg-autopilot bootstrap graph required a primary agent (`cg-autopilot`) to
dispatch a subagent stage (`cg-workflow-stage`) which itself dispatches reviewer,
fix, and restricted-leaf children through the native Task tool. The permission
maps used deny-first Task baselines with narrow allow exceptions, e.g. the stage
map `task: {"*": "deny", "cg-code-quality": "allow", "cg-fix-problems": "allow"}`.

Native probes showed the stage subagent had no effective Task tool at all:

- Probe `phase1-20260914-stage-general-02` (edge `stage-general`): receipt
  `blocked: native-dispatch-unavailable`; stage `ses_f5eac919bffe5BOuMjyVSWtcgO`
  observed with effective tools `[cg_native_identity, read]` only; leaf never
  reached. Report section "Bootstrap Probe Stage-General Edge Blocked
  2026-09-14T19:22:45Z".
- Probe `phase1-20260914-stage-reviewer-01` (edge `stage-reviewer`): receipt
  `blocked: dispatch-tool-unavailable`; stage `ses_f5e9b14b2ffe2dTAR01Z1FFwYv`
  observed with tools `[cg_native_evidence, cg_native_identity, glob, grep, read]`
  — no `task`. Report section "Bootstrap Probe Stage-Reviewer Edge Blocked
  2026-09-14T20:09:14Z".

`subagent_depth: 3` was configured but cannot help while no effective Task tool
exists.

## Root Cause

Kilo inherits the session-level Task deny into child sessions while dropping
the declared allow exceptions. A deny-first baseline (`"*": "deny"` plus exact
allows) therefore leaves every subagent with no effective Task tool regardless
of the allow entries. The two blocked receipts bind the finding; the earlier
source investigation corroborates that deny inheritance differs from other
permission keys (`kilocode/tool/task.ts` also explicitly omits broad
parent-agent bash denials from inheritance).

## Solution

Replace deny-first Task baselines on participating agents with non-denying
`ask` baselines plus exact named allows, and add a restricted read-only leaf.
Applied in unit TASK-DISPATCH-01 (user approval `2026-09-14T20:33:52Z`):

- `.github/shared/target-mapping.json:179` — parent:
  `"task": {"*": "ask", "cg-workflow-stage": "allow"}`
- `.github/shared/target-mapping.json:210` — stage:
  `"task": {"*": "ask", "cg-code-quality": "allow", "cg-fix-problems": "allow", "cg-bootstrap-leaf": "allow"}`
- `.github/shared/target-mapping.json:199` — fix-problems (symmetric, same root
  cause would block its depth-3 `general` dispatch):
  `"permission": {"task": {"*": "ask", "general": "allow"}}`
- New restricted read-only leaf `.github/agents/cg-bootstrap-leaf.agent.md`
  (mode subagent, no Task key, git-probe-only bash, read/glob/grep allow;
  mapping at `.github/shared/target-mapping.json:182-196`). Focused repair 1/2
  added `"cg_native_identity": "ask"` (line 189) with an identity-first body so
  the leaf verifies its caller before running its four read-only Git probes.
- Generator enforcement: `scripts/cg_generate_targets.py:346-386`
  (`_validate_asset_metadata`) validates exact task maps and builds the
  `{"*": "ask", ...allow}` shape.
- Plan cross-reference (Approved Permission-Baseline Correction):
  `.cg-docs/plans/2026-09-11-kilo-first-autopilot.md:515-534`.

No `task: {"*": "allow"}` exists anywhere; `ask` is not a bypass — dispatch
still requires native approval.

## Evidence

Succeeded native receipts after the fix (all foreground, settled, permission
`allowed`, branch `cg-autopilot`, HEAD
`b94f585c8a485dfb03965ca9711fb83257aaa7de`):

- `phase1-20260914-stage-reviewer-02` SUCCEEDED (depth 2): stage
  `ses_f5e1f3210ffecE4TmQXItNfn7k` -> `cg-code-quality`
  `ses_f5e1c1327ffe4uM42wOtyOjpDp`. Report "Fresh Probe Outcomes
  2026-09-15T14:00:44Z".
- `phase1-20260915-stage-fix-general-01` SUCCEEDED (conditional depth 3): stage
  `ses_f5a79b259ffeRhyaPhF2QDw4L2` -> `cg-fix-problems`
  `ses_f5a74a59affemZ0yiGY5sh9bd3` -> `general`
  `ses_f5a7268a7ffeFybvmV38UGNN9H`. Report "Bootstrap Probe Outcomes
  2026-09-15T15:14:36Z".
- `phase1-20260915-stage-general-05` SUCCEEDED (depth 2, restricted leaf):
  primary `ses_f5a1e6cfeffeLNWbxgyvhbuh0E` -> stage -> `cg-bootstrap-leaf`.
  Report "MAJOR MILESTONE: Final Restricted-Leaf Edge Succeeded
  2026-09-15T17:22Z".
- Final conformance set: `stage-reviewer-03`, `stage-general-06`, and
  `phase1-20260916-stage-fix-general-01` SUCCEEDED (report "Step 16 Final
  Native Conformance Closure 2026-09-16T12:46:05Z").

Tests: authoritative pytest gate 2682 passed / 50 skipped / 0 failed; Node
24.21.0 SDK suite 125 passed / 0 failed; `test_native_evidence.py` 9 passed;
Pester full safe runner 2929 total / 2927 passed / 0 failed / 2 existing skips;
frontmatter lint 71 files (31 agents + 40 skills). Touched suites:
`scripts/tests/test_target_mapping.py`, `test_target_kilo.py`,
`test_autopilot_runtime.py`, `test_autopilot_contracts.py`,
`test_native_evidence.py`, `tests/model-assignments.Tests.ps1` (30 -> 31
agents).

## Confirmation

Status `confirmed-by-human`: the probes were executed in user-driven dedicated
`cg-autopilot` sessions and their receipts recorded as user-supplied evidence
("Phase 1 Step 3 Acceptance (native delegation without self-hosting):
SATISFIED" — accepted by three actually-executed probes); the fix unit was
explicitly approved by the user and the parent concluded the verify/triage
stage green. Source: `.cg-docs/work-reports/2026-09-11-kilo-first-autopilot.md`.

## Prevention

- Never use deny-first Task baselines (`{"*": "deny", <exact allows>}`) on
  agents that must dispatch children. Use `{"*": "ask", <exact allows>}`.
- Keep the allow set exact and named; the generator validator
  (`_validate_asset_metadata`) rejects missing or malformed task maps before
  emission.
- When a subagent reports no Task tool, inspect its observed effective toolset
  first — an effective toolset missing `task` while the declared map contains
  task allows is the deny-inheritance signature, not a missing installation.
- Probe evidence requires settled receipts with permission `allowed`; a
  `blocked` receipt with reason `native-dispatch-unavailable` /
  `dispatch-tool-unavailable` is not denial-policy enforcement.

## Related

- `.cg-docs/solutions/testing-patterns/2026-09-16-native-evidence-edge-budget-requires-fresh-probe-session.md`
- `.cg-docs/solutions/bugs/2026-08-05-kilo-markdown-source-permission.md`
- `.cg-docs/work-reports/2026-09-11-kilo-first-autopilot.md`
- `.cg-docs/plans/2026-09-11-kilo-first-autopilot.md`
