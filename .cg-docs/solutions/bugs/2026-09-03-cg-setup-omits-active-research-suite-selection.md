---
date: 2026-09-03
title: "cg-setup omitted active research-suite selection"
category: "bugs"
type: "bug"
language: "both"
tags: [cg-setup, compound-research, active-suites, configuration, setup, regression-test]
root-cause: "Normal Mode A setup did not ask for active suites and the config template defaulted to suites: [cg], so selected research activation was not persisted."
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
red-phase-confirmed: "yes"
expected-behavior-source: "user-requirement"
test-gap: "missing-test"
---

# cg-setup omitted active research-suite selection

## Symptom

After running `/cg-setup`, a project that needed Compound Research could still be
configured without the `cr` suite. Running a `/cr-*` prompt then displayed:

> Research module is not enabled. Run `/cg-setup` to add it, or proceed anyway?

## Expected Behavior Source

User requirement -- `/cg-setup` must ask at the outset which workflow suites to
activate and must write a configuration containing `cr` (`[cr]` or `[cg, cr]`)
when research workflows are required. A correctly configured research project
must not trigger the disabled-module warning.

## Root Cause

The normal scanner-success path in `/cg-setup` configured language, R dialect,
project type, and review depth but never asked for active suites. The only suite
question was in the manual fallback path. The shared config template also
hard-coded `suites: [cg]`, so normal setup could silently create a
technical-only configuration.

## Reproduction Test

Regression coverage was added to `tests/prompt-tools.Tests.ps1`. It checks that:

- the normal A2 setup flow asks for active suites;
- the template exposes `[cg]`, `[cr]`, and `[cg, cr]` as selectable values; and
- setup explicitly persists the selected value.

The test was red before the fix: 1,441 total, 1,439 passed, and 2 failed.

## Test Gap

`missing-test` -- existing setup tests checked prompt structure and the presence
of configuration references, but no test covered active-suite selection and
persistence in the normal scanner-success setup path. The new regression test
covers that path directly.

## Fix

The canonical setup flow was updated to:

- ask Question 3.5 for active workflow suites during normal Mode A setup;
- replace the `suites:` template placeholder with exactly `[cg]`, `[cr]`, or
  `[cg, cr]` before writing `compound-gpid.local.md`;
- explicitly confirm or update active suites at the start of returning-project
  configuration, including legacy configs without a `suites:` field; and
- show the active suite selection in the setup completion summary.

The setup reference skill and generated Claude Code, Codex, OpenCode, and Kilo
copies were regenerated from the canonical `.github/` files.

The focused prompt suite passed after the fix with 1,441/1,441 tests passing.
The full Pester suite passed with 2,448 passed, 0 failed, and 3 skipped. Target
closure and drift validation passed with 36 tests passing.

## Lessons Learned

A `missing-test` gap can leave an orchestration prompt apparently complete while
its normal execution path omits a required configuration decision. Setup tests
must cover every configuration field through the path used when detection
succeeds, not only fallback questions or broad keyword presence. When a suite is
optional, the setup prompt must both ask for the choice and state how that choice
is materialized in the persisted config.

## Related

None.
