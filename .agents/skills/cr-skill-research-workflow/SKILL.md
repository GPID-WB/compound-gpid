---
name: cr-skill-research-workflow
module: research
description: "Overarching conventions for the compound-research workflow loop.
  Covers research task taxonomy (10 types), Research Integrity Priority System
  (P0–P3), active P0 detection mechanisms, verification chain, .cg-docs/research/
  layout, reasoning-trail documentation, and PhD student scaffolding conventions.
  ALWAYS load for any /cr-* command."
---

# Compound Research Workflow

Reference skill for the `/cr-*` research workflow loop. Load for every research
task regardless of type.

---

## Research Task Taxonomy

Classify every research request into one of these 10 types before beginning work.
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
| **Measurement/Classification** | Composite indicators, thresholds, clustering, and classification validity with comparability controls | Multidimensional index ranking, poverty threshold classification, cross-country cluster typologies |
| **Research Scoping** | Front-end framing and normative decision surfacing before plan lock-in | Framing alternatives, priors, success criteria, value-laden decision register |

### Deterministic Normative-Decision Gate

`/cr-brainstorm` and `/cr-work` must apply a bounded, per-task-type checklist
of value-laden decision points and check each item against the per-study
register before continuing. This is deterministic workflow logic, not model
inference.

Coverage rule for reuse of a decision ID:
- Same `study` slug
- Same decision category (e.g., threshold, weighting, framing)
- `applies_to` includes the current memo/plan step/output path
- No contradiction with the option now being used

If coverage fails, escalate to a human and record a new decision ID.

---

## Responsible Research Lifecycle

Every `/cr-*` task, regardless of type, runs inside a single eight-stage
lifecycle. The stages are the *spine*; the task type and its method pack (see
below) plug into it. The lifecycle makes the responsible-AI backbone — evidence,
measurement integrity, and normative gates — **structural and uniform** across
methods, rather than duplicated per method.

```
Scope → Evidence → Theory → Method → Execute → Verify → Communicate → Maintain
```

| Stage | Purpose | Responsible surface(s) |
|-------|---------|------------------------|
| **Scope** | Frame the question; surface value-laden decisions before lock-in | `cr-skill-research-scoping` + Normative-Decision Gate |
| **Evidence** | Establish source authority and claim provenance | `cr-skill-evidence-provenance` + `@cr-provenance-audit` |
| **Theory** | Derive the model / identification argument | `cr-skill-structural-econometrics` / `cr-skill-mathematical-derivation` |
| **Method** | Select and configure the estimator | the **method pack** (structural / ML / measurement) |
| **Execute** | Run code under active P0 gates | `/cr-work` P0 gates (seed, evidence, measurement, normative) |
| **Verify** | Audit results against theory and diagnostics | `/cr-review` agents + `@cr-mathematical-verification` |
| **Communicate** | Narrate and present results | `cr-skill-academic-writing` / `cr-skill-publication-output` |
| **Maintain** | Preserve reproducibility and comparability over time | `cr-skill-replication-standards` + vintages |

### Task types mapped onto lifecycle stages

The ten task types are not stages — each enters the lifecycle at its primary
stage and flows forward. Scope, Evidence, and Verify apply to **every** task.

| Task type | Primary stage(s) |
|-----------|------------------|
| Research Scoping | Scope |
| Theory/Modeling | Theory |
| Specification Analysis | Theory → Method |
| Measurement/Classification | Method (Measurement pack) |
| ML/Prediction | Method (ML pack) |
| Implementation | Method → Execute |
| EDA | Evidence → Execute |
| Tables/Figures | Communicate |
| Writing | Communicate |
| Reproducibility | Maintain |

### Method Packs

A **method pack** is a `Theory + Method + Verify` bundle that plugs into the
shared lifecycle. Packs differ only in their theory/estimator/diagnostic
surfaces; they **share the same Scope, Evidence, Normative, Verify, and
Communicate stages** — the responsible backbone is never re-implemented per pack.

| Pack | Theory / Method skill | Verify agent(s) |
|------|-----------------------|-----------------|
| **Structural** | `cr-skill-structural-econometrics` | `@cr-econometric-reasoning`, `@cr-identification-audit` |
| **ML** | `cr-skill-ml-economics` | `@cr-ml-methodology` |
| **Measurement** | `cr-skill-measurement` | `@cr-measurement-integrity` |

This is **documentation cross-linking only**: packs name existing skills/agents
by reference — no files move, no routing changes, and `/cr-review` dispatch
(below) remains the single source of routing truth. Fuller pack framing (packs
participating in dispatch) is deferred to a later phase.

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
| **Fabricated/unverifiable citation** | Source/locator/quote cannot be resolved in evidence artifacts | Replace with verifiable source or remove claim |
| **Uncited substantive claim** | Empirical/methodological claim missing verified evidence row | Add verified evidence or withdraw claim |

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
When running estimation code, append to `.cg-docs/research/results/manifest.json`.
The file contains an array of objects — one entry per estimation run:
```json
[
  {"date": "YYYY-MM-DD", "description": "...", "file": "relative/path/to/script.R", "seed": 42},
  {"date": "YYYY-MM-DD", "description": "...", "file": "relative/path/to/script.R", "seed": null}
]
```
Use `"seed": 42` (a numeric value) when random code was executed.
Use `"seed": null` when estimation is deterministic (e.g., OLS with no sampling).
All four fields (`date`, `description`, `file`, `seed`) are **required**. If `file` is unknown,
halt and resolve the path before writing the entry.
**Idempotency**: check whether an entry with the same (`file`, `date`) already exists before
appending. If it does, update it rather than creating a duplicate — prevents manifest pollution
on re-runs.
Create the file and `.cg-docs/research/results/` directory if absent.
This enables specification-search detection during review.

<!-- The manifest schema above is mirrored in cr-work.prompt.md under
     "P0: Specification Logging". Keep both in sync when modifying. -->

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
├── evidence/
│   ├── provenance-ledger.yaml     # Source authority map + origin flags
│   ├── claim-evidence-matrix.yaml # Claim verification matrix
│   └── converted/                 # Converted source text for locator indexing
├── measurement/
│   ├── weighting-sensitivity.yaml # Sensitivity scenarios and rank stability summaries
│   └── cluster-validity.yaml      # Cluster validity and stability summaries
├── vintages/           # Vintage manifests with coverage/method change attribution
├── scoping/            # Front-end scoping memos per study slug
├── normative-decisions/# Per-study normative decision registers
├── derivations/        # LaTeX or Markdown derivations (.tex, .md)
├── specifications/     # Spec memos: what models were tested and why
├── results/
│   └── manifest.json  # Auto-appended by /cr-work on every estimation run
├── manuscript/         # Working paper drafts, sections
└── replication/        # Journal submission replication materials
```

Evidence corpus policy:
- Default corpus is repo-local.
- External sources are opt-in and must be explicitly flagged.
- Original source files remain authoritative; converted text is an index.

### Normative-Decision Entry Schema

Per-study register path:
- `.cg-docs/research/normative-decisions/<study-slug>.md`

Entry template:
```markdown
## ND-<study-slug>-001 — <short name>
- study: <study-slug>
- plan: <plan-file-slug or "none">
- applies_to: [<scoping-memo path>, <plan step/section>, <output path>]
- choice: <the value-laden decision>
- defensible_options: [<option A>, <option B>, ...]
- consequences: <who/what is affected; expected ranking or threshold shifts>
- decided_by: <human name/role>            # never "default"
- decision: <chosen option>
- justification: <why, in value terms>
- decided_on: YYYY-MM-DD
```

Created by `/cg-setup` when `modules:` includes `research`.

## Local Evidence Workbench Boundary

For repository-local evidence tasks, the dedicated `research_evidence/` Python
workbench is the executable implementation of the shared Evidence and Verify
surfaces. Use the existing `/cr-work [phaseX]` launcher to start or resume it;
do not add a parallel `/cr-evidence` command in v1.

The boundary remains local-only and offline: no internet search, URL fetching,
external API model execution, hidden downloads, or external fallback. Original
resources and canonical YAML remain authoritative. Converted/OCR text, indexes,
API responses, and browser views are derived. Legacy `external-opt-in` rows stay
read-only in `external-quarantine.yaml`; local retrieval/model output remains
candidate data until independent source-version, typed-locator, quote, and
original-authority checks succeed.

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
