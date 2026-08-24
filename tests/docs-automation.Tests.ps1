# tests/docs-automation.Tests.ps1
# Contract tests for deterministic documentation rebuild, deployment, and release sequencing.

Set-StrictMode -Version Latest

$repoRoot = if ($env:CG_TEST_ROOT) { $env:CG_TEST_ROOT } else { Split-Path $PSScriptRoot -Parent }
if ($env:CG_TEST_ROOT -and -not (Test-Path $env:CG_TEST_ROOT)) { throw "CG_TEST_ROOT '$env:CG_TEST_ROOT' does not exist" }

$rebuildWorkflow = Get-Content (Join-Path $repoRoot ".github\workflows\doc-rebuild.yml") -Raw -Encoding UTF8
$pagesWorkflow = Get-Content (Join-Path $repoRoot ".github\workflows\pages.yml") -Raw -Encoding UTF8
$releaseWorkflow = Get-Content (Join-Path $repoRoot ".github\workflows\release-docs.yml") -Raw -Encoding UTF8
$releasePagesWorkflow = Get-Content (Join-Path $repoRoot ".github\workflows\release-pages.yml") -Raw -Encoding UTF8
$releasePrompt = Get-Content (Join-Path $repoRoot ".github\prompts\cg-release.prompt.md") -Raw -Encoding UTF8
$scanner = Get-Content (Join-Path $repoRoot ".github\agents\cg-release-scanner.agent.md") -Raw -Encoding UTF8
$rebuildScript = Get-Content (Join-Path $repoRoot "scripts\rebuild-docs.js") -Raw -Encoding UTF8
$whatsNewScript = Get-Content (Join-Path $repoRoot "scripts\generate-whats-new.js") -Raw -Encoding UTF8

Describe "Documentation rebuild workflow contracts" {
    It "filters only approved canonical documentation inputs on main" {
        foreach ($pathFilter in @('.github/prompts/**', '.github/skills/**', '.github/agents/**', 'docs/**', 'scripts/rebuild-docs.js', 'scripts/generate-whats-new.js', 'scripts/check-docs-site.js', '.github/workflows/doc-rebuild.yml', '.github/workflows/pages.yml', '.github/workflows/release-docs.yml', '.github/workflows/release-pages.yml')) {
            $escapedPathFilter = [regex]::Escape($pathFilter)
            $rebuildWorkflow | Should -Match $escapedPathFilter
        }
        $rebuildWorkflow | Should -Match 'branches:\s*\[main\]'
    }

    It "uses least privilege, detects no-op output, and stages only docs" {
        $rebuildWorkflow | Should -Match 'contents:\s*write'
        $rebuildWorkflow | Should -Match 'git diff --quiet -- docs/'
        $rebuildWorkflow | Should -Match 'git add -- docs/'
        $rebuildWorkflow | Should -Match 'git diff --cached --name-only'
        $rebuildWorkflow | Should -Match 'git push origin HEAD:refs/heads/main'
    }

    It "builds and validates complete docs before uploading provenance" {
        $buildIndex = $rebuildWorkflow.IndexOf('rebuild-docs.js --all')
        $validateIndex = $rebuildWorkflow.IndexOf('node scripts/check-docs-site.js')
        $uploadIndex = $rebuildWorkflow.IndexOf('Upload complete docs artifact')
        $buildIndex | Should -BeGreaterThan -1
        $validateIndex | Should -BeGreaterThan $buildIndex
        $uploadIndex | Should -BeGreaterThan $validateIndex
        $rebuildWorkflow | Should -Match 'docs-site'
        $rebuildWorkflow | Should -Match '\.docs-build-metadata\.json'
        $rebuildWorkflow | Should -Match 'include-hidden-files:\s*true'
        $rebuildWorkflow | Should -Match 'if-no-files-found:\s*error'
    }

    It "pins every privileged action to an immutable commit" {
        foreach ($workflow in @($rebuildWorkflow, $releaseWorkflow, $pagesWorkflow, $releasePagesWorkflow)) {
            foreach ($match in [regex]::Matches($workflow, 'uses:\s*[^@\s]+@([^\s#]+)')) {
                $match.Groups[1].Value | Should -Match '^[0-9a-f]{40}$'
            }
        }
    }
}

Describe "Pages exact-artifact deployment contracts" {
    It "runs only after successful main rebuild completion" {
        $pagesWorkflow | Should -Match 'workflow_run:'
        $pagesWorkflow | Should -Match 'Rebuild documentation'
        $pagesWorkflow | Should -Match "workflow_run\.conclusion == 'success'"
        $pagesWorkflow | Should -Match "workflow_run\.head_branch == 'main'"
    }

    It "downloads, verifies, freshness-checks, and uploads the unchanged artifact" {
        $downloadIndex = $pagesWorkflow.IndexOf('actions/download-artifact')
        $digestIndex = $pagesWorkflow.IndexOf('--verify-artifact')
        $freshnessIndex = $pagesWorkflow.IndexOf('--verify-fingerprint')
        $uploadIndex = $pagesWorkflow.IndexOf('path: site-artifact/docs')
        $downloadIndex | Should -BeGreaterThan -1
        $digestIndex | Should -BeGreaterThan $downloadIndex
        $freshnessIndex | Should -BeGreaterThan $digestIndex
        $uploadIndex | Should -BeGreaterThan $freshnessIndex
        $pagesWorkflow | Should -Match 'run-id:\s*\$\{\{ github\.event\.workflow_run\.id \}\}'
        $pagesWorkflow | Should -Match 'Skipping stale main rebuild artifact'
    }

    It "supports unprivileged tag builds through the protected workflow-run controller" {
        $releaseWorkflow | Should -Match 'tags:\s*\["v\*\.\*\.\*"\]'
        $releaseWorkflow | Should -Match 'release-docs-site'
        $releaseWorkflow | Should -Not -Match 'pages:\s*write|id-token:\s*write'
        $pagesWorkflow | Should -Not -Match '(?m)^\s*push:\s*$'
        $pagesWorkflow | Should -Not -Match 'workflow_dispatch:'
        $releasePagesWorkflow | Should -Match 'Build release documentation'
        $releasePagesWorkflow | Should -Match 'name: Deploy release documentation'
        $releasePagesWorkflow | Should -Match 'merge-base --is-ancestor'
        $releasePagesWorkflow | Should -Match 'v\[0-9\]\+\\\.\[0-9\]\+\\\.\[0-9\]\+'
        $releaseWorkflow | Should -Match 'rebuild-docs\.js --all'
    }

    It "accepts dev-series pre-release tags (v1.2.0.900x) in the unprivileged builder" {
        $tagPatterns = @([regex]::Matches($releaseWorkflow, '\$RELEASE_TAG"\s*=\~\s*([^ ]+)') | ForEach-Object { $_.Groups[1].Value } | Where-Object { $_ -match '^\^v' })
        $tagPatterns.Count | Should -Be 2
        ([regex]$tagPatterns[0]).IsMatch('v1.2.0.9004') | Should -Be $true
        ([regex]$tagPatterns[1]).IsMatch('v1.2.0') | Should -Be $true
        ([regex]$tagPatterns[1]).IsMatch('v1.2') | Should -Be $false
    }

    It "binds stable tags to main and prerelease tags to dev" {
        $releaseWorkflow | Should -Match 'required_branch="main"'
        $releaseWorkflow | Should -Match '\^v\[0-9\]\+\\\.\[0-9\]\+\\\.\[0-9\]\+\\\.\[0-9\]\+\$[\s\S]*required_branch="dev"'
        $releaseWorkflow | Should -Match 'is-ancestor "\$RELEASE_SHA" "origin/\$required_branch"'
        $releaseWorkflow | Should -Match 'is-ancestor origin/main "\$RELEASE_SHA"'
    }

    It "binds tag deployments to the exact latest durable payload" {
        $validatePayloadIndex = $releaseWorkflow.IndexOf('--validate-payload "releases/$RELEASE_TAG.json"')
        $validateSetIndex = $releaseWorkflow.IndexOf('--validate-release-set')
        $byteMatchIndex = $releaseWorkflow.IndexOf('cmp -s "releases/$RELEASE_TAG.json" releases/latest.json')
        $uploadIndex = $releaseWorkflow.IndexOf('Upload release documentation artifact')
        $validatePayloadIndex | Should -BeGreaterThan -1
        $validateSetIndex | Should -BeGreaterThan $validatePayloadIndex
        $byteMatchIndex | Should -BeGreaterThan $validateSetIndex
        $uploadIndex | Should -BeGreaterThan $byteMatchIndex
    }

    It "never rebuilds or mutates the downloaded main artifact" {
        $artifactJob = [regex]::Match($pagesWorkflow, '(?s)deploy-rebuild-artifact:.*?(?=\n  [a-z].*?:|\z)').Value
        $artifactJob | Should -Match '--verify-artifact'
        $artifactJob | Should -Match '--verify-fingerprint'
        $artifactJob | Should -Not -Match 'rebuild-docs\.js --all'
        $artifactJob | Should -Not -Match 'generate-whats-new\.js'
    }

    It "builds tagged code without Pages credentials and deploys only the verified prebuilt artifact" {
        $releaseWorkflow | Should -Match 'rebuild-docs\.js --all'
        $releaseWorkflow | Should -Match 'actions/upload-artifact'
        $releaseWorkflow | Should -Not -Match 'pages:\s*write|id-token:\s*write'
        $deployJob = [regex]::Match($releasePagesWorkflow, '(?s)deploy:.*?(?=\n  [a-z].*?:|\z)').Value
        $deployJob | Should -Match 'actions/download-artifact'
        $deployJob | Should -Match 'actions/upload-pages-artifact'
        $deployJob | Should -Match 'pages:\s*write'
        $deployJob | Should -Match 'ref:\s*main'
        $deployJob | Should -Match 'Artifact digest mismatch'
        $deployJob | Should -Match 'release-validation/current-latest\.json'
        $deployJob | Should -Not -Match 'rebuild-docs\.js --all'
    }
}

Describe "Deterministic generator contracts" {
    It "fingerprints canonical inputs and verifies every artifact file digest" {
        $rebuildScript | Should -Match 'canonicalInputFingerprint'
        $rebuildScript | Should -Match 'perFileDigests'
        $rebuildScript | Should -Match '--verify-fingerprint'
        $rebuildScript | Should -Match '--verify-artifact'
        $rebuildScript | Should -Match 'artifact digest mismatch'
    }

    It "validates source tags, deduplicates latest, caps history, and escapes payload text" {
        $whatsNewScript | Should -Match 'sourceUrl'
        $whatsNewScript | Should -Match 'MAX_RELEASES = 20'
        $whatsNewScript | Should -Match 'byte-match'
        $whatsNewScript | Should -Match 'must match newest immutable payload'
        $whatsNewScript | Should -Match 'GPID-WB/compound-gpid'
        $whatsNewScript | Should -Match 'must not be a symbolic link'
        $whatsNewScript | Should -Match 'View older releases'
        $whatsNewScript | Should -Match 'escapeText'
    }
}

Describe "Release payload sequencing contracts" {
    It "requires scanner Release Payload JSON with exact controlled kinds" {
        $scanner | Should -Match '## Release Payload'
        $scanner | Should -Match '"kind": "new\|fixed\|internal"'
        $scanner | Should -Match 'only `new`, `fixed`, or `internal` kinds'
    }

    It "creates and validates durable payloads before exact tag and API publication" {
        $payloadIndex = $releasePrompt.IndexOf('releases/<next-tag>.json')
        $validateIndex = $releasePrompt.IndexOf('--validate-payload releases/<next-tag>.json')
        $commitIndex = $releasePrompt.IndexOf('chore(release): prepare <next-tag> payload')
        $tagIndex = $releasePrompt.IndexOf('git tag <next-tag>')
        $deployIndex = $releasePrompt.IndexOf('Wait for the unprivileged `release-docs.yml`')
        $apiIndex = $releasePrompt.IndexOf('.\create-release.ps1 -Tag <tag>')
        $payloadIndex | Should -BeGreaterThan -1
        $validateIndex | Should -BeGreaterThan $payloadIndex
        $commitIndex | Should -BeGreaterThan $validateIndex
        $tagIndex | Should -BeGreaterThan $commitIndex
        $deployIndex | Should -BeGreaterThan $tagIndex
        $apiIndex | Should -BeGreaterThan $deployIndex
    }

    It "uses record delimiters, idempotent tag handling, and an explicit resume path" {
        $releasePrompt | Should -Match '%H%x1f%s%x1f%b%x1e'
        $scanner | Should -Match '0x1e'
        $releasePrompt | Should -Match 'git rev-parse --verify "<next-tag>\^\{commit\}"'
        $releasePrompt | Should -Match '--resume <tag>'
        $releasePrompt | Should -Match '\^v\\d\+\\\.\\d\+\\\.\\d\+\(\\\.\\d\+\)\?\$'
        $releasePrompt | Should -Match 'four-component `vX\.Y\.Z\.<build>` prerelease tag'
        $releasePrompt | Should -Match 'Four-component tags always[\s\S]*GitHub prereleases'
        $releasePrompt | Should -Match 'Add `-Prerelease` whenever `<prerelease>` is `true`'
        $releasePrompt | Should -Match 'Never overwrite an immutable[\s\S]*payload or create a new tag during resume'
    }

    It "maps stable releases to main and four-component prereleases to dev" {
        $releasePrompt | Should -Match 'Set `<release-branch>` to `dev` when `<prerelease>` is `true`; otherwise set it[\s\S]*to `main`'
        $releasePrompt | Should -Match 'git fetch origin <release-branch> --tags'
        $releasePrompt | Should -Match 'git rev-parse origin/<release-branch>'
        $releasePrompt | Should -Match 'git push origin <release-branch>'
        $releasePrompt | Should -Match 'merge-base --is-ancestor origin/main HEAD'
        $releasePrompt | Should -Not -Match 'Require a clean, up-to-date `main` checkout before writing payloads'
    }

    It "requires immutable tags, admin-only tag creation, and protected dev history" {
        $releasePrompt | Should -Match 'Protect release tags'
        $releasePrompt | Should -Match 'Restrict release tag creation'
        $releasePrompt | Should -Match 'Protect dev'
        $releasePrompt | Should -Match 'Draft releases are not supported'
    }

    It "uses the durable latest payload rather than temporary tags as the scan baseline" {
        $releasePrompt | Should -Match 'Get-Content releases/latest\.json'
        $releasePrompt | Should -Match '--validate-release-set'
        $releasePrompt | Should -Match 'gh release view \$latestTag'
        $releasePrompt | Should -Match 'Every immutable payload must have a matching non-draft GitHub Release'
        $releasePrompt | Should -Match 'Never use unrestricted `git describe`'
        $releasePrompt | Should -Not -Match 'git describe --tags --abbrev=0'
    }

    It "allows exact-tag resume after the release branch advances" {
        $resumeBlock = [regex]::Match($releasePrompt, '(?s)### Resume An Interrupted Release.*?(?=### Step 6:)').Value
        $resumeBlock | Should -Match 'detached checkout is allowed'
        $resumeBlock | Should -Match 'merge-base --is-ancestor "<tag>\^\{commit\}" origin/<release-branch>'
        $resumeBlock | Should -Not -Match 'branch --show-current'
    }

    It "does not dispatch wiki rebuilds or derive scanner kinds from prose" {
        $releasePrompt | Should -Match 'Do not invoke `/cg-wiki`'
        $releasePrompt | Should -Match 'Do not derive kinds by scraping'
    }
}
