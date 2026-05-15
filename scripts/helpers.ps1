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

        Falls back to placeholder values when charter or local config files are absent --
        never fails silently on missing config (only on missing template).
    .PARAMETER TemplateDir
        Path to the Compound GPID installation directory (parent of .github\).
    .PARAMETER ProjectRoot
        Path to the consumer project root directory. When called from update.ps1,
        pass (Get-Location) after Pop-Location -- at that point it resolves to
        the consumer project root, not the compound-gpid install dir.
    .EXAMPLE
        $content = New-CopilotInstructions -TemplateDir "C:\WBG\.compound-gpid" -ProjectRoot (Get-Location)
        Set-Content -Path ".github\copilot-instructions.md" -Value $content
    .OUTPUTS
        System.String
        Generated copilot-instructions.md content with the management marker
        prepended. Write with Set-Content -- do not pipe directly into New-Item.
    #>
    param(
        [Parameter(Mandatory)][string]$TemplateDir,
        [Parameter(Mandatory)][string]$ProjectRoot
    )

    if (-not (Test-Path -Path $ProjectRoot -PathType Container)) {
        throw "ProjectRoot does not exist or is not a directory: '$ProjectRoot'"
    }

    $marker       = "<!-- compound-gpid:managed -->"
    $templatePath = Join-Path $TemplateDir ".github\copilot-instructions.template.md"

    if (-not (Test-Path $templatePath)) {
        throw "Compound GPID template not found at: $templatePath. The installation may be corrupted -- run cg-update --fix."
    }

    $template = Get-Content $templatePath -Raw -Encoding UTF8
    if ([string]::IsNullOrWhiteSpace($template)) {
        throw "Template file is empty: $templatePath. Installation may be corrupted -- run cg-update --fix."
    }

    # --- Read project-name from compound-gpid.md frontmatter ---
    $charterPath = Join-Path $ProjectRoot "compound-gpid.md"
    $projectName = "<project-name>"
    if (Test-Path $charterPath) {
        $charterContent = Get-Content $charterPath -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        # Match YAML frontmatter block (--- ... ---) and extract project-name
        if ($charterContent -match '(?s)^---[ \t]*\r?\n(.*?)\r?\n---') {
            $fm = $Matches[1]
            if ($fm -match '(?m)^\s*project-name:\s*["\x27]?([^"''\r\n]+)["\x27]?\s*$') {
                $val = $Matches[1].Trim()
                if (-not [string]::IsNullOrWhiteSpace($val)) { $projectName = $val }
            }
        }
    }

    # --- Read language, project-type, review-depth, r-syntax, modules from compound-gpid.local.md ---
    $localPath   = Join-Path $ProjectRoot "compound-gpid.local.md"
    $language    = "<not configured>"
    $projectType = "<not configured>"
    $reviewDepth = "<not configured>"
    $modules     = "engineering"
    $rSyntax     = $null
    if (Test-Path $localPath) {
        $localContent = Get-Content $localPath -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        if ($localContent -match '(?s)^---[ \t]*\r?\n(.*?)\r?\n---') {
            $fm = $Matches[1]
            if ($fm -match '(?m)^\s*language:\s*["\x27]?([^"''\r\n]+)["\x27]?\s*$')      { $language    = $Matches[1].Trim() }
            if ($fm -match '(?m)^\s*project-type:\s*["\x27]?([^"''\r\n]+)["\x27]?\s*$')  { $projectType = $Matches[1].Trim() }
            if ($fm -match '(?m)^\s*review-depth:\s*["\x27]?([^"''\r\n]+)["\x27]?\s*$')  { $reviewDepth = $Matches[1].Trim() }
            if ($fm -match '(?m)^\s*r-syntax:\s*["\x27]?([^"''\r\n]+)["\x27]?\s*$')      { $rSyntax     = $Matches[1].Trim() }
            if ($fm -match '(?m)^\s*modules:\s*["\x27]?([^"''\r\n]+)["\x27]?\s*$')       { $modules     = $Matches[1].Trim() }
        }
    }

    # Validate modules: field
    # Reject YAML list/array notation (e.g. modules: [engineering, research] or modules:\n  - research)
    # which the single-line regex would either miss entirely or capture with brackets verbatim.
    if ($modules -match '^\[') {
        throw "Invalid modules format in compound-gpid.local.md: YAML list notation is not supported. Use a quoted string: modules: ""engineering, research"""
    }
    # Allowlist: only recognized module names are accepted
    $validModules = @('engineering', 'research', 'engineering, research', 'research, engineering')
    if ($validModules -notcontains $modules) {
        throw "Invalid modules value '$modules' in compound-gpid.local.md. Valid values: $($validModules -join ', ')"
    }

    # Build languages string -- append R dialect when configured
    $languages = $language
    if ($null -ne $rSyntax -and $language -match '(?i)\bR\b') {
        $languages = "$language (R dialect: $rSyntax)"
    }

    # --- Fill template placeholders ---
    # Use the .Replace() string method (literal substitution) rather than the
    # -replace operator (which interprets $0, $1 etc. in the replacement as
    # regex backreferences and would silently corrupt values like "R$0 Pipeline").
    # Guard: reject config values that contain placeholder tokens to prevent
    # cross-injection (e.g. a project-name of "{{project-type}}" would corrupt the output).
    foreach ($val in @($projectName, $projectType, $languages, $reviewDepth, $modules)) {
        if ($val -match '\{\{') {
            throw "A config value contains a placeholder token ('{{') which would corrupt the generated output. Check compound-gpid.md and compound-gpid.local.md."
        }
    }

    $output = $template
    $output = $output.Replace('{{project-name}}', $projectName)
    $output = $output.Replace('{{project-type}}', $projectType)
    $output = $output.Replace('{{languages}}',    $languages)
    $output = $output.Replace('{{review-depth}}', $reviewDepth)
    $output = $output.Replace('{{modules}}',      $modules)

    # Prepend the managed marker so cg-link/cg-update can identify managed files
    # Match the template's line-ending style to avoid mixed line endings.
    $sep = "`n"
    if ($output -match '\r\n') { $sep = "`r`n" }
    return $marker + $sep + $output
}

function Update-ManagedInstructionsFile {
    <#
    .SYNOPSIS
        Refreshes a CG-managed copilot-instructions.md if content has changed.
    .DESCRIPTION
        Reads the file at Dest. If it contains the management marker, regenerates
        content via New-CopilotInstructions and writes back only if content changed.
        This is the testable core of update.ps1's refresh logic.
    .PARAMETER Dest
        Path to the copilot-instructions.md to refresh.
    .PARAMETER Marker
        The management marker string that identifies a CG-managed file.
    .PARAMETER TemplateDir
        Path to the Compound GPID installation directory (parent of .github\).
    .PARAMETER ProjectRoot
        Path to the consumer project root directory.
    .OUTPUTS
        System.String
        "refreshed"  -- file was regenerated and written.
        "up-to-date" -- content unchanged, no write performed.
        "skipped"    -- file has no management marker; treated as user-managed.
    #>
    param(
        [Parameter(Mandatory)][string]$Dest,
        [Parameter(Mandatory)][string]$Marker,
        [Parameter(Mandatory)][string]$TemplateDir,
        [Parameter(Mandatory)][string]$ProjectRoot
    )
    $existing = Get-Content $Dest -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    if (-not ($existing -and $existing -match [regex]::Escape($Marker))) {
        return "skipped"
    }
    $generated = New-CopilotInstructions -TemplateDir $TemplateDir -ProjectRoot $ProjectRoot
    if ($generated -ne $existing) {
        Set-Content -Path $Dest -Value $generated -Encoding UTF8
        return "refreshed"
    }
    return "up-to-date"
}
