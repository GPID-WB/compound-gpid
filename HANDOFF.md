# Documentation Redesign Handoff

Updated: 2026-09-17. Temporary handoff requested for a browser-enabled computer.
Remove this file after the successor has completed the work and saved final
evidence in the canonical work report. Do not treat this file as a replacement
for the approved plan or as proof that the work is complete.

## Browser Pickup Update, 2026-09-17

The execute-all-phases request resumed this handoff. Local repairs now pass all
31 browser tests, 20 axe matrix scans, 180 docs Node tests, and the canonical
unfiltered macOS Pester run (2,925 passed, 0 failed, 3 platform skips). Escape now
explicitly closes search; reduced-motion transitions use zero duration to avoid
stale inherited theme colors. The second two-attempt renewal is used and passed.
Source changes are uncommitted on `improve-website-design`.

**Current work: implementing the canonical help documentation integration.** The user explicitly approved
deferring human screen-reader and 200% zoom visual checks in Run 18. Step 4 is
complete with that limited exception. Step 5 implements immutable source
verification, separate staging, paired metadata, shell integrity and legacy
switching. Phase 3 is complete: 191 Node tests, 44 browser tests and the fresh
full Pester gate (2,925 pass, zero fail, three platform skips) pass. See Run 18
and `2026-09-17-docs-phase3-evidence.json`. Gate A is checkpointed at de64bf06.
Merged dev 7a4df8c6 has the catalog but its help Plan has completed phases 1-4
only; phase 6's documentation writer/checker, marker migration and wiki ownership
transfer are absent. Run 19's external-blocker interpretation is superseded by
Run 20: implement those missing pieces in their canonical `scripts/help/` owner
as part of the authorized website integration. The repeat merge is verified;
phase 4 is active. Phase 5 and the final pipeline remain pending. No deployment exists.

Read Run 17 in the canonical work report and
`.cg-docs/work-reports/2026-09-17-docs-step4-browser-recovery.json` for current
source hashes, evidence and platform qualifications. The session review server
is `http://127.0.0.1:64400/compound-gpid/#page=modular-guide`, with the paired dev
fixture at `/compound-gpid/dev/`. It may need restarting in a later session.
Remote `dev` now contains the merged help catalog/scripts; the older claim below
that readiness must be rechecked still applies before integrating Gate B.

The remaining sections preserve the incoming checkpoint and historical CI
evidence. Their repair-authorization blocker is superseded by this update.

## Current State

- Repository: `GPID-WB/compound-gpid`.
- Working and remote branch: `improve-website-design`.
- Latest implementation checkpoint: `cdea701a24748262d720782accd322c3b67577ac`.
- The commit containing this handoff adds documentation/state, not runtime fixes.
- Plan: `.cg-docs/plans/2026-09-16-documentation-ia-ux-redesign.md`.
- Work report: `.cg-docs/work-reports/2026-09-16-documentation-ia-ux-redesign.md`.
- Compact state: `.cg-docs/active-state/current.json`.
- Plan status: `active`; `completed-phases: [1, 2]`; `current-phase: 3`;
  `failing-steps: [4]`. This means implementation step 4 inside phase 3.
- Phase 3 implementation step 5 has NOT started. Phases 4 and 5 have NOT started.
- No PR or deployment was created by this pipeline. Integration PRs target
  **`dev` only**, not `main`.

The pipeline is blocked on browser verification, not dependency installation.
The original step 4 repair allowance (2/2) and approved renewal (2/2) are used.
Before code repair, obtain and record a new bounded recovery approval. Do not
reset that accounting, weaken assertions, or silently accept missing evidence.
The current user request authorizes this commit/push/handoff, not a new repair
loop or a waiver. Read the saved plan's completion contract before resuming.

## Completed Work

| Area | State |
| --- | --- |
| Phase 1: migration contracts | Complete. Shared heading/slug rules, manifest validation, route/heading preservation inventory, actual legacy runtime/generator fixtures, and continuing CI registration. |
| Phase 2: navigation and content | Complete. Seven navigation groups; separate responsive TOC; breadcrumbs, permalinks, routing/history/focus safeguards; guarded storage; balanced CG/CR guidance; unified Skill Management guide; retained operation references and compatibility routes; command checklists and task recipes. |
| Phase 2 verification | Passed scoped technical/research content reviews, dark-theme visual review, 18 browser tests, 158 docs Node tests, and all native checks on three OS targets. Passing run: `35163119256`. Later shared changes still require regression checks. |
| Phase 3, step 4: discovery | Implemented but NOT verified complete. Deterministic section-index helpers; lazy channel-local search; retry/error and unsafe-input handling; exact-byte copy and fallback; printable cheat sheet; truthful preview/unverified identity and source-link helpers. |
| Production build integration | NOT complete. Production search-index emission and the versioned build/identity contract remain step 5 work. A passing test-fixture search does not prove production generation. |
| Browser environment | GitHub Actions successfully installs the locked dependencies and Chromium. A complete repaired `package-lock.json` is committed; use normal `npm ci`, not another lock repair. |

Useful checkpoints: `98c5e718` migration/CI recovery, `d3154c40` shell/content,
`393a1975` mobile and migration corrections, `eaf6348a` search contracts/browser
baseline, and `cdea701a` live discovery integration.

The original proposal is preserved byte-for-byte in
`.cg-docs/archive/2026-09-16-documentation-ia-ux-redesign-proposal.md`.
Do not put it back into the generated `.kilo` tree. Its old local path is ignored.
Frozen files under `scripts/tests/fixtures/docs-redesign/legacy/` must not be
regenerated with the new builder or edited to make tests pass.

## Current Evidence

Latest run: https://github.com/GPID-WB/compound-gpid/actions/runs/35173151334

It tested `cdea701a24748262d720782accd322c3b67577ac`, attempt 1. Its final
conclusion, checked on 2026-09-17, is **failure**: 7 jobs passed, 1 failed,
2 skipped. The Windows native job finished successfully after the earlier
blocked-state report was written.

| Check | Actual result |
| --- | --- |
| Documentation browser suite | 31 executed: **21 passed, 10 failed**, 0 skipped, 0 flaky |
| Dependencies and Chromium | Passed; `repair_docs_lockfile` false and repair step skipped |
| Docs Node suite | Latest executed source checks: **180 passed**, no failures |
| Local canonical Pester | `2026-09-17T02:01:22Z`: 3,013 total, **3,011 passed, 0 failed, 2 skipped**, all 21 files, `filteredFiles: null`; source-relevant to the implementation checkpoint |
| Native target jobs | Windows, macOS, Ubuntu all passed |
| Other jobs | Both CI Pester jobs, Python 3.8 compatibility, and generic Kilo report passed |
| Not verified by this run | Docs staleness and certified Kilo integration were skipped; browser evidence capture and its tests were skipped after the browser failure |

Local Pester emitted non-terminating TestDrive cleanup errors. Its zero failed
assertions are not proof of clean cleanup. Individual reasons for the two update
test skips were not recorded. Do not substitute this historical pass for fresh
phase-completion evidence after further changes.

### Ten Browser Failures

| Cases | Failure and source |
| --- | --- |
| Lazy section search, root and dev | Escape did not restore focus to the search trigger; `scripts/tests/docs-discovery.browser.js:31`. |
| Reopen search while pending and after completion while closed | Escape did not hide the dialog; `scripts/tests/docs-discovery.browser.js:76`. Both tests stopped BEFORE testing reopening. |
| Responsive root 320, dev 390, root 768, root 1024, dev 1024, dev 1440 | Axe `color-contrast` findings on table/list text; `scripts/tests/docs-browser.spec.js:146`. |

The search snapshots show an open dialog with an empty search input. The input
is `type="search"`, and the helper has no explicit Escape handling. Native
clear-first behavior is a hypothesis to reproduce, not a confirmed diagnosis.
Retain the intended close/focus contract and the existing keyboard assertions.

The contrast assertion saves IDs/targets but not full computed ratios or the
failing theme. Diagnose computed foreground/background colors, inherited styles,
theme transitions, font readiness, and measurement timing in a real browser.
Do not assume these are false positives or suppress the axe rule.

Focused-result Enter after ArrowDown/Tab passed. Index failure/retry, malformed
index rejection, query races, clipboard success/failure, print, and both
drawer/TOC/table keyboard journeys passed. Keep all those regressions intact.

### Downloadable Evidence

- Artifact: `docs-browser-evidence-35173151334-1`, ID `10477431891`.
- Archive SHA-256: `bba35dfedeede9ccaa56067fbdf2e8230dcac6c664e2e711828c96427b6352ab`.
- Artifact expiry: **2026-09-24T02:08:24Z**; download before expiry if needed.
- Contains `test-results/docs-browser.json`, `docs-browser-provenance.json`,
  screenshots, traces, and error contexts under `test-results/docs-browser/`.
- Runtime recorded by CI: Node 22.23.2, npm 10.9.8, Playwright 1.52.0,
  axe-core 4.10.3, Chromium 136.0.7103.25.

Do not depend on the previous computer's absolute paths or temporary files.
Retrieve the artifact into an approved external temporary directory. For example,
in PowerShell, after verifying `$env:TEMP`:

```powershell
if (-not (Test-Path -LiteralPath $env:TEMP)) { throw 'TEMP directory is missing' }
$evidence = Join-Path $env:TEMP 'compound-gpid-docs-35173151334'
gh run download 35173151334 --repo GPID-WB/compound-gpid --name docs-browser-evidence-35173151334-1 --dir "$evidence"
gh run view 35173151334 --repo GPID-WB/compound-gpid --log-failed
```

Verify the run SHA/attempt and provenance before treating downloaded output as
evidence. If the artifact has expired, reproduce the failures on the recorded
source; do not claim the old screenshots were inspected.

## Browser-Enabled Pickup

1. Check out or pull `improve-website-design` without discarding other work.
   Read this file, `AGENTS.md`, `.github/copilot-instructions.md`, the canonical
   plan, and the latest work-report sections. In Kilo, load
   `.kilo/commands/cg-work.md` and its contracts. Obtain the bounded repair
   approval before editing implementation or tests.
2. Use Node 22 to match CI and install the committed dependency lock. Do not
   upgrade Playwright or rewrite the lock as an attempted browser fix.
3. Reproduce the failures locally, then inspect them with a headed browser or
   Playwright UI. Establish the actual Escape and contrast causes before repair.
4. Apply only approved repairs, preserve negative/security tests and legacy
   fixtures, and record each recovery attempt and result.
5. Run the full regression commands, complete remaining accessibility evidence,
   and return to the phase 3 plan. Do not mark phase 3 complete after step 4 alone.

Run these commands from the repository root, one at a time. On Windows, use
`npm.cmd` instead of `npm` if PowerShell blocks the npm script wrapper. Linux
may require Chromium system libraries through the normal approved host setup.

```text
npm ci --ignore-scripts --no-audit --no-fund
node node_modules/playwright/cli.js install chromium
npm run test:docs-browser -- --list
npm run test:docs-browser -- --reporter=line,json
```

The current collection is 31 tests. For interactive diagnosis:

```text
npm run test:docs-browser -- --ui
npm run test:docs-browser -- --headed --debug --grep "phase3 lazy section search|phase3 reopen search"
npm run test:docs-browser -- --headed --grep "responsive accessible"
```

Set `PLAYWRIGHT_JSON_OUTPUT_NAME` to a chosen report path if a persistent JSON
report is needed; CI uses `test-results/docs-browser.json`. Traces and screenshots
are under `test-results/docs-browser/`. Use the Playwright trace viewer to inspect
an actual downloaded `trace.zip`; do not commit those generated artifacts.

**Important fixture boundary:** `docs-browser.spec.js` starts its own server on
an ephemeral loopback port and imports `docs-discovery.browser.js`. The server
generates `assets/search-index.json` in memory and simulates `/compound-gpid/`
and `/compound-gpid/dev/`. No separate preview server is required for the tests.
Serving raw `docs/` alone will NOT supply the unfinished production index.
The browser suite also blocks Google Fonts; it tests fallback-font rendering,
not production loaded-font layout or a deployed Pages site.

### Files To Inspect

| Purpose | Files |
| --- | --- |
| Search input, dialog, and events | `docs/index.html`, `docs/assets/docs-search.js`, `docs/assets/site.js` |
| Theme/contrast, responsive layout, print | `docs/assets/site.css`, `docs/assets/docs-reading.js` |
| Copy, status, identity/source helpers | `docs/assets/docs-tools.js` |
| Search extraction and index validation | `scripts/docs-search-index.js`, `docs/assets/docs-search.js`, `scripts/tests/docs-search.test.js` |
| Browser setup and failing cases | `playwright.docs.config.js`, `scripts/tests/docs-browser.spec.js`, `scripts/tests/docs-discovery.browser.js` |
| Shared migration/rendering | `docs/assets/docs-contract.js`, `scripts/tests/docs-migration.test.js`, `scripts/tests/fixtures/docs-redesign/` |
| Build and provenance work still needed | `scripts/docs-build-contract.js`, `scripts/rebuild-docs.js`, `scripts/assemble-docs-site.js`, `scripts/legacy-pages.js` |
| Continuing CI and artifact capture | `.github/workflows/tests.yml`, `package.json`, `package-lock.json` |

### Required Browser Scenarios

- Escape with a nonempty query closes search and restores trigger focus in both
  channels; verify that it does not only clear the input.
- Close and reopen while an index request is pending and after it completes
  while closed; query/results recover, and the validated/pending request is reused.
- ArrowDown, Tab, and Enter activate the focused result, not an old selection.
- Repeat the complete 320/390/768/1024/1440 width matrix for both channels and both
  themes. Save full axe node details, failing theme, and computed contrast ratios.
- Keep retry, malformed/unsafe index rejection, stale-query suppression,
  channel-local fetching, exact copied bytes, failure feedback, and print tests.
- Review light/dark screenshots, drawer/TOC focus, skip links, history without
  refetching, banner offsets, keyboard table scrolling, reduced motion, and
  storage-denied behavior. Do not infer interaction success from screenshots.
- Check real browser zoom at 200 percent. The existing CSS `zoom = "2"` test
  explicitly does NOT establish browser-zoom behavior.
- Obtain the required focused human/screen-reader review, or record an explicitly
  approved evidence exception. No manual screen-reader pass has been recorded.
- Check loaded-font layout separately if required by the plan. Keep browser/OS
  versions and source SHA with all new evidence.

### Regression Commands

```text
npm run test:docs-automation
npm run test:docs-browser -- --reporter=line,json
node scripts/check-docs-site.js
node scripts/rebuild-docs.js --check --all
node scripts/tests/fixtures/docs-redesign/capture-baseline.js --check
node --test scripts/tests/docs-search.test.js scripts/tests/docs-reading-tools.test.js scripts/tests/docs-migration.test.js
```

The repository also requires a fresh unfiltered canonical Pester gate at phase
boundaries. Load `cg-skill-pester-safety` and dispatch a dedicated execution
subagent to run `. tests\Run-Tests.ps1`, without flags or a pipeline. Read fresh
`tests/last-run.json`; require `passed: true` and `filteredFiles: null`, and record
skips/cleanup warnings. Never replace it with direct `Invoke-Pester` or a directory
run. A child without Task support must ask its parent to dispatch this executor.

Use a short, approved temporary directory with sufficient space. The previous
computer had a broken npm proxy and about 0.29 GiB free on C: when work stopped.
Deep TEMP paths inside the worktree caused Windows path failures; a short path
removed those failures. Two `.kilo/<GUID>/` test remnants were deliberately left
untracked and are NOT part of this handoff. Do not recreate, stage, or copy them.

## Remaining Plan And Pipeline

After step 4 passes, complete phase 3 step 5, not just the visible UI:

- Independently verify producer output against unchanged canonical inputs before
  import; use separate staging and reject self-consistent forged artifacts.
- Implement the exact two-channel metadata, loaded-shell build identity,
  content-addressed assets/SRI, safe cache invalidation, and truthful labels.
- Preserve actual legacy producer/fingerprint rules, supported recovery, and
  legacy-channel switching limitations; reject downgrade/unknown contracts.
- Wire production generation only under the matching versioned contract; retain
  one writer for each generated section. Record protected-controller rollout
  readiness separately from local validation. Do not enable publication or
  change release policy to make the checks pass.
- Complete V4-V6/Gate A and the fresh phase gate, then write completion metadata
  in the order required by `/cg-work`.

Phase 4/Gate B requires merged canonical help catalog contracts, fresh source
validation, ownership transfer, and parity evidence. Phase 5/Gate C requires
current source-bound host-support evidence. Read the plan's exact gates and
recheck current sources; do not copy unmerged sibling work or assume readiness.

Resume commands, strictly in order and only after each preceding gate passes:

```text
/cg-work phase3 review:auto .cg-docs/plans/2026-09-16-documentation-ia-ux-redesign.md
/cg-work phase4 review:auto .cg-docs/plans/2026-09-16-documentation-ia-ux-redesign.md
/cg-work phase5 review:auto .cg-docs/plans/2026-09-16-documentation-ia-ux-redesign.md
/cg-review mode:verify
/cg-fix-triage
/cg-compound
/cg-commit-push-pr
[Wait at least 5 full minutes after PR submission]
/cg-verify-pr
```

For `/cg-commit-push-pr`, the PR base must be `dev`. The earlier approved test
checkpoints and this handoff commit are NOT completion of that final pipeline
step. No PR exists from this pipeline, so the five-minute wait has not started.

For remote verification after an authorized checkpoint push, use:

```text
gh workflow run tests.yml --repo GPID-WB/compound-gpid --ref improve-website-design
```

This branch does not match the workflow's push filters; do not assume a push
starts the test workflow. Leave `repair_docs_lockfile` false. Verify the returned
run's exact SHA and attempt before accepting its results. Keep any future PRs
off `main`, preserve protected deployment boundaries, and stop if a required
gate cannot pass within its approved recovery allowance.
