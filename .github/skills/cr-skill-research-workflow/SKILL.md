---
name: cr-skill-research-workflow
module: research
description: "Overarching conventions for the compound-research workflow loop.
  Covers research task taxonomy (8 types), Research Integrity Priority System
  (P0–P3), active P0 detection mechanisms, verification chain, .cg-docs/research/
  layout, reasoning-trail documentation, and PhD student scaffolding conventions.
  ALWAYS load for any /cr-* command."
---

# Compound Research Workflow

Reference skill for the `/cr-*` research workflow loop. Load for every research
task regardless of type.

---

## Research Task Taxonomy

Classify every research request into one of these 8 types before beginning work.
The task type determines which skills and agents are loaded.

| Type | Description | Examples |
|------|-------------|---------|
| **Theory/Modeling** | Economic model derivation, DGP specification, identification strategy design | Structural demand model, Roy model of selection, DiD identification proof |
| **Specification Analysis** | Choosing regressors, functional forms, interaction terms from theoretical predictions | Testing linear vs log-log wage equation, instrument validity analysis |
| **EDA** | Exploratory data analysis motivated by research question | Distribution checks, covariate balance, pre-trend analysis |
| **Implementation** | Coding a previously derived model or estimator | Coding MLE from derivation, implementing custom GMM estimator |
| **ML/Prediction** | Prediction-focused ML with economic interpretation | Causal forests, LASSO for control selection, poverty prediction |
| **Writing** | Academic writing, results narration, abstract, literature review | Introduction section, results table narrative, referee response |
| **Tables/Figures** | Producing publication-quality output | Regression tables, distribution plots, event-study graphs |
| **Reproducibility** | Replication packages, environment setup, seed management | Archive for journal submission, Docker environment, repkit workflow |

---

## Research Integrity Priority System (P0–P3)

### P0 — BLOCKING (active enforcement during `/cr-work`)

Silent errors that produce wrong results without warning. Must be caught and
fixed before any output is shared or published.

| Category | Detection | Remediation |
|----------|-----------|-------------|
| **Code-math mismatch** | Compare variable names, functional forms, and operations between LaTeX derivation and code | Side-by-side audit; variable mapping table |
| **Specification searching** | Count estimation runs in manifest vs. specifications reported in paper | Report all specifications or document the selection criterion explicitly |
| **Identification theater** | Claimed strategy (IV/RDD/DiD) without matching diagnostic (first-stage F, McCrary, parallel trends) | Run the diagnostic; if it fails, revisit the identification strategy |
| **Unseeded randomness** | Scan for bootstrap/simulation/CV calls without preceding `set.seed()` / `np.random.seed()` / `set seed` | Add explicit seed at the top of every random code block |
| **Asymptotic assumption violations** | Check sample size against estimator requirements (MLE needs n >> p). Flag when n/p < 10 | Revisit estimator choice or document the limitation explicitly |
| **Wrong SE clustering** | Check if clustering level matches the treatment variation level | Fix clustering level; document mismatch if intentional |
| **Distributional assumption untested** | Model assumes distributional form (normal errors, log-normal wages) without an empirical test | Run the appropriate test; document if test is infeasible |

### P1 — CRITICAL (must fix before results are shared)

Errors that cause incorrect behavior but are not silently hidden.

- Incorrect welfare/poverty weights (summing instead of averaging)
- PPP vintage mismatch between datasets
- Incorrect standard error formula for survey data
- Missing `quietly` or `preserve/restore` corrupting intermediate data

### P2 — IMPORTANT (fix before final results)

- Missing robustness checks standard for the identification strategy
- Key assumptions not tested (e.g., parallel trends, McCrary)
- Reproducibility gaps (missing seed, relative paths not used)
- Documentation gaps for modeling choices

### P3 — ADVISORY (note, don't block)

- Alternative functional forms worth exploring
- Presentation improvements for tables/figures
- Additional robustness specs to mention in paper

---

## Active P0 Detection Mechanisms

These run automatically during `/cr-work` before executing code.

### 1. Seed Enforcement
Before executing any code involving randomness, check for an explicit seed:
- R: `set.seed(<n>)` immediately before the random block
- Python: `np.random.seed(<n>)` or `random.seed(<n>)`
- Stata: `set seed <n>`

**If missing**: halt, add seed, log seed value in the specification manifest.

### 2. Specification Logging
When running estimation code, append to `.cg-docs/research/results/manifest.json`:
```json
{"date": "YYYY-MM-DD", "description": "...", "file": "...", "seed": null_or_N}
```
Create the file if absent. This enables specification-search detection during review.

### 3. Derivation Cross-Reference
When implementing from a derivation, load the corresponding
`.cg-docs/research/derivations/*.tex` or `.md` file and verify:
- Variable names match between derivation and code
- Functional forms are identical (not just equivalent)
- Summation/integration limits match

### 4. Identification Audit
When a causal identification strategy is claimed, check for the required diagnostic:
- IV: first-stage F-statistic ≥ 10 (or Montiel-Pflueger robust F)
- RDD: McCrary density test
- DiD: parallel trends (visual + statistical)
- Matching: overlap/common support

---

## Verification Chain

| When | What | Who |
|------|------|-----|
| During `/cr-work` | P0 active detection (seed, spec logging, derivation cross-ref) | Agent (automatic) |
| During `/cr-review` | Derivation trail audit, symbolic checks (if derivation exists) | `@cr-mathematical-verification` |
| After `/cr-review` | Monte Carlo simulation to validate estimator | User-requested (offer in Step 5) |
| Always | Reasoning-trail documentation | Agent (for every modeling choice) |

---

## `.cg-docs/research/` Directory Layout

```
.cg-docs/research/
├── derivations/        # LaTeX or Markdown derivations (.tex, .md)
├── specifications/     # Spec memos: what models were tested and why
├── results/
│   └── manifest.json  # Auto-appended by /cr-work on every estimation run
├── manuscript/         # Working paper drafts, sections
└── replication/        # Journal submission replication materials
```

Created by `/cg-setup` when `modules:` includes `research`.

---

## Reasoning Trail Documentation

Every research artifact must record the *why*, not just the *what*:

1. **Modeling choice**: Why this functional form? What alternatives were considered?
2. **Identification strategy**: What variation is being exploited? What threats exist?
3. **Data decision**: Why this sample? What observations are excluded and why?
4. **Specification choice**: If this specification was selected from alternatives, document the selection criterion.

Use the `.cg-docs/research/specifications/` directory for decision memos.

---

## PhD Student Scaffolding Convention

When a research step involves a modeling choice, document the reasoning at a
level appropriate for a PhD student learning the methodology:

- State the economic intuition, not just the technical decision
- Identify the key identifying assumption and explain why it might or might not hold
- Reference the canonical paper that established this method
- Flag alternative approaches and why the chosen approach is preferred for this application

This convention turns implementation work into a living methodology record.
