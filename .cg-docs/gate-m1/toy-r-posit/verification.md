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
not found
```

## Outputs map

| Output | Where it lives | What proves it right |
|---|---|---|
| Survey reader return value | `R/read_survey.R` | Existing tests check dimensions, names and rejection of a non-positive weight. |
| Proposed headcount share | Not yet implemented | Human's prior expectation for the toy survey: 0.153846; not yet verified. |

## Evidence

Evidence is kept in `.cg-docs/work-reports/`. It holds commands, exit codes, digests and counts, and never data.
