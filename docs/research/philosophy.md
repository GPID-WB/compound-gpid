# Why Compound Research Exists

<!-- Created 2026-09-03. -->

Research has always moved from resources to notes, from notes to claims, and
from claims to a paper, report, or decision. AI can make each step faster, but
it can also make a polished answer appear before its source, uncertainty, or
reasoning has been inspected.

Compound Research puts useful AI assistance inside a workflow that keeps the
path from evidence to claim to composition visible. It is designed to support
research judgment, not to replace it.

## The four risks

- **Source detachment**: a fluent claim may have no recoverable source, or its
  source may not support what the claim says.
- **Epistemic instability**: a generative run can produce different claims,
  omissions, or emphases across runs. A seed or low temperature can improve
  control, but does not guarantee identical output across providers, model
  revisions, or serving environments.
- **Selection opacity**: a system may choose one source passage,
  interpretation, or caveat from several plausible alternatives without making
  that choice visible.
- **Amplified composition**: once a plausible sentence enters a report or
  institutional workflow, its fluency can make it easier to repeat than to
  question.

These risks do not mean that AI assistance is unusable. They mean that a
researcher should be able to inspect what a claim is based on, what was chosen,
what remains uncertain, and who accepted the result.

## The stable research object

A generated answer is a proposal. It can help search, compare, summarize,
organize questions, or suggest a method. It is not automatically an approved
research claim.

An important claim should carry enough context for another researcher to
inspect it:

- the source and its version;
- a locator such as a page, table, paragraph, variable, or code output;
- the evidence supporting the claim;
- the relationship between the evidence and the claim;
- the method, assumptions, and checks that matter; and
- the review state and remaining limitations.

This is the plain-language idea behind **Proof Carrying Claim**. It is a
traceability rule for substantive claims intended for reuse, not a separate
command or task type.

## What CR can and cannot do

CR can help a researcher scope a question, organize evidence, compare methods,
record decisions, execute planned work, review outputs, and preserve lessons.
It can make the process more inspectable and make missing support harder to
ignore.

CR cannot establish by itself that a source is true, that a causal design is
valid, that a threshold is normatively correct, or that a result is fit for
publication. Researchers remain responsible for interpretation, assumptions,
conclusions, and release decisions.

## Human decisions stay visible

Applied research includes choices about the population, comparison, threshold,
weighting rule, sample restriction, outlier policy, and language used to
 describe distributional effects. CR surfaces these choices and records the
alternatives and consequences instead of hiding them inside a prompt or a
model.

The practical starting point is the [first CR workflow](first-workflow.md).
