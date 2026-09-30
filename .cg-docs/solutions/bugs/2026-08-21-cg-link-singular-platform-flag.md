---
date: 2026-08-21
title: "cg-link ignored singular --platform flag"
category: "bugs"
type: "bug"
language: "both"
tags: [cg-link, platform, platforms, kilo, argument-parser, bash, powershell]
root-cause: "Both cg-link launchers recognized only --platforms, so singular --platform and its value were ignored and the empty selection defaulted to all platforms."
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
red-phase-confirmed: "yes"
expected-behavior-source: "user-requirement"
test-gap: "edge-case-gap"
---

# cg-link Ignored Singular --platform Flag

## Symptom

On version `v1.2.0.9006`, running `cg-link --platform kilo` produced warnings
that `--platform` and `kilo` were unrecognized, then linked every supported
platform instead of only Kilo.

## Expected Behavior Source

User requirement: `cg-link --platform kilo` must recognize the singular alias,
select only Kilo, and avoid installing Copilot, Claude Code, Codex, or OpenCode
assets. The existing plural forms remain supported.

## Root Cause

The PowerShell and bash argument parsers recognized `--platforms` and
`-Platforms`, but not singular `--platform`. Unrecognized arguments left the
platform selection empty, and the normalizer interpreted an empty selection as
the default `all` platform set.

## Reproduction Test

Added to `tests/parity.Tests.ps1`:

- Verifies the PowerShell parser recognizes `--platform`.
- Verifies the bash parser recognizes `--platform`.

The reproduction test initially failed with 2 failures on the unchanged code.

## Test Gap

`edge-case-gap` — existing tests covered the documented plural `--platforms`
forms, but did not cover the singular alias used by the bug report. Therefore,
the fallback-to-all behavior was not detected.

## Fix

Added singular aliases to both launchers while preserving all existing forms:

```text
--platform kilo
--platform=kilo
--platforms kilo
--platforms=kilo
```

PowerShell now accepts `--platform` in both separated and equals forms in
`Resolve-CgLinkArguments`. Bash accepts the same forms in its argument-parser
`case` statement.

## Lessons Learned

For parser changes, test every supported spelling and both separated and
equals-value forms. The `edge-case-gap` occurred because coverage followed the
plural documentation only and omitted the singular input path. A parser must
also fail closed or report an explicit error when a selection flag is unknown,
rather than silently falling back to an all-platform default.

## Related

- `.cg-docs/solutions/bugs/2026-08-11-windows-link-kilo-copy-directory-parse-failure.md` — related Windows `cg-link` argument handling and Kilo installation issue.
