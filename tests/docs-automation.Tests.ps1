# tests/docs-automation.Tests.ps1
# Contract tests for deterministic documentation rebuild, deployment, and release sequencing.

Set-StrictMode -Version Latest

$repoRoot = if ($env:CG_TEST_ROOT) { $env:CG_TEST_ROOT } else { Split-Path $PSScriptRoot -Parent }
if ($env:CG_TEST_ROOT -and -not (Test-Path $env:CG_TEST_ROOT)) { throw "CG_TEST_ROOT '$env:CG_TEST_ROOT' does not exist" }

$rebuildWorkflow = Get-Content (Join-Path $repoRoot ".github\workflows\doc-rebuild.yml") -Raw -Encoding UTF8
$pagesWorkflow = Get-Content (Join-Path $repoRoot ".github\workflows\pages.yml") -Raw -Encoding UTF8
$releasePrompt = Get-Content (Join-Path $repoRoot ".github\prompts\cg-release.prompt.md") -Raw -Encoding UTF8
$scanner = Get-Content (Join-Path $repoRoot ".github\agents\cg-release-scanner.agent.md") -Raw -Encoding UTF8
$rebuildScript = Get-Content (Join-Path $repoRoot "scripts\rebuild-docs.js") -Raw -Encoding UTF8
$whatsNewScript = Get-Content (Join-Path $repoRoot "scripts\generate-whats-new.js") -Raw -Encoding UTF8

Describe "Documentation rebuild workflow contracts" {
    It "filters only approved canonical documentation inputs on main" {
        foreach ($pathFilter in @('.github/prompts/**', '.github/skills/**', '.github/agents/**', 'docs/**', 'scripts/rebuild-docs.js', 'scripts/generate-whats-new.js', 'scripts/check-docs-site.js', '.github/workflows/doc-rebuild.yml', '.github/workflows/pages.yml')) {
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
        foreach ($workflow in @($rebuildWorkflow, $pagesWorkflow)) {
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

    It "supports tag and explicit immutable-ref deployment without main freshness checks" {
        $pagesWorkflow | Should -Match 'tags:\s*\["v\*\.\*\.\*"\]'
        $pagesWorkflow | Should -Match 'workflow_dispatch:'
        $pagesWorkflow | Should -Match 'resolve-immutable-ref:'
        $pagesWorkflow | Should -Match 'needs:\s*resolve-immutable-ref'
        $pagesWorkflow | Should -Match 'merge-base --is-ancestor'
        $pagesWorkflow | Should -Match 'v\[0-9\]\+\\\.\[0-9\]\+\\\.\[0-9\]\+'
        $pagesWorkflow | Should -Match 'rebuild-docs\.js --all'
    }

    It "never rebuilds or mutates the downloaded main artifact" {
        $artifactJob = [regex]::Match($pagesWorkflow, '(?s)deploy-rebuild-artifact:.*?(?=\n  [a-z].*?:|\z)').Value
        $artifactJob | Should -Match '--verify-artifact'
        $artifactJob | Should -Match '--verify-fingerprint'
        $artifactJob | Should -Not -Match 'rebuild-docs\.js --all'
        $artifactJob | Should -Not -Match 'generate-whats-new\.js'
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
        $deployIndex = $releasePrompt.IndexOf('Wait for the Pages tag deployment')
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
        $releasePrompt | Should -Match 'git rev-parse --verify <next-tag>\^\{commit\}'
        $releasePrompt | Should -Match '--resume <tag>'
        $releasePrompt | Should -Match 'Never overwrite an[\s\S]*immutable payload or create a new tag during resume'
    }

    It "does not dispatch wiki rebuilds or derive scanner kinds from prose" {
        $releasePrompt | Should -Match 'Do not invoke `/cg-wiki`'
        $releasePrompt | Should -Match 'Do not derive kinds by scraping'
    }
}
