---
date: 2026-08-17
title: "Manifest-driven install gate prevents junction conflicts with projection synchronizer"
category: "environment-issues"
language: "PowerShell"
tags: [manifest, projection, junction, reparse-point, link, native-platforms, install-gate]
root-cause: "Legacy junction install of native roots runs before projection --sync, causing _reject_unsafe_destination to abort on reparse-point ancestors"
severity: "P1"
---

# Manifest-Driven Install Gate Prevents Junction Conflicts

## Problem

`link.ps1`/`link.sh` create directory junctions for `.agents/*`, `.claude/*`, `.opencode/*` installUnits before the projection `--sync` block runs. The projection synchronizer's `_reject_unsafe_destination` → `secure_fs.revalidate_destination_ancestors` rejects any destination whose ancestor is a link/reparse point, so the same-run projection of junctioned roots aborts publication with "Linking is blocked by manifest projection failure" (exit 1).

This affects every manifest-driven consumer using `--platforms all` (the default profile) on all OSes. Kilo (copy-directory) and copilot (null `generatedTreePath`) escape the issue.

## Root Cause

The legacy link-directory install and the manifest-driven projection are two competing install mechanisms for the same native roots. When both run in the same `link` invocation, the junctions created by the legacy path become reparse-point ancestors that the projection's safety checks reject.

## Solution

For manifest-driven consumers (when `compound-gpid.local.md` exists), skip the legacy link-directory install of native generated-tree roots. The projection synchronizer materializes them as real directories instead.

```powershell
# link.ps1 — manifest-driven install gate
$manifestDriven = Test-Path -LiteralPath (Join-Path $ProjectRoot "compound-gpid.local.md")
# ...
if ($manifestDriven -and $nativeProjected -and
    $installUnit.type -eq "directory") {
    Write-Host "  Skipping $platform (manifest-driven projection)" -ForegroundColor DarkGray
    continue
}
```

The shell equivalent uses `platform_generated_tree` helper + `MANIFEST_DRIVEN` check:

```bash
MANIFEST_DRIVEN="false"
[ -f "$PROJECT_ROOT/compound-gpid.local.md" ] && MANIFEST_DRIVEN="true"
# ...
if [ "$MANIFEST_DRIVEN" = "true" ] && [ "$GENERATED_PROJECTED" = "true" ] && [ "$unit_type" = "directory" ]; then
    echo "  Skipping $platform (manifest-driven projection)"
    continue
fi
```

## Prevention

- Native generated-tree platforms (claude, codex, opencode) should never have both junction install and projection materialization active in the same link run.
- The gate is conditioned on `compound-gpid.local.md` existence, which is the manifest-driven consumer indicator.
- Phase 6 migration will remove the legacy junction install path entirely for native platforms.

## Related

- `.cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-phase3-verify-review.md` (P1.6)
- `scripts/link.ps1` — manifest-driven gate at line ~768-778
- `scripts/link.sh` — `platform_generated_tree` helper + gate at line ~609-622
- `.cg-docs/plans/2026-08-13-manifest-driven-skill-loading.md` — Phase 6 migration intent
