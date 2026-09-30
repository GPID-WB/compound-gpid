---
date: 2026-09-03
title: "CR ML Skill Redesign Review"
scope: "Canonical CR ML skill, references, routing, tests, documentation, generated targets, and derived audit evidence"
plan: ".cg-docs/plans/2026-09-03-cr-ml-skill-redesign.md"
review-mode: "full"
findings:
  P0.1: fixed
  P0.2: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: fixed
  P1.7: fixed
  P1.8: fixed
  P1.9: fixed
  P1.10: fixed
  P1.11: fixed
  P1.12: fixed
  P1.13: skipped
  P1.14: fixed
  P1.15: fixed
  P1.16: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P2.9: fixed
  P2.10: skipped
  P3.1: fixed
  P3.2: fixed
skipped_reasons:
  P1.13: "Skipped under fix-triage permissions: the work report and generated context-audit artifacts are outside the permitted edit scope; reconcile them in a dedicated evidence-maintenance pass."
  P2.10: "Skipped under fix-triage permissions: the work report is outside the permitted edit scope; reconcile its deviation metadata in a dedicated evidence-maintenance pass."
---

# Review: CR ML Skill Redesign for Econometricians

## Review scope and routing

Reviewed the uncommitted changes on `feat/cr-ml-skill-redesign` relative to
`HEAD` (`1ef1227`). The review included the canonical `.github` sources, all
eight ML references, CR routing, tests and fixtures, documentation, generated
native bundles/manifests, and derived context-audit evidence. The 14 intentional
untracked source/evidence paths were included in the review scope even though
`git diff` does not list them.

The resolved route is `full`: the project config requests thorough review and
the change includes a large research-skill refactor, statistical methodology,
context routing, generated targets, and documentation validation.

Dispatched shared reviewers: `@cg-code-quality`, `@cg-testing`,
`@cg-reproducibility`, `@cg-data-quality`, `@cg-version-control`,
`@cg-documentation`, `@cg-performance`, `@cg-architecture`.

Dispatched research reviewers: `@cr-research-integrity`,
`@cr-provenance-audit`, `@cr-ml-methodology`, and
`@cr-specification-analysis`. Thorough-review lenses `@cg-learnings-researcher`
and `@cg-adversarial` were also dispatched. `@cr-mathematical-verification`
was skipped because no `.tex` or `.md` derivation files are present under
`c-research/derivations/`; provenance review ran because `c-research/evidence/`
exists.

## Review Findings

### P0 — Blocking

**[P0.1]** [Malformed approximate-sparsity notation](.github/skills/cr-skill-ml-economics/references/high-dimensional-and-regularized-methods.md#L128)

**Evidence:** The canonical reference contains a literal U+0008 BACKSPACE in
`where $<control character>eta_0$` instead of `where $\\beta_0$`. The same byte
is present in each generated native copy.

**Impact:** A central high-dimensional definition can render as invalid or
misleading mathematics. This is a silent research-methodology error in a
reference intended to guide econometricians.

**Fix:** Replace the control character with `\\beta`, regenerate all native
bundles and manifests, and add a control-character/encoding regression test.

**[P0.2]** [Unseeded stochastic R forest example](.github/skills/cr-skill-ml-economics/references/implementation-r-tidymodels.md#L113)

**Evidence:** The `ranger` engine is configured with permutation importance but
no engine seed, and the nearby forest workflow does not establish a seed before
fitting. The repository's research-integrity policy treats unseeded stochastic
ML operations as P0.

**Impact:** Forest fits and importance rankings can depend on ambient RNG state,
parallel execution, or call order, undermining reproducibility when the example
is copied into research code.

**Fix:** Add an explicit numeric `seed` at the engine/fitting boundary and show
how the split, resampling, tuning, and final-fit seeds are recorded. Also
cross-check `@cr-research-integrity` Check 4.

### P1 — Critical

**[P1.1]** [Seed policy falsely rejects deterministic or estimator-seeded Python workflows](.github/agents/cr-ml-methodology.agent.md#L181)

**Evidence:** The ML reviewer universally requires `random_state` or a global
RNG seed for `KFold`, `GroupKFold`, `StratifiedKFold`, and `RidgeCV`, while the
Python reference uses deterministic `GroupKFold(n_splits=5)` with default
`shuffle=False`. `/cr-work` likewise accepts only `np.random.seed()` or
`random.seed()` in its active seed gate ([cr-work](.github/prompts/cr-work.prompt.md#L109)).

**Impact:** Correct code using estimator-level `random_state` can be falsely
halted, and deterministic splitters may be “fixed” with unsupported arguments.
This weakens confidence in the P0 seed gate.

**Fix:** Define stochasticity explicitly. Require seeds for `shuffle=True`,
randomized search, stochastic estimators, direct RNG calls, bootstrap, or
randomized SVD; accept estimator-level seeds and record deterministic splitter
parameters without inventing randomness.

**[P1.2]** [Nested cross-validation is incorrectly rejected](.github/agents/cr-ml-methodology.agent.md#L107)

**Evidence:** Check 2 says any tuning requires a separate final test set. The
splitting reference correctly states that nested cross-validation can provide
an outer assessment loop without a three-way split ([splitting reference](.github/skills/cr-skill-ml-economics/references/splitting-resampling-and-evaluation.md#L49)).

**Impact:** Valid nested-CV designs may receive a false P1 finding, and users
may unnecessarily sacrifice observations or contaminate a final holdout to
satisfy the reviewer.

**Fix:** Require either an untouched final holdout or a correctly specified
nested outer/inner evaluation design, and make the estimand of the reported
performance explicit.

**[P1.3]** [Split and stratification checks are not target-conditional](.github/agents/cr-ml-methodology.agent.md#L97)

**Evidence:** The panel rule treats random within-panel splits as invalid for
all tasks, although the reference distinguishes new-row prediction within known
units from new-unit prediction. The stratification rule requires
`StratifiedKFold`/`strata=` without first conditioning on group or temporal
separation ([ML agent](.github/agents/cr-ml-methodology.agent.md#L125)).

**Impact:** Valid known-unit forecasts can be rejected, while applying ordinary
stratification to panel or temporal data can destroy the dependence structure
that the evaluation is supposed to preserve.

**Fix:** Require the reviewer to establish the generalization target first:
known rows, new units, future periods, or target population. Then require
cluster/group, temporal, blocked group-time, and optional within-block
stratification in that order.

**[P1.4]** [Out-of-sample check hard-codes regression metrics](.github/agents/cr-ml-methodology.agent.md#L238)

**Evidence:** Check 7 requires RMSE, MAE, and/or OOS R2 for every ML result and
requires a separate test set. The references support classification metrics,
calibration, and cross-fitted causal scores, but the reviewer does not branch
on prediction product or task.

**Impact:** Valid classification and DML workflows can be falsely rejected;
reviewers may push researchers toward inappropriate regression metrics or an
unnecessary holdout.

**Fix:** Branch the check by regression, probability prediction, ranking,
hard-label classification, forecasting, or causal-score evaluation. Require
appropriate held-out evidence, calibration/PR-AUC/log loss where relevant, and
DML estimand/overlap/inference checks rather than universal regression metrics.

**[P1.5]** [R forest workflow bypasses identifier exclusion](.github/skills/cr-skill-ml-economics/references/implementation-r-tidymodels.md#L118)

**Evidence:** The recipe assigns `unit_id` a non-predictor role
([implementation-r-tidymodels.md#L71](.github/skills/cr-skill-ml-economics/references/implementation-r-tidymodels.md#L71)),
but the forest workflow uses `add_formula(outcome ~ .)`, bypassing that recipe
and potentially including the identifier.

**Impact:** A flexible panel model can memorize unit IDs and produce invalid
new-unit performance or fail on unseen levels.

**Fix:** Use the identifier-aware recipe in the forest workflow or explicitly
exclude `unit_id`; require the choice to match the stated generalization target.

**[P1.6]** [DML nuisance notation is ambiguous and not implementation-safe](.github/skills/cr-skill-ml-economics/references/econometric-causal-ml.md#L34)

**Evidence:** The reference defines `g(X)` as the structural baseline in
`Y = theta D + g(X) + epsilon`, then instructs users to fit `g(X)` directly as
the outcome nuisance ([econometric-causal-ml.md#L55](.github/skills/cr-skill-ml-economics/references/econometric-causal-ml.md#L55)).
In partially linear DML, the directly learned outcome nuisance is normally
`ell(X) = E[Y | X]`, distinct from the structural baseline `g(X)`.

**Impact:** A user can implement the wrong nuisance regression while believing
it matches the displayed orthogonal score, invalidating the target estimate.

**Fix:** Define `ell(X)` explicitly, use it consistently in the score and
cross-fitting procedure, and distinguish it from the structural `g(X)`.

**[P1.7]** [Classification examples leave the positive event implicit](.github/skills/cr-ml-economics/references/implementation-r-tidymodels.md#L153)

**Evidence:** The R metric set omits `event_level`, and the Python guidance
lists classification metrics without fixing the positive class or probability
column ([implementation-python-scikit-learn.md#L165](.github/skills/cr-skill-ml-economics/references/implementation-python-scikit-learn.md#L165)).

**Impact:** PR-AUC, sensitivity, specificity, recall, and threshold decisions
can silently target the wrong class, especially when a rare positive is coded
as the second factor/category.

**Fix:** Declare the event/positive class in every example, use the explicit
`event_level`/`pos_label` or probability-column mapping supported by the
library, and add a non-default class-order test.

**[P1.8]** [Survey review omits validity, domain-support, and missingness gates](.github/agents/cr-ml-methodology.agent.md#L262)

**Evidence:** Check 8 verifies target population, weight definition, estimator
support, design structure, and design-based variance, but does not require
nonmissing/positive weights, extreme-weight diagnostics, effective sample
size, PSU/domain representation, or missingness/nonresponse analysis. Those
checks are required by the survey reference ([survey reference](.github/skills/cr-skill-ml-economics/references/survey-panel-and-target-population.md#L125)).

**Impact:** A weighted learner can pass review while high-weight households are
missing, a domain has no assessment support, or nonresponse is concentrated in
the outcome. This can silently bias population-risk claims.

**Fix:** Add explicit checks for weight validity and extremity, weight/domain
shares, effective sample size, PSU/domain coverage, missingness by weight and
outcome, complete-case loss, and outcome-imputation behavior. Keep this as a
high-stakes research-integrity gate, not optional advice.

**[P1.9]** [Specification-search detection covers named tuning APIs only](.github/agents/cr-ml-methodology.agent.md#L140)

**Evidence:** Check 4 scans listed APIs such as `GridSearchCV`, `tune_grid`,
`cv.glmnet`, and `xgb.cv`, while the splitting reference correctly identifies
model-class, feature, transformation, split-rule, metric, and outcome searches
as specification searches.

**Impact:** Manual fit loops or data-dependent feature/split/metric searches can
remain undisclosed even when no named tuning API appears.

**Fix:** Require an ML specification/search ledger covering candidate classes,
features, transformations, split designs, metrics, trials, selection rules,
test-set use, and the final selected configuration.

**[P1.10]** [New CR ML tests are omitted from CI and release coverage](.github/workflows/tests.yml#L49)

**Evidence:** The explicit pytest list includes `test_cr_baseline.py` but not
`scripts/tests/test_cr_ml_skill.py`; the release preflight has the same omission
in `create-release.ps1#L129`.

**Impact:** The new router, reference inventory, survey qualification, and
routing tests can regress locally without CI or release-gate detection.

**Fix:** Add `test_cr_ml_skill.py` to both explicit gates and add a regression
assertion that the required CR ML test is present in CI/release coverage.

**[P1.11]** [Routing tests are global vocabulary checks rather than route checks](scripts/tests/test_cr_ml_skill.py#L150)

**Evidence:** The fixture declares expected references, but the test searches
the entire core for each task's terms and reference names. It does not parse
route rows, assert exclusions, test an unknown task, or include the claimed
review/leakage case. A swapped association can pass while all filenames remain
present.

**Impact:** The central progressive-disclosure behavior can regress into wrong
reference selection or broad loading without a failing test.

**Fix:** Parse or structurally isolate each route row; assert exact expected
reference sets and forbidden references. Add negative cases for non-ML work,
unknown task labels, high-dimensional-plus-panel tasks, survey prediction,
rare outcomes, and review/leakage routing.

**[P1.12]** [The reproducibility gate treats `pyproject.toml` as a lockfile](.github/prompts/cr-work.prompt.md#L117)

**Evidence:** The lockfile check accepts `requirements.txt` / `pyproject.toml` /
`uv.lock` for Python, although `pyproject.toml` commonly contains version ranges
rather than a resolved dependency graph.

**Impact:** A project can pass the P0 reproducibility gate while package and
transitive versions float across machines.

**Fix:** Treat `uv.lock`, `poetry.lock`, `renv.lock`, or exact/hash-pinned
requirements as lock evidence. Treat `pyproject.toml` as project metadata
unless it contains a separately verified exact lock representation.

**[P1.13]** [Completion evidence is internally contradictory and stale](.cg-docs/work-reports/2026-09-03-cr-ml-skill-redesign.md#L64)

**Evidence:** The work report records V9 as `warnings 0, failures 0` and records
16 focused ML tests at [work report V4](.cg-docs/work-reports/2026-09-03-cr-ml-skill-redesign.md#L59).
The current generated audit reports 60 guardrail failures and 11 warnings, with
no baseline comparison; [TOKEN-DASHBOARD.md#L13](.cg-docs/token/TOKEN-DASHBOARD.md#L13)
reports `Status: fail`. The current focused test file collects 20 tests.

**Impact:** The completion record presents false-green context evidence and
understates test coverage, so downstream users cannot tell which claims were
actually verified against this worktree.

**Fix:** Re-run the audit against an explicit HEAD/worktree baseline, classify
inherited versus introduced warnings, update the report with the current test
count, and make the plan/report/active-state/dashboard agree before merge.

**[P1.14]** [Review-critical canonical sources are untracked](.github/skills/cr-skill-ml-economics/references/econometric-causal-ml.md#L1)

**Evidence:** The eight canonical references, the new CR ML test and fixture,
the public research page, and the dated brainstorm/plan/work report are
untracked. Generated mirrors are tracked/modified and depend on those sources.

**Impact:** A commit using `git commit -a`, or a handoff based only on `git diff`,
can omit the canonical source files while retaining generated outputs, leaving
broken or unsupported native content.

**Fix:** Add all intentional canonical and evidence files explicitly before
commit, then rerun generated drift and source-inventory checks. Preserve any
unrelated user changes.

**[P1.15]** [R `yardstick::rsq` does not implement the documented training-mean OOS R2](.github/skills/cr-skill-ml-economics/references/implementation-r-tidymodels.md#L134)

**Evidence:** The R example tunes and evaluates `metric_set(rmse, mae, rsq)`,
while the statistical reference defines OOS R2 against the training mean. The
standard `yardstick::rsq` is not that training-mean benchmark by default.

**Impact:** The reported R score can measure a different benchmark than the
skill's stated OOS R2, making model comparisons and claims inconsistent across
languages.

**Fix:** Define a custom training-mean OOS R2 metric or calculate it explicitly
from held-out predictions; label test-centered R2 separately.

**[P1.16]** [Python iid split example fails for continuous outcomes](.github/skills/cr-skill-ml-economics/references/implementation-python-scikit-learn.md#L32)

**Evidence:** The generic iid example uses `stratify=y` without saying that `y`
must be categorical. For continuous income or welfare outcomes, nearly unique
values can make `train_test_split` fail because strata have too few members.

**Impact:** A common regression workflow can fail at the initial split or lead
users to bin a continuous target without documenting that change.

**Fix:** Restrict `stratify` to categorical outcomes, or provide a separate
explicitly binned regression example with a documented rationale.

### P2 — Important

**[P2.1]** [Progressive-disclosure cap is per check, not per review](.github/agents/cr-ml-methodology.agent.md#L36)

**Evidence:** The agent says to read one or two references for each review
check, but mandates all eight checks. The cumulative union of the check routes
can therefore load all eight references, defeating the core's one-or-two rule
([SKILL.md#L20](.github/skills/cr-skill-ml-economics/SKILL.md#L20)).

**Impact:** A thorough ML review can recreate the monolithic context burden that
this redesign was intended to remove.

**Fix:** Set a per-file/per-review reference budget, load more only when a
concrete evidence trigger requires it, and test the cumulative reference union.

**[P2.2]** [ML-specific parity test checks inventory but not content](scripts/tests/test_cr_ml_skill.py#L230)

**Evidence:** The test compares canonical and generated relative-path sets only.
It does not compare bytes, hashes, links, or rewritten references. The broader
repository parity tests compensate for this, but running the focused ML test
alone does not.

**Impact:** The focused contract can pass with stale generated content or a
corrupted generated file that happens to have the expected name.

**Fix:** Compare hashes/content for each generated ML file or make the global
content-drift gate an explicit dependency of the focused test command.

**[P2.3]** [Research catalog validation reports completeness without requiring all CR entries](scripts/check-docs-site.js#L73)

**Evidence:** The checker compares missing entries only for technical
`cg-skill-*` skills. `researchCatalog` is used to reject unknown entries, while
[research.md#L14](docs/skills/research.md#L14) lists only `cr-skill-ml-economics`
although 15 canonical CR skill directories exist. The checker still prints
“complete skills catalog.”

**Impact:** Research skills can remain undiscoverable while the documentation
release gate reports success.

**Fix:** Either enumerate all CR skills and compare both canonical sets, or make
this an explicitly incremental ML catalog with an allowlist and change the
success message so it does not claim full catalog completeness.

**[P2.4]** [Neural-network scope is promised but not routed or covered](.github/skills/cr-skill-ml-economics/SKILL.md#L56)

**Evidence:** The core promises a bounded neural-network overview, but no route
points to a neural-network reference and the foundations reference offers only
a brief mention ([foundations-and-esl.md#L202](.github/skills/cr-skill-ml-economics/references/foundations-and-esl.md#L202)).

**Impact:** Users asking whether neural networks fit an econometric problem lack
guidance on scaling, regularization, validation, architecture choice, and
reproducibility safeguards.

**Fix:** Add a bounded routed subsection/reference, or remove the promise from
the core and public catalog for this iteration.

**[P2.5]** [Specialized package boundary for `ranger` is imprecise](.github/skills/cr-skill-ml-economics/references/implementation-r-tidymodels.md#L218)

**Evidence:** The R reference says to verify `ranger` “cluster options,” which
can imply cluster-aware variance or survey-cluster inference, although the
ordinary engine interface does not supply the full design-based uncertainty
procedure.

**Impact:** Users may infer that `ranger` handles cluster dependence or survey
inference when only fitting/sampling options are available.

**Fix:** State that `ranger` case weights and sampling options do not provide
cluster-robust or design-based variance; direct cluster handling to split design
and external uncertainty procedures.

**[P2.6]** [Starter R tuning example is unnecessarily expensive](.github/skills/cr-skill-ml-economics/references/implementation-r-tidymodels.md#L141)

**Evidence:** The example combines 10-fold CV, a 20-configuration grid,
`save_pred = TRUE`, and a 1,000-tree forest default at
[implementation-r-tidymodels.md#L112](.github/skills/cr-skill-ml-economics/references/implementation-r-tidymodels.md#L112).

**Impact:** Copying the starter pattern to survey data can create hundreds of
fits and prediction storage proportional to sample size without a stated
compute or memory budget.

**Fix:** Make prediction saving opt-in, use smaller illustrative defaults, and
state fit/thread/memory budgets for larger survey or panel workflows.

**[P2.7]** [Scholarly references are not fully traceable](.github/skills/cr-skill-ml-economics/references/foundations-and-esl.md#L224)

**Evidence:** Most references provide author-year/title only, without journal,
publisher, DOI, pages, or stable landing page. The rare-outcome PR-AUC claim
also lacks the Davis and Goadrich (2006) citation used in the former monolith.

**Impact:** Researchers cannot reliably retrieve or audit the methodological
basis of important recommendations.

**Fix:** Add complete bibliographic records and stable identifiers/URLs, restore
Davis and Goadrich for the PR-AUC claim, and correct any truncated titles.

**[P2.8]** [Focused route tests do not test generated content or semantic safeguards](scripts/tests/test_cr_ml_skill.py#L110)

**Evidence:** Reference checks assert substrings and inventory, so the malformed
math byte, missing event-level semantics, missingness/domain gates, and
conditional seed rules can all coexist with green focused tests.

**Impact:** Future edits can remove a high-risk safeguard while preserving the
same broad keywords.

**Fix:** Add targeted structural/content assertions for equations, forbidden
control characters, route-local associations, event coding, target-conditional
splits, survey validity, and stochastic versus deterministic operations.

**[P2.9]** [Characterization fixture includes unrelated generated hash repairs](scripts/tests/fixtures/cg_characterization_manifest.json#L249)

**Evidence:** The fixture refresh changes hashes for pre-existing `cg-setup`,
`setup-templates`, and `cg-skill-setup` outputs in addition to the CR ML assets.
Those canonical files are not part of this redesign.

**Impact:** Unrelated generated churn obscures the ML change and makes review or
rollback harder.

**Fix:** Separate the stale baseline repair into its own change, or document the
exact pre-existing generator drift and why it must be updated here.

**[P2.10]** [Execution-report deviation metadata contradicts itself](.cg-docs/work-reports/2026-09-03-cr-ml-skill-redesign.md#L22)

**Evidence:** The report says “No deviations approved” but also records a
post-run blocker repair under `deviation-policy: ask` at
[work report#L38](.cg-docs/work-reports/2026-09-03-cr-ml-skill-redesign.md#L38).

**Impact:** The durable report does not clearly show whether the repair was
approved, in scope, or an exception.

**Fix:** Record the explicit approval/decision in the policy summary, or classify
the docs-checker repair as in-scope and remove the deviation entry.

### P3 — Advisory

**[P3.1]** [Detailed references are not directly discoverable from the public catalog](docs/skills/research.md#L25)

**Evidence:** The eight reference names are plain code spans rather than links
to canonical files or navigable documentation pages.

**Impact:** Readers must manually browse the repository to reach the detailed
method guidance.

**Fix:** Link each reference to its canonical source or expose a dedicated
reference-navigation surface without counting references as separate skills.

**[P3.2]** [ML implementation still loads derivation guidance for every implementation task](.github/prompts/cr-work.prompt.md#L36)

**Evidence:** The ML route correctly loads `cr-skill-ml-economics` conditionally,
but the adjacent rule still loads `cr-skill-mathematical-derivation` for every
`Implementation` task, even when no derivation artifact exists.

**Impact:** Unnecessary context expansion and possible confusion between
predictive ML implementation and derived structural-model implementation.

**Fix:** Make derivation loading conditional on a declared or detected
`c-research/derivations/` artifact.

## Clean areas

- The compact core is materially smaller and preserves the strongest boundaries:
  target/estimand framing, prediction versus causality, leakage, dependence,
  seeds, weights, and final assessment.
- The eight-reference separation is coherent and follows the repository's
  progressive-disclosure pattern.
- The substantive foundations on target population, loss/risk, baselines,
  high-dimensional regularization, trees, DML, and survey-design limitations
  are generally strong once the defects above are corrected.
- Generated native bundles have recursive inventory parity and deterministic
  content; the broader target drift and closure tests compensate for the
  focused parity test's content gap.
- No derivation-to-code mismatch was assessed because no derivation files are
  present. No study-specific provenance violation was found; generic skill
  documentation was not treated as a research output requiring claim-evidence
  rows.
- No secrets, unsafe path, symlink, or module-ownership issue was found.

## Verification context

Previously recorded validation remains relevant: the focused CR ML tests passed
20/20 at review time, the broader script suite passed 910 tests with one skip,
the locked `research_evidence` suite passed 122 tests, the docs-site checker
passed after its catalog-logic repair, and the safe Pester suite passed 2,448
tests with zero failures. This review itself was read-only and did not rerun
those suites.

The review should not be considered merge-ready while either P0 finding is open,
or while the P1 review-rule/evidence inconsistencies remain unresolved.
