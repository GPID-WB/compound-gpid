---
created: "2026-07-30"
status: "design note"
tags:
  - academic-research
  - agentic-workflow
  - provenance
  - document-ingestion
---

# Reusable Patterns for an Academic-Research AI Harness

This note extracts three reusable design ideas from the AI Readiness reporting pipeline:

1. Separate analysis from composition.
2. Convert source documents into machine-readable Markdown before asking agents to reason over them.
3. Treat scholarly search, retrieval, and citation as a specialized provenance and verification workflow.

The central principle is that the harness should distinguish **what the sources support** from **how that support is expressed in a paper**. A fluent draft is not evidence that the underlying research is correct.

## 1. Analysis and Composition for Academic Writing

An academic-research harness should use two deliberate phases with a human or automated verification checkpoint between them.

### Phase A: Analysis

Analysis agents read the research materials and produce structured, evidence-linked artifacts rather than polished prose. Depending on the project, these artifacts can include:

- research questions and hypotheses;
- definitions of concepts, variables, and populations;
- claims made by each source;
- methods, data, identification assumptions, and estimands;
- reported results and uncertainty measures;
- limitations, boundary conditions, and author qualifications;
- competing explanations and disagreements across papers;
- exact quotations or paraphrases linked to source locations;
- a bibliography record with verified metadata; and
- a claim-to-evidence matrix showing which sources support, qualify, or contradict each claim.

The analysis phase should preserve uncertainty. An agent should be able to record `unverified`, `unclear`, `not reported`, and `conflicting evidence` rather than filling gaps with plausible language.

The outputs should be structured, for example as YAML or JSON, and should include stable identifiers for sources, claims, and evidence passages. A simplified claim record might look like:

```yaml
claim_id: claim-014
claim: "The estimated effect is positive under the authors' preferred specification."
source_id: source-003
evidence:
  - evidence_id: source-003-p12-e02
    page: 12
    locator: "Table 4, column 3; paragraph below the table"
    support_type: reported_result
    quotation: "..."
    verification_status: verified
caveats:
  - "The estimate is conditional on the paper's identifying assumptions."
status: reviewed
```

### Checkpoint: Evidence Review

Before composition, a reviewer should be able to inspect and correct the structured artifacts. At minimum, the checkpoint should verify:

- every substantive claim has one or more source links;
- source metadata and publication status are verified;
- page numbers and locators point to the original document;
- quotations match the source exactly;
- paraphrases do not strengthen the source's claim;
- methods and limitations have not been omitted;
- conflicting findings are represented; and
- unsupported or unresolved claims are marked for removal or further research.

This checkpoint is the boundary between an evidence base and a draft. Composition should not silently repair missing evidence.

### Phase B: Composition

Composition agents consume only the reviewed analysis artifacts, approved source records, and an explicit writing brief. They can then produce:

- a literature review;
- a research memorandum;
- a methods or identification section;
- a results narrative;
- a policy or research synthesis; or
- a complete paper draft.

Composition should transform verified material into an argument, but should not invent sources, results, methods, quotations, page numbers, or certainty. Citations should be generated from source identifiers and evidence records, not from free-form model memory.

A quality-review agent should compare the draft back to the analysis artifacts and report unsupported claims, citation mismatches, omitted caveats, overstatements, and references that cannot be verified. This makes selective revision possible without repeating the entire research process.

### Suggested Agent Boundary

A useful division of responsibility is:

| Agent | Main responsibility | Structured output |
| --- | --- | --- |
| Research planner | Refine the question, scope, and search criteria | `research-plan.yaml` |
| Scholarly source finder | Discover candidate papers and record provenance | `source-candidates.yaml` |
| Source verifier | Check identity, publication status, metadata, and accessibility | `verified-sources.yaml` |
| Document ingester | Download and normalize approved documents | Markdown plus `document-manifest.yaml` |
| Paper analyst | Extract methods, claims, findings, caveats, and evidence locations | `paper-analysis.yaml` |
| Synthesis analyst | Compare sources and construct the claim-evidence matrix | `evidence-synthesis.yaml` |
| Academic writer | Compose from reviewed artifacts | Quarto Markdown or Markdown draft |
| Citation auditor | Check every citation and page locator against source files | `citation-review.yaml` |

The names are illustrative. The important boundary is that the writer is downstream of structured evidence and does not serve as the primary source-discovery or fact-verification agent.

## 2. Converting Documents to Machine-Readable Markdown

Research papers, working papers, reports, theses, appendices, and supplementary files should be normalized before analysis. Machine-readable Markdown gives agents a consistent representation that is easier to search, chunk, cite, and review than a mixture of PDFs, Word files, scanned pages, and web pages.

### Preferred Tool: Microsoft `markitdown`

The research harness should prefer Microsoft's [`markitdown`](https://github.com/microsoft/markitdown) for document-to-Markdown conversion. It supports common office and document formats and provides a practical normalization layer for a mixed research library.

A local ingestion command can follow this pattern:

```bash
uv run markitdown "sources/source-003/original.pdf" \
  -o "sources/source-003/document.md"
```

The exact command should be confirmed against the installed version and file type. Conversion should happen locally where the source material is confidential or access-controlled.

### Preserve the Original and Its Provenance

Conversion is a derived representation, not a replacement for the source. For every document, retain:

- the original downloaded file, preferably with a cryptographic hash;
- the converted Markdown file;
- the canonical landing-page URL and direct download URL;
- retrieval timestamp;
- title, authors, year, venue, DOI, repository identifier, and version;
- document type and version, such as preprint, working paper, accepted manuscript, or published article;
- the converter and version used;
- conversion warnings or failures; and
- a page or section map used for later citation verification.

A manifest entry could look like:

```yaml
source_id: source-003
original_file: original.pdf
markdown_file: document.md
sha256: "..."
landing_url: "https://doi.org/..."
download_url: "https://.../article.pdf"
retrieved_at: "2026-07-30T14:25:00Z"
document_version: "published_version"
converter:
  name: markitdown
  version: "..."
page_count: 28
page_mapping_status: verified
```

### Page Preservation Is a Separate Requirement

Markdown conversion may preserve headings and text order without preserving reliable PDF page boundaries. This matters because a citation such as `(Author, 2024, p. 12)` is a claim about the original document, not merely about the converted text.

Therefore:

1. Keep the original PDF immutable.
2. Assign page-aware identifiers while extracting or reviewing text, such as `source-003-p12-e02`.
3. Store the page number and a short locator with every citation-worthy passage.
4. Verify the passage against the original PDF before marking it `verified`.
5. Treat a page number inferred only from Markdown offsets as unverified.

If `markitdown` output does not contain dependable page markers, create a separate page-indexed derivative during ingestion. That derivative can contain explicit markers such as `<!-- page: 12 -->` while retaining the ordinary Markdown file for general analysis. The original PDF remains the authority for the final check.

For scanned documents, OCR quality should be recorded. A quotation from a low-confidence OCR region should require manual verification or a visual review of the original page.

## 3. Specialized Workflow for Rigorous Scholarly Search and Citation

Finding a paper is not the same as verifying a paper. A general web-search agent can return plausible-looking but unsuitable results, confuse versions, misstate publication status, or fabricate a citation when it cannot access the source. Scholarly retrieval should therefore be an explicit workflow with separate discovery, verification, download, conversion, analysis, and citation-audit steps.

### Step 1: Define the Research Need

The research planner should turn the user's request into searchable criteria:

- research question and key concepts;
- population, setting, period, and geography;
- study design or identification strategy of interest;
- acceptable evidence types;
- minimum source-quality requirements;
- whether working papers or preprints are acceptable;
- required language and access constraints; and
- date range or version requirements.

This prevents the search agent from selecting papers merely because their titles contain familiar words.

### Step 2: Discover Candidate Sources

The source finder should search reputable scholarly channels appropriate to the field, such as:

- publisher and journal websites;
- DOI registration and metadata services;
- established disciplinary repositories;
- university repositories;
- recognized working-paper series;
- bibliographic indexes; and
- institutional or intergovernmental research libraries where relevant.

Search results are **candidates**, not evidence. The agent should record the exact query, search service, result URL, access date, and reason for selection. It should never create a bibliography entry from a title-like snippet alone.

### Step 3: Verify Academic Identity and Quality

A source verifier should confirm the paper using at least one authoritative record and, where feasible, a second corroborating record. Checks should include:

- title, author list, year, and venue match;
- DOI or stable repository identifier;
- journal or series identity;
- publication status and document version;
- whether the source is peer-reviewed, a working paper, a preprint, a report, or an opinion piece;
- whether the document is actually available at the claimed URL; and
- whether the paper is relevant to the defined research need.

The harness should prefer reputable publications or sources, but should not convert reputation into an unsupported binary score. It should record the basis for the classification and distinguish peer-reviewed evidence from credible but non-peer-reviewed research.

A candidate should be rejected or held for review when:

- the citation cannot be independently verified;
- author, title, or venue information conflicts across records;
- only a search snippet is available;
- the supposed paper is not downloadable from a trustworthy source;
- the source is clearly outside the requested academic scope; or
- the agent cannot determine which version is being cited.

The system should return an explicit `not_verified` result rather than fill in missing metadata.

### Step 4: Download and Preserve the Exact Source

After verification, download the source from the most authoritative accessible location. Store it in a source-specific directory with a stable identifier. Do not overwrite a prior version silently. If a published article, accepted manuscript, and preprint are all available, preserve their relationships and state which version is used for citation.

Record the download response, file hash, URL, retrieval time, and any access or licensing restrictions. A failed or partial download must not be passed to the analysis agent as if it were a complete paper.

### Step 5: Convert and Index Locally

Run `markitdown` on the preserved source, write the Markdown derivative, and create the document manifest. Then index the Markdown by headings, page markers, tables, figures, footnotes, and paragraph or block identifiers. Tables and footnotes need special attention because their meaning can be lost when text is flattened.

The ingester should report conversion warnings, missing pages, OCR use, and unsupported elements. A paper with an incomplete conversion may still be useful, but its analysis and citation status must reflect that limitation.

### Step 6: Extract Evidence Before Writing

The paper analyst should extract only what can be located in the source:

- research question and contribution;
- data and sample;
- model or empirical design;
- assumptions and identification argument;
- estimates, uncertainty, and robustness results;
- limitations and external-validity qualifications; and
- exact passages supporting important claims.

Each extracted item should carry a source ID, page number, locator, evidence type, and verification status. The analyst should distinguish the authors' claims from the harness's interpretation.

### Step 7: Cite and Audit at Page Level

The harness should support page-level citation as a verified evidence link, not as a page number generated from model memory.

The writer should cite using evidence records, for example:

```yaml
citation:
  source_id: source-003
  locator:
    page: 12
    section: "Results"
    detail: "Table 4, column 3 and the paragraph immediately below"
  status: verified
```

The citation auditor should then:

- resolve every source ID to one manifest entry;
- confirm that the cited page exists in the original file;
- locate the quoted or paraphrased passage;
- compare quotations character-for-character apart from documented normalization;
- check that the paraphrase has not added stronger causal language;
- check that the cited version matches the bibliography; and
- flag citations that point only to a search result, abstract, metadata page, or inaccessible derivative.

A citation should be rendered as verified only after this check. Where exact page verification is impossible, the draft should say so internally and use a lower-confidence status rather than inventing a page number.

## Anti-Hallucination and Provenance Rules

The academic harness should enforce the following rules in prompts, schemas, validators, and review agents:

- Never invent a paper, author, journal, DOI, URL, quotation, result, or page number.
- Never treat a search-result snippet as proof of a paper's content.
- Never infer publication status from a domain name or title alone.
- Never merge metadata from different versions without recording the relationship.
- Never cite a source that was not downloaded or otherwise directly verified.
- Never present an unverified page locator as exact.
- Preserve negative search results and unresolved candidates so users can see what remains unknown.
- Require explicit evidence links for substantive claims.
- Keep the original files and derived Markdown under versioned or auditable storage.
- Log source discovery queries, retrieval dates, converter versions, and validation outcomes.
- Prefer abstention and a review flag over a plausible completion when evidence is missing.

## Recommended End-to-End Flow

```text
Research question and scope
        |
        v
Search plan -> candidate sources -> metadata and publication verification
                                      |
                           reject / hold / approve
                                      |
                                      v
                         download original + manifest
                                      |
                                      v
                   markitdown conversion + page-aware index
                                      |
                                      v
                    paper analysis and evidence extraction
                                      |
                                      v
                human or automated evidence-review checkpoint
                                      |
                                      v
                  synthesis, argument design, and composition
                                      |
                                      v
                       citation audit and quality review
                                      |
                                      v
                      final paper or research memorandum
```

This design preserves the useful separation from the AI Readiness pipeline while adapting it to a harder scholarly requirement: every important sentence should be traceable to an identified, retained, and verified source. The harness can help discover and synthesize research, but it should make the boundary between evidence, interpretation, and prose visible throughout the workflow.
