# Reproducibility

GPID produces official World Bank poverty and inequality statistics. Every
do-file must be reproducible: running it twice on the same machine must produce
identical results, and running it on a different machine must produce identical
results. These tools enforce that standard.

---

## 1. `repkit` — Overview

`repkit` is the World Bank DIME Analytics package for reproducibility tooling
in Stata. It is the canonical standard for WB-adjacent empirical work.

Install once per machine:
```stata
ssc install repkit
```

Four commands: `repado` (pin package versions), `reprun` (detect non-reproducibility),
`lint` (style enforcement), `repscan` (detect reproducibility-breaking commands).

---

## 2. `repado` — Pinning Package Versions

**The problem:** SSC packages update silently. If a collaborator installs
`estout` a month after you did, they may have a different version. Results
can differ. Neither machine errors — the difference is silent.

**The solution:** `repado` installs and manages all community-contributed
packages into a project-local `code/ado/` folder that is committed to version
control. Everyone on the project uses identical package versions.

### Setup (run once per project, commit `code/ado/` to git)

```stata
* In master.do, before any community-contributed commands
repado using "${gpid_root}/code/ado"

* Install packages into the project cache (first-time setup)
repado using "${gpid_root}/code/ado": ssc install estout
repado using "${gpid_root}/code/ado": ssc install outreg2
repado using "${gpid_root}/code/ado": ssc install psmatch2
repado using "${gpid_root}/code/ado": ssc install ftools
repado using "${gpid_root}/code/ado": ssc install reghdfe
repado using "${gpid_root}/code/ado": ssc install ivreg2
```

### Usage in master.do

```stata
* master.do header
version 17
set more off
macro drop _all

global gpid_root "C:/WBG/gpid-analysis"

* FIRST: set up package environment
repado using "${gpid_root}/code/ado"
// All community-contributed commands now resolve from code/ado/, not PLUS

* THEN: run analysis
do "${gpid_root}/code/01_clean.do"
do "${gpid_root}/code/02_merge.do"
do "${gpid_root}/code/03_analysis.do"
```

### What to commit to git

```
code/
└── ado/               ← commit this entire folder
    ├── e/
    │   └── estout.ado
    ├── r/
    │   └── reghdfe.ado
    └── ...
```

Add to `.gitignore`: nothing — commit the whole `ado/` folder.

---

## 3. `reprun` — Automated Reproducibility Detection

`reprun` runs a do-file **twice** and compares all state values between the
two runs: RNG state (`r(seed)`), `datasignature`, stored `r()` and `e()`
results, and dataset checksums. Any difference is flagged.

### When to run

- Before any merge request or code review
- Before submitting to internal quality review
- After any significant refactor
- Whenever random processes (`bootstrap`, `simulate`, `sample`, `drawnorm`) are added

```stata
* Basic usage — run master.do twice and compare
reprun "${gpid_root}/code/master.do"

* With verbose output — see exactly which state values differ
reprun "${gpid_root}/code/master.do", verbose

* Check a single do-file
reprun "${gpid_root}/code/03_analysis.do"
```

### Interpreting output

```
Reproducibility check: PASSED
  Run 1 datasignature: 12345678:9012:3456789:0123
  Run 2 datasignature: 12345678:9012:3456789:0123
  All state values match.
```

```
Reproducibility check: FAILED
  datasignature differs between runs.
  Likely cause: random process without set seed, or sort-dependent operation.
  See reprun_comparison.dta for details.
```

**Common causes of failure:**
- Missing `set seed` before `bootstrap`, `simulate`, `sample`, `splitsample`
- `bysort` without secondary sort variable (arbitrary within-group order)
- `sort` on non-unique key (tied observations sorted differently each run)
- Date/time functions (`clock()`, `now()`) used in computed variables
- External file reads that change between runs

---

## 4. `lint` — Code Style Enforcement

`lint` checks do-files against DIME Analytics coding standards: indentation,
line length, delimiter use, variable naming, and other style rules.

```stata
* Check a single file
lint "${gpid_root}/code/01_clean.do"

* Check all do-files in a folder
lint "${gpid_root}/code/", recursive

* Auto-apply safe fixes (indentation, spacing — not logic changes)
lint "${gpid_root}/code/01_clean.do", autofix

* Check with verbose output — see all warnings
lint "${gpid_root}/code/01_clean.do", verbose
```

### Common lint warnings

| Warning | Fix |
|---------|-----|
| Line exceeds 80 characters | Break with `///` continuation |
| `#delimit ;` used | Remove — use `///` instead |
| `if condition == 1` | Simplify to `if condition` |
| Hardcoded file path | Use global macro for root |
| Missing space after comma | Style fix |
| `global` defined in non-master file | Move to master.do |

**Integrate into `/cg-review`:** run `lint` on all `.do` files in the project
when the `cg-reproducibility` agent is active.

---

## 5. `repscan` — Detect Reproducibility-Breaking Commands

`repscan` scans a do-file and flags commands known to introduce
non-reproducibility: `sort` on non-unique keys, `sample`, date functions,
`set seed`-less random processes.

```stata
repscan "${gpid_root}/code/03_analysis.do"
repscan "${gpid_root}/code/", recursive
```

Run `repscan` before `reprun` to identify likely problem areas before doing the
full two-run comparison.

---

## 6. `set seed` — RNG Reproducibility

Any operation involving random number generation requires a seed. Set it once,
near the top of the do-file that contains the random operation, after `repado`.

```stata
* Standard location: after repado, before data loading
version 17
set more off
macro drop _all

global gpid_root "C:/WBG/gpid-analysis"
repado using "${gpid_root}/code/ado"

set seed 20240301   // YYYYMMDD format is readable and meaningful

use "${gpid_data}/clean/households.dta", clear
```

### Commands that require `set seed`

```stata
set seed 20240301

bootstrap r(mean), reps(500): summarize welfare [pw=weight]
simulate mean=r(mean), reps(1000): ...
sample 10                    // random 10% sample
splitsample, generate(fold) nsplit(5)
drawnorm x1 x2, n(1000) corr(R)
```

**Document the seed in the do-file header.** If results are ever challenged,
you must be able to reproduce them exactly from the seed value.

---

## 7. Standard Do-file Reproducibility Header

Every production do-file should begin with this block:

```stata
/*==================================================
Project:    GPID Poverty Analysis
Do-file:    03_welfare_aggregation.do
Date:       2025-03-01
Author:     [name]
Modified:   2025-03-15 [name] — added PPP conversion

Purpose:    Compute per-capita consumption aggregate from
            harmonized household survey microdata.

Inputs:     ${gpid_data}/intermediate/02_cleaned.dta
Outputs:    ${gpid_data}/intermediate/03_welfare.dta

Notes:      PPP conversion uses 2017 ICP round.
            Survey design: complex sample, use svyset throughout.
            Random seed: 20240301 (bootstrap in section 4 only)
==================================================*/

version 17
set more off
set linesize 120
clear all
macro drop _all

* Package environment (reads from code/ado/)
repado using "${gpid_root}/code/ado"

* Set seed if this do-file contains any random operations
* set seed 20240301

* Open log
capture log close
log using "${gpid_root}/output/logs/03_welfare.log", replace text
```
