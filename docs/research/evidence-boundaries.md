# Evidence, Review, and Boundaries

<!-- Created 2026-09-03. -->

CR treats evidence as part of the research output, not as something to
reconstruct after the writing is finished. The basic path is:

```text
resource -> source unit -> evidence -> claim -> reviewed composition
```

A source unit might be a page and paragraph in a paper, a data release and
variable definition, a code output, or a documented model derivation. The
locator should make it possible for another researcher to return to the
relevant support.

## Proof Carrying Claim

**Proof Carrying Claim** is the plain-language rule that an important claim
intended for reuse should carry its supporting evidence and checks. A
literature claim may carry a source version, quotation, locator, relationship
between evidence and claim, and review state. A data finding may carry the data
source, variable definition, sample restriction, code or specification, run
record, diagnostic, and review state.

PCC is not a separate task type or a promise that a source is true. It is a
traceability requirement that can begin in Evidence, Theory, Measurement, EDA,
or data work and becomes especially visible when results are communicated.

## Review and consequential choices

`/cr-review` matches review to the work. A causal design needs identification
checks; a measurement task needs attention to weights, thresholds, clusters,
comparability, and sensitivity; a writing task needs provenance and argument
checks; an implementation task needs code, tests, and reproducibility.

Research also contains normative choices about what should count and who is
included. Examples include a threshold, weighting rule, sample restriction,
outlier policy, comparison group, or language used to describe distributional
effects. CR surfaces alternatives and consequences and records the human
choice. It does not smuggle that choice in as a technical default.

## What CR does not establish

CR can help make a process more inspectable, but it cannot establish by itself
that:

- a source is true or authoritative in every relevant sense;
- a causal design identifies the claimed effect;
- a model, threshold, weighting rule, or classification is normatively correct;
- a generated answer is stable across model runs or providers; or
- a result is fit for publication, policy use, or release.

Researchers remain responsible for interpretation, assumptions, conclusions,
and release decisions. When a serious review finding remains unresolved, keep
the work blocked or clearly label the limitation rather than compounding it as a
settled lesson.

Return to the [CR philosophy](philosophy.md) or continue with the [research
lifecycle](lifecycle.md).
