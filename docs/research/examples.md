# Research Examples and Use Cases

These illustrative briefs show how to use Compound Research on applied
economic and policy work. They are workflow examples, not empirical findings
or completed studies. Use authorized data and choose methods with the researcher.

Activate `suites: [cr]` or `suites: [cg, cr]` through
[setup](../getting-started/index.md). Each example follows
[/cr-brainstorm, /cr-plan, /cr-work, /cr-review, and /cr-compound](first-workflow.md),
with approval and verification between stages.

## Reproduce a published poverty estimate

**Question:** can the team recover a published figure and explain any discrepancy?

Start `/cr-brainstorm`, then provide:

```text
Plan a replication of the poverty headcount in the specified report table.
First confirm the exact table, survey version, population, welfare aggregate,
weight, price basis, poverty line, and PPP vintage where applicable.
Inventory the authorized data and code available to us.
Do not substitute a nearby dataset or definition without approval.
Separate a successful replication from an explanation of discrepancies.
```

**Plan and outputs:** a source inventory, definition/coverage table, approved
calculation, reproducible script, comparison with the target, and discrepancy log.

**Checks before acceptance:** recover the stated denominator and weighting
rule; account for exclusions and missing values; independently cross-check a
small synthetic calculation; distinguish rounding from substantive differences;
confirm another authorized researcher can reproduce the result. An unavailable
input remains a limitation, not permission to invent a match.

## Evaluate a policy intervention

**Question:** what would support a credible claim about an intervention's effect?

```text
Help scope an evaluation of the specified intervention and outcome.
Clarify the policy decision, target population, treatment timing, available
comparison groups, estimand, and data access.
Compare feasible identification approaches and their assumptions.
Do not select a method solely because the dataset contains a treatment flag.
List what evidence would weaken or prevent a causal interpretation.
```

**Plan and outputs:** an explicit estimand, causal argument, candidate designs,
data feasibility assessment, approved analysis plan, and interpretation limits.

**Checks before acceptance:** timing and assignment support the chosen design;
measurement and sample construction are documented; diagnostics address the
actual identifying assumptions; uncertainty and sensitivity checks match the
design; claims stay within what the evidence supports. If no defensible design
is available, a documented descriptive result may be the appropriate outcome.

## Assess a welfare prediction model

**Question:** does a model predict usefully for the intended population and use?

```text
Scope a welfare prediction exercise using the authorized survey data.
Clarify the prediction target, use at deployment, and which features would
actually be available then. Propose evaluation splits that avoid household,
geographic, temporal, and preprocessing leakage as relevant.
Compare against a simple baseline and examine performance across meaningful
groups. Do not interpret predictive associations as causal effects.
```

**Plan and outputs:** target and feature definitions, a split strategy,
baseline, reproducible training/evaluation pipeline, and a limitations record.

**Checks before acceptance:** held-out outcomes do not influence training or
preprocessing; tuning is separated from final evaluation; results can be
reproduced; subgroup errors and distribution shift are examined; intended use
and human review requirements are explicit.

## Turn verified results into a policy brief

**Question:** how can approved findings be communicated without overstating them?

```text
Plan a two-page policy brief from the approved analysis and source materials.
Identify the audience and decision first. Build a claim-to-evidence table.
Distinguish findings, interpretation, and policy options.
Use only verified numbers; preserve uncertainty, caveats, and source attribution.
Propose one chart that supports the central finding.
```

**Plan and outputs:** an audience brief, evidence map, draft narrative,
reproducible chart, references, and a review record.

**Checks before acceptance:** every number and substantive claim maps to
approved evidence; chart labels and denominators agree with the analysis;
causal language matches the design; limitations survive editing; publication
review and permissions are complete. Rendering a polished brief does not
establish that its content is ready for publication.

## Explore a climate-risk example

The [Kenya precipitation walkthrough](short-example.md) follows a location-based
question through data selection, coverage checks, an approved extreme-event
definition, reproducible calculations, and maps/charts for dissemination.

## Reuse the process, not an unchecked conclusion

After `/cr-review`, resolve serious findings and rerun relevant checks. Use
`/cr-compound` to capture a verified method or lesson with its evidence and
limits. See [Evidence, Review, and Boundaries](evidence-boundaries.md) and the
[research skills catalog](../skills/research.md) for deeper guidance.
