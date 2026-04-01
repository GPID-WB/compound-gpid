# Review Report: Charter Maintenance (2026-04-01)

**Status**: Fixed 19/20 findings (2026-04-01 via `/cg-fix-triage`)  
**Skipped**: P3.5 — `.cg-docs/` plan file write restricted in fix-triage  
**Branch**: `feat/charter-maintenance`

**Review depth**: thorough  
**Files reviewed**: 4 modified, 2 new untracked  
**Agents**: cg-code-quality, cg-testing, cg-documentation, cg-version-control, cg-reproducibility, cg-performance, cg-architecture, cg-data-quality, cg-learnings-researcher  
**Findings**: 1 P1, 13 P2, 6 P3

---

## P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-testing] `compound-gpid.md`:L1–5 — `last-reviewed` frontmatter field missing from this project's own charter  
  **Why**: Step 2f in `/cg-resume` treats a missing `last-reviewed` as stale and fires the nudge on every session — indefinitely. The project that dogfoods the plugin won't get accurate staleness tracking until this field is added.  
  **Fix**: Add `last-reviewed: "2026-04-01"` to the YAML frontmatter block in `compound-gpid.md`.

---

## P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-documentation + cg-reproducibility] `.github/prompts/cg-resume.prompt.md`:L121 vs `docs/workflow.md`:L26 — Threshold inconsistency: "more than 30 days" vs "30+ days"  
  **Why**: "more than 30 days" means >30 (nudge fires at day 31+). "30+ days" means ≥30 (fires at day 30). At exactly 30 days: the implementation stays silent, but the docs imply a nudge. These are semantically different.  
  **Fix**: Standardize both to "more than 30 days ago" (matching the implementation). Change `docs/workflow.md` line 26 from "30+ days" to "more than 30 days".

- **[P2.2]** [cg-architecture + cg-documentation] `docs/workflow.md`:L25 — Archive behavior documented as present, but not yet implemented  
  **Why**: The callout says "When content is removed, it is archived to `.cg-docs/archive/charter-history.md` automatically." No prompt currently performs this write — Task 3 (the rule in `copilot-instructions.md`) is explicitly deferred. Users who remove charter content will find no archive entry.  
  **Fix**: Qualify: "...will be archived to `.cg-docs/archive/charter-history.md` (enabled in a future release)." Or omit the sentence until Task 3 lands.

- **[P2.3]** [cg-architecture] `.github/prompts/cg-setup.prompt.md` + `.github/prompts/cg-resume.prompt.md` — `last-reviewed` has no update path after initial creation  
  **Why**: `cg-setup` Mode A writes `last-reviewed` once on charter creation. No other prompt updates it. After 30 days, the nudge fires on every `/cg-resume` session — even for users actively maintaining their charter — until Task 3 lands. The warning becomes noise and will be ignored.  
  **Fix (minimal, no Task 3 required)**: In `cg-setup` Mode B, when the user confirms or approves a charter change, also update `last-reviewed`. Alternatively, add a one-line instruction to `cg-resume` Step 3: "If you updated the charter today, also update `last-reviewed` to today's date."

- **[P2.4]** [cg-code-quality + cg-documentation] `.github/prompts/cg-setup.prompt.md` — Mode B: no migration path for existing 6-section charters  
  **Why**: Mode B reads the existing charter but doesn't detect or handle charters that still have the deprecated Architecture Notes, Roadmap, or Related Resources sections. Returning users get no guidance to migrate. Old sections persist silently.  
  **Fix**: At Mode B Step B1.1, after reading the charter, check for sections beyond the four canonical ones. If found, surface: "Your charter has sections beyond the new 4-section standard. Would you like guidance on migrating them?" Then offer destinations: `copilot-instructions.md`, `.cg-docs/brainstorms/`, or `.cg-docs/archive/charter-history.md`.

- **[P2.5]** [cg-data-quality] `.github/prompts/cg-resume.prompt.md`:L121 — Future `last-reviewed` date silently suppresses the staleness nudge  
  **Why**: A date in the future is not "missing" and is not ">30 days ago" — it passes the check silently, disabling the nudge indefinitely. An accidental future date (fat-finger on year, or a placeholder) would permanently suppress warnings with no visible indicator.  
  **Fix**: Add a third branch: if the computed delta is negative (future date), treat as malformed and fire the nudge: "⚠️ **Charter review due**: `last-reviewed` is set to a future date (`<value>`). Treating as unreviewed."

- **[P2.6]** [cg-data-quality] `.github/prompts/cg-resume.prompt.md`:L120 — Malformed date not explicitly handled  
  **Why**: The instruction to "compute the number of days between that date and today" gives no fallback if the value is not a valid ISO date (e.g., `"April 2026"`, `"done"`, `"2026/01/15"`). An LLM may treat a failed parse as zero days, suppressing the nudge — the opposite of the intended behavior.  
  **Fix**: Add: "If the value cannot be parsed as a valid `YYYY-MM-DD` date, treat it as missing and surface the nudge."

- **[P2.7]** [cg-version-control] `.cg-docs/archive/` + `.cg-docs/plans/2026-04-01-charter-maintenance.md` — Untracked institutional knowledge files  
  **Why**: Both items show `??` in git status — untracked. The project constraint states "the entire `.cg-docs/` directory must be version-controlled." These are institutional knowledge artifacts that could be lost.  
  **Fix**: `git add .cg-docs/archive/.gitkeep .cg-docs/plans/2026-04-01-charter-maintenance.md`

- **[P2.8]** [cg-version-control] Working directly on `main` — branching policy violation  
  **Why**: `copilot-instructions.md` requires feature branches: "Use feature branches off `main`. Name them `type/short-description`." This work is on `main` directly.  
  **Fix**: For this changeset, use a branch: `feat/charter-maintenance`. Suggested commit message: `feat(charter): add staleness check, 4-section rule, and archive scaffold`

- **[P2.9]** [cg-documentation] `docs/reference.md`:L136 — `last-reviewed` frontmatter field not documented  
  **Why**: The directory tree comment for `compound-gpid.md` now mentions 4 sections but doesn't document the YAML frontmatter fields (`project-name`, `team`, `created`, `last-reviewed`). Users won't know what fields to maintain.  
  **Fix**: Expand the comment: "Project charter (4 sections: Objective, Key Deliverables, Constraints, Current Focus). YAML frontmatter: `project-name`, `team`, `created`, `last-reviewed`. Committed — shared."

- **[P2.10]** [cg-documentation] `docs/reference.md` / `docs/workflow.md` — Archive file format not documented  
  **Why**: Both files mention archiving to `.cg-docs/archive/charter-history.md` but neither documents the file format (section structure, date stamp format). The format is defined in the plan (Task 3) but that's not user-facing.  
  **Fix**: Add to `docs/reference.md` an "Archive File Format" note: sections headed `## Archived YYYY-MM-DD`, sub-label `**Removed from**: <section name>`, then removed content.

- **[P2.11]** [cg-code-quality] `.github/prompts/cg-setup.prompt.md` — Mode B missing `last-reviewed` update instruction  
  **Why**: Mode A Step A3.5 explicitly sets `last-reviewed` to today. Mode B has no corresponding step, so users who update their charter via `/cg-setup` Mode B won't reset the staleness clock.  
  **Fix**: Add a step in Mode B: "After updating any charter content, update `last-reviewed` to today's date."

- **[P2.12]** [cg-testing] New test: `compound-gpid.md` frontmatter and 4-section validation  
  **Why**: The staleness check depends on `last-reviewed` being present and valid. The 4-section rule is a new structural constraint. No Pester tests validate these. A regression (e.g., someone adding a 5th section) would go undetected.  
  **Fix**: Create `tests/charter.Tests.ps1` with tests for: `last-reviewed` present and `YYYY-MM-DD` format; exactly 4 section headings; no deprecated section headings (Architecture Notes, Roadmap, Related Resources).

- **[P2.13]** [cg-testing] Missing test: `.cg-docs/archive/` scaffold in install/setup  
  **Why**: The setup prompt now scaffolds `.cg-docs/archive/.gitkeep` but no existing test validates this. A future edit removing the scaffold step would go undetected.  
  **Fix**: Add to `tests/install.Tests.ps1` (or a new integration test): "`.cg-docs/archive/` is created with `.gitkeep` on new project setup."

---

## P3 — MINOR (nice to have)

- **[P3.1]** [cg-architecture] `.github/prompts/cg-resume.prompt.md`:Step 3 — Staleness warning not anchored in the Step 3 output block  
  **Why**: Step 2f fires the warning before Step 3's structured summary. If the LLM batches output, the warning may appear detached from the summary. Step 3 has 4 defined output sections; the warning is floating above.  
  **Fix**: Add a `### ⚠️ Maintenance Nudges` block to the Step 3 output template where the 2f warning (and future nudges) are collected.

- **[P3.2]** [cg-architecture + cg-reproducibility] `.github/prompts/cg-setup.prompt.md`:L157 — `team` field hardcoded, not portable  
  **Why**: `team: "DECDG / GPID -- World Bank"` is baked into the template. Other teams adopting the plugin will get the wrong team name silently.  
  **Fix**: Add as optional Question 3.5 in Mode A, pre-populated with the DECDG value as default. Most current users press Enter; other teams can override.

- **[P3.3]** [cg-code-quality] DRY: 4-section rule repeated across 3 files  
  **Why**: The instruction "charter has exactly 4 sections, content that doesn't fit belongs elsewhere" appears in cg-setup (full), workflow.md (abbreviated), and reference.md (implicit). Not harmful but slightly inconsistent in detail level.  
  **Fix**: cg-setup is the authoritative source (correct). In workflow.md, append "See `/cg-setup` for where non-charter content belongs." Low priority.

- **[P3.4]** [cg-code-quality] `docs/reference.md` — Archive directory comment is vague  
  **Why**: Comment says "Archived charter content (never loaded at session start)" but doesn't clarify what "never loaded" means or whether it's one file or many.  
  **Fix**: Tighten to: "Archived charter sections removed by the user (not loaded at session start)."

- **[P3.5]** [cg-reproducibility] `.cg-docs/plans/2026-04-01-charter-maintenance.md`:L157 — Em-dash in plan template vs double-dash in implementation  
  **Why**: Task 1 in the plan shows `team: "DECDG / GPID — World Bank"` (em-dash U+2014) but the actual cg-setup template correctly uses `team: "DECDG / GPID -- World Bank"` (double-dash). The plan is a `.md` file and not PS 5.1 sensitive, but the inconsistency is confusing.  
  **Fix**: Update the plan's template example to use `--` to match the implementation.

- **[P3.6]** [cg-performance] `.github/prompts/cg-resume.prompt.md`:L121 — Staleness check phrasing could be tighter  
  **Why**: "Compute the number of days between that date and today. If... more than 30 days ago" is two sentences with a redundant instruction. A model without date context could over-reason.  
  **Fix**: Collapse to one conditional: "If `last-reviewed` is missing, or is a date more than 30 days before today's date, surface a nudge:"

---

## ✅ Passed

- **cg-code-quality**: `last-reviewed` field name consistent (hyphenated) across all files; section capitalization consistent; archive path consistent; charter section names consistent
- **cg-testing**: PS 5.1 compat — `--` in team field is ASCII-safe; existing `ps51-compat.Tests.ps1` scope is correct (`.ps1` only)
- **cg-performance**: Step 2f is a free read (cg-resume already reads `compound-gpid.md` in Step 0); charter template reduction (3 sections removed) is a net token savings
- **cg-reproducibility**: `YYYY-MM-DD` date format is unambiguously specified; archive `.gitkeep` ensures directory tracking; date computation is deterministic given the VS Code session date injection
- **cg-data-quality**: Missing `last-reviewed` (null) handled correctly — nudge fires; no-frontmatter case falls into null branch; YAML quoting guard present; overwrite guard present
- **cg-architecture**: Placement of staleness check in cg-resume (not task prompts) is correct; archive directory scaffolded before enforcement; 4-section comment embedded in template output is the right placement
- **cg-learnings-researcher**: No contradictions with past decisions; remove-then-rewrite pattern (2026-03-04) supports future archive-write implementation; `.cg-docs/` gitignore strategy confirmed correct
- **cg-data-quality**: `--` in YAML string is valid and parses correctly; no issue

---

## Light Follow-Up Review (2026-04-01 post-commit)

> Note: Resolves P2.12 and P2.13 from the thorough review above — `tests/charter.Tests.ps1` was created. This light review covers the committed test file and prompt changes.

**Review depth**: light
**Files reviewed**: 9 (commit `5f6b456` on `feat/charter-maintenance`)
**Agents**: cg-code-quality, cg-testing
**Findings**: 0 P1, 1 P2, 3 P3

### P1 — CRITICAL

None.

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-testing] `tests/charter.Tests.ps1:69` — False negative in "last-reviewed is not set to a future date" test
  **Why**: The `if ($match.Success)` guard without a prior assertion means the test silently passes when `last-reviewed` is missing or malformed — the exact condition it was designed to catch.
  **Fix**:
  ```powershell
  It "last-reviewed is not set to a future date" {
      $match = [regex]::Match($yamlBlock, 'last-reviewed\s*:\s*"?(\d{4}-\d{2}-\d{2})"?')
      $match.Success | Should Be $true
      $dateValue = $match.Groups[1].Value
      $today     = Get-Date -Format 'yyyy-MM-dd'
      ($dateValue -le $today) | Should Be $true
  }
  ```

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `tests/charter.Tests.ps1:105` — `.Count` on `Where-Object` output without `@()` wrap
  **Why**: In PS 5.1, if `Where-Object` returns `$null` (no matches), `.Count` may not evaluate as expected.
  **Fix**: `$sectionCount = @($body -split '\r?\n' | Where-Object { $_ -match '^## \S' }).Count`

- **[P3.2]** [cg-testing] `tests/charter.Tests.ps1:105` — Section count regex requires exactly one space after `##`
  **Why**: `'^## \S'` fails on `'##  Title'` (two spaces). Standard Markdown allows any whitespace after the `##` marker.
  **Fix**: Use `'^##\s+\S'` to allow one or more spaces.

- **[P3.3]** [cg-testing] `tests/charter.Tests.ps1:47` — YAML `last-reviewed` regex doesn't handle single-quoted values
  **Why**: `'last-reviewed\s*:\s*"?(\d{4}-\d{2}-\d{2})"?'` misses `last-reviewed: '2026-04-01'`, silently returning `$match.Success = $false`.
  **Fix**: `'last-reviewed\s*:\s*["\x27]?(\d{4}-\d{2}-\d{2})["\x27]?'` — or document that only double-quotes and bare values are supported (no single quotes).

### ✅ Passed

- **cg-code-quality**: PS 5.1 compatibility (`Should Be` syntax), ASCII-only content, naming conventions, DRY, logic correctness in prompts — all clean
- **cg-testing**: Test isolation, naming clarity, canonical path coverage, `.cg-docs/archive/` scaffold test — all good
