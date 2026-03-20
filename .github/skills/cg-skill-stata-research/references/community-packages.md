# Community Packages Quick Reference

Concise syntax reference for community-contributed packages used in GPID
analytical work. Install all packages via `ssc install` or `net install`.
For GPID projects, use `repado` to pin versions (see `cg-skill-stata-core`
Reproducibility workflow).

---

## reghdfe — High-Dimensional Fixed Effects

Preferred over `xtreg` and `areg` when absorbing multiple FE sets.

```stata
ssc install reghdfe
ssc install ftools      // required dependency

// Basic: two-way FE
reghdfe y x1 x2, absorb(id year) cluster(id)

// Three-way FE
reghdfe y x1 x2, absorb(id year region#year) cluster(id)

// Two-way clustering
reghdfe y x1 x2, absorb(id year) cluster(id year)

// Save absorbed FE
reghdfe y x1 x2, absorb(fe_id=id fe_year=year) cluster(id)

// Singleton observations: reghdfe drops them by default (correct)
// To see how many: check the output message
```

---

## estout / esttab — Publication Tables

```stata
ssc install estout

// Store estimates
estimates clear
quietly reghdfe y x1 x2, absorb(id year) cluster(id)
estimates store m1

// Basic table
esttab m1 m2 m3, se star(* 0.10 ** 0.05 *** 0.01)

// LaTeX
esttab m1 m2 m3 using "table.tex", replace ///
    se(3) star(* 0.10 ** 0.05 *** 0.01) ///
    label booktabs ///
    keep(x1 x2) order(x1 x2) ///
    stats(N r2_a, labels("N" "Adj. R²") fmt(0 3)) ///
    title("Results") ///
    mtitles("(1)" "(2)" "(3)")

// Word (RTF)
esttab using "table.rtf", replace se(3) label star(* .10 ** .05 *** .01)

// Inline: using eststo shorthand
eststo clear
eststo: reghdfe y x1, absorb(id year) cluster(id)
eststo: reghdfe y x1 x2, absorb(id year) cluster(id)
esttab, se star(* .10 ** .05 *** .01)
```

---

## csdid — Callaway & Sant'Anna DiD

For staggered DiD with heterogeneous treatment effects.

```stata
ssc install csdid
ssc install drdid       // dependency

// Basic usage
// gvar = first treatment period (0 for never-treated)
csdid y, ivar(id) time(year) gvar(first_treat) notyet

// With covariates
csdid y x1 x2, ivar(id) time(year) gvar(first_treat) notyet

// Aggregations
csdid_estat simple       // overall ATT
csdid_estat group        // by treatment cohort
csdid_estat event        // event-time ATT
csdid_estat calendar     // calendar-time ATT

// Event study plot
csdid_plot

// With not-yet-treated as control (recommended over never-treated)
// notyet option = use not-yet-treated; omit = use never-treated only
```

---

## did_multiplegt — de Chaisemartin & D'Haultfoeuille

Alternative robust DiD estimator.

```stata
ssc install did_multiplegt

did_multiplegt y id year treatment, ///
    robust_dynamic ///
    placebo(5) dynamic(5) ///
    breps(100) cluster(id)
```

---

## rdrobust — Regression Discontinuity

```stata
net install rdrobust, from("https://raw.githubusercontent.com/rdpackages/rdrobust/master/stata")

// Sharp RD
rdrobust y running_var, c(0)

// Fuzzy RD
rdrobust y running_var, c(0) fuzzy(treatment)

// With covariates
rdrobust y running_var, c(0) covs(x1 x2)

// Bandwidth selection
rdbwselect y running_var, c(0) all

// RD plot
rdplot y running_var, c(0) nbins(20 20)

// Density test (manipulation)
rddensity running_var, c(0)
```

---

## psmatch2 — Propensity Score Matching

```stata
ssc install psmatch2

// Nearest-neighbor matching
psmatch2 treated x1 x2 x3, outcome(y) neighbor(5) caliper(0.05) common

// Balance check
pstest x1 x2 x3, both graph

// Kernel matching
psmatch2 treated x1 x2 x3, outcome(y) kernel kerneltype(epan)
```

---

## coefplot — Coefficient Plots

```stata
ssc install coefplot

// Basic
coefplot m1 m2, keep(x1 x2) xline(0)

// Vertical (event study style)
coefplot, vertical drop(_cons) xline(-0.5) yline(0)

// Multiple models side by side
coefplot (m1, label("OLS")) (m2, label("IV")), ///
    keep(treatment) xline(0, lpattern(dash))
```

---

## ineqdeco — Inequality Decomposition

```stata
ssc install ineqdeco

// Gini and GE indices
ineqdeco welfare [pw=weight]
// Returns: r(gini), r(ge0), r(ge1), r(ge2), r(a05), r(a1), r(a2)

// By-group decomposition
ineqdeco welfare [pw=weight], by(region)
// Returns: r(between_ge0), r(within_ge0), etc.
```

---

## ivreg2 — Enhanced IV/2SLS

```stata
ssc install ivreg2
ssc install ranktest    // dependency

ivreg2 y controls (endogenous = instrument1 instrument2), ///
    first cluster(id)
// Reports: Kleibergen-Paap F, Hansen J, Anderson-Rubin CI
```

---

## xtabond2 — Dynamic Panel GMM

```stata
ssc install xtabond2

// Arellano-Bond / Blundell-Bond
xtabond2 y L.y x1 x2, ///
    gmm(L.y, lag(2 5)) iv(x1 x2) ///
    twostep robust small
// Check: AR(1) reject, AR(2) not reject, Hansen J not reject
```

---

## Other Useful Packages

| Package | Purpose | Install |
|---------|---------|---------|
| `winsor2` | Winsorize/trim variables | `ssc install winsor2` |
| `gtools` | Fast collapse, egen, etc. | `ssc install gtools` |
| `bacondecomp` | Bacon decomposition for TWFE DiD | `ssc install bacondecomp` |
| `binsreg` | Binned scatter plots with CI | `net install binsreg, from(...)` |
| `synth` | Synthetic control method | `ssc install synth` |
| `outreg2` | Alternative table exporter | `ssc install outreg2` |
| `asdoc` | One-command Word doc creation | `ssc install asdoc` |
| `boottest` | Wild cluster bootstrap | `ssc install boottest` |
| `eventstudyinteract` | Event study (Sun & Abraham) | `ssc install eventstudyinteract` |
| `epctile` | Survey-weighted percentiles | `ssc install epctile` |
| `fastgini` | Fast Gini computation | `ssc install fastgini` |
