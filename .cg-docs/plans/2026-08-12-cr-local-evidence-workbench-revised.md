---
date: 2026-08-12
title: "CR Local Evidence Workbench for Verifiable Research Claims (Revised)"
status: completed
completed-date: 2026-08-13
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-08-12-cr-local-evidence-workbench.md"
supersedes: ".cg-docs/plans/2026-08-12-cr-local-evidence-workbench.md"
predecessor-plan: ".cg-docs/plans/2026-07-30-cr-evidence-provenance-spine.md"
language: "Python/Markdown"
estimated-effort: large
deviation-policy: autonomous
execution-report: ".cg-docs/work-reports/2026-08-12-cr-local-evidence-workbench-revised.md"
artifact-schema-version: 1
revision: 2
phases: 5
completed-phases: [1, 2, 3, 4, 5]
tags: [compound-research, evidence, provenance, claims, document-ingestion, retrieval, verification, local-first, browser-ui, research-integrity, offline-runtime, dependency-governance]
---
<!-- Created 2026-08-12. Revision 2 addresses the plan-review findings. -->

# Plan: CR Local Evidence Workbench for Verifiable Research Claims

## Objective

Build a local-first research evidence workbench for World Bank researchers. It
will turn repository-local research resources into versioned, searchable,
reviewable, and verifiably cited claim/evidence records that can support later
analysis and prose.

The delivery strategy is phased, but Phase 1 must produce a thin, complete and
executable evidence loop over Markdown resources:

```text
resource -> parsed source unit -> local lexical search -> atomic claim
-> deterministic quote verification -> journaled YAML decision -> restart recovery
```

Later phases expand that loop to PDF, DOCX, LaTeX, HTML, OCR, incremental source
lifecycle management, optional local semantic retrieval/reranking, and the
browser workbench. This removes the previous ambiguity between a contracts-only
Phase 1 and the requirement for an early end-to-end vertical slice.

Original resource files remain authoritative. Canonical YAML and append-only
review records are version-controlled. Converted text, OCR text, embeddings,
indexes, browser views, and API responses are derived or explicitly recorded
artifacts.

## Context

The completed predecessor plan,
[2026-07-30-cr-evidence-provenance-spine.md](.cg-docs/plans/2026-07-30-cr-evidence-provenance-spine.md),
delivered the CR evidence/provenance methodology, repo-local corpus default,
claim-evidence and provenance-ledger schemas, anti-hallucination P0 rules, and
workflow/audit surfaces. The earlier workbench plan,
[2026-08-12-cr-local-evidence-workbench.md](.cg-docs/plans/2026-08-12-cr-local-evidence-workbench.md),
was reviewed and is superseded by this revision. Both remain historical
artifacts; this plan is the implementation authority for the workbench.

The workbench is inspired by the strongest AI-DQSS procedures without copying
its assessment-specific application:

- stable source-segment citation IDs;
- parse/index/retrieve/rerank separation;
- structured evidence output rather than prose-only output;
- deterministic quote verification; and
- source-context inspection with independent relevance signals.

The v1 processing policy is local-only. Internet search, external paper
retrieval, URL fetching, and external API model execution are not implemented.
Local open-source retrieval/reranking models may be evaluated as optional
profiles. Model weights may be acquired through a separate, explicit setup
operation when allowed by organizational policy, then loaded from a verified
local cache during offline processing. No model, registry, or package is treated
as enterprise-approved merely because it runs locally.

### Review findings addressed

This revision directly addresses all findings from the plan review:

- **P1.1:** fail-closed runtime network enforcement, loopback binding, offline
  model loading, URL rejection, subprocess controls, and executable tests;
- **P1.2:** explicit compatibility behavior for legacy `external-opt-in` rows;
- **P1.3:** typed versioned locators, source/version identity, parser compatibility,
  ambiguity handling, and an explicit invalidation graph;
- **P1.4:** journaled multi-artifact transactions, locking, crash recovery, and
  deterministic conflict records;
- **P1.5:** Phase 1 now includes a thin Markdown vertical slice rather than
  claiming that contracts alone complete the evidence loop;
- **P2.1:** a dedicated Python subproject, pinned Python range, committed
  `pyproject.toml` and `uv.lock`, and dependency activation states;
- **P2.2:** fixed corpus sizes, reference-environment capture, latency/memory
  targets, and profile-specific benchmark gates; and
- **P2.3:** unconditional Python documentation requirements plus an AST check.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | The verified claim/evidence base is the primary product; literature-review prose generation is not part of v1. | Brainstorm |
| R2 | The active v1 corpus is repository-local and read from a configured resources folder; no internet search or autonomous external-paper discovery exists. | Brainstorm; predecessor plan |
| R3 | The workbench supports PDF, DOCX, Markdown, LaTeX, HTML, and scanned/image-based PDFs through an explicit OCR path. | Brainstorm |
| R4 | Original files remain the evidence authority; converted/OCR text is an indexing aid tied to the original source version. | Brainstorm; predecessor plan |
| R5 | Every source unit has a typed, deterministic, explainable locator that resolves to source context or an explicit ambiguity state. | Brainstorm; AI-DQSS procedure; review P1.3 |
| R6 | Evidence records contain source identity/version, locator, verbatim quotation, extraction method, verification status, confidence, and review state. | Brainstorm; predecessor plan |
| R7 | Claims are atomic factual, methodological, interpretive, or normative statements linked to evidence with explicit supports/contradicts/contextualizes relations. | Brainstorm; predecessor plan |
| R8 | High confidence requires successful quote and locator verification against the original; fuzzy, OCR-uncertain, inferred, conflicting, inaccessible, table/figure/equation, ambiguous, and stale cases remain flagged. | Brainstorm |
| R9 | The local browser workbench manages resources, source context, candidate evidence, claims, analysis links, review queues, selections, approvals, exclusions, edits, and history. | Brainstorm |
| R10 | Researcher actions are durably persisted in readable, diffable YAML and append-only history; derived JSON/index/view artifacts are rebuildable and non-authoritative. | Brainstorm; artifact-view conventions |
| R11 | Resource additions and changes are detected using normalized paths, file identity, and SHA-256 hashes; unchanged source units are reused only under a compatible locator contract. | Brainstorm; review P1.3 |
| R12 | Source changes invalidate affected evidence, claims, and analysis links, require re-verification before re-approval, and preserve prior review history. | Brainstorm |
| R13 | Normal processing is fail-closed and offline: missing local capabilities produce explicit errors and never trigger hidden downloads, telemetry, URL calls, or external fallback. | Brainstorm; charter; review P1.1 |
| R14 | Any model or dependency profile records exact source/version/revision, hashes where available, network behavior, and run metadata; future external API profiles require a new planning decision. | Brainstorm; model governance |
| R15 | The workbench is project-contained, binds to loopback by default, rejects remote hosts and URL resources, and does not write outside the repository. | Charter; review P1.1 |
| R16 | Existing CR provenance artifacts and workflows remain compatible, including explicit handling of legacy `external-opt-in` records; engineering-only projects remain unaffected. | Predecessor plan; review P1.2 |
| R17 | The implementation is efficient for repeated corpus updates, with fixed benchmark corpus sizes and measurable latency, memory, and incremental-update targets. | Brainstorm; review P2.2 |
| R18 | All source-derived content is untrusted data; document text, OCR output, YAML records, and user-authored claims cannot inject workflow instructions. | Security conventions; predecessor plan |
| R19 | Dependency/model selection prefers broadly available, maintained options, while useful restricted options may be retained with explicit caveats and disclaimers. | Owner decision, 2026-08-12 |
| R20 | Every included third-party package, parser, OCR engine, model, or model-weight distribution is inventoried with source, version/revision, hash where available, license/access restrictions, setup/runtime network requirements, telemetry notes, platform support, and enterprise-review status. | Owner decision; review P2.1 |
| R21 | The Python runtime is isolated in a dedicated subproject with a pinned supported Python range and committed `pyproject.toml` and `uv.lock`. | Charter; review P2.1 |
| R22 | Legacy external-source records are preserved but quarantined read-only in v1; they are not fetched, indexed, or eligible for approval without a new local verification event. | Review P1.2 |
| R23 | Canonical state mutations use a journaled transaction protocol with operation IDs, expected revisions, locking, atomic staged writes, commit markers, and crash recovery. | Review P1.4 |
| R24 | New Python functions/classes satisfy the charter documentation standard: docstring, parameters, return values, and at least one example. | Charter; review P2.3 |

## Architecture Decisions

### Dedicated Python subproject and lockfile

The runtime is isolated under `research_evidence/`:

```text
research_evidence/
├── pyproject.toml
├── uv.lock
├── src/research_evidence/
├── tests/
├── benchmarks/
└── README.md
```

The package uses a pinned supported range of Python `>=3.11,<3.14`. Its
`pyproject.toml` declares runtime and development dependencies; `uv.lock` is
committed. The existing repository-level Python scripts remain outside this
runtime dependency graph unless a later plan explicitly integrates them.

The package may use third-party parsers, OCR engines, retrieval libraries,
FastAPI, Pydantic, browser-test tooling, and local model runtimes. Each is
listed in a dependency/model inventory before activation. A dependency is not
rejected solely because it is third-party or restricted, but its restriction,
value, and caveat must be visible and its activation status must be explicit.

### Canonical versus derived state

Canonical state lives under the project evidence directory:

```text
.cg-docs/research/evidence/
├── provenance-ledger.yaml
├── source-records.yaml
├── evidence-records.yaml
├── claim-evidence-matrix.yaml
├── analysis-links.yaml
├── review-history.yaml
├── dependency-model-inventory.yaml
├── runs/
│   ├── <run-id>.yaml
│   └── journal/
└── converted/
```

A local SQLite/FTS or embedding index, browser cache, and rendered source view
are derived artifacts. The package must rebuild derived state from canonical
records and current resources. Derived files are never the only copy of a
researcher decision.

### Dependency/model inventory and activation states

Every package, executable parser, OCR engine, model runtime, and model-weight
distribution has an inventory entry with at least:

```yaml
id: local-reranker-example
kind: package | executable | model | weights
distribution_source: "registry or repository URL used during setup"
exact_version_or_revision: "..."
sha256: "..." # required when the distribution exposes a stable artifact hash
license_or_access_terms: "..."
restriction: "..."
setup_network_required: false
runtime_network_required: false
telemetry_notes: "none known / declared behavior / not verified"
platform_support: [macos, windows, linux]
enterprise_review_status: unreviewed | reviewed | restricted | blocked
selection_rationale: "..."
caveat_disclaimer: "..."
activation_status: candidate | enabled-local | enabled-with-caveat | blocked
```

Activation rules are deterministic:

- `candidate` entries are inventory-only and cannot run;
- `enabled-local` entries have complete provenance and no unresolved blocking
  restriction;
- `enabled-with-caveat` entries have complete provenance, a visible disclaimer,
  and an explicit local activation acknowledgment, but are not labeled
  enterprise-approved; and
- `blocked` entries cannot be selected.

Model-weight acquisition is separate from normal processing. A user-directed
setup command may download or import weights and must record the source,
revision, hash, license/access terms, and caveat. Normal runs use offline/local
loading (`local_files_only` or the equivalent for the selected runtime), fail if
weights are absent, and never download silently.

### Fail-closed network boundary

The v1 runtime enforces all of the following:

1. The service binds to `127.0.0.1` by default and rejects non-loopback bind
   addresses unless a future plan explicitly changes the boundary.
2. Resource inputs must be project-relative local paths; URL schemes, remote
   hosts, redirects, and external citation fetches are rejected before parsing.
3. The offline processing profile disables HTTP clients, proxy use, model
   downloads, telemetry hooks, and remote browser requests.
4. Model loaders must use local-cache-only mode. Setup-time acquisition is a
   separate command and is never called by normal scan, search, or review paths.
5. Child processes are allowlisted local parser/OCR executables from the
   dependency inventory. Shell commands, `curl`, `wget`, package installers,
   and document-provided commands are rejected during normal processing.
6. A process-level network guard rejects non-loopback socket attempts by the
   service and its local worker paths. The test harness attempts direct socket,
   HTTP-client, proxy, model-loader, and browser requests and expects explicit
   denial. OS firewall configuration may provide additional hardening but is
   not treated as the sole control.

### Source identity, typed locators, and compatibility

Resource identity, source version, and source-unit identity are separate:

- `resource_id` identifies a logical resource in the ledger;
- `source_version_id` identifies immutable bytes plus parser/OCR profile,
  locator-schema version, and source hash; and
- `source_unit_id` identifies a unit within a source version using a canonical
  typed locator and normalized text fingerprint.

Typed locators are format-specific structured values, serialized canonically:

```yaml
kind: pdf_text | pdf_image | docx_paragraph | docx_table_row |
      markdown_block | latex_block | html_block
page: 4
block: 12
line_start: null
line_end: null
anchor: null
unit_fingerprint: "sha256:..."
```

The actual fields vary by `kind`; invalid combinations are rejected. A unit ID
is derived from `source_version_id`, canonical locator serialization, and the
unit fingerprint. Same bytes, parser profile, and locator contract reproduce the
same IDs. A parser or locator-contract change creates a new source version.

A move with one unambiguous matching content hash may preserve `resource_id` and
source-unit IDs while recording path history. Duplicate matches are ambiguous
and require review. Parser-version changes use exact unit fingerprints and
neighbor context for best-effort mapping; unique mappings may be proposed, but
ambiguous or missing mappings are review-required and never silently reused.
Legacy free-text locators are imported as `legacy_locator`, remain readable, and
are marked review-required until the original source and locator are verified.

### External-record compatibility matrix

The active v1 corpus accepts only `origin: repo-local` records whose original
path is inside the configured resources root. Existing records are handled as:

| Existing record | v1 behavior |
|---|---|
| `origin: repo-local`, valid local path and hash | Import and index after verification of the current hash |
| `origin: external-opt-in` | Preserve read-only in `external-quarantine.yaml`; do not fetch, index, or approve |
| External row with a copied local original | Preserve origin metadata; require a new local source-version record and original verification |
| Missing/invalid origin | Preserve in unresolved migration output; block activation |
| Legacy quote verified only against converted text | Preserve history; mark `legacy-converted-authority` and require original verification |

This compatibility behavior is tested and documented. It does not silently
rewrite the predecessor artifacts.

### Transaction-safe canonical writes

All state-changing actions use an `ArtifactTransaction` coordinator:

1. Acquire a project evidence-directory lock and validate the expected aggregate
   revision supplied by the caller.
2. Create an operation ID and a prepare journal entry containing affected files,
   previous hashes, new hashes, actor/action metadata, and payload hash.
3. Validate all staged YAML records before changing canonical files.
4. Write temporary files, flush and fsync them, then atomically replace the
   affected canonical files as one coordinated commit sequence.
5. Append the review event and commit marker with the operation ID.
6. Rebuild or invalidate derived indexes after the canonical commit; derived
   rebuild failure leaves an explicit stale-index state, not a partial decision.

Recovery scans prepare entries without commit markers, removes abandoned
staging files, and records an aborted operation. A commit marker with an
incomplete derived rebuild is replayed or marked for rebuild deterministically.
Concurrent writers receive a conflict record containing the expected and actual
revision; the service never silently overwrites a decision.

## Implementation Steps

## Phase 1: Contracts and thin vertical slice

### 1. Create the dedicated Python subproject and runtime boundary

- **Requirements**: R1, R2, R10, R13, R14, R15, R19, R20, R21, R24
- **Files**: `research_evidence/pyproject.toml`, `research_evidence/uv.lock`, `research_evidence/src/research_evidence/`, `research_evidence/tests/`, `research_evidence/README.md`, `.gitignore`.
- **Details**:
  - Define the Python range `>=3.11,<3.14`, package entry points, runtime/dev
    dependencies, and committed lockfile.
  - Create typed settings, custom errors, loguru configuration, and an explicit
    local-only processing profile.
  - Create the dependency/model inventory schema and activation-state validator.
  - Implement loopback host validation, project-root/resource-root confinement,
    URL rejection, local-cache-only model settings, and the process network gate
    contract.
  - Require docstrings with parameters, returns, and an example for every new
    function and class; add the AST check in this phase.
- **Test Scenarios**: package import; `uv` lock consistency; CLI help; invalid Python/runtime profile; invalid project root; missing resources root; non-loopback host; URL input; incomplete restricted inventory; undocumented function/class.
- **Tests**: `research_evidence/tests/test_runtime_contract.py`, `test_inventory.py`, `test_documentation_contract.py`.
- **Acceptance criteria**: The dedicated package is locked, path-confined, loopback-only, inventory-aware, and fails clearly for unavailable or incomplete local capabilities.

### 2. Define schemas, typed identity, external compatibility, and transactions

- **Requirements**: R4, R5, R6, R7, R8, R10, R11, R12, R16, R22, R23, R24
- **Files**: `research_evidence/src/research_evidence/schemas.py`, `identity.py`, `compatibility.py`, `transactions.py`, schema fixtures, migration fixtures.
- **Details**:
  - Define strict models for resources, source versions, typed locators, source
    units, evidence, claims, analysis links, review events, dependency/model
    entries, run manifests, invalidation events, and transaction journal entries.
  - Define state transitions and the approved-evidence predicate in code.
  - Implement the external-record compatibility matrix above, preserving legacy
    fields and marking converted-only verification as review-required.
  - Implement canonical serialization and schema-version checks.
  - Implement journal prepare/commit/abort/recovery behavior with expected
    aggregate revisions and deterministic conflict records.
- **Test Scenarios**: valid/invalid locators; duplicate IDs; legacy free-text locator; external-opt-in row; malformed origin; invalid status transition; concurrent revision conflict; crash after prepare; crash after canonical replacement; recovery with stale derived index.
- **Tests**: schema, migration, identity, transaction, and recovery tests.
- **Acceptance criteria**: Existing provenance artifacts remain readable; unsafe legacy/external records are preserved but not activated; canonical multi-file writes recover without losing history.

### 3. Deliver the thin Markdown evidence loop

- **Requirements**: R1, R2, R4, R5, R6, R7, R8, R9, R10, R13, R15, R18, R23, R24
- **Files**: `src/research_evidence/parsers/markdown.py`, `source_records.py`, `index/lexical.py`, `claims.py`, `verification/basic.py`, CLI commands, thin-loop fixtures.
- **Details**:
  - Parse Markdown blocks into typed source units and deterministic locators.
  - Build a small local SQLite FTS index with deterministic tie-breaking.
  - Allow a researcher to select a source unit, create an atomic claim and
    verbatim evidence record manually, run exact normalized quote verification,
    and commit the decision through `ArtifactTransaction`.
  - Provide CLI dry-run/search/create/verify/recover commands; the browser UI is
    intentionally deferred to Phase 4.
  - Include a restart test proving that the approved decision and review history
    survive process termination.
- **Test Scenarios**: clean Markdown; empty resource folder; no search result; multi-assertion claim; exact quote; fabricated locator; stale source; interrupted write; restart recovery.
- **Tests**: end-to-end thin-loop pytest fixture.
- **Acceptance criteria**: Phase 1 contains a complete executable local evidence loop over Markdown without any network call, external fallback, or browser dependency.

## Phase 2: Format ingestion and source lifecycle

### 4. Implement deterministic resource discovery and version detection

- **Requirements**: R2, R3, R4, R5, R11, R12, R15, R18
- **Files**: `src/research_evidence/resources.py`, `hashing.py`, `identity.py`, discovery fixtures, tests.
- **Details**:
  - Discover only configured project-local resource roots and supported
    extensions; reject symlink escapes and unsupported paths.
  - Normalize project-relative paths and compute SHA-256 hashes.
  - Detect new, unchanged, changed, moved, removed, duplicate-content, and
    revised resources.
  - Preserve identity for an unambiguous move; require review for duplicate
    matches and revisions that cannot be mapped.
  - Record file timestamps as metadata only; hashes determine content identity.
- **Test Scenarios**: new file; unchanged file; same path changed bytes; moved file with same hash; duplicate files; deletion; unsupported extension; symlink escape; inaccessible file; same bytes with changed metadata.
- **Tests**: discovery, hash, identity, and path-safety tests.
- **Acceptance criteria**: Repeated scans emit deterministic resource events and never read outside the configured corpus.

### 5. Implement format-specific parsers and typed locator maps

- **Requirements**: R3, R4, R5, R6, R8, R11, R18, R20, R24
- **Files**: `src/research_evidence/parsers/` for PDF, DOCX, Markdown, LaTeX, and HTML; `source_records.py`; parser fixtures; tests.
- **Details**:
  - Parse each supported format into source units with source version, typed
    locator, heading/context path, extracted text, and parser metadata.
  - Preserve page, paragraph, block, table-row, heading, line, and HTML-anchor
    context where available.
  - Mark tables, figures, equations, captions, footnotes, and lossy conversions
    as typed/review-required units rather than ordinary prose.
  - Record parser package/source, exact version, license/access terms, and
    caveats in the dependency inventory.
  - Apply parser compatibility rules: exact profile reuse preserves IDs; a
    locator-contract change creates a new source version and mapping events.
- **Test Scenarios**: ordinary text; multi-page PDF; DOCX headings/tables; Markdown/LaTeX headings/equations; HTML headings/links; malformed/password-protected file; missing PDF text layer; table/figure/equation locator; parser-version change.
- **Tests**: parser, locator, determinism, malformed-input, and mapping tests.
- **Acceptance criteria**: All non-OCR formats produce inspectable deterministic records with honest unsupported/ambiguous states.

### 6. Add explicit OCR with original-page verification

- **Requirements**: R3, R4, R5, R6, R8, R13, R17, R18, R19, R20, R24
- **Files**: `src/research_evidence/parsers/ocr.py`, OCR profile, OCR fixtures, tests, documentation.
- **Details**:
  - Detect image-based PDFs and expose OCR as an explicit local capability.
  - Record OCR engine/source/version, page/image locator, confidence metadata,
    language/configuration, generated-text hash, license/access terms, and
    restriction disclaimer.
  - Use OCR text for retrieval candidates, but cap confidence and require
    original-page verification for high-confidence evidence.
  - Preserve original PDFs and stable page/image references.
  - Fail loudly when OCR is requested but unavailable; do not silently download
    an OCR engine or send pages to a remote service.
- **Test Scenarios**: text PDF skips OCR; scanned PDF detects OCR need; unavailable OCR; low OCR confidence; altered quote; page image locator; mixed text/image PDF; remote OCR configuration rejected.
- **Tests**: OCR capability, metadata, uncertainty, and no-fallback tests.
- **Acceptance criteria**: OCR passages are searchable and reviewable but cannot automatically receive high confidence without original-page verification.

### 7. Implement lifecycle invalidation and re-verification propagation

- **Requirements**: R6, R8, R11, R12, R17, R23
- **Files**: `src/research_evidence/lifecycle.py`, `invalidation.py`, mapping fixtures, tests.
- **Details**:
  - Apply discovery events to resource versions and parsed units.
  - Reuse unchanged units only when source hash, parser/OCR profile, and locator
    contract are compatible.
  - Model the explicit graph:
    `resource version -> source unit -> evidence -> claim -> analysis link`.
  - Mark affected downstream records stale while preserving the previous
    verification/review decision and reason.
  - Use exact fingerprint mapping for parser changes; unique mappings may be
    proposed, ambiguous mappings require review, and missing mappings remain
    stale.
  - Treat duplicate/revised editions as distinct until a researcher links them.
- **Test Scenarios**: unchanged update; one-page change; changed quote; removed source; moved source; duplicate edition; parser-version change; ambiguous mapping; interrupted invalidation; re-verification restores approval only after checks pass.
- **Tests**: state-machine, graph propagation, mapping, idempotence, and recovery tests.
- **Acceptance criteria**: No stale evidence, claim, or analysis link remains eligible for approved downstream use without successful re-verification.

## Phase 3: Retrieval profiles and candidate evidence

### 8. Generalize the deterministic lexical index and measure the baseline

- **Requirements**: R2, R5, R9, R10, R11, R17, R18, R21, R24
- **Files**: `src/research_evidence/index/`, `retrieval/lexical.py`, index schema, benchmark harness, tests.
- **Details**:
  - Generalize the Phase 1 SQLite FTS index to all parsed source units and
    source versions.
  - Index text, headings, metadata, and typed unit markers without logging raw
    corpus text or making network requests.
  - Make ranking deterministic for equal scores and preserve source order.
  - Update only affected units after lifecycle events; provide a rebuild path
    for corruption/schema changes.
  - Use two fixed benchmark corpora: small (25 documents/2,500 source units)
    and medium (100 documents/20,000 source units). Capture OS, CPU, RAM,
    Python, package versions, and profile in every benchmark.
- **Test Scenarios**: keyword/heading match; no result; equal-score order; changed/deleted unit replacement; corrupt index rebuild; repeated deterministic run.
- **Tests**: index schema, retrieval, incremental update, determinism, and benchmark tests.
- **Acceptance criteria**: On the recorded reference environment, the lexical profile targets p95 query latency <=250 ms on the medium corpus, single-resource incremental update <=10 s for a 1,000-unit resource, full lexical rebuild <=60 s on the medium corpus, and <=1 GB process memory excluding optional model processes. A missed target leaves the profile in `candidate` status and is reported; it is not described as efficient.

### 9. Evaluate optional local semantic retrieval and independent reranking

- **Requirements**: R2, R5, R8, R13, R14, R17, R19, R20, R21, R24
- **Files**: `src/research_evidence/retrieval/dense.py`, `sparse.py`, `rerank.py`, profile configuration, inventory entries, tests, benchmarks.
- **Details**:
  - Evaluate AI-DQSS-inspired local options such as dense embeddings,
    SPLADE-style sparse retrieval, and a local cross-encoder reranker.
  - Prefer broadly available, maintained options. A restricted option may be
    retained when its quality/usability benefit is material, but only with a
    complete inventory entry, visible caveat, and `enabled-with-caveat` status.
  - Do not hard-code a model until source, exact version/revision, hash where
    available, license/access terms, package/model size, hardware support,
    determinism, setup network behavior, runtime network behavior, telemetry,
    and benchmark results are recorded.
  - Keep lexical retrieval enabled as the baseline. Optional model absence is an
    explicit capability error or an intentional profile choice, never a hidden
    external fallback.
  - Set a profile-specific p95 query and memory budget before benchmarking. The
    default target is p95 query <=5 s and <=4 GB additional memory on the
    recorded reference environment; profiles missing their declared target stay
    `candidate` and cannot be the default.
  - Model acquisition is separate from processing and uses verified local cache
    loading only during normal runs.
- **Test Scenarios**: model available; cache missing; offline loader; CPU/MPS differences; deterministic repeat run; lexical/hybrid comparison; short/noisy segment; incomplete inventory; restricted model without acknowledgment; attempted download.
- **Tests**: mocked retrieval contract tests; optional local-model integration tests; activation-gate tests; benchmark harness.
- **Acceptance criteria**: Optional profiles are explicitly selectable, inventory-complete, caveat-visible, reproducible enough for evidence review, benchmarked against lexical retrieval, and never external.

### 10. Generate candidate evidence and optional local claim proposals

- **Requirements**: R6, R7, R8, R9, R10, R14, R18, R19, R20, R24
- **Files**: `src/research_evidence/evidence.py`, `claims.py`, local claim-proposal adapter, fixtures, tests.
- **Details**:
  - Keep manual claim creation available and fully supported.
  - Optionally allow an enabled local model to propose candidate evidence and
    atomic claims from retrieved passages. All proposals remain `candidate`.
  - Require claim type, atomic statement, source unit/version, verbatim quote,
    relation (`supports`, `contradicts`, or `contextualizes`), rationale, run ID,
    profile ID, and dependency/model inventory reference.
  - Flag multiple independent assertions for researcher splitting.
  - Treat model output as untrusted data; citation IDs and paraphrases never
    bypass verification.
- **Test Scenarios**: manual claim; local proposal; no evidence; multi-assertion claim; fabricated source ID; paraphrase without quote; conflicting evidence; duplicate proposal; restricted model caveat displayed.
- **Tests**: candidate-record, atomicity, fabricated-reference, and profile-reference tests.
- **Acceptance criteria**: Candidate records are source-linked and reviewable without proposal output bypassing verification or approval.

## Phase 4: Verification and browser workbench

### 11. Implement deterministic quotation, locator, and confidence verification

- **Requirements**: R4, R5, R6, R7, R8, R11, R12, R18, R24
- **Files**: `src/research_evidence/verification/`, `confidence.py`, verification fixtures, tests.
- **Details**:
  - Resolve source IDs and typed locators against the current source version and
    original resource.
  - Prefer exact normalized quote matching and exact source-unit matching.
  - Use fuzzy/chunk matching only as a diagnostic; it cannot promote evidence to
    high confidence automatically.
  - Handle cross-page/unit quotes, tables, captions, equations, and OCR through
    typed review-required outcomes.
  - Verify source hash/version, quote presence, locator validity, source/quote
    association, and evidence relation independently.
  - Emit machine-readable reasons for `verified-high`, `flagged-medium`,
    `flagged-low`, `stale`, `abstained`, and `rejected`.
- **Test Scenarios**: exact quote; whitespace normalization; cross-page quote; source ID mismatch; fabricated locator; fuzzy-only match; OCR mismatch; table/equation/figure; stale source; inaccessible original; conflicting evidence; legacy locator.
- **Tests**: verifier unit/property, source-version, locator, and confidence transition tests.
- **Acceptance criteria**: Only evidence with a resolvable typed locator, matching source version, and successful original-authority verification can receive high confidence automatically.

### 12. Implement the transaction-safe local FastAPI service

- **Requirements**: R2, R9, R10, R11, R12, R13, R15, R18, R23, R24
- **Files**: `src/research_evidence/api/`, `service.py`, typed request/response models, transaction endpoints, tests.
- **Details**:
  - Expose loopback-only endpoints for resource scan/ingestion, source search,
    source context, candidate evidence, claims, analysis links, review actions,
    lifecycle events, recovery, and run status.
  - Reject arbitrary paths, URLs, remote hosts, and unsupported operations.
  - Route every mutation through `ArtifactTransaction` with operation ID,
    expected revision, lock, staged YAML, commit marker, and review event.
  - Return source provenance, source version, verification reason, confidence,
    caveat disclaimer, and history with every evidence/claim view.
  - Make state-changing actions idempotent and return deterministic conflict
    records when the expected revision is stale.
- **Test Scenarios**: loopback startup; scan/search/context; create/edit/approve/reject; stale/reverify; invalid path; URL input; malformed YAML; concurrent tabs; crash at each journal stage; recovery; repeated action; non-loopback bind rejected.
- **Tests**: FastAPI/httpx API tests; transaction, locking, recovery, path-safety, and network-boundary tests.
- **Acceptance criteria**: The API is a safe typed local management boundary over canonical YAML and derived indexes, with recoverable multi-artifact state changes and no v1 network retrieval path.

### 13. Build the first browser review flow

- **Requirements**: R6, R7, R8, R9, R10, R12, R14, R15, R18, R20, R23, R24
- **Files**: `src/research_evidence/ui/`, templates/static assets, browser tests, UI documentation.
- **Details**:
  - Provide resource inventory, source search, source context, candidate
    evidence, claim editing, analysis links, review queue, stale records, run
    status, and dependency/model caveat views.
  - Let researchers select passages, create/edit atomic claims, inspect original
    locators, approve/reject/flag records, and see append-only history.
  - Make confidence, verification method, source version, unresolved issues,
    and dependency caveats visible at the decision point.
  - Route every mutation through the API; browser state is never canonical.
  - Disable external links/requests in source rendering and test restart/refresh
    recovery from YAML-backed state.
- **Test Scenarios**: empty corpus; new resource; search-to-evidence selection; claim edit; low-confidence approval behavior; stale claim; history display; restricted dependency disclaimer; malformed source; refresh/restart; external request blocked.
- **Tests**: browser smoke tests at representative desktop/mobile viewports; API/UI integration tests; YAML/history assertions; no-network browser tests.
- **Acceptance criteria**: A researcher can complete the local resource-to-review decision loop in the browser and recover the same state after restart.

## Phase 5: CR integration, security, performance, and release validation

### 14. Integrate the workbench with the CR research workflow

- **Requirements**: R1, R2, R8, R10, R13, R14, R16, R18, R19, R20, R22, R24
- **Files**: `.github/skills/cr-skill-evidence-provenance/SKILL.md`, `.github/skills/cr-skill-research-workflow/SKILL.md`, `.github/prompts/cr-work.prompt.md`, `.github/prompts/cr-review.prompt.md`, a new `/cr-evidence` prompt only if approved, CR tests, docs.
- **Details**:
  - Document the workbench as the executable implementation of the evidence/
    provenance spine and the analysis/composition checkpoint.
  - Document the external-record compatibility matrix and ensure legacy
    `external-opt-in` rows remain read-only/quarantined in v1.
  - Add guidance for starting/resuming local evidence runs, selecting profiles,
    reviewing flags, and importing approved claim rows into downstream CR work.
  - Keep `/cr-work` P0 enforcement aligned with schema/status/version rules.
  - Decide whether an existing launcher is sufficient before adding `/cr-evidence`;
    if a new prompt is needed, register and regenerate it across targets.
  - Make model/dependency choices visible at planning gates and record them in
    the run manifest. Do not add API-backed execution.
- **Test Scenarios**: CR enabled; engineering-only project; no evidence folder; predecessor artifacts; external-quarantine rows; workbench unavailable; local profile; flagged claim; generated claim not approved.
- **Tests**: prompt/skill contracts; workflow fixtures; module gating; command discovery/parity if needed.
- **Acceptance criteria**: CR users can invoke and reason about the workbench without weakening existing P0s, external-record boundaries, or CG-only behavior.

### 15. Add fixture, security, and prompt-injection validation

- **Requirements**: R2, R3, R8, R13, R15, R18, R20, R22, R23, R24
- **Files**: `research_evidence/tests/fixtures/`, no-network tests, path-safety tests, dependency inventory fixtures, security documentation.
- **Details**:
  - Cover clean PDF, OCR PDF, DOCX, Markdown, LaTeX, HTML, tables, equations,
    figures, duplicate/revised sources, conflicting findings, malformed files,
    inaccessible files, legacy external rows, and injected document instructions.
  - Test direct sockets, HTTP clients, proxy variables, model loaders, browser
    requests, redirects, non-loopback binding, and forbidden subprocesses.
  - Test that source text and YAML content are never executed as instructions.
  - Test missing optional models and restricted inventory caveats.
- **Test Scenarios**: full fixture run; repeated deterministic run; one-resource change; injected instruction; attempted URL/path escape; absent model; attempted download; remote OCR; crash recovery; external legacy row.
- **Tests**: pytest integration/security suite and network-boundary harness.
- **Acceptance criteria**: Executable evidence demonstrates source safety, offline behavior, path confinement, migration safety, and prompt-injection resistance.

### 16. Produce measurable performance and reproducibility evidence

- **Requirements**: R11, R13, R14, R17, R19, R20, R21, R23, R24
- **Files**: `research_evidence/benchmarks/`, benchmark manifests, reports, tests.
- **Details**:
  - Run the small and medium fixed corpora defined in Step 8.
  - Record hardware, OS, Python, package lock hash, profile, model/device,
    corpus counts, latency distributions, memory peak, and incremental update
    cost.
  - Require lexical baseline thresholds from Step 8. Optional model profiles
    require their declared p95/memory budgets from Step 9; otherwise remain
    candidates and cannot become defaults.
  - Run repeatability checks for source IDs, rankings, verification outcomes,
    canonical YAML serialization, and transaction recovery.
- **Test Scenarios**: cold/warm index; repeated query; one-resource update; full rebuild; optional model load; CPU/MPS profile; interrupted run.
- **Tests**: benchmark harness and reproducibility assertions.
- **Acceptance criteria**: Performance and determinism claims are backed by a complete machine-readable benchmark artifact; unmet targets are visible and prevent default-profile promotion.

### 17. Generate targets, enforce documentation, and complete validation

- **Requirements**: R10, R13, R14, R16, R17, R18, R19, R20, R21, R24
- **Files**: `docs/reference.md`, relevant docs, `.github` canonical workflow files if changed, generated `.agents/`, `.claude/`, `.opencode/`, `.kilo/`, `adapters/`, release/validation artifacts.
- **Details**:
  - Regenerate native targets from canonical sources; never hand-edit generated
    files.
  - Document setup-time dependency/model acquisition, offline runtime behavior,
    source-folder contract, supported formats, OCR setup, activation states,
    caveats/disclaimers, artifact paths, review states, stale recovery, and v1
    non-goals.
  - Run the AST documentation check over every new Python function/class and
    require docstrings, parameters, returns, and an example.
  - Run Python tests, generator/parity tests, docs checks, `git diff --check`,
    and the canonical safe Pester runner where PowerShell is available.
- **Test Scenarios**: fresh package setup; existing CR project; predecessor artifacts; target regeneration; documentation links; local-only startup; PowerShell unavailable.
- **Tests**: `uv run --project research_evidence pytest`; affected target tests; docs checks; `. tests\Run-Tests.ps1` where available.
- **Acceptance criteria**: Canonical/generated workflow surfaces are synchronized, the operating procedures disclose dependency restrictions, all new Python code meets documentation standards, and the execution report contains evidence for every required verification row.

## Testing Strategy

### Unit and contract tests

- Strict YAML/Pydantic schema, inventory, activation, lifecycle, and transaction
  validation.
- Deterministic hashing, typed identity, locator, parser, source mapping, and
  quote-verification tests.
- Migration compatibility tests for predecessor local, external, and
  converted-authority records.
- Path confinement, loopback binding, offline loading, forbidden URL/subprocess,
  atomic write, crash recovery, malformed-input, and no-network tests.
- AST documentation tests for every new function/class.

### Integration tests

- Markdown thin loop: scan -> parse -> lexical search -> candidate claim ->
  exact verification -> transaction -> restart recovery.
- Full resource scan -> parse -> source records -> index -> retrieval -> claim ->
  verification -> review decision -> YAML persistence.
- Changed-resource -> mapping -> invalidation -> re-verification flow.
- API/browser mutations across multiple canonical artifacts and review history.
- Local model profiles mocked by default; integration tests only when local model
  assets are explicitly present and inventory-complete.

### Performance and reproducibility

- Fixed small/medium corpora and threshold table from Steps 8 and 16.
- Repeat-run determinism for source IDs, rankings, verification, YAML, and
  transaction recovery.
- Complete environment/profile/model/dependency metadata in benchmark manifests.
- No performance or local-safety claim without executed evidence.

### Required validation commands

- `uv run --project research_evidence pytest -q`.
- Affected repository Python tests with `python3 -m pytest ...`.
- `python3 scripts/cg_generate_targets.py --all` when canonical workflow files change.
- `git diff --check`.
- Canonical PowerShell runner: `. tests\Run-Tests.ps1`, with results read from
  `tests/last-run.json` when PowerShell is available. Never run Pester as a
  directory or through unsafe output pipelines.

## Documentation Checklist

- [ ] Dedicated package README documents Python setup, committed lockfile,
      local-only policy, setup-time model acquisition, offline runtime, formats,
      OCR, and project layout.
- [ ] Dependency/model inventory documents source, exact version/revision, hash,
      license/access terms, network behavior, telemetry, platform support,
      enterprise status, rationale, and caveat for every included component.
- [ ] Evidence README documents canonical/derived files, schema versions, typed
      IDs/locators, lifecycle states, transactions, and predecessor migration.
- [ ] API/UI documentation explains scanning, review actions, transaction
      recovery, external-record quarantine, and stale-resource recovery.
- [ ] CR skills/prompts document the workbench boundary without making literature
      prose or internet search part of v1.
- [ ] `docs/reference.md` and relevant workflow/configuration pages list the
      local evidence workflow.
- [ ] Every new Python function/class has a docstring with parameters, return
      values, and at least one example; the AST check passes.
- [ ] Every created artifact carries a creation date in frontmatter or header.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Scope expands into a full AI-DQSS clone | Keep the domain model research-specific; prove the thin loop first and defer optional breadth behind phase gates. |
| Phase 1 becomes contracts-only again | Make the Markdown thin-loop test a required Phase 1 completion item. |
| Network calls escape application-level controls | Loopback-only binding, URL rejection, offline loaders, process network guard, subprocess allowlist, and executable tests. |
| Legacy external records are silently activated | Compatibility matrix quarantines them read-only; only new local verification can activate a local copy. |
| Locator mapping creates false continuity | Typed versioned locators, parser compatibility, fingerprint mapping, and review-required ambiguity. |
| Source changes leave approved claims active | Explicit invalidation graph and stale-state approval predicate. |
| YAML files diverge after a crash or concurrent browser actions | Journaled transaction coordinator, locks, revisions, commit markers, recovery, and conflict records. |
| Restricted dependency/model causes enterprise or license risk | Inventory, rationale, exact source/version/hash, visible caveat, activation acknowledgment, and no claim of enterprise approval. |
| Runtime dependencies drift or are unavailable | Dedicated `pyproject.toml`/`uv.lock`, capability probe, explicit activation status, and fail-loud behavior. |
| Local models are too heavy or nondeterministic | Lexical baseline remains functional; optional profiles have predeclared resource/determinism budgets and cannot become defaults when unmet. |
| PDF/OCR conversion loses page/table/equation fidelity | Preserve originals, typed locators, extraction metadata, uncertainty flags, and original-page review. |
| Model proposal hallucination or prompt injection | Treat source/YAML content as untrusted data, verify IDs/quotes independently, and never execute document instructions. |
| Dynamic updates become too slow | Incremental hashes, affected-unit invalidation, derived-index updates, and fixed benchmark thresholds. |
| Static tests overstate runtime security/performance | Require executable network, crash-recovery, browser, benchmark, and fixture evidence. |
| Generated target drift | Regenerate canonical targets and run ownership/parity tests after any workflow-surface edit. |

## Out of Scope

- Literature-review, summary, or argument prose generation.
- Internet search, autonomous external-paper discovery, URL fetching, and
  external citation retrieval.
- External API model execution in v1. A future API path requires a new planning
  decision with provider, model, data exposure, cost, and security review.
- Hosted deployment, multi-user collaboration, authentication, and remote access.
- Citation-manager integration.
- Automatic resolution of contradictory findings or normative judgments.
- Full semantic interpretation or automatic correction of equations, tables, and
  figures; these remain preserved and review-required.
- Cross-project/team evidence library (`cr-team-evidence-library`).
- Silent destructive migration of predecessor artifacts.

Third-party libraries and locally run model weights are explicitly allowed when
selected through the inventory/activation policy. Restricted components may be
retained with documented caveats and disclaimers; they are not automatically
enterprise-approved.

## Completion Contract

### Outcome

Compound Research has a local-first evidence workbench whose first phase proves
a complete Markdown resource-to-review loop, followed by supported-format
ingestion, source-version lifecycle management, deterministic verification,
transaction-safe YAML persistence, optional local retrieval/reranking, and a
loopback-only browser workbench. Original files remain authoritative. All
third-party components are inventory-controlled, and restricted components are
surfaced with caveats rather than silently treated as approved.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Dedicated Python subproject, pinned Python range, `pyproject.toml`, `uv.lock`, inventory schema, activation states, and documentation AST check validate | `uv run --project research_evidence pytest tests/test_runtime_contract.py tests/test_inventory.py tests/test_documentation_contract.py -q` | yes |
| V2 | 1 | Markdown resource -> lexical search -> manual atomic claim -> exact verification -> journaled YAML decision -> restart recovery works offline | `test_thin_loop.py` end-to-end fixture | yes |
| V3 | 1 | Typed identity/locator schemas and legacy external/converted-authority compatibility behavior validate | identity/migration fixture report | yes |
| V4 | 1 | Journaled multi-artifact transaction handles prepare, commit, abort, crash recovery, concurrent revision conflict, and stale derived index | transaction/recovery tests | yes |
| V5 | 2 | PDF, DOCX, Markdown, LaTeX, HTML, and OCR paths produce deterministic records and explicit uncertainty | parser/OCR fixture report | yes |
| V6 | 2 | Resource lifecycle events map source versions/units and stale all affected evidence, claims, and analysis links | lifecycle golden report | yes |
| V7 | 3 | Lexical baseline meets declared thresholds; optional local profiles are inventory-complete, benchmarked, and never external | benchmark artifact and profile activation tests | yes |
| V8 | 4 | Original-authority quote/locator verification gates high confidence and flags uncertain cases | verifier/confidence fixtures | yes |
| V9 | 4 | Loopback API/browser mutations preserve canonical YAML, journal, conflict records, and history | API/browser/crash integration report | yes |
| V10 | 5 | CR workflow preserves P0 enforcement, quarantines legacy external rows, and leaves CG-only projects unaffected | prompt/skill/module tests and generated-target checks | yes |
| V11 | final | Runtime rejects remote hosts/URLs, blocks outbound network and hidden downloads, loads models offline, and rejects forbidden subprocesses | network-boundary/path-safety report | yes |
| V12 | final | Fixed-corpus performance and reproducibility thresholds are met or visible candidate-profile failures are recorded | benchmark manifest/report | yes |
| V13 | final | Documentation, Python tests, affected target/parity tests, docs checks, and safe Pester validation pass where available | test outputs, `tests/last-run.json`, execution report | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | 1 | Dedicated runtime uses pinned `pyproject.toml`/`uv.lock` and supported Python range | package/lock tests |
| C2 | 1-5 | Existing `external-opt-in` records are preserved read-only/quarantined and not activated by v1 | migration/integration tests |
| C3 | 1-4 | Typed source identity and locator versions prevent unsafe automatic remapping | identity/mapping tests |
| C4 | 1-4 | Canonical writes are journaled, locked, revisioned, and recoverable | transaction tests |
| C5 | all | Normal processing is loopback-only and offline; no URL, telemetry, hidden download, or external fallback | network-boundary tests |
| C6 | 1-5 | Included components have complete inventory records and visible caveats when restricted | inventory/UI/manifest checks |
| C7 | 3-5 | Performance claims use fixed corpus, hardware, version, and explicit thresholds | benchmark report |
| C8 | all | New Python code has docstrings, parameters, returns, and examples | AST documentation test |
| C9 | all | Raw resources, credentials, caches, and generated indexes remain path-safe and uncommitted by default | ignore/path-safety tests |
| C10 | final | Required checks are executed rather than inferred from static inspection | execution report |
| C11 | final | Pester uses only the safe runner | `tests/last-run.json` or documented external gap |

### Boundaries

- **Allowed:** Dedicated local Python package/service, third-party local
  parser/OCR/retrieval/UI dependencies and model weights selected through the
  inventory policy, local indexes, YAML evidence artifacts, browser assets,
  fixtures/benchmarks, CR integration, and generated target updates.
- **Out of scope:** Internet/external-paper search, URL fetching, external APIs,
  hosted collaboration, citation-manager integration, automatic conflict
  resolution, literature prose, and destructive predecessor migration.
- **Legacy external records:** preserved as read-only quarantined metadata, not
  fetched/indexed/approved by v1.

### Iteration Policy

1. Active `deviation-policy: autonomous` permits a justified deviation from
  the plan when it stays within the charter and protected boundaries; record
  the rationale, impact, and affected verification evidence in the execution
  report. Deviations that cross local-only runtime, original-source authority,
  canonical YAML, transaction safety, or stated boundaries remain blocked.
2. Phase 1 must pass the thin Markdown end-to-end gate before broader formats,
   OCR, optional models, or browser work proceed.
3. Prefer broadly available dependencies/models. A restricted component may be
   retained only with complete inventory, explicit activation status, caveat,
   and no claim of enterprise approval.
4. Preserve predecessor artifacts through additive migration; quarantine legacy
   external/converted-authority records rather than silently activating them.
5. Treat locator ambiguity, source-version mapping uncertainty, stale records,
   transaction recovery failure, network-boundary failure, and missing required
   documentation as blocking correctness issues.
6. Keep lexical retrieval as the baseline. Optional models remain candidates
   until dependency, licensing, hardware, determinism, privacy, offline, and
   performance gates pass.
7. Record deviations, accepted exceptions, benchmark failures, and unresolved
   uncertainty in the execution report.

### Blocked-Stop Conditions

- The Phase 1 thin loop cannot complete without an external service or hidden
  network call.
- The service can bind remotely, fetch URLs, download models during processing,
  emit telemetry, or execute forbidden subprocesses.
- Legacy provenance/external metadata would be lost or silently activated.
- Typed source identity or locator mapping is ambiguous without a review flag.
- A source change cannot be mapped to affected downstream records.
- A multi-artifact mutation cannot recover after interruption or concurrent
  revision conflict.
- A dependency/model restriction cannot be inventoried and surfaced with its
  caveat/disclaimer.
- A required benchmark target or documentation check fails.
- Any required test fails after allowed local repairs.
- A proposed deviation lacks a documented rationale and impact, or would cross
  a charter, security, evidence-authority, transaction-safety, or stated-scope
  boundary.
- Required validation cannot run through the safe runner.
- The execution report cannot be durably created or updated.

## Deviation Policy

`autonomous`
