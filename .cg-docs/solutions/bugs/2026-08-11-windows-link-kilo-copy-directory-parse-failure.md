---
date: 2026-08-11
title: "Windows cg-link Kilo parse failures — enforce copy-directory instead of junctions"
category: "bugs"
language: "both"
tags: [kilo, agents, link, windows, junction, symlink, copy-directory, checksum, manifest, parsing, posix, pester]
root-cause: "Windows scripts/link.ps1 ignored the copy-directory strategy and created junctions to the external Compound GPID install, so Kilo resolved .kilo/ agent markdown outside the project root and rejected every file (cascading 'Failed to parse agent')."
severity: "P1"
---

# Windows cg-link Kilo Parse Failures — Copy-Directory Over Junctions

## Problem

Opening a project in VS Code or Positron with the Compound GPID plugin installed
(v1.1.9+) reported the same error for **all 17 agent files** in `.kilo/agents/`:

```
Failed to parse agent E:\...\metapip\.kilo\agents\cg-wiki.md
{ "name": "UnknownError", ... }
```

The agent YAML itself was valid: frontmatter validation (description quoted,
`mode: subagent`, no BOM) passed for every file. The files were also not stale
generated copies — the error persisted across IDE restarts and reloads.

## Root Cause

`target-mapping.json` declares Kilo directory units with strategy
`copy-directory` (introduced in v1.1.9 to fix the macOS symlink regression), but
the fix was implemented **only in `scripts/link.sh`**:

- `link.sh` honored the strategy and copied the tree into the project.
- `link.ps1` (Windows) ignored `unit.strategy`, always created a **junction**
  to the global install: `E:\...\metapip\.kilo\agents -> C:\Users\<u>\.compound-gpid\.kilo\agents`.

Kilo (and issue #12391 showed the upstream regression) refuses to load markdown
sources that resolve outside the project root through junctions/symlinks. Every
`cg-*.md` in `.kilo/agents` was then "external", so all 17 failed together — the
"Failed to parse agent" message is a masking wrapper, not a YAML problem.

A second, compounding defect: `Resolve-CgLinkArguments` declared its parameter as
`[object[]]$Args`, colliding case-insensitively with PowerShell's automatic
`$args` variable. `--platforms kilo --yes` was silently discarded, so a "kilo
only" run actually linked **all** platforms (and later runs could also drop the
non-interactive `--yes`).

## Solution

Implemented the `copy-directory` strategy properly in `scripts/link.ps1` with a
checksum-managed per-directory mirror, and closed the cleanup lifecycle:

1. **Strategy pass-through + junction migration**: `Install-CgDirectoryUnit`
   receives `Strategy` and, for `copy-directory`, migrates an existing
   Compound-owned junction to a real local directory (removing the reparse
   point only — never traversing into the shared source).
2. **Checksum manifest**: each copied directory gets a
   `.compound-gpid-managed-copy.json` marker (`schemaVersion`, `source`,
   `files` = relative path → SHA-256). Sync policy: overwrite only when absent,
   byte-identical to source, or byte-identical to the previous managed
   checksum; anything else is user-owned and preserved with a warning. Stale
   managed files are deleted only when their current checksum still equals the
   recorded one.
3. **Path safety**: marker/relative paths are validated as safe relative paths
   that cannot escape the target directory; reparse points in any path ancestor
   cause the file to be preserved. Marker writes are atomic (temp file +
   `File.Replace` + backup). Marker reads reject malformed/non-object roots,
   self-referencing keys, non-64-hex checksums, and empty `files` maps (a crash
   or silent un-manage — never).
4. **Baseline adoption**: a real directory without a valid marker (partial,
   user-populated, empty, or corrupt) is not skipped-forgotten — it is synced
   from baseline: CG files are installed, user files preserved, fresh marker
   written. No previous manifest ⇒ stale-removal disabled, so unrecorded user
   files can never be deleted.
5. **Unlink lifecycle**: `unlink.ps1`/`unlink.sh` now remove checksum-verified
   managed copies and the marker (preserving user-modified files) instead of
   leaving a stale, un-ignored `.kilo/` tree behind.
6. **`$Args` collision fix**: `Resolve-CgLinkArguments` and
   `Resolve-CgUnlinkArguments` parameters renamed to `$Arguments`; both scripts
   correctly honor `--platforms kilo --yes` in non-interactive runs.
7. **`.gitignore`**: markers are excluded via `**/.compound-gpid-managed-copy.json*`,
   and the managed-items block is now written as UTF-8 without a BOM (PS 5.1
   `Set-Content -Encoding UTF8` adds a BOM, which corrupted `.gitignore`).

The current project (`metapip`) was migrated by re-running the fixed linker:
`.kilo/{commands,skills,agents,instructions,shared}` are now project-local
copies with markers, and all 17 agents pass frontmatter validation.

## Prevention

- **Never implement a strategy on one OS only**: a `copy-directory` change
  landed in `link.sh` while `link.ps1` silently junctioned. Add a mapping-level
  guard (the Python test pins the 5 Kilo directory units to `copy-directory`)
  plus cross-script parity tests.
- **Respect PowerShell's automatic `$Args`** — never name a parameter `$Args`;
  add the `Should -Not -Match 'param(\\[object\\[\\]\\]\\$Args\\))'` regression
  guard.
- **Trust-boundaries for markdown**: Kilo requires project-local markdown
  sources; junctions/symlinks to an external install are a recurring source of
  "Failed to parse agent/skill" cascades (upstream #12391). Keep consumer
  install units as local copies with an ownership marker.
- **Checksum-gated deletion everywhere**: never `Remove-Item -Recurse` trees
  that may contain junctions (follows the link; hangs VS Code / Language
  Server), and only delete files whose bytes still match their recorded
  checksum.
- **Keep `.ps1` sources pure ASCII**: the repo's `ps51-compat` suite flags any
  non-ASCII comment as a PS 5.1 AST-corruption risk — use `--`/`(e.g. ...)`.

## Related

- `.cg-docs/solutions/bugs/2026-08-06-kilo-agent-skill-parsing-failures.md` — original incident; the YAML hardening there was necessary but not sufficient; this is the link.ps1 mechanism that actually fixes the recurring Windows case
- `.cg-docs/solutions/bugs/2026-08-05-kilo-markdown-source-permission.md` — the global `kilo.jsonc` `markdown_source` permission workaround; copy-directory reduces reliance on it
- `.cg-docs/solutions/git-workflows/2026-05-13-e2e-smoke-test-github-actions-windows-junction-teardown.md` — junction-removal safety (`Remove-Item -Recurse` follows links)
- `.cg-docs/solutions/testing-patterns/2026-03-04-pester-testdrive-follows-junctions-freezes-vscode.md` — Pester `$TestDrive` junction-teardown hazard (AfterAll/AfterEach non-recursive cleanup)
- `.cg-docs/solutions/testing-patterns/2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md` — never pipeline Pester `-PassThru`; use the canonical runner
- Upstream: Kilo issue #12391 / PR #12846 — external-directory symlink agent loading regression

## 2026-08-20 Addendum: Cross-Adapter Auto-Discovery

This fix remains correct for native `.kilo/*` units but was not sufficient when
Codex and Kilo were installed together. Kilo also auto-discovers
`.agents/skills`, so Codex's intentional external `link-directory` still crossed
Kilo's project markdown boundary even though `.kilo/skills` was a real copy.

The follow-up
`.cg-docs/solutions/bugs/2026-08-20-kilo-cross-adapter-skill-autodiscovery.md`
complements this solution by keeping `.agents/skills` linked while redirecting
it to an adapter-specific managed mirror inside the consumer project. It does
not supersede the Kilo `copy-directory` strategy; the local `.kilo/skills` copy
and its marker remain required. That follow-up also brought the POSIX linker to
the same checksum-preserving managed-copy contract instead of wholesale
overwriting user edits.
