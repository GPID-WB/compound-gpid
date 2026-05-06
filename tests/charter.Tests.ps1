# tests/charter.Tests.ps1
# Pester tests validating compound-gpid.md charter structure and frontmatter.
# Also validates that .cg-docs/archive/ is scaffolded (dogfooding check).
#
# Run with: Invoke-Pester tests/charter.Tests.ps1
# Compatible with Pester 3.4+ (ships built-in on Windows)

$repoRoot = Split-Path -Parent $PSScriptRoot

Describe "compound-gpid.md - file exists" {
    It "compound-gpid.md is present in the project root" {
        $charterPath = Join-Path $repoRoot "compound-gpid.md"
        Test-Path $charterPath | Should Be $true
    }
}

Describe "compound-gpid.md - YAML frontmatter" {
    $charterPath = Join-Path $repoRoot "compound-gpid.md"
    $content     = if (Test-Path $charterPath) { Get-Content $charterPath -Raw } else { "" }

    # Extract the YAML block between the first two --- delimiters
    $yamlBlock = if ($content -match "(?s)^---\s*\r?\n(.+?)\r?\n---") { $Matches[1] } else { "" }

    Context "required fields" {
        It "contains project-name" {
            ($yamlBlock -match 'project-name\s*:') | Should Be $true
        }

        It "contains created" {
            ($yamlBlock -match 'created\s*:') | Should Be $true
        }

        It "contains last-reviewed" {
            ($yamlBlock -match 'last-reviewed\s*:') | Should Be $true
        }
    }

    Context "last-reviewed format" {
        It "last-reviewed value is a valid YYYY-MM-DD date" {
            $match = [regex]::Match($yamlBlock, 'last-reviewed\s*:\s*["\'']?(\d{4}-\d{2}-\d{2})["\'']?')
            $match.Success | Should Be $true

            if ($match.Success) {
                $dateValue = $match.Groups[1].Value
                # Validate using a strict regex (month 01-12, day 01-31)
                $isValid = $dateValue -match '^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$'
                $isValid | Should Be $true
            }
        }

        It "last-reviewed is not set to a future date" {
            $match = [regex]::Match($yamlBlock, 'last-reviewed\s*:\s*["\'']?(\d{4}-\d{2}-\d{2})["\'']?')
            $match.Success | Should Be $true
            $dateValue = $match.Groups[1].Value
            $today     = Get-Date -Format 'yyyy-MM-dd'
            # ISO date strings compare chronologically
            ($dateValue -le $today) | Should Be $true
        }
    }
}

Describe "compound-gpid.md - section structure" {
    $charterPath = Join-Path $repoRoot "compound-gpid.md"
    $content     = if (Test-Path $charterPath) { Get-Content $charterPath -Raw } else { "" }

    # Extract all ## headings from the body (after the closing ---)
    $body = if ($content -match "(?s)^---.*?---\r?\n(.*)") { $Matches[1] } else { $content }

    Context "canonical sections present" {
        It "has an Objective section" {
            ($body -match '(?m)^## Objective') | Should Be $true
        }

        It "has a Key Deliverables section" {
            ($body -match '(?m)^## Key Deliverables') | Should Be $true
        }

        It "has a Constraints section" {
            ($body -match '(?m)^## Constraints') | Should Be $true
        }

        It "has a Current Focus section" {
            ($body -match '(?m)^## Current Focus') | Should Be $true
        }
    }

    Context "no deprecated sections" {
        It "does not contain Architecture Notes section" {
            ($body -match '(?m)^## Architecture Notes') | Should Be $false
        }

        It "does not contain Roadmap section" {
            ($body -match '(?m)^## Roadmap') | Should Be $false
        }

        It "does not contain Related Resources section" {
            ($body -match '(?m)^## Related Resources') | Should Be $false
        }
    }

    Context "section count" {
        It "has exactly four level-2 sections" {
            # Split into lines and count those starting with '## ' (followed by non-whitespace)
            $sectionCount = @($body -split '\r?\n' | Where-Object { $_ -match '^##\s+\S' }).Count
            $sectionCount | Should Be 4
        }
    }
}

Describe ".cg-docs/archive/ - scaffold present" {
    # P2.13: validate that the archive directory is scaffolded in this project

    It ".cg-docs/archive/ directory exists" {
        $archivePath = Join-Path (Join-Path $repoRoot ".cg-docs") "archive"
        Test-Path $archivePath | Should Be $true
    }

    It ".cg-docs/archive/ is tracked via .gitkeep" {
        $gitkeepPath = Join-Path (Join-Path (Join-Path $repoRoot ".cg-docs") "archive") ".gitkeep"
        Test-Path $gitkeepPath | Should Be $true
    }
}

Describe "Charter archiving rules - format in copilot-instructions.md" {
    $instructionsPath = Join-Path (Join-Path $repoRoot ".github") "copilot-instructions.md"
    $content = if (Test-Path $instructionsPath) { Get-Content $instructionsPath -Raw } else { "" }

    It "copilot-instructions.md exists" {
        Test-Path $instructionsPath | Should Be $true
    }

    It "references .cg-docs/archive/charter-history.md as the archive destination" {
        ($content -match '\.cg-docs[/\\]archive[/\\]charter-history\.md') | Should Be $true
    }

    It "instructs creating the archive directory if it does not exist" {
        ($content -match "create.*directory|create.*dir") | Should Be $true
    }
}
