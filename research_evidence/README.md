# Research Evidence Workbench

Created: 2026-08-12

This package is the local-first implementation boundary for Compound Research's
claim/evidence workflow. Phase 1 covers Markdown resources, deterministic local
lexical search, exact quote verification, and journaled YAML persistence.

## Runtime

- Supported Python: `>=3.11,<3.14`
- Dependency resolution: `uv` with the committed `uv.lock`
- Normal processing: offline, project-contained, and loopback-only
- Model loading: local-cache-only; setup-time acquisition is a separate future
  operation and is never triggered by scanning or review

Set up the package with:

```text
uv sync --project research_evidence
uv run --project research_evidence research-evidence --help
uv run --project research_evidence pytest -q
```

The configured resources root must be inside the project root. URL resources,
remote hosts, hidden downloads, telemetry, and external model/API fallbacks are
rejected. Original resources remain authoritative; YAML records and review
history are canonical, while indexes and other runtime caches are derived.

## Format and OCR boundary

Phase 2 parses PDF, DOCX, Markdown, LaTeX, and HTML resources into typed source
units. Page, paragraph, table-row, block, heading, anchor, equation, and other
locators are retained. Tables and equations are marked review-required rather
than treated as ordinary prose. Image-only PDFs expose an explicit OCR
requirement; the OCR profile is local and inventory-controlled, and OCR output
is always low-confidence until the original page is independently verified.
No OCR engine is downloaded or contacted during normal processing.

Optional dense, sparse, and reranking adapters are candidate-only in Phase 3.
They require a complete inventory record, verified local cache, declared
latency/memory budgets, and explicit activation before execution. No model
weights are selected or acquired by the default profile; lexical retrieval stays
the baseline.

## API and browser boundary

Phase 4 provides a loopback-only FastAPI service and derived browser review page.
The service exposes resource scan, source search/context, candidate evidence,
review actions, history, recovery, and run status. All mutations use the
journaled canonical YAML transaction path. The browser page uses same-origin
API calls and is never canonical; original files, YAML records, and append-only
history remain authoritative. FastAPI/httpx/uvicorn are inventory-controlled and
runtime network access remains disabled.

## Dependency inventory

Every package, parser, executable, model, and weight distribution is recorded in
`.cg-docs/research/evidence/dependency-model-inventory.yaml` before activation.
Inventory entries disclose exact versions, source, license/access terms, network
behavior, telemetry notes, platform support, enterprise-review status, rationale,
and caveats. `candidate` and `blocked` entries cannot run. A restricted component
requires a visible caveat and explicit local activation acknowledgement.

## Phase 1 layout

```text
research_evidence/
├── pyproject.toml
├── uv.lock
├── src/research_evidence/
└── tests/

.cg-docs/research/evidence/
├── provenance-ledger.yaml
├── source-records.yaml
├── evidence-records.yaml
├── claim-evidence-matrix.yaml
├── review-history.yaml
└── runs/
```

No browser UI, internet search, external citation retrieval, or external API
model execution is part of v1.
