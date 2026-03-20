# Macro System

The macro system is the single highest-risk area for Copilot-generated Stata code.
Every mistake here produces code that runs without errors but computes wrong results.

---

## 1. `local` vs `global` — Scope and Lifetime

A `local` macro exists **only within the do-file or program where it is defined**.
The moment that do-file or program ends, it is gone. It is never visible to other
do-files called with `do` or `run`.

A `global` persists for the **entire Stata session** and is visible everywhere —
including do-files called later, programs defined elsewhere, and interactive commands.
This is almost always wrong in collaborative, reproducible research. Two people running
the same master do-file on the same machine in the same session can produce different
results if globals from a previous run are still in memory.

```stata
* WRONG — global pollutes the Stata session
global country "ETH"
use "${country}_survey.dta", clear
// Any other do-file in this session can read or overwrite $country

* RIGHT — local scoped to this do-file only
local country "ETH"
use "`country'_survey.dta", clear
// Nothing outside this do-file can see `country'
```

**The only legitimate use of globals:** a single master do-file that defines root
directory paths (e.g., `global root "C:/projects/gpid"`), then runs subordinate
do-files that consume those paths. Even then:
- Name them with a project prefix to avoid collisions: `$gpid_root`, not `$root`
- Drop all globals at the start of the master do-file: `macro drop _all`
- Never define globals in subordinate do-files

```stata
* master.do — only place globals belong
macro drop _all
global gpid_root  "C:/WBG/gpid-analysis"
global gpid_data  "${gpid_root}/data"
global gpid_out   "${gpid_root}/output"

do "${gpid_root}/code/01_clean.do"
do "${gpid_root}/code/02_merge.do"
```

```stata
* 01_clean.do — subordinate do-file consumes globals, defines only locals
local survey_year 2022
use "${gpid_data}/raw/`survey_year'_hh.dta", clear
```

---

## 2. Compound Double Quotes — The Most Common Silent Error

This is the pattern Copilot gets wrong most often in GPID-relevant code.

Plain quotes `"..."` work correctly when the macro value is simple text with no
embedded quotes or leading/trailing spaces. But in many real scenarios — welfare
variable labels, country names with apostrophes, dynamic string construction,
file paths with spaces — plain quotes silently mis-parse.

**Compound double quotes** are opened with backtick + double-quote (ASCII 96 + 34)
and closed with double-quote + single-quote (ASCII 34 + 39). They handle *any*
string content including embedded double quotes, embedded macros, and special
characters. Regular double quotes (`""`, ASCII 34) can appear freely inside
compound double quotes without breaking the string.

```stata
* Works for simple values
local label "Consumption per capita"
label variable welfare "`label'"

* BREAKS silently — the label contains double quotes
local label "Consumption "adjusted" per capita"
label variable welfare "`label'"
// Stata parses this as: label variable welfare "Consumption "  (truncated at inner quote)

* RIGHT — compound quotes handle embedded quotes correctly
local label `"Consumption "adjusted" per capita"'
label variable welfare `"`label'"'
```

```stata
* File paths with spaces — always use compound quotes for tempfile
tempfile merged_data
save `"`merged_data'"', replace
use  `"`merged_data'"', clear

* Country names with apostrophes
local ctry_name "Côte d'Ivoire"
display `"`ctry_name'"'   // safe
notes: Data source: `"`ctry_name'"' 2022 survey
```

**Rule of thumb:** use compound quotes whenever the macro value:
- Will be used in a `label`, `notes`, or `display` statement
- Comes from user input, a file name, or a variable
- Contains or might contain embedded quotes, apostrophes, or special characters
- Is a `tempfile` path (always — file paths are unpredictable)

---

## 3. Stata expands macros eagerly at definition time

When one macro references another, the inner macro is resolved
**immediately** — the result is a frozen string, not a live reference.
If the source macro changes later, the derived macro does not update.

```stata
* --- THE TRAP: eager expansion freezes the value at definition ---
local suffix "_pc"
local varname "cons`suffix'"    // `suffix' expands NOW → varname = "cons_pc"

display "`varname'"             // Prints: cons_pc  ✓

* Now change the source macro:
local suffix "_ppp"
display "`varname'"             // Prints: cons_pc  ✗
                                // NOT "cons_ppp" — the old expansion is baked in

* --- WHERE THIS BITES: a loop that changes the inner macro ---
local welfare "cons"
local fullvar "`welfare'_pc"    // Expands NOW → fullvar = "cons_pc"

foreach w in cons income {
    display "`fullvar'"         // Prints "cons_pc" EVERY iteration
                                // It never becomes "income_pc"
}

* --- THE FIX: rebuild the derived macro inside the loop ---
foreach w in cons income {
    local fullvar "`w'_pc"      // Re-expand on each iteration
    display "`fullvar'"         // Prints: cons_pc, then income_pc  ✓
}
```

The rule: **a macro stores a string, not a formula.** Any backtick
references inside it are resolved once, at the moment the `local`
(or `global`) command runs. If you need the reference to stay
"live," you must redefine the macro after every change to its inputs.

---

## 4. Debugging Macros

Always verify macro contents before using them in consequential operations.

```stata
* Display a local macro's current value
display "`mymacro'"
display `"`mymacro'"'       // compound version — safe for any content

* Display a global macro
display "$myglobal"
display `"$myglobal"'

* List all currently defined locals (inside a program, after display won't work)
macro list _locals

* List all globals
macro list _globals

* Check if a local is empty
if `"`mymacro'"' == `""' {
    display as error "mymacro is empty — check assignment"
    exit 198
}
```

**Defensive pattern for program arguments:**
```stata
program define myprog
    syntax varlist(min=1 max=1) , Countries(string) [ Year(integer 2017) ]

    local welfare_var : word 1 of `varlist'

    // --- Validate and normalize countries() ---
    local clean_countries ""
    foreach cc of local countries {
        // Each code must be exactly 3 characters
        if length("`cc'") != 3 {
            display as error "Invalid ISO3 code: `cc' (must be exactly 3 characters)"
            exit 198
        }
        // Reject if it contains non-alpha characters
        if !regexm("`cc'", "^[a-zA-Z]+$") {
            display as error "Invalid ISO3 code: `cc' (must contain only letters)"
            exit 198
        }
        // Convert to uppercase
        local cc = upper("`cc'")
        local clean_countries "`clean_countries' `cc'"
    }
    local clean_countries = strtrim("`clean_countries'")

    // Must have at least one country
    if "`clean_countries'" == "" {
        display as error "countries() must include at least one ISO3 code"
        exit 198
    }

    // --- Validate year ---
    if `year' < 1990 | `year' > 2030 {
        display as error "year(`year') out of plausible range [1990, 2030]"
        exit 198
    }

    display "Processing: welfare=`welfare_var', year=`year'"
    display "Countries: `clean_countries'"
    // ... rest of program
end

// Usage:
myprog consumption, countries(col per arg) year(2022)
// Internally works with: COL PER ARG
```

`syntax` handles the structural parsing — required vs. optional,
types, defaults — but anything domain-specific (valid code length,
character restrictions, case normalization, plausible ranges) must
be validated manually after parsing.

---

## 5. `macro drop` — Cleaning Up

At the start of any master do-file or session-initialization block:

```stata
macro drop _all      // Drop all user-defined globals
// Do NOT use this inside programs — it would drop the caller's macros too
```

Inside programs, you do not need `macro drop` because locals are automatically
scoped. Only use `macro drop` at the top level.
