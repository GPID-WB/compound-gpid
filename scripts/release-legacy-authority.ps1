# Fresh remote authority for routine prereleases, legacy bridge, and recovery.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-CgReleaseBranchName {
    <# Validate an unqualified source branch before using it in Git/API arguments.
    Example: Assert-CgReleaseBranchName -Branch 'deploy/1.x'. No remote writes.
    #>
    param([AllowNull()][string]$Branch)
    if ([string]::IsNullOrEmpty($Branch) -or $Branch.Length -gt 1024 -or
        $Branch.StartsWith('-') -or $Branch.EndsWith('.') -or
        $Branch -cmatch '[\x00-\x20\x7f~^:?*\[\\]' -or
        $Branch.Contains('..') -or $Branch.Contains('@{') -or
        @($Branch.Split('/') | Where-Object { $_ -eq '' -or $_.StartsWith('.') -or $_.EndsWith('.lock') }).Count -gt 0) {
        throw 'Invalid release source branch name.'
    }
    git -C $PSScriptRoot check-ref-format "refs/heads/$Branch" 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Invalid release source branch name.' }
}

function Get-CgLegacyRemoteDocument {
    <# Read data at an exact remote commit. Example: Get-CgLegacyRemoteDocument '.release-controller.json' $sha. #>
    param([string]$Path, [string]$Commit)
    $value = Invoke-CgReleaseApi -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/contents/$($Path)?ref=$Commit" -AllowNotFound
    if ($null -eq $value) { return $null }
    if ($value.type -cne 'file' -or $value.encoding -cne 'base64' -or $value.content.Length -gt 1048576) {
        throw 'Remote legacy authority document is invalid.'
    }
    $raw = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($value.content))
    # These authority records are flat; reject duplicate keys before PS5.1 can discard them.
    $keys = @([regex]::Matches($raw, '("(?:\\.|[^"\\])*")\s*:') | ForEach-Object { $_.Groups[1].Value | ConvertFrom-Json })
    if (@($keys | Select-Object -Unique).Count -ne $keys.Count -and $Path -cne '.release-controller.json') {
        throw 'Duplicate historical recovery authority fields.'
    }
    if ($Path -ceq '.release-controller.json' -and @($keys | Where-Object { $_ -ceq 'enabled' }).Count -ne 1) {
        throw 'Remote cutover policy has ambiguous enabled authority.'
    }
    if ($Path -ceq '.release-controller.json' -and @($keys | Where-Object { $_ -ceq 'production_branches' }).Count -gt 1) {
        throw 'Remote production_branches policy is ambiguous.'
    }
    return ($raw | ConvertFrom-Json)
}

function Assert-CgLegacyAuthority {
    <# Recheck before each effect. Recovery keeps an existing stranded tag or a reviewed historical identity.
    Example: $authority = Assert-CgLegacyAuthority -Operation Recovery -ReleaseTag $Tag -Commit $sha -Object $oid -RemoteTag $remote -SourceBranch 'dev'.
    Returns the exact authority SHA and the optional reviewed historical record. No writes.
    #>
    param(
        [ValidateSet('Routine', 'Bridge', 'Recovery')][string]$Operation,
        [string]$ReleaseTag, [string]$Commit, [string]$Object, $RemoteTag,
        [Parameter(Mandatory)][string]$SourceBranch,
        [switch]$RequireRecoveryRecord
    )
    $base = 'https://api.github.com/repos/GPID-WB/compound-gpid'
    $repo = Invoke-CgReleaseApi -Uri $base
    if ($repo.full_name -cne 'GPID-WB/compound-gpid' -or $repo.fork -ne $false -or
        [string]$repo.id -cnotmatch '^[1-9][0-9]*$' -or
        [string]$repo.default_branch -cnotmatch '^[A-Za-z0-9][A-Za-z0-9/_.-]*$') { throw 'Protected remote repository authority is invalid.' }
    Assert-CgReleaseBranchName -Branch $SourceBranch
    if ($Operation -eq 'Routine') {
        $branchName = [uri]::EscapeDataString($SourceBranch)
        $branch = Invoke-CgReleaseApi -Uri "$base/branches/$branchName"
        if ($branch.name -cne $SourceBranch -or $branch.commit.sha -cnotmatch '^[0-9a-f]{40}$') {
            throw 'Routine authority requires the exact current remote source branch.'
        }
        $policy = Get-CgLegacyRemoteDocument -Path '.release-controller.json' -Commit $branch.commit.sha
        if ($null -eq $policy -or $policy.enabled -isnot [bool] -or $policy.enabled) {
            throw 'Routine publication requires a disabled controller policy at the exact remote source revision.'
        }
    } else {
        $branchName = [uri]::EscapeDataString([string]$repo.default_branch)
        $branch = Invoke-CgReleaseApi -Uri "$base/branches/$branchName"
        if ($branch.protected -isnot [bool] -or -not $branch.protected -or
            $branch.name -cne $repo.default_branch -or $branch.commit.sha -cnotmatch '^[0-9a-f]{40}$') {
            throw 'Legacy authority requires the protected remote default branch.'
        }
        # The active default-branch ruleset carries the authority the classic
        # branch-protection endpoint used to provide.
        $defaultRuleset = Get-CgRepositoryRuleset -RulesetName "Protect main" -RulesetTarget "branch"
        $defaultRuleTypes = @($defaultRuleset.rules | ForEach-Object { [string]$_.type })
        $defaultIncludes = @($defaultRuleset.conditions.ref_name.include | ForEach-Object { [string]$_ })
        $defaultExcludes = @($defaultRuleset.conditions.ref_name.exclude | ForEach-Object { [string]$_ })
        $defaultBypass = @($defaultRuleset.bypass_actors)
        $defaultBypassOk = $true
        foreach ($actor in $defaultBypass) {
            if ([string]$actor.actor_type -cne 'RepositoryRole' -or [int]$actor.actor_id -ne 5 -or
                [string]$actor.bypass_mode -cne 'always') { $defaultBypassOk = $false }
        }
        if ($defaultRuleTypes -cnotcontains 'deletion' -or
            $defaultRuleTypes -cnotcontains 'non_fast_forward' -or
            $defaultRuleTypes -cnotcontains 'pull_request' -or
            $defaultRuleTypes -cnotcontains 'required_status_checks' -or
            ($defaultIncludes -cnotcontains "refs/heads/$($repo.default_branch)" -and
                $defaultIncludes -cnotcontains '~DEFAULT_BRANCH') -or
            $defaultExcludes.Count -ne 0 -or -not $defaultBypassOk) {
            throw 'Legacy protected-default review authority is insufficient.'
        }
        $policy = Get-CgLegacyRemoteDocument -Path '.release-controller.json' -Commit $branch.commit.sha
        if ($null -ne $policy -and ($policy.enabled -isnot [bool] -or ($Operation -eq 'Bridge' -and $policy.enabled))) {
            throw 'Legacy Bridge is disabled after remote controller cutover or with invalid policy.'
        }
    }
    $productionBranches = @()
    if ($null -ne $policy -and $null -ne $policy.PSObject.Properties['production_branches']) {
        if ($policy.production_branches -isnot [array]) { throw 'Remote production_branches must be an array of branch names.' }
        foreach ($productionBranch in $policy.production_branches) {
            if ($productionBranch -isnot [string]) { throw 'Remote production_branches contains an invalid branch.' }
            try { Assert-CgReleaseBranchName -Branch $productionBranch }
            catch { throw 'Remote production_branches contains an invalid branch.' }
            $productionBranches += $productionBranch
        }
    }
    if ($ReleaseTag -cmatch '^v\d+\.\d+\.\d+$' -and
        $SourceBranch -cne $repo.default_branch -and $productionBranches -cnotcontains $SourceBranch) {
        throw "Stable release source branch '$SourceBranch' is neither a configured deployment branch nor the remote default."
    }
    $actor = Invoke-CgReleaseApi -Uri 'https://api.github.com/user'
    if ([string]$actor.id -cnotmatch '^[1-9][0-9]*$' -or [string]$actor.login -cnotmatch '^[A-Za-z0-9-]+$') { throw 'Current legacy actor authority is unavailable.' }
    $role = Invoke-CgReleaseApi -Uri "$base/collaborators/$($actor.login)/permission"
    if ($role.user.id -ne $actor.id -or $role.role_name -cnotin @('maintain', 'admin') -or
        $role.permission -cne $(if ($role.role_name -ceq 'admin') { 'admin' } else { 'write' })) {
        throw 'Current maintainer authority is required for legacy publication.'
    }
    $record = $null
    if ($Operation -eq 'Recovery') {
        if ($null -ne $RemoteTag -and ($RemoteTag.Object -cne $Object -or $RemoteTag.Commit -cne $Commit)) {
            throw 'Historical recovery cannot change immutable tag identity.'
        }
        if ($null -eq $RemoteTag -or $RequireRecoveryRecord) {
            $record = Get-CgLegacyRemoteDocument -Path ".github/release-recovery/$ReleaseTag.json" -Commit $branch.commit.sha
            if ($null -eq $record -or ($record.schema_version -isnot [int] -and $record.schema_version -isnot [long]) -or $record.schema_version -ne 1 -or $record.repository_id -ne $repo.id -or
                $record.tag -cne $ReleaseTag -or $record.tag_object -cne $Object -or $record.release_sha -cne $Commit -or
                $Object -cnotmatch '^[0-9a-f]{40}$' -or $Commit -cnotmatch '^[0-9a-f]{40}$' -or
                $actor.id -notin @($record.actor_ids) -or [string]::IsNullOrWhiteSpace($record.reason)) {
                throw 'Explicit reviewed historical recovery authority is required; routine new publication is forbidden.'
            }
            $allowed = @('schema_version', 'repository_id', 'tag', 'tag_object', 'release_sha', 'actor_ids', 'reason', 'build_run_id', 'artifact_id', 'artifact_digest')
            if (@($record.PSObject.Properties.Name | Where-Object { $_ -cnotin $allowed }).Count -gt 0) {
                throw 'Unknown historical recovery authority fields.'
            }
            if ($RequireRecoveryRecord -and (
                ($record.build_run_id -isnot [int] -and $record.build_run_id -isnot [long]) -or $record.build_run_id -le 0 -or
                ($record.artifact_id -isnot [int] -and $record.artifact_id -isnot [long]) -or $record.artifact_id -le 0 -or
                $record.artifact_digest -cnotmatch '^sha256:[0-9a-f]{64}$')) {
                throw 'Historical recovery requires exact numeric build/artifact IDs and a SHA-256 digest.'
            }
        }
    }
    $current = Invoke-CgReleaseApi -Uri "$base/branches/$branchName"
    $currentRepo = Invoke-CgReleaseApi -Uri $base
    if ($current.commit.sha -cne $branch.commit.sha -or $current.name -cne $branch.name -or
        $currentRepo.id -ne $repo.id -or $currentRepo.full_name -cne $repo.full_name -or
        ($Operation -ne 'Routine' -and ($current.protected -ne $true -or $currentRepo.default_branch -cne $repo.default_branch))) {
        throw $(if ($Operation -eq 'Routine') { 'Remote source policy changed during Routine authority checks.' } else { 'Protected default policy changed during legacy authority checks.' })
    }
    return [pscustomobject]@{ Commit = $branch.commit.sha; Branch = $branch.name; Record = $record; Actor = $actor.id }
}

function Assert-CgLegacyDeployment {
    <# Read the exact attempt's deploy job and its GitHub environment result.
    Example: Assert-CgLegacyDeployment -Run $run -Authority $authority.
    Returns deployment/job IDs only after a successful protected-default deployment.
    Bounded complete inventories fail closed; this function has no remote writes.
    #>
    param($Run, $Authority)
    $base = 'https://api.github.com/repos/GPID-WB/compound-gpid'
    if ($Run.head_branch -cne $Authority.Branch -or $Run.head_sha -cne $Authority.Commit -or
        [string]$Run.run_attempt -cnotmatch '^[1-9][0-9]*$') {
        throw 'Pages controller must run at the exact protected default revision.'
    }
    $inventory = Invoke-CgReleaseApi -Uri "$base/actions/runs/$($Run.id)/attempts/$($Run.run_attempt)/jobs?per_page=100"
    if ($inventory.total_count -ne @($inventory.jobs).Count -or $inventory.total_count -ge 100) {
        throw 'Exact protected deploy job inventory is incomplete.'
    }
    $jobs = @($inventory.jobs | Where-Object { $_.name -ceq 'deploy' })
    if ($jobs.Count -ne 1 -or [string]$jobs[0].id -cnotmatch '^[1-9][0-9]*$' -or
        $jobs[0].run_id -ne $Run.id -or $jobs[0].run_attempt -ne $Run.run_attempt -or
        $jobs[0].status -cne 'completed' -or $jobs[0].conclusion -cne 'success' -or
        @($jobs[0].steps | Where-Object { $_.name -ceq 'Deploy to GitHub Pages' -and $_.conclusion -ceq 'success' }).Count -ne 1) {
        throw 'The exact protected deploy job and Pages deployment step must succeed.'
    }
    $job = $jobs[0]
    if ([string]$job.html_url -cnotmatch '^https://github\.com/GPID-WB/compound-gpid/(?:actions/runs/[0-9]+/(?:job|jobs)/[0-9]+|runs/[0-9]+)$') {
        throw 'The protected deploy job has no repository-bound log identity.'
    }
    $deployments = Invoke-CgReleaseApi -Uri "$base/deployments?sha=$($Authority.Commit)&environment=github-pages&per_page=100"
    if (@($deployments).Count -ge 100) { throw 'Pages deployment result inventory is incomplete.' }
    # Regex operators write the case-insensitive automatic variable $Matches.
    $successfulDeployments = @()
    foreach ($deployment in @($deployments)) {
        if ($deployment.sha -cne $Authority.Commit -or $deployment.environment -cne 'github-pages' -or
            $deployment.ref -cnotin @($Authority.Branch, "refs/heads/$($Authority.Branch)")) { continue }
        if ([string]$deployment.id -cnotmatch '^[1-9][0-9]*$') { throw 'Invalid Pages deployment result identity.' }
        $statuses = Invoke-CgReleaseApi -Uri "$base/deployments/$($deployment.id)/statuses?per_page=100"
        if (@($statuses).Count -ge 100) { throw 'Pages deployment result statuses are incomplete.' }
        if (@($statuses).Count -gt 0 -and $statuses[0].state -ceq 'success' -and
            $statuses[0].environment -ceq 'github-pages' -and $statuses[0].log_url -ceq $job.html_url) {
            $successfulDeployments += $deployment
        }
    }
    if ($successfulDeployments.Count -ne 1) { throw 'An exact successful Pages deployment result for the protected deploy job is required.' }
    return [pscustomobject]@{ Deployment = $successfulDeployments[0].id; Job = $job.id }
}
