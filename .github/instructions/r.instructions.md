---
applyTo: "**/*.R,**/*.r,**/*.Rmd"
---

# R Dialect Router

Check `compound-gpid.local.md` for the `r-syntax` field and load the appropriate dialect skill(s):

- `r-syntax: "data.table-collapse"` (or field absent → default): load `cg-skill-r-collapse` AND `cg-skill-r-datatable`
- `r-syntax: "tidyverse"`: load `cg-skill-r-tidyverse`
- Any other value: default to `data.table-collapse` behavior and warn the user. Accepted values: `"data.table-collapse"` and `"tidyverse"`.

Regardless of dialect, also load:

- `cg-skill-r-visualization` when writing or reviewing visualization code (`ggplot2`, `wbplot`)
- `cg-skill-r-analytical` for domain-specific analytical work (survey analysis, welfare measurement, econometrics, Stata migration)
- `cg-skill-r-technical` for infrastructure work (packages, plumber, Shiny, targets, httr2, renv)
- `cg-skill-r-testing` when writing, reviewing, or debugging R tests
- `cg-skill-r-shared` for base R style rules (`<-` assignment, `snake_case`, `TRUE`/`FALSE`, line length)
