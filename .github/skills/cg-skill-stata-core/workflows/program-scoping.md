# Program Scoping

Understanding how programs store results, share data, and receive arguments is
essential for writing correct Stata programs. Copilot's default pattern — plain
`program define` with no return type — silently discards results that callers
depend on.

---

## 1. Program Return Types

Every Stata program falls into one of three categories. Choose the right one
before writing a single line of the program body.

### Plain program — returns nothing

```stata
program define clean_welfare
    // Transforms data in memory; no results stored in r() or e()
    replace welfare = . if welfare < 0
    replace welfare = welfare / 12  // annual to monthly
end
```

Use this for: data transformations, do-file runners, utility programs that
modify data but do not compute values the caller needs back.

### `rclass` — results stored in `r()`

```stata
program define summarize_welfare, rclass
    syntax varname [if] [in] [aweight pweight]
    
    // Run computation
    quietly summarize `varlist' `if' `in' [`weight'`exp']
    
    // Store results — these survive until the next r-class command runs
    return scalar mean   = r(mean)
    return scalar sd     = r(sd)
    return scalar n      = r(N)
    return scalar cv     = r(sd) / r(mean)
end

// Calling code:
summarize_welfare welfare if year == 2022 [pw = weight]
display "Mean: " r(mean) "  CV: " r(cv)
local m = r(mean)   // SAVE before calling anything else
```

Use this for: summary statistics, data quality checks, any program that
computes scalars or matrices the caller needs.

### `eclass` — results stored in `e()`

```stata
program define estimate_poverty, eclass
    syntax varlist [if] [in], pline(real) [vce(string)]
    
    // ... estimation logic ...
    
    // Post coefficient matrix and variance-covariance matrix
    ereturn post b V, esample(sample_flag)
    ereturn scalar pline = `pline'
    ereturn local  cmd   "estimate_poverty"
end

// Calling code:
estimate_poverty welfare [pw=weight], pline(2.15)
ereturn list       // inspect stored results
matrix list e(b)   // examine coefficient matrix
```

Use this for: custom estimation commands that should work with `esttab`,
`margins`, `test`, and other post-estimation tools.

---

## 2. The Stored Results Disappear Problem

This is the single most dangerous pattern in Copilot-generated Stata code.
After any `r`-class or `e`-class command, calling **another command of the
same class** immediately wipes the stored results. There is no warning.

```stata
* WRONG — r(mean) from income is silently overwritten
summarize income
summarize expenditure    // r(mean) is now expenditure's mean — income's is GONE
display r(mean)          // prints expenditure mean, not income mean

* RIGHT — save immediately after the command that produces the result
summarize income
local income_mean = r(mean)    // save NOW, before anything else
local income_sd   = r(sd)

summarize expenditure
local exp_mean = r(mean)       // save expenditure results
local exp_sd   = r(sd)

display "Income mean: `income_mean'"
display "Expenditure mean: `exp_mean'"
```

```stata
* Same problem with estimation results
regress welfare i.urban i.year [pw=weight]
local r2 = e(r2)        // save r-squared immediately
local N  = e(N)

regress welfare i.urban i.year i.region [pw=weight]   // e(r2) now overwritten
// `r2' and `N' are safe — they were saved to locals
```

**Rule:** Immediately after any estimation or summary command, if you need any
stored result, save it to a local. Do not assume `r()` or `e()` will survive
even one more line of code.

---

## 3. Local Scope Inside Programs

Locals defined inside a program are **completely invisible** outside it. This is
intentional and correct behavior. It means programs do not pollute the caller's
local namespace.

```stata
program define myprog
    local x 5
    local result = `x' * 2
    display "Inside program: result = `result'"
end

myprog
display "`result'"    // EMPTY — `result' does not exist in the calling scope
display "`x'"         // EMPTY — `x' does not exist in the calling scope
```

When a program calls another program, the inner program gets a **completely
fresh local scope**. Outer locals are not inherited.

```stata
program define outer
    local welfare_var "cons_pc"
    inner_prog          // `welfare_var' is NOT visible inside inner_prog
end

program define inner_prog
    display "`welfare_var'"   // prints nothing — empty local
end
```

**To pass data between programs:** use function arguments (`syntax` or `args`),
`r()` return values, or global macros (only when absolutely necessary and
scoped to a master do-file).

---

## 4. Argument Parsing with `syntax`

The `syntax` command is the correct way to parse arguments in any non-trivial
program. It handles optional arguments, flags, variable lists, and `if`/`in`
qualifiers automatically.

```stata
program define gpid_summarize, rclass
    syntax varname(numeric) [if] [in] [aweight pweight fweight], ///
        [ BYvar(varname) Detail POVline(real 2.15) ]
    // Note: capitalized letters in option names = abbreviation allowed
    // BYvar can be called as byvar, byv, by — Stata matches abbreviated options
    
    // After syntax, these locals are automatically defined:
    // `varlist'  — the confirmed numeric variable name
    // `if'       — the if condition (empty string if not specified)
    // `in'       — the in range (empty string if not specified)
    // `weight'   — weight type (empty string if not specified)
    // `exp'      — weight expression (empty string if not specified)
    // `byvar'    — the by-variable (empty string if not specified)
    // `detail'   — "detail" if specified, empty string otherwise
    // `povline'  — the real number (2.15 if not specified)
    
    if "`byvar'" != "" {
        quietly bysort `byvar': summarize `varlist' `if' `in' [`weight'`exp']
    }
    else {
        quietly summarize `varlist' `if' `in' [`weight'`exp'], `detail'
    }
    
    return scalar mean    = r(mean)
    return scalar median  = r(p50)    // only available with detail
    return scalar povline = `povline'
end
```

**Common `syntax` patterns for GPID programs:**

```stata
* Required variable + required option
syntax varname, pline(real)

* Optional variable list + optional if/in + optional weight
syntax [varlist(numeric)] [if] [in] [aweight pweight]

* Multiple options with defaults
syntax varname, [ Year(integer 2022) PPP(real 1.0) Verbose ]

* Using/saving file paths
syntax anything [using/], [ replace ]
```

---

## 5. `ereturn post` — Correct Pattern for Estimation Programs

If you are writing a custom estimation command (for poverty indices, inequality
decompositions, etc.), the post step must be done correctly or `esttab` and
`margins` will not work.

```stata
program define fgt_poverty, eclass
    syntax varname(numeric) [if] [in] [pweight], ///
        pline(real) [ Alpha(integer 0) ]
    
    marksample touse        // creates binary variable: 1 if obs in estimation sample
    
    // ... compute FGT index ...
    local fgt_value = ...
    
    // Construct coefficient and VCE matrices
    matrix b = (`fgt_value')
    matrix V = (0)          // replace with actual variance if available
    matrix colnames b = fgt`alpha'
    matrix colnames V = fgt`alpha'
    matrix rownames V = fgt`alpha'
    
    // Post results
    ereturn post b V, esample(`touse') obs(`=r(N)')
    ereturn scalar alpha  = `alpha'
    ereturn scalar pline  = `pline'
    ereturn local  cmd    "fgt_poverty"
    ereturn local  title  "FGT Poverty Index (alpha=`alpha')"
end
```
