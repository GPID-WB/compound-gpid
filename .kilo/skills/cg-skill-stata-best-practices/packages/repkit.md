# repkit — Stata Reproducibility Toolkit

`repkit` is a Stata package providing utility tools for computational
reproducibility best-practices. Developed by DIME Analytics and the LSMS Team
at the World Bank, but applicable to any Stata project.

**Source**: https://github.com/worldbank/repkit  
**Documentation**: https://worldbank.github.io/repkit/  
**Version**: v4.0 (August 2025)

---

## Installation

```stata
* Install from SSC (recommended)
ssc install repkit

* Check if already installed before installing
cap which repkit
if _rc == 111 {
    display as error "repkit not installed. Run: ssc install repkit"
    exit 111
}
```

To install a specific older version from GitHub:
```stata
local tag "v4.0"
net install repkit, ///
    from("https://raw.githubusercontent.com/worldbank/repkit/`tag'/src")
```

---

## Commands Overview

| Command | Purpose |
|---------|---------|
| `repado` | Pin community-contributed package versions in a project-local folder |
| `repadolog` | Report commands installed in the current PLUS folder |
| `repkit` | Package utility command (enables `which repkit`) |
| `reproot` | Dynamically set root paths with no manual per-user setup |
| `reproot_setup` | Set up the environment settings file for `reproot` |
| `reprun` | Automated reproducibility check: run a do-file twice and compare all state values |
| `repscan` | Scan a do-file for commands that may cause reproducibility issues |
| `lint` | Opinionated detector and corrector for Stata do-file readability and style |

---

## `repado` — Pin Package Versions

### The Problem

SSC only provides the most recent version of each package. When a collaborator
installs `estout` a month after you did, they may have a different version.
Results can differ silently. Neither machine errors.

### The Solution

`repado` sets the Stata PLUS folder to a project-local `code/ado/` directory.
All community-contributed commands installed while `repado` is active are placed
in that project folder. Commit the folder to version control so all collaborators
and future reproducers use identical package versions.

### How It Works

When `repado` is active:
- Stata only looks in `BASE` (built-ins) and the project `code/ado/` folder
- All other ado-paths (the user's default PLUS folder, PERSONAL, etc.) are removed
- Settings reset when Stata is restarted — call `repado` at the top of each session

```
Before repado:
  [1] BASE   "C:\Stata18\ado\base/"
  [2] SITE   "C:\Stata18\ado\site/"
  [3] PLUS   "C:\Users\user\ado\plus/"
  ...

After repado using "${root}/code/ado":
  [1] BASE   "C:\Stata18\ado\base/"
  [2] PLUS   "C:\Users\user\project\code/ado/"   ← project folder
```

### Setup (do once per project)

```stata
* Create the ado folder inside code/
* Then in master.do, at the very top:

global root "C:/Users/myname/project"

* Activate project ado folder
repado using "${root}/code/ado"

* Install packages into the project folder (interactive, first-time setup only)
* Run these interactively in Stata's command window — NOT in do-files:
*   ssc install estout
*   ssc install reghdfe
*   ssc install ftools
*   ssc install repkit   (if not already in user PLUS)
```

Commit `code/ado/` to git so collaborators and replicators have identical
package files.

### Usage in master.do

```stata
version 17
set more off
clear all
macro drop _all

global root "C:/Users/myname/project"

* FIRST: activate project ado folder
repado using "${root}/code/ado"

* THEN: run analysis
do "${root}/code/01_clean.do"
do "${root}/code/02_analysis.do"
```

### `nostrict` Mode

`repado, nostrict` sets the project folder as `PERSONAL` (second priority after
`BASE`) rather than replacing PLUS entirely. This preserves access to commands in
the user's default PLUS folder.

Use `nostrict` temporarily during development — e.g., testing a package before
deciding to pin it. **The final reproducibility package must always use strict
mode** (no `nostrict`). This ensures all dependencies are either built-in or
in the project ado folder.

```stata
* Temporary development use only
repado using "${root}/code/ado", nostrict
```

### `repado` Cannot Install Itself

`repado` cannot pin its own installation. Users must have `repkit` in their
personal PLUS folder to use `repado`. The recommended approach:

```stata
cap which repkit
if _rc == 111 {
    display as error "{pstd}repkit is not installed. " ///
        "Click {stata ssc install repkit} to install it.{p_end}"
    exit 111
}
```

### Alternative — Without `repkit`

If distributing code to users who cannot install repkit, replicate `repado`'s
strict mode directly:

```stata
global root "C:/Users/myname/project"

* Set PLUS to the project ado folder
sysdir set PLUS "${root}/code/ado"
adopath ++ PLUS
adopath ++ BASE

* Remove all other ado-paths
local morepaths 1
while (`morepaths' == 1) {
    capture adopath - 3
    if _rc local morepaths 0
}
```

### Custom Graph Schemes in Strict Mode

In strict mode, Stata's PERSONAL folder (default scheme install location) is
removed. Install custom schemes directly into the project ado folder:

```stata
global root "/path/to/project/"
repado using "${root}/ado"

* Download scheme into project ado folder
local url "https://github.com/graykimbrough/uncluttered-stata-graphs/raw/master/schemes/scheme-uncluttered.scheme"
copy "`url'" "${root}/ado/scheme-uncluttered.scheme", replace

set scheme uncluttered, perm
```

---

## `repadolog` — List Installed Packages

Reports all commands installed in the current active PLUS folder. Useful for
auditing what is installed in the project ado folder.

```stata
repado using "${root}/code/ado"
repadolog
```

---

## `repkit` — Package Utility Command

`repkit` is the utility command provided by the package itself. Its primary
purpose is to make `which repkit` work, so reproducible code can check whether
repkit is installed before calling its other commands.

```stata
cap which repkit
if _rc == 111 {
    display as error "{pstd}repkit is not installed. " ///
        "Click {stata ssc install repkit} to install it.{p_end}"
    exit 111
}
```

Place this check at the top of any master do-file that uses `repado`, `reproot`,
`reprun`, `repscan`, or `lint`.

---

## `reproot_setup` — Configure Root Path Environment

`reproot_setup` is an interactive utility to create or update the
`reproot-env.yaml` file in your home directory. Run this **once per computer**
before using `reproot` on any project.

```stata
reproot_setup
```

The command opens a dialog that guides you through:
1. Specifying parent folders where your project roots live
2. Setting the recursion depth for the folder search
3. Listing folder names to skip (e.g., `.git`)

The resulting `~/reproot-env.yaml` is machine-specific and gitignored — all
projects on that machine share it so no per-project setup is needed.

**Manual alternative**: create `~/reproot-env.yaml` directly (see `reproot` Setup below).

---

## `reproot` — Dynamic Root Paths

### The Problem

Different users have the project at different absolute paths (`C:/Users/alice/`,
`/Users/bob/`, network drives). Hardcoding paths breaks for every other user.

### The Solution

`reproot` searches for `reproot.yaml` files on the user's computer. Each project
has a root file in each root folder. `reproot` reads these files and sets global
macros automatically — no manual per-user configuration in the do-file.

### Setup

**Step 1 — Create `reproot-env.yaml` (once per computer, in home folder `~`)**

```yaml
recursedepth: 4
paths:
    - "C:/Users/myname/github"
    - "C:/Users/myname/OneDrive/work"
skipdirs:
    - ".git"
```

- `recursedepth`: how many subfolder levels to search within each path
- `paths`: parent folders where root files may exist (absolute paths)
- `skipdirs`: folder names to skip (`.git` speeds up search significantly)

**Step 2 — Create `reproot.yaml` in each root folder (once per project per location)**

Single-rooted project (code and data in same folder):
```yaml
project_name: "my-project"
root_name:    "root"
```

Multi-rooted project (code on GitHub, data on OneDrive):
```yaml
# In the git repo root:
project_name: "my-project"
root_name:    "code"

# In the OneDrive data folder:
project_name: "my-project"
root_name:    "data"
```

**Step 3 — Use `reproot` in master.do**

```stata
reproot, project("my-project") roots("code" "data")
* Stata now has:
*   ${root_code} = "C:/Users/myname/github/my-project"
*   ${root_data} = "C:/Users/myname/OneDrive/work/my-project-data"
* These paths are correct for every user — no manual setup needed
```

Set up `reproot.yaml` files once; share them via git or OneDrive so other team
members get the same files without any per-user configuration.

Use `reproot_setup` to open a dialog that guides creation of `reproot-env.yaml`:
```stata
reproot_setup
```

---

## `reprun` — Automated Reproducibility Checking

`reprun` executes a do-file **twice** and compares all Stata state values between
the two runs: RNG seed state, sort-order RNG, and data checksum after every line.
Any mismatch is flagged as a reproducibility failure.

### When to Run

- Before any code review, merge, or submission
- After adding any random process (`bootstrap`, `simulate`, `sample`, etc.)
- After any refactor that touches data sorting or variable generation

### Basic Usage

```stata
* Run a do-file twice and check for mismatches
reprun "path/to/analysis.do"

* Save the comparison report to a specific location
reprun "path/to/analysis.do" using "path/to/report"

* More detail — shows all lines with changes, not just mismatches
reprun "path/to/analysis.do", verbose

* Less detail — show only seed/sort RNG lines that both change AND mismatch between runs (data checksum excluded)
reprun "path/to/analysis.do", compact
```

A SMCL report is saved in a `/reprun/` subfolder next to the do-file. Results
also print to the Results window.

### Reading the Output

The output table has three tracked states per line:

| Column | What it tracks |
|--------|---------------|
| Seed RNG State | Random number generator state — changes when `runiform()`, `rnormal()`, etc. are called |
| Sort Order RNG | Internal sort randomness — changes when data is sorted by a non-unique key |
| Data Checksum | CSV-based data snapshot — changes when any variable values change between runs |

- **DIFF**: value differs between Run 1 and Run 2 → reproducibility failure
- **Change + OK!**: value changed within the run but matches between runs → informational only

```
Example output (failure on line 3):
| Line # | Seed RNG State                    | Sort Order RNG                    | Data Checksum                     |
|--------+-----------+-----------+-------+-----------+-----------+-------+-----------+-----------+-------|
|        | Run 1     | Run 2     | Match | Run 1     | Run 2     | Match | Run 1     | Run 2     | Match |
|--------+-----------+-----------+-------+-----------+-----------+-------+-----------+-----------+-------|
| 3      | Change    | Change    | DIFF  |           |           |       | Change    | Change    | DIFF  |
```

### Common Causes of Failure and Fixes

| Cause | Fix |
|-------|-----|
| `gen x = runiform()` without `set seed` | Add `set seed 12345` before the random call |
| `sort mpg` (non-unique variable) | Sort on a unique combination: `sort mpg model` |
| `bysort id:` without secondary sort | Add secondary sort: `bysort id (year):` |
| Date/time functions (`clock()`, `now()`) | Avoid in computed variables; use a fixed reference date |

```stata
* Fix for missing seed
set seed 20240301
gen random_group = runiform() < 0.5

* Fix for non-unique sort
sort mpg make    // unique combination

* Fix for bysort without secondary sort
bysort id (year): gen obs_num = _n    // deterministic within-group order
```

### Recursive Checking (Master + Sub-files)

`reprun` steps into all do-files called by the target file, reporting mismatches
for each sub-file and showing how issues propagate back to the calling file:

```stata
reprun "master.do"
* Checks master.do, steps into 01_clean.do, 02_analysis.do, etc.
* Reports mismatches at each level and how they affect master.do
```

---

## `repscan` — Scan for Non-Reproducible Commands

`repscan` scans a do-file and flags commands known to introduce
non-reproducibility: `sort` on non-unique keys, `sample`, date functions, and
random processes without `set seed`.

Run `repscan` before `reprun` to identify likely problem areas quickly:

```stata
repscan "path/to/analysis.do"

* Recursive — scan all do-files in a folder
repscan "path/to/code/", recursive
```

---

## `lint` — Code Style Enforcement

`lint` detects and optionally corrects bad coding practices in Stata do-files.
Based on DIME Analytics Stata Style Guide standards.

**Requirements:** Stata 16+, Python 3+, Python packages `pandas` and `openpyxl`.

### Detection

```stata
* Check a single file
lint "analysis.do"

* Check with line-by-line detail
lint "analysis.do", verbose

* Check all do-files in a folder
lint "code/"
```

Example summary output:
```
Bad practice                                    Occurrences
---------------------------------------------------------------
Hard tabs used instead of soft tabs:            Yes
One-letter local name in for-loop:              3
Non-standard indentation in { } code block:     7
Lines too long (> 80 chars):                    5
Use of . where missing() is appropriate:        6
Tilde (~) used instead of bang (!) in expr:     5
Delimiter changed (#delimit):                   1
```

### Correction

```stata
* Correct to a new file (keep original as backup)
lint "bad.do" using "bad_corrected.do"

* Automatic — no interactive confirmations
lint "bad.do" using "bad_corrected.do", automatic replace
```

`lint` corrects:
- Replaces `#delimit ;` with `///` line continuations
- Replaces hard tabs with 4 soft spaces
- Indents lines inside `{ }` blocks with 4 spaces
- Breaks long lines (> 80 chars) at whitespaces using `///`
- Adds space before opening `{`
- Removes redundant blank lines after `}`

**Important:** The correction feature does not guarantee results are unchanged.
Always diff the corrected file and verify it produces identical output.

### Linting Rules — Full List

#### Style issues detected (not auto-corrected):
- One-letter index names in for-loops (use descriptive names)
- Non-standard indentation after `{`, `}`, `///`
- Missing whitespaces around operators (`+`, `=`, `<`, `>`)
- `if var` instead of `if var == 1` (implicit logic)
- Global macros referenced without `${}` braces (use `${global}` not `$global`)
- Conditions like `var != 0` that include missings (use `!missing(var)` explicitly)
- Backslashes in file paths (use forward slashes `/`)
- Tilde `~` for negation (use `!` instead)
- `cd` to change working directory (use absolute/dynamic paths)

#### Style issues detected AND auto-corrected:
- `#delimit ;` → replace with `///`
- Hard tabs → 4 soft spaces
- Non-standard indentation inside `{ }` blocks
- Lines > 80 characters → break with `///`
- Missing space before opening `{`
- Redundant blank lines after `}`
- Duplicate blank lines

### Troubleshooting Stata-Python Integration

If `lint` fails with Python-related errors on Windows with IT restrictions:

```
1. Check which Python Stata is using:
   python query
   (note the path next to "set python_exec")

2. Install required packages using that exact Python:
   "C:\wbg\Anaconda3\python.exe" -m pip install pandas openpyxl
```

---

## Reproducibility Workflow Summary

```stata
* master.do — complete reproducible setup
version 17
set more off
clear all
macro drop _all

* 1. Check repkit installed
cap which repkit
if _rc == 111 {
    display as error "Install repkit: ssc install repkit"
    exit 111
}

* 2. Set root paths (use reproot for multi-user projects)
global root "C:/Users/myname/project"
* reproot, project("my-project") roots("code" "data")   // alternative

* 3. Activate project ado folder (pins package versions)
repado using "${root}/code/ado"

* 4. Set seed if this master file calls random operations
* set seed 20240301

* 5. Run analysis
do "${root}/code/01_clean.do"
do "${root}/code/02_analysis.do"
do "${root}/code/03_tables.do"

* Before submitting/merging: run reproducibility check
* reprun "${root}/code/master.do"
* repscan "${root}/code/", recursive
* lint "${root}/code/", autofix
```
