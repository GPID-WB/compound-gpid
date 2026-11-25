---
type: verification-profile
status: draft
---

# Verification profile

How this project is run and checked (principle P4). The status stays `draft` until the Run command has been run from start to finish. Fix this file before using it whenever it no longer matches the project.

## Run

The one command that produces the outputs from the inputs:

```
not found
```

## Doctor

One command that only reads, and shows the environment is fit to run (package versions, data vintage present, credentials valid):

```
Rscript -e 'devtools::test()'
```

## Outputs map

| Output | Where it lives | What proves it right |
|---|---|---|
| `read_survey()` | `R/read_survey.R` | `tests/testthat/test-read_survey.R`: 20 rows, columns `hhid`, `welfare`, `weight`, error on non-positive weight. Not yet covered: missing columns, non-positive `welfare`, duplicate `hhid`. |

## Evidence

Evidence is kept in `.cg-docs/work-reports/`. It holds commands, exit codes, digests and counts, and never data.
