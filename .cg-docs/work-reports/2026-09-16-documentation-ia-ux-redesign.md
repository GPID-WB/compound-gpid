# Work Report: Documentation Information Architecture and UX Redesign

## Plan Reference

`.cg-docs/plans/2026-09-16-documentation-ia-ux-redesign.md`

## Active Deviation Policy

Stored policy: `ask`. No runtime override. Run 3 records the approved managed
refresh; Run 6 records the approved CI recovery and pipeline sequence exception.
No missing or failed evidence exception is approved. Earlier run statuses below
are historical; the latest run is the current handoff.

## Run 1: 2026-09-16T10:57:15Z

- Requested command: `/cg-work phase1 review:auto .cg-docs/plans/2026-09-16-documentation-ia-ux-redesign.md`.
- Branch: `improve-website-design`.
- Source revision: `9afd40ef4499da1b1cc9ade18e20ab596e4af6d2`.
- Initial working tree: modified `roadmap.json`; untracked selected plan and `.kilo/plans/`. These existing changes are preserved.
- Read the complete work command and plan, project instructions, charter/local settings, and context-loading, goal-execution, active-state, and artifact-view contracts.
- Loaded `cg-skill-brain-query` and `cg-skill-pester-safety`.
- Open-brain is not exposed by this session. Consulted the local Brain through its bounded CLI query. The selected workflow-token-baseline plan reinforces canonical safe-runner integration; the skill-management plan reinforces explicit contracts. Neither is execution evidence for this phase.
- Roadmap handling: matched feature `documentation-ia-ux-redesign` has status `planned`. No roadmap write or agent dispatch was made because the safe-execution prerequisite blocked implementation before work started.
- Preserved the prior workflow's active-state record at `.cg-docs/active-state/2026-09-13-release-controller-handoff.json` before writing the current blocked pointer.

### Blocker

The session exposes neither a native `task` tool nor an `execution_subagent` tool. The user and Pester safety contract require a dedicated execution subagent for `. tests\Run-Tests.ps1`. Direct terminal execution is prohibited for agent workflows. Agent Manager is not an authorized substitute for an internal task subagent. No test command was run through an unsafe substitute.

The block occurs before implementation, not after a failed test. Functional fix attempts used: 0 of 2. No product, test, workflow, navigation, or fixture file was changed. No commit, push, PR, or later pipeline command was executed. Integration remains limited to `dev`.

### Executed Checks

| Command | Result |
| --- | --- |
| `git status --short --branch` | Confirmed the branch and initial changes listed above. |
| `git rev-parse HEAD` | `9afd40ef4499da1b1cc9ade18e20ab596e4af6d2`. |
| `.\bin\cg-render-artifact.cmd --validate-only .cg-docs/plans/2026-09-16-documentation-ia-ux-redesign.md` | Passed: `Validated .cg-docs/plans/2026-09-16-documentation-ia-ux-redesign.md`. |
| `.\bin\cg-index.cmd query --intent work --query "documentation migration heading contracts preservation safe test runner" --budget 700 --format md` | Succeeded; selected two artifacts. Reported 624 Brain build warnings, including unknown `evidence-fixtures` and `inbox` directories. Not verification evidence. |
| `.\bin\cg-render-artifact.cmd --validate-only .cg-docs/plans/2026-09-16-documentation-ia-ux-redesign.md` (after metadata update) | Passed again. No phase completion recorded. |
| `git diff --check` | Passed for tracked changes. Not a test-suite result. |
| `git status --short --branch` (after handoff writes) | Confirmed only workflow records were added/updated by this run; existing roadmap and proposal changes remain. |

The Node checks, red-phase tests, and full-suite phase gate were not run. Full-suite counts are unavailable, not zero passing tests. No fresh `tests/last-run.json` was produced or accepted; completeness and `filteredFiles: null` are unverified. No editor diagnostics tool is exposed. No implementation review was run; `/cg-work` Step 3.9 is not reached at this blocked phase 1 stop.

## Completed Steps and Phases

None. Plan preflight validation passed, but phase 1 remains incomplete. The plan remains `status: active`, with `current-phase: 1` and no completed phase recorded.

## Deviations

None applied. Required execution capability is missing; the workflow is blocked rather than changed.

## Accepted Exceptions

None.

## Evidence Table

| ID | Phase | Status | Evidence |
| --- | --- | --- | --- |
| V1 | 1 | blocked | Migration implementation and tests have not started; dedicated safe execution subagent unavailable. |
| V2 | 2 | not started | Outside this invocation. |
| V3 | 2 | not started | Outside this invocation. |
| V4 | 3 | not started | Outside this invocation. |
| V5 | 3 | not started | Outside this invocation. |
| V6 | 3 | not started | Gate A not reached. |
| V7 | 4 | not started | Gate B not reached. |
| V8 | 5 | not started | Gate C not reached. |
| V9 | final | missing | No full-suite phase gate or final regression evidence. |

## Constraints Check

| ID | Status |
| --- | --- |
| C1 | No site, channel, or framework changes made; behavioral checks not run. |
| C2 | No routes, anchors, references, or safety content changed; preservation checks not run. |
| C3 | No publishing or producer changes made; integrity checks not run. |
| C4 | No command, suite, or release-policy changes made; no PR created. |
| C5 | No generated sections changed; generation checks not run. |
| C6 | No catalog or runtime-support claims added; support checks not run. |
| C7 | No tests added or omitted from CI; full-suite completion gate unavailable, so completion is blocked. |

## Remaining Uncertainty

All phase 1 implementation and required test evidence remain outstanding. The parent must restore a dedicated task/execution subagent before resuming. Do not advance to phase 2 or infer a passing gate from earlier reports.

## Final Status

`blocked`

Next command, in a session with the required dedicated execution subagent:

`/cg-work phase1 review:auto .cg-docs/plans/2026-09-16-documentation-ia-ux-redesign.md`

## Run 2: Capability Recovery, 2026-09-16T11:07:40Z

The parent confirmed native task capability and will dispatch dedicated Pester,
review, and roadmap subagents. Node tests may run in this isolated task context.
The previous capability block is resolved without an evidence exception. When
targeted Pester or the full suite is required, this task returns the exact request
to the parent and resumes with its result. Phase completion remains gated on a
fresh, unfiltered `. tests\Run-Tests.ps1` result.

The parent dispatched `cg-roadmap`; a targeted read confirms feature
`documentation-ia-ux-redesign` is now `active`, with its plan path unchanged.
Plan validation passed again before implementation. No roadmap edit was made by
this task. The previous run's blocked result remains historical, not current.

Test index: `scripts/tests/check-docs-site.test.js` (real-source link/workflow
validation), `assemble-docs-site.test.js` (paired artifacts and provenance),
`rebuild-docs.test.js` (generation/fingerprints), `docs-preview-runtime.test.js`
(HTTP channel isolation), and new `docs-navigation.test.js` (phase 1 contracts).
Pester assessment: `tests/docs-automation.Tests.ps1` covers publishing and
generation; `tests/docs-preview.Tests.ps1` covers composer source contracts;
`tests/wiki.Tests.ps1` covers wiki ownership. No wiki ownership change is planned
in phase 1. Node behavioral tests will establish the red baseline; the parent
will execute the required Pester gate after implementation.

Current run status: active. Phase 1 and V1 are not complete.

### Phase 1 Implementation Checkpoint: 2026-09-16T11:35:30Z

Implemented Step 1's migration baseline, pending the parent-run phase gate:

- `docs/assets/docs-contract.js` supplies the shared block parser, Unicode heading
  IDs, collision-safe suffixes, legacy alias resolution, manifest validation,
  visibility/search rules, and redirect destination validation.
- `docs/assets/site.js` renders that shared block tree; it retains escaping and
  the request guard. Section lookup stays inside the article and reports missing
  or ambiguous fragments. The shell loads the helper before the runtime.
- `docs/navigation.json` preserves all 76 IDs and paths. Seven explicit alias
  decisions preserve the legacy first-heading behavior for repeated installation
  and context-file headings; the fixture records the rationale for each.
- `scripts/check-docs-site.js` uses the same headings and manifest rules. Hidden
  references still need full registration and valid links. The independent
  candidate-page allowance is preserved and tested. Fenced headings cannot
  satisfy either a link target or the H1 requirement.
- `scripts/docs-build-contract.js` defines the exact two-channel public schema,
  producer/fingerprint/runtime/heading version tuples, capability declarations,
  shell identity, asset/SRI inventory, exact output reservations, and permitted
  transform descriptions. Schema validation is explicitly not source derivation
  or publication authority. New producers, shell stamping, channels.json output,
  and publishing integration are NOT enabled in phase 1.
- The composer rejects exact reserved channel/asset outputs before replacing an
  existing output. It does not exempt arbitrary JSON or generated directories.
- Revision-bound fixtures capture the actual legacy HTML, JS, CSS, navigation,
  Markdown, generator and dependencies from commit
  `9afd40ef4499da1b1cc9ade18e20ab596e4af6d2`. Digests and fixture attributes preserve
  original bytes. The old runtime executes in tests; the old generator builds
  and verifies an isolated fixture using its actual algorithm, not the new
  builder. The real old-root/new-dev composition fixture preserves both source
  trees and the legacy root bytes.
- The inventory covers 76 routes, 347 repository-local inbound links from docs,
  README and canonical .github sources, all headings, and every content block
  from all 29 management entries plus importing.md. Narrative destinations for
  phase 2 are recorded separately; no guide consolidation is claimed yet.
- `package.json` registers all three new Node test files and the existing HTTP
  preview test. The bounded CI-selection assertion confirms the exact test
  inventory and the existing workflow's `npm run test:docs-automation` command.
  No workflow edit is needed to select these tests.

Current source boundary: no `.github/shared/*help*` source was found. Gate A
remains independent of help readiness; Gates B/C need their later source checks.
No installation, suite, release branch, tag, or command behavior was changed.

### Executed Phase 1 Evidence

| Command | Actual result |
| --- | --- |
| `node --test scripts/tests/docs-navigation.test.js` before implementation | Red confirmed: 19 tests, 9 failed. Existing renderer reused IDs; helper absent; continuing CI list omitted navigation/HTTP tests. Negative-only assertions were then tightened so missing modules cannot satisfy them. |
| `node --test --test-name-pattern "producer selection\|reserves only" scripts/tests/docs-build-contract.test.js scripts/tests/assemble-docs-site.test.js` before build-contract implementation | Red confirmed: 2 failed. Composer accepted reserved channels.json; producer contract absent. |
| `node --test scripts/tests/docs-navigation.test.js scripts/tests/check-docs-site.test.js scripts/tests/assemble-docs-site.test.js scripts/tests/docs-build-contract.test.js scripts/tests/docs-migration.test.js` first combined run | 58 tests: 57 passed, 1 failed in the independently modeled legacy fingerprint transcript. |
| Recovery attempt 1 | Fixed the independent test transcript to retain the CR before the managed-interior replacement, as required by the exact legacy algorithm. Added the observed fixed digest assertion. Historical implementation and expected behavior were not changed. All later tests pass. Functional recovery budget: 1 of 2 used. |
| `node --test scripts/tests/docs-navigation.test.js scripts/tests/check-docs-site.test.js scripts/tests/assemble-docs-site.test.js` | 50 passed, 0 failed, 0 skipped; subsequently added H1 regression also passed in the final complete docs command. |
| `node --test scripts/tests/docs-build-contract.test.js scripts/tests/assemble-docs-site.test.js` | 14 passed, 0 failed, 0 skipped; includes actual legacy producer and mixed-runtime composition. |
| `npm run test:docs-automation` final run | 145 passed, 0 failed, 0 skipped, 0 cancelled, 0 todo; 18.972 seconds. Complete bounded docs Node command, NOT the repository full-suite gate. All three new test files and the HTTP preview file executed. |
| `node scripts/check-docs-site.js` final run | Passed: 76 navigable Markdown pages, 8 current groups, complete skills catalog. The seven-group presentation change belongs to phase 2. |
| `node --check docs/assets/site.js` | Passed. |
| `node --check docs/assets/docs-contract.js` | Passed. |
| `node --check scripts/check-docs-site.js` | Passed, including after the final H1 change. |
| `node --check scripts/docs-build-contract.js` | Passed. |
| `node scripts/tests/fixtures/docs-redesign/capture-baseline.js --check` | Passed; captured revision, routes, preservation inventory and seven decisions match. Legacy Markdown was then added as an immutable fixture and its source digests passed in the final docs command. |
| `git diff --check` | Passed; Git reports normal LF-to-CRLF checkout warnings for existing JavaScript attributes. Pinned fixtures have their own no-conversion rule. |

Platform qualification: the existing composer symlink test reported Windows
`EPERM` and used its existing portable Dirent boundary path. This is not native
file-symlink qualification; it is not a skipped test. No test assertion was
weakened. Editor `get_errors` is not available here; JavaScript syntax checks
were executed and no editor-diagnostics pass is claimed.

### Supplemental Freshness Failure and Required Decision

`node scripts/rebuild-docs.js --check --all` exited 1, naming only
`docs/whats-new.md`. The unchanged pinned legacy builder also exited 1 with the
same output after its release-version dependency was captured. The first legacy
attempt reported a missing `./release-version.js`; that fixture dependency is
now captured, pinned, and tested successfully. The current published-source
payload is `v1.2.0.9018`, while the checked-in generated page starts at
`v1.2.0.9015`. The freshness drift predates this implementation.

No source release-note page has been regenerated. This check is not reported as
passed or accepted. Because phase 1 freezes migration contracts rather than
rewriting release history, the parent must resolve D2 before completion:

1. Approve the narrow managed-output refresh using
   `node scripts/generate-whats-new.js`, preserve prose and old headings, then
   rerun freshness, migration, docs automation, and the full-suite phase gate.
2. Leave `docs/whats-new.md` unchanged and keep completion pending until the
   freshness scope/evidence issue is resolved. No silent evidence waiver.

### Tested Working-Tree Identity

HEAD remains `9afd40ef4499da1b1cc9ade18e20ab596e4af6d2`. These Git blob IDs were
recorded with `git hash-object --no-filters` at the final Node run. The original
roadmap/proposal changes remain, with the parent-authorized active status.

| Path | Tested blob |
| --- | --- |
| `docs/assets/site.js` | `c6885aed3e3eb170f1a957b5332d9f227ae61879` |
| `docs/assets/docs-contract.js` | `d38fe8795f2340778da27d74c29275b60235f371` |
| `docs/index.html` | `cb80888c708c5fcdf9fcebaf66a9d317c7cb0378` |
| `docs/navigation.json` | `e37a4e1c754ecc91f783f66a249dbf83e96b038c` |
| `scripts/check-docs-site.js` | `63e65b7d72cd29fd5d496ed05e17265e3b6644f1` |
| `scripts/assemble-docs-site.js` | `5b699bccc352190d9d0ffc9d0a8481f926fa22d1` |
| `scripts/docs-build-contract.js` | `7feb02da0aba2544a83d3089286786bf3d7c258b` |
| `package.json` | `bba2fa7de07497ee0937c22f9cca76913d5b3210` |
| `scripts/tests/docs-navigation.test.js` | `909463e63e25d4f12f9fba56838eb00355027c0b` |
| `scripts/tests/docs-build-contract.test.js` | `1ad5c51a744e91f31d95d83bd8b5f694db5bca8e` |
| `scripts/tests/docs-migration.test.js` | `5ffa8535e98aae3f92d8c3f2fb59e27fd66762dc` |
| `scripts/tests/check-docs-site.test.js` | `49a846c9940e6619611ffeda8df7a29f16ab824b` |
| `scripts/tests/assemble-docs-site.test.js` | `768767bdb1ff65d00155e5e7f209afbd83069eef` |
| `scripts/tests/fixtures/docs-redesign/capture-baseline.js` | `b1fc75cc33b716e43a80aebab34dff0240dfacca` |
| `scripts/tests/fixtures/docs-redesign/provenance.json` | `8395d5384a0cc9838c5b27eecf4265072a4940d7` |
| `scripts/tests/fixtures/docs-redesign/migration-inventory.json` | `c859b38c244db3e48392003f1491a975187bcbd7` |
| `scripts/tests/fixtures/docs-redesign/legacy-documents.json` | `6b87c072f93cf24e9eae335a8a6a9dc590639d15` |

### Parent Handoff

`NEEDS_FULL_SUITE`, with D2 also requiring resolution. Dedicated subagent command:
`. tests\Run-Tests.ps1` with no flags or pipeline, from this worktree root.
Load `cg-skill-pester-safety` first and return `gitSha`, `ranAt`, `passed`,
`totalCount`, `passedCount`, `failedCount`, `failFast`, `filteredFiles`, failure
details, and skipped/pending counts from the fresh runner artifact. Do not use a
targeted result as the phase gate. Full-suite counts and completeness remain
unknown until that result returns.

V1's implemented contract/inventory checks pass; phase completion is still
pending the full-suite gate and D2. V2-V9 remain uncompleted. Constraints C1-C7
remain scoped to phase 1: no UI redesign, publishing enablement, catalog claims,
or generator ownership transfer is claimed. No review dispatch is required at
this intermediate phase boundary by `/cg-work` Step 3.9, which runs after the
final phase; no independent implementation review is claimed here.

Run 2 status: handoff, not completed. No `completed-phases` write, commit, push,
PR, or later pipeline command. Resume the original phase 1 command with parent
evidence; do not start phase 2 yet.

## Run 3: Approved Managed Refresh, 2026-09-16T12:42:45Z

Explicit approval for D2: the user selected the exact option
`Approve Refresh (Recommended)`. Approval covers running
`node scripts/generate-whats-new.js` to refresh only managed content in
`docs/whats-new.md`, preserving existing prose and old headings, then rerunning
freshness, migration, docs automation, and the dedicated full-suite phase gate.
This is an approved narrow scope adjustment under `deviation-policy: ask`, not
an evidence exception. D2 is resolved.

The frozen legacy baseline must remain unchanged and must not be regenerated
through the current generator. No later phase, completion write, commit, push,
or PR is authorized during this checkpoint. Full-suite execution remains with
the parent's dedicated test subagent.

### Refresh Verification

Checks started at 2026-09-16T12:44:48Z. The approved generator updated only
`docs/whats-new.md`: 68 inserted lines within the `release-notes` marker pair,
adding releases v1.2.0.9016 through v1.2.0.9018. All prior headings remain.
Manual prose outside the marker pair is byte-identical to the captured original.
One focused regression assertion was added to `docs-migration.test.js` to check
that preservation directly; it also rejects a deliberately changed prose prefix.

| Command | Actual result |
| --- | --- |
| `node scripts/generate-whats-new.js` | Passed: wrote 15 releases. Only current source docs were refreshed. |
| `node scripts/generate-whats-new.js --check` | Passed: current. |
| `node scripts/rebuild-docs.js --check --all` | Passed: complete build current. The previous freshness failure is resolved, not waived. |
| `node --test scripts/tests/docs-migration.test.js` | 6 passed, 0 failed, 0 skipped. Includes all old routes/headings, content blocks, inbound links, actual legacy runtime, and manual-prose preservation. |
| `node scripts/check-docs-site.js` | Passed: 76 navigable pages, 8 current groups, complete skills catalog. |
| `npm run test:docs-automation` | 146 passed, 0 failed, 0 skipped, 0 cancelled, 0 todo; 22.614 seconds. Complete bounded docs Node command, not the repository full-suite gate. |
| `node scripts/tests/fixtures/docs-redesign/capture-baseline.js --check` | Passed in read-only check mode. The frozen baseline was not regenerated. |
| `git diff -- docs/whats-new.md` | Only additions inside the approved managed marker pair; no existing lines or headings removed. |
| `git diff --check` | Passed, with the previously recorded JavaScript checkout line-ending warnings. |

Before/after baseline blob identities are unchanged:

- `provenance.json`: `8395d5384a0cc9838c5b27eecf4265072a4940d7`.
- `migration-inventory.json`: `c859b38c244db3e48392003f1491a975187bcbd7`.
- `legacy-documents.json`: `6b87c072f93cf24e9eae335a8a6a9dc590639d15`.

Updated tested blobs from `git hash-object --no-filters`:

- `docs/whats-new.md`: `136885335b0ec0e088903f80a9dd5fdf58b52150`.
- `scripts/tests/docs-migration.test.js`: `afb0746a7f7adb3402ae51e31e39b004785e241d`.

The existing Windows file-symlink test still reports its portable boundary
qualification; there are no failed or skipped Node tests. No additional recovery
attempt was needed. D2 is closed with explicit approval and passing evidence.

Run 3 status: `NEEDS_FULL_SUITE`. No remaining user decision at this checkpoint.
Parent must dispatch `. tests\Run-Tests.ps1` with no flags or pipeline through
the dedicated safety-loaded test subagent in this worktree. Return the fresh
runner artifact's identity, timestamp, full counts, skipped/pending counts,
failures, failFast, and filteredFiles. Pester counts and completeness remain
unknown. Phase 1 is not marked complete and no later pipeline command ran.

## Run 4: Phase 1 Evidence Gate, 2026-09-16T12:52:52Z

The parent dispatched the required dedicated safe-test subagent and reported
exit 0 for `. tests\Run-Tests.ps1` with no flags or pipeline. Read the fresh
`tests/last-run.json` in full and checked its relevance before any completion
write. Its `gitSha: 9afd40e` matches current full HEAD
`9afd40ef4499da1b1cc9ade18e20ab596e4af6d2`; its timestamp is
`2026-09-16T12:51:18Z`, after the approved refresh and final Node checks.

### Full-Suite Result

| Field | Verified result |
| --- | --- |
| Command | `. tests\Run-Tests.ps1`, parent dedicated subagent, no flags or pipeline |
| Parent-reported exit | 0 |
| passed | true |
| totalCount | 2994 |
| passedCount | 2992 |
| failedCount | 0 |
| skippedCount | 2, both reported in `update` |
| pending | Not separately recorded; no claim of zero pending tests |
| failFast | false |
| filteredFiles | null |
| failures | Empty array |
| Missing-file skips | None; `skipped` is an empty array |
| Completeness | All 21 entries in the canonical runner's ordered test list are present |
| Directly relevant files | docs-automation 24/24; docs-preview 10/10; wiki 126/126; all with zero failures/skips |
| Source artifact blob | `15e533de25a95fc552c3e43fcdc916135458eeab` from `git hash-object --no-filters tests/last-run.json` |

The runner labels the unpassed/unfailed remainder as skipped and does not retain
separate pending counts or individual skip reasons. Do not report all 2994 tests
as passed. All required phase-specific docs tests ran without skipped cases.

Cleanup caveat: the parent reported non-terminating link temporary-directory
cleanup output containing `DirectoryNotFoundException` / `directory not empty`.
The raw cleanup log was not supplied here. The artifact confirms link 94/94 and
unlink 33/33, zero failed tests, and completed execution. Record this as a
cleanup qualification, not a failed test or evidence waiver.

Durable compact evidence:
`.cg-docs/work-reports/2026-09-16-documentation-ia-ux-redesign-phase1-pester.json`.
It preserves the artifact identity, all per-file counts, and the qualification
before a later phase can replace `tests/last-run.json`.

Recomputed the 18 recorded production/test/fixture blobs with
`git hash-object --no-filters`; every identity matches the Run 2 table plus
Run 3's approved replacements. No production or test code changed after the
passed gate. Only plan/report/active-state evidence is being finalized.

### Phase Evidence and Constraints

| Evidence | Current status |
| --- | --- |
| V1 | Passed: executable route/heading/content inventory, shared contracts, actual legacy fixtures, mixed-runtime composition, and continuing CI selection; final docs Node command 146/146 passed |
| Phase 1 full-suite gate | Passed: fresh unfiltered canonical result above; 2992 passed, 0 failed, 2 reported skipped |
| V2-V8 | Not started; future-phase evidence is not claimed |
| V9 | Phase 1 evidence retained; final whole-plan evidence remains pending |

| Constraint | Phase 1 assessment |
| --- | --- |
| C1 | Static foundation and current presentation retained; two-channel contract tested; no legacy UI claims added |
| C2 | All 76 routes, recorded headings/inbound links, and 30 preservation pages verified; reference paths retained |
| C3 | Legacy bytes, version rules and paired composition verified for the baseline; phase 3 derivation, shell publication and rollout gates remain pending |
| C4 | No command, suite-dependency, installation or release-policy change; no PR created; integration target remains dev |
| C5 | Approved release-note refresh preserves marker ownership and manual prose; complete freshness check passes |
| C6 | No catalog readiness or host-certification claim added; Gates B/C remain separate |
| C7 | All new Node tests selected by the continuing CI command; fresh unfiltered canonical phase gate verified |

No in-phase failing step remains. D2 has explicit approval and executed passing
checks. There is no accepted missing-evidence exception. All phase 1 completion
prerequisites are satisfied. Independent review dispatch is not due until the
final phase under `/cg-work`; no review completion is claimed here.

### Phase Boundary

Completed Step 1 and Phase 1 on 2026-09-16. Wrote
`completed-phases: [1]` first, then reread the plan and confirmed that unquoted
integer flow sequence while `current-phase` was still 1. Only after that check,
advanced `current-phase` to 2. Plan `status: active` remains unchanged; no
whole-plan completion date is set. The active-state record is a phase-boundary
handoff with no unresolved decision.

Reread both final records and confirmed `completed-phases: [1]`,
`current-phase: 2`, and the exact phase 2 handoff command. Post-write validation
passed with `.\bin\cg-render-artifact.cmd --validate-only
.cg-docs/plans/2026-09-16-documentation-ia-ux-redesign.md`.
Final `git diff --check` passed with only the previously recorded checkout
line-ending warnings.

Suggested phase commit only, not executed:
`feat(docs): complete phase 1 -- migration and contract baseline`.

Final status for this invocation: `completed` (Phase 1 only). Phase 2 has not
started. No production/test changes followed the passing gate; no commit, push,
PR, publishing action, or later pipeline command ran.

Exact next command for the parent:

`/cg-work phase2 review:auto .cg-docs/plans/2026-09-16-documentation-ia-ux-redesign.md`

## Run 5: Phase 2 Implementation, 2026-09-16T13:04:00Z

Scope: Steps 2-3 only. The complete plan, work command, charter/local settings,
project instructions, and execution contracts were read. Versioned plan validation
passed before mutation. Phase 1 work and the approved release-note refresh remain
intact. No legacy fixture regeneration, commit, push, PR, or publication is allowed.
The parent owns Pester and subject-review dispatch; missing nested tools are not
an implementation blocker. Fresh phase 2 full-suite evidence remains mandatory.

Brain consultation used the bounded `cg-index query --intent work` command with
query `documentation navigation skill management ownership browser` and budget
700. It selected this plan and the scalable-skill-management plan. Apply explicit
roles and digest-bound approval; neither prior plan is current test evidence.
Open-brain and editor `get_errors` tools are not exposed in this session.

Test index: existing docs-navigation and docs-migration Node tests cover routing
and frozen preservation contracts; check-docs-site covers links and registration;
rebuild-docs covers generated/manual ownership. The new dedicated Playwright suite
will cover shell behavior. Pester assessment: docs-automation and docs-preview
assert publishing/generation contracts; wiki asserts generated ownership. These
will run through the parent, not this task. No publishing contract is changed in
phase 2. Red browser/content baselines precede implementation.

Current evidence: V2 and V3 in progress; phase 2 full-suite missing. No accepted
exception or additional scope deviation. Recovery attempts: 0 of 2 per step.

### Phase 2 Environment Checkpoint: 2026-09-16T13:08:42Z

Status: `NEEDS_TARGETED_TEST`, blocked before the browser red baseline. This is
an environment setup failure, not a failed behavior test or exhausted functional
repair budget. No phase 2 production shell/content edit has been made.

Completed preparation:

- Added `playwright.docs.config.js` and `scripts/tests/docs-browser.spec.js`.
  The suite owns an ephemeral loopback server and exercises repository-prefixed
  root/dev fixtures, responsive layouts, TOC/history/focus, route races, storage
  denial, axe checks, zoom, and the no-JavaScript fallback. These are unexecuted
  assertions, not evidence of implementation success. Content redirect cases
  and final fixture coverage still need to be added with implementation.
- Registered `npm run test:docs-browser` and placed its CI step after Chromium
  installation. Extended the continuing CI-selection assertion to check ordering.
- Preserved phase 1 production edits, frozen fixtures, approved release-note
  refresh, original roadmap/proposal changes, and all prior report sections.

| Executed command | Result |
| --- | --- |
| `npm run test:docs-browser -- --grep "seven collapsible\|section movement\|storage failure"` | Could not start: `playwright` is not recognized. No browser test ran. The local npm launcher also did not retain `--grep` in its displayed invocation; use the direct pinned CLI after setup. |
| `npm ci` | Timed out after 120 seconds with no output. |
| `npm ci --ignore-scripts --no-audit --no-fund --loglevel verbose` | Failed: `getaddrinfo ENOTFOUND wbaproxy.worldbank.org` while fetching existing pinned dependencies. |
| `npm ci --offline --ignore-scripts --no-audit --no-fund` | Failed: `ENOTCACHED` for `@playwright/test`. |
| `node -p "require.resolve('@playwright/test')"` in the main repository | Failed: `MODULE_NOT_FOUND`; no installed parent copy is available. |
| `node --check scripts/tests/docs-browser.spec.js` | Passed syntax only. |
| `node --check playwright.docs.config.js` | Passed syntax only. |
| `node --test scripts/tests/docs-navigation.test.js` | 20 passed, 0 failed, 0 skipped; includes CI registration/order. Not a phase 2 behavioral red baseline or full-suite gate. |

Critical npm diagnostic log:
`C:/Users/wb384996/AppData/Local/npm-cache/_logs/2026-09-16T13_04_15_834Z-debug-0.log`.
The existing lockfile only records the reveal.js package entry, despite listing
the pinned Playwright/axe dependencies at its root. Successful dependency setup
must reconcile that existing incomplete lockfile through npm, not guessed manual
integrity values. No lockfile or network/proxy setting was changed here.

Parent request: restore the approved npm dependency/network path, install the
existing pinned packages and Chromium, and dispatch this targeted red baseline
in the same worktree:

`node node_modules/@playwright/test/cli.js test --config playwright.docs.config.js --grep "seven collapsible|section movement|storage failure"`

Return setup commands/results, actual red test failures, and any lockfile changes.
Then resume this phase 2 command. Do not request the full-suite gate yet: Steps
2-3 implementation, V2 browser/accessibility evidence, V3 content migration and
technical/research subject review, generation checks, and fresh canonical Pester
evidence are still outstanding. No accepted exception, phase completion write,
commit, push, PR, or later pipeline step occurred.

## Final Halt: Phase 2, 2026-09-16T13:13:54Z

Final status: `blocked`. The user halted the pipeline after the dedicated parent
recovery agent confirmed that dependency recovery is not available in the current
environment. This final halt supersedes the earlier targeted-test dispatch request.
No further task is requested and no recovery or implementation is authorized now.

### Confirmed Recovery Findings

The following evidence was supplied by the parent; these commands were not rerun
by this task:

- Configured npm proxy: `http://wbaproxy.worldbank.org:8080`.
- `npm ping --fetch-retries=0 --fetch-timeout=15000 --loglevel=error` exited 1
  with `ENOTFOUND wbaproxy.worldbank.org`. DNS returned
  `DNS_ERROR_RCODE_NAME_ERROR`. No proxy bypass was attempted.
- Neither the default nor the checked alternate npm cache contains the required
  `@playwright/test` and `playwright` 1.52.0 or `axe-core` 4.10.3 packages. No
  suitable checked local installation was found.
- The default `%LOCALAPPDATA%/ms-playwright` browser cache is absent. No
  browser-path override is configured.
- The lockfile root declares the exact dependencies, but installed-package
  records contain only `reveal.js`. Playwright/axe resolution and integrity
  records are missing. No lockfile change is authorized or was made.

The browser RED baseline did not run. There is no product failure result and no
passing browser evidence. V2 and V3 remain uncompleted; the phase 2 full-suite
gate remains unrun. Missing evidence is not accepted as an exception.

### Handoff And Boundaries

Minimum prerequisites for any later authorized recovery: restore approved
proxy/DNS access or supply verified offline dependencies plus matching Chromium;
separately authorize repair of the incomplete lockfile before `npm ci`. This is
a prerequisite record, not authority to install, change configuration, or resume.

The plan remains `status: active`, `completed-phases: [1]`, and `current-phase: 2`.
Only this existing report and `.cg-docs/active-state/current.json` were changed
for the final halt. Prior phase 1 implementation, frozen fixtures, approved
release-note refresh, roadmap/proposal changes, and phase 2 browser-test/CI
preparation remain uncommitted and unchanged.

User protocol steps 3-11 were not run. No Pester command, later pipeline command,
commit, push, or PR ran at this halt. There is no PR; the mandatory five-minute
wait is not applicable and was not started. The active-state record has no next
command while the pipeline is halted. Parent owns the final pipeline report.

### Final Validation

- `./bin/cg-render-artifact.cmd --validate-only .cg-docs/plans/2026-09-16-documentation-ia-ux-redesign.md`:
  passed. Plan metadata was also read directly and matches the state above.
- `git diff --check`: passed; only the previously recorded LF-to-CRLF checkout
  warnings were emitted. These checks do not supply V2/V3 or full-suite evidence.

## Run 6: Approved CI Browser Recovery, 2026-09-16T17:47:39Z

### Approval And Sequence Exception

The user explicitly selected `Approve CI Recovery (Recommended)`. This supersedes
the final halt only for bounded CI recovery. It permits limited changes to the
existing test workflow, runner-side repair of the incomplete lockfile, early
feature-branch checkpoint commits/pushes for tests, and GitHub Actions runs.
The parent owns all git/gh remote operations and dedicated test subagent dispatch.
This implementation task has not committed, pushed, dispatched Actions, opened a
PR, or deployed anything.

This is a pipeline sequence exception, not an evidence waiver. No PR or deployment
is allowed before the original pipeline Step 9. Any eventual PR targets `dev`
only. The active default branch `main` is not an integration or mutation target.
Do not change protected policies, branch triggers, other jobs, or permissions to
make recovery work. The branch `improve-website-design` does not match the push
triggers; the parent must explicitly dispatch `tests.yml` on this feature branch.

Phase 1 remains complete. Phase 2 remains incomplete. No phase 2 website shell,
content, style, fixture, or browser assertion was implemented or changed in this
recovery. The plan body and frontmatter remain unchanged, including
`completed-phases: [1]` and `current-phase: 2`. V2 still needs an executed browser
RED baseline; V3 and the phase 2 completion gate are not satisfied.

### Recovery Implementation

- `.github/workflows/tests.yml`: adds only the boolean dispatch input
  `repair_docs_lockfile`, default `false`, and changes the existing
  `browser-evidence` job. Repair runs only for explicit manual dispatch with the
  input `true`. It runs `npm install --package-lock-only --ignore-scripts
  --no-audit --no-fund`, followed by `npm ci --ignore-scripts --no-audit --no-fund`.
  Normal CI never repairs the lockfile. No package version, local lockfile record,
  integrity hash, proxy setting, or dependency configuration was changed here.
- Checkout uses the full event SHA, with persisted credentials disabled and full
  history available for revision-bound legacy fixture verification. The existing
  read-only permission is unchanged. All other jobs and protected controls remain
  unchanged.
- Documentation automation stays before Chromium installation. The complete
  existing docs-browser suite follows Chromium, with line and JSON reporters.
  Existing failure traces/screenshots and responsive screenshots are retained.
  The original capture and evidence-test commands remain in their existing order.
  A failed browser step still fails the job and skips later success-only steps;
  it does not become GREEN because diagnostics uploaded successfully.
- A small inline Node provenance step and pinned `actions/upload-artifact` run
  with `always()`. The seven-day artifact contains only `package.json`,
  `package-lock.json`, `test-results/docs-browser.json`, the docs-browser result
  directory, and `test-results/docs-browser-provenance.json`. It does not upload
  the workspace, dependencies, credentials, or unrelated result directories.
- Provenance records the checked-out full SHA, event SHA/ref, repository, run
  ID/attempt, timestamp, Node/npm/package/Chromium versions, package and lock
  digests, original committed lock digest, browser JSON digest, exact commands,
  and step outcomes/conclusions. Unavailable diagnostics are `null` or `unknown`,
  not invented successes. SHA mismatch or missing JSON after a successful browser
  step fails provenance after saving its diagnostic record.
- `scripts/tests/docs-navigation.test.js`: retains exact bounded CI registration
  and adds opt-in, ordering, source-binding, fail-closed, bounded always-upload,
  and executed inline-provenance assertions. The provenance test covers failed
  and skipped outcomes, unavailable Chromium, repair false, missing results, and
  mismatched source SHA. No new test dependency or separate test file is needed.

### Executed Recovery Checks

Local source HEAD remains `9afd40ef4499da1b1cc9ade18e20ab596e4af6d2`; tests ran
against the uncommitted working tree. This is not a source-bound Actions result.

| Check | Result |
| --- | --- |
| Plan `cg-render-artifact --validate-only` preflight | Passed; plan unchanged. |
| `node --test scripts/tests/docs-navigation.test.js`, before workflow edit | RED: 20 passed, 3 failed, 0 skipped. Failures identify absent repair input, event-SHA checkout binding, and provenance step. |
| Same command after workflow edit | GREEN: 23 passed, 0 failed, 0 skipped. |
| `npm run test:docs-automation` | Failed before tests: `ENOSPC` writing the npm log on C:. Not a test failure or passing npm run. |
| Direct Node execution of the exact registered docs test inventory, command below | GREEN: 149 passed, 0 failed, 0 skipped/cancelled/todo; 25.364 seconds. |
| `node scripts/check-docs-site.js` | Passed: 76 pages, 8 current groups, complete skills catalog. No seven-group implementation is claimed. |
| `node scripts/rebuild-docs.js --check --all` | Passed: complete build current. |
| `git diff --check` | Passed, with existing checkout line-ending warnings only. |
| Workflow scope diff | Only `tests.yml` changed; its non-browser jobs and branch triggers are unchanged. |

The direct Node command used process-local TEMP/TMP on E: because C: reports
zero free space. No persistent environment or npm setting changed. Existing
tests left 28 small scratch directories; only those exact newly created paths
were removed after the run. The existing Windows EPERM qualification for the
portable file-link boundary remains; no native symlink coverage is claimed.

```powershell
$env:TEMP = Join-Path (Get-Location) '.kilo'
$env:TMP = $env:TEMP
node --test --test-reporter=spec scripts/tests/rebuild-docs.test.js scripts/tests/generate-whats-new.test.js scripts/tests/release-version.test.js scripts/tests/docs-snapshots.test.js scripts/tests/legacy-pages.test.js scripts/tests/assemble-docs-site.test.js scripts/tests/check-docs-site.test.js scripts/tests/docs-navigation.test.js scripts/tests/docs-build-contract.test.js scripts/tests/docs-migration.test.js scripts/tests/docs-preview-runtime.test.js scripts/evidence/tests/release-pages.test.js
```

Open-brain is unavailable in this session. The bounded local Brain query returned
the historical per-step failure-handling plan; it adds no authority to this
explicit recovery approval. Local `actionlint` is unavailable. No browser,
dependency install, Chromium install, fresh Pester gate, or Actions syntax/run
result is claimed by this task.

### Parent Checkpoint And Evidence Request

Status: `NEEDS_CHECKPOINT`. The parent must perform the authorized feature-branch
checkpoint and push before dispatch. Before the checkpoint, use a dedicated
test subagent, load `cg-skill-pester-safety`, and run `. tests\Run-Tests.ps1` with
no flags or pipeline from this worktree. Return fresh `tests/last-run.json`
identity, timestamp, counts, failures, `failFast`, and `filteredFiles`; report any
disk/setup failure rather than accepting old results. This is the checkpoint
regression gate, not phase 2 completion. This task did not run Pester.

After the parent checkpoint/push, the exact recovery dispatch is:

```text
gh workflow run tests.yml --repo GPID-WB/compound-gpid --ref improve-website-design -F repair_docs_lockfile=true
```

Artifact name: `docs-browser-evidence-<run_id>-<run_attempt>`. Download the artifact
from that exact run and attempt. Check its repository, full event/checkout SHA
against the checkpoint SHA, and file digests before accepting the repaired lock.
Review that `package.json` and the exact pins are unchanged. Check step outcomes
and JSON test failures to distinguish a real behavior RED baseline from setup,
automation, browser-install, or test-collection failure. Traces/screenshots are
diagnostics, not independent source proof. The artifact is untrusted test output,
not permission to execute arbitrary files or deploy.

The parent can then checkpoint the reviewed repaired lock and run normal CI:

```text
gh workflow run tests.yml --repo GPID-WB/compound-gpid --ref improve-website-design
```

The input defaults to false on that run, so installation must succeed with
`npm ci`. Do not silently repeat repair on later normal runs. Expected missing
website features must remain RED until the parent resumes separately authorized
phase 2 implementation. No browser evidence has yet been obtained. No missing
evidence is accepted, and no later pipeline step, PR, or deployment ran here.

### Parent Checkpoint Gate: 2026-09-16T18:05:10Z

The parent has supplied the checkpoint test and review results. This resolves
Run 6's pending checkpoint regression gate, not the phase 2 completion gate.
This task did not rerun Pester or perform a git mutation or gh operation.

The first canonical full-suite attempt used process-local TEMP/TMP inside this
deep worktree's `.kilo` directory. The parent reports `ranAt:
2026-09-16T17:56:22Z`, 3013 total, 3005 passed, 6 failed, and 2 skipped. The six
filesystem assertion failures included `WinError 206` from long generated paths.
This failed attempt is retained as failed evidence, not waived or reported as
passing.

The environmental retry used the verified, pre-approved short path
`C:\Users\wb384996\AppData\Local\Temp\3\kilo` for process-local TEMP/TMP. No code
or test change was made between attempts; no persistent environment setting was
changed. The parent reports canonical runner exit 0. This task read the fresh
`tests/last-run.json` and confirmed the fields below against the parent report.

| Checkpoint field | Result |
| --- | --- |
| Command | `. tests\Run-Tests.ps1`, parent dedicated subagent, no flags or pipeline |
| Full source SHA | `9afd40ef4499da1b1cc9ade18e20ab596e4af6d2`, confirmed by current `git rev-parse HEAD` |
| Artifact gitSha | `9afd40ef`, matching that full SHA |
| ranAt | `2026-09-16T18:03:51Z` |
| Parent-reported exit | 0 |
| passed | true |
| totalCount | 3013 |
| passedCount | 3011 |
| failedCount | 0 |
| skippedCount | 2, both in `update` |
| failures | Empty array |
| failFast | false |
| filteredFiles | null |
| Completeness | All 21 canonical test files present; no missing-file skips |
| Directly relevant files | docs-automation 24/24; docs-preview 10/10; wiki 126/126; zero failures/skips |

Separate pending-test counts and individual skip reasons are not recorded in
the artifact. Do not report all 3013 tests as passed. None of the six failures
recurred on the short-path retry. The parent still reports non-terminating
cleanup warnings for long generated paths. Those warnings remain a cleanup
qualification; they do not change the fresh zero-failure result. The earlier
deep-worktree TEMP/TMP workaround for Node tests is not a suitable Pester setup.

The parent also reports these completed checkpoint checks; this task did not
repeat them or create a new full-review artifact:

- Focused `cg-adversarial` static review of the recovery workflow: no material
  P0, P1, or P2 finding. This is a bounded static review, not browser evidence or
  a completed whole-plan review.
- Implementation precommit review of actual diffs in 8 files: no material issue.
- File inventory and secret-pattern scan: clean across the 42-path allowlist.
- All 11 frozen baseline files match their exact original bytes.

Only this report and `.cg-docs/active-state/current.json` are updated after the
gate. No product, test, workflow, lockfile, plan, or fixture change is made.
Unrelated `.kilo` temporary directories and generated temporary helper files
must remain excluded from the checkpoint allowlist. They were not removed or
modified by this metadata update.

Status: `READY` for the parent's already approved checkpoint commit, push, and
feature-branch dispatch, in that order. Those operations remain pending. The
exact dispatch command and artifact verification requirements in Run 6 remain
unchanged. The active-state `nextCommand` remains null because the parent must
complete the allowlisted checkpoint and push before dispatch.

Phase 1 remains complete; phase 2 remains incomplete. The passing checkpoint
does not satisfy V2/V3 or the phase 2 completion gate. Browser evidence and
runner-side lockfile repair are still pending. No PR or deployment is allowed
before original Step 9, and any eventual PR must target `dev` only.

Metadata-update preflight: plan `cg-render-artifact --validate-only` passed.
No Pester, browser, or Actions run was performed by this task during this update.

## Run 7: Phase 2 Resumed After Remote RED, 2026-09-16T18:20:43Z

The parent completed the approved feature-branch checkpoint at
`98c5e7181ccda3947a9e93eace87b5ecc9826000`. Remote run
https://github.com/GPID-WB/compound-gpid/actions/runs/35132434045 is bound to that
exact SHA, `workflow_dispatch`, branch `improve-website-design`, attempt 1.
Read the downloaded provenance record: dependency/lock repair and Chromium
installation succeeded. Node 22.23.2, Playwright 1.52.0, axe-core 4.10.3,
Chromium 136.0.7103.25. Docs Node: 149 passed. Browser: 15 total, 9 passed,
6 failed, 0 skipped/flaky; no collection errors. This run is RED, not GREEN.

Red-phase confirmed: seven-group assertion expected 7 `[data-nav-group]` nodes,
got 0; section/history TOC link absent; missing-section route notice absent;
denied localStorage prevented article startup; root and dev overflow at 320 px.
These executed failures establish Step 2's behavior baseline before implementation.

Parent-verified artifact: `docs-browser-evidence-35132434045-1`, ID 10461064674,
SHA-256 `ebf862a3dd020d477c405bb03674ac4d2d3695c9ac81f1467068f19136497718`.
Local evidence root: `C:/Users/wb384996/AppData/Local/Temp/3/kilo/docs-browser-evidence-35132434045-1`.
The parent applied only the verified repaired lockfile, SHA-256
`5641c6e80be9b96c88dfda09157be84bc96920c585e395c92e2b02ad9f4c22c1`;
exact dependency pins remain unchanged. Preserve this change.

Plan validation passed on resume. The previous halt is resolved by the user's
approved CI fallback, not by an evidence waiver. No local npm installation or
browser run is allowed. Parent owns checkpoint/push/Actions, Pester, and subject
reviews. Later browser runs must disable lock repair. No PR before pipeline
Step 9; eventual base is dev only. The separate generated-proposal preflight
issue belongs to the parent researcher: this task must not change the proposal,
its links, or the preflight checker. Preserve unrelated untracked `.kilo` scratch
files. The 3011-pass checkpoint Pester run is not phase 2 completion evidence.

Current status: active Step 2-3 implementation. V2/V3 and fresh phase 2 full-suite
evidence remain incomplete. No phase completion, commit, push, or later command
is performed by this task. Functional recovery attempts: 0 of 2 per step.

### Phase 2 Implementation Handoff: 2026-09-16T18:52:54Z

Status: `NEEDS_REMOTE_BROWSER` and `NEEDS_CONTENT_REVIEW`. Steps 2-3 implementation
is ready for those checks. It is not phase completion. No `completed-phases`,
`current-phase`, or plan-body change was made. No later phase was started.

#### Implemented Scope

- Seven task-oriented primary groups, with all 76 IDs and source paths retained.
  Primary groups use actual collapsible buttons and open the active group. Hidden
  references stay registered, validated and searchable; compatibility stubs are
  excluded from search. No numeric prefixes or literal backticks in labels.
- `docs/assets/docs-reading.js` owns primary-navigation controls, article-only
  H2/H3 TOC, breadcrumbs, contextual next steps, permalinks, passive current-section
  tracking, geometry measurement, and mobile focus. The router remains in
  `site.js`; both scripts stay below 300 lines. The TOC is a separate right rail
  on desktop and an independent collapsible block above the article at narrower
  widths, never part of the primary drawer.
- Same-page section changes retain the parsed article and do not fetch/render
  again. Redirect mappings are applied before loading. Skip-to-content keeps the
  current route. Loading/errors clear the TOC and disconnect route observers.
  Storage reads/writes are guarded; the DOM retains an in-memory theme choice.
  Existing escaping and navigation-request race guard remain.
- Paper/navy typography is retained. Technical, Research and Shared text badges
  use distinct accessible color tokens; safe fixed-label callouts do not enable
  embedded HTML. Homepage Technical and Research entry paths have equal treatment.
- `modular-guide.md` now leads with the engineering-question/research-claim
  comparison, suite examples, and bounded mixed-work handoffs. Existing headings
  remain. Getting Started and Research Start Here qualify `/cg-setup` by actual
  suite eligibility, rather than requiring an inactive prompt in a CR-only project.
- Skill Management is one guide with the eight required H2 sections. All 17 old
  narratives are short raw-Markdown compatibility pages with preserved headings
  and explicit links. All 12 operation-reference files are byte-unchanged; their
  descriptor paths, result anchors and guide links remain valid. The migration
  tests cover all 29 management entries plus importing content and every frozen
  old-heading destination.
- The command hub has complete editorial checklist rows for every shipped prompt
  and shell wrapper, distinct chat/terminal context, role/suite prerequisites,
  expected output, approval/verification, failure and next step. Eight task
  recipes are in `docs/workflows/index.md`. Exact generated syntax/summary ownership
  remains unchanged until Gate B; no help catalog or runtime-support claim was added.
- The site validator now checks the actually loaded reading helper plus router,
  and rejects a missing helper or missing accessibility contract. Existing legacy
  shells still validate through their original single-script path. No publication
  authority, channel identity, producer upgrade, or release policy was changed.

#### Source Reconciliation And Content Checklist

Current `.github/shared/module-registry.json` declares `cap-skill-management`
support for `cg` only. The guide and command entry therefore use Technical, not a
guessed Shared classification. Capability-layer membership alone does not prove
cross-suite support. Rendering/report-writing capabilities retain their actual
shared support distinction without granting inactive chat prompts eligibility.
The new badge test compares display against canonical support metadata.

The wiki generator permits root-page entries, not nested paths. The final
`docs/_wiki.yml` retains its existing structured entries and generated owners;
an explanatory comment records manual ownership of nested guide/command prose.
No validator was relaxed to admit unsupported paths.

`scripts/tests/fixtures/docs-redesign/phase2-content-edits.json` records nine
explicit importing-content edits, their old-block selectors, canonical authority,
rationale, and mandatory replacement text. The edits correct scope-specific
admission, include the already-supported opaque SVG/resource-class rule, label
synthetic examples, and make plan/apply distinct. Every other preserved block is
checked after only heading-level, whitespace and relative-link normalization.
All retained operation contracts still have exact original hashes. The new edit
record is subject-review input, with `reviewStatus: pending-parent-subject-review`;
it is not reviewer approval and does not change the frozen phase 1 inventory.

| V3 checklist item | Executed evidence / remaining review |
| --- | --- |
| CG/CR comparison and bounded mixed handoff | Link/heading checks pass; technical and research semantic review pending |
| Seven groups and complete registration | Validator: 76 pages, 7 groups; all frozen routes/headings pass |
| One guide, 17 compatibility narratives, 12 retained references | Migration/content tests pass for all 30 preservation pages; subject review of nine edits pending |
| Every public command checklist and eight recipes | Source-inventory coverage test passes; invocation/output/approval semantics need parent subject reviewers |
| Descriptors and evidence anchors | All 12 descriptors still point to registered unchanged operation files; result anchors and canonical consumer links pass |
| One generated owner / manual prose | Complete build freshness and existing managed-interior/prose-preservation tests pass |
| Visual/screen-reader usability | Remote browser/axe/screenshots and focused accessibility review still required; not replaced by Node tests |

Canonical sources inspected for this work include module registry and vendor
policy, the import descriptor, retained operation contracts, and the canonical
`cg-skill`, `cg-release`, `cg-render-doc`, `cg-roadmap-view`, and commit/PR prompt
contracts. Remaining commands use the current generated reference and focused
workflow guides; parent reviewers must check their exact canonical prompts/wrappers.
No complete independent subject review is claimed by this implementation task.

#### Executed Checks And Recovery

| Command/check | Actual result |
| --- | --- |
| `node --test --test-name-pattern "phase 2" scripts/tests/docs-migration.test.js` before content/navigation edits | RED: 2 failed, identifying the old guide structure and eight old groups |
| Initial migration/navigation check | 30 passed, 1 failed; preservation matcher exposed nine explicitly edited importing blocks; the separate migration record now binds each old block to required source-correct text |
| Subsequent migration/navigation check | 35 passed, 1 failed; incorrect new assumption of CG+CR skill-management support rejected by current source; documentation/badge corrected without changing suite metadata |
| Intermediate `node scripts/rebuild-docs.js --check --all` | Failed: `traversal rejected in wiki manifest page file: skills/management/index.md`; removed this task's unsupported nested entry, retained manual ownership and existing validation |
| First complete registered docs Node inventory after shell split | 156 tests: 133 passed, 23 failed. Runtime validator still searched only `site.js` for `aria-current`, and hidden-reference fixture selected the retired group title. No publishing assertions were waived |
| Final complete registered docs Node inventory | **158 passed, 0 failed, 0 skipped/cancelled/todo; 19.564 seconds**. Includes new negative helper/accessibility validation and source-bound badge checks |
| `node scripts/check-docs-site.js` final | Passed: 76 pages, 7 groups, complete skills catalog |
| `node scripts/rebuild-docs.js --check --all` final | Passed: complete build current |
| `node --check docs/assets/site.js` | Passed after final navigation-module split |
| `node --check docs/assets/docs-reading.js` | Passed after final navigation-module split |
| `node --check scripts/check-docs-site.js` | Passed after final validator change |
| `node --check scripts/tests/docs-browser.spec.js` | Passed; syntax only, not browser execution |
| `node scripts/tests/fixtures/docs-redesign/capture-baseline.js --check` | Passed read-only: 76 routes, 30 preservation pages, 347 inbound links, 7 explicit alias decisions |
| Plan `cg-render-artifact --validate-only` | Passed on resume and at handoff; phase metadata unchanged |
| `git diff --check` | Passed; existing LF-to-CRLF checkout warnings only |

Conservative recovery accounting: Step 2 used two correction rounds (source-bound
badge correction, then split-runtime validator/fixture alignment). Step 3 used
two rounds (explicit content-migration reconciliation and removal of unsupported
nested wiki entries). No failing local test remains. If remote behavior or later
required tests fail, return the exact failure to the parent for the bounded-recovery
decision rather than silently start extra repair loops or accept missing evidence.

The final Node command was the exact current `test:docs-automation` inventory,
executed directly to avoid the unavailable local npm setup:

```powershell
$env:TEMP = 'C:\Users\wb384996\AppData\Local\Temp\3\kilo'
$env:TMP = $env:TEMP
node --test --test-reporter=spec scripts/tests/rebuild-docs.test.js scripts/tests/generate-whats-new.test.js scripts/tests/release-version.test.js scripts/tests/docs-snapshots.test.js scripts/tests/legacy-pages.test.js scripts/tests/assemble-docs-site.test.js scripts/tests/check-docs-site.test.js scripts/tests/docs-navigation.test.js scripts/tests/docs-build-contract.test.js scripts/tests/docs-migration.test.js scripts/tests/docs-preview-runtime.test.js scripts/evidence/tests/release-pages.test.js
```

The short TEMP parent was verified first. These variables were process-local.
Existing Windows file-symlink EPERM coverage uses the portable Dirent boundary;
no native symlink qualification is claimed. No local npm install, browser run,
Pester run, or persistent environment change was performed. Editor diagnostics
remain unavailable; JavaScript syntax checks are not an editor-diagnostics pass.

#### Tested Source Identity

HEAD remains `98c5e7181ccda3947a9e93eace87b5ecc9826000`; the final Node run tested
the uncommitted implementation plus the parent-applied lockfile. These blobs came
from `git hash-object --no-filters`, in the final tested working tree:

| Path | Blob |
| --- | --- |
| `docs/assets/site.js` | `d6c05b63476609effcf9722db8241faab7c1bff9` |
| `docs/assets/docs-reading.js` | `519692548d6995034cb3c0f5d45dec45672ddc76` |
| `docs/assets/docs-contract.js` | `4048cc15e627ba6d4b8253971bbfd011a9a3dfc9` |
| `docs/assets/site.css` | `858a408ab3e6591721fa1f4faebab883be8be254` |
| `docs/index.html` | `a410f14947b4f31e8559ceca2b4258aa6494140e` |
| `docs/navigation.json` | `2a9e6783493356390d0491e6b1626bdbf0a8219b` |
| `docs/modular-guide.md` | `b3f80b6e8661a02271173326016bee01f2c23191` |
| `docs/skills/management/index.md` | `6f15fe6e7760148398bd838f08f299c74df75299` |
| `docs/reference/commands.md` | `3779ec80b075861da81446a2a8d1e8489eff11fe` |
| `docs/workflows/index.md` | `d2431afdb4a43bca4ff4f30a794accbb6c8b3bb9` |
| `scripts/check-docs-site.js` | `7ef71322f5ff3eb50bb6e11205fcf88c6fb27ffc` |
| `scripts/tests/check-docs-site.test.js` | `b2674bc9c4b00b42bd9927afb5d906d9e6f0787b` |
| `scripts/tests/docs-navigation.test.js` | `0d0bd9d51ca391268e5dd1d336aae62e2d47ea4b` |
| `scripts/tests/docs-migration.test.js` | `24c4f9fa7516faf6f3caf1f3756ad96a92b0d93d` |
| `scripts/tests/docs-browser.spec.js` | `e8f81c34e4a85aeceab60a6e2a5d2390209d8c95` |
| `scripts/tests/fixtures/docs-redesign/phase2-content-edits.json` | `61bc69471e12fcbdfc6ba97977912b1bf1418f8b` |
| Parent-applied `package-lock.json` | `40093fd2e527b6520d006858889568d84ba7cea8` |

#### Exact Parent Requests

1. `NEEDS_REMOTE_BROWSER`: after the authorized allowlisted checkpoint/push,
   dispatch `gh workflow run tests.yml --repo GPID-WB/compound-gpid --ref improve-website-design`
   with lock repair disabled/default false. Run the entire
   `npm run test:docs-browser -- --reporter=line,json` suite, not a filtered subset.
   Expected current collection is 18 tests. Retain JSON, trace/error output,
   responsive screenshots and run/package/lock/source provenance. Verify the
   exact checkpoint SHA and attempt before accepting results. The independent
   native-preflight proposal issue is owned by the parent researcher, not waived.
2. `NEEDS_CONTENT_REVIEW`, technical/documentation reviewer: review
   `docs/reference/commands.md`, `docs/workflows/index.md`,
   `docs/getting-started/index.md`, `docs/modular-guide.md`,
   `docs/skills/management/index.md`, all 17 changed compatibility narratives,
   and `scripts/tests/fixtures/docs-redesign/phase2-content-edits.json` against
   canonical prompts, bin wrappers, descriptors, vendor policy and module registry.
   Focus on all command checklist rows, eight recipes, CG-only skill eligibility,
   nine importing edits, unique safety/examples, exact apply grammar and retained
   operation/evidence paths. Do not infer that passing links proves semantics.
3. `NEEDS_CONTENT_REVIEW`, research reviewer: review `docs/modular-guide.md`,
   `docs/research/index.md`, the Research entries in `docs/reference/commands.md`,
   and Run Research/mixed-work recipes in `docs/workflows/index.md`. Verify
   comparability, welfare/PPP/survey-design assumptions, human normative choices,
   research integrity and the `/cg-review` versus `/cr-review` boundary against
   current canonical CR prompts. No claim certification or new host-support claim.
4. Required visual/accessibility review: inspect the new root/dev responsive
   screenshots and browser keyboard/axe evidence; review landmarks, focus and
   heading announcements, separate mobile TOC/drawer, actual banner offsets,
   light/dark contrast, 200% zoom and 320px layout. Record what was actually checked;
   absent screen-reader evidence is not a pass.
5. `NEEDS_FULL_SUITE`: through the safety-loaded dedicated parent test subagent,
   run `. tests\Run-Tests.ps1` with no flags or pipeline and approved short
   process-local TEMP/TMP. Return fresh timestamp, source identity, counts,
   failures, `failFast`, `filteredFiles`, missing-file skips and pending/skip
   qualifications. The prior 3011-pass checkpoint is not this phase's gate.

Only after all required V2/V3 evidence and the fresh full-suite gate pass may the
parent resume this phase to finalize completion metadata. No evidence exception
is approved. V1 remains preserved; V4-V8 are not completed by this work. C1-C7
remain enforced within phase 2 scope; phase 3 publishing, search and identity
guarantees are not claimed. Unrelated `.kilo` scratch files, original proposal
and plan links, roadmap, frozen fixtures, and existing release-note output remain
untouched. No commit, push, PR, deployment, five-minute PR wait, or later pipeline
step was performed by this implementation task.

## Run 8: Four Technical Content Corrections, 2026-09-16T22:54:10Z

Status: `NEEDS_REMOTE_BROWSER`; technical reviewer verification and fresh safe
Pester evidence also remain required. Scope was the four concrete P2 corrections
reported by parent reviewer `cg-documentation`, followed only by targeted Node,
generation, preservation, metadata, and whitespace checks. These are explicitly
authorized content-review remediations, not a new test-failure repair allowance.
No new failing test or additional repair loop occurred in this run.

### Received Reviews

Parent supplied the technical review with four P2 findings below. The corrections
are applied, but the technical reviewer has not yet verified them. No clean
technical-review result is claimed.

Parent supplied a passing research review of `docs/modular-guide.md`,
`docs/research/index.md`, the CR checklist/reference material, and research/mixed
recipes. It reported no P0 or material discrepancy, no claim certification, and
no new host-support claim. Those scoped conclusions are retained. This run did
not change that research content or rerun its review. The research pass does not
supply missing technical, browser, accessibility, or full-suite evidence.

### Corrections And Canonical Verification

| Finding | Correction | Canonical source read before editing |
| --- | --- | --- |
| Select-before-fix recipe used autofix review | Both review passes in `docs/workflows/index.md` now use `/cg-review standard --report-only`. The recipe says to decline interactive Fix offers until selecting findings for triage. The review checklist in `docs/reference/commands.md` states that default review immediately applies `safe_auto` fixes and can edit files; manual fixes require approval | `.github/prompts/cg-review.prompt.md:257-267` |
| High-risk onboarding forced light review | `docs/getting-started/index.md` now uses `/cg-review` for automatic risk routing and explains that an explicit depth overrides routing and must match risk | `.github/prompts/cg-review.prompt.md:63-77` |
| Strategy prerequisite permitted only an objective | The strategy checklist requires existing `compound-gpid.md` and a resolved project type from local settings or clarification. Missing-charter recovery is `/cg-setup`; missing or blank project type must be resolved before proceeding | `.github/prompts/cg-strategy.prompt.md:33-44` |
| Import table claimed frontmatter validation for every Markdown file | `docs/skills/management/index.md` now states `Strict frontmatter validation for SKILL.md`; the matching required text and rationale in the phase 2 content-edit record were corrected | `scripts/skill_management/services/admission.py:544-557` delegates bundle inventory; `scripts/skill_management/services/bundles.py:614-623` parses `SKILL.md` |

Only those four Markdown files, the associated non-frozen
`scripts/tests/fixtures/docs-redesign/phase2-content-edits.json`, this report, and
active state were edited by this run. No runtime, canonical prompt, Python,
package, lockfile, or frozen-baseline change was made.

### Executed Checks

| Command | Actual result |
| --- | --- |
| `node --test scripts/tests/docs-migration.test.js scripts/tests/docs-navigation.test.js` | **37 passed, 0 failed, 0 skipped/cancelled/todo** |
| `node scripts/rebuild-docs.js --check --all` | Passed: complete build current; no generated output written |
| `node scripts/check-docs-site.js` | Passed: 76 pages, 7 groups, complete skills catalog |
| `node scripts/tests/fixtures/docs-redesign/capture-baseline.js --check` | Passed read-only: 76 routes, 30 preservation pages, 347 inbound links, 7 explicit alias decisions |
| `./bin/cg-render-artifact.cmd --validate-only .cg-docs/plans/2026-09-16-documentation-ia-ux-redesign.md` | Passed; parent-approved source link retained |
| `git diff --check` | Passed; existing LF-to-CRLF checkout warnings only |

The earlier 158-pass complete docs Node run preceded these four content
corrections. The current result is the 37-test targeted run, not a fresh complete
Node or Pester run. No browser, Pester, installation, commit, push, PR, deployment,
or later-phase command ran here. V2/V3 remain incomplete and phase metadata is not
advanced.

### Parent Bookkeeping Preserved

Parent reports separately approved recovery changes: the exact proposal archive
at `.cg-docs/archive/2026-09-16-documentation-ia-ux-redesign-proposal.md`, original
proposal retained as ignored/untracked after staged index removal, one approved
plan source-link update, and the nullable-handoff test correction plus 11
regressions (94 tests passed in the parent's run). The reported original/archive
SHA-256 is `8c99c6e075d3894abeaf3db9c3ff396a527831a8e065820098adc675ab87d0c6`.
These changes, `.gitignore`, and `scripts/tests/test_issue_dispatch.py` were not
edited, reverted, staged, or tested again by this task. The parent removed only
the eight test-created pyfm/pysum scratch scripts; this task did not remove
anything. The two old `.kilo` fixture directories remain untouched.

### Exact Technical Re-Verification Scope

Recheck only the four reported P2s against the canonical sources in the table:
`docs/workflows/index.md:130-147`, `docs/getting-started/index.md:112-125`,
`docs/reference/commands.md:125` and `:133`,
`docs/skills/management/index.md:381`, and the frontmatter required-text entry in
`scripts/tests/fixtures/docs-redesign/phase2-content-edits.json:49-52`.
Confirm report-only still presents optional Fix offers, explicit depth overrides
risk routing, strategy hard-stops without its charter, and strict frontmatter
validation is specific to `SKILL.md`. Do not close these findings from this
implementer's report alone.

Corrected working-tree identities from `git hash-object --no-filters`:

| Path | Blob |
| --- | --- |
| `docs/workflows/index.md` | `baac83dd15d80f9c4fa7b6be17fcbd4158e8415f` |
| `docs/getting-started/index.md` | `2a9d742722e3820a2fa41eea0311833f6d73c025` |
| `docs/reference/commands.md` | `3762c39a1766975e9eec58a0734a56473a4f7783` |
| `docs/skills/management/index.md` | `73d36db92e3bf166418cbe74e4d053ed2eb85875` |
| `scripts/tests/fixtures/docs-redesign/phase2-content-edits.json` | `bc125b343806bf5384813bf20a7ea1ab1a10d4d0` |

Parent owns technical re-verification, fresh safe Pester, and the subsequent
authorized remote checkpoint/push and complete browser CI with lock repair
disabled. Previous exact remote-browser/artifact requirements remain in force.
No PR before pipeline Step 9; eventual PR base remains `dev` only. No new task
was dispatched and no missing evidence was accepted as a pass.

## Run 9: Early Test Checkpoint, 2026-09-16T23:04:18Z

This is the explicitly approved EARLY TEST CHECKPOINT, not pipeline Step 9 or
`/cg-commit-push-pr`. Scope is the existing phase 2 implementation, verified
lockfile repair, and separately approved proposal bookkeeping and nullable
handoff test correction. Only this report and active state are edited in this
checkpoint preparation. No product or test code changed after the fresh gate.

### Final Content Review Evidence

The parent supplied the final scoped V3 results. Technical reviewer
`ses_f539f41a3ffeZaH3Kcl1mnLawm` independently verified all four Run 8 P2 fixes:
report-only review with optional Fix offers declined, risk-routed onboarding,
strategy charter/project-type prerequisites, and `SKILL.md`-specific frontmatter
validation. The scoped technical review passed. Research reviewer
`ses_f539f41a0ffeRAz138t3Xg7maN` earlier passed the research semantic scope with no
material findings. These are content-review results, not browser, accessibility,
or whole-plan approval. The five corrected source blobs in Run 8 still match.
The content-edit fixture's pending-review label is historical input; final
review evidence is recorded here without changing the tested fixture.

Retained executed checks: migration/navigation 37 passed after correction;
complete docs Node 158 passed before correction; site validation passed for
76 pages and 7 groups; complete build freshness and frozen baseline checks
passed. Parent-supplied native correction evidence: issue-dispatch 94 passed
and drift 19 passed after removal of only the parent's eight scratch Python
scripts. No local test was rerun for this checkpoint preparation.

### Fresh Full-Suite Gate

Read the fresh `tests/last-run.json` and confirmed these fields against the
parent's dedicated safe-runner result. This replaces the earlier pending
full-suite request, but does not complete phase 2.

| Field | Verified result |
| --- | --- |
| Command | `. tests\Run-Tests.ps1`, parent dedicated subagent, no flags or pipeline |
| Start reported by parent | `2026-09-16T22:57:19.6395337Z` |
| Artifact ranAt | `2026-09-16T23:01:05Z` |
| Source HEAD | `98c5e7181ccda3947a9e93eace87b5ecc9826000` |
| Artifact gitSha | `98c5e718`, matching source HEAD |
| Parent-reported exit / passed | 0 / true |
| Total / passed / failed / skipped | 3013 / 3011 / 0 / 2 |
| Skip location | Both in `update`; separate pending counts and individual reasons not recorded |
| failFast / filteredFiles | false / null |
| failures / missing-file skips | Empty arrays |
| Completeness | All 21 canonical test files present |
| Relevant files | docs-automation 24/24; docs-preview 10/10; wiki 126/126 |
| Artifact Git blob, no filters | `2b73b648113aa71b5845b1342f6aeb625d192878` |

The runner used the approved short process-local TEMP/TMP path
`C:\Users\wb384996\AppData\Local\Temp\3\kilo`. The parent reported
non-terminating cleanup warnings. They remain a cleanup qualification, not a
failed test or evidence exception. Do not report all 3013 tests as passed.

### Checkpoint Boundary

Inspected Git status, actual diffs, and the ten recent commits. HEAD and the
existing upstream both match the source SHA above. The retained local proposal
and archive both have SHA-256
`8c99c6e075d3894abeaf3db9c3ff396a527831a8e065820098adc675ab87d0c6`.
The original remains present and ignored by its exact path; its existing staged
deletion is preserved. The plan has only the approved source-link revision.
The repaired lockfile still has SHA-256
`5641c6e80be9b96c88dfda09157be84bc96920c585e395c92e2b02ad9f4c22c1`.

Stage only the approved changed docs sources, phase 2 helper/tests/content-edit
fixture, `.gitignore`, issue-dispatch test, archive, plan, report, state, and
lockfile. Exclude both leftover `.kilo` GUID directories, all scratch/temp files,
`tests/last-run.json`, and downloaded artifacts. Preserve unrelated files.

Status: ready for the approved checkpoint commit and push to
`origin/improve-website-design`, then normal dispatch with no repair flag:

```text
gh workflow run tests.yml --repo GPID-WB/compound-gpid --ref improve-website-design
```

At this precommit record, commit/push/dispatch are pending. Stop after dispatch;
do not run later pipeline steps. Browser/visual/accessibility evidence remains
pending. Phase 2 remains incomplete, with `completed-phases: [1]`,
`current-phase: 2`, and plan status active. No evidence exception, PR, deployment,
or phase completion is authorized by this checkpoint. `nextCommand` stays null.
