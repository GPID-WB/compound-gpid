---
date: 2026-08-13
plan: ".cg-docs/plans/2026-08-12-automated-documentation-deployment.md"
status: active
---

# Work Report: Automated Documentation Deployment and What's New Page

## Run: 2026-08-13 All Phases

- Plan reference: `.cg-docs/plans/2026-08-12-automated-documentation-deployment.md`
- Active deviation policy: `ask` (plan stored value; no runtime override)
- Review mode: `auto`
- Scope: all phases (1-5), following the phased dispatch flow

## Completed Steps And Phases

- Phase 1 - contracts, page ownership, fixtures, and Node test entry points.
- Phase 2 - deterministic command-table and What's New generators; marker migration.
- Phase 3 - rebuild artifact workflow, Pages handoff, and durable release payload sequence.
- Phase 4 - Pester workflow contracts, native target regeneration, and parity gates.
- Phase 5 - local documentation validation matrix and canonical safe Pester run.

## Deviations

- Fixed generator defects found during implementation audit: full artifact digests,
  canonical-input freshness coverage, multiline prompt descriptions, source-tag release
  links, bounded release history, and byte-level `latest.json` matching. These changes
  remained within the plan requirements and did not widen bot permissions or release scope.

## Accepted Exceptions

- (none yet)

## Evidence

| ID | Status | Artifact |
|----|--------|----------|
| V1 | passed | `node scripts/check-docs-site.js`; Node fixtures |
| V2 | passed | 20 Node tests; consecutive `rebuild-docs --check` passes |
| V3 | passed | Node release tests; valid and invalid payload validation fixtures |
| V4 | passed | `docs-automation.Tests.ps1`; reviewed `doc-rebuild.yml` |
| V5 | passed | `docs-automation.Tests.ps1`; `node scripts/check-docs-site.js` |
| V6 | passed | `docs-automation.Tests.ps1`; payload validation command |
| V7 | passed | target generation; 280 passed/10 skipped scoped pre-commit pytest gate |
| V8 | passed | canonical safe Pester runner: passed, 0 failures |
| V9 | pending | GitHub Actions run URLs after merge |

## Constraints Check

| ID | Status | Result |
|----|--------|--------|
| C1 | passed | Fixture preservation and docs-only resolved-path guards |
| C2 | passed | Negative Node fixtures fail before write |
| C3 | passed | docs-only staging and diff guard covered by Pester contracts |
| C4 | passed | `workflow_run`, digest, freshness, and immutable-ref contracts covered |
| C5 | passed | release-prompt ordering contract covered |
| C6 | passed | native projections regenerated from canonical sources |
| C7 | passed | canonical safe runner used for full and focused Pester checks |

## Remaining Uncertainty

- V9 requires post-merge GitHub Actions evidence: changed rebuild, no-op rebuild,
  stale-main skip, artifact handoff, and release-tag deployment.
- `test_target_drift.py` compares generated trees to committed `HEAD`; its final
  no-drift assertion must run after committing the regenerated projections.

## Final Status

- blocked pending required post-merge CI evidence (V9)
