---
name: cr-skill-research-integrity
module: research
description: "Catalog of P0 silent research errors with detection patterns and
  remediation. Covers code-math mismatch, specification searching, identification
  theater, unseeded randomness, asymptotic-assumption violations, wrong SE
  clustering, and untested distributional assumptions. Loaded by @cr-research-integrity
  and /cr-review."
---

# Research Integrity: P0 Silent-Error Catalog

This skill provides detailed detection patterns and remediation guidance for
each class of P0 silent research error. These errors produce incorrect results
without raising warnings or exceptions.

---

## Error Class 1: Code-Math Mismatch

**What it is**: The implementation does not faithfully translate the mathematical
derivation. Variable names, functional forms, or operations diverge between the
LaTeX/markdown derivation and the code.

**Detection patterns**:
1. Read the derivation file in `c-research/derivations/`
2. Build a variable mapping table: derivation symbol → code variable name
3. Check that each transformation in the derivation has a corresponding code operation
4. Check functional forms: `log(x)` in derivation means `log(x)` in code — not `log(x+1)`
5. Check summation limits: if derivation sums over `i=1..N`, code must loop or vectorize over the same index

**Remediation**:
- Create a variable mapping table in `c-research/specifications/`
- Add inline comments in the code linking each computation to the derivation equation number
- If a simplification was made (e.g., numerical approximation), document it explicitly

**Example**:
```
Derivation: β = (X'WX)^{-1} X'Wy   # weighted OLS with weight matrix W
Code: lm(y ~ X)                      # unweighted — MISMATCH
Fix:  lm(y ~ X, weights = w)
```

---

## Error Class 2: Specification Searching

**What it is**: Running many model specifications and reporting only the
preferred result without disclosing the search process. Creates spurious
false-discovery rates.

**Detection patterns**:
1. Read `c-research/results/manifest.json`
2. Count the total number of estimation runs logged
3. Compare against the number of specifications reported in the paper/output
4. If (logged runs) > (reported specs) by a large margin: flag for review
5. Check for patterns: multiple runs with the same dependent variable but different controls

**Remediation**:
- Report all specifications in an appendix table
- Alternatively: document the pre-specified selection criterion (e.g., "Akaike IC minimization") and show it was applied before seeing results
- Use pre-registration for confirmatory work

**Red flags**:
- `manifest.json` shows 20+ estimation runs but paper reports 3
- Different standard error specifications tested without disclosure
- Sample restriction varied across runs with no documented reason

---

## Error Class 3: Identification Theater

**What it is**: Claiming a causal identification strategy without running the
required diagnostic test to support the claim.

**Detection patterns**:
Check for the claimed strategy AND the required diagnostic:

| Claimed Strategy | Required Diagnostic | Code Indicator |
|-----------------|---------------------|----------------|
| IV/2SLS | First-stage F ≥ 10 (or Montiel-Pflueger) | `estat firststage`, `ivreg2` with `first` option |
| Regression Discontinuity | McCrary density test + bandwidth selection | `rddensity`, `rdplot` |
| Difference-in-Differences | Parallel trends (visual + statistical) | Event-study plot; pre-trend F-test |
| Propensity Score Matching | Common support / overlap check | `pscore`, trimming, balance table |
| Synthetic Control | Donor pool pre-period fit | Pre-period RMSPE |

**Remediation**:
- Run the required diagnostic immediately after fitting the model
- If the diagnostic fails: revisit the identification strategy; do not proceed to results
- If the diagnostic is infeasible: document why and acknowledge the limitation in the paper

---

## Error Class 4: Unseeded Randomness

**What it is**: Code that uses randomness (bootstrap, simulation, CV, random
forests, train/test split) without an explicit random seed. Results change on
every run, preventing exact reproducibility.

**Detection patterns**:
Scan code files for these functions/patterns WITHOUT a preceding seed:

| Language | Random Functions to Check | Seed Function |
|----------|--------------------------|---------------|
| R | `sample()`, `rnorm()`, `runif()`, `boot()`, `cv.glm()`, `randomForest()`, `sample_n()`, `createFolds()` | `set.seed(N)` |
| Python | `np.random.*`, `random.*`, `sklearn.model_selection.*`, `torch.*`, `keras.*` | `rng = np.random.default_rng(N)` (modern, preferred) or `np.random.seed(N)` (legacy, accepted) |
| Stata | `bootstrap`, `simulate`, `permute` | `set seed N` |

**Remediation**:
1. Add `set.seed(<n>)` / `np.random.seed(<n>)` / `set seed <n>` immediately before the first random call in each code block
2. Choose seed values deliberately (e.g., 42, 12345) — document why in `c-research/results/manifest.json`
3. For bootstrap: set seed once before the bootstrap call, not inside the bootstrap function

---

## Error Class 5: Asymptotic Assumption Violations

**What it is**: Using estimators that require large samples in settings where
the sample is too small for the asymptotic approximation to be reliable.

**Detection patterns**:
1. **MLE**: Check `n/p` ratio (number of observations / number of parameters). Flag if `n/p < 10`
2. **Clustered SE**: Check number of clusters. Flag if fewer than 30-50 clusters (Cameron-Miller rule of thumb)
3. **HAC/Newey-West**: Check time series length. Flag if `T < 50` with long lags
4. **Nonparametric estimators**: Check bandwidth relative to sample size
5. **Fixed effects**: Check for thin cells (few obs per FE unit)

**Remediation**:
- With few clusters: use wild cluster bootstrap instead of standard clustered SE
- With small n/p: use regularization (ridge, LASSO) or reduce model complexity
- With thin FE cells: drop or combine small cells; check for incidental parameter bias
- Always: acknowledge the limitation explicitly in the paper

---

## Error Class 6: Wrong SE Clustering

**What it is**: Clustering standard errors at the wrong level — typically
at a higher level than the treatment variation, or failing to cluster when
treatment is clustered.

**Detection patterns**:
1. Identify the level at which treatment varies (county, firm, household)
2. Identify the level at which SEs are clustered in the code
3. Flag if clustering level < treatment variation level (under-clustering)
4. Flag if clustering level >> treatment variation level without justification
5. Check for multi-way clustering when treatment varies along multiple dimensions

**Example mismatches**:
```
Treatment varies at: county level (N=500 counties)
SE clustering at:    individual level  → UNDER-CLUSTERED (too small SE)
SE clustering at:    state level       → may be fine, but document why
```

**Remediation**:
- Match clustering level to treatment variation level
- If two-way clustering needed: use `ivreg2` with `cluster(id1 id2)` or R's `sandwich` package
- Document the clustering choice in the empirical strategy section

---

## Error Class 7: Distributional Assumption Untested

**What it is**: The model assumes a specific distributional form (normal errors,
log-normal wages, Pareto tail for top incomes) but no empirical test of that
assumption is run.

**Detection patterns**:
1. Identify distributional assumptions in the model:
   - OLS: normal errors (for inference, not consistency)
   - Probit/Logit: normal/logistic CDF
   - Tobit: normal errors
   - MLE: distributional likelihood specified
2. Check whether a diagnostic test was run:
   - Normality: Shapiro-Wilk, QQ-plot, Jarque-Bera
   - Homoskedasticity: Breusch-Pagan, White test
   - Distributional fit: KS test, histogram vs. theoretical density

**Remediation**:
- Run the relevant diagnostic before reporting results
- If assumption fails: use robust inference (HC3 SE for heteroskedasticity)
- If distributional test is infeasible: acknowledge in the paper and explain why robustness is still plausible
- For welfare/poverty work: always test whether welfare distribution is non-negative (welfare ≥ 0)

---

## Error Class 8: Measurement Comparability Breakdown

**What it is**: Rankings or classifications are compared across vintages or
across units without harmonized definitions, stable coverage, or explicit
change attribution.

**Detection patterns**:
1. Check `c-research/vintages/` for vintage manifests tied to the study.
2. Verify over-time comparisons record coverage and method changes.
3. Verify cross-unit comparisons document harmonized definitions/coverage.
4. Flag as P0 when comparisons are asserted without attribution artifacts.

**Remediation**:
1. Produce or update vintage manifest with coverage and method deltas.
2. Add harmonization notes before ranking across units.
3. Separate real-change claims from coverage/method artifacts.

---

## Error Class 9: Spurious Cluster Or Classification Claim

**What it is**: Cluster labels or classification boundaries are presented as
stable findings without validity/stability evidence.

**Detection patterns**:
1. Check `c-research/measurement/cluster-validity.yaml` exists.
2. Verify selected `k` plus validity indices are recorded.
3. Verify stability metrics are present for the selected solution.
4. Flag as P0 when classification claims lack any validity artifact.

**Remediation**:
1. Generate cluster-validity artifact with index and stability summaries.
2. Downgrade unsupported cluster/classification claims until validated.
3. Reframe uncertain boundaries as exploratory, not definitive.

---

## Error Class 10: Normative-Choice Smuggling

**What it is**: A consequential value-laden choice (for example weighting,
threshold setting, inclusion boundaries, or framing baseline) is treated as a
technical default without explicit human approval in the per-study normative
register.

**Detection patterns**:
1. Identify consequential choices that can change ranking, threshold
   classification, or distributional interpretation.
2. Check `c-research/normative-decisions/<study-slug>.md` for a matching
   entry with a stable `ND-<study-slug>-NNN` ID.
3. Verify required fields are present: `study`, `plan`, `applies_to`,
   `defensible_options`, `consequences`, `decided_by`, `decision`,
   `justification`, `decided_on`.
4. Flag as P0 if `decided_by` is missing or equals `default`.
5. Flag as P0 if no matching entry covers the current artifact/step via
   `applies_to`.

**Remediation**:
1. Surface the choice explicitly to the human decision-maker.
2. Record defensible alternatives and likely consequences, including expected
   ranking or threshold shifts.
3. Capture explicit human decision and value-based justification in the
   per-study normative register before proceeding.
4. Add or update `applies_to` links so downstream steps can reuse coverage
   deterministically.

---

## Error Class 11: Fabricated or Unverifiable Citation

**What it is**: A cited source, DOI, quote, page, or locator cannot be mapped
to a verifiable source record in the provenance ledger and converted evidence
artifacts.

**Detection patterns**:
1. Check `c-research/evidence/provenance-ledger.yaml` for the cited source.
2. Confirm `source_id` exists and `original_path` is resolvable.
3. Verify claimed locator maps to converted evidence content.
4. Flag if DOI/quote/page is asserted without resolvable source linkage.

**Remediation**:
1. Remove unverifiable claims or replace with verifiable citations.
2. Add complete provenance entries with valid source and locator linkage.
3. Never fabricate likely-looking citation metadata.

---

## Error Class 12: Uncited Substantive Claim

**What it is**: An empirical or methodological assertion appears in output
without a verified row in the claim-evidence matrix.

**Detection patterns**:
1. Scan substantive claims in outputs or summaries.
2. Verify each claim appears in
   `c-research/evidence/claim-evidence-matrix.yaml`.
3. Require `status: verified` for publishable assertions.
4. Flag claims with missing entries or non-verified status as P0.

**Remediation**:
1. Add a matrix row and attach verifiable evidence, or
2. Downgrade claim status to `unverified`/`abstained` and remove from final claims.
