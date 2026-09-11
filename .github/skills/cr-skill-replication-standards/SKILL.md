---
name: cr-skill-replication-standards
module: research
description: "AEA/AER replication package standards for journal submission.
  Covers archive structure, README templates, dependency lockfiles, seed
  registries, data documentation (codebook + data dictionary), path
  portability rules, sensitive-data handling, and archive packaging checklists.
  Loaded by @cr-replication-package for Reproducibility tasks."
---

# Replication Standards

Reference skill for building and auditing journal-submission replication
packages. Load for all Reproducibility task types.

The canonical in-project staging location is `c-research/replication/`. A
submission archive exported from that location may use the AEA root name
`replication-package/`; the export is derived and is not a second project
authority. Do not create project data inputs under `c-research/`; keep them in
the separate project `data/` location and include them in an export only when
the archive policy permits it.

---

## 1. AEA Archive Structure

The American Economic Association Data and Code Availability Policy requires
a self-contained archive that a third party can run without contacting the
authors.

### Required Top-Level Layout of an Exported Archive

The following `replication-package/` tree describes the root of an exported
submission archive. It is not the canonical in-project path.

```
replication-package/
├── README.md               # Entry point — instructions, data sources, runtime
├── code/                   # All scripts, in order of execution
│   ├── main.R              # Master script that runs the entire pipeline
│   ├── 01_data_prep.R
│   ├── 02_analysis.R
│   └── 03_tables_figures.R
├── data/
│   ├── raw/                # Immutable original data (or instructions to obtain)
│   └── derived/            # Intermediate datasets produced by code
├── output/                 # Final tables and figures
└── environment/            # Lockfiles, environment specs
    ├── renv.lock           # R environment
    ├── requirements.txt    # Python environment (or pyproject.toml + uv.lock)
    └── stata_packages.txt  # List of Stata packages (installed via repado)
```

### Master Script Pattern

The master script must be runnable from a clean environment in a single call:

```r
# main.R — runs the entire replication pipeline
# Expected runtime: ~45 minutes on [CPU spec]
# Memory: ~8 GB peak

source("code/01_data_prep.R")
source("code/02_analysis.R")
source("code/03_tables_figures.R")
```

The master script must:
- Set working directory to the project root via `here::here()` or `reproot`
- Set a global seed at the top
- Document expected runtime and memory in comments
- Produce all outputs referenced in the README

### Expected Runtime Documentation

Every README must state:

> **Computational requirements**: Estimated runtime is X minutes (or X hours)
> on a [CPU model/specification] machine with Y GB RAM running [OS]. Peak
> memory usage is approximately Z GB.

For long-running analyses, document how to produce a minimal reproducible
subset (e.g., single bootstrap iteration).

---

## 2. README for Replication

A replication README must survive 5 years without author involvement.

### Required Sections (in order)

1. **Data availability and access**: List every dataset by name, source URL
   or institutional contact, access restrictions (public/restricted/licensed),
   and the version or vintage used. For restricted data: exact steps to apply
   for access.

2. **Software requirements**: List every language version (R 4.4.0, Python
   3.12, Stata 18) and every package with the exact version used. The lockfile
   (Section 3) is the authoritative source; the README summarizes human-
   readable requirements.

3. **Instructions to replicate**: Step-by-step, numbered instructions. Must
   be runnable by someone unfamiliar with the project. Start from the point
   where raw data is in `data/raw/`.

4. **Expected output**: For each output file, state what it contains and which
   table/figure in the paper it corresponds to.

5. **Computational requirements**: Runtime and memory estimates (see Section 1).

6. **Data citations**: Formal bibliographic citations for all datasets, in the
   same format as paper references.

### README Anti-Patterns

- "Run `main.R` in order" — too vague. Specify working directory and R version.
- "See paper for details" — the README must be self-contained.
- Omitting restricted-data access instructions — reviewers cannot verify.
- No runtime estimate — reviewer cannot plan replication session.

---

## 3. Dependency Lockfiles

Every language used in the project must have a committed lockfile.

| Language | Lockfile | How to create | How to restore |
|----------|----------|--------------|----------------|
| R | `renv.lock` | `renv::snapshot()` | `renv::restore()` |
| Python | `uv.lock` (preferred) or `poetry.lock` | `uv lock` or `poetry lock` | `uv sync` or `poetry install` |
| Python (legacy) | `requirements.txt` with pinned versions | `pip freeze > requirements.txt` | `pip install -r requirements.txt` |
| Stata | `code/ado/` directory | `repado, adopt` | Committed to git — auto-available |

**Rules**:
- Commit lockfiles to git — never `.gitignore` them.
- Never pin to a range (`>=1.2`) in a lockfile — exact versions only.
- If multiple languages are used, each must have its own lockfile.
- Lockfile must be regenerated after any package change.

**Verification pattern**:
```r
# Verify renv.lock is current
renv::status()  # Should report "No issues found"
```

---

## 4. Seed Management

### Seed Registry

Maintain a single seed registry file at
`c-research/results/manifest.json`. Every estimation run that uses
randomness must have an entry (see `cr-skill-research-workflow` for manifest
format).

For the replication package, also document seeds in the README and in code
comments:

```r
# Analysis seed: 12345 (registered in manifest.json, 2026-05-22)
set.seed(12345)
bootstrap_results <- boot(data, statistic = my_func, R = 1000)
```

### Seed Registry Template

Create `c-research/replication/seeds.md` in the project; the export may place
the same file at `replication-package/seeds.md`:

```markdown
# Seed Registry

| Script | Location | Seed | Purpose |
|--------|----------|------|---------|
| 02_analysis.R | Line 47 | 12345 | Bootstrap SE estimation |
| 02_analysis.R | Line 83 | 12345 | Train/test split |
| 03_tables_figures.R | Line 12 | 99 | Jitter in scatter plots |
```

All seeds must be positive integers. Use the same seed for steps that should
be jointly reproducible (e.g., bootstrap and CI calculation from same draw).

### Cross-Reference Requirement

The seed registry must cross-reference `c-research/results/manifest.json`:
every `"seed":` entry in the manifest must appear in `seeds.md` with a
matching script and line number.

---

## 5. Data Documentation

### Codebook (Required)

For every dataset used or produced, provide a codebook at
`c-research/replication/documentation/codebook-<dataset>.md` in the project,
or at `replication-package/data/codebook-<dataset>.md` in an exported archive:

```markdown
# Codebook: survey_clean.dta

| Variable | Type | Definition | Units | Values | Missing |
|----------|------|-----------|-------|--------|---------|
| welfare | float | Per capita household welfare | USD/day | [0, ∞) | 0.3% |
| weight | float | Survey sampling weight | — | (0, ∞) | 0% |
| urban | int | Urban/rural indicator | — | 0=rural, 1=urban | 0.1% |
| year | int | Survey year | — | 2018–2023 | 0% |
```

### Data Dictionary (Required for administrative/proprietary data)

If the data cannot be included in the archive (restricted access, size,
licensing), provide a data dictionary that enables a reviewer to verify the
code logic without the data:

```markdown
# Data Dictionary: admin_panel.csv (not included — restricted access)

Source: World Bank LSMS, available at [URL]
Access: Requires data-use agreement (see data/access-instructions.md)
Observations: ~50,000 households × 5 waves
Key variables: [list with types and ranges]
```

### PII/Sensitivity Checklist

Before packaging the archive, verify:

- [ ] No names, addresses, phone numbers, or email addresses in any dataset
- [ ] No government ID numbers (SSN, NIN, passport)
- [ ] No precise geocoordinates for individuals (aggregate to district or
      higher if required by data-use agreement)
- [ ] Any suppressed cells documented in the codebook

---

## 6. Path Portability

### Forbidden Patterns

Any of these patterns is a P1 finding in `@cr-replication-package`:

| Pattern | Example | Why forbidden |
|---------|---------|---------------|
| Windows absolute path | `C:\Users\analyst\data\` | Breaks on Linux/macOS |
| macOS/Linux absolute path | `/Users/analyst/projects/` | Breaks on other machines |
| Tilde expansion | `~/projects/data.csv` | Home directory varies |
| Hardcoded username | `\zprinsloo\` | Other users cannot run |
| Parent-traversal path | `../data/raw/` or `..\data\raw\` | Non-portable when subscripts are sourced from project root |

### Required Patterns

| Language | Pattern | Example |
|----------|---------|---------|
| R | `here::here("data", "raw", "survey.dta")` | Roots to project root |
| R | `reproot` globals | `"${root_data}/raw/survey.dta"` |
| Python | `pathlib.Path(__file__).parent / "data" / "raw"` | Relative to script |
| Stata | `reproot` globals | `use "${root_data}/raw/survey.dta"` |

**Rule**: If a path string contains `:`, `~`, or a username, it is forbidden.
All paths must be relative to the project root.

---

## 7. Sensitive Data Handling

### `.gitignore` Rules

Every replication archive project must have a `.gitignore` that excludes:

```gitignore
# Data files — never commit raw or derived data
data/raw/
data/derived/
*.dta
*.csv
*.parquet
*.feather

# Secrets
.Renviron
.env
*.pem
*.key
api_keys.*

# System
.DS_Store
Thumbs.db
```

Exception: small reference data (e.g., crosswalk tables ≤ 100 KB) may be
committed if they contain no PII and are not subject to licensing restrictions.

### Synthetic/Simulated Data Alternatives

When real data cannot be shared, include a synthetic data generator:

```r
# data/generate_synthetic.R
# Produces synthetic data with the same structure as the restricted dataset.
# Use for code verification only — results will not match the paper.

set.seed(42)
n <- 5000
synthetic_data <- data.frame(
  welfare = rexp(n, rate = 1/1200),
  weight  = runif(n, 0.5, 2.0),
  urban   = rbinom(n, 1, 0.6),
  year    = sample(2018:2023, n, replace = TRUE)
)
```

### Data-Use Agreement Documentation

For restricted data, provide `data/access-instructions.md`:

```markdown
# Data Access Instructions

The data used in this paper are restricted. To obtain access:

1. Contact [institution] at [email/URL]
2. Submit data-use agreement (template: [URL])
3. Expect [N weeks] processing time
4. Upon approval, download to `data/raw/` (structure matches codebook)

The authors used version [X] accessed on [date].
```

---

## 8. Archive Packaging

### File Inventory

Before submission, verify:

- [ ] Every file referenced in the README exists in the archive
- [ ] Every output file listed in Section 4 of the README is produced by the
      master script
- [ ] No file in the archive is undocumented (no orphan scripts)
- [ ] Archive can be unzipped and run from a clean environment (no assumed
      pre-installed packages beyond the lockfile)

### What to Include

| Include | Exclude |
|---------|---------|
| All code files | Intermediate output (can be regenerated) |
| All lockfiles | Raw data (if restricted/licensed) |
| README.md | `.Rhistory`, `__pycache__`, `.DS_Store` |
| seeds.md | Personal configuration (`.Renviron`, `.env`) |
| Codebooks | Log files, `.log` |
| Access instructions | Editor backup files |

### Compression and Submission

- AEA: Submit as `.zip`. Maximum 2 GB (contact editor for larger packages).
- Use lowercase, hyphenated filenames: `smith-jones-2026-replication.zip`.
- The zip must unpack to a single top-level directory: `smith-jones-2026/`.
- Test the archive by unzipping to a fresh directory and running the master
  script before submission.

---

## 9. Review Criteria

The following checklist is used by `@cr-replication-package` during audit.
Each item maps to one of the 8 checks in the agent.

**Check 1 — Archive Structure (P1)**
- [ ] Top-level layout matches Section 1 convention
- [ ] Master script exists and names all subscripts in order
- [ ] Expected runtime documented in master script and README

**Check 2 — README Completeness (P1)**
- [ ] All 6 required sections present (data availability, software, instructions,
      expected output, computational requirements, data citations)
- [ ] Instructions are step-by-step and start from raw data

**Check 3 — Dependency Lockfiles (P1)**
- [ ] Every language used has a committed lockfile
- [ ] Lockfile is current (not stale from a prior session)

**Check 4 — Seed Registry (P0)**
- [ ] Every random operation has a `set.seed()` / `set seed` / `np.random.seed()`
- [ ] seeds.md exists and lists every seed with script + line number
- [ ] seeds.md cross-references manifest.json

**Check 5 — Data Documentation (P1)**
- [ ] Codebook present for every dataset
- [ ] PII/sensitivity checklist completed
- [ ] Data-use agreement instructions provided for restricted data

**Check 6 — Path Portability (P1)**
- [ ] No absolute paths, tilde paths, or hardcoded usernames
- [ ] All paths use `here::here()`, `reproot`, or `pathlib.Path`

**Check 7 — Sensitive Data (P0)**
- [ ] `.gitignore` covers all data directories and secret files
- [ ] No PII in any committed file
- [ ] Synthetic data generator provided if real data is restricted

**Check 8 — File Inventory (P2)**
- [ ] All README-referenced files exist in the archive
- [ ] All output files are produced by the master script
- [ ] No undocumented files in the archive
