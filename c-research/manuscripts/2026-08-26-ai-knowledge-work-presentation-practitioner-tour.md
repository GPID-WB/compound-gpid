---
date: 2026-08-26
title: "AI and Research: A Practitioner Tour of the Compound Research Workflow"
status: draft-for-owner-review
previous-manuscript: "c-research/manuscripts/2026-08-13-ai-knowledge-work-presentation.md"
derived-presentation: "presentation/ai-knowledge-work-presentation.html"
brainstorm: ".cg-docs/brainstorms/2026-08-26-ai-knowledge-work-presentation-practitioner-tour.md"
task-type: "Writing"
audience: "World Bank practitioners doing global or regional applied poverty, inequality, or welfare research"
speaking-time: "15 minutes"
created: 2026-08-26
last-revised: 2026-08-26
tags: [research, writing, presentation, ai, compound-research, poverty, inequality, welfare, evidence, provenance]
---
<!-- Created 2026-08-26. Revised practitioner-first presentation manuscript. -->

# AI and Research: A Practitioner Tour of the Compound Research Workflow

## How to use this manuscript

This is the revised, practitioner-first version of the presentation. It is
written for people doing applied poverty, inequality, and welfare research at
the World Bank. The audience already knows the Compound GPID (`cg`) workflow;
the talk uses that shared experience to explain what the research module (`cr`)
adds.

The Markdown file is the authoritative narrative. The Reveal.js file at
`presentation/ai-knowledge-work-presentation.html` is a derived delivery
surface. Speaker notes carry the explanation; slide text stays brief.

The presentation makes no new statistical claim and includes no live model
demonstration. Statements about the plugin's current behavior are tied to the
source anchors in Appendix C. The central claim about stochastic generation is
presented as conceptual framing, not as a measured result.

## Presentation brief

### The question

> How can researchers use AI for useful research assistance while keeping
> evidence, judgment, verification, and responsibility visible?

### What the audience should leave with

A practitioner should be able to explain:

- what AI can help with in research and what it cannot decide;
- how the familiar `brainstorm -> plan -> work -> review -> compound` loop is
  adapted for research;
- why the research task type is identified early and changes the later route;
- what Proof Carrying Claim means in ordinary research language; and
- why consequential normative choices remain human decisions.

### Tone and vocabulary

Use ordinary research language: source, evidence, claim, uncertainty, review,
method, and judgment. Define Proof Carrying Claim once. Do not assume that the
audience knows Python, repositories, model architecture, or econometric code.
The exact command names should be visible, with a plain-language explanation
beside each one.

### Narrative architecture

The 15-minute talk has four movements:

1. **Why the workflow matters:** risks AI creates for research, followed by the
   useful work AI can support.
2. **A familiar route with research safeguards:** the `cg` loop and the `cr`
   research lifecycle.
3. **The five research commands:** what each command is for, what it leaves
   behind, and what the researcher still decides.
4. **Routing and accountability:** task types, skills and agents, PCC, the path
   from source to prose, and normative decisions.

## Main presentation

### Slide 1. AI and Research

**Time:** 10 seconds

**On the slide:**

> AI and Research
>
> A guide for using the Compound-GPID plug in for research

**What to say:**

This presentation introduces the Compound-GPID research plug in: what problem
it addresses, how it organizes research work, and where human judgment remains
essential.

**Transition:**

Here is the route we will take.

### Slide 2. Outline

**Time:** 20 seconds

**On the slide:**

1. AI and Research
2. The workflow, tasks, and the research lifecycle
3. A quick example
4. The commands
5. Literature reviews, evidence, and PCCs
6. On human decision-making

**What to say:**

We will begin with the problem AI creates for research, then connect the
familiar workflow to the research lifecycle and task types. We will use one
concrete research question as a quick example, review the commands, discuss
literature reviews, evidence, and Proof Carrying Claims, and close with human
decision-making.

**Transition:**

Let us begin with the risks that make this workflow necessary.

### Slide 3. What can go wrong when AI enters research?

**Time:** 40 seconds

**On the slide:**

> What can go wrong when AI enters research?
>
> The workflow is protecting four things:
>
> - connection to the source;
> - stability and uncertainty;
> - visibility of selection; and
> - responsibility for the final claim.

Small footer: `Fluent language is useful. It is not evidence by itself.`

**What to say:**

AI can make research faster. It can also make an unsupported statement look
ready for a paper, a brief, or a poverty-monitoring discussion before anyone
has checked the source, the context, or the reasoning behind it.

The risks the research workflow is designed to address are straightforward.
A claim can become detached from its source. A repeated run can produce a
different emphasis or omission, while the prose still sounds certain. The
system can select one source or interpretation without showing what it left
out. And once polished language enters a report, people may repeat it because
it reads well rather than because its support is clear.

These are not arguments against using AI. They are reasons to keep the route
from evidence to claim visible.

**Transition:**

The point is not to ask AI to do nothing. The point is to give it useful work
without giving it unexamined authority.

**Evidence status:** The four-risk framing is interpretation. The instability
component is the abstained conceptual claim `C017` in the existing evidence
matrix; no repeated-run result is claimed.

### Slide 4. Where AI can help a researcher

**Time:** 25 seconds

**On the slide:**

| AI can help with | A researcher still decides |
|---|---|
| Finding and sorting relevant material | Whether the material is relevant and authoritative |
| Comparing passages, definitions, or methods | Whether the comparison is fair |
| Summarizing a document or a result | Whether the summary preserves the qualification |
| Suggesting questions, mechanisms, or specifications | Which question or specification is defensible |
| Drafting alternative wording | What can be responsibly stated |

**What to say:**

For global poverty measurement, AI can help locate definitions across technical
documents, compare how a measure is described, summarize a long report, or
suggest questions for a literature review. It can help organize the work that
surrounds research judgment.

It cannot decide that a source is authoritative for the question, that a
method identifies a causal effect, or that a sentence is ready to publish. A
useful shorthand is: **AI helps with research effort; researchers retain
research authority.**

**Transition:**

That division of labor is already familiar in the `cg` workflow.

**Evidence status:** Examples are illustrative. The division between generated
proposals and human decisions is a presentation principle grounded in the CR
workflow and evidence/provenance rules.

### Slide 5. The workflow you already know

**Time:** 25 seconds

**On the slide:**

```text
brainstorm -> plan -> work -> review -> compound
```

Under the line:

```text
clarify the task -> decide the route -> do the work -> check it -> retain the lesson
```

**What to say:**

This is the workflow many of you already know. First, make the question and the
constraints clear. Then make a plan that someone else can inspect. Do the work
against that plan. Review the result. Finally, retain the lesson so that the
next project does not start from zero.

The important feature is not the names of the steps. It is that the reasoning
and the checks are part of the work, rather than something reconstructed after
the result is finished. Compound Research extends this structure to research
questions, evidence, methods, and claims. `[C001]`

**Transition:**

The research module keeps the loop, then adds the parts of the research process
that determine whether a finding is fit to use.

**Evidence status:** `C001`; workflow explanation is a plain-language
interpretation of the documented Compound Research approach.

### Slide 6. The lifecycle works at two levels

**Time:** 30 seconds

**On the slide:**

| Lifecycle stage | Micro command mapping | Task-type mapping |
|---|---|---|
| Scope | Brainstorm | Research Scoping |
| Evidence | Shared safeguard | EDA -> Execute |
| Theory | Task-specific | Theory/Modeling; Specification Analysis -> Method |
| Method | Plan | Measurement/Classification; ML/Prediction; Implementation -> Execute |
| Execute | Work | None |
| Verify | Review | Shared safeguard |
| Communicate | Task-specific | Tables/Figures; Writing |
| Maintain | Compound | Reproducibility |

Under the table: `Macro = the whole lifecycle. Micro = the command route and the current task.`

**What to say:**

The previous slide showed the workflow you already know. This slide makes the
two levels of the research lifecycle visible.

At the **macro** level, the lifecycle describes the whole research process:
Scope, Evidence, Theory, Method, Execute, Verify, Communicate, and Maintain.

At the **micro** level, the familiar commands map onto the stages they
primarily serve: Brainstorm to Scope, Plan to Method, Work to Execute, Review
to Verify, and Compound to Maintain. Evidence and verification also remain
shared safeguards; they are not owned by one task type.

Task types provide a second mapping. Research Scoping belongs to Scope,
Theory/Modeling to Theory, Measurement and prediction mainly to Method, Writing
and Tables/Figures to Communicate, and Reproducibility to Maintain. Some task
types span two stages: EDA runs from Evidence to Execute, Specification Analysis
from Theory to Method, and Implementation from Method to Execute.

Classification happens in `/cr-brainstorm`, where the researcher confirms or
corrects the proposed task type. The same command route organizes every task;
the task type tells the workflow where specialized guidance is needed.

**Transition:**

The next slide explains what each lifecycle stage means in plain language.

**Evidence status:** Directly documented in
`.github/skills/cr-skill-research-workflow/SKILL.md` and
`docs/reference/commands.md`; the three-layer explanation is a plain-language
interpretation of the documented routing model.

### Slide 7. The research lifecycle

**Time:** 45 seconds

**On the slide:**

| Stage | What it means |
|---|---|
| **Scope** | Define the question, population, decision context, and choices that need a person. |
| **Evidence** | Establish the sources, data, and provenance that support important claims. |
| **Theory** | Explain the mechanism, model, or identification argument behind the work. |
| **Method** | Choose how the question will be measured, estimated, compared, or tested. |
| **Execute** | Carry out the planned work and record what happens, including deviations. |
| **Verify** | Check evidence, assumptions, diagnostics, uncertainty, and limitations. |
| **Communicate** | Turn reviewed findings into prose, tables, figures, or a briefing. |
| **Maintain** | Preserve sources, versions, code, decisions, and lessons for later recovery. |

**What to say:**

The lifecycle is not another command sequence. It is a checklist of what
responsible research needs to cover.

Scope asks what question we are answering and which choices matter. Evidence
asks what supports the claims. Theory and method explain the reasoning and the
way the question will be tested. Execute is the work itself. Verify checks
whether the result is supported and whether its limitations are visible.
Communicate turns reviewed findings into outputs. Maintain preserves the
sources, decisions, and records so the work can be recovered later.

A task can focus on one stage without making the other responsibilities
disappear. The task type tells us where the emphasis is; the lifecycle tells us
what the whole process must protect.

**Transition:**

The lifecycle tells us where the work contributes. Task types tell us what kind
of work it is.

**Evidence status:** Directly documented in
`.github/skills/cr-skill-research-workflow/SKILL.md`.

### Slide 8. Task types describe the work

**Time:** 50 seconds

**On the slide:**

| Task type | Plain-language question | Primary focus |
|---|---|---|
| Research Scoping | What question and decision context are we framing? | Scope |
| Theory/Modeling | What economic model or identification argument are we using? | Theory |
| Specification Analysis | Which variables, forms, or comparisons test the idea? | Theory -> Method |
| Measurement/Classification | How should an index, threshold, or label be constructed and checked? | Method |
| ML/Prediction | How can we predict, and how should prediction be evaluated? | Method |
| Implementation | How do we code a method already chosen? | Method -> Execute |
| EDA | What does the data show before formal analysis? | Evidence -> Execute |
| Tables/Figures | How should results be shown for publication or discussion? | Communicate |
| Writing | How should evidence and results be explained? | Communicate |
| Reproducibility | Can another researcher recover the environment and result? | Maintain |

**What to say:**

These ten categories answer a different question from the lifecycle. They
describe the kind of work being done, not the quality of the work and not a
fixed order.

A global poverty project might include Research Scoping at the beginning,
Measurement and EDA in the middle, Implementation for an estimator, Tables and
Figures for results, Writing for the report, and Reproducibility for handoff. A
single project can therefore contain several task types.

The classification tells the system which guidance and review surfaces are
most relevant to the current task. It does not remove the shared lifecycle
safeguards.

**Transition:**

Here is one task placed in all three maps.

**Evidence status:** Directly documented in
`.github/skills/cr-skill-research-workflow/SKILL.md`.

### Slide 9. Example of one task

**Time:** 35 seconds

**On the slide:**

> **Prompt to `/cr-brainstorm`:** Given that people don't live independently,
> but they live in households, is there a more reliable way to compare living
> standards across countries, than using GNI per capita? Per capita assumes
> that people live independently. This question is more relevant because
> household size differs a lot across countries. There is a literature about
> using the square-root allocation rule for allocating household consumption to
> account for economies of scale and household public goods when distributing
> welfare within a household. Brainstorm an approach to this open research
> question.

| Question | Provisional answer |
|---|---|
| What kind of work? | **Research Scoping** |
| Where does it primarily contribute? | **Scope** |
| What happens next? | Confirm or correct the classification |

**What to say:**

This is the research question we are using as a dry run. The submitted prompt
asks whether a household-based welfare measure could improve on GNI per capita
when household size and economies of scale differ across countries. It points
to the square-root allocation rule as a candidate, but it does not yet choose
that rule.

The provisional classification is **Research Scoping** because the request is
to frame an open research question before a measure or method is selected. The
researcher confirms or corrects that classification. A likely later task would
be Measurement/Classification, but that is not the classification of this first
brainstorm.

The command still follows the familiar route: `/cr-brainstorm` is the first
step, followed by `/cr-plan`, `/cr-work`, `/cr-review`, and `/cr-compound` as the
work develops.

**Transition:**

After the researcher confirms the route, the brainstorm asks the questions that
make the open problem workable and compares possible approaches.

**Evidence status:** The research question is supplied by the presentation
owner. The classification and follow-up flow are a faithful illustration of
the CR prompt contract; the example is not a completed research study.

### Slide 10. What the brainstorm asks next

**Time:** 55 seconds

**On the slide:**

**Questions:**

1. What decision should this comparison inform: global monitoring, country
   ranking, poverty measurement, or welfare analysis?
2. What is the unit of analysis: household, person, or country average?
3. Which survey, PPP, GNI, household-size, and time-series sources are
   comparable?
4. What would "more reliable" mean: a better welfare concept, stable rankings,
   or external validity?
5. Which within-household assumptions and alternative allocation rules should
   be tested?

**Approaches:**

- **Equivalized survey welfare:** compare per-capita, square-root, and one
  alternative using harmonized household survey data.
- **Validation and sensitivity:** test changes in levels and rankings, then
  compare them with selected external welfare indicators.
- **Distributional comparison:** report country distributions, quantiles,
  poverty, and inequality rather than only one average.

**Working recommendation:** Start with a bounded measurement study. Keep GNI as
a benchmark, treat square-root allocation as a candidate rather than a default,
and report how levels, rankings, and distributions change across alternatives.

**What to say:**

These are the follow-up questions the scoping skill is designed to surface. They
clarify the decision context, unit of analysis, comparable evidence, meaning of
reliability, and assumptions with distributional consequences.

The brainstorm then compares approaches instead of jumping directly to the
square-root rule. The first is transparent and close to the proposed question.
The second adds validation and sensitivity. The third asks whether a single
country average is too narrow.

The working recommendation is deliberately provisional: run a bounded
measurement study, retain GNI as a benchmark, treat square-root allocation as a
candidate, and report sensitivity across alternatives. The workflow then runs
the devil's-advocate check: challenge the question, simplicity, effort-value,
and fit with the project focus. The researcher still challenges, approves or
revises, or replaces that recommendation before the brainstorm is saved and
handed off to `/cr-plan`.

**Transition:**

Now we can return to the command itself and see what `/cr-brainstorm` produces
for any research question.

**Evidence status:** The questions, approaches, and recommendation are
illustrative brainstorm output, not findings. The required scoping fields and
approach-comparison step are documented in the CR scoping and brainstorm
contracts.

### Slide 11. `/cr-brainstorm`: make the research question workable

**Time:** 45 seconds

**On the slide:**

> `/cr-brainstorm`
>
> Clarify the question and act as a sparring partner: ask questions that flesh
> out ideas before choosing the method.
>
> **Leaves behind:** a scoped research brief, task type, assumptions,
> alternatives, and an explicit decision record where needed.
>
> **The researcher decides:** what the question means, what population or
> comparison matters, and which value-laden choices are acceptable.

**What to say:**

Use `/cr-brainstorm` when the question is still fuzzy. It begins by reading the
project context, then identifies which of the ten research task types best
matches the request. The researcher confirms or corrects that classification.

It also acts as a sparring partner. By asking questions, it helps the researcher
flesh out the idea, its decision context, its assumptions, and what a credible
answer would need to show before a method is selected.

For research work, the command also surfaces decisions that should not be
smuggled in as technical defaults. Depending on the task, that may include a
sample restriction, a threshold, a weighting rule, an outlier policy, or the
language used to describe who gains and who loses.

The output is not code and it is not a final method. It is a clearer question,
a named task type, a scoping record, and a visible list of decisions that need
to be made.

**Transition:**

Once the question and route are clear, the next step is to turn them into work
that can be checked.

**Evidence status:** Directly documented in
`.github/prompts/cr-brainstorm.prompt.md` and
`.github/skills/cr-skill-research-scoping/SKILL.md`.

### Slide 12. `/cr-plan`: turn the question into a research plan

**Time:** 45 seconds

**On the slide:**

> `/cr-plan`
>
> Turn a clarified research question into steps and checks.
>
> **Leaves behind:** a plan with task type, files or data, assumptions,
> evidence requirements, test scenarios, and acceptance criteria.
>
> **The researcher decides:** which design is proportionate, which alternatives
> matter, and what counts as a credible answer.

**What to say:**

Use `/cr-plan` after the brainstorm. The plan records what will be done, in
what order, and how the result will be checked. For a global poverty question,
that could mean identifying the source documentation, defining the comparison,
checking the relevant data, documenting a methodological choice, and stating
what evidence would be enough to support the final paragraph or table.

The plan carries the task type forward. That lets later steps prepare the
right evidence and review surfaces instead of treating every research request
as the same kind of job.

The plan is a commitment to a method and a verification path, not a guarantee
that the initial design will survive contact with the data.

**Transition:**

The plan becomes useful when the work is executed with its integrity checks
still active.

**Evidence status:** Directly documented in `.github/prompts/cr-plan.prompt.md`.

### Slide 13. `/cr-work`: do the work with research-integrity gates

**Time:** 55 seconds

**On the slide:**

> `/cr-work`
>
> Execute the plan, one step at a time, with research safeguards active.
>
> **Leaves behind:** working outputs, evidence artifacts, run records, and a
> report of what was completed or blocked.
>
> **The researcher decides:** whether assumptions are plausible, whether a
> deviation is acceptable, and whether the result answers the question.

**What to say:**

Use `/cr-work` to carry out the plan or a named phase. It keeps the research
checks active during execution. If the work uses randomness, a seed must be
recorded. If it makes a substantive claim, the source and evidence must be
recorded. If it implements a derived model, the derivation and code must be
compared. If the work reaches a consequential normative choice, the decision
gate is revisited rather than silently defaulted.

For the local evidence workbench, this is also where source identity, source
version, typed locators, candidate records, and verification state become
concrete artifacts. The exact checks depend on the task type, but the principle
is stable: a result should leave enough evidence for someone else to inspect
how it was produced.

**Transition:**

Execution produces material. Review asks whether that material is adequate,
correctly supported, and fit for the intended use.

**Evidence status:** Directly documented in `.github/prompts/cr-work.prompt.md`
and `cr-skill-research-workflow`; package-specific details are supported by
`C008-C014` in the existing evidence matrix.

### Slide 14. `/cr-review`: bring the right reviewers to the result

**Time:** 45 seconds

**On the slide:**

> `/cr-review`
>
> Review the work through research and engineering lenses matched to the task.
>
> **Leaves behind:** prioritized findings, unresolved risks, and a decision
> about what must change before the result is used.
>
> **The researcher decides:** how to respond to a finding and whether the
> remaining limitations are acceptable for the audience and purpose.

**What to say:**

Use `/cr-review` when the work needs a deliberate check. The command combines
shared reviewers for code quality, testing, reproducibility, data quality,
performance, architecture, documentation, and version control with research
reviewers for integrity, provenance, identification, econometrics, machine
learning, measurement, writing, publication output, or replication.

The task type helps determine which research reviewer is relevant. A
measurement task needs attention to weighting, thresholds, clusters, and
comparability. A causal design needs identification diagnostics. A writing
task needs a provenance and argument check. Review is therefore not a generic
last read. It is a check chosen for the kind of claim being made.

**Transition:**

After the result has been checked, the final command turns experience into
institutional memory.

**Evidence status:** Directly documented in `.github/prompts/cr-review.prompt.md`
and `docs/reference/agents.md`.

### Slide 15. `/cr-compound`: retain the lesson

**Time:** 35 seconds

**On the slide:**

> `/cr-compound`
>
> Capture a verified research lesson for future work.
>
> **Leaves behind:** a dated solution note with the problem, approach, reason it
> works, failure modes, and references.
>
> **The researcher decides:** whether the lesson is general enough to reuse and
> where it should not be applied.

**What to say:**

Use `/cr-compound` after a research problem has been solved and checked. It
captures the reasoning, not only the final answer. The note records what was
unclear, what approach worked, why it worked, and when it would fail.

That matters for applied research because a decision about a poverty line, a
survey-weighted estimate, a data restriction, or a literature-search strategy
can otherwise disappear into one project folder. A compound note makes the
lesson available to the next researcher, with its limits attached.

**Transition:**

The five commands are shared entry points. The next question is how the system
knows which research route to prepare.

**Evidence status:** Directly documented in `.github/prompts/cr-compound.prompt.md`.

### Slide 16. Where classification happens

**Time:** 50 seconds

**On the slide:**

```text
/cr-brainstorm
  identify the task type -> researcher confirms or corrects it
        |
        v
/cr-plan
  record the type -> design the evidence and checks
        |
        v
/cr-work and /cr-review
  load the relevant skills, gates, and reviewers
```

Small footer: `Classification routes the work.`

**What to say:**

The decision is made in `/cr-brainstorm`, after the project bearings are clear
and before the clarifying questions and approach are finalized. The command
proposes a task type from the fixed taxonomy. The researcher confirms or
corrects it.

The selected type is then carried into the plan. During work, it determines
which research safeguards and method guidance matter. During review, it helps
select the relevant research agents. The shared evidence, normative, and
integrity checks still apply across the task types.

This is routing, not automation of judgment. If a request changes, the task
type can be reconsidered. If a task combines kinds of work, the plan should say
which part is being addressed and what additional checks are needed.

**Transition:**

Behind that route is a set of skills and reviewers. Practitioners do not need
to manage them one by one, but it helps to know what kinds of expertise are
available.

**Evidence status:** Directly documented in
`.github/prompts/cr-brainstorm.prompt.md`, `.github/prompts/cr-plan.prompt.md`,
`.github/prompts/cr-work.prompt.md`, and `.github/prompts/cr-review.prompt.md`.

### Slide 17. The work after task classification

**Time:** 30 seconds

**On the slide:**

| Task type | Agents for this task type |
|---|---|
| Research Scoping | `@cr-specification-analysis`, `@cr-provenance-audit` |
| Theory/Modeling | `@cr-identification-audit`, `@cr-econometric-reasoning`, `@cg-adversarial` |
| Specification Analysis | `@cr-specification-analysis` |
| EDA | `@cg-performance`, `@cg-data-quality` (shared reviewers; no dedicated CR EDA agent yet) |
| Implementation | `@cg-performance`, `@cr-ml-methodology`, `@cr-specification-analysis`, `@cr-publication-output` (when output-producing code is present) |
| ML/Prediction | `@cr-ml-methodology`, `@cr-specification-analysis`, `@cg-performance` |
| Writing | `@cr-academic-writing`, `@cr-provenance-audit` |
| Tables/Figures | `@cr-publication-output`, `@cg-documentation` (when exported functions are present) |
| Reproducibility | `@cr-replication-package` |
| Measurement/Classification | `@cr-measurement-integrity` |

At the bottom:

> Across the route: `@cr-research-integrity` and the shared `cg` reviewers
> remain available when the review scope calls for them.

**What to say:**

This is what happens after task classification. The left column lists the ten
kinds of research work. The right column shows the agents the review route
brings in for each kind.

For example, a theory or modeling task brings identification and econometric
reasoning into the review. A measurement task brings measurement integrity. A
writing task brings academic writing and provenance. EDA uses shared
performance and data-quality reviewers because there is not yet a dedicated CR
EDA reviewer.

Some agents are conditional. Implementation may need publication-output review
when the code produces tables or figures. Tables and Figures may need
documentation review when the file defines exported functions. The shared
research-integrity and `cg` reviewers remain available across the route.

**Transition:**

All of these routes become more useful when the claim itself carries enough
information to be checked.

**Evidence status:** Directly documented in `docs/reference/agents.md`, the
research workflow skill, and the task-specific skill and agent files listed in
Appendix B.

### Slide 18. Proof Carrying Claim: the claim brings its support

**Time:** 1 minute

**On the slide:**

> **Proof Carrying Claim (PCC)**
>
> **Trigger:** any substantive claim intended for reuse. PCC is most visible in
> **Communicate**, especially **Writing**, but it can originate in evidence,
> theory, measurement, EDA, or data work.
>
> For a literature claim: source, version, locator, quotation, relationship,
> and review state.
>
> For a data finding: data source, definition, sample, method, run record,
> diagnostic, and review state.

Small footer: `PCC is a traceability idea, not a guarantee that the claim is true.`

**What to say:**

Proof Carrying Claim is not a separate task type. It is a rule that applies
whenever research produces a substantive claim intended for reuse.

It is most visible in the Communicate part of the lifecycle, especially in a
Writing task, because that is where a claim enters a report, paper, or briefing.
But the claim record is assembled upstream, and the same rule applies to a data
finding, a measurement choice, a theory statement, an EDA result, or a
specification claim.

An important claim should not travel alone. It should bring the evidence and the
checks that let another person inspect it.

For a literature claim about global poverty measurement, that might be the
source document, its version, the page or paragraph locator, the quotation, the
relationship between the quotation and the claim, and the review state.

For a data finding, the corresponding support might be the data source and
variable definition, the sample restriction, the specification or code, the
run record, the diagnostic, and the review state.

The word proof needs a boundary here. The plugin can verify that a quotation
matches a source unit or that a record satisfies an approval rule. That does
not prove that the source is true, that a causal interpretation is identified,
or that a policy conclusion is normatively correct.

**Transition:**

The plugin handles the record and the checks. The researcher still turns a
reviewed record into an argument.

**Evidence status:** PCC is the presentation's organizing concept. Its concrete
record structure is grounded in `C011-C014` and the current evidence-workbench
sources in Appendix C.

### Slide 19. From source to written prose

**Time:** 1 minute 5 seconds

**On the slide:**

```text
long research paper
  p. 15, paragraph 3
    ->
  atomic claim
    ->
literature review paragraph
```

The review paragraph points to the atomic claim, and the atomic claim points
back to `p. 15, paragraph 3` in the paper.

**What to say:**

This slide is deliberately simple. Imagine a research paper with many pages of
text. The procedure extracts an atomic claim from that text and preserves its
location: for example, page 15, paragraph 3.

Later, when we write a literature review, a sentence or paragraph can point to
the atomic claim, and the claim can point back to the exact place in the paper.
The reader does not have to search the whole paper to recover the support.

This is the basic approach used by Rafael in the Data Quality Assessment work:
long documents were divided into addressable text segments so drafted
statements could be returned to their sources.

The plugin supports the link by keeping source segments addressable and keeping
the claim record distinct from the prose. This is a slight oversimplification
of the full evidence workflow, chosen to make the core idea visible. `[C006]`,
`[C008-C014]`

**Transition:**

The final safeguard concerns choices that no evidence or model can make on a
researcher's behalf.

**Evidence status:** The diagram is a simplified representation of the current
claim/evidence workflow, grounded in `C006` and `C008-C014`. The attribution to
Rafael's Data Quality Assessment work is supplied by the presentation owner;
the repository-local evidence records document the addressable text-segment
pattern but do not independently identify Rafael by name.

### Slide 20. Normative decisions remain human decisions

**Time:** 1 minute 30 seconds

**On the slide:**

> `/cr-brainstorm` and `/cr-work` surface consequential choices.
>
> 1. Identify the choice.
> 2. State defensible options and consequences.
> 3. Ask the human decision-maker.
> 4. Record the decision and its scope.
> 5. Recheck it when the output or context changes.
>
> Start with `/cr-brainstorm` when the research question is still taking shape.

**What to say:**

A normative decision is a choice about what should count, who is included, how
burdens or benefits are described, or which comparison should anchor the
argument. In applied poverty and inequality research, examples can include a
threshold, a weighting rule, a sample restriction, an outlier policy, or the
language used to describe distributional effects.

The workflow does not hide these choices inside a prompt or a model. The
research scoping rules provide a bounded checklist for the task type. If an
existing decision record covers the same study, category, context, and option,
the workflow can reuse it. If it does not, the workflow stops and presents
defensible options and their consequences to a human. The decision is recorded
with a stable ID, its scope, the person or role who decided, the justification,
and the date.

That record is not bureaucracy added after the research. It is part of the
evidence about how the research was framed. It lets a later researcher see
which choices were technical, which were empirical, and which required
judgment.

The practical starting point is `/cr-brainstorm`: state the research question,
let the workflow identify the likely task type, correct it if needed, and make
the consequential choices visible before the work begins.

**Evidence status:** Directly documented in
`.github/prompts/cr-brainstorm.prompt.md`, `.github/prompts/cr-work.prompt.md`,
and `cr-skill-research-scoping`. The examples are illustrative applications of
the documented decision categories.

### Slide 21. This plug-in is for us

**Time:** 45 seconds

**On the slide:**

> This plug-in is for us.
>
> It should support effective and responsible AI use in research.

**Next priorities:**

- Improve existing skills.
- Add new skills.
- Bring in external source-discovery tools, such as OpenAlex, for literature
  review.

**What to say:**

This plug-in is for us. It should support effective and responsible AI use in
research, and it should improve through actual use.

The next priorities are to improve the skills that already exist, add new skills
where researchers need them, and bring in external source-discovery tools such
as OpenAlex to make literature review more useful.

Please use it and send feature requests. The only way to make the plug-in
useful for you is to learn from the work you are actually trying to do. I will
send around instructions on installation, getting started, and submitting
feature requests.

**Evidence status:** This is a closing commitment and invitation from the
presentation owner, not a claim about completed product work.

## Email-ready narrative

**Subject:** Using AI in applied research without losing the evidence trail

The research module is an extension of the Compound GPID workflow that many of
us already know: brainstorm, plan, work, review, and compound. It is intended
for research where the result may become a paper, a policy brief, an official
statistic, or institutional knowledge.

The starting point is a practical concern. AI can make it easier for an
unsupported statement to enter a research workflow. A claim may lose its
connection to the source that motivated it. A repeated generation may change an
emphasis or omit a qualification. The system may select one passage or
interpretation without showing what it left out. Once fluent language is in a
report, it can be repeated because it sounds settled. These are reasons to keep
the route from evidence to claim visible, not reasons to stop using AI.

AI can help researchers find and sort material, compare definitions and
methods, summarize long documents, suggest questions, and draft alternative
wording. For a global poverty measurement project, those are real sources of
research effort. But a researcher still decides whether a source is
appropriate, whether a comparison is fair, whether a qualification survived a
summary, which specification is defensible, and what can responsibly be said.

The `cr` module keeps the familiar five-step loop and gives it a research
lifecycle: scope, evidence, theory, method, execute, verify, communicate, and
maintain. The commands are entry points into that lifecycle.

`/cr-brainstorm` is for a question that is not yet fully specified. It
identifies the research task type and asks the researcher to confirm or correct
it. It also surfaces value-laden choices that should not be hidden inside a
technical default. The result is a clearer question, a scoping record, a named
route, and a visible decision list.

`/cr-plan` turns that clarified question into steps, assumptions, evidence
requirements, test scenarios, and acceptance criteria. It carries the task
type into the plan, so later work can use the relevant guidance and review
surfaces. The researcher still decides which design is proportionate and what
would count as a credible answer.

`/cr-work` executes the plan. Research-integrity checks remain active during
the work. Random operations need recorded seeds. Substantive claims need
source and evidence records. A derived model needs a comparison between its
derivation and its implementation. A consequential decision that is not
already covered needs to return to the human decision-maker. The output is
working material plus the evidence and run records needed for inspection.

`/cr-review` brings the appropriate reviewers to the result. It combines shared
checks for code, tests, paths, data quality, reproducibility, performance,
architecture, documentation, and version control with research-specific checks
for integrity, provenance, identification, econometrics, machine learning,
measurement, writing, publication output, or replication. The task type helps
select the relevant research lens.

`/cr-compound` captures a verified lesson. It records the problem, the approach,
why it works, failure modes, and references. The result is a dated piece of
institutional knowledge that another researcher can reuse without losing the
conditions under which it applies.

The workflow recognizes ten kinds of research task: Research Scoping,
Theory/Modeling, Specification Analysis, Measurement/Classification,
ML/Prediction, Implementation, EDA, Tables/Figures, Writing, and
Reproducibility. They are categories of work, not grades. A measurement
question about poverty thresholds needs different guidance from a writing
question about a results section. A prediction exercise needs different checks
from a causal identification argument. The task type is proposed in
`/cr-brainstorm`, confirmed by the researcher, carried into `/cr-plan`, and
used by `/cr-work` and `/cr-review` to assemble relevant safeguards and
reviewers.

This routing is supported by research skills and agents. The skills cover
research scoping, evidence and provenance, structural econometrics,
mathematical derivation, theory-data dialogue, EDA, machine learning,
measurement, replication, academic writing, and publication output. Research
review agents cover integrity, provenance, identification, econometrics,
machine learning, specification, measurement, writing, replication, and
publication output. The shared `cg` reviewers remain available for code,
testing, data quality, reproducibility, performance, architecture,
documentation, and version control. Practitioners do not need to select every
component manually; the route assembles them around the task.

This leads to the idea of a **Proof Carrying Claim (PCC)**. An important claim
should bring its support with it. A literature claim should carry the source,
source version, locator, quotation, relationship between evidence and claim,
and review state. A data finding should carry the data source and definition,
sample, method or code, run record, diagnostic, and review state.

The word proof is deliberately limited. The plugin can help verify that a
quotation matches a source unit and that a record meets an approval rule. It
cannot establish that the source is true, that a causal interpretation is
identified, that a model is fully reproducible across environments, or that a
normative conclusion is correct.

The path from source to prose is therefore explicit:

```text
original source -> source unit with locator -> candidate evidence and claim
-> verification -> researcher review -> approved evidence record
-> analysis and written prose
```

Original resources remain authoritative. Derived text, indexes, and browser
views help with discovery and inspection. Candidate material remains distinct
from approved evidence. If the source changes, affected records can become
stale and require review again. A model may suggest a claim, but the source and
review record determine what can travel into an analysis or a paragraph.

Normative decisions remain human decisions. The workflow surfaces choices such
as thresholds, weights, sample restrictions, outlier rules, and framing
language. It states defensible options and consequences, checks whether a
previous decision genuinely covers the same study and context, and stops for a
human decision when coverage is missing. The decision is recorded with its
scope, justification, decision-maker, and date.

The practical starting point is `/cr-brainstorm`. Use it when the question is
still taking shape. Let it propose the task type, correct that proposal when
needed, and make the decisions that matter visible before the research work
begins.

## Appendix A. Plain-language vocabulary

| Term | Meaning in this presentation |
|---|---|
| Source | The original document, dataset, table, or other material used in research. |
| Source unit | An addressable part of a source, such as a paragraph, page, table row, or variable definition. |
| Evidence | Material recorded because it supports, contradicts, or contextualizes a claim. |
| Claim | A statement that can be examined against evidence. |
| Atomic claim | One statement kept small enough to support, question, or leave unresolved. |
| Candidate | Proposed material that has not passed the verification and review steps. |
| Approved evidence | Evidence that meets the relevant verification, confidence, authority, freshness, and review conditions. |
| Provenance | The record of where material came from and how it was handled. |
| PCC | Proof Carrying Claim: an important claim carries the evidence and verification trail needed to inspect it. |
| Normative decision | A consequential choice about what should count, who is included, or how findings are framed. |
| Task type | A description of the kind of research work currently being done; it routes guidance and review. |

## Appendix B. Research work, skills, and agents

### Skills

The research suite includes shared workflow and integrity guidance plus
specialist skills for:

- research workflow, research scoping, evidence and provenance, and research
  integrity;
- structural econometrics, mathematical derivation, symbolic verification, and
  theory-data dialogue;
- research-framed EDA, machine-learning methodology, and measurement;
- academic writing, publication output, and replication standards.

### Research review agents

The research review route can dispatch:

- `@cr-research-integrity` for silent research errors and integrity gates;
- `@cr-provenance-audit` for source, citation, and claim traceability;
- `@cr-econometric-reasoning` and `@cr-identification-audit` for structural and
  causal reasoning;
- `@cr-specification-analysis` for theory-data and specification discipline;
- `@cr-ml-methodology` for prediction methodology;
- `@cr-measurement-integrity` for indicators, thresholds, clustering, and
  comparability;
- `@cr-academic-writing` for research prose;
- `@cr-publication-output` for tables and figures; and
- `@cr-replication-package` for replication materials.

The shared route also uses `@cg-code-quality`, `@cg-testing`,
`@cg-reproducibility`, `@cg-data-quality`, `@cg-version-control`,
`@cg-documentation`, `@cg-performance`, and `@cg-architecture` when the
review scope calls for them.

### Method packs in plain language

The workflow groups related task types for orientation:

| Method pack | Task types | What changes |
|---|---|---|
| Structural | Theory/Modeling and Specification Analysis | Theory, identification, functional form, and econometric review. |
| ML | ML/Prediction | Prediction target, leakage, validation, and economic interpretation. |
| Measurement | Measurement/Classification | Weighting, thresholds, clusters, validity, and comparability. |

These packs change the method-specific guidance and review surfaces. The
shared scope, evidence, normative, communication, and integrity responsibilities
still apply.

## Appendix C. Source anchors and evidence boundaries

### Repository-local sources

- `compound-gpid.md`: project objective, research-suite deliverable, and
  correctness constraints.
- `docs/reference/commands.md`: public list of research workflow commands.
- `docs/reference/agents.md`: public research-agent capabilities.
- `.github/prompts/cr-brainstorm.prompt.md`: classification, researcher
  confirmation, scoping, normative gate, and brainstorm handoff.
- `.github/prompts/cr-plan.prompt.md`: plan structure and task-type carryover.
- `.github/prompts/cr-work.prompt.md`: execution, evidence, seed, derivation,
  and normative gates.
- `.github/prompts/cr-review.prompt.md`: shared and task-specific review
  routing.
- `.github/prompts/cr-compound.prompt.md`: verified research-lesson capture.
- `.github/skills/cr-skill-research-workflow/SKILL.md`: ten task types,
  lifecycle, method packs, integrity priorities, and evidence layout.
- `.github/skills/cr-skill-research-scoping/SKILL.md`: problem framing,
  success criteria, and bounded normative decision taxonomy.
- `c-research/evidence/claim-evidence-matrix.yaml`: verified and
  abstained presentation claims `C001-C017`.
- `c-research/normative-decisions/ai-knowledge-work-presentation.md`:
  approved framing, caveat, and comparison decisions for the broader
  presentation study.

### Current evidence-workbench anchors

The earlier presentation manuscript and claim matrix document the current
package boundary and its source-linked state model:

- local-first, project-contained, offline normal processing and loopback-only
  browser service (`C008-C009`);
- candidate-only optional retrieval/model adapters (`C010`);
- source-linked candidate proposals from untrusted model output (`C011`);
- candidate claims after a lightweight atomicity check (`C012`);
- approval conditions for high verification, confidence, authority, review, and
  non-stale state (`C013`); and
- original resources, canonical records, and review history as authority while
  indexes and browser views are derived (`C014`).

The previous 30-minute manuscript remains available at
`2026-08-13-ai-knowledge-work-presentation.md` for the longer AI-DQSS lineage,
source register, and technical appendix. It is not the source for the revised
15-minute slide order.

### Evidence boundaries

- The risks in Slide 1 and the PCC label are conceptual framing for this talk.
- No performance, coverage, productivity, or model-quality metric is claimed.
- No repeated-run demonstration is included, so stochastic instability remains
  an abstained conceptual claim rather than a measured result.
- Verification of a quotation is not verification of the truth of the source,
  causal validity, full reproducibility, or normative correctness.
- The presentation describes current plugin contracts and current package
  anchors; future source discovery or richer literature interfaces are not
  described as completed features.

## Appendix D. Speaker checklist

Before presenting:

- Keep the first slide on research risks, not software architecture.
- Give the audience the practical AI-help slide before introducing safeguards.
- Treat the `cg` loop as familiar shared ground.
- Keep each command slide to purpose, durable output, and human decision.
- Explain the task taxonomy as routing, not ranking.
- Say that PCC means traceability and verification, not a guarantee of truth.
- Give one literature example and mention data findings as the parallel case.
- End with normative decisions and `/cr-brainstorm` as the practical starting
  point.
