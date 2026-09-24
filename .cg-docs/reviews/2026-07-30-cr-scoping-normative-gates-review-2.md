---
date: 2026-07-31
depth: full
type: standard
plan: .cg-docs/plans/2026-07-30-cr-scoping-normative-gates.md
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
---

## Review Report

**Review mode**: full (composite coverage with research agents per shared routing contract)
**Files reviewed**: 643
**Findings**: 9 (P0: 0, P1: 4, P2: 5, P3: 0)

Auto-routing applied: research-task signals across the CR workflow surfaces plus security-risk signals from install/update/link/release paths. Resolved review mode: full. Mandatory emphasis: research-integrity coverage plus adversarial coverage on operational tooling.

### P1 - CRITICAL (must fix before merge)
- **[P1.1]** [cg-architecture] .github/prompts/cr-review.prompt.md:206 - `/cr-review` still writes a legacy review frontmatter schema that does not match `/cg-fix-triage`
  **Why**: The prompt still emits `status: open` plus `findings: N` and then tells users to run `/cg-fix-triage` by finding ID. The generic fix-triage flow expects the `/cg-review` finding-status map shape (`findings: { P1.1: open|fixed|skipped }`). That makes the CR review artifact a producer/consumer mismatch on a canonical remediation path.
  **Fix**: Align `/cr-review` report frontmatter with the `/cg-review` tracking schema, or stop routing users from `/cr-review` directly to `/cg-fix-triage` until a CR-compatible schema/consumer path exists.

- **[P1.2]** [cr-provenance-audit] .cg-docs/work-reports/2026-07-30-cr-scoping-normative-gates.md:52 - CR phase reports still treat `tests/last-run.json` as durable historical evidence for prior phase-specific validation claims
  **Why**: `tests/last-run.json` is a mutable runner artifact that is overwritten on subsequent runs. The work reports cite it as if it were a stable proof object for earlier phase-specific checks, including the `tests/cr-prompts.Tests.ps1 -> tests/last-run.json` claim in this phase report. That weakens provenance for the exact validation events the CR governance surfaces are meant to make traceable.
  **Fix**: Replace mutable `tests/last-run.json` citations in CR work reports with run-stamped immutable snapshots or committed summary artifacts, and keep the report text scoped to evidence that the cited artifact can actually prove.

- **[P1.3]** [cg-code-quality] .github/prompts/cg-review.prompt.md:24 - `/cg-review` research route drifted from the shared routing contract
  **Why**: The canonical review entry point still parsed only the older five explicit modes and its Research dispatch block omitted `@cr-provenance-audit` and `@cr-measurement-integrity`, despite the shared contract treating both as first-class research reviewers.
  **Fix**: Fixed during review autofix. `/cg-review` now accepts explicit `research`, dispatches the full shared research agent set, documents composite `full + research` coverage for research plus security-risk diffs, and the prompt-tools guard suite now enforces those surfaces.

- **[P1.4]** [cg-testing] tests/Run-Tests.ps1:212 - Canonical test artifact omitted explicit skipped/unaccounted counts
  **Why**: The runner previously derived top-level totals without exposing the non-passed/non-failed remainder explicitly. That allowed downstream evidence language to overstate reconciliation even when the artifact still contained a silent gap.
  **Fix**: Fixed during review autofix. `tests/Run-Tests.ps1` now records `skippedCount` plus per-file `skipped`, and `tests/run-tests-runner.Tests.ps1` now requires exact reconciliation: `totalCount = passedCount + failedCount + skippedCount`.

### P2 - IMPORTANT (should fix)
- **[P2.1]** [cg-documentation] .github/prompts/cg-setup.prompt.md:137 - Wiki initialization failure still directs users to `/cg-wiki rebuild` instead of `/cg-wiki init`
  **Why**: `rebuild` presumes an existing `_wiki.yml`, but the failure path here is exactly the case where initialization did not finish and no manifest may exist. The rest of the branch documents `init` as the bootstrap path for this state.
  **Fix**: Change the recovery message to point users to `/cg-wiki init`.

- **[P2.2]** [cg-documentation] docs/getting-started/index.md:8 - Packaging limitation note contradicts the current generated-target packaging contract
  **Why**: The page still says generated non-canonical skill mirrors do not include every progressively loaded support file, while the current packaging docs and branch behavior describe atomic target bundles generated from the canonical `.github/` source.
  **Fix**: Update or remove the outdated limitation note so getting-started guidance matches the shipped packaging model.

- **[P2.3]** [cg-version-control] .posit/assistant/settings.json:2 - Editor-local Posit Assistant settings are committed with sandbox disabled
  **Why**: This is local IDE state rather than canonical project source, and it weakens local safety defaults across clones without any explicit repository policy describing why it belongs in version control.
  **Fix**: Remove `.posit/assistant/settings.json` from the branch and ignore it, or document explicitly why shared Posit settings with sandbox disabled are intentional project configuration.

- **[P2.4]** [cg-documentation] docs/reference.md:147 - CR command metadata and review-route docs were stale relative to canonical prompt frontmatter and routing
  **Why**: The public reference still showed all `/cr-*` commands as Claude Sonnet 4 and omitted the `research` review mode from `/cg-review` docs, even though the canonical prompts and routing contract had moved on.
  **Fix**: Fixed during review autofix. `docs/reference.md`, `docs/workflow.md`, `docs/model-guide.md`, and the corresponding guard tests now match the shipped CR command models, review-mode surface, and CR review-agent inventory.

- **[P2.5]** [cr-specification-analysis] .github/prompts/cr-compound.prompt.md:53 - CR compounding taxonomy lagged the 10-type research workflow
  **Why**: The solution-file `task-type:` enum still stopped at `Reproducibility`, so captured lessons from `Measurement/Classification` and `Research Scoping` could not be tagged consistently with the rest of the CR workflow.
  **Fix**: Fixed during review autofix. `cr-compound.prompt.md`, `.github/copilot-instructions.md`, and `tests/cr-prompts.Tests.ps1` now include the new task types and the scoping/normative integrity summary.

### ⚠️ Incomplete Reviews
- `@cr-mathematical-verification` did not produce usable output due to a network error. Consider re-running `/cg-review full` or invoking `@cr-mathematical-verification` directly when network stability returns.
- `@cr-identification-audit` did not produce usable output due to a network error. Consider re-running `/cg-review full` or invoking `@cr-identification-audit` directly when network stability returns.
- `@cr-econometric-reasoning` did not produce usable output due to a network error. Consider re-running `/cg-review full` or invoking `@cr-econometric-reasoning` directly when network stability returns.
- `@cr-academic-writing` did not produce usable output due to a network error. Consider re-running `/cg-review full` or invoking `@cr-academic-writing` directly when network stability returns.
- `@cr-publication-output` did not produce usable output due to a network error. Consider re-running `/cg-review full` or invoking `@cr-publication-output` directly when network stability returns.

> Review report saved to `.cg-docs/reviews/2026-07-30-cr-scoping-normative-gates-review-2.md`. Use `/cg-fix-triage` in a future session to apply findings by ID (for example `/cg-fix-triage P1.1 P2.1`) or by priority level (for example `/cg-fix-triage P1`).