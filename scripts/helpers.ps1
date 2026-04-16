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

function New-CopilotInstructions {
    <#
    .SYNOPSIS
        Generates a slim, project-specific copilot-instructions.md from the Compound GPID template.
    .DESCRIPTION
        Reads the template from TemplateDir\.github\copilot-instructions.template.md,
        reads project-specific values from compound-gpid.md and compound-gpid.local.md
        in ProjectRoot, fills placeholders, and returns the generated content with
        the management marker prepended.

        Falls back to placeholder values when charter or local config files are absent —
        never fails silently on missing config (only on missing template).
    .PARAMETER TemplateDir
        Path to the Compound GPID installation directory (parent of .github\).
    .PARAMETER ProjectRoot
        Path to the consumer project root directory. When called from update.ps1,
        pass (Get-Location) after Pop-Location — at that point it resolves to
        the consumer project root, not the compound-gpid install dir.
    .EXAMPLE
        $content = New-CopilotInstructions -TemplateDir "C:\WBG\.compound-gpid" -ProjectRoot (Get-Location)
        Set-Content -Path ".github\copilot-instructions.md" -Value $content
    #>
    param(
        [Parameter(Mandatory)][string]$TemplateDir,
        [Parameter(Mandatory)][string]$ProjectRoot
    )

    $marker       = "<!-- compound-gpid:managed -->"
    $templatePath = Join-Path $TemplateDir ".github\copilot-instructions.template.md"

    if (-not (Test-Path $templatePath)) {
        throw "Compound GPID template not found at: $templatePath. The installation may be corrupted — run cg-update --fix."
    }

    $template = Get-Content $templatePath -Raw

    # --- Read project-name from compound-gpid.md frontmatter ---
    $charterPath = Join-Path $ProjectRoot "compound-gpid.md"
    $projectName = "<project-name>"
    if (Test-Path $charterPath) {
        $charterContent = Get-Content $charterPath -Raw -ErrorAction SilentlyContinue
        # Match YAML frontmatter block (--- ... ---) and extract project-name
        if ($charterContent -match '(?s)^---\s*\r?\n(.*?)\r?\n---') {
            $fm = $Matches[1]
            if ($fm -match '(?m)^\s*project-name:\s*"?([^"\r\n]+)"?\s*$') {
                $val = $Matches[1].Trim()
                if (-not [string]::IsNullOrWhiteSpace($val)) { $projectName = $val }
            }
        }
    }

    # --- Read language, project-type, review-depth, r-syntax from compound-gpid.local.md ---
    $localPath   = Join-Path $ProjectRoot "compound-gpid.local.md"
    $language    = "<not configured>"
    $projectType = "<not configured>"
    $reviewDepth = "<not configured>"
    $rSyntax     = $null
    if (Test-Path $localPath) {
        $localContent = Get-Content $localPath -Raw -ErrorAction SilentlyContinue
        if ($localContent -match '(?s)^---\s*\r?\n(.*?)\r?\n---') {
            $fm = $Matches[1]
            if ($fm -match '(?m)^\s*language:\s*"?([^"\r\n]+)"?\s*$')      { $language    = $Matches[1].Trim() }
            if ($fm -match '(?m)^\s*project-type:\s*"?([^"\r\n]+)"?\s*$')  { $projectType = $Matches[1].Trim() }
            if ($fm -match '(?m)^\s*review-depth:\s*"?([^"\r\n]+)"?\s*$')  { $reviewDepth = $Matches[1].Trim() }
            if ($fm -match '(?m)^\s*r-syntax:\s*"?([^"\r\n]+)"?\s*$')      { $rSyntax     = $Matches[1].Trim() }
        }
    }

    # Build languages string — append R dialect when configured
    $languages = $language
    if ($null -ne $rSyntax -and $language -match '(?i)\bR\b') {
        $languages = "$language (R dialect: $rSyntax)"
    }

    # --- Fill template placeholders ---
    # Use the .Replace() string method (literal substitution) rather than the
    # -replace operator (which interprets $0, $1 etc. in the replacement as
    # regex backreferences and would silently corrupt values like "R$0 Pipeline").
    $output = $template
    $output = $output.Replace('{{project-name}}', $projectName)
    $output = $output.Replace('{{project-type}}', $projectType)
    $output = $output.Replace('{{languages}}',    $languages)
    $output = $output.Replace('{{review-depth}}', $reviewDepth)

    # Prepend the managed marker so cg-link/cg-update can identify managed files
    return $marker + "`n" + $output
}
