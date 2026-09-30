---
date: 2026-09-24
title: "Legacy-first routine four-part prerelease"
status: completed
completed-date: 2026-09-24
scope: "Focused"
deviation-policy: "ask"
tags: [release, prerelease, legacy-publisher]
---

# Legacy-First Routine Four-Part Prerelease

## Objective

Make `/cg-release vX.Y.Z.<build>` the GPID routine prerelease request using
the existing PowerShell Reserve and Finalize publisher. Keep the controller
disabled; do not add a second publisher, change GitHub settings, or publish
a live release as part of this implementation.

## Approved Scope

1. Select a distinct `Routine` operation for a bare four-component GPID tag
   (and its explicit `--resume <tag>` form). Keep generic
   `plan/start/status/resume`, exceptional Bridge/Recovery, and stable release
   rules separate. A native launcher cannot prepare notes and payloads from a
   bare tag, so it must give a clear slash-workflow instruction.
2. Reuse the existing reviewed payload, exact source and tag checks, local
   preflight, Release conflict checks, successful prerelease build, and
   attestation path. Require the protected remote controller policy to exist
   and remain disabled at each consequential authority check. Do not claim
   exclusive GitHub API authority over other people with write permission.
3. Update canonical command, generated targets, help evidence and docs. Test
   the routine Reserve/Finalize path and negative stable, missing policy, and
   enabled-controller cases with offline fixtures. Do not create or change a
   remote tag, Release, setting, or credential during implementation.

## Verification

- `create-release` and `prompt-tools` isolated safe Pester files: passed,
  zero failures. The saved `tests/last-run.json` describes only the last
  filtered `prompt-tools` run (1804 passed), not a full-suite gate.
- Python launcher/source policy: 41 passed. Help catalog: 69 passed.
  Generated target drift: 24 passed.
- `python scripts/cg_generate_help_catalog.py --check` and `--check-docs`:
  passed after individual reviewed definition repins and docs regeneration.
  `git diff --check`: passed. No live publisher was tested.

## Limits

This local implementation does not satisfy the superseded plan's exclusive
gateway, stable-docs baseline, remote denial probes, Bridge qualification,
or live `v1.2.0.9020` acceptance. It does not authorize publication.
