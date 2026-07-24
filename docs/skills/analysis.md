# Analysis and Economics Skills

These skills support data scientists and economists working in R, Python, and
Stata. They provide task guidance; they do not assert that a result is correct
without project-specific data, assumptions, and validation.

| Skill | Purpose | When to use | Availability | Source |
|---|---|---|---|---|
| `cg-skill-python-best-practices` | Python guidance for polars, FastAPI, pydantic, pytest, loguru, typing, profiling, and `uv` | Creating or reviewing Python, notebooks, APIs, data processing, or asynchronous code | Broad; language-conditional | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-python-best-practices/SKILL.md) |
| `cg-skill-r-analytical` | Survey analysis, welfare and poverty measurement, inequality, econometrics, Stata migration, tables, and research documents | Analytical R work, especially economic and official-statistics workflows | Broad; language-conditional | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-r-analytical/SKILL.md) |
| `cg-skill-r-collapse` | Fast grouped, weighted, panel, and summary statistics with `collapse` | Aggregation, transformations, weighted statistics, or panel operations in either supported R dialect | Broad; automatically loaded for matching R tasks | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-r-collapse/SKILL.md) |
| `cg-skill-r-datatable` | `data.table` filtering, mutation, joins, reshaping, I/O, keys, and performance patterns | Data management when `r-syntax` is `data.table-collapse` or code already uses `data.table` | Conditional dialect | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-r-datatable/SKILL.md) |
| `cg-skill-r-tidyverse` | Modern dplyr, tidyr, readr, stringr, and purrr patterns, retaining `collapse` for weighted statistics | Data management when `r-syntax` is `tidyverse` or code already uses that ecosystem | Conditional dialect | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-r-tidyverse/SKILL.md) |
| `cg-skill-r-visualization` | World Bank chart conventions using ggplot2 and wbplot, including themes, colors, chart choices, and export | Creating or reviewing R visualizations for institutional use | Broad; task-conditional | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-r-visualization/SKILL.md) |
| `cg-skill-stata-best-practices` | Routed Stata reference for coding, data work, econometrics, causal inference, graphics, Mata, repkit, and community packages | Writing, reviewing, or debugging any `.do` or `.ado` file | Broad; language-conditional | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-stata-best-practices/SKILL.md) |
| `cg-skill-stata-testing` | Stata assertions, data validation, result verification, reproducibility checks, and test scaffolding | Adding or reviewing Stata validation, tests, or replication checks | Conditional testing layer | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-stata-testing/SKILL.md) |

## Common combinations

- R analytical work: `r-analytical` + `r-shared` + the selected manipulation
  dialect + `r-collapse`; add `r-visualization` or `r-testing` by task.
- Stata analytical work: `stata-best-practices`; add `stata-testing` for
  assertions, result checks, and reproducibility scaffolding.
- Python data/API work: `python-best-practices`, with review agents selected by
  the workflow's risk route.

## Related pages

- [Development and Testing Skills](development.md)
- [Review and Assure](../workflows/assure.md)
- [Governance and Security](../governance/index.md)
