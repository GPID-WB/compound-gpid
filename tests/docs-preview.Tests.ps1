# Contract tests for the combined stable-root and dev-preview documentation site.
# Created 2026-09-03.

Set-StrictMode -Version Latest

$repoRoot = if ($env:CG_TEST_ROOT) { $env:CG_TEST_ROOT } else { Split-Path $PSScriptRoot -Parent }
if ($env:CG_TEST_ROOT -and -not (Test-Path $env:CG_TEST_ROOT)) { throw "CG_TEST_ROOT '$env:CG_TEST_ROOT' does not exist" }

function Read-OptionalFile([string]$Path) {
    if (Test-Path $Path) { return Get-Content $Path -Raw -Encoding UTF8 }
    return ''
}

$buildWorkflow = Read-OptionalFile (Join-Path $repoRoot ".github\workflows\docs-site-build.yml")
$pagesWorkflow = Read-OptionalFile (Join-Path $repoRoot ".github\workflows\pages.yml")
$releaseWorkflow = Read-OptionalFile (Join-Path $repoRoot ".github\workflows\release-docs.yml")
$releasePagesWorkflow = Read-OptionalFile (Join-Path $repoRoot ".github\workflows\release-pages.yml")
$assembler = Read-OptionalFile (Join-Path $repoRoot "scripts\assemble-docs-site.js")

Describe "Combined documentation build contracts" {
    It "builds from dev changes and successful main documentation rebuilds" {
        $buildWorkflow | Should -Match 'workflow_run:'
        $buildWorkflow | Should -Match 'Rebuild documentation'
        $buildWorkflow | Should -Match 'branches:\s*\[dev\]'
        $buildWorkflow | Should -Match 'paths:'
        $buildWorkflow | Should -Match 'docs-site-build|Build combined documentation'
    }

    It "checks out stable and preview sources independently" {
        $buildWorkflow | Should -Match 'ref:\s*main'
        $buildWorkflow | Should -Match 'path:\s*sources/main'
        $buildWorkflow | Should -Match 'ref:\s*dev'
        $buildWorkflow | Should -Match 'path:\s*sources/dev'
        $buildWorkflow | Should -Match 'git -C sources/main rev-parse HEAD'
        $buildWorkflow | Should -Match 'git -C sources/dev rev-parse HEAD'
    }

    It "executes builds without Pages credentials and uploads one combined artifact" {
        $buildWorkflow | Should -Match 'cp -R sources/dev producer-input'
        $buildWorkflow | Should -Match 'rebuild-docs\.js --root .*producer-input.*--all'
        $buildWorkflow | Should -Not -Match 'rebuild-docs\.js --root .*sources/dev.*--all'
        $buildWorkflow | Should -Match '--dev-build .*dev-build'
        $buildWorkflow | Should -Not -Match 'rebuild-docs\.js --root .*sources/main.*--all'
        $buildWorkflow | Should -Match 'sources/dev/scripts/check-docs-site\.js.*--legacy'
        $buildWorkflow | Should -Match 'working-directory:\s*sources/main'
        $buildWorkflow | Should -Match 'working-directory:\s*producer-input'
        $buildWorkflow | Should -Match 'run:\s*node .*sources/dev/scripts/check-docs-site\.js'
        $buildWorkflow | Should -Match 'assemble-docs-site\.js --verify combined-artifact'
        $buildWorkflow | Should -Match 'assemble-docs-site\.js'
        $buildWorkflow | Should -Match 'combined-docs-site'
        $buildWorkflow | Should -Match '\.docs-build-metadata\.json'
        $buildWorkflow | Should -Match 'include-hidden-files:\s*true'
        $buildWorkflow | Should -Not -Match 'pages:\s*write|id-token:\s*write'
    }
}

Describe "Split dev builder and protected Pages controller contracts" {
    It "runs from pushes to dev" {
        $pagesWorkflow | Should -Match 'push:'
        $pagesWorkflow | Should -Match 'branches:\s*\[dev\]'
        $pagesWorkflow | Should -Not -Match 'workflow_run:'
    }

    It "restores authenticated official data and uses protected default code as controller" {
        $pagesWorkflow | Should -Match 'ref:.*github.sha'
        $devController = [regex]::Match($releasePagesWorkflow, '(?s)\n  deploy-dev:.*').Value
        $devController | Should -Match 'ref:.*github.sha'
        $devController | Should -Not -Match 'ref:\s*main'
        $devController | Should -Match 'legacy-pages.js restore-official official-source official-state.json'
        $devController | Should -Match '--main-root official-source'
        $devController | Should -Match 'legacy-pages.js recheck-official official-state.json'
        $devController | Should -Match 'ref:.*steps.authority.outputs.release_sha'
        $devController | Should -Match 'path:\s*sources/dev'
        $devController | Should -Match 'legacy-pages.js import-dev sources/dev dev-artifact'
        $devController | Should -Match 'scripts/assemble-docs-site\.js'
        $devController | Should -Match '--verify combined-artifact'
        $devController | Should -Match '--main-root official-source --dev-root sources/dev'
        $devController | Should -Match 'combined-artifact/site'
        $devController | Should -Match 'run-id:.*github.event.workflow_run.id'
        $devController | Should -Match 'artifact-ids:.*steps.authority.outputs.artifact_id'
    }

    It "keeps legacy Pages permissions in the protected controller and never rebuilds downloaded content" {
        $pagesWorkflow | Should -Not -Match 'pages:\s*write|id-token:\s*write|environment:|secrets\.'
        $pagesWorkflow | Should -Match 'contents:\s*read'
        $pagesWorkflow | Should -Match 'rebuild-docs\.js --all'
        $pagesWorkflow | Should -Match 'actions/upload-artifact'
        $pagesWorkflow | Should -Not -Match 'actions/upload-pages-artifact|actions/deploy-pages'
        $releasePagesWorkflow | Should -Match 'pages:\s*write'
        $releasePagesWorkflow | Should -Match 'id-token:\s*write'
        $releasePagesWorkflow | Should -Match 'actions:\s*read'
        $releasePagesWorkflow | Should -Match 'concurrency:\s*\r?\n\s*group:\s*pages'
        $releasePagesWorkflow | Should -Match 'actions/configure-pages'
        $releasePagesWorkflow | Should -Match 'actions/upload-pages-artifact'
        $releasePagesWorkflow | Should -Match 'actions/deploy-pages'
        $releasePagesWorkflow | Should -Not -Match 'rebuild-docs\.js|node sources/|node current-dev/'
    }
}

Describe "Isolated release producers and combined Pages artifact contracts" {
    It "builds release and dev snapshots in separate unprivileged jobs" {
        # Approved plan: GPID Documentation Provenance, lines433-445; P0.1 repair.
        $releaseJob = [regex]::Match($releaseWorkflow, '(?ms)^  build:\r?\n.*?(?=^  [a-z][a-z0-9-]*:\r?$|\z)').Value
        $devJob = [regex]::Match($releaseWorkflow, '(?ms)^  build-dev:\r?\n.*?(?=^  [a-z][a-z0-9-]*:\r?$|\z)').Value
        foreach ($job in @($releaseJob, $devJob)) {
            $job.Length | Should -BeGreaterThan 0
            $job | Should -Match 'runs-on:\s*ubuntu-latest'
            $job | Should -Match 'permissions:\r?\n\s+contents:\s*read\r?\n\s+steps:'
            ([regex]::Matches($job, 'uses:\s*actions/checkout@')).Count | Should -Be 1
            $job | Should -Match 'persist-credentials:\s*false'
            $job | Should -Match 'node scripts/rebuild-docs\.js --all'
            $job | Should -Match 'node scripts/check-docs-site\.js'
            ([regex]::Matches($job, 'uses:\s*actions/upload-artifact@')).Count | Should -Be 1
            $job | Should -Match 'path:\s*\|\r?\n\s+docs/\r?\n\s+\.docs-build-metadata\.json'
            $job | Should -Match 'include-hidden-files:\s*true'
            $job | Should -Match 'if-no-files-found:\s*error'
        }
        $releaseJob | Should -Match 'ref:\s*\$\{\{\s*github\.sha\s*\}\}'
        $releaseJob | Should -Match '(?m)^\s+name:\s*release-docs-site\s*$'
        $releaseJob | Should -Not -Match 'ref:\s*dev\b|current-dev|name:\s*release-dev-docs'
        $devJob | Should -Match '(?m)^\s+ref:\s*dev\s*$'
        $devJob | Should -Match '(?m)^\s+name:\s*release-dev-docs\s*$'
        $devJob | Should -Not -Match 'name:\s*release-docs-site\b'
        $releaseWorkflow | Should -Not -Match 'pages:\s*write|id-token:\s*write|environment:|secrets\.|create-github-app-token'
        $releaseWorkflow | Should -Not -Match 'assemble-docs-site\.js|combined-artifact|actions/upload-pages-artifact|actions/deploy-pages'
    }

    It "verifies release and dev provenance before publishing the complete artifact" {
        $deployJob = [regex]::Match($releasePagesWorkflow, '(?ms)^  deploy:\r?\n.*?(?=^  [a-z][a-z0-9-]*:\r?$|\z)').Value
        $deployJob.Length | Should -BeGreaterThan 0
        $deployJob | Should -Match 'path:\s*release-source'
        $deployJob | Should -Match 'path:\s*current-dev'
        $deployJob | Should -Match 'ref:\s*dev'
        $steps = [regex]::Matches($deployJob, '(?ms)^      - .*?(?=^      - |\z)')
        $archiveCommand = 'node scripts/legacy-pages.js archive "$ARTIFACT_ID" "$ARTIFACT_DIGEST"'
        $lastDownload = -1
        foreach ($artifactPrefix in @('artifact', 'dev_artifact')) {
            $idPattern = 'ARTIFACT_ID:\s*\$\{\{\s*steps\.authority\.outputs\.' + $artifactPrefix + '_id\s*\}\}'
            $digestPattern = 'ARTIFACT_DIGEST:\s*\$\{\{\s*steps\.authority\.outputs\.' + $artifactPrefix + '_digest\s*\}\}'
            $downloadPattern = 'artifact-ids:\s*\$\{\{\s*steps\.authority\.outputs\.' + $artifactPrefix + '_id\s*\}\}'
            $archiveSteps = @($steps | Where-Object { $_.Value.Contains($archiveCommand) -and $_.Value -match $idPattern })
            $downloadSteps = @($steps | Where-Object { $_.Value -match 'uses:\s*actions/download-artifact@' -and $_.Value -match $downloadPattern })
            $archiveSteps.Count | Should -Be 1
            $downloadSteps.Count | Should -Be 1
            $archiveSteps[0].Value | Should -Match $digestPattern
            $downloadSteps[0].Value | Should -Match 'run-id:.*inputs.build_run_id.*github.event.workflow_run.id'
            $downloadSteps[0].Index | Should -BeGreaterThan $archiveSteps[0].Index
            $lastDownload = [Math]::Max($lastDownload, $downloadSteps[0].Index)
        }
        $releaseImport = $deployJob.IndexOf('legacy-pages.js import-docs release-source release-artifact')
        $devImport = $deployJob.IndexOf('legacy-pages.js import-dev current-dev release-dev-artifact')
        $composeIndex = $deployJob.IndexOf('node scripts/assemble-docs-site.js --main-root release-source')
        $verifyIndex = $deployJob.IndexOf('--verify release-artifact')
        $releaseImport | Should -BeGreaterThan $lastDownload
        $devImport | Should -BeGreaterThan $lastDownload
        $composeIndex | Should -BeGreaterThan $releaseImport
        $composeIndex | Should -BeGreaterThan $devImport
        $verifyIndex | Should -BeGreaterThan $composeIndex
        $deployJob.IndexOf('uses: actions/upload-pages-artifact@') | Should -BeGreaterThan $verifyIndex
        $deployJob | Should -Match 'release-artifact/site'
        $deployJob | Should -Match 'Artifact digest mismatch'
        $deployJob | Should -Match 'pages:\s*write'
        $deployJob | Should -Match 'id-token:\s*write'
        $deployJob | Should -Not -Match 'rebuild-docs\.js|(?:release-source|current-dev)/scripts/'
        $deployJob | Should -Match 'uses:\s*actions/deploy-pages@'
    }
}

Describe "Combined artifact implementation contracts" {
    It "records branch/ref identity and verifies source commit identities" {
        $assembler | Should -Match 'sources:'
        $assembler | Should -Match 'branch:'
        $assembler | Should -Match 'ref:'
        $assembler | Should -Match 'mainSha'
        $assembler | Should -Match 'devSha'
        $assembler | Should -Match 'source fingerprint is stale'
    }

    It "keeps development marking and verification deterministic" {
        $assembler | Should -Match 'Development preview built from'
        $assembler | Should -Match 'dev-preview-banner'
        $assembler | Should -Match 'combined site digest mismatch'
        $assembler | Should -Match 'symbolic links are not allowed'
        $assembler | Should -Match 'output path collision'
    }
}
