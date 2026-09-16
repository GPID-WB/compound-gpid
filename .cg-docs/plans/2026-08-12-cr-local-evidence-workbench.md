---
date: 2026-08-12
title: "CR Local Evidence Workbench for Verifiable Research Claims"
status: active
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-08-12-cr-local-evidence-workbench.md"
predecessor-plan: ".cg-docs/plans/2026-07-30-cr-evidence-provenance-spine.md"
language: "Python/Markdown"
estimated-effort: large
deviation-policy: ask
artifact-schema-version: 1
phases: 5
tags: [compound-research, evidence, provenance, claims, document-ingestion, retrieval, verification, local-first, browser-ui, research-integrity]
---
<!-- Created 2026-08-12. Follow-up plan: the predecessor plan remains completed historical work. -->

# Plan: CR Local Evidence Workbench for Verifiable Research Claims

## Objective

Build the first implementation of a local-first research evidence workbench for
World Bank researchers. The workbench will turn resources in a repository-local
research folder into versioned, searchable, reviewable, and verifiably cited
claim/evidence records that can support later research analysis and prose.

The long-term architecture is a full local evidence workbench. This plan uses a
phased delivery strategy, but Phase 1 must establish the complete evidence
control loop rather than a static demo:

```text
resource -> parsed source units -> local retrieval -> candidate evidence
-> atomic claim -> deterministic verification -> confidence/review decision
-> approved YAML record -> analysis link -> downstream composition
```

Original resource files remain authoritative. YAML records are canonical and
version-controlled. Converted text, OCR text, embeddings, indexes, browser
views, and API responses are derived or explicitly recorded artifacts.

## Context

The completed predecessor plan,
[2026-07-30-cr-evidence-provenance-spine.md](.cg-docs/plans/2026-07-30-cr-evidence-provenance-spine.md),
delivered the CR evidence/provenance methodology, repo-local corpus default,
claim-evidence and provenance-ledger schemas, anti-hallucination P0 rules, and
workflow/audit surfaces. This plan follows up on that work; it does not replace
or repeat it.

The new requirement is an interactive, maintainable local workbench inspired by
the strongest AI-DQSS procedures without copying its assessment-specific
architecture. The workbench must support a dynamic research corpus over the
lifecycle of a paper, including new, changed, moved, removed, duplicate, and
revised resources. Researchers must be able to inspect source context and
record selections, claims, evidence decisions, analysis links, and review
history through a local browser interface.

AI-DQSS is used as a procedural reference for:

- stable source-segment citation IDs;
- parse/index/retrieve/rerank separation;
- structured evidence output rather than prose-only output;
- deterministic quote verification;
- source-context inspection; and
- independent local relevance signals.

The v1 processing policy is local-only. Internet search, external paper
retrieval, and external API model integration are not implemented. AI-DQSS's
local open-source retrieval/reranking models may be evaluated as optional local
profiles, subject to dependency, resource, deterministic-validation, and
performance checks. If a future plan proposes an external API profile, it must
return to brainstorm/planning with the provider, model, data exposure, cost,
and security implications explicitly surfaced for approval.

The dependency policy is pragmatic: add dependencies when they materially
improve the workbench, and prefer options that are widely available, maintained,
well documented, and straightforward to install across supported environments.
A useful dependency or model with license, access, platform, or enterprise
restrictions is not automatically excluded. It may remain an evaluated or
implemented option when its value justifies the restriction, but the restriction
must be recorded and surfaced through a clear caveat/disclaimer in setup
documentation, the workbench UI, and the relevant run manifest. The plugin must
not imply that an included dependency is enterprise-approved; approval remains
an organizational decision.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | The verified claim/evidence base is the primary product; literature-review prose generation is not part of v1. | Brainstorm |
| R2 | The corpus is repository-local and is read from a configured resources folder; no internet search or autonomous external-paper discovery exists in v1. | Brainstorm; predecessor plan |
| R3 | v1 supports PDF, DOCX, Markdown, LaTeX, HTML, and scanned/image-based PDFs through an explicit OCR path. | Brainstorm |
| R4 | Original files remain the evidence authority; converted/OCR text is an indexing aid and must retain provenance to the original. | Brainstorm; predecessor plan |
| R5 | Every source unit has a deterministic, explainable locator that can be resolved to source context. | Brainstorm; AI-DQSS procedure |
| R6 | Evidence records contain source identity, source version, locator, verbatim quotation, extraction method, verification status, confidence, and review state. | Brainstorm; predecessor plan |
| R7 | Claims are atomic factual, methodological, interpretive, or normative statements and link to one or more evidence records with an explicit supports/contradicts relationship. | Brainstorm; predecessor plan |
| R8 | High confidence requires successful quote and locator verification against the original; fuzzy, OCR-uncertain, inferred, conflicting, inaccessible, table/figure/equation, and stale cases remain flagged for researcher review. | Brainstorm |
| R9 | The local browser workbench manages resources, source context, candidate evidence, claims, analysis links, review queues, selections, approvals, exclusions, edits, and history. | Brainstorm |
| R10 | Researcher actions are durably persisted in readable, diffable YAML; derived JSON/index/view artifacts can be regenerated without becoming authoritative. | Brainstorm; artifact-view conventions |
| R11 | Resource additions and changes are detected using normalized paths, file identity, and SHA-256 hashes; unchanged source units are reused where safe. | Brainstorm |
| R12 | Source changes invalidate affected evidence and claims, require re-verification before re-approval, and preserve prior review history. | Brainstorm |
| R13 | Local-only processing fails loudly when a required local capability is unavailable and never silently falls back to an external service. | Brainstorm; charter |
| R14 | Any future external-model path remains an explicit planning choice; v1 records local processing profile, model, versions, and run metadata. | Brainstorm; model/retrieval governance |
| R15 | The workbench is project-contained, path-safe, and does not write outside the repository or expose resources beyond localhost by default. | Charter; browser/evidence conventions |
| R16 | Existing CR provenance artifacts and workflows remain compatible, and research-module gating remains intact for engineering-only projects. | Predecessor plan; charter |
| R17 | The implementation is efficient for repeated corpus updates and produces benchmark evidence rather than relying on unmeasured performance claims. | Brainstorm; project performance conventions |
| R18 | All source-derived content is treated as untrusted data by AI-facing components; document text, OCR output, YAML records, and user-authored claims cannot inject workflow instructions. | Security conventions; predecessor plan |
| R19 | Dependency and model selection prioritizes widely available, maintained options, while allowing useful restricted options when their caveats and limitations are explicit. | Owner decision, 2026-08-12 |
| R20 | Every included third-party package, parser, OCR engine, model, or model-weight distribution is inventoried with source, exact version/revision, hash where available, license/access restrictions, download/network requirements, telemetry notes, platform support, and enterprise-review status. | Owner decision, 2026-08-12 |

## Architecture Decisions

### Canonical versus derived state

Canonical state lives under `.cg-docs/research/evidence/` and is versioned with
the project:

```text
.cg-docs/research/evidence/
├── provenance-ledger.yaml
├── source-records.yaml
├── evidence-records.yaml
├── claim-evidence-matrix.yaml
├── analysis-links.yaml
├── review-history.yaml
├── runs/
└── converted/
```

The exact schema may split records into files for manageable diffs, but each
record must have a stable ID, schema version, source-version reference, status,
and timestamps. A local SQLite/FTS or embedding index, browser cache, and
rendered source view are derived artifacts. Rebuilding derived state from the
canonical records and current resources must be supported.

### Processing profiles

The first implementation exposes a local profile with explicit capability
metadata:

- parser/OCR profile and versions;
- lexical retrieval profile;
- optional local dense/sparse embedding profile;
- optional local reranker profile;
- claim-proposal mode (manual, local model, or disabled);
- deterministic seed where a model or algorithm uses randomness;
- network policy, which is `disabled` for v1; and
- run ID, timestamp, dependency lock, and resource hashes.

The workbench must distinguish a missing local model from an empty retrieval
result. It must not silently choose an API provider.

### Dependency and model selection policy

Dependencies and model weights are allowed when they are needed to make the
workbench useful. Selection follows this order:

1. Prefer broadly available, actively maintained, well-documented packages and
  model distributions with ordinary installation paths and broad platform
  support.
2. Evaluate a restricted option when it provides material quality or usability
  benefits that a broadly available option does not provide.
3. For every restricted option that is retained, record the restriction,
  rationale, exact source/version or revision, hash where available, license
  or access terms, setup-time network requirement, runtime network behavior,
  telemetry considerations, supported platforms, and known enterprise-policy
  caveat.
4. Surface the caveat/disclaimer in the setup instructions, dependency/model
  inventory, run manifest, and relevant browser status view. Do not describe
  the option as approved merely because it runs locally.

Model-weight acquisition is a separate, user-directed setup operation. Normal
processing runs from the installed local cache with network access disabled.
Missing weights or packages produce an explicit capability error; they do not
trigger a hidden download or external fallback.

### Confidence and review state

Confidence is evidence quality, not model self-confidence. At minimum, the
state machine distinguishes:

```text
candidate -> verified-high -> researcher-approved
candidate -> flagged-medium/flagged-low -> researcher-review
candidate -> abstained/rejected
approved -> stale -> reverify -> approved or rejected
```

A researcher may approve a flagged record for a local working set, but the
record must retain its confidence, flag reason, approver, decision, and history.
The approved evidence base used for downstream composition contains only records
that satisfy the configured approval rule; no UI action may erase the original
verification result.

## Implementation Steps

## Phase 1: Contracts and package foundation

### 1. Define the workbench package boundary and local runtime contract

- **Requirements**: R1, R2, R10, R13, R14, R15, R16, R18, R19, R20
- **Files**: `research_evidence/` (new package), `pyproject.toml` or a dedicated local `pyproject.toml`, `uv.lock` (if the package is isolated), `.gitignore`, `.cg-docs/research/evidence/README.md`, tests for package/runtime contracts.
- **Details**:
  - Choose a project-contained package boundary that does not entangle the
    plugin's existing prompt-generation utilities with application runtime code.
  - Define a CLI/service entry point for starting the local workbench on
    localhost, with an explicit project root and resources-folder argument.
  - Define a no-network runtime policy and a capability probe that reports
    unavailable parsers/models rather than silently substituting external APIs.
  - Create an initial dependency/model inventory covering parser, OCR, retrieval,
    reranking, UI, and claim-proposal candidates. Prefer broadly available
    options, but retain useful restricted candidates as conditional options when
    their caveats and disclaimers are explicit.
  - Use typed Python models and custom errors; follow the repository's FastAPI,
    Pydantic, loguru, pytest, and `uv` conventions where applicable.
  - Keep raw resources and model caches out of generated/committed artifacts by
    default; document safe project layout and ignore rules.
- **Test Scenarios**: package imports; CLI help; invalid project root; missing resources folder; local-only profile refuses network-capable configuration; logs contain no source contents by default.
- **Tests**: package contract tests; CLI tests; path-safety tests.
- **Acceptance criteria**: A locked, project-contained package can start in dry-run mode, identifies its resource and artifact roots, publishes a dependency/model inventory with any restrictions and caveats, and fails clearly when required local capabilities are unavailable.

### 2. Specify versioned YAML schemas and lifecycle transitions

- **Requirements**: R6, R7, R8, R9, R10, R12, R14, R18
- **Files**: `research_evidence/schemas.py`, `research_evidence/schema_versions.py`, `.cg-docs/research/evidence/*.yaml` fixture files, schema documentation, tests.
- **Details**:
  - Define Pydantic models or equivalent strict validators for provenance
    sources, source versions, parsed units, evidence records, claims,
    analysis links, review decisions, processing profiles, run manifests, and
    invalidation events.
  - Include schema version, stable IDs, created/updated timestamps, source hash,
    source locator, confidence, status, review reason, and provenance pointers.
  - Represent direct evidence, inference, synthesis, normative judgment, and
    methodological interpretation distinctly.
  - Represent supports, contradicts, and unresolved relationships explicitly.
  - Define compatibility rules for the predecessor ledger and claim matrix;
    migrate by additive fields and preserve unknown historical fields where
    safe, never by destructive rewrite.
  - Define the approved-evidence predicate and stale/reverification transitions
    as deterministic code, not UI inference.
- **Test Scenarios**: valid records; missing IDs; invalid status transition; stale source version; fabricated locator shape; duplicate record IDs; predecessor schema fixture; YAML round trip preserves meaningful fields.
- **Tests**: schema/unit tests; migration tests; fixture validation tests.
- **Acceptance criteria**: Canonical YAML can be validated, migrated, diffed, and regenerated without losing provenance or review history.

### 3. Add migration, run-manifest, and derived-artifact contracts

- **Requirements**: R4, R10, R11, R12, R13, R14, R15, R16, R20
- **Files**: `research_evidence/migrations.py`, `research_evidence/manifest.py`, `.cg-docs/research/evidence/README.md`, tests.
- **Details**:
  - Read existing `.cg-docs/research/evidence/provenance-ledger.yaml` and
    `claim-evidence-matrix.yaml` without changing their meaning.
  - Produce an explicit migration report showing imported, upgraded, skipped,
    and unresolved records.
  - Define a run manifest that records tool versions, profile, network policy,
    resource hashes, changed resources, derived-index version, and counts of
    candidates/verified/flagged/stale records.
  - Extend the run manifest with the exact dependency/model inventory used for
    the run, including version or revision, hashes where available, and any
    restriction caveat/disclaimer presented to the user.
  - Define which files are canonical, generated, cacheable, or excluded from
    git, and make stale derived artifacts detectable.
- **Test Scenarios**: empty evidence directory; predecessor artifacts present; malformed YAML; changed schema version; interrupted run; index cache from an old schema.
- **Tests**: migration and manifest tests; path/atomic-write tests.
- **Acceptance criteria**: A new workbench run can consume predecessor artifacts and emit a complete, auditable run manifest without modifying historical records in place.

## Phase 2: Resource ingestion and source lifecycle

### 4. Implement deterministic resource discovery and version detection

- **Requirements**: R2, R3, R4, R5, R11, R12, R15, R18
- **Files**: `research_evidence/resources.py`, `research_evidence/hashing.py`, `research_evidence/source_ids.py`, tests, minimal fixtures.
- **Details**:
  - Discover only configured, repository-local resource roots and supported
    extensions; reject symlinks/path escapes according to the project security
    policy or record them as unsupported.
  - Normalize project-relative paths and compute SHA-256 content hashes.
  - Detect new, unchanged, changed, moved, removed, duplicate-content, and
    revised resources between runs.
  - Define source identity separately from source version so unchanged logical
    resources can retain identity while revisions create new versions.
  - Make file timestamps advisory only; hashes determine content identity.
- **Test Scenarios**: new file; unchanged file; content change with same path; move with same hash; duplicate files; deletion; unsupported extension; symlink escape; inaccessible file; same bytes with changed metadata.
- **Tests**: resource discovery/hash/version tests; path-safety tests.
- **Acceptance criteria**: Repeated scans produce deterministic resource events and never read outside the configured project-contained corpus.

### 5. Implement format-specific parsing and locator maps

- **Requirements**: R3, R4, R5, R6, R8, R18
- **Files**: `research_evidence/parsers/` (PDF, DOCX, Markdown, LaTeX, HTML, OCR adapters), `research_evidence/source_records.py`, parser fixtures, tests.
- **Details**:
  - Parse supported formats into stable source units with document identity,
    source version, locator, heading/context path, extracted text, and parser
    metadata.
  - Preserve page, paragraph, block, table-row, heading, line, and HTML-anchor
    context where available. Do not pretend a lossy conversion has exact page
    semantics when it does not.
  - Keep parser adapters independent so a parser can be replaced without
    changing canonical source IDs for unchanged units where the locator contract
    permits it.
  - Treat LaTeX commands, equations, tables, figures, footnotes, and captions
    as typed source units or review-required units rather than flattening them
    into ordinary prose without a marker.
  - Store converted artifacts with parser/tool versions and a source hash.
- **Test Scenarios**: ordinary text for every format; multi-page PDF; DOCX headings/tables; Markdown and LaTeX headings/equations; HTML headings/links; malformed file; password-protected file; missing text layer; unsupported extraction; table/figure/equation locator.
- **Tests**: parser fixture tests; locator determinism tests; malformed-input tests.
- **Acceptance criteria**: Each supported format yields inspectable source records with deterministic locators, explicit extraction metadata, and an honest uncertainty/unsupported state where needed.

### 6. Add OCR as an explicit, review-aware parser path

- **Requirements**: R3, R4, R5, R6, R8, R13, R17, R18, R19, R20
- **Files**: `research_evidence/parsers/ocr.py`, OCR profile/configuration, OCR fixtures, tests, documentation.
- **Details**:
  - Detect image-based PDFs and expose OCR as an explicit local capability rather
    than silently applying it.
  - Record OCR engine/version, page/image locator, confidence metadata when
    available, language/configuration, and generated-text hash.
  - Record the OCR engine's package/source, exact version, license or access
    restriction, setup requirements, and any enterprise-policy caveat in the
    dependency/model inventory. A restricted OCR engine may remain an explicit
    option when its quality benefit justifies the documented caveat.
  - Use OCR text for retrieval candidates, but cap confidence and require
    original-page verification for high-confidence evidence.
  - Preserve page images or stable page references for researcher inspection;
    do not overwrite the original PDF.
  - Fail loudly when OCR is requested but unavailable, and provide a clear
    install/configuration message.
- **Test Scenarios**: text PDF skips OCR; scanned PDF detects OCR need; OCR unavailable; low OCR confidence; quote altered by OCR; page image locator; mixed text/image PDF.
- **Tests**: OCR capability and metadata tests; fixture tests; no-silent-fallback tests.
- **Acceptance criteria**: OCR-derived passages are searchable and reviewable but cannot be promoted to high confidence without original-page verification.

### 7. Implement incremental source lifecycle and invalidation propagation

- **Requirements**: R6, R8, R11, R12, R17
- **Files**: `research_evidence/lifecycle.py`, `research_evidence/invalidation.py`, lifecycle fixtures, tests.
- **Details**:
  - Apply discovery events to source versions and parsed-unit records.
  - Reuse unchanged parsed units and derived index entries where source hash,
    parser profile, and locator contract remain compatible.
  - Mark evidence and claims affected by changed/removed source units as stale;
    preserve the previous verification decision and reason.
  - Treat moved resources with unchanged content as identity-preserving when the
    authority path policy allows it; record path history.
  - Treat duplicate/revised editions as distinct source versions unless a
    researcher explicitly links them; never merge silently.
  - Make re-verification an explicit transition and emit a run-manifest event.
- **Test Scenarios**: unchanged update; one-page change; changed quote; removed source; moved source; duplicate edition; parser-version change; interrupted invalidation; reverify restores approval only after checks pass.
- **Tests**: lifecycle state-machine tests; invalidation propagation tests; idempotence tests.
- **Acceptance criteria**: Resource updates are incremental where safe, and no stale evidence remains eligible for approved downstream use without re-verification.

## Phase 3: Local indexing, retrieval, and candidate evidence

### 8. Build a persistent local lexical index with deterministic retrieval

- **Requirements**: R2, R5, R9, R10, R11, R17, R18
- **Files**: `research_evidence/index/`, `research_evidence/retrieval/lexical.py`, derived-index storage, tests, benchmark fixtures.
- **Details**:
  - Start with a project-contained SQLite FTS or equivalent local lexical index
    keyed by source-unit IDs and source versions.
  - Index text, headings, document metadata, and typed unit markers without
    putting raw corpus text in logs or network requests.
  - Support query results with stable IDs, scores, document context, and index
    version.
  - Make ranking deterministic for equal scores and preserve document/source
    ordering for readable review.
  - Update only affected source units after lifecycle events and provide a
    rebuild command for corruption or schema changes.
- **Test Scenarios**: keyword match; heading match; no results; equal-score ordering; changed unit replacement; deleted unit removal; corrupt index rebuild; path outside project rejected.
- **Tests**: index/retrieval tests; SQLite schema tests; deterministic repeat-run tests.
- **Acceptance criteria**: A local lexical profile provides fast, reproducible candidate retrieval with no network requirement.

### 9. Add optional local semantic retrieval and independent reranking profiles

- **Requirements**: R2, R5, R8, R13, R14, R17, R18, R19, R20
- **Files**: `research_evidence/retrieval/dense.py`, `research_evidence/retrieval/sparse.py`, `research_evidence/retrieval/rerank.py`, model profile configuration, tests, benchmarks.
- **Details**:
  - Evaluate AI-DQSS-inspired local open-source options such as dense
    embeddings, SPLADE-style sparse retrieval, and a local cross-encoder
    reranker. Prefer widely available options, but do not automatically discard
    a restricted option that materially improves retrieval or ranking. A
    retained restricted option must have a visible caveat/disclaimer and a
    complete inventory entry before it is presented for use.
  - Do not hard-code a model or dependency until its source, exact version or
    revision, hash where available, license/access terms, package/model size,
    hardware support, determinism, setup-time network requirement, runtime
    network behavior, and benchmark results are documented.
  - Keep lexical retrieval as a functioning local fallback profile, but do not
    silently change profiles when an optional model is unavailable.
  - Define hybrid fusion, candidate pool, reranking, minimum-text filters, and
    tie-breaking as versioned configuration.
  - Record model name/version, device, package versions, seed/determinism notes,
    corpus size, benchmark results, and any dependency/model caveat shown to the
    researcher in the run manifest.
  - Keep model download/network behavior outside normal runs; model acquisition
    must be a separate, user-directed setup action.
- **Test Scenarios**: local model available; model unavailable; cache missing; CPU/MPS differences; deterministic repeated run; hybrid/lexical comparison; short/noisy segment; model profile mismatch.
- **Tests**: retrieval contract tests; mocked model tests; optional local-model integration tests; benchmark harness.
- **Acceptance criteria**: Approved local profiles are explicitly selectable, reproducible enough for evidence review, benchmarked against lexical retrieval, disclose any dependency/model restrictions, and never fall back to an external service.

### 10. Generate candidate evidence and atomic claim proposals

- **Requirements**: R6, R7, R8, R9, R10, R14, R18, R20
- **Files**: `research_evidence/evidence.py`, `research_evidence/claims.py`, local claim-proposal adapter, fixtures, tests.
- **Details**:
  - Let researchers create claims manually from selected source units.
  - Optionally allow a local model to propose candidate evidence and atomic
    claims from retrieved passages, with all proposals marked `candidate` and
    linked to the run/profile that produced them.
  - Record the local claim-proposal package/model and its caveat/disclaimer when
    a third-party component is used; manual claim creation must remain available
    when no model is installed.
  - Require each candidate claim to identify claim type, statement, source unit,
    quote, relation (`supports`/`contradicts`/`contextualizes`), and rationale.
  - Enforce atomicity heuristics and flag claims containing multiple independent
    assertions for researcher splitting.
  - Never treat a model-generated claim or paraphrase as verified merely because
    the model returned a citation ID.
- **Test Scenarios**: manual claim; local proposal; no candidate evidence; multi-assertion claim; fabricated source ID; paraphrase without quote; supports/contradicts links; duplicate claim proposal.
- **Tests**: candidate-record tests; claim atomicity tests; fabricated-reference rejection tests.
- **Acceptance criteria**: The system can produce reviewable, source-linked candidate claims without allowing proposal output to bypass verification or approval.

## Phase 4: Verification and local browser workbench

### 11. Implement deterministic quotation and locator verification

- **Requirements**: R4, R5, R6, R7, R8, R12, R18
- **Files**: `research_evidence/verification/`, `research_evidence/confidence.py`, verification fixtures, tests.
- **Details**:
  - Resolve source IDs and locators against the current source version and
    original resource where possible.
  - Prefer exact normalized quote matching and exact source-unit matching.
  - Use fuzzy/chunk matching only as a candidate diagnostic; mark its result as
    uncertain and never promote it to high confidence automatically.
  - Handle quotes spanning source units/pages, tables, captions, equations, and
    OCR text through typed review-required outcomes.
  - Verify source hash/version, quote presence, locator validity, quote/source
    association, and evidence relation independently.
  - Produce machine-readable reasons for `verified-high`, `flagged-medium`,
    `flagged-low`, `stale`, `abstained`, and `rejected` states.
- **Test Scenarios**: exact quote; whitespace normalization; quote spanning pages; quote spanning blocks; source ID mismatch; fabricated locator; fuzzy-only match; OCR mismatch; table/equation/figure; stale source; inaccessible original; conflicting evidence.
- **Tests**: verifier unit/property tests; source-version tests; confidence transition tests.
- **Acceptance criteria**: Only evidence with a resolvable locator, matching source version, and successful original-authority verification can receive high confidence automatically.

### 12. Implement the local FastAPI service and safe artifact API

- **Requirements**: R2, R9, R10, R11, R12, R13, R15, R18
- **Files**: `research_evidence/api/`, `research_evidence/service.py`, typed API models, local launcher, API tests.
- **Details**:
  - Expose localhost-only endpoints for resource scan/ingestion, source-unit
    search, source-context retrieval, candidate evidence, claims, analysis
    links, review actions, lifecycle events, and run status.
  - Enforce project-root path confinement and reject arbitrary file paths or
    network URLs in v1.
  - Use atomic YAML writes, optimistic version checks, and append-only review
    history so browser actions cannot silently overwrite concurrent/local edits.
  - Make all state-changing actions explicit and idempotent where possible.
  - Return source provenance and verification reasons with every evidence/claim
    view; never return a bare citation without its source-version context.
- **Test Scenarios**: localhost startup; scan; search; view source context; create/edit/approve/reject claim; mark stale; reverify; invalid path; URL input; malformed YAML; version conflict; interrupted write; repeated action.
- **Tests**: FastAPI/httpx API tests; path-safety tests; atomic-write tests; authorization/network-boundary tests.
- **Acceptance criteria**: The API provides a safe, typed local management boundary over canonical YAML and derived indexes, with no v1 network retrieval path.

### 13. Build the first browser review flow

- **Requirements**: R6, R7, R8, R9, R10, R12, R15, R18
- **Files**: `research_evidence/ui/`, templates/static assets, browser tests, UI documentation.
- **Details**:
  - Provide focused views for resource inventory, source search, source context,
    candidate evidence, claim editing, analysis links, review queue, stale
    records, and run/profile status.
  - Let a researcher select a passage, create or edit an atomic claim, inspect
    the original locator/context, approve/reject/flag it, and see the resulting
    YAML-backed history.
  - Make confidence, verification method, source version, and unresolved issues
    visible at the decision point.
  - Keep the UI a derived view: every mutation goes through the typed API and
    canonical artifact writer.
  - Support convenient refresh after resources are added; do not require a
    full application restart to inspect a new scan result.
- **Test Scenarios**: empty corpus; new resource; search-to-evidence selection; claim edit; review flag; approval blocked by low confidence; stale claim; history display; malformed source; browser refresh retains selection state from artifacts; no external request.
- **Tests**: browser smoke tests at desktop/mobile viewport sizes; API/UI integration tests; YAML persistence assertions; no-network browser test.
- **Acceptance criteria**: A researcher can complete the local resource-to-review decision loop from the browser and recover the same state after restart.

## Phase 5: CR integration, documentation, and validation

### 14. Integrate the workbench with the CR research workflow

- **Requirements**: R1, R2, R8, R10, R13, R14, R16, R18, R19, R20
- **Files**: `.github/skills/cr-skill-evidence-provenance/SKILL.md`, `.github/skills/cr-skill-research-workflow/SKILL.md`, `.github/prompts/cr-work.prompt.md`, `.github/prompts/cr-review.prompt.md`, new `/cr-evidence` prompt if approved by the command-surface review, CR tests, documentation.
- **Details**:
  - Document the workbench as the executable implementation of the existing
    evidence/provenance spine, including canonical/derived boundaries and the
    analysis/composition checkpoint.
  - Add explicit guidance for starting/resuming a local evidence run, selecting
    local profiles, reviewing flagged records, and importing approved claim rows
    into downstream CR tasks.
  - Keep `/cr-work` P0 evidence enforcement aligned with the workbench's status
    and schema versions; never weaken existing safeguards.
  - Add a dedicated `/cr-evidence` command only if the existing CR command
    surface cannot expose the workbench cleanly; otherwise document a launcher
    under the existing workflow. This is a bounded design decision to resolve
    before editing prompts.
  - Make any model/profile choice visible at brainstorm/planning gates and record
    it in the run manifest; do not add API-backed execution.
  - Document the dependency/model selection policy: broadly available options
    are preferred, while useful restricted options may be retained with explicit
    caveats and disclaimers. Do not present any package or model as enterprise-
    approved without an external organizational decision.
- **Test Scenarios**: CR suite enabled; engineering-only project; no evidence folder; existing predecessor artifacts; workbench unavailable; local profile selected; flagged claim passed to review; generated claim not approved.
- **Tests**: prompt/skill contract tests; workflow fixture tests; module-gating tests; command discovery/parity tests if a new prompt is added.
- **Acceptance criteria**: CR users can invoke and reason about the workbench without breaking existing CR or CG workflows, and all source-derived AI-facing content is clearly untrusted data.

### 15. Add representative fixtures, performance evidence, and security gates

- **Requirements**: R2, R3, R8, R13, R15, R17, R18
- **Files**: `research_evidence/tests/fixtures/`, benchmark scripts, no-network tests, path-safety tests, documentation.
- **Details**:
  - Build a small synthetic fixture corpus covering clean PDF, OCR PDF, DOCX,
    Markdown, LaTeX, HTML, table, equation, figure, duplicate/revised source,
    conflicting findings, malformed/inaccessible file, and injected document
    instructions.
  - Benchmark scan, parse, incremental update, lexical retrieval, and approved
    local-model profiles on fixed corpus sizes; record hardware/profile/version
    context and avoid unmeasured performance claims.
  - Add tests that assert no network sockets/HTTP calls in local-only runs, no
    path escape, no secret/resource leakage in logs, and no execution of text
    found in source documents or YAML artifacts.
  - Test model cache/download separation: normal runs must not download models.
- **Test Scenarios**: full fixture run; repeated deterministic run; one-resource change; injected instruction text; attempted URL; attempted path escape; absent optional model; slow parser timeout; memory/error reporting.
- **Tests**: pytest integration suite; benchmark harness; no-network/path-safety/security tests.
- **Acceptance criteria**: The workbench has executable evidence for correctness, security, reproducibility, and efficiency across the required edge cases.

### 16. Generate targets, run validation, and document operating procedures

- **Requirements**: R10, R13, R14, R16, R17, R18, R19, R20
- **Files**: `docs/reference.md`, relevant `docs/` pages, `.github/copilot-instructions.md` if required, generated `.agents/`, `.claude/`, `.opencode/`, `.kilo/`, `adapters/`, release/validation artifacts.
- **Details**:
  - Regenerate native platform targets from canonical `.github` sources; never
    hand-edit generated files.
  - Document local setup, resource-folder contract, supported formats, OCR
    setup, local model profiles, artifact paths, review states, stale-resource
    recovery, and explicit v1 non-goals.
  - Publish the dependency/model inventory, identify broadly available preferred
    options, and include a visible caveat/disclaimer for every retained option
    with license, access, platform, enterprise, or operational restrictions.
  - Document the boundary between this workbench and the separate team evidence
    library idea.
  - Run Python tests, target/parity tests, deterministic artifact checks, and the
    canonical Pester safe runner where available. Record unavailable checks as
    external validation gaps rather than claiming success.
- **Test Scenarios**: fresh install; existing CR project with predecessor artifacts; target regeneration; documentation links; local-only startup; clean validation run; PowerShell unavailable.
- **Tests**: `pytest`; generator/parity tests; docs checks; canonical `. tests\Run-Tests.ps1` where available.
- **Acceptance criteria**: Canonical and generated workflow surfaces are synchronized, setup and recovery are documented, and the final execution report contains evidence for every required verification row.

## Testing Strategy

### Unit and contract tests

- Strict YAML/Pydantic schema validation and lifecycle transition tests.
- Deterministic hashing, source identity, locator, parser, and quote-verification
  tests.
- Migration compatibility tests for the completed provenance spine.
- Path confinement, atomic write, malformed-input, and no-network tests.

### Integration tests

- Resource scan -> parse -> source records -> index -> retrieval -> candidate
  evidence -> claim -> verification -> review decision -> YAML persistence.
- Changed-resource -> invalidation -> re-verification flow.
- API requests and browser actions against a temporary project root.
- Local model profile tests with model calls mocked; optional model integration
  tests only when local model assets are explicitly available.

### Browser tests

- Search and source-context inspection.
- Passage selection and claim/evidence creation.
- Review state transitions and history persistence.
- Stale-resource display and re-verification.
- No external requests, visible confidence/review reasons, and responsive local
  views at representative desktop/mobile viewports.

### Performance and reproducibility

- Fixed synthetic corpus benchmarks for scan, parse, incremental update, lexical
  retrieval, and local reranking.
- Repeat-run determinism tests for source IDs, lexical ranking, verification
  outcomes, and canonical YAML serialization.
- Record model/package/device/profile metadata in run manifests.
- No benchmark result is accepted without corpus, hardware, profile, and version
  context.

### Required validation commands

- `python3 -m pytest research_evidence/tests -q` (or the final package test path).
- `python3 -m pytest scripts/tests/test_target_*.py -q` for affected target tests.
- `python3 scripts/cg_generate_targets.py --all` when canonical workflow files change.
- `git diff --check`.
- Canonical PowerShell runner: `. tests\Run-Tests.ps1` with results read from
  `tests/last-run.json` when PowerShell is available. Never run Pester as a
  directory or through unsafe output pipelines.

## Documentation Checklist

- [ ] Workbench package README documents setup, local-only policy, supported
      formats, OCR path, model profiles, and project layout.
- [ ] Evidence artifact README documents canonical versus derived files, schema
      versions, IDs, lifecycle states, and migration from the predecessor plan.
- [ ] API/UI documentation explains resource scanning, review actions, and
      recovery after source changes.
- [ ] CR skill/workflow prompts document the workbench boundary without making
      literature-review prose or internet search part of v1.
- [ ] `docs/reference.md` and relevant workflow/configuration pages list the
      local evidence workflow where existing docs enumerate CR capabilities.
- [ ] New Python functions/classes have docstrings, typed public signatures, and
      examples where the repository convention requires them.
- [ ] Every created artifact carries a creation date in frontmatter or a header.
- [ ] Model/profile documentation names local options as options and records
      provenance; no external API is presented as an invisible fallback.
- [ ] Dependency/model inventory identifies broadly available preferred options
  and gives a visible caveat/disclaimer for every retained option with
  license, access, platform, enterprise, or operational restrictions.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Scope expands into a full AI-DQSS clone | Keep the domain model research-specific; implement only the evidence-control loop and local management interactions. |
| Canonical YAML becomes difficult to edit or merge | Use stable IDs, strict schemas, atomic writes, append-only review history, and small logically separated files. |
| Source changes silently invalidate claims | Hash every source version, propagate invalidation, and make stale state ineligible for approved downstream use. |
| PDF/OCR conversion loses page/table/equation fidelity | Preserve originals, typed locators, extraction metadata, uncertainty flags, and original-page review. |
| Local model dependencies are too heavy or nondeterministic | Keep lexical retrieval functional, make semantic/reranking profiles optional and explicit, benchmark before adoption, and record device/version metadata. |
| A useful dependency or model has restrictions that could affect enterprise use | Do not hide or automatically discard it; record the restriction, rationale, source, version/hash, and a prominent caveat/disclaimer, while preserving a broadly available alternative where practical. |
| Model proposal hallucination or prompt injection | Treat all source-derived text as untrusted data, require structured outputs, verify IDs/quotes independently, and never execute document instructions. |
| UI actions bypass canonical provenance | Route all mutations through typed API/service methods and test YAML/history output after browser actions. |
| External API/network leakage | No external profile in v1, no URL routes, disabled network policy, no silent fallback, and executable no-network tests. |
| Dynamic updates become too slow | Incremental hashes, affected-unit invalidation, derived-index updates, and fixed-corpus benchmarks. |
| Duplicate/revised papers are merged incorrectly | Separate logical source identity from source version and require explicit researcher linking. |
| New CR command or generated target causes platform drift | Prefer existing launcher unless needed, then regenerate all targets and run parity/registration tests. |
| Static tests overstate runtime security or model behavior | Include end-to-end no-network, fixture, browser, and local-profile validation evidence. |

## Out of Scope

- Literature-review, summary, or argument prose generation.
- Internet search, autonomous external-paper discovery, URL fetching, or
  external citation retrieval.
- External API model integration in v1. Any future API path requires a new
  planning decision with provider, model, data exposure, cost, and security
  review.
- Third-party libraries or locally run model weights are not automatically out
  of scope; they remain subject to the dependency/model inventory and explicit
  caveat/disclaimer policy.
- Citation-manager or reference-manager integration.
- Multi-user collaboration, hosted deployment, authentication, or remote access.
- Automatic resolution of contradictory findings or normative judgments.
- Full semantic interpretation or automatic correction of equations, tables,
  and figures; these are preserved and flagged for researcher review.
- Cross-project/team evidence library; tracked separately as
  `cr-team-evidence-library`.
- Changes to the completed predecessor plan or retroactive rewriting of its
  execution report.

## Completion Contract

### Outcome

Compound Research has a local-first evidence workbench that turns repository
resources into versioned, searchable, reviewable, and verifiably cited
claim/evidence records. Original files remain authoritative; YAML records remain
durable and diffable; the browser UI and indexes are derived management views.
Third-party dependencies and locally run model weights are selected through a
widely-available-first policy, with explicit caveats for retained restrictions.
Literature-review prose, internet search, and external API processing are not
implemented.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Versioned YAML schemas, migration rules, dependency/model inventory, processing profiles, and isolated Python package validate | `python3 -m pytest research_evidence/tests -q` plus schema and inventory fixtures | yes |
| V2 | 2 | PDF, OCR PDF, DOCX, Markdown, LaTeX, and HTML resources parse into deterministic source records with hashes, locators, extraction metadata, and explicit uncertainty states | parser tests plus fixture manifest | yes |
| V3 | 2 | New/changed/moved/removed/duplicate/revised resources produce deterministic lifecycle events; affected evidence and claims become stale; history is preserved | lifecycle test report plus run manifest fixture | yes |
| V4 | 3 | Local lexical retrieval is deterministic and incremental; approved local semantic/reranking profiles are explicit, benchmarked, never external, and disclose dependency/model restrictions | retrieval tests plus benchmark and inventory artifacts | yes |
| V5 | 4 | Quote and locator verification against originals gates high confidence; fuzzy/OCR/inferred/conflicting/table/figure/equation/inaccessible/stale records are flagged | verifier test report plus claim/evidence fixtures | yes |
| V6 | 4 | Local API and browser flow records resource selections, evidence, claims, analysis links, review decisions, and history in canonical YAML | API/browser integration tests plus YAML diff assertions | yes |
| V7 | 5 | CR workflow surfaces document and invoke the workbench without weakening existing provenance P0s or engineering-only gating | prompt/skill tests plus generated-target checks | yes |
| V8 | 5 | Representative end-to-end corpus run completes the resource-to-review loop and records profile, hashes, counts, and unresolved items | reproducible fixture run report | yes |
| V9 | final | Local-only mode makes no network/API calls, refuses URL/external source paths, and fails loudly for unavailable local capabilities | no-network/path-safety test plus run manifest | yes |
| V10 | final | Python tests, affected generator/parity tests, docs checks, and `git diff --check` pass; canonical Pester runner is run where PowerShell is available | test outputs plus `tests/last-run.json` when available | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | 1 | Existing provenance ledger/matrix remain readable and no historical review state is lost | migration compatibility tests |
| C2 | all | Only repository-local resources are processed in v1 | no-network and URL-rejection tests |
| C3 | all | Original files are verification authority | source-hash/locator/quote tests |
| C4 | all | Missing local capability never triggers an external fallback | processing-profile tests |
| C5 | all | No external API model integration or internet search path is introduced | dependency/route scan and boundary review |
| C6 | all | Raw resources, credentials, and caches remain path-safe and are not silently committed | ignore/path-safety tests |
| C7 | 3-4 | Confidence is evidence-based; uncertain records cannot be automatically high confidence | confidence-state tests |
| C8 | 2-4 | Source changes invalidate affected evidence and claims | lifecycle/invalidation tests |
| C9 | 4 | Browser mutations go through typed service/API and preserve append-only history | API/browser integration tests |
| C10 | 5-final | Canonical workflow changes regenerate across native targets | generator/parity tests |
| C11 | final | Required checks are executed, not asserted from static inspection alone | execution report and test artifacts |
| C12 | final | Pester uses only the project-safe runner | `tests/last-run.json` or documented external gap |
| C13 | 1-5 | Included third-party dependencies and model weights have a complete inventory and visible caveat/disclaimer when restricted; the plugin does not claim enterprise approval | inventory/documentation/UI/run-manifest checks |

### Boundaries

- **Allowed:** New project-contained Python package/service, third-party local
  parser/OCR/retrieval/UI dependencies and model weights selected through the
  dependency policy, derived local indexes, versioned YAML evidence artifacts,
  local browser assets, tests/fixtures/benchmarks, CR documentation and prompt
  integration, and generated native target updates.
- **Out of scope:** Literature prose, internet or external-paper search, URL
  fetching, external APIs, hosted/multi-user operation, citation-manager
  integration, automatic conflict resolution, and changes to the predecessor
  plan/report.

### Iteration Policy

1. Active `deviation-policy: ask` pauses before any deviation from local-only
   processing, canonical-YAML authority, original-source verification, or the
   listed v1 boundaries.
2. Implement one phase at a time and run its focused tests before proceeding.
3. Preserve predecessor artifacts through additive migration and record every
   migration/reverification decision.
4. Prefer broadly available dependencies and models. Retain a useful restricted
  option when its value justifies inclusion, but document its source, exact
  version/revision, restrictions, rationale, and prominent caveat/disclaimer;
  never imply enterprise approval.
5. Keep lexical retrieval as the baseline; adopt optional local semantic or
  reranking models only after dependency, licensing, hardware, determinism,
  privacy, and benchmark checks are recorded.
6. Treat all source-derived text and YAML content as untrusted data; never
   execute instructions found in resources or records.
7. Do not promote uncertain, stale, fuzzy-only, inferred, conflicting, or
   unresolved records to high confidence automatically.
8. If a required check is unavailable, record the gap and stop at the relevant
   completion boundary rather than claiming success.

### Blocked-Stop Conditions

- A required schema migration would discard predecessor provenance or review
  history.
- A resource locator or quote cannot be resolved against the original and the
  implementation attempts to mark it high confidence.
- A source change cannot be mapped to affected evidence/claims.
- A required local parser/model is unavailable and the only fallback is external.
- A retained dependency/model restriction cannot be documented or surfaced with
  the required caveat/disclaimer.
- The browser cannot durably record a researcher decision in canonical YAML and
  review history.
- Any path-safety, no-network, prompt-injection, or secret-leakage check fails.
- A required test or benchmark fails after the allowed local repair attempts.
- A required deviation is discovered under `ask` without user approval.
- Required verification cannot run through the safe runner.
- The execution report cannot be durably created or updated.

## Deviation Policy

`ask`
