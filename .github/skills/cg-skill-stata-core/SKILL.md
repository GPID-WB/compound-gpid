---
name: cg-skill-stata-core
description: "Core Stata language patterns for the GPID team. Covers the macro system (local vs global, compound quotes, expansion order), program scoping (rclass/eclass, stored results lifetime), data management idioms (tempvar/tempfile, preserve/restore, by-groups), and reproducibility tools (repkit, repado, reprun, lint). Consumed by cg-work and review agents whenever .do or .ado files are present. ALWAYS load this skill when writing, reviewing, or debugging any Stata code — Copilot's default Stata output contains silent errors that this skill corrects."
---

# Stata Core Patterns

Reference skill for Stata development in the GPID team at the World Bank. Copilot's default Stata output is dangerous: it produces syntactically valid code that runs without errors but yields silently wrong results — wrong macro scoping, dropped stored results, non-reproducible sort orders. This skill corrects the most common failure patterns and enforces the conventions required for official poverty and inequality statistics.

**This skill covers language fundamentals.** For survey econometrics, welfare aggregates, and poverty measurement patterns, see `cg-skill-stata-research`.

---

## Quick Reference

| Topic | Key Rule | Detail |
|-------|----------|--------|
| `local` vs `global` | Prefer `local`; globals leak across do-files and break reproducibility | [Macro System](workflows/macro-system.md) |
| Compound quotes | Use `` `"`macroname'"' `` whenever macro may contain spaces, quotes, or dynamic content | [Macro System](workflows/macro-system.md) |
| Macro expansion | Variables without quotes expand at assignment time; quoted strings do not — know the difference | [Macro System](workflows/macro-system.md) |
| Program return type | Declare `rclass` or `eclass` explicitly; plain programs return nothing | [Program Scoping](workflows/program-scoping.md) |
| Stored results | Save `r()` and `e()` results to locals *immediately* after the command — the next command wipes them | [Program Scoping](workflows/program-scoping.md) |
| Temp objects | Use `tempvar`, `tempname`, `tempfile` — never invent `_temp_` names manually | [Data Management](workflows/data-management.md) |
| `preserve`/`restore` | For within-do-file transforms; use `tempfile` when data must survive a program call | [Data Management](workflows/data-management.md) |
| `by:` vs `bysort:` | `bysort:` sorts first; `by:` requires pre-sorted data. Always specify secondary sort for order-sensitive ops | [Data Management](workflows/data-management.md) |
| `repado` | Pin package versions into `code/ado/` at project start | [Reproducibility](workflows/reproducibility.md) |
| `reprun` | Run before every merge/submission to detect non-reproducible results | [Reproducibility](workflows/reproducibility.md) |
| `lint` | Run on all do-files; use `autofix` for safe corrections | [Reproducibility](workflows/reproducibility.md) |
| `set seed` | Required before any bootstrap, simulate, or sample command | [Reproducibility](workflows/reproducibility.md) |
| Comments | Use `//` for all inline comments; `*` is valid only at the start of a line — mid-line `*` is multiplication | [Anti-Patterns](references/stata-anti-patterns.md) |

---

## Workflows

- [Macro System](workflows/macro-system.md) — `local` vs `global`, compound quotes, expansion order, debugging
- [Program Scoping](workflows/program-scoping.md) — `rclass`/`eclass`, stored results, argument parsing with `syntax`
- [Data Management](workflows/data-management.md) — `tempvar`/`tempfile`, `preserve`/`restore`, `by:`/`bysort:`, `_n`/`_N`
- [Reproducibility](workflows/reproducibility.md) — `repkit`, `repado`, `reprun`, `lint`, `set seed`

## References

- [Anti-Patterns](references/stata-anti-patterns.md) — 11 patterns Copilot generates incorrectly; consult before reviewing any Stata output
- [Do-file Conventions](references/do-file-conventions.md) — Standard header, file organization, naming conventions, master do-file rules

---

## When to Load This Skill

Load this skill whenever:
- Any `.do` or `.ado` file is open or being created
- The user mentions: Stata, macros, `local`, `global`, `program define`, `preserve`, `svyset`, `merge`, `reshape`, `tempvar`, `tempfile`
- Writing loops (`forvalues`, `foreach`) in Stata
- Writing programs that return results (`rclass`, `eclass`)
- Reviewing Stata code for correctness or reproducibility
- The `cg-code-quality` or `cg-reproducibility` agents are running on a project with `.do` files
