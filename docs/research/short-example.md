# Short Workflow Example: Extreme Precipitation in Kenya

<!-- Created 2026-09-03. -->

This short example shows the shape of a CR workflow. It is not a complete
climate-analysis tutorial and it does not claim that the study has already been
conducted.

## The question

> Assess the risk of extreme precipitation at a project site in Kenya
> (Latitude: -1.2921, Longitude: 36.8219). Get credible daily rainfall data
> from 2020 to present, define "extreme precipitation" based on a common
> practice, and calculate extreme precipitation by location. Produce materials
> to help dissemination of the findings, such as maps and charts.

## The short route

1. **Activate CR.** In `compound-gpid.local.md`, set `suites: [cr]` or
   `suites: [cg, cr]`, then start `/cr-brainstorm`.
2. **Frame the task.** The researcher and `/cr-brainstorm` clarify the decision
   the result should inform, the site and spatial unit, the period, the target
   population or location, and what "risk" should mean. The initial work may
   combine Research Scoping, EDA, Implementation, and Tables/Figures; the
   researcher confirms the useful framing.
3. **Plan evidence and methods.** `/cr-plan` records candidate daily rainfall
   sources, coverage and resolution checks, coordinate or grid-cell handling,
   the extreme-event definition, sensitivity checks, and the map/chart outputs.
4. **Execute with records attached.** `/cr-work` retrieves the approved data,
   checks dates, missingness, units, and location coverage, calculates the
   selected indicator, and records source metadata, code, parameters, and
   outputs while the work happens.
5. **Review before dissemination.** `/cr-review` checks data quality,
   statistical and methodological choices, reproducibility, and whether maps
   and charts support the stated result. Resolve serious findings before
   treating the output as ready to share.
6. **Capture the lesson.** After the checks pass, `/cr-compound` records what
   worked, what was uncertain, and when the method should not be reused.

## Make the definition explicit

A common-practice candidate might define an extreme day using a site-specific
95th percentile of wet-day daily rainfall, with a 99th-percentile sensitivity
check. Other defensible choices include an annual maximum one-day total or a
standardized climate index. The workflow should compare the relevant choices
and record the selected definition before calculation; it should not let a
model silently choose a threshold.

The same applies to the rainfall source. A credible source must be checked for
coverage from 2020 to the present, daily resolution, units, spatial meaning,
and suitability for the project site. A source link alone is not evidence that
the data answer the question.

## What the first result should leave behind

A proportionate result might include:

- a source and coverage record;
- the approved definition and sensitivity choices;
- a reproducible calculation and location-handling note;
- a checked summary, map, and chart; and
- review findings, limitations, and a clear dissemination status.

The example demonstrates how to get off the ground. The researcher still
judges whether the data, definition, uncertainty, and communication are fit for
the decision.

Continue with the [research lifecycle and task types](lifecycle.md) or the
[full first-workflow guide](first-workflow.md).
