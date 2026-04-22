---
date: 2026-04-21
title: "Competitive repo review system (/cg-review-repos prompt)"
status: completed
completed-date: 2026-04-21
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-04-21-competitive-repo-review-system.md"
language: "PowerShell"
estimated-effort: "medium"
tags: [architecture-research, competitive-analysis, prompt-design, workflow]
---

# Plan: Competitive Repo Review System (`/cg-review-repos`)

## Objective

Build a structured system for tracking and reviewing external repos
(Compound Engineering, Superpowers, GSD-2) to identify features worth
integrating into compound-gpid. The system has two modes: a full initial
assessment and a recurring delta review that only covers new releases since
the last review.

## Context

The developer manually skims three external repos that solve similar problems
(AI-assisted development workflows) but has never done a systematic
assessment. The Architecture Research milestone in `roadmap.json` already
has idea-stage features anticipating this work. A brainstorm session
(2026-04-21) selected the "Registry File + Review Prompt" approach.

Key constraints from the brainstorm:
- Output must be **implementation-ready** — each feature card must contain
  enough context for a future `/cg-brainstorm` session to skip re-discovery
- Recurring reviews track by **release tag**, not commits
- The prompt must have a **guardrail** preventing use in consumer projects
- The repo list must be **extensible** via a registry file
- `fetch_webpage` has content size limits — fetch releases pages, not full
  changelogs

Existing patterns to follow:
- Prompt structure: YAML frontmatter with `description:` and `model:`,
  no `tools:` key (orchestrating prompts must be unrestricted)
- Test pattern: existence, frontmatter, no-tool-restriction, content checks
  (see `prompt-tools.Tests.ps1`)
- File naming: `cg-*.prompt.md` for prompts
- Documentation: update `docs/reference.md` with new commands

## Requirements

| ID  | Requirement                                                    | Source      |
|-----|----------------------------------------------------------------|-------------|
| R1  | Registry file (`repos.json`) stores repo list + last-reviewed  | brainstorm  |
| R2  | Prompt has two modes: `--full` (initial) and default (delta)   | brainstorm  |
| R3  | Dev-repo guardrail checks `compound-gpid.md` project-name     | brainstorm  |
| R4  | Feature card template with implementation sketch               | brainstorm  |
| R5  | Delta review fetches releases page, scopes to new releases     | brainstorm  |
| R6  | Registry updated after each review with new release tag + date | brainstorm  |
| R7  | Concept mapping table normalizes terminology across repos      | brainstorm  |
| R8  | Decision criteria filter applied to each feature               | brainstorm  |
| R9  | Tests for prompt structure (frontmatter, guardrail, sections)  | convention  |
| R10 | Docs updated with new command                                  | convention  |

## Implementation Steps

### 1. Create Registry File

- **Requirements**: R1
- **Files**: `.cg-docs/competitive-reviews/repos.json` (create)
- **Details**: Create a JSON file with the following schema:
  ```json
  {
    "schemaVersion": "compound-gpid-competitive-reviews-v1",
    "lastFullReview": null,
    "repos": [
      {
        "id": "compound-engineering",
        "url": "https://github.com/EveryInc/compound-engineering-plugin",
        "releasesUrl": "https://github.com/EveryInc/compound-engineering-plugin/releases",
        "shortName": "CE",
        "lastReviewedRelease": null,
        "lastReviewDate": null
      },
      {
        "id": "superpowers",
        "url": "https://github.com/obra/superpowers",
        "releasesUrl": "https://github.com/obra/superpowers/releases",
        "shortName": "SP",
        "lastReviewedRelease": null,
        "lastReviewDate": null
      },
      {
        "id": "gsd-2",
        "url": "https://github.com/gsd-build/gsd-2",
        "releasesUrl": "https://github.com/gsd-build/gsd-2/releases",
        "shortName": "GSD",
        "lastReviewedRelease": null,
        "lastReviewDate": null
      }
    ]
  }
  ```
  All `lastReviewedRelease` and `lastReviewDate` fields are null initially
  (populated after the first review runs).
- **Test Scenarios**:
  - ✅ Happy path: File exists, valid JSON, three repos listed
  - 🛑 Edge case: Schema version field present
  - ❌ Error path: Malformed JSON detected by prompt
- **Tests**: Add to `prompt-tools.Tests.ps1` — validate file exists and
  parses as valid JSON with required fields
- **Acceptance criteria**: `repos.json` exists, is valid JSON, has
  `schemaVersion` and `repos` array with 3 entries each having `id`, `url`,
  `releasesUrl`, `shortName`, `lastReviewedRelease`, `lastReviewDate`

### 2. Create the `/cg-review-repos` Prompt

- **Requirements**: R2, R3, R4, R5, R6, R7, R8
- **Files**: `.github/prompts/cg-review-repos.prompt.md` (create)
- **Details**: Create a new prompt file with this structure:

  **Frontmatter**:
  ```yaml
  ---
  description: "Review external repos for features to integrate into compound-gpid. Developer-only."
  model: Claude Opus 4.6 (copilot)
  ---
  ```

  **Guardrail (Step 0)**:
  - Read `compound-gpid.md`. Check that frontmatter contains
    `project-name: "Compound GPID"`.
  - If not found or different: display the consumer-project warning and
    **stop immediately** (do not proceed to Step 1).
  - Message: "This prompt is for compound-gpid development only. It reviews
    external repos for feature ideas. It does not apply to consumer projects."

  **Mode Detection (Step 0.5)**:
  - Parse arguments for `--full` flag.
  - `--full`: Initial deep assessment mode — review full README, docs,
    skills/commands/agents directories for each repo.
  - Default (no flag): Delta review mode — only review releases since
    `lastReviewedRelease` in `repos.json`.

  **Registry Read (Step 1)**:
  - Read `.cg-docs/competitive-reviews/repos.json`.
  - If missing: warn and offer to create from template.
  - For delta mode: skip repos where `lastReviewedRelease` is null (they
    need `--full` first). Warn: "Repo '<name>' has no baseline review.
    Run `/cg-review-repos --full` first."

  **Concept Mapping Reference (Step 1.5)**:
  - Include the concept mapping table from the brainstorm as inline
    reference so the prompt can normalize terminology:

  | compound-gpid | CE Plugin | Superpowers | GSD-2 |
  |---------------|-----------|-------------|-------|
  | Prompts | Slash commands | Skills (auto-triggered) | Commands |
  | Agents | Agents | Agents | Extensions |
  | Skills | Skills | Skills | Skills (within extensions) |
  | Instructions | — | Hooks | AGENTS.md / CLAUDE.md |
  | `.cg-docs/` | `.ce-docs/` | Design docs | `.gsd/` (state files) |

  **Review Execution (Step 2)**:

  > **Tool name verification**: Before writing the prompt body, confirm the
  > exact web-fetching tool name available in VS Code Copilot. The tool is
  > `fetch_webpage` in the current environment. If the tool name changes or
  > is unavailable, the prompt must fail visibly ("Could not fetch repo
  > data — verify the web-fetching tool is available") rather than
  > generating feature cards from hallucination.

  For `--full` mode:
  - For each repo in `repos.json`:
    1. Fetch the repo's main page (README) via `fetch_webpage`
    2. Fetch the repo's releases page for current release info
    3. Identify all features/capabilities
    4. For each feature, produce a Feature Card (see template below)
    5. Group features by compatibility verdict
  - Save per-repo assessment:
    `.cg-docs/competitive-reviews/YYYY-MM-DD-<repo-id>-assessment.md`

  For delta mode:
  - For each repo in `repos.json` (that has a baseline):
    1. Fetch the repo's releases page
    2. Identify releases newer than `lastReviewedRelease`
    3. For each new release, analyze the release notes
    4. For each new feature found, produce a Feature Card
  - Save delta report:
    `.cg-docs/competitive-reviews/YYYY-MM-DD-delta-review.md`

  **Feature Card Template (Step 2.5)**:
  ```markdown
  ### Feature: <name>
  - **Source**: <repo shortName> <release-tag> — <link>
  - **What it does**: <1–2 sentence description>
  - **How source implements it**: <brief technical description — files,
    architecture, key patterns>
  - **Compatibility**: Directly applicable / Needs adaptation / Not applicable
  - **Why this verdict**: <1 sentence justification>
  - **How we'd adapt it**: <implementation sketch for compound-gpid —
    which files to create/modify, rough approach>
  - **Maps to**: <prompt | agent | skill | instruction | script>
  - **Effort**: Small / Medium / Large
  - **Priority**: High / Medium / Low
  - **Decision criteria check**:
    - Implementable in Copilot model? Yes/No
    - Benefits GPID team workflows? Yes/No
    - Duplicates existing feature? Yes/No
    - Effort proportional to value? Yes/No
  - **Notes**: <edge cases, dependencies, related CG features>
  ```

  **Decision Criteria Filter (Step 3)**:
  - Apply the four criteria from the brainstorm to each feature:
    1. Implementable within GitHub Copilot's prompt/agent/skill model
    2. Benefits GPID team workflows
    3. Does not duplicate existing compound-gpid functionality
    4. Effort proportional to improvement delivered
  - Features failing any criterion get `Compatibility: Not applicable` with
    explanation.

  **Registry Update (Step 4)**:
  - Update `repos.json` **per-repo immediately** after each repo's review
    completes — not at the end of all repos. This prevents partial-failure
    scenarios where a successful repo's data is lost because a later repo
    failed.
  - For each successfully reviewed repo:
    - Set `lastReviewedRelease` to the latest release tag found
    - Set `lastReviewDate` to today's date (YYYY-MM-DD)
  - If a fetch fails for one repo: log the failure in the summary table,
    skip that repo's registry update, and continue with the next repo.
  - For `--full` mode: also set `lastFullReview` in the root object
    (only after all repos have been attempted).

  **Summary (Step 5)**:
  - Present a summary table:

  | Repo | Releases Reviewed | Features Found | Directly Applicable | Needs Adaptation | Not Applicable |
  |------|-------------------|----------------|---------------------|------------------|----------------|
  | CE   | v2.68.0–v2.68.1   | 5              | 2                   | 2                | 1              |
  | ...  | ...               | ...            | ...                 | ...              | ...            |

  - Highlight top 3 features worth pursuing.
  - Ask: "Want me to add any of these to the roadmap via `@cg-roadmap`?"

- **Test Scenarios**:
  - ✅ Happy path: Prompt exists with correct frontmatter, no tools key
  - ✅ Happy path: Guardrail section references `compound-gpid.md` and
    `project-name`
  - 🛑 Edge case: `--full` flag mentioned in prompt body
  - 🛑 Edge case: Feature card template includes all required fields
  - ❌ Error path: Consumer-project warning text present
- **Tests**: See Step 4
- **Acceptance criteria**: Prompt file exists with correct frontmatter,
  guardrail logic, two modes, feature card template, registry update logic,
  and summary output

### 3. Create Assessment File Template

- **Requirements**: R4, R7
- **Files**: None created now — the prompt generates these on execution
- **Details**: Document the expected output format for assessment files:

  ```markdown
  ---
  date: YYYY-MM-DD
  repo: "<repo-id>"
  repo-url: "<url>"
  release-reviewed: "<tag>"
  review-type: "full|delta"
  features-found: <count>
  directly-applicable: <count>
  needs-adaptation: <count>
  not-applicable: <count>
  ---

  # <Repo Short Name> Assessment — <release-tag>

  ## Overview
  <Brief repo description and philosophy>

  ## Concept Mapping
  <How this repo's architecture maps to compound-gpid>

  ## Features — Directly Applicable
  <Feature cards for directly applicable features>

  ## Features — Needs Adaptation
  <Feature cards for features needing adaptation>

  ## Features — Not Applicable
  <Feature cards with explanation of why not>

  ## Summary
  <Top recommendations and next steps>
  ```

  This structure is embedded in the prompt (Step 2) so the prompt produces
  it when run. No separate template file needed.

- **Test Scenarios**:
  - ✅ Happy path: Prompt mentions the assessment file path format
  - 🛑 Edge case: Prompt mentions delta report path format
- **Tests**: Content check in prompt-tools.Tests.ps1
- **Acceptance criteria**: Prompt body contains both file path patterns

### 4. Write Tests

- **Requirements**: R9
- **Files**:
  - `tests/prompt-tools.Tests.ps1` (modify — append new test blocks)
  - `tests/model-assignments.Tests.ps1` (modify — update count sentinel
    from 17 to 18)
- **Details**:

  **4a. Update count sentinel**: In `tests/model-assignments.Tests.ps1`,
  update the prompt file count sentinel from 17 to 18. The test reads:
  `$promptFiles.Count | Should Be 17` — change `17` to `18`. This test
  validates against `Get-ChildItem` on `.github/prompts/*.prompt.md` at
  runtime and will fail immediately if not updated.

  **4b. Add Pester test blocks** following the established pattern
  (see cg-ideate tests as reference):

  **Block 1: File existence**
  ```powershell
  Describe "cg-review-repos.prompt.md - file existence" {
      $promptFile = Join-Path $repoRoot ".github\prompts\cg-review-repos.prompt.md"
      It "exists in the repository" {
          Test-Path $promptFile | Should Be $true
      }
  }
  ```

  **Block 2: Frontmatter validation**
  ```powershell
  Describe "cg-review-repos.prompt.md - frontmatter" {
      $promptFile = Join-Path $repoRoot ".github\prompts\cg-review-repos.prompt.md"
      $frontmatter = Get-Frontmatter -FilePath $promptFile
      Context "required frontmatter fields" {
          It "has a description in frontmatter" {
              $frontmatter | Should Match 'description:'
          }
          It "has a model in frontmatter" {
              $frontmatter | Should Match 'model:'
          }
      }
  }
  ```

  **Block 3: No tool restriction**
  ```powershell
  Describe "cg-review-repos.prompt.md - no tool restriction" {
      $promptFile = Join-Path $repoRoot ".github\prompts\cg-review-repos.prompt.md"
      Context "orchestrator must have unrestricted tools" {
          $frontmatter = Get-Frontmatter -FilePath $promptFile
          It "does not have a tools: key" {
              ($frontmatter -notmatch '(?m)^\s*tools:') | Should Be $true
          }
      }
  }
  ```

  **Block 4: Guardrail content**
  ```powershell
  Describe "cg-review-repos.prompt.md - dev-repo guardrail" {
      $promptFile = Join-Path $repoRoot ".github\prompts\cg-review-repos.prompt.md"
      $content = Get-Content $promptFile -Raw -Encoding UTF8
      It "checks compound-gpid.md for project-name" {
          ($content -match 'project-name') | Should Be $true
      }
      It "contains consumer-project warning message" {
          ($content -match 'compound-gpid development only') | Should Be $true
      }
  }
  ```

  **Block 5: Content structure**
  ```powershell
  Describe "cg-review-repos.prompt.md - content structure" {
      $promptFile = Join-Path $repoRoot ".github\prompts\cg-review-repos.prompt.md"
      $content = Get-Content $promptFile -Raw -Encoding UTF8
      It "references --full flag for initial assessment mode" {
          ($content -match '--full') | Should Be $true
      }
      It "references repos.json registry file" {
          ($content -match 'repos\.json') | Should Be $true
      }
      It "feature card template includes Compatibility field" {
          ($content -match 'Compatibility:') | Should Be $true
      }
      It "feature card template includes How we'd adapt it field" {
          ($content -match 'How we''d adapt it') | Should Be $true
      }
      It "mentions concept mapping table" {
          ($content -match 'Concept Mapping') | Should Be $true
      }
  }
  ```

  **Block 6: Registry file validation**
  ```powershell
  Describe "competitive-reviews/repos.json - registry" {
      $registryFile = Join-Path $repoRoot ".cg-docs\competitive-reviews\repos.json"
      It "exists in the repository" {
          Test-Path $registryFile | Should Be $true
      }
      It "is valid JSON" {
          { Get-Content $registryFile -Raw | ConvertFrom-Json } | Should Not Throw
      }
      $json = Get-Content $registryFile -Raw | ConvertFrom-Json
      It "has schemaVersion field" {
          $json.schemaVersion | Should Not BeNullOrEmpty
      }
      It "has repos array with at least one entry" {
          $json.repos.Count | Should BeGreaterThan 0
      }
      It "repo 'compound-engineering' has required fields" {
          $repo = $json.repos | Where-Object { $_.id -eq 'compound-engineering' }
          $repo.id | Should Not BeNullOrEmpty
          $repo.url | Should Not BeNullOrEmpty
          $repo.releasesUrl | Should Not BeNullOrEmpty
          $repo.shortName | Should Not BeNullOrEmpty
      }
      It "repo 'superpowers' has required fields" {
          $repo = $json.repos | Where-Object { $_.id -eq 'superpowers' }
          $repo.id | Should Not BeNullOrEmpty
          $repo.url | Should Not BeNullOrEmpty
          $repo.releasesUrl | Should Not BeNullOrEmpty
          $repo.shortName | Should Not BeNullOrEmpty
      }
      It "repo 'gsd-2' has required fields" {
          $repo = $json.repos | Where-Object { $_.id -eq 'gsd-2' }
          $repo.id | Should Not BeNullOrEmpty
          $repo.url | Should Not BeNullOrEmpty
          $repo.releasesUrl | Should Not BeNullOrEmpty
          $repo.shortName | Should Not BeNullOrEmpty
      }
  }
  ```

- **Test Scenarios**:
  - ✅ Happy path: All tests pass with correct prompt and registry
  - 🛑 Edge case: Missing frontmatter field detected
  - ❌ Error path: Missing prompt file detected
- **Tests**: Self-testing (these ARE the tests)
- **Acceptance criteria**: All 6 test blocks pass via
  `. tests\Run-Tests.ps1`

### 5. Update Documentation

- **Requirements**: R10
- **Files**:
  - `docs/reference.md` (modify)
  - `docs/model-guide.md` (modify)
- **Details**:

  **5a. Update `docs/reference.md`**: Add `/cg-review-repos` to the command
  reference table:

  | Command | Description |
  |---------|-------------|
  | `/cg-review-repos` | Review external repos for features to integrate (developer-only) |
  | `/cg-review-repos --full` | Full initial assessment of all tracked repos |

  Also add a brief section explaining the competitive review system,
  registry file location, and how to add new repos.

  **5b. Update `docs/model-guide.md`**: This file is the authoritative
  model-tier record and requires a table row for every prompt file.
  - Append a row for `cg-review-repos.prompt.md` to the prompt table:
    `| cg-review-repos | Opus 4.6 | Orchestration 4, reasoning 4 — multi-repo analysis with registry write |`
  - Update the header count from "30 prompt and agent files" to "31 prompt
    and agent files".
  - Update any inline constants that track total file counts.

- **Test Scenarios**:
  - ✅ Happy path: Command appears in reference.md
  - ✅ Happy path: New row appears in model-guide.md prompt table
- **Tests**: Verify via content checks (optional)
- **Acceptance criteria**: `docs/reference.md` includes the new command;
  `docs/model-guide.md` includes a row for `cg-review-repos` and correct
  total count

## Testing Strategy

- **Structural tests** (Pester): Validate prompt file existence, frontmatter
  fields, no-tool-restriction, guardrail content, feature card template
  presence, and registry JSON validity.
- **No behavioral tests**: The prompt's actual review behavior (web fetching,
  analysis quality) cannot be tested structurally. Quality is validated
  during Phase 2 of the brainstorm's Next Steps (running the first full
  assessment).
- **Test runner**: Use `. tests\Run-Tests.ps1` via `execution_subagent` per
  Pester safety rules.

## Documentation Checklist

- [ ] Prompt file has clear inline documentation (comments explaining each
      step)
- [ ] `docs/reference.md` updated with new command
- [ ] Registry file schema documented in prompt body
- [ ] Feature card template documented in prompt body
- [ ] Brainstorm file cross-referenced

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| `fetch_webpage` truncates large release pages (GSD-2 has 113 releases) | Missing features in delta review | Fetch specific release URLs (`/releases/tag/<tag>`) for detailed notes; use releases list page only for identifying new tags |
| `fetch_webpage` tool name wrong or unavailable | Prompt generates hallucinated feature cards from no data — worse than a hard failure | Prompt must verify fetch succeeded before generating cards; fail visibly if tool returns no content |
| Feature cards lack implementation detail | `/cg-brainstorm` sessions still need extensive discovery | Require "How we'd adapt it" field in every card; include file paths and rough approach |
| Registry gets stale (user forgets to run reviews) | Drift from external repos | Low risk — user has committed to biweekly cadence; registry date makes staleness visible |
| Partial fetch failure across repos | Successful repos' data lost if all-or-nothing update | Per-repo registry update immediately after each repo completes; failed repos logged in summary but not updated |
| Prompt used in consumer project by mistake | Confusing output, wasted time | Guardrail checks `project-name` in `compound-gpid.md` and refuses to proceed |
| New repos added but no `--full` baseline exists | Delta review skips them | Prompt warns when `lastReviewedRelease` is null; instructs user to run `--full` |

## Out of Scope

- **Actually implementing any discovered features** — Each feature goes
  through its own `/cg-brainstorm` → `/cg-plan` → `/cg-work` cycle
- **Automated scheduling** — No GitHub Actions or cron; always user-initiated
- **Repos beyond the initial three** — The system is extensible but the plan
  only covers CE, Superpowers, and GSD-2
- **Running the first full assessment** — This plan builds the infrastructure;
  the actual assessment is a separate `/cg-review-repos --full` invocation
- **Adapting features for Claude Code or Codex** — Target platform is GitHub
  Copilot (VS Code); other platforms are noted but not pursued
