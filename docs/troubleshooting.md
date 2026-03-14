# Troubleshooting

Known issues and step-by-step fixes for Compound GPID.

> For installation help, see [Installation](installation.md). For workflow guidance, see [Workflow](workflow.md).

---

## `cg-update` fails with "Updated 0 paths from the index"

**Symptom**:
```
cg-update
Checking for updates...
update.ps1 : Update failed: Updated 0 paths from the index
```

**Cause**: The global clone has an old version of `update.ps1` that crashes on PowerShell 5.1 before it can pull the fix.

**Fix — run these two commands once in any terminal** (substitute your install path: `C:\WBG\.compound-gpid` or `$env:USERPROFILE\.compound-gpid`):
```powershell
# Uncomment your install path:
$cg = "C:\WBG\.compound-gpid"              # local machine (OneDrive)
# $cg = "$env:USERPROFILE\.compound-gpid"    # remote server
git -C $cg checkout . 2>$null              # suppress stderr (PS5.1 stderr-to-error promotion)
git -C $cg pull --ff-only
```

This manually updates the global clone. After that, `cg-update` works normally from all projects.

> **If `pull --ff-only` fails** with `fatal: Not possible to fast-forward`, the global clone has an unexpected local commit. Fix it with:
> ```powershell
> git -C $cg reset --hard origin/main
> ```

**Then run `cg-update` from each linked project** to apply any structural migrations:
```powershell
cg-update  # run from your project root
```

If the issue persists, open a [GitHub Issue](https://github.com/GPID-WB/compound-gpid/issues).

---

## `. $PROFILE` fails with "Cannot dot-source" error (Constrained Language Mode)

**Symptom**:
```
. $PROFILE
Microsoft.PowerShell_profile.ps1 : Cannot dot-source this command because it was defined in a different language mode.
```

**Cause**: Your organization enforces Constrained Language Mode (CLM) via AppLocker or Windows Defender Application Control. OneDrive has redirected your Documents folder to a path CLM treats as untrusted, blocking profile dot-sourcing.

**Fix**: Re-install using the current approach (batch wrappers on PATH â€” no profile manipulation):
```powershell
# Clone to your chosen path (see Installation > Choose your install path)
git clone https://github.com/GPID-WB/compound-gpid.git "C:\WBG\.compound-gpid"

# Run the installer
& "C:\WBG\.compound-gpid\install.ps1"

# Restart VS Code / Positron and your terminal
```

The installer automatically removes any old `$PROFILE` block from previous installs.

---

## Upgrading from `$env:USERPROFILE\.compound-gpid` (old default path — local OneDrive machines only)

> **Remote server users**: `$env:USERPROFILE\.compound-gpid` is the correct path on a remote server — no migration needed. Just re-run `install.ps1`.

If you are on a **local OneDrive machine** and previously installed to `$env:USERPROFILE\.compound-gpid`, you must migrate to `C:\WBG\.compound-gpid`. See the **[Upgrading from an old installation](installation.md#upgrading-from-an-old-installation)** section on the Installation page for the full four-step process.

---

## `cg-link` fails with a junction/symlink error

**Cause**: Windows requires Developer Mode to create directory junctions without admin rights on some configurations.

**Fix**: Enable Developer Mode:
Settings â†’ System â†’ For developers â†’ Developer Mode â†’ On

Then retry `cg-link` from your project root.

---

> Still stuck? Open a [GitHub Issue](https://github.com/GPID-WB/compound-gpid/issues).
> 
> See [Reference](reference.md) for a full list of commands and agents.

