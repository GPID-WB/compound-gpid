---
applyTo: "**/*.do,**/*.ado"
---

# Stata Coding Standards

> **Full guidance**: Load `cg-skill-stata-core` for macro system, program scoping, data management, and
> reproducibility patterns. Load `cg-skill-stata-research` for survey econometrics, welfare measurement,
> and causal inference. This file is a condensed rule-reference for common standards.

## Macro System

- Prefer `local` macros over `global`. Globals persist across do-files and break reproducibility.
- Use compound double quotes whenever the macro value may contain spaces, quotes, apostrophes, or dynamic content. The opening delimiter is backtick + double-quote (ASCII 96 + 34), the closing delimiter is double-quote + single-quote (ASCII 34 + 39). Regular double quotes (`""`, ASCII 34) can appear freely inside compound double quotes without breaking the string. Example: `` `"She said "hello" to `name'"' ``.
- Always use compound quotes for `tempfile` paths — file paths are unpredictable.
- Use `macro drop _all` at the top of master do-files to clear stale globals.
- Name globals with a project prefix to avoid collisions: `$gpid_root`, not `$root`.
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
- Use `repado` to pin package versions into a project-local `code/ado/` folder.
- Set `set seed` before any random process (`bootstrap`, `simulate`, `sample`, `splitsample`).
- Run `reprun` before every merge request to detect non-reproducible results.
- Run `lint` on all do-files. Use `///` for continuation lines, never `#delimit ;`.

## Do-file Organization

- Every do-file has a standard header block: project, filename, date, author, purpose, inputs, outputs.
- Open a log at the start: `capture log close` then `` log using `"${gpid_root}/output/logs/${dofile_name}.log"', replace text `` (use a global-rooted path, not a bare filename).
- Use section delimiters: `* ---- 1. Section name -----`.
- Keep do-files under 300 lines. Split by responsibility.
- Master do-file contains zero analysis code — only globals, `repado`, and `do` calls.

## Naming Conventions

- Variables: `lowercase_with_underscores`. Use prefixes: `is_` for dummies, `ln_` for logs, `d_` for differences.
- Locals: short, descriptive, matching the variable they reference when possible.
- Programs/ado files: `lowercase_with_underscores`, prefixed with project identifier for team programs (e.g., `gpid_fgt`).
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
