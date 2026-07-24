---
date: 2026-07-23
title: "World Bank institutional report-writing skill"
status: decided
scope: "Standard"
chosen-approach: "Phased skill with per-document-type reference files"
tags: [skill, writing, institutional, world-bank, report-writing, quarto]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# World Bank Institutional Report-Writing Skill

## Context

The roadmap feature `world-bank-institutional-report-writing-skill` under the **Skills Enhancement** milestone needs requirements discovery before implementation. The goal is a future skill that helps draft institutional World Bank documents — reports, policy notes, executive summaries, analytical documents, and blog posts — with appropriate tone, structure, safety guardrails, and institutional conventions.

## Requirements

### Document Types (all in scope for v1)

1. **Policy Research Working Papers (PRWPs)** — formal academic-style, methodology-heavy
2. **Policy Notes / Briefs** — 2–4 pages, distilled for decision-makers
3. **Executive Summaries** — distilled highlights for senior management
4. **Flagship Report Sections** — e.g., Poverty & Shared Prosperity Report prose
5. **Country/Regional Analytical Narratives** — regional context, trend interpretation
6. **Technical/Methodology Documentation** — methodology annex-style content
7. **Internal Memos / Decision Notes**
8. **Data Blog Posts** — World Bank Data Blog style, accessible storytelling

### Skill Users and Document Readers

- **Skill users**: Compound GPID users who also write institutional documents (not just code)
- **Document readers**: Same audiences that currently read each document type (policymakers for briefs, academics for Working Papers, general public for Data Blog, senior management for executive summaries, etc.)
- Each document type gets its own writing pattern in `references/` — tone, depth, structure, and formality calibrated to the specific reader audience

### Skill Structure

- Single `SKILL.md` + multiple reference files in `references/` for specific document types/tasks (consistent with other Compound GPID skills)
- Creation via `.agents/skills/skill-creator` (`/create-skill`) when implementation begins

### Operations (all v1)

1. **Drafting from scratch** — given document type + topic + data, produce a first draft
2. **Section expansion** — given bullet points or outline, expand into institutional prose
3. **Revision/editing** — take existing text and improve (tighten, formalize, WB tone alignment)
4. **Summarization** — condense a long document into an executive summary or blog post
5. **Translation between document types** — convert Working Paper section into policy brief, technical section into blog post
6. **Quality review** — check draft against WB conventions and flag issues (tone violations, missing caveats, unsupported claims)
7. **End-to-end document production** — produce a complete document given sufficient inputs

### Style Authority

- **WBG Publications Editorial Style Guide (2020)** — the cross-cutting style authority for all WB publications. Supplements Chicago Manual of Style 17th ed. and Merriam-Webster's Collegiate Dictionary 11th ed.
- **Exemplar documents** — 2–3 gold-standard examples per document type, referenced by URL/path to published documents. The skill will encode tone, structure, and conventions inductively from these.
- **Terminology list** — precise institutional vocabulary definitions supplied by the user
- **Anti-patterns** — derived from exemplars (what they don't do) and flagged during skill development

### Safety Guardrails (Four Principles)

#### 1. Institutional Positions
The skill should never independently generate text that reads as an official World Bank position. However, it is legitimate for a user to instruct the skill to write *in* institutional voice, provided the user is themselves authorized to speak for that position. The distinction is between the skill *inventing* a position versus *transcribing or drafting around* a position the user supplies or points to. When a draft could plausibly be read as staking out an institutional stance that wasn't explicitly given by the user or grounded in a cited source, the skill should flag it: `[INSTITUTIONAL POSITION — confirm reflects cleared Bank guidance]`.

#### 2. Unpublished Data
If the user tells the skill the data is preliminary, pre-release, or unpublished, the skill should carry that status forward automatically into the document with visible markers like `[UNPUBLISHED — DO NOT CIRCULATE]` or `[PRELIMINARY — subject to revision]` attached to the relevant figures or sections. If the user doesn't specify status but the content is clearly the kind of thing that's typically embargoed (e.g., poverty headcount estimates ahead of a scheduled release), the skill should ask rather than assume either way.

#### 3. Country-Sensitive Content
Light-touch guardrails: flag when sensitive framing is detected (governance quality, conflict, sanctions, contested territorial descriptions) and prompt the author to confirm they're using the currently approved terminology or disclaimer language. The substantive judgment about what to say remains the author's and their management chain's call; the skill's role is procedural.

#### 4. Fabrication Boundary (Firmest Line)
The skill should **never** generate specific factual figures — poverty rates, growth numbers, dates, statistics — that were not supplied by the user or retrieved from a verifiable source. The correct behavior is to leave an explicit placeholder — `[INSERT POVERTY RATE — SOURCE NEEDED]` — rather than fill in a guessed number "for verification." A plausible-sounding but invented figure is far more dangerous than a placeholder because it's fluent and easy to mistake for real data. Reviewers catch missing numbers but not plausible-looking wrong ones.

**Key asymmetry**: Citations can be structurally generated and marked for verification. Numeric facts **cannot** — they get placeholders only.

### Three-Tier Content Marking

1. **Final prose** — ready for the document as-is
2. **Needs-verification markers** — citations, statistics, or claims the user must check (marker format TBD — likely HTML comments or Quarto callouts)
3. **Author-only annotations** — caveats, suggestions, structural notes for the writer, not the reader (distinct marker format so the user never confuses them with body text)

### Data and Statistics

- The skill should pull numbers directly from project context and data (not just prompt text)
- Quarto (.qmd) integration is a future stage but the skill should be designed for it now
- v1 handles basic `.qmd` (structure, prose, YAML frontmatter); v2 will integrate with future Quarto-specific skills for code chunks and data binding

### Citations

- In Quarto mode: use `.bib` files for references (standard academic citation workflow)
- Outside Quarto: citations may be generated but must be visibly marked as unverified
- Never let fabricated citations look like verified ones

### Format and Language

- **v1**: English only
- **v1**: Basic `.qmd` support (structure/prose, no code-chunk data-binding)
- **v2**: Full Quarto integration with future Quarto-specific skills

### Evaluation

- **Guardrail testing**: Deliberately feed the skill scenarios designed to trigger violations (ask to write about a country without providing data, state a policy position without grounding). Verify it produces placeholders/flags rather than fabrications.
- **Document-type fidelity**: For each document type, check that output matches the structural template (correct heading hierarchy, expected sections present, appropriate length, right level of technicality for the audience).
- **User acceptance**: Explicitly the user's responsibility — human revision and final editing is always assumed necessary.

### Out of Scope for v1

- Typesetting/formatting (LaTeX, Word templates)
- Automated data retrieval from PIP/APIs
- Document clearance workflow integration
- Multi-author collaboration features
- Full Quarto code-chunk data binding (deferred to v2)
- Languages other than English

## Reference Sources

### Publicly Accessible

- WBG Publications Editorial Style Guide (2020): <https://documents1.worldbank.org/curated/en/318281583390046594/txt/World-Bank-Group-Publications-Editorial-Style-Guide-2020.txt>
- Public PRWP overview page: <https://www.worldbank.org/en/research/brief/world-bank-policy-research-working-papers>
- Full PRWP catalog on RePEc/IDEAS: <https://ideas.repec.org/s/wbk/wbrwps.html>
- PRWP citation index (CitEc): <https://citec.repec.org/s/2024/wbkwbrwps.html>
- PRWP No. 10,000 blog post: <https://blogs.worldbank.org/en/developmenttalk/world-bank-research-milestone-policy-research-working-paper-no-10000>
- SciSpace PRWP journal listing: <https://scispace.com/journals/world-bank-policy-research-working-paper-30a5j1y9>
- Land and Poverty Conference paper formatting guidelines: <https://www.worldbank.org/content/dam/Worldbank/Event/DEC/Land_and_Poverty_Conference/Guidelines_and_Formatting_Instructions_for_Full_Papers.pdf>
- PSPR 2020 "Reversals of Fortune" event page: <https://www.worldbank.org/en/events/2020/11/12/poverty-and-shared-prosperity-2020-reversals-of-fortune>

### Internal (SharePoint — accessible to WB staff)

- PRWP Series homepage: <https://worldbankgroup.sharepoint.com/sites/WBPRWP/SitePages/Home.aspx>
- PRWP Series publishing/about page: <https://worldbankgroup.sharepoint.com/sites/WBPRWP/SitePages/PublishingPages/index.aspx>
- PRWP submission guidelines: <https://worldbankgroup.sharepoint.com/sites/WBPRWP/SitePages/PublishingPages/Submission-11052018-093820.aspx>
- T&C Brief Series guidelines: <https://worldbankgroup.sharepoint.com/sites/WBMFM/SitePages/PublishingPages/TC-Brief-Series-06282018-103015.aspx>
- AskWater Policy Note examples: <https://worldbankgroup.sharepoint.com/sites/WBWaterpractice/SitePages/News/AskWater-Policy-Note-11032021-141214.aspx>
- ECR Briefing Notes guidelines: <https://worldbankgroup.sharepoint.com/sites/ecr/SitePages/PublishingPages/Guidelines-1737745701884.aspx>
- PSPR 2022 "Correcting Course" release announcement: <https://worldbankgroup.sharepoint.com/sites/WBPoverty/SitePages/News/JUST%20RELEASED%20-%20Pove-1665073149927.aspx>
- PSPR 2019 project page: <https://worldbankgroup.sharepoint.com/sites/commnet/SitePages/SystemPages/Detail.aspx/Documents/mode=view?_Id=1867&SiteURL=/sites/commnet>
- "Shared Prosperity Paving the Way in Europe and Central Asia": <https://worldbankgroup.sharepoint.com/sites/WBECA/SitePages/PublishingPages/Shared%20prosperity%20paving%20the%20way%20in%20Europe%20and%20Central%20Asia.aspx>

### Key Style Guide Findings

The WBG Publications Editorial Style Guide (2020) is the cross-cutting style authority. Key conventions:

- **Primary references**: Supplements Chicago Manual of Style 17th ed. and Merriam-Webster's Collegiate Dictionary 11th ed.
- **Citation style**: Author-date preferred (e.g., `(Smith 2019, 23)`)
- **Serial comma**: Required
- **Numbers**: Spell out one through nine; numerals for 10 and above, percentages, physical quantities, and monetary amounts
- **Dates**: Month-day-year format (e.g., December 10, 2019)
- **Country names**: Must follow approved World Bank Corporate Secretariat list (Appendix C)
- **Currency**: Specific formatting per country (Appendix D); "US$" with no space before amount
- **Abbreviations**: Spell out at first occurrence in each chapter/box, even if used only once
- **Headings**: Headline-style capitalization; no more than four levels; must be self-contained
- **Figures**: Every figure must have number, title (What + Where + When), and source line
- **Tables**: No blank cells (use — for not available, n.a. for not applicable, .. for negligible, 0 for zero)
- **Source lines**: "Authors" must not be used as a source; use "World Bank" or specific data source
- **Boxes**: Maximum 700 words; self-contained lettering for notes
- **Maps**: Must clear Cartography Unit; specific country name conventions
- **Approved terms**: Appendix F has extensive list (e.g., "policy maker" two words, "indexes" not "indices", "toward" not "towards")
- **Words to avoid**: Appendix G lists alternatives (e.g., "utilize" → "use", "endeavor" → "try", "prior to" → "before")
- **Publishing categories**: Premium (flagships), Basic (ASA), Knowledge (short papers)

## Approaches Considered

### Approach 1: Phased skill with per-document-type reference files (Chosen)

**Summary**: Build a single `SKILL.md` with core guardrails and dispatch logic, plus one `references/` file per document type, implemented in phases.

**Pros**:
- Each document type gets dedicated depth in its own phase
- Modular — new document types can be added without changing the core
- Consistent with existing Compound GPID skill architecture
- Phasing mitigates risk of shallow/generic coverage

**Cons**:
- Large total surface area (10+ reference files)
- Exemplars needed for each type before that phase can begin

**Effort**: Large (phased across multiple iterations)

**Recommended?**: Yes — the phased approach addresses the breadth-vs-depth concern while covering all document types.

### Approach 2: Core-only skill (considered, not chosen)

**Summary**: Build only the `SKILL.md` with universal WB style rules and guardrails, no per-type reference files.

**Pros**: Simpler, faster to ship
**Cons**: Generic — wouldn't differentiate between a blog post and a Working Paper
**Effort**: Medium
**Recommended?**: No — the per-type calibration is a core requirement.

## Decision

**Chosen: Approach 1 — Phased skill with per-document-type reference files.**

The phased plan (one reference file per document type per phase, plus cross-cutting phases for testing, Quarto integration, and setup) prevents genericness while covering all eight document types. Each phase delivers a usable increment.

### Proposed Skill Architecture

**Name**: `cg-skill-wb-report-writing`

**Core file**: `SKILL.md`
- When to load (trigger conditions for each document type)
- The four safety guardrails
- Three-tier content marking conventions
- Universal WB style rules (distilled from Editorial Style Guide)
- Dispatch logic to per-type reference files

**Per-type references**:
- `references/policy-research-working-paper.md`
- `references/policy-brief.md`
- `references/executive-summary.md`
- `references/flagship-report-section.md`
- `references/country-analytical-narrative.md`
- `references/technical-methodology.md`
- `references/internal-memo.md`
- `references/data-blog-post.md`

**Cross-cutting references**:
- `references/style-conventions.md` — distilled WBG Editorial Style Guide rules
- `references/terminology.md` — institutional vocabulary definitions
- `references/quality-review-checklist.md` — what to check during quality review

## Next Steps

1. **`/cg-plan`** — Turn this brainstorm into a phased implementation plan using `/create-skill`
2. Gather exemplar documents for the first batch of document types (user to supply URLs/paths)
3. Compile the terminology list (user to supply)
4. Decide on marker format (HTML comments vs. Quarto callouts vs. custom brackets) during planning
