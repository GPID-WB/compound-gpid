---
date: 2026-05-21
plan: .cg-docs/plans/2026-05-20-compound-research-phase5-ml-economics.md
findings:
  P1.1: fixed
  P1.2: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
---

## Review Report

**Review depth**: standard
**Commit reviewed**: `edf342b` — feat(compound-research): apply Phase 5 ML-economics review fixes
**Files reviewed**: 9
**Findings**: 12 (P0: 0, P1: 2, P2: 7, P3: 3)

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-code-quality] `.github/agents/cr-ml-methodology.agent.md:66,93,118,146,179,208,230` — Inline "Flag as" directives in Checks 1–7 use old format `**[cr-ml-methodology] [P0.N]**`; Check 8 (newly added) uses new format `**[P0.N]** [cr-ml-methodology]`; output template also uses new format.
  **Why**: When an agent reasons check-by-check, it follows the proximal "Flag as" instruction, not the distant output template. Checks 1–7 may produce old-format findings while Check 8 produces new-format findings, making compiled review reports inconsistent and potentially unparseable by `/cg-fix-triage`.
  **Fix**: Update all 7 "Flag as" directives (lines 66, 93, 118, 146, 179, 208, 230) to `Flag as **[P{severity}.N]** [cr-ml-methodology]`.

- **[P1.2]** [cg-code-quality] `.github/agents/cr-specification-analysis.agent.md:100,129,152,176,193` — Same issue: Check 1 (line 65) uses new format `**[P0.N]** [cr-specification-analysis]`; Checks 2–6 (lines 100, 129, 152, 176, 193) use old format `**[cr-specification-analysis] [P1/P2.N]**`; output template uses new format. Also: line 65 uses lowercase `flag` — inconsistent capitalisation.
  **Fix**: Update all 5 "Flag as" directives to priority-first format. Normalize `flag` → `Flag` on line 65.

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-testing] `tests/cr-prompts.Tests.ps1:787` — Test coverage downgrade. The P3.3 fix replaced `'(?i)not enabled|run.*cg-setup|proceed anyway'` with `'(?i)research.*module'`. The old test verified concrete warning text; the replacement only confirms the phrase "research module" exists anywhere in the file.
  **Why**: The cr-brainstorm.prompt.md has "Research module is not enabled. Run `/cg-setup` to add it, or proceed anyway?" — the old test was behavioural; the new test is vacuous.
  **Fix**: Split into three independent assertions:
  ```powershell
  It "warns that research module is not enabled" {
      ($content -match '(?i)not enabled') | Should -Be $true
  }
  It "offers /cg-setup to enable the module" {
      ($content -match '(?i)\/cg-setup') | Should -Be $true
  }
  It "offers proceed anyway fallback" {
      ($content -match '(?i)proceed anyway') | Should -Be $true
  }
  ```

- **[P2.2]** [cg-architecture] `.github/agents/cr-ml-methodology.agent.md:39` — Empty-file guard not updated after adding Check 8. Guard reads: "Do not run Checks 1–7 against empty files." Check 8 (Survey Weight Usage — P0) was added in this commit but the guard was not updated.
  **Fix**: Change to "Do not run Checks 1–8 against empty files."

- **[P2.3]** [cg-architecture] `.github/skills/cr-skill-ml-economics/SKILL.md:112` — Sections 2a (Survey-Weighted ML) and 2b (Missing Data) are sub-sections under "Section 2: Penalized Regression". Both contain `ranger()`, `xgb.DMatrix()`, and `sklearn` examples — tree-based methods that belong to Section 3. Practitioners consulting Section 3 for random-forest patterns will miss the GPID survey-weight and missing-data requirements.
  **Fix**: Add a cross-reference note at the start of Section 3: "> **GPID cross-cutting requirements** (survey weights, missing data) apply to ALL ML methods — see Sections 2a and 2b before implementing any estimator."

- **[P2.4]** [cg-data-quality] `.github/skills/cr-skill-ml-economics/SKILL.md:167` — Weight normalisation anti-pattern states an incorrect rationale: "estimator expects unnormalised probability weights." None of the four listed estimators require unnormalized weights. The real concern for `cv.glmnet` is lambda-grid scale comparability across runs.
  **Fix**: Replace second bullet with: "Normalising weights (`weights / sum(weights)`) changes the lambda scale in `cv.glmnet` — the CV-selected `lambda.min` is not comparable across model runs with different weight normalisations. Prefer raw probability weights throughout a pipeline."

- **[P2.5]** [cg-data-quality] `.github/skills/cr-skill-ml-economics/SKILL.md:200,208` — `mice(m=1)` is labeled "Multiple imputation" in the strategy table and section header. `m=1` is single imputation (one draw from the PMM posterior) — not multiple imputation. A practitioner using this code for econometric inference would have underestimated standard errors with no warning.
  **Fix**: Either change `m = 1` → `m = 5` with pooling guidance, OR update the table cell and code comment to: "Single imputation (PMM) per fold — use `m ≥ 5` with Rubin's rules for inference; `m=1` is sufficient for ML prediction."

- **[P2.6]** [cg-data-quality] `.github/skills/cr-skill-ml-economics/SKILL.md:210` — Test-fold imputation is documented only as a comment stub: `# Fit model on train_complete; impute test fold using the same mice object`. No working code shown. A practitioner filling this gap will likely call `mice(test_df)` independently — imputing from test-fold marginal distributions (data leakage).
  **Why**: `mice` objects have no `transform()` method equivalent.
  **Fix**: Replace the comment with:
  ```r
  # Option A: mice.reuse() (mice >= 3.16)
  test_imputed  <- mice.reuse(train_imputed, test_df, seed = 42)
  test_complete <- complete(test_imputed)
  # Option B: tidymodels — use step_impute_bag() in a recipe;
  # prep() fits on train fold, bake() applies fitted imputer to test fold
  ```

- **[P2.7]** [cg-data-quality] `.github/skills/cr-skill-ml-economics/SKILL.md:346` — AUROC listed as primary metric for rare outcomes ("Default to **AUROC**, **precision-recall AUC**, or **F1**…"). At 2–5% positive rates (GPID program take-up, extreme poverty flagging), AUROC stays high (≥ 0.85) for near-useless classifiers because it is dominated by true-negative pairs. PR-AUC is the appropriate primary metric under severe class imbalance.
  **Fix**: Reorder: "Default to **precision-recall AUC** as primary metric; supplement with AUROC as a secondary check. At prevalence below 5%, AUROC remains high even for near-useless classifiers (Davis & Goadrich 2006)."

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-testing] `tests/cr-prompts.Tests.ps1:882` — New "contains MSM and SMM estimation references" test uses `'\bMSM\b|\bSMM\b'` alternation. Test name asserts "AND" but regex verifies "OR". Residual alternation masking — same pattern as P3.3 fixes applied in this commit.
  **Fix**: Split into two `It` blocks: one for `'\bMSM\b'`, one for `'\bSMM\b'`.

- **[P3.2]** [cg-data-quality] `.github/skills/cr-skill-ml-economics/SKILL.md:223,376` — "Section 1 Check 1" cross-references (×2) are broken. SKILL.md has no numbered checks — "Section 1" covers "When ML Is Appropriate" with no sub-checks.
  **Fix**: Replace both occurrences with: "(data leakage — see Check 1 in cr-ml-methodology.agent.md for the full detection protocol)".

- **[P3.3]** [cg-testing] `tests/cr-prompts.Tests.ps1:1267` — Check 5 cross-reference test uses alternation `'(?i)cross.reference.*cr-research-integrity|cr-research-integrity.*Check 1'`. The two branches are not semantically equivalent — if only `@cr-research-integrity Check 1` appeared without "cross-reference", the test would still pass.
  **Fix**: Tighten to require both in sequence: `'(?i)cross.reference.*cr-research-integrity.*Check 1'`.

### ✅ Passed

- **cg-version-control**: Conventional commit format, clean scope, no secrets, feature branch — no issues.
- **cg-performance**: `BeforeAll` hoist in `model-assignments.Tests.ps1` correctly scoped for Pester 4; Phase 5 `Describe` body assignments confirmed equivalent to `BeforeAll`.
- **cg-reproducibility**: PCA fix (removing `random_state=42` from variance-ratio call) technically correct; seed table extensions (PyTorch CPU+GPU, TensorFlow/Keras) accurate and complete; `uv lock` + `uv export` pattern correct.
- **cg-documentation**: SKILL.md Sections 2a/2b contain working code examples with GPID context; Check 8 gives adequate weight-detection guidance; weight variable names list accurate for GPID surveys.
- **cg-architecture** (passing areas): Both new CR agents follow established agent pattern; dispatch table is non-circular; CR skills order in `copilot-instructions.md` correct.
- **cg-data-quality** (passing areas): Weight API calls correct across R/Python/Stata; `class_weight='balanced'` appropriate; SMOTE guidance (inside CV fold only) technically correct; MCAR/MAR/MNAR table accurate for poverty surveys; P0/P1 severities on new anti-patterns entries correct.
