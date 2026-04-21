---
plan: .cg-docs/plans/2026-04-20-prompt-prose-compression.md
findings:
  P1.1: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: skipped
  P3.1: fixed
  P3.2: skipped
  P3.3: skipped
  P3.4: fixed
  P3.5: skipped
  P3.6: fixed
  P3.7: fixed
  P3.8: fixed
  P3.9: fixed
  P3.10: fixed
  P3.11: skipped
  P3.12: fixed
  P3.13: fixed
  P3.14: fixed
  P3.15: fixed
  P3.16: skipped
---

## Review Report

**Review depth**: standard (auto-escalated from `light` — ~1,540 non-test lines changed across 20 files)
**Files reviewed**: 20 staged files
**Findings**: 25 (P0: 0, P1: 1, P2: 8, P3: 16)

> Note: This is a follow-up verification review of the P3 fix-triage pass and the `/cg-compound` session. Two prior reviews cover the same changeset: `2026-04-20-prompt-prose-compression-review.md` and `2026-04-20-prompt-prose-compression-review-2.md`.

---

### P0 — BLOCKING

None.

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-reproducibility / cg-architecture] `.github/prompts/cg-fix-triage.prompt.md:Step 0.5` — Step 0.5 is placed before Step 1 in document order but specifies execution after Step 1.3
  **Why**: Sequential-reading models will attempt to load language skills at Step 0.5 with no findings context yet loaded. The body says "After Step 1.3 identifies which file types appear in findings…" — a forward dependency with no deferral instruction. The `--migrate` guard fires correctly (flag is visible at invocation), but non-migrate invocations may load skills prematurely (before findings are parsed), producing session-to-session variance.
  **Fix**: Add `<!-- Execute AFTER Step 1.3 — do not load skills before findings are parsed. -->` immediately before the step header, and add to the opening line: "(Deferred: execute after Step 1.3 completes. The `--migrate` flag is visible at invocation time — no need to wait for Step 2.)"

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality / cg-testing] `tests/helpers.ps1:20` — `Get-ToolsList` does not guard against multiple-match result from `Where-Object`
  **Why**: `Where-Object` returns a `PSObject[]`. `[regex]::Matches($line, …)` on an array coerces via `.ToString()` (space-joined), producing incorrect merged tokens rather than failing. Duplicate `tools:` keys in malformed frontmatter silently produce wrong results.
  **Fix**: Add `| Select-Object -First 1` after the `Where-Object`:
  ```powershell
  $line = ($Frontmatter -split '\r?\n' | Where-Object { $_ -match '^\s*tools:' } | Select-Object -First 1)
  ```

- **[P2.2]** [cg-testing] `tests/helpers.ps1:18` — `Get-ToolsList` has no unit tests
  **Why**: `Get-ToolsList` drives the "Agent files - tools restriction enforcement" assertions. If it silently returns `@()` for any agent (e.g., due to a YAML multiline tools syntax), the write-capability safety assertion passes regardless, creating false-negative coverage.
  **Fix**: Add a `Describe "Get-ToolsList helper - edge cases"` block covering: empty string → `@()`, no `tools:` key → `@()`, inline array → correct tokens, comment-prefixed `# tools: foo` → no match.

- **[P2.3]** [cg-reproducibility] `.github/prompts/cg-review.prompt.md:144` Step 3.5 — Missing mtime fallback in plan-selection sort rule
  **Why**: `cg-work` Step 1 and `cg-plan` Step 0.5 implement the full three-step rule: `date:` → mtime → alpha. `cg-review` Step 3.5 specifies only `date:` → alpha-last, omitting the mtime fallback. On repos containing plans without a `date:` field, `cg-review` cannot rank undated plans, making selection non-deterministic. `compound-gpid.context.md` documents the three-step rule as canonical — but `cg-review` doesn't fully implement it.
  **Fix**: Change Step 3.5 to: "by `date:` field; if `date:` is absent, fall back to last-write time; if tied, prefer the alphabetically last filename."

- **[P2.4]** [cg-reproducibility] `.github/prompts/cg-fix-triage.prompt.md:79` — Full-suite regression gate missing `Test-Path` guard on `last-run.json`
  **Why**: The per-finding partial-run query correctly wraps the `ConvertFrom-Json` call with `if (-not (Test-Path tests\last-run.json))`. The full-suite gate at the end of Step 3 does not. If `Run-Tests.ps1` exits without writing `last-run.json` (e.g., execution-policy failure), the subagent returns an error string that the model may interpret as "tests passed," silently masking regressions.
  **Fix**: Wrap the full-suite gate read: `if (-not (Test-Path tests\last-run.json)) { Write-Output 'last-run.json not found — run tests first' } else { Get-Content tests\last-run.json | ConvertFrom-Json | Select-Object passed, failedCount, failures, filteredFiles }`.

- **[P2.5]** [cg-architecture] `roadmap.json:~65` — `fix-triage-migrate-mode` feature linked to mismatched plan
  **Why**: `"plan": ".cg-docs/plans/2026-04-20-prompt-prose-compression.md"` is a prose-compression plan — not a migration-mode implementation plan. `/cg-resume` and `/cg-ideate` surface feature→plan pairings to derive project state; this pairing misrepresents what was built. Two features in two milestones now point at the same plan file.
  **Fix**: Either (a) set `"plan": null` (acceptable — the migrate feature was a byproduct), or (b) create a stub plan `2026-04-20-fix-triage-migrate.md` and link to it.

- **[P2.6]** [cg-performance] `compound-gpid.context.md:10–17` — Both context file conventions duplicate inline prompt instructions
  **Why**: The "plan selection sort key" and "skill loading" bullets are verbatim-equivalent to inline text already in `cg-plan`, `cg-work`, `cg-fix-triage`, and `cg-review`. The context file is loaded in Step 0 of **every** invocation — including `cg-review` and `cg-brainstorm`, which have no plan-selection step — adding ~10 lines of noise per session across the highest-frequency workflows.
  **Fix**: Remove both bullets from `compound-gpid.context.md`. Reserve the conventions section for facts that are **not already stated** in the prompts that act on them. (If retained for discoverability, at minimum add `cg-review` to the plan-sort-key list — see P3.5.)

- **[P2.7]** [cg-testing] `tests/prompt-tools.Tests.ps1:303` — P3.7 test name promises recognized-options list but body only checks for "Unrecognized argument"
  **Why**: "warns on unrecognized arguments with recognized options list" claims two properties. The body only tests `'Unrecognized argument'` — the options-enumeration half of the contract is unchecked.
  **Fix**: Extend pattern: `($content -match 'Unrecognized argument') -and ($content -match '--migrate') | Should Be $true` (using `--migrate` as proxy for the options list being present).

- **[P2.8]** [cg-version-control] `(staged set)` — Commit mixes two logically distinct deliverables
  **Why**: The 20-file staged set spans (a) context-layer restructuring (completed 2026-04-16, files: `compound-gpid.context.md`, `2026-04-16-context-layer-restructuring.md`) and (b) prompt-prose-compression fix-triage work (2026-04-20). These are independently valuable and separately planned.
  **Fix**: Split into two commits: `feat(context): context layer restructuring — context file and Step 0 integration` and `fix(prompts): P1–P3 fix-triage from 2026-04-20 standard review`.

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `tests/prompt-tools.Tests.ps1:~329` — Section separator encodes historical finding ID `P2.1 —`
  **Fix**: Remove the `P2.1 —` prefix: `# cg-skill-fix-triage-migrate SKILL.md - behavioral rules`

- **[P3.2]** [cg-code-quality] `.cg-docs/solutions/testing-patterns/2026-04-20-behavioral-pester-tests-for-skill-md-files.md:7` — Tag `SKILL.md` breaks lowercase-kebab convention
  **Fix**: Change `SKILL.md` → `skill-md` in the `tags:` array.

- **[P3.3]** [cg-documentation] `.cg-docs/solutions/testing-patterns/2026-04-20-behavioral-pester-tests-for-skill-md-files.md:44` — Typo "untestedge"
  **Fix**: Change `untestedge` → `untested`.

- **[P3.4]** [cg-documentation / cg-architecture] `compound-gpid.context.md` — Missing `mode-specific step skipping` convention
  **Fix**: Add third bullet: "**Mode-specific step skipping**: Steps depending on in-scope findings (e.g., skill loading) are skipped when a mode flag (`--migrate`) is present. The flag is evaluable at invocation time — no formal arg-parsing step needed."

- **[P3.5]** [cg-architecture / cg-reproducibility] `compound-gpid.context.md:14` — `cg-review` omitted from plan-sort-key convention list
  **Fix**: Change "standardized across `cg-work`, `cg-plan`, and `cg-fix-triage`" → "…`cg-work`, `cg-plan`, `cg-review`, and `cg-fix-triage`".

- **[P3.6]** [cg-testing] `tests/prompt-tools.Tests.ps1:~320` — "prepend" regex too broad (matches "avoid prepend")
  **Fix**: Narrow from `'prepend'` → `'prepend full block'`.

- **[P3.7]** [cg-testing] `tests/prompt-tools.Tests.ps1:~1818` — P2.5 "Step 3.5 changes status to completed" is a whole-file search, not scoped to Step 3.5 block
  **Fix**: Use IndexOf to extract text between `"### Step 3.5:"` and `"### Step 3.7:"`, then assert within that block.

- **[P3.8]** [cg-testing] `tests/prompt-tools.Tests.ps1:~1289` — P3.3 `safe_auto` statistical regex missing `(?s)` flag
  **Fix**: Change `'Never.*safe_auto.*statistical|statistical.*escalate.*manual'` → `'(?s)Never.*safe_auto.*statistical|(?s)statistical.*escalate.*manual'`.

- **[P3.9]** [cg-testing] `tests/prompt-tools.Tests.ps1:~1797` — P2.4 "status.*planned" pattern could match anywhere in the file
  **Fix**: Either scope to the Step 1.5 block with IndexOf, or tighten to `'status is.*planned'` (the actual text).

- **[P3.10]** [cg-data-quality] `.github/skills/cg-skill-fix-triage-migrate/SKILL.md:21-22` — YAML findings template uses hardcoded `P1.1`/`P2.1` as placeholders
  **Why**: A model following the template literally may write exactly those two keys for any review file, then append the comment — producing silently malformed frontmatter.
  **Fix**: Replace with clearly generic notation:
  ```yaml
  findings:
    <id>: open   # one entry per parsed ID — replace <id> with actual IDs (e.g., P1.1, P2.3)
  ```

- **[P3.11]** [cg-data-quality] `.cg-docs/plans/2026-04-16-context-layer-restructuring.md:~357` — Two documentation checklist items unchecked despite `status: completed`
  **Fix**: Either tick the items if completed, or append: `<!-- deferred: not completed as part of this plan — tracked separately -->`.

- **[P3.12]** [cg-reproducibility] `.github/prompts/cg-review.prompt.md:161` Step 4 — `mode:autofix` space-sensitivity note absent from the step that applies it
  **Fix**: Add to Step 4 header: "`mode:autofix` requires no spaces around `:` (see Step 1.3); skip this block if autofix was not passed."

- **[P3.13]** [cg-documentation] `.github/prompts/cg-fix-triage.prompt.md:Step 0.5` — No explanation of why `--migrate` skip is evaluable before Step 2
  **Fix**: Add to the skip line: "(the flag is visible in the invocation command — no need to wait for Step 2)".

- **[P3.14]** [cg-architecture] `.github/prompts/cg-fix-triage.prompt.md:116` — "Skill as mode implementation" pattern undocumented
  **Fix**: Add comment above the delegation line:
  ```
  <!-- cg-skill-fix-triage-migrate implements the full --migrate workflow.
       Edit that skill to change migration behavior — not this file. -->
  ```

- **[P3.15]** [cg-architecture] `.gitignore` — No comment explaining `compound-gpid.context.md` is intentionally NOT gitignored
  **Fix**: Add adjacent to the `compound-gpid.local.md` entry: `# NOTE: compound-gpid.context.md is intentionally not listed here — it is shared institutional knowledge and must be committed.`

- **[P3.16]** [cg-reproducibility] (advisory) `cg-resume`, `cg-brainstorm`, `cg-ideate` — Still use mtime-based plan selection; inconsistent with `compound-gpid.context.md` claim of standardization
  **Fix**: Out of scope for this commit — follow-on task to update those three prompts and extend the context file's list.

---

### ✅ Passed — No issues found

- **`cg-skill-fix-triage-migrate/SKILL.md`**: All behavioral contracts present (all-open default, no-delegate rule, empty-result response, `prepend` instruction, cross-file dependency note).
- **`cg-setup.prompt.md`**: Duplicate EOF line removed; unclosed quote in B1.1.5 fixed; `setup-templates.md` check moved to A1.
- **`cg-work.prompt.md`**: `failing-steps` in File Permissions; `Test-Path` guard on both Pattern A and Pattern B; "skip this surface" clarified; roadmap re-read contingent.
- **`cg-plan.prompt.md`**: `brainstorm: null` convention; parenthetical removed from Risk row; roadmap re-read contingent.
- **Step 0 consistency**: All 5 changed prompts share identical 3-line Step 0 (intentional duplication for standalone use).
- **`tests/helpers.ps1` `Get-Frontmatter`**: CRLF/LF regex correct; shared via dot-source.
- **All new `It` blocks**: P3.1 split (4 separate blocks), P3.6 `.Rbuildignore`, P3.8 `3+ keywords`, P2.4 Step 1.5, P2.5 Step 3.5, P2.6 skip-Q4, P2.1 SKILL.md behavioral rules — all match actual prompt text.
- **`roadmap.json` schema**: All required fields present; `fix-triage-migrate-mode` entry is structurally valid.
- **Review file frontmatter**: Both review-1 and review-2 have canonical finding ID sort order; ID counts match body.
- **`compound-gpid.context.md`**: File is correctly committed (not gitignored); institutional knowledge, not user config.
- **Security**: No credentials, API keys, or PII in any staged file. Injection guard present in `cg-fix-triage` Step 3.
- **`README.md` banner**: Downgraded from CAUTION to NOTE with appropriate scope narrowing.
- **`docs/reference.md`**: `cg-skill-fix-triage-migrate` row present; `**/` glob prefix on all auto-escalation patterns.
