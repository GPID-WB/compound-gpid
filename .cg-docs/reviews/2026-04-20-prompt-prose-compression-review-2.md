---
plan: .cg-docs/plans/2026-04-20-prompt-prose-compression.md
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
  P2.13: fixed
  P2.14: fixed
  P2.15: fixed
  P2.16: fixed
  P2.17: fixed
  P2.18: fixed
  P2.19: fixed
  P2.20: fixed
  P2.21: skipped
  P2.22: fixed
  P2.23: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: skipped
  P3.6: fixed
  P3.7: fixed
  P3.8: fixed
  P3.9: fixed
  P3.10: fixed
  P3.11: fixed
  P3.12: fixed
  P3.13: fixed
  P3.14: skipped
  P3.15: fixed
  P3.16: fixed
  P3.17: fixed
  P3.18: skipped
  P3.19: skipped
  P3.20: fixed
  P3.21: fixed
  P3.22: fixed
  P3.23: fixed
  P3.24: fixed
---

## Review Report

**Review depth**: standard (auto-escalated from `light` — ~830 non-test lines changed across 8 files)
**Files reviewed**: 9 tracked modified + 4 untracked new files
**Findings**: 50 (P0: 0, P1: 3, P2: 23, P3: 24)

> Note: `2026-04-20-prompt-prose-compression-review.md` already exists from a prior review pass (P1–P3 findings from that session are tracked there). This file captures findings from the follow-up light/standard review of the same changeset.

---

### P0 — BLOCKING

None.

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-documentation / cg-version-control / cg-reproducibility] `.github/skills/cg-skill-fix-triage-migrate/SKILL.md` — Step 2b instruction says "Set all findings to `open`" but Step 3 report template says "M defaulted to `fixed` (companion plan completed), K defaulted to `open`."
  **Why**: Step 2b and its inline comment ("default to open; mark resolved ones fixed manually") make clear everything is set to `open`. The Step 3 template contradicts this: a model following the instructions correctly will then emit a report claiming some findings are `fixed` when all are `open`. Users will incorrectly believe resolved findings are closed and skip them. This finding was independently raised by three agents.
  **Fix**: Replace the Step 3 report template with: `"Migrated N review file(s). All findings defaulted to open — mark resolved ones fixed manually with /cg-fix-triage <IDs>."` Remove the `M defaulted to fixed / K defaulted to open` clause entirely.

- **[P1.2]** [cg-documentation] `cg-work.prompt.md` — File Permissions section allows only `status` and `completed-date` but Step 2 Test Failure Recovery writes a `failing-steps` field.
  **Why**: File Permissions says: "You may modify the YAML frontmatter of the plan file currently being implemented (status and completed-date fields only)." Step 2 sub-step 5 says: "Append the current step number to the plan file's `failing-steps:` frontmatter list (create the field if absent)." An AI strictly following File Permissions could refuse to write `failing-steps`, breaking the double-notification deduplication logic.
  **Fix**: Extend File Permissions: "You may modify the YAML frontmatter of the plan file currently being implemented (status, completed-date, and failing-steps fields only)."

- **[P1.3]** [cg-version-control] Working tree — 4 new institutional files are untracked and will be silently omitted from the commit.
  **Why**: Project constraint: "always commit institutional knowledge." `git status` shows these as `??` (untracked, not gitignored): `.cg-docs/brainstorms/2026-04-20-reduce-late-sequence-token-cost.md`, `.cg-docs/plans/2026-04-20-prompt-prose-compression.md`, `.cg-docs/reviews/2026-04-20-prompt-prose-compression-review.md`, and `.github/skills/cg-skill-fix-triage-migrate/` (directory). None are gitignored.
  **Fix**:
  ```powershell
  git add .cg-docs/brainstorms/2026-04-20-reduce-late-sequence-token-cost.md
  git add .cg-docs/plans/2026-04-20-prompt-prose-compression.md
  git add .cg-docs/reviews/2026-04-20-prompt-prose-compression-review.md
  git add .github/skills/cg-skill-fix-triage-migrate/
  ```

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` — `cg-skill-fix-triage-migrate/SKILL.md` has zero behavioral tests.
  **Why**: The existing `SKILL.md files - required frontmatter` loop checks only `name:` and `description:` fields. The skill defines three distinct runtime behaviors (all-open default, two frontmatter insertion paths, "do NOT delegate" safety rule) with no corresponding `It` blocks. The `cg-fix-triage.prompt.md` tests verify the prompt references `--migrate` and `companion-plan`, but not the SKILL.md content.
  **Fix**: Add a `Describe "cg-skill-fix-triage-migrate SKILL.md - behavioral rules"` block with tests for: all-open default, "do NOT delegate" instruction, "No legacy review files found" empty-set response, and prepend-when-no-frontmatter instruction.

- **[P2.2]** [cg-testing] `tests/prompt-tools.Tests.ps1` — `cg-fix-triage.prompt.md` "Do NOT delegate" instruction for frontmatter status updates is untested.
  **Why**: `cg-review.prompt.md` has an explicit symmetrical test ("explicitly instructs DO NOT delegate the Step 3.5 file write"). `cg-fix-triage` Step 3 item 4 has the same safety property ("Edit only frontmatter, not the body. **Do NOT delegate to a subagent.**") but no test.
  **Fix**: Add to the `cg-fix-triage.prompt.md - per-finding status tracking` Describe block: `It "instructs DO NOT delegate frontmatter status update to a subagent" { ($content -match 'Do NOT delegate') | Should Be $true }`

- **[P2.3]** [cg-testing] `tests/prompt-tools.Tests.ps1` — `cg-review.prompt.md` mode:autofix statistical-function escalation guard is untested.
  **Why**: The prompt says "Never `safe_auto` findings touching statistical functions, welfare/income variables, or weight parameters — escalate to `manual`." This is a data-correctness safety rule. Existing tests verify the tagging system exists but not this exclusion.
  **Fix**: Add to `Describe "cg-review.prompt.md - mode:autofix argument"`: `It "prohibits safe_auto for statistical functions (escalate to manual)" { ($content -match '(?s)safe_auto.*statistical|Never.*safe_auto.*statistical|statistical.*escalate.*manual') | Should Be $true }`

- **[P2.4]** [cg-testing] `tests/prompt-tools.Tests.ps1` — `cg-work.prompt.md` Step 1.5 "Mark Work Started" (planned → active) transition is untested.
  **Why**: Steps 3.7 (done), 3.8 (milestone), and 3.5 (plan complete) all have tests, but the `active` status transition at work start has none. The roadmap can silently remain at `planned` for an entire implementation cycle.
  **Fix**: Add `Describe "cg-work.prompt.md - Step 1.5 Mark Work Started"` with tests that `@cg-roadmap` dispatch for `status active` is documented and conditioned on `status is planned`.

- **[P2.5]** [cg-testing] `tests/prompt-tools.Tests.ps1` — `cg-work.prompt.md` Step 3.5 "Mark Plan Complete" (`completed-date`) is untested.
  **Why**: Step 3.5 triggers Step 3.7 (roadmap done update) and depends on writing `status: completed` + `completed-date:` to plan frontmatter. No test verifies this plan-file mutation.
  **Fix**: Add `It "Step 3.5 writes completed-date"` and `It "Step 3.5 changes status to completed in plan frontmatter"` to a new or existing describe block.

- **[P2.6]** [cg-testing] `tests/prompt-tools.Tests.ps1` — `cg-setup.prompt.md` skip-Q4 guard for `compound-gpid.md` creation is untested.
  **Why**: "If the user skips ALL charter questions (skips before Q4 or skips Q4), do NOT create `compound-gpid.md`." The existing overwrite-guard test covers the file-exists case but nothing tests the skip/non-creation path.
  **Fix**: Add to `Describe "cg-setup.prompt.md - mode detection and overwrite guard"`: `It "does NOT create compound-gpid.md if user skips Q4" { ($content -match 'do NOT create|skips.*Q4|skips before Question 4') | Should Be $true }`

- **[P2.7]** [cg-documentation] `.github/skills/cg-skill-fix-triage-migrate/SKILL.md` Step 2c — No YAML template for the new-frontmatter case.
  **Why**: `cg-review.prompt.md` Step 3.5 provides an explicit frontmatter template. This skill's Step 2c ("Add frontmatter") omits it entirely, risking schema drift (e.g., using `status:` key instead of per-finding keys, or omitting `plan:`).
  **Fix**: Add a frontmatter template to Step 2c showing `plan:` and `findings:` keys with `open` values, matching the schema from `cg-review.prompt.md` Step 3.5.

- **[P2.8]** [cg-documentation / cg-version-control / cg-performance] `cg-setup.prompt.md` — Duplicate "Ready to work" line at end of Mode B (compression artifact).
  **Why**: The final two lines are identical: `> "Ready to work. Use '/cg-brainstorm', '/cg-plan', '/cg-work', or '/cg-review'."` appears twice. The model emits the completion message twice for every Mode B invocation.
  **Fix**: Remove one of the two identical lines.

- **[P2.9]** [cg-documentation / cg-code-quality] `cg-setup.prompt.md` Step B1.1.5 — Opening `"` in deprecated-sections blockquote is never closed.
  **Why**: The user-facing message begins with `> "Your charter contains sections beyond...` and ends several lines later without a closing `"`. A model treating the entire block as a string literal may include internal notes (archiving instruction) in the user-visible output.
  **Fix**: Add closing `"` after the final line of the quoted block: `> Removed content should be archived to '.cg-docs/archive/charter-history.md'. The user should manually perform this archiving — this prompt does not do it."`

- **[P2.10]** [cg-documentation] `docs/reference.md` Skills table — `cg-skill-fix-triage-migrate` is not listed.
  **Why**: The table lists other internal-use skills (`cg-skill-brainstorming`, `cg-skill-compound-docs`). The new skill follows the same pattern but is absent. A user reading the table to understand `/cg-fix-triage --migrate` would find no entry.
  **Fix**: Add row: `| cg-skill-fix-triage-migrate | Migration mode for /cg-fix-triage --migrate: backfills findings: frontmatter on legacy review files. Does NOT apply fixes. |`

- **[P2.11]** [cg-documentation] `cg-review.prompt.md` Step 4 — "Before dispatching agents" is anachronistic; agents are dispatched at Step 2.
  **Why**: Step 1.2 correctly says "include tagging instructions in each agent dispatch at Step 2." Step 4 opens with "Before dispatching agents, add to each agent's instructions:" — at Step 4, agents have already returned. A model reading sequentially may re-dispatch agents, duplicating Step 2 work.
  **Fix**: Replace "Before dispatching agents, add to each agent's instructions:" with "(Tagging instructions were added at Step 2; now apply the tagged findings:)" and restructure the autofix logic accordingly.

- **[P2.12]** [cg-documentation] `cg-review.prompt.md` Step 3.5 vs `cg-plan.prompt.md` Step 0.5 — Inconsistent plan-file selection criteria.
  **Why**: `cg-review` selects by `date:` frontmatter field; `cg-plan` selects by last-write time. Git does not preserve mtime on clone — the two prompts may select different "most recent" plans in the same session.
  **Fix**: Standardize both to `date:` frontmatter field first, fall back to last-write time if absent, then alphabetically-last filename as tiebreaker. Apply consistently to `cg-plan.prompt.md` Step 0.5.

- **[P2.13]** [cg-documentation] `cg-fix-triage.prompt.md` Step 3.3 — "prompt/docs fixes" vs "code fixes" test runner hint is ambiguous.
  **Why**: A finding such as "missing docstring in an `.R` file" is simultaneously a "docs fix" (→ `prompt-tools`) and a "code fix" (→ module test), creating confusion about which test suite to run.
  **Fix**: Clarify: "For findings in `.md` prompt or documentation files, use `prompt-tools`; for findings in code files (`.R`, `.py`, `.do`, `.ps1`), use the test file covering the changed module."

- **[P2.14]** [cg-architecture / cg-performance] `cg-fix-triage.prompt.md` Step 0.5 — Language skills loaded unconditionally before `--migrate` detection and before reading findings.
  **Why**: Step 0.5 fires before Step 1 detects `--migrate` or reads the review report. If findings are all docs/prompt-only (common for this project), R/Python/Stata skills are loaded for no purpose (~200–500 tokens each). `--migrate` mode never touches code yet still triggers skill loading.
  **Fix**: Move Step 0.5 to after Step 1.5 (after finding types and arguments are parsed). Make skill loading conditional: "If findings reference `.R`/`.Rmd` files → load R skills; `.py` → Python; `.do`/`.ado` → Stata; `--migrate` → skip skill loading entirely."

- **[P2.15]** [cg-architecture] `cg-skill-fix-triage-migrate/SKILL.md` Step 2b — Companion-plan naming contract is an undocumented implicit cross-file dependency.
  **Why**: The heuristic ("strip `-review` suffix → find matching plan in `.cg-docs/plans/`") depends on `cg-review.prompt.md` Step 3.5 naming convention. Neither file documents this dependency. If `cg-review`'s naming rule changes, `--migrate` silently defaults all findings to `open` with no warning.
  **Fix**: Add to SKILL.md Step 2b: "This heuristic relies on review files being named `<plan-stem>-review.md` per `cg-review.prompt.md` Step 3.5. If no match is found, log: `No companion plan found for <filename> — defaulting all findings to open.`"

- **[P2.16]** [cg-architecture] `tests/prompt-tools.Tests.ps1` — No test verifies `cg-fix-triage.prompt.md` names `cg-skill-fix-triage-migrate` by name.
  **Why**: Existing tests check `--migrate` and `companion-plan` appear in the main prompt, but not that the skill name itself (`cg-skill-fix-triage-migrate`) is referenced. If someone renames the skill, the delegation breaks silently.
  **Fix**: Add to `Describe "cg-fix-triage.prompt.md - per-finding status tracking"`: `It "loads cg-skill-fix-triage-migrate for --migrate mode by name" { ($content -match 'cg-skill-fix-triage-migrate') | Should Be $true }`

- **[P2.17]** [cg-architecture] `tests/prompt-tools.Tests.ps1` — `Get-ToolsList` helper defined in the test file rather than `tests/helpers.ps1`.
  **Why**: `tests/helpers.ps1` already has `Get-Frontmatter` for shared extraction logic. `Get-ToolsList` follows the same pattern but lives in `prompt-tools.Tests.ps1`. If agent-tools tests are split into a dedicated file, `Get-ToolsList` will need to be duplicated or the two copies will diverge.
  **Fix**: Move `Get-ToolsList` to `tests/helpers.ps1`. The existing dot-source at line 21 of the test file already covers the import.

- **[P2.18]** [cg-reproducibility] All file-selection prompts (`cg-fix-triage`, `cg-plan`, `cg-work`) — "Most recently modified" selection based on last-write mtime is non-reproducible across machines.
  **Why**: Git does not preserve mtime. On a fresh clone, all files get the checkout timestamp, making mtime-based selection order non-deterministic across machines. `/cg-fix-triage` on Machine A may select a different review file than on Machine B.
  **Fix**: Use `date:` frontmatter field as primary sort key (deterministic, git-stable); fall back to last-write mtime only if `date:` is absent; use alphabetically-last filename as the final tiebreaker. Apply consistently across all three prompts and document that explicit filename argument overrides auto-selection.

- **[P2.19]** [cg-reproducibility] `cg-setup.prompt.md` Step A3 — `setup-templates.md` existence checked lazily after collecting user input.
  **Why**: Mode A asks Q1–Q3 before Step A3 reads `setup-templates.md`. If the template is missing, the user has already answered all questions for nothing. The command produces a dead-end after identical effort on every broken-install invocation.
  **Fix**: Move the `setup-templates.md` existence check to Step A1 (before any questions). Only proceed to A2 if the file is confirmed present.

- **[P2.20]** [cg-reproducibility] `cg-fix-triage.prompt.md` Step 3 — Inferred test file name has no existence check; a wrong guess silently passes with 0 tests run.
  **Why**: The `execution_subagent` template says "use the test file covering the changed module." The AI fills in `<relevant-test-name>` from context. If it guesses a non-existent file, `Run-Tests.ps1 -File nonexistent` may exit with 0 failures, masking all untested code.
  **Fix**: Add to the template: "First verify `tests\<test-name>.Tests.ps1` exists. If not found, run `prompt-tools` as the default and note that the targeted file was not found."

- **[P2.21]** [cg-performance] `cg-review.prompt.md` Step 4 — The autofix block (~16 lines of tagging definitions + application rules + report template) is always loaded in context despite `mode:autofix` being an infrequent advanced option.
  **Why**: Normal mode is the default for ≥95% of runs. The tagging definition, three application-rule bullets, statistical exclusion rule, delegate prohibition, and reporting template ride in context on every invocation. Additionally, Step 1 says tags are added "at Step 2" but Step 4 says "before dispatching agents" — contradictory execution order.
  **Fix**: Extract autofix-specific content to a new `cg-skill-review-autofix` SKILL.md; replace Step 4's autofix block with a stub: "If `mode:autofix`: load `cg-skill-review-autofix` and follow its instructions." Fix Step 1 cross-reference to say "see Step 4 for tagging instructions to include."

- **[P2.22]** [cg-data-quality] `.cg-docs/reviews/2026-04-20-prompt-prose-compression-review.md` — Body header finding count (42 total) is stale vs frontmatter (71 total findings across P1/P2/P3).
  **Why**: Additional findings were appended in a subsequent fix-triage session but the body header was never updated. A user or reviewer seeing "8 P3" when there are 27 P3 findings draws incorrect conclusions about review scope.
  **Fix**: Update the body header to reflect cumulative counts, or append a note: `*(updated: 29 additional findings added in a subsequent review pass — see frontmatter for totals)*`.

- **[P2.23]** [cg-data-quality] `cg-fix-triage.prompt.md` Step 1.3 — No regex pattern specified for parsing legacy finding IDs.
  **Why**: Step 1.3 uses only examples (`P1.1`, `P2.3`, etc.) while `cg-review.prompt.md` Step 3.5 specifies the exact pattern `P[0-3]\.\d+[a-z]?`. For legacy files without `findings:` frontmatter, an AI following the looser spec may silently miss two-digit IDs (`P1.12`) or lettered sub-IDs (`P1.1a`).
  **Fix**: Add to Step 1.3: "Match IDs using the pattern `P[0-3]\.\d+[a-z]?` — consistent with the pattern used by cg-review when saving."

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `tests/prompt-tools.Tests.ps1:~256` — Multi-condition `-match` chain with `-and` inside a single `It` block produces unactionable "False | Should Be True" failure message.
  **Why**: When the test fails, there is no indication which of the four P-level patterns was missing. Split assertions produce actionable failure output.
  **Fix**: Split the four `-match` conditions into four separate `It` blocks, one per priority level.

- **[P3.2]** [cg-code-quality] `cg-plan.prompt.md:~98` — `brainstorm:` template field uses "if applicable" instead of the `null` convention.
  **Why**: `roadmap.json` consistently uses `null` for absent optional path references. The plan template's `brainstorm: "<link to brainstorm if applicable>"` is the only optional reference that doesn't document the `null` fallback.
  **Fix**: Change to `brainstorm: "<link to brainstorm, or null>"`.

- **[P3.3]** [cg-code-quality] `cg-work.prompt.md:117` — "skip this surface" is undefined jargon in the Auto-Fix Diagnostics section.
  **Why**: "surface" has no established meaning in this prompt. A model may interpret "skip this surface" as skipping the entire diagnostics section rather than suppressing one specific message.
  **Fix**: Replace "skip this surface" with "skip emitting the 'Tests are still failing but no diagnostic errors were found' message below."

- **[P3.4]** [cg-code-quality] `.cg-docs/plans/2026-04-16-context-layer-restructuring.md:6` — `Step-0` tag uses mixed case while all other tags are lowercase-kebab.
  **Why**: Tags: `[context, copilot-instructions, template, consumer-projects, Step-0, multi-folder]`. `Step-0` is the only tag with an uppercase letter.
  **Fix**: Change `Step-0` to `step-0`.

- **[P3.5]** [cg-testing] `tests/prompt-tools.Tests.ps1` — Three Describe blocks are duplicated for context-layer features (~12 extra `It` blocks).
  **Why**: Lines testing `cg-compound context enrichment`, `cg-resume Current Focus staleness`, and `cg-work milestone completion` each appear in two separate Describe blocks. When the prompt changes, only one block is typically updated.
  **Fix**: Merge each pair by keeping the more comprehensive block and moving unique assertions from the second into it.

- **[P3.6]** [cg-testing] `tests/prompt-tools.Tests.ps1` — `cg-review.prompt.md` R package `.Rbuildignore` check has no test.
  **Why**: `cg-setup` has an `A4.5` test for `.Rbuildignore`; `cg-review` has an inline equivalent instruction with no coverage parity.
  **Fix**: Add `It "includes R package .Rbuildignore check for .cg-docs/"` to `Describe "cg-review.prompt.md - review file output step"`.

- **[P3.7]** [cg-testing] `tests/prompt-tools.Tests.ps1` — `cg-fix-triage.prompt.md` unrecognized-argument warning has no test.
  **Why**: The prompt specifies an exact fallback message for unrecognized arguments. `cg-review` has coverage for its equivalent path. Coverage parity is missing.
  **Fix**: Add `It "warns on unrecognized arguments with recognized options list" { ($content -match 'Unrecognized argument') | Should Be $true }` to the cg-fix-triage describe block.

- **[P3.8]** [cg-testing] `tests/prompt-tools.Tests.ps1` — `cg-plan.prompt.md` `3+ matching keywords` threshold is untested.
  **Why**: The threshold is marked `<!-- threshold synced with cg-brainstorm.prompt.md Step 0.5 -->`. A silent reword to "2+" would not be caught.
  **Fix**: Add `It "uses 3+ matching keywords threshold (synced with cg-brainstorm)"` asserting `$content -match '3\+? matching keywords'`.

- **[P3.9]** [cg-documentation] `cg-skill-fix-triage-migrate/SKILL.md` Step 2b — No fallback instruction when companion plan file is not found.
  **Why**: "Strip `-review` suffix → find matching plan" but no guidance if no match exists. An AI would silently default to `open` (correct behavior) but the omission creates doubt.
  **Fix**: Add: "If no matching plan is found, skip the plan-status check and set all findings to `open`."

- **[P3.10]** [cg-documentation] `docs/reference.md` Auto-Escalation Rules table — `**/` glob prefix missing from pattern display.
  **Why**: The table shows `pipeline*.{R,py}` but the actual patterns in `cg-review.prompt.md` Step 1.5 are `**/pipeline*.{R,py}`. Without `**/`, the table implies patterns only match files in the repo root.
  **Fix**: Add `**/` prefix to the four pipeline/extract/load/scripts patterns in the reference table.

- **[P3.11]** [cg-documentation] `README.md` — "[!CAUTION] WORK IN PROGRESS — DO NOT USE IN PRODUCTION" banner may be stale.
  **Why**: Per-finding status tracking, migration tooling, and multiple tagged releases suggest the system has reached a stability level inconsistent with "not yet ready for use."
  **Fix**: If production-stable, remove or downgrade the banner. If still pre-release, narrow scope: specify which parts are unstable rather than the whole system.

- **[P3.12]** [cg-documentation] `cg-work.prompt.md` Step 2 — `execution_subagent` query for test reads lacks `Test-Path` guard for `last-run.json`.
  **Why**: `cg-fix-triage.prompt.md` wraps the `ConvertFrom-Json` call with `if (-not (Test-Path tests\last-run.json))`. `cg-work.prompt.md` unconditionally runs `Get-Content tests\last-run.json | ConvertFrom-Json`. If `Run-Tests.ps1` exits early, `last-run.json` may not exist.
  **Fix**: Add the same `Test-Path` guard to both Pattern A and Pattern B in `cg-work.prompt.md`'s `execution_subagent` query template.

- **[P3.13]** [cg-version-control] Working tree — All 9 modified tracked files and 4 new files are unstaged.
  **Why**: Pre-commit reminder. Nothing in the working tree is staged. Suggested commit message: `refactor(prompts): compress prose and dedup Step 0 across top 5 prompts`.
  **Fix**: `git add -p` to review and stage all changed files (include the 4 untracked files per P1.3).

- **[P3.14]** [cg-architecture] `tests/prompt-tools.Tests.ps1` — "Existence + frontmatter + no tool restriction" trinity is inlined ~9 times across all orchestrating prompts.
  **Why**: Any new orchestrating prompt gets baseline structural tests only if someone remembers to copy-paste all three blocks. Pester 3.4 supports `foreach` at the outer scope.
  **Fix**: Consolidate with a `$orchestratingPrompts` list and `foreach` loop generating the three `Describe` blocks per prompt. Content-specific tests remain as individual `Describe` blocks.

- **[P3.15]** [cg-reproducibility] `cg-review.prompt.md` Step 1 — `mode:autofix` argument parsing does not document space-sensitivity.
  **Why**: `mode: autofix` (with space) hits the unrecognized-argument fallback, silently disabling the feature. The difference is easy to miss.
  **Fix**: Either normalize the argument by stripping spaces around `:` before matching, or explicitly document: "Argument must be `mode:autofix` (no spaces around `:`)."

- **[P3.16]** [cg-reproducibility] `cg-plan.prompt.md` Step 5 / `cg-work.prompt.md` Step 3.7 — Roadmap update verification by immediate re-read is potentially racy.
  **Why**: Both prompts re-read `roadmap.json` immediately after `@cg-roadmap` writes it. If the agent write is asynchronous or VS Code's file-system watcher hasn't flushed, the re-read may show pre-write content, producing a spurious "may not have been applied" warning.
  **Fix**: Make the re-read contingent on the agent's confirmation: "After `@cg-roadmap` confirms the update, re-read `roadmap.json` to verify."

- **[P3.17]** [cg-reproducibility] `cg-fix-triage.prompt.md` `--migrate` stub — No verification that the skill file exists before delegating.
  **Why**: If `cg-skill-fix-triage-migrate/SKILL.md` is absent (e.g., after partial `cg-link` failure), the AI proceeds without skill context and likely produces an incomplete or hallucinated migration. `cg-setup.prompt.md` has a stop condition for its equivalent missing-template case.
  **Fix**: Add guard: "If `cg-skill-fix-triage-migrate/SKILL.md` cannot be read, stop and say: 'Migration skill not found. Re-run `cg-link` to restore it.'"

- **[P3.18]** [cg-performance] `tests/prompt-tools.Tests.ps1` — Same file read multiple times across separate `Describe` blocks for the same prompt.
  **Why**: `cg-fix-triage.prompt.md` incurs 4 reads; `cg-review.prompt.md` incurs 4 reads (combinations of `Get-Frontmatter` and `Get-Content -Raw`). In Pester 3.4, `BeforeAll` is unavailable, so each `Describe` re-reads independently.
  **Fix**: Consolidate related `Describe` blocks for the same file into one parent `Describe` with nested `Context` blocks. The file is assigned once at `Describe` scope; all `Context`/`It` blocks share the variable.

- **[P3.19]** [cg-performance] `cg-work.prompt.md` Step 2 — `execution_subagent` query template repeated verbatim for Pattern A and Pattern B.
  **Why**: Patterns A and B are near-identical ~5-line blocks differing only in the `-File <name>` argument and `filteredFiles` field. The model re-reads ~10 lines of boilerplate per iteration.
  **Fix**: Define both patterns once as a named reference block at the top of Step 2; refer to them by name in per-step instructions.

- **[P3.20]** [cg-performance] `cg-plan.prompt.md` Step 4.5 — Redundant parenthetical in Confidence Check table risk row.
  **Why**: "Fewer than 3 risks listed **and** scope is Standard or Deep (Lightweight plans may have 1–2 risks without penalty)" — the parenthetical restates the exclusion already encoded in the `and scope is Standard or Deep` condition.
  **Fix**: Remove the parenthetical; the condition clause is sufficient.

- **[P3.21]** [cg-data-quality] `.cg-docs/plans/2026-04-20-prompt-prose-compression.md` frontmatter — `scope: "Standard"` is an undocumented field with a capitalized value.
  **Why**: No other plan file uses `scope`. All other enum-style fields use lowercase. If `scope` is a new schema field, no valid-value documentation exists.
  **Fix**: Either document `scope` as a valid plan frontmatter field with allowed lowercase values (`standard`, `large`), or remove it until formally adopted.

- **[P3.22]** [cg-data-quality] `.cg-docs/reviews/2026-04-20-prompt-prose-compression-review.md` — `findings:` YAML map has IDs out of canonical sort order.
  **Why**: `P1.12`, `P2.24`–`P2.32` appear after `P3.8` (appended in a later session). YAML parsing is unaffected but human reading is harder.
  **Fix**: Reorder to `P0.*` → `P1.*` (all) → `P2.*` (all) → `P3.*` (all). Add a note in `cg-review.prompt.md` Step 3.5 that subsequent-session additions should be inserted at the correct sorted position.

- **[P3.23]** [cg-data-quality / cg-code-quality] `cg-skill-fix-triage-migrate/SKILL.md` Step 2c — Frontmatter insertion point unspecified.
  **Why**: "insert `findings:` map only (do not create a second `---` block)" does not say *where* in the existing frontmatter block to insert. A model could insert before `plan:`, at the bottom before `---`, or randomly. If appended after `---`, it produces silently malformed YAML.
  **Fix**: Change to: "insert the `findings:` map as the last key before the closing `---` delimiter."

- **[P3.24]** [cg-data-quality] `roadmap.json` — `cg-skill-fix-triage-migrate` capability (`/cg-fix-triage --migrate`) has no feature entry.
  **Why**: This is a new user-invocable mode with distinct behavior. `/cg-resume` and `/cg-ideate` infer project state from the roadmap. This feature is invisible to those prompts.
  **Fix**: Add a feature entry under the `quality-loop` milestone (e.g., `fix-triage-migrate-mode`, `status: done`) so the capability appears in roadmap-driven workflows.

---

### ✅ Passed — No issues found

- **cg-code-quality**: `cg-fix-triage.prompt.md` (overall structure), `cg-review.prompt.md` (agent list comment, auto-escalation table, Step 3.5 save logic), `cg-work.prompt.md` (Pattern A/B comments, filteredFiles guard), `roadmap.json` (schema consistent), `.gitignore` (well-organized), `cg-skill-fix-triage-migrate/SKILL.md` (frontmatter present and well-formed)
- **cg-testing**: New P1.21–P1.31 test coverage for compressed prompts (scope assessment, confidence check, prior-work scan, depth overrides) — well-structured and non-overlapping
- **cg-architecture**: No circular dependencies. `cg-skill-fix-triage-migrate` isolation is clean (thin one-line delegation, no logic duplication). `roadmap.json` schema consistent with `compound-gpid-roadmap-v1`. Step 0 intentional boilerplate duplication is correctly documented.
- **cg-reproducibility**: `cg-setup.prompt.md` file-write operations are idempotent. `cg-review.prompt.md` findings parsing has an integrity check. `cg-work.prompt.md` `filteredFiles` check prevents partial runs as commit gate. All prompts have `compound-gpid.md` missing fallback.
- **cg-data-quality**: `roadmap.json` fully valid — all cross-references resolve. `cg-review.prompt.md` finding-ID regex handles two-digit IDs and lettered sub-variants. `cg-fix-triage.prompt.md` security injection guard is correctly placed. Frontmatter write safety ("Do NOT delegate") is present.
- **cg-version-control**: No credentials, API keys, or sensitive data in any changed file. `tests/last-run.json` and `compound-gpid.local.md` correctly gitignored.
