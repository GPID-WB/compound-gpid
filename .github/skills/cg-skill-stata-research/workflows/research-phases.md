# Research Phases

Structured workflow for analytical projects in GPID. Every project follows
six phases with explicit pause points. This workflow applies to poverty
assessments, analytical reports, academic papers, and any analysis producing
official World Bank statistics.

Philosophy: design before data, identify before estimate, verify before
publish. AI assists at every phase but does not decide — the researcher
decides. (Adapted from Cunningham's AI workflow for empirical research.)

---

## Phase 0: Research Design

**Reproducibility prerequisites (set up before Phase 0):**
```stata
version 17
set more off
clear all
macro drop _all
repado using "${gpid_root}/code/ado"   // pin all community packages
// set seed YYYYMMDD                   // add once you know which random ops this project uses
```

**Goal:** Establish the identification strategy before touching data.

**What to do:**
- State the research question as a precise causal or descriptive claim
- Identify the estimation strategy: DiD, IV, RD, matching, panel FE,
  cross-sectional decomposition, or descriptive
- List the key identifying assumptions and assess their plausibility
- Identify threats to identification (confounders, selection, measurement error)
- Plan the overall analysis approach and sequence of specifications

**What to produce:**
```stata
/*==================================================
DESIGN MEMO — [Project name]

Research question:
    [Precise statement of what we are estimating]

Identification strategy:
    [Method] because [assumption justification]

Key assumptions:
    1. [Assumption] — plausible because [reason]
    2. [Assumption] — testable via [test]

Threats:
    - [Threat 1]: mitigated by [approach]
    - [Threat 2]: cannot be ruled out; discuss in limitations

Planned specifications:
    Baseline: [equation]
    Extended: [equation with additional controls]
    Robustness: [alternative specifications]

Data requirements:
    [What variables, sample, time period]
==================================================*/
```

> **PAUSE.** Confirm the design with the research team before proceeding.
> If the identification strategy changes later, return to Phase 0 and
> update the design memo before re-running any analysis.

---

## Phase 1: Data Familiarization

**Goal:** Understand the data before modeling. Never estimate a model on
data you have not described.

**What to do:**
```stata
// ---- 1.1 Load and inspect structure --------------------------------
use "${gpid_data}/clean/analysis_sample.dta", clear
describe
codebook, compact
isid hhid                    // verify unique identifier

// ---- 1.2 Summary statistics (Table 1) ------------------------------
// For survey data, ALWAYS use svy: or weights
svyset psu [pw=weight], strata(stratum)

svy: mean welfare income education age
svy: proportion is_urban is_female

// Store for Table 1
estpost svy: mean welfare income education age
esttab using "${gpid_out}/tables/table1_descriptives.tex", ///
    cells("b(fmt(2)) se(fmt(2))") replace

// ---- 1.3 Data quality checks ---------------------------------------
// Missing values
misstable summarize welfare income education
misstable patterns welfare income education, frequency

// Outliers
summarize welfare, detail
// Check top/bottom 1%
centile welfare, centile(1 5 95 99)

// ---- 1.4 Key relationships (visual) --------------------------------
// Distributions
// Use [aw=weight] for continuous survey weights in histogram
histogram welfare [aw=weight], ///
    title("Distribution of welfare") ///
    xtitle("Per-capita consumption (2017 PPP USD)")

// Trends — preserve/restore is required: collapse destroys the current dataset
// For large datasets, gcollapse (gtools) is 10-100x faster with identical syntax
preserve
    collapse (mean) mean_welfare=welfare [pw=weight], by(year)
    // Alternative for large surveys: gcollapse (mean) mean_welfare=welfare [pw=weight], by(year)
    twoway line mean_welfare year, ///
        title("Mean welfare over time") ///
        ytitle("2017 PPP USD")
restore

// ---- 1.5 Verify design feasibility ---------------------------------
// Does the data support the planned identification strategy?
// For DiD: verify treatment/control group overlap, parallel pre-trends
// For IV: verify first-stage strength
// For survey: verify svyset is correctly specified
svydescribe
```

**What to produce:** Data report documenting sample size, key descriptives,
data quality issues, and preliminary assessment of whether the data supports
the planned identification strategy.

> **PAUSE.** Review descriptives with the team. Confirm sample definition
> and variable operationalization. If the data cannot support the planned
> design, return to Phase 0.

---

## Phase 2: Model Specification

**Goal:** Fully specify models before estimation. Write the equation first,
then write the code.

**What to do:**
- Write the estimating equation in mathematical notation
- Justify every variable's inclusion (theory-driven, not data-mining)
- Specify the fixed effects structure
- Determine the clustering level for standard errors
- Plan the sequence: baseline → full → robustness

**What to produce:**
```stata
/*==================================================
SPECIFICATION MEMO

Estimating equation:
    Y_it = β₁ Treatment_it + X_it'γ + α_i + δ_t + ε_it

Dependent variable:
    Y_it = log per-capita welfare (2017 PPP USD, daily)

Treatment:
    Treatment_it = 1 if household i in year t received [intervention]

Controls (X_it):
    - household size (demographic composition affects welfare)
    - education of head (human capital channel)
    - urban indicator (price level differences)

Fixed effects:
    α_i = household FE (absorb time-invariant unobservables)
    δ_t = year FE (absorb common shocks)

Standard errors:
    Clustered at [enumeration area / district] because treatment
    assigned at [level] and errors likely correlated within [unit].

Specification sequence:
    Model 1: Treatment + year FE only (baseline)
    Model 2: + household FE (within estimator)
    Model 3: + controls (preferred specification)
    Model 4: alternative clustering (robustness)
==================================================*/
```

> **PAUSE.** Team approves specification before estimation begins. This
> prevents p-hacking — the specifications are committed before seeing results.

---

## Phase 3: Main Analysis

**Goal:** Estimate the models specified in Phase 2. Do not add, remove, or
modify specifications based on results — that belongs in Phase 4.

**What to do:**
```stata
// ---- 3.1 Prepare data for estimation --------------------------------
use "${gpid_data}/clean/analysis_sample.dta", clear

// Declare panel structure
xtset hhid year

// Declare survey design (if applicable)
svyset psu [pw=weight], strata(stratum)

// ---- 3.2 Run committed specifications ------------------------------
estimates clear

// Model 1: Baseline
quietly reghdfe ln_welfare treatment, absorb(year) cluster(ea_id)
estimates store m1

// Model 2: + household FE
quietly reghdfe ln_welfare treatment, absorb(hhid year) cluster(ea_id)
estimates store m2

// Model 3: + controls (preferred)
quietly reghdfe ln_welfare treatment hh_size educ_head is_urban, ///
    absorb(hhid year) cluster(ea_id)
estimates store m3

// ---- 3.3 Initial results table (internal, not publication) ----------
esttab m1 m2 m3, ///
    se star(* 0.10 ** 0.05 *** 0.01) ///
    title("Main Results — Internal Draft") ///
    mtitles("Baseline" "HH FE" "Preferred") ///
    keep(treatment hh_size educ_head is_urban) ///
    stats(N r2_a, labels("Observations" "Adj. R²"))

// ---- 3.4 Interpretation checkpoint ---------------------------------
// What is the magnitude of the treatment effect?
// Is the sign consistent with the theoretical prediction?
// Does adding controls/FE change the estimate substantially?
// If large changes: potential omitted variable bias — discuss.
```

> **PAUSE.** Discuss findings with the team before running robustness checks.
> If results are surprising, reconsider identification assumptions before
> adding more specifications. Do NOT fish for significance.

---

## Phase 4: Robustness & Sensitivity

**Goal:** Stress-test the main findings. A result that only holds under one
specification is not a result.

**What to do:**
```stata
// ---- 4.1 Alternative specifications --------------------------------
// Different controls
quietly reghdfe ln_welfare treatment age_head female_head, ///
    absorb(hhid year) cluster(ea_id)
estimates store r1_altcontrols

// Different FE structure
quietly reghdfe ln_welfare treatment hh_size educ_head is_urban, ///
    absorb(hhid year#region) cluster(ea_id)
estimates store r2_altfe

// ---- 4.2 Alternative clustering ------------------------------------
quietly reghdfe ln_welfare treatment hh_size educ_head is_urban, ///
    absorb(hhid year) cluster(district_id)
estimates store r3_altcluster

// Wild cluster bootstrap (if few clusters)
// Requires set seed before running
// set seed 20240301
// boottest treatment, cluster(district_id) reps(999)

// ---- 4.3 Subgroup analysis -----------------------------------------
foreach group in urban rural male_head female_head {
    quietly reghdfe ln_welfare treatment hh_size educ_head ///
        if `group' == 1, absorb(hhid year) cluster(ea_id)
    estimates store sub_`group'
}

// ---- 4.4 Placebo / falsification tests -----------------------------
// Placebo outcome (should NOT be affected by treatment)
quietly reghdfe ln_hh_size treatment, absorb(hhid year) cluster(ea_id)
estimates store placebo1

// Placebo treatment timing (if DiD)
// gen fake_treat = (year >= treatment_year - 2) & treated
// reghdfe ln_welfare fake_treat, absorb(hhid year) cluster(ea_id)

// ---- 4.5 Sensitivity to outliers -----------------------------------
// Winsorize at 1st/99th percentile
winsor2 welfare, cuts(1 99) replace
quietly reghdfe ln_welfare treatment hh_size educ_head is_urban, ///
    absorb(hhid year) cluster(ea_id)
estimates store r4_winsor

// ---- 4.6 Robustness table ------------------------------------------
esttab r1_altcontrols r2_altfe r3_altcluster r4_winsor, ///
    se star(* 0.10 ** 0.05 *** 0.01) ///
    title("Robustness Checks") ///
    keep(treatment)
```

> **PAUSE.** Assess whether findings are robust. If the main result flips
> sign or loses significance across reasonable specifications, the finding
> is fragile — report this honestly, do not cherry-pick.

---

## Phase 5: Output & Interpretation

**Goal:** Produce publication-ready outputs and interpretation. See
[Output Workflow](output-tables.md) for detailed patterns.

**What to produce:**
- Publication-quality tables (esttab → LaTeX/Word/Excel)
- Figures (coefplot, trend graphs, distribution plots)
- Results narrative: what the estimates mean in substantive terms
- Limitations section: what the analysis cannot claim
- Replication materials: master do-file that reproduces everything

> See [Output Workflow](output-tables.md) for esttab, coefplot, putexcel,
> and putdocx patterns specific to GPID publication standards.

---

## Cross-Software Verification

For results appearing in official World Bank products, verify critical
calculations in a second software (R or Python). This is not optional for
poverty headcount rates and inequality indices.

```stata
// In Stata: FGT(0) headcount
svyset psu [pw=weight], strata(stratum)
svy: proportion poor
// Result: 0.1234 (SE: 0.0089)

// In R: verify with collapse + explicit calculation
// fmean(poor, w = weight)
// Expected: 0.1234 (within rounding tolerance)
```

Document the cross-verification in the do-file header or in a separate
verification log.

---

## Adversarial Review (Referee 2)

Before finalizing any analysis, apply the Referee 2 lens:

1. **Would a hostile referee accept the identification strategy?**
   - What is the strongest objection? Address it in the robustness section.
2. **Are the standard errors correct for the design?**
   - Clustered at the right level? Few-clusters problem?
3. **Does the sample selection introduce bias?**
   - Who is excluded and why? Does exclusion correlate with treatment?
4. **Are the magnitudes plausible?**
   - A 50% increase in welfare from a small intervention is suspicious.
5. **What would the result look like if the null is true?**
   - Placebo tests, pre-trend tests, falsification exercises.
