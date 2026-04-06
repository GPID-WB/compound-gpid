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

    .OUTPUTS
    [string] One of: "planned", "in-progress", "done"

    .NOTES
    MIRRORS @cg-roadmap agent logic -- keep synchronized with
    .github/agents/cg-roadmap.agent.md (Milestone Status Calculation section).
    Internal helper for Pester tests; not exported.
    #>
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [object[]]$Features
    )

    if ($Features.Count -eq 0) { return "planned" }

    $allDone = $true; $anyActive = $false; $anyDone = $false
    foreach ($f in $Features) {
        if ($f.status -ne "done")   { $allDone   = $false }
        if ($f.status -eq "active") { $anyActive = $true  }
        if ($f.status -eq "done")   { $anyDone   = $true  }
    }

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

    .OUTPUTS
    [bool] $true when more than 60% of features are unstarted; $false otherwise.

    .NOTES
    MIRRORS @cg-roadmap agent logic -- keep synchronized with
    .github/prompts/cg-resume.prompt.md (scope health nudge section).
    Internal helper for Pester tests; not exported.
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

    .DESCRIPTION
    Checks all required fields (schemaVersion, milestones, id, title,
    objective, status, features), validates status enumerations, enforces
    kebab-case IDs, detects duplicates, verifies array types, and validates
    that stored milestone status matches the derived status (per the
    @cg-roadmap agent spec invariant: status is always derived, never set
    directly). Uses @(...) wrapping for PS 5.1 compatibility where
    ConvertFrom-Json returns a bare PSCustomObject for single-element arrays.

    .PARAMETER Roadmap
    Hashtable or PSCustomObject representing parsed roadmap.json.

    .EXAMPLE
    $roadmap = @{ schemaVersion = "compound-gpid-roadmap-v1"; milestones = @() }
    $errors = Test-RoadmapSchema $roadmap
    $errors.Count  # 0 for a valid empty roadmap

    .OUTPUTS
    [string[]] Array of error strings. Empty array means the roadmap is valid.

    .NOTES
    MIRRORS @cg-roadmap agent logic -- keep synchronized with
    .github/agents/cg-roadmap.agent.md (Schema and Milestone Status Calculation
    sections). Internal helper for Pester tests; not exported.
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

    # Reject strings and other scalars explicitly (string check must come before
    # @(...) wrapping, which would silently turn "not-an-array" into @("not-an-array")).
    if ($Roadmap.milestones -is [string] -or $Roadmap.milestones -is [int] -or
        $Roadmap.milestones -is [bool]) {
        $errors += "milestones must be an array"
        return $errors
    }

    # @() forces array coercion on PS 5.1 where ConvertFrom-Json returns a bare
    # PSCustomObject (not an array) when the JSON array has exactly one element.
    $milestones = @($Roadmap.milestones)

    $milestoneIds = @{}
    foreach ($m in $milestones) {
        if (-not $m.id) {
            $errors += "Milestone missing id"
        } elseif ($m.id -cnotmatch $idPattern) {
            $errors += "Milestone id '$($m.id)' is not valid kebab-case"
        } elseif ($milestoneIds.ContainsKey($m.id)) {
            $errors += "Duplicate milestone id: $($m.id)"
        } else {
            $milestoneIds[$m.id] = $true
        }

        if (-not $m.title) {
            $errors += "Milestone '$($m.id)' missing required field: title"
        }

        if (-not $m.objective) {
            $errors += "Milestone '$($m.id)' missing required field: objective"
        }

        if (-not $m.status) {
            $errors += "Milestone '$($m.id)' missing required field: status"
        } elseif ($validMilestoneStatuses -notcontains $m.status) {
            $errors += "Milestone '$($m.id)' has invalid status: $($m.status)"
        }

        if ($null -eq $m.features) {
            $errors += "Milestone '$($m.id)' missing required field: features"
            continue
        }

        if ($m.features -is [string] -or $m.features -is [int] -or $m.features -is [bool]) {
            $errors += "Milestone '$($m.id)': features must be an array"
            continue
        }

        # @() forces array coercion on PS 5.1 (see milestones comment above).
        $features = @($m.features)

        # Validate that the stored status matches the derived status.
        # Milestone status is always derived from features -- never set directly.
        if ($m.status -and $validMilestoneStatuses -contains $m.status) {
            $derived = Get-MilestoneStatus $features
            if ($m.status -ne $derived) {
                $errors += "Milestone '$($m.id)' status is '$($m.status)' but derived status from features is '$derived'"
            }
        }

        $featureIds = @{}
        foreach ($f in $features) {
            if (-not $f.id) {
                $errors += "Feature in milestone '$($m.id)' missing id"
            } elseif ($f.id -cnotmatch $idPattern) {
                $errors += "Feature id '$($f.id)' is not valid kebab-case"
            } elseif ($featureIds.ContainsKey($f.id)) {
                $errors += "Duplicate feature id '$($f.id)' in milestone '$($m.id)'"
            } else {
                $featureIds[$f.id] = $true
            }

            if (-not $f.title) {
                $errors += "Feature '$($f.id)' in milestone '$($m.id)' missing required field: title"
            }

            if (-not $f.status) {
                $errors += "Feature '$($f.id)' in milestone '$($m.id)' missing required field: status"
            } elseif ($validFeatureStatuses -notcontains $f.status) {
                $errors += "Feature '$($f.id)' in milestone '$($m.id)' has invalid status: $($f.status)"
            }

            if ($null -ne $f.plan -and $f.plan -isnot [string]) {
                $errors += "Feature '$($f.id)' in milestone '$($m.id)': plan must be a string or null"
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

    It "rejects milestones as a string instead of array" {
        $roadmap = @{
            schemaVersion = "compound-gpid-roadmap-v1"
            milestones    = "not-an-array"
        }
        $errors = Test-RoadmapSchema $roadmap
        ($errors -join " ") | Should Match "must be an array"
    }

    It "rejects features as a string instead of array" {
        $roadmap = @{
            schemaVersion = "compound-gpid-roadmap-v1"
            milestones    = @(
                @{ id = "m1"; title = "M1"; objective = "x"; status = "planned"; features = "not-an-array" }
            )
        }
        $errors = Test-RoadmapSchema $roadmap
        ($errors -join " ") | Should Match "must be an array"
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

    It "rejects milestone with null status" {
        $roadmap = @{
            schemaVersion = "compound-gpid-roadmap-v1"
            milestones    = @(
                @{ id = "m1"; title = "M1"; objective = "x"; status = $null; features = @() }
            )
        }
        $errors = Test-RoadmapSchema $roadmap
        ($errors -join " ") | Should Match "status"
    }

    It "rejects milestone missing title" {
        $roadmap = @{
            schemaVersion = "compound-gpid-roadmap-v1"
            milestones    = @(
                @{ id = "m1"; objective = "x"; status = "planned"; features = @() }
            )
        }
        $errors = Test-RoadmapSchema $roadmap
        ($errors -join " ") | Should Match "title"
    }

    It "rejects milestone missing objective" {
        $roadmap = @{
            schemaVersion = "compound-gpid-roadmap-v1"
            milestones    = @(
                @{ id = "m1"; title = "M1"; status = "planned"; features = @() }
            )
        }
        $errors = Test-RoadmapSchema $roadmap
        ($errors -join " ") | Should Match "objective"
    }

    It "rejects milestone missing features array" {
        $roadmap = @{
            schemaVersion = "compound-gpid-roadmap-v1"
            milestones    = @(
                @{ id = "m1"; title = "M1"; objective = "x"; status = "planned" }
            )
        }
        $errors = Test-RoadmapSchema $roadmap
        ($errors -join " ") | Should Match "features"
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

    It "rejects feature with null status" {
        $roadmap = @{
            schemaVersion = "compound-gpid-roadmap-v1"
            milestones    = @(
                @{
                    id       = "m1"; title = "M1"; objective = "x"; status = "planned"
                    features = @(
                        @{ id = "f1"; title = "F1"; status = $null; plan = $null }
                    )
                }
            )
        }
        $errors = Test-RoadmapSchema $roadmap
        ($errors -join " ") | Should Match "status"
    }

    It "rejects feature missing title" {
        $roadmap = @{
            schemaVersion = "compound-gpid-roadmap-v1"
            milestones    = @(
                @{
                    id       = "m1"; title = "M1"; objective = "x"; status = "planned"
                    features = @(
                        @{ id = "f1"; status = "idea"; plan = $null }
                    )
                }
            )
        }
        $errors = Test-RoadmapSchema $roadmap
        ($errors -join " ") | Should Match "title"
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

    It "rejects invalid kebab-case milestone IDs" {
        $badIds = @("MyId", "my_id", "my--id", "-my-id")
        foreach ($badId in $badIds) {
            $roadmap = @{
                schemaVersion = "compound-gpid-roadmap-v1"
                milestones    = @(
                    @{ id = $badId; title = "M"; objective = "o"; status = "planned"; features = @() }
                )
            }
            $errors = Test-RoadmapSchema $roadmap
            ($errors -join " ") | Should Match "not valid kebab-case"
        }
    }

    It "rejects non-string plan field" {
        $roadmap = @{
            schemaVersion = "compound-gpid-roadmap-v1"
            milestones    = @(
                @{
                    id       = "m1"; title = "M1"; objective = "x"; status = "planned"
                    features = @(
                        @{ id = "f1"; title = "F1"; status = "idea"; plan = 42 }
                    )
                }
            )
        }
        $errors = Test-RoadmapSchema $roadmap
        ($errors -join " ") | Should Match "plan must be a string or null"
    }
}

Describe "Milestone Status Calculation" {
    It "empty features -> planned" {
        Get-MilestoneStatus @() | Should Be "planned"
    }

    It "single done feature -> done" {
        Get-MilestoneStatus @(@{ status = "done" }) | Should Be "done"
    }

    It "single active feature -> in-progress" {
        Get-MilestoneStatus @(@{ status = "active" }) | Should Be "in-progress"
    }

    It "single idea feature -> planned" {
        Get-MilestoneStatus @(@{ status = "idea" }) | Should Be "planned"
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

    It "mix of done + active -> in-progress" {
        $features = @(
            @{ status = "done" }
            @{ status = "active" }
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
        $features = @(
            1..61 | ForEach-Object { @{ status = "idea" } }
            1..39 | ForEach-Object { @{ status = "done" } }
        )
        Get-ScopeHealthNudge $features | Should Be $true
    }

    It "nudge does not fire when exactly 60% are unstarted (at threshold)" {
        # 60 idea out of 100 total -- ratio is exactly 0.60, not > 0.60
        $features = @(
            1..60 | ForEach-Object { @{ status = "idea" } }
            1..40 | ForEach-Object { @{ status = "done" } }
        )
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
        @($agentFiles).Count | Should BeGreaterThan 0

        $invokable = $agentFiles | Where-Object {
            (Get-Content $_.FullName -Raw) -match 'user-invokable:\s*true'
        }
        $invokable.Count | Should Be 1
        $invokable[0].Name | Should Be "cg-roadmap.agent.md"
    }

    It "roadmap.json is NOT in .gitignore" {
        $gitignore = Get-Content ".gitignore" -ErrorAction SilentlyContinue
        $isIgnored = $gitignore | Where-Object { $_ -match 'roadmap\.json' }
        @($isIgnored).Count | Should Be 0
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

    It "cg-roadmap requires confirmation before removing features or milestones" {
        $content = Get-Content ".github\agents\cg-roadmap.agent.md" -Raw
        ($content -match 'Confirm.*user.*before|before.*delete|before.*remov') | Should Be $true
    }

    It "cg-setup and cg-roadmap agree on the empty JSON skeleton schemaVersion" {
        $setupContent   = Get-Content ".github\prompts\cg-setup.prompt.md" -Raw
        $roadmapContent = Get-Content ".github\agents\cg-roadmap.agent.md" -Raw
        ($setupContent   -match '"schemaVersion":\s*"compound-gpid-roadmap-v1"') | Should Be $true
        ($roadmapContent -match '"schemaVersion":\s*"compound-gpid-roadmap-v1"') | Should Be $true
    }
}

Describe "roadmap.json schema -- additional coverage" {
    It "passes for a valid roadmap with features" {
        $roadmap = @{
            schemaVersion = "compound-gpid-roadmap-v1"
            milestones    = @(
                @{
                    id       = "m1"; title = "Milestone 1"; objective = "Does X."; status = "planned"
                    features = @(
                        @{ id = "feat-1"; title = "Feature 1"; status = "idea"; plan = $null }
                    )
                }
            )
        }
        $errors = Test-RoadmapSchema $roadmap
        $errors.Count | Should Be 0
    }

    It "rejects milestone whose stored status does not match derived status" {
        $roadmap = @{
            schemaVersion = "compound-gpid-roadmap-v1"
            milestones    = @(
                @{
                    id       = "m1"; title = "M1"; objective = "x"; status = "done"
                    features = @(@{ id = "f1"; title = "F1"; status = "idea"; plan = $null })
                }
            )
        }
        $errors = Test-RoadmapSchema $roadmap
        ($errors -join " ") | Should Match "derived"
    }

    It "validates a one-milestone roadmap parsed from JSON (ConvertFrom-Json coercion)" {
        $json = '{"schemaVersion":"compound-gpid-roadmap-v1","milestones":[{"id":"m1","title":"M","objective":"o","status":"planned","features":[]}]}'
        $roadmap = $json | ConvertFrom-Json
        $errors = Test-RoadmapSchema $roadmap
        $errors.Count | Should Be 0
    }

    It "validates a roadmap with one feature parsed from JSON (ConvertFrom-Json coercion)" {
        $json = '{"schemaVersion":"compound-gpid-roadmap-v1","milestones":[{"id":"m1","title":"M","objective":"o","status":"planned","features":[{"id":"f1","title":"F","status":"idea","plan":null}]}]}'
        $roadmap = $json | ConvertFrom-Json
        $errors = Test-RoadmapSchema $roadmap
        $errors.Count | Should Be 0
    }

    It "rejects milestone missing id" {
        $roadmap = @{
            schemaVersion = "compound-gpid-roadmap-v1"
            milestones    = @(
                @{ title = "M1"; objective = "x"; status = "planned"; features = @() }
            )
        }
        $errors = Test-RoadmapSchema $roadmap
        ($errors -join " ") | Should Match "missing id"
    }

    It "rejects feature missing id" {
        $roadmap = @{
            schemaVersion = "compound-gpid-roadmap-v1"
            milestones    = @(
                @{
                    id       = "m1"; title = "M1"; objective = "x"; status = "planned"
                    features = @(
                        @{ title = "F1"; status = "idea"; plan = $null }
                    )
                }
            )
        }
        $errors = Test-RoadmapSchema $roadmap
        ($errors -join " ") | Should Match "missing id"
    }

    It "rejects invalid kebab-case feature IDs" {
        $badIds = @("MyId", "my_id", "my--id", "-my-id", "my-id-")
        foreach ($badId in $badIds) {
            $roadmap = @{
                schemaVersion = "compound-gpid-roadmap-v1"
                milestones    = @(
                    @{
                        id       = "m1"; title = "M1"; objective = "o"; status = "planned"
                        features = @(
                            @{ id = $badId; title = "F"; status = "idea"; plan = $null }
                        )
                    }
                )
            }
            $errors = Test-RoadmapSchema $roadmap
            ($errors -join " ") | Should Match "not valid kebab-case"
        }
    }

    It "handles features as a single hashtable (PS 5.1 coercion compatibility)" {
        # In PS 5.1, ConvertFrom-Json may return a single PSCustomObject instead of
        # a one-element array. @() wrapping handles this gracefully. This test
        # verifies no crash and the feature is validated correctly.
        $roadmap = @{
            schemaVersion = "compound-gpid-roadmap-v1"
            milestones    = @(
                @{
                    id       = "m1"; title = "M1"; objective = "x"; status = "planned"
                    features = @{ id = "f1"; title = "F1"; status = "idea"; plan = $null }
                }
            )
        }
        { Test-RoadmapSchema $roadmap } | Should Not Throw
        $errors = Test-RoadmapSchema $roadmap
        # single "idea" feature -> derived "planned" which matches stored "planned" -> valid
        $errors.Count | Should Be 0
    }
}

Describe "Milestone Status Calculation -- additional coverage" {
    It "single planned feature -> planned" {
        Get-MilestoneStatus @(@{ status = "planned" }) | Should Be "planned"
    }
}

Describe "/cg-resume scope health -- additional coverage" {
    It "single unstarted feature (idea) -> nudge fires" {
        $features = @(@{ status = "idea" })
        Get-ScopeHealthNudge $features | Should Be $true
    }

    It "single started feature (done) -> nudge does not fire" {
        $features = @(@{ status = "done" })
        Get-ScopeHealthNudge $features | Should Be $false
    }
}

# ---------------------------------------------------------------------------
# Test-RecentStrategyDocument helper + tests (mirrors /cg-resume Step 4 logic)
# ---------------------------------------------------------------------------

function Test-RecentStrategyDocument {
    <#
    .SYNOPSIS
    Returns $true when a strategy document newer than 60 days exists.

    .DESCRIPTION
    Checks .cg-docs/strategy/ for .md files whose name starts with YYYY-MM-DD.
    Uses the filename date prefix (not file modification time) so the check is
    reproducible. A missing directory is treated as zero documents ($false).

    .PARAMETER StrategyPath
    Path to .cg-docs/strategy/ directory.

    .PARAMETER ReferenceDate
    The date to measure "60 days" from. Defaults to today. Accepts [datetime].

    .EXAMPLE
    Test-RecentStrategyDocument ".cg-docs\strategy"   # $true if recent doc exists

    .OUTPUTS
    [bool] $true if any strategy document is <=60 days old; $false otherwise.

    .NOTES
    MIRRORS /cg-resume prompt logic (scope-check condition) -- keep synchronized.
    #>
    param(
        [Parameter(Mandatory = $true)]
        [string]$StrategyPath,
        [Parameter(Mandatory = $false)]
        [datetime]$ReferenceDate = (Get-Date)
    )

    if (-not (Test-Path $StrategyPath)) { return $false }

    $cutoff = $ReferenceDate.AddDays(-60)
    $files = Get-ChildItem -Path $StrategyPath -Filter "*.md" -ErrorAction SilentlyContinue |
             Where-Object { $_.Name -ne ".gitkeep" }

    foreach ($f in $files) {
        $match = [regex]::Match($f.Name, '^\d{4}-\d{2}-\d{2}')
        if ($match.Success) {
            try {
                $fileDate = [datetime]::ParseExact($match.Value, 'yyyy-MM-dd', [System.Globalization.CultureInfo]::InvariantCulture)
                if ($fileDate -ge $cutoff) { return $true }
            } catch {
                Write-Verbose "Skipping '$($f.Name)': not a valid date prefix"
            }
        }
    }
    return $false
}

Describe "Test-RecentStrategyDocument helper" {
    $tmpDir  = Join-Path ([System.IO.Path]::GetTempPath()) ("cg-test-strategy-" + [guid]::NewGuid().ToString("N"))
    $refDate = [datetime]"2026-01-01"

    AfterEach {
        if (Test-Path $tmpDir) { Remove-Item $tmpDir -Recurse -Force }
    }

    It "returns false when directory does not exist" {
        Test-RecentStrategyDocument (Join-Path $tmpDir "nonexistent") -ReferenceDate $refDate | Should Be $false
    }

    It "returns false when directory is empty" {
        New-Item -ItemType Directory -Path $tmpDir | Out-Null
        Test-RecentStrategyDocument $tmpDir -ReferenceDate $refDate | Should Be $false
    }

    It "returns false when directory contains only non-.md files" {
        New-Item -ItemType Directory -Path $tmpDir | Out-Null
        New-Item -ItemType File -Path (Join-Path $tmpDir ".gitkeep") | Out-Null
        Test-RecentStrategyDocument $tmpDir -ReferenceDate $refDate | Should Be $false
    }

    It "returns false when only file is older than 60 days" {
        New-Item -ItemType Directory -Path $tmpDir | Out-Null
        $oldDate = $refDate.AddDays(-61).ToString("yyyy-MM-dd")
        New-Item -ItemType File -Path (Join-Path $tmpDir "$oldDate-old-session.md") | Out-Null
        Test-RecentStrategyDocument $tmpDir -ReferenceDate $refDate | Should Be $false
    }

    It "returns true when a file is exactly today (reference date)" {
        New-Item -ItemType Directory -Path $tmpDir | Out-Null
        $todayDate = $refDate.ToString("yyyy-MM-dd")
        New-Item -ItemType File -Path (Join-Path $tmpDir "$todayDate-session.md") | Out-Null
        Test-RecentStrategyDocument $tmpDir -ReferenceDate $refDate | Should Be $true
    }

    It "returns true when a file is 30 days old (within 60-day window)" {
        New-Item -ItemType Directory -Path $tmpDir | Out-Null
        $recentDate = $refDate.AddDays(-30).ToString("yyyy-MM-dd")
        New-Item -ItemType File -Path (Join-Path $tmpDir "$recentDate-session.md") | Out-Null
        Test-RecentStrategyDocument $tmpDir -ReferenceDate $refDate | Should Be $true
    }

    It "returns true when mixed old and recent files exist" {
        New-Item -ItemType Directory -Path $tmpDir | Out-Null
        $oldDate    = $refDate.AddDays(-90).ToString("yyyy-MM-dd")
        $recentDate = $refDate.AddDays(-10).ToString("yyyy-MM-dd")
        New-Item -ItemType File -Path (Join-Path $tmpDir "$oldDate-old.md")    | Out-Null
        New-Item -ItemType File -Path (Join-Path $tmpDir "$recentDate-new.md") | Out-Null
        Test-RecentStrategyDocument $tmpDir -ReferenceDate $refDate | Should Be $true
    }

    It "returns true when a file is exactly 60 days old (inclusive boundary)" {
        New-Item -ItemType Directory -Path $tmpDir | Out-Null
        $boundaryDate = $refDate.AddDays(-60).ToString("yyyy-MM-dd")
        New-Item -ItemType File -Path (Join-Path $tmpDir "$boundaryDate-boundary.md") | Out-Null
        Test-RecentStrategyDocument $tmpDir -ReferenceDate $refDate | Should Be $true
    }

    It "ignores .md files without a date prefix" {
        New-Item -ItemType Directory -Path $tmpDir | Out-Null
        New-Item -ItemType File -Path (Join-Path $tmpDir "session-notes.md") | Out-Null
        Test-RecentStrategyDocument $tmpDir -ReferenceDate $refDate | Should Be $false
    }
}
