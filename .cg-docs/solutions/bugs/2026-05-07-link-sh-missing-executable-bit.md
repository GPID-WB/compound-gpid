---
date: 2026-05-07
title: "scripts/link.sh missing executable bit in git index"
category: "bugs"
type: "bug"
language: "both"
tags: [bash, git, permissions, install, cg-link, executable-bit]
root-cause: "scripts/link.sh was committed to git with mode 100644 instead of 100755, so every fresh clone lacks the execute bit and bin/cg-link fails with Permission denied"
severity: "P1"
test-written: "yes"
fix-confirmed: "yes"
---

# scripts/link.sh missing executable bit in git index

## Symptom

Running `cg-link` after a fresh install fails immediately with:

```
/Users/<user>/.compound-gpid/bin/cg-link: line 5: /Users/<user>/.compound-gpid/bin/../scripts/link.sh: Permission denied
```

The wrapper `bin/cg-link` calls `exec "$SCRIPT_DIR/../scripts/link.sh"`, but `link.sh` has no execute bit, so the shell refuses to run it.

## Root Cause

`scripts/link.sh` was tracked in the git index with mode `100644` (regular file, not executable) while all sibling scripts (`install.sh`, `unlink.sh`, `update.sh`) were correctly tracked as `100755`. Git preserves file modes on clone, so every fresh clone of the repo produced a non-executable `link.sh`. `install.sh` only calls `chmod +x` on the generated `bin/cg-*` wrappers — it never sets permissions on the source scripts in `scripts/`, assuming git would preserve them. That assumption was silently broken for `link.sh`.

## Reproduction Test

The test already existed in [tests/bash-scripts.Tests.ps1](../../../tests/bash-scripts.Tests.ps1) under the `"bash-scripts - scripts exist with executable bit"` describe block:

```powershell
It "scripts/link.sh is executable" {
    Test-Executable $scriptPath | Should -Be $true
}
```

Where `Test-Executable` runs `bash -c "[ -x '<path>' ] && echo yes || echo no"`.

Confirmed failing via direct bash check (pwsh not installed on the affected machine):
```bash
bash -c "[ -x scripts/link.sh ] && echo PASS || echo FAIL"
# → FAIL: not executable
```

## Fix

Two commands were needed — one to fix the git index (what will be committed), one to fix the working-tree file on disk:

```bash
git update-index --chmod=+x scripts/link.sh   # fix git index: 100644 → 100755
chmod +x scripts/link.sh                       # fix working-tree file
```

After the fix:
```bash
git ls-files -s scripts/link.sh
# → 100755 c6cef41dcec0a7d5275e16ae4fe8f623fd661f18 0  scripts/link.sh

bash -c "[ -x scripts/link.sh ] && echo PASS || echo FAIL"
# → PASS: link.sh executable
```

Running `bin/cg-link` no longer produced "Permission denied".

## Lessons Learned

- **`git update-index --chmod=+x <file>` only patches the index** — it does not touch the working-tree file. Always follow it with `chmod +x` on disk, or simply run `chmod +x` first and let `git add` pick up the mode change.
- **The safe single-command pattern** to fix a missing executable bit and stage it in one step is:
  ```bash
  chmod +x scripts/link.sh && git add scripts/link.sh
  ```
- **When adding a new bash script to the repo**, always verify its git mode with `git ls-files -s <file>` and confirm it shows `100755` before committing.
- **`install.sh` should not need to compensate** for missing executable bits on source scripts — those must be correct in git. Adding defensive `chmod +x` calls in `install.sh` for `scripts/*.sh` would be a belt-and-suspenders safety net worth considering.

## Related

None.
