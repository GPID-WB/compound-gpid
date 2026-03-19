---
date: 2026-03-19
title: "Release automation via /cg-release prompt"
status: completed
brainstorm: ".cg-docs/brainstorms/2026-03-19-release-automation.md"
language: "PowerShell"
estimated-effort: "small-medium"
tags: [releases, automation, github-api, semver, cg-release, powershell, prompt]
---

# Plan: Release automation via /cg-release prompt

## Objective

Build a repeatable `/cg-release` workflow that Copilot can drive end-to-end: detect the next semver tag from git history, draft curated release notes from commits and `.cg-docs/` knowledge, check `SCHEMA_VERSION` status, and publish a GitHub Release — all parameterized through a generalized `create-release.ps1` script.

## Context

- **Current state**: `create-release.ps1` has tag `v0.0.5`, release name, and ~40 lines of notes hardcoded. Each release requires manual editing.
- **Brainstorm decision**: Approach 1 — Prompt + Generalized Script. Dumb script (parameters, GCM auth, API call) + smart prompt (version detection, changelog analysis, SCHEMA_VERSION check, confirmation, execution).
- **SCHEMA_VERSION**: Read from repo root by `update.ps1` and stamped into each project's `compound-gpid.local.md`. Needs bumping only for structural migrations. The prompt must warn (not auto-bump).
- **Release notes**: Ephemeral `RELEASE_NOTES.md` (gitignored). GitHub Release is source of truth.
- **Conventions**: Pester 3.4+ tests (Describe/Context/It, `$TestDrive`, no Pester 5 features). Prompt files use YAML frontmatter with `description` and `model` fields.
- **Past learnings**: PowerShell `[switch]` parameter testing requires simulating actual parameter binding semantics, not magic strings (`.cg-docs/solutions/testing-patterns/2026-03-19-testing-powershell-switch-parameters.md`).

## Implementation Steps

### Step 1: Generalize `create-release.ps1`

- **Files**: `create-release.ps1` (modify)
- **Details**:
  - Add `param()` block at top with:
    - `[Parameter(Mandatory)][string]$Tag` — the git tag (e.g. `v0.0.6`)
    - `[Parameter(Mandatory)][string]$Name` — release name (e.g. `"v0.0.6 - Release automation"`)
    - `[Parameter(Mandatory)][string]$NotesFile` — path to a Markdown file whose content becomes the release body
    - `[switch]$Draft` — create as draft release
    - `[switch]$Prerelease` — mark as prerelease
  - Read `$NotesFile` content via `Get-Content -Raw` with existence check
  - Replace hardcoded `v0.0.5` in the idempotency check URL with `$Tag`
  - Replace hardcoded payload values with parameters: `tag_name = $Tag`, `name = $Name`, `body = $notes`, `draft = $Draft.IsPresent`, `prerelease = $Prerelease.IsPresent`
  - Keep GCM auth logic verbatim
  - Keep `release-result.txt` output format (`EXISTS|id|url` or `CREATED|id|url`)
  - Validate `$Tag` matches `v\d+\.\d+\.\d+` pattern; error on bad format
  - `$ErrorActionPreference = "Stop"` stays at top
- **Tests**: Step 3
- **Acceptance criteria**: Script can be invoked as `.\create-release.ps1 -Tag v0.0.6 -Name "v0.0.6 - Test" -NotesFile RELEASE_NOTES.md` and also as `.\create-release.ps1 -Tag v0.0.6 -Name "v0.0.6 - Test" -NotesFile RELEASE_NOTES.md -Draft`. All hardcoded values removed.

### Step 2: Add `RELEASE_NOTES.md` and `release-result.txt` to `.gitignore`

- **Files**: `.gitignore` (modify)
- **Details**:
  - Add a `# Release automation` section after the existing `# Secrets` section
  - Add `RELEASE_NOTES.md` (ephemeral draft — GitHub Release is source of truth)
  - Add `release-result.txt` (script output, local only)
- **Tests**: Visual inspection
- **Acceptance criteria**: Both files are listed in `.gitignore`. `git status` no longer shows them as untracked.

### Step 3: Add Pester tests for `create-release.ps1`

- **Files**: `tests/create-release.Tests.ps1` (create)
- **Details**: Follow existing test conventions (Pester 3.4+, `Describe`/`Context`/`It`, `$TestDrive`). Test the following without making real API calls:
  - **Parameter validation**: Tag format validation — `v1.2.3` passes, `1.2.3` fails, `v1.2` fails, `vx.y.z` fails.
  - **NotesFile existence check**: Script errors when the file doesn't exist.
  - **Switch parameter semantics**: When `-Draft` is passed, `$Draft.IsPresent` is `$true`; when omitted, `$false`. Same for `-Prerelease`. Follow the lesson from `2026-03-19-testing-powershell-switch-parameters.md`.
  - **Idempotency output format**: When a release already exists, output matches `EXISTS|<id>|<url>` pattern.
  - **Create output format**: On successful create, output matches `CREATED|<id>|<url>`.
  - **Notes file content**: Notes read from file match the body sent to the API.
  - Note: Tests should validate parameter binding and local logic. Actual HTTP calls to GitHub are out of scope for unit tests (would require mocking `Invoke-RestMethod`, which Pester 3.4 supports but adds fragility). Focus on input validation and output format.
- **Acceptance criteria**: `Invoke-Pester tests/create-release.Tests.ps1` passes. Covers parameter validation, switch semantics, file existence check, and output format patterns.

### Step 4: Create `/cg-release` prompt

- **Files**: `cg-release.prompt.md` at repo root (create) — NOT inside `.github/prompts/`
- **Why repo root?**: `.github/prompts/` is junctioned into every linked user project via `cg-link`. Placing the release prompt there would expose a developer-only command to all users. The repo root is discoverable by VS Code as a slash command when the compound-gpid workspace is open, but invisible to linked projects (junctions only cover `.github/` subdirectories). Architecture-level isolation — no guard needed.
- **Details**: YAML frontmatter with `description` and `model` fields (match `cg-work.prompt.md` pattern). The prompt instructs Copilot to execute this flow:

  **Step 1 — Detect current version**:
  - Run `git describe --tags --abbrev=0` to find the latest tag.
  - If no tags exist, treat as `v0.0.0` (first release).

  **Step 2 — Analyze changes since last tag**:
  - Run `git log <tag>..HEAD --oneline` to get commit list.
  - Classify commits by conventional commit type prefix: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `data`, `analysis`.
  - Apply semver rules: any `feat` → minor bump, only `fix` → patch bump, any commit message containing `BREAKING CHANGE` or `!:` → major bump. Suggest the result as next tag.
  - Read `.cg-docs/brainstorms/`, `.cg-docs/plans/`, `.cg-docs/solutions/` for entries dated after the last release tag. Note which are relevant.

  **Step 3 — Check SCHEMA_VERSION**:
  - Read `SCHEMA_VERSION` from repo root.
  - Scan the changes for structural migrations (new/renamed/moved folders or config fields in `compound-gpid.local.md`, changes to `scripts/update.ps1` migration logic, new `.cg-docs/` subfolders).
  - If structural changes detected, warn: _"This release includes structural changes. Consider bumping `SCHEMA_VERSION` before publishing."_
  - If no structural changes, confirm: _"No structural migrations detected. `SCHEMA_VERSION` (`<current>`) is up to date."_

  **Step 4 — Draft release notes**:
  - Write curated, human-friendly narrative to `RELEASE_NOTES.md` (not a raw commit log).
  - Include: "What's new" section with feature descriptions, "Bug fixes" section, "Under the hood" section for internal improvements, "Upgrading" section with the `cg-update` command.
  - Cross-reference relevant `.cg-docs/` entries for depth and context.
  - Style should match the v0.0.5 release notes (prose, tables where helpful, code blocks for commands).

  **Step 5 — Present confirmation summary**:
  - Show the user: proposed tag, proposed release name, SCHEMA_VERSION status, and the full notes preview.
  - Ask user to confirm, adjust tag/name, or edit notes.

  **Step 6 — Execute**:
  - On confirmation, run in terminal: `.\create-release.ps1 -Tag <tag> -Name "<name>" -NotesFile RELEASE_NOTES.md`
  - Add `-Draft` or `-Prerelease` if user requested.
  - Read `release-result.txt` and report the result (link to the GitHub Release).

- **Tests**: Manual — invoke `/cg-release` and verify the flow.
- **Acceptance criteria**: `/cg-release` is discoverable in VS Code's slash command list when the compound-gpid workspace is open. NOT visible from linked user projects. Invoking it produces a version suggestion, drafted notes, confirmation prompt, and successful execution.

### Step 5: Update documentation

- **Files**: `docs/reference.md` (modify — add `/cg-release` to the prompts table), `docs/workflow.md` (modify — mention release as optional final step after the compound loop)
- **Details**:
  - Add `/cg-release` entry to the reference table of prompts with description: _"Create a GitHub Release. Detects next semver tag, drafts release notes, checks SCHEMA_VERSION, and publishes. Developer-only — lives at repo root, not junctioned to user projects."_
  - In workflow docs, add a brief note after the Compound step: _"When ready to publish, use `/cg-release` to create a GitHub Release (available only from the compound-gpid workspace)."_
- **Tests**: Visual inspection.
- **Acceptance criteria**: Both docs reference `/cg-release` and note it is developer-only.

## Testing Strategy

- **Unit tests** (Pester 3.4+): Parameter validation, switch semantics, file checks, output format — all in `tests/create-release.Tests.ps1`. No real HTTP calls.
- **Integration test** (manual): Run `/cg-release` end-to-end with `-Draft` to create a draft release on GitHub, verify it appears correctly, then delete the draft.
- **Edge cases to cover**:
  - No tags exist yet (first release)
  - Tag already exists (idempotency)
  - NotesFile path doesn't exist
  - Invalid tag format
  - `-Draft` and `-Prerelease` both passed
  - Empty commit log since last tag (nothing to release)
  - SCHEMA_VERSION file missing from repo

## Documentation Checklist

- [ ] Script header comment in `create-release.ps1` documenting parameters and usage
- [ ] `/cg-release` prompt described in `docs/reference.md`
- [ ] Release step mentioned in `docs/workflow.md`
- [ ] Inline comments in prompt file explaining each step

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| GCM token missing or expired | Script already errors with clear message. Prompt should mention: _"Make sure you're authenticated — run `git credential fill` to check."_ |
| Semver suggestion wrong (e.g., treats breaking change as minor) | User confirms version before execution. Override always available. |
| `SCHEMA_VERSION` bump forgotten | Prompt explicitly warns when structural changes detected. Not automated — user decides. |
| Terminal tools disabled in session | Prompt falls back to printing the command for manual execution. |
| Pester 3.4 vs 5 incompatibility | Use only Pester 3.4 syntax (`Should Be`, not `Should -Be`). Match existing test files. |

## Out of Scope

- Multi-repo releases
- Build artifact attachments
- Persistent `CHANGELOG.md`
- Automatic `SCHEMA_VERSION` bumping
- CI/CD integration (script is CI-ready but pipeline config is deferred)
