---
plan: .cg-docs/plans/2026-05-05-phased-plan-and-execution.md
findings:
  P0.1: fixed
  P0.2: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: fixed
  P1.7: fixed
  P1.vc1: open
  P1.vc2: fixed
  P1.vc3: fixed
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
  P2.14: skipped
  P2.15: fixed
  P2.16: fixed
  P2.17: fixed
  P2.18: fixed
  P2.19: fixed
  P2.20: fixed
  P2.21: fixed
  P2.22: fixed
  P2.23: fixed
  P2.24: fixed
  P2.25: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
  P3.7: fixed
  P3.8: skipped
  P3.9: fixed
  P3.10: fixed
  P3.11: skipped
  P3.12: skipped
  P3.13: fixed
  P3.14: fixed
  P3.15: fixed
---

## Review Report

**Review depth**: thorough  
**Branch**: main (not a feature branch — see P1.vc1)  
**Files reviewed**: 7 (`.github/prompts/cg-plan.prompt.md`, `.github/prompts/cg-work.prompt.md`, `.github/prompts/cg-resume.prompt.md`, `roadmap.json`, `tests/prompt-tools.Tests.ps1`, `.cg-docs/brainstorms/2026-05-05-phased-plan-and-execution.md` (untracked), `.cg-docs/plans/2026-05-05-phased-plan-and-execution.md` (untracked))  
**Agents dispatched**: cg-code-quality, cg-testing, cg-architecture, cg-adversarial, cg-documentation, cg-version-control, cg-reproducibility, cg-performance, cg-data-quality, cg-learnings-researcher  
**Findings**: 2 P0, 10 P1, 25 P2, 15 P3

---

## P0 — BLOCKING (immediate remediation required)

- **[P0.1]** [adversarial] `cg-work.prompt.md` Step 2.5 — **Write order for `completed-phases` + `current-phase` not specified; enables phase re-execution if crash occurs between writes**  
  If the agent crashes or is interrupted between writing `completed-phases: [N]` and setting `current-phase: N+1`, a subsequent no-arg run reads `current-phase: N` (still the old value) and may re-execute phase N.  
  **Fix**: Mandate atomic write order: "(1) append N to `completed-phases`; (2) then update or remove `current-phase`". Write `completed-phases` first — it is the authoritative completion record; `current-phase` is secondary.  
  > Note: architecture P2.12 recommends removing `current-phase` entirely. If accepted, P0.1 is automatically resolved.

- **[P0.2]** [adversarial] `cg-work.prompt.md` Step 2.5 — **YAML list format not enforced; string write silently breaks all downstream reads**  
  Step 2.5 says "create the field as `completed-phases: [N]`" but does not specify that N must be an unquoted YAML integer. A model could write `completed-phases: ["1"]` (string). Membership checks (`"1"` ≠ `1`) would then produce false negatives: sequential enforcement would fail to recognize phase 1 as complete, allowing phase 2 to start while phase 1 is re-executeable.  
  **Fix**: Add to Step 2.5: "Write as YAML flow sequence with unquoted integers (e.g., `completed-phases: [1]`, `completed-phases: [1, 2]`). Never use quoted strings (`"1"`) or block style. After writing, re-read the line and verify it matches this format."

---

## P1 — CRITICAL (must fix before merge)

- **[P1.1]** [code-quality] `cg-work.prompt.md` Step 2.5 — **Final-phase boundary is ambiguous; quality checks incorrectly skipped**  
  Step 2.5 item 5 always says "Continue to Phase N+1?" — but for the final phase, N+1 does not exist. Item 7 says "if user stops, halt and do NOT run Step 3" — but for the final phase, the user has no choice (there's nothing to continue to), so Step 3 must always run.  
  **Fix**: Add a branch: if phase N is the final phase (N = M), skip the continue/stop offer and proceed directly to Step 3 → Step 3.2 → Step 3.5 → Step 3.7.

- **[P1.2]** [adversarial, reproducibility] `cg-work.prompt.md` Step 1.2 — **`## Phase` inside fenced code blocks triggers false positive phased detection**  
  Any plan file whose narrative body (e.g., an example showing the phase structure) contains a fenced code block with `## Phase 1:` lines would be falsely classified as a phased plan. The `cg-plan` Step 3.5 template itself includes a fenced code block with example `## Phase` headers.  
  **Fix**: Amend the detection rule: "Scan for `## Phase` headers — ignore any occurrences inside fenced code blocks (delimited by ` ``` ` or `~~~`)."

- **[P1.3]** [adversarial] `cg-work.prompt.md` Step 1.2 — **No lower-bound validation; `phase0` passes the out-of-bounds check and reaches sequential enforcement with a nonsense error**  
  Out-of-bounds validation checks N > M. If N = 0, the check passes (0 ≤ M) and sequential enforcement is triggered with `phase -1` as prerequisite — which produces a confusing error.  
  **Fix**: Add lower-bound check: "If N < 1, halt with: 'Phase argument must be ≥ 1. `phase0` is not valid.'"

- **[P1.4]** [adversarial] `cg-resume.prompt.md` Step 2a — **Malformed `completed-phases` (non-integers, duplicates, strings) breaks the next-phase formula**  
  If a user manually edits frontmatter to `completed-phases: [done, 1, "2"]`, the formula "smallest integer not in list" would compute incorrect results or produce a parsing error.  
  **Fix**: Add a sanitization step: "Before computing X, deduplicate the list and discard any entries that are not positive integers. If any entry was discarded, warn: 'Unexpected values in `completed-phases` — frontmatter may have been edited manually. Proceeding with valid entries: [...]'"

- **[P1.5]** [adversarial] `cg-plan.prompt.md` Step 3.5 — **Adding or restructuring phases during plan refinement silently invalidates existing `completed-phases` data**  
  If a user re-runs `/cg-plan` on a partially executed phased plan (to add a phase or restructure), Step 3.5 would rewrite `## Phase` headers and `phases: N` without checking whether `completed-phases` is non-empty. The old completion record is now inconsistent with the new structure.  
  **Fix**: Add a pre-flight check to Step 3.5: "Before restructuring `## Phase` headers, check if `completed-phases` is non-empty in the plan frontmatter. If so, warn: 'This plan has completed phases recorded. Restructuring phases will invalidate the completion history. Continue anyway? [yes/no]'"

- **[P1.6]** [documentation] `docs/reference.md` — **`/cg-work` entry missing phase argument syntax**  
  The reference page documents `/cg-work` but does not mention the `[phaseX]` argument syntax added by this feature.  
  **Fix**: Add to the `/cg-work` entry: "Accepts optional `phaseX` argument (e.g., `/cg-work phase2`) to execute a specific phase of a phased plan."

- **[P1.7]** [documentation] `docs/reference.md` or `docs/workflow.md` — **New plan frontmatter fields (`phases:`, `completed-phases:`, `current-phase:`) not documented anywhere**  
  Users and future developers have no reference for what these fields mean, who writes them, or what values are valid.  
  **Fix**: Add a "Plan Frontmatter Reference" section (either in `docs/reference.md` or a new `docs/plan-schema.md`) documenting each field: type, valid values, writer (which prompt writes it), reader (which prompts read it), and whether the field is authoritative or a hint.

- **[P1.vc1]** [version-control] **Working directly on `main`; feature branches required by project convention**  
  All feature work should use a branch named `type/short-description`.  
  **Fix**: Retroactively move work to `feat/phased-plan-execution`. (Ask user before proceeding.)

- **[P1.vc2]** [version-control] **`.cg-docs/brainstorms/2026-05-05-phased-plan-and-execution.md` is untracked and must be committed**

- **[P1.vc3]** [version-control] **`.cg-docs/plans/2026-05-05-phased-plan-and-execution.md` is untracked and must be committed**

---

## P2 — IMPORTANT (should fix)

- **[P2.1]** [code-quality] `cg-work.prompt.md` Step 1.2 — **No-arg run when all phases already complete has undefined behavior**  
  If `completed-phases: [1, 2, 3]` for a 3-phase plan and user runs `/cg-work` with no arg, the "skip completed phases, run remaining" path has no remaining phases. The dispatch table does not define this case.  
  **Fix**: Add handling: "If all phases are complete (every phase 1..M is in `completed-phases`), display: 'All N phases are already complete. Nothing to run. Use `/cg-work phaseN` to re-run a specific phase if needed.'"

- **[P2.2]** [code-quality] `cg-work.prompt.md` Step 2.5 — **Hard-coded "sub-step 6" reference is fragile**  
  The phrase "skip Step 2 sub-step 6 for the final step of each phase" will silently break if Step 2 is renumbered.  
  **Fix**: Replace with description: "skip the per-step commit sub-step (the one that commits after each individual step) for the final step of each phase."

- **[P2.3]** [code-quality] `cg-work.prompt.md` Step 1.2 — **Out-of-bounds error list emoji labels undefined**  
  The error says "show a list of valid phases with status indicators" but does not define which emoji labels to use for `next` vs `not-started` vs `completed`.  
  **Fix**: Specify the label set, e.g.: "✅ completed (in `completed-phases`), 🔄 next (first incomplete), ⬜ not started (remaining)."

- **[P2.4]** [code-quality, architecture, reproducibility, data-quality, performance] `cg-resume.prompt.md` Step 2a — **`phases:` frontmatter hint used as fallback for M; two sources of truth can diverge**  
  `cg-resume` reads only frontmatter in its plan-scan loop and falls back to the `phases:` hint for M when headers are "not yet loaded." In practice, this is always — the hint is the de-facto value. If the plan is edited to add/remove a phase without updating `phases:`, `cg-resume` displays wrong progress and suggests the wrong next phase.  
  **Fix**: Remove the fallback. Change the rule to: "M = count of `## Phase` headers in the plan body. If the plan body has not yet been read, read it now." The `phases:` hint must never be used as the source of truth for M.  
  > Corollary (adversarial P2.17): If `phases:` is present but no `## Phase` headers exist in the body, cg-resume and cg-work will disagree. The fix above resolves this by making body-count authoritative in both prompts.

- **[P2.5]** [code-quality] `tests/prompt-tools.Tests.ps1` — **No regression test for no-arg sequential run skipping completed phases**  
  The core no-arg phased behavior ("skip phases already in `completed-phases`, run remaining") has no Pester assertion.  
  **Fix**: Add: `It "Step 1.2 no-arg phased path skips completed phases" { ($content -match 'skip.*completed|already.*completed-phases') | Should Be $true }`

- **[P2.6]** [testing] `tests/prompt-tools.Tests.ps1` — **Step 1.2 argument normalization forms completely untested**  
  The spec accepts `phase1`, `phase 1`, `Phase 1` (case-insensitive, strip spaces). No test verifies any of these forms are specified.  
  **Fix**: Add assertion: `It "Step 1.2 accepts case-insensitive phase argument forms" { ($content -match 'case.insensitive|phase 1.*phase1|strip.*spaces') | Should Be $true }`

- **[P2.7]** [testing] `tests/prompt-tools.Tests.ps1` — **Non-phased plan + phase arg warning branch untested**  
  The dispatch row "Non-phased plan | phaseX arg → warn + proceed as non-phased" is unverified.  
  **Fix**: Add: `It "Step 1.2 warns when phase arg given on non-phased plan" { ($content -match 'no phases|non.phased.*warn') | Should Be $true }`

- **[P2.8]** [testing] `tests/prompt-tools.Tests.ps1` — **Phase 1 exception to sequential enforcement not tested**  
  Phase 1 is exempted from sequential enforcement ("phase 1 is always allowed"). No test verifies this exception exists in the text.  
  **Fix**: Add: `It "Step 1.2 sequential enforcement exempts phase 1" { ($content -match 'phase 1.*always|except.*phase 1') | Should Be $true }`

- **[P2.9]** [testing] `tests/prompt-tools.Tests.ps1` — **cg-plan Lightweight and Standard scope phase offers untested**  
  Deep scope offer is tested. Standard scope ("offer but don't push") and Lightweight scope ("skip silently") are not.  
  **Fix**: Add two `It` blocks verifying the scope-conditional behavior text is present.

- **[P2.10]** [testing, code-quality] `tests/prompt-tools.Tests.ps1` — **cg-resume three-branch phase display: only 1 of 3 branches tested**  
  Requirement: absent `completed-phases` → show nothing; `completed-phases: []` → "0/M"; `completed-phases: [1, ...]` → "N/M. Next: `/cg-work phaseX`". Only the non-empty case is verified.  
  **Fix**: Add tests for the absent-field (no display) and empty-list ("0/M") branches.

- **[P2.11]** [testing] `tests/prompt-tools.Tests.ps1` — **Step 2.5 final-phase `current-phase` removal not tested**  
  "Remove `current-phase` if final phase" is a distinct code path with no assertion.  
  **Fix**: Add: `It "Step 2.5 removes current-phase frontmatter after final phase" { ($content -match 'remove.*current-phase|current-phase.*final') | Should Be $true }`

- **[P2.12]** [architecture] `cg-work.prompt.md` — **`current-phase` is a write-only field with no declared consumer**  
  Step 2.5 writes `current-phase` but no prompt (cg-work, cg-resume, cg-plan) reads or acts on it. It creates write-order risk (P0.1) and adds frontmatter noise without providing value.  
  **Fix**: Either (a) remove `current-phase` entirely — which also resolves P0.1 — or (b) formally specify at least one consumer in a prompt and add a test for it. Option (a) is recommended.

- **[P2.13]** [architecture] `cg-resume.prompt.md` Step 2a — **"All phases complete" state produces `/cg-work phase4` for a 3-phase plan**  
  When all phases are complete, X = (smallest integer not in completed-phases) = M+1. The display would read "Next: `/cg-work phaseM+1`" — which is an invalid phase argument.  
  **Fix**: Add a guard: "If `completed-phases` contains all integers 1..M (all phases complete), display: 'All N phases completed. Run `/cg-work` to proceed to final quality checks.' — do not display a phaseX suggestion."

- **[P2.14]** [architecture] `cg-work.prompt.md` Step 2.5 — **No lightweight quality gate at phase pause; quality debt accumulates silently**  
  When a user pauses between phases, Step 3.2 (fix diagnostics) and Step 3.5 (update roadmap) are skipped. Accumulated lint/type errors from earlier steps are deferred indefinitely.  
  **Fix**: Before the continue/stop offer in Step 2.5, add: "Run Step 3.2 lightweight diagnostics check (errors only, current-phase files). Report count to user."

- **[P2.15]** [architecture] `cg-plan-review.prompt.md` (`@cg-plan-critic`) — **No phase-structure review dimension**  
  `/cg-plan-review` dispatches `@cg-plan-critic` but the critic has no checklist item for phase structure. A phased plan with poorly-scoped phases, circular dependencies between phases, or missing sequential justification would not be flagged.  
  **Fix**: Add "Phase Structure" to `@cg-plan-critic`'s review dimensions: check that phases are cohesive, in a logical order, and that each phase has a clear completion criterion.

- **[P2.16]** [architecture] Cross-prompt — **No mechanism to re-open a completed phase**  
  Once a phase N is in `completed-phases`, there is no documented way to remove it and re-run it. A review finding in phase N's work could strand the user.  
  **Fix**: Document a recovery path (e.g., "To re-run phase N: manually remove N from `completed-phases` in the plan frontmatter, then run `/cg-work phaseN`").

- **[P2.17]** [adversarial] `cg-work.prompt.md` Step 1.2 — **Phase argument not re-evaluated after plan-loading fallback**  
  If the plan file is not found at the initial location but is recovered via a fallback path, the phase argument parsed in Step 1.2 uses the pre-fallback plan. If the fallback plan has a different phase count, the parsed phase N may now be out-of-bounds or map to a different step set.  
  **Fix**: After any plan-file fallback, re-run phase validation (re-count M from the recovered plan body; re-validate N against the new M).

- **[P2.18]** [adversarial] `cg-work.prompt.md` Step 1.2 — **`### N.` headings in preamble text are ambiguous; LLM may count them as phase steps**  
  The preamble (text above the first `## Phase` header) may contain `### N.` numbered headings (e.g., from a background context section). The phase-membership rule says "steps are `### N.` headings between `## Phase K:` and the next `## Phase`" — but if the LLM scans the entire document, it might include preamble headings.  
  **Fix**: Explicitly state: "Phase membership scan starts at the first `## Phase` header. Any `### N.` headings before the first `## Phase` header are preamble and are NOT steps of any phase."

- **[P2.19]** [documentation] `docs/workflow.md` — **Work section doesn't document `/cg-work phaseX` syntax**  
  **Fix**: Add phaseX invocation example to the workflow documentation.

- **[P2.20]** [documentation] `cg-work.prompt.md` frontmatter — **`[plan_file]` advertised in `description:` but not parsed by any step**  
  The updated description reads: "Supports `/cg-work [phaseX] [plan_file]`" — but no step in the prompt actually parses a `plan_file` argument.  
  **Fix**: Either (a) remove `[plan_file]` from the description, or (b) add Step 1.3 that parses the optional plan file path.

- **[P2.21]** [documentation] `docs/workflow.md` — **`/cg-resume` phase progress display not mentioned in user docs**  
  **Fix**: Add a note in the workflow docs that `/cg-resume` shows phase progress for in-progress phased plans.

- **[P2.22]** [version-control] `compound-gpid.context.md` — **Modified in git diff but not addressed in the proposed commit**  
  **Fix**: Review the diff, determine if the change is intentional, and either include it in the commit or revert it.

- **[P2.23]** [data-quality] `cg-work.prompt.md` Step 1.2 — **Absent `completed-phases` field not explicitly specified as equivalent to `[]`**  
  Sequential enforcement ("phase X-1 is not in `completed-phases`") does not define behavior when the field is absent. For phase 2 on a new phased plan, the enforcement could fail unpredictably.  
  **Fix**: Add: "If `completed-phases` is absent from the frontmatter, treat it as `[]` (empty list)."

- **[P2.24]** [data-quality] `cg-work.prompt.md` Step 1.2 — **No contiguous-range validation before no-arg phased run**  
  A manually edited `completed-phases: [1, 3]` on a 3-phase plan causes no-arg execution to run phase 2 only, skipping phase 3 silently.  
  **Fix**: Before proceeding in the no-arg phased path, validate: "All entries in `completed-phases` are positive integers in [1, M]. If any entry is out of range, warn the user and ask whether to proceed."

- **[P2.25]** [learnings] `tests/prompt-tools.Tests.ps1` — **No pipeline contract test between cg-plan → cg-work → cg-resume**  
  Per [testing-patterns/2026-03-30-prompt-pipeline-contract-testing.md], prompts that pass state to each other need joint interface tests. The `## Phase N:` header format emitted by cg-plan is consumed by cg-work (detection) and cg-resume (display) — but no test verifies the formats match.  
  **Fix**: Add contract tests:  
  ```powershell
  It "cg-plan phased template uses '## Phase N:' format (matches cg-work parser)" {
      ($planContent -match '## Phase \d+:') | Should Be $true
  }
  It "cg-resume /cg-work suggestion matches cg-work accepted phase arg format" {
      ($resumeContent -match '/cg-work phase\d') | Should Be $true
  }
  ```

---

## P3 — MINOR (nice to have)

- **[P3.1]** [code-quality] `tests/prompt-tools.Tests.ps1` — New `Describe` blocks lack section-header ID comments (used by other blocks for navigation in this file)

- **[P3.2]** [code-quality, testing] `tests/prompt-tools.Tests.ps1` — Standard scope phase offer in cg-plan not tested (only Deep scope is)

- **[P3.3]** [testing] `tests/prompt-tools.Tests.ps1` line ~3663 — `'does not exist'` pattern too broad; tighten to `'Phase \d+ does not exist'`

- **[P3.4]** [testing] `tests/prompt-tools.Tests.ps1` line ~3713 — cg-resume "in Step 2a" claim is not section-scoped; test could pass even if the text appears in a different step

- **[P3.5]** [testing] `tests/prompt-tools.Tests.ps1` — Silent `$permBlock = ""` fallback gives unhelpful error messages on assertion failure; add a guard `It` block: `"File Permissions section exists" { $permBlock | Should Not BeNullOrEmpty }`

- **[P3.6]** [documentation] `copilot-instructions.md` — Workflow Entry Points table doesn't mention phase support (e.g., "Implement a specific phase" → `/cg-work phaseX`)

- **[P3.7]** [documentation] `compound-gpid.md` — Current Focus section still lists the phased plan/execution work as active; should be updated now that it's done

- **[P3.8]** [version-control] Suggested commit message: `feat(workflow): add phased plan structure and phased execution to /cg-plan and /cg-work`

- **[P3.9]** [reproducibility, data-quality] `cg-work.prompt.md` Step 2.5 — `completed-phases` append form should specify flow-sequence style explicitly: "Always use `[1, 2, 3]` inline format — never YAML block style"

- **[P3.10]** [reproducibility] `cg-plan.prompt.md` Step 3.5 — Add a comment next to the `phases:` field in the plan template: `phases: 2  # convenience hint — may be stale; always recount from ## Phase headers`

- **[P3.11]** [performance] `cg-resume.prompt.md` Step 2a — Reword parenthetical to make the hint-first intent clear: "use the `phases:` frontmatter hint when available; only read the plan body if `phases:` is absent" (replaces the ambiguous "if headers are not yet loaded" phrasing)

- **[P3.12]** [architecture] `cg-work.prompt.md` — Phase logic complexity is embedded in the prompt rather than extracted to a skill; consider creating `cg-skill-phased-execution` for future reuse

- **[P3.13]** [learnings] `tests/prompt-tools.Tests.ps1` — Alternation pattern `status.*active.*phases|paused between phases` at line ~3686 has a potentially stale first branch; confirm both branches match current prompt text, or simplify to the more stable branch

- **[P3.14]** [learnings] `tests/prompt-tools.Tests.ps1` — cg-work `description:` frontmatter update (documented in implementation plan step 2a) has no Pester assertion verifying it was applied

- **[P3.15]** [data-quality] `@cg-roadmap` agent — No instruction to verify plan file paths exist before writing `plan:` to `roadmap.json`; add write-time validation to prevent stale references

---

## ✅ Passed / No Issues

- **cg-performance**: No P0/P1 issues. +28% token increase in cg-work is proportionate. Dispatch table is token-efficient. Test suite performance unchanged.
- **cg-learnings**: All 7 directly applicable past learnings were correctly applied (write-order, dead-step-after-wait, IndexOf position tests, guard conditions coverage, within-step preflight, forward dependency ordering, co-authored tests).
- **cg-data-quality**: `roadmap.json` plan paths verified present on disk. No P0/P1 data corruption paths identified.
- **cg-version-control**: No secrets or credentials found. `.gitignore` is correct. roadmap.json transitions follow conventions.
- **cg-reproducibility**: Test determinism confirmed (no external resources, timestamp, or random values). Lockfiles unaffected.
- **Test count**: 1,381/1,381 passing (per cg-performance agent).
