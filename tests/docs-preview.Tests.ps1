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
        $buildWorkflow | Should -Match 'rebuild-docs\.js --root .*sources/main.*--all'
        $buildWorkflow | Should -Match 'rebuild-docs\.js --root .*sources/dev.*--all'
        $buildWorkflow | Should -Match 'check-docs-site\.js --source-root'
        $buildWorkflow | Should -Match 'assemble-docs-site\.js'
        $buildWorkflow | Should -Match 'combined-docs-site'
        $buildWorkflow | Should -Match '\.docs-build-metadata\.json'
        $buildWorkflow | Should -Match 'include-hidden-files:\s*true'
        $buildWorkflow | Should -Not -Match 'pages:\s*write|id-token:\s*write'
    }
}

Describe "Protected combined Pages controller contracts" {
    It "runs only after a successful combined build from main or dev" {
        $pagesWorkflow | Should -Match 'workflow_run:'
        $pagesWorkflow | Should -Match 'Build combined documentation'
        $pagesWorkflow | Should -Match "workflow_run\.conclusion == 'success'"
        $pagesWorkflow | Should -Match "head_branch == 'dev'"
        $pagesWorkflow | Should -Match "head_branch == 'main'"
    }

    It "checks out trusted main and current dev, then verifies the exact artifact" {
        $pagesWorkflow | Should -Match 'ref:\s*main'
        $pagesWorkflow | Should -Match 'path:\s*current-dev'
        $pagesWorkflow | Should -Match 'ref:\s*dev'
        $pagesWorkflow | Should -Match 'combined-docs-site'
        $pagesWorkflow | Should -Match 'run-id:\s*\$\{\{ github\.event\.workflow_run\.id \}\}'
        $pagesWorkflow | Should -Match 'assemble-docs-site\.js[\s\\]+--verify'
        $pagesWorkflow | Should -Match '--main-sha'
        $pagesWorkflow | Should -Match '--dev-sha'
        $pagesWorkflow | Should -Match 'combined-artifact/site'
    }

    It "keeps Pages permissions in one controller and never rebuilds downloaded content" {
        $pagesWorkflow | Should -Match 'pages:\s*write'
        $pagesWorkflow | Should -Match 'id-token:\s*write'
        $pagesWorkflow | Should -Match 'actions:\s*read'
        $pagesWorkflow | Should -Not -Match 'rebuild-docs\.js --all'
        $pagesWorkflow | Should -Not -Match 'assemble-docs-site\.js --main-root'
        $pagesWorkflow | Should -Match 'concurrency:\s*\r?\n\s*group:\s*pages'
        $pagesWorkflow | Should -Match 'actions/upload-pages-artifact'
        $pagesWorkflow | Should -Match 'actions/deploy-pages'
    }
}

Describe "Release combined-artifact contracts" {
    It "builds the tagged release root and current dev preview without Pages credentials" {
        $releaseWorkflow | Should -Match 'path:\s*current-dev'
        $releaseWorkflow | Should -Match 'ref:\s*dev'
        $releaseWorkflow | Should -Match 'assemble-docs-site\.js'
        $releaseWorkflow | Should -Match 'combined-docs-site|release-docs-site'
        $releaseWorkflow | Should -Match 'combined-artifact'
        $releaseWorkflow | Should -Not -Match 'pages:\s*write|id-token:\s*write'
    }

    It "verifies release and dev provenance before publishing the complete artifact" {
        $releasePagesWorkflow | Should -Match 'path:\s*release-source'
        $releasePagesWorkflow | Should -Match 'path:\s*current-dev'
        $releasePagesWorkflow | Should -Match 'ref:\s*dev'
        $releasePagesWorkflow | Should -Match 'assemble-docs-site\.js[\s\\]+--verify'
        $releasePagesWorkflow | Should -Match 'release-artifact/site'
        $releasePagesWorkflow | Should -Match 'Artifact digest mismatch|combined artifact'
        $releasePagesWorkflow | Should -Match 'pages:\s*write'
        $releasePagesWorkflow | Should -Match 'id-token:\s*write'
        $releasePagesWorkflow | Should -Match 'Deploy to GitHub Pages'
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
