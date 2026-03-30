# tests/roadmap.Tests.ps1
# Pester tests for roadmap.json schema validation, milestone status calculation,
# and /cg-resume scope health nudge logic.
#
# Run with: Invoke-Pester tests/roadmap.Tests.ps1
# Compatible with Pester 3.4+ (ships built-in on Windows)

# ---------------------------------------------------------------------------
# Pure PowerShell helper functions (no LLM) -- mirrors @cg-roadmap agent logic
# ---------------------------------------------------------------------------

function Get-MilestoneStatus {
    <#
    .SYNOPSIS
    Derives milestone status from its features array.

    .DESCRIPTION
    Applies the ordered cascade defined in the @cg-roadmap agent spec:
    1. Empty features array  -> "planned"
    2. ALL features "done"   -> "done"
    3. ANY feature "active"  -> "in-progress"
    4. ANY feature "done" (but not all, none active) -> "in-progress"
    5. Otherwise (all "idea"/"planned" or mix) -> "planned"

    .PARAMETER Features
    Array of feature objects. Each must have a "status" property.

    .EXAMPLE
    Get-MilestoneStatus @()                          # "planned"
    Get-MilestoneStatus @(@{status="done"})           # "done"
    Get-MilestoneStatus @(@{status="active"})         # "in-progress"
    #>
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [object[]]$Features
    )

    if ($Features.Count -eq 0) { return "planned" }

    $allDone   = ($Features | Where-Object { $_.status -ne "done" }).Count -eq 0
    $anyActive = ($Features | Where-Object { $_.status -eq "active" }).Count -gt 0
    $anyDone   = ($Features | Where-Object { $_.status -eq "done" }).Count -gt 0

    if ($allDone)   { return "done" }
    if ($anyActive) { return "in-progress" }
    if ($anyDone)   { return "in-progress" }
    return "planned"
}

function Get-ScopeHealthNudge {
    <#
    .SYNOPSIS
    Returns $true when more than 60% of all features are unstarted.

    .DESCRIPTION
    Unstarted means status is "idea" or "planned".
    Returns $false when the feature list is empty (no divide-by-zero).

    .PARAMETER Features
    Flat array of all feature objects across all milestones.

    .EXAMPLE
    Get-ScopeHealthNudge @()   # $false
    Get-ScopeHealthNudge @(@{status="idea"},@{status="idea"},@{status="done"})  # $true  (67%)
    #>
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [object[]]$Features
    )

    if ($Features.Count -eq 0) { return $false }

    $unstarted = ($Features | Where-Object { $_.status -eq "idea" -or $_.status -eq "planned" }).Count
    $ratio = $unstarted / $Features.Count
    return $ratio -gt 0.60
}

function Test-RoadmapSchema {
    <#
    .SYNOPSIS
    Validates a roadmap hashtable against the compound-gpid-roadmap-v1 schema.
    Returns a list of error strings; empty list means valid.

    .PARAMETER Roadmap
    Hashtable or PSCustomObject representing parsed roadmap.json.
    #>
    param(
        [Parameter(Mandatory = $true)]
        $Roadmap
    )

    $errors = @()
    $validMilestoneStatuses = @("planned", "in-progress", "done")
    $validFeatureStatuses   = @("idea", "planned", "active", "done")
    $idPattern = '^[a-z0-9]+(-[a-z0-9]+)*$'

    if (-not $Roadmap.schemaVersion) {
        $errors += "Missing required field: schemaVersion"
    } elseif ($Roadmap.schemaVersion -ne "compound-gpid-roadmap-v1") {
        $errors += "Invalid schemaVersion: $($Roadmap.schemaVersion)"
    }

    if ($null -eq $Roadmap.milestones) {
        $errors += "Missing required field: milestones"
        return $errors
    }

    if ($Roadmap.milestones -is [string]) {
        $errors += "milestones must be an array"
        return $errors
    }

    $milestoneIds = @()
    foreach ($m in $Roadmap.milestones) {
        if (-not $m.id) {
            $errors += "Milestone missing id"
        } elseif ($m.id -notmatch $idPattern) {
            $errors += "Milestone id '$($m.id)' is not valid kebab-case"
        } elseif ($milestoneIds -contains $m.id) {
            $errors += "Duplicate milestone id: $($m.id)"
        } else {
            $milestoneIds += $m.id
        }

        if ($m.status -and $validMilestoneStatuses -notcontains $m.status) {
            $errors += "Milestone '$($m.id)' has invalid status: $($m.status)"
        }

        $featureIds = @()
        foreach ($f in $m.features) {
            if (-not $f.id) {
                $errors += "Feature in milestone '$($m.id)' missing id"
            } elseif ($f.id -notmatch $idPattern) {
                $errors += "Feature id '$($f.id)' is not valid kebab-case"
            } elseif ($featureIds -contains $f.id) {
                $errors += "Duplicate feature id '$($f.id)' in milestone '$($m.id)'"
            } else {
                $featureIds += $f.id
            }

            if ($f.status -and $validFeatureStatuses -notcontains $f.status) {
                $errors += "Feature '$($f.id)' in milestone '$($m.id)' has invalid status: $($f.status)"
            }
        }
    }

    return $errors
}

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

Describe "roadmap.json schema" {
    It "parses without error for a minimal valid roadmap" {
        $roadmap = @{
            schemaVersion = "compound-gpid-roadmap-v1"
            milestones    = @()
        }
        $errors = Test-RoadmapSchema $roadmap
        $errors.Count | Should Be 0
    }

    It "requires schemaVersion field" {
        $roadmap = @{ milestones = @() }
        $errors = Test-RoadmapSchema $roadmap
        ($errors -join " ") | Should Match "schemaVersion"
    }

    It "rejects wrong schemaVersion value" {
        $roadmap = @{ schemaVersion = "wrong-v99"; milestones = @() }
        $errors = Test-RoadmapSchema $roadmap
        ($errors -join " ") | Should Match "schemaVersion"
    }

    It "rejects invalid milestone status" {
        $roadmap = @{
            schemaVersion = "compound-gpid-roadmap-v1"
            milestones    = @(
                @{ id = "m1"; title = "Milestone 1"; objective = "x"; status = "invalid-status"; features = @() }
            )
        }
        $errors = Test-RoadmapSchema $roadmap
        ($errors -join " ") | Should Match "invalid status"
    }

    It "rejects invalid feature status" {
        $roadmap = @{
            schemaVersion = "compound-gpid-roadmap-v1"
            milestones    = @(
                @{
                    id       = "m1"; title = "M1"; objective = "x"; status = "planned"
                    features = @(
                        @{ id = "f1"; title = "F1"; status = "blocked"; plan = $null }
                    )
                }
            )
        }
        $errors = Test-RoadmapSchema $roadmap
        ($errors -join " ") | Should Match "invalid status"
    }

    It "rejects duplicate milestone IDs" {
        $roadmap = @{
            schemaVersion = "compound-gpid-roadmap-v1"
            milestones    = @(
                @{ id = "dup-id"; title = "A"; objective = "x"; status = "planned"; features = @() }
                @{ id = "dup-id"; title = "B"; objective = "y"; status = "planned"; features = @() }
            )
        }
        $errors = Test-RoadmapSchema $roadmap
        ($errors -join " ") | Should Match "Duplicate milestone id"
    }

    It "rejects duplicate feature IDs within a milestone" {
        $roadmap = @{
            schemaVersion = "compound-gpid-roadmap-v1"
            milestones    = @(
                @{
                    id       = "m1"; title = "M1"; objective = "x"; status = "planned"
                    features = @(
                        @{ id = "dup-feat"; title = "F1"; status = "idea"; plan = $null }
                        @{ id = "dup-feat"; title = "F2"; status = "idea"; plan = $null }
                    )
                }
            )
        }
        $errors = Test-RoadmapSchema $roadmap
        ($errors -join " ") | Should Match "Duplicate feature id"
    }
}

Describe "Milestone Status Calculation" {
    It "empty features -> planned" {
        Get-MilestoneStatus @() | Should Be "planned"
    }

    It "all done -> done" {
        $features = @(
            @{ status = "done" }
            @{ status = "done" }
        )
        Get-MilestoneStatus $features | Should Be "done"
    }

    It "any active -> in-progress" {
        $features = @(
            @{ status = "active" }
            @{ status = "idea" }
        )
        Get-MilestoneStatus $features | Should Be "in-progress"
    }

    It "mix of done + idea (no active) -> in-progress" {
        $features = @(
            @{ status = "done" }
            @{ status = "idea" }
        )
        Get-MilestoneStatus $features | Should Be "in-progress"
    }

    It "mix of done + planned (no active) -> in-progress" {
        $features = @(
            @{ status = "done" }
            @{ status = "planned" }
        )
        Get-MilestoneStatus $features | Should Be "in-progress"
    }

    It "all idea -> planned" {
        $features = @(
            @{ status = "idea" }
            @{ status = "idea" }
        )
        Get-MilestoneStatus $features | Should Be "planned"
    }

    It "all planned -> planned" {
        $features = @(
            @{ status = "planned" }
            @{ status = "planned" }
        )
        Get-MilestoneStatus $features | Should Be "planned"
    }

    It "mix of planned + idea -> planned" {
        $features = @(
            @{ status = "planned" }
            @{ status = "idea" }
        )
        Get-MilestoneStatus $features | Should Be "planned"
    }
}

Describe "/cg-resume scope health" {
    It "nudge fires when exactly 61% are unstarted (above threshold)" {
        # 61 idea out of 100 total
        $features = @()
        1..61 | ForEach-Object { $features += @{ status = "idea" } }
        1..39 | ForEach-Object { $features += @{ status = "done" } }
        Get-ScopeHealthNudge $features | Should Be $true
    }

    It "nudge does not fire when exactly 60% are unstarted (at threshold)" {
        # 60 idea out of 100 total -- ratio is exactly 0.60, not > 0.60
        $features = @()
        1..60 | ForEach-Object { $features += @{ status = "idea" } }
        1..40 | ForEach-Object { $features += @{ status = "done" } }
        Get-ScopeHealthNudge $features | Should Be $false
    }

    It "nudge does not fire when below 60%" {
        $features = @(
            @{ status = "idea" }
            @{ status = "done" }
            @{ status = "done" }
        )
        # 1/3 = 33% unstarted
        Get-ScopeHealthNudge $features | Should Be $false
    }

    It "empty feature list -> no divide-by-zero, returns false" {
        Get-ScopeHealthNudge @() | Should Be $false
    }

    It "all features unstarted -> nudge fires" {
        $features = @(
            @{ status = "idea" }
            @{ status = "planned" }
            @{ status = "idea" }
        )
        Get-ScopeHealthNudge $features | Should Be $true
    }
}

Describe "Structural validation" {
    It "only @cg-roadmap has user-invokable: true" {
        $agentFiles = Get-ChildItem -Path ".github\agents\*.agent.md" -ErrorAction SilentlyContinue
        $agentFiles | Should Not BeNullOrEmpty

        $invokable = $agentFiles | Where-Object {
            (Get-Content $_.FullName -Raw) -match 'user-invokable:\s*true'
        }
        $invokable.Count | Should Be 1
        $invokable[0].Name | Should Be "cg-roadmap.agent.md"
    }

    It "roadmap.json is NOT in .gitignore" {
        $gitignore = Get-Content ".gitignore" -ErrorAction SilentlyContinue
        $isIgnored = $gitignore | Where-Object { $_ -match 'roadmap\.json' }
        $isIgnored | Should BeNullOrEmpty
    }

    It "cg-setup scaffolds roadmap.json" {
        $setupContent = Get-Content ".github\prompts\cg-setup.prompt.md" -Raw
        ($setupContent -match 'roadmap\.json') | Should Be $true
    }

    It "cg-plan references @cg-roadmap" {
        $content = Get-Content ".github\prompts\cg-plan.prompt.md" -Raw
        ($content -match 'cg-roadmap') | Should Be $true
    }

    It "cg-work references @cg-roadmap" {
        $content = Get-Content ".github\prompts\cg-work.prompt.md" -Raw
        ($content -match 'cg-roadmap') | Should Be $true
    }

    It "cg-brainstorm references @cg-roadmap" {
        $content = Get-Content ".github\prompts\cg-brainstorm.prompt.md" -Raw
        ($content -match 'cg-roadmap') | Should Be $true
    }

    It "cg-resume reads roadmap.json" {
        $content = Get-Content ".github\prompts\cg-resume.prompt.md" -Raw
        ($content -match 'roadmap\.json') | Should Be $true
    }

    It "agent uses schemaVersion (not dollar-schema)" {
        $content = Get-Content ".github\agents\cg-roadmap.agent.md" -Raw
        ($content -match 'schemaVersion') | Should Be $true
        ($content -match '\$schema') | Should Be $false
    }
}
