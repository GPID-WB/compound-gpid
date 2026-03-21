---
name: cg-skill-stata-best-practices
description: >
  Comprehensive Stata best-practices reference for writing correct .do files.
  Covers universal coding principles (compound quotes, macro expansion traps,
  stored results, survey subpopulations, clustering), data management,
  econometrics, causal inference, graphics, Mata programming, reproducibility
  tools (repkit: repado, reprun, reproot, lint, repscan), and 21 community
  packages (reghdfe, estout, did, rdrobust, etc.). Covers syntax, options,
  gotchas, and idiomatic patterns. ALWAYS load this skill when writing,
  reviewing, or debugging any Stata code.
---

# Stata Best-Practices Skill

You have access to comprehensive Stata reference files. **Do not load all files.**
Read only the 1-3 files relevant to the user's current task using the routing table below.

---

## Routing Table

Read only the files relevant to the user's task. Paths are relative to this SKILL.md file.

### Data Operations
| File | Topics & Key Commands |
|------|----------------------|
| `references/basics-getting-started.md` | `use`, `save`, `describe`, `browse`, `sysuse`, basic workflow |
| `references/data-import-export.md` | `import delimited`, `import excel`, ODBC, `export`, web data |
| `references/data-management.md` | `generate`, `replace`, `merge`, `append`, `reshape`, `collapse`, `recode`, `egen`, `encode`/`decode` |
| `references/variables-operators.md` | Variable types, `byte`/`int`/`long`/`float`/`double`, operators, missing values (`.<.a`), `if`/`in` qualifiers |
| `references/string-functions.md` | `substr()`, `regexm()`, `strtrim()`, `split`, `ustrlen()`, regex, Unicode |
| `references/date-time-functions.md` | `date()`, `clock()`, `%td`/`%tc` formats, `mdy()`, `dofm()`, business calendars |
| `references/mathematical-functions.md` | `round()`, `log()`, `exp()`, `abs()`, `mod()`, `cond()`, distributions, random numbers |

### Statistics & Econometrics
| File | Topics & Key Commands |
|------|----------------------|
| `references/descriptive-statistics.md` | `summarize`, `tabulate`, `correlate`, `tabstat`, `codebook`, weighted stats |
| `references/linear-regression.md` | `regress`, `vce(robust)`, `vce(cluster)`, `test`, `lincom`, `margins`, `predict`, `ivregress` |
| `references/panel-data.md` | `xtset`, `xtreg fe`/`re`, Hausman test, `xtabond`, dynamic panels |
| `references/time-series.md` | `tsset`, ARIMA, VAR, `dfuller`, `pperron`, `irf`, forecasting |
| `references/limited-dependent-variables.md` | `logit`, `probit`, `tobit`, `poisson`, `nbreg`, `mlogit`, `ologit`, `margins` for nonlinear |
| `references/bootstrap-simulation.md` | `bootstrap`, `simulate`, `permute`, Monte Carlo |
| `references/survey-data-analysis.md` | `svyset`, `svy:`, `subpop()`, complex survey design, replicate weights |
| `references/missing-data-handling.md` | `mi impute`, `mi estimate`, FIML, `misstable`, diagnostics |
| `references/maximum-likelihood.md` | `ml model`, custom likelihood functions, `ml init`, gradient-based optimization |
| `references/gmm-estimation.md` | `gmm`, moment conditions, `estat overid`, J-test |

### Causal Inference
| File | Topics & Key Commands |
|------|----------------------|
| `references/treatment-effects.md` | `teffects ra/ipw/ipwra/aipw`, `stteffects`, ATE/ATT/ATET |
| `references/difference-in-differences.md` | DiD, parallel trends, event studies, staggered adoption |
| `references/regression-discontinuity.md` | Sharp/fuzzy RD, bandwidth selection, `rdplot` |
| `references/matching-methods.md` | PSM, nearest neighbor, kernel matching, `teffects nnmatch` |
| `references/sample-selection.md` | `heckman`, `heckprobit`, treatment models, exclusion restrictions |

### Advanced Methods
| File | Topics & Key Commands |
|------|----------------------|
| `references/survival-analysis.md` | `stset`, `stcox`, `streg`, Kaplan-Meier, parametric models |
| `references/sem-factor-analysis.md` | `sem`, `gsem`, CFA, path analysis, `alpha`, reliability |
| `references/nonparametric-methods.md` | `kdensity`, rank tests, `qreg`, `npregress` |
| `references/spatial-analysis.md` | `spmatrix`, `spregress`, spatial weights, Moran's I |
| `references/machine-learning.md` | `lasso`, `elasticnet`, `cvlasso`, cross-validation |

### Graphics
| File | Topics & Key Commands |
|------|----------------------|
| `references/graphics.md` | `twoway`, `scatter`, `line`, `bar`, `histogram`, `graph combine`, `graph export`, schemes |

### Programming
| File | Topics & Key Commands |
|------|----------------------|
| `references/programming-basics.md` | `local`, `global`, `foreach`, `forvalues`, `program define`, `syntax`, `return` |
| `references/advanced-programming.md` | `syntax`, `mata`, classes, `_prefix`, dialog boxes, `tempfile`/`tempvar` |
| `references/mata-introduction.md` | Mata basics, when to use Mata vs ado, data types |
| `references/mata-programming.md` | Mata functions, flow control, structures, pointers |
| `references/mata-matrix-operations.md` | Matrix creation, decompositions, solvers, `st_matrix()` |
| `references/mata-data-access.md` | `st_data()`, `st_view()`, `st_store()`, performance tips |

### Output & Workflow
| File | Topics & Key Commands |
|------|----------------------|
| `references/tables-reporting.md` | `putexcel`, `putdocx`, `putpdf`, LaTeX integration, `collect` |
| `references/workflow-best-practices.md` | Project structure, master do-files, version control, debugging, common mistakes, running Stata from CLI (batch mode, log checking) |
| `references/external-tools-integration.md` | Python via `python:`, R via `rsource`, shell commands, Git |

### Best Practices & Reproducibility
| File | When to Read |
|------|-------------|
| `references/coding-principles.md` | Reviewing any Stata code for correctness; compound quotes; macro expansion traps; stored results; survey subpopulations; clustering; `bysort` secondary sort; `set seed` for reproducibility; anti-patterns checklist |
| `packages/repkit.md` | Using `repado` to pin packages, `reprun` for reproducibility checks, `reproot` for dynamic root paths, `lint` for code style enforcement, `repscan` for non-reproducible command detection |

### Community Packages
| `packages/reghdfe.md` | High-dimensional fixed effects OLS (absorbs multiple FE sets efficiently) |
| `packages/estout.md` | `esttab`/`estout`: publication-quality regression tables |
| `packages/outreg2.md` | Alternative regression table exporter (Word, Excel, TeX) |
| `packages/asdoc.md` | One-command Word document creation for any Stata output |
| `packages/tabout.md` | Cross-tabulations and summary tables to file |
| `packages/coefplot.md` | Coefficient plots from stored estimates |
| `packages/graph-schemes.md` | `grstyle`, `schemepack`, `plotplain` — better graph themes |
| `packages/did.md` | Modern DiD: `csdid`, `did_multiplegt`, `did_imputation` (Callaway-Sant'Anna, de Chaisemartin-D'Haultfoeuille, Borusyak-Jaravel-Spiess) |
| `packages/event-study.md` | `eventstudyinteract`, `eventdd` — event study estimators |
| `packages/rdrobust.md` | Robust RD estimation with optimal bandwidth (`rdrobust`, `rdplot`, `rdbwselect`) |
| `packages/psmatch2.md` | Propensity score matching (nearest neighbor, kernel, radius) |
| `packages/synth.md` | Synthetic control method (`synth`, `synth_runner`) |
| `packages/ivreg2.md` | Enhanced IV/2SLS: `ivreg2`, `xtivreg2` with additional diagnostics |
| `packages/xtabond2.md` | Dynamic panel GMM (Arellano-Bond/Blundell-Bond) |
| `packages/binsreg.md` | Binned scatter plots with CI (`binsreg`, `binstest`) |
| `packages/nprobust.md` | Nonparametric kernel estimation and inference |
| `packages/diagnostics.md` | `bacondecomp`, `xttest3`, collinearity, heteroskedasticity tests |
| `packages/winsor.md` | Winsorizing and trimming: `winsor2`, `winsor` |
| `packages/data-manipulation.md` | `gtools` (fast collapse/egen), `rangestat`, `egenmore` |
| `packages/package-management.md` | `ssc install`, `net install`, `ado update`, finding packages |
