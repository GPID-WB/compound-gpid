---
date: 2026-08-14
title: "Kilo coexistence requires a certified contained launch and no-follow local copies"
category: "environment-issues"
language: "both"
tags: [kilo, codex, claude, coexistence, containment, preflight, copy-directory, no-follow, checksum, pester]
root-cause: "Kilo auto-discovered external compatibility skill roots while platform linkers used inconsistent copy semantics and untyped host checks."
severity: "P0"
plan: ".cg-docs/plans/2026-08-13-manifest-driven-skill-loading.md"
reviewed-in: ".cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-verify-review.md"
---

# Kilo Coexistence Requires a Certified Contained Launch and No-Follow Local Copies

## Problem

When Kilo, Codex, and Claude-compatible roots coexist in one project, Kilo can
discover skills outside the project-local `.kilo/skills` tree. External Markdown
roots can cause inventory leakage or be reported as misleading parser failures.
The Windows and POSIX Kilo copy-directory paths also had different ownership and
link-following behavior.

## Root Cause

Kilo's `skills.paths` configuration is additive and cannot be treated as an
exclusion boundary. A project-local copy alone does not prevent host-level
compatibility-root discovery. The existing link/update flows also performed
mutation before all host/content checks completed, and recursive POSIX copying
could follow user-controlled links.

## Solution

- Characterize the installed embedded Kilo hosts with local, Codex, and Claude
  sentinel skills using `kilo debug skill`.
- Certify Kilo 7.4.20, 7.4.21, and 7.4.22 only after the child-process control
  `KILO_DISABLE_EXTERNAL_SKILLS=1` preserves the local sentinel and excludes
  compatibility-root inventory records.
- Provide `cg-kilo` and `cg-kilo.cmd` as the only supported launch path for a
  project containing Kilo plus Codex/Claude roots. The launcher copies the
  caller environment, sets the control only for the child, preserves caller
  state, and relays the child's exit code.
- Use typed preflight statuses for missing hosts, unsupported versions, local
  projection/content failures, host schema failures, and ineffective
  containment. Keep local Markdown/content failures separate from Kilo's
  upstream schema-validation failures.
- Validate managed Kilo files with marker source/checksum ownership and reject
  symlinks/reparse points, unsafe marker paths, invalid hashes, and local skill
  inventory records outside the project-local root.
- Use `secure_fs` for the POSIX Kilo copy worker so reads, writes, stale deletes,
  and marker updates are root-relative, no-follow, checksum-owned operations.
- Bound preserved-file warnings and construct preflight JSON directly instead of
  recursively copying the full result object.

Example certified invocation:

```text
cg-kilo --project-or-kilo-arguments
```

The project-local preflight result records the executable path, Kilo version,
executable SHA-256, selected containment environment, and inventory evidence.

## Prevention

- Never treat an environment-variable probe or direct editor launch as proof of
  containment. Require an executed supported-host inventory check.
- Keep Codex/Claude compatibility roots and Kilo local roots separate in tests;
  test Codex-only, Claude-only, and mixed-root cases.
- Use one no-follow synchronizer for both operating systems. Do not reintroduce
  recursive `cp -R` for runtime Markdown trees.
- Preserve modified or unowned files; delete stale files only when their bytes
  match recorded ownership checksums.
- Keep staged/journaled multi-root publication and active-manifest persistence
  as explicit later-phase gates. Phase 1 preflight success is not whole-project
  atomicity or final release evidence.
- Use `tests/Run-Tests.ps1 -File <name>` for Pester and consume
  `tests/last-run.json`; do not run unsafe directory or output pipelines.

## Related

- `.cg-docs/solutions/bugs/2026-08-11-windows-link-kilo-copy-directory-parse-failure.md`
- `.cg-docs/solutions/bugs/2026-08-06-kilo-agent-skill-parsing-failures.md`
- `.cg-docs/solutions/bugs/2026-08-05-kilo-markdown-source-permission.md`
- `.cg-docs/solutions/testing-patterns/2026-07-28-handle-relative-filesystem-mutations-and-real-boundary-tests.md`
- `.cg-docs/solutions/bugs/2026-08-01-secure-publication-rollback-must-not-clobber.md`
- `scripts/cg_kilo_preflight.py`
- `scripts/cg_kilo_copy.py`
- `scripts/tests/test_kilo_coexistence.py`
- `scripts/tests/test_kilo_copy.py`
- `.cg-docs/solutions/git-workflows/2026-08-21-pr-ci-preflight-native-target-kilo-capability-gates.md`
