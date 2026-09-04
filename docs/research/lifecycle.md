# Research Lifecycle and Task Types

<!-- Created 2026-09-03. -->

CR follows a lifecycle that keeps a research question, its evidence, and its
communication connected:

| Stage | Guiding question |
|---|---|
| **Scope** | What question and decision are we addressing? |
| **Evidence** | What sources or data can support the work, and can they be recovered? |
| **Theory** | What mechanism, model, or identification argument matters? |
| **Method** | Which design, measure, estimator, or comparison fits the question? |
| **Execute** | What work produces the planned outputs? |
| **Verify** | Do the evidence, code, assumptions, and results withstand review? |
| **Communicate** | How should the result and its limitations be explained? |
| **Maintain** | Can another researcher recover the environment, choices, and result? |

The stages are a spine, not a rigid recipe. A project can return to an earlier
stage when evidence changes the question or a review exposes a weak assumption.

## Task types describe the work

Task types answer a different question from the lifecycle: what kind of work is
being done now? A single project can contain several types.

| Task type | Typical work |
|---|---|
| **Research Scoping** | Frame an open question and surface consequential choices before a plan is fixed. |
| **Theory/Modeling** | Derive an economic model, data-generating process, or identification argument. |
| **Specification Analysis** | Choose regressors, functional forms, interactions, or specifications from theory and evidence. |
| **EDA** | Explore data with checks motivated by the research question. |
| **Implementation** | Code a previously derived model, estimator, or analysis. |
| **ML/Prediction** | Build prediction-focused statistical learning with economic interpretation and appropriate evaluation. |
| **Measurement/Classification** | Construct and test indicators, thresholds, clusters, labels, or comparisons. |
| **Writing** | Explain the question, evidence, methods, results, and limitations in research prose. |
| **Tables/Figures** | Produce publication-quality tables, charts, maps, or other research outputs. |
| **Reproducibility** | Preserve environments, seeds, paths, data documentation, and replication materials. |

## How classification helps

`/cr-brainstorm` proposes a task type and the researcher confirms or corrects
it. The selected type carries into planning, where it helps identify the right
evidence and checks. During review, it helps route relevant research and
engineering reviewers, such as identification, econometrics, measurement,
provenance, publication, data quality, or reproducibility.

Classification is routing guidance. It is not a judgment about the importance
or quality of the research, and it does not remove shared integrity or human
review requirements.

The [short workflow example](short-example.md) shows how one applied question
can move across several task types. The [Commands reference](../reference/commands.md)
contains the complete command contracts.
