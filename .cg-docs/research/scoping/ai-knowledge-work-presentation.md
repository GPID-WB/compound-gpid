---
date: 2026-08-13
title: "AI and the Conditions for Verifiable Knowledge Work"
status: approved
task-type: "Writing"
study-slug: "ai-knowledge-work-presentation"
audiences: ["AI for Data team", "DRG head for poverty, inequality, and human development"]
created: 2026-08-13
---

# Scoping Memo: AI and the Conditions for Verifiable Knowledge Work

## Problem framing

### Policy or measurement question

How should research and institutional knowledge work change when large language
models can produce fluent, useful-looking text without reliably establishing
where its claims came from, whether the source supports them, or whether the
claims are true?

The presentation should explain the epistemological problem in plain language:
LLMs change the cost and appearance of producing knowledge, but fluent language
is not the same thing as justified belief. A second problem is epistemic
instability: many LLM deployments generate by sampling from a distribution, so
the same prompt and source context can produce different claims, omissions, or
emphases on different runs. Even a nominally deterministic setting does not
guarantee identical output across providers, model versions, or serving
environments. The central question is therefore how to preserve a visible path
from source to claim to composition while still using AI to reduce research
friction.

### Intended decision context

The presentation is intended to create a shared basis for discussion with the
AI for Data team that developed AI-DQSS and with the head of research on
poverty, inequality, and human development in the World Bank Development
Research Group. It should support decisions about:

- whether the problem framing is useful to both technical and research leaders;
- whether the claim/evidence workflow is a credible bridge between AI systems
  and research practice; and
- which next problems deserve joint attention, especially source discovery and
  the design of research interfaces.

It is not yet a request for approval of a product roadmap, a claim that the
current package is production-ready, or a claim that it reproduces AI-DQSS.

### Stakeholders affected

- Researchers and analysts who rely on literature, institutional documents,
  and prior work to make substantive claims.
- AI and data-system builders who decide how retrieval, generation, and
  verification are separated.
- Research managers, reviewers, and institutional decision makers who need to
  assess whether an output is trustworthy enough to use.
- Future coauthors and users of institutional knowledge who need to recover the
  source and reasoning behind a statement.

### Target population and unit of analysis

The target population is knowledge workers doing document-heavy research,
especially policy and economic research. The recurring unit of analysis is a
source passage linked to an atomic claim, followed by the composition that uses
that claim. This unit is deliberately smaller than a paragraph or a generated
answer, but it must retain enough source context for interpretation.

### Time horizon and comparability constraints

The presentation covers the current conceptual and technical lineage and a
near-term research agenda. The earliest recoverable Compound Research artifact
is dated 2026-05-13; the evidence/provenance spine is dated 2026-07-30; and the
current `research_evidence` package is dated 2026-08-12 and 2026-08-13. These are
documented milestones, not necessarily the dates on which each idea was first
conceived or executed.

The three technical stages must remain distinct:

1. the original Compound Research/plugin workflow and evidence-provenance
   design;
2. AI-DQSS as a procedural reference, not an assessment architecture to copy;
3. the current local-first package, which adapts the useful source, retrieval,
   candidate, verification, and review pattern to research claims.

The origin and contents of the referenced `Suggestions-For-CR.md` design note
are not currently available in this repository. Any claim about that note's
influence must be marked as partial or unresolved unless the source is supplied.

The target speaking time is 30 minutes. The deliverable is one Markdown
document containing a slide-by-slide structure, speaker notes/talk track, a
self-contained email-ready narrative, and an appendix with repository
structure, named files, and implementation examples. The main presentation
starts with the conceptual pipeline; technical detail is deferred to the
appendix. AI-DQSS, its team, and the current package may be named explicitly.

## Competing conceptual frames

### Frame A: AI as a productivity and access layer

- **Prioritizes:** speed, search, summarization, drafting, and lowering the
  cost of working through large document collections.
- **Makes visible:** the practical gains from retrieval and generation.
- **Makes less visible:** source ambiguity, false confidence, omitted context,
  and the difference between a plausible answer and a justified claim.
- **Most likely to shift:** perceptions of short-run productivity and adoption
  value.

### Frame B: AI as epistemic infrastructure

- **Prioritizes:** how claims are formed, checked, qualified, reused, and
  composed into research outputs.
- **Makes visible:** source authority, atomic claims, uncertainty, review states,
  provenance, and the boundary between evidence and interpretation.
- **Makes less visible:** the convenience of an answer-first interface and the
  full range of creative or exploratory uses of LLMs.
- **Most likely to shift:** perceptions of what must be built around an LLM for
  high-stakes research and institutional knowledge.

### Frame C: Literature review as a research interface

- **Prioritizes:** helping a researcher move through a source universe,
  compare passages, inspect context, record claims, and return to composition.
- **Makes visible:** the interaction design of research rather than only the
  quality of generated text.
- **Makes less visible:** the possibility that source selection itself embeds
  disciplinary, institutional, or normative judgments.
- **Most likely to shift:** priorities for the next generation of research tools,
  especially source discovery, review queues, and evidence maps.

The approved structure uses Frame A, ordinary research practice and answer-first
LLM use, as the practical comparison baseline. Frame B supplies the conceptual
lens for the solution, and Frame C becomes the future agenda. The technical
lineage then has three clearly separated sections: the original Compound
Research/plugin approach, AI-DQSS, and the current package.

## Epistemological threats to name explicitly

The presentation should introduce four related but distinct threats. Keeping
them separate prevents randomness from being reduced to a generic complaint
about unreliable AI.

1. **Source detachment:** a fluent claim may not have a recoverable source, or
  the cited source may not support what the claim says.
2. **Epistemic instability:** stochastic generation can produce materially
  different claims or omissions from the same prompt and evidence. A single
  output is therefore an event in a generation process, not automatically a
  stable research object.
3. **Selection opacity:** the system may choose one passage, interpretation, or
  caveat from many plausible alternatives without making that selection
  inspectable.
4. **Amplified composition:** once a plausible statement enters a report,
  memo, or institutional workflow, its fluency can make it easier to repeat
  than to question.

The talk should use a simple thought experiment here: give the same source and
question to the same model twice, then ask what would count as evidence if the
answers differ. The point is not that variation makes every answer false. The
point is that variation changes what must be recorded and checked before an
answer can become part of shared knowledge.

The key distinction to carry into the rest of the presentation is:

> Generation may be probabilistic; the authoritative evidence record must be
> inspectable, attributable, and as reproducible as the environment allows.

## Theory priors

1. **Fluency and justification are different properties.** An LLM can produce
   coherent language without a reliable source, locator, or verification path.
   The presentation should distinguish language generation from knowledge
   justification.
2. **Stochastic generation creates process uncertainty.** Randomness can be
  useful for exploring alternative formulations, but a single sampled output
  should not be treated as a unique interpretation or a reproducible finding.
  A seed and a low temperature are controls, not guarantees: a provider may
  ignore a seed, and output can still vary across model versions, providers,
  hardware, or serving stacks.
3. **Retrieval reduces exposure to irrelevant material but does not establish
   truth.** Better retrieval and reranking improve the evidence candidates; they
   do not prove a source's claims or settle causal validity.
4. **Atomic claims improve inspection.** Splitting a passage or paragraph into
   smaller claims makes support and contradiction visible, but atomicity does
   not eliminate the need to preserve source context and interpretation.
5. **Verification has a limited object.** Matching a quote and locator against
   the original source verifies source linkage. It does not verify that the
   source is correct, that the research design identifies a causal effect, or
   that a normative conclusion is justified.
6. **Human review remains a substantive stage.** The researcher or reviewer
   remains responsible for deciding whether evidence is adequate, whether an
   inference is warranted, and whether a composition is fit for its purpose.
7. **Source discovery is the next bottleneck.** Once source-to-claim traceability
   is explicit, finding the right sources in the wider universe becomes the next
   unresolved research problem.
8. **Lineage claims require provenance.** The presentation may say that current
   work is inspired by AI-DQSS procedures because that relationship is
   documented. It should not imply that the two systems have the same purpose,
   architecture, or model choices.

## Success criteria

### Substantive criterion

A listener should be able to explain:

- what LLMs change about the conditions for trustworthy knowledge work;
- why a plausible response is not necessarily a stable or reproducible research
  object;
- why the resource -> source unit -> evidence -> atomic claim -> composition
  path matters;
- how the plugin, AI-DQSS, and current package differ; and
- why source discovery and research-interface design are the next questions.

The emailed version should preserve this narrative without requiring the
presenter to supply missing transitions orally.

### Statistical and evidence criterion

No new statistical result is required for this presentation. Any performance,
cost, coverage, or model-quality number that is included must have a dated,
resolvable source and should be presented with its scope and limitations. The
core evidence standard is instead that documented facts, inferences, and
proposals are visibly separated.

### Integrity criterion

- Do not present generated prose as evidence.
- Do not claim that quote verification establishes the truth of a source claim
  or the validity of a research conclusion.
- Do not claim that temperature `0` or a recorded seed makes a generative run
  fully deterministic. Record generation settings and provider/model versions
  where a generative path is used, and state when the provider may not honor
  them.
- Do not imply that the current package is a direct clone of AI-DQSS.
- Mark the missing `Suggestions-For-CR.md` source and any other unresolved
  lineage as unresolved rather than filling the gap with a plausible story.
- Record consequential framing decisions in the linked normative register.

### Reproducibility criterion

The final narrative should retain a source list with repository name, path,
section or symbol, date/version where available, and an explicit label for
inference. The technical lineage should be reconstructable from the dated
Compound GPID artifacts, the AI-DQSS documentation, and the current package
README/source. Any later slide deck or email rendering should preserve these
source references. For any generative path, reproducibility metadata should
also include the provider, model and revision, prompt or task specification,
temperature/top-p settings where available, seed and whether it was honored,
retrieved context, and the number or pattern of repeated runs used to assess
stability. The current workbench's lexical baseline and canonical evidence
checks provide the stable control path; optional model proposals remain
candidate data until independently verified and approved.

## Recommended placement in the presentation

Use epistemic instability as the second movement in the opening problem
section, immediately after source detachment. Then return to it at two points:

1. **Framework:** distinguish a probabilistic generation layer from a stable
  evidence layer. The aim is not to remove all randomness, but to prevent a
  sampled answer from silently becoming authoritative knowledge.
2. **Technical lineage:** show that AI-DQSS controls generation with settings
  such as temperature and a seed, while its documentation also notes that a
  provider may silently drop the seed. Show the current package's response:
  deterministic local retrieval and quote/locator checks form the baseline;
  optional model proposals are source-linked candidates, not approved facts.

Close the loop in the future-work section with a reproducibility question:
which parts of a research interaction should be repeatable, which may remain
exploratory, and what run record is needed to tell the difference? This keeps
randomness tied to the core philosophy of the approach rather than turning it
into an isolated engineering detail.

## Initial normative decision register links

The following decisions are unresolved and must be made explicitly before the
presentation narrative is locked:

- `ND-ai-knowledge-work-presentation-001`: framing language for harms,
  responsibility, and the phrase "epistemological threats".
- `ND-ai-knowledge-work-presentation-002`: which uncertainty and limitation
  caveats are foregrounded during the talk versus deferred to notes or the
  email version.
- `ND-ai-knowledge-work-presentation-003`: comparison baseline used to explain
  progress and the future direction.

See `.cg-docs/research/normative-decisions/ai-knowledge-work-presentation.md`.
