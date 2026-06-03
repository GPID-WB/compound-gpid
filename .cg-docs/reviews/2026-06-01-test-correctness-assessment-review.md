---
plan: .cg-docs/plans/2026-06-01-test-correctness-assessment.md
date: 2026-06-03
depth: thorough
findings:
  P1.1: open
  P1.2: open
  P1.3: open
  P1.4: open
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
  P2.16: open
  P2.17: open
  P2.18: open
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: open
  P3.5: open
  P3.6: open
  P3.7: open
  P3.8: open
---

## Review Report

**Review depth**: thorough  
**Files reviewed**: 6 (`.github/prompts/cg-fixbug.prompt.md`, `.github/prompts/cg-work.prompt.md`,
`.github/skills/cg-skill-r-testing/SKILL.md`, `.github/skills/cg-skill-r-testing/references/test-integrity.md`,
`tests/prompt-tools.Tests.ps1`, `.cg-docs/plans/2026-06-01-test-correctness-assessment.md`)  
**Agents**: cg-code-quality, cg-testing, cg-documentation, cg-version-control, cg-reproducibility,
cg-performance, cg-architecture, cg-data-quality, cg-learnings-researcher, cg-adversarial  
**Findings**: 30 (P0: 0, P1: 4, P2: 18, P3: 8)

> Note: cg-documentation raised a P1 claiming `## When to Apply` is missing from
> `test-integrity.md`. Section exists at line 101; all 1141 Pester assertions pass. Discarded as
> false positive.

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-version-control] `roadmap.json` — Feature `fixbug-test-correctness-assessment`
  still has `"status": "idea"` and `"plan": null`. Work is fully implemented across two commits.  
  **Why**: Roadmap is stale; the feature appears unplanned to anyone reading the roadmap.  
  **Fix**: Via `@cg-roadmap`, set `"status": "done"` and `"plan": ".cg-docs/plans/2026-06-01-test-correctness-assessment.md"`. Commit as `chore(roadmap): mark fixbug-test-correctness-assessment done`.  
  **Tag**: [manual]

- **[P1.2]** [cg-adversarial] `.github/prompts/cg-work.prompt.md` — Red-phase gate skip condition
  lists **"prompt text"** as a structural category, which could exempt *all* prompt file edits from
  the red-phase gate — the primary use case for `/cg-work` in this project.  
  **Why**: An agent implementing a plan step that modifies a `.prompt.md` file could reason:
  "this is a prompt-text change, therefore structural, therefore skip red-phase." This makes the
  gate a no-op exactly where it's most needed (implementing new prompt protocols with colocated
  Pester tests).  
  **Fix**: Narrow the skip condition. Change `"prompt text, documentation, YAML frontmatter"` to
  `"markdown documentation or YAML frontmatter with **no colocated Pester assertions**"`. This
  preserves the skip for unverifiable prose-only changes while requiring red-phase when
  `prompt-tools.Tests.ps1` coverage exists for the changed content.  
  **Tag**: [manual]

- **[P1.3]** [cg-architecture] `.github/prompts/cg-fixbug.prompt.md` Step 2.5 and
  `.github/skills/cg-skill-r-testing/references/test-integrity.md` — Taxonomy tables already
  diverged at creation: `cg-fixbug` Step 2.5 has 2 columns (Category, Meaning); `test-integrity.md`
  has 3 columns (Category, Meaning, Typical Signal). Neither file references the other.  
  **Why**: Any future category addition to one table won't propagate to the other. Agents running
  `/cg-fixbug` see the thin table without detection signals; the richer version in `test-integrity.md`
  is invisible unless explicitly loaded. Drift is present at creation.  
  **Fix**: Add a pointer at the end of the Step 2.5 table: *"For typical signals distinguishing
  each category, see `cg-skill-r-testing/references/test-integrity.md — Test Gap Taxonomy`."*
  Add a reciprocal note in `test-integrity.md`.  
  **Tag**: [manual]

- **[P1.4]** [cg-learnings-researcher] `.github/prompts/cg-fixbug.prompt.md` Step 2 HARD STOP —
  Missing handler for the "test is **not** failing" response branch. The HARD STOP instructs the
  agent to wait for `'confirmed failing'` but provides no instruction for when the user replies
  "it passed" or "the test didn't fail."  
  **Why**: `2026-04-13-prompt-interaction-branch-completeness.md` documents: "Never leave a response
  branch implicit. Implicit behavior is undefined behavior for a language model." An agent receiving
  a "passed" reply has no handler and may proceed anyway.  
  **Fix**: Add after "Do NOT proceed to Step 2.5 until...":
  > "If the user indicates the test is **not** failing: the test does not detect the bug. Return to
  > the pre-check, revise the test (new input, tighter assertion, or different function call), and
  > request confirmation again. Do not advance to Step 2.5 until a genuinely failing test is
  > confirmed."  
  **Tag**: [manual]

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality / cg-testing / cg-reproducibility] `tests/prompt-tools.Tests.ps1:5386` —
  Dead first `$refPath` assignment with space typo (`. github\` with space). Immediately overwritten
  by the correct assignment on line 5387.  
  **Why**: Silently overwritten at runtime, but a future reader may think the space is intentional.
  If line 5387 is deleted, all 9 test-integrity assertions pass vacuously (`Test-Path` returns
  `$false` → `$content = ""` → every `$false` check passes).  
  **Fix**: Delete line 5386 (the `". github\"` line).  
  **Tag**: [safe_auto]

- **[P2.2]** [cg-code-quality / cg-documentation / cg-data-quality] `.github/prompts/cg-fixbug.prompt.md`
  Step 1.5 and Schema Rules — Source type #3 appears as three inconsistent strings:
  "Mathematical/statistical definition" (Step 1.5 prose), "Mathematical definition" (body template
  example), and `mathematical-definition` (Schema Rules slug, no "statistical").  
  **Why**: An agent filling in `expected-behavior-source` for a statistical derivation may write
  `mathematical-statistical-definition` or `mathematical/statistical definition` — neither is a
  valid slug value, producing a silently invalid schema field.  
  **Fix**: Update Step 1.5 display text to: `**Mathematical/statistical definition**
  (slug: \`mathematical-definition\`)`. Update the body template example to use the slug form.  
  **Tag**: [safe_auto]

- **[P2.3]** [cg-testing / cg-architecture / cg-data-quality] `tests/prompt-tools.Tests.ps1` —
  Layer 2 Describe block covers only 5/8 gap categories for `cg-fixbug.prompt.md`. Missing:
  `ambiguous-spec`, `fixture-gap`, `integration-gap`. All three could be silently deleted from the
  Step 2.5 table without a single Pester failure.  
  **Why**: The test-integrity.md Describe block's `foreach` loop guards the *reference file*, not
  the *prompt*. They are independent coverage targets.  
  **Fix**: Add 3 `It` blocks to the Layer 2 Describe block.  
  **Tag**: [safe_auto]

- **[P2.4]** [cg-testing / cg-data-quality] `tests/prompt-tools.Tests.ps1` — Layer 1 Describe
  block covers only 3/7 source types for `cg-fixbug.prompt.md`. Missing: `documentation`,
  `package-convention`, `external-reference`, `backward-compatibility-contract`.  
  **Why**: `documentation` is priority #2 and the most common source in day-to-day R work.
  All four could be silently removed from Step 1.5's enumerated list without a test failure.  
  **Fix**: Add `It` blocks for the missing source types (at minimum `documentation` and
  `backward-compat`).  
  **Tag**: [safe_auto]

- **[P2.5]** [cg-testing / cg-architecture] `tests/prompt-tools.Tests.ps1` — Schema Rules
  invariants for `expected-behavior-source` and `test-gap` not tested. Only `red-phase-confirmed`
  has a `"must"` constraint assertion. The rules for the other two new fields could be silently
  weakened ("should" vs "must") without a test failure.  
  **Fix**: Add 2 `It` blocks: `($content -match 'expected-behavior-source.*must')` and
  `($content -match 'test-gap.*must')`.  
  **Tag**: [safe_auto]

- **[P2.6]** [cg-testing / cg-learnings-researcher] `tests/prompt-tools.Tests.ps1` — No `IndexOf`
  ordering test verifying Step 1.5 appears *before* Step 2. A `-match` presence check cannot detect
  a section that was accidentally moved to after a HARD STOP (dead-step pattern documented in
  `2026-04-13-prompt-step-ordering-indexof-tests.md`).  
  **Fix**: Add an `It` block using `$content.IndexOf("### Step 1.5:")` vs
  `$content.IndexOf("### Step 2: Reproduce")` — former must be less than latter.  
  **Tag**: [safe_auto]

- **[P2.7]** [cg-learnings-researcher] `tests/prompt-tools.Tests.ps1` — No `IndexOf` ordering
  test verifying red-phase gate appears before `Step 2.5: Phase Boundary`. If the gate drifts past
  the phase boundary in a multi-phase plan, agents working on Phase 2+ steps never encounter it.  
  **Fix**: `$content.IndexOf("Red-phase verification")` must be less than
  `$content.IndexOf("Step 2.5: Phase Boundary")`.  
  **Tag**: [safe_auto]

- **[P2.8]** [cg-learnings-researcher] `tests/prompt-tools.Tests.ps1` — No `IndexOf` ordering
  test verifying Test Gap Classification appears *after* the `"confirmed failing"` hard stop phrase.
  If Step 2.5 were pulled before the hard stop, an agent could classify the gap before confirming
  the test fails — defeating the classification's evidential basis.  
  **Fix**: `$content.IndexOf("confirmed failing")` must be less than
  `$content.IndexOf("Test Gap Classification")`.  
  **Tag**: [safe_auto]

- **[P2.9]** [cg-documentation] `.cg-docs/plans/2026-06-01-test-correctness-assessment.md` —
  Plan status is `complete` (should be `completed` per `/cg-work` Step 3.5 spec). Plan also missing
  `completed-date: 2026-06-01` field. Future tooling indexing by `status: completed` will not find
  this plan.  
  **Fix**: Change `status: complete` → `status: completed`; add `completed-date: 2026-06-01`.  
  **Tag**: [safe_auto]

- **[P2.10]** [cg-version-control] `.cg-docs/brainstorms/2026-06-01-fixbug-test-correctness-assessment.md`
  — Brainstorm file is untracked (`??` in `git status`). All other plan-phase artifacts from this
  work were committed; this brainstorm is the only orphan.  
  **Fix**: `git add` and commit with the roadmap update (P1.1) or as a standalone `docs:` commit.  
  **Tag**: [safe_auto]

- **[P2.11]** [cg-architecture] `.github/skills/cg-skill-r-testing/references/test-integrity.md` —
  File lives in an R-only namespace and uses R code examples exclusively, but its taxonomy, mutation
  verification protocol, and detection signals are entirely language-agnostic. `/cg-fixbug` is
  trilingual.  
  **Fix**: Add a scope note near the top: *"Examples are in R, but the taxonomy and protocol apply
  equally to Python and Stata projects."*  
  **Tag**: [safe_auto]

- **[P2.12]** [cg-architecture] `.github/prompts/cg-fixbug.prompt.md` Step 1.5 — No instruction
  to load `cg-skill-r-testing` or `test-integrity.md`. The richer taxonomy (3-column with Typical
  Signal) is unreachable via explicit invocation during a bug-fix session.  
  **Fix**: Add to Step 1.5: *"R projects: load `cg-skill-r-testing` and its
  `references/test-integrity.md` for detection signals when classifying test gaps."*  
  **Tag**: [safe_auto]

- **[P2.13]** [cg-data-quality] `.github/prompts/cg-fixbug.prompt.md` Step 4 sub-point 6 —
  `fixture-gap` and `edge-case-gap` are excluded from the repair trigger (`wrong-test`,
  `circular-test`, `weak-test`) without explanation. Both are test-present-but-inadequate
  categories where repair is possible (add the triggering data shape to fixtures; add boundary
  condition tests).  
  **Fix**: Add footnote to Step 4 sub-point 6: *"For `fixture-gap` and `edge-case-gap`:
  add the triggering data shape or boundary input to the fixture/test rather than replacing
  existing assertions."*  
  **Tag**: [safe_auto]

- **[P2.14]** [cg-learnings-researcher] `tests/prompt-tools.Tests.ps1:5364` — Over-broad bare
  `structural` alternative in the cg-work red-phase gate skip-condition test:
  `($content -match 'structural|config files.*skip|skip.*structural')`. The bare `structural`
  matches any prose occurrence of the word, not specifically the skip condition.  
  **Why**: `2026-04-07-pester-test-quality-patterns.md` Pattern 2: stem-only matches are fragile.  
  **Fix**: Remove the bare `structural` alternative; tighten to:
  `($content -match 'config files.*skip|skip.*structural|purely structural')`.  
  **Tag**: [safe_auto]

- **[P2.15]** [cg-architecture] `.github/prompts/cg-fixbug.prompt.md` Step 1.5 and
  `.github/skills/cg-skill-r-testing/references/test-integrity.md` — Dual source-type lists with
  no cross-reference. Both are self-contained. If a type is added or renamed in one, the other
  won't track.  
  **Fix**: Add to end of Step 1.5 source list: *"See also `cg-skill-r-testing/references/test-integrity.md — Expected Behavior Sources` for source examples."*
  Add to `test-integrity.md`: *"This list mirrors the source types declared in `/cg-fixbug` Step 1.5."*  
  **Tag**: [safe_auto]

- **[P2.16]** [cg-documentation / cg-data-quality] `.github/skills/cg-skill-r-testing/references/test-integrity.md`
  — "Mutation Verification Protocol" section (a) uses a misleading name (actual content is the
  standard TDD red-green cycle, not mutation testing — which involves deliberate defect injection),
  and (b) describes only 4 steps while the authoritative `/cg-fixbug` Step 4 has 6 sub-points
  (missing: "failure matches reported symptom" and "existing tests pass / no regressions").  
  **Why**: A reader who memorizes the 4-step reference and uses it to audit a `/cg-fixbug` run will
  not notice that sub-points 2 and 5 were skipped.  
  **Fix**: Either rename to "Red-Green Verification Protocol" and add the 2 missing steps, or
  rename to "Mutation Verification Protocol" and add the plan-specified deliberate-defect injection
  step as an optional 5th step for P1 functions.  
  **Tag**: [manual]

- **[P2.17]** [cg-data-quality] `.github/prompts/cg-fixbug.prompt.md` Step 1.5 — Priority ordering
  inversion: `external-reference` (#6) ranks below `hand-computed-example` (#4). A hand-computed
  example is *derived from* an external reference; ranking the derivative source higher than its
  parent means an agent resolves conflicts by preferring a calculation over the published
  specification.  
  **Why**: For GPID welfare statistics (FGT indices, poverty lines, PPP vintages), a methodology
  note from the World Bank Poverty Handbook is more authoritative than any team-computed example.
  The inversion is most dangerous when the hand-computed example contains an error the methodology
  note would have caught.  
  **Fix**: Swap ranks: move `external-reference` to #4, `hand-computed-example` to #6. Update
  `test-integrity.md` table row ordering to match.  
  **Tag**: [manual]

- **[P2.18]** [cg-learnings-researcher] `.github/prompts/cg-fixbug.prompt.md` Step 2 pre-check —
  No escape hatch when the test runner is unavailable during the existing-test pre-check instruction
  ("run it on the current buggy code"). The analogous escape hatch exists in `/cg-work`
  ("Could not establish failing baseline") but is absent from the equivalent Step 2 pre-check.  
  **Why**: `2026-03-13-regression-test-trycatch-guard-clm-environment.md` documents that
  CLM/OneDrive environments prevent test invocation; the pre-check could block with no recovery
  path.  
  **Fix**: Add after the pre-check sub-bullets: *"If tests cannot be run (CLM restriction,
  missing test runner): log 'Test runner unavailable — skipping existing-test pre-check. Writing
  new failing test from the expected behavior source declared in Step 1.5.' and proceed."*  
  **Tag**: [manual]

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-learnings-researcher] `tests/prompt-tools.Tests.ps1` — Dead second alternative
  in "Do NOT proceed" test regex: `($content -match 'Do NOT proceed to Step 2 until|before.*expected behavior')`.
  The first alternative always matches; `before.*expected behavior` is broad dead code.  
  **Fix**: Remove the second alternative; keep only `'Do NOT proceed to Step 2 until'`.  
  **Tag**: [safe_auto]

- **[P3.2]** [cg-documentation] `.github/skills/cg-skill-r-testing/SKILL.md:373` — Cross-reference
  line leads with content description rather than a "when to load" trigger, unlike all other entries
  in the section.  
  **Fix**: Change to: *"Load when fixing bugs or reviewing tests for tautology. Covers expected
  behavior sources, mutation verification protocol, test gap taxonomy, and tautological test
  detection."*  
  **Tag**: [safe_auto]

- **[P3.3]** [cg-testing] `tests/prompt-tools.Tests.ps1` — Layer 3 Red-Green Proof Describe block
  has no test for the "Only after all six sub-points are confirmed" gate language that makes Step 4
  a hard stop.  
  **Fix**: Add `It "Step 4 requires all six proof points before confirmation"` with
  `($content -match 'Only after all six|six sub-points') | Should -Be $true`.  
  **Tag**: [safe_auto]

- **[P3.4]** [cg-code-quality] `.github/prompts/cg-fixbug.prompt.md:50` — Step 1.5 heading uses
  `— MANDATORY` while Steps 2 and 4 use `— HARD STOP`. Step 1.5 body says "Do NOT proceed" —
  semantically a hard stop — but the heading is labelled differently.  
  **Fix**: Either rename to `— HARD STOP` for consistency, or add a comment noting the distinction:
  `MANDATORY` = agent-enforced gate; `HARD STOP` = user-confirmed gate.  
  **Tag**: [advisory]

- **[P3.5]** [cg-documentation] `.github/prompts/cg-fixbug.prompt.md` Step 2.5 — Table omits the
  "Typical Signal" column present in `test-integrity.md`. Acceptable as intentional brevity in a
  prompt, but undocumented.  
  **Fix**: Add a note at end of the table: *"For typical signals distinguishing each category, see
  `cg-skill-r-testing/references/test-integrity.md`."* (Also addresses P1.3.)  
  **Tag**: [advisory]

- **[P3.6]** [cg-learnings-researcher] `docs/reference.md` — `/cg-fixbug` entry still reads
  "intake → reproduce (hard stop) → diagnose → fix (hard stop) → document." Does not reflect
  the new three-layer protocol (Step 1.5, Step 2 diagnostic fork, Step 2.5).  
  **Fix**: Update to: "intake → expected-behavior source (Step 1.5) → reproduce with diagnostic
  fork (hard stop) → test-gap classification (Step 2.5) → diagnose → fix with red-green proof
  (hard stop) → document."  
  **Tag**: [advisory]

- **[P3.7]** [cg-data-quality / cg-documentation] `.github/prompts/cg-fixbug.prompt.md` Step 2.5 —
  `circular-test` and `wrong-test` overlap is undocumented. Every `circular-test` is a `wrong-test`,
  but not vice versa. Agents may misclassify inconsistently.  
  **Fix**: Add footnote: *"Note: `circular-test` is a subcategory of `wrong-test`. Prefer
  `circular-test` when the root cause is the derivation method (expected value was computed by
  running the implementation). Use `wrong-test` when expected values are incorrect for other
  reasons."*  
  **Tag**: [advisory]

- **[P3.8]** [cg-code-quality] `.github/skills/cg-skill-r-testing/references/test-integrity.md`
  — "Mutation Verification Protocol" describes a 4-step sequence but `/cg-fixbug` Step 4 has 6
  sub-points. A reader consulting only the reference will miss the symptom-match check (sub-point 2)
  and the regression check (sub-point 5).  
  **Fix**: Add one sentence at the end of the section: *"When using this protocol in `/cg-fixbug`,
  also confirm the failure message matches the reported symptom and that existing tests show no
  regressions (Step 4, sub-points 2 and 5)."*  
  **Tag**: [advisory]

---

### ✅ Passed

- **cg-reproducibility**: No hardcoded absolute paths; `$PSScriptRoot`-based paths used correctly;
  `test-integrity.md` is self-contained with no external dependencies.
- **cg-performance**: No catastrophic regex backtracking; repeated file reads are immaterial at
  this scale.
- **cg-version-control**: Commit messages follow conventional commits; no secrets or credentials
  committed; branch name correct; `.gitignore` complete.
- **cg-code-quality**: YAML schema template syntactically valid; hard stop formatting in Steps 2
  and 4 consistent; all 8 gap category names match exactly between Step 2.5 and test-integrity.md;
  `cg-work.prompt.md` sub-step numbering continues correctly.
- **cg-learnings-researcher (design confirmations)**: Diagnostic fork correctly operationalizes
  `2026-04-15` post-mortem; "NOT a hard stop" in `/cg-work` correctly avoids dead-step risk per
  `2026-04-13` lesson; diagnostic fork branch completeness follows `2026-04-13` pattern.
