# tests/helpers.Tests.ps1
# Pester tests for New-CopilotInstructions in scripts/helpers.ps1
#
# Run with: Invoke-Pester tests/helpers.Tests.ps1
# Compatible with Pester 3.4+ (ships built-in on Windows)

$repoRoot = if ($env:CG_TEST_ROOT) { $env:CG_TEST_ROOT } else { Split-Path $PSScriptRoot -Parent }
. "$PSScriptRoot/helpers.ps1"
. (Join-Path (Join-Path $repoRoot "scripts") "helpers.ps1")

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

function New-TemplateDir {
    param([string]$Root, [string]$Content = $null)
    $githubDir = Join-Path $Root ".github"
    New-Item -ItemType Directory -Path $githubDir -Force | Out-Null
    $body = if ($Content) { $Content } else {
@'
# {{project-name}}
project-type: {{project-type}}
languages: {{languages}}
review-depth: {{review-depth}}
'@
    }
    Set-Content -Path (Join-Path $githubDir "copilot-instructions.template.md") `
                -Value $body -Encoding UTF8
    return $Root
}

function New-CharterFile {
    param([string]$Root, [string]$ProjectName)
    $content = @"
---
project-name: $ProjectName
---
## Objective
Test project.
"@
    Set-Content -Path (Join-Path $Root "compound-gpid.md") -Value $content -Encoding UTF8
}

function New-LocalConfigFile {
    param([string]$Root, [string]$Language = "R", [string]$ProjectType = "analytical",
          [string]$ReviewDepth = "standard", [string]$RSyntax = $null)
    $rSyntaxLine = if ($RSyntax) { "`nr-syntax: $RSyntax" } else { "" }
    $content = @"
---
language: $Language
project-type: $ProjectType
review-depth: $ReviewDepth$rSyntaxLine
---
"@
    Set-Content -Path (Join-Path $Root "compound-gpid.local.md") -Value $content -Encoding UTF8
}

# ---------------------------------------------------------------------------
# New-CopilotInstructions - basic generation
# ---------------------------------------------------------------------------

Describe "New-CopilotInstructions - basic generation" {
    $templateDir = Join-Path $TestDrive "basic-template"
    $projectRoot = Join-Path $TestDrive "basic-project"
    New-Item -ItemType Directory -Path $projectRoot -Force | Out-Null
    New-TemplateDir -Root $templateDir | Out-Null
    New-CharterFile -Root $projectRoot -ProjectName "Poverty Analysis"
    New-LocalConfigFile -Root $projectRoot -Language "R" -ProjectType "analytical" `
                        -ReviewDepth "standard"

    $result = New-CopilotInstructions -TemplateDir $templateDir -ProjectRoot $projectRoot

    Context "output structure" {
        It "returns a non-empty string" {
            [string]::IsNullOrWhiteSpace($result) | Should Be $false
        }

        It "first line is the management marker" {
            $lines = $result -split '\r?\n'
            $lines[0] | Should Be "<!-- compound-gpid:managed -->"
        }
    }

    Context "placeholder substitution" {
        It "setup succeeded (guard: result is not null)" {
            [string]::IsNullOrWhiteSpace($result) | Should Be $false
        }

        It "replaces {{project-name}} with charter project-name" {
            ($result -match 'Poverty Analysis') | Should Be $true
        }

        It "does not contain unreplaced {{project-name}} placeholder" {
            ($result -match '\{\{project-name\}\}') | Should Be $false
        }

        It "replaces {{project-type}} with local config value" {
            ($result -match 'analytical') | Should Be $true
        }

        It "does not contain unreplaced {{project-type}} placeholder" {
            ($result -match '\{\{project-type\}\}') | Should Be $false
        }

        It "replaces {{languages}} with local config language" {
            ($result -match '\bR\b') | Should Be $true
        }

        It "does not contain unreplaced {{languages}} placeholder" {
            ($result -match '\{\{languages\}\}') | Should Be $false
        }

        It "replaces {{review-depth}} with local config value" {
            ($result -match 'standard') | Should Be $true
        }

        It "does not contain unreplaced {{review-depth}} placeholder" {
            ($result -match '\{\{review-depth\}\}') | Should Be $false
        }

        It "does not append R dialect annotation when r-syntax is not configured" {
            ($result -match '\(R dialect:') | Should Be $false
        }

        It "handles project names containing dollar signs (literal, not regex backreferences)" {
            # Regression guard for P2.1: .Replace() must be used (not -replace) so that
            # values like "R$0 Pipeline" are preserved literally in the output.
            $dollarDir  = Join-Path $TestDrive "dollar-template"
            $dollarProj = Join-Path $TestDrive "dollar-project"
            New-Item -ItemType Directory -Path $dollarProj -Force | Out-Null
            New-TemplateDir -Root $dollarDir | Out-Null
            New-CharterFile -Root $dollarProj -ProjectName 'R$0 Analysis'
            New-LocalConfigFile -Root $dollarProj -Language "R" -ProjectType "tool" `
                                -ReviewDepth "standard"
            $dollarResult = New-CopilotInstructions -TemplateDir $dollarDir -ProjectRoot $dollarProj
            # $0 must appear literally — if -replace was used it would be substituted away
            ($dollarResult -match '\$0') | Should Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# New-CopilotInstructions - R dialect appended when r-syntax is set
# ---------------------------------------------------------------------------

Describe "New-CopilotInstructions - R dialect in languages string" {
    $templateDir = Join-Path $TestDrive "dialect-template"
    $projectRoot = Join-Path $TestDrive "dialect-project"
    New-Item -ItemType Directory -Path $projectRoot -Force | Out-Null
    New-TemplateDir -Root $templateDir | Out-Null
    New-CharterFile -Root $projectRoot -ProjectName "Test"
    New-LocalConfigFile -Root $projectRoot -Language "R" -ProjectType "analytical" `
                        -ReviewDepth "standard" -RSyntax "data.table-collapse"

    $result = New-CopilotInstructions -TemplateDir $templateDir -ProjectRoot $projectRoot

    It "appends R dialect info when r-syntax is set" {
        ($result -match 'data\.table-collapse') | Should Be $true
    }

    It "includes both R and dialect in the languages string" {
        ($result -match 'R.*data\.table-collapse|data\.table-collapse.*R') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# New-CopilotInstructions - r-syntax ignored for non-R languages
# ---------------------------------------------------------------------------

Describe "New-CopilotInstructions - r-syntax does not annotate non-R language" {
    $templateDir = Join-Path $TestDrive "non-r-dialect-template"
    $projectRoot = Join-Path $TestDrive "non-r-dialect-project"
    New-Item -ItemType Directory -Path $projectRoot -Force | Out-Null
    New-TemplateDir -Root $templateDir | Out-Null
    New-CharterFile -Root $projectRoot -ProjectName "Test"
    New-LocalConfigFile -Root $projectRoot -Language "Python" -ProjectType "analytical" `
                        -ReviewDepth "standard" -RSyntax "data.table-collapse"

    $result = New-CopilotInstructions -TemplateDir $templateDir -ProjectRoot $projectRoot

    It "does not append R dialect info when language is Python" {
        ($result -match 'data\.table-collapse') | Should Be $false
    }

    It "does not inject '(R dialect:' for non-R language" {
        ($result -match '\(R dialect:') | Should Be $false
    }
}

# ---------------------------------------------------------------------------
# New-CopilotInstructions - fallbacks when charter is missing
# ---------------------------------------------------------------------------

Describe "New-CopilotInstructions - fallback when compound-gpid.md is missing" {
    $templateDir = Join-Path $TestDrive "no-charter-template"
    $projectRoot = Join-Path $TestDrive "no-charter-project"
    New-Item -ItemType Directory -Path $projectRoot -Force | Out-Null
    New-TemplateDir -Root $templateDir | Out-Null
    # No charter file — only local config
    New-LocalConfigFile -Root $projectRoot -Language "Python" -ProjectType "technical" `
                        -ReviewDepth "light"

    $result = New-CopilotInstructions -TemplateDir $templateDir -ProjectRoot $projectRoot

    It "uses <project-name> fallback when charter is absent" {
        ($result -match '<project-name>') | Should Be $true
    }

    It "still fills local config values (project-type)" {
        ($result -match 'technical') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# New-CopilotInstructions - fallbacks when local config is missing
# ---------------------------------------------------------------------------

Describe "New-CopilotInstructions - fallback when compound-gpid.local.md is missing" {
    $templateDir = Join-Path $TestDrive "no-local-template"
    $projectRoot = Join-Path $TestDrive "no-local-project"
    New-Item -ItemType Directory -Path $projectRoot -Force | Out-Null
    New-TemplateDir -Root $templateDir | Out-Null
    New-CharterFile -Root $projectRoot -ProjectName "Charter Only"
    # No local config file

    $result = New-CopilotInstructions -TemplateDir $templateDir -ProjectRoot $projectRoot

    It "uses project-name from charter" {
        ($result -match 'Charter Only') | Should Be $true
    }

    It "uses <not configured> fallback for project-type" {
        ($result -match '<not configured>') | Should Be $true
    }

    It "all three unconfigured fields (project-type, language, review-depth) fall back" {
        ([regex]::Matches($result, [regex]::Escape('<not configured>')).Count) | Should Be 3
    }
}

# ---------------------------------------------------------------------------
# New-CopilotInstructions - fallbacks when both files are missing
# ---------------------------------------------------------------------------

Describe "New-CopilotInstructions - fallback when both charter and local config are missing" {
    $templateDir = Join-Path $TestDrive "no-files-template"
    $projectRoot = Join-Path $TestDrive "no-files-project"
    New-Item -ItemType Directory -Path $projectRoot -Force | Out-Null
    New-TemplateDir -Root $templateDir | Out-Null
    # No charter, no local config

    $result = New-CopilotInstructions -TemplateDir $templateDir -ProjectRoot $projectRoot

    It "uses <project-name> fallback" {
        ($result -match '<project-name>') | Should Be $true
    }

    It "uses <not configured> fallback for language/project-type/review-depth" {
        ($result -match '<not configured>') | Should Be $true
    }

    It "still prepends the management marker" {
        $lines = $result -split '\r?\n'
        $lines[0] | Should Be "<!-- compound-gpid:managed -->"
    }
}

# ---------------------------------------------------------------------------
# New-CopilotInstructions - throws when template is missing (fail loudly)
# ---------------------------------------------------------------------------

Describe "New-CopilotInstructions - throws when template file is missing" {
    $templateDir = Join-Path $TestDrive "missing-template-dir"
    $projectRoot = Join-Path $TestDrive "missing-template-project"
    New-Item -ItemType Directory -Path $projectRoot -Force | Out-Null
    New-Item -ItemType Directory -Path $templateDir -Force | Out-Null
    # No template file under $templateDir\.github\

    It "throws when copilot-instructions.template.md is not found" {
        { New-CopilotInstructions -TemplateDir $templateDir -ProjectRoot $projectRoot } |
            Should Throw
    }
}

# ---------------------------------------------------------------------------
# copilot-instructions.template.md - file structure
# ---------------------------------------------------------------------------

Describe "copilot-instructions.template.md - file exists and contains all placeholders" {
    $templateFile = Join-Path (Join-Path $repoRoot ".github") "copilot-instructions.template.md"

    It "template file exists" {
        Test-Path $templateFile | Should Be $true
    }

    $content = if (Test-Path $templateFile) {
        Get-Content $templateFile -Raw -Encoding UTF8
    } else { "" }

    It "contains {{project-name}} placeholder" {
        ($content -match '\{\{project-name\}\}') | Should Be $true
    }

    It "contains {{project-type}} placeholder" {
        ($content -match '\{\{project-type\}\}') | Should Be $true
    }

    It "contains {{languages}} placeholder" {
        ($content -match '\{\{languages\}\}') | Should Be $true
    }

    It "contains {{review-depth}} placeholder" {
        ($content -match '\{\{review-depth\}\}') | Should Be $true
    }

    It "does not contain {{workspace-section}} (removed per P1.2 - workspace lives in context.md)" {
        ($content -match '\{\{workspace-section\}\}') | Should Be $false
    }

    It "does not contain {{essential-rules}} (static text in template, not a placeholder)" {
        ($content -match '\{\{essential-rules\}\}') | Should Be $false
    }
}

# ---------------------------------------------------------------------------
# Get-ToolsList helper - edge cases
# ---------------------------------------------------------------------------

Describe "Get-ToolsList helper - edge cases" {
    It "returns empty array for empty string" {
        $result = Get-ToolsList -Frontmatter ""
        @($result).Count | Should Be 0
    }

    It "returns empty array when no tools key present" {
        $fm = "plan: null`ndate: 2026-01-01"
        $result = Get-ToolsList -Frontmatter $fm
        @($result).Count | Should Be 0
    }

    It "parses inline array correctly" {
        $fm = "tools: ['agent', 'read', 'write']"
        $result = Get-ToolsList -Frontmatter $fm
        ($result -contains 'agent') | Should Be $true
        ($result -contains 'read') | Should Be $true
        ($result -contains 'write') | Should Be $true
    }

    It "does not match comment-prefixed tools line" {
        $fm = "# tools: 'fake'"
        $result = Get-ToolsList -Frontmatter $fm
        @($result).Count | Should Be 0
    }

    It "returns only first tools line when multiple tools: keys present (dedup guard)" {
        $fm = "tools: ['agent']`ntools: ['read', 'write']"
        $result = Get-ToolsList -Frontmatter $fm
        @($result).Count | Should Be 1
        ($result -contains 'agent') | Should Be $true
    }
}
