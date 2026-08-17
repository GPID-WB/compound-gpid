---
date: 2026-08-13
title: "AI and the Conditions for Verifiable Knowledge Work"
status: draft-for-owner-review
plan: ".cg-docs/plans/2026-08-13-ai-knowledge-work-presentation-production.md"
brainstorm: ".cg-docs/brainstorms/2026-08-13-ai-knowledge-work-presentation.md"
task-type: "Writing"
audiences: ["AI for Data team", "DRG head for poverty, inequality, and human development"]
speaking-time: "30 minutes"
created: 2026-08-13
---
<!-- Created 2026-08-13. Canonical presentation manuscript. -->

# AI and the Conditions for Verifiable Knowledge Work

## How to use this manuscript

This document is designed to support two uses:

1. A 30-minute in-person presentation. The main section gives slide text,
   speaker notes, transitions, and evidence tags.
2. An email-ready narrative. The email section can be circulated without the
   slides or the speaker's oral explanation.

The main presentation is conceptual first. The technical appendix contains the
repository map, named files, and implementation examples.

Evidence tags such as `[C003]` refer to the verified or abstained claim records
in `.cg-docs/research/evidence/claim-evidence-matrix.yaml`. The labels are
included so a reader can distinguish documented facts from interpretation and
future proposals.

The AI-DQSS materials are from the explicitly approved local sibling checkout
of the AI-DQSS repository. They are external-opt-in sources for this artifact,
not files in the Compound GPID repository.

## Presentation brief

### Audience

This presentation is for two audiences at once:

- The AI for Data team that developed AI-DQSS, who will recognize the staged
  retrieval, citation, and verification lineage and can correct the account of
  what was carried forward.
- The head of research on poverty, inequality, and human development in the
  World Bank Development Research Group, who needs to see why this is a
  research and knowledge problem rather than only a software problem.

### Central thesis

> LLMs lower the cost of producing language, but they also make it easier for
> unsupported, unstable, or poorly selected claims to enter knowledge work. The
> answer is not to remove generation from research. It is to place generation
> inside a workflow that keeps the path from resource to claim to composition
> visible, reviewable, and as reproducible as the environment allows.

### Plain-language definition

An **epistemological threat** is a threat to how we move from information to
justified knowledge. The term does not mean that an LLM is always wrong. It
means that a fluent answer can make it harder to tell:

- where a claim came from;
- whether the source actually supports it;
- whether another run would produce the same claim;
- what the system left out; and
- who is responsible for deciding that the claim is fit to reuse.

The phrase should be defined once and then used sparingly. The presentation
should prefer ordinary words such as source, claim, evidence, uncertainty, and
review.

### Narrative architecture

| Movement | Slides | Time | Purpose |
|---|---:|---:|---|
| The problem | 1-4 | 9 minutes | Start from ordinary research practice and define four epistemological threats, including stochastic generation. |
| The framework | 5-7 | 8 minutes | Explain the philosophy: separate generation from authority and move from resource to atomic claim to composition. |
| The lineage | 8-10 | 9 minutes | Explain the original Compound Research/plugin approach, AI-DQSS, and the current package. |
| The next questions | 11-12 | 4 minutes | Treat source discovery and literature review as interface problems and offer avenues for exploration. |

## Main presentation

### Slide 1. From fluent answers to inspectable claims

**Time:** 1 minute

**On the slide:**

> AI and the conditions for verifiable knowledge work
>
> From resource to claim to composition

Small subtitle: A research conversation inspired by AI-DQSS and Compound
Research.

**What to say:**

Research has always involved a movement from sources to notes, from notes to
claims, and from claims to a paper, report, or decision. LLMs change the cost
and speed of every part of that process. They also change the risk: language can
arrive before its source, its uncertainty, or its reasoning has been made
visible.

The question today is not whether LLMs are useful. They clearly are. The
question is what has to surround them if the output is going to become part of
research or institutional knowledge.

**Transition:**

To see the change, start with the ordinary literature review rather than with a
model architecture.

**Evidence tags:** `C001`, `C003`, `C008`; opening framing is interpretation.

### Slide 2. The ordinary research workflow has a hidden control system

**Time:** 2 minutes

**On the slide:**

```text
Question -> search -> read -> take notes -> compare -> interpret -> write -> cite
```

Under the arrow, show three quiet controls: memory, judgment, and return to the
source.

**What to say:**

A literature review is not only a search for text. It is a series of judgments.
A researcher decides which sources matter, reads enough context to understand a
passage, records what the passage supports, compares it with other sources, and
then writes a composition that is supposed to remain answerable to the sources.

Much of this control system is informal. It lives in notes, habits, source
folders, citation managers, and the researcher's ability to return to a page
months later. It is imperfect, but the researcher can usually distinguish a
source, a note, an interpretation, and a final sentence.

An answer-first LLM interface compresses these steps into one fluent response.
That is useful for exploration. But if the compressed steps are not recovered
and recorded, the output can look more settled than the underlying process was.

**Transition:**

The problem is not just the familiar possibility of a false statement. It is a
set of threats to how statements acquire authority.

**Evidence tags:** The workflow description is conceptual framing, not a
measured claim.

### Slide 3. What changes when the answer arrives first?

**Time:** 2 minutes

**On the slide:**

| Ordinary workflow | Answer-first AI workflow |
|---|---|
| Source is encountered before the claim | Claim may appear before the source |
| Notes preserve some uncertainty | Fluency can hide uncertainty |
| Re-reading is part of the work | Source context may be reduced to a snippet |
| Composition follows analysis | Analysis and composition can happen together |

**What to say:**

An LLM can make the final form of knowledge appear early. Before we have
settled the source, the context, the comparison, or the uncertainty, we may
already have a paragraph that sounds ready to use.

That reverses the normal burden of the research process. Instead of asking,
"What can I responsibly say from these sources?" we are tempted to ask, "Can I
find a source that makes this answer defensible?"

The framework proposed here is an attempt to restore the order of operations
without giving up the speed of AI-assisted exploration.

**Transition:**

There are four threats worth naming. Randomness is one of them, but it is not
the whole problem.

**Evidence tags:** Interpretation and proposed comparison baseline.

### Slide 4. Four epistemological threats

**Time:** 4 minutes

**On the slide:**

1. **Source detachment**
2. **Epistemic instability**
3. **Selection opacity**
4. **Amplified composition**

**What to say:**

First, **source detachment**. A fluent claim may have no recoverable source, or
the cited source may not support what the claim says. This is the problem most
people call hallucination, but the broader issue is loss of the source-to-claim
connection.

Second, **epistemic instability**. LLMs commonly generate by sampling from a
distribution of possible continuations. The same prompt and source context can
therefore yield different claims, omissions, or emphases across runs. One
sampled answer is an event in a generation process, not automatically a stable
research object.

This is not a claim that randomness makes every output false. It changes the
burden of proof. We need to know whether the variation matters, which parts of
the output are stable, and which generation settings and model versions were
used. A seed and a low temperature can improve control, but they do not
guarantee identical results across providers, model revisions, hardware, or
serving environments. AI-DQSS itself documents a seed setting that may be
dropped when the provider does not support it. `[C007]`

Third, **selection opacity**. The system may choose one source passage, one
interpretation, or one caveat from many plausible alternatives without making
that choice visible. Retrieval is not neutral simply because it is automated.

Fourth, **amplified composition**. Once a plausible sentence enters a report,
memo, or institutional workflow, its fluency makes it easier to repeat than to
question. A weakly supported claim can acquire institutional weight merely by
being well written.

The common thread is not that AI produces language. It is that language can
acquire authority before its provenance, variability, and selection process are
inspectable.

**Optional demonstration:**

Ask the same model the same source-grounded question twice and display only the
parts that differ. Include this only if the runs, model version, settings, seed
status, retrieved context, and outputs are captured. Otherwise present it as a
thought experiment, not as a measured result. This manuscript does not claim
that such a demonstration has been run. `[C017]`

**Transition:**

That leads to the central design question: what should count as the stable
object in an AI-assisted research process?

**Evidence tags:** `C007`; the four-threat framework and instability claim are
conceptual framing, not an empirical result.

### Slide 5. The stable object is not the answer

**Time:** 2 minutes

**On the slide:**

```text
A generated answer is a proposal.
A verified claim/evidence record is a research object.
```

**What to say:**

The proposal is to stop treating the generated paragraph as the primary
product. The primary product should be a structured, inspectable record:

- a claim stated narrowly enough to examine;
- the source and source version it refers to;
- the locator that takes us back to the passage;
- the verbatim quotation or other evidence;
- the relationship between evidence and claim;
- the verification result; and
- the review decision that determines whether the record can be reused.

Generation remains useful. It can suggest a claim, find a passage, propose a
comparison, or help a researcher see a pattern. But it does not get to decide
that the proposal has become knowledge.

**Transition:**

Before showing the pipeline, it is important to state what this framework can
and cannot establish.

**Evidence tags:** `C002`, `C008`, `C011`, `C012`.

### Slide 6. Caveat checkpoint: what the framework can and cannot establish

**Time:** 2 minutes

**On the slide:**

| The framework can help establish | The framework cannot establish by itself |
|---|---|
| A claim has a recoverable source | The source is true or authoritative in every sense |
| A quotation matches the recorded source unit | The claim has causal validity |
| The source version and review state are visible | The interpretation is the only reasonable one |
| A proposal was generated under a recorded process | The model's output is fully reproducible |
| Unresolved or stale evidence remains visible | A normative judgment is justified |

**What to say:**

This is the boundary that should remain visible throughout the presentation.
Quote and locator verification can establish that a quotation is linked to a
particular source. It cannot establish that the source is correct, that the
research design identifies a causal effect, or that a policy judgment is
normatively right.

Likewise, recording a seed, temperature, model, and prompt improves
reproducibility. It does not turn a generative process into a proof. The
framework is a control system for provenance, review, and composition. It is
not a truth machine.

**Transition:**

With that boundary in place, the philosophy can be expressed as a simple path.

**Evidence tags:** `C007`, `C013`, `C014`; limits are conceptual and normative.

### Slide 7. From resource to atomic claim and back to composition

**Time:** 4 minutes

**On the slide:**

```text
Original resource
      |
      v
Parsed source unit with stable locator
      |
      v
Candidate evidence and atomic claim
      |
      v
Quote/locator verification and human review
      |
      v
Approved claim/evidence record
      |
      v
Analysis and composition
```

Side label: `Generation may be probabilistic; authority is earned through
inspection.`

**What to say:**

The process begins with the original resource. That resource remains the
authority. Parsed text, OCR, indexes, embeddings, and browser views are aids to
finding and inspecting it.

The resource is divided into source units with stable, explainable locators.
From those units we can retrieve candidate passages and propose evidence. The
claim is atomic: one statement that can be supported, contradicted, or left
unresolved. If a sentence contains several independent assertions, it should
be split rather than treated as one smooth block.

The system then checks the quote and locator against the original source and
records the result. A researcher reviews the evidence and decides whether it is
approved for downstream analysis or composition. Only then does the process
return to writing.

This is an analysis/composition split. Analysis produces and verifies the
claim/evidence base. Composition uses approved records. The point is not to
remove interpretation. Interpretation is essential to research. The point is
to make the move from evidence to interpretation visible instead of allowing a
fluent paragraph to hide it.

**Transition:**

That philosophy did not begin with a browser workbench. It developed through
three related technical stages.

**Evidence tags:** `C002`, `C006`, `C008`, `C013`, `C014`.

### Slide 8. The original Compound Research/plugin approach

**Time:** 2 minutes

**On the slide:**

```text
Brainstorm -> Plan -> Work -> Review -> Compound
```

Under it: `Make the next research step easier, and preserve what was learned.`

**What to say:**

The first stage was the Compound GPID approach itself. The plugin began as a
structured workflow for data science work: brainstorm the problem, plan the
work, execute it, review it, and capture what was learned. Compound Research
adapted that workflow to economics and econometrics research. `[C001]`

The key move was not a particular model. It was to treat research reasoning as
something that should leave an inspectable trail: why a model was chosen, what
evidence informed a specification, which assumptions mattered, and what was
learned for the next task.

The evidence and provenance spine then made one part of that philosophy more
explicit. It separated analysis from composition, kept the original document as
the authority, made the local corpus the default, and treated an uncited or
unverifiable substantive claim as a blocking research-integrity problem.
`[C002]`

The exact origin of every idea is not fully recoverable. The earliest available
Compound Research brainstorm is dated 2026-05-13, and the evidence/provenance
spine is dated 2026-07-30. The referenced `Suggestions-For-CR.md` design note is
not present in the current repository, so its contents are not represented
here. `[C016]`

**Transition:**

AI-DQSS supplied a concrete procedural example of how source-grounded AI work
could be staged.

**Evidence tags:** `C001`, `C002`, `C016`.

### Slide 9. AI-DQSS: separate the stages, then verify the words

**Time:** 3 minutes

**On the slide:**

```text
Documents -> Parse -> Index -> Retrieve -> Rerank -> Assess -> Verify -> Report
```

Small caption: Built for WBG data quality self-assessment against 13 policy
pillars; outputs are drafts for human review.

**What to say:**

AI-DQSS is a data quality self-assessment system developed by the AI for Data
team. Its purpose is specific: assess data products, processes, and systems
against the World Bank Group's 13 data quality principles and produce a draft
assessment report for human review. `[C003]`, `[C004]`

Its procedural lesson is broader than that domain. Documents are parsed and
assigned stable citation IDs. Local dense and sparse retrieval narrows the
corpus. A reranker selects stronger candidate passages. An LLM assesses the
requirements and drafts narrative. A verification step checks quoted passages
against the source before the report is exported. `[C005]`, `[C006]`

The important design choice is separation. Finding a passage, ranking a
passage, writing an assessment, and checking a quotation are different stages
with different responsibilities.

The Compound Research work does not copy the 13-pillar assessment structure or
turn research into a compliance report. It carries forward the useful pattern:
source units with addresses, staged retrieval, structured evidence, and
independent checking. AI-DQSS remains an important reference implementation,
not the specification for a research literature-review product.

**Transition:**

The current package brings that procedural pattern into a research-specific
claim and evidence model, with a deliberately conservative default.

**Evidence tags:** `C003`, `C004`, `C005`, `C006`, `C007`; the adaptation boundary
is documented in `C015` and interpreted for this presentation.

### Slide 10. The current local-first research evidence workbench

**Time:** 4 minutes

**On the slide:**

```text
Resource
  -> source version and typed unit
  -> local retrieval
  -> candidate evidence and atomic claim
  -> deterministic quote/locator verification
  -> researcher review
  -> canonical YAML
  -> analysis and composition
```

Call out three controls: `original authority`, `candidate != approved`, and
`stale evidence must be re-verified`.

**What to say:**

The current `research_evidence` package is the executable boundary for this
approach. It is local-first, project-contained, offline during normal
processing, and loopback-only for its browser service. `[C008]`, `[C009]`

It supports the resource lifecycle rather than assuming that a corpus never
changes. Resources receive identities and hashes. Parsed units receive typed
locators. When a source changes or disappears, affected evidence and claims
become stale and must be re-verified before they can return to approved use.
This lifecycle is part of the current workbench design, while richer discovery
is future work. `[C014]`

The baseline retrieval path is deterministic lexical search. Optional dense,
sparse, and reranking profiles are explicit, inventory-controlled, and
candidate-only until they meet their activation and benchmark conditions.
`[C010]` A model may propose a claim or evidence record, but that record remains
a candidate. It must point to a local source unit, include a quotation and a
rationale, and pass independent verification before approval. `[C011]`

Canonical state is written as readable, diffable YAML. The browser interface is
a management surface, not the authority. This matters because it separates the
convenience of an interactive tool from the records that need to survive a
review, a source revision, or a future researcher. `[C013]`, `[C014]`

The package therefore combines two ideas: AI-DQSS's staged evidence procedure
and Compound Research's claim/evidence, review, and knowledge-compounding
workflow. It does not remove uncertainty. It makes uncertainty and review
state visible. `[C015]`

**Transition:**

That gets us from a source to a defensible working set. It does not yet solve
the next problem: how to find the right sources in the first place.

**Evidence tags:** `C008`, `C009`, `C010`, `C011`, `C013`, `C014`, `C015`.

### Slide 11. The next bottleneck is the universe of sources

**Time:** 2 minutes

**On the slide:**

```text
Known corpus: can we verify the claim?
Source universe: did we find the right evidence at all?
```

**What to say:**

The current workbench starts with a repository-local corpus by design. That is
a useful boundary for verification, privacy, and reproducibility. But research
usually begins before the corpus exists. `[C008]`, `[C009]`

The next problem is source discovery: finding the relevant literature and
institutional material in a universe of sources, while recording what was
searched, what was excluded, and why.

This is not simply a request for a bigger search box. Source discovery has its
own risks. A retrieval system can favor highly cited or familiar sources. It
can miss work that uses different language. It can return relevant passages
from sources that are not appropriate for the question. It can also make the
researcher forget that the corpus was selected by a system with its own
coverage and ranking behavior.

A credible next step would therefore need both discovery and a discovery
record: search scope, source identity, version, relevance rationale, exclusions,
and unresolved gaps.

**Transition:**

That points toward a different idea of the literature review: not a machine
that writes the review, but an interface that helps the researcher build it.

**Evidence tags:** Future research proposal; current local-corpus boundary is
`C008` and `C009`.

### Slide 12. Literature review as a research interface

**Time:** 2 minutes

**On the slide:**

```text
Question / claim
      |
Source candidates -> passages -> claims -> supports / contradicts / unresolved
      |                                      |
Search history, exclusions, versions       Approved evidence -> composition
```

At the bottom: `Avenues for exploration, not a finished product roadmap.`

**What to say:**

Imagine a literature-review interface organized around the researcher's claims
rather than around a blank document. The researcher could ask a question,
inspect candidate sources, compare passages side by side, save atomic claims,
record whether sources support or contradict one another, and keep unresolved
items visible.

The interface could show a reading trail: which searches produced a source,
which passages were selected, what was rejected, and which source versions were
used. It could help a researcher move between a claim and its context without
pretending that relevance is the same as truth.

The composition surface would then draw from approved evidence records. It
could still help draft prose, but the draft would be visibly downstream of the
researcher's evidence decisions.

This is an avenue for exploration rather than a finished product roadmap. The
questions are how to discover sources without hiding selection effects, how to
represent disagreement and uncertainty, how to measure retrieval quality for
development research, and how to divide labor between researchers and models.
AI for Data brings experience with staged retrieval and source verification.
DRG brings the research questions, domain judgment, and standards for evidence.
The opportunity is to explore the next interface together while keeping one
principle fixed: AI can help produce proposals, but knowledge should remain
traceable to sources and accountable to human judgment.

**Evidence tags:** Future research proposal; it is intentionally not a claim
that this interface exists in the current package.

## Email-ready narrative

**Subject:** AI and the conditions for verifiable knowledge work

I would like to discuss a question at the intersection of AI for Data and
research: what has to surround a large language model if its output is going to
become part of institutional or scholarly knowledge?

LLMs lower the cost of producing language. They can search, summarize, compare,
and draft at a speed that changes the practical economics of research. But they
also create a problem that is larger than ordinary factual error. A fluent
answer can arrive before its source, its uncertainty, and its reasoning have
been made visible.

In ordinary research, the process generally runs from question to search to
reading to notes to comparison to interpretation to writing. That process is
not perfect, but it contains a hidden control system. The researcher can
usually distinguish a source from a note, an interpretation from a quotation,
and a draft sentence from a settled claim. An answer-first LLM interface
compresses those steps. The result is useful for exploration, but it can also
make a paragraph appear more settled than the underlying process was.

I see four related epistemological threats. The first is source detachment: a
claim may have no recoverable source, or the source may not support what the
claim says. The second is epistemic instability: LLMs commonly generate by
sampling from possible continuations, so the same prompt and source context can
produce different claims, omissions, or emphases. A single sampled answer is
not automatically a stable research object. A seed and a low temperature can
improve control, but they do not guarantee identical output across providers,
model revisions, hardware, or serving environments. AI-DQSS documents both a
low-temperature setting and a seed that may be dropped if the provider does not
support it. `[C007]`

The third threat is selection opacity: the system may choose one passage or
interpretation from many plausible alternatives without making that choice
visible. The fourth is amplified composition: once a plausible sentence enters
a report or workflow, its fluency can make it easier to repeat than to question.

The response should not be to remove generation from research. It should be to
separate generation from authority. A generated answer can be a useful
proposal. The stable research object should instead be a structured record
containing an atomic claim, its source and source version, a locator, the
verbatim evidence, the relation between evidence and claim, the verification
result, and the review decision that determines whether it can be reused.

The process is therefore:

```text
resource -> source unit -> candidate evidence -> atomic claim
-> quote/locator verification -> human review -> approved record
-> analysis and composition
```

The original resource remains the authority. Converted text, OCR, indexes,
embeddings, and browser views help us find and inspect the source, but they do
not replace it. The claim should be narrow enough to examine. Evidence may
support, contradict, or contextualize it. If a source changes, affected records
become stale and require re-verification. Only approved records should flow
into downstream analysis or prose. `[C002]`, `[C008]`, `[C013]`, `[C014]`

This framework has a clear boundary. It can help establish that a claim has a
recoverable source, that a quotation matches a source unit, that source
versions and review states are visible, and that unresolved material has not
silently disappeared. It cannot establish that the source is true, that a
causal design is valid, that an interpretation is the only reasonable one, or
that a normative judgment is justified. It also cannot make a generative model
fully deterministic. It is a control system for provenance, review, and
composition, not a truth machine.

The technical lineage has three stages.

First, Compound GPID began with a structured workflow: brainstorm, plan, work,
review, and compound. Compound Research adapted this approach to economics and
econometrics, emphasizing reasoning trails, methodological choices, evidence,
and reusable knowledge. The later evidence and provenance spine made the
source-to-claim boundary explicit: analysis creates a verified claim/evidence
matrix, composition uses verified claims, the original document remains
authoritative, and uncited or unverifiable substantive claims are blocking
research-integrity problems. `[C001]`, `[C002]`

Second, AI-DQSS provides a concrete procedural exemplar. It was developed by
the AI for Data team to assess data products, processes, and systems against the
World Bank Group's 13 data quality principles and produce draft reports for
human review. Its pipeline separates parsing, indexing, retrieval, reranking,
LLM assessment, quotation verification, and reporting. Stable citation IDs make
source passages addressable; local retrieval narrows the material before the
LLM sees it; and verification checks whether quoted text can be found in the
source. `[C003]`, `[C004]`, `[C005]`, `[C006]`

The research work does not copy the 13-pillar assessment architecture. It
carries forward the separation of stages and the insistence that generated
prose should remain answerable to source evidence. The current workbench
brainstorm explicitly describes AI-DQSS as a design input rather than an
assessment-specific architecture to copy. `[C015]`

Third, the current `research_evidence` package combines that procedural lesson
with the research-specific claim/evidence model. It is local-first,
project-contained, offline during normal processing, and loopback-only for its
browser surface. It discovers resources, hashes source versions, parses typed
source units, performs deterministic lexical retrieval, creates candidate
claims and evidence, verifies quotes and locators, records researcher review,
and persists canonical YAML. Optional model profiles may propose candidates,
but candidates cannot bypass verification or approval. Source changes
invalidate affected records. The browser is a management surface; the original
resources, canonical YAML, and review history remain authoritative. `[C008]`,
`[C009]`, `[C010]`, `[C011]`, `[C013]`, `[C014]`

The current boundary is deliberate. The workbench begins with a known local
corpus. The next bottleneck is the universe of sources: how to find the right
literature and institutional evidence, how to measure coverage, and how to
record what was searched and excluded. This suggests a new interface for
literature review, organized around questions and claims rather than a blank
document. A researcher could inspect candidate sources, compare passages, save
atomic claims, record supports and contradictions, preserve a reading trail,
and compose only from approved evidence.

I see this as a set of avenues for exploration rather than a finished product
roadmap. The interesting questions are how to discover sources without hiding
selection effects, how to represent disagreement and uncertainty, how to
measure retrieval quality for development research, and how to divide labor
between researchers and models. AI for Data brings experience with staged
retrieval and source verification. DRG brings the research questions, domain
judgment, and standards for evidence. The opportunity is to explore the next
interface together while keeping one principle fixed: AI can help produce
proposals, but knowledge should remain traceable to sources and accountable to
human judgment.

## Appendix A. Vocabulary and caveat checkpoint

### Terms to use

| Term | Plain-language meaning |
|---|---|
| Resource | The original document or file used as evidence. |
| Source unit | A passage, paragraph, table row, equation, or other addressable part of a resource. |
| Evidence | Source material recorded for inspection, usually as a verbatim quotation with a locator. |
| Atomic claim | One statement that can be supported, contradicted, or left unresolved. |
| Composition | A report, paper, memo, or other prose assembled from claims and interpretations. |
| Provenance | The record of where a claim or passage came from and how it was handled. |
| Epistemological threat | A threat to how information becomes justified knowledge. |
| Epistemic instability | The possibility that the same generation task produces materially different claims or omissions. |

### Caveat checkpoint wording

> **What this framework can do:** make source links, quotations, source versions,
> review states, uncertainty, and unresolved material visible.
>
> **What it cannot do by itself:** establish that a source is true, prove causal
> validity, guarantee model reproducibility, remove selection bias, or settle a
> normative judgment.

This checkpoint appears once as a full slide. Later references should be short:
`candidate, not approved` and `source linkage is not truth`.

## Appendix B. Repository structure and named files

This map is for the technical appendix or an emailed follow-up. The main talk
should show only the conceptual pipeline.

```text
compound-gpid/
├── .github/
│   ├── prompts/
│   │   └── cr-brainstorm.prompt.md
│   └── skills/
│       ├── cr-skill-research-workflow/SKILL.md
│       ├── cr-skill-research-scoping/SKILL.md
│       ├── cr-skill-evidence-provenance/SKILL.md
│       └── cr-skill-research-integrity/SKILL.md
├── .cg-docs/
│   ├── brainstorms/
│   │   ├── 2026-05-13-compound-research-extension.md
│   │   ├── 2026-08-12-cr-local-evidence-workbench.md
│   │   └── 2026-08-13-ai-knowledge-work-presentation.md
│   ├── plans/
│   │   ├── 2026-07-30-cr-evidence-provenance-spine.md
│   │   └── 2026-08-12-cr-local-evidence-workbench-revised.md
│   ├── research/
│   │   ├── evidence/
│   │   ├── scoping/ai-knowledge-work-presentation.md
│   │   └── normative-decisions/ai-knowledge-work-presentation.md
│   └── manuscript/
│       └── 2026-08-13-ai-knowledge-work-presentation.md
├── research_evidence/
│   ├── README.md
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── src/research_evidence/
│   │   ├── claims.py
│   │   ├── evidence.py
│   │   ├── schemas.py
│   │   ├── resources.py
│   │   ├── lifecycle.py
│   │   ├── workbench.py
│   │   ├── verification/basic.py
│   │   └── retrieval/
│   │       ├── lexical.py
│   │       └── profiles.py
│   └── tests/
│       ├── test_claims_verification.py
│       ├── test_candidate_proposals.py
│       ├── test_lifecycle.py
│       └── test_reproducibility.py
```

The AI-DQSS sibling repository is referred to here by repository name and
relative path: `AI-work/ai-dq-assessor/`. The key documentation files are
`README.md` and `DOCUMENTATION.md`; the key pipeline surfaces are under
`app/parsers/` and `app/pillars/`.

The exact origin of every design idea should not be inferred from this tree.
The `Suggestions-For-CR.md` note referenced by the 2026-07-30 plan is not
present in the current Compound GPID repository. `[C016]`

## Appendix C. Implementation examples

All examples in this appendix are labeled as existing implementation or future
proposal. They illustrate the philosophy; they are not claims that the package
solves source discovery or generates approved prose.

### 1. Existing AI-DQSS citation IDs

AI-DQSS assigns stable identifiers while parsing source material. Examples
documented in its technical documentation include:

```text
DOC-1:PG4:P3     -> document 1, PDF page 4, paragraph 3
DOC-3:P25        -> document 3, paragraph 25
DOC-5:S1:R3:C2   -> document 5, sheet 1, row 3, column 2
```

The design lesson is that a citation is not only a name or a URL. It should be
an address that can take a reviewer back to source context. `[C006]`

### 2. Existing package behavior: candidate claims remain candidates

Simplified from `research_evidence/src/research_evidence/claims.py`:

```python
claim = create_claim(
    "claim-1",
    "The source reports a decline in the poverty rate.",
)

# The claim starts as candidate material.
# Evidence is linked to a typed local source unit.
evidence = create_evidence(
    "evidence-1",
    claim,
    source_unit,
    "Verbatim sentence from the source.",
)
```

The constructor performs a lightweight atomicity check and creates a candidate
record. It does not claim that the statement is true. A statement containing
multiple independent assertions is rejected for splitting, and an evidence
record starts with low confidence and a candidate review state. `[C012]`

### 3. Existing package behavior: model proposals are source-linked and untrusted

The candidate-proposal path in
`research_evidence/src/research_evidence/evidence.py` requires:

- a local source-unit ID;
- an atomic statement;
- a quotation;
- an evidence relation such as supports, contradicts, or contextualizes;
- a rationale retained for review;
- a run ID;
- a retrieval/model profile ID; and
- a dependency/model inventory reference.

A proposal with a fabricated or unavailable source-unit ID is rejected. A
proposal does not become approved merely because a model produced it. `[C011]`

### 4. Existing package behavior: the approved-evidence gate

The `is_approved_evidence` predicate in
`research_evidence/src/research_evidence/schemas.py` requires all of the
following:

```text
verification status = verified-high
confidence = high
review state = approved
original authority verified = true
stale = false
locator is not legacy
```

This is a useful implementation expression of the philosophy: approval is a
state with explicit conditions, not a visual impression in the browser. `[C013]`

### 5. Existing package behavior: source and browser authority

The README describes the browser page as a derived management surface. Original
files, YAML records, and append-only history remain authoritative. Indexes,
cache files, and browser views can be regenerated or replaced without replacing
the source record. `[C014]`

### 6. Future proposal: metadata for a generative path

The current lexical baseline has deterministic repeatability checks. If a
future generative profile is added, the presentation proposes metadata like
this rather than claiming that a seed solves the problem:

```yaml
run_id: run-2026-08-13-001
provider: anthropic
model: claude-example
model_revision: recorded-or-unknown
prompt_or_task_hash: sha256:...
temperature: 0.0
top_p: null
seed: 13
seed_honored: unknown
retrieved_source_unit_ids: [unit-001, unit-014]
repeat_runs: 3
stability_assessment: pending-human-review
```

This is a future proposal. The important separation is between recording the
conditions of generation and approving the content generated under those
conditions.

## Appendix D. Technical lineage: what was adopted and what was not

| Stage | Purpose | Adopted for research | Not adopted as the research target |
|---|---|---|---|
| Compound Research/plugin | Structure research work and preserve reasoning | Brainstorm/plan/work/review/compound loop; analysis/composition split; evidence and reasoning trail | Treating every research task as an engineering task; assuming workflow records alone verify claims |
| AI-DQSS | Assess WBG data quality policy pillars | Stable citation IDs; parse/index/retrieve/rerank separation; structured evidence; quotation verification; human review boundary | 13-pillar assessment structure; compliance scoring; assessment-specific report template; direct clone of model stack |
| Current package | Local research evidence workbench | Typed source units; deterministic local baseline; candidate/approved states; source lifecycle; stale invalidation; canonical YAML; browser review surface | Internet search; autonomous external-paper discovery; automatic conflict resolution; prose generation as the v1 primary product |

## Appendix E. Avenues for exploration

### 1. Finding sources in the universe of sources

Questions for a future research/discovery phase:

- What counts as a sufficiently broad search for a particular research question?
- How should the system record databases, queries, dates, filters, and excluded
  results?
- How can relevance ranking be evaluated without confusing popularity with
  authority or coverage?
- How should duplicate editions, working papers, published versions, and
  institutional revisions be related?
- How can the system identify gaps in the evidence base rather than merely
  returning more passages?
- What source-discovery choices require explicit researcher or institutional
  judgment?

A useful first experiment would compare several discovery strategies on one
small, bounded development-research question and record not only which sources
were found, but which kinds of sources each strategy missed.

### 2. Literature review as an interface

A possible interface could include:

- a question or claim workspace;
- source candidates with provenance and version information;
- side-by-side passage and context inspection;
- claim cards with supports, contradicts, and unresolved links;
- a review queue for low-confidence, stale, or conflicting evidence;
- a visible search and exclusion history;
- a map from approved claims to draft sections, tables, or analyses; and
- a composition view that warns when prose uses unapproved evidence.

The interface should help the researcher read and decide. It should not hide
selection, generate an apparently complete literature review by default, or
turn uncertainty into a single confidence number without explanation.

### 3. Joint pilot questions

For the AI for Data team:

- Which AI-DQSS procedures were most valuable in practice: stable IDs,
  retrieval, reranking, quote verification, or report review?
- Where did users need source context that the original citation format did not
  provide?
- How should model variability be measured and communicated in a review flow?

For DRG research users:

- What is the smallest evidence unit that researchers would actually maintain?
- Which types of claims need direct quotation, and which require a different
  record for tables, equations, estimates, or theory?
- What makes a literature review feel complete enough to support a paper or
  policy argument?
- Which unresolved disagreements should remain visible in the final composition?

For both audiences:

- What would count as a credible pilot result: better source recovery, fewer
  unverifiable citations, faster review, broader coverage, or more transparent
  disagreement?

## Appendix F. Devil's advocate

### Concern 1: Strong risk framing could sound anti-AI

The opening may be heard as a rejection of LLMs rather than a case for better
conditions of use. The mitigation is to state the opportunity immediately and
to place responsibility on institutions, researchers, and reviewers to protect
against risk while enabling useful applications. The argument is about workflow
and authority, not prohibition.

### Concern 2: Ordinary research practice is not a perfect baseline

Researchers also forget sources, select evidence selectively, and vary in their
judgments. The point is not that human research is deterministic or unbiased.
The point is that its judgments can be made visible and revisited. The proposed
workflow should make AI-assisted variability and selection visible rather than
pretending that human judgment has disappeared.

### Concern 3: Quote verification could be mistaken for truth verification

This is the most important overclaim risk. A quote can be exactly present in a
source and still be misleading out of context, based on weak evidence, or
irrelevant to the research question. The central caveat checkpoint must state
this explicitly.

### Concern 4: The package could be presented as more complete than it is

The current workbench has a strong local evidence boundary and a documented
implementation, but source discovery, richer document semantics, and future
generative profiles remain open areas. The talk should describe the current
package as an implementation of the evidence-control loop, not as a finished
literature-review product.

### Concern 5: Randomness is not unique to LLMs

Human reasoning, retrieval scores, and research interpretation also vary. The
specific LLM concern is that a hidden sampled variation can be wrapped in
polished language and passed forward without a record of the alternatives or
conditions. The response is not to demand impossible perfect determinism. It is
to distinguish exploratory variation from authoritative records and to preserve
the metadata needed to inspect the process.

### Concern 6: Source discovery may be the harder problem

A well-verified local corpus can still be incomplete or one-sided. This is why
the next stage should include search scope, coverage, exclusions, source
versions, and discovery rationale. The presentation should offer this as an
avenue for joint exploration rather than promise that the current workbench
solves it.

## Appendix G. Source and evidence register

### Source status

- **Verified:** directly documented in an identified source whose current hash
  is recorded in the provenance ledger.
- **Interpretation:** an argument or framing built from verified sources, not a
  measured empirical result.
- **Proposal:** a possible future design or avenue for exploration.
- **Abstained:** deliberately not promoted to verified because the current
  evidence does not establish it.
- **Unresolved:** a referenced source or lineage detail is unavailable.

### Sources

| ID | Source | Origin and authority |
|---|---|---|
| S001 | [Compound Research extension](../../brainstorms/2026-05-13-compound-research-extension.md) | Repo-local; SHA-256 recorded in the provenance ledger. |
| S002 | [CR Evidence and Provenance Spine](../../plans/2026-07-30-cr-evidence-provenance-spine.md) | Repo-local; SHA-256 recorded in the provenance ledger. |
| S003 | [CR Evidence and Provenance skill](../../../.github/skills/cr-skill-evidence-provenance/SKILL.md) | Repo-local; SHA-256 recorded in the provenance ledger. |
| S004 | [CR Local Evidence Workbench brainstorm](../../brainstorms/2026-08-12-cr-local-evidence-workbench.md) | Repo-local; SHA-256 recorded in the provenance ledger. |
| S005 | [Research Evidence Workbench README](../../../research_evidence/README.md) | Repo-local; SHA-256 recorded in the provenance ledger. |
| S006 | [claims.py](../../../research_evidence/src/research_evidence/claims.py) | Repo-local implementation source; SHA-256 recorded in the provenance ledger. |
| S007 | [evidence.py](../../../research_evidence/src/research_evidence/evidence.py) | Repo-local implementation source; SHA-256 recorded in the provenance ledger. |
| S008 | [schemas.py](../../../research_evidence/src/research_evidence/schemas.py) | Repo-local implementation source; SHA-256 recorded in the provenance ledger. |
| S009 | AI-DQSS `README.md` in the approved local sibling repository `AI-work/ai-dq-assessor/` | External-opt-in local source; SHA-256 recorded in the provenance ledger. |
| S010 | AI-DQSS `DOCUMENTATION.md` in the approved local sibling repository `AI-work/ai-dq-assessor/` | External-opt-in local source; SHA-256 recorded in the provenance ledger. |

### Claim status map

| Claim IDs | Presentation subject | Status |
|---|---|---|
| C001-C002 | Compound Research and evidence/provenance foundation | Verified |
| C003-C007 | AI-DQSS purpose, human-review boundary, staged architecture, citation IDs, and generation controls | Verified |
| C008-C015 | Current package boundary, processing policy, candidate state, approval gate, and AI-DQSS design relationship | Verified |
| C016 | Missing `Suggestions-For-CR.md` lineage source | Verified filesystem absence and unresolved contents |
| C017 | Epistemic instability from stochastic generation | Abstained conceptual framing; no measured demonstration claimed |

The full claim records, locators, quotations, source hashes, and verification
notes are maintained in `.cg-docs/research/evidence/claim-evidence-matrix.yaml`
and `.cg-docs/research/evidence/provenance-ledger.yaml`. The original source
files remain authoritative.

## Appendix H. Open questions for the conversation

The presentation should end by inviting discussion rather than asking the
audience to approve a fixed roadmap.

1. Which parts of AI-DQSS were most valuable in practice: stable IDs, retrieval,
   reranking, quote verification, source-context views, or report review?
2. What is the smallest evidence unit that researchers would actually maintain
   throughout a paper's lifecycle?
3. How should source discovery record coverage, exclusions, versions, and
   selection rationale?
4. How should disagreement, absence, and uncertainty remain visible in a
   literature-review interface?
5. Which research questions in poverty, inequality, and human development would
   make a useful bounded pilot?
6. What would count as credible evidence that the workflow helps: better source
   recovery, fewer unverifiable citations, faster review, broader coverage, or
   more transparent disagreement?

The proposed collaboration is modest: use the current local evidence-control
loop as a concrete object for discussion, then explore the next interface and
source-discovery questions with researchers and builders together.
