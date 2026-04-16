---
plan: .cg-docs/plans/2026-04-16-context-layer-restructuring.md
findings:
  P1.1: fixed
  P1.2: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: skipped
---

## Review Report

**Review depth**: thorough
**Files reviewed**: 24 (15 prompt `.md` files, 3 scripts, 4 modified test files, 2 new untracked test/template files, 1 plan file, `roadmap.json`)
**Findings**: P0: 0 · P1: 2 · P2: 3 · P3: 3

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-version-control] `.github/copilot-instructions.template.md` — file is untracked (not staged)
  **Why**: This is the critical asset of the entire feature. `New-CopilotInstructions` in `scripts/helpers.ps1` throws an explicit error when this file is missing: *"Compound GPID template not found… The installation may be corrupted"*. After merge and `cg-update`, all consumer projects will hit this error on every `cg-link` / `cg-update` run until the file is committed to the repo.
  **Fix**: `git add ".github/copilot-instructions.template.md"` before committing.

- **[P1.2]** [cg-version-control] `tests/helpers.Tests.ps1` — file is untracked (not staged)
  **Why**: `tests/Run-Tests.ps1` lists `'helpers'` in `$testNames`. If this file is absent from the commit, the test runner warns about a missing file and `New-CopilotInstructions` has zero test coverage in the deployed version — defeating the entire `helpers.Tests.ps1` test suite created for this feature.
  **Fix**: `git add "tests/helpers.Tests.ps1"` before committing.

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `scripts/helpers.ps1:88–91` — `-replace` operator treats replacement strings as regex, risking silent output corruption
  **Why**: PowerShell's `-replace` operator (wrapping .NET `Regex.Replace`) interprets `$0`, `$1`, `$&`, `$$` in the *replacement* string as backreferences to captured groups. If `$projectName`, `$languages`, or any config value contains a `$`-digit sequence (e.g., `"R$0 Pipeline"`, `"Data$1 Team"`), the generated `copilot-instructions.md` will have those substrings replaced with the regex match text rather than the literal `$` character. The generated file silently diverges from intent with no error.
  **Fix**: Replace all four `-replace` calls with the `.Replace()` string method, which performs literal substitution with no regex interpretation:
  ```powershell
  $output = $output.Replace('{{project-name}}', $projectName)
  $output = $output.Replace('{{project-type}}', $projectType)
  $output = $output.Replace('{{languages}}',    $languages)
  $output = $output.Replace('{{review-depth}}', $reviewDepth)
  ```

- **[P2.2]** [cg-testing] `tests/helpers.Tests.ps1` — no edge-case test for special characters in config values
  **Why**: All existing tests use simple project names (`"Poverty Analysis"`, `"Test"`, `"Charter Only"`). No test covers project names or language values containing `$`, backticks, or `+` — the exact inputs that would expose P2.1 if the `-replace` pattern were ever reintroduced by a future refactor.
  **Fix**: Add one test in the "placeholder substitution" Context:
  ```powershell
  It "handles project names with dollar signs (literal, not backreferences)" {
      # Validates that $0-style strings are preserved literally
      ...
  }
  ```

- **[P2.3]** [cg-testing] `tests/prompt-tools.Tests.ps1` — three new prompt behaviors lack Pester coverage
  **Why**: Three new behaviors added in this feature have no guards against future accidental removal:
  1. `cg-compound.prompt.md` Step 5 — context enrichment: proposes additions to `compound-gpid.context.md`
  2. `cg-resume.prompt.md` Step 2f.5 — Current Focus staleness check: cross-references milestone statuses
  3. `cg-work.prompt.md` Step 3.8 — milestone completion check: dispatches `@cg-roadmap` when all features are `done`

  **Fix**: Add three `Describe` blocks using the same `Get-Content + regex` pattern as existing tests. Examples:
  ```powershell
  Describe "cg-compound.prompt.md - context enrichment step" {
      It "references compound-gpid.context.md in Step 5" { ... }
      It "proposes creating context.md when it does not exist" { ... }
  }
  Describe "cg-resume.prompt.md - Current Focus staleness check" {
      It "includes Step 2f.5 Current Focus staleness check" { ... }
      It "references milestone status done in staleness logic" { ... }
  }
  Describe "cg-work.prompt.md - milestone completion check" {
      It "includes Step 3.8 milestone completion check" { ... }
      It "dispatches @cg-roadmap when milestone features are all done" { ... }
  }
  ```

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-version-control] `.cg-docs/plans/2026-04-16-context-layer-restructuring.md` — untracked (not staged)
  **Why**: The active plan file should be committed so `cg-resume` can reference it and the team can track implementation history.
  **Fix**: `git add ".cg-docs/plans/2026-04-16-context-layer-restructuring.md"`

- **[P3.2]** [cg-documentation] `copilot-instructions.template.md:33` — workspace reference lacks "if it exists" qualifier
  **Why**: The line *"For multi-folder workspace details, see `## Workspace Notes` in `compound-gpid.context.md`."* links to a file that does not exist in all consumer projects. This could confuse users who get the generated `copilot-instructions.md` before running `/cg-setup`.
  **Fix**: Add the qualifier: `"…see \`## Workspace Notes\` in \`compound-gpid.context.md\` (if it exists)."`

- **[P3.3]** [cg-reproducibility] `scripts/helpers.ps1` — CRLF warning in `git diff --stat`
  **Why**: `git diff --stat` reported a line-ending conversion warning for `helpers.ps1`. Mixed or inconsistent line endings cause noisy diffs and can affect regex matching on Windows when `Get-Content -Raw` includes `\r` characters.
  **Fix**: Verify the file uses CRLF (Windows-native). If needed, add `scripts/helpers.ps1 text=auto eol=crlf` to `.gitattributes`.

---

### ✅ Passed

- **cg-code-quality**: No DRY violations; `New-CopilotInstructions` is focused and well-named; constants are extracted; no magic strings beyond the justified `"<project-name>"` / `"<not configured>"` fallbacks.
- **cg-performance**: No performance concerns; file reads are minimal; regex patterns are non-catastrophic (non-greedy `.*?` in frontmatter parser is correct).
- **cg-architecture**: Clean separation — template lives in install dir, not in consumer projects; managed-file marker model is consistent with existing `link.ps1`/`update.ps1` behavior; `New-CopilotInstructions` correctly receives `$TemplateDir` vs `$ProjectRoot` as distinct inputs.
- **cg-data-quality**: `New-CopilotInstructions` has explicit `Test-Path` guards and falls back to placeholder values rather than failing silently on missing config — consistent with the project constraint "fail loudly, never silently".
- **cg-documentation**: All 15 prompts have consistent Step 0 updates; `New-CopilotInstructions` has a complete `.SYNOPSIS`, `.DESCRIPTION`, `.PARAMETER`, `.EXAMPLE` docblock.
- **cg-learnings-researcher**: No directly relevant prior solutions in `.cg-docs/solutions/`; the `-replace` backreference pattern is a known PowerShell pitfall not previously documented in this repo.
- **cg-adversarial**: Managed-file marker check correctly uses `[regex]::Escape($CopilotInstructionsMarker)` for safe regex matching; paths are constructed from trusted `$PSScriptRoot`-relative sources; no path traversal vectors; no credential handling. Prompt injection via charter content is theoretically possible but is a trusted-author scenario.
