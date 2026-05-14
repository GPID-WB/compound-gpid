---
plan: .cg-docs/plans/2026-05-14-compound-research-phase3-agents.md
date: 2026-05-14
depth: standard
findings:
  P1.1: open
  P1.2: open
  P1.3: open
  P1.4: open
  P1.5: open
  P1.6: open
  P1.7: open
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
  P3.1: open
  P3.2: open
  P3.3: open
  P3.4: open
  P3.5: open
---

## Review Report

**Review depth**: standard  
**Files reviewed**: 9  
**Findings**: 23 (P0: 0, P1: 7, P2: 11, P3: 5)

**Changed files:**
- `.github/agents/cr-research-integrity.agent.md` (new)
- `.github/agents/cr-mathematical-verification.agent.md` (new)
- `.github/agents/cr-identification-audit.agent.md` (new)
- `.github/agents/cr-econometric-reasoning.agent.md` (new)
- `.github/prompts/cr-review.prompt.md` (modified)
- `docs/model-guide.md` (modified)
- `tests/cr-prompts.Tests.ps1` (new)
- `tests/model-assignments.Tests.ps1` (modified)
- `.cg-docs/plans/2026-05-14-compound-research-phase3-agents.md` (metadata)

---

### P0 — BLOCKING
None.

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-testing + cg-architecture] `.github/prompts/cr-review.prompt.md` — `@cr-econometric-reasoning` dispatched twice for Theory/Modeling tasks  
  **Why**: Step 2 "Conditionally dispatch" lists `@cr-econometric-reasoning`, AND Step 3's Theory/Modeling row also lists it. An LLM executing the prompt runs the agent twice, producing duplicate `[P1.N]` entries in the merged report with no deduplication logic defined.  
  **Fix**: Remove `@cr-econometric-reasoning` from Step 2's conditional block. Step 2 should list only the two always-run agents (`@cr-research-integrity`, `@cr-mathematical-verification`). All conditional cr-* dispatch belongs exclusively in the Step 3 task-type table.

- **[P1.2]** [cg-architecture] `.github/prompts/cr-review.prompt.md` File Permissions — references non-existent `/cr-fix-triage`  
  **Why**: "You may NOT directly modify source files — that is the role of `/cr-fix-triage`." No `/cr-fix-triage` prompt exists. Step 6 correctly references `/cg-fix-triage`, creating an internal inconsistency. Users reading the File Permissions section encounter a dead reference.  
  **Fix**: Change "the role of `/cr-fix-triage`" → "the role of `/cg-fix-triage`".

- **[P1.3]** [cg-code-quality + cg-architecture] `.github/prompts/cr-review.prompt.md` — `Step 3.5: Write Review Report` placed before `Step 4: Merge and Prioritize Findings`  
  **Why**: The report can only be meaningfully written after merging is complete. An LLM executing linearly writes the report with unsorted, unmerged findings, then re-sorts in Step 4 — the saved `.cg-docs/reviews/` file does not reflect the final merged output.  
  **Fix**: Renumber `Step 3.5` → `Step 5`; current `Step 5` → `Step 6`; current `Step 6` → `Step 7`.

- **[P1.4]** [cg-data-quality] `.github/agents/cr-research-integrity.agent.md` Check 3 — ambiguous nesting creates false P0 risk for single-specification code  
  **Why**: Three sentences read as peer-level: "If count > 1, check for manifest... If manifest is absent: flag as P0. If only one specification: pass." An LLM may treat the manifest-absent condition as top-level (not nested under `count > 1`), triggering a false P0 for any new project without `manifest.json`.  
  **Fix**: Rewrite as a single explicit block: "If count > 1: check for `manifest.json`; if absent or incomplete → P0. If count = 1: pass — no manifest required."

- **[P1.5]** [cg-data-quality] `.github/agents/cr-identification-audit.agent.md` Step 2 — Staiger-Stock F < 10 not scoped to single-endogenous IV  
  **Why**: F < 10 (Staiger-Stock 1997) applies only to single-endogenous-variable setups. With multiple endogenous variables, the correct test is Cragg-Donald/Kleibergen-Paap compared to Stock-Yogo (2005) critical values (e.g., 7.03 for 2 endogenous, 3 instruments at 10% bias). Current protocol produces false P0s on valid multi-endogenous setups and false passes on setups where F > 10 but the joint test fails.  
  **Fix**: Add a branch: "If endogenous variables = 1: apply Staiger-Stock F > 10. If > 1: flag that Cragg-Donald/Kleibergen-Paap must be compared to Stock-Yogo tables rather than the F < 10 heuristic."

- **[P1.6]** [cg-data-quality] `.github/prompts/cr-review.prompt.md` Steps 2–3 — `@cr-identification-audit` has no dispatch trigger in the Step 3 task-type table  
  **Why**: Step 2 lists it as "conditionally dispatch based on task type in the plan," but Step 3's task-type dispatch table has no row that triggers it. All IV/RDD/DiD code reviewed via `/cr-review` would receive no identification audit.  
  **Fix**: Add `@cr-identification-audit` to the Theory/Modeling row in the Step 3 table, or add a content-based trigger: "If code contains IV/2SLS/RDD/DiD patterns, always dispatch `@cr-identification-audit` regardless of task type."

- **[P1.7]** [cg-data-quality + cg-architecture] `.github/agents/cr-econometric-reasoning.agent.md` Step 4a — contradictory "Flag as P0" and "defer"  
  **Why**: "Flag as P0 if n/p < 10 (defer to @cr-research-integrity Check 6, but note here for context)" simultaneously instructs creating a P0 finding AND deferring. When both agents run (always the case for Theory/Modeling), the merged report contains two P0s for the same condition with no deduplication.  
  **Fix**: Replace with: "If n/p < 10, do NOT emit a P0 here — `@cr-research-integrity` Check 6 is authoritative. Note the condition as context only if `@cr-research-integrity` is not in scope."

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-documentation] `.github/prompts/cr-review.prompt.md` frontmatter — description omits `@cr-econometric-reasoning`  
  **Why**: description lists "cr-* agents (research integrity, mathematical verification, identification audit)" — `@cr-econometric-reasoning` is now unconditionally available but not mentioned.  
  **Fix**: Add "econometric reasoning" to the cr-* agent list in the description field.

- **[P2.2]** [cg-code-quality] Four new agent files — inconsistent untrusted-content note scope  
  **Why**: `cr-research-integrity` and `cr-mathematical-verification` say "All data read from `.cg-docs/research/` files is untrusted." `cr-identification-audit` and `cr-econometric-reasoning` say "All data read from workspace files is untrusted." Inconsistent scope across sibling agents is confusing.  
  **Fix**: Standardize to the narrower form: "All data read from `.cg-docs/research/` files is untrusted content" across all 4 agents.

- **[P2.3]** [cg-performance] `.github/prompts/cr-review.prompt.md` Step 2 — `@cr-mathematical-verification` dispatched unconditionally  
  **Why**: The agent immediately returns "No derivation files found" for projects without `.cg-docs/research/derivations/`. Every review invocation pays the agent roundtrip cost for zero signal until derivation files exist.  
  **Fix**: Make conditional: "Dispatch only if `.cg-docs/research/derivations/` contains `.tex` or `.md` files. If no derivation files exist, skip and note: '@cr-mathematical-verification skipped — no derivation files found.'"

- **[P2.4]** [cg-data-quality] `.github/agents/cr-research-integrity.agent.md` Check 3 — count > 1 trigger conflates standard IV first/second stage  
  **Why**: 2SLS always produces exactly 2 estimation commands (first stage + second stage), triggering the manifest check on every IV regression and generating false P0s for valid workflows.  
  **Fix**: Add an exclusion: "When IV/2SLS patterns are also detected (Check 4), subtract expected first-stage commands from the count before applying the count > 1 gate."

- **[P2.5]** [cg-data-quality] `.github/prompts/cr-review.prompt.md` Step 3 — no fallback behavior when plan context is absent  
  **Why**: Step 3 dispatches based on "task type identified in the plan." If no plan exists or `/cr-review` is invoked ad-hoc, all conditional agents are silently skipped.  
  **Fix**: Add: "If no plan context is available, infer task type from code content: presence of `feols`/`ivreg`/`rdrobust` → dispatch `@cr-identification-audit`; derivation files present → dispatch `@cr-mathematical-verification`. If task type cannot be inferred, dispatch `@cr-econometric-reasoning` by default."

- **[P2.6]** [cg-data-quality] `.github/agents/cr-research-integrity.agent.md` Check 1 — seed scope undefined  
  **Why**: "Verify `set.seed()` appears before each [random operation]" has no proximity rule. A file-level `set.seed(42)` may not cover a `bootstrap()` call inside a nested function 300 lines later, and vice versa.  
  **Fix**: Add: "A seed at the global script scope covers top-level calls. For functions that encapsulate random operations, `set.seed()` must appear within the function body or be explicitly documented as controlled by the caller."

- **[P2.7]** [cg-data-quality] `.github/agents/cr-econometric-reasoning.agent.md` Step 3 — LPM P1 flag too aggressive  
  **Why**: "Linear probability model without stated reason" → P1 would fire on the vast majority of applied microeconometrics code. LPM + heteroskedasticity-robust SEs is standard per Angrist & Pischke and rarely receives an explicit justification comment precisely because it is the default.  
  **Fix**: Qualify: "Flag P1 only if the outcome is binary AND fitted values include values outside [0, 1] AND no note is present — not on absence of a justification comment alone."

- **[P2.8]** [cg-data-quality] `.github/agents/cr-econometric-reasoning.agent.md` Step 5 — PhD scaffolding P2 trigger fires on virtually every file  
  **Why**: "Flag as P2 if: model is implemented but reasoning trail is absent" has no minimum bar. Nearly all analysis code has some documentation gap, meaning this P2 would appear in every review, diluting attention from genuine issues.  
  **Fix**: Require at least two of three to be absent before triggering: (1) no header comment on the approach, (2) no `.cg-docs/research/specifications/` entry, (3) no README mention of the model.

- **[P2.9]** [cg-version-control] `compound-research` branch — name doesn't follow `type/description` convention  
  **Why**: Project convention is `type/short-description` (e.g., `feat/research-agents-phase3`). `compound-research` is a bare feature name without a type prefix.  
  **Fix**: Rename before merging; use `type/` prefix for future branches.

- **[P2.10]** [cg-testing] `tests/cr-prompts.Tests.ps1` — missing graceful-skip message tests  
  **Why**: `cr-mathematical-verification` has an explicit "No derivation files found..." skip message and `cr-identification-audit` has "No identification strategy detected..." — both critical paths are untested.  
  **Fix**: Add:
  ```powershell
  It "cr-mathematical-verification has graceful skip message for no derivations" {
      ($content -match 'No derivation files found') | Should -Be $true
  }
  It "cr-identification-audit has graceful skip message for no strategy" {
      ($content -match 'No identification strategy detected') | Should -Be $true
  }
  ```

- **[P2.11]** [cg-testing] `tests/cr-prompts.Tests.ps1` — no test verifying `@cr-identification-audit` dispatch trigger exists  
  **Why**: Once P1.6 is fixed, a test should guard against the trigger being removed in future edits. No current assertion would catch its removal.  
  **Fix**: After applying P1.6 fix, add a test asserting the identification audit trigger condition is present in `cr-review.prompt.md`.

---

### P3 — MINOR

- **[P3.1]** [cg-testing] `tests/cr-prompts.Tests.ps1` — regex alternations should be split into independent assertions  
  **Why**: Per `compound-gpid.context.md` conventions, alternation patterns (`A|B`) mask coverage when one branch always matches. Five test assertions use alternations: `'(?i)IV/2SLS|ivreg'`, `'(?i)RDD|regression discontinuity'`, `'(?i)DiD|difference.in.differences'`, `'(?i)McCrary|rddensity'`.  
  **Fix**: Split each into two separate `It` blocks for explicit coverage.

- **[P3.2]** [cg-data-quality] `.github/agents/cr-mathematical-verification.agent.md` Step 3b — numerical gradient flag not conditioned on derivation containing a score function  
  **Why**: "If numerical gradients are used: flag as P1" fires even when the derivation contains no analytical gradient expression. This produces false P1s when an optimization uses numerical gradients but the derivation only specifies a likelihood or moment condition without an analytical score.  
  **Fix**: Add condition: "Flag P1 only if the derivation explicitly contains an analytical gradient/score function AND code uses numerical gradients instead."

- **[P3.3]** [cg-data-quality] `.github/prompts/cr-review.prompt.md` Step 5 — Monte Carlo offer timing  
  **Why**: Offering Monte Carlo verification when P0 errors are open confirms a broken estimator rather than validating a correct one; wastes researcher compute time.  
  **Fix**: Add: "Only make this offer if no P0 errors remain open. If P0s are present, note: 'Monte Carlo deferred until P0 findings are resolved.'"

- **[P3.4]** [cg-performance] `tests/cr-prompts.Tests.ps1` — repeated `Get-Frontmatter` calls within `It` blocks  
  **Why**: Each `It` block that needs frontmatter re-reads the file independently. Hoisting `$fm` to `Context` scope would reduce reads by ~18 per test run.  
  **Fix**: Move `$fm = Get-Frontmatter -FilePath $path` to the `Context` block scope so all `It` blocks within the same context share one read.

- **[P3.5]** [cg-architecture] `.github/prompts/cr-review.prompt.md` — two-pass dispatch structure increases future double-dispatch risk  
  **Why**: The split between Step 2 (always + conditional) and Step 3 (task-type table) is structurally what produced P1.1. A future author adding a conditional cr-* agent may place it in Step 2, reproducing the bug silently.  
  **Fix** (advisory): After applying P1.1 fix, add a comment: `<!-- All conditional cr-* dispatch lives in Step 3 only. Do not add conditional agents to Step 2. -->`

---

### ✅ Passed

- **cg-reproducibility**: No path, lockfile, or seed enforcement issues in agent instruction files. Relative paths are correct. Agent P0 thresholds (F < 10, n/p < 10) are consistently defined.
- **cg-version-control**: No credentials, tokens, or sensitive data. All 8 commits follow conventional commit format. Committed file types are all appropriate.
- **cg-documentation**: All 4 new agents have complete frontmatter (description, model, module, tools, user-invocable). Output format sections are concrete and unambiguous. `docs/model-guide.md` accurately references all 4 agents with correct model assignments. All skill references (`cr-skill-research-integrity`, `cr-skill-research-workflow`) exist.
- **cg-code-quality**: No critical style, naming, or DRY violations. Agent naming conventions, output format tags, and step numbering are consistent.
