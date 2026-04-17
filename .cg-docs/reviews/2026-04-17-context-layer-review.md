---
plan: .cg-docs/plans/2026-04-16-context-layer-restructuring.md
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P2.9: fixed
  P2.10: fixed
  P2.11: fixed
  P2.12: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
  P3.7: fixed
  P3.8: fixed
  P3.9: fixed
  P3.10: fixed
  P3.11: fixed
  P3.12: fixed
  P3.13: skipped
  P3.14: skipped
---
# Code Review: Context Layer + New-CopilotInstructions

**Date**: 2026-04-17
**Branch**: feat/context-layer
**Requested depth**: light — **escalated to standard** (≥ 50 non-test lines changed; `scripts/` trigger adds `@cg-data-quality`)
**Files reviewed**: 33 changed files (1,814 insertions, 65 deletions)
**Primary changes**: `New-CopilotInstructions` function, template-based instructions generation, `compound-gpid.context.md` lifecycle, milestone-completion check (Step 3.8)
**Agents**: cg-code-quality, cg-testing, cg-documentation, cg-version-control, cg-reproducibility, cg-performance, cg-architecture, cg-data-quality

---

## Summary

The template-based `New-CopilotInstructions` function is well-designed — the `.Replace()` approach (not `-replace`) correctly avoids regex backreference corruption, the fallback strategy is solid, and the test coverage is broad. The dominant issue across all agents is a **file encoding regression** (P1.1–P1.2): replacing `Copy-Item` with `Get-Content`/`Set-Content` without `-Encoding UTF8` silently corrupts non-ASCII project names on any non-Western locale Windows system and writes UTF-16LE output where UTF-8 is expected. This must be fixed before merge.

---

## P1 — CRITICAL (must fix before merge)

**[P1.1]** `cg-code-quality` / `cg-reproducibility` / `cg-data-quality` · `scripts/helpers.ps1:49,55,73` — `Get-Content` missing `-Encoding UTF8` for all three reads
**Why**: PS5.1 `Get-Content` without `-Encoding` defaults to the system ANSI codepage (Windows-1252 on Western machines, Shift-JIS on Japanese, GBK on Chinese). Git-tracked files are UTF-8 without BOM. On any non-Western-locale Windows system (common across the World Bank), non-ASCII characters in project names (`"Análisis de Pobreza"`, Arabic institution names, etc.) are silently corrupted before placeholder substitution.
**Fix**: Add `-Encoding UTF8` to all three reads:
```powershell
$template       = Get-Content $templatePath -Raw -Encoding UTF8
$charterContent = Get-Content $charterPath  -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
$localContent   = Get-Content $localPath    -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
```

**[P1.2]** `cg-code-quality` / `cg-data-quality` · `scripts/link.ps1:172,182` / `scripts/update.ps1:363` — `Set-Content` missing `-Encoding UTF8`, writing `copilot-instructions.md` as ANSI
**Why**: PS5.1 `Set-Content` without `-Encoding` defaults to the system ANSI codepage. Before this refactor, `Copy-Item` preserved the source's UTF-8 encoding. The new `Set-Content -Value $generated` calls write ANSI-encoded output, making `git diff` see binary-like garbage on non-Western systems and potentially corrupting the file for VS Code Copilot. This is a direct encoding regression introduced by replacing `Copy-Item` with `Set-Content`.
**Fix**: Add `-Encoding UTF8` to all three `Set-Content` calls:
```powershell
Set-Content -Path $CopilotInstructionsDest -Value $generated -Encoding UTF8
```
(applies to both branches of Step 4 in `link.ps1` and the refresh block in `update.ps1`)

**[P1.3]** `cg-testing` · `tests/link.Tests.ps1:541` — `$entries` list in new Describe block is hardcoded in the test, disconnected from `$cgGitignoreEntries` in `link.ps1`
**Why**: The "context.md is not gitignored" Describe defines its own `$entries = @(...)` literal. This test cannot detect if someone adds `compound-gpid.context.md` to the actual `$cgGitignoreEntries` array in `link.ps1` — the hardcoded test list would still pass. The test is tautologically true by construction and provides zero regression protection for the actual gitignore list.
**Fix**: Read the real array from `link.ps1` by extracting it via regex instead of duplicating it:
```powershell
$linkContent = Get-Content (Join-Path $repoRoot "scripts\link.ps1") -Raw
$block = [regex]::Match($linkContent, '(?s)\$cgGitignoreEntries\s*=\s*@\((.+?)\)').Groups[1].Value
$entries = $block -split '\r?\n' |
           ForEach-Object { $_.Trim().Trim('"').Trim("'") } |
           Where-Object { $_ -ne '' }
($entries -contains "compound-gpid.context.md") | Should Be $false
($entries | Measure-Object).Count | Should BeGreaterThan 0  # guard against empty extraction
```

---

## P2 — IMPORTANT (should fix)

**[P2.1]** `cg-code-quality` · `scripts/link.ps1:168-184` — DRY violation: identical generate-and-write block in two branches of Step 4
**Why**: The two-liner `$generated = New-CopilotInstructions ...; Set-Content ... -Value $generated` appears in both the marker-present branch and the file-absent branch. Future changes (e.g., the `-Encoding` fix) must be applied twice, and the branches can silently diverge.
**Fix**: Hoist the condition to a single boolean; call generate-and-write once:
```powershell
$skipGenerate = (Test-Path $CopilotInstructionsDest) -and
    ($existingContent = Get-Content $CopilotInstructionsDest -Raw -ErrorAction SilentlyContinue) -and
    ($existingContent -notmatch [regex]::Escape($CopilotInstructionsMarker))

if ($skipGenerate) {
    Write-Host "  copilot-instructions.md - user-managed (marker absent), skipping" -ForegroundColor Yellow
} else {
    $generated = New-CopilotInstructions -TemplateDir $CompoundGpidDir -ProjectRoot $ProjectRoot
    Set-Content -Path $CopilotInstructionsDest -Value $generated -Encoding UTF8
    Write-Host "  copilot-instructions.md - generated" -ForegroundColor DarkGray
}
```

**[P2.2]** `cg-testing` · `tests/update.Tests.ps1:160-196` — Tests simulate logic inline; actual `update.ps1` code path is untested
**Why**: Both update.ps1 tests write a file, run an inline `if ($existing -match ...)` conditional, and assert the result. The real `update.ps1` code path — which uses `[regex]::Escape()`, `New-CopilotInstructions`, and guards on `$cwdGithub` — is never executed. A regression in `update.ps1` (wrong marker, missing Escape, bad path) would leave these tests green.
**Fix**: Extract the marker-check and file-refresh logic from `update.ps1` into a helper function (e.g., `Update-ManagedInstructionsFile` in `helpers.ps1`). Tests can then call the function directly with `$TestDrive`-based paths.

**[P2.3]** `cg-testing` · `tests/helpers.Tests.ps1` — Missing test: `r-syntax` set but language is not R — dialect must NOT be appended
**Why**: `helpers.ps1` guards `if ($null -ne $rSyntax -and $language -match '(?i)\bR\b')`. If someone removes or widens that guard, a Python or Stata project would get the R dialect annotation injected. No test covers the language-is-not-R path.
**Fix**:
```powershell
Describe "New-CopilotInstructions - r-syntax with non-R language does not append dialect" {
    # ... setup with Language = "Python", RSyntax = "data.table-collapse"
    It "does not append R dialect info when language is Python" {
        ($result -match 'data\.table-collapse') | Should Be $false
    }
    It "does not inject '(R dialect:' for non-R language" {
        ($result -match '\(R dialect:') | Should Be $false
    }
}
```

**[P2.4]** `cg-documentation` · `docs/reference.md` — `/cg-work` entry missing Step 3.8 milestone-completion behaviour
**Why**: The reference entry documents Steps 1–3.7 but omits Step 3.8 (milestone completion check + Current Focus update offer). A user reading `reference.md` cannot discover that `/cg-work` may prompt to update the project charter after a milestone completes.
**Fix**: Extend the `/cg-work` description to include: *"If all features in a milestone are marked done, prompts to update the charter's Current Focus."*

**[P2.5]** `cg-documentation` · `docs/reference.md` — Schema note "milestone status never set directly" contradicts Step 3.8 dispatch
**Why**: `reference.md` states milestone status is derived from features and never set directly. Step 3.8 in `cg-work` dispatches `@cg-roadmap` with "Update milestone `<id>` to status done" — a direct set command. Conflicting instructions for the same agent.
**Fix**: Clarify: *"Milestone status is computed by `@cg-roadmap` from feature statuses. After all features in a milestone are marked `done`, `/cg-work` dispatches `@cg-roadmap` to trigger re-evaluation (see Step 3.8)."*

**[P2.6]** `cg-reproducibility` · `scripts/link.ps1:172,182` / `scripts/update.ps1:363` — Unconditional `Set-Content` makes every `cg-link`/`cg-update` run dirty in git
**Why**: Both callers write the generated file unconditionally whenever the marker is present, regardless of whether the content changed. Every run modifies mtime, causing `git status` to report a changed file even when template and config are unchanged. This affects users who run `cg-update` as a CI pre-step or git hook.
**Fix**: Guard the write with a content equality check:
```powershell
$generated = New-CopilotInstructions -TemplateDir $CompoundGpidDir -ProjectRoot $ProjectRoot
if ($generated -ne $existingContent) {
    Set-Content -Path $CopilotInstructionsDest -Value $generated -Encoding UTF8
    Write-Host "  copilot-instructions.md - generated" -ForegroundColor DarkGray
} else {
    Write-Host "  copilot-instructions.md - up to date" -ForegroundColor DarkGray
}
```

**[P2.7]** `cg-reproducibility` · `scripts/helpers.ps1:101` — Marker joined with bare LF; produces mixed line endings when template has CRLF
**Why**: `return $marker + "`n" + $output`. On Windows, `Get-Content -Raw` preserves CRLF (checked-out by git with `core.autocrlf=true`). Joining with LF produces a file where line 1 ends with `LF` and all subsequent lines end with `CRLF`. This causes the file hash to differ between platforms and silently fails `.editorconfig` end-of-line rules.
**Fix**: Match the template's line-ending style:
```powershell
$sep = if ($output -match '\r\n') { "`r`n" } else { "`n" }
return $marker + $sep + $output
```

**[P2.8]** `cg-architecture` · `scripts/link.ps1:34` / `scripts/link.ps1:196` / `tests/link.Tests.ps1:547` — Three independent hardcoded copies of the managed-directory list
**Why**: `$ManagedDirs`, `$cgGitignoreEntries`, and the test's `$entries` literal are three separate hardcoded arrays that must be kept in sync manually. If a new managed directory is added, three edits are required, and the test cannot detect that `link.ps1`'s gitignore block drifted from its junction list.
**Fix**: In `link.ps1`, derive `$cgGitignoreEntries` from `$ManagedDirs`:
```powershell
$cgGitignoreEntries = @($ManagedDirs | ForEach-Object { ".github/$_/" }) +
                      @(".github/copilot-instructions.md")
```
Then update `link.Tests.ps1` to extract the list from `link.ps1` source rather than duplicating it (see P1.3 fix).

**[P2.9]** `cg-architecture` · `.github/prompts/cg-work.prompt.md:262-274` — Step 3.8 mixes charter body editing (a `/cg-strategy` concern) into `/cg-work`
**Why**: The roadmap bookkeeping (`@cg-roadmap` dispatch, milestone-complete notification) correctly belongs in `cg-work`. But the inline offer to propose new Current Focus text, archive old text to `charter-history.md`, and rewrite `compound-gpid.md` is charter management owned by `/cg-strategy`. This creates a lower-scrutiny path for modifying the protected charter body at a moment when the user's attention is on the code change just completed.
**Fix**: Trim Step 3.8 to its bookkeeping scope. Keep the `@cg-roadmap` dispatch and milestone notification. Replace the inline suggestion offer with a hard redirect:
> "🎉 Milestone complete. The charter's Current Focus may be stale. Run `/cg-strategy` to review direction."
Remove the inline Current Focus proposal, archival, and `compound-gpid.md` write logic from `cg-work` entirely.

**[P2.10]** `cg-data-quality` · `scripts/helpers.ps1:49` — No guard against empty template file; fails silently
**Why**: If `copilot-instructions.template.md` is a zero-byte or whitespace-only file (e.g., after a corrupted `git pull`), `$template` is `""`, all `.Replace()` calls are no-ops, and the function writes a file containing only the managed marker. No error is surfaced — VS Code Copilot gets no instructions, and the user has no indication of corruption.
**Fix**:
```powershell
$template = Get-Content $templatePath -Raw -Encoding UTF8
if ([string]::IsNullOrWhiteSpace($template)) {
    throw "Template file is empty: $templatePath. Installation may be corrupted -- run cg-update --fix."
}
```

**[P2.11]** `cg-data-quality` · `scripts/helpers.ps1:96-100` — Chained `.Replace()` allows placeholder cross-injection
**Why**: Each `.Replace()` operates on the already-modified `$output`. If a YAML value contains a downstream placeholder token — e.g., `project-name: "{{project-type}}"` — the first Replace injects that token, and the second Replace substitutes it with `$projectType`. The output silently contains the wrong field's value.
**Fix**: Validate extracted values before the replacement loop:
```powershell
foreach ($val in @($projectName, $projectType, $languages, $reviewDepth)) {
    if ($val -match '\{\{') {
        throw "A config value contains a placeholder token ('{{') which would corrupt the generated output. Check compound-gpid.md and compound-gpid.local.md."
    }
}
```

**[P2.12]** `cg-data-quality` · `scripts/helpers.ps1:43` — `$ProjectRoot` not validated as an existing directory
**Why**: `[Parameter(Mandatory)]` prevents omission but accepts an empty string or non-existent path without error. With `$ProjectRoot = ""`, `Join-Path "" "compound-gpid.md"` resolves to a CWD-relative bare filename, `Test-Path` returns `$false`, and all values silently fall back to `<not configured>` placeholders with no error.
**Fix**:
```powershell
if (-not (Test-Path -Path $ProjectRoot -PathType Container)) {
    throw "ProjectRoot does not exist or is not a directory: '$ProjectRoot'"
}
```

---

## P3 — MINOR (nice to have)

**[P3.1]** `cg-code-quality` · `scripts/update.ps1:363` — Implicit `PathInfo→string` coercion for `$ProjectRoot`
**Why**: `New-CopilotInstructions -ProjectRoot (Get-Location)` passes a `PathInfo` object to a `[string]` parameter. PS5.1 coerces via `.ToString()` today, but the explicit form is clearer.
**Fix**: `New-CopilotInstructions -TemplateDir $CompoundGpidDir -ProjectRoot (Get-Location).Path`

**[P3.2]** `cg-documentation` · `scripts/helpers.ps1:18` — Missing `.OUTPUTS` tag in comment-based help
**Why**: `Get-Help New-CopilotInstructions` shows a blank Outputs section. The function returns a `[string]` that callers must write with `Set-Content`.
**Fix**: Add after the last `.PARAMETER`:
```powershell
.OUTPUTS
    System.String
    Generated copilot-instructions.md content with the management marker
    prepended. Write with Set-Content — do not pipe directly into New-Item.
```

**[P3.3]** `cg-testing` / `cg-code-quality` · `tests/helpers.Tests.ps1:63` — Test setup and function call at Describe scope; setup errors cascade as opaque failures across all `It` blocks
**Why**: In Pester 3.4, code at `Describe` scope runs during test collection. If `New-CopilotInstructions` throws (e.g., bad encoding, missing template), every `It` in that block fails with a confusing null-reference message rather than a clear setup-failure message. This affects all six Describe blocks.
**Fix**: Add a guard `It` as the first item in each `Context`:
```powershell
It "New-CopilotInstructions setup succeeded (guard)" {
    $result | Should Not BeNullOrEmpty
}
```

**[P3.4]** `cg-testing` · `tests/helpers.Tests.ps1:173` — "fallback when local config missing" Describe only asserts `project-type` fallback; `languages` and `review-depth` fallbacks not separately covered
**Why**: The single assertion `($result -match '<not configured>')` passes as long as the string appears once — it doesn't guarantee all three fields fell back.
**Fix**: Add assertions for all three fallback fields, or assert count: `([regex]::Matches($result, [regex]::Escape('<not configured>')).Count) | Should Be 3`

**[P3.5]** `cg-testing` · `tests/helpers.Tests.ps1:91` — Missing test: no dialect annotation in the basic case (r-syntax not set)
**Why**: The basic-generation Describe never asserts `(R dialect:` is absent when r-syntax is not configured. If the dialect guard were accidentally removed, basic tests would still pass.
**Fix**: Add to "placeholder substitution" Context:
```powershell
It "does not append R dialect annotation when r-syntax is not configured" {
    ($result -match '\(R dialect:') | Should Be $false
}
```

**[P3.6]** `cg-documentation` · `.github/prompts/cg-setup.prompt.md:132` — Non-sequential step numbering; A3.6 and A3.8 are phantom gaps
**Why**: The file uses `.5`-increment decimals throughout. New steps A3.7 and A3.9 skip A3.6 and A3.8, inconsistent with the established convention.
**Fix**: Renumber A3.7 → A3.6 and A3.9 → A3.7.

**[P3.7]** `cg-documentation` · `.github/copilot-instructions.template.md:1` — Template file has no header comment identifying it as a source template
**Why**: The file opens with `# Project Instructions` — identical to the generated output. A developer who opens it cold has no indication it is a template, that `{{placeholders}}` are filled by `New-CopilotInstructions`, or which script to run to regenerate the output.
**Fix**: Prepend an HTML comment (invisible in rendered Markdown):
```html
<!-- TEMPLATE FILE — managed by New-CopilotInstructions in scripts/helpers.ps1.
     Placeholders: {{project-name}}, {{project-type}}, {{languages}}, {{review-depth}}.
     Do not edit .github/copilot-instructions.md directly; run `cg-update` to regenerate. -->
```

**[P3.8]** `cg-documentation` · `.github/prompts/cg-setup.prompt.md:260` — B4.7 silently discards workspace folder descriptions when `compound-gpid.context.md` does not exist
**Why**: B4.7 appends folder descriptions "if `compound-gpid.context.md` exists" but gives no instruction for the case where the user provided descriptions yet the file is absent (declined at B1.1.3). The information is silently lost.
**Fix**: Add an else branch: *"If context.md does not exist, note: 'Folder descriptions cannot be saved — no `compound-gpid.context.md` exists. Re-run `/cg-setup` and choose to create it.'"*

**[P3.9]** `cg-reproducibility` · `scripts/link.ps1:62` — `$env:CG_INTERNAL_CALL` may persist if the process is killed between set and `finally`
**Why**: `link.ps1` sets `$env:CG_INTERNAL_CALL = "1"` before calling `update.ps1` and clears it in a `finally` block. `finally` runs on `Ctrl+C` but not on `taskkill /F` or terminal force-close. A hard-killed process leaves the var set, silently suppressing copilot-instructions.md refresh on all subsequent `cg-update` calls in that terminal session.
**Fix**: Document the workaround in `docs/troubleshooting.md`: *"If `cg-update` silently skips refreshing `copilot-instructions.md`, open a new terminal — a stale `$env:CG_INTERNAL_CALL` from an interrupted `cg-link` may be suppressing the refresh."*

**[P3.10]** `cg-architecture` · `.github/prompts/cg-setup.prompt.md:12` — "already loaded" claim for `setup-templates.md` conflicts with its own "loaded on-demand" header
**Why**: `setup-templates.md` begins with "Loaded on-demand — do not bulk-load at prompt start." `cg-setup.prompt.md` refers to it as "(already loaded)" when referencing the template in steps A3.7 and B1.1.3. These contradict each other; an agent that hasn't yet read the file will silently generate context.md from its own knowledge rather than the canonical template.
**Fix**: Replace "(already loaded)" with: "(read it now with `read_file` if not already in context)".

**[P3.11]** `cg-architecture` · `.github/prompts/cg-setup.prompt.md:137` — Step A3.7 creates `compound-gpid.context.md` without an overwrite guard; B1.1.3 is correctly idempotent
**Why**: Path A (new project setup) at A3.7 has no existence check. If a user clones a project with an existing `context.md` and re-runs setup, A3.7 silently overwrites accumulated institutional knowledge. B1.1.3 correctly skips if the file exists; A3.7 should too.
**Fix**: Add: *"If `compound-gpid.context.md` already exists, skip this step."*

**[P3.12]** `cg-data-quality` · `scripts/helpers.ps1:57,74` — Frontmatter regex uses `\s*` (matches tabs) where `[ \t]*` is the correct intent
**Why**: `^---\s*\r?\n` also matches `---\t\n` (embedded tab) as a valid frontmatter delimiter. This is not valid YAML front matter.
**Fix**: Tighten both frontmatter patterns: `'(?s)^---[ \t]*\r?\n(.*?)\r?\n---'`

**[P3.13]** `cg-version-control` · `feat/context-layer` — Branch mixes context-layer and pester-safety features
**Why**: The branch contains (1) `New-CopilotInstructions` + template system (context-layer) and (2) Pester crash prevention work visible in `tests/prompt-tools.Tests.ps1` (+280 lines) and `tests/ps51-compat.Tests.ps1`. These have different reviewers and different rollback risk. A revert of pester-safety would also revert context-layer.
**Fix**: If both features are complete, document both in the PR description. If either is still in flux, consider a second branch to keep them separable.

**[P3.14]** `cg-version-control` · `feat/context-layer` — Branch name understates scope
**Why**: The branch name implies only context-layer work but contains substantial pester-safety test additions.
**Fix**: No action required if merging soon. Document both features in the PR title and description.

---

## ✅ Passed — No issues found

- **cg-performance**: No algorithmic or I/O issues. `New-CopilotInstructions` performs a handful of small file reads and four in-memory string replacements — negligible for a developer CLI tool.
- **Secrets**: No credentials, API keys, tokens, or PII in any changed file.
- **Commit message format**: All existing commits follow conventional commits format. ✓
- **`New-CopilotInstructions` design**: Well-placed in `helpers.ps1`; `.Replace()` (not `-replace`) correctly avoids regex backreference corruption; `{{double-curly}}` placeholder syntax is unambiguous and consistent.
- **`compound-gpid.context.md` lifecycle**: Creation (cg-setup), reading (all prompt Step 0s), write (cg-compound) are clearly defined and non-overlapping. ✓
- **Template file committed correctly**: `copilot-instructions.template.md` is a source file for the tool — correct to commit, no `.gitignore` entry needed. ✓
