---
date: 2026-09-17
depth: full
type: standard
plan: .cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: fixed
---

# Phase 3 Review

## Source And Scope

Parent supplied full-route review from `ses_f500045e6ffeO3eQZ2tY87ZkFl`:
10/10 specifications complete, three P1 manual findings. Scope is Phase 3 and
the clarified source-branch policy. Phase 1/2 accepted evidence remains historical
baseline. The user authorized in-scope repairs on 2026-09-17. No finding is closed
until executed regression tests and independent delta review confirm it.

## Findings

- **[P1.1] [manual]** `create-release.ps1:861-869,904-918` at the reviewed revision: prerelease Finalize accepts a successful workflow wrapper even if the release build was skipped and only build-dev succeeded. Require the exact successful attempt's build job, mandatory successful steps and matching artifact before attestation, without requiring Pages.
- **[P1.2] [manual]** `.github/workflows/release-pages.yml:142-151,299-332`, `.github/workflows/pages.yml:12` at the reviewed revision: a dev preview composes official content from main. After a stable release from deploy/2.x, the next dev payload push can restore the old main tree. Bind preview official content to verified deployed release source/artifact and test stable-deploy followed by preview preservation.
- **[P1.3] [manual]** `scripts/release-version.js:118-147` at the reviewed revision: automatic stable resolution chooses the first containing branch without checking its current payload. An advanced default branch can mask the eligible deployment branch and fail the later newest-payload check. Match candidate ancestry and exact payload identity before selecting it.

## Repair Round 1

- P1.1: exact run-attempt jobs endpoint; one completed successful build job at the exact SHA; all seven required steps successful and ordered; one nonexpired release-docs-site artifact for the run/SHA with digest; artifact creation within that successful attempt's job interval. Added skipped/missing/mismatched job, step, artifact and attempt cases plus successful retry coverage. Pages remains absent from the prerelease path.
- P1.2: protected preview resolves a bounded history of successful official deploy jobs, ordered by actual completion, verifies controller lineage and the exact successful stable build/artifact, downloads that immutable artifact, imports its validated docs into an exact-SHA source checkout and composes only the new dev tree. Rechecks the official identity tuple before deployment. Missing, expired or changed evidence stops; no main/older-release fallback. Added remote selection/failure tests and a sequential composition test comparing all official site bytes after a dev update.
- P1.3: resolver requires tag payload/latest byte identity and reads each candidate's latest payload at its exact branch-tip SHA. Mismatched candidates are skipped, not selected. Added ambiguous automatic default/deployment selection, explicit mismatched-source rejection and absent/skewed payload cases.
- Re-derived the one obsolete Node guard to require --resolve-source and executable source policy cases. Retained protected controller, exact build, tag/SHA, selected-branch lineage, newest-payload and predeployment recheck assertions.

## Evidence And Gates

- Pre-repair focused Pester: create-release 199 passed at 2026-09-17T15:33:55Z; docs-automation 24 passed at 2026-09-17T15:34:27Z. Both gitSha 8bc05e51, filtered to their named suites, zero failures/skips.
- Pre-repair Python: 144 passed, 3 skipped, zero failures.
- Pre-repair Node: 37 total, 36 passed, one failed obsolete legacy-docs-branch guard at scripts/evidence/tests/release-pages.test.js:149. This result does not verify the repairs.
- Post-repair focused tests, unfiltered Pester boundary and independent delta review are pending. All three findings remain open. V13 remote activation is still required after step9. No live deployment, Phase 4, commit, push or PR is claimed.

## Round 1 Verification And New Findings

The statements above describe historical checkpoints. Parent reported focused
green results: create-release 214 passes, docs-automation 24 passes, Node 42
passes, Python 144 passes and 3 skips. Reviewer confirmed P1.1 and P1.3 static
repairs; their runtime cases now pass. The original P1.2 overwrite is prevented,
with its sequential preservation case passing. These original findings are fixed;
the remaining durability failures are tracked separately below, not waived.

- Full Pester: 3109 total, 3106 passed, 1 failed, 2 skipped; gitSha 8bc05e51, ranAt 2026-09-17T16:00:51Z, filteredFiles null. The docs-preview assertion still required a main checkout. Missing/nonempty TestDrive cleanup diagnostics remain a separate qualification.
- **[P1.4] [manual]** legacy-pages.js:90-92,134-167 and release-docs.yml:59 at the reviewed revision: one-day artifact retention and a 100-mixed-run search window stop ordinary previews. Durable official identity and bytes must not depend on these ephemeral surfaces.
- **[P1.5] [manual]** legacy-pages.js:160-164 at the reviewed revision: historical reuse calls the new-deployment source resolver, so advancing a source branch's latest payload invalidates a still-valid deployed official snapshot. Separate historical preservation from new-release freshness checks; keep P1.3 for new deployment.

## Repair Round 2

The user authorized durable snapshot repairs without new remote write authority.
Inspected existing docs snapshot schema/inventory helpers and the disabled async
controller registry. Reused only the strict static-data envelope, not its registry,
App credentials or controller enablement. Added a dedicated legacy snapshot helper
to keep this protocol separate from the current artifact/actor gate.

The existing official Pages artifact now carries official identity and bytes plus
its publisher tuple. A successful Pages deploy is the only publication point.
Previews read the repository's exact workflow-managed HTTPS Pages URL without a
credential header or redirects; validate the complete snapshot inventory; bind
the publisher to the current successful github-pages deployment, exact job/run
attempt, default-controller identity and lineage; restore immutable official bytes;
compose dev; and carry the same official record with the new preview publisher.
No old build artifact, mixed Actions history scan, or current release-source payload
is read for historical preservation. The new-release resolver retains P1.3.

Re-derived docs-preview, docs-automation and Python workflow tests around protected
controller code plus authenticated official static data, not a hardcoded branch.
Added positive expiry/history/source-advance and pending/failed-deployment cases;
corrupt, stale, foreign publisher/origin cases; and a complete seal -> restore ->
preview stamp -> replay/recheck sequence preserving official bytes. These repairs
still need focused/full execution and independent delta review. P1.4/P1.5 remain
open. Initial durable-state seeding is a required V13 activation step, not a local
deployment claim or an automatic bootstrap from main.

## Round 2 Verification And Recovery Token Repair

- Parent focused evidence, gitSha 8bc05e51: create-release 216 passed at 2026-09-17T16:23:24Z; docs-automation 24 passed at 16:23:49Z; docs-preview 9 passed, 1 failed at 16:24:16Z. The sole failure was its remaining obsolete combined-root assertion `--main-root sources/main --dev-root sources/dev`. No cleanup errors. Full Pester was not run.
- Node: 67 passed. Python: 144 passed, 3 skipped. Reviewer confirmed P1.2/P1.4/P1.5 static resolution; their runtime regressions pass. All findings through P1.5 are fixed. Earlier pending/qualification text is historical.
- **[P1.6] [safe_auto]** release-pages.yml:237-238 at the reviewed revision: sealing inherits github.token, while sealOfficial calls the recovery authority check requiring administration read. Initial and final checks already select the existing recovery-authority token. Forward the same token to sealing, with no new permission or token creation.
- Applied P1.6: sealing now uses `${{ steps.recovery-authority.outputs.token || github.token }}`. Updated the stable contract recognizer to require this propagation, added an executable Pester case rejecting its removal before remote effects, and added a parsed-workflow Python test asserting identical initial/seal/final token selection and existing manual-recovery administration-read configuration.
- Re-derived the remaining preview assertion to `--main-root official-source --dev-root sources/dev`; protected default code, authenticated restore/recheck, exact dev source/artifact and combined-site verification assertions remain.
- P1.6 stays open until focused/full tests and independent delta review confirm the fix. V13 and the no-Phase-4/no-shared-publication constraints remain unchanged.

## Final Local Closure: 2026-09-17

- Parent reviewer confirmed P1.6 fixed with no new P0/P1 or cross-file findings. Recovery-token propagation, ordinary-token fallback, unchanged permissions, fail-closed controller recognition and tests were reviewed. Full-route coverage remains 10/10; all six Phase 3 findings are fixed, zero open.
- Final focused Pester: create-release 217 passed, 0 failed, 0 skipped, gitSha 8bc05e51, ranAt 2026-09-17T16:31:24Z; docs-preview 10 passed, 0 failed, ranAt 2026-09-17T16:31:44Z. Final focused Python release policy: 15 passed, 0 failed, 0 skipped.
- Unchanged coverage retained: docs-automation 24 passes; four Node files 67 passes; combined Python 144 passes and 3 skips. These are separate runs and are not added together as one test count.
- Final unfiltered Pester: 3112 total, 3110 passed, 0 failed, 2 skipped in update; gitSha 8bc05e51, ranAt 2026-09-17T16:36:46Z, passed true, filteredFiles null, failFast false, failures empty. The implementation thread read tests/last-run.json and confirmed the full-run identity and counts against the parent evidence.
- Full-suite TestDrive cleanup reported missing/nonempty temporary freshmanifest directories. This remains an explicit cleanup qualification, not an assertion failure or a partial run. No cleanup errors were reported for the final focused runs.
- All required local Phase 3 gates, including clarified V6, are complete. Earlier pending statements in this ledger are historical. V13 remains pending actual authorized protected activation, initial durable snapshot seeding and preview verification at the final stages. No live policy activation, deployment, commit, push, PR or Phase 4 execution is claimed.
