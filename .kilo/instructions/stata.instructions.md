---
applyTo: "**/*.do,**/*.ado"
---

# Stata Coding Standards

> **Full guidance**: Load `cg-skill-stata-best-practices` for the complete reference including coding principles,
> reproducibility tools (repkit), and all Stata patterns. This file is a condensed rule-reference for common standards.

Also load:

- `cg-skill-stata-testing` when writing, reviewing, or debugging test blocks, assertion patterns, or reproducibility checks

## MCP Stata connection
- Make sure you have the MCP Stata connection set up and working. If not, notify the user. If you do, make sure you use it to test everything you do. 

## Macro System

- Prefer `local` macros over `global`. Globals persist across do-files and break reproducibility.
- Use compound double quotes whenever the macro value may contain spaces, quotes, apostrophes, or dynamic content. The opening delimiter is backtick + double-quote (ASCII 96 + 34), the closing delimiter is double-quote + single-quote (ASCII 34 + 39). Regular double quotes (`""`, ASCII 34) can appear freely inside compound double quotes without breaking the string. Example: `` `"She said "hello" to `name'"' ``.
- Always use compound quotes for `tempfile` paths — file paths are unpredictable.
- Use `macro drop _all` at the top of master do-files to clear stale globals.
- Name globals with a project prefix to avoid collisions: `$project_root`, not `$root`.
- Globals belong only in master do-files. Subordinate do-files define only locals.

## Comments

- Use `//` as the default comment style for both full-line and inline comments.
- `*` is valid ONLY at the start of a line. Mid-line, `*` is the multiplication operator — NOT a comment. This is the #1 Copilot-generated Stata bug.
- Reserve `*` exclusively for section delimiter lines: `* ---- 1. Section name -----`.
- Use `/* ... */` for block comments and header blocks.
- Never place `*` after code on the same line.

## Program Scoping

- Declare return type explicitly: `rclass` for programs returning `r()` results, `eclass` for estimation commands. Plain programs return nothing.
- Save stored results to locals **immediately** after the command that produces them — the next command of the same class wipes them.
- Use `syntax` (not `args`) for argument parsing in non-trivial programs.
- Use `marksample touse` in estimation programs to handle `if`/`in` qualifiers correctly.

## Data Management

- Use `tempvar`, `tempname`, `tempfile` exclusively for temporary objects. Never invent `_temp_` prefixes manually.
- Use `preserve`/`restore` for within-do-file transforms. Use `tempfile` when data must survive a program call.
- Always specify a secondary sort variable in `bysort` for order-sensitive operations: `bysort hhid (year):`.
- After every `merge`, check `_merge` with `tabulate _merge` and assert the expected result before dropping `_merge`.

## Reproducibility

- Every do-file starts with `version 17` (or appropriate version), `set more off`, and `clear all`.
- Make use of `repkit` Stata package for reproducibility by adding it `cap which repkit` into the main do-file. If not, warn the user and suggest to install it from SSC with `ssc install repkit`. 
- if `repkit` is installed, the following are available: 

| Command | Description |
| --- | --- |
| [repado](https://worldbank.github.io/repkit/reference/repado.html) | Command used to manage a project's dependencies of commands installed from external sources such as SSC. This command provides a way to make sure that all team members as well as future reproducers of the projects code use the exact same version of all command dependencies. |
| [repadolog](https://worldbank.github.io/repkit/reference/repadolog.html) | Outputs a report of the commands installed in the current PLUS folder. |
| [repkit](https://worldbank.github.io/repkit/reference/repkit.html) | Command named the same as the package. Most important purpose is that this command makes the code `which repkit` work. |
| [reproot](https://worldbank.github.io/repkit/reference/reproot.html) | This command allows teams to dynamically set root-paths with no manual user-specific set-up, in both single-rooted and multi-rooted projects. |
| [reproot_setup](https://worldbank.github.io/repkit/reference/reproot_setup.html) | This command helps setting up the environment setting file used in `reproot` |
| [reprun](https://worldbank.github.io/repkit/reference/reprun.html) | This command is used to automate reproducibility checks by running a do-file or a set of do-files and compare all state values (seed RNG state, sort-order RNG, data checksum) between the two runs. This command is currently only release as a beta-version. |
| [repscan](https://worldbank.github.io/repkit/reference/repscan.html) | Scans a do-file and flags the use of commands that may cause issues with the reproducibility of results. |
| [lint](https://worldbank.github.io/repkit/reference/lint.html) | `lint` is an opinionated detector that attempts to improve the readability and organization of Stata do files. The command is written based on the good coding practices of the Development Impact Evaluation Unit at The World Bank. |


- Use `repado` to pin package versions into a project-local `code/ado/` folder.
- Set `set seed` before any random process (`bootstrap`, `simulate`, `sample`, `splitsample`).
- Run `reprun` before every merge request to detect non-reproducible results.
- Run `lint` on all do-files. Use `///` for continuation lines, never `#delimit ;`.

## Do-file Organization

- Every do-file has a standard header block: project, filename, date, author, purpose, inputs, outputs.
- Open a log at the start: `capture log close` then `` log using `"${project_root}/output/logs/${dofile_name}.log"', replace text `` (use a global-rooted path, not a bare filename).
- Use section delimiters: `* ---- 1. Section name -----`.
- Keep do-files under 300 lines. Split by responsibility.
- Master do-file contains zero analysis code — only globals, `repado`, and `do` calls.

## Naming Conventions

- Variables: `lowercase_with_underscores`. Use prefixes: `is_` for dummies, `ln_` for logs, `d_` for differences.
- Locals: short, descriptive, matching the variable they reference when possible.
- Programs/ado files: `lowercase_with_underscores`, prefixed with project identifier for team programs (e.g., `proj_measure`).
- Never use CamelCase or ALL_CAPS for variable names.

## Common Anti-Patterns to Avoid

- `=` instead of `==` in `if` conditions (silently wrong, not an error).
- String vs numeric type confusion in `if` conditions (silently produces no matches).
- `replace` without a units comment documenting before/after units.
- Missing `quietly` inside loops and programs (enormous log output).
- `merge` without checking `_merge`.
- `forvalues` for non-sequential or non-integer lists (use `foreach` instead).
- `log using` without `replace` or `append` (errors on second run).
- Missing `set more off` and `version` at the top of do-files.

## Documentation

- Every distributed `.ado` file (community package or reusable team library) starts with `*!` version comments parsed by `which`.
- Use the standard do-file header block for all production do-files.
- Document units before and after every `replace` that transforms units.
- Complex logic should have inline comments explaining *why*, not *what*.
