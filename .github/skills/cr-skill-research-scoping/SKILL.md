---
name: cr-skill-research-scoping
module: research
description: "Scoping and normative-choice surfacing for policy-relevant research.
  Load at the start of CR tasks (especially fuzzy or value-laden requests) to
  produce scoping memos, enumerate bounded decision points, and route
  consequential normative decisions to a human for explicit approval."
---

# Research Scoping and Normative Decision Surfacing

Use this skill before planning or implementation when the request is policy-facing,
measurement-heavy, or likely to involve value-laden choices.

---

## Creation Date

- 2026-07-30

---

## Problem Framing

Restate the research problem in decision terms before selecting methods.

Required framing fields:
- Policy or measurement question
- Intended decision context (what decision this evidence informs)
- Stakeholders affected by classification/ranking/threshold choices
- Target population and unit of analysis
- Time horizon and comparability constraints

If any field is unknown, mark it explicitly as unknown and ask for resolution.

---

## Competing Conceptual Frames

List at least two defensible frames for the same question.

For each frame:
- What it prioritizes
- What it makes visible
- What it makes less visible or invisible
- Which outcomes/rankings are most likely to shift

Do not collapse alternatives into one default frame at this stage.

---

## Theory Priors

Record priors and assumptions before seeing results.

Examples:
- Behavioral assumptions (e.g., intrahousehold pooling, labor supply response)
- Data assumptions (e.g., missingness pattern, comparability across waves)
- Identification assumptions (if causal claims are expected)

Each prior should have a short rationale and a plausibility risk.

---

## Success Criteria

Define what a credible answer looks like before model fitting.

Minimum criteria:
- Substantive criterion (the answer resolves the decision question)
- Statistical criterion (uncertainty and diagnostics are reported)
- Integrity criterion (all consequential normative choices are recorded)
- Reproducibility criterion (paths, seeds, and artifact references are explicit)

These criteria reduce ex-post specification searching and reframing.

---

## Bounded Normative Decision-Point Taxonomy

Use this fixed checklist by task type. The checklist is deterministic workflow
logic and must be walked explicitly.

### Theory/Modeling
- Welfare objective choice
- Social aggregation rule
- Normative boundary conditions (inclusion/exclusion assumptions)

### Specification Analysis
- Functional form with value implications (levels/logs/thresholds)
- Covariate inclusion that changes subgroup fairness/comparability
- Sample restriction with distributional consequence

### EDA
- Outlier handling rule
- Missingness treatment policy
- Grouping/binning choices that affect narrative emphasis

### Implementation
- Encoded threshold/cutoff defaults
- Loss/objective weighting choices
- Tie-breaking or fallback rules with distributional effects

### ML/Prediction
- Error trade-off objective (precision/recall balance)
- Threshold for action classification
- Fairness/coverage constraints across groups

### Writing
- Framing language for winners/losers and burden allocation
- Which uncertainty caveats are foregrounded vs deferred
- Comparison baseline chosen for narrative interpretation

### Tables/Figures
- Ranking metric choice
- Visual truncation/binning that can suppress tails
- Highlight/annotation selection affecting interpretation

### Reproducibility
- Disclosure boundaries for restricted data
- What is treated as non-shareable versus reproducible proxy
- Replication success criterion (strict vs practical equivalence)

---

## Scoping Memo Schema

Write a scoping memo to:
- `c-research/scoping/<study-slug>.md`

Required sections:
- Problem framing
- Competing conceptual frames
- Theory priors
- Success criteria
- Initial normative decision register links

Create the directory if absent.

---

## Per-Study Normative Register Linking

Record decisions in:
- `c-research/normative-decisions/<study-slug>.md`

Each decision must have:
- Stable ID (`ND-<study-slug>-NNN`)
- `study` and `plan` scope
- `applies_to` links back to memo/plan/step
- Explicit human decision and justification

Never use implicit or defaulted decisions for consequential value-laden choices.

---

## Coverage Rule

Before escalating a new decision, check whether an existing ID in the same
study register already covers the current step.

A decision is considered covered only if all are true:
- Same study slug
- Same choice category (e.g., threshold, weighting, framing)
- `applies_to` includes the active artifact/step (or an explicit broader scope)
- No contradiction with the currently proposed option

If not covered, escalate to the human and add a new decision ID.

---

## Anti-Patterns

- Treating value-laden choices as purely technical defaults
- Recording a decision without alternatives or consequences
- Reusing an old decision ID across studies without scope justification
- Omitting ranking/threshold shift consequences when they are plausible
