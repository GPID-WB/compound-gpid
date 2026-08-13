---
created: "2026-08-12"
plan: ".cg-docs/plans/2026-08-12-cr-local-evidence-workbench-revised.md"
status: completed
---

# Execution Report: CR Local Evidence Workbench (Phase 1)

- Plan reference: `.cg-docs/plans/2026-08-12-cr-local-evidence-workbench-revised.md`
- Active deviation policy: `autonomous` (no runtime override)
- Run started: 2026-08-12

## Completed Steps/Phases

- Phase 1: in progress
- Step 1: complete (2026-08-12)
- Step 2: complete (2026-08-12)
- Step 3: complete (2026-08-12)
- Phase 1: complete (2026-08-12)

## Deviations

None recorded.

## Accepted Exceptions

None recorded.

## Evidence Table

| ID | Phase | Evidence | Status | Artifact |
|----|-------|----------|--------|----------|
| V1 | 1 | Runtime package, lock metadata, inventory activation, and documentation AST contract | passed | `uv lock --project research_evidence --check`; 14 focused pytest tests passed |
| V2 | 1 | Markdown thin loop completes offline from resource to verified journaled decision and restart recovery | passed | `pytest test_thin_loop.py -q`: 3 passed, including changed-original stale rejection |
| V3 | 1 | Typed identity/locator schemas and external/converted-authority compatibility | passed | `pytest test_schemas.py test_identity.py test_compatibility.py -q`: 10 passed |
| V4 | 1 | Journaled transactions cover prepare, commit, abort, recovery, conflict, and stale derived state | passed | `pytest test_transactions.py -q`: 4 passed through shared secure_fs publication |

## Constraints Check

| ID | Constraint | Status | Evidence |
|----|------------|--------|----------|
| C1 | Dedicated runtime uses pinned package metadata and supported Python range | passed | `uv lock --project research_evidence --check`; focused package tests |
| C2 | Legacy external records remain quarantined and read-only | passed | V3 compatibility fixture |
| C3 | Typed identity and locator versions prevent unsafe remapping | passed | V3 identity/schema fixtures |
| C4 | Canonical writes are journaled, locked, revisioned, and recoverable | passed | V4 transaction/recovery fixtures |
| C5 | Normal processing is local-only and offline | passed for Step 1 boundary | Runtime socket, proxy, URL, and subprocess tests |
| C6 | Included components have inventory records and caveats | passed for Step 1 direct dependencies | `dependency-model-inventory.yaml`; inventory tests |
| C8 | New Python code has required docstrings | passed for Step 1 source | `test_documentation_contract.py` |
| C9 | Generated state is path-safe and uncommitted by default | passed for Step 1 paths/ignore rules | Runtime path tests; `.gitignore` review |

## Remaining Uncertainty

- Process-level network enforcement is covered for the current macOS runtime;
	cross-platform subprocess/socket hardening remains a later integration concern.
- Optional parsers, OCR, semantic profiles, lifecycle invalidation, API, and UI
	are not yet implemented and remain Phase 2-5 work.
- A repository-wide pytest run reached 1,762 tests: 1,760 passed, 6 skipped,
	and two unrelated existing release-fixture tests failed. The package-only
  Phase 1 suite passed 39/39 and is the applicable phase gate.

## Superseded Phase 1 Status

`superseded` -- Phase 1 complete; later phases are recorded below.

## Phase 2 Run/Resume (2026-08-12)

- Resumed explicitly with `/cg-work phase2` on branch `cr-lit-review`.
- Artifact preflight passed: `cg-render-artifact --validate-only`.
- Active deviation policy: `autonomous` (no runtime override).
- Steps 4-7 completed on 2026-08-12; Phase 1 evidence and decisions remain unchanged.

### Completed Phase 2 Steps

- Step 4: complete (2026-08-12) -- 10 hashing/discovery tests passed, including
	hash-based unchanged/revised/moved/removed/duplicate events and symlink escape
	rejection.
- Step 5: complete (2026-08-12) -- 11 parser/source-record/identity tests passed
	across PDF, DOCX, Markdown, LaTeX, and HTML, with typed review-required units
	and locked pypdf provenance.
- Step 6: complete (2026-08-12) -- 4 OCR capability tests passed, plus the
	combined parser/OCR/documentation gate (13 passed); scanned-page output remains
	low-confidence and original-page verification is mandatory.
- Step 7: complete (2026-08-12) -- 6 lifecycle tests passed, including exact
	fingerprint mapping, stale graph propagation, idempotence, re-verification,
	and interrupted canonical invalidation recovery.

### Phase 2 Evidence Update

| ID | Status | Evidence |
|----|--------|----------|
| V5 | passed | Combined parser/OCR/documentation gate: 13 tests passed; pypdf and candidate Tesseract inventory records |
| V6 | passed | Resource/hash/lifecycle gate: 16 tests passed, including interrupted invalidation recovery |

### Phase 2 Evidence

| ID | Step | Evidence | Status | Artifact |
|----|------|----------|--------|----------|
| V5 | 5-6 | PDF, DOCX, Markdown, LaTeX, HTML, and OCR paths produce deterministic records and explicit uncertainty | passed | V5 gate: 13 tests |
| V6 | 7 | Resource lifecycle events map source versions/units and stale affected evidence, claims, and analysis links | passed | V6 gate: 16 tests |

### Phase 2 Remaining Uncertainty

- Parser and OCR dependencies must be inventoried with exact versions, licenses,
  network behavior, platform support, and caveats before activation.
- Tesseract remains a `candidate` capability until setup, enterprise review, and
	a verified local engine version/hash are recorded.

### Phase 2 Constraints Check

| ID | Constraint | Status | Evidence |
|----|------------|--------|----------|
| C2 | Legacy external records remain quarantined and read-only | passed | Phase 1 compatibility tests remain green in 67-test package suite |
| C3 | Typed source identity and locator versions prevent unsafe remapping | passed | Parser/version and lifecycle mapping tests |
| C4 | Canonical writes are journaled, locked, revisioned, and recoverable | passed | Lifecycle persistence recovery test |
| C5 | Normal processing is loopback-only and offline | passed | Phase 1 network tests plus OCR no-network contract |
| C6 | Included parser/OCR components have inventory records and caveats | passed | pypdf and candidate Tesseract inventory entries |
| C8 | New Python code has required docstrings | passed | Documentation AST gate |
| C9 | Generated state is path-safe and uncommitted by default | passed | Resource path/symlink tests and package ignore rules |

### Superseded Phase 2 Status

`superseded` -- Phase 2 complete; later phases are recorded below.

## Phase 3 Run/Resume (2026-08-12)

- Resumed explicitly with `/cg-work phase3` on branch `cr-lit-review`.
- Artifact preflight passed: `cg-render-artifact --validate-only`.
- Active deviation policy: `autonomous` (no runtime override).
- Steps 8-10 completed on 2026-08-13; Phase 1 and Phase 2 evidence remain unchanged.

### Phase 3 Evidence

| ID | Step | Evidence | Status | Artifact |
|----|------|----------|--------|----------|
| V7 | 8-10 | Lexical baseline, optional local profiles, and candidate evidence/claim proposals satisfy deterministic offline gates | passed | 15 focused tests; 81-test package suite; fixed benchmark report |

### Completed Phase 3 Steps

- Step 8: complete (2026-08-13) -- generalized typed SQLite FTS retrieval with
	replacement/removal and corrupt-index rebuild; fixed small/medium benchmarks
	passed all thresholds.
- Step 9: complete (2026-08-13) -- dense, sparse, and reranker adapters remain
	candidate-only, cache-gated, budget-aware, and local-files-only.
- Step 10: complete (2026-08-13) -- source-linked candidate proposals preserve
	candidate/flagged-low status, reject fabricated IDs and non-atomic claims, and
	reject duplicate proposal IDs.

### Phase 3 Benchmark Evidence

| Corpus | Documents | Source Units | Rebuild | Query p95 | Status |
|--------|-----------|--------------|---------|-----------|--------|
| small | 25 | 2,500 | 0.34 s | 1.70 ms | passed |
| medium | 100 | 20,000 | 17.31 s | 10.46 ms | passed |

Benchmark artifact: `research_evidence/benchmarks/lexical-baseline-2026-08-13.json`.
It records environment, thresholds, update/RSS/memory metrics, and `raw_text: false`.

### Phase 3 Constraints Check

| ID | Constraint | Status | Evidence |
|----|------------|--------|----------|
| C5 | Normal processing remains offline with no external fallback | passed | Profile loader and candidate tests |
| C6 | Included components have complete inventory records and caveats | passed | 9-entry validated inventory |
| C7 | Performance claims use fixed corpora and explicit thresholds | passed | Small/medium benchmark artifact |
| C8 | New Python code has required docstrings | passed | Documentation AST gate |
| C9 | Derived indexes remain rebuildable and path-safe | passed | Corrupt-index/replacement tests |

### Superseded Phase 3 Status

`superseded` -- Phase 3 complete; later phases are recorded below.

## Phase 4 Run/Resume (2026-08-13)

- Resumed explicitly with `/cg-work phase4` on branch `cr-lit-review`.
- Artifact preflight passed: `cg-render-artifact --validate-only`.
- Active deviation policy: `autonomous` (no runtime override).
- Steps 11-13 completed on 2026-08-13; Phase 1-3 evidence remains unchanged.
- FastAPI/httpx/uvicorn were added to the locked environment and inventory with
  runtime-network-disabled caveats.

### Phase 4 Evidence

| ID | Step | Evidence | Status | Artifact |
|----|------|----------|--------|----------|
| V8 | 11 | Original-authority verification and confidence transitions cover exact, stale, typed-review, and abstained outcomes | passed | 7 verifier/confidence tests; full package regression passed |
| V9 | 12-13 | Loopback API and browser review flow preserve canonical YAML, transactions, history, and no-network behavior | passed | 5 API + 2 browser tests; full package regression passed |

## Phase 5 Run/Resume Results (2026-08-13)

### Phase 5 Evidence

| ID | Step | Evidence | Status | Artifact |
|----|------|----------|--------|----------|
| V10 | 14 | CR workflow preserves P0 enforcement, quarantines legacy external rows, and leaves CG-only projects unaffected | passed | 4 CR integration tests; 169 CR/module/target tests; regenerated native targets |
| V11 | 15 | Runtime rejects remote hosts/URLs, blocks outbound network and hidden downloads, loads models offline, and rejects forbidden subprocesses | passed | 6 executable security tests; 112-test package suite; browser no-external-request checks |
| V12 | 16 | Fixed-corpus performance and reproducibility thresholds are met or visible candidate-profile failures are recorded | passed | Existing small/medium benchmark report plus `reproducibility-2026-08-13.json`; lockfile hash and transaction recovery match |
| V13 | 17 | Documentation, Python tests, affected target/parity tests, docs checks, and safe Pester validation pass where available | passed | 112 package Python tests; clean target/module/drift checks; module validator; canonical Pester runner passed with 0 failures and no filtered files; two unrelated release-fixture assertions documented below |

### Completed Phase 5 Steps

- Step 14: complete (2026-08-13) -- CR evidence/provenance and lifecycle skills,
	`/cr-work`, and `/cr-review` document the local workbench boundary. Existing
	`/cr-work` remains the launcher; no `/cr-evidence` command was added.
- Step 15: complete (2026-08-13) -- executable security tests cover remote URL/
	browser targets, proxy/socket boundaries, model-loader download flags,
	forbidden subprocesses, safe YAML handling, injected source text, and browser
	external-request absence.
- Step 16: complete (2026-08-13) -- final reproducibility manifest records lockfile
	hash, repeated source IDs/rankings, canonical YAML hash, and transaction
	recovery without raw corpus text. Existing fixed small/medium lexical thresholds
	remain passed.
- Step 17: complete (2026-08-13) -- reference documentation, package README,
	inventory, CR canonical assets, generated native targets, module validation,
	docs contracts, and final test gates are synchronized.

### Phase 5 Constraints Check

| ID | Constraint | Status | Evidence |
|----|------------|--------|----------|
| C2 | Legacy external records remain quarantined and read-only | passed | CR integration contract and compatibility regression |
| C4 | Canonical writes are journaled, locked, revisioned, and recoverable | passed | API/lifecycle/transaction recovery tests |
| C5 | Normal processing remains loopback-only and offline | passed | Security harness, API bind gate, browser same-origin checks |
| C6 | Included components have complete inventory records and caveats | passed | 12-entry validated inventory |
| C7 | Performance/reproducibility claims use fixed inputs and explicit metadata | passed | Benchmark and reproducibility artifacts |
| C8 | New Python code has required docstrings | passed | Documentation AST gate in full package suite |
| C9 | Canonical/derived state and generated targets remain path-safe | passed | Target path/ownership/drift checks and API/browser tests |
| C10 | Required checks are executed rather than inferred | passed | V10-V13 command evidence above |
| C11 | Pester uses only the safe runner | passed | Canonical runner: passed, 0 failures, filteredFiles null |

### Final Remaining Uncertainty

- Starlette emits a deprecation warning that its TestClient/httpx integration will
	change; tests remain green and the warning is documented for future dependency
	maintenance.
- The broader repository Python suite retains two pre-existing release-fixture
	assertion failures in `scripts/tests/test_release_gate_targets.py`; no release
	files were changed by this work.
- The artifact-view evidence validator reports a pre-existing stale brainstorm-view
	SHA-256 in `.cg-docs/work-reports/2026-07-31-dual-audience-workflow-artifact-views.design-evidence.json`.

### Final Status

`completed`

## Completion Handoff (2026-08-13)

- Plan marked `completed` with `completed-date: 2026-08-13`.
- Matched roadmap feature `cr-local-evidence-workbench-for-verifiable-research-claims` marked `done` through `@cg-roadmap`.
- Milestone `responsible-research-partner` remains in progress because other
	features are not complete.
- Recommended follow-up: `/cr-review` for research-integrity/provenance review;
	engineering routing is high-risk `full` if `/cg-review` is also requested.

### Superseded Phase 4 Steps

- Step 11: complete (2026-08-13) -- context-aware verification now checks source
	identity/version/hash, exact normalized quotes, cross-unit and fuzzy diagnostics,
	typed review-required units, stale sources, inaccessible originals, and legacy
	locators. Only unchanged exact prose can reach high confidence automatically.
- Step 12: complete (2026-08-13) -- loopback-only FastAPI routes cover health,
	scan, search, source context, candidate evidence, review actions, history,
	recovery, run status, deterministic conflicts, and canonical transaction writes.
- Step 13: complete (2026-08-13) -- derived responsive HTML review flow covers
	inventory, search, candidate evidence, review queue/history, run status, and
	dependency caveats using same-origin API calls only.

### Superseded Phase 4 Constraints Check

| ID | Constraint | Status | Evidence |
|----|------------|--------|----------|
| C2 | Legacy external records remain quarantined and read-only | passed | Full package compatibility regression |
| C4 | Canonical writes are journaled, locked, revisioned, and recoverable | passed | API mutation/history/conflict tests plus transaction regression |
| C5 | Normal processing remains loopback-only and offline | passed | App bind rejection, no external UI URLs, OCR/profile network gates |
| C6 | Included components have complete inventory records and caveats | passed | 12-entry validated inventory |
| C8 | New Python code has required docstrings | passed | Documentation AST gate |
| C9 | Browser/API state remains derived and canonical files remain path-safe | passed | API/YAML mutation and browser smoke tests |

### Superseded Phase 4 Remaining Uncertainty

- Starlette emits a deprecation warning that its TestClient/httpx integration will
	change; tests remain green, but a future dependency update should revisit the
	local API test client choice.

### Superseded Phase 4 Status

`superseded` -- Phase 4 complete; Phase 5 is the terminal phase below.

## Superseded Phase 5 Initialization Snapshot (2026-08-13)

- Resumed explicitly with `/cg-work phase5` on branch `cr-lit-review`.
- Artifact preflight passed: `cg-render-artifact --validate-only`.
- Active deviation policy: `autonomous` (no runtime override).
- This initialization snapshot is superseded by the final Phase 5 results above.
- Existing `/cr-work` is sufficient as the workbench launcher; no new
	`/cr-evidence` prompt is being added.

### Phase 5 Evidence

| ID | Step | Evidence | Status | Artifact |
|----|------|----------|--------|----------|
| V10 | 14 | CR workflow preserves P0 enforcement, quarantines legacy external rows, and leaves CG-only projects unaffected | passed | See final Phase 5 results above |
| V11 | 15 | Runtime rejects remote hosts/URLs, blocks outbound network and hidden downloads, loads models offline, and rejects forbidden subprocesses | passed | See final Phase 5 results above |
| V12 | 16 | Fixed-corpus performance and reproducibility thresholds are met or visible candidate-profile failures are recorded | passed | See final Phase 5 results above |
| V13 | 17 | Documentation, Python tests, affected target/parity tests, docs checks, and safe Pester validation pass where available | passed | See final Phase 5 results above |
