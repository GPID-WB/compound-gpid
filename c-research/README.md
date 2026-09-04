<!-- Created 2026-09-02. -->

# c-research

`c-research/` is the canonical project-level workspace for research outputs
produced for a research question or study. It is used by human researchers and
by the Compound Research (CR) workflows and agents.

This workspace is organized by artifact type:

```text
c-research/
├── evidence/              # source-backed evidence and provenance records
├── manuscripts/           # working papers, sections, abstracts, responses
├── normative-decisions/   # per-study human decisions on value-laden choices
├── scoping/               # research-question and study scoping memos
├── derivations/           # mathematical model derivations
├── specifications/        # theory-data and specification decision trails
├── results/               # estimation manifests and result records
├── replication/           # replication-package output and documentation
├── eda/                   # research-framed exploratory analysis outputs
├── measurement/           # measurement and classification diagnostics
└── vintages/              # version, coverage, and comparability records
```

## Ownership boundary

Only research outputs belong here. Project inputs belong elsewhere. In
particular, `data/` is separate input storage and is not created or migrated by
Compound GPID. Source documents, code, and other inputs remain in their
project-owned locations unless a particular file is itself a research output.

Compound GPID process and knowledge records remain under `.cg-docs/`, including
brainstorms, plans, reviews, solutions, strategy records, work reports, the
shared `evidence-fixtures/` publishing tests, the `inbox/` strategy holding
area, and generated `views/`. These are not moved into `c-research/`.

The generic Compound GPID Brain indexes `.cg-docs/` process and knowledge
records. CR workflows read and write `c-research/` directly; this directory is
not silently added to the generic Brain.

When the `cr` suite is active, setup creates the artifact-type directories as
needed. Disabling `cr` never deletes an existing `c-research/` workspace or its
research outputs.

The legacy-layout migrator is fail-closed: reserved input directories such as
data, raw, source, and code are never migrated, and every legacy file requires
an explicit `--allow-output <project-relative-path>` approval. Unresolved
destination conflicts and live legacy references block migration.

Normal research processing is local-only: no internet search or URL fetching is
allowed. No external API model execution is allowed.
