---
date: 2026-08-12
title: "CR Local Evidence Workbench for Verifiable Research Claims"
status: decided
scope: "Deep"
artifact-schema-version: 1
chosen-approach: "Phased implementation strategy for a full local evidence workbench (Approach 2 under Approach 1's long-term architecture)"
tags: [compound-research, evidence, provenance, claims, literature-review, local-first, document-ingestion, retrieval, verification, research-integrity, browser-ui]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# CR Local Evidence Workbench for Verifiable Research Claims

## Context

World Bank researchers need a rigorous way to use a repository of research
resources as the basis for later analysis and writing. The resources may be
highly relevant, marginally relevant, or contain only one useful passage. The
central research artifact should therefore not be generated prose. It should be
a reusable, auditable evidence base in which:

```text
original resource -> parsed source -> evidence passage -> atomic claim
-> analysis link -> later prose
```

The AI-DQSS repository provides a strong procedural exemplar for this problem.
Its useful pattern is not the full data-quality assessment application, but the
separation and verification of stages:

```text
document parsing -> stable citation IDs -> local indexing -> retrieval
-> independent reranking -> structured evidence -> quote verification
-> source-context report/view
```

This brainstorm starts fresh from the earlier CR extension discussion and uses
AI-DQSS as a design input. The goal is to determine how to bring its strongest
provenance and verification practices into the Compound Research suite without
copying an assessment-specific workflow.

## Users

The primary users are World Bank researchers with doctoral-level research
training. The workflow should assume that users can exercise methodological
judgment, while ensuring that coauthors, reviewers, and future researchers can
inspect the original source, locator, quote, claim, status, and review history.

## Requirements

### Core purpose

- The verified claim/evidence base is the primary product.
- Literature reviews, summaries, arguments, and other prose are downstream
  compositions over approved evidence and are out of scope for this first
  implementation.
- The system must make it possible to move from an original resource to a
  traceable, verifiable atomic claim without treating generated prose as the
  source of truth.

### Corpus and supported resources

- The corpus is repo-local by default and consists of resources in a dedicated
  research resources folder.
- Internet search and autonomous retrieval of external papers are out of scope
  for v1.
- v1 should support PDF, DOCX, Markdown, LaTeX, and HTML resources.
- Scanned or image-based PDFs are supported through an explicit OCR path.
  OCR text may support indexing and retrieval, but the original page/image
  remains authoritative for quote and locator verification.
- Original files are immutable authorities for evidence. Converted text,
  extracted text, OCR output, embeddings, and browser views are derived assets.

### Evidence and claim model

- Every parsed source unit receives a stable, deterministic source locator.
- Evidence records contain the source identity, original path, locator, verbatim
  quotation, extraction method, and verification result.
- Claims are atomic factual or methodological statements, not paragraphs of
  prose. Each claim links to one or more evidence records and records whether
  the evidence supports the claim.
- The model must distinguish direct textual evidence from inference, synthesis,
  normative judgment, and methodological interpretation.
- Claims and evidence have explicit confidence flags. High confidence requires
  successful quote and locator verification against the original source.
- Medium- and low-confidence records may be retained for researcher review but
  cannot silently enter the approved evidence base.
- Conflicting findings, ambiguous locators, inaccessible sources, OCR
  uncertainty, unsupported inference, and evidence involving tables, figures,
  or equations must remain visible and be flagged rather than silently
  reconciled.

### Local workbench and persistence

- The system provides a completely local browser UI for viewing and managing
  resources, source passages, evidence records, claims, review queues, and
  analysis links.
- User selections, approvals, edits, exclusions, and review decisions must be
  conveniently recorded as durable artifacts and reused by later processing.
- YAML is the preferred canonical format because it is structured, readable,
  diffable, and suitable for version control. Markdown and JSON may be derived
  views or interoperability formats where useful.
- The evidence base must be incrementally maintainable throughout the full
  lifecycle of a research paper.
- Adding or changing a resource must be detectable through file identity and
  hashes; new content should be parsed and indexed incrementally where possible.
- Source changes must mark affected evidence and claims stale and require
  re-verification before they return to the approved evidence base.
- Stable source identifiers should be preserved when the underlying passage is
  unchanged; changed or removed passages must be represented explicitly.
- Review and selection history must be retained rather than overwritten.

### Processing, security, and cost

- Processing should be efficient enough for repeated updates as the corpus grows.
- Local processing is the default, especially for parsing, OCR, indexing, and
  reranking where practical.
- If any external API-backed model is presented as an option during the planning phase of building this workflow, it should be flagged explicitly. This is because of certain concerns: who is the provider, model, what data
   would leave the repository, estimated cost, and security implications
  before approval, etc. Should prefer local models, but any open source options used in AI-DQSS can be surfaced as options in the planning phase of this task.
- Local-only mode must fail loudly if a required local capability is unavailable;
  it must not silently fall back to an external model.
- Approved external-model use must be recorded in the run/provenance manifest.
- Python dependencies and a local service are acceptable.

### Verification and research integrity

- The original resource is the verification authority, not a converted Markdown
  representation.
- Deterministic quote matching and locator resolution are required. Exact
  normalized matching should be preferred; fuzzy matching may help identify
  candidates but cannot silently promote uncertain text to high confidence.
- Fabricated source IDs, page numbers, locators, quotations, DOIs, or claims are
  prohibited.
- A claim without high-confidence, resolvable evidence is flagged for researcher
  review or abstained from the approved evidence base.
- The analysis/composition boundary remains explicit: analysis produces and
  verifies structured claims and evidence; downstream composition may use only
  approved records unless it visibly marks unresolved material.

## Approaches Considered

### Approach 1: Full local evidence workbench

Build the complete local web application modeled on the AI-DQSS evidence
procedure: parsing/OCR, stable source segments, local hybrid retrieval,
independent reranking, evidence extraction, atomic claims, quote and locator
verification, review queues, source-context viewing, persistent selections, and
incremental corpus management.

**Pros:**

- Directly realizes the desired end-state user experience.
- Makes resource, claim, evidence, and review management first-class.
- Can support dynamic research corpora and richer source views from the outset.

**Cons:**

- Large initial implementation with several coupled uncertainties: document
  extraction, OCR, indexing, UI state, persistence, and invalidation.
- Higher risk of building features before the evidence schemas and review rules
  have been tested on representative research documents.
- A broad first release could obscure which parts of the workflow researchers
  actually need most.

**Effort:** Large.

**Recommended?** Yes as the long-term product architecture, but not as a
single undifferentiated first delivery.

### Approach 2: Phased CR-native evidence workbench

Use the existing CR evidence/provenance spine as the canonical model and
implement the full local workbench through staged, testable vertical slices.
The first phase must already contain the complete evidence-control loop:

```text
resource manifest -> parse/OCR -> stable IDs -> local index/search
-> independent reranking -> candidate evidence -> atomic claims
-> deterministic verification -> confidence/review queue
-> researcher approval -> durable YAML records
```

The local browser service manages resources, claims, evidence, selections, and
review decisions. Derived indexes and views are rebuilt or updated from the
canonical YAML and source records. Later phases can add richer PDF highlighting,
advanced table/equation handling, incremental re-indexing optimizations, and
additional workbench views without changing the provenance contract.

Dynamic corpus management is a first-phase requirement, not a later enhancement:

1. Detect new, changed, moved, and removed files using path metadata and hashes.
2. Parse and index only new or changed resources where possible.
3. Preserve stable identifiers for unchanged source units.
4. Mark affected evidence and claims stale when source content changes.
5. Require re-verification before stale claims become approved again.
6. Retain selection, approval, edit, exclusion, and re-verification history.
7. Record the processing profile and any approved model/API choice for each run.

**Pros:**

- Retains Approach 1's full rigor and end-state architecture while controlling
  delivery risk.
- Delivers the core claim/evidence value before optional UI and extraction
  features expand.
- Fits the existing CR module, evidence/provenance artifacts, P0 integrity
  rules, and review gates.
- Makes the critical dynamic-resource lifecycle explicit and testable.
- Supports comparison against AI-DQSS on a small representative corpus without
  cloning its assessment-specific report workflow.

**Cons:**

- The first workbench release will have a deliberately focused UI and may defer
  some rich source-view features.
- Later phases require disciplined schema and compatibility management.
- Incremental invalidation and source-version history add real complexity even
  in the first phase.

**Effort:** Medium to large, delivered in phases.

**Recommended?** Yes. This is the chosen implementation strategy for Approach
1's long-term architecture.

### Approach 3: Artifact-first workflow with a lightweight viewer

Extend CR prompts and Python utilities to create YAML evidence artifacts, then
provide a mostly read-oriented local HTML evidence map with limited editing.

**Pros:**

- Fastest way to validate schemas, verification rules, and a small research
  corpus.
- Lowest dependency and implementation burden.

**Cons:**

- Weak resource and claim management experience.
- Selections and updates would be cumbersome over a paper's lifecycle.
- Does not fully satisfy the requirement for a dynamic local workbench.

**Effort:** Small to medium.

**Recommended?** No as the target architecture. It may be useful as a narrow
schema-validation prototype inside Approach 2.

## Decision

Choose **Approach 2: the phased implementation strategy for Approach 1's
long-term architecture**.

This is not a decision to build a weaker, mostly static version of the AI-DQSS
procedure. The first phase must include the critical evidence controls:

- deterministic source and passage identifiers;
- parsers and an explicit OCR path for the supported resource types;
- local indexing, hybrid retrieval, and independent reranking;
- structured candidate evidence and atomic claims;
- deterministic quote and locator verification against original resources;
- confidence flags and a researcher review queue;
- a local browser UI for managing resources, claims, evidence, and selections;
- durable YAML artifacts and review history;
- incremental updates and stale-claim invalidation; and
- explicit local-only versus approved external-model processing profiles.

The phased boundary applies to optional breadth and refinement, not to
traceability. The long-term workbench can grow richer without changing the
canonical provenance model or allowing generated prose to become authoritative.

## Devil's Advocate

### Problem validation

AI-DQSS demonstrates that the parsing, retrieval, structured citation, and
verification procedure is technically viable. It does not yet establish which
review interactions World Bank researchers will use most. The first vertical
slice should be tested against a small representative corpus containing clean
PDFs, an OCR PDF, a DOCX, Markdown or LaTeX, HTML, and at least one source with
a table, equation, or figure.

### Simplicity check

The existing CR provenance artifacts can generate useful claim/evidence records
without a full application. However, a static evidence map would not satisfy
the requirement to manage selections conveniently and update them throughout a
research lifecycle. A localhost service backed by canonical YAML and a derived
index is the simplest adequate workbench boundary.

### Effort-value check

A single release covering every possible extraction and display problem would
be disproportionate. The value-first sequence is: stable identities and
provenance, candidate evidence, deterministic verification, review persistence,
and incremental updates; richer source highlighting and advanced document
semantics can follow.

### Charter alignment

The decision aligns with the active CR suite, the project's statistical and
research-integrity constraints, and the completed provenance spine. It also
preserves the repo-local corpus default and makes external data handling an
explicit, visible choice. No internet literature-search backend is included.

## Next Steps

The plan should begin with a thin end-to-end vertical slice rather than a broad
platform build:

1. Define and test the canonical YAML schemas for resource provenance, source
   segments, evidence records, atomic claims, analysis links, review decisions,
   run manifests, and stale/invalidation states.
2. Define the resource-folder contract and deterministic source-ID strategy for
   PDF, DOCX, Markdown, LaTeX, HTML, and OCR-derived content.
3. Build an ingestion/indexing service with local-only and explicit external
   model profiles, including incremental file detection and hash tracking.
4. Implement retrieval, independent reranking, deterministic quote matching,
   locator resolution, confidence scoring, and review-flag generation.
5. Build the first local browser review flow for resource inspection, evidence
   approval, claim editing, and persistent selections.
6. Add fixtures and tests covering ordinary text, OCR uncertainty, tables,
   equations, figures, source changes, duplicate/revised documents, conflicts,
   inaccessible files, fabricated citations, and unsupported inference.
7. Use a small representative research corpus to compare the workflow against
   the AI-DQSS procedure and tune retrieval/review thresholds without copying
   AI-DQSS's domain-specific assessment architecture.
8. Defer literature-review prose generation, internet search, citation-manager
   integration, multi-user collaboration, and automatic conflict resolution.
