---
date: 2026-07-30
title: "CR as a responsible research partner for policy-relevant measurement work"
status: decided
scope: "Deep"
chosen-approach: "Phased lifecycle, value-first (Approach 3) — converges on a responsible-lifecycle re-spine"
tags: [compound-research, responsible-ai, measurement, composite-indicators, clustering, provenance, evidence-synthesis, research-integrity, lifecycle, method-packs]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# CR as a Responsible Research Partner for Policy-Relevant Measurement Work

## Context

The Compound Research (CR) module today is, in effect, a **rigor-and-reproducibility
harness for structural-econometrics / causal-identification papers headed to a
journal**. Its spine is `derive → specify → estimate → identify → write →
replicate`, and its integrity model is estimator-centric: code-math mismatch,
identification theater, unseeded randomness, specification searching (see
`.github/skills/cr-skill-research-workflow/SKILL.md` and the two prior CR
brainstorms, `2026-05-13-compound-research-extension.md` and
`2026-07-29-cr-module-migration-to-v1.md`).

This brainstorm was prompted by a request to **improve CR so it provides real
value on the kind of research the World Bank actually does**, using a concrete
exemplar brief as a stress test:

> **Exemplar brief — "Beyond GDP" development classifications.** The Bank's ICP
> team divides countries into four income groups (low, lower-middle,
> upper-middle, high) based only on GNI per capita in USD. Income does not
> capture all of development. This project scopes an *alternative* classification
> of development groups for the "Beyond GDP" agenda. Two initial ideas: (1) take
> the ~30 Beyond-GDP indicators, run a clustering analysis, and build an index
> to capture the clusters; (2) find thresholds for classification based on
> multivariate development indicators (inequality, education, etc.) that map onto
> an income threshold of $X per capita. The classification should be redone at
> regular intervals to measure progress consistently and comparably. The project
> must scope the problem, survey literature, reason from economic and development
> theory, do modeling and empirical work, and propose approaches.

The exemplar is a **probe**, not the deliverable. It exposes that CR's current
orientation is a poor fit for a large, important class of Bank research:

- It is **open-ended scoping**, not a pre-specified estimator.
- Its core methods are **measurement and unsupervised learning** — composite
  index construction, clustering, threshold mapping — which CR barely covers
  (its ML skill is prediction/causal-focused; there is no measurement skill).
- It needs a **literature survey**, which v1 CR explicitly ruled out of scope.
- It produces a **recurring, comparable-over-time official classification** — a
  living data product — not a one-shot paper.
- It is **politically consequential** (reclassifying countries' development
  status), so the *responsible-AI* dimension is load-bearing, not decorative.

**Decision frame confirmed with the product owner:** the goal is not to "add a
clustering skill." It is to **relook at how the plugin functions as a research
partner** and broaden CR from a journal-paper econometrics assistant into a
**responsible partner for the full research lifecycle of policy-relevant
measurement work**, of which the classification problem is a canonical example.

A companion design note (`Suggestions-For-CR.md`, from a separate AI
report-writing pipeline) was contributed and critically reviewed; its provenance
spine is adopted and adapted (see Requirements).

## Requirements

### Responsible-AI model (the load-bearing design choice)

1. **Normative choices are P0.** For measurement/classification work the most
   consequential decisions are *normative, not technical*: which indicators are
   admissible, how they are weighted, how many groups, where thresholds sit,
   what "development" means. **Silently making a value-laden methodological
   choice is a new P0-class integrity violation**, on par with identification
   theater. CR must make such choices *visible, contestable, and documented* —
   never hide a value judgment behind a technical result ("the clustering said
   so").
2. **Human-in-the-loop is front-loaded at the design gates.** CR *may execute*
   technical analysis (run the clustering, fit the index, produce sensitivity
   tables), but the **human explicitly approves the specification set at the
   `/cr-brainstorm` and `/cr-plan` gates**; `/cr-work` then executes against that
   approved specification. Any *new* value-laden choice that surfaces mid-work
   **re-triggers the gate**. The plan becomes a *specification contract*.
3. **Every normative decision is recorded** in a first-class artifact
   (`normative-decisions.md`): the choice, the defensible options, their
   consequences (e.g., how country rankings shift under 2–3 defensible
   weightings), the human decision, and its justification.

### Evidence & provenance (anti-hallucination)

4. **Repo-local corpus by default.** The default evidence source is
   **documents inside the working repository only.** External / autonomous
   scholarly search is **opt-in and clearly flagged** — this is the responsible
   default because autonomous web search is the highest hallucination-and-leak
   surface, especially for confidential Bank work.
5. **Provenance-disciplined literature.** Adopt the design note's provenance
   spine, folded into CR's existing loop:
   - **Analysis/composition split** with an approval checkpoint between — which
     *is* the brainstorm/plan gate (structure and verify evidence before any
     prose).
   - A **claim → source → locator matrix** (`claim_id → source_id → page/locator
     → verification_status`) — the literature analogue of CR's derivation trail
     and specification manifest.
   - A **provenance ledger** (original file + hash, retrieval timestamp,
     converter + version, page map, version-of-record).
   - **Anti-hallucination rules as P0 catalog entries**: never invent a
     paper/DOI/quotation/page number; never cite a source not verified against
     the original; **an uncited or unverifiable substantive claim is a blocker**;
     prefer abstention + review flag over plausible completion.
6. **Improvements over the source note (agreed):**
   - **Evidence justifies method choices, not just prose** — a verified evidence
     base grounds scoping and methodological decisions, and ties into the
     normative-choice gates (a value-laden choice should cite evidence or be
     flagged as a pure value judgment).
   - **Compound the evidence across projects** — verified-source records and the
     claim-evidence matrix are reusable institutional knowledge (candidate
     team-brain asset; see Next Steps — split off as its own idea).
   - **Do not clone the note's ~8-agent pipeline** — map its *stages* onto a
     small set of additions and reuse existing agents.
   - **Tool-agnostic ingestion; original is the authority** — `markitdown` is a
     sensible default, but PDF→MD is lossy where economics evidence lives
     (tables, equations); any table/figure/equation citation must point at the
     original.
   - **Verification depth proportional to stakes** — tie citation-audit rigor to
     the existing light/standard/thorough review tiers.

### Measurement / classification archetype

7. **New first-class "Measurement/Classification" research archetype** (a 9th
   task type) with its **own P0/P1 integrity catalog**, rather than stretching
   estimator-centric checks. Failure modes it must catch:
   - **Undisclosed/arbitrary weighting** driving results (also a normative P0).
   - **Ranking instability** — a unit's group flips under equally-defensible
     methodological choices and the fragility is not disclosed.
   - **Coverage/vintage artifacts** — a unit "moves groups" because its
     underlying data changed, not because it developed.
   - **Spurious cluster structure** — clusters reported as real without
     stability/validity checks.
   - **Non-comparability across vintages** — re-running later is not
     backward-compatible, so "progress" is a method artifact.
8. **Comparability is P0** for measurement/indicator work — **both over time and
   across units (e.g., countries)**. A recurring classification is a *living
   data product*: vintage versioning, change attribution ("did the unit move or
   did the method move?"), and backward-compatible re-runs are first-class
   concerns.

### Build constraints

9. Must **not break** the existing structural-econometrics CR flow, prompts,
   agents, skills, or tests. Prefer **extending** the task taxonomy and loop over
   re-architecting it in one step. Reuse existing `cr-*` and `cg-*` agents;
   add new machinery only where a genuinely new responsibility exists.
10. Preserve the compound philosophy: new artifacts live in `.cg-docs/` and feed
    the knowledge/brain system so measurement and provenance lessons compound.

## Approaches Considered

### Approach 1 — Bolt-on modules
Ship the Measurement archetype, the Evidence/Provenance subsystem, and the
Scoping front-end as three independent additions, leaving CR's spine untouched.
- **Pros:** Lowest risk to the existing flow; separately testable; fastest first
  delivery.
- **Cons:** No unifying model — the responsible-AI gate logic is re-implemented
  three times and drifts; "full relook" degrades into "three attachments"; the
  normative-decision backbone is weak because it isn't central. Contradicts the
  explicit ask to relook at how the plugin *functions* as a partner.
- **Effort:** Medium. **Recommended?** No.

### Approach 2 — Responsible-lifecycle re-spine
Re-architect CR around an explicit gated lifecycle
(`Scope → Evidence → Theory → Method → Execute → Verify → Communicate →
Maintain`) with the responsible-AI gate model + provenance spine as the
backbone. Structural econometrics, ML, and Measurement become interchangeable
**method packs** that plug into that lifecycle.
- **Pros:** Most coherent; the responsible-AI model is *structural*, not
  duplicated; future methods (Bayesian, causal-ML) become cheap new packs; best
  embodiment of "responsible partner for the full lifecycle"; the existing
  structural flow survives as the first pack (backward-compatible).
- **Cons:** Largest single design effort; touches CR's conceptual spine → more
  up-front alignment and test rewriting; over-engineering risk if scope isn't
  policed.
- **Effort:** Large. **Recommended?** As the **north-star architecture**, yes —
  but not as a big-bang delivery.

### Approach 3 — Phased lifecycle, value-first **(CHOSEN)**
Adopt Approach 2's architecture as the target, but deliver it in standalone,
value-ordered, test-guarded phases (see Next Steps). Front-load the
highest-risk/highest-value work (provenance, then measurement), formalize the
unifying backbone once the pieces have proven their shape, and retrofit the
existing structural/ML flows into the method-pack model last.
- **Pros:** Coherent endpoint (converges on Approach 2) without big-bang risk;
  every phase delivers standalone value; validates the architecture in real use
  before formalizing the spine; a clean stop after Phase 2 still leaves CR
  dramatically more capable.
- **Cons:** Requires discipline to hold the north star across phases; some
  Phase-1 artifacts may be lightly reworked when the backbone lands.
- **Effort:** Large (incremental). **Recommended?** Yes.

## Decision

**Approach 3 — Phased lifecycle, value-first**, converging on the Approach-2
responsible-lifecycle architecture. Build order front-loads the scariest failure
mode (hallucinated citations) and the highest-value new capability (measurement),
then formalizes the responsible-AI backbone, then retrofits existing flows into
the method-pack model.

### Devil's-advocate notes carried forward
- **Demand inferred from one exemplar.** Confirm generality with a second real
  measurement use case before over-building the archetype (composite-indicator
  work is common at the Bank, so confidence is moderate-to-high, but named as an
  assumption).
- **Avoid reinvention.** The measurement skill must reference established
  methodology (OECD/JRC *Handbook on Constructing Composite Indicators*,
  Alkire-Foster multidimensional methods, cluster-validity literature), not
  reinvent it; the provenance layer must reuse the existing manifest /
  reproducibility patterns, not fork a parallel system.
- **80/20.** Phases 1–2 deliver ~80% of the value; Phases 3–4 are the coherence
  investment. Stopping after Phase 2 is a legitimate fallback.
- **Charter is affected.** This is a genuine scope expansion of
  `compound-gpid.md` (new deliverables; "research integrity" constraint grows to
  include "normative transparency" and "citation provenance"). A charter update
  is a named output requiring explicit approval — see Next Steps.

## Next Steps

Concrete handoff to `/cr-plan` (this brainstorm inherits **Deep** scope; the plan
may skip its own Step 1.5). Suggested phases, each ending with passing tests and a
working artifact:

### Phase 1 — Provenance / evidence spine + repo-local default
- Skill `cr-skill-evidence-provenance`: analysis/composition split, claim-evidence
  matrix schema, provenance ledger schema, ingestion pattern (tool-agnostic;
  original = authority), anti-hallucination rules.
- Agent `@cr-provenance-audit`: source verification + citation/locator audit;
  reuse `@cr-academic-writing` for composition.
- New P0 catalog entries (uncited/unverifiable claim; fabricated
  source/DOI/quote/page).
- Artifacts: `.cg-docs/research/evidence/` (provenance ledger, claim-evidence
  matrix, verified sources, converted markdown).
- Default = repo-local corpus; external search opt-in + flagged.

### Phase 2 — Measurement/Classification archetype + comparability P0s
- Skill `cr-skill-measurement`: composite indicators (OECD/JRC), clustering &
  cluster validity, thresholding/index construction, weighting sensitivity,
  Alkire-Foster; grounded in cited methodology.
- Agent `@cr-measurement-integrity`: weighting disclosure, ranking-stability,
  coverage/vintage-artifact, spurious-cluster, comparability checks.
- Register **Measurement/Classification** as the 9th task type in
  `cr-skill-research-workflow` + `/cr-brainstorm` classifier.
- Comparability P0 (over time + across units); vintage versioning +
  change-attribution artifacts (`.cg-docs/research/vintages/`).
- Wire `@cr-measurement-integrity` into `/cr-review` orchestration.

### Phase 3 — Scoping front-end + normative-gate backbone
- Skill `cr-skill-research-scoping`: problem framing, competing conceptual
  frames, theory priors, success criteria; produces a **scoping memo**
  (`.cg-docs/research/scoping/`).
- Normative-decision gate framework: `normative-decisions.md` artifact +
  P0 gate logic in `/cr-work`; spec-contract approval formalized at
  `/cr-brainstorm` and `/cr-plan`.
- Make normative-choice-smuggling an actively-detected P0.

### Phase 4 — Method-pack retrofit + orchestration cleanup
- Refactor structural-econometrics and ML flows into the method-pack model under
  the unified lifecycle (`Scope → Evidence → Theory → Method → Execute → Verify →
  Communicate → Maintain`).
- Converge `/cr-review` dispatch onto the pack model; finalize tests.

### Governance / handoff items
- **Charter update (requires explicit approval):** expand `compound-gpid.md`
  deliverables + research-integrity constraint family (normative transparency,
  citation provenance, measurement comparability).
- **Adjacent idea to log separately (not in scope here):** a **team-level
  evidence library** — verified-source records compounding across projects into a
  shared, searchable team-brain asset (its own storage/governance design).
- **Validation:** confirm archetype generality against a second real measurement
  use case before broad build-out.
