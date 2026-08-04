---
name: cg-skill-wb-report-writing
user-invokable: false
description: "Progressive-disclosure skill for World Bank institutional report writing. Routes by operation and document type for drafting, expansion, revision, summarization, adaptation, quality review, and end-to-end production across PRWPs, policy briefs, executive summaries, flagship sections, country or regional narratives, technical methodology notes, internal memos, and data blog posts. Enforces source integrity, marker grammar, and should-not-trigger boundaries for non-English or unsupported full Quarto requests."
---

# World Bank Institutional Report-Writing

Use this skill to produce source-grounded institutional prose for World Bank
outputs while preserving verification status and safety guardrails.

Do not load all references. Load only the shared files plus the one requested
operation and document type.

## Shared Files (always load)

- [references/safety-and-markers.md](references/safety-and-markers.md)
- [references/style-conventions.md](references/style-conventions.md)

## Conditional Shared Files

- [references/workflows.md](references/workflows.md) for operation routing.
- [references/terminology.md](references/terminology.md) when terminology,
  disclaimers, or unresolved language needs checking.
- [references/quality-review-checklist.md](references/quality-review-checklist.md)
  for quality review and final QA passes.

## Router Protocol

1. Identify operation: draft, expand, revise, summarize, adapt, quality review,
   or end-to-end production.
2. Confirm source/data status before writing prose:
   user-cleared inputs, verifiable citations, approved exemplars, or placeholder.
3. Run source pack preflight for the requested type:
   2-3 approved exemplars, intended audience, required terminology,
   required disclaimers, and source links.
4. If preflight fails, return a missing-input list and stop for that type.
5. If preflight passes, continue using shared references in this phase.
   Type-specific `references/<type>.md` files are added by child plans.

## Supported Document Types

- policy-research-working-paper (PRWP)
- policy-brief (policy brief)
- executive-summary (executive summary)
- flagship-report-section (flagship report section)
- country-analytical-narrative (country or regional narrative)
- technical-methodology (technical methodology)
- internal-memo (internal memo)
- data-blog-post (data blog post)

## Safety Boundaries

- Never invent figures, dates, citations, or institutional positions.
- Never silently upgrade placeholder content into verified claims.
- Carry safety markers across summarization and document conversion.
- Preserve sensitive country terminology checks from approved sources.

## Trigger Boundaries

Trigger when the request is about World Bank institutional report writing for
one of the supported operations and document types.

Should not trigger for near misses:
- generic creative writing unrelated to institutional reports
- non-English output requests
- unsupported full Quarto code execution or data binding workflows
- requests to fabricate citations or unverified Bank positions

## Scope Notes

- English output only.
- Markdown and basic .qmd structure or prose only.
- Citation structure in Quarto mode only when a verifiable .bib source exists.
- Unsupported capabilities must return explicit defer or reject guidance.
