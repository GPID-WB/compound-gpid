# Working with AI Responsibly

Compound GPID was inspired by Compound Engineering, but engineering workflow
is only part of what high-stakes analytical work requires. This page states the
second philosophy that grounds the plugin: use AI in ways that preserve human
judgment, make reasoning inspectable, and prevent the distance between generated
work and understood work from growing.

This is not a promise that a tool makes AI safe by itself. It is a standard for
how people should use the tool, and an explanation of the structures Compound
GPID provides to make that standard practical.

> **AI is not the risk. The gap is.**
>
> The dangerous gap is between what AI generates and what a human genuinely
> understands, owns, and can independently evaluate.

## Why unstructured AI use is not neutral

Using a general chat interface for consequential work can feel efficient, but
it changes where risk lives. The following problems are not hypothetical
details around an otherwise neutral process. They are predictable consequences
of using a tool without a specification, evidence trail, or independent check.

### 1. The wrong tool creates false progress

A general chat interface is not a project harness. Unless the user supplies
the context manually, the model does not see the repository, data, project
conventions, tests, or the history of decisions. That creates several risks:

- The model works from what the user remembers and describes, not from the
  files that actually exist.
- It can invent plausible paths, functions, APIs, or project conventions.
- The user becomes an error-prone copy-and-paste intermediary.
- Confidential or preliminary information can be placed in a consumer product
  without an appropriate governance decision.
- There is no review specification telling the model what must be checked.
- The next session starts from zero because the reasoning has no durable home.

The most insidious result is a conversation that feels productive while
producing no tested, integrated artifact. For institutional work, a useful
conversation is not the same thing as implemented and verified work.

> A long conversation about code can create the feeling of progress while
> leaving behind zero lines of working, tested, integrated output.

### 2. Review can become an illusion

The idea that AI can do the work and a person can review it manually sounds
responsible. In practice, two forces undermine it:

- **Automation bias:** polished, fluent, well-commented output is often
  examined less critically than equivalent human-written output.
- **Volume pressure:** when AI increases production by 10 times, review becomes
  the bottleneck and can turn into rubber-stamping.

There is also a circular validation trap. If the same AI system writes the code
and writes the tests, passing tests are not independent evidence of correctness.
The same misunderstanding can generate both the defect and a test that fails to
notice it. This is a structural loss of independence, not a problem solved by
asking for more tests in the same conversation.

### 3. Accepting code you cannot explain creates liability

Vibe coding means accepting generated output that the user cannot explain. The
consequences are practical and institutional:

- You cannot reliably debug or extend the work.
- Your maintenance ability becomes dependent on a model that may change or be
  unavailable.
- Security problems, injection risks, weak authentication, and insecure
  defaults can enter silently.
- New team members do not develop the diagnostic reasoning needed when the tool
  fails.

The answer "the AI did it" is not a defensible explanation for code, a model,
or an official estimate. The person who accepts and submits the work owns the
responsibility for understanding it.

### 4. Individual use creates organizational risks

When AI-assisted work remains in private conversations, risks spread beyond one
person or one file:

- **Accountability breaks:** decisions and responsibility cannot be traced.
- **Errors homogenize:** the same model and the same blind spots can create
  correlated failures across teams.
- **Speed outruns understanding:** deployment and production move faster than
  comprehension and review.
- **Reproducibility collapses:** nondeterministic tools make it difficult to
  reconstruct how a result was produced.

For a team publishing official poverty statistics under the World Bank name,
these are not abstract concerns. A locally plausible mistake can become a
shared institutional mistake.

## The deepest problem is epistemic

The operational risks above can often be reduced with better process. The
deeper problem concerns knowledge itself: what we believe, how we know it, and
whether we can still judge the quality of our own work.

AI output often feels trustworthy because it is confident, fluent, plausible,
and well structured. Those signals are powerful precisely because they usually
carry useful information in human interaction. With AI, they do not carry the
same information.

### Confidence without calibration

When a human expert says, "I am not sure," that hesitation can be a meaningful
signal. It is shaped by years of feedback about when their judgment succeeds or
fails. AI does not have that property. Its hedges and qualifications are
patterns of language, not an honest measurement of reliability.

The same confident style can accompany an answer that is 95 percent right and
one that is 40 percent right. The words do not tell us where the model is near
the edge of its knowledge.

### The competence asymmetry

Experts can often catch errors in their domain. That lets them develop a more
accurate sense of when AI is useful and when it is unreliable. Outside their
expertise, they may not be able to catch the errors at all, and can instead
develop a false sense of reliability.

The uncomfortable rule is:

> Where reliable information matters most, you may be least equipped to
> evaluate whether the AI is right.

This matters in a mixed team. An economist may be unable to assess an AI answer
about software architecture, while a developer may be unable to assess an AI
answer about identification, survey design, or poverty measurement. Expertise
in one area does not transfer automatically to verification in another.

### Sycophancy contaminates the question

The user's framing shapes the answer. Asking, "Is my regression specification
correct?" invites validation. Asking, "What are the strongest objections to my
specification?" invites criticism. The model is not providing an independent
evaluation in either case; it is completing a narrative established by the
conversation.

Most people naturally use AI to confirm a belief. Responsible use requires the
opposite discipline: use it to attack the belief and expose what would make it
wrong.

### Fluency looks like reasoning

Well-structured prose creates a cognitive impression of careful thought. We
associate clear expression with intelligence and understanding because that is
often a useful shortcut with human speakers. A fluent argument for a false
conclusion defeats that shortcut.

The dangerous output is not always an obvious error. It can be a beautiful
results table accompanied by a confident but subtly wrong interpretation that
looks ready for publication.

### Hallucination is structural

Hallucination is not only a temporary defect waiting to be eliminated. The model
has no external oracle that checks every statement against ground truth before
it produces the statement. It generates probable continuations from patterns in
its training and context.

Models will become better and hallucinations will be reduced. They will not
become zero. A workflow that depends on the model never being wrong will fail.
A workflow that expects errors and verifies important claims independently can
remain robust when the model is wrong.

### Erosion of our own calibration

Judgment develops through a feedback loop:

> Produce -> evaluate -> discover that you are wrong -> update your model of
> quality.

When AI produces the work and the person only evaluates it, the activity can
feel like learning without exercising the same muscles. Over time, the
internal metric that says "this is wrong" can atrophy. The tool being used as a
replacement for judgment may not be available precisely when it is most needed.

This is slow and easy to miss. It is not an argument for doing every task
manually. It is an argument for being deliberate about which tasks we continue
to do ourselves because they develop the expertise needed to evaluate future
work.

## The common structure of the risks

The epistemic risks compound when several conditions are present:

- The human has not specified intent before AI acts.
- The output cannot be independently verified.
- There is no persistent record of what was decided and why.
- The process produces outputs faster than people can understand them.

The philosophy is a response to that pattern. It does not ask people to use AI
less as a matter of principle. It asks them to use AI in ways that preserve,
rather than erode, human epistemic agency: the ability to think independently,
make informed judgments, and evaluate what one is responsible for.

## Seven principles for responsible AI use

### 1. Specification is for you, not the AI

Before asking AI to do anything consequential, state:

- What exactly do I want?
- What would a correct result look like?
- What would an incorrect result look like?
- How would I tell the difference?

Writing the specification makes intent explicit to the person who must later
judge the result. Without a standard for correctness, there is nothing real to
review. Brainstorming and planning are not bureaucratic preambles; they are how
the human builds that standard.

### 2. Generate hypotheses, then verify independently

AI is useful for generating first drafts, candidate approaches, alternatives,
and code shaped to a specification. It is not a reliable validator of the
candidate it generated. Generation and verification are different phases and
must be treated as different responsibilities.

Independent verification can include tests defined by the human, cross-software
comparison, reference values, executed checks, or review by a colleague who can
challenge the result. Asking the same model to write a test for its own code is
not enough. For this team, an R result compared with a trusted Stata result can
be meaningful evidence when the comparison is designed and recorded properly.

### 3. Default to adversarial, not trusting

The natural question is, "Does this seem right?" The disciplined questions are:

- What would make this wrong?
- What edge case would break it?
- Which assumption has not been verified?
- What would a skeptical expert object to?

This is the Referee 2 principle: become the reviewer trying to make the work
fail. Adversarial questioning is not cynicism. It is a way to counter
sycophancy, fluency, and automation bias and discover the truth about output
quality.

### 4. Protect your epistemic independence

Use AI as an amplifier of judgment, not as a replacement for judgment.

- In your domain, use AI for drafts that you can critically evaluate, not for
  conclusions you accept without understanding.
- Outside your expertise, use AI to develop understanding, not to skip the
  understanding you need to evaluate its answer.
- Do not accept output that you cannot independently verify unless you have
  consciously identified and accepted the risk.

This principle is deliberately not presented as a future feature request. A
tool can ask for a plan and display review findings, but only the person can
decide whether they understand and genuinely endorse them.

### 5. The artifact is the reasoning, not only the output

Code can compile, an analysis can look clean, and a document can be beautiful.
None of these facts proves that the right decisions were made. The valuable
artifact is the record of reasoning:

- What was the problem, precisely?
- Which approaches were considered?
- Why was this approach chosen?
- What risks were known and what limitations were accepted?

That record lets a reviewer who was not present evaluate the work. It gives the
team a source for methodological choices such as a poverty line, welfare
aggregate, harmonization rule, or validation threshold. Without it, the team
has outputs without source and decisions without provenance.

### 6. Calibrate trust by failure mode

"I trust AI for coding" and "I do not trust AI for analysis" are both too
coarse. Trust must be mapped to types of failure, and the map must be updated
as models and tasks change.

AI may be structurally useful for code structure, documented concepts, reviewed
drafting, common patterns, and generating alternatives. It is structurally less
reliable for precise calculations, citations, post-training information,
specialized edge cases, and private or local knowledge.

The map is not created by accepting a general reputation for a model. It is
created by observing where it fails, identifying the kind of failure, and
adjusting future skepticism. That ongoing observation is itself professional
knowledge.

### 7. Shared cognition requires shared artifacts

Private AI use is invisible. If one person discovers a methodological pitfall
in a chat log and another person cannot find it, the organization has not
learned. The second person is likely to repeat the first person's work and
mistake.

Team epistemic integrity requires decisions to be visible, challengeable, and
findable. Artifacts committed to a shared repository turn individual AI use into
organizational intelligence. The team starts from accumulated judgment instead
of starting from zero each time.

## How Compound GPID makes the philosophy practical

Compound GPID is infrastructure for practicing these principles. It is not the
philosophy itself, and it cannot make a person thoughtful by adding commands.
Used mechanically, it creates overhead. Used with critical engagement, it makes
intent, evidence, disagreement, and institutional memory easier to preserve.

The core loop is:

```text
/cg-brainstorm -> /cg-plan -> /cg-work -> /cg-review -> /cg-fix-triage -> /cg-compound
```

| Stage | Human responsibility | AI and plugin responsibility | Durable evidence |
|---|---|---|---|
| Brainstorm | Define the problem and evaluate approaches | Explore tradeoffs and challenge assumptions | `.cg-docs/brainstorms/` |
| Plan | Approve the specification and acceptance criteria | Structure tasks and surface missing details | `.cg-docs/plans/` |
| Work | Supervise, understand the change, and catch scope creep | Implement against the approved plan | Code and tests |
| Review | Judge findings critically and decide what is acceptable | Search for failures through risk-matched review routes | `.cg-docs/reviews/` |
| Fix and verify | Confirm the fix and the evidence | Apply bounded changes and report what remains | Verification record |
| Compound | Check that the lesson is accurate and reusable | Extract a durable pattern from verified work | `.cg-docs/solutions/` |

The human responsibility column is the point. This is not AI doing the work
while a person watches passively. Brainstorm and plan record human intent;
review and verification require human judgment; compound turns verified
reasoning into team memory.

### What the plugin minimizes

- **Wrong-tool risk:** project-linked files, conventions, prompts, skills, and
  artifacts provide a harness instead of relying on copied context.
- **False progress:** the workflow asks for plans, code, tests, review records,
  and captured lessons rather than treating conversation as the deliverable.
- **Review illusion:** explicit review stages and risk-based agents make review
  a visible activity with findings and evidence instead of an unrecorded
  feeling that the output looks good.
- **Unexplainable code:** specifications, acceptance criteria, tests, and review
  findings create a trail that makes implementation easier to inspect and
  defend.
- **Organizational memory loss:** committed `.cg-docs/` artifacts preserve
  decisions, known limitations, and solutions for the next person.
- **Epistemic drift:** explicit intent, adversarial prompts, independent checks,
  and reasoning records narrow the gap between generated work and understood
  work.

### What it covers structurally

The current plugin provides meaningful structural support for five of the seven
principles:

- `/cg-brainstorm` and `/cg-plan` put specification before generation.
- `/cg-review` creates a separate, explicit critique phase rather than making
  implementation and approval one conversation.
- Brainstorming and review routes encourage adversarial questions and findings.
- `.cg-docs/` records decisions, plans, reviews, verification, and solutions.
- Shared repository artifacts make lessons visible and searchable to future
  team members.

The structures reduce risk; they do not turn AI review into a truly independent
mind. Human peer review remains essential, especially when the work is novel or
methodologically consequential.

### What is not fully covered yet

The philosophy also makes the current gaps visible. Compound GPID does not yet
fully provide:

- An explicit confidence and uncertainty check at each stage.
- A domain-specific adversarial review that understands poverty measurement,
  survey methodology, econometric validity, and analytical interpretation as
  deeply as the subject-matter team.
- A structured cross-verification route that records the same computation in
  independent software such as R and Stata.
- A required "what would make this wrong?" checkpoint at every transition from
  plan to work to review sign-off.

These gaps are reasons to use human expertise more deliberately, not reasons to
pretend that a workflow tool has solved the epistemic problem.

## The two responsibilities no tool can take over

The following are not merely features that Compound GPID has not implemented
yet. They are human disciplines. No plugin, prompt, model, or review dashboard
can guarantee them for the user.

In plain terms, the two jobs are intellectual honesty and calibrated trust. A
plugin can reduce surrounding process risks, but no single tool can do either
job on the user's behalf.

### 1. You must protect your epistemic independence

The plugin cannot:

- Force you to read and understand the plan before approving it.
- Detect that you have rubber-stamped a review finding.
- Know when your dependence on AI is eroding your judgment, skills, or agency.
- Decide whether a limitation is acceptable in the context of your work.

If you accept review findings without understanding them, you have automated
the review and removed the value of the review. If you generate artifacts that
you cannot explain, the process has added a veneer of rigor to an unchanged
problem.

The user must remain able to explain what was done, why it was done, what could
be wrong, and what evidence supports the result. In the user's domain, that
includes interpreting analytical output and recognizing when a measure,
decomposition, weight, or validation result does not make sense. Outside the
user's domain, it means learning enough to know what must be checked by a
qualified colleague.

### 2. You must calibrate your trust by failure mode

The plugin cannot:

- Maintain a personal history of the errors AI has made for you.
- Tell you which domains you are over-trusting because you cannot detect the
  errors there.
- Develop your ability to recognize model limitations.
- Guarantee that a changed model will fail in the same way as the previous one.

Calibration is earned, not installed. Use AI, observe failures, ask what kind of
failure occurred, update your mental map, and repeat. Share recurring failure
patterns with colleagues so individual calibration can become team knowledge.

These two responsibilities are the boundary between responsible use and
process theater. The tool can create opportunities for judgment; the user must
exercise the judgment.

## What the tool will never guarantee

Compound GPID is intentionally honest about limits:

- It cannot keep a person intellectually honest.
- It cannot remove the model's tendency toward sycophancy. Adversarial prompts
  mitigate that tendency but do not create a genuinely independent mind.
- It cannot develop a person's calibration or protect skills that the person no
  longer practices.
- It cannot know what the team has not yet learned at the frontier of a new
  method, data situation, or research question.

Human expertise is always the final layer. For genuinely new work, the plugin
can help the team document assumptions, alternatives, risks, and evidence. It
cannot tell the team whether the frontier conclusion is correct.

## The question to carry into every AI-assisted task

The plugin closes the gap structurally. The philosophy closes it mentally.
Neither is sufficient alone.

> **Am I narrowing the gap, or widening it?**

Use that question before accepting an answer, approving a plan, merging a
change, or capturing a solution. If the answer is unclear, slow down, specify
the standard, seek independent evidence, or bring in a human reviewer who can
genuinely disagree.

## Relationship to Compound Engineering

Compound GPID is inspired by
[Every's Compound Engineering philosophy](https://every.to/guides/compound-engineering)
and the
[Compound Engineering plugin](https://github.com/EveryInc/compound-engineering-plugin).
That inspiration supplies the compounding workflow: deliberate requirements,
planning, implementation, review, and captured lessons make later work easier.

Compound GPID adds a distinct responsibility for institutional analytical work:
the workflow must narrow the epistemic gap between AI generation and human
understanding. It is therefore not presented as a fork, official extension, or
endorsed distribution of the upstream project.

## Source and related pages

This page distills the GPID team's presentation,
[Working with AI Responsibly](https://github.com/GPID-WB/compound-gpid_slides/blob/main/index.qmd),
including its account of operational and epistemic risks, seven principles,
plugin mapping, and human responsibility boundaries.

- [Getting Started](getting-started/index.md)
- [Why Compound GPID?](why-compound-gpid.md)
- [Governance and Security](governance/index.md)
- [Workflow Overview](workflows/index.md)
