# tests/cr-prompts.Tests.ps1
# Pester tests for compound-research (/cr-*) prompt and skill files.
#
# Run with: Invoke-Pester tests/cr-prompts.Tests.ps1 -Quiet
# Compatible with Pester 4.10.1

$repoRoot = if ($env:CG_TEST_ROOT) {
    if (-not (Test-Path (Join-Path $env:CG_TEST_ROOT 'compound-gpid.md'))) {
        throw "CG_TEST_ROOT ('$env:CG_TEST_ROOT') does not point to a valid Compound GPID repository (missing compound-gpid.md)"
    }
    $env:CG_TEST_ROOT
} else {
    Split-Path $PSScriptRoot -Parent
}
. "$PSScriptRoot/helpers.ps1"

# ---------------------------------------------------------------------------
# Helper: resolve paths
# ---------------------------------------------------------------------------
$promptsDir = Join-Path $repoRoot ".github\prompts"
$skillsDir  = Join-Path $repoRoot ".github\skills"

# ---------------------------------------------------------------------------
# CR prompt files — structural checks
# ---------------------------------------------------------------------------

Describe "CR prompt files - structural checks" {
    $crPrompts = @(
        'cr-brainstorm.prompt.md',
        'cr-plan.prompt.md',
        'cr-work.prompt.md',
        'cr-review.prompt.md',
        'cr-compound.prompt.md'
    )

    foreach ($name in $crPrompts) {
        $path = Join-Path $promptsDir $name

        Context "$name - existence and frontmatter" {
            $fm = Get-Frontmatter -FilePath $path

            It "[$name] exists" {
                Test-Path $path | Should -Be $true
            }

            It "[$name] has a description: field in frontmatter" {
                ($fm -match 'description:') | Should -Be $true
            }

            It "[$name] has module: research" {
                ($fm -match '(?m)^\s*module:\s*[''"]?research[''"]?\s*$') | Should -Be $true
            }

            It "[$name] does not have a tools: restriction (orchestrating prompts must not restrict tools)" {
                ($fm -notmatch '(?m)^\s*tools:') | Should -Be $true
            }
        }
    }
}

# ---------------------------------------------------------------------------
# cr-brainstorm.prompt.md — research task classifier
# ---------------------------------------------------------------------------

Describe "cr-brainstorm.prompt.md - research task classification" {
    $path    = Join-Path $promptsDir "cr-brainstorm.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "contains Step 1.1 (Research Task Classification)" {
        ($content -match 'Step 1\.1') | Should -Be $true
    }

    It "lists Theory/Modeling as a task type" {
        ($content -match 'Theory/Modeling') | Should -Be $true
    }

    It "lists Specification Analysis as a task type" {
        ($content -match 'Specification Analysis') | Should -Be $true
    }

    It "lists EDA as a task type" {
        ($content -match '\bEDA\b') | Should -Be $true
    }

    It "lists Implementation as a task type" {
        ($content -match '\bImplementation\b') | Should -Be $true
    }

    It "lists ML/Prediction as a task type" {
        ($content -match 'ML/Prediction') | Should -Be $true
    }

    It "lists Writing as a task type" {
        ($content -match '\bWriting\b') | Should -Be $true
    }

    It "lists Tables/Figures as a task type" {
        ($content -match 'Tables/Figures') | Should -Be $true
    }

    It "lists Reproducibility as a task type" {
        ($content -match '\bReproducibility\b') | Should -Be $true
    }

    It "contains Devil's Advocate step (Step 3.5)" {
        ($content -match '3\.5') | Should -Be $true
        ($content -match '(?i)devil') | Should -Be $true
    }

    It "handoff references /cr-plan (not /cg-plan)" {
        ($content -match '/cr-plan') | Should -Be $true
    }

    It "loads cr-skill-research-workflow" {
        ($content -match 'cr-skill-research-workflow') | Should -Be $true
    }

    It "checks modules: includes research before proceeding" {
        ($content -match '(?i)modules') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cr-work.prompt.md — P0 enforcement
# ---------------------------------------------------------------------------

Describe "cr-work.prompt.md - P0 enforcement" {
    $path    = Join-Path $promptsDir "cr-work.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "contains seed enforcement logic" {
        ($content -match '(?i)seed') | Should -Be $true
    }

    It "contains specification logging to manifest.json" {
        ($content -match 'manifest\.json') | Should -Be $true
    }

    It "supports phased execution (/cr-work phase1 pattern)" {
        ($content -match '(?i)phase') | Should -Be $true
    }

    It "references cr-skill-research-integrity" {
        ($content -match 'cr-skill-research-integrity') | Should -Be $true
    }

    It "references cr-skill-research-workflow" {
        ($content -match 'cr-skill-research-workflow') | Should -Be $true
    }

    It "includes derivation cross-reference check" {
        ($content -match '(?i)derivation') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cr-review.prompt.md — agent orchestration
# ---------------------------------------------------------------------------

Describe "cr-review.prompt.md - agent orchestration" {
    $path    = Join-Path $promptsDir "cr-review.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "references @cg-code-quality" {
        ($content -match '@cg-code-quality') | Should -Be $true
    }

    It "references @cg-testing" {
        ($content -match '@cg-testing') | Should -Be $true
    }

    It "references @cg-reproducibility" {
        ($content -match '@cg-reproducibility') | Should -Be $true
    }

    It "references @cg-data-quality" {
        ($content -match '@cg-data-quality') | Should -Be $true
    }

    It "references @cr-research-integrity" {
        ($content -match '@cr-research-integrity') | Should -Be $true
    }

    It "references @cr-mathematical-verification" {
        ($content -match '@cr-mathematical-verification') | Should -Be $true
    }

    It "references @cr-identification-audit" {
        ($content -match '@cr-identification-audit') | Should -Be $true
    }

    It "contains P0 priority token in findings format" {
        ($content -match 'P0') | Should -Be $true
    }

    It "contains P1 priority token in findings format" {
        ($content -match 'P1') | Should -Be $true
    }

    It "contains P2 priority token in findings format" {
        ($content -match 'P2') | Should -Be $true
    }

    It "contains P3 priority token in findings format" {
        ($content -match 'P3') | Should -Be $true
    }

    It "contains Monte Carlo verification offer" {
        ($content -match '(?i)monte carlo') | Should -Be $true
    }

    It "writes review report to .cg-docs/reviews/" {
        ($content -match '\.cg-docs[/\\]reviews') | Should -Be $true
    }

    It "instructs Do NOT delegate the report write" {
        ($content -match 'Do NOT delegate') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cr-compound.prompt.md — extended categories
# ---------------------------------------------------------------------------

Describe "cr-compound.prompt.md - research categories" {
    $path    = Join-Path $promptsDir "cr-compound.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "contains 'identification' research category" {
        ($content -match '`identification`') | Should -Be $true
    }

    It "contains 'specification' research category" {
        ($content -match '`specification`') | Should -Be $true
    }

    It "contains 'derivation' research category" {
        ($content -match '`derivation`') | Should -Be $true
    }

    It "contains 'ml-methodology' research category" {
        ($content -match '`ml-methodology`') | Should -Be $true
    }

    It "contains 'reproducibility' research category" {
        ($content -match '`reproducibility`') | Should -Be $true
    }

    It "contains inherited engineering category 'bugs'" {
        ($content -match '`bugs`') | Should -Be $true
    }

    It "contains inherited engineering category 'testing-patterns'" {
        ($content -match '`testing-patterns`') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cr-skill-research-workflow — content validation
# ---------------------------------------------------------------------------

Describe "cr-skill-research-workflow/SKILL.md - content" {
    $path    = Join-Path $skillsDir "cr-skill-research-workflow\SKILL.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "exists" {
        Test-Path $path | Should -Be $true
    }

    It "has module: research" {
        $fm = Get-Frontmatter -FilePath $path
        ($fm -match '(?m)^\s*module:\s*[''"]?research[''"]?\s*$') | Should -Be $true
    }

    It "contains all 8 task types" {
        ($content -match 'Theory/Modeling') | Should -Be $true
        ($content -match 'Specification Analysis') | Should -Be $true
        ($content -match '\bEDA\b') | Should -Be $true
        ($content -match '\bImplementation\b') | Should -Be $true
        ($content -match 'ML/Prediction') | Should -Be $true
        ($content -match '\bWriting\b') | Should -Be $true
        ($content -match 'Tables/Figures') | Should -Be $true
        ($content -match '\bReproducibility\b') | Should -Be $true
    }

    It "contains P0-P3 priority table" {
        ($content -match 'P0') | Should -Be $true
        ($content -match 'P1') | Should -Be $true
        ($content -match 'P2') | Should -Be $true
        ($content -match 'P3') | Should -Be $true
    }

    It "contains .cg-docs/research/ directory layout" {
        ($content -match '\.cg-docs[/\\]research') | Should -Be $true
    }

    It "contains seed enforcement section" {
        ($content -match '(?i)seed') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cr-skill-research-integrity — content validation
# ---------------------------------------------------------------------------

Describe "cr-skill-research-integrity/SKILL.md - content" {
    $path    = Join-Path $skillsDir "cr-skill-research-integrity\SKILL.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "exists" {
        Test-Path $path | Should -Be $true
    }

    It "has module: research" {
        $fm = Get-Frontmatter -FilePath $path
        ($fm -match '(?m)^\s*module:\s*[''"]?research[''"]?\s*$') | Should -Be $true
    }

    It "contains Error Class 1: Code-Math Mismatch" {
        ($content -match '(?i)code.math mismatch') | Should -Be $true
    }

    It "contains Error Class 2: Specification Searching" {
        ($content -match '(?i)specification searching') | Should -Be $true
    }

    It "contains Error Class 3: Identification Theater" {
        ($content -match '(?i)identification theater') | Should -Be $true
    }

    It "contains Error Class 4: Unseeded Randomness" {
        ($content -match '(?i)unseeded randomness') | Should -Be $true
    }

    It "contains Error Class 5: Asymptotic Assumption Violations" {
        ($content -match '(?i)asymptotic') | Should -Be $true
    }

    It "contains Error Class 6: Wrong SE Clustering" {
        ($content -match '(?i)clustering') | Should -Be $true
    }

    It "contains Error Class 7: Distributional Assumption Untested" {
        ($content -match '(?i)distributional assumption') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-skill-setup — research directory layout documented
# ---------------------------------------------------------------------------

Describe "cg-skill-setup/SKILL.md - research directory layout" {
    $path    = Join-Path $skillsDir "cg-skill-setup\SKILL.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "documents .cg-docs/research/ directory" {
        ($content -match '\.cg-docs[/\\]research') | Should -Be $true
    }

    It "documents research directories as conditional on research module" {
        ($content -match '(?i)research module|modules.*research') | Should -Be $true
    }

    It "documents modules: field in compound-gpid.local.md schema" {
        ($content -match '(?m)^\s*modules:') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# CR agent files — structural checks
# ---------------------------------------------------------------------------

Describe "CR agent files - structural checks" {
    $crAgents = @(
        'cr-research-integrity.agent.md',
        'cr-mathematical-verification.agent.md',
        'cr-identification-audit.agent.md',
        'cr-econometric-reasoning.agent.md'
    )

    $agentsDir = Join-Path $repoRoot ".github\agents"

    foreach ($name in $crAgents) {
        $path = Join-Path $agentsDir $name

        Context "$name - existence and frontmatter" {
            $fm = Get-Frontmatter -FilePath $path

            It "[$name] exists" {
                Test-Path $path | Should -Be $true
            }

            It "[$name] has a description: field in frontmatter" {
                ($fm -match 'description:') | Should -Be $true
            }

            It "[$name] has module: research" {
                ($fm -match '(?m)^\s*module:\s*[''"]?research[''"]?\s*$') | Should -Be $true
            }

            It "[$name] has tools: ['read', 'search'] (no write)" {
                ($fm -match "tools:.*'read'") | Should -Be $true
                ($fm -notmatch "'write'") | Should -Be $true
            }

            It "[$name] has user-invocable: false" {
                ($fm -match '(?m)^\s*user-invocable:\s*false') | Should -Be $true
            }

            It "[$name] has a model: field in frontmatter" {
                ($fm -match '(?m)^\s*model:') | Should -Be $true
            }
        }
    }
}

# ---------------------------------------------------------------------------
# cr-research-integrity.agent.md — content
# ---------------------------------------------------------------------------

Describe "cr-research-integrity.agent.md - content" {
    $path    = Join-Path (Join-Path $repoRoot ".github\agents") "cr-research-integrity.agent.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "references Code-Math Mismatch error class" {
        ($content -match '(?i)code.math mismatch') | Should -Be $true
    }

    It "references Specification Searching error class" {
        ($content -match '(?i)specification searching') | Should -Be $true
    }

    It "references Identification Theater error class" {
        ($content -match '(?i)identification theater') | Should -Be $true
    }

    It "references Unseeded Randomness error class" {
        ($content -match '(?i)unseeded randomness') | Should -Be $true
    }

    It "references Asymptotic assumption violation check" {
        ($content -match '(?i)asymptotic') | Should -Be $true
    }

    It "references Wrong SE Clustering check" {
        ($content -match '(?i)clustering') | Should -Be $true
    }

    It "references Distributional assumption check" {
        ($content -match '(?i)distributional assumption') | Should -Be $true
    }

    It "contains untrusted-content safety note with 'execute or relay'" {
        ($content -match '(?i)execute or relay') | Should -Be $true
    }

    It "output format includes [cr-research-integrity] tag" {
        ($content -match '\[cr-research-integrity\]') | Should -Be $true
    }

    It "contains empty-file guard at protocol start" {
        ($content -match '(?i)zero-byte|empty file.*research integrity check skipped') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cr-mathematical-verification.agent.md — content
# ---------------------------------------------------------------------------

Describe "cr-mathematical-verification.agent.md - content" {
    $path    = Join-Path (Join-Path $repoRoot ".github\agents") "cr-mathematical-verification.agent.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "references .cg-docs/research/derivations/" {
        ($content -match '\.cg-docs[/\\]research[/\\]derivations') | Should -Be $true
    }

    It "contains variable mapping table concept" {
        ($content -match '(?i)variable mapping table') | Should -Be $true
    }

    It "uses Claude Opus 4.6 model" {
        $fm = Get-Frontmatter -FilePath $path
        ($fm -match 'Claude Opus 4\.6') | Should -Be $true
    }

    It "contains graceful skip message for no derivation files" {
        ($content -match 'No derivation files found') | Should -Be $true
    }

    It "contains 20-file pagination limit" {
        ($content -match '(?i)more than 20.*derivation|File count limit') | Should -Be $true
    }

    It "contains 50 KB circuit-breaker for oversized files" {
        ($content -match '50 KB|50KB') | Should -Be $true
    }

    It "contains prompt injection guard with SYSTEM/OVERRIDE detection" {
        ($content -match '(?i)prompt injection|SYSTEM|OVERRIDE') | Should -Be $true
    }

    It "contains structural guard preventing prose relay from derivation files" {
        ($content -match '(?i)structural guard|never relay prose') | Should -Be $true
    }

    It "includes code file path validation against review set" {
        ($content -match '(?i)code file path validation|not among the files under review') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cr-identification-audit.agent.md — content
# ---------------------------------------------------------------------------

Describe "cr-identification-audit.agent.md - content" {
    $path    = Join-Path (Join-Path $repoRoot ".github\agents") "cr-identification-audit.agent.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "covers IV/2SLS terminology" {
        ($content -match '(?i)IV/2SLS') | Should -Be $true
    }

    It "contains ivreg command indicator" {
        ($content -match 'ivreg') | Should -Be $true
    }

    It "covers RDD terminology" {
        ($content -match '(?i)\bRDD\b') | Should -Be $true
    }

    It "covers regression discontinuity terminology" {
        ($content -match '(?i)regression discontinuity') | Should -Be $true
    }

    It "covers DiD terminology" {
        ($content -match '(?i)\bDiD\b') | Should -Be $true
    }

    It "covers difference-in-differences terminology" {
        ($content -match '(?i)difference.in.differences') | Should -Be $true
    }

    It "covers control function approach" {
        ($content -match '(?i)control function') | Should -Be $true
    }

    It "contains required diagnostic table (first-stage F)" {
        ($content -match '(?i)first.stage') | Should -Be $true
    }

    It "contains McCrary density test requirement for RDD" {
        ($content -match '(?i)McCrary') | Should -Be $true
    }

    It "contains rddensity command reference" {
        ($content -match 'rddensity') | Should -Be $true
    }

    It "contains parallel trends requirement for DiD" {
        ($content -match '(?i)parallel trends') | Should -Be $true
    }

    It "contains graceful skip message for no identification strategy" {
        ($content -match 'No identification strategy detected') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cr-econometric-reasoning.agent.md — content
# ---------------------------------------------------------------------------

Describe "cr-econometric-reasoning.agent.md - content" {
    $path    = Join-Path (Join-Path $repoRoot ".github\agents") "cr-econometric-reasoning.agent.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "references DGP (data-generating process)" {
        ($content -match '\bDGP\b') | Should -Be $true
    }

    It "references MLE estimation strategy" {
        ($content -match '\bMLE\b') | Should -Be $true
    }

    It "references GMM estimation strategy" {
        ($content -match '\bGMM\b') | Should -Be $true
    }

    It "contains assumption-data consistency section" {
        ($content -match '(?i)assumption.data consistency') | Should -Be $true
    }

    It "contains PhD student scaffolding reference" {
        ($content -match '(?i)PhD student') | Should -Be $true
    }

    It "uses Claude Opus 4.6 model" {
        $fm = Get-Frontmatter -FilePath $path
        ($fm -match 'Claude Opus 4\.6') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cr-review.prompt.md - Phase 3 wiring verification
# ---------------------------------------------------------------------------

Describe "cr-review.prompt.md - Phase 3 wiring" {
    $path    = Join-Path $promptsDir "cr-review.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8
    $lines   = $content -split "`n"

    It "does NOT contain umbrella Phase 2/3 skip paragraph" {
        ($content -match 'For Phase 2, they are not yet available') | Should -Be $false
    }

    It "does NOT contain Phase 3 annotation on @cr-research-integrity" {
        # The line for cr-research-integrity must not say Phase 3
        $riLine = $lines | Where-Object { $_ -match 'cr-research-integrity' } | Select-Object -First 1
        ($riLine -match 'Phase 3') | Should -Be $false
    }

    It "does NOT contain Phase 3 annotation on @cr-mathematical-verification" {
        $mvLine = $lines | Where-Object { $_ -match 'cr-mathematical-verification' } | Select-Object -First 1
        ($mvLine -match 'Phase 3') | Should -Be $false
    }

    It "does NOT contain Phase 3 annotation on @cr-identification-audit" {
        $iaLine = $lines | Where-Object { $_ -match 'cr-identification-audit' -and $_ -notmatch 'Phase 4' } | Select-Object -First 1
        ($iaLine -match 'Phase 3') | Should -Be $false
    }

    It "does NOT contain Phase 4 annotation on @cr-econometric-reasoning" {
        $erLine = $lines | Where-Object { $_ -match 'cr-econometric-reasoning' } | Select-Object -First 1
        ($erLine -match 'Phase 4') | Should -Be $false
    }

    It "still contains Phase 5 annotation for @cr-specification-analysis (future agent)" {
        ($content -match 'cr-specification-analysis.*Phase 5') | Should -Be $true
    }

    It "still contains Phase 5 annotation for @cr-ml-methodology (future agent)" {
        ($content -match 'cr-ml-methodology.*Phase 5') | Should -Be $true
    }

    It "contains availability guard message" {
        ($content -match '(?i)not available.*skip') | Should -Be $true
    }

    It "@cr-identification-audit appears in Theory/Modeling dispatch row" {
        ($content -match 'Theory/Modeling.*cr-identification-audit') | Should -Be $true
    }

    It "still contains Phase 6 annotation for @cr-academic-writing (future agent)" {
        ($content -match 'cr-academic-writing.*Phase 6') | Should -Be $true
    }

    It "still contains Phase 7 annotation for @cr-replication-package (future agent)" {
        ($content -match 'cr-replication-package.*Phase 7') | Should -Be $true
    }

    It "Step 7 Handoff routes to /cg-fix-triage (not /cr-fix-triage)" {
        ($content -match 'Step 7') | Should -Be $true
        ($content -match '`/cg-fix-triage`') | Should -Be $true
        ($content -notmatch '`/cr-fix-triage`') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cr-review.prompt.md — end-to-end journey tests
# ---------------------------------------------------------------------------

Describe "cr-review.prompt.md - dispatch journey" {
    $path            = Join-Path $promptsDir "cr-review.prompt.md"
    $content         = Get-Content $path -Raw -Encoding UTF8
    $cgReviewPath    = Join-Path $promptsDir "cg-review.prompt.md"
    $cgReviewContent = Get-Content $cgReviewPath -Raw -Encoding UTF8

    It "Theory/Modeling dispatch row routes to both @cr-identification-audit and @cr-econometric-reasoning" {
        # Both agents must appear in the same Theory/Modeling row
        ($content -match 'Theory/Modeling.*cr-identification-audit') | Should -Be $true
        ($content -match 'Theory/Modeling.*cr-econometric-reasoning') | Should -Be $true
    }

    It "contains identification override that always dispatches @cr-identification-audit when IV patterns present" {
        ($content -match '(?i)identification override') | Should -Be $true
        ($content -match '(?i)feols.*ivreg.*rdrobust') | Should -Be $true
    }

    It "contains plan file validation before dispatch" {
        ($content -match '(?i)plan file not found') | Should -Be $true
    }

    It "contains file accessibility validation before dispatch" {
        ($content -match '(?i)not found.*excluded from review') | Should -Be $true
    }

    It "verify mode exception dispatches @cr-research-integrity when prior P0 cr-* findings open" {
        # This fix lives in cg-review.prompt.md (engineering prompt) not cr-review.prompt.md
        ($cgReviewContent -match '(?i)research integrity exception') | Should -Be $true
        ($cgReviewContent -match '(?i)\[cr-\*\]') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.4 — cr-plan.prompt.md content tests
# ---------------------------------------------------------------------------

Describe "cr-plan.prompt.md - research planning process" {
    $path    = Join-Path $promptsDir "cr-plan.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "contains Step 0 (Get Bearings) that reads compound-gpid.md" {
        ($content -match 'compound-gpid\.md') | Should -Be $true
    }

    It "loads cr-skill-research-workflow" {
        ($content -match 'cr-skill-research-workflow') | Should -Be $true
    }

    It "enforces P0 seed requirement in plan template" {
        ($content -match '(?i)seed') | Should -Be $true
    }

    It "enforces P0 derivation file structure" {
        ($content -match '(?i)derivation') | Should -Be $true
    }

    It "enforces P0 specification logging" {
        ($content -match '(?i)specification') | Should -Be $true
    }

    It "handoff at end routes toward /cr-work (not /cg-work)" {
        ($content -match '/cr-work') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.5 — CR handoff chain tests
# ---------------------------------------------------------------------------

Describe "CR handoff chain" {
    # Hoist reads to Describe scope to avoid per-It disk reads
    $bsContent     = Get-Content (Join-Path $promptsDir "cr-brainstorm.prompt.md") -Raw -Encoding UTF8
    $planContent   = Get-Content (Join-Path $promptsDir "cr-plan.prompt.md")       -Raw -Encoding UTF8
    $workContent   = Get-Content (Join-Path $promptsDir "cr-work.prompt.md")       -Raw -Encoding UTF8
    $reviewContent = Get-Content (Join-Path $promptsDir "cr-review.prompt.md")     -Raw -Encoding UTF8

    It "cr-brainstorm handoff reaches /cr-plan" {
        ($bsContent -match '/cr-plan') | Should -Be $true
    }

    It "cr-plan handoff reaches /cr-work" {
        ($planContent -match '/cr-work') | Should -Be $true
    }

    It "cr-work handoff reaches /cr-review" {
        ($workContent -match '/cr-review') | Should -Be $true
    }

    It "cr-review handoff reaches /cr-compound or /cg-compound" {
        ($reviewContent -match '/cr-compound|/cg-compound') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.9 — cr-brainstorm: availability guard when modules: research absent
# ---------------------------------------------------------------------------

Describe "cr-brainstorm.prompt.md - modules availability guard" {
    $path    = Join-Path $promptsDir "cr-brainstorm.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "instructs checking modules includes research before proceeding" {
        ($content -match '(?i)modules.*research|research.*module') | Should -Be $true
    }

    It "warns or asks confirmation when research module not enabled" {
        ($content -match '(?i)not enabled|run.*cg-setup|proceed anyway') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P3.5 — CR files must declare module: research in frontmatter
# ---------------------------------------------------------------------------

Describe "CR files - module: research frontmatter" {
    $crPrompts = @('cr-brainstorm', 'cr-plan', 'cr-work', 'cr-review', 'cr-compound')
    foreach ($name in $crPrompts) {
        $promptFile  = Join-Path $promptsDir "$name.prompt.md"
        $frontmatter = if (Test-Path $promptFile) { Get-Frontmatter -FilePath $promptFile } else { "" }

        It "$name.prompt.md has module: research in frontmatter" {
            ($frontmatter -match 'module:\s*research') | Should -Be $true
        }
    }

    $crSkills = @('cr-skill-research-workflow', 'cr-skill-research-integrity')
    foreach ($skill in $crSkills) {
        $skillFile   = Join-Path $repoRoot ".github\skills\$skill\SKILL.md"
        $frontmatter = if (Test-Path $skillFile) { Get-Frontmatter -FilePath $skillFile } else { "" }

        It "$skill/SKILL.md has module: research in frontmatter" {
            ($frontmatter -match 'module:\s*research') | Should -Be $true
        }
    }

    $crAgents = @('cr-research-integrity', 'cr-mathematical-verification', 'cr-identification-audit', 'cr-econometric-reasoning')
    foreach ($agent in $crAgents) {
        $agentFile   = Join-Path $repoRoot ".github\agents\$agent.agent.md"
        $frontmatter = if (Test-Path $agentFile) { Get-Frontmatter -FilePath $agentFile } else { "" }

        It "$agent.agent.md has module: research in frontmatter" {
            ($frontmatter -match 'module:\s*research') | Should -Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# Phase 4 skills — existence and frontmatter
# ---------------------------------------------------------------------------

Describe "Phase 4 skills - existence and frontmatter" {
    $phase4Skills = @(
        'cr-skill-structural-econometrics',
        'cr-skill-mathematical-derivation',
        'cr-skill-symbolic-verification',
        'cr-skill-identification-strategies',
        'cr-skill-theory-data-dialogue',
        'cr-skill-research-eda'
    )

    foreach ($skill in $phase4Skills) {
        $path = Join-Path $skillsDir "$skill\SKILL.md"

        Context "$skill/SKILL.md" {
            $fm = Get-Frontmatter -FilePath $path

            It "[$skill] exists" {
                Test-Path $path | Should -Be $true
            }

            It "[$skill] has module: research" {
                ($fm -match '(?m)^\s*module:\s*[''"]?research[''"]?\s*$') | Should -Be $true
            }

            It "[$skill] has a name: field matching the skill directory" {
                ($fm -match "name:\s*$skill") | Should -Be $true
            }

            It "[$skill] has a description: field" {
                ($fm -match 'description:') | Should -Be $true
            }
        }
    }
}

# ---------------------------------------------------------------------------
# Phase 4 skills — key content sections
# ---------------------------------------------------------------------------

Describe "cr-skill-structural-econometrics/SKILL.md - content" {
    $path    = Join-Path $skillsDir "cr-skill-structural-econometrics\SKILL.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "contains Discrete Choice section" {
        ($content -match '(?i)discrete choice') | Should -Be $true
    }

    It "contains Dynamic Programming section" {
        ($content -match '(?i)dynamic programming') | Should -Be $true
    }

    It "contains Simulation-Based Estimation section" {
        ($content -match '(?i)simulation.based estimation|MSM|SMM') | Should -Be $true
    }

    It "contains Maximum Likelihood section" {
        ($content -match '(?i)maximum likelihood|MLE for structural') | Should -Be $true
    }

    It "contains GMM section" {
        ($content -match '\bGMM\b') | Should -Be $true
    }

    It "contains Standard Errors section" {
        ($content -match '(?i)standard errors') | Should -Be $true
    }

    It "contains Identification section" {
        ($content -match '(?i)identification') | Should -Be $true
    }

    It "contains anti-patterns table" {
        ($content -match '(?i)## .*anti-pattern|Anti-Patterns') | Should -Be $true
    }
}

Describe "cr-skill-mathematical-derivation/SKILL.md - content" {
    $path    = Join-Path $skillsDir "cr-skill-mathematical-derivation\SKILL.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "contains Notation Discipline section" {
        ($content -match '(?i)notation discipline') | Should -Be $true
    }

    It "contains Equation Conventions section" {
        ($content -match '(?i)equation convention|equation numbering') | Should -Be $true
    }

    It "contains FOC Derivation section" {
        ($content -match '(?i)FOC') | Should -Be $true
    }

    It "contains Common Derivation Techniques section" {
        ($content -match '(?i)envelope theorem|leibniz|change of variable') | Should -Be $true
    }

    It "contains Asymptotic Expansions section" {
        ($content -match '(?i)asymptotic expansion|sandwich variance') | Should -Be $true
    }

    It "contains Code-Math Variable Mapping section" {
        ($content -match '(?i)variable mapping') | Should -Be $true
    }

    It "contains Derivation File Organization section" {
        ($content -match '(?i)derivation file organization|derivation.*organization') | Should -Be $true
    }

    It "references .cg-docs/research/derivations/" {
        ($content -match '\.cg-docs[/\\]research[/\\]derivations') | Should -Be $true
    }

    It "contains anti-patterns table" {
        ($content -match '(?i)## .*anti-pattern|Anti-Patterns') | Should -Be $true
    }
}

Describe "cr-skill-symbolic-verification/SKILL.md - content" {
    $path    = Join-Path $skillsDir "cr-skill-symbolic-verification\SKILL.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "contains SymPy gradient verification section" {
        ($content -match '(?i)sympy') | Should -Be $true
    }

    It "contains Hessian verification section" {
        ($content -match '(?i)hessian') | Should -Be $true
    }

    It "contains Moment Condition Verification section" {
        ($content -match '(?i)moment condition') | Should -Be $true
    }

    It "references @cr-mathematical-verification" {
        ($content -match '@cr-mathematical-verification') | Should -Be $true
    }

    It "contains numerical verification harness" {
        ($content -match '(?i)numerical verification harness') | Should -Be $true
    }

    It "contains anti-patterns table" {
        ($content -match '(?i)## .*anti-pattern|Anti-Patterns') | Should -Be $true
    }
}

Describe "cr-skill-identification-strategies/SKILL.md - content" {
    $path    = Join-Path $skillsDir "cr-skill-identification-strategies\SKILL.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "contains IV/2SLS section" {
        ($content -match 'IV/2SLS') | Should -Be $true
    }

    It "contains RDD section" {
        ($content -match '\bRDD\b') | Should -Be $true
    }

    It "contains DiD section" {
        ($content -match '(?i)difference.in.differences') | Should -Be $true
    }

    It "contains Event Studies section" {
        ($content -match '(?i)event stud') | Should -Be $true
    }

    It "contains Synthetic Control section" {
        ($content -match '(?i)synthetic control') | Should -Be $true
    }

    It "contains Matching/IPW section" {
        ($content -match '(?i)matching|IPW') | Should -Be $true
    }

    It "contains Strategy Selection Guide section" {
        ($content -match '(?i)strategy selection') | Should -Be $true
    }

    It "references @cr-identification-audit" {
        ($content -match '@cr-identification-audit') | Should -Be $true
    }

    It "contains anti-patterns table" {
        ($content -match '(?i)## .*anti-pattern|Anti-Patterns') | Should -Be $true
    }
}

Describe "cr-skill-theory-data-dialogue/SKILL.md - content" {
    $path    = Join-Path $skillsDir "cr-skill-theory-data-dialogue\SKILL.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "contains Theory-Data Dialogue Pattern section" {
        ($content -match '(?i)theory.data dialogue') | Should -Be $true
    }

    It "contains Distributional Tests section" {
        ($content -match '(?i)distributional tests') | Should -Be $true
    }

    It "contains Reduced-Form Regressions section" {
        ($content -match '(?i)reduced.form') | Should -Be $true
    }

    It "references .cg-docs/research/specifications/" {
        ($content -match '\.cg-docs[/\\]research[/\\]specifications') | Should -Be $true
    }

    It "contains anti-patterns table" {
        ($content -match '(?i)## .*anti-pattern|Anti-Patterns') | Should -Be $true
    }
}

Describe "cr-skill-research-eda/SKILL.md - content" {
    $path    = Join-Path $skillsDir "cr-skill-research-eda\SKILL.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "contains Research-Framed EDA Philosophy section" {
        ($content -match '(?i)research.framed eda') | Should -Be $true
    }

    It "contains Targeted Distributional Checks section" {
        ($content -match '(?im)^##.*distributional check') | Should -Be $true
    }

    It "contains Conditional Moment Plots section" {
        ($content -match '(?im)^##.*conditional moment') | Should -Be $true
    }

    It "contains weighted descriptive statistics using collapse" {
        # Match fmean/fsd/fmedian with w= argument in code (distinct from frontmatter description)
        ($content -match '(?i)fmean\([^)]+w\s*=|fsd\([^)]+w\s*=|fmedian\([^)]+w\s*=') | Should -Be $true
    }

    It "contains Missingness Patterns section" {
        ($content -match '(?i)missingness') | Should -Be $true
    }

    It "contains Outlier Analysis section" {
        ($content -match '(?im)^##.*outlier analysis') | Should -Be $true
    }

    It "contains Sample Restriction Documentation section" {
        ($content -match '(?i)sample restriction') | Should -Be $true
    }

    It "contains Subgroup Analysis section" {
        ($content -match '(?im)^##.*subgroup analysis') | Should -Be $true
    }

    It "contains anti-patterns table" {
        ($content -match '(?i)## .*anti-pattern|Anti-Patterns') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase 4 — instruction files existence and frontmatter
# ---------------------------------------------------------------------------

Describe "Phase 4 instruction files - existence and frontmatter" {
    $instructionsDir = Join-Path $repoRoot ".github\instructions"

    Context "latex.instructions.md" {
        $path = Join-Path $instructionsDir "latex.instructions.md"

        It "exists" {
            Test-Path $path | Should -Be $true
        }

        It "has module: research in frontmatter" {
            $fm = Get-Frontmatter -FilePath $path
            ($fm -match '(?m)^\s*module:\s*[''"]?research[''"]?\s*$') | Should -Be $true
        }

        It "applyTo includes .tex files" {
            $fm = Get-Frontmatter -FilePath $path
            ($fm -match '\.tex') | Should -Be $true
        }

        It "references cr-skill-mathematical-derivation" {
            $content = Get-Content $path -Raw -Encoding UTF8
            ($content -match 'cr-skill-mathematical-derivation') | Should -Be $true
        }
    }

    Context "math.instructions.md" {
        $path    = Join-Path $instructionsDir "math.instructions.md"
        $fm      = Get-Frontmatter -FilePath $path
        $content = Get-Content $path -Raw -Encoding UTF8

        It "exists" {
            Test-Path $path | Should -Be $true
        }

        It "has module: research in frontmatter" {
            ($fm -match '(?m)^\s*module:\s*[''"]?research[''"]?\s*$') | Should -Be $true
        }

        It "references cr-skill-mathematical-derivation" {
            ($content -match 'cr-skill-mathematical-derivation') | Should -Be $true
        }

        It "references cr-skill-symbolic-verification" {
            ($content -match 'cr-skill-symbolic-verification') | Should -Be $true
        }

        It "contains path-based glob risk note" {
            ($content -match '(?i)risk note|path.based|applyTo') | Should -Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# Phase 4 — agent skill-load assertions
# ---------------------------------------------------------------------------

Describe "Phase 4 agent skill-load assertions" {
    $agentsDir   = Join-Path $repoRoot ".github\agents"
    $mathVerify  = Get-Content (Join-Path $agentsDir "cr-mathematical-verification.agent.md") -Raw -Encoding UTF8

    It "cr-mathematical-verification loads cr-skill-symbolic-verification" {
        ($mathVerify -match '(?is)load.*cr-skill-symbolic-verification') | Should -Be $true
    }

    It "cr-mathematical-verification loads cr-skill-mathematical-derivation" {
        ($mathVerify -match '(?is)load.*cr-skill-mathematical-derivation') | Should -Be $true
    }

    It "cr-identification-audit loads cr-skill-identification-strategies" {
        $content = Get-Content (Join-Path $agentsDir "cr-identification-audit.agent.md") -Raw -Encoding UTF8
        ($content -match '(?is)load.*cr-skill-identification-strategies') | Should -Be $true
    }

    $erContent = Get-Content (Join-Path $agentsDir "cr-econometric-reasoning.agent.md") -Raw -Encoding UTF8

    It "cr-econometric-reasoning loads cr-skill-structural-econometrics" {
        ($erContent -match '(?is)load.*cr-skill-structural-econometrics') | Should -Be $true
    }

    It "cr-econometric-reasoning loads cr-skill-research-workflow" {
        ($erContent -match '(?is)load.*cr-skill-research-workflow') | Should -Be $true
    }

    It "cr-econometric-reasoning contains P0 deferral policy" {
        ($erContent -match '(?i)P0 deferral policy|do not defer P0') | Should -Be $true
    }

    It "cr-mathematical-verification loads cr-skill-research-workflow" {
        ($mathVerify -match '(?is)load.*cr-skill-research-workflow') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase 4 — prompt cleanup assertions (stale name removal + phase relabeling)
# ---------------------------------------------------------------------------

Describe "Phase 4 prompt cleanup - cr-brainstorm" {
    $path    = Join-Path $promptsDir "cr-brainstorm.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "does NOT contain stale cr-skill-specification-analysis reference" {
        ($content -match 'cr-skill-specification-analysis') | Should -Be $false
    }

    It "does NOT contain 'Phase 4, not yet available' annotation" {
        ($content -match 'Phase 4, not yet available') | Should -Be $false
    }

    It "references cr-skill-structural-econometrics as live skill" {
        # Must reference it WITHOUT 'not yet available' annotation
        $lines = ($content -split "`n") | Where-Object { $_ -match 'cr-skill-structural-econometrics' }
        $lines | ForEach-Object {
            ($_ -match 'not yet available') | Should -Be $false
        }
        ($content -match 'cr-skill-structural-econometrics') | Should -Be $true
    }

    It "references cr-skill-theory-data-dialogue" {
        ($content -match 'cr-skill-theory-data-dialogue') | Should -Be $true
    }

    It "references cr-skill-research-eda" {
        ($content -match 'cr-skill-research-eda') | Should -Be $true
    }
}

Describe "Phase 4 prompt cleanup - cr-review" {
    $path    = Join-Path $promptsDir "cr-review.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "@cr-specification-analysis is labeled Phase 5 (not Phase 4)" {
        # Must NOT match Phase 4 annotation next to cr-specification-analysis
        ($content -match 'cr-specification-analysis.*Phase 4') | Should -Be $false
        # Must match Phase 5 annotation
        ($content -match 'cr-specification-analysis.*Phase 5') | Should -Be $true
    }
}
