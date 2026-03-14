# Installation

This page covers installing Compound GPID on a new machine, linking it to a project, and upgrading from an older version.

> **New here?** See the [Home](../README.md) page for an overview of what Compound GPID is and why it exists.

---

> **Choose your install path before Step 1:**
>
> | Environment | Recommended path | Why |
> |-------------|-----------------|-----|
> | Local machine (OneDrive) | `C:\WBG\.compound-gpid` | Avoids Constrained Language Mode issues caused by OneDrive redirecting the Documents folder |
> | Remote server (no OneDrive) | `$env:USERPROFILE\.compound-gpid` | Standard user-profile location; no OneDrive/CLM concerns. **Caveat**: if your username contains spaces or `$env:USERPROFILE` resolves to a UNC path (e.g. `\\server\home\...`), use a local path instead (e.g. `C:\local\.compound-gpid`). |
>
> The scripts are fully location-agnostic — substitute your chosen path in Steps 1 and 2.

## Step 1 — Clone (once per machine)

**Local machine (OneDrive):**
```powershell
git clone https://github.com/GPID-WB/compound-gpid.git "C:\WBG\.compound-gpid"
```

**Remote server (no OneDrive):**
```powershell
git clone https://github.com/GPID-WB/compound-gpid.git "$env:USERPROFILE\.compound-gpid"
```

## Step 2 - Install (once per machine)

**Local machine (OneDrive):**
```powershell
& "C:\WBG\.compound-gpid\install.ps1"
```

**Remote server (no OneDrive):**
```powershell
& "$env:USERPROFILE\.compound-gpid\install.ps1"
```

This creates `cg-link`, `cg-unlink`, and `cg-update` as batch wrappers in the `bin\` subdirectory of your install location and adds that directory to your PATH.

> ⚠️ **IMPORTANT — After install, restart both your terminal and VS Code / Positron:**
> - **Terminal restart**: the PATH change only takes effect in new processes — `cg-link` will not be found until the terminal is restarted.
> - **VS Code / Positron restart**: Copilot must re-index the workspace to pick up new commands — restart the IDE as well.

> **Execution policy**: if PowerShell blocks the script, run:
> `powershell -ExecutionPolicy Bypass -File "<your-install-path>\install.ps1"`

## Step 3 - Link your project (once per project)

From your project root:

```powershell
cg-link
```

This creates **per-subdirectory junctions** inside `.github/` for the Compound GPID managed directories (`prompts/`, `skills/`, `agents/`, `instructions/`) and copies `copilot-instructions.md` with a management marker. Any existing `.github/` content (GitHub Actions workflows, issue templates, CODEOWNERS, etc.) is preserved untouched.

> ⚠️ **IMPORTANT — Restart VS Code / Positron after linking.**
> Copilot must re-index the workspace to see the newly linked prompts, skills, and agents.
> Without a restart, `/cg-setup` and other prompts will not be available.

> **Developer Mode**: if `cg-link` fails, enable Developer Mode in Windows Settings:
> Settings → System → For developers → Developer Mode → On

> **Managed vs. user-owned files**: files inside the junction directories (`prompts/`, `skills/`, etc.) are managed by Compound GPID - do not edit them directly. To customise `copilot-instructions.md`, remove the `<!-- compound-gpid:managed -->` marker at the top of the file; `cg-update` will then leave your version untouched.

## Step 4 - Configure your project (once per project)

Open your project in VS Code and run in Copilot Chat:

```
/cg-setup
```

This configures language preferences, project type, and review depth, and scaffolds the `.cg-docs/` directory.

---

## Updating

From any terminal:

```powershell
cg-update
```

This resets any accidental local changes and then pulls the latest version. Because the managed subdirectories use junctions to the global clone, updates are instantly visible in every linked project - no per-project update step is needed.

---

## Upgrading from an old installation (local OneDrive machines only)

> **Remote server users**: `$env:USERPROFILE\.compound-gpid` is still the correct path on a remote server — no migration needed. Simply re-run `install.ps1` from your existing clone; it is idempotent and will update your PATH and batch wrappers without a fresh clone.

> **Local OneDrive machine users**: if you have an existing installation at `$env:USERPROFILE\.compound-gpid` (the old default path from versions prior to 0.0.2), you must **migrate to `C:\WBG\.compound-gpid`** before installing the new version. Skipping this step will leave a stale PATH entry and potentially a stale PowerShell profile block that conflicts with the new install.

Follow the steps below **before** running Step 1 above.

### Step A - Remove the old `$PROFILE` block

Run `install.ps1` from the new location (Step 2) - it will remove the old profile block automatically. If you want to clean it up manually first:

```powershell
$p = Get-Content $PROFILE -Raw
$p = $p -replace "(?s)# --- Compound GPID.*?# --- End Compound GPID ---\r?\n?", ""
Set-Content $PROFILE $p.TrimEnd()
```

### Step B - Remove the old `bin\` directory from PATH

> **Note**: `[Environment]::GetEnvironmentVariable` is blocked in Constrained Language Mode. Use `reg.exe` instead - it works in all language modes.

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

### Step D — Restart your terminal and IDE

Restart your terminal **and VS Code / Positron** to pick up the PATH change, then proceed with Steps 1–4 above.

---

> **Having trouble?** Check the [Troubleshooting](troubleshooting.md) page for known issues and fixes.

