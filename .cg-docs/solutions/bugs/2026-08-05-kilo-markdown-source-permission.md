---
date: 2026-08-05
title: "Kilo platform missing markdown_source permission for symlinked commands"
category: "bugs"
type: "bug"
language: "both"
tags: [kilo, symlink, permissions, global-config, kilo.jsonc, markdown_source, platform-support]
root-cause: "link scripts created symlinks for .kilo/commands/ but did not update global kilo.jsonc with the markdown_source permission Kilo requires to trust external command files"
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
red-phase-confirmed: "yes"
expected-behavior-source: "documentation"
test-gap: "missing-test"
---

# Kilo platform missing markdown_source permission for symlinked commands

## Symptom

After running `cg-link --platform kilo`, the `.kilo/commands/` directory is correctly symlinked to the compound-gpid installation, but Kilo refuses to load the external command files. The `/cg-*` commands do not appear in Kilo's command picker because the global `~/.config/kilo/kilo.jsonc` lacks the required `markdown_source` permission.

## Expected Behavior Source

Kilo documentation (https://kilo.ai/docs/customize/workflows) explicitly states:

> If `.kilo/commands/` is a symlink to a directory outside the project, allow that exact source in your global `~/.config/kilo/kilo.jsonc`:
> ```json
> {
>   "permission": {
>     "markdown_source": {
>       "/path/to/shared/commands/*": "allow"
>     }
>   }
> }
> ```

## Root Cause

The `link.ps1` and `link.sh` scripts handle all aspects of platform linking (symlinks, .gitignore management, managed file copies) but were missing the Kilo-specific step of updating the global `~/.config/kilo/kilo.jsonc` with the `markdown_source` permission. The kilo platform was added to the link scripts alongside other platforms, but the Kilo-specific requirement of whitelisting symlink targets in the global config was not addressed.

## Reproduction Test

Added to `tests/link.Tests.ps1` in the `Describe "link.ps1 - kilo global kilo.jsonc markdown_source permission"` block. Seven assertions verify:
- `link.ps1` references `markdown_source` permission
- `link.ps1` references the global `kilo.jsonc` path
- `link.ps1` updates global config when kilo platform is selected
- `link.sh` references `markdown_source` permission
- `link.sh` references the global `kilo.jsonc` path
- `unlink.ps1` references `markdown_source` cleanup
- `unlink.sh` references `markdown_source` cleanup

## Test Gap

missing-test — No test existed for Kilo global config permission handling. The kilo platform was added to the link scripts alongside other platforms, but the Kilo-specific requirement of whitelisting symlink targets in `~/.config/kilo/kilo.jsonc` was not addressed or tested.

## Fix

Added `Update-CgKiloGlobalPermission` (PowerShell) and `update_kilo_global_permission` (bash) functions to the link scripts that:
1. Resolve the global `~/.config/kilo/kilo.jsonc` path
2. Read existing JSON config (preserving all other settings)
3. Add `permission.markdown_source.<compound-gpid-path>/.kilo/commands/*` = `"allow"`
4. Write back the config

Added corresponding cleanup functions (`Remove-CgKiloGlobalPermission` / `remove_kilo_global_permission`) to the unlink scripts that remove the permission entry when unlinking.

**Files changed:**
- `scripts/link.ps1` — Added `Update-CgKiloGlobalPermission` function and call after kilo platform linking
- `scripts/link.sh` — Added `update_kilo_global_permission` function and call after kilo platform linking
- `scripts/unlink.ps1` — Added `Remove-CgKiloGlobalPermission` function and call during unlink
- `scripts/unlink.sh` — Added `remove_kilo_global_permission` function and call during unlink
- `tests/link.Tests.ps1` — Added 7 reproduction tests for the new behavior

**Configuration managed through `cg-link` (not `cg-update`):** The `markdown_source` permission is a direct consequence of symlink creation, which happens in `cg-link`. The `cg-update` command only updates repo content (git pull + platform tree regeneration) and does not create or modify symlinks. This is consistent with how `cg-link` already manages `.gitignore` entries and the managed-files manifest.

## Lessons Learned

When adding a new platform to the multi-platform link system, the platform-specific configuration requirements (beyond just symlinks/copies) must be identified and implemented. Kilo's security model requires explicit permission for symlinked command directories, unlike GitHub Copilot, Claude Code, Codex, and OpenCode which load symlinked content without additional configuration. Future platform additions should include a "platform-specific config requirements" checklist item in the implementation plan.

## Related

None.
