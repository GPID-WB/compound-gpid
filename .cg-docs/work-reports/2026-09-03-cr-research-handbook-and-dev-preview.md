---
date: 2026-09-03
plan: ".cg-docs/plans/2026-09-03-cr-research-handbook-and-dev-preview.md"
status: blocked
---

# Work Report: User-facing Compound Research Handbook and Isolated Dev Preview

## Run: 2026-09-03 All Phases

- Plan reference: `.cg-docs/plans/2026-09-03-cr-research-handbook-and-dev-preview.md`
- Active deviation policy: `ask` (plan stored value; no runtime override)
- Review mode: `manual` (default; no review agent dispatched)
- Scope: all phases (1-5), following the phased dispatch flow
- Branch: `feat/cr-documentation`, based on `origin/dev`
- Roadmap startup status: no feature currently links to this plan; no roadmap mutation performed

## Completed Steps And Phases

- Steps 1-4 - CR handbook information architecture, six pages, navigation, and CG entry-point integration.
- Phase 1 - completed on 2026-09-03.
- Steps 5-6 - deterministic combined artifact assembly, explicit-root validation, and HTTP preview smoke coverage.
- Phase 2 - completed on 2026-09-03.
- Steps 7-9 - unprivileged main/dev builder, protected single-controller Pages deployment, and release-preview preservation.
- Phase 3 - completed on 2026-09-03.
- Steps 10-11 - focused content/artifact regression coverage, real combined build, and HTTP preview validation.
- Phase 4 - completed on 2026-09-03.
- Step 12 local gates - managed docs, site, artifact, workflow syntax, diagnostics, focused Node tests, module validation, target dry-run, and safe Pester verification.

## Deviations

- None.

## Accepted Exceptions

- None.

## Evidence

| ID | Status | Artifact |
|----|--------|----------|
| V1 | passed | `node scripts/check-docs-site.js`; six routes and navigation |
| V2 | passed | `scripts/tests/research-handbook.test.js`; activation and recovery assertions |
| V3 | passed | `scripts/tests/research-handbook.test.js`; Kenya scope and path assertions |
| V4 | passed | `scripts/tests/assemble-docs-site.test.js`; deterministic root/dev artifact and metadata |
| V5 | passed | `scripts/tests/check-docs-site.test.js` and `scripts/tests/docs-preview-runtime.test.js` |
| V6 | passed | `tests/docs-automation.Tests.ps1` and `tests/docs-preview.Tests.ps1`; main/dev build and single-controller contracts |
| V7 | passed | `scripts/tests/assemble-docs-site.test.js`; stale, digest, collision, and symlink failures |
| V8 | passed | `tests/docs-preview.Tests.ps1`, `tests/docs-automation.Tests.ps1`; release combined artifact and existing immutable gates |
| V9 | passed | `scripts/tests/*` focused set; canonical safe runner `tests/last-run.json` (2,724 passed, 0 failed) |
| V10 | blocked | Requires commit/push and merge into `dev`, then GitHub Actions and public `/dev/` URL verification |

## Constraints Check

| ID | Status | Result |
|----|--------|--------|
| C1 | passed | Six focused pages; no full climate tutorial or exhaustive skill duplication |
| C2 | passed | `node scripts/check-docs-site.js`; existing routes and modular links remain valid |
| C3 | passed | Assembly test proves stable root and `dev/` paths coexist without collision |
| C4 | passed | Assembly test verifies source fingerprints and every published file digest |
| C5 | passed | Pester workflow contracts; Pages permissions confined to controller and no dev execution there |
| C6 | passed | Pester workflow contracts; main and release paths upload combined site |
| C7 | passed | Assembler and workflow contracts; source freshness, digest, and no-mutation gates |
| C8 | passed | `git diff --check`; content/path review and no new framework dependency |
| C9 | passed | `tests/Run-Tests.ps1` registration; safe runner result in `tests/last-run.json` |

## Remaining Uncertainty

- The implementation has not been committed or pushed, so GitHub Actions cannot yet build the branch-derived preview or prove the public `/dev/` URL.
- The full `python3 -m pytest scripts/tests -q` gate reported 1,992 passed, 23 failed, and 10 skipped. The failures are in pre-existing untracked CR-ML/generated-target work and the local Python-launcher assumptions, not in files changed for this plan; that work was not altered.
- Repository Pages settings and post-merge workflow behavior still require CI evidence.

## Final Status

- blocked after local Phase 5 gates; implementation is ready for commit/push, but V10 requires post-merge GitHub Actions and public preview evidence.
