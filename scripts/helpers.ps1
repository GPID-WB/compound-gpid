# scripts/helpers.ps1
# Shared constants and helpers dot-sourced by link.ps1 and update.ps1.

# Static guidance shown when the Compound GPID install directory is missing.
# The directory path itself is interpolated by each calling script.
$CG_INSTALL_GUIDANCE = @"

This script expects to run from within a Compound GPID installation.
See docs/installation.md for setup instructions and path guidance.
  # Local machine (OneDrive):  git clone https://github.com/GPID-WB/compound-gpid.git "C:\WBG\.compound-gpid"
  # Remote server:             git clone https://github.com/GPID-WB/compound-gpid.git "`$env:USERPROFILE\.compound-gpid"
  # Then run: & "<your-path>\install.ps1"
"@
