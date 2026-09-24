---
name: cr-skill-evidence-provenance
module: research
description: "Evidence and provenance protocol for CR tasks that ingest documents,
  justify methods, or produce cited claims. Defines analysis/composition split,
  claim-evidence and provenance schemas, repo-local corpus defaults, and
  anti-hallucination enforcement."
---

# CR Evidence and Provenance

Reference skill for evidence-traceable research outputs. Load when a task uses
sources, makes cited claims, or justifies methodological choices from evidence.

---

## Creation Date

- 2026-07-30

---

## Analysis and Composition Split

Separate source analysis from prose composition.

- Analysis stage creates a verified claim-evidence matrix.
- Composition stage may only use claims with `status: verified`.
- If a claim is not verifiable, mark `unverified` or `abstained`; do not invent.

This split is mandatory for empirical and methodological claims.

---

## Repo-Local Corpus Default

Default evidence corpus is files already inside the working repository.

- `origin: repo-local` is default.
- External search/use is opt-in and must be explicitly flagged.
- External items require: `origin: external-opt-in` and `external_flag: true`.

If external origin is used without flagging, treat as a workflow violation.

---

## Original-Document Authority and Ingestion

The original source file is the authority.

- Keep authority pointer in `original_path`.
- Converted text is an indexing aid, not canonical evidence.
- Record `sha256` of the original and `conversion_tool` used.
- Ingestion is tool-agnostic. `markitdown` may be used, but is optional.

---

## Provenance Ledger Schema

Path:
- `.cg-docs/research/evidence/provenance-ledger.yaml`

Schema:
```yaml
sources:
  - id: S003
    title: "..."
    authors: ["..."]
    year: 2020
    origin: repo-local
    original_path: "data/refs/source.pdf"
    converted_path: ".cg-docs/research/evidence/converted/source.md"
    conversion_tool: "markitdown@x.y"
    sha256: "<hash-of-original>"
    external_flag: false
    ingested_on: 2026-07-30
```

Required fields: `id`, `origin`, `original_path`, `sha256`, `external_flag`.

---

## Claim-Evidence Matrix Schema

Path:
- `.cg-docs/research/evidence/claim-evidence-matrix.yaml`

Schema:
```yaml
claims:
  - id: C001
    statement: "..."
    type: empirical
    status: verified
    evidence:
      - source_id: S003
        locator: "Table 2, p. 14"
        quote: "..."
        supports: true
    verified_by: cr-provenance-audit
    verified_on: 2026-07-30
```

Claim `type` values:
- `empirical`
- `methodological`
- `normative`

`type: methodological` is how method-justification evidence is represented.

---

## Anti-Hallucination Rules

Never fabricate:
- source existence
- DOI
- quote text
- page/locator
- verification status

If evidence cannot be verified:
- set claim status to `unverified` or `abstained`
- flag the issue for correction
- avoid plausible completion language

Quotes must be verbatim from the converted artifact tied to `source_id`.

---

## Verification Depth by Review Tier

Light:
- Schema validity checks
- Spot-check sampled claim/source links

Standard:
- Every substantive claim has at least one verified source
- Locators resolve to cited converted artifacts

Thorough:
- Verbatim quote checks
- Locator-to-page resolution checks against source-derived artifacts
- Cross-check provenance consistency (`origin`, `external_flag`, `sha256`)

---

## Artifact Layout

Evidence artifacts live under:
- `.cg-docs/research/evidence/provenance-ledger.yaml`
- `.cg-docs/research/evidence/claim-evidence-matrix.yaml`
- `.cg-docs/research/evidence/converted/`

Create directories on demand during `/cr-work` when absent.

---

## Anti-Patterns

- Writing results text before evidence mapping is complete
- Treating converted markdown as authority over original files
- Mixing external sources into repo-local mode without explicit flags
- Assigning `verified` without resolvable source and locator
