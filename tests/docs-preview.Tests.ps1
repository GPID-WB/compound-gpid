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

Describe "Documentation pull-request validation contracts" {
    It "validates proposed changes to both maintained branches" {
        $buildWorkflow | Should -Match 'pull_request:'
        $buildWorkflow | Should -Match 'branches:\s*\[main, dev\]'
        $buildWorkflow | Should -Match 'npm run docs:build'
        $buildWorkflow | Should -Match 'npm run docs:test'
        $buildWorkflow | Should -Match 'docs-review-'
    }

    It "keeps proposed source unprivileged" {
        $buildWorkflow | Should -Match 'persist-credentials:\s*false'
        $buildWorkflow | Should -Not -Match 'pages:\s*write|id-token:\s*write|contents:\s*write'
        $buildWorkflow | Should -Not -Match 'pull_request_target:'
    }
}

Describe "Development Pages producer contracts" {
    It "rebuilds every dev push without a path filter" {
        $pagesWorkflow | Should -Match 'push:'
        $pagesWorkflow | Should -Match 'branches:\s*\[dev\]'
        $pagesWorkflow | Should -Match 'workflow_dispatch:'
        $pagesWorkflow | Should -Not -Match 'paths:|paths-ignore:'
    }

    It "builds the exact commit and uploads the protected publisher handoff" {
        $pagesWorkflow | Should -Match 'name: Deploy documentation site'
        $pagesWorkflow | Should -Match 'ref:\s*\$\{\{ github.sha \}\}'
        $pagesWorkflow | Should -Match 'persist-credentials:\s*false'
        $pagesWorkflow | Should -Match 'rebuild-docs\.js --all'
        $pagesWorkflow | Should -Match 'node scripts/check-docs-site\.js'
        $pagesWorkflow | Should -Match 'name: legacy-dev-docs'
        $pagesWorkflow | Should -Match '\.docs-build-metadata\.json'
        $pagesWorkflow | Should -Match 'include-hidden-files:\s*true'
    }

    It "leaves deployment authority in the protected main controller" {
        $pagesWorkflow | Should -Not -Match 'pages:\s*write|id-token:\s*write|contents:\s*write'
        $pagesWorkflow | Should -Not -Match 'actions/deploy-pages|actions/upload-pages-artifact'
        $pagesWorkflow | Should -Not -Match 'ref:\s*main|sources/main'
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
