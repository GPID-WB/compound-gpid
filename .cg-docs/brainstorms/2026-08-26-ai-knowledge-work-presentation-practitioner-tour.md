---
date: 2026-08-26
title: "AI and Research: A Practitioner Tour of the Compound Research Workflow"
status: decided
scope: "Standard"
task-type: "Writing"
study-slug: "ai-knowledge-work-presentation"
approved-approach: "Workflow-first practitioner tour"
audience: "World Bank practitioners doing global or regional applied poverty, inequality, or welfare research"
speaking-time: "15 minutes"
deliverables: "Revised canonical manuscript and locally runnable Reveal.js deck"
created: 2026-08-26
tags: [research, writing, presentation, ai, compound-research, poverty, inequality, welfare, evidence, provenance]
---
<!-- Created 2026-08-26. -->

# AI and Research: A Practitioner Tour of the Compound Research Workflow

## Research question and task type

This is a **Writing** task: prepare a short, plain-language presentation for
World Bank practitioners who work mainly on global or regional applied poverty,
inequality, or welfare research. The presentation should explain how the
Compound Research (`cr`) module extends the familiar Compound GPID (`cg`)
workflow for research tasks.

The practical question is:

> How can researchers use AI for useful research assistance while keeping
> evidence, judgment, verification, and responsibility visible?

The presentation is not a software demonstration, a programming tutorial, or a
claim that the workflow can replace research judgment.

## Audience and scope

The audience already knows the `cg` sequence:

```text
brainstorm -> plan -> work -> review -> compound
```

The talk should therefore use that shared experience as its organizing bridge.
It should explain the research-specific differences without assuming that the
audience knows programming, repository structure, model architecture, or
econometric implementation details.

Target length is 15 minutes. The main deck has 21 slides, with a title and
outline opening, one slide for
each `cr` command, separate explanations of the layers, lifecycle, and task
types, one worked example, and a final slide on normative decisions. The technical
appendix and manuscript may retain a light repository map, but code is excluded
from the main talk.

## Approved approach

Use a workflow-first practitioner tour:

1. Start with the risks AI creates for research: source detachment, unstable
   outputs, hidden selection, and fluent prose that can make weak claims easier
   to repeat.
2. Acknowledge what AI can help a researcher do: search, compare, summarize,
   identify possible mechanisms, draft alternatives, and organize questions.
3. Refresh the familiar `cg` workflow, then show how `cr` applies the same loop
   to research questions, evidence, methods, and claims.
4. Give one short slide to each command: `/cr-brainstorm`, `/cr-plan`,
   `/cr-work`, `/cr-review`, and `/cr-compound`. Explain that
   `/cr-brainstorm` also acts as a sparring partner, asking questions that help
   flesh out ideas before a method is chosen.
5. Explain the ten research task types, where classification is made, and how
   the selected type changes the skills, checks, and review surfaces used later.
6. Explain the available work in plain terms: scoping, theory, specification,
   data exploration, implementation, prediction, measurement, writing,
   publication output, and reproducibility.
7. Introduce **Proof Carrying Claim (PCC)** in plain language: an important
  claim carries a traceable evidence and verification layer, whether its
  evidence comes from literature or data. Make clear that PCC is not a task
  type: it is triggered whenever a substantive claim is intended for reuse. It
  is most visible in Communicate, especially Writing, but can originate in
  evidence, theory, measurement, EDA, or data work.
8. Show the path from original source to source unit to evidence to claim to
   reviewed prose, and state the boundary between plugin support and researcher
   judgment.
  For the main illustration, simplify this to a long paper, a precise locator
  such as page 15 paragraph 3, an atomic claim, and a literature-review
  paragraph that points back to the claim and paper location. Mention that this
  is the basic approach used by Rafael in the Data Quality Assessment work.
9. End with the normative-decision register: consequential choices are made by
   people, recorded with alternatives and consequences, and checked again when
   the output changes. Invite practitioners to begin with `/cr-brainstorm`.

## Slide contract

| Slide | Purpose | Approximate time |
|---:|---|---:|
| 1 | Title: AI and Research | 0:10 |
| 2 | Outline | 0:20 |
| 3 | Risks AI creates for research | 0:40 |
| 4 | Where AI can help a researcher | 0:25 |
| 5 | Refresh the familiar `cg` loop | 0:25 |
| 6 | Macro lifecycle with micro command and task-type mappings | 0:30 |
| 7 | The research lifecycle | 0:45 |
| 8 | Task types describe the work | 0:50 |
| 9 | Example of one task: Research Scoping | 0:35 |
| 10 | `/cr-brainstorm` follow-up questions and approaches | 0:55 |
| 11 | `/cr-brainstorm` command | 0:45 |
| 12 | `/cr-plan` | 0:45 |
| 13 | `/cr-work` | 0:55 |
| 14 | `/cr-review` | 0:45 |
| 15 | `/cr-compound` | 0:35 |
| 16 | Where classification happens and what changes | 0:50 |
| 17 | The work after task classification | 0:30 |
| 18 | PCC: the claim carries its evidence | 1:00 |
| 19 | From source to written prose | 1:05 |
| 20 | Normative decisions and where to begin | 1:30 |
| 21 | Conclusion and next steps | 0:45 |
| **Total** |  | **15:00** |

Each command slide should answer three questions only:

- What is this command for?
- What does it leave behind?
- What does the researcher still decide?

## Worked example: household welfare and GNI per capita

The presentation should show the actual kind of input a practitioner might
send to `/cr-brainstorm`:

> Given that people don't live independently, but they live in households, is
> there a more reliable way to compare living standards across countries, than
> using GNI per capita? Per capita assumes that people live independently. This
> question is more relevant because household size differs a lot across
> countries. There is a literature about using the square-root allocation rule
> for allocating household consumption to account for economies of scale and
> household public goods when distributing welfare within a household.
> Brainstorm an approach to this open research question.

The illustrative flow is:

1. **Provisional classification:** Research Scoping, because the request asks
  to frame an open question before selecting a measure or method.
2. **Human checkpoint:** the researcher confirms or corrects that
  classification. Measurement/Classification is a likely follow-on task, not
  the classification of this initial brainstorm.
3. **Follow-up questions:** clarify the decision context, unit of analysis,
  comparable survey/PPP/GNI evidence, the meaning of "more reliable," and the
  household-allocation assumptions to test.
4. **Approaches:** compare equivalized survey welfare, validation and
  sensitivity, and a distributional comparison rather than jumping directly
  to the square-root rule.
5. **Working recommendation:** begin with a bounded measurement study, retain
  GNI as a benchmark, treat square-root allocation as a candidate rather than
  a default, and report changes in levels, rankings, and distributions across
  alternatives. The workflow then runs its devil's-advocate check. This
  remains provisional until the researcher approves or revises it and hands it
  off to `/cr-plan`.

## Research integrity boundaries

- A generated answer is a proposal, not an approved research claim.
- A source link or verified quotation establishes source linkage, not truth,
  causal validity, or normative correctness.
- Task classification is routing guidance, not a judgment about the quality or
  importance of a researcher's work.
- A seed or low temperature can improve control of a generative run but cannot
  guarantee full reproducibility across providers, model revisions, or serving
  environments.
- The plugin supports scoping, evidence handling, execution, review, and
  knowledge capture. Researchers remain responsible for interpretation,
  assumptions, conclusions, and release decisions.
- The presentation should not imply that the current local evidence workbench
  is a finished literature-discovery system or that it replaces expert review.

## Normative decisions

The presentation owner explicitly approved:

- **Framing:** start with direct research risks while making clear that the
  response is better workflow and institutional responsibility, not prohibition.
- **Uncertainty:** use plain language and show the boundary between candidate
  material and approved evidence without filling the talk with caveats.
- **Comparison:** use the familiar `cg` workflow as the main bridge after the
  opening risk slide; retain the ordinary research process as the intuitive
  background.
- **PCC wording:** explain the idea in ordinary language before naming Proof
  Carrying Claim.
- **Example:** use a Research Scoping task about global poverty measurement to
  show how one task appears across the command, lifecycle, and task-type
  layers; keep the later PCC discussion available for literature and data
  evidence without adding a code demonstration.
- **Technical level:** show exact command names and a light repository map, but
  no code in the main talk.

## Next steps

1. Revise the canonical manuscript to the 17-slide sequence and add the
   research-command, classification, PCC, and normative-decision sections.
2. Revise the derived Reveal.js deck so its visible slide count, notes, and
   timing match the manuscript.
3. Validate headings, timing, local asset loading, and desktop rendering.