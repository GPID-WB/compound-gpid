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

            It "[$name] references context-loading.contract.md in Step 0" {
                $content = if (Test-Path $path) { Get-Content $path -Raw -Encoding UTF8 } else { '' }
                ($content -match 'context-loading\.contract\.md') | Should -Be $true
            }
        }
    }
}

# ---------------------------------------------------------------------------
# Shared instruction frontmatter — module: shared
# ---------------------------------------------------------------------------

Describe "Shared instruction files - module frontmatter" {
    $sharedInstructions = @(
        '.github\\instructions\\r.instructions.md',
        '.github\\instructions\\python.instructions.md',
        '.github\\instructions\\stata.instructions.md'
    )

    foreach ($relPath in $sharedInstructions) {
        $path = Join-Path $repoRoot $relPath
        $fm = if (Test-Path $path) { Get-Frontmatter -FilePath $path } else { '' }

        It "$relPath has module: shared in frontmatter" {
            ($fm -match '(?m)^\s*module:\s*shared\s*$') | Should -Be $true
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

    It "lists Measurement/Classification as a task type" {
        ($content -match 'Measurement/Classification') | Should -Be $true
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
        It "references cr-skill-evidence-provenance" {
            ($content -match 'cr-skill-evidence-provenance') | Should -Be $true
        }

    It "includes derivation cross-reference check" {
        ($content -match '(?i)derivation') | Should -Be $true
    }
    It "contains evidence/provenance enforcement language" {
        ($content -match '(?i)evidence|provenance|claim-evidence-matrix|provenance-ledger') | Should -Be $true
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

    It "references @cg-architecture" {
        ($content -match '@cg-architecture') | Should -Be $true
    }

    It "references @cr-research-integrity" {
        ($content -match '@cr-research-integrity') | Should -Be $true
    }

    It "references @cr-mathematical-verification" {
        ($content -match '@cr-mathematical-verification') | Should -Be $true
    }
    It "references @cr-provenance-audit" {
        ($content -match '@cr-provenance-audit') | Should -Be $true
    }

    It "references @cr-identification-audit" {
        ($content -match '@cr-identification-audit') | Should -Be $true
    }

    It "aligns shared dispatch step with review-routing contract language" {
        ($content -match 'review-routing\.contract\.md') | Should -Be $true
        ($content -match '(?i)aligned with the canonical shared routing contract') | Should -Be $true
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

    It "solution frontmatter enum includes Measurement/Classification and Research Scoping" {
        ($content -match 'task-type:.*Measurement/Classification') | Should -Be $true
        ($content -match 'task-type:.*Research Scoping') | Should -Be $true
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

    It "contains all 10 task types" {
        ($content -match 'Theory/Modeling') | Should -Be $true
        ($content -match 'Specification Analysis') | Should -Be $true
        ($content -match '\bEDA\b') | Should -Be $true
        ($content -match '\bImplementation\b') | Should -Be $true
        ($content -match 'ML/Prediction') | Should -Be $true
        ($content -match '\bWriting\b') | Should -Be $true
        ($content -match 'Tables/Figures') | Should -Be $true
        ($content -match '\bReproducibility\b') | Should -Be $true
        ($content -match 'Measurement/Classification') | Should -Be $true
        ($content -match 'Research Scoping') | Should -Be $true
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

    It "contains Error Class 11: Fabricated or Unverifiable Citation" {
        ($content -match '(?i)fabricated|unverifiable citation') | Should -Be $true
    }

    It "contains Error Class 12: Uncited Substantive Claim" {
        ($content -match '(?i)uncited substantive claim') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cr-skill-evidence-provenance — content validation
# ---------------------------------------------------------------------------

Describe "cr-skill-evidence-provenance/SKILL.md - content" {
    $path    = Join-Path $skillsDir "cr-skill-evidence-provenance\SKILL.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "exists" {
        Test-Path $path | Should -Be $true
    }

    It "has module: research" {
        $fm = Get-Frontmatter -FilePath $path
        ($fm -match '(?m)^\s*module:\s*[''\"]?research[''\"]?\s*$') | Should -Be $true
    }

    It "contains provenance-ledger schema path" {
        ($content -match 'provenance-ledger\.yaml') | Should -Be $true
    }

    It "contains claim-evidence matrix schema path" {
        ($content -match 'claim-evidence-matrix\.yaml') | Should -Be $true
    }

    It "contains repo-local corpus default" {
        ($content -match '(?i)repo-local corpus') | Should -Be $true
    }

    It "contains anti-hallucination language" {
        ($content -match '(?i)never fabricate|anti-hallucination') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cr-skill-measurement — content validation
# ---------------------------------------------------------------------------

Describe "cr-skill-measurement/SKILL.md - content" {
    $path    = Join-Path $skillsDir "cr-skill-measurement\SKILL.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "exists" {
        Test-Path $path | Should -Be $true
    }

    It "has module: research" {
        $fm = Get-Frontmatter -FilePath $path
        ($fm -match '(?m)^\s*module:\s*[''\"]?research[''\"]?\s*$') | Should -Be $true
    }

    It "cites OECD/JRC and Alkire-Foster" {
        ($content -match 'OECD/JRC') | Should -Be $true
        ($content -match 'Alkire-Foster') | Should -Be $true
    }

    It "includes cluster validity named sources" {
        ($content -match 'Rousseeuw|Tibshirani|Hennig') | Should -Be $true
    }

    It "contains weighting and cluster artifact paths" {
        ($content -match 'weighting-sensitivity\.yaml') | Should -Be $true
        ($content -match 'cluster-validity\.yaml') | Should -Be $true
    }

    It "contains comparability and thresholding sections" {
        ($content -match '(?i)comparability') | Should -Be $true
        ($content -match '(?i)threshold') | Should -Be $true
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
        'cr-measurement-integrity.agent.md',
        'cr-provenance-audit.agent.md',
        'cr-mathematical-verification.agent.md',
        'cr-identification-audit.agent.md',
        'cr-econometric-reasoning.agent.md',
        'cr-ml-methodology.agent.md',
        'cr-specification-analysis.agent.md',
        'cr-academic-writing.agent.md',
        'cr-replication-package.agent.md',
        'cr-publication-output.agent.md'
    )

    $agentsDir = Join-Path $repoRoot ".github\agents"

    foreach ($name in $crAgents) {
        $path = Join-Path $agentsDir $name

        Context "$name - existence and frontmatter" {
            $fm = if (Test-Path $path) { Get-Frontmatter -FilePath $path } else { '' }

            It "[$name] exists" {
                Test-Path $path | Should -Be $true
            }

            It "[$name] has a description: field in frontmatter" {
                ($fm -match 'description:') | Should -Be $true
            }

            It "[$name] has module: research" {
                ($fm -match '(?m)^\s*module:\s*[''"]?research[''"]?\s*$') | Should -Be $true
            }

            It "[$name] has tools including 'read'" {
                $tools = Get-ToolsList -Frontmatter $fm
                ($tools -contains 'read') | Should -Be $true
            }

            It "[$name] does not have 'write' tool" {
                $tools = Get-ToolsList -Frontmatter $fm
                ($tools -contains 'write') | Should -Be $false
            }

            It "[$name] has user-invocable: false" {
                ($fm -match '(?m)^\s*user-invocable:\s*false') | Should -Be $true
            }

            It "[$name] has model: GPT-5.4" {
                ($fm -match '(?m)^\s*model:\s*GPT-5\.4\s*$') | Should -Be $true
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

    It "contains normative-choice smuggling check" {
        ($content -match '(?i)normative-choice smuggling') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cr-provenance-audit.agent.md — content
# ---------------------------------------------------------------------------

Describe "cr-provenance-audit.agent.md - content" {
    $path    = Join-Path (Join-Path $repoRoot ".github\agents") "cr-provenance-audit.agent.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "references provenance ledger" {
        ($content -match 'provenance') | Should -Be $true
    }

    It "references claim-evidence linkage" {
        ($content -match '(?i)claim.*evidence') | Should -Be $true
    }

    It "states audit-only responsibilities" {
        ($content -match '(?i)audit-only|do not compute') | Should -Be $true
    }

    It "contains P0 output format tag" {
        ($content -match '\[cr-provenance-audit\]') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cr-measurement-integrity.agent.md — content
# ---------------------------------------------------------------------------

Describe "cr-measurement-integrity.agent.md - content" {
    $path    = Join-Path (Join-Path $repoRoot ".github\agents") "cr-measurement-integrity.agent.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "references measurement and comparability artifacts" {
        ($content -match 'weighting-sensitivity\.yaml') | Should -Be $true
        ($content -match 'cluster-validity\.yaml') | Should -Be $true
        ($content -match 'vintage-manifest\.yaml') | Should -Be $true
    }

    It "states audit-only responsibilities" {
        ($content -match '(?i)audit-only|do not recompute|Do not recompute') | Should -Be $true
    }

    It "contains P0/P1 parseable output tag" {
        ($content -match '\[cr-measurement-integrity\]') | Should -Be $true
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

    It "uses GPT-5.4 model" {
        $fm = Get-Frontmatter -FilePath $path
        ($fm -match 'GPT-5\.4') | Should -Be $true
    }

    It "contains graceful skip message for no derivation files" {
        ($content -match 'No derivation files found') | Should -Be $true
    }

    It "contains 20-file pagination limit" {
        ($content -match '(?i)more than 20.*derivation|File count limit') | Should -Be $true
    }

    It "contains 50 KB circuit-breaker for oversized files" {
        ($content -match '50 KB') | Should -Be $true
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

    It "uses GPT-5.4 model" {
        $fm = Get-Frontmatter -FilePath $path
        ($fm -match 'GPT-5\.4') | Should -Be $true
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

    It "does NOT contain Phase 5 annotation on @cr-specification-analysis" {
        # Phase 5 is now live — annotation must be removed
        ($content -match 'cr-specification-analysis.*Phase 5') | Should -Be $false
    }

    It "does NOT contain Phase 5 annotation on @cr-ml-methodology" {
        # Phase 5 is now live — annotation must be removed
        ($content -match 'cr-ml-methodology.*Phase 5') | Should -Be $false
    }

    It "contains availability guard message" {
        ($content -match '(?i)not available.*skip') | Should -Be $true
    }

    It "@cr-identification-audit appears in Theory/Modeling dispatch row" {
        ($content -match 'Theory/Modeling.*cr-identification-audit') | Should -Be $true
    }

    It "does NOT contain Phase 6 annotation for @cr-academic-writing (agent now live)" {
        # Phase 6 is now live — annotation must be removed
        ($content -match 'cr-academic-writing.*Phase 6') | Should -Be $false
    }

    It "does NOT contain Phase 7 annotation for @cr-replication-package (agent now live)" {
        # Phase 7 is now live — annotation must be removed
        ($content -match 'cr-replication-package.*Phase 7') | Should -Be $false
    }

    It "Step 7 Handoff routes to /cg-fix-triage (not /cr-fix-triage)" {
        ($content -match 'Step 7') | Should -Be $true
        ($content -match '`/cg-fix-triage`') | Should -Be $true
        ($content -notmatch '`/cr-fix-triage`') | Should -Be $true
    }

    It "Step 5 writes a findings status map for /cg-fix-triage compatibility" {
        ($content -match 'findings:\s*\r?\n\s+P1\.1:\s+open') | Should -Be $true
        ($content -match 'Valid\s+statuses\s+are\s+`open`,\s+`fixed`,\s+and\s+`skipped`') | Should -Be $true
        ($content -notmatch 'status:\s+open\s*\r?\nfindings:\s+N') | Should -Be $true
    }

    It "Step 5 handoff example uses bare finding IDs" {
        ($content -match '/cg-fix-triage P0\.1') | Should -Be $true
        ($content -notmatch '/cg-fix-triage \[P0\.1\]') | Should -Be $true
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

    It "frontmatter enum includes Research Scoping" {
        ($content -match 'task-type:.*Research Scoping') | Should -Be $true
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
        ($content -match '(?i)modules.*research') | Should -Be $true
    }

    It "warns that research module is not enabled" {
        ($content -match '(?i)not enabled') | Should -Be $true
    }

    It "offers /cg-setup to enable the module" {
        ($content -match '(?i)\/cg-setup') | Should -Be $true
    }

    It "offers proceed anyway fallback" {
        ($content -match '(?i)proceed anyway') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P3.5 — CR files must declare module: research in frontmatter
# ---------------------------------------------------------------------------

Describe "CR files - module: research frontmatter" {
    $crPrompts = @('cr-brainstorm', 'cr-plan', 'cr-work', 'cr-review', 'cr-compound')
    foreach ($name in $crPrompts) {
        $promptFile = Join-Path $promptsDir "$name.prompt.md"
        $fm         = if (Test-Path $promptFile) { Get-Frontmatter -FilePath $promptFile } else { "" }

        It "$name.prompt.md has module: research in frontmatter" {
            ($fm -match 'module:\s*research') | Should -Be $true
        }
    }

    $crSkills = @('cr-skill-research-workflow', 'cr-skill-research-integrity')
    foreach ($skill in $crSkills) {
        $skillFile = Join-Path $repoRoot ".github\skills\$skill\SKILL.md"
        $fm        = if (Test-Path $skillFile) { Get-Frontmatter -FilePath $skillFile } else { "" }

        It "$skill/SKILL.md has module: research in frontmatter" {
            ($fm -match 'module:\s*research') | Should -Be $true
        }
    }

    $crAgents = @('cr-research-integrity', 'cr-measurement-integrity', 'cr-provenance-audit', 'cr-mathematical-verification', 'cr-identification-audit', 'cr-econometric-reasoning', 'cr-ml-methodology', 'cr-specification-analysis', 'cr-academic-writing', 'cr-replication-package', 'cr-publication-output')
    foreach ($agent in $crAgents) {
        $agentFile = Join-Path $repoRoot ".github\agents\$agent.agent.md"
        $fm        = if (Test-Path $agentFile) { Get-Frontmatter -FilePath $agentFile } else { "" }

        It "$agent.agent.md has module: research in frontmatter" {
            ($fm -match 'module:\s*research') | Should -Be $true
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
        ($content -match '(?i)simulation.based estimation') | Should -Be $true
    }

    It "contains MSM estimation references" {
        ($content -match '\bMSM\b') | Should -Be $true
    }

    It "contains SMM estimation references" {
        ($content -match '\bSMM\b') | Should -Be $true
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
        ($content -match '(?i)anti-pattern') | Should -Be $true
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
        ($content -match '(?i)anti-pattern') | Should -Be $true
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
        ($content -match '(?i)anti-pattern') | Should -Be $true
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
        ($content -match '(?i)anti-pattern') | Should -Be $true
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
        ($content -match '(?i)anti-pattern') | Should -Be $true
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
        ($content -match '(?i)anti-pattern') | Should -Be $true
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
# Phase 5 skill and agents — existence, frontmatter, and content
# ---------------------------------------------------------------------------

Describe "Phase 5 skill - cr-skill-ml-economics" {
    $path    = Join-Path $skillsDir "cr-skill-ml-economics\SKILL.md"
    $content = Get-Content $path -Raw -Encoding UTF8
    $fm      = Get-Frontmatter -FilePath $path

    It "exists" {
        Test-Path $path | Should -Be $true
    }

    It "has module: research" {
        ($fm -match '(?m)^\s*module:\s*[''"]?research[''"]?\s*$') | Should -Be $true
    }

    It "has name: cr-skill-ml-economics" {
        ($fm -match 'name:\s*cr-skill-ml-economics') | Should -Be $true
    }

    It "has a description: field" {
        ($fm -match 'description:') | Should -Be $true
    }

    It "contains LASSO/penalized regression section" {
        ($content -match '(?i)LASSO|penalized regression') | Should -Be $true
    }

    It "contains tree-based methods section" {
        ($content -match '(?i)tree.based|random forest') | Should -Be $true
    }

    It "contains cross-validation section" {
        ($content -match '(?i)cross.validation') | Should -Be $true
    }

    It "contains panel-aware CV guidance (GroupKFold)" {
        ($content -match 'GroupKFold') | Should -Be $true
    }

    It "contains post-selection inference / double ML section" {
        ($content -match '(?i)double ML|debiased|post.selection inference') | Should -Be $true
    }

    It "references DoubleML package" {
        ($content -match 'DoubleML') | Should -Be $true
    }

    It "contains out-of-sample assessment section" {
        ($content -match '(?i)out.of.sample') | Should -Be $true
    }

    It "contains Diebold-Mariano test reference" {
        ($content -match '(?i)Diebold.Mariano') | Should -Be $true
    }

    It "contains reproducibility / seed table section" {
        ($content -match '(?i)seed') | Should -Be $true
    }

    It "contains anti-patterns catalog" {
        ($content -match '(?i)anti.pattern') | Should -Be $true
    }
}

Describe "cr-ml-methodology.agent.md - content" {
    $path    = Join-Path (Join-Path $repoRoot ".github\agents") "cr-ml-methodology.agent.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "contains Check 1: Data Leakage (P0)" {
        ($content -match '(?i)data leakage') | Should -Be $true
    }

    It "contains Check 2: Train/Test/Validation Split (P1)" {
        ($content -match '(?i)train.*test.*split|train.*test.*validation') | Should -Be $true
    }

    It "contains Check 3: CV Correctness (P1)" {
        ($content -match '(?i)cross.validation correctness|CV Correctness') | Should -Be $true
    }

    It "contains Check 4: Hyperparameter Search Transparency (P1)" {
        ($content -match '(?i)hyperparameter search') | Should -Be $true
    }

    It "Check 5: Seed Coverage emits cross-reference note to cr-research-integrity Check 1" {
        ($content -match '(?i)cross.reference.*cr-research-integrity.*Check 1') | Should -Be $true
    }

    It "Check 5: Seed Coverage preserves ML-specific detail via supplementary context note" {
        ($content -match '(?i)supplementary context') | Should -Be $true
    }

    It "contains Check 6: Economic Interpretation Quality (P2)" {
        ($content -match '(?i)economic interpretation') | Should -Be $true
    }

    It "contains Check 7: Out-of-Sample Assessment (P1)" {
        ($content -match '(?i)out.of.sample assessment') | Should -Be $true
    }

    It "loads cr-skill-ml-economics" {
        ($content -match 'cr-skill-ml-economics') | Should -Be $true
    }

    It "loads cr-skill-identification-strategies" {
        ($content -match 'cr-skill-identification-strategies') | Should -Be $true
    }

    It "loads cr-skill-research-workflow" {
        ($content -match 'cr-skill-research-workflow') | Should -Be $true
    }

    It "loads cr-skill-research-integrity" {
        ($content -match 'cr-skill-research-integrity') | Should -Be $true
    }

    It "contains untrusted-content safety note with 'execute or relay'" {
        ($content -match '(?i)execute or relay') | Should -Be $true
    }

    It "output format includes [cr-ml-methodology] tag" {
        ($content -match '\[cr-ml-methodology\]') | Should -Be $true
    }

    It "contains empty-file guard at protocol start" {
        ($content -match '(?i)zero-byte|empty.*ML methodology review skipped') | Should -Be $true
    }
}

Describe "cr-specification-analysis.agent.md - content" {
    $path    = Join-Path (Join-Path $repoRoot ".github\agents") "cr-specification-analysis.agent.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "contains Check 1: Specification Search Detection (P0)" {
        ($content -match '(?i)specification search detection') | Should -Be $true
    }

    It "Check 1 emits cross-reference to @cr-research-integrity Check 3" {
        ($content -match '(?i)cross.reference.*cr-research-integrity|cr-research-integrity.*Check 3') | Should -Be $true
    }

    It "contains Check 2: Theory-Data Dialogue Documentation (P1)" {
        ($content -match '(?i)theory.data dialogue documentation') | Should -Be $true
    }

    It "references .cg-docs/research/specifications/" {
        ($content -match '\.cg-docs[/\\]research[/\\]specifications') | Should -Be $true
    }

    It "contains Check 3: Distributional Assumption Tests (P1)" {
        ($content -match '(?i)distributional assumption tests') | Should -Be $true
    }

    It "contains Check 4: Conditional Moment Checks (P2)" {
        ($content -match '(?i)conditional moment checks') | Should -Be $true
    }

    It "contains Check 5: Sample Restriction Documentation (P2)" {
        ($content -match '(?i)sample restriction documentation') | Should -Be $true
    }

    It "contains Check 6: Robustness Specification Coverage (P2)" {
        ($content -match '(?i)robustness specification coverage') | Should -Be $true
    }

    It "loads cr-skill-theory-data-dialogue" {
        ($content -match 'cr-skill-theory-data-dialogue') | Should -Be $true
    }

    It "loads cr-skill-research-eda" {
        ($content -match 'cr-skill-research-eda') | Should -Be $true
    }

    It "loads cr-skill-research-workflow" {
        ($content -match 'cr-skill-research-workflow') | Should -Be $true
    }

    It "loads cr-skill-research-integrity" {
        ($content -match 'cr-skill-research-integrity') | Should -Be $true
    }

    It "contains untrusted-content safety note with 'execute or relay'" {
        ($content -match '(?i)execute or relay') | Should -Be $true
    }

    It "output format includes [cr-specification-analysis] tag" {
        ($content -match '\[cr-specification-analysis\]') | Should -Be $true
    }

    It "contains empty-file guard at protocol start" {
        ($content -match '(?i)zero-byte|empty.*specification analysis skipped') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase 5 prompt cleanup — negative annotation tests
# ---------------------------------------------------------------------------

Describe "Phase 5 prompt cleanup - cr-brainstorm" {
    $path    = Join-Path $promptsDir "cr-brainstorm.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "does NOT contain 'Phase 5, not yet available' annotation on ML/Prediction" {
        ($content -match '(?i)phase\s*5.*not yet available') | Should -Be $false
    }

    It "references cr-skill-ml-economics (not stale cr-skill-ml-methodology)" {
        ($content -match 'cr-skill-ml-economics') | Should -Be $true
        ($content -match 'cr-skill-ml-methodology') | Should -Be $false
    }
}

Describe "Phase 5 prompt cleanup - cr-review @cr-eda-reviewer relabeling" {
    $path    = Join-Path $promptsDir "cr-review.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "@cr-eda-reviewer is labeled 'future phase' (not 'Phase 5')" {
        # After Phase 5 completion, the EDA agent placeholder must not say Phase 5
        ($content -match 'cr-eda-reviewer.*Phase 5') | Should -Be $false
        ($content -match 'cr-eda-reviewer.*future phase') | Should -Be $true
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

    It "@cr-specification-analysis is NOT labeled Phase 4 or Phase 5 (both are now live)" {
        # Phase 5 is live — neither Phase 4 nor Phase 5 annotation should remain
        ($content -match 'cr-specification-analysis.*Phase 4') | Should -Be $false
        ($content -match 'cr-specification-analysis.*Phase 5') | Should -Be $false
    }
}

# ---------------------------------------------------------------------------
# Phase 5 agent skill-load assertions
# ---------------------------------------------------------------------------

Describe "Phase 5 agent skill-load assertions" {
    $agentsDir = Join-Path $repoRoot ".github\agents"

    $mlContent   = Get-Content (Join-Path $agentsDir "cr-ml-methodology.agent.md")       -Raw -Encoding UTF8
    $specContent = Get-Content (Join-Path $agentsDir "cr-specification-analysis.agent.md") -Raw -Encoding UTF8

    It "cr-ml-methodology loads cr-skill-ml-economics" {
        ($mlContent -match '(?is)load.*cr-skill-ml-economics') | Should -Be $true
    }

    It "cr-ml-methodology loads cr-skill-research-workflow" {
        ($mlContent -match '(?is)load.*cr-skill-research-workflow') | Should -Be $true
    }

    It "cr-ml-methodology loads cr-skill-research-integrity" {
        ($mlContent -match '(?is)load.*cr-skill-research-integrity') | Should -Be $true
    }

    It "cr-ml-methodology loads cr-skill-identification-strategies" {
        ($mlContent -match '(?is)load.*cr-skill-identification-strategies') | Should -Be $true
    }

    It "cr-specification-analysis loads cr-skill-theory-data-dialogue" {
        ($specContent -match '(?is)load.*cr-skill-theory-data-dialogue') | Should -Be $true
    }

    It "cr-specification-analysis loads cr-skill-research-eda" {
        ($specContent -match '(?is)load.*cr-skill-research-eda') | Should -Be $true
    }

    It "cr-specification-analysis loads cr-skill-research-workflow" {
        ($specContent -match '(?is)load.*cr-skill-research-workflow') | Should -Be $true
    }

    It "cr-specification-analysis loads cr-skill-research-integrity" {
        ($specContent -match '(?is)load.*cr-skill-research-integrity') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase 5 dispatch journey tests
# ---------------------------------------------------------------------------

Describe "cr-review.prompt.md - Phase 5 dispatch journey" {
    $path    = Join-Path $promptsDir "cr-review.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "ML/Prediction dispatch row routes to @cr-ml-methodology" {
        ($content -match 'ML/Prediction.*cr-ml-methodology') | Should -Be $true
    }

    It "ML/Prediction dispatch row also routes to @cr-specification-analysis" {
        ($content -match 'ML/Prediction.*cr-specification-analysis') | Should -Be $true
    }

    It "Specification Analysis dispatch row routes to @cr-specification-analysis" {
        ($content -match 'Specification Analysis.*cr-specification-analysis') | Should -Be $true
    }

    It "Implementation dispatch row routes to @cr-ml-methodology" {
        ($content -match 'Implementation.*cr-ml-methodology') | Should -Be $true
    }

    It "Implementation dispatch row routes to @cr-specification-analysis" {
        ($content -match 'Implementation.*cr-specification-analysis') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase 5 - Brain and active-state integration
# ---------------------------------------------------------------------------

Describe "Phase 5 integration - Consult Brain and active-state contract" {
    $reviewPath = Join-Path $promptsDir "cr-review.prompt.md"
    $workPath   = Join-Path $promptsDir "cr-work.prompt.md"
    $reviewContent = Get-Content $reviewPath -Raw -Encoding UTF8
    $workContent   = Get-Content $workPath -Raw -Encoding UTF8

    It "cr-review includes a Consult Brain step using cg-skill-brain-query" {
        ($reviewContent -match '(?i)consult brain') | Should -Be $true
        ($reviewContent -match 'cg-skill-brain-query') | Should -Be $true
    }

    It "cr-work includes a Consult Brain step using cg-skill-brain-query" {
        ($workContent -match '(?i)consult brain') | Should -Be $true
        ($workContent -match 'cg-skill-brain-query') | Should -Be $true
    }

    It "cr-work references active-state contract and current.json handoff" {
        ($workContent -match 'active-state\.contract\.md') | Should -Be $true
        ($workContent -match '\.cg-docs/active-state/current\.json') | Should -Be $true
    }

    It "cr-work links active-state updates to /cg-resume discoverability" {
        ($workContent -match '/cg-resume') | Should -Be $true
    }
}

Describe "Generated CR command frontmatter parity" {
    $generatedCommands = @(
        '.agents\commands\cr-review.md',
        '.agents\commands\cr-work.md',
        '.claude\commands\cr-review.md',
        '.claude\commands\cr-work.md',
        '.opencode\commands\cr-review.md',
        '.opencode\commands\cr-work.md'
    )

    foreach ($relPath in $generatedCommands) {
        $path = Join-Path $repoRoot $relPath
        $content = if (Test-Path $path) { Get-Content $path -Raw -Encoding UTF8 } else { '' }

        It "$relPath preserves a non-corrupted description frontmatter line" {
            Test-Path $path | Should -Be $true
            ($content -match '(?m)^description:\s*(?!"\\)') | Should -Be $true
            ($content -notmatch '(?m)^description:\s*"\\') | Should -Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# cr-skill-academic-writing - existence and content
# ---------------------------------------------------------------------------

Describe "cr-skill-academic-writing - existence and content" {
    $path    = Join-Path $skillsDir "cr-skill-academic-writing\SKILL.md"
    $content = Get-Content $path -Raw -Encoding UTF8
    $fm      = Get-Frontmatter -FilePath $path

    It "exists" {
        Test-Path $path | Should -Be $true
    }

    It "has module: research" {
        ($fm -match '(?m)^\s*module:\s*[''"]?research[''"]?\s*$') | Should -Be $true
    }

    It "has a name: field in frontmatter" {
        ($fm -match '(?m)^\s*name:\s*cr-skill-academic-writing') | Should -Be $true
    }

    It "has a description: field in frontmatter" {
        ($fm -match 'description:') | Should -Be $true
    }

    It "contains AER journal style coverage" {
        ($content -match '(?i)AER') | Should -Be $true
    }

    It "contains Econometrica journal style coverage" {
        ($content -match '(?i)Econometrica') | Should -Be $true
    }

    It "contains JPE journal style coverage" {
        ($content -match '(?i)JPE\b') | Should -Be $true
    }

    It "contains QJE journal style coverage" {
        ($content -match '(?i)QJE\b') | Should -Be $true
    }

    It "contains section structure guidance" {
        ($content -match '(?i)section structure') | Should -Be $true
    }

    It "contains Hook introduction element" {
        ($content -match '(?i)\bHook\b') | Should -Be $true
    }

    It "contains Gap introduction element" {
        ($content -match '(?i)\bGap\b') | Should -Be $true
    }

    It "contains abstract writing patterns" {
        ($content -match '(?i)abstract writing') | Should -Be $true
    }

    It "contains four-sentence abstract structure" {
        ($content -match '(?i)four.sentence') | Should -Be $true
    }

    It "contains equation exposition guidance" {
        ($content -match '(?i)equation exposition') | Should -Be $true
    }

    It "contains notation discipline guidance" {
        ($content -match '(?i)notation.*discipline') | Should -Be $true
    }

    It "contains citation style guidance" {
        ($content -match '(?i)citation style') | Should -Be $true
    }

    It "contains author-year citation format" {
        ($content -match '(?i)author.year') | Should -Be $true
    }

    It "contains response-to-referee guidance" {
        ($content -match '(?i)response.to.referee') | Should -Be $true
    }

    It "contains point-by-point referee response" {
        ($content -match '(?i)point.by.point') | Should -Be $true
    }

    It "contains anti-patterns section" {
        ($content -match '(?i)anti.pattern') | Should -Be $true
    }

    It "has substantive content (> 500 words)" {
        ($content -split '\s+').Count | Should -BeGreaterThan 500
    }
}

# ---------------------------------------------------------------------------
# cr-skill-publication-output - existence and content
# ---------------------------------------------------------------------------

Describe "cr-skill-publication-output - existence and content" {
    $path     = Join-Path $skillsDir "cr-skill-publication-output\SKILL.md"
    $content  = Get-Content $path -Raw -Encoding UTF8
    $fm       = Get-Frontmatter -FilePath $path
    # Pre-compute section text once at Describe scope (avoids re-scanning in each It)
    $sec5Text = [regex]::Match($content, '(?si)## 5\..*?(?=## 6\.)').Value
    $sec6Text = [regex]::Match($content, '(?si)## 6\..*?(?=## 7\.|$)').Value

    It "exists" {
        Test-Path $path | Should -Be $true
    }

    It "has module: research" {
        ($fm -match '(?m)^\s*module:\s*[''"]?research[''"]?\s*$') | Should -Be $true
    }

    It "has a name: field in frontmatter" {
        ($fm -match '(?m)^\s*name:\s*cr-skill-publication-output') | Should -Be $true
    }

    It "has a description: field in frontmatter" {
        ($fm -match 'description:') | Should -Be $true
    }

    It "contains modelsummary regression table patterns" {
        ($content -match '(?i)modelsummary') | Should -Be $true
    }

    It "contains fixest::etable patterns" {
        ($content -match '(?i)etable|fixest') | Should -Be $true
    }

    It "contains kableExtra LaTeX table patterns" {
        ($content -match '(?i)kableExtra') | Should -Be $true
    }

    It "contains ggplot2 figure guidance" {
        ($content -match '(?i)ggplot2') | Should -Be $true
    }

    It "contains wbplot theme guidance" {
        ($content -match '(?i)wbplot') | Should -Be $true
    }

    It "contains font conventions" {
        ($content -match '(?i)font.*size') | Should -Be $true
    }

    It "contains size conventions" {
        ($content -match '(?i)size.*convention') | Should -Be $true
    }

    It "documents specific font sizes in pt" {
        ($content -match '(?i)10.?11.?pt|9.?10.?pt') | Should -Be $true
    }

    It "contains figure-caption discipline" {
        ($content -match '(?i)figure.caption discipline|caption.*self.contained') | Should -Be $true
    }

    It "contains table-note discipline" {
        ($content -match '(?i)table.note discipline') | Should -Be $true
    }

    It "documents variable definitions in table notes" {
        ($content -match '(?i)variable definition') | Should -Be $true
    }

    It "contains ggsave with explicit dimensions guidance" {
        ($content -match '(?i)ggsave') | Should -Be $true
    }

    It "ggsave() criterion appears in figure-caption section (Section 5)" {
        ($sec5Text -match 'ggsave') | Should -Be $true
    }

    It "ggsave() criterion does NOT appear in table-note section (Section 6)" {
        ($sec6Text -match 'ggsave') | Should -Be $false
    }

    It "has substantive content (> 500 words)" {
        ($content -split '\s+').Count | Should -BeGreaterThan 500
    }
}

# ---------------------------------------------------------------------------
# cr-academic-writing.agent.md - content
# ---------------------------------------------------------------------------

Describe "cr-academic-writing.agent.md - content" {
    $path    = Join-Path (Join-Path $repoRoot ".github\agents") "cr-academic-writing.agent.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "contains Check 1: Section Structure (P2)" {
        ($content -match '(?i)section structure') | Should -Be $true
    }

    It "contains Check 2: Abstract Quality (P2)" {
        ($content -match '(?i)abstract quality') | Should -Be $true
    }

    It "contains Check 3: Equation Exposition (P1)" {
        ($content -match '(?i)equation exposition') | Should -Be $true
    }

    It "contains Check 4: Notation Consistency (P1)" {
        ($content -match '(?i)notation consistency') | Should -Be $true
    }

    It "contains Check 5: Citation Completeness (P2)" {
        ($content -match '(?i)citation completeness') | Should -Be $true
    }

    It "contains Check 6: Figure and Table Presentation (P2)" {
        ($content -match '(?i)figure.*table presentation|figure.*presentation') | Should -Be $true
    }

    It "contains Check 7: Argument Flow (P2)" {
        ($content -match '(?i)argument flow') | Should -Be $true
    }

    It "Check 7 is assigned P2 (not P1)" {
        # Verify Check 7 block labels Argument Flow as P2
        ($content -match 'Argument Flow.*P2') | Should -Be $true
    }

    It "Check 1 Section Structure is labeled P2" {
        ($content -match 'Section Structure.*P2') | Should -Be $true
    }

    It "Check 2 Abstract Quality is labeled P2" {
        ($content -match 'Abstract Quality.*P2') | Should -Be $true
    }

    It "Check 3 Equation Exposition is labeled P1" {
        ($content -match 'Equation Exposition.*P1') | Should -Be $true
    }

    It "Check 4 Notation Consistency is labeled P1" {
        ($content -match 'Notation Consistency.*P1') | Should -Be $true
    }

    It "Check 5 Citation Completeness is labeled P2" {
        ($content -match 'Citation Completeness.*P2') | Should -Be $true
    }

    It "Check 6 Figure and Table Presentation is labeled P2" {
        ($content -match '(?i)figure.*table presentation.*P2|figure.*presentation.*P2') | Should -Be $true
    }

    It "loads cr-skill-academic-writing" {
        ($content -match 'cr-skill-academic-writing') | Should -Be $true
    }

    It "loads cr-skill-publication-output" {
        ($content -match 'cr-skill-publication-output') | Should -Be $true
    }

    It "loads cr-skill-research-workflow" {
        ($content -match 'cr-skill-research-workflow') | Should -Be $true
    }

    It "loads cr-skill-research-integrity" {
        ($content -match 'cr-skill-research-integrity') | Should -Be $true
    }

    It "contains untrusted-content safety note with 'execute or relay'" {
        ($content -match '(?i)execute or relay') | Should -Be $true
    }

    It "output format includes [cr-academic-writing] tag" {
        ($content -match '\[cr-academic-writing\]') | Should -Be $true
    }

    It "contains empty-file guard" {
        ($content -match '(?i)empty.*academic writing review skipped|academic writing review skipped') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase 6 dispatch journey tests
# ---------------------------------------------------------------------------

Describe "cr-review.prompt.md - Phase 6 dispatch journey" {
    $path    = Join-Path $promptsDir "cr-review.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "Writing dispatch row routes to @cr-academic-writing" {
        ($content -match 'Writing.*cr-academic-writing') | Should -Be $true
    }

    It "Tables/Figures dispatch row routes to @cg-documentation" {
        ($content -match 'Tables/Figures.*@cg-documentation') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase 6 prompt cleanup - cr-review
# ---------------------------------------------------------------------------

Describe "Phase 6 prompt cleanup - cr-review" {
    $path    = Join-Path $promptsDir "cr-review.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "does NOT contain Phase 6 annotation on @cr-academic-writing" {
        # Phase 6 is now live - annotation must be removed
        ($content -match 'cr-academic-writing.*Phase 6') | Should -Be $false
    }

    It "does NOT contain reversed Phase 6 annotation for @cr-academic-writing" {
        ($content -match 'Phase 6.*cr-academic-writing') | Should -Be $false
    }

    It "does NOT contain 'not yet available' on @cr-academic-writing" {
        ($content -match 'cr-academic-writing.*not yet available') | Should -Be $false
    }
}

# ---------------------------------------------------------------------------
# Phase 6 prompt cleanup - cr-brainstorm
# ---------------------------------------------------------------------------

Describe "Phase 6 prompt cleanup - cr-brainstorm" {
    $path    = Join-Path $promptsDir "cr-brainstorm.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "does NOT contain Phase 6 annotation on cr-skill-academic-writing" {
        # Phase 6 is now live - annotation must be removed
        ($content -match '(?i)phase\s*6.*not yet available') | Should -Be $false
    }

    It "does NOT contain reversed Phase 6 annotation for cr-skill-academic-writing" {
        ($content -match 'Phase 6.*cr-skill-academic-writing') | Should -Be $false
    }

    It "does NOT contain 'not yet available' on cr-skill-academic-writing" {
        ($content -match 'cr-skill-academic-writing.*not yet available') | Should -Be $false
    }
}

# ---------------------------------------------------------------------------
# Phase 6 skill loading cross-reference
# ---------------------------------------------------------------------------

Describe "copilot-instructions.md - Phase 6 skills registered" {
    $path    = Join-Path $repoRoot ".github\copilot-instructions.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "lists cr-skill-academic-writing in CR Skills section" {
        ($content -match 'cr-skill-academic-writing') | Should -Be $true
    }

    It "lists cr-skill-publication-output in CR Skills section" {
        ($content -match 'cr-skill-publication-output') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase 6 brainstorm cross-reference
# ---------------------------------------------------------------------------

Describe "cr-brainstorm.prompt.md - Phase 6 cross-reference" {
    $path    = Join-Path $promptsDir "cr-brainstorm.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "cr-skill-publication-output appears in Writing skill row" {
        ($content -match 'Writing.*cr-skill-publication-output') | Should -Be $true
    }

    It "cr-skill-publication-output appears in Tables/Figures skill row" {
        ($content -match 'Tables/Figures.*cr-skill-publication-output') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase 7: cr-skill-replication-standards skill
# ---------------------------------------------------------------------------

Describe "cr-skill-replication-standards - frontmatter and structure" {
    $path    = Join-Path $repoRoot ".github\skills\cr-skill-replication-standards\SKILL.md"
    $content = Get-Content $path -Raw -Encoding UTF8
    $fm      = Get-Frontmatter -FilePath $path

    It "skill file exists" {
        Test-Path $path | Should -Be $true
    }

    It "has name: cr-skill-replication-standards in frontmatter" {
        ($fm -match 'name:\s*cr-skill-replication-standards') | Should -Be $true
    }

    It "has module: research in frontmatter" {
        ($fm -match '(?m)^\s*module:\s*[''"]?research[''"]?\s*$') | Should -Be $true
    }

    It "has a description: field in frontmatter" {
        ($fm -match 'description:') | Should -Be $true
    }

    It "contains Section 1 (AEA Archive Structure)" {
        ($content -match '(?i)## 1\.\s+AEA Archive Structure') | Should -Be $true
    }

    It "contains Section 2 (README for Replication)" {
        ($content -match '(?i)## 2\.\s+README for Replication') | Should -Be $true
    }

    It "contains Section 3 (Dependency Lockfiles)" {
        ($content -match '(?i)## 3\.\s+Dependency Lockfiles') | Should -Be $true
    }

    It "contains Section 4 (Seed Management)" {
        ($content -match '(?i)## 4\.\s+Seed Management') | Should -Be $true
    }

    It "contains Section 5 (Data Documentation)" {
        ($content -match '(?i)## 5\.\s+Data Documentation') | Should -Be $true
    }

    It "contains Section 6 (Path Portability)" {
        ($content -match '(?i)## 6\.\s+Path Portability') | Should -Be $true
    }

    It "contains Section 7 (Sensitive Data Handling)" {
        ($content -match '(?i)## 7\.\s+Sensitive Data Handling') | Should -Be $true
    }

    It "contains Section 8 (Archive Packaging)" {
        ($content -match '(?i)## 8\.\s+Archive Packaging') | Should -Be $true
    }

    It "contains Section 9 (Review Criteria)" {
        ($content -match '(?i)## 9\.\s+Review Criteria') | Should -Be $true
    }

    It "mentions AEA replication standards" {
        ($content -match '(?i)AEA') | Should -Be $true
    }

    It "mentions seed registry" {
        ($content -match '(?i)seed registry') | Should -Be $true
    }

    It "mentions PII checklist" {
        ($content -match '(?i)PII') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase 7: cr-replication-package.agent.md - content
# ---------------------------------------------------------------------------

Describe "cr-replication-package.agent.md - content" {
    $path    = Join-Path (Join-Path $repoRoot ".github\agents") "cr-replication-package.agent.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "contains Check 1: Archive Structure (P1)" {
        ($content -match '(?i)archive structure') | Should -Be $true
    }

    It "contains Check 2: README Completeness (P1)" {
        ($content -match '(?i)README Completeness') | Should -Be $true
    }

    It "contains Check 3: Dependency Lockfiles (P1)" {
        ($content -match '(?i)Dependency Lockfiles') | Should -Be $true
    }

    It "contains Check 4: Seed Registry (P0)" {
        ($content -match '(?i)Seed Registry') | Should -Be $true
    }

    It "contains Check 5: Data Documentation (P1)" {
        ($content -match '(?i)Data Documentation') | Should -Be $true
    }

    It "contains Check 6: Path Portability (P1)" {
        ($content -match '(?i)Path Portability') | Should -Be $true
    }

    It "contains Check 7: Sensitive Data (P0)" {
        ($content -match '(?i)Sensitive Data') | Should -Be $true
    }

    It "contains Check 8: File Inventory (P2)" {
        ($content -match '(?i)File Inventory') | Should -Be $true
    }

    It "Check 4 Seed Registry is labeled P0" {
        ($content -match 'Seed Registry.*P0') | Should -Be $true
    }

    It "Check 7 Sensitive Data is labeled P0" {
        ($content -match 'Sensitive Data.*P0') | Should -Be $true
    }

    It "Check 5 Data Documentation includes P0 for PII in committed codebooks" {
        ($content -match '\[P0\.N\].*PII|PII.*\[P0\.N\]') | Should -Be $true
    }

    It "Check 4 detects dynamic non-literal seeds (Sys.time)" {
        ($content -match 'Sys\.time') | Should -Be $true
    }

    It "Check 4 flags seed value 0 or negative as P2" {
        ($content -match 'seed.*0.*negative|0.*negative.*seed|negative integer') | Should -Be $true
    }

    It "Check 6 forbids parent-traversal paths (../)" {
        ($content -match '\.\./') | Should -Be $true
    }

    It "Check 7 includes manual git ls-files verification advisory" {
        ($content -match 'git ls-files') | Should -Be $true
    }

    It "injection guard covers replication-package/ files including seeds.md" {
        # Guard text spans two lines: "replication-package/" and "(including `seeds.md`)"
        ($content -match 'replication-package/') | Should -Be $true
        ($content -match 'seeds\.md') | Should -Be $true
    }

    It "injection halt returns exact prescribed string" {
        ($content -match 'return exactly|Review halted') | Should -Be $true
    }

    It "loads cr-skill-replication-standards" {
        ($content -match 'cr-skill-replication-standards') | Should -Be $true
    }

    It "loads cr-skill-research-workflow" {
        ($content -match 'cr-skill-research-workflow') | Should -Be $true
    }

    It "loads cr-skill-research-integrity" {
        ($content -match 'cr-skill-research-integrity') | Should -Be $true
    }

    It "contains untrusted-content safety note with 'execute or relay'" {
        ($content -match '(?i)execute or relay') | Should -Be $true
    }

    It "contains empty-archive guard" {
        ($content -match '(?i)no replication package found|empty.*replication') | Should -Be $true
    }

    It "output format includes [cr-replication-package] tag" {
        ($content -match '\[cr-replication-package\]') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase 7 prompt cleanup - cr-review
# ---------------------------------------------------------------------------

Describe "Phase 7 prompt cleanup - cr-review" {
    $path    = Join-Path $promptsDir "cr-review.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "does NOT contain Phase 7 annotation on @cr-replication-package" {
        # Phase 7 is now live — annotation must be removed
        ($content -match 'cr-replication-package.*Phase 7') | Should -Be $false
    }

    It "does NOT contain reversed Phase 7 annotation for @cr-replication-package" {
        ($content -match 'Phase 7.*cr-replication-package') | Should -Be $false
    }

    It "does NOT contain 'not yet available' on @cr-replication-package" {
        ($content -match 'cr-replication-package.*not yet available') | Should -Be $false
    }

    It "Reproducibility dispatch row routes to @cr-replication-package" {
        ($content -match 'Reproducibility.*cr-replication-package') | Should -Be $true
    }

    It "Reproducibility dispatch row has no Phase 7 qualifier" {
        ($content -match 'Reproducibility.*Phase 7') | Should -Be $false
    }
}

# ---------------------------------------------------------------------------
# Phase 7 prompt cleanup - cr-brainstorm
# ---------------------------------------------------------------------------

Describe "Phase 7 prompt cleanup - cr-brainstorm" {
    $path    = Join-Path $promptsDir "cr-brainstorm.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "Reproducibility routes to cr-skill-replication-standards" {
        ($content -match 'Reproducibility.*cr-skill-replication-standards') | Should -Be $true
    }

    It "does NOT route Reproducibility to cg-skill-pester-safety" {
        ($content -match 'Reproducibility.*cg-skill-pester-safety') | Should -Be $false
    }

    It "does NOT route Reproducibility to cr-skill-git-workflow" {
        ($content -match 'Reproducibility.*cr-skill-git-workflow') | Should -Be $false
    }
}

# ---------------------------------------------------------------------------
# Phase 7 prompt cleanup - cr-work
# ---------------------------------------------------------------------------

Describe "Phase 7 prompt cleanup - cr-work" {
    $path    = Join-Path $promptsDir "cr-work.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "contains conditional load for Reproducibility task type" {
        ($content -match '(?i)Reproducibility.*cr-skill-replication-standards') | Should -Be $true
    }

    It "contains replication directory setup for Reproducibility tasks" {
        ($content -match '(?i)research/replication') | Should -Be $true
    }

    It "contains P0 seed check for Reproducibility tasks" {
        ($content -match '(?i)P0 check.*seed') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase 7 skill loading cross-reference
# ---------------------------------------------------------------------------

Describe "copilot-instructions.md - Phase 7 skills registered" {
    $path    = Join-Path $repoRoot ".github\copilot-instructions.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "lists cr-skill-replication-standards in CR Skills section" {
        ($content -match 'cr-skill-replication-standards') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# END Phase 7

# ---------------------------------------------------------------------------
# Phase 9: cr-publication-output.agent.md — structural checks
# ---------------------------------------------------------------------------

Describe "cr-publication-output.agent.md" {
    $path    = Join-Path (Join-Path $repoRoot ".github\agents") "cr-publication-output.agent.md"
    $content = Get-Content $path -Raw -Encoding UTF8
    $fm      = Get-Frontmatter -FilePath $path

    # --- structural / frontmatter ---
    It "agent file exists" {
        Test-Path $path | Should -Be $true
    }

    It "has module: research in frontmatter" {
        ($fm -match "(?m)^\s*module:\s*['""]?research['""]?\s*$") | Should -Be $true
    }

    It "has tools: ['read', 'search'] in frontmatter — 'search' value present" {
        ($fm -match "tools:.*'search'") | Should -Be $true
    }

    It "has user-invocable: false in frontmatter" {
        ($fm -match "(?m)^\s*user-invocable:\s*false") | Should -Be $true
    }

    It "has a description: field in frontmatter" {
        ($fm -match "description:") | Should -Be $true
    }

    # --- content ---
    It "loads cr-skill-publication-output" {
        ($content -match 'cr-skill-publication-output') | Should -Be $true
    }

    It "loads cr-skill-research-workflow" {
        ($content -match 'cr-skill-research-workflow') | Should -Be $true
    }

    It "loads cr-skill-research-integrity" {
        ($content -match 'cr-skill-research-integrity') | Should -Be $true
    }

    It "has untrusted-content note with 'execute or relay'" {
        ($content -match '(?i)execute or relay') | Should -Be $true
    }

    It "has empty-file guard" {
        ($content -match '(?si)Empty-file guard|publication output review.*skipped') | Should -Be $true
    }

    It "has size limit (50 KB)" {
        ($content -match '50 KB') | Should -Be $true
    }

    It "output format uses [cr-publication-output] tag" {
        ($content -match '\[cr-publication-output\]') | Should -Be $true
    }

    It "contains Check 1: Regression Table Standards with (P1) label" {
        ($content -match '(?i)### Check 1:.*Regression Table Standards.*\(P1\)') | Should -Be $true
    }

    It "contains Check 2: LaTeX Table Patterns with (P2) label" {
        ($content -match '(?i)### Check 2:.*LaTeX Table Patterns.*\(P2\)') | Should -Be $true
    }

    It "contains Check 3: Figure Output Compliance with (P2) label" {
        ($content -match '(?i)### Check 3:.*Figure Output Compliance.*\(P2\)') | Should -Be $true
    }

    It "contains Check 4: Font and Size Conventions with (P2) label" {
        ($content -match '(?i)### Check 4:.*Font and Size Conventions.*\(P2\)') | Should -Be $true
    }

    It "contains Check 5: Figure-Caption Discipline with (P2) label" {
        ($content -match '(?i)### Check 5:.*Figure[\s-]Caption Discipline.*\(P2\)') | Should -Be $true
    }

    It "contains Check 6: Table-Note Discipline with (P2) label" {
        ($content -match '(?i)### Check 6:.*Table[\s-]Note Discipline.*\(P2\)') | Should -Be $true
    }

    It "contains Check 7: Output File Management with (P3) label" {
        ($content -match '(?i)### Check 7:.*Output File Management.*\(P3\)') | Should -Be $true
    }

    It "contains Check 8: Deterministic Output with (P1) label" {
        ($content -match '(?i)### Check 8:.*Deterministic Output.*\(P1\)') | Should -Be $true
    }

    It "does NOT load cg-skill-r-visualization (redundant - cr-skill-publication-output covers this)" {
        ($content -match 'cg-skill-r-visualization') | Should -Be $false
    }

    It "all 'Flag as' lines use priority-first format [P<N>.<M>] [cr-publication-output]" {
        # Every "Flag as" instruction must lead with the priority tag before the agent tag
        $flagLines = ($content -split "`n") | Where-Object { $_ -match 'Flag as \*\*' }
        $badLines = $flagLines | Where-Object { $_ -notmatch 'Flag as \*\*\[P[0-3]\.\w+\]\*\*\s+\[cr-publication-output\]' }
        $badLines.Count | Should -Be 0
    }

    It "geom_jitter(seed=N) exception is documented in Check 8" {
        ($content -match '(?i)geom_jitter.*seed') | Should -Be $true
    }

    It "theme_set(theme_wb()) exception is documented in Check 3" {
        ($content -match '(?i)theme_set') | Should -Be $true
    }

    It "ggplot2:: namespace form is referenced" {
        ($content -match 'ggplot2::') | Should -Be $true
    }

    It "alias / indirect dispatch detection is documented" {
        ($content -match '(?i)alias|indirect dispatch|do\.call') | Should -Be $true
    }

    It "Unicode homograph normalization is mentioned in injection guard" {
        ($content -match '(?i)homoglyph|unicode.*lookalike|non-ascii.*homoglyph|lookalike') | Should -Be $true
    }

    It "Check 6 SE-type deduplication guard is present" {
        ($content -match '(?i)check 1.*already flag|already flag.*check 1') | Should -Be $true
    }

    It "Check 5 has LaTeX external-caption scope note" {
        ($content -match '(?i)latex.*import|import.*latex|\\\\caption|standalone.*pdf|pdf.*standalone') | Should -Be $true
    }

    It "graceful-skip for no-output-calls is documented" -Pending {
        # Behavioral integration test: run @cr-publication-output against a fixture file
        # containing only library() calls and verify it returns the skip message.
        # Requires an agent integration test harness — deferred.
        $true | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase 9 dispatch journey tests
# ---------------------------------------------------------------------------

Describe "cr-review.prompt.md - Phase 9 dispatch journey" {
    $path    = Join-Path $promptsDir "cr-review.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "Tables/Figures dispatch row routes to @cr-publication-output" {
        ($content -match 'Tables/Figures.*cr-publication-output') | Should -Be $true
    }

    It "Tables/Figures dispatch row does NOT route to @cr-academic-writing (Phase 9 routing)" {
        ($content -match 'Tables/Figures.*cr-academic-writing') | Should -Be $false
    }

    It "Writing dispatch row still routes to @cr-academic-writing (unchanged)" {
        ($content -match 'Writing.*cr-academic-writing') | Should -Be $true
    }

    It "dispatch table covers all 10 task types from research workflow taxonomy" {
        $taskTypes = @(
            'Theory/Modeling', 'Specification Analysis', 'ML/Prediction',
            'Writing', 'Reproducibility', 'Measurement/Classification', 'Tables/Figures', 'EDA', 'Implementation', 'Research Scoping'
        )
        $missingTypes = $taskTypes | Where-Object { $content -notmatch [regex]::Escape($_) }
        $missingTypes.Count | Should -Be 0
    }

    It "Measurement/Classification dispatch row routes to @cr-measurement-integrity" {
        ($content -match 'Measurement/Classification.*cr-measurement-integrity') | Should -Be $true
    }

    It "mixed-format files (.Rnw .qmd .Rmd .ipynb) dispatch both academic-writing and publication-output agents" {
        ($content -match '(?i)\.Rnw|\.qmd|\.Rmd|\.ipynb') | Should -Be $true
    }

    It "Implementation dispatch row includes @cr-publication-output" {
        ($content -match 'Implementation.*cr-publication-output') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase 9: @cr-academic-writing cleanup
# ---------------------------------------------------------------------------

Describe "cr-academic-writing.agent.md - Phase 9 cleanup" {
    $path    = Join-Path (Join-Path $repoRoot ".github\agents") "cr-academic-writing.agent.md"
    $content = Get-Content $path -Raw -Encoding UTF8
    $fm      = Get-Frontmatter -FilePath $path

    It "description does NOT mention Tables/Figures (Writing-only after Phase 9)" {
        ($fm -match 'Tables/Figures') | Should -Be $false
    }

    It "task type guard paragraph is removed" {
        ($content -match '(?i)task type guard') | Should -Be $false
    }

    It "Check 6 Figure and Table Presentation is still present (Writing still needs it)" {
        ($content -match '(?i)figure.*table presentation|figure.*presentation') | Should -Be $true
    }

    It "Check 6 'Flag as' uses [cr-publication-output] tag (Phase 9 tag change)" {
        ($content -match '\[cr-publication-output\]') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase 9: /cr-work Tables/Figures skill loading
# ---------------------------------------------------------------------------

Describe "cr-work.prompt.md - Phase 9 Tables/Figures skill loading" {
    $path    = Join-Path $promptsDir "cr-work.prompt.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "loads cr-skill-publication-output for Tables/Figures tasks" {
        ($content -match 'cr-skill-publication-output') | Should -Be $true
    }

    It "Tables/Figures skill loading is conditional on task type" {
        ($content -match 'Tables/Figures.*cr-skill-publication-output|cr-skill-publication-output.*Tables/Figures') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase 9: copilot-instructions.md updated reference
# ---------------------------------------------------------------------------

Describe "copilot-instructions.md - Phase 9 skill reference updated" {
    $path    = Join-Path $repoRoot ".github\copilot-instructions.md"
    $content = Get-Content $path -Raw -Encoding UTF8

    It "cr-skill-publication-output references @cr-publication-output" {
        ($content -match 'cr-skill-publication-output.*cr-publication-output') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# END Phase 9
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Responsible Research Lifecycle + Method Packs (2026-07-30 Phase 4)
#   Additive checks — the existing Step 3 dispatch table remains the single
#   source of routing truth and is verified verbatim by the dispatch-journey
#   Describe above. These tests assert the additive lifecycle/pack framing only.
# ---------------------------------------------------------------------------

Describe "Responsible Research Lifecycle - spine, method packs, and doc sync" {
    $workflowSkill = Get-Content (Join-Path $skillsDir "cr-skill-research-workflow\SKILL.md") -Raw -Encoding UTF8
    $reviewPrompt  = Get-Content (Join-Path $promptsDir "cr-review.prompt.md")                -Raw -Encoding UTF8
    $workPrompt    = Get-Content (Join-Path $promptsDir "cr-work.prompt.md")                  -Raw -Encoding UTF8
    $bsPrompt      = Get-Content (Join-Path $promptsDir "cr-brainstorm.prompt.md")            -Raw -Encoding UTF8
    $instructions  = Get-Content (Join-Path $repoRoot ".github\copilot-instructions.md")      -Raw -Encoding UTF8
    $reference     = Get-Content (Join-Path $repoRoot "docs\reference.md")                    -Raw -Encoding UTF8

    # Collapse whitespace and blockquote markers so the spine matches regardless
    # of markdown line wrapping or '>' continuation. The '.' between stage names
    # matches the unicode arrow; spaces are literal.
    $spine        = 'Scope . Evidence . Theory . Method . Execute . Verify . Communicate . Maintain'
    $workflowFlat = ($workflowSkill -replace '[\s>]+', ' ')
    $reviewFlat   = ($reviewPrompt  -replace '[\s>]+', ' ')
    $workFlat     = ($workPrompt    -replace '[\s>]+', ' ')
    $bsFlat       = ($bsPrompt      -replace '[\s>]+', ' ')
    $instrFlat    = ($instructions  -replace '[\s>]+', ' ')
    $refFlat      = ($reference     -replace '[\s>]+', ' ')

    # V1 — lifecycle spine in the workflow skill
    It "workflow skill has a Responsible Research Lifecycle section" {
        ($workflowSkill -match '(?i)Responsible Research Lifecycle') | Should -Be $true
    }

    It "workflow skill contains the eight-stage lifecycle spine in order" {
        ($workflowFlat -match $spine) | Should -Be $true
    }

    It "workflow skill preserves all 10 task types (no taxonomy regression)" {
        ($workflowSkill -match 'Measurement/Classification') | Should -Be $true
        ($workflowSkill -match 'Research Scoping') | Should -Be $true
    }

    # V2 — method-pack model in the workflow skill
    It "workflow skill defines a Method Packs subsection" {
        ($workflowSkill -match '(?i)Method Packs') | Should -Be $true
    }

    It "workflow skill maps the structural, ML, and measurement packs to existing files" {
        ($workflowSkill -match 'cr-skill-structural-econometrics') | Should -Be $true
        ($workflowSkill -match 'cr-skill-ml-economics') | Should -Be $true
        ($workflowSkill -match 'cr-skill-measurement') | Should -Be $true
    }

    # V3 — additive lifecycle framing in cr-review; dispatch table intact
    It "cr-review adds additive Lifecycle & Method Packs framing" {
        ($reviewPrompt -match '(?i)Lifecycle & Method Packs|Lifecycle and Method Packs') | Should -Be $true
        ($reviewFlat -match $spine) | Should -Be $true
    }

    It "cr-review preserves the Step 3 Theory/Modeling routing verbatim" {
        ($reviewPrompt -match 'Theory/Modeling.*cr-identification-audit') | Should -Be $true
        ($reviewPrompt -match 'Theory/Modeling.*cr-econometric-reasoning') | Should -Be $true
    }

    # V4 — lifecycle references in cr-work + cr-brainstorm
    It "cr-work references the lifecycle Execute stage" {
        ($workPrompt -match '(?i)lifecycle') | Should -Be $true
        ($workFlat -match $spine) | Should -Be $true
    }

    It "cr-brainstorm references the lifecycle and method-pack selection" {
        ($bsPrompt -match '(?i)lifecycle') | Should -Be $true
        ($bsPrompt -match '(?i)method pack') | Should -Be $true
    }

    # V5 — doc sync
    It "copilot-instructions.md documents the lifecycle spine and three packs" {
        ($instructions -match '(?i)Responsible Research Lifecycle') | Should -Be $true
        ($instrFlat -match $spine) | Should -Be $true
        ($instructions -match '(?i)Structural pack') | Should -Be $true
        ($instructions -match '(?i)ML pack') | Should -Be $true
        ($instructions -match '(?i)Measurement pack') | Should -Be $true
    }

    It "docs/reference.md documents the lifecycle spine and packs" {
        ($reference -match '(?i)Responsible Research Lifecycle') | Should -Be $true
        ($refFlat -match $spine) | Should -Be $true
    }
}
