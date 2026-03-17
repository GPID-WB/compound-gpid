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

## 3. Macro Expansion Order — The Invisible Bug

Stata expands macros when a line is *executed*, not when it is *defined* — but
only for bare references. Quoted strings at definition time do **not** expand the
macros inside them in the way you might expect.

```stata
* WRONG — `i' is NOT expanded at assignment time inside double quotes
local i 3
local varname "variable`i'"
display "`varname'"
// Prints: variable3  — this actually WORKS, counter to expectation

* The real trap: macro inside a macro at definition
local suffix "_pc"
local welfare "cons`suffix'"     // `suffix' IS expanded here — result: cons_pc

* BUT this fails:
local welfare "cons"
local full_name "`welfare'`suffix'"  // Both expand correctly at execution time
display "`full_name'"   // Prints: cons_pc — correct

* Where expansion genuinely fails: extended macro functions
local i 3
local var_`i' "variable three"   // Creates a macro named var_3
display "`var_3'"                 // Prints: variable three — correct
display "`var_`i''"               // WRONG — nested expansion is not supported this way

* RIGHT — use intermediate local for nested expansion
local i 3
local varname "var_`i'"          // first expand i -> var_3
display "``varname''"            // then expand var_3 -> "variable three"
```

**The double-macro expansion pattern** (`` ``macroname'' ``) is powerful but
easy to get wrong. Test all nested macro references with `display` before using
them in production code.

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
if "`mymacro'" == "" {
    display as error "mymacro is empty — check assignment"
    exit 198
}
```

**Defensive pattern for program arguments:**

```stata
program define myprog
    args welfare_var year_var
    
    // Verify args were passed
    if "`welfare_var'" == "" {
        display as error "welfare_var required"
        exit 198
    }
    
    display "Processing: welfare=`welfare_var', year=`year_var'"
    // ... rest of program
end
```

---

## 5. `macro drop` — Cleaning Up

At the start of any master do-file or session-initialization block:

```stata
macro drop _all      // Drop all user-defined globals
// Do NOT use this inside programs — it would drop the caller's macros too
```

Inside programs, you do not need `macro drop` because locals are automatically
scoped. Only use `macro drop` at the top level.
