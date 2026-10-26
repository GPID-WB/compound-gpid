# Upgrade To v1.2.0.9024

## Who Should Use This Guide
Everyone on an older version, whether pinned or tracking `latest`. Start with a
fresh clone of the NEW release, not the old `cg-update` or `cg-link`.
These commands apply after the `v1.2.0.9024` tag is published.

## Before You Start
Close editors, terminals, and other tools that use the installation. Keep one
terminal outside the installation for migration. Back up your projects first.
You need Git and Python 3.8+; use PowerShell on Windows and bash/zsh on macOS.
Check your installed version (replace the path if your installation is elsewhere):

| Windows (PowerShell) | macOS |
|---|---|
| `git -C "$HOME\.compound-gpid" describe --tags --always` | `git -C ~/.compound-gpid describe --tags --always` |

## Get The New Release
Clone the official repository into a separate, fresh folder. Do not put this
folder inside the old installation or put the old installation inside it.
Keep this NEW clone clean and available for rollback.

| Windows (PowerShell) | macOS |
|---|---|
| `git clone --branch v1.2.0.9024 https://github.com/GPID-WB/compound-gpid.git "$HOME\compound-gpid-9024-new"` | `git clone --branch v1.2.0.9024 https://github.com/GPID-WB/compound-gpid.git "$HOME/compound-gpid-9024-new"` |

## Run Migration From The New Clone
Run the script by its full path, not an installed command. Choose ONE row:

| Installation | Windows (PowerShell) | macOS |
|---|---|---|
| Default/discovered | `& "$HOME\compound-gpid-9024-new\scripts\migrate-install.ps1"` | `bash "$HOME/compound-gpid-9024-new/scripts/migrate-install.sh"` |
| Custom path (replace example) | `& "$HOME\compound-gpid-9024-new\scripts\migrate-install.ps1" -InstallPath 'C:\WBG\.compound-gpid'` | `bash "$HOME/compound-gpid-9024-new/scripts/migrate-install.sh" --install-path "$HOME/tools/.compound-gpid"` |

If more than one installation is found, nothing is changed. Select the intended
path from the report and rerun with `-InstallPath` / `--install-path`.
Existing backups also stop migration: inspect them and use the printed rollback
command before retrying. Do not delete backups to bypass the stop.
Only standalone Git clones are supported, not worktrees or linked install paths.

## Check The Result

Expect `Migrated: ... -> v1.2.0.9024 (pinned)` and `Backup preserved: ...`.
The old folder, including local edits, stays beside the installation as
`<install>.backup-<old-version>-<timestamp>` (Windows includes milliseconds).
Those installation edits are not merged into the new clone. Keep the backup.
The new `.cg-version` pin must be `v1.2.0.9024`:

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

From each project root, use the NEW commands, in this order (same on both OSes):

| Windows (PowerShell) | macOS |
|---|---|
| `cg-link --check` | `cg-link --check` |
| `cg-link` | `cg-link` |

Keep the project's adapter selection with `--platforms` if it used one.
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

Do not run `cg-update latest` until we announce it. Today `latest` tracks `main`,
which still contains the old line. It is not the newest four-part release tag.

## Rollback

Close affected tools and stop install/update/link activity. Use the exact rollback
command printed by migration, with the original install path and backup path:

| Windows (PowerShell) | macOS |
|---|---|
| `& "$HOME\compound-gpid-9024-new\scripts\migrate-install.ps1" -InstallPath '<original-install-path>' -Rollback '<printed-backup-path>'` | `bash "$HOME/compound-gpid-9024-new/scripts/migrate-install.sh" --install-path '<original-install-path>' --rollback '<printed-backup-path>'` |

Replace the placeholders. Rollback restores the old folder and keeps the current
one at `<install>.rollback-<timestamp>`. Review PATH/profile changes manually and
open a new terminal. Rollback does NOT undo project changes; restore those only
from reviewed project backups. Installer PATH/profile writes are not snapshotted.
