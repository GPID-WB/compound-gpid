# Upgrade from an older version

## Quick steps
For step 2, use this clone command with your OS's destination from the table:
`git clone --branch v1.2.0.9025 https://github.com/GPID-WB/compound-gpid.git "<NEW-CLONE>"`

| Step | Windows (PowerShell) | macOS (bash) |
|---|---|---|
| 1. Close tools | Close editors and other terminals; keep one terminal outside the installation. | Close editors and other terminals; keep one terminal outside the installation. |
| 2. Clone the newest release | Use `"$HOME\compound-gpid-new"` as the destination in the command above. | Use `"$HOME/compound-gpid-new"` as the destination in the command above. |
| 3. Run migration by full path | `& "$HOME\compound-gpid-new\scripts\migrate-install.ps1"` | `bash "$HOME/compound-gpid-new/scripts/migrate-install.sh"` |
| 4. Open a new terminal | Open a new terminal to load the NEW commands. | Open a new terminal to load the NEW commands. |
| 5. Link each project | From each project root, run `cg-link`, with `--platforms` if you use one. | From each project root, run `cg-link`, with `--platforms` if you use one. |

The rest of this page explains each step and what to do if something stops.

## Who Should Use This Guide
Use this guide for any older installed version, whether pinned to a tag or
tracking `latest`. Start with a fresh clone of the newest published release,
not the OLD installation's `cg-update` or `cg-link`.

If your old `cg-update` already ran and something looks wrong, follow the same
steps; your old folder is kept as a backup.

## Before You Start
Close editors, terminals, and other tools that use the installation. Keep one
terminal outside the installation for migration. Back up your projects first.
Stop all install/update/link activity while migrating or rolling back.
You need Git and Python 3.8+; use PowerShell 5.1+ on Windows and bash on macOS
(with bash or zsh as your login shell).
Check your installed version (replace the path if your installation is elsewhere):

| Windows (PowerShell) | macOS |
|---|---|
| `git -C "$HOME\.compound-gpid" describe --tags --always` | `git -C ~/.compound-gpid describe --tags --always` |

## Get The New Release
Clone the official repository into a separate, fresh folder. Do not put this
folder inside the old installation or put the old installation inside it.
Keep this NEW clone clean and available for rollback. The destination must not
already exist, and its parent directory must exist and be writable.

Use the clone command in Quick steps, replacing `<NEW-CLONE>` with your full
destination path. The examples below use `"$HOME\compound-gpid-new"` on Windows
and `"$HOME/compound-gpid-new"` on macOS; substitute your actual path throughout.

## Run Migration From The New Clone
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

## Check The Result

Expect `Migrated: ... -> <new-release-tag> (pinned)` and `Backup preserved: ...`,
where the new tag matches the clone command in Quick steps.
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

## In Each Project

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

## Stay Pinned

Migration pins the replacement installation to the release tag above, even if
the old installation tracked `latest`. Keep that pin. The keyword `latest`
means tracking `main`, not selecting the newest published release tag; switching
to that mode is not part of this upgrade procedure.

## Rollback

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
