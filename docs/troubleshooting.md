# Troubleshooting

Known issues and step-by-step fixes for Compound GPID.

> For installation help, see [Installation](installation.md). For workflow guidance, see [Workflow](workflow.md).

---

## `cg-update` (or `cg-link`, `cg-unlink`) not recognized after install

**Symptom**:
```
cg-update: The term 'cg-update' is not recognized as a name of a cmdlet,
function, script file, or executable program.
```
This happens right after running `install.ps1`, even in a "new" terminal tab.

**Cause**: `install.ps1` writes `C:\WBG\.compound-gpid\bin` (or `$env:USERPROFILE\.compound-gpid\bin`) to your user `PATH` in the Windows registry. However, VS Code's integrated terminal inherits its environment from the VS Code process, which in turn inherits from **Explorer.exe**. Explorer only re-reads the registry when it receives a `WM_SETTINGCHANGE` message. Until Explorer gets that broadcast, every new terminal tab — including ones opened after `install.ps1` ran — will be missing the new entry.

**Fix (fastest)**: Add the path to the current terminal session manually, then re-run `install.ps1` so the broadcast fires:

```powershell
# Uncomment your install path:
$cg = "C:\WBG\.compound-gpid"              # local machine (OneDrive)
# $cg = "$env:USERPROFILE\.compound-gpid"    # remote server

$env:PATH = "$cg\bin;" + $env:PATH
& "$cg\install.ps1"
```

After this, open a **brand new terminal tab** and `cg-update` will work.

**Fix (alternative)**: Sign out of Windows and sign back in. This forces Explorer to re-read the registry, so all new processes (including VS Code) inherit the updated PATH automatically.

**Verify the PATH is set**:
```powershell
$env:PATH -split ';' | Select-String 'compound'
# Should print: C:\WBG\.compound-gpid\bin
```

**Verify the bin directory exists and contains the wrappers**:
```powershell
Get-ChildItem "C:\WBG\.compound-gpid\bin"   # adjust path if needed
# Should list: cg-link.cmd, cg-unlink.cmd, cg-update.cmd
```

> **PATH length truncation**: If `C:\WBG\.compound-gpid\bin` is present in the registry
> but never appears in a live terminal (even after a sign-out), your combined system + user
> PATH may be too long for Windows to merge without truncation. Fix: remove duplicate
> entries from your user PATH.
> ```powershell
> $raw = (reg query "HKCU\Environment" /v PATH) |
>     Where-Object { $_ -match 'REG_' } |
>     ForEach-Object { ($_ -replace '.*REG_EXPAND_SZ\s+', '').Trim() }
> $deduped = ($raw -split ';' | Where-Object { $_ -ne '' } | Select-Object -Unique) -join ';'
> reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d $deduped /f
> ```
> Then re-run `install.ps1` to trigger the broadcast.

---

## `.cg-version` missing or corrupted

**Symptom**: `cg-update` fails with an error about an invalid version, or unexpectedly pins to an unrecognised value.

**Cause**: The `.cg-version` file in your install directory was manually edited, truncated, or written incorrectly.

**Fix**: Delete the file and run `cg-update`. It defaults to `latest` (tracking `main`) when the file is absent.

```powershell
# Uncomment your install path:
$cg = "C:\WBG\.compound-gpid"              # local machine (OneDrive)
# $cg = "$env:USERPROFILE\.compound-gpid"    # remote server
Remove-Item (Join-Path $cg ".cg-version") -ErrorAction SilentlyContinue
cg-update
```

After this, `cg-update` runs in `latest` mode. To re-pin, run `cg-update v0.2.0` (or your desired tag).

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

## `cg-update` fails due to untracked files or local changes

**Symptom**: `cg-update` fails with messages about untracked files, merge conflicts, or local changes in the global clone.

**Fix**: Use the built-in repair command:
```powershell
cg-update --fix
```

This cleans untracked files, discards local changes, and pulls the latest code. If `--fix` itself fails (e.g. the installed copy is too old), see the [Repairing a broken installation](installation.md#repairing-a-broken-installation) section.

---

## `. $PROFILE` fails with "Cannot dot-source" error (Constrained Language Mode)

**Symptom**:
```
. $PROFILE
Microsoft.PowerShell_profile.ps1 : Cannot dot-source this command because it was defined in a different language mode.
```

**Cause**: Your organization enforces Constrained Language Mode (CLM) via AppLocker or Windows Defender Application Control. OneDrive has redirected your Documents folder to a path CLM treats as untrusted, blocking profile dot-sourcing.

**Fix**: Re-install using the current approach (batch wrappers on PATH - no profile manipulation):
```powershell
# Clone to your chosen path (see Installation > Choose your install path)
git clone https://github.com/GPID-WB/compound-gpid.git "C:\WBG\.compound-gpid"

# Run the installer
& "C:\WBG\.compound-gpid\install.ps1"

# Restart VS Code / Positron and your terminal
```

The installer automatically removes any old `$PROFILE` block from previous installs.

---

## Upgrading from `$env:USERPROFILE\.compound-gpid` (old default path -- local OneDrive machines only)

> **Remote server users**: `$env:USERPROFILE\.compound-gpid` is the correct path on a remote server -- no migration needed. Just re-run `install.ps1`.

If you are on a **local OneDrive machine** and previously installed to `$env:USERPROFILE\.compound-gpid`, you must migrate to `C:\WBG\.compound-gpid`. Follow the steps below **before** running a fresh install.

### Step A - Remove the old `$PROFILE` block

Run `install.ps1` from the new location -- it will remove the old profile block automatically. If you want to clean it up manually first:

```powershell
$p = Get-Content $PROFILE -Raw
$p = $p -replace "(?s)# --- Compound GPID.*?# --- End Compound GPID ---\r?\n?", ""
Set-Content $PROFILE $p.TrimEnd()
```

### Step B - Remove the old `bin\` directory from PATH

> **Note**: `[Environment]::GetEnvironmentVariable` is blocked in Constrained Language Mode. Use `reg.exe` instead -- it works in all language modes.

```powershell
$oldBin = "$env:USERPROFILE\.compound-gpid\bin"
$currentPath = (reg query "HKCU\Environment" /v PATH 2>$null |
    Where-Object { $_ -match 'PATH' }) -replace '.*REG_[A-Z_]+\s+', ''
$newPath = ($currentPath.Trim() -split ';' |
    Where-Object { $_ -and $_ -ne $oldBin }) -join ';'
reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d $newPath /f
```

### Step C - Delete the old clone

```powershell
Remove-Item -Path "$env:USERPROFILE\.compound-gpid" -Recurse -Force
```

### Step D - Restart your terminal and IDE

Restart your terminal **and VS Code / Positron** to pick up the PATH change, then proceed with the [Installation](installation.md) steps.

---

## `cg-link` fails with a junction/symlink error

**Cause**: Windows requires Developer Mode to create directory junctions without admin rights on some configurations.

**Fix**: Enable Developer Mode:
Settings → System → For developers → Developer Mode → On

Then retry `cg-link` from your project root.

---

> Still stuck? Open a [GitHub Issue](https://github.com/GPID-WB/compound-gpid/issues).
> 
> See [Reference](reference.md) for a full list of commands and agents.

