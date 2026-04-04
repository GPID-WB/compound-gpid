## Review Report

**Review depth**: light
**Files reviewed**: 11 (`.github/agents/cg-roadmap.agent.md`, `.github/copilot-instructions.md`,
`.github/prompts/cg-resume.prompt.md`, `.github/prompts/cg-setup.prompt.md`,
`.github/prompts/cg-strategy.prompt.md`, `docs/installation.md`, `docs/reference.md`,
`docs/workflow.md`, `tests/charter.Tests.ps1`, `tests/prompt-tools.Tests.ps1`,
`tests/roadmap.Tests.ps1`)
**Findings**: 0 P1, 6 P2, 5 P3

> **Context**: Light review run on 2026-04-02 to verify fixes from
> `2026-04-01-cg-strategy-and-roadmap-fix-review.md`. A `docs/installation.md` typo
> ("sstructure") detected in the diff was already corrected before this review ran.

---

### P1 — CRITICAL (must fix before merge)

_(none — the "sstructure" typo in `docs/installation.md` was already fixed)_

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `.github/copilot-instructions.md`:26 — Broken cross-reference: "The full archiving procedure is in `/cg-strategy`."
  **Why**: `cg-strategy.prompt.md`'s File Permissions block explicitly restricts writes to `.cg-docs/strategy/` and `roadmap.json`; it does not contain any charter-archiving procedure. A user following this reference finds nothing.
  **Fix**: Either add the archiving procedure to `cg-strategy.prompt.md` (e.g., as a note in Step 4) or change the reference to wherever the procedure actually lives. If the procedure is intended to live in `cg-strategy.prompt.md`, add it there. Suggested text to add in `cg-strategy.prompt.md` under "File Permissions":
  > **Charter archiving**: If `Current Focus` is updated, never delete existing content. Archive removed sections to `.cg-docs/archive/charter-history.md` (create the directory if it doesn't exist) before editing `compound-gpid.md`.

- **[P2.2]** [cg-code-quality + cg-testing] `tests/roadmap.Tests.ps1`:~829–871 — New `Describe "Test-RecentStrategyDocument helper"` block uses `Should Be` (Pester 3 legacy) throughout; all other assertions in the file use `Should -Be` (Pester 5).
  **Why**: The file header documents Pester 5 compatibility. Legacy syntax emits deprecation warnings in Pester 5 and will break under strict mode.
  **Fix**: Replace all `| Should Be $true` / `| Should Be $false` in the new block with `| Should -Be $true` / `| Should -Be $false`.

- **[P2.3]** [cg-code-quality] `tests/roadmap.Tests.ps1`:~811 — `[datetime]::ParseExact($match.Value, 'yyyy-MM-dd', $null)` uses `$null` as the culture provider.
  **Why**: `$null` resolves to the current thread culture, which varies by system locale. On non-Gregorian calendar locales, `ParseExact` can fail or parse unexpectedly. The project runs on World Bank machines with mixed locales.
  **Fix**:
  ```powershell
  $fileDate = [datetime]::ParseExact($match.Value, 'yyyy-MM-dd', [System.Globalization.CultureInfo]::InvariantCulture)
  ```

- **[P2.4]** [cg-testing] `tests/roadmap.Tests.ps1` — The 60-day inclusive boundary is not tested; the `$ReferenceDate` injection parameter is never used in any test.
  **Why**: The function returns `$true` when `$fileDate -ge $cutoff` (i.e., exactly 60 days old is accepted). Only −61 days (false) and −30 days (true) are verified. The `$ReferenceDate` parameter exists precisely for deterministic boundary testing but is unused.
  **Fix**: Add a boundary test with a fixed reference date:
  ```powershell
  It "returns true when a file is exactly 60 days old (inclusive boundary)" {
      New-Item -ItemType Directory -Path $tmpDir | Out-Null
      $ref = [datetime]"2026-01-01"
      $boundaryDate = $ref.AddDays(-60).ToString("yyyy-MM-dd")
      New-Item -ItemType File -Path (Join-Path $tmpDir "$boundaryDate-session.md") | Out-Null
      Test-RecentStrategyDocument $tmpDir -ReferenceDate $ref | Should -Be $true
  }
  ```
  Also update remaining 7 tests to pass `-ReferenceDate` explicitly for clock-independent execution.

- **[P2.5]** [cg-testing] `tests/prompt-tools.Tests.ps1` — `copilot-instructions.md` Workflow Entry Points tests match against the entire file content, not the specific section; four commands are missing.
  **Why**: `$content -match '/cg-strategy'` passes if the string appears *anywhere* — frontmatter, inline examples, other prose — not necessarily inside the Workflow Entry Points table. Currently missing: `/cg-work`, `/cg-review`, `/cg-fix-triage`, `/cg-compound`.
  **Fix**: Scope content to the section before matching:
  ```powershell
  $section = if ($content -match '(?s)(## Workflow Entry Points.*?)(\n## |\z)') { $Matches[1] } else { "" }
  ```
  Then assert against `$section`, and add `It` blocks for the four missing commands.

- **[P2.6]** [cg-code-quality] `.github/prompts/cg-resume.prompt.md`:~170 — Pre-existing double emoji `📋💡` in "### 📋💡 Decided Brainstorms Without a Plan" heading.
  **Why**: The `📋` (clipboard) is a copy-paste artifact from the "Pending Review Findings" heading immediately above. All other template headings use a single emoji; the clipboard has no semantic meaning in a brainstorm context.
  **Fix**: Remove the leading `📋`; keep `### 💡 Decided Brainstorms Without a Plan (<count>)`.

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `docs/workflow.md`:~8–11 — Loop diagram: `Resume` is visually attached to the `Strategy` entry arc, implying it re-enters at `Strategy` specifically.
  **Why**: `Resume` is documented as a re-entry at any stage, not only at `Strategy`. The new layout loses the independent `^` arrows from the old diagram.
  **Fix**: Add separate connectors:
  ```
  Setup -> Strategy -> Brainstorm -> Plan -> Work -> Review -> Fix Triage -> Compound -> Release
                ^             ^                                    ^
       (vision/rethink)   (one task)                            Fix Bug
  Resume (re-entry at any stage)
  ```

- **[P3.2]** [cg-code-quality + cg-testing] `tests/charter.Tests.ps1`:~157 — `doesn'?t exist` branch in `"create.*directory|create.*dir|doesn'?t exist"` is too broad.
  **Why**: Without a `create.*` prefix anchor, any sentence in the file containing "doesn't exist" satisfies the regex, including unrelated guards like "If the gitignore doesn't exist, skip it."
  **Fix**: Drop the third alternative — `create.*directory` already matches the actual text:
  ```powershell
  ($content -match "create.*directory|create.*dir") | Should Be $true
  ```

- **[P3.3]** [cg-code-quality] `tests/roadmap.Tests.ps1`:~815 — Bare `catch { }` silently suppresses all `[datetime]::ParseExact` failures.
  **Why**: Project coding standard: "Never silently swallow errors." Files with malformed date prefixes are dropped with no diagnostic signal.
  **Fix**:
  ```powershell
  } catch {
      Write-Verbose "Skipping '$($f.Name)': not a valid date prefix"
  }
  ```

- **[P3.4]** [cg-testing] `tests/roadmap.Tests.ps1` — "returns false when only file is .gitkeep" test exercises the `-Filter "*.md"` upstream filter, not the explicit `Where-Object { $_.Name -ne ".gitkeep" }` guard (`.gitkeep` has no `.md` extension and is excluded before the guard runs).
  **Why**: The test title promises it validates the explicit guard, but the guard is dead for this input. False confidence about coverage.
  **Fix**: Either rename to "returns false when directory contains only non-.md files", or add a `*.md`-named file to actually exercise the guard (e.g., `something.gitkeep.md`).

- **[P3.5]** [cg-testing] `tests/roadmap.Tests.ps1` — No test for a `.md` file whose name lacks a `yyyy-MM-dd` prefix.
  **Why**: The function silently skips such files (`$match.Success` is false). This documented skip behaviour could regress if the regex is tightened, and no test would catch it.
  **Fix**:
  ```powershell
  It "ignores .md files without a date prefix" {
      New-Item -ItemType Directory -Path $tmpDir | Out-Null
      New-Item -ItemType File -Path (Join-Path $tmpDir "session-notes.md") | Out-Null
      Test-RecentStrategyDocument $tmpDir | Should -Be $false
  }
  ```

---

### ✅ Passed

- cg-code-quality: All YAML frontmatter is well-formed; `description:` and `model:` present in all changed prompts and agents
- cg-code-quality: `@cg-roadmap` model correctly updated to Haiku 4.5 in both `cg-roadmap.agent.md` and `docs/reference.md` — in sync
- cg-code-quality: `cg-strategy.prompt.md` has no `tools:` frontmatter key — file permissions are prose-only per convention (correct, matches test expectation)
- cg-code-quality: Workflow Entry Points table in `copilot-instructions.md` is correctly formatted
- cg-code-quality: `cg-setup.prompt.md` scaffold now includes `reviews/` and `strategy/` under `.cg-docs/`
- cg-code-quality: No DRY violations; each file owns its authoritative content
- cg-code-quality: `docs/installation.md` typo ("sstructure") already corrected before this review
- cg-testing: `AfterEach` cleanup with GUID temp directory ensures test isolation in `roadmap.Tests.ps1`
- cg-testing: `cg-strategy.prompt.md` test set (existence, frontmatter, no-tools) mirrors established patterns for other prompts
- cg-testing: `charter.Tests.ps1` uses `""` fallback for missing file — no null-dereference risk
- cg-testing: `charter.Tests.ps1` path separator regex `[/\\]` correctly handles cross-platform paths
- cg-testing: `Test-RecentStrategyDocument` function has complete PowerShell doc comments
