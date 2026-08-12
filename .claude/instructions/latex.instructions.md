---
applyTo: "**/*.tex,**/*.Rnw"
module: research
---

# LaTeX and Sweave/knitr Coding Standards

> **Full guidance**: Load `cr-skill-mathematical-derivation` for the complete
> reference including notation discipline, equation conventions, FOC derivation
> patterns, and code-math variable mapping tables.

---

## Equation Environments

- Use `align` (not `eqnarray`) for multi-line derivations
- Use `equation` for single numbered equations
- Use `align*` for intermediate algebra steps (no numbers)
- Number only equations that are referenced: `\label{eq:<name>}`
- Cross-reference with `\eqref{eq:name}` (not `\ref`)

## Notation Conventions

- `\mathbb{R}`, `\mathbb{E}`, `\mathbb{P}` for reals, expectation, probability
- `\mathcal{L}`, `\mathcal{F}` for likelihood, filtration
- `\boldsymbol{\beta}` for parameter vectors; `\beta_k` for scalar components
- `\text{}` inside math mode for words: `p(\text{work} \mid x)`
- Never reuse a letter for two different objects in the same document

## BibTeX / BibLaTeX

- Use `biblatex` with `style=apa` for economics papers
- Cite with `\textcite{Author2020}` (narrative) or `\parencite{Author2020}` (parenthetical)
- Keep `.bib` file in `references/` directory; name by first-author year
- Always include `doi` field when available

## Cross-Reference Conventions

- Figures: `\label{fig:<name>}` → `Figure~\ref{fig:<name>}`
- Tables: `\label{tab:<name>}` → `Table~\ref{tab:<name>}`
- Equations: `\label{eq:<name>}` → `\eqref{eq:<name>}` (automatic parentheses)
- Sections: `\label{sec:<name>}` → `Section~\ref{sec:<name>}`
- Use `~` (non-breaking space) before `\ref` and `\eqref`

## Required Packages

```latex
\usepackage{amsmath, amssymb, amsthm}   % math environments
\usepackage{bm}                          % \bm{} bold math (prefer \boldsymbol)
\usepackage{booktabs}                    % professional tables (\toprule, \midrule)
\usepackage{natbib}                      % or biblatex
\usepackage{hyperref}                    % clickable cross-references
\usepackage{cleveref}                    % \cref{} for smart cross-references
\usepackage{siunitx}                     % number formatting in tables
```

## Variable Mapping Table

Every `.tex` derivation file must include a variable mapping table linking
math symbols to code variables. See `cr-skill-mathematical-derivation` Section 6.
This enables `@cr-mathematical-verification` to audit the implementation.

## Anti-Patterns

- `eqnarray` — outdated; produces wrong spacing; use `align`
- Numbering every equation line — number only cited equations
- `$` for display math — use `\[...\]` or `equation` environment
- Hard-coded numbers in text (e.g., "the coefficient 1.234") — use `\num{1.234}` (siunitx)
