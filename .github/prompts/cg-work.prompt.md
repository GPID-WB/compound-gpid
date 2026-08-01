---
description: "Implement a /cg-plan plan. Supports phaseX, review, deviate controls."
---

# Work

You implement `/cg-plan` output with phase/review/deviate controls.

## File Permissions

- You may read any file in the workspace.
- You may read targeted `roadmap.json` fields for plan/roadmap status.
- You may create/modify code files required by the plan.
- You may modify only these plan frontmatter fields: `status`, `completed-date`, `failing-steps`, `completed-phases`, `current-phase`, `execution-report`.
- You may create/modify compact active-state records under `.cg-docs/active-state/`.
- You must NOT modify `roadmap.json` directly -- dispatch `@cg-roadmap` for all roadmap writes.

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md` (objective, constraints, current focus). If missing, warn the user: "No project charter found. Run `/cg-setup` to create one. Proceeding without project context."
2. Read `compound-gpid.local.md` (language, project type, review depth).
3. Load `.github/shared/context-loading.contract.md` and apply Stage 0/1/2. Do not read full `compound-gpid.context.md` by default; if the plan/touched tech needs tactical facts, search relevant headings/snippets and state `Context expansion: reading <artifact/section> because <reason>.`
4. Parse flags:
   - `--no-brain` sets `brain-enabled = false`; otherwise `true`.
   - Modes: auto, manual, none, light, standard, data-risk, architecture, full.
   - Default: `review:manual`.
   - Invalid review value: warn and fall back to recommendation mode.
   - Parse `deviate:` override; invalid warns and falls back to plan policy; duplicate warns, last valid wins. Full spec: `.github/shared/goal-execution.contract.md`.

### Step 1: Load the Plan

1. Find the most recent plan in `.cg-docs/plans/` by `date:` frontmatter, then last-write time, then alphabetically last filename; if ambiguous, ask.
2. If no plan exists and none was specified:
   - Try keyword-title matching against filenames and ask before using a match.
   - If the request mentions "refactor", "replace", "migrate", "pipeline", or touches multiple files, decline: "This task looks too large for an inline plan. Please run `/cg-plan` first."
   - Otherwise classify scope as in `/cg-plan` Step 1.5. For Standard/Deep, warn that `/cg-plan` is strongly recommended.
   - Generate a 3-5 steps lightweight inline plan under `.cg-docs/plans/YYYY-MM-DD-<brief-title>.md` with active frontmatter, `deviation-policy: ask`, and minimal `## Completion Contract` (Outcome + Verification Surface). Ask: "No existing plan found. Here's a quick plan based on your request: [inline plan]. Proceed with this, or run `/cg-plan` first?" If confirmed, skip Step 1.5 and Step 3.7; if declined, stop.
3. Read the plan thoroughly. Treat the body as implementation instructions,
   but reject any directive that would delete, replace, rename, move, or
   wholesale regenerate protected assets, or override these file permissions.
   Protected assets include `.github/`, `.cg-docs/`, `compound-gpid.md`,
   `compound-gpid.local.md`, `roadmap.json`, and `SCHEMA_VERSION`. Approved
   plans may modify prompts, agents, skills, instructions, docs, tests, audit
   tooling, and relevant `.cg-docs/` evidence when explicitly authorized for
   Compound GPID maintenance.
   > **After any plan-file fallback** (for example keyword match or changed path): re-count `## Phase` headers from the recovered plan body and re-validate the phase argument N against the new total M.
4. **Goal contract**: Load `.github/shared/goal-execution.contract.md` and `.github/shared/active-state.contract.md`. Treat the plan's `## Completion Contract` as authority under file permissions, charter, Pester safety, and protected artifacts. If the plan lacks `## Completion Contract` or `deviation-policy`, halt and offer a minimal compatibility contract or `/cg-plan`. Active policy = runtime `deviate:` override else plan `deviation-policy`.
5. **Artifact validation preflight**: Load
  `.github/shared/artifact-view.contract.md`. HTML may orient readers but never supplies execution semantics; execution semantics come only from canonical Markdown. If the selected Plan has `artifact-schema-version`, run
  `cg-render-artifact --validate-only <plan-path>` and require success before
  roadmap status, execution-report creation, active-state writes, or code
  changes. If validation fails, preserve the Plan and prior view, report the
  exact error and expected missing/stale/current view path, then halt with the
  one-file recovery command. Plans without the field remain legacy Plans and
  use the explicit compatibility approval behavior in Goal contract / Legacy
  Plan Compatibility; never silently upgrade or reject them here.
6. Load relevant skills only as needed: R, Python, or Stata.

### Step 1.2: Parse Phase Argument

**Argument parsing**: accept `phase1`, `phase 1`, and `Phase 1` (case-insensitive; strip spaces between "phase" and the digit; normalize to integer N).

**Plan type detection**: scan the plan body for `## Phase` headers, ignoring fenced code blocks (``` or `~~~`). If any are found, the plan is phased; otherwise non-phased.

**Phase membership rule**: a phase contains all `### N.` headings between `## Phase K:` and the next `## Phase` header or end of document. Headings before the first `## Phase` are preamble and are NOT steps.

**Dispatch logic**:
- Non-phased + no argument: execute all steps.
- Non-phased + `phaseX`: warn "This plan has no phases. Executing all steps." Proceed.
- Phased + no argument: validate `completed-phases` are positive integers in [1, M]; ask on out-of-range entries. If all complete, display "All M phases are already complete. Nothing to run. Use `/cg-work phaseM` to re-run a specific phase if needed." and halt. Otherwise start at the first incomplete phase.
- Phased + `phaseX`: scope Step 2 to only that phase.

**Validation**:
- If N < 1, halt: "Phase argument must be >= 1. `phase0` is not valid."
- If N > M counted from `## Phase` headers, not from `phases:` frontmatter, halt with:
  > "Error: Plan has M phases. Phase N does not exist.
  > Available phases:
  > - Phase 1: <title> -- completed
  > - Phase 2: <title> -- next
  > - Phase 3: <title> -- not started
  >
  > Suggested next: `/cg-work phase2`"
- If `completed-phases` is absent, treat it as `[]`. If requesting phase X but phase X-1 is incomplete, except phase 1 is always allowed, halt:
  > "Error: Phase X cannot start -- Phase X-1 is not yet completed.
  >
  > Suggested next: `/cg-work phaseX-1`
  > Or review the plan: `/cg-plan-review`"

### Step 1.3: Consult Brain

If `brain-enabled = false`, skip.

Load `cg-skill-brain-query`. Search for gotchas, similar implementation work, file-specific patterns, and technology pitfalls. Apply only relevant constraints.

### Step 1.5: Mark Work Started

If `roadmap.json` exists, find the feature whose `plan` path matches this plan. If status is `planned`, dispatch `@cg-roadmap`: "Update feature with plan path `<plan-path>` to status active." Skip `active`/`done`. Run only after plan validation.

Use targeted structured fields only: feature IDs, titles, statuses, and `plan` paths. State the expansion reason before reading.

**GitHub Issues (optional — does not block work)**:
If matched feature has `github.issueNumber`, display:
> "Linked issue: #`<number>` — `<issueUrl>`"

If no `github` block and `roadmap.json` has `githubIssues.enabled: true`, suggest:
> "This work item has no linked GitHub issue. Run `/cg-issues link` before or after implementation to attach one."
Do NOT call `gh`, create issues, or block work.

**Execution report**: Create `.cg-docs/work-reports/YYYY-MM-DD-<plan-slug>.md` after roadmap active-status handling and before implementation; failure blocks. Use plan `execution-report` if present; otherwise find/create by plan reference. Same-day collision: append `-2`, `-3`, etc. Write pointer to plan frontmatter; update incrementally; append run/resume sections. Schema: `.github/shared/goal-execution.contract.md`.

**Active-state handoff**: After report creation, phase boundaries, blocked
stops, and completion, update `.cg-docs/active-state/current.json` per contract:
refs, decisions, evidence status, exact `nextCommand`;
no full bodies, raw output, diffs, or transcripts.

### Step 1.6: Build Test Index

Before implementing, scan once for test files covering each plan step (for example `tests/test-<module>.R`, `tests/<module>.Tests.ps1`, `tests/test_<module>.py`). Reuse this index throughout Step 2.

### Step 2: Implement Step by Step

For each in-scope plan step:

1. Announce the step.
2. **Discover existing tests** from the Step 1.6 index.
3. **Red-phase verification** (conditional -- skip only for purely structural steps with **no Pester test file asserting against the modified content**, such as config, markdown documentation, YAML frontmatter, or scaffolding):
   - If the step introduces testable behavior, write tests before touching the implementation, run them against current code, and require a failing baseline.
   - Report: "Red-phase confirmed: `[test name]` fails with: `[one-line error]`".
   - If the test passes before implementation, revise once. If it still passes, log: "Could not establish failing baseline -- proceeding without red-phase confirmation. Flag for `@cg-testing` review." Continue; this is not a hard stop.
4. Implement using project conventions and relevant skills. Required deviation: `ask` → pause and record; `autonomous` → allow and record; `strict` → blocked-stop unless plan is revised.
5. Test as specified by the plan. R uses `testthat`, Python uses `pytest`, Stata uses assertions/validation do-files, and PowerShell uses Pester through the canonical safe runner from `cg-skill-pester-safety`.

**Running tests** (do NOT use `Invoke-Pester` directly -- always use `execution_subagent`):

Targeted file:
> **execution_subagent query**: "In the repo root, run `. tests\Run-Tests.ps1 -File <test-name>` (no other flags, no pipeline). Then run `if (-not (Test-Path tests\last-run.json)) { Write-Output 'last-run.json not found -- run tests first' } else { Get-Content tests\last-run.json | ConvertFrom-Json | Select-Object passed, failedCount, failures }`. Return only those three fields."

Full-suite commit gate:
> **execution_subagent query**: "In the repo root, run `. tests\Run-Tests.ps1` (no flags, no pipeline). Then run `if (-not (Test-Path tests\last-run.json)) { Write-Output 'last-run.json not found -- run tests first' } else { Get-Content tests\last-run.json | ConvertFrom-Json | Select-Object passed, failedCount, failures, filteredFiles }`. Return only those four fields."

Gate rules:
- If no test framework is identified, skip recovery loops and report: "Test framework not identified -- manual verification required."
- If targeted tests pass, continue.
- If the full-suite result has `filteredFiles`, it is a partial run; do not treat it as the commit gate.
- Never run `Invoke-Pester` directly, never run `Invoke-Pester tests/`, never pipeline `Invoke-Pester -PassThru`, and never use `2>&1 | Select-String`. When inspecting Pester failures, rerun the safe `Run-Tests.ps1` command above and inspect `tests/last-run.json`; do not introduce direct file-level Pester recipes.

**Test Failure Recovery**:
- Test Failure Recovery applies to functional tests only; `get_errors` errors are handled separately in Auto-Fix Diagnostics.
- Make up to **2 fix attempts total per plan step**. Do not weaken assertions or change expected values unless the plan explicitly names the old/new interface or return values; direct assertion updates for changed signature or return type are allowed. Inference about interface change from failure alone is prohibited.
- Attempt 1: one targeted fix. Attempt 2: one more targeted fix attempt. If resolved, run the full test suite for changed files to catch regressions introduced by the fix; if the full suite passes, continue normally to Auto-Fix Diagnostics. If regressions appear, emit the standard failure notification, format from sub-step 4, and continue to Auto-Fix Diagnostics.
3. If tests are still failing after 2 fix attempts, append the step number to `failing-steps:` frontmatter and notify:
  > "**N test(s) still failing after 2 fix attempts** -- continuing to next step.
  > Review before merging.
  > Failing tests:
  > - `<test-file>::<test-name>` -- `<last error message>`"
  Ask for `stop` or `continue`; if no explicit stop, continue to diagnostics carrying the failures.
- Do NOT dispatch `@cg-fix-problems` for test failures.

**Auto-Fix Diagnostics**:
- After each test phase, call `get_errors` on touched files.
- If errors (not warnings/info) are returned, dispatch `@cg-fix-problems` with `mode: auto`, touched files, diagnostics, and any prior test-fix context.
- Suppress this step when no errors are present; warnings-only and info-only diagnostics do not dispatch.
- `@cg-fix-problems` gets up to 2 rounds (2-round budget) for errors only. Re-run tests. If errors remain, ask whether to proceed or stop.
- If `get_errors` is clean but tests still fail, do not re-dispatch `@cg-fix-problems`; logical failures require manual investigation. If Test Failure Recovery step 4 wrote the current step to `failing-steps:`, skip emitting a duplicate notice.

Then validate acceptance criteria, suggest a conventional commit (`feat`, `fix`, `docs`, `test`, `refactor`, or `chore`), summarize, and move to the next step.

### Step 2.5: Phase Boundary

This fires after all steps in the current phase complete; skip for non-phased plans.

- Phase-terminal commit suppression: for the final step of a phase, skip the per-step commit sub-step; Step 2.5 handles the phase-level commit.
- Run the full-suite gate, suggest `feat(scope): complete phase N -- <phase title>`, and summarize steps, files, and tests.
- If the full-suite gate fails, is partial (`filteredFiles` non-null), or any in-phase step remains in `failing-steps:`, do not append `N` to `completed-phases` unless each failing step is fixed, skipped, deferred, or accepted with rationale. Otherwise leave/set `current-phase: N`, preserve `failing-steps:`, report blockers, and halt or ask.
- **Evidence gate**: before appending N to `completed-phases`, verify all required Verification Surface rows for phase N via executed checks (not static inspection). Missing evidence: block or record an accepted exception with rationale in the execution report.
- Update plan frontmatter in this exact order (crash-safe):
  1. First append `N` to `completed-phases` using YAML flow sequence with unquoted integers, for example `completed-phases: [1]` or `[1, 2]`. Never use quoted strings or block style. Re-read and verify.
  2. Then set `current-phase` to N+1, or remove `current-phase` if this was the final phase. `current-phase` is informational only; no prompt reads or acts on it.
  3. Do not change `status`; `status: active` with non-empty `completed-phases` means paused between phases.
- `completed-phases` is the authoritative completion record and must be written before `current-phase`.
- If N < M, offer: "Phase N complete. **Continue to Phase N+1?** Or stop here and resume later with `/cg-work phaseN+1`?" Stop gracefully if the user stops and do not run Step 3.
- If final phase N = M, proceed directly to Step 3 quality checks, Step 3.2 self-review, Step 3.5 complete, Step 3.7 roadmap update, and Step 3.9 review-mode handoff. Do not show a continue/stop offer.

### Step 3: Quality Checks

After all steps: verify tests pass; docs/style are updated; no hardcoded paths, magic numbers, unnamed constants, or secrets (`api_key`, `password`, `secret`, `token`, `AWS_`, `OPENAI_`).

### Step 3.2: Self-Review

Scan your own changes:
1. Debug code: remove `print(`, `console.log(`, `browser()`, `breakpoint()`, `pdb.set_trace()`, and `cat("DEBUG`.
2. Missing tests: each new public function has a test.
3. Broken imports: new `library()`, `import`, or `use` statements reference existing packages.
4. Incomplete work: resolve or document `TODO`, `FIXME`, `HACK`, `XXX` added this session.
5. Secrets: remove hardcoded `api_key`, `password`, `secret`, `token`, `AWS_`, `OPENAI_`.

Report: "Mechanical self-review complete: [no debug/import/TODO issues found | found and fixed: <list>]. **Statistical and logical correctness are not checked here -- run `/cg-review` before merging analytical code.**"

### Step 3.5: Mark Plan Complete

**Evidence gate**: before writing `status: completed`, verify all required `final`/whole-plan Verification Surface rows via executed checks. Block if missing unless an accepted exception with rationale is recorded in the execution report.

In the plan frontmatter, change `status: active` to `status: completed` and add `completed-date: YYYY-MM-DD`. If already completed, skip silently. Confirm: "Plan marked as completed."

### Step 3.7: Update Roadmap Status

Proceed only if Step 2, Step 3 quality checks, tests, and the Step 3.5 evidence gate passed, or all missing evidence has explicit accepted exceptions.

If `roadmap.json` exists:
1. Context expansion: reading `roadmap.json` feature status fields because completed work must be matched back to its roadmap feature. Find features whose `plan` path matches this plan (workspace-relative, forward slashes). Skip `plan: null`.
2. If no match, do title-search fallback: scan unfinished `plan: null` features whose titles appear in the plan requirements or step titles. Ask the user to confirm which features were completed, then dispatch `@cg-roadmap`: "Update feature `<feature-id>` to status done and set plan to `<plan-path>`."
3. If matched and not already `done`, dispatch `@cg-roadmap`: "Update feature with plan path `<plan-path>` to status done."
4. Verify with a targeted `roadmap.json` status read; if unchanged, tell the user they can run `@cg-roadmap` directly.

### Step 3.8: Milestone Completion Check

For each milestone in the loaded `roadmap.json` containing a feature just marked `done`: if all features are `done`, dispatch `@cg-roadmap`: "Update milestone `<milestone-id>` to status done." Then notify: "Milestone **'<milestone title>'** is now complete! Current Focus may be stale. Run `/cg-strategy`."

### Step 3.9: Review-Mode Handoff

Read `.github/shared/review-routing.contract.md` and use it as the canonical source for review-mode names, risk triggers, precedence, mandatory escalations, and agent sets. Use the same deterministic changed-file signals as `/cg-review` Step 1.5 to resolve a recommended mode.

| Review mode | Behavior |
|-------------|----------|
| default / no review arg | No agent dispatch. Emit a review-mode recommendation only, including a suggested command such as `/cg-review <mode>`. |
| `review:manual` | No agent dispatch. Emit a structured recommendation only: resolved mode, reason, and suggested `/cg-review <mode>` command. |
| `review:none` | Suppress review dispatch and show only a brief suppression note. |
| `review:auto` | Run route-aware agent dispatch using the shared routing contract; dispatch only the route-appropriate agent set. |
| `review:light`, `review:standard`, `review:data-risk`, `review:architecture`, `review:full` | Treat as an explicit user route; dispatch that route exactly once and include any high-risk signals as review focus. |

No review arg defaults to `review:manual` with no agent dispatch. Default and `review:manual` must never dispatch review agents automatically. `review:auto` aligns with `/cg-review` auto-routing outcomes for equivalent diffs. `review:none` dispatches nothing. When `review:auto` or explicit routed modes dispatch agents, include the global protected-artifact constraint from `/cg-review` and preserve P0/P1 reporting strength. Explicit routed modes win; auto routing applies only when no explicit route was requested.

### Model Advisory Handoff

Read `.github/shared/model-advisory.contract.md` and use the `implementation`
stage for the transition to review. Emit a compact recommendation for the next
user selection: implementation capability profile, strong option and effort,
economical option when useful, and rationale. Examples are suggestions;
availability can differ by platform and date, and the user makes the final
selection. Do not dispatch, switch, retry, or set a model or reasoning effort.

### Step 4: Summary

Provide:

```markdown
## Work Summary
### Completed Steps
- <step> -- Done
### Files Created/Modified
- `path/to/file` -- <what changed>
### Tests
- X tests run, result
### Suggested Commits
- `feat(scope): description` -- files: ...
```

Then ask next action:
1. **`/cg-review <recommended-mode>`** -- Run staged review. Omit for `review:none`; if `review:auto` already dispatched, say "Review already dispatched with resolved mode: <mode>".
2. **`/cg-compound`** -- Capture learnings
3. **`/cg-fixbug`** -- Document fixed bug
4. **`/cg-plan`** -- Plan next

Wait for the user's response before proceeding.

## Rules

- Follow the plan; stop and discuss needed adjustments.
- Never skip required tests/docs.
- Preserve diagnostics discipline: test failures are not `@cg-fix-problems`; Problems errors may dispatch it.
- Keep commits focused.
- Ask before proceeding when a step is unclear.
