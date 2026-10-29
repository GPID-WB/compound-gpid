# Upgrade, install or remove Compound GPID

Works from any older version, today or after future releases. About 10 minutes.

- Close VS Code / Positron and other terminals first.
- Windows: use **Windows PowerShell**. macOS: use **Terminal**.
- Run all commands in the **same** window, in order.
- You need Git 2.18 or newer and Python 3.8 or newer.

## 1. Choose the version

The first lines pick the newest stable version, or the newest pre-release when
no stable version of that line exists yet.

**Windows**
```powershell
$repo = "https://github.com/GPID-WB/compound-gpid.git"
$tag = ((git ls-remote --tags --refs --sort=-v:refname $repo 'v*' | Select-Object -First 1) -split '/')[-1]
$base = ($tag -split '\.')[0..2] -join '.'
if (git ls-remote --tags $repo "refs/tags/$base") { $tag = $base }
# Or a specific version instead (remove the # and edit):
# $tag = 'v1.2.0.9025'
$tag
```

**macOS**
```bash
repo="https://github.com/GPID-WB/compound-gpid.git"
tag=$(git ls-remote --tags --refs --sort=-v:refname "$repo" 'v*' | head -n 1 | sed 's#.*/##')
base=$(printf '%s' "$tag" | cut -d. -f1-3)
git ls-remote --exit-code --tags "$repo" "refs/tags/$base" >/dev/null && tag="$base"
# Or a specific version instead (remove the # and edit):
# tag=v1.2.0.9025
echo "$tag"
```

## 2. Check what you have now

**Windows**
```powershell
foreach ($p in "C:\WBG\.compound-gpid", "$HOME\.compound-gpid") { if (Test-Path "$p\.git") { "$p -> $(git -C $p describe --tags --always)" } }
```

**macOS**
```bash
git -C "$HOME/.compound-gpid" describe --tags --always
```

| You see | Go to |
|---|---|
| `v1.2.0.9024` or newer (for example `v1.2.0.9025`, `v2.0.0`) | **3B** |
| An older version (for example `v1.1.11`, `v1.2.0.9021`) | **3A** |
| Nothing, or an error | **5** (fresh install) |

## 3A. One-time upgrade (older versions)

**Windows**
```powershell
$new = "$HOME\compound-gpid-$tag"
git clone --branch $tag $repo $new
& "$new\scripts\migrate-install.ps1"
```

**macOS**
```bash
new="$HOME/compound-gpid-$tag"
git clone --branch "$tag" "$repo" "$new"
bash "$new/scripts/migrate-install.sh"
```

Success ends with `Migrated: ... -> <version> (pinned)`. Your old folder is kept as
a backup, and the script prints a rollback command: keep it. Keep the
`compound-gpid-<version>` folder too. Continue with **4**.

## 3B. Quick update (v1.2.0.9024 or newer)

**Windows**
```powershell
Set-Location $HOME
cg-update $tag
```

**macOS**
```bash
cd "$HOME" && cg-update "$tag"
```

Run it from your home folder, not inside a project. Continue with **4**.

## 4. Refresh each project

Open a **new** terminal. In each project folder:
```text
cg-link --check
cg-link
```

- Add `--platforms` if you use only some tools, for example `cg-link --platforms kilo`.
  Values: `copilot`, `claude-code`, `codex`, `opencode`, `kilo`, or `all` (the default).
- "Manual action required" means files you edited were kept. Review them.
- Restart your editor.

## 5. Fresh install (new computer, or after removal)

Run step 1 first, then:

**Windows**
```powershell
$cg = "C:\WBG\.compound-gpid"     # on a remote server use: "$HOME\.compound-gpid"
git clone --branch $tag $repo $cg
Set-Content -LiteralPath "$cg\.cg-version" -Value $tag
& "$cg\install.ps1"
```

**macOS**
```bash
cg="$HOME/.compound-gpid"
git clone --branch "$tag" "$repo" "$cg"
printf '%s\n' "$tag" > "$cg/.cg-version"
bash "$cg/scripts/install.sh"
```

Restart your terminal and editor, then do step 4.

## 6. Remove completely

First, in each project you want to clean (optional), run `cg-unlink`.

**Windows**
```powershell
$cg = Split-Path (Split-Path (Get-Command cg-link.cmd -ErrorAction Stop).Source)   # if this fails: $cg = "C:\WBG\.compound-gpid"
& "$cg\install.ps1" -Uninstall
Remove-Item -LiteralPath $cg -Recurse -Force
Get-ChildItem -LiteralPath (Split-Path $cg) -Directory -Filter "$(Split-Path $cg -Leaf).backup-*" | Remove-Item -Recurse -Force
```

**macOS**
```bash
cg="$(cd "$(dirname "$(command -v cg-link)")/.." && pwd)"   # if this fails: cg="$HOME/.compound-gpid"
bash "$cg/scripts/install.sh" --uninstall
rm -rf "$cg"
find "$(dirname "$cg")" -maxdepth 1 -name "$(basename "$cg").backup-*" -exec rm -rf {} +
```

Deleting the folder also deletes any edits you made inside it. Restart your
terminal and editor. To install again, run steps 1 and 5.

## Other choices

- **Follow `main` (unreleased changes) instead of a version** (only on v1.2.0.9024
  or newer): `cg-update latest`. To go back to a version: `cg-update $tag`.

## If something stops

| Message | What to do |
|---|---|
| `running scripts is disabled` (Windows) | Run the same script as `powershell -ExecutionPolicy Bypass -File "<script>.ps1" <same options>` |
| `Multiple installations found` | Run step 3A's last line again with your path: `-InstallPath "C:\WBG\.compound-gpid"` (macOS: `--install-path "$HOME/.compound-gpid"`) |
| `Existing backup found` | You upgraded before: use **3B** |
| `No installation found` | Use **5** |
| `already exists and is not an empty directory` | You cloned before: delete that folder, or use another folder name |
| A PATH warning | Open a new terminal and follow the line the script printed |
| Anything else | Copy the full output and open an issue: https://github.com/GPID-WB/compound-gpid/issues |

Full details: https://gpid-wb.github.io/compound-gpid/#page=upgrade

## Details

### Who Should Use This Guide
Use this guide for any older installed version, whether pinned to a tag or
tracking `latest`. Start with a fresh clone of the newest published release,
not the OLD installation's `cg-update` or `cg-link`.

If your old `cg-update` already ran and something looks wrong, follow the same
steps; your old folder is kept as a backup.

### Before You Start
Close editors, terminals, and other tools that use the installation. Keep one
terminal outside the installation for migration. Back up your projects first.
Stop all install/update/link activity while migrating or rolling back.
You need Git and Python 3.8+; use PowerShell 5.1+ on Windows and bash on macOS
(with bash or zsh as your login shell).
Check your installed version (replace the path if your installation is elsewhere):

| Windows (PowerShell) | macOS |
|---|---|
| `git -C "$HOME\.compound-gpid" describe --tags --always` | `git -C ~/.compound-gpid describe --tags --always` |

### Get The New Release
Clone the official repository into a separate, fresh folder. Do not put this
folder inside the old installation or put the old installation inside it.
Keep this NEW clone clean and available for rollback. The destination must not
already exist, and its parent directory must exist and be writable.

Choose the release with step 1, then use the clone command in step 3A with your
full destination path. The examples below use `"$HOME\compound-gpid-new"` on Windows
and `"$HOME/compound-gpid-new"` on macOS; substitute your actual path throughout.

### Run Migration From The New Clone
Run the script by its full path, not an installed command. Choose ONE row:

| Installation | Windows (PowerShell) | macOS |
|---|---|---|
| Default/discovered | `& "$HOME\compound-gpid-new\scripts\migrate-install.ps1"` | `bash "$HOME/compound-gpid-new/scripts/migrate-install.sh"` |
| Explicit path (replace example) | `& "$HOME\compound-gpid-new\scripts\migrate-install.ps1" -InstallPath 'C:\WBG\.compound-gpid'` | `bash "$HOME/compound-gpid-new/scripts/migrate-install.sh" --install-path "$HOME/.compound-gpid"` |

On Windows, use `-InstallPath "$HOME\.compound-gpid"` instead if that is your
installation location, rather than `C:\WBG\.compound-gpid` on the local machine.

If Windows execution policy blocks the NEW script, use this fallback, appending
`-InstallPath '<actual-install-path>'` when selecting an explicit installation:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\compound-gpid-new\scripts\migrate-install.ps1"
```

If the script reports `Multiple installations found`, nothing is changed. Select
the intended path from the report and rerun the NEW script with `-InstallPath`
(Windows) or `--install-path` (macOS), as in the explicit-path row.
Existing backups also stop migration: inspect them and use the printed rollback
command before retrying. Do not delete backups to bypass the stop.
Only standalone Git clones are supported, not worktrees or linked install paths.

### Check The Result

Expect `Migrated: ... -> <new-release-tag> (pinned)` and `Backup preserved: ...`,
where the new tag matches the version chosen in step 1.
The old folder, including local edits, stays beside the installation as
`<install>.backup-<old-version>-<timestamp>` (Windows includes milliseconds).
Those installation edits are not merged into the new clone. Keep the backup.
The new `.cg-version` pin must match that tag:

| Windows (PowerShell) | macOS |
|---|---|
| `Get-Content -LiteralPath "$HOME\.compound-gpid\.cg-version"` | `cat "$HOME/.compound-gpid/.cg-version"` |
| `Get-Command cg-link -All -CommandType Application` | `command -v cg-link` |

Use your actual install path above. Open a NEW terminal before checking command
resolution: `cg-link` must point to that installation's `bin` directory.
A PATH warning means the verified new installation was kept, but a fresh shell
could not resolve its `cg-update`. Follow the exact repair line printed by the
script; remove the reported old/shadowing bin entry from User/Machine PATH on
Windows or your shell profile on macOS. Open a new terminal and check again.
Do not run a shadowing old command.

### In Each Project

Migration replaces the installation but does not reconcile project files.
From each project root, after verifying command resolution, use the NEW
`cg-link` once per project, with a read-only check first (same on both OSes):

| Windows (PowerShell) | macOS |
|---|---|
| `cg-link --check` | `cg-link --check` |
| `cg-link` | `cg-link` |

Keep the project's intended adapter selection with `--platforms` on both
commands if it used one. For example, a Copilot-only project uses
`cg-link --check --platforms copilot`, then `cg-link --platforms copilot`.
Supported values are `copilot`, `claude-code`, `codex`, `opencode`, and `kilo`,
in a comma-separated list, or `all`. Without this option, all are selected.
`--check` is read-only: it does not update, launch Kilo, or write project/global
files. Exit `1` means a block or preserved conflict; review it before linking.
"Manual action required" means edited or unproven files are kept, not silently
overwritten. User-added files are kept. Review the listed paths; do not delete
adapter folders or use unlink as a cleanup shortcut.
One exception is the first transition of legacy managed Copilot instructions:
`.github/copilot-instructions.md` is backed up byte-for-byte to
`.github/copilot-instructions.md.pre-9024.bak` before replacement. Review and
merge your custom instructions from that backup. An existing backup is kept;
a conflicting transition needs manual action. Restart your editor after linking.

### Stay Pinned

Migration pins the replacement installation to the release tag above, even if
the old installation tracked `latest`. Keep that pin. The keyword `latest`
means tracking `main`, not selecting the newest published release tag; switching
to that mode is not part of this upgrade procedure.

### Rollback

Close affected tools and stop install/update/link activity. Use the exact rollback
command printed by migration, with the original install path and backup path:

| Windows (PowerShell) | macOS |
|---|---|
| `& "$HOME\compound-gpid-new\scripts\migrate-install.ps1" -InstallPath '<original-install-path>' -Rollback '<printed-backup-path>'` | `bash "$HOME/compound-gpid-new/scripts/migrate-install.sh" --install-path '<original-install-path>' --rollback '<printed-backup-path>'` |

Replace the placeholders with the exact paths printed by migration. Rollback is
an explicit mode: `-Rollback` requires `-InstallPath`, and `--rollback` requires
`--install-path`. On Windows, the execution-policy fallback above also accepts
these two parameters after the script path. Use the NEW script, not an old updater.
Rollback restores the old folder and keeps the current
one at `<install>.rollback-<timestamp>`. Review PATH/profile changes manually and
open a new terminal. Rollback does NOT undo project changes; restore those only
from reviewed project backups. Installer PATH/profile writes are not snapshotted.
Keep the preserved folders until you have verified the installation and projects;
do not rename, edit, or delete backups to bypass a safety stop. If migration
fails, read its restore result: it attempts to restore the old folder, but if
automatic restore fails, preserve both folders and follow the printed rollback
command only after inspection.
