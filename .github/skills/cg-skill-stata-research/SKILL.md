---
name: cg-skill-stata-research
description: "Research methodology and analytical patterns for GPID Stata work. Enforces a 6-phase workflow (Phases 0–5: Design → Data → Specification → Analysis → Robustness → Output) with explicit pause points. Covers survey design (svyset, svy:, complex sampling), poverty and welfare measurement (FGT, PPP conversion, inequality decomposition), causal inference (DiD, RD, matching, IV), and publication-ready output (esttab, coefplot, putexcel). ALWAYS load this skill alongside cg-skill-stata-core when working on analytical .do files — poverty statistics, econometric analysis, survey-based research, or any work producing results for reports, papers, or official World Bank products."
---

# Stata Research Patterns

Research methodology skill for the GPID team at the World Bank. Enforces a
structured, phased analytical workflow that produces correct results and
auditable documentation. Designed for official poverty statistics, analytical
reports (e.g., Poverty, Prosperity and Planet Report), and academic papers.

**This skill covers research methodology.** For Stata language fundamentals
(macros, scoping, data management, reproducibility), load `cg-skill-stata-core`.
Both skills should be active when writing analytical do-files.

---

## The Phased Research Workflow

Every analytical project follows six phases with explicit pause points between
them. **Do not skip phases. Do not combine phases.** Each phase produces a
documented artifact before the next phase begins.

| Phase | Goal | Output | Detail |
|-------|------|--------|--------|
| 0. Design | Establish identification strategy before touching data | Design memo | [Research Phases](workflows/research-phases.md) |
| 1. Data | Understand the data before modeling | Data report with descriptives | [Research Phases](workflows/research-phases.md) |
| 2. Specification | Fully specify models before estimation | Specification memo with equations | [Research Phases](workflows/research-phases.md) |
| 3. Analysis | Estimate primary models and interpret results | Main results table | [Research Phases](workflows/research-phases.md) |
| 4. Robustness | Stress-test findings | Robustness tables and sensitivity assessment | [Research Phases](workflows/research-phases.md) |
| 5. Output | Publication-ready tables, figures, and interpretation | Final deliverables | [Output Workflow](workflows/output-tables.md) |

> **Hard stop between every phase.** Discuss findings and get explicit
> confirmation before proceeding. This is not a suggestion — it is required
> for any work producing official World Bank statistics.

---

## Critical Analytical Gotchas

These are methodological errors, not syntax errors. They produce results that
look correct but are wrong. These are highlights; see
[Research Anti-Patterns](references/stata-research-anti-patterns.md) for the
complete list.



---

## Routing Table

Read only the 1-3 files relevant to the current task. Paths are relative to
this SKILL.md file.

### Methodology & Workflow
| File | When to Read |
|------|-------------|
| [Research Phases](workflows/research-phases.md) | Starting any analytical project; need the phased workflow; writing a design memo or specification memo |
| [Output Workflow](workflows/output-tables.md) | Creating publication-ready tables, figures, or reports; Phase 5 of the workflow |

### Domain-Specific Methods
| File | When to Read |
|------|-------------|
| [Survey & Poverty](workflows/survey-poverty.md) | Working with survey microdata; `svyset`; poverty rates; FGT indices; Gini; welfare aggregation; PPP conversion |
| [Causal Inference](workflows/causal-inference.md) | DiD, event studies, RD, matching, IV, treatment effects; any causal claim |

### Reference
| File | When to Read |
|------|-------------|
| [Research Anti-Patterns](references/stata-research-anti-patterns.md) | Auditing existing code for suspicious results; cross-checking welfare or poverty calculations |
| [Community Packages](references/community-packages.md) | Need syntax for `reghdfe`, `estout`, `csdid`, `rdrobust`, `psmatch2`, `coefplot`, or other packages |

---

## When to Load This Skill

Load this skill whenever:
- Any `.do` file involves statistical analysis, econometrics, or poverty/inequality measurement
- The user mentions: regression, poverty, inequality, survey weights, `svyset`, DiD, event study, RD, matching, IV, FGT, Gini, PPP, poverty line, welfare
- Writing code that produces results for reports, papers, or official statistics
- The `cg-review` or `cg-reproducibility` agents are running on analytical work
- **Always load alongside `cg-skill-stata-core`** — this skill assumes core language patterns are enforced separately
