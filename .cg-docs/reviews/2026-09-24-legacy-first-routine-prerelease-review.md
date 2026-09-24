---
date: 2026-09-24
depth: full
type: standard
plan: .cg-docs/plans/2026-09-24-legacy-first-routine-prerelease.md
findings:
  P1.1: skipped
  P2.1: fixed
  P2.2: fixed
---

# Legacy-First Routine Prerelease Review

## Route And Scope

Requested `mode:verify`; resolved to a normal `full` security-risk review, **not**
a verification of fixes. The most recent eligible report by frontmatter date and
filename is `.cg-docs/reviews/2026-09-16-documentation-ia-ux-redesign-review.md`
(date 2026-09-17, four fixed findings). Its fixed blocks concern the docs UI,
search and help projection, not this Routine publisher. The related September 17
prerelease Phase 3 review also predates these new changes. Suppressing this release
scope under either prior report would not review the new path.

Reviewed the 31 tracked changed paths and four untracked context artifacts in the
working tree: the canonical release prompt and help definitions; `create-release.ps1`,
`scripts/release-legacy-authority.ps1`, `scripts/cg_release_cli.py`; their Pester
and pytest tests; generated `.agents`, `.claude`, `.kilo` and `.opencode` release,
help, shell and manifest targets; docs/reference, commands, controller and
versioning; and the active-state pointer. Generated targets were checked by
drift tests rather than treated as independent sources. No view bodies were read.

Agent-role protocols for code quality, testing, documentation, version control,
reproducibility, performance, architecture, data quality, learnings and adversarial
review were applied locally. No native Task/subagent dispatch was available here:
these are not ten independent second opinions. Protected artifacts were not
recommended for deletion or replacement. No source or remote state was changed.

## Review Report

**Review mode**: full (normal security-risk fallback, not verify)
**Files reviewed**: 31 tracked changes plus 4 untracked context artifacts
**Findings**: 3 (P0: 0, P1: 1, P2: 2, P3: 0)
**Status**: failed security review; P1.1 remains open

### P0 - Blocking

None found. This is not a clearance to publish.

### P1 - Critical

- **[P1.1]** [cg-adversarial] `create-release.ps1:810-830`,
  `scripts/release-legacy-authority.ps1:90-96` - Routine policy reads cannot
  prevent cutover between the final check and the tag push.
  **Why**: A cutover to `enabled: true` after the final authority read at line 810
  but before the `git push` at line 816 can admit the new Routine tag while the
  controller has already become active. The later authority recheck at line 827
  blocks the Release POST, but the immutable remote tag exists and its push can
  trigger the docs workflow. This is a partial publication across the policy
  boundary, not an atomic reservation. The existing Bridge fixture deliberately
  models the same interleaving at `tests/create-release.Tests.ps1:1055-1060`.
  The approved focused plan explicitly does not provide an exclusive publisher;
  it cannot establish race-free cutover by repeated reads alone.
  **Fix**: Resolve manually with a mutually controlled cutover/publication
  protocol that fences the tag creation effect and its matching Release, or
  explicitly accept and document the residual partial-publication risk under
  separate authority. Do not label the current Routine path race-free or use
  local test success as proof of live exclusivity.
  **Disposition**: manual; no security-sensitive autofix was applied.

### P2 - Important

- **[P2.1]** [cg-testing] `tests/create-release.Tests.ps1:756-777,1055-1060` -
  New Routine tests omit the cutover-after-tag-push branch.
  **Why**: They exercise disabled-policy success and enabled/missing-policy
  rejection before effects, but only Bridge runs with `CutoverAfterPush`. A
  Routine regression that posts a Release after the controller enables would
  not be caught by the new tests.
  **Fix**: Add a Routine fixture transition after the push and assert the tag
  remains exact, no Release POST occurs, and the interruption is reported.
  **Disposition**: manual because it tests a publication authority boundary.
- **[P2.2]** [cg-documentation] `.github/prompts/cg-release.prompt.md:169-175` -
  Stranded-payload guidance still directs an explicit legacy selector.
  **Why**: A four-part Routine payload without a local tag is told to use an
  exceptional selector and `--resume`. Routine is now the default for a
  four-part resume, while Bridge/Recovery need separate authorization. This
  guidance can route an ordinary repair to the wrong operation or block it.
  **Fix**: Distinguish the authorized Routine repair from a separately approved
  Bridge/Recovery recovery case; do not grant tag creation as part of resume.
  **Disposition**: manual; the repair procedure needs a maintainer decision.

### P3 - Minor

None found.

## Verification Evidence And Limits

- Focused launcher pytest: 26 passed. Generated-target drift pytest: 24 passed.
- `cg_generate_help_catalog.py --check` and `--check-docs`: current.
  `git diff --check`: clean. Generator `--all --dry-run` completed without a write.
- Combined drift/help test run timed out at 120 seconds; the standalone help
  pytest run timed out at 300 seconds after partial progress. Neither is a
  passed test suite. An attempted generator `--check` was invalid because that
  option does not exist; the drift test is the valid check.
- Pester was not re-run in this review; the focused green Pester counts in the
  completed plan are prior implementation evidence, not a fresh review gate.
  No unfiltered full suite or live release/cutover was run. No independent
  multi-agent output or live remote-state proof is claimed.

## Handoff

Parsed 3 standard finding IDs, all open. `/cg-fix-triage` may start in a future
pipeline step to address these findings, with P1.1 first; publication and any
claim that security review passed remain blocked. No fix-triage or later pipeline
step was executed here.
