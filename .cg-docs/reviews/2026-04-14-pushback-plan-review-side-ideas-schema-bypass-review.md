---
plan: .cg-docs/plans/2026-04-14-pushback-plan-review-side-ideas-schema-bypass.md
findings:
  P1.1: open
  P1.2: open
  P1.3: open
  P2.1: open
  P2.2: open
  P2.3: open
  P2.4: open
  P2.5: open
  P2.6: open
  P2.7: open
  P2.8: open
  P2.9: open
  P2.10: open
  P2.11: open
  P2.12: open
  P2.13: open
  P2.14: open
  P2.15: open
  P2.16: open
  P2.17: open
  P2.18: open
  P2.19: open
  P2.20: open
  P3.1: open
  P3.2: open
  P3.3: open
  P3.4: open
  P3.5: open
  P3.6: open
  P3.7: open
  P3.8: open
  P3.9: open
  P3.10: open
  P2.21: open
  P2.22: open
  P2.23: open
  P3.11: open
  P3.12: open
  P3.13: open
  P3.14: open
  P3.15: open
  P3.16: open
---

## Review Report

**Review depth**: thorough
**Files reviewed**: 9 (7 modified + 2 new)
**Branch**: main (unstaged changes)
**Findings**: 0 P0 / 3 P1 / 20 P2 / 10 P3

### Modified files
- `.github/prompts/cg-brainstorm.prompt.md` — Step 3.5 Devil's Advocate + Step 5c Side-Idea Capture
- `.github/prompts/cg-plan.prompt.md` — Step 6a Side-Idea Capture + Step 6b Handoff
- `.github/prompts/cg-resume.prompt.md` — Schema bypass guard
- `.github/copilot-instructions.md` — `/cg-plan-review` entry
- `docs/reference.md` — Plan Review Agent section
- `tests/prompt-tools.Tests.ps1` — Test blocks P1.26–P1.31
- `.cg-docs/reviews/2026-04-08-ce-improvements-integration-light-review.md` — Findings marked fixed

### New files
- `.github/agents/cg-plan-critic.agent.md`
- `.github/prompts/cg-plan-review.prompt.md`

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-version-control] `(branch)` — Feature work committed directly to `main`
  **Why**: Project conventions require feature branches: "Never commit directly to main. Always use feature branches and PRs." This changeset adds a new agent, a new prompt, and enhances three existing prompts — all feature work requiring a branch. The last committed branch `bug/cg-work_roadmap` confirms conventions are in active use.
  **Fix**: `git checkout -b feat/plan-review-pushback` from current state to preserve all unstaged changes, then PR back to main.

- **[P1.2]** [cg-adversarial] `.github/prompts/cg-plan-review.prompt.md`:Step 1.2 — Active plan scan misses `status: in-progress` plans
  **Why**: `/cg-work` transitions plans from `active` to `in-progress` once implementation starts. A user who started work, was interrupted, ran `/cg-resume`, then ran `/cg-plan-review` would find that Step 1.2 (scanning for `status: active`) finds nothing — the in-progress plan is invisible. The fallback shows 3 most-recently-modified plans, which may be unrelated abandoned plans. The user reviews the wrong plan; all critic findings apply to the wrong document.
  **Fix**: Change Step 1.2 to scan for `status: active` OR `status: in-progress`, matching the same union that `cg-resume` uses.

- **[P1.3]** [cg-testing / cg-learnings-researcher] `tests/model-assignments.Tests.ps1` + `docs/model-guide.md` — New files not registered per the 7-file checklist
  **Why**: Past solution `.cg-docs/solutions/testing-patterns/2026-04-08-new-prompt-agent-addition-checklist.md` documents 7 files that must be updated in sync when adding a prompt or agent. Adding `cg-plan-review.prompt.md` and `cg-plan-critic.agent.md` requires: (1) `$promptStems` array in `model-assignments.Tests.ps1` to include `cg-plan-review`, (2) `$agentStems` to include `cg-plan-critic`, (3) `docs/model-guide.md` to have rows for both and updated total count. Verify these were updated — if any counts are stale, the test suite will silently miss model assignment regressions on the new files.
  **Fix**: Check model-assignments.Tests.ps1 line ~105 (`$promptStems`) and ~119 (`$agentStems`). Check model-guide.md count sentinel (should be 30 after +2). Update if needed.

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-architecture / cg-adversarial] `.github/prompts/cg-resume.prompt.md`:Step 1 — Schema bypass heuristic too coarse; false positive risk
  **Why**: The bypass fires when `SCHEMA_VERSION` exists at workspace root. Any ETL/data project with its own schema versioning file would silently bypass the entire Step 1 schema check forever — including the check that `cg-schema-version` is present and non-empty in `compound-gpid.local.md`. A project with a blank or stale `cg-schema-version` would never receive migration warnings.
  **Fix**: Use a compound condition: `SCHEMA_VERSION` AND (`install.ps1` OR `cg-release.prompt.md`) all present at workspace root. These co-occur only in compound-gpid itself.

- **[P2.2]** [cg-architecture] `.github/prompts/cg-brainstorm.prompt.md`:Step 3.5 — Devil's Advocate has no Lightweight scope adaptation
  **Why**: Step 1.5 already classifies brainstorms as Lightweight / Standard / Deep and maps each scope to fewer questions. Step 3.5 is declared "always-on and unconditional" with no corresponding scale-down. For a Lightweight brainstorm (single file, problem well understood, < 2 days), running all four checks — especially "Is this problem real and worth solving?" — creates overhead disproportionate to scope. Compare: Step 2 maps scope explicitly to question depth; Step 3.5 has no equivalent.
  **Fix**: For Lightweight scope, condense to checks 3 (effort-value) and 4 (charter alignment) only, with a single short observation rather than a four-check sweep. Preserve full four checks for Standard/Deep.

- **[P2.3]** [cg-adversarial] `.github/prompts/cg-brainstorm.prompt.md`:Step 3.5 — "Is this problem real?" unconditional for already-validated bug reports
  **Why**: If the user provided explicit validation evidence in Steps 1-2 (reproduction steps, stack traces, user-reported data), check 1 ("Is this problem real and worth solving?") is condescending and wasteful. Two turns re-litigating a closed question erodes tool credibility.
  **Fix**: Add a signal check: "If the user provided explicit validation evidence (reproduction steps, user reports, quantitative data) during Steps 1-2, skip check 1 and note it as pre-validated."

- **[P2.4]** [cg-adversarial] `.github/prompts/cg-brainstorm.prompt.md`:Step 5c — Undefined "meaningful pushback exchange" condition → hallucinated roadmap entries
  **Why**: The context-aware variant triggers if "a meaningful pushback exchange occurred in Step 3.5." This is a model judgment call with no definition. If the user said "looks good, proceed," the model may still choose the affirmative branch and produce: "During our pushback discussion, we touched on [X, Y, Z]..." — summarizing topics the user never raised. Hallucinated summaries dispatched to `@cg-roadmap` create permanent roadmap entries from confabulations.
  **Fix**: Remove the condition. Use one unconditional closing question: "Summarize any adjacent ideas that came up. Ask: 'Want to capture any of these to the roadmap? If nothing came up, say so and we'll skip.'" The model can correctly say "no ideas surfaced" without needing a binary condition.

- **[P2.5]** [cg-adversarial] `.github/prompts/cg-brainstorm.prompt.md`:Step 5c — Missing `roadmap.json` guard → hallucinated milestone names
  **Why**: Step 5b correctly says "if `roadmap.json` does not exist, skip this section entirely." Step 5c has no equivalent guard. When the model tries to fill in "[suggest the most relevant milestone from roadmap.json]" and no roadmap exists, it hallucinates a milestone name. If the user approves, `@cg-roadmap` creates a roadmap with the hallucinated milestone embedded as permanent structure.
  **Fix**: Add to Step 5c: "If `roadmap.json` does not exist, skip the milestone suggestion and ask: 'No roadmap exists yet — want me to create one and add this idea?'"

- **[P2.6]** [cg-adversarial] `.github/prompts/cg-plan-review.prompt.md`:Step 3 — No circuit breaker for finding flood
  **Why**: If `@cg-plan-critic` returns 10+ P2 findings, Step 3's "one at a time" interaction runs 40-50 turns with follow-up discussions. Context may saturate before reaching the handoff. No decisions are captured. The user must start over.
  **Fix**: "If P1+P2 findings exceed 5, present all findings as a summary list first and ask whether to engage interactively or accept/defer all at once."

- **[P2.7]** [cg-adversarial] `.github/agents/cg-plan-critic.agent.md`:Priority definitions — Contradictory P3 definition inflates finding count
  **Why**: The output format template defines P3 as "Suggestion — something worth considering but not blocking." The Rules section defines P3 as requiring "a real risk." These are different bars. A model anchoring on the first definition generates P3 findings for general observations, style preferences, and speculative concerns, burying P1/P2 in noise. Users learn to ignore the output.
  **Fix**: Remove "something worth considering" from the output format block. Use one canonical definition: "P3: Potential risk — a realistic failure mode that is unlikely or low-impact enough that it is non-blocking." Both locations must match.

- **[P2.8]** [cg-reproducibility] `.github/prompts/cg-plan-review.prompt.md`:Step 2 — "charter context" dispatch payload undefined
  **Why**: Step 2 says "Dispatch `@cg-plan-critic` with the full plan content and charter context" — but "charter context" is unspecified. It could mean the entire `compound-gpid.md`, just the Constraints section, or just the project name. The critic has no Step 0 to read the charter itself. Different runs can include different amounts of context, producing inconsistent scope-creep analysis on identical plans.
  **Fix**: Make the payload explicit: "Dispatch `@cg-plan-critic` with: (1) full plan content, (2) the Objective, Constraints, and Current Focus sections copied verbatim from `compound-gpid.md`." Or add a Step 0 to the critic agent.

- **[P2.9]** [cg-reproducibility] `.github/prompts/cg-plan-review.prompt.md`:Step 1 — "Most recent file" ordering criterion unspecified
  **Why**: Step 1.2 scans for "the most recent file with `status: active`" but doesn't define recency — filename date prefix, filesystem mtime, or frontmatter `date:` field all produce different rankings. If two plans share the same date prefix, selection is non-deterministic.
  **Fix**: "Sort by the YYYY-MM-DD prefix in the filename; for ties, sort by frontmatter `date:` field; for remaining ties, sort alphabetically."

- **[P2.10]** [cg-version-control] `.cg-docs/reviews/2026-04-08-ce-improvements-integration-light-review.md`:1–14 — Findings marked `fixed` without verifiable changes in this diff
  **Why**: Several findings (e.g., P2.1 required removing `agents:` key from `cg-review.prompt.md`; P2.2 required adding `cg-compound` tests) are marked `fixed` but the corresponding files are not in the current diff. Marking findings `fixed` without the fix risks that future reviewers trust the status and skip re-checking.
  **Fix**: Audit each finding against the actual diff. Revert statuses to `open` or `deferred` for any finding without a corresponding file change.

- **[P2.11]** [cg-version-control] `.github/agents/cg-plan-critic.agent.md` + `.github/prompts/cg-plan-review.prompt.md` — New untracked files not yet staged; risk of omission
  **Why**: Both new files are untracked. A partial `git add` targeting specific files will silently skip them. The tests guard these files with `Test-Path` — if omitted from the commit, a clean clone fails those tests immediately.
  **Fix**: Stage explicitly: `git add .github/agents/cg-plan-critic.agent.md .github/prompts/cg-plan-review.prompt.md`, then verify with `git status`.

- **[P2.12]** [cg-code-quality / cg-testing] `tests/prompt-tools.Tests.ps1`:~1503 — Duplicate comment IDs P1.26–P1.31
  **Why**: The file already uses comment labels `# P1.26` through `# P1.31` for earlier test blocks (around lines 1153–1284). The new additions append a second set of the same IDs. These comment IDs are the cross-reference system for the test file; duplicates make it impossible to uniquely cite a test group.
  **Fix**: Renumber the new additions as `# P1.37` through `# P1.42` (verify the last existing comment number and increment from there).

- **[P2.13]** [cg-code-quality / cg-testing] `tests/prompt-tools.Tests.ps1`:Workflow Entry Points describe — Missing `/cg-plan-review` assertion
  **Why**: The `"copilot-instructions.md - Workflow Entry Points"` Describe block has `It` assertions for every other command in the table but not for `/cg-plan-review`, which was added to that table in this changeset. Removing `/cg-plan-review` from `copilot-instructions.md` would go undetected.
  **Fix**: Add `It "references /cg-plan-review in Workflow Entry Points" { ($section -match '/cg-plan-review') | Should Be $true }`

- **[P2.14]** [cg-testing] `tests/prompt-tools.Tests.ps1`:P1.26 block — "Always-on and unconditional" contract not tested
  **Why**: The source explicitly says "This step is always-on and unconditional — run it for every brainstorm at every scope." This phrase is the behavioral contract that prevents Step 3.5 from being skipped for Lightweight tasks. No test verifies it.
  **Fix**: `It "Step 3.5 is always-on and unconditional for all scopes" { ($content -match 'always-on and unconditional') | Should Be $true }`

- **[P2.15]** [cg-testing] `tests/prompt-tools.Tests.ps1`:P1.26 block — Thinking Partner mode adaptations untested
  **Why**: Step 3.5 defines distinct Thinking Partner behavior (substituting "decision reversibility" and "stakeholder impact"). Neither term is tested. A regression here silently breaks non-software brainstorms.
  **Fix**: Add two `It` blocks: check `($content -match 'decision reversibility')` and `($content -match 'stakeholder impact')`.

- **[P2.16]** [cg-testing] `tests/prompt-tools.Tests.ps1`:P1.27 block — `@cg-roadmap` dispatch not verified in Step 5c
  **Why**: The two conditional variants are tested but the action instruction "dispatch `@cg-roadmap` for each" is not checked. If the dispatch line is removed, Step 5c becomes dead text with no test catching it.
  **Fix**: `It "Step 5c dispatches @cg-roadmap for captured ideas" { ($content -match '@cg-roadmap') | Should Be $true }` (scoped to the Step 5c context via index range or anchored regex).

- **[P2.17]** [cg-learnings-researcher] `tests/prompt-tools.Tests.ps1` — Missing step-ordering tests for Step 3.5 and Step 5c
  **Why**: Past solution `.cg-docs/solutions/testing-patterns/2026-04-13-prompt-step-ordering-indexof-tests.md` establishes that content-presence tests (`-match 'Step 3.5'`) don't catch steps placed in the wrong position. Past regression: `cg-work` roadmap update moved after a session-terminating wait and went undetected for multiple sessions. Step 3.5 must appear before Step 4; Step 5c must appear before the final "Wait for the user's response" to avoid being dead code.
  **Fix**: Add `IndexOf` ordering tests: `$content.IndexOf("### Step 3.5") -lt $content.IndexOf("### Step 4:")` and `$content.IndexOf("5c. Side-Idea")` pre-dating the session wait phrase.

- **[P2.18]** [cg-documentation] `docs/workflow.md` — Plan Review step missing from workflow diagram and Plan section
  **Why**: The workflow loop diagram and the Plan step's "Handoff options" description in workflow.md do not mention `/cg-plan-review`. The `cg-plan.prompt.md` Step 6b now offers it as option 2, creating an inconsistency between the prompt behavior and the user documentation.
  **Fix**: (1) Add `[Plan Review]` to the workflow loop diagram. (2) Update Plan handoff options to include `/cg-plan-review — Challenge the plan before starting (recommended for Standard/Deep)`.

- **[P2.19]** [cg-documentation] `docs/workflow.md` — No Plan Review section; no Brainstorm devil's advocate description
  **Why**: Every user-invocable prompt has a dedicated section in workflow.md. `/cg-plan-review` has none. The Brainstorm section doesn't describe the new Step 3.5 devil's advocate challenge.
  **Fix**: Add a `### Plan Review (/cg-plan-review)` section. Append to Brainstorm "What happens": "...runs an always-on devil's advocate challenge (Step 3.5) covering problem validity, simplicity, effort-value, and charter alignment before the decision is finalized."

- **[P2.20]** [cg-documentation] `docs/manual.md` + `docs/reference.md` — Missing `/cg-plan-review` and devil's advocate in quick-orientation / reference entry
  **Why**: `docs/manual.md` shows the typical path omitting `/cg-plan-review`. `docs/reference.md` `/cg-brainstorm` entry doesn't mention the new always-on devil's advocate behavior — the most user-visible change to that command.
  **Fix**: Update manual.md path to include `[/cg-plan-review]`. Append to reference.md `/cg-brainstorm` description: "After proposing approaches, runs an always-on devil's advocate challenge covering problem validity, simplicity, effort-value, and charter alignment."

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `.github/agents/cg-plan-critic.agent.md` — Mixed `{N}` and `<N>` placeholder syntax in output format
  **Why**: The output format uses `{N}` for the finding number but `<plan section>`, `<title>` etc. Every other agent uses angle-bracket placeholders exclusively.
  **Fix**: Replace `{N}` with `<N>` throughout the template.

- **[P3.2]** [cg-performance] `.github/agents/cg-plan-critic.agent.md` — Focus areas 1 and 6 give the same core instruction twice
  **Why**: Area 1 says "Verify named things against the actual codebase." Area 6 says "Verify referenced files, packages, and APIs via search." Primary action is identical; results in duplicate findings or model confusion about attribution.
  **Fix**: Merge Area 6's two unique bullets (version/schema currency; undeclared external deps) into Area 1 as items 4–5. Renumber remaining areas.

- **[P3.3]** [cg-performance] `.github/agents/cg-plan-critic.agent.md` — Output format hardcodes `P1` as priority example
  **Why**: Template shows `**[P1.{N}]**` — model generates its first finding as P1 before reading the priority definitions. Other agents use `**[P0|P1|P2|P3]**` to make the full range visible at the format definition site.
  **Fix**: Change to `**[P1|P2|P3.<N>]** [cg-plan-critic]...`

- **[P3.4]** [cg-architecture] `.github/prompts/cg-plan-review.prompt.md`:L1 — Missing agent-list documentation comment
  **Why**: `cg-review.prompt.md` opens with a maintenance comment listing every dispatched agent (workaround for non-functional `agents:` frontmatter in `.prompt.md` files). `cg-plan-review.prompt.md` dispatches `@cg-plan-critic` and `@cg-roadmap` but has no equivalent comment.
  **Fix**: Add at line 1: `<!-- Agents dispatched: cg-plan-critic (plan review), cg-roadmap (side-idea capture). Note: 'agents:' frontmatter is non-functional in .prompt.md files. -->`

- **[P3.5]** [cg-architecture] `.github/prompts/cg-brainstorm.prompt.md`:Step 3.5 — Side-idea capture embedded in body copy, not labeled as sub-step
  **Why**: In `cg-plan.prompt.md` and `cg-plan-review.prompt.md`, side-idea capture is a first-class heading. In `cg-brainstorm.prompt.md` Step 3.5, it's an unlabeled paragraph easily overlooked when maintaining the file.
  **Fix**: Add a bold label: `**Side-idea capture (during this exchange):**` before the paragraph.

- **[P3.6]** [cg-documentation] `docs/reference.md`:Plan Review Agent table — "User-invocable" vs "user-invokable" inconsistency
  **Why**: The new table header uses `User-invocable` (c); the prose below uses `user-invokable` (k); the adjacent Roadmap Agent table also uses `User-invokable` (k). Three occurrences, two spellings.
  **Fix**: Change the header to `User-invokable` to match the Roadmap Agent table.

- **[P3.7]** [cg-code-quality] `tests/prompt-tools.Tests.ps1`:P1.28 — Assertion title overpromises what is checked
  **Why**: `It "has tools: restricted to read and search (not write)"` but assertion only checks `'read'` — doesn't verify `'search'` present or `'write'` absent (the write-absence is covered by a separate all-agents dynamic test, but the title is misleading).
  **Fix**: Either strengthen assertion to also check `'search'`, or rename to `"has tools: restricted (no write access)"`.

- **[P3.8]** [cg-reproducibility] `.github/prompts/cg-brainstorm.prompt.md`:Step 3.5 — Charter alignment check lacks absent-charter guard
  **Why**: Check 4 reads "Does it conflict with constraints in `compound-gpid.md` (loaded in Step 0)?" — but Step 0 allows proceeding without a charter. When charter was absent, the model has no reference and may hallucinate plausible constraints.
  **Fix**: Add: "If no charter was loaded in Step 0, skip this check and note: 'Charter alignment could not be verified — no `compound-gpid.md` found.'"

- **[P3.9]** [cg-reproducibility] `tests/prompt-tools.Tests.ps1`:~L916 — `GetTempFileName()` leaks orphaned `.tmp` files
  **Why**: `[System.IO.Path]::GetTempFileName()` pre-creates a zero-byte `.tmp` file on disk. The test then appends `.md` and uses the derived filename, so those `.tmp` files are never cleaned up; they accumulate across test runs.
  **Fix**: Use `[System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), [System.IO.Path]::GetRandomFileName() + ".md")` instead — doesn't pre-create a file.

- **[P3.10]** [cg-performance] `tests/prompt-tools.Tests.ps1`:P1.29 — `Test-Path` guard is incomplete
  **Why**: The `$content` assignment has a `Test-Path` guard, but the `Get-Frontmatter` call inside the same Describe block is unguarded. If the file is absent, `Get-Frontmatter` calls `Get-Content` and throws an unhandled exception rather than a clean test failure.
  **Fix**: Guard consistently: `$frontmatter = if (Test-Path $promptFile) { Get-Frontmatter -FilePath $promptFile } else { "" }`. Or drop the guard on `$content` and rely on the `It "exists"` test to surface the failure cleanly.

---

### ✅ Passed

- **cg-data-quality**: YAML frontmatter valid in both new files; review file finding statuses all use valid `open`/`fixed`/`skipped` values; `tools: ['read', 'search']` is valid YAML and consistent with other Sonnet-class agents; `model: Claude Sonnet 4.6 (copilot)` consistent with review agents; `model: Claude Opus 4.6 (copilot)` consistent with orchestration prompts.
- **cg-reproducibility**: All four changed prompts read `compound-gpid.md` and `compound-gpid.local.md` at Step 0. No hardcoded absolute paths. All new Pester tests are deterministic (pure regex string matching, no randomness or time-dependency). `cg-plan-critic` correctly restricted to `tools: ['read', 'search']` with `user-invocable: false`.
- **cg-code-quality** (DRY/duplication): Side-idea capture duplication across three prompts is intentional per the standalone-prompt design convention. No issue.
- **cg-architecture** (agent/prompt split): 1:1 orchestrator/specialist split is architecturally consistent. `/cg-review` vs `/cg-plan-review` distinction is correct (code diff vs plan doc review). `cg-plan-critic` absence from `copilot-instructions.md` agent list is intentional — it's a plan tool, not a code review agent, and is correctly documented in `docs/reference.md`.
- **cg-learnings-researcher** (brainstorm spec): Implementation follows the `2026-04-14-pushback-side-ideas-schema-bypass.md` brainstorm spec. Both side-idea capture variants (no-pushback and pushback) are present. Schema bypass uses file-presence detection as specified.

---

> Review report saved to `.cg-docs/reviews/2026-04-14-pushback-plan-review-side-ideas-schema-bypass-review.md`. Use `/cg-fix-triage` in a future session to apply findings by ID (e.g., `/cg-fix-triage P1.2 P2.4`) or by priority level (e.g., `/cg-fix-triage P1`).

---

## Standard Re-Review Additions (2026-04-14)

The following findings were added in a standard re-review run and are not in the thorough review above.

### P2 — IMPORTANT (additions)

- **[P2.21]** [cg-code-quality] `.github/prompts/cg-brainstorm.prompt.md:207` — Step 5c first-branch condition is unreachable
  **Why**: Step 3.5 is declared "always-on and unconditional — run it for every brainstorm." The condition "if no substantive exchange occurred" is therefore never true — the branch is dead code. The wording "No adjacent ideas surfaced" conflates *whether the exchange happened* with *whether ideas emerged*.
  **Fix**: Replace condition with idea-discovery framing: "If no adjacent ideas emerged from the Step 3.5 exchange" / "If adjacent ideas surfaced during Step 3.5".

- **[P2.22]** [cg-code-quality] `.github/prompts/cg-plan-review.prompt.md:91` — Step 5 handoff has no threshold for "needs revision" vs "solid"
  **Why**: No rule defines when to use "If findings need revision" vs "If plan is solid". For a P3-only outcome, neither branch fits cleanly. The "solid" branch also offers `/cg-plan` with label "Make minor adjustments before starting", undercutting the meaning of solid.
  **Fix**: Add threshold: "Use 'solid' when zero P1/P2 findings remain. Rename 'solid' option 2 to 'Make minor optional adjustments'." 

- **[P2.23]** [cg-code-quality] `.github/prompts/cg-plan-review.prompt.md:48` — P3 findings silently omitted from interactive pass
  **Why**: Step 3 says "For P1 and P2 findings, engage interactively." P3 findings appear in agent output but have no stated handling — they will be silently dropped without ever being shown to the user.
  **Fix**: Add: "P3 findings: list them all at once after the P1/P2 interactive pass, without requiring individual responses."

### P3 — MINOR (additions)

- **[P3.11]** [cg-code-quality] `.github/prompts/cg-brainstorm.prompt.md:Step3.5` — "chosen or leading approach" undefined at Step 3.5 timing
  **Why**: At Step 3.5 the user has not committed to an approach yet. "Leading approach" is undefined — it could mean the one marked Recommended, the one the user mentioned most, or all of them.
  **Fix**: Replace with "the recommended approach (or all proposed approaches if the user hasn't expressed a preference yet)."

- **[P3.12]** [cg-testing] `tests/prompt-tools.Tests.ps1:~1549` — P1.27 doesn't verify old `5c. Handoff` label is gone
  **Why**: A botched rename leaving both `5c. Handoff` and `5d. Handoff` passes all P1.27 tests.
  **Fix**: Add `($content -notmatch '5c\.\s+Handoff') | Should Be $true`

- **[P3.13]** [cg-testing] `tests/prompt-tools.Tests.ps1:~1627` — P1.29 Step 4 location test bypassed by OR fallback
  **Why**: `($content -match 'Step 4.*Side-Idea|Side-Idea Capture')` — second branch matches anywhere in the file, voiding the location constraint.
  **Fix**: Drop the OR fallback: `($content -match 'Step 4.*Side-Idea Capture') | Should Be $true`

- **[P3.14]** [cg-testing] `tests/prompt-tools.Tests.ps1:~1657` — P1.31 regex requires both terms on same line
  **Why**: PowerShell `-match` `.` does not cross newlines; if terms appear in adjacent sentences the regex fails.
  **Fix**: `($content -match 'SCHEMA_VERSION') -and ($content -match 'workspace root') | Should Be $true`

- **[P3.15]** [cg-documentation] `docs/workflow.md` — `/cg-plan-review` absent from The Loop diagram
  **Why**: The ASCII loop diagram at the top of workflow.md shows `Plan → Work` directly, making the new optional step invisible.
  **Fix**: Revise to show `... → Plan → [Plan-Review] → Work → ...`

- **[P3.16]** [cg-architecture] `.github/prompts/cg-plan-review.prompt.md` — No subagent output quality check
  **Why**: `/cg-review` has a Step 2.5 that detects empty/garbled agent output and reports it explicitly. `/cg-plan-review` has no equivalent — silent empty output confuses users.
  **Fix**: Add lightweight check: if `@cg-plan-critic` returns no findings and no explicit "no issues found" statement, display: "The plan critic did not return usable output. Try invoking `@cg-plan-critic` directly with the plan file."

