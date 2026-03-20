# Output Workflow

Patterns for producing publication-ready tables and figures from GPID
analytical work. This is Phase 5 of the research workflow. All outputs
must be reproducible — generated from code, not manual editing.

---

## 1. Regression Tables with `esttab`

### Basic Publication Table

```stata
// Store models (from Phase 3)
estimates clear
quietly reghdfe y treat, absorb(id year) cluster(id)
quietly summarize y if e(sample)
estadd scalar ymean = r(mean)    // store dep var mean for Table 1 row
estimates store m1
quietly reghdfe y treat x1 x2, absorb(id year) cluster(id)
quietly summarize y if e(sample)
estadd scalar ymean = r(mean)
estimates store m2
quietly reghdfe y treat x1 x2 x3, absorb(id year) cluster(id)
quietly summarize y if e(sample)
estadd scalar ymean = r(mean)
estimates store m3

// LaTeX table
esttab m1 m2 m3 using "${gpid_out}/tables/main_results.tex", replace ///
    se(3) star(* 0.10 ** 0.05 *** 0.01) ///
    label booktabs alignment(D{.}{.}{-1}) ///
    title("Effect of Treatment on Welfare") ///
    mtitles("Baseline" "Controls" "Preferred") ///
    keep(treat x1 x2 x3) order(treat x1 x2 x3) ///
    stats(N r2_a ymean, ///
        labels("Observations" "Adj. R\$^2\$" "Mean dep. var.") ///
        fmt(0 3 2)) ///
    addnotes("Standard errors clustered at household level in parentheses." ///
             "All specifications include household and year fixed effects.")
```

### Word/Excel Output (for GPID reports)

```stata
// Word table
esttab m1 m2 m3 using "${gpid_out}/tables/main_results.rtf", replace ///
    se(3) star(* 0.10 ** 0.05 *** 0.01) ///
    label ///
    title("Table 2: Effect of Treatment on Welfare") ///
    mtitles("(1)" "(2)" "(3)") ///
    keep(treat x1 x2 x3) ///
    stats(N r2_a, labels("Observations" "Adj. R²") fmt(0 3))

// Excel table
esttab m1 m2 m3 using "${gpid_out}/tables/main_results.csv", replace ///
    se(3) star(* 0.10 ** 0.05 *** 0.01) ///
    label csv ///
    keep(treat x1 x2 x3) ///
    stats(N r2_a, labels("Observations" "Adj. R²") fmt(0 3))
```

### Advanced: Multi-Panel Tables

```stata
// Panel A: OLS
esttab m1 m2 m3 using "${gpid_out}/tables/multi_panel.tex", replace ///
    se(3) star(* 0.10 ** 0.05 *** 0.01) ///
    label booktabs ///
    prehead("\begin{table}[htbp]\centering" ///
            "\caption{Treatment Effects}" ///
            "\begin{tabular}{l*{3}{c}}" "\hline\hline" ///
            "\multicolumn{4}{l}{\textit{Panel A: OLS}} \\\\") ///
    postfoot("\hline")

// Panel B: IV
esttab iv1 iv2 iv3 using "${gpid_out}/tables/multi_panel.tex", append ///
    se(3) star(* 0.10 ** 0.05 *** 0.01) ///
    label booktabs ///
    prehead("\multicolumn{4}{l}{\textit{Panel B: IV}} \\\\") ///
    postfoot("\hline\hline" "\end{tabular}" "\end{table}")
```

---

## 2. Descriptive Statistics Table (Table 1)

### Standard Table 1

```stata
// Using estpost for survey-weighted descriptives
svyset psu [pw=weight], strata(stratum)

estpost svy: mean welfare income education age hh_size is_urban
esttab using "${gpid_out}/tables/table1.tex", replace ///
    cells("b(fmt(2)) se(fmt(2))") ///
    label booktabs ///
    title("Summary Statistics") ///
    nomtitles nonumbers ///
    collabels("Mean" "SE")
```

### Table 1 with Treatment/Control Comparison

```stata
// Means by group
eststo clear
eststo all: estpost svy: mean welfare income education age
eststo treated: estpost svy, subpop(treated): mean welfare income education age
eststo control: estpost svy, subpop(if treated==0): mean welfare income education age

esttab all treated control using "${gpid_out}/tables/table1_balance.tex", ///
    replace cells("b(fmt(2)) se(fmt(2))") ///
    label booktabs ///
    mtitles("Full Sample" "Treated" "Control") ///
    title("Table 1: Summary Statistics and Balance")
```

---

## 3. Coefficient Plots

### Basic Coefficient Plot

```stata
// From stored estimates
coefplot m1 m2 m3, ///
    keep(treat) ///
    xline(0, lcolor(red) lpattern(dash)) ///
    title("Treatment Effect Across Specifications") ///
    legend(order(2 "Baseline" 4 "Controls" 6 "Preferred"))
graph export "${gpid_out}/figures/coefplot_main.pdf", replace
```

### Event Study Plot

```stata
coefplot, vertical ///
    drop(_cons) ///
    rename(*.event_time#1.treated = .event_time) ///
    at(_coef) ///
    xline(-0.5, lcolor(red) lpattern(dash)) ///
    yline(0, lcolor(gray) lpattern(dash)) ///
    title("Event Study: Treatment Effects Over Time") ///
    xtitle("Periods Relative to Treatment") ///
    ytitle("Effect on Log Welfare") ///
    ciopts(lcolor(navy) recast(rcap))
graph export "${gpid_out}/figures/event_study.pdf", replace
```

### Subgroup Effects Plot

```stata
coefplot sub_urban sub_rural sub_male_head sub_female_head, ///
    keep(treat) ///
    xline(0, lcolor(red) lpattern(dash)) ///
    labels("Urban" "Rural" "Male-headed" "Female-headed") ///
    title("Treatment Effects by Subgroup") ///
    legend(off)
graph export "${gpid_out}/figures/subgroup_effects.pdf", replace
```

---

## 4. Excel Output with `putexcel`

### Custom Excel Tables (for GPID-specific formatting)

```stata
putexcel set "${gpid_out}/tables/poverty_rates.xlsx", replace sheet("Poverty")

// Headers
putexcel A1 = "Country"
putexcel B1 = "Year"
putexcel C1 = "Headcount ($2.15)"
putexcel D1 = "Headcount ($3.65)"
putexcel E1 = "Gini"

// Fill from results
local row = 2
levelsof country_code, local(countries)
foreach c of local countries {
    levelsof year if country_code == "`c'", local(years)
    foreach y of local years {
        putexcel A`row' = "`c'"
        putexcel B`row' = `y'

        // Survey-weighted poverty rate
        quietly svy, subpop(if country_code == "`c'" & year == `y'): ///
            proportion poor_215
        putexcel C`row' = matrix(e(b)[1,2]), nformat(number_d2)

        local ++row
    }
}
```

---

## 5. Figures for GPID Reports

### Poverty Trend Chart

```stata
// Prepare data
preserve
collapse (mean) headcount=poor_215 [pw=weight], by(year)

twoway line headcount year, ///
    lcolor(navy) lwidth(medthick) ///
    title("Poverty Headcount Rate ($2.15/day)") ///
    subtitle("National estimate, 2017 PPP") ///
    ytitle("Share of population (%)") ///
    xtitle("Year") ///
    ylabel(0(0.05)0.30, format(%4.1f)) ///
    scheme(s2color)
graph export "${gpid_out}/figures/poverty_trend.pdf", replace as(pdf)
graph export "${gpid_out}/figures/poverty_trend.png", replace as(png) width(2400)
restore
```

### Cross-Country Bar Chart

```stata
preserve
collapse (mean) headcount=poor_215 [pw=weight], by(country_name)
gsort -headcount

graph hbar headcount, ///
    over(country_name, sort(1) descending label(labsize(small))) ///
    ytitle("Poverty rate ($2.15/day)") ///
    title("Poverty Headcount by Country") ///
    blabel(bar, format(%4.1f)) ///
    bar(1, color(navy))
graph export "${gpid_out}/figures/country_poverty_bar.pdf", replace
restore
```

### Distribution Plot (Welfare)

```stata
twoway (kdensity welfare_pc [aw=weight] if treated==1, ///
            lcolor(navy) lwidth(medthick)) ///
       (kdensity welfare_pc [aw=weight] if treated==0, ///
            lcolor(cranberry) lwidth(medthick) lpattern(dash)), ///
    xline(2.15, lcolor(red) lpattern(dot)) ///
    title("Welfare Distribution by Treatment Status") ///
    xtitle("Daily per-capita consumption (2017 PPP USD)") ///
    ytitle("Density") ///
    legend(order(1 "Treated" 2 "Control")) ///
    note("Vertical line = $2.15/day poverty line")
graph export "${gpid_out}/figures/welfare_density.pdf", replace
```

---

## 6. Replication Package Checklist

Before finalizing outputs, run `reprun` on the master do-file to verify
reproducibility:

```stata
reprun "${gpid_root}/code/master.do"
// Two runs must produce identical outputs. If it fails, check for:
//   - missing `set seed` before bootstrap/simulate/sample
//   - `bysort` without secondary sort variable
//   - date/time functions in computed variables
// Run repscan for quick diagnosis: repscan "${gpid_root}/code/", recursive
```

Then verify:

- [ ] Master do-file runs entire analysis from raw data to final outputs
- [ ] All paths use global macros (single root in `00_master.do`)
- [ ] All output files are named to match paper/report elements (Table 1 = `table1.tex`)
- [ ] `repado` initialized; community packages pinned in `code/ado/` and committed to git
- [ ] `version 17` set at top of every do-file; `set more off` and `clear all` present
- [ ] `set seed` documented for all random processes (`bootstrap`, `simulate`, `sample`)
- [ ] `reprun` passes — two runs produce identical outputs
- [ ] `repscan` run; no unexplained non-deterministic commands
- [ ] `lint` passes or `autofix` applied to all do-files
- [ ] README documents: software version, package requirements, execution order
- [ ] All intermediate datasets saved (not just final)
- [ ] Log files generated for every do-file
