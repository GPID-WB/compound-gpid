# Release Controller Execution Report

- Plan reference: `.cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`
- Current invocation: pipeline step 11, `/cg-commit-push-pr --base dev`.
- Active deviation policy: `ask`; no runtime override.
- Current status: Phase 7 **Success-qualified**, complete under approved local/live deferral with all current local gates passing and both P2 findings independently fixed (zero open/unverified/new). Completed phases [1,2,3,4,5,6,7]; current-phase removed in crash-safe order. Plan remains active; V8 and whole-plan acceptance remain pending for the later committed gate and ordinary PR CI. Publisher disabled. Historical runs, qualifications and counters below are preserved.
- Current assessment: `.cg-docs/work-reports/release-controller/2026-09-13-phase7-final-evidence.json`. Prior implementation, failed/passing gates, GPG diagnosis, review, repair and Phase 6 assessments remain unchanged as historical evidence.
- Current pipeline gate: prepare failed on stale handoff metadata; routing corrected, complete prepare rerun pending. No staging, commit, push or PR submission. See the dated step 11 entry below.

## Run 2026-09-11

Preflight stopped before implementation. The available session tools do not
include `execution_subagent` or a native child-task runner. Phase 1 Step 2
requires legacy Pester tests, and the phase boundary requires the full safe
Pester gate. The loaded Pester safety skill requires execution through a child.
Plan C6 and the blocked-stop contract prohibit a direct-shell substitute.
No Pester command was attempted. Agent Manager sessions were not requested and
were not created as a substitute. The missing tool is a capability blocker,
not a failed test or a consumed recovery attempt.

## Completed Scope

- Read local Kilo command, project instructions, charter/configuration, phase
  scope, artifact, context-loading, goal-execution, and active-state contracts.
- Loaded Pester safety and Brain query skills; consulted saved release decisions.
- `cg-render-artifact --validate-only .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`: passed.
- `cg-index query --intent work --query "release controller Pester safety package isolation subprocess timing" --budget 800 --format md`: succeeded; two selected artifacts, 591 index warnings. No runtime evidence inferred.
- Relevant Brain source: `.cg-docs/solutions/bugs/2026-08-26-release-drift-ignore-checks-spawn-thousands-of-git-processes.md`; retain bounded subprocess counts and do not infer live speedup.
- `open-brain` tools unavailable; local Brain query used.
- No implementation steps or phases completed. Tests run: 0. Review agents run: 0; `review:auto` not reached.
- Recovery attempts used: Step 1 = 0/2; Step 2 = 0/2. No budgets reset.

## Evidence

| ID | Status | Evidence |
|---|---|---|
| V1 | blocked | Package, build/install, CI, timing, baseline, and safe Pester checks not executed |
| V2-V7 | not started | Later phases excluded from this invocation |
| V8 | not started | Final gate excluded from this invocation |

## Constraints Check

| ID | Status |
|---|---|
| C1 | No remote writes performed; runtime assertions not run |
| C2 | No controller implementation or credential access; tests not run |
| C3 | No branch override attempted; tests not run |
| C4 | No proposal or confirmation behavior implemented; tests not run |
| C5 | Existing payloads and release identities unchanged; tests not run |
| C6 | Preserved by stopping; required child runner unavailable |

## Deviations And Exceptions

None approved or applied. Roadmap unchanged, as required by the plan.
Existing untracked plan and brainstorm content preserved; only the permitted
execution-report pointer was added to plan frontmatter. No code, commit, push,
PR, remote setup, release, or later pipeline command executed.

## Remaining Uncertainty And Handoff

All Phase 1 implementation and runtime evidence remain outstanding. Resume
in a session with the required safe child runner, using the exact invocation
above. Do not start Phase 2 until Phase 1 V1 and the phase gate pass and
`review:auto` is completed. Plan completion fields remain unchanged.

## Resume 2026-09-11T17:29:17Z

The parent clarified that it has native child-task dispatch and launched this
implementation child. The earlier stop did not establish absence of capability
in the parent. The approved continuation uses separate parent-dispatched Pester
and review children; no direct-shell Pester substitute has been used here.
The current blocker is an explicit sequential test handoff, not lack of parent
capability. Earlier run history above is retained, not reset.

### Implementation Scope

- Step 1 implemented locally: standalone Hatchling/src package, locked dependencies,
  four-command fail-closed CLI, strict schema-v1 policy/request/event/provenance
  models, canonical digest fixture, SemVer/legacy/invariant corpus, redacted errors,
  argv process boundary, installed-wheel tests, offline six-cell CI and aggregate,
  and separate locked controller preflight route. No provider operations enabled.
- Step 2 partially implemented: opt-in injected-clock recorder and non-publishing
  fixture benchmark. Confirmation is a separate timing category; actual CLI human
  confirmation remains disabled with all beyond-contract behavior until Phase 2.
- Prepared three legacy Pester timing tests in the existing offline fixture.
  `create-release.ps1` is unchanged. The new `-Timing` parameter is deliberately
  absent until the parent returns the Pester red-phase evidence.
- No phase completion fields changed. No later phase, commit, push, PR, remote
  mutation, setup, or live trial performed. Roadmap remains unchanged.

### Executed Evidence

| Check | Command or artifact | Result |
|---|---|---|
| Step 1 red | `python -m pytest scripts/tests/test_cg_pr_preflight.py -q` | 8 expected failures for missing controller_required; 37 passed |
| Step 1 red | package test_contracts.py before implementation | Collection failure: missing cg_release.cli |
| Step 1 CI red | package tests excluding installed tests, before workflow addition | 6 missing-workflow failures; 51 passed |
| Package regression | `uv run --project packages/cg-release --python 3.12 --locked pytest packages/cg-release/tests -q --tb=short` | 77 passed after timing implementation |
| Native preflight | `python -m pytest scripts/tests/test_cg_pr_preflight.py -q --tb=short` | 46 passed |
| Diagnostics | `uv run --project packages/cg-release --python 3.12 --locked ruff check packages/cg-release scripts/benchmark_release.py` | Passed |
| Distributions | `uv build --project packages/cg-release --python 3.12` | Wheel and sdist built under packages/cg-release/dist |
| Installed wheel | test_install.py real temporary environment, outside source tree | All four console help commands and disabled-operation smoke passed |
| Step 2 red | test_timing.py before implementation | Collection failure: missing cg_release.timing |
| Offline baseline | `.cg-docs/work-reports/release-controller/2026-09-11-offline-baseline.json` | 3 local Git calls; 1 gate; 0 remote writes; live baseline/speedup missing |
| Whitespace | `git diff --check` | Passed before checkpoint append |
| Pester | Dedicated child result pending | Not executed in this implementation session |
| review:auto | Full route required for release/schema/install/security changes | 0 review agents executed; pending after implementation and tests |

The offline report was generated with:
`uv run --project packages/cg-release --python 3.12 --locked python scripts/benchmark_release.py --offline --output .cg-docs/work-reports/release-controller/2026-09-11-offline-baseline.json`.
Local platform: Windows Server 2022, Python 3.12.0, uv 0.11.3. The first red
package invocation used uv's default Python 3.14.3; all green commands explicitly
selected 3.12. No Linux/macOS or six-cell remote execution is claimed.

Installed-wheel test commands are executable in `test_install.py`: `uv build
--project <package> --python <current-interpreter> --no-build-isolation --out-dir
<temporary-dist>`; `uv venv --python <current-interpreter> <temporary-env>`;
`uv export --project <package> --locked --no-dev --no-emit-project --output-file
<requirements>`; `uv pip install --python <temporary-python> --require-hashes -r
<requirements>`; `uv pip install --python <temporary-python> --no-deps <wheel>`;
then each installed `cg-release <command> --help` and isolated module smoke.
These paths are allocated by pytest outside the source tree.

Resolved direct dependencies: semver 3.0.4, Pydantic 2.13.5, Loguru 0.7.3,
tomlkit 0.15.1, packaging 26.3. Build/test tools: Hatchling 1.32.0, build 1.6.1,
pytest 9.1.1, Ruff 0.16.7. All dependency resolutions are in package `uv.lock`.

### Recovery Accounting

- Step 1 functional recovery: 2/2 used, both resolved. Attempt 1 added bounded
  pytest parameter IDs after an oversized case exceeded Windows' environment
  variable limit. Attempt 2 added exact SemVer round-trip rejection because the
  library accepts a trailing newline; invalid corpus cases now test the controller
  boundary with the same required rejection outcome. No assertions were weakened.
- Step 1 diagnostics: 1/2 used; Ruff formatting and removal of an unreachable
  runtime branch resolved 16 diagnostics. Unsupported runtime rejection is proven
  through distribution Requires-Python metadata; no Python 3.10 execution claimed.
- Step 2 functional recovery: 0/2 used. The initial missing-module collection
  failure is the expected red phase, not a recovery attempt.
- Step 2 diagnostics: 1/2 used; one nested-with style issue resolved.
- No budgets reset. Further Step 1 unresolved test failures must stop the path.

### Current Verification Surface

V1 is partial: package/build/install/schema/CI wiring/preflight/timing/offline
baseline evidence passed locally. Legacy instrumentation, targeted and full safe
Pester evidence, final diagnostics, and review:auto remain outstanding. V2-V8
remain unstarted. C1-C5 implementation checks remain phase-scoped; no remote
protection, authorization, or publication evidence is inferred. C6 is preserved
by delegating safe Pester execution through the parent.

### Required Parent Handoff

Dispatch one dedicated test child in this worktree. Load
`cg-skill-pester-safety`, then run `. tests\Run-Tests.ps1 -File create-release`
with no other flags and no pipeline. Read `tests/last-run.json` and return only
`passed`, `failedCount`, `failures`, and `filteredFiles` (include counts if available).
Expected red cases are the two opt-in timing tests because the production script
does not yet declare `-Timing`; the default-disabled timing test should pass.
Do not implement fixes in that test child. Return the result to this implementation
child before any publisher instrumentation. Unexpected prior-test failures require
separate diagnosis and must not be hidden as intended red evidence.

After red confirmation: implement only narrow opt-in legacy timing, get targeted
Pester green, run the unfiltered safe phase gate, and dispatch the full review route
sequentially. The full route is the eight standard agents plus
cg-learnings-researcher and cg-adversarial, once each, under the review contract.
Review should examine Phase 1 changes only and preserve all protected assets.
Phase 2 remains prohibited until Phase 1 completion and review evidence are recorded.

Current status: `blocked` at the parent-dispatched Pester red-phase handoff.

## Resume 2026-09-11T17:35:58Z

The parent returned the dedicated child Pester red result. This session also
read `tests/last-run.json`: ranAt `2026-09-11T17:32:05Z`, gitSha `b94f585`,
totalCount 95, passedCount 93, failedCount 2, filteredFiles `create-release`.
Only the two intended opt-in timing cases failed, both because `-Timing` was
not yet declared. Existing cases passed. This is confirmed red evidence, not
a recovery attempt, a full-suite gate, or an irreversible failure.

### Publisher Instrumentation

- Added opt-in `-Timing` with documented JSON Lines stderr output.
- Added fixed-label Stopwatch records for preparation, all pre-publication
  gates, the native preflight subprocess, publication, and Finalize reconciliation.
- `finally` records distinguish complete spans from interrupted spans. Records
  never include tag/name/notes, paths, command argv, credentials, HTTP bodies,
  or exception text. Disabled timing creates no clocks and emits no records.
- The timing sink reports a generic warning if unavailable, without replacing
  the original operation outcome after a remote write.
- Original validation and publication statements retain their order. No gate,
  tag grammar, credential access, retry, API mutation, or publisher authority was
  removed or broadened. No publisher command was executed by this child.

### Verification

- Windows PowerShell AST parse of `create-release.ps1`: 0 errors; parser only,
  no script execution and no Pester execution in this implementation child.
- Full package pytest regression: 77 passed.
- Native preflight pytest regression: 46 passed.
- `git diff --check`: passed before this checkpoint append.
- No new functional failures or diagnostic fixes. Recovery budgets remain:
  Step 1 functional 2/2 used and resolved; Step 2 functional 0/2 used;
  diagnostics 1/2 used per step. No budgets reset.
- Mechanical self-review found no new debug code, broken imports, TODOs, or
  hardcoded credentials. Statistical and logical correctness are not established
  by that mechanical check; the full routed review remains required.

### Next Dedicated Test Child

In this worktree, load Pester safety and run
`. tests\Run-Tests.ps1 -File create-release` with no other flags or pipeline.
Read and retain the compact `tests/last-run.json` result before another run.
Return `passed`, total/passed counts, `failedCount`, `failures`, and `filteredFiles`.
The expected green result is 95/95 with zero failures; this expectation is not
evidence until executed.

If and only if that targeted run passes, the same dedicated test child may next
run `. tests\Run-Tests.ps1` with no flags or pipeline. Return the same compact
fields and require `filteredFiles: null` for the full phase gate. If either run
fails, return the result without applying fixes or starting reviews. The parent
must keep these runs sequential with all writers stopped.

After the test evidence passes, the full ten-agent review:auto route is still
required. No review result, phase completion, or Phase 2 authorization is claimed.
Current status: `blocked` pending dedicated targeted and full Pester evidence.

## Resume 2026-09-11T17:41:57Z

Dedicated test-child results received:

- Targeted `. tests\Run-Tests.ps1 -File create-release`: passed true, 95/95,
  failedCount 0, failures [], filteredFiles `create-release`.
- Full `. tests\Run-Tests.ps1`: passed true, totalCount 2906, passedCount 2904,
  failedCount 0, skippedCount 2, failures [], filteredFiles null.
- This child read `tests/last-run.json` directly: ranAt 2026-09-11T17:40:51Z,
  gitSha b94f585; the create-release row is 95/95. Both skips are in `update`;
  the artifact does not supply their names or reasons.
- The parent reported repeated TestDrive cleanup RemoveFileSystemItemIOError
  messages for missing paths/nonempty directories under temporary
  fresh-manifest-kilo-project. These are retained as a qualification. The runner
  completed with zero test failures, but successful temporary-directory cleanup
  is not claimed. No claim is made that these errors were fixed or independently
  diagnosed by this implementation child.
- Compact durable evidence:
  `.cg-docs/work-reports/release-controller/2026-09-11-pester-phase1.json`.

The required unfiltered safe-runner gate passed according to the executed runner
artifact. Phase 1 package, build/install, schema, offline CI wiring, preflight,
timing, offline baseline, and legacy functional checks have local evidence.
No required V1 case was reported skipped. Final completion still waits for the
explicit review:auto stage requested by this invocation. No phase completion
fields are written yet; no recovery budget was used by these passing runs.

### Review Routing

Read `.kilo/commands/cg-review.md` and re-read the shared routing contract.
Deterministic triggers: release automation/publishing in create-release.ps1,
schema boundaries in models.py, installed-wheel paths, credential/error
redaction, and workflow/preflight security controls. The resolved risk class is
security-risk and the resolved mode is `full`. The eight standard agents plus
cg-learnings-researcher and cg-adversarial are required once each. This is the
embedded `/cg-work review:auto` stage, not a new pipeline `/cg-review` command.

### Required Review Child

The parent should dispatch one dedicated review child in this same worktree,
with all implementation writers paused. Execute the embedded review:auto stage
of `/cg-work phase1 review:auto .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`,
resolved mode `full`. Use the local review prompt's bearings, scope, Brain,
agent-output-quality, priority, and report-schema rules. Do not execute a later
pipeline command, autofix, fix-triage, commit, push, PR, or remote write.

Run these ten local agent specs sequentially, exactly once each:
cg-code-quality, cg-testing, cg-documentation, cg-version-control,
cg-reproducibility, cg-performance, cg-architecture, cg-data-quality,
cg-learnings-researcher, cg-adversarial. Load `.kilo/agents/<name>.md` and the
relevant Python/Pester skills. If native subagent dispatch is unavailable inside
the review child, use the repository adapter's sequential in-thread emulation;
do not represent that as ten independent sessions. Every agent result must have
findings or an explicit no-issues statement with file context; flag incomplete
outputs without automatic retry. Preserve P0/P1 reporting strength.

Review only the Phase 1 changes, including new untracked files:

- `packages/cg-release/`: pyproject.toml, uv.lock, src, tests, fixtures; exclude
  .venv, dist, build, __pycache__, and test/lint caches.
- `.github/workflows/release-controller-ci.yml`.
- `scripts/cg_pr_preflight.py` and `scripts/tests/test_cg_pr_preflight.py`.
- `scripts/benchmark_release.py`.
- `create-release.ps1` and `tests/create-release.Tests.ps1`.
- Associated execution report, offline baseline, Pester evidence, and active-state
  checkpoint for evidence consistency only. Read the selected plan's Phase 1 and
  relevant design contracts as authority, not as proof of implemented behavior.

Do not treat untouched brainstorm content, future-phase planned functionality,
or generated view bodies as implementation changes. Do not require live sandbox
or remote six-cell execution in Phase 1; they are later required evidence. Do
verify disabled behavior, schema/security boundaries, install isolation, old
Python route preservation, interpreter selection, aggregate failure handling,
timing truthfulness, and unchanged legacy publication authority. Investigate
cleanup qualifications only enough to determine their effect on required evidence.

Include this protected-artifact constraint for every agent: never recommend
deleting, replacing, renaming, or moving `.cg-docs/brainstorms/`,
`.cg-docs/solutions/`, `.cg-docs/archive/`, compound-gpid.md,
compound-gpid.local.md, roadmap.json, SCHEMA_VERSION, or `.github/` infrastructure.
Content/security/schema findings are still reportable. Preserve unrelated files.

The review child may create only the consolidated report at
`.cg-docs/reviews/2026-09-11-generic-asynchronous-release-controller-review.md`
(not present at handoff), with plan reference, depth full, type standard, finding
IDs/statuses, ten-agent completion coverage, test/cleanup qualifications, and
file/line evidence. Mark findings open; apply no implementation fixes. Return
only status, agent completion count, P0/P1/P2/P3 counts, critical finding summaries,
and the artifact path to this implementation child for bounded handling.

Model advisory (implementation transition): strong option is a capable reviewer
with independent critical reasoning and high effort for release/schema boundaries;
an economical option is suitable only for bounded mechanical checks. This is
capability-only advice, not a routing override. Suggestions and availability
vary by platform/date; the user chooses model and effort. No selection changed.

Current status: `blocked` pending full review output, 0/10 agents completed.

## Resume 2026-09-11T17:54:30Z

Read the completed embedded full review:
`.cg-docs/reviews/2026-09-11-generic-asynchronous-release-controller-review.md`.
Coverage is 10/10 local agent specs emulated sequentially, not ten independent
sessions. The report has four open findings: P0 0, P1 1, P2 3, P3 0.

### Open Findings

| ID | Step | Finding | Disposition |
|---|---|---|---|
| P1.1 | 1 | Authorization: token with an opaque value bypasses argv rejection and diagnostic/event redaction | Open; blocks Phase 1 completion |
| P2.1 | 1 | Explicit empty version/channel options bypass CLI validation | Open |
| P2.2 | 1 | Existing native preflight producers do not provision the newly required pinned uv tool | Open |
| P2.3 | 2 | Benchmark resource-count test observes a manual report counter rather than actual process execution | Open |

The review used synthetic, in-memory probes for P1.1 and P2.1. No real credential
exposure or remote operation was established. Existing passing tests remain
valid records of the cases they ran, but do not refute these missing checks.

### Contract And Budget Decision

- Re-read `/cg-work` Step 2 Test Failure Recovery (lines 149-159): it applies to
  functional tests and permits two fix attempts total per plan step.
- Re-read Auto-Fix Diagnostics (lines 161-166): its separate two-round allowance
  applies to IDE errors, not review findings or logical test failures.
- Re-read embedded Review-Mode Handoff (lines 221-233): it specifies route-aware
  dispatch and P0/P1 reporting strength. It defines no autonomous review-fix loop
  and no separate numeric review-repair allowance.
- `/cg-review` Step 4 has a tagged-finding triage procedure, but it is not the
  embedded `/cg-work` dispatch contract. The supplied report has no safe_auto
  disposition, and this invocation does not authorize starting that separate
  command or `/cg-fix-triage` as an early pipeline step.
- The plan's Iteration Policy retains two-attempt per-step recovery and requires
  approval for contract deviations under `deviation-policy: ask`.

Functional failures and review findings are distinct; no new test failure or
additional functional attempt is claimed here. However, the loaded contracts do
not supply the requested separate bounded review-repair procedure. Step 1 has
already used both functional attempts, resolved, so this child cannot infer a
fresh two-round allowance or relabel the critical defect as a diagnostic. The
parent's conditional instruction preserved those boundaries rather than approving
a budget extension or a new repair procedure. Stop at that authorization boundary.

No review correction was attempted. Budget state is unchanged: Step 1 functional
2/2 used and resolved, Step 2 functional 0/2; diagnostics 1/2 used per step.
No separate review-fix budget was invented, consumed, or reset. No failures were
added to `failing-steps` because the existing executed suites passed; the review
report is the authority for the open critical finding.

### Gate Status And Handoff

- Phase 1 implementation and full review are performed, but Phase 1 is not
  complete: P1.1 disproves the required redaction/credential boundary in V1.
- Preserve all implementation, test evidence, cleanup qualifications, and open
  review finding statuses. Plan completion fields remain unchanged.
- No new tests are needed to repeat the already-confirmed review finding merely
  to consume another recovery round. A future authorized repair should add exact
  negative regressions, fix the four scoped findings, re-run affected checks, and
  independently verify the fixes before a Phase 1 completion decision.
- Necessary handoff: obtain explicit authorization for a separately bounded
  review-repair action under the stored ask policy. Do not infer permission to
  reset Step 1 budgets or run the later fix-triage pipeline now.
- No later phase, remote write, commit, push, PR, or separate pipeline command ran.

Final current status: `blocked` by open P1.1 and absent authority for an additional
review-repair procedure. Review coverage is complete, 10/10; all four findings
remain open. Phase 2 must not start.

## Authorized Repair 2026-09-11T18:24:33Z

The user explicitly authorized continuing Phase 1 and repairing all four findings
on 2026-09-11T18:15:23Z. The parent correctly clarified that the two-attempt rule
applies to functional-test recovery, not a blanket ban on review repairs. The
earlier interpretation that absence of a dedicated review loop itself prevented
repair was too restrictive. This continuation corrects that interpretation;
it does not erase the historical report or reset any recovery counter.

### Repair Accounting

- Authorized review-repair implementation passes: 1.
- New negative-test red baseline: 28 package failures and 5 preflight failures,
  expected before repair. They are not failed green runs or prior-step retries.
- Failed post-repair functional runs: 0. The first green package run passed 107
  tests; an additional explicit fourth-call budget test raised final coverage to
  108, also passing.
- One new lint issue was corrected by formatting; no semantic recovery loop.
- Earlier counts stay unchanged: Step 1 functional 2/2 used and resolved;
  Step 2 functional 0/2; earlier diagnostics 1/2 per step. No fabricated review
  allowance, budget reset, or separate fix-triage command was used.

### Four Findings Repaired

- P1.1: process argv rejection now checks the authorization field key separately
  from the display redactor. Diagnostics remove complete authorization values,
  independent of token prefix or scheme, including folded headers. New synthetic
  regressions prove rejection before subprocess execution and no human/JSON leak.
- P2.1: version/channel supplied-option checks use `is not None`. Explicit empty
  values and forbidden combinations reject through the parser and CLI main.
- P2.2: the existing native-target CI producer installs uv==0.11.3. Shared
  preflight selection first checks the exact uv version and reports actionable
  local install prerequisites if missing or wrong. This also covers the existing
  legacy/local producers through their shared preflight invocation. The selector
  still imports on Python 3.8; package execution alone selects Python 3.11/3.12.
  Native CI setup is a narrow direct-integration correction, not remote setup.
- P2.3: OfflineGit restricts and counts calls at its local process boundary.
  Tests spy on real Popen execution, reject network/gh or unlisted Git operations,
  compare observed and reported counts, and demonstrate detection of an injected
  duplicate-call defect. A fourth wrapper call fails before execution. The real
  offline smoke test remains present.

The existing review report's four statuses are `fixed` with local evidence and
an explicit independent-verification-pending qualification. Original findings
and review observations remain intact as historical evidence.

### Executed Checks

| Check | Result |
|---|---|
| `uv run --project packages/cg-release --python 3.12 --locked pytest packages/cg-release/tests -q --tb=short` | 108 passed |
| `python -m pytest scripts/tests/test_cg_pr_preflight.py -q --tb=short` | 52 passed |
| `uv run --project packages/cg-release --python 3.12 --locked ruff check packages/cg-release scripts/benchmark_release.py` | Passed |
| `python scripts/cg_pr_preflight.py --phase prepare --changed-file packages/cg-release/src/cg_release/process.py --run-native-target --format text` | Passed actual package-only route: uv version, pytest, Ruff, locked build; native-only test list not substituted |
| `git diff --check` | Passed before report update |

The actual preflight reported 322 local-only cache paths with its bounded first
100 sample. They were not tracked/manifest-owned and were nonfatal; no cache
cleanup was attempted. This is a prepare-phase working-tree run, not the final
committed-candidate gate. Package tests include real installed-wheel smoke in a
temporary generic directory; no live hosting or publication call was made.

Post-repair offline report was created, without overwriting the prior baseline,
using `uv run --project packages/cg-release --python 3.12 --locked python
scripts/benchmark_release.py --offline --output
.cg-docs/work-reports/release-controller/2026-09-11-offline-baseline-review-repair.json`.
The publisher script and its Pester cases were unchanged by the review repairs.
The CI workflow, shared preflight producer, package, and timing benchmark changed.

### Exact Sequential Child Handoff

1. Dedicated test child: load Pester safety and run `. tests\Run-Tests.ps1`, no
   flags or pipeline. Return passed, totalCount, passedCount, failedCount,
   skippedCount, failures, filteredFiles, and a concise cleanup qualification.
   Require an unfiltered successful result. Do not apply fixes. Stop on failure.
2. If that passes, dedicated finding-verification child: verify P1.1, P2.1, P2.2,
   P2.3 against the fixed scopes and executed evidence in the review's Authorized
   Repair section. Use cg-code-quality and cg-testing specs sequentially, with
   explicit security/reproducibility/resource-bound focus. Read the local review
   verification rules, but do not start a separate pipeline command, perform
   autofix, or repeat the full ten-agent route without a new need. Always report
   P0/P1 and cross-file breakage; do not suppress genuine fix regressions.
3. The verification child may write only
   `.cg-docs/reviews/2026-09-11-generic-asynchronous-release-controller-verify-review.md`,
   using verification frontmatter with parent-review pointing to the full review.
   Return verified finding IDs, remaining/new priority counts, incomplete scopes,
   and artifact path. Apply no implementation fixes or completion metadata.

Scope includes packages/cg-release source/tests, scripts/cg_pr_preflight.py and
its tests, scripts/benchmark_release.py, and both CI producer workflows. Exclude
environments/builds/caches and unrelated or future-phase work. Preserve the
global protected-artifact constraint from the original review handoff. Pester
and review children must run sequentially with this writer paused.

Current status: `blocked` only pending refreshed safe gate and independent
verification evidence. Repair authorization is resolved. No phase completion,
Phase 2, commit, push, PR, or remote write is claimed or executed.

## Phase 1 Completion 2026-09-11T18:37:52Z

Final Phase 1 status: **Success**. Both in-scope implementation steps and the
requested embedded review:auto stage are complete. Later phases are unstarted.
This section supersedes prior blocked handoffs without deleting their history.

### Final Evidence Gate

- Read refreshed `tests/last-run.json`: ranAt 2026-09-11T18:31:09Z, gitSha b94f585,
  passed true, total 2906, passed 2904, failed 0, skipped 2, failures [], and
  filteredFiles null. The create-release row is 95/95 with no failures or skips.
- Both skips belong to update; names and reasons are absent. Retain the known
  TestDrive cleanup missing-path/nonempty-directory errors. They do not appear as
  failed assertions in the executed runner result; successful cleanup is not
  claimed. The independent verifier found no evidence that they invalidate V1.
- Read the independent verification report. Both sequential specs completed;
  P1.1/P2.1/P2.2/P2.3 are confirmed fixed. Remaining/new findings: 0 at every
  priority. The verifier ran 102 package tests plus 52 preflight tests, all
  passing, with six installed-wheel tests deliberately deselected. Its boundary
  probes and Ruff passed. One initial probe quoting error was corrected without
  source changes; it was not a product failure or recovery attempt.
- The complete post-repair package run in this implementation child passed all
  108 tests, including the six real build/install tests. The actual package-only
  prepare preflight executed the pinned-tool check, package pytest, Ruff, and
  locked wheel/sdist build successfully. Thus the verifier's bounded deselection
  does not leave required installed-wheel evidence missing.
- Executed offline timing evidence records 3 local Git calls, 1 gate, and 0 remote
  writes. Live baseline and speedup remain absent, not zero or inferred success.

V1 is passed for Phase 1. No required Phase 1 evidence exception was needed.
V2-V7 and final V8 remain unstarted. CI configuration, failure-path tests, and
producer setup were verified locally; no remote six-cell execution, release-mode
registration, sandbox trial, committed-candidate gate, or publication is claimed.

### Constraints And Scope

- C1/C5: no published object, payload, pin, or attestation identity changed.
- C2/C3: credential rejection and disabled operation contracts passed their
  Phase 1 checks; future remote policy/authorization protections are not enabled
  or claimed verified.
- C4: CLI contract validation passed; preview/confirmation/admission remain
  intentionally disabled for later implementation.
- C6: targeted and unfiltered Pester gates ran in parent-dispatched dedicated
  test children through the canonical runner. This implementation child did not
  execute Pester directly.
- Full review coverage: 10 sequential agent specs, followed by 2 sequential
  finding-verification specs in a separate child. No claim of twelve independent
  sessions or remote security testing is made.

Changed implementation comprises packages/cg-release source, lockfile and tests;
the new controller CI workflow; narrow native CI uv provisioning; preflight
selection/prerequisite code and tests; offline benchmark; and opt-in legacy
publisher timing and its Pester tests. Associated plan metadata, reviews, work
report, evidence snapshots, and active-state handoff are updated. Existing
brainstorm content and unrelated changes remain preserved.

### Completion Metadata

Applied the crash-safe phase sequence: first wrote `completed-phases: [1]`,
then re-read and verified it, and only then wrote `current-phase: 2`.
Plan `status: active` remains unchanged; no whole-plan completed date is added.
Current phase 2 is an informational next-phase pointer, not execution evidence.

Recovery history is preserved: Step 1 functional 2/2 used and resolved; Step 2
functional 0/2; earlier diagnostics 1/2 per step. Authorized review repair used
one implementation pass with no failed post-repair functional run. No counters
were reset and no separate fix-triage pipeline command was executed.

Final compact evidence:
`.cg-docs/work-reports/release-controller/2026-09-11-phase1-final-evidence.json`.
Verified review:
`.cg-docs/reviews/2026-09-11-generic-asynchronous-release-controller-verify-review.md`.

Suggested commit only, not executed:
`feat(release): complete phase 1 package contracts and timing baseline`.

Next handoff command, not executed:
`/cg-work phase2 review:auto .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`.
This child stops at the Phase 1 boundary. No commit, push, PR, remote write, or
later phase has been executed.

## Phase 2 Start 2026-09-11

Invocation: `/cg-work phase2 review:auto .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`.
Active deviation policy remains `ask`. Scope is globally numbered Steps 3-4
only, followed by dedicated verification and embedded review:auto. Fixable
in-scope review findings may be repaired; absence of a named review-repair loop
is not an authorization blocker. No recovery counters are reset.

Read the local command first, project instructions, charter/config, complete plan,
execution and artifact contracts, Phase 1 final evidence, and relevant brainstorm
CLI/design sections. The plan validator passed. Current completion metadata is
`completed-phases: [1]`, `current-phase: 2`; V1 evidence confirms that boundary.
No roadmap write is authorized or performed.

Loaded Python, Brain-query, and Pester-safety skills and Python instructions.
The bounded Brain query selected the plan and
`.cg-docs/solutions/git-workflows/2026-08-13-verified-pages-artifact-and-release-tag-gates.md`:
retain exact immutable input identities; do not import its older main-only branch
policy over the current plan. Query reported 593 index warnings. `open-brain`
is unavailable in this child; no live evidence is inferred from Brain results.

Test index: existing package test_contracts.py, test_install.py, test_process.py,
and test_timing.py. Step 3/4 test modules do not yet exist. Existing Phase 1
implementation and unrelated worktree changes are preserved.

Step 3 starts with new version-selection tests before production implementation.
Dedicated execution is required by this invocation. This child has no nested
task tool; the parent has task dispatch. The next boundary is a parent-dispatched
test sibling, not a claim that testing is unavailable to the workflow.

### Step 3 Red-Phase Handoff

Added `packages/cg-release/tests/test_versions.py`: stable bumps, numeric RC
continuation, shared syntax/precedence corpus, explicit initial version/promotion,
ambiguous sequences, metadata-insensitive global collisions, maintenance lines,
core bounds, direct-call option validation, and malformed adopted history.
These are the first Step 3 tests, not complete V2 coverage. Policy/provider tests
and all Step 4 cases remain to be written before their implementation changes.
Production `versions.py` does not yet exist. No test has been executed in this
session; missing-module collection failure is expected, not confirmed evidence.

Parent: dispatch one dedicated test sibling in this same worktree with all
writers paused. Run exactly:

`uv run --project packages/cg-release --python 3.12 --locked pytest packages/cg-release/tests/test_versions.py -q --tb=short`

Return exit code, collection/test counts, and the one-line collection error.
Expected error: missing `cg_release.versions`. Do not implement fixes, run Pester,
run review, or make remote calls in this red-only sibling. Return its result to
this implementation child, then resume Step 3. If collection fails for an
environment/import error other than the absent production module, diagnose that
separately rather than calling it red confirmation.

Current status: `handoff` for sequential dedicated testing. Phase 2 is not
complete. Tests executed: 0; review specs executed: 0. V2 pending; V3-V8 remain
outside this invocation. No remote authority is needed for the offline red check.
Phase 2 submission stays disabled until Phase 3. No production implementation,
Pester run, commit, push, remote mutation, or later pipeline step was performed.

Recovery accounting: Step 3 functional 0/2, diagnostics 0/2; Step 4 not started.
Prior Step 1 functional 2/2 used and resolved, Step 2 functional 0/2, diagnostics
1/2 per prior step, and the one authorized Phase 1 review-repair pass all remain
unchanged. No new failure or recovery attempt is claimed.

## Phase 2 Implementation 2026-09-11T19:12:00Z

The parent returned the requested version red baseline: exact locked Python 3.12
command exited 2, 0 passed, 0 failed, 1 collection error at test_versions.py:14,
`ModuleNotFoundError: cg_release.versions`. This is confirmed expected red, not
a functional recovery attempt. The continuation authorizes ordinary Python
tests in this implementation child. Pester and routed review remain dedicated
parent-dispatched stages. The writer has now paused for that sequential handoff.

### Implemented Scope

- Step 3: strict library SemVer, numeric RC sequence selection, explicit initial
  version and promotion, line bounds/membership, build-metadata-insensitive
  collisions, audited legacy baseline records, semantic trusted-policy checks,
  current actor role checks, and production-branch override routing.
- GET-only GitHub reader: explicit host/slug, HTTP status classification without
  raw-body diagnostics, three bounded read attempts, shared deadlines, REST
  Release pagination, and GraphQL GET cursor pagination for tag refs. REST
  matching-refs has no documented page API and is not used as a complete large
  inventory. Exact REST ref/object reads verify adopted Release IDs and peeled
  commits; drafts, missing publications, malformed or unadopted managed history,
  duplicate identities, and mismatched repositories fail explicitly.
- Immutable acquisition reads policy from the protected default commit, not the
  source branch or checkout. It reads declared regular Git blobs and verifies
  their object SHA, size, UTF-8 encoding, modes, tree completeness, and case
  identity. It does not fetch, edit working-tree files, or execute source hooks.
  Detached HEAD requires --branch; fork/missing-branch/unknown authority fails.
- Step 4: pure JSON Pointer, static Python TOML, stable R DESCRIPTION, changelog,
  and schema-v1 manifest edits with input/output SHA-256. Distinct JSON fields
  can share one file; duplicate/overlapping declarations and path aliases fail.
  Python projections use packaging and adopted per-distribution/line history;
  missing history and beta-to-dev downgrade fail. TOML comments and DCF
  continuations survive supported edits. Reapplication is byte-idempotent.
- Preview shows canonical inputs, edit digests/projections, source/policy SHAs,
  history digest, approval route, signing requirements, and proposal digest in
  human or JSON Lines output. Notes use paginated exact-commit inventories.
  Start computes its own fresh preview, handles --yes/decline/noninteractive
  confirmation, excludes human wait from its deadline, and recomputes inputs
  after acceptance. Changed inputs cannot silently select a new version.
- Submission remains disabled with E_SUBMISSION_UNAVAILABLE. Status/resume remain
  disabled for Phase 3. No durable locator, receipt, reservation, dispatch, PR,
  metadata write, or publication is claimed or performed.

The approved module-splitting rule was used for independently reusable read
responsibilities: history.py, source_blobs.py, source.py, notes.py, and preview.py.
They keep provider acquisition, immutable blob validation, identity inventory,
note inventory, and proposal calculation separate and keep production modules
within the project line limit. No extra dependency, transport, plugin framework,
or target-project GPID dependency was added.

### Phase Boundaries And Prerequisites

The pure version resolver checks a supplied global occupied-identity set. Remote
preview verifies that the state branch is absent only when policy.enabled is
false. An existing journal returns E_STATE_UNAVAILABLE because Phase 3 owns its
schema/reader; an enabled policy without that journal returns E_STATE_REQUIRED.
Neither case is treated as an empty reservation set. This is an explicit
fail-closed later-phase integration prerequisite, not a tested reservation
journal implementation or a remote authorization request.

Preview manifest edits carry `request_id: preview-not-submitted`. They are
preview data, not an admitted request's applicable edit set. Phase 3 must bind a
real request identity and Phase 4 must recompute/validate the request-bound
manifest before application; no preview output is submitted by this phase.
Signing fingerprints and required approval environment are preview requirements,
not evidence of key availability, protected approval, or App/ruleset enforcement.
Those live/privileged checks remain in their planned later phases.

### Executed Local Evidence

| Check | Executed result |
|---|---|
| Parent version red test | Exit 2; 1 missing-module collection error, confirmed above |
| test_policy.py + test_github_reads.py red | Exit 2; missing policy/github modules, 2 collection errors |
| First version green attempt | 23 passed, 1 failed: manual 1.4.1 below stable 1.4.2 was accepted |
| Step 3 after baseline correction | 41 passed |
| test_metadata.py + test_preview.py red | Exit 2; 2 missing metadata-module collection errors |
| Initial metadata/preview green | 27 passed |
| test_cli.py red | 4 expected failures: acquisition integration absent / CLI still disabled |
| test_source.py red | 1 missing source-module collection error |
| First full package regression | 185 passed, including installed wheel |
| Added real REST/history and multi-field cases | 25 passed, 3 failed: REST URL field compared as identity; same-file distinct JSON fields rejected |
| Full package after those corrections | 198 passed |
| test_notes.py red | 1 missing notes-module collection error |
| Full package with commit-inventory notes | 200 passed |
| Final `uv run --project packages/cg-release --python 3.12 --locked pytest packages/cg-release/tests -q --tb=short` | 204 passed in 7.35 seconds, including real build/install and CLI subprocess cases |
| `python -m pytest scripts/tests/test_cg_pr_preflight.py -q --tb=short` | 52 passed in 0.39 seconds |
| `uv run --project packages/cg-release --python 3.12 --locked ruff check packages/cg-release scripts/benchmark_release.py --output-format concise` | Passed |
| `git diff --check` | Passed; this command covers tracked changes, not untracked package content |
| IDE diagnostics | get_errors is unavailable; Ruff is executed evidence, not an IDE-diagnostic claim |
| Pester / embedded review:auto | Not run in this implementation child; dedicated stages pending |

The installed-wheel suite builds wheel and sdist in a temporary generic directory,
installs locked dependencies, and exercises all four help commands. Its start
smoke now expects a local E_PROCESS from missing Git origin in that generic
non-checkout, not the removed Phase 1 contract-only response. The Phase 1
all-disabled CLI test now applies only to status/resume. These two test changes
implement the plan's explicit Phase 2 interface change, not weakened assertions.
No real GitHub request or remote matrix run occurred. Python remains explicitly
3.12 locally; other OS/interpreter evidence is not inferred.

### Recovery Accounting

- Step 3 functional recovery: 2/2 used and resolved. Attempt 1 fixed the stable
  baseline downgrade; attempt 2 compared exact REST identity fields rather than
  incorrectly requiring absence of the real API's informational object URL.
- Step 4 functional recovery: 1/2 used and resolved for distinct JSON field edits
  sharing one file. Duplicate field and case/overlap rejection remain enforced.
- Missing-module/new-interface red runs are recorded separately, not charged as
  failed post-implementation recovery attempts. No assertion was weakened.
- Local lint correction sequence completed: Ruff formatting/import sorting and
  manual line wrapping. No cg-fix-problems or IDE diagnostic dispatch occurred;
  no new IDE recovery allowance was invented or borrowed for logical failures.
- Prior counts remain unchanged: Step 1 functional 2/2 resolved, Step 2 functional
  0/2, prior diagnostics 1/2 per step, and one authorized Phase 1 review-repair
  pass. No counters reset. Fixable in-scope review findings remain authorized
  when the dedicated review returns; no separate pipeline command is needed.

### Mechanical Review And Evidence Gate

Mechanical self-review found no new debug code, broken imports, TODO markers, or
hardcoded credentials. This does not establish independent logical/security
correctness. Required auto routing resolves to **full**, because these changes
touch release policy, authorization, provider reads, and schemas.

V2 has passing local package checks but remains pending the phase gate and
independent full review. V1 remains passed. V3-V8 are not executed here. C1/C5:
historical tags, assets, payloads, pins, and attestations were not changed. C2-C4:
phase-local policy, read-only, and stale-confirmation tests passed; no later-phase
remote controls are claimed. C6: no Pester was run outside a dedicated child.
Plan stays active with completed-phases [1] and current-phase 2.

### Exact Sequential Parent Handoff

1. Dispatch a dedicated test sibling in this worktree with all writers paused.
   Load cg-skill-pester-safety. Run `. tests\Run-Tests.ps1` with no flags and no
   pipeline. Read tests/last-run.json and return passed, totalCount, passedCount,
   failedCount, skippedCount, failures, filteredFiles, ranAt, and a compact
   cleanup qualification. Require filteredFiles null; do not reuse Phase 1's
   runner result as Phase 2 evidence. Do not repair or run review on failure.
2. Only after the full gate passes, dispatch one dedicated embedded review:auto
   sibling for Phase 2, resolved mode full. This is not a new /cg-review pipeline
   step. Read local cg-review bearings/report/output-quality rules and all ten
   local specs sequentially: cg-code-quality, cg-testing, cg-documentation,
   cg-version-control, cg-reproducibility, cg-performance, cg-architecture,
   cg-data-quality, cg-learnings-researcher, cg-adversarial. Load relevant Python
   and Pester skills. If nested tasks are unavailable, emulate specs sequentially
   inside that dedicated review child; do not claim ten independent sessions.
3. Review Phase 2 additions under packages/cg-release/src and tests, plus the
   Phase 2 edits to cli.py, events.py, models.py, process.py, test_contracts.py,
   and test_install.py. Use the plan's Steps 3-4 and design contracts as authority.
   Inspect existing Phase 1 dependencies where needed for cross-file effects,
   not as a request to redo Phase 1. Exclude .venv, dist, build and caches.
   Explicitly assess the journal prerequisite, preview-only manifest identity,
   signing/approval requirement versus evidence distinction, paginated real
   protocols, metadata projections/aliases, deadline accounting, and no-write
   guarantees. Report actual missing Phase 2 acceptance evidence rather than
   treating this implementation summary as proof of completeness.
4. Preserve P0/P1 strength and global protected artifacts. Never recommend
   deleting/replacing/renaming/moving .cg-docs/brainstorms, solutions, archive,
   compound-gpid.md, compound-gpid.local.md, roadmap.json, SCHEMA_VERSION, or
   .github infrastructure. Content/security findings remain reportable.
5. Review child may write only a new consolidated report at
   `.cg-docs/reviews/2026-09-11-generic-asynchronous-release-controller-phase2-review.md`.
   Keep Phase 1 review artifacts unchanged. Include plan reference, full depth,
   standard type, open finding IDs/statuses, ten-spec coverage, file/line evidence,
   incomplete outputs, and test qualifications. Apply no implementation fixes.
   Return compact P0/P1/P2/P3 counts and critical findings to this implementation
   child for in-scope repair and subsequent verification. No Phase 3, commit,
   push, remote mutation, or later pipeline step is authorized by this handoff.

Advisory stage: implementation. Strong option: an independent reviewer with
reliable tool use and high-effort critical reasoning for release trust boundaries.
An economical option is suitable for bounded mechanical checks only. Suggestions
and availability vary by platform/date; the user chooses model and effort. No
model selection or dispatch override was made.

Current status: **handoff**, not Phase 2 completed. Next required child is the
unfiltered safe Pester test sibling, followed strictly by the full review sibling.

## Phase 2 Review Repair 2026-09-11T19:44:13Z

The parent supplied the unfiltered Pester success at 2026-09-11T19:18:59Z:
total 2906, passed 2904, failed 0, skipped 2, filteredFiles null. This child
checked the corresponding timestamp/count fields in tests/last-run.json.
The known TestDrive cleanup missing-path/nonempty-directory caveat remains;
successful temporary-directory cleanup is not claimed.

Read the completed Phase 2 full review: 10/10 specs, seven findings (P0 1,
P1 4, P2 2, P3 0), no incomplete outputs. The user explicitly authorized all
seven in-scope repairs while retaining the prior functional recovery budgets.
No extra pipeline command or contract exception was introduced.

### Repairs And Tests

All seven findings have local fixes and regressions; detailed mapping is appended
to `.cg-docs/reviews/2026-09-11-generic-asynchronous-release-controller-phase2-review.md`.

- P0.1: replace only the declared JSON string token after full strict validation;
  preserve unrelated numbers and all other input bytes, including underflow,
  overflow, long decimals, signed zero, escaped strings/keys, and nested arrays.
  Invalid JSON produces ControllerError/JSON events, not a raw serializer error.
- P1.1: verify standard role_name against GitHub's legacy permission mapping and
  numeric authenticated actor ID. Maintainers retain override eligibility;
  custom/unknown/missing/contradictory roles are explicit authority failures.
- P1.2: strictly parse existing schema-v1 manifests before replacement, including
  field shapes, duplicate/unknown keys, canonical version/tag, safe unique paths,
  and supported projections. Absence and supported prior/reapplied manifests
  remain permitted. Preview identity never becomes admission evidence.
- P1.3: use exact `graphql` endpoint with separate `--raw-field query=...` and
  explicit GET; retain public/Enterprise host selection and cursor pagination.
- P1.4: share baseline selection between version policy and note acquisition.
  Resolve one eligible line and proposal before selecting its baseline commit.
  Stable patches ignore a future higher-core RC; promotion/continuation use the
  relevant RC record.
- P2.1: record the actual input wait through TimingRecorder and emit a separate
  confirmation event. Injected-clock CLI tests cover acceptance, decline,
  interruption, long human wait, policy timeout, and combined read/recheck budget.
- P2.2: replace full-buffer subprocess.run capture with bounded concurrent pipe
  reads, terminating/reaping on overflow or timeout. Both streams are limited.
  Check advertised tree blob size before retrieval. Small real producers prove
  early stdout/stderr overflow rejection and process cleanup.

The process wrapper tests now spy on its bounded capture boundary and Popen,
not the removed subprocess.run boundary. Argv separation, explicit cwd, no shell,
credential rejection before execution, typed failures, and disabled observation
commands retain assertions. Source fixtures now carry real role_name fields and
declare the feature branch used by their source-policy test; line selection is
performed before notes rather than deferred until proposal composition.

| Executed check | Result |
|---|---|
| New review regressions before repair | 27 failed, 8 passed; expected red baseline |
| First targeted repaired pass | 35 passed |
| First full repaired package pass | 239 passed |
| Final full package, locked Python 3.12 | 243 passed in 8.04 seconds; build/install included |
| Native preflight tests | 52 passed in 0.41 seconds |
| Ruff over package and benchmark | Passed |
| Tracked git diff whitespace | Passed |
| Refreshed Pester | Pending dedicated child; prior result preserved, not reused as fresh evidence |
| Independent finding verification | Pending; no completed verification specs claimed |

Final commands were `uv run --project packages/cg-release --python 3.12 --locked
pytest packages/cg-release/tests -q --tb=short`, `python -m pytest
scripts/tests/test_cg_pr_preflight.py -q --tb=short`, and `uv run --project
packages/cg-release --python 3.12 --locked ruff check packages/cg-release
scripts/benchmark_release.py --output-format concise`.

### Accounting And Constraints

- Authorized Phase 2 review-repair implementation passes: 1.
- Failed post-repair functional runs: 0. New red cases are not charged as green
  recovery failures. Formatting/import correction is not a logical repair retry.
- Prior functional budgets remain Step 1 2/2 resolved, Step 2 0/2, Step 3 2/2
  resolved, Step 4 1/2 resolved. Prior diagnostic counts and Phase 1 review-repair
  history are unchanged. No budget was reset or silently extended.
- Review statuses are locally fixed, not independently verified. The P0 finding
  continues to prevent completion until verification confirms the repair.
- V2 remains pending final verification; V1 remains passed. No Phase 3 or later
  stage, commit, push, PR, remote mutation, or live Enterprise test was executed.
  Plan metadata stays active, completed-phases [1], current-phase 2.
- The reservation-reader prerequisite, preview-only manifest identity, and lack
  of live signing/approval/App enforcement claims are unchanged. No measured
  handoff speed or general process-tree supervision is inferred from these tests.

### Next Sequential Children

1. Dedicated test child, with writers paused: load Pester safety and run
   `. tests\Run-Tests.ps1` with no flags or pipeline. Return passed, counts,
   failedCount, failures, skippedCount, filteredFiles, ranAt, and the cleanup
   qualification. Require filteredFiles null. Do not repair on failure.
2. After that passes, dedicated finding-verification child: read the Phase 2
   review and its Authorized Repair section. Use cg-code-quality and cg-testing
   specs sequentially under the local review verification rules, checking all
   seven IDs with explicit security, data-preservation, actual wire-protocol,
   timing, and resource-limit focus. Always report P0/P1 and cross-file breakage.
   Do not repeat the full ten-spec route without a new need; do not run a separate
   pipeline command, apply fixes, or modify phase completion metadata.
3. The verification child may write only
   `.cg-docs/reviews/2026-09-11-generic-asynchronous-release-controller-phase2-verify-review.md`,
   with type verification, depth light, and parent-review pointing to the Phase 2
   full review. Preserve all protected artifacts and Phase 1 reports. Return
   verified IDs, remaining/new P0/P1/P2/P3 counts, incomplete scopes, and its path.
4. Return both compact results to this implementation child for the Phase 2
   evidence/completion decision. Do not advance to Phase 3 from this handoff.

Current status: **handoff**, all seven repairs locally passing, refreshed safe
gate and independent verification pending.

## Phase 2 P1.5 Repair 2026-09-11T20:01:42Z

The independent verification completed both specs and confirmed all seven
original findings fixed. Its one new P1.5 finding showed that generated manifests
could pass proposal creation and fail exact reapplication: duplicate output paths
or a 260-character combined tag were accepted by the producer but not the reader.
The user authorized its repair at 2026-09-11T19:58:15Z. The independent report is
preserved unchanged; the parent Phase 2 review tracker records P1.5 locally fixed.

The correction is limited to policy.py, metadata.py, manifest.py, and a new
test_manifest.py. Policy now rejects duplicate/case-aliased artifact paths and
safe_ref enforces the reader's 255-character complete-name limit. Generated
manifest bytes pass the same strict validate_manifest function before any edit
set is returned. Existing manifest validation is not weakened.

| Check | Result |
|---|---|
| New P1.5 regressions before correction | 11 failed, 2 passed; expected red baseline |
| Targeted test_manifest.py after correction | 13 passed |
| Full locked Python 3.12 package tests | 256 passed in 7.77 seconds; build/install included |
| Native preflight regression | 52 passed in 0.40 seconds |
| Ruff over package and benchmark | Passed |
| Tracked git diff whitespace | Passed |

Commands: `uv run --project packages/cg-release --python 3.12 --locked pytest
packages/cg-release/tests/test_manifest.py -q --tb=short`; the same pytest command
with `packages/cg-release/tests` for full regression; `python -m pytest
scripts/tests/test_cg_pr_preflight.py -q --tb=short`; `uv run --project
packages/cg-release --python 3.12 --locked ruff check packages/cg-release
scripts/benchmark_release.py --output-format concise`; `git diff --check`.

Accepted boundary evidence covers 254/255-character tags and two distinct output
paths: validate the returned manifest, replace all source blobs with returned
edit bytes, repeat the exact public proposal call, and compare every output byte.
Rejected cases include exact/case-aliased duplicate paths, 256/260-character tags,
and direct producer input with bad source SHA, empty line/request identity, or
unsafe output paths. No returned manifest bypasses its reader validation.

Accounting: one additional authorized review-repair pass, Phase 2 cumulative 2;
failed post-repair functional runs remain 0. Expected red failures do not consume
green recovery attempts. Prior functional counts stay Step 1 2/2 resolved,
Step 2 0/2, Step 3 2/2 resolved, Step 4 1/2 resolved. Prior diagnostics and Phase 1
repair history are unchanged. No new budget or accepted exception was invented.

Checked the supplied latest Pester fields: ranAt 2026-09-11T19:51:46Z, total 2906,
passed 2904, failed 0, skipped 2, filteredFiles null. Preserve the known TestDrive
cleanup caveat. This predates P1.5's repair; no fresh Pester command ran here.

### Final Verification Handoff

1. With writers paused, a dedicated test child loads Pester safety and runs
   `. tests\Run-Tests.ps1` without flags or pipeline. Return passed, counts,
   failures, skippedCount, filteredFiles, ranAt, and cleanup qualification.
   Require filteredFiles null and stop for failures; do not implement fixes.
2. After the gate passes, a dedicated verifier uses cg-code-quality and cg-testing
   sequentially to verify P1.5 and cross-file regressions. Read the first Phase 2
   verification report for the independent finding and this repair evidence.
   Keep all seven prior confirmations; always report P0/P1 and cross-file breakage.
   Do not repeat the full review, run a later pipeline command, or apply fixes.
3. Write only a new report at
   `.cg-docs/reviews/2026-09-11-generic-asynchronous-release-controller-phase2-verify-review-2.md`,
   type verification, depth light, with parent-review pointing to the Phase 2
   standard review (which now tracks P1.5). Reference the prior verification in
   the body; preserve it and Phase 1 artifacts unchanged. Return verified IDs,
   remaining/new priority counts, incomplete scopes, and the report path.
4. Return compact evidence to this implementation child for the Phase 2 completion
   decision only. No Phase 3 or later execution is authorized by this handoff.

Current status: **handoff**, seven original findings independently verified and
P1.5 locally fixed. V2 remains pending final verification; completed-phases stays
[1], current-phase 2, status active. No commits, pushes, or remote mutations ran.

## Phase 2 Final Evidence Gate 2026-09-11T20:11:54Z

Read the final independent verification report and checked the supplied current
Pester timestamp/counts in tests/last-run.json. Canonical plan validation passed
again before completion writes. Phase 2's only required Verification Surface row
is V2; its executed Steps 3-4 checks and both acceptance criteria are satisfied.
No missing required Phase 2 row or accepted exception remains. Remote CI is not
part of V2 acceptance and was not executed; its required later rows remain open.

| Required evidence | Executed result and source |
|---|---|
| V2 / Step 3 deterministic SemVer, line, branch, authority, and provider reads | Full package: 256 passed, final independent run, 8.43 seconds. Includes maintained-library version corpus, explicit baseline/legacy handling, real role envelopes, stale identity checks, typed unknown authority/history, and pagination/protocol regressions. |
| V2 / Step 4 pure metadata/projections, read-only preview, confirmation | Same full run includes every declared parser, JSON preservation, dual Python ordering, strict existing/generated manifests, byte-idempotent reapplication, no-write/dirty-source tests, CLI events, explicit disabled submission, and shared-deadline/confirmation tests. |
| Package/build isolation and preflight regression | Installed wheel/sdist and generic-directory tests included in 256; native preflight 52 passed in 0.44 seconds, final independent verifier. |
| Unfiltered safe full-suite gate / C6 | Dedicated child runner: 2904 passed, 0 failed, 2 skipped, total 2906; failures []; filteredFiles null; ranAt 2026-09-11T20:07:43Z. Preserve known TestDrive cleanup caveat; no successful cleanup claim. |
| Embedded review:auto full and repair verification | Initial full review 10/10 specs. Two dedicated light verification passes, 2/2 specs each. All eight IDs independently confirmed fixed; remaining/new P0/P1/P2/P3 all zero; incomplete scopes zero. |
| Diagnostics and source integrity | Final verifier Ruff and tracked whitespace checks passed. This parent also ran canonical plan validation successfully. No IDE-diagnostics or untracked-git-diff coverage claim. |

Phase-local constraints: C1/C5 published identities, assets, old payloads, pins,
and attestations were not changed; offline legacy/ref identity tests passed.
C2 trusted-source and C3 role/override routing checks passed offline, without
claiming live secret isolation, protected approval, App rulesets, or signing
capability. C4 stale-confirmation tests passed. C6 uses the dedicated safe runner.
Live probes, bridge delivery, remote CI/matrix results, and committed exact-input
publication evidence remain explicit requirements of later phases, not inferred
from these local checks.

Final artifact:
`.cg-docs/work-reports/release-controller/2026-09-11-phase2-final-evidence.json`.
Final independent review:
`.cg-docs/reviews/2026-09-11-generic-asynchronous-release-controller-phase2-verify-review-2.md`.

Accounting is unchanged: Step 3 functional 2/2 resolved, Step 4 functional 1/2
resolved; Phase 2 authorized review-repair passes 2, failed post-repair functional
runs 0. All prior Phase 1 functional/diagnostic and review history is preserved.
There is no in-phase failing-steps entry. No commit, push, roadmap mutation, or
later pipeline step is requested or performed.

Evidence and report are persisted before checkpoint advancement. The next write
appends 2 to completed-phases; re-read must confirm it before current-phase moves
to 3. That next-phase pointer is informational, not Phase 3 execution authority.

### Phase 2 Completion Checkpoint

Successfully wrote completed-phases: [1, 2] first and re-read it while
current-phase still equaled 2. Only then set current-phase: 3 and updated the
active-state handoff. Plan status remains active, paused between phases.
V1 and V2 are passed; V3-V8 remain unexecuted here. Phase 2 is complete.

Result: **Success**. No further child is required for Phase 2. The exact next
command is `/cg-work phase3 review:auto .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`,
recorded for a separately authorized future invocation only. This session stops
at the Phase 2 boundary. Remote CI, Phase 3, commits, pushes, and remote mutations
were not executed. All recovery counters and unrelated changes are preserved.

## Phase 3 Start 2026-09-11

Invocation: `/cg-work phase3 review:auto .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`.
Scope is Steps 5-6 only. Plan validation passed; V1/V2 and completed-phases [1, 2]
were checked against the prior completion evidence. The stored deviation policy
remains ask. Ordinary in-scope review repairs are authorized; no prior counter
is reset. Step 5/6 functional recovery starts at 0/2 each.

Read the local command, project instructions, charter/config, complete plan,
execution/active-state/context/artifact contracts, Python skill/instructions,
and prior execution evidence. The bounded Brain query selected journal input
validation guidance at `.cg-docs/solutions/testing-patterns/2026-08-17-journal-security-hardening-patterns.md`;
validate all untrusted locator/journal fields before use. It reported 596 index
warnings. open-brain is unavailable; no remote evidence is inferred.

Test index contains the completed Phase 1/2 package suites; Step 5/6 modules do
not yet exist. New Step 5 tests precede implementation. This child may run
ordinary offline Python tests. Pester and independent routed review require
dedicated parent-dispatched siblings, with writers paused. No remote operation,
later phase, commit, push, or roadmap change is authorized or performed here.

## Phase 3 Intermediate Checkpoint 2026-09-11T20:36:52Z

Status: **handoff**, not phase completion. Step 5 is partially implemented;
Step 6 has not started. The CLI remains at its Phase 2 disabled-submission and
disabled-observation boundary. No later-phase or remote capability is enabled.

### Implemented And Tested So Far

- `admission.py`: bounded canonical base64url locators, strict inbox envelopes,
  pre-write intent, one create attempt, complete-inventory reconciliation,
  exact full-request read-back, duplicate/conflicting nonce detection, and
  rejection of edited/unauthenticated/wrong-repository receipts. Unknown outcomes
  retain the emitted locator; discovering an unresolved locator does not write.
- `inbox.py`: one-shot gh issue POST with public request JSON through bounded
  stdin, explicit host, repository numeric-identity check, enabled-Issues check,
  GraphQL GET pagination across open/closed issues, author identity and edit-history
  fields, and numeric-ID-verified renamed repository routing. Tests use actual gh
  HTTP envelopes and GraphQL field shapes. No GitHub call was executed.
- `journal.py` / `journal_rules.py`: canonical event hash chain, parent/revision
  checks, immutable request identity, normalized reservations, bounded CAS retries,
  uncertain-result reconciliation, intent/result matching, and conservative audited
  abandon primitives. These are low-level primitives; their caller must still
  verify authority, protections, fresh proposal, and remote effects. They are not
  an implemented trusted admission controller.
- `git_journal.py`: explicitly offline local bare-Git backend, with an explicit
  bootstrap anchor and atomic event/request/reservation tree validation. Real
  sibling expected-old-ref updates preserve the winner and retry on its parent.
  A local author string is not App identity or proof of remote writer protection.
  This backend cannot target a normal checkout and does not fetch or push.
- `process.py`: optional bounded public stdin with concurrent input/output,
  timeout handling, credential-shaped-input rejection, and no body in argv.
  The default no-input call shape remains compatible with existing callers.
- `events.py`: human output now displays the portable request ID and safe next
  action, in addition to the existing JSON Lines fields.
- New tests: test_admission.py, test_journal.py, test_concurrency.py,
  test_inbox_transport.py, test_process_input.py; journal_store.py is a test-only
  fault store, not production persistence or authority evidence.

### Executed Evidence

| Check | Result |
|---|---|
| Admission/journal red baseline | Exit 2, two missing-module collection errors before implementation |
| Real Git transport red baseline | Exit 2, missing cg_release.git_journal before implementation |
| Inbox wire red baseline | Exit 2, missing cg_release.inbox before implementation |
| Initial core green | 37 passed, including real bare-Git sibling updates |
| Inbox plus core green | 43 passed |
| First full package regression | 299 passed |
| Full-request read-back negative regression | 1 expected failure, 19 passed, then repaired |
| Human pre-write locator negative regression | 1 expected failure, 20 passed, then implemented |
| Final locked Python 3.12 package regression | 301 passed in 18.85 seconds; build/install smoke included |
| Native preflight regression | 52 passed in 0.55 seconds |
| Ruff package and benchmark | Passed |
| Tracked git diff --check | Passed; not untracked-content diff coverage |
| Pester | 0 runs in this child; dedicated intermediate regression handoff below |
| Embedded review:auto | 0/10 specs; full route required after Steps 5-6 implementation |

Final commands: `uv run --project packages/cg-release --python 3.12 --locked pytest
packages/cg-release/tests -q --tb=short`; `python -m pytest
scripts/tests/test_cg_pr_preflight.py -q --tb=short`; `uv run --project
packages/cg-release --python 3.12 --locked ruff check packages/cg-release
scripts/benchmark_release.py --output-format concise`; `git diff --check`.

Real Git object creation and commits occurred only in pytest's isolated temporary
bare repositories. No commit was made in this worktree, and no remote write,
live App/environment/ruleset test, measured submission result, or queue runtime
evidence is claimed. get_errors is unavailable; Ruff is not IDE evidence.

### Recovery And Qualifications

- Preserve all prior counters: Step 1 functional 2/2 resolved; Step 2 0/2;
  Step 3 2/2 resolved; Step 4 1/2 resolved. Prior diagnostics and Phase 1/2
  authorized review-repair histories remain unchanged.
- Step 5 used two test-harness correction passes after its first implementation:
  renamed pytest's reserved request fixture; corrected the duplicate-issue fixture
  URL to match its changed issue number. Conservatively record Step 5 functional
  recovery 2/2 used and resolved. These do not prove product defects in the
  authority or transport implementation, and do not prohibit new behavior tests
  or authorized review repairs. Step 6 remains unstarted, functional 0/2.
- The stdin red run was partially invalid: oversized automatic parameter IDs
  exceeded Windows' environment limit. Two cases failed for the missing input_text
  interface, but the oversized case had fixture/setup errors. Added bounded IDs;
  no clean oversized-case red baseline was rerun before implementation. Flag this
  red-phase qualification for cg-testing; the final oversized-input test passes.
  Raw output: `C:\Users\wb384996\.local\share\kilo\tool-output\tool_09225db350012NzH6RmXuRis31`.
- Two added negative checks exposed the missing exact-request comparison and
  human locator display. Each had one expected red failure followed by a passing
  full package run. These are recorded separately from repeated failed green-run
  recovery; neither resets a prior counter or starts a separate fix-triage command.
- One formatting/import cleanup sequence resolved Ruff diagnostics. A timestamp
  command used an unsupported PowerShell 7 flag; it was replaced with the
  PowerShell 5.1-compatible `[DateTime]::UtcNow.ToString(...)`. Neither is a
  functional recovery attempt or remote evidence.
- Mechanical checks found no newly added debug code, secret values, or TODO
  markers. Independent logical/security review has not occurred. No P0/P1/P2/P3
  review count is inferred from passing tests.

### Required Remaining Implementation

Step 5 still needs the GitHub protected state-branch reader/writer and verified
App-only write authority, trusted-policy/environment/ref-protection capability
checks, authenticated fresh-actor/original-requester checks, confirmed-input
revalidation at sealing, external tag collision rechecks, and disabled reviewed
bootstrap workflow/policy examples. Connect reservations to source.py only after
the remote journal reader is verified. Keep local fixture author metadata distinct
from trusted GitHub writer evidence. Add negative authority/protection/rewrite
tests before implementing these paths.

Step 6 still needs start wiring, trusted issue/manual/scheduled wakeups, durable
bounded queue cursor/checkpoints, status/watch, second-machine sealed-locator
resolution, authorized reconciliation-only resume dispatch, and the trusted
audited-abandon workflow input. Preserve the confirmed proposal digest when binding
the real locator; Phase 4 owns request-bound metadata application. Final error
events must retain the locator and must not claim no submission after a write.
Required lifecycle/status/queue/fault tests, workflow tests, fresh final safe gate,
and full embedded review:auto all remain. No acceptance exception was approved.

V3 is **partial**, not passed. V1/V2 remain passed. V4-V8 are outside this run.
Plan stays active, completed-phases [1, 2], current-phase 3. C6 remains enforced.

### Exact Next Child

The writer is paused for a parent-dispatched dedicated test sibling in this same
worktree. Load cg-skill-pester-safety, then run `. tests\Run-Tests.ps1` with no
flags and no pipeline. Read `tests/last-run.json`; return only passed, totalCount,
passedCount, failedCount, skippedCount if available, failures, filteredFiles,
ranAt, and a compact cleanup qualification. Require filteredFiles null. Do not
apply fixes, review, mark a phase complete, or mutate remotes. Stop on failures.

This is an intermediate regression checkpoint for the changed shared process and
event boundaries, not the final Phase 3 gate. Return the result to the Phase 3
implementation child, then continue the exact same invocation with the remaining
Step 5 and Step 6 scopes above. No new permission is needed for ordinary in-scope
implementation or review fixes. After all implementation and required tests are
complete, dispatch the embedded full ten-spec review once in a dedicated sibling;
do not dispatch it now as if V3 were complete. No Phase 4 or later command follows
from this handoff.

## Phase 3 Implementation And Final Gate Handoff 2026-09-11T22:03:30Z

This checkpoint supersedes the intermediate Step 5 implementation handoff, not
its historical evidence. The parent returned the dedicated intermediate Pester
result: passed 2904, failed 0, skipped 2, total 2906, filteredFiles null,
ranAt 2026-09-11T20:44:18Z, gitSha b94f585. The local `tests/last-run.json` was
checked and matched the returned counts, filter, SHA, and timestamp. Retain the
known TestDrive cleanup-error qualification and two update-test skips. No Pester
command was run directly in this implementation child.

After the connection reset, git status was checked again before any edit. No
write was replayed. Prior edits, counters, and completed-phases [1, 2] remain
intact. The following work completes the **implementation scope of Steps 5-6**;
it does not complete the phase gate or embedded review.

### Step 5 Completion Scope

- Added verified current numeric-user permission lookup and fail-closed control
  checks in `authority.py`: repository identity, protected reviewed default
  branch, installed active controller workflow, App slug/ID/bot mapping, complete
  secret-name inventories, no repository/organization fallback for the declared
  credential slots, exact default-ref environment restrictions, independent
  reviewers, no self-review, and no approval bypass.
- Ref rules separate permissions instead of giving an App blanket history
  bypass: control-App-only state updates; state force-update/deletion denied to
  all; publishing-App-only release-tag creation; tag update/deletion/non-fast-
  forward denied to all. The controller token does not receive tag-creation
  authority. The source/default review branch has no bypass allowances.
- Added `github_journal.py`: exact reviewed orphan/empty root pin, signed control
  identity checks, bounded complete linear history, canonical event hashes,
  immutable blob identity validation, atomic derived request/reservation/queue
  trees, and GraphQL createCommitOnBranch with expectedHeadOid. Writes are
  single-attempt and require read-back; uncertain acceptance is reconciled before
  a possible CAS retry. There is no force-update or root-recreation path.
- Journal records now retain the immutable inbox mapping, original full request,
  zoned event/receipt timestamps, last verified checkpoint, typed failure code,
  failed step, retryability, pending intent, and monotone publication flags.
  A failure does not erase published history or release a reservation.
- Schema-v1 policy now requires `journal_root` and `apps.control_slug`; requests
  retain requested_bump and requested_channel so the server can reproduce the
  exact confirmed digest, including base-bump baseline selection. Fixtures and
  examples were updated. These are unshipped Phase 1-3 schemas; no deployed
  controller data was migrated, and no compatibility bypass was added.
- The verified journal reader now supplies preview/global reservations in
  source.py. Absence under enabled policy and unverifiable existing state fail
  closed. Controller revalidation uses immutable remote blobs with the original
  requester identity; it never reads or executes the target worktree. Revalidation
  runs again on an admission CAS retry, including current tag/history collisions.
- Final verification identified repeated immutable-object fetching during journal
  rechecks. Added command-local `read_session.py` caching bounded to 32 MiB and
  1024 entries per reader, with at most four repository identities per command.
  Only exact immutable Git-object endpoints are cached. Refs, actor permissions,
  protections, workflow state, and issue inventory remain fresh. Cache hits still
  enforce the current deadline and return independent decoded values. A 101-request
  offline protocol test proves ten further journal reads use ten fresh head reads,
  not another full set of immutable-object HTTP reads. Its clock/network costs
  are synthetic and do not establish the live handoff target.
- Shared remote context and strict JSON decoding were separated into context.py
  and jsonio.py to retain the module-size limit. Source acquisition now records
  verified canonical repository spelling, so client confirmation and controller
  replay do not disagree solely because an origin uses different letter case.
  Repository ID remains the authority boundary. Overflowed numeric JSON values
  are rejected as typed response errors before cache serialization.
- Added disabled `templates/controller.yml`, `policy.example.json`, and
  `bootstrap.example.json`. Bootstrap remains explicit and reviewed, with pins
  and settings placeholders, not implicit creation or remote setup. The workflow
  installs a digest-checked controller wheel with locked dependencies before
  minting the repository-scoped control App token in its protected environment.
  Checkout credentials are not persisted; the App token action revokes its token
  by default. No target source code runs with these credentials.

### Step 6 Completion Scope

- Enabled start through the Phase 3 provider only after confirmation and fresh
  checks. Policy-disabled behavior remains explicit. The provisional locator is
  flushed before the one issue write; only verified exact read-back emits a queued
  receipt. Unknown outcome, timeout, and Ctrl+C after intent retain the locator
  and do not claim that submission did not occur.
- Added `controller.py` for issue, manual, and scheduled default-ref wakeups. It
  verifies the actual run/actor/attempt/default SHA/workflow path and reviewed
  controller/wheel pins before allowing journal writes. It seals admission and
  stops at the Phase 3 checkpoint; it does not prepare metadata, build, approve,
  or publish. A repeated wakeup returns the verified checkpoint without replay.
- Added durable cursor events and a snapshot ceiling in `queue.py`. Each run
  processes bounded work, persists the cursor after processing, and eventually
  revisits old failures even during continuous arrivals. Lost wakeups or a crash
  before cursor commit leave work replayable. Unfinished sealed requests remain
  in the inventory after issue deletion; edited current bodies cannot replace
  their journal mapping. Admission rejection codes remain in immutable scan events.
- Added read-only status and bounded watch in `runtime.py` / `lifecycle.py`.
  Locators work without Git discovery, a cached issue number, or local request
  files. Sealed state is authoritative. Status distinguishes publication from
  completion and reports pending intents, failures, retryability, receipts, and
  separate stage timing fields. Missing measurements remain null, not zero.
  Watch timeout/Ctrl+C stops observation only.
- Resume resolves first, rechecks current requester/resumer authority and policy,
  and makes one default-ref reconciliation dispatch. It neither creates an issue
  nor unconditionally replays a write. Override recovery requires current
  maintainer authority; unknown dispatch outcomes remain explicit.
- Added audited maintainer-workflow abandon in `abandon.py`, not a destructive
  public CLI. Tags, Releases/drafts, preparation branches, other active workflows,
  pending intents, or publication history prevent retirement. Verified absence
  permits an append-only abandoned record and reservation removal, with actor,
  role, and reason retained. No remote artifact is deleted.

### Final Local Evidence

| Check | Result |
|---|---|
| Full locked Python 3.12 package suite | **362 passed**, 0 failed, 29.03 seconds |
| Build/install smoke | Included in the passing full package suite |
| Native preflight regression | **52 passed**, 0 failed, 0.47 seconds |
| Ruff package and benchmark | Passed |
| Tracked git diff --check | Passed; not untracked-content diff coverage |
| Real isolated bare-Git journal tests | **5 passed**, including sibling CAS and request/queue coexistence |
| Intermediate dedicated Pester | 2904 passed, 0 failed, 2 skipped; known cleanup qualification; not the fresh final gate |
| Fresh final Pester | Pending dedicated child after this implementation |
| Embedded review:auto | Resolved full; **0/10 specs executed**; finding counts not assessed |

Executed final commands:

```text
uv run --project packages/cg-release --python 3.12 --locked pytest packages/cg-release/tests -q --tb=short
python -m pytest scripts/tests/test_cg_pr_preflight.py -q --tb=short
uv run --project packages/cg-release --python 3.12 --locked ruff check packages/cg-release scripts/benchmark_release.py --output-format concise
git diff --check
```

Additional coverage is in test_authority.py, test_remote_journal.py,
test_remote_faults.py, test_queue.py, test_status.py, test_lifecycle.py,
test_runtime.py, test_controller.py, test_controller_templates.py,
test_progress.py, test_abandon.py, and test_read_session.py, plus the extended
earlier tests.
Cases include lost remote acceptance responses, signed-history/tree corruption,
revoked authority, missing/weak controls, cross-App tag bypass, secret fallback,
unresolved locators, continuous arrivals, issue deletion, worker interruption,
failed checkpoints, watch stop, authorized/unauthorized resume, and unsafe abandon.

The signed GitHub protocol tests use explicit offline fixtures. They are not
evidence that any App, ruleset, signature support, environment, or workflow is
installed in a real repository. The only network reads in this continuation were
public dependency metadata/source: the create-github-app-token v2 ref resolved to
fee1f7d63c2ff003460e3d139729b119787bc349, and that commit's action.yml confirmed the
permission input names and default token revocation. These are dependency-pin
evidence, not sandbox or release evidence. No remote mutation was executed.

### Recovery Accounting And Qualifications

- Preserve inherited functional counters exactly: Step 1 2/2 resolved; Step 2
  0/2; Step 3 2/2 resolved; Step 4 1/2 resolved; Step 5 2/2 resolved. Step 6 has
  no failed post-implementation functional repair loop; its counter remains 0/2.
- Missing-module/file red baselines were executed before the new authority,
  remote journal, queue/lifecycle/status, runtime/controller, timing, and template
  implementations. Added negative tests deliberately exposed fairness under
  continuous arrivals, deleted-issue inventory, unrestricted secret fallback,
  tag-creation bypass, missing failure fields, receipt timestamp validation, and
  interruption after intent. Each was implemented/repaired and included in the
  passing final suite. These are new-behavior red cases, not resets of old counters.
- The first broad package run had one stale test fixture missing the newly required
  apps.control_slug field. Updated that valid-schema fixture so its existing
  same-App semantic rejection assertion still tests the intended defect. No
  assertion was weakened. This is recorded separately from functional recovery.
- Mechanical diagnostics cleanup used two passes: import/UTC alias normalization,
  then unused-import/line-width cleanup. Current Ruff is clean. Prior diagnostic
  histories are not reset. Native get_errors remains unavailable.
- The final cache follow-up added its own missing-module red baseline and then
  passing cache bounds/deadline/fresh-authority tests. Canonical repository spelling
  and overflowed JSON numbers each had an expected red regression before repair.
  The new files received import and line-width cleanup. The final complete suite
  was rerun after these changes; the earlier 355-test pass is not the final count.
- Patch-context mismatches were atomic failures; corrected patches matched the
  inspected current files. No successful write was blindly replayed. The missing
  rg executable only affected a line-count inspection; specialized Read was used
  instead. Largest changed production modules were checked below 300 lines.
- Formal embedded review repairs have not started. No P0/P1/P2/P3 count is inferred
  from local testing. Review findings may still require ordinary authorized fixes.

### Exact Final Gate And Review Handoff

All implementation writers are paused. First dispatch **one dedicated test
sibling** in this worktree. Load cg-skill-pester-safety and run
`. tests\Run-Tests.ps1` with no flags or pipeline. Read tests/last-run.json; return
passed, totalCount, passedCount, failedCount, skippedCount if present, failures,
filteredFiles, ranAt, gitSha, and the compact cleanup qualification. Require
filteredFiles null. Do not fix, review, commit, push, mutate remotes, or mark a
phase complete in that child. Stop on failures and return them to the Phase 3
implementation child.

After the final safe gate passes, dispatch the **embedded full review sibling**
for the current Phase 3 Steps 5-6 implementation. Use the local review-routing
contract and all ten specs exactly once: cg-code-quality, cg-testing,
cg-documentation, cg-version-control, cg-reproducibility, cg-performance,
cg-architecture, cg-data-quality, cg-learnings-researcher, and cg-adversarial.
Review the complete Phase 3 surface, including changed Phase 1/2 interfaces, but
do not mistake prior verified Phase 1/2 findings for current unresolved findings.
The package is still untracked: inspect the explicit source/tests/templates and
schema/config files, not only `git diff`. Exclude .venv and test/build caches.
Record findings and coverage at
`.cg-docs/reviews/2026-09-11-generic-asynchronous-release-controller-phase3-review.md`.
Return compact priority counts, artifact path, and critical evidence. Do not run
later workflow commands or modify implementation files during this read-only
review. Return actual findings to the Phase 3 implementation child for already
authorized in-scope repair and verification.

V3 implementation tests now pass; phase completion remains pending the fresh
safe gate and full review. V1/V2 stay passed. V4-V8 are not claimed. Keep the plan
active with completed-phases [1, 2] and current-phase 3. No Phase 4, commit, push,
PR, settings change, or publication follows from this handoff. The roadmap is
unchanged.

## Phase 3 Review Repair Batch 1 2026-09-11T22:54:27Z

The parent returned the full safe gate at 2026-09-11T22:09:18Z: passed 2904,
failed 0, skipped 2, total 2906, filteredFiles null, gitSha b94f585. These fields
were checked in tests/last-run.json. Preserve the known TestDrive missing-path/
nonempty-directory cleanup errors and the two update-test skips. This gate is
valid pre-repair evidence, not the new gate for the repaired code.

Read the complete Phase 3 full review at
`.cg-docs/reviews/2026-09-11-generic-asynchronous-release-controller-phase3-review.md`.
Coverage was 10/10 specs, emulated sequentially in one review session. The six
original findings were P0: 0, P1: 3, P2: 3, P3: 0. All six have local repairs in
this batch. Their review frontmatter remains open until independent verification;
passing implementation tests do not independently close a finding.

The transport reset did not discard the edits or the completed test results.
Rechecked git status and the persisted authority, deadline, rendering, and
verification changes after the reset. No successful write was replayed.

### Findings And Repairs

| ID | Local repair | Regression evidence |
|---|---|---|
| P1.1 | Shared authorize_resume checks now serve CLI and worker paths. verify_run returns the verified actor and actual event type; manual reconcile carries that actor to the journal boundary. Both initial and final replay checks, including CAS revalidation, enforce current override-resumer authority. Scheduled/issue scans remain automatic wakeups, not maintainer recovery. | Direct controller.main write-only override resumer is rejected before any journal write; revocation during replay is also rejected. Scheduled scans with a write-only triggering actor still admit an authorized original request. |
| P1.2 | Each automatic item uses at most 20 seconds of the real shared API deadline, leaving a 40-second checkpoint reserve. The parent deadline is restored in finally. The batch stops before using the reserve, and records E_ITEM_DEADLINE for an exhausted item before advancing fairly. Unknown write outcomes remain subject to signed journal reconciliation. | Three real-worker attempts revisit a deadline-heavy entry while reaching the healthy later request. Accepted-write timeout and checkpoint-failure recovery do not duplicate admission. |
| P1.3 | Unchanged empty scans no longer write. Removed the 10,000-event lifetime cap from replay and both stores; event paths support revisions beyond the old fixed-width boundary. Added verification_guard for bounded read attempts, constrained by the active command/item deadline. Cycle detection remains explicit. No history is deleted, rewritten, or automatically compacted. | Five empty remote-protocol scans make zero writes. Real replay of 10,000 valid retained events permits admission and a cursor update at events 10,001/10,002. Expired verification leaves those events intact; a fresh read can verify them. Wire-file tests cover revisions 10,001 and 10,000,000,000. |
| P2.1 | Added a transport-only offline server plus complete worker integration tests. No context, permission, proposal replay, admission, journal, or worker decision function is replaced. The worker accepts an injected clock without replacing time globally. | Actual confirmed start, receipt, unsealed controller.main admission, fresh-session status without Git discovery, manual resume, stale policy/source/role, external tag race, direct dispatch, deadline, and checkpoint paths execute together. Real bare-Git tests remain in the full suite. |
| P2.2 | Human events explicitly render version, observed state, current step, and expected state. | Separate queued, failed, published, and complete human-output assertions; locator behavior retained. |
| P2.3 | Missing receipt creation time stays unknown for total queue duration. It is not replaced with the first admission event timestamp. Later stage transitions still have their own timestamps. | Queue duration remains null at an injected 60 seconds after admission when the receipt timestamp is absent. |

The history change removes a consumable lifetime counter, not all physical read
limits. Full history is still replayed and retained. Slow or oversized histories
can fail explicit per-command time/response bounds; constant-time cold reads for
arbitrarily large histories are not claimed. The 10,000-event retention test is
synthetic core verification, not a live GitHub throughput or sandbox result.
The deadline reserve protects the work/checkpoint split; it does not promise a
successful remote write during a provider outage. Such outcomes remain explicit
and are reconciled on a later worker attempt.

### Executed Evidence

| Check | Result |
|---|---|
| Initial direct review regressions | 9 expected failures before repair |
| Full transport-level baseline after fixture setup | 5 passed; actual manual-authority and deadline failures reproduced |
| Focused repaired review/worker suite | 16 passed |
| Additional authority, uncertain-write, checkpoint, retention tests | 11 passed |
| First complete repaired package suite | 382 passed, 31.14 seconds |
| Final complete repaired package suite | **382 passed**, 0 failed, **31.68 seconds**; build/install and real bare-Git tests included |
| Native preflight regression | **52 passed**, 0 failed, **0.43 seconds** |
| Ruff package and benchmark | Passed |
| Tracked git diff --check | Passed; not untracked package-content coverage |
| New Pester execution in this child | None; dedicated post-repair gate pending |
| Independent repair verification | Not run; all six IDs remain open pending that verification |

Final commands:

```text
uv run --offline --project packages/cg-release --python 3.12 --locked pytest packages/cg-release/tests -q --tb=short
python -m pytest scripts/tests/test_cg_pr_preflight.py -q --tb=short
uv run --offline --project packages/cg-release --python 3.12 --locked ruff check packages/cg-release scripts/benchmark_release.py --output-format concise
git diff --check
```

New regression files: test_phase3_review_repairs.py, test_worker_e2e.py,
worker_transport.py, and test_journal_retention.py. Changed implementation:
authority.py, controller.py, runtime.py, queue.py, events.py, progress.py,
journal.py, journal_models.py, git_journal.py, github_journal.py, and the new
verification.py. Existing controller/runtime unit fixtures were adjusted for the
shared authority function and verified run tuple; assertions were not weakened.

### Counters And Scope

- Authorized review-repair batch: **1**. Six local repair claims; zero independent
  repair-verification passes. Do not reinterpret the prior two-attempt functional
  counters as a blanket ban on the explicitly authorized review fixes.
- Preserve prior functional counters unchanged: Step 1 2/2 resolved; Step 2 0/2;
  Step 3 2/2 resolved; Step 4 1/2 resolved; Step 5 2/2 resolved; Step 6 0/2.
- Harness setup initially omitted the paginated rulesets endpoint; fixed that
  transport fixture, then added the worker's clock injection point. Only after
  these setup corrections were the actual P1.1/P1.2 red behaviors recorded.
  Setup failures are not product findings or resets of functional budgets.
- The repair batch passed its first complete functional regression. Mechanical
  import/format cleanup and one remaining long fixture string were corrected;
  final Ruff is clean. Prior diagnostic histories remain intact. get_errors is
  unavailable; no IDE diagnostics evidence is claimed.
- All provider, actor, signature, and timeout evidence in the new integration
  tests is explicitly synthetic. No remote mutation, live settings change,
  worktree commit, push, PR, or publication was executed. Temporary bare-Git
  fixture commits remain isolated tests. No Phase 4 command was run.
- Existing unrelated edits, prior evidence, plan completion fields, and roadmap
  are preserved. V1/V2 remain passed. V3 remains partial until the fresh safe
  gate and independent verification accept the repairs.

### Exact Sequential Handoff

All implementation writers are paused. Dispatch one dedicated **post-repair safe
test child** in this worktree. Load cg-skill-pester-safety and run
`. tests\Run-Tests.ps1` with no flags or pipeline. Read tests/last-run.json and
return passed, totalCount, passedCount, failedCount, skippedCount if present,
failures, filteredFiles, ranAt, gitSha, and a compact cleanup qualification.
Require filteredFiles null. Do not fix code or run review in that child. Return
failures to this implementation session if the gate fails.

After that gate passes, dispatch one **independent Phase 3 repair-verification
child**. Read the original six findings and this repair evidence. Verify P1.1,
P1.2, P1.3, P2.1, P2.2, and P2.3 against the actual current code and tests;
check nearby regressions rather than accepting the local repair claims. Inspect
untracked package source/tests explicitly, not only git diff. Retain the original
10/10 full-review evidence; this is verification of those findings, not a claim
of ten new independent review sessions. Record the result at
`.cg-docs/reviews/2026-09-11-generic-asynchronous-release-controller-phase3-verify-review.md`.
Return confirmed-fixed IDs, unresolved/new findings with priority counts,
critical evidence, and artifact path. Do not implement fixes or mark the phase
complete in that child. Only independently confirmed IDs should be closed.

Return any findings to the authorized Phase 3 implementation session. Keep
completed-phases [1, 2], current-phase 3, and all counters intact. No Phase 4 or
remote mutation follows from this handoff.

## Phase 3 Completion Gate 2026-09-11T23:08:05Z

Received and read the independent phase3-verify-review.md: all six original
findings confirmed fixed, zero remaining, zero new. It executed cg-code-quality
then cg-testing in one verification session. The original full review executed
all ten specs sequentially in its own session. No incomplete review scopes remain.
Closed only the six independently confirmed IDs in the source review frontmatter.

Checked tests/last-run.json against the returned final post-repair safe gate:
2026-09-11T23:01:57Z, gitSha b94f585, passed 2904, failed 0, skipped 2, total 2906,
filteredFiles null. Retain the two update-test skips and TestDrive cleanup caveat;
successful cleanup is not claimed. No Pester command was run in this finalizer.

The independently executed package suite passed 382 tests in 32.32 seconds,
including build/install and real isolated bare-Git tests. Native preflight passed
52 tests in 0.44 seconds. Independent Ruff and tracked whitespace checks passed.
Canonical plan validation was rerun successfully before any completion mutation.
The parent's UNAVAILABLE response to a peer exclusivity request is not an
execution prohibition; no exclusivity or peer permission was assumed.

### Required Evidence

| ID | Phase | Status | Evidence |
|---|---|---|---|
| V1 | 1 | Passed, retained | phase1-final-evidence.json |
| V2 | 2 | Passed, retained | phase2-final-evidence.json |
| V3 | 3 | Passed | Steps 5-6 admission, journal, real Git CAS, queue, status, worker-loss and transport-level recovery tests; final Pester; full review and independent six-finding closure |
| V4-V7 | 4-7 | Not claimed | Outside this finalization scope |
| V8 | final | Not claimed | Whole-plan final gate remains outstanding |

V3 is the only required Verification Surface row assigned to Phase 3. There are
no missing Phase 3 required rows, failing steps, accepted exceptions, or unresolved
review findings. Steps 5 and 6 meet their phase-local acceptance criteria.

### Constraint Check

| ID | Phase 3 result |
|---|---|
| C1 | No publication or remote mutation; non-force identity and journal conflict tests pass. Published tag/asset live checks remain later-phase evidence. |
| C2 | Trust-boundary and credential/protection negative tests pass. Templates remain disabled. Live hostile-source and installation enforcement probes are not claimed. |
| C3 | Current original-requester/manual-resumer authority and protected-environment checks pass offline, including direct dispatch and role revocation. Bound live approval belongs to later phases. |
| C4 | Confirmed source/policy/collision replay regressions pass; no silent confirmed-version change accepted. |
| C5 | Existing unrelated release payload/identity work remains preserved; preflight regressions pass. Future reader/bridge/live compatibility evidence remains Phase 6 scope. |
| C6 | Final unfiltered Pester gate ran through the dedicated safe child; artifact was read and verified. |

Final evidence was saved before plan completion fields at
`.cg-docs/work-reports/release-controller/2026-09-11-phase3-final-evidence.json`.
Crash-safe checkpoint sequence: append 3 to completed-phases, reread/verify that
authoritative field, then set informational current-phase to 4. Keep status active.
Phase 4 is only the next-phase marker; no Phase 4 command or implementation is
authorized by this checkpoint. No commit, push, PR, remote write, or roadmap
change is performed. All existing functional/diagnostic histories and the single
Phase 3 review-repair batch remain unchanged.

Limits remain explicit: verification is local/offline and describes the
uncommitted worktree, not a release candidate commit. Full retained-history
replay remains resource-bounded; constant-time or unlimited-capacity reads are
not claimed. The checkpoint reserve does not guarantee writes during an outage
or when startup reads consume the budget. No live latency, sandbox, approval,
signing, or remote matrix evidence is inferred.

### Checkpoint Recorded

Saved final evidence first, then appended completed-phases [1, 2, 3] and reread
that field while current-phase still equaled 3. Only after verification was
current-phase changed to 4. Status remains active; the whole plan is not complete.
Phase 3 result: **Success**. No Phase 4 execution follows. Final active-state
references point to the passed V3 evidence and independent verification report.

## Phase 4 Start 2026-09-11T23:11:45Z

Scope: Steps 7-8 only, then the full safe phase gate and embedded review:auto.
The user authorized in-scope review repairs and ordinary Python tests. Pester
and review use dedicated parent-dispatched siblings when nested tasks are absent.
No Phase 5, worktree commit, push, remote mutation, shared configuration edit,
or change to another worktree is authorized. No peer exclusivity was agreed.

Read the command first, project instructions, charter/configuration, plan,
execution report, and context/artifact/goal/active-state contracts. Canonical
plan validation passed. Completion metadata is [1, 2, 3], current-phase 4.
Loaded Python and Pester safety skills. The bounded Brain query selected exact
artifact/commit provenance guidance in
`.cg-docs/solutions/git-workflows/2026-08-13-verified-pages-artifact-and-release-tag-gates.md`.
Apply immutable identity binding, not its old main-only policy. Query returned
598 index warnings; open-brain is unavailable. No live evidence is inferred.

Test index: existing metadata/manifest, controller/worker, journal, source,
installed-wheel, and workflow-contract suites. Step 7 preparation and Step 8
build/artifact suites do not yet exist. Tests precede their implementations.
Inherited counters remain Step 1 2/2 resolved, Step 2 0/2, Step 3 2/2 resolved,
Step 4 1/2 resolved, Step 5 2/2 resolved, Step 6 0/2. Step 7 and Step 8 begin
at 0/2. Prior diagnostic and review-repair histories are unchanged.
V4 is pending; V1-V3 remain passed. No accepted exception is recorded.

## Phase 4 Intermediate Checkpoint 2026-09-11T23:25:51Z

This is a partial Step 7 implementation and a dedicated-test handoff. It is not
the final phase gate. Step 8 and embedded review:auto have not started.

### Implemented Scope

- `preparation.py` consumes a complete policy edit allowlist, immutable source
  blobs, and flattened Git entries. It hashes the complete source tree before
  staging, verifies input blob IDs/modes and both edit digests, rejects duplicate,
  missing, extra, overlapping, traversal, and case-aliased paths, and permits only
  an absent release manifest as a new file. Existing modes and unrelated Git
  symlink/submodule entries remain unchanged without materializing those entries.
- It stages only approved metadata bytes in a fresh private temporary worktree.
  No source checkout, attributes, filters, hooks, submodule operation, commit,
  fetch, or push runs. Git routing/config environment variables are removed;
  system/global config and templates are disabled. Exclusive writes and file
  identity checks reject links/aliases in staged output. `hash-object --no-filters`
  verifies bytes; `write-tree --missing-ok` verifies the complete expected tree.
  Missing untouched source blobs are intentional: their verified object IDs enter
  the index, not executable source or working-tree files.
- Staging has explicit limits: 10000 flattened input entries, the process stdin
  limit of 64 KiB for the index inventory, 1 MiB per metadata blob, and 16 MiB
  total staged metadata. Oversized inventories fail explicitly, not partially.
  Git calls use one shared deadline with per-call bounds. The helper accepts a
  caller deadline; production controller integration must pass its current one.
- `process.py` adds an optional complete child environment, preserving default
  behavior for current callers. This supports the isolated Git environment;
  it does not broaden the Git/gh tool allowlist or add a remote operation.
- Journal records can retain bounded append-only stage evidence. A result may
  add only its own operation key, bound to that intent's canonical digest.
  Admission and intent writes cannot inject evidence, earlier evidence cannot
  change, cumulative record-size limits fail before a write, and uncertain
  append responses reconcile through normal journal replay. This is a persistence
  primitive, not authority to trust caller-supplied PR/build evidence.

### Executed Evidence

| Check | Result |
|---|---|
| Preparation red baseline | Exit 2, one collection error: missing cg_release.preparation |
| First preparation run | 10 passed, 3 failed because the fixture's git add inherited CRLF conversion |
| Exact-byte fixture correction | 13 passed; fixture Git calls explicitly disable core.autocrlf |
| Stage-evidence red baseline | 4 expected failures: result interface and evidence rules absent |
| Evidence/journal/remote-journal/real-Git targeted regression | 24 passed |
| Full package before final boundary cases | 403 passed |
| Final full package, locked offline Python 3.12 | **405 passed**, 0 failed, 37.10 seconds; real Git and build/install included |
| Native preflight regression | **52 passed**, 0 failed, 0.44 seconds |
| Full package and benchmark Ruff | Passed |
| Tracked git diff --check | Passed; not untracked-content diff coverage |
| Pester executed in this implementation child | 0; dedicated checkpoint run requested below |
| Embedded review:auto | 0/10; full route resolved from release/schema/filesystem changes |

Final commands:

```text
uv run --offline --project packages/cg-release --python 3.12 --locked pytest packages/cg-release/tests -q --tb=short
python -m pytest scripts/tests/test_cg_pr_preflight.py -q --tb=short
uv run --offline --project packages/cg-release --python 3.12 --locked ruff check packages/cg-release scripts/benchmark_release.py --output-format concise
git diff --check
```

New tests: test_preparation.py (18 cases) and test_stage_evidence.py (5 cases).
All three metadata formats reuse proposed_edits and are checked through the real
local Git staging path. Tests also cover host Git environment redirection,
unmaterialized hostile attributes, shared deadline expiry, exact mode/blob/tree
identity, immutable evidence, and cumulative record capacity. The deadline and
cumulative-size follow-up tests were added after their defensive code; no separate
red baseline is claimed for those two cases. Flag this qualification for cg-testing.

### Counters And Limitations

- Step 7 functional recovery: conservatively **1/2 used and resolved** for the
  test fixture's inherited CRLF conversion. Production correctly rejected the
  resulting mismatch. No assertion or expected product result was weakened.
- Step 8 functional recovery: 0/2, not started. Prior Step 1-6 counters and all
  prior review-repair histories remain unchanged. No review repair was attempted.
- One mechanical formatting/import cleanup sequence resolved Ruff diagnostics.
  get_errors is unavailable; Ruff is executed evidence, not IDE evidence.
- All new checks were local/offline. There was no source-worktree commit, remote
  write, publication, settings change, shared config edit, or other-worktree edit.
  Test-only Git index/object writes occurred inside isolated temporary directories.
- No P0/P1 count can be inferred: independent review has not run. No observed
  functional failure remains in the executed checks. Mechanical self-review found
  no new debug/import/TODO/credential issue; logical/security review is outstanding.
- V4 is **partial**. No phase completion field changed, no exception was accepted,
  and no roadmap write occurred. The old Pester result remains Phase 3 evidence,
  not a new Phase 4 gate. No live execution prerequisite blocks these local steps.

### Remaining Phase 4 Work

Step 7 still requires production acquisition of the exact source inventory,
request-bound manifest/edit recomputation, preparation object/branch/PR writes
with durable intents and uncertain-response reconciliation, source-base and
current-authority checks, exact reviewed head and final merge/squash/rebase tree
verification, immutable PR/review/release-SHA evidence, and controller integration.
The pure staging helper is not currently called by the controller. Preserve the
current fail-closed message until this path is implemented and tested.

Integration must exclude only the verified request's own reservation when
reproducing its confirmed preview. Current acquire_snapshot/read_reservations
includes every reservation; blindly calling the existing pre-admission revalidate
on an already admitted request would collide with its own version. Add a specific
regression before that integration; do not discard other reservations or remote
tag/draft collisions. This is a known integration requirement, not a claimed fix.

Step 8 remains entirely outstanding: sealed build requests and actual run/attempt
registration, trusted default-ref dispatch, separate controller/source identities,
six-cell release-mode CI and aggregate verification, complete reuse keys, isolated
build template, API-verified job/artifact identities, untrusted-byte inventory
verification, expiry/substitution/fault tests, and lifecycle integration. The
existing `verification.py` is the Phase 3 bounded-history helper; preserve it.
The current CI workflow still rejects release-mode dispatch by design.

After both steps and their regressions pass, run a fresh final unfiltered Pester
gate and the full ten-spec embedded review:auto in dedicated sequential siblings.
Repair in-scope findings under the existing authorization, independently verify
repairs, and only then evaluate V4 and the crash-safe phase completion sequence.
Do not start Phase 5 under this request.

### Exact Immediate Parent Handoff

The implementation writer is paused. Dispatch one dedicated test sibling in this
same worktree. Load cg-skill-pester-safety, then run `. tests\Run-Tests.ps1` with
no flags and no pipeline. Read tests/last-run.json and return passed, totalCount,
passedCount, failedCount, skippedCount if present, failures, filteredFiles,
ranAt, gitSha, and a compact cleanup qualification. Require filteredFiles null.
Do not repair, review, mutate remotes, or mark a phase complete in the test child.

This intermediate regression protects the changed shared process and journal
boundaries. Return its result to the Phase 4 implementation continuation. Then
resume exactly `/cg-work phase4 review:auto .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`
with the remaining Step 7 and Step 8 scopes above. Do not treat this checkpoint
as full phase implementation or dispatch the final full review prematurely.
No new user authorization is needed for the already approved in-scope work.

Live Phase 7 prerequisites remain explicit: allowlisted sandbox repository IDs
and approved operations, reviewed pinned controller/workflow setup, protected
App/environment/ruleset separation, and actual registered matrix/run/secret-boundary
records. They are not present or fabricated here, and are not substituted by YAML
inspection or these 405 offline tests.

## Phase 4 Continuation 2026-09-11T23:31:59Z

Read and verified the parent-returned intermediate Pester artifact: ranAt
2026-09-11T23:31:30Z, gitSha b94f585, passed true, total 2906, passed 2904,
failed 0, skipped 2, filteredFiles null. Preserve the known cleanup caveat.
This is the requested intermediate gate, not the final Phase 4 gate. No Pester
command ran directly here. The user authorized all remaining Steps 7-8 and
requested the final gate/review handoff only after implementation is complete.
Counters remain Step 7 functional 1/2 resolved; Step 8 0/2 not started.

## Phase 4 Continuation Checkpoint 2026-09-11T23:59:10Z

The requested full remaining implementation is **not complete**. No final
gate/review handoff is issued at this checkpoint. No new intermediate Pester
run is requested. Continue implementation before the final dedicated stages.

### Additional Implemented Scope

- `source.py` and `replay.py`: a sealed replay verifies the exact active journal
  request and excludes only its own reservation. Remote tag/draft collisions and
  other reservations remain in the proposal inputs. The full worker-transport
  fixture verifies admitted replay and external collision rejection. Replay is
  now a separate reusable module; controller imports it and keeps its prior
  admission behavior. No Phase 4 worker stage is enabled yet.
- `preparation_remote.py`: content-addressed blobs, expected tree and deterministic
  commit, a nonce-specific non-force branch, and one exact all-state preparation
  PR. A lost response always reaches read-back; repeats do not create another PR.
  Changed heads, ambiguous/closed PRs, missing refs and unverifiable object IDs
  stop. Commit bytes use immutable receipt time and were checked with real Git.
  These are control-context primitives, not standalone authorization entry points.
- `github_checks.py`: bounded complete check/run inventories with duplicate and
  shape rejection. Required PR checks bind name, App, check suite, actual workflow
  path/run/attempt, head SHA and successful conclusion. Ordinary PR check evidence
  remains distinct from required registered release-mode evidence.
- `reviewed_commit.py`: exact PR/head/repository/base identity, independent current
  authorized reviewer, latest undismissed head-bound approval, required check
  evidence, exact final tree and permitted parents. Merge and single-commit
  squash/rebase outcomes are supported. Changed bases, trees, heads, stale/self
  approvals, outstanding change requests, revoked reviewer roles and wrong
  producers stop. An unchanged open PR returns waiting without polling.
- `prepare_stage.py`: coordinates replay, request-bound manifest bytes, real local
  staging, durable preparation intent, remote reconciliation, immutable PR identity
  and reviewed release binding through the real journal. Evidence capacity is
  checked before consequential writes. Completed preparation evidence cannot be
  used to recreate a disappeared remote object. The coordinator is tested directly
  but **is not connected to controller.reconcile**; that connection is still required.
- Step 8 foundations: `build_evidence.py` verifies the exact registered source/
  controller/run/attempt/nonce tuple, successful six-cell matrix plus Ruff and
  aggregate, and a complete immutable reuse-key field set. `artifacts.py` checks
  archive metadata against registered run/controller identity and verifies bounded
  declared file bytes without extracting or executing them. It rejects expiry,
  swapped runs, digest mismatch, traversal, absolute paths, links, duplicate or
  undeclared entries, excessive sizes and invalid archives. These are pure
  verifier primitives; no registration, build dispatch or artifact download is
  implemented by them. They do not make release-mode CI available.

### Executed Checks And Counters

| Check | Result |
|---|---|
| Own-reservation replay red | 2 expected missing-interface failures, then 2 passed |
| Preparation transport red | Missing preparation_remote module; then 8 passed |
| Reviewed-commit red | Missing reviewed_commit module; then 12 passed |
| PR producer-check red | Missing github_checks module; then 6 passed |
| Preparation coordinator red | Missing prepare_stage module; then 1 passed with real journal and mocked remote boundary |
| Build/archive red | 2 missing-module collection errors; then 28 passed |
| First complete continuation regression | 462 passed |
| Added real-Git commit-byte test | 1 failed, 462 passed; Windows text stdin translated LF to CRLF |
| Corrected real-Git byte test | 1 passed using binary stdin; Git computed the same commit ID |
| Final full locked/offline Python 3.12 package regression | **463 passed**, 0 failed, 39.34 seconds |
| Native preflight regression | **52 passed**, 0 failed, 0.40 seconds |
| Package/benchmark Ruff | Passed |
| Tracked git diff --check | Passed |
| Pester | Returned intermediate 23:31:30Z result retained; no new run |
| Embedded review:auto | 0/10, full route still required after implementation |

Commands remain the exact locked/offline package pytest, native preflight pytest,
package/benchmark Ruff, and git diff --check commands recorded above. The real-Git
fixture calls hash-object on binary LF bytes in a temporary directory; it does
not create a commit in this worktree. No live GitHub call or mutation was made.

Step 7 functional recovery is now **2/2 used and resolved**. The second attempt
corrected Windows newline translation in the added test fixture, not production
commit hashing. The diagnostic rerun exposed Git's exact badTreeSha1 error and
was not a second repair attempt. Step 8 functional recovery is **0/2**; its pure
verifier tests passed after the missing-module red phase. All inherited counters
and review-repair history remain intact. Mechanical import/format corrections
completed; get_errors remains unavailable. No new review findings or independent
critical-error count are claimed. The existing tests pass, but review is pending.

### Required Remaining Work

1. Connect the preparation coordinator to the real worker with one bounded action
   per wakeup. Add a transport-only end-to-end fixture from sealed request through
   PR creation/reconciliation and actual merged binding; current coordinator tests
   replace its remote ensure/merge boundaries and are not that evidence. Preserve
   earlier admission-only test intent while testing the new stage transition.
2. Implement strict sealed build-request records, registration to an actual trusted
   default-ref run/attempt before source execution, duplicate-claim rejection and
   immutable source/controller/job identities. The pure dictionaries in the verifier
   are not a registration or remote schema-validation implementation.
3. Implement one-shot trusted workflow dispatch and uncertain dispatch reconciliation,
   full reuse-key acquisition from exact source locks/toolchain/policy inputs, API
   collection of run/jobs/check-suite/artifact evidence, a bounded binary download
   path, and lifecycle evidence reuse/expiry handling. Keep separate source and
   workflow head SHAs. Do not reuse ordinary PR aggregates for release admission.
4. Implement the isolated build/registration/verifier template and connect
   release-controller-ci.yml's arbitrary-branch release mode to exact registered
   source checkout. It still deliberately rejects release-mode dispatch today.
   Prove actual policy argv, credential/cache isolation and complete job failure
   handling through workflow/security and transport-level integration tests.
5. After all of that passes local regression, request the fresh final unfiltered
   Pester child and full ten-spec embedded review sibling, then authorized repairs
   and independent verification. Only then evaluate V4 and completion metadata.

Live secret-boundary and six-cell execution remain Phase 7/final evidence with
explicit sandbox authorization, installed pins and protected App/environment/ref
settings. Their absence is not used as an excuse to stop the remaining offline
Phase 4 implementation, nor are the local verifier tests represented as live proof.

Plan metadata remains status active, completed-phases [1, 2, 3], current-phase 4.
V4 remains partial; no accepted exception, Phase 5, commit/push, roadmap update,
remote mutation, shared configuration edit or other-worktree edit occurred.
Exact continuation: `/cg-work phase4 review:auto .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`.

## Phase 4 Final Gate And Review Handoff 2026-09-12T00:56:41Z

The remaining Step 7/8 implementation is connected and locally verified. This
supersedes the outstanding implementation lists in the two earlier Phase 4
checkpoints. It is now ready for the requested **final** dedicated test sibling,
then the full embedded review:auto sibling. Phase 4 is not marked complete until
those stages and any required repair verification pass. No Phase 5 is authorized.

### Completed Implementation

- `controller.reconcile` now advances already sealed requests through the new
  stage router. Admission remains one separate bounded wakeup; preparation,
  review binding, build dispatch/collection and waiting states do not poll or
  perform publication. Disabled policies retain the prior no-stage-write behavior.
- The preparation coordinator is connected to the worker. It uses exact own-
  reservation replay, request-bound manifest bytes, isolated staging, expected
  tree/commit identities, intent-before-write PR reconciliation, current reviewer
  authority and protected-branch review counts. Metadata-only default-branch
  movement after merge is accepted only with an identical canonical policy
  digest; it does not silently replace the confirmed policy or source inputs.
- Strict sealed build tickets cover request/source/tree, controller/workflow
  revision/ref, policy/controller/check digests, actual lock digests, declared
  argv/cwd/artifacts, runner/toolchain profile and dispatch nonce. Each required
  workflow gets its own ticket and producer identity. Exactly one workflow is
  designated to produce authoritative release assets; secondary gates do not
  duplicate that build. The generic build template has priority when present.
- Trusted registration verifies actual default-ref workflow/run/attempt and
  installed pins before source jobs start. The journal grants one registration
  claim; duplicates and reruns cannot consume it again. Actual registration can
  reconcile a lost dispatch response. Unknown dispatch is never blindly replayed.
  Controller and registration templates share a non-cancelling control concurrency
  group, and the coordinator does not write over a pending registration.
- Source jobs check out only the registered release SHA. The pinned installed
  helper runs with Python isolated mode and executes the declared argv without a
  shell in the source directory. The real-command fixture verifies generated
  bytes, not only an argv spy. Source output staging permits only declared regular
  files and bounded bytes. It has no control/publishing environment, App key,
  credential, or shared cache. The control job does not check out source code.
- `build_step` obtains actual run, attempt, job, runner, check-suite and artifact
  API records. It checks the current run attempt as well as the historical attempt,
  so a later rerun cannot hide behind prior success. Every required matrix/job and
  exact App/workflow identity must succeed. Source SHA and workflow HEAD remain
  separate; no ordinary PR aggregate is accepted as release-mode evidence.
- Binary artifact download uses an exact numeric GitHub artifact endpoint, no
  source-provided URL, and bounded byte capture. Verification checks retention,
  actual run/controller association, archive digest when provided, declared file
  inventory, sizes, media types and hashes. No archive is extracted or executed
  in the control/verifier context. At this checkpoint the pre-parser guard checked
  only the reported EOCD count, not the actual central-directory count. Review
  P2.1 proved that claim insufficient. Repair cycle 1 below replaces it with a
  physical-range/header walk before allocation. The compressed download capacity
  remains explicitly 64 MiB; policy limits still apply.
- Reuse rechecks remote jobs, attempt and artifact bytes, not a cached boolean.
  Expired pre-approval artifacts or changed workflow inputs produce a new ticket
  and invalidate the prior ready-for-approval state. A narrowly validated journal
  transition permits that rebuild only before publication and for the same
  reviewed release SHA/tree. Prior final build evidence remains immutable under
  versioned build-validated keys. Publication-started state cannot move backwards.
- `.github/workflows/release-controller-ci.yml` now has protected registration,
  isolated source build, registered-source six-cell package matrix and Ruff, and
  a strict release aggregate. Ordinary PR/merge/push CI bypasses registration and
  needs no protected secrets. `templates/build.yml` supplies a disabled generic
  build template. The controller template requests actions write for dispatch;
  registration requests only actions read. Deployment still needs reviewed setup.

### Actual Verification

| Check | Result |
|---|---|
| Final full locked/offline Python 3.12 package suite | **487 passed**, 0 failed, 41.71 seconds |
| Final native preflight regression | **52 passed**, 0 failed, 0.44 seconds |
| Package and benchmark Ruff | Passed |
| Tracked git diff --check | Passed |
| Real worker/registration transport-only scenarios | Passed: normal and lost-PR-response paths through awaiting-approval and verified reuse; later rerun rejected |
| Actual isolated build command | Passed: real subprocess generated the declared wheel fixture and staging retained exact bytes |
| Workflow tests | Passed: credential/job isolation, six-cell route, disabled generic template, and executed ordinary/release aggregates |
| Final Pester | **Pending dedicated child**; old 23:31:30Z run remains intermediate evidence only |
| Embedded review:auto | **Pending, full route, 0/10 specs** |
| Live build/publication/latency/secret-boundary trials | Not executed or claimed |

The Phase 4 package delta adds 105 cases over the Phase 3 count of 382. The two
worker integration cases execute real CLI/context/controller/router/journal/
registration/verification decisions. Only GitHub wire responses, clock and job
environment are simulated. The earlier Phase 3 transport tests explicitly stub
only the new Phase 4 router so their original admission/queue scope remains intact;
their real Phase 3 admission/replay decisions are not replaced. The new Phase 4
tests do not use that stub.

Commands:

```text
uv run --offline --project packages/cg-release --python 3.12 --locked pytest packages/cg-release/tests -q --tb=short
python -m pytest scripts/tests/test_cg_pr_preflight.py -q --tb=short
uv run --offline --project packages/cg-release --python 3.12 --locked ruff check packages/cg-release scripts/benchmark_release.py --output-format concise
git diff --check
```

No actionlint executable is available. Workflow unit tests and executed aggregate
checks passed; no live Actions execution or actionlint result is inferred from
them. get_errors is unavailable, so Ruff is the recorded diagnostic check. A final
annotation-only correction makes binary process return types explicit; it does
not change execution. Its final affected regression passed 33/33 in 0.80 seconds;
Ruff, tracked whitespace, and canonical plan validation also passed after the
handoff artifacts were written. The dedicated gate can rerun the package suite too.

### Counters And Review Focus

Step 7 remains **2/2 functional recovery attempts used and resolved**, both for
the recorded Windows byte-conversion fixtures. Step 8 remains **0/2**. All prior
Step 1-6 and review-repair counters are preserved. New integration requirements
were added as explicit red tests before fixes: post-merge default-branch policy
digest binding, lost-dispatch registration, runner identity, later-attempt reuse,
pre-approval artifact expiry, pre-parser ZIP inventory bounds, and protected-branch
review counts. These expected test-first red baselines are not hidden as passing
tests and do not reset prior recovery history. The complete suite then passed.

No unresolved test failure is observed. Independent critical-finding counts are
**not assessed** until the full review runs. Review should inspect identity and
authority boundaries, multi-workflow/nonce/intent races, evidence capacity and
rebuild transitions, archive bounds, workflow credential isolation, exact-source
checkouts, protected review requirements, and the distinction between mocked wire
evidence and real future live proof. No exception has been accepted.

### Exact Parent Handoff

The implementation writer is paused for the final stages. Run these strictly
sequentially in the current improve-cg-release worktree:

1. Dedicated test sibling: load cg-skill-pester-safety; run
   `. tests\Run-Tests.ps1` with no flags or pipeline. Read tests/last-run.json and
   return passed, totalCount, passedCount, failedCount, skippedCount if present,
   failures, filteredFiles, ranAt and gitSha, plus the existing cleanup caveat or
   any changed caveat. Require filteredFiles null. Do not repair or change phases.
   Optionally repeat the exact package/preflight/Ruff commands above in that child.
2. After the final gate passes, dedicated read-only embedded review:auto sibling:
   resolve full via review-routing.contract.md. Read and apply all ten unique
   specs: code-quality, testing, documentation, version-control, reproducibility,
   performance, architecture, data-quality, learnings-researcher and adversarial.
   Review Phase 4 files and their necessary interactions, not an untracked-files-
   invisible git diff. Save the findings artifact at
   `.cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase4-review.md`.
   Return compact counts, finding IDs with file/line evidence and V4 coverage.
   Do not implement fixes, publish, or advance a phase in the review child.
3. Return findings for already-authorized in-scope repairs, then independently
   verify any repairs and rerun affected/final gates. Preserve all counters.
   Only after this succeeds may the parent complete V4 and the phase metadata
   transaction. Stop at the Phase 4 boundary; do not execute Phase 5.

Exact repair/completion continuation remains
`/cg-work phase4 review:auto .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`.

Phase 7/final live evidence still requires an explicitly authorized sandbox,
reviewed controller wheel/revision and workflow installation, configured control
and publication App/environment/ref protections, actual registered six-cell run
IDs, and secret/approval and latency trials. None were fabricated or substituted
by local YAML inspection or provider fixtures. No remote write, worktree commit,
push, Phase 5 operation, shared configuration or other-worktree edit occurred.

## Phase 4 Review Repair Cycle 1 Start 2026-09-12T01:17:45Z

Read the full review at
`.cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase4-review.md`.
The ten-spec review reports P0 0, P1 2, P2 1, P3 0. It emulated all ten specs
sequentially, not ten independent sessions. The user authorized repairs for all
three findings and requested the next independent verification handoff.

Read and confirmed the final pre-review Pester record: 2026-09-12T01:05:10Z,
gitSha b94f585, 2904 passed, 0 failed, 2 skipped, total 2906, filteredFiles null.
Retain the known cleanup qualification. No Pester command runs in this repair
writer. The reviewed package/preflight results remain historical until rerun.

This is review repair cycle **1** for P1.1, P1.2 and P2.1, separate from functional
recovery. Step 7 remains 2/2 used and resolved; Step 8 remains 0/2. All earlier
counters remain unchanged. No phase advancement, exception, or remote mutation
is authorized. Keep the original review findings open until independent verification.

P1.1 red proof uses the real CLI/controller/journal from before PR binding with
both generic and package-CI workflows. The fixture provides only the real ordinary
CI PR role, not an invented PR run for the dispatch-only generic workflow. It
failed at review binding with E_CHECK_EVIDENCE before the fix. The first repair
adds explicit mandatory check stages to trusted policy while retaining every
declared check as a final registered release gate.

## Phase 4 Review Repair Cycle 1 Handoff 2026-09-12T01:50:16Z

All three requested repairs are implemented and regression-tested. They remain
**pending independent verification**, not independently resolved. The original
review file and its open finding statuses are unchanged. No Phase 4 completion
field, review finding count, or prior counter was silently cleared.

### P1.1: Stage-Aware Check Policy

RequiredCheck now has a mandatory trusted `stage` field with exactly two values:
`preparation-and-release` and `release`. Preparation verification consumes only
the former; ticket creation, producer binding, final gate collection and reuse
digests retain the complete required-check list. Policy validation rejects a
configuration without any preparation PR check. Missing or unknown stages fail
strict schema validation rather than being inferred from filenames.

The generic build template now instructs setup to declare its dispatch-only
`build` check as `release` and ordinary CI as `preparation-and-release`. The
policy example and fixtures are updated. This is an explicit unreleased policy
contract change; no remote policy or deployed configuration was edited.

`test_phase4_generic.py` starts through the real CLI, sealed request, preparation
PR and reviewed-commit binding, then completes both actual workflow roles. Its
PR inventory includes only ordinary CI, never a fictional generic PR build.
The registered generic build and registered CI use separate actual run IDs;
both remain in final evidence and only the generic run supplies release assets.
The test reproduced E_CHECK_EVIDENCE before the fix and now passes. Four stage
schema/policy negatives also pass.

### P1.2: Atomic Tickets And Registration Claims

Added `journal_checkpoint.py` for one-transaction, controller-only build data.
Initial and replacement tickets now atomically store their complete nonce,
inputs, checkpoint and state. There is no intent/result gap for these records.
Registration likewise records its whole claim in one atomic transaction after
actual run identity validation and before returning source-job outputs.

The journal validator narrowly allows these atomic audits only for sequential
`build-request-N` and exact-ticket-bound `build-registration-N`, with typed data,
matching digests, append-only evidence and pre-publication building states.
Dispatch and publication cannot use this path. A competing or completed claim
is rejected, even for identical proposed data. Existing opaque or unrelated
intents are not cleared, replaced, or guessed. The repaired code no longer emits
the old digest-only ticket/registration half-state; no live migration is claimed.

The existing journal read-back path reconciles an accepted atomic append whose
HTTP response is lost. Worker restart tests also inject actual process death
before and after the provider commit, outside the recoverable-error handler.
Before commit, no partial record remains. After commit, the exact complete ticket
or registration remains. Replacement-ticket tests preserve old verified evidence.

A stop after a registration commits but before source outputs are returned does
not authorize a second claim on that run. If that actual run then fails, the
controller verifies its recorded identity and permits an **authorized manual
resume** to create one fresh ticket/nonce. Automatic scans do not start that retry;
later attempts, wrong identities and publication-started states remain blocked.
The old registration stays immutable. This avoids an unresolved claim or a dead
version reservation without treating the failed run as successful build evidence.

Six full-worker restart cases cover before/after initial ticket, replacement
ticket, and registration commits. Six atomic-checkpoint tests cover lost response,
single append, external/publication exclusion, opaque-intent preservation, ticket
sequence and registration binding. The red run had four failures and two passes;
the repairs now pass all these cases with the real journal and provider wire model.

### P2.1: Actual Central-Directory Bound

The verifier no longer trusts EOCD's entry count as an allocation bound. It binds
the declared directory to the exact physical range used by the non-ZIP64 reader,
rejects ZIP64 locator overrides and split-volume forms, then walks every fixed
central-directory header with checked variable lengths, offsets and an actual
entry counter. It rejects the first entry above the lesser of the policy limit
and declared inventory length, malformed framing, and a count mismatch before
constructing ZipFile. Existing archive byte, file-size, total-size, compression,
digest, run association and decompression checks remain.

Three new regressions forge a smaller EOCD count, a misleading directory offset,
and a ZIP64 override. They failed before the fix. All now reject before even
calling the ZipFile constructor, rather than allocating extra entries and then
rejecting. The honest-count test remains. This corrects the earlier execution
report's overstatement; no large-memory exhaustion trial or live service result
is claimed.

### Executed Repair Evidence

| Check | Result |
|---|---|
| P1.1 real generic-route red proof | 1 failed at E_CHECK_EVIDENCE before review binding |
| P1.1 first focused green run | 64 passed, including contracts and gate consumers |
| P1.2 worker crash red proof | 4 failed, 2 passed at the actual journal wire boundary |
| P1.2 first integration green run | 25 passed |
| Atomic scope/restart/build verification regression | 32 passed |
| P2.1 forged-directory red proof | 3 failed, 10 passed |
| P2.1 plus repaired worker paths | 20 passed |
| Full locked/offline Python 3.12 package suite | **507 passed**, 0 failed, 47.83 seconds |
| Native preflight regression | **52 passed**, 0 failed, 0.42 seconds |
| Package and benchmark Ruff | Passed |
| Tracked git diff --check | Passed |
| Updated final Pester | Pending dedicated child; 01:05:10Z result predates these repairs |
| Independent repair verification | Pending |

The package now has 20 additional review-regression cases over the reviewed count
of 487. This is review repair cycle 1 for each of P1.1, P1.2 and P2.1. Step 7 stays
2/2 functional recoveries used/resolved, Step 8 stays 0/2, and all Phase 1-3 and
earlier review counters are preserved. No ordinary functional budget was reset.
All changed source modules remain within the 300-line project limit. Standalone
rg was unavailable; Read metadata verified the relevant module lengths instead.
get_errors and actionlint remain unavailable; no IDE or actionlint result is claimed.

### Exact Next Verification Handoff

The repair writer is paused. Use this same improve-cg-release worktree, sequentially:

1. Dedicated test sibling: load cg-skill-pester-safety and run
   `. tests\Run-Tests.ps1` with no flags or pipeline. Return the compact
   tests/last-run.json fields (passed, counts, skipped/failures, filteredFiles,
   ranAt and gitSha) and cleanup qualification. Require filteredFiles null.
   Preserve the known cleanup caveat; do not repair unrelated environment state.
2. Independent read-only repair verifier: read the original Phase 4 review, this
   cycle's evidence and the changed files. Verify P1.1, P1.2 and P2.1 plus adjacent
   regressions. Focus on complete generic-to-final evidence, atomic before/after
   boundaries and exact claim identity, explicit-only failed-run retry, and actual
   central-directory allocation bounds. Do not treat a passing old probe or a
   constructed review binding as proof of the repaired full route. Test the actual
   new atomic boundaries; never erase an old opaque intent to make a test pass.
3. Record the independent result at
   `.cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase4-verify-review.md`.
   Return compact verified/unresolved finding IDs, any new in-scope findings,
   test counts and V4 recommendation. Do not edit implementation or advance a phase
   in the verifier. If findings remain, return them for the next authorized repair
   cycle without resetting counters. Only the parent completes V4/phase metadata
   after all required evidence passes. Do not execute Phase 5.

Exact available commands for the verifier/test child:

```text
uv run --offline --project packages/cg-release --python 3.12 --locked pytest packages/cg-release/tests -q --tb=short
python -m pytest scripts/tests/test_cg_pr_preflight.py -q --tb=short
uv run --offline --project packages/cg-release --python 3.12 --locked ruff check packages/cg-release scripts/benchmark_release.py --output-format concise
git diff --check
```

The repair evidence artifact lists the exact source/test scope. All provider
effects were simulated; real Git activity stayed in isolated test fixtures.
There was no remote mutation, commit/push, Phase 5 action, other-worktree edit,
shared configuration change, or fabricated live build/security/latency evidence.

## Phase 4 Completion Decision 2026-09-12T02:10:27Z

The parent supplied the refreshed final gate and independent repair verification.
Read both original artifacts directly and accepted the verified results below.
Canonical plan validation passed before any completion writes. No implementation
changed during this finalization, and no test run is falsely attributed to this
finalization session.

| Required evidence | Accepted executed result |
|---|---|
| V4 Steps 7-8 | Bounded edit-set application and real-Git expected trees; reviewed release binding; actual worker/provider-model registration, exact-source multi-workflow gates, artifact verification, interruption recovery and isolation tests |
| Full package regression | Independent verifier: 507 passed, 0 failed, 51.49 seconds, locked/offline Windows Python 3.12 |
| Native preflight | Independent verifier: 52 passed, 0 failed, 0.56 seconds |
| Additional registration probes | Independent verifier: 5 passed with the real in-memory journal and atomic helper |
| Full safe Pester | Dedicated child, 2026-09-12T02:00:08Z, gitSha b94f585, passed true, 2904 passed, 0 failed, 2 skipped, total 2906, filteredFiles null |
| Review | Full 10/10-spec review followed by independent code-quality/testing verification; P1.1, P1.2 and P2.1 fixed, 0 open, 0 new findings at every priority |
| Diagnostics | Verifier Ruff and tracked whitespace checks passed; canonical plan validation passed in finalization |

Verification authority:
`.cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase4-verify-review.md`.
Final phase evidence:
`.cg-docs/work-reports/release-controller/2026-09-12-phase4-final-evidence.json`.

**V4 decision: passed.** No Phase 4 evidence item remains unmet, no failing step
remains, and no accepted exception is needed. The full review's 10 specs were
sequential local spec passes, not ten independent sessions. The later verifier
was independent and performed two spec passes, full executed regressions and
five additional probes. Those counts are not added together as independent agents.

Retain the Pester TestDrive missing-path/nonempty-directory cleanup caveat and
the two skips. Zero failed assertions does not prove successful temporary cleanup.
The independent verifier found no evidence that this qualification invalidates
the Phase 4 checks. No cleanup was attempted. get_errors and actionlint remain
unavailable; Ruff is not a type-check or IDE diagnostic claim.

This is local Phase 4 completion, not whole-plan completion or production
readiness. Actual six-cell Actions execution, live hostile-source/secret-boundary
probes, protected approval and publication trials, and latency evidence remain
the plan's later authorized gates, especially V7 and V8. They are not inferred
from YAML or offline provider fixtures. No historical opaque-state migration is
claimed. No Phase 5 operation is authorized or executed.

Counters are preserved: Step 7 functional recovery 2/2 used and resolved; Step 8
0/2. Review repair cycle 1 resolves all three findings by independent verification.
All prior phase and repair histories remain unchanged.

Crash-safe finalization sequence: save this evidence decision first; append 4 to
the plan's completed-phases and re-read; only then set informational current-phase
to 5; retain status active; finally refresh the active-state pointer and confirm
the completed transaction. No next execution command is authorized at this boundary.

## Phase 4 Checkpoint Reconciliation 2026-09-12T02:18:24Z

The user authorized completion of the interrupted original pipeline Step 4 only,
with no repeated implementation and no Phase 5. Read the local cg-work command,
project instructions, completion and active-state contracts, the canonical plan,
the 02:10:27Z completion decision, and its original implementation, repair, final
evidence and review artifacts. The local Brain query returned the compact
active-state handoff plan; current contracts and direct evidence remain authority.
open-brain tools were unavailable.

Canonical plan validation passed in this reconciliation before any write:
`cg-render-artifact --validate-only .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`.
Direct reads confirmed the required V4 Steps 7-8 evidence, 507 package passes,
52 preflight passes, five additional atomic probes, and the dedicated child's
unfiltered `tests/last-run.json` at 2026-09-12T02:00:08Z: passed true, 2904 passed,
0 failed, 2 skipped, total 2906, filteredFiles null, failures empty, gitSha b94f585.
The current commit remains b94f585. These are existing executed test results;
no implementation, test suite or review was repeated in this reconciliation.

The full review has all ten required spec passes. The independent verification
has both required light-route spec passes and confirms P1.1, P1.2 and P2.1 fixed,
with zero open findings, zero new findings and no incomplete review scope.
Retain the distinction between spec passes and independent sessions, the two
Pester skips and the TestDrive cleanup caveat. No V4 requirement remains unmet;
no exception or new repair attempt is needed.

The authoritative plan already contained `completed-phases: [1, 2, 3, 4]`,
`current-phase: 5`, and `status: active`, with no failing-steps field. Those
crash-safe completion writes survived the interruption and are left unchanged;
Phase 4 is not appended again. Only the stale execution-report status,
active-state handoff and final-evidence completion marker are reconciled.
Active-state remains `handoff`, records V4 passed, points to the final evidence
and independent verification, and has informational currentPhase 5.
Its nextCommand is null because no next execution command is authorized here;
currentPhase 5 is not evidence that Phase 5 started.

Step 7 functional recovery remains 2/2 used and resolved; Step 8 remains 0/2.
Review repair cycle 1 and all prior counters, evidence and work are unchanged.
No code, test, workflow, plan, review, roadmap, configuration, remote object or
other worktree was changed. No commit, push, publication, cleanup or later
pipeline step was performed. Live matrix, security-boundary, approval,
publication and latency evidence remain later gates, not local V4 claims.

**Original pipeline Step 4: Success.** Phase 4 completion is reconciled;
the overall plan remains active and paused before Phase 5.

## Phase 5 Start 2026-09-12

Authorized invocation is Phase 5 Steps 9-10 and embedded review:auto only. Read
the matching local prompt first, project instructions, charter/configuration,
the full selected plan and relevant execution/artifact/active-state contracts.
The canonical plan validator passed before edits. Phase 4 reconciliation and
final evidence record 507 package passes, 52 preflight passes, 2904 Pester passes,
zero failures and two skips; retain the TestDrive cleanup qualification.

Loaded Python, Brain-query and Pester safety skills. The bounded Brain query
selected the current plan and the immutable tag/artifact solution
`.cg-docs/solutions/git-workflows/2026-08-13-verified-pages-artifact-and-release-tag-gates.md`.
Apply its exact provenance and no privileged source execution rules, not its
superseded main-only branch policy. The query reported 600 index warnings.
open-brain is unavailable. No missing remote evidence is inferred from memory.

Test index includes journal, authority, process, build, worker and transport
fixtures. Phase 5 approval/publisher/signing/recovery/fault tests do not exist yet.
Tests precede new behavior. Step 9 and Step 10 functional recovery counters start
at 0/2. Prior counters remain unchanged, including Step 7 2/2 resolved and Step 8
0/2, and Phase 4 review repair cycle 1. Ordinary in-scope review repair is
authorized; no artificial review-authorization stop will be added.

No Pester runs in this implementation session. Required Pester/review stages use
dedicated parent-dispatched siblings if nested dispatch is unavailable. No
Phase 6, roadmap write, commit, push, PR, live release, settings change or secret
deployment is included. Actual protected GitHub and signing trials remain V7.

## Phase 5 Transport-Reset Checkpoint 2026-09-12T02:43:55Z

Inspected the preserved worktree and own Phase 5 files after the transport reset.
No remote operations occurred; there is no external write to replay. Existing
Phase 1-4 evidence/counters and unrelated changes remain untouched.

Executed red baselines: approval/signing, publisher/fault matrix, recovery, and
publication transport/control imports each failed because its new production
module did not yet exist. Subsequent focused runs passed: 29 approval/signing,
19 publisher/fault, 13 recovery, 7 transport, and 36 combined control/publication/
recovery tests (overlapping scopes, not additive counts). Full locked/offline
Python 3.12 package regression passed **579 tests**, zero failed, in 53.26 seconds,
including installed-wheel tests. This is intermediate evidence, not V5 completion.

GPG setup initially failed before the signing test body: Git for Windows bundles
GPG outside PATH, and its MSYS agent cannot use the supplied Windows home syntax.
The investigation tried a short temporary directory, forward-slash drive paths,
and finally MSYS /c/... paths. Five setup-error runs are retained in session tool
evidence; no failed product assertion was hidden or weakened. The final combined
29-case run passed with real ephemeral Ed25519 key generation, signing, Git
verification and wrong-key rejection. Test and production GPG homes are temporary;
no global key/configuration or live signing credential was used. No new functional
recovery allowance is claimed from this environment investigation.

The first Ruff run reported 166 diagnostics, mainly compact unformatted code and
fixture import shadowing. Targeted formatting left 24; cleanup is in progress.
No IDE get_errors or actionlint result is claimed. Pester and embedded review have
not run for Phase 5. Approval acquisition, workflow integration and complete
recovery-worker coverage remain required before a final handoff.

## Phase 5 Implementation Handoff 2026-09-12T03:16:27Z

Phase 5 is **not complete**. Its checked implementation now reaches generic
publication/completion offline, but full V5 scope and embedded review remain
open. This is an implementation and evidence handoff, not a missing-authorization
stop, a final verification claim, or permission to proceed to Phase 6.

### Implemented Scope

- `approval.py` and `publication_approval.py`: bind actual run/attempt, workflow,
  repository, controller SHA, numeric environment, digest, successful seal job,
  active protected job and permitted independent approver. Reject requester and
  reconfirmer approval, administrative bypass and changed job/run inputs.
- `publication_inputs.py`: recheck exact registered build runs/jobs, current
  policy and authority, safe immutable source blobs, inventory bytes and notes.
  Produce the public provenance asset without extracting or executing source.
- `publication_control.py`, `publication_rules.py`, `journal_checkpoint.py` and
  `journal_rules.py`: atomic one-run/one-nonce seals, repository-wide owner claims,
  immutable public tag bytes, and recovery metadata which preserves outstanding
  publication intents. Existing build checkpoint rules remain covered.
- `publication_stage.py`, `stage_router.py`, `controller.py`, `publish_worker.py`:
  one bounded publication dispatch, a pre-approval seal with immutable GitHub
  evidence URL, and a separate protected publisher. Lost dispatches do not replay.
- `publication_credentials.py` and `templates/publish.yml`: separate per-process
  control/publishing credentials, a disabled separate-job workflow, App permission
  requirements, and a conservative credential-expiry upper bound. The template
  is not installed or enabled; no repository/environment secret was accessed.
- `signing.py` and `process.py`: isolated ephemeral GPG homes, optional/required
  allowlisted signing, exact public object bytes/OID and `git verify-tag` checks.
- `publication_remote.py` and `publisher.py`: exact non-force tag push, draft
  staging with latest disabled, bounded asset upload/download, no clobber/delete,
  explicit final latest selection and remote read-back before completion.
- `publication_reconcile.py` and `recovery.py`: read-only partial-effect checks,
  terminal/expired-owner reassignment, pre-tag tip equality, post-tag ancestry,
  mirror-prefix verification and separate published/complete hook states.
- `runtime.py`: permit unchanged policy content after a reviewed release binding
  when the protected default branch advances. An unreviewed request retains its
  original exact policy-SHA check; current authority and digest checks remain.
- Tests cover the above, actual temporary bare-Git pack/ref operations, actual
  ephemeral Ed25519 signing and wrong-key rejection, separate credential roles,
  normal/partial protected-worker publication, new approval after prior-owner
  expiry, and recovery after default-branch advancement without changing already
  uploaded provenance bytes.

### Executed Evidence

| Check | Result | Qualification |
|---|---|---|
| Full locked/offline package suite, Python 3.12 | 604 passed, 0 failed, 54.94 s | Includes installed-wheel tests; local/simulated-provider only |
| Native preflight pytest | 52 passed, 0 failed, 0.42 s | Existing non-Pester checks |
| Ruff, package plus benchmark script | All checks passed | Final command after import-only cleanup |
| Canonical plan validator | Passed | No Phase 5 completion metadata was written |
| `git diff --check` | Passed | Tracks existing tracked changes; untracked package covered by Ruff/tests |
| Pester | Not run here | Dedicated canonical runner remains required |
| Embedded review:auto | 0/10 completed | Resolves to full; parent dispatch required |
| Live GitHub, protected signing and cross-role server trials | Not run | Phase 7 controlled trials, not fabricated offline evidence |

Evidence summary:
`.cg-docs/work-reports/release-controller/2026-09-12-phase5-intermediate-evidence.json`.
Final source modules remain below the project 300-line production-module limit.
No dependencies, global key configuration, release tags, live Releases, settings,
secrets deployments, project commits, pushes or PRs were created.

### Failure And Counter Preservation

Preserve all prior phase counters, including Step 7 2/2 resolved, Step 8 0/2 and
Phase 4 review repair cycle 1. Phase 5 Step 9 has **2/2 resolved functional
corrections**: the new registered-inventory fixture needed its real `_request`
interface; the full regression later found the old `Phase 4` user-message
assertion after the intended Phase 5 routing extension. The latter was replaced
with an exact disabled-policy instruction assertion, not removed. Five GPG setup
errors and their environment investigation remain separately recorded above.
No new ordinary Step 9 retry allowance is claimed. Step 10 remains **0/2** for
failed post-implementation functional runs. Additional new behavior had explicit
red-before-green tests, including initial dispatch, duplicate nonce sealing,
owner/intention coexistence, reviewed-default resume, and frozen-provenance
recovery. Embedded review repair count is **0** because review has not run.

The intermediate 599-pass/1-failure full run (52.56 s) is superseded by the
604-pass run, not erased. All earlier phase evidence remains historical evidence
for its original scope only. The earlier Pester 2904/0/2 and TestDrive cleanup
qualification are not represented as a Phase 5 Pester result.

### Remaining Offline Scope

1. Complete exact rebuild plus fresh protected approval when Actions artifacts
   expire after `publication_started`. The current worker correctly returns
   `E_REBUILD_REQUIRED` instead of publishing unverified bytes, but automatic
   recovery from that state is not yet wired. This is implementation work, not a
   request for live-release authorization.
2. Complete the audited stranded-history and journal-restore operational paths.
   Exact mismatch guards and mirror-prefix checks exist, but a helper alone does
   not satisfy the entire Step 10 recovery workflow and its tested checkpoint
   combinations.
3. Integrate newly published journal history into future admission, and recheck
   the complete remote managed history before the repository-wide latest choice.
   The current worker uses policy bootstrap plus journal publication versions;
   `source.adopted_history` still needs the full durable-history integration.
4. Complete the required checkpoint/fault matrix: cancellation between remote
   effect and journal result, uncertain reads, delayed/denied observations and
   recovery combinations. Current primitive before/after-write tests and the
   real-journal protected-worker tests are meaningful but not the whole V5 row.
   Publication `main`/GitHub transport integration also needs independent coverage
   beyond the existing component and wire-format tests.

No accepted exception removes these requirements. Do not mark Steps 9-10 or V5
complete merely because the current package suite passes.

### Exact Parent Handoff

The implementation child has no native nested task/execution tool. The parent
can dispatch the required dedicated siblings; do not treat this as a capability
failure which stops authorized Phase 5 work. Keep the writer paused while the
following current-snapshot checks run, then return the results for ordinary
in-scope completion and repairs under the same Phase 5 authorization.

**Dedicated test sibling instruction:** Read project instructions and
`cg-skill-pester-safety`. In this same worktree, run `. tests\Run-Tests.ps1` with
no flags and no pipeline. Read `tests/last-run.json` with the Read tool. Return
only `passed`, `failedCount`, `failures`, `totalCount`, `passedCount`, skipped
count, `filteredFiles`, `ranAt`, `gitSha`, and any explicit runner cleanup error.
Require `filteredFiles: null`; preserve any TestDrive cleanup qualification.
Do not compose `Invoke-Pester`, run in a shared implementation session, edit
unrelated files or reset any prior counters. This is Phase 5 current-snapshot
evidence, not permission to complete the phase.

**Dedicated review sibling instruction:** Read the matching `/cg-review` prompt,
the selected plan, this report's Phase 5 sections, the routing/context contracts,
and all ten applicable agent specs. Resolve `review:auto` to **full** because
release automation, signing, credentials, permissions and schema boundaries are
security-risk changes. Review Phase 5 changed/new modules and tests, template,
runtime/router/journal changes and their Phase 4 interfaces. Inspect the four
open scope items explicitly; classify defects and missing contract coverage, not
as invented authorization blockers. No Pester or implementation edits in the
review sibling. Required agents: code-quality, testing, documentation,
version-control, reproducibility, performance, architecture, data-quality,
learnings-researcher and adversarial. Load the Python skill for each Python
review. Give each agent the global protected-artifact constraint. Require each
result to contain findings with file/line evidence or an explicit no-issues
statement with at least two non-header lines. Do not silently count missing
reviewer output as success, and do not retry an empty reviewer automatically.

Return compact per-agent results to the workflow parent so it can write the
review report itself, using the Phase 5 filename
`.cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase5-review.md`
without overwriting earlier phase reports. Keep `findings:` tracking and P0/P1
strength. Ordinary in-scope repairs remain authorized after the report; no new
permission question is required. Verify repairs and rerun required final tests
in dedicated siblings before marking Phase 5 complete.

Advisory only: the implementation-to-review handoff needs strong independent
reasoning about permissions, provenance and crash recovery, with high effort.
Availability can differ by platform and date; the user makes the final model
and effort selection. No model or effort switch was requested or performed.

Exact continuation remains
`/cg-work phase5 review:auto .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`.

## Phase 5 Review Repair Cycle 2 Start 2026-09-12T07:24:04Z

Read the independent Phase 5 verification report. It confirms P1.1, P1.2, P1.3,
P2.1 and P2.2 fixed and reports one new open P1.4. Preserve that independent
result and all prior counters. The directly read Pester result is 07:06:28Z,
2904 passed, zero failed, two skipped, filteredFiles null, with the known cleanup
qualification; it predates this new repair. The plan validator passed. Cycle 2
will repair only the inconsistent audited override-reason use and add bounded
fake full-path regressions. Phase 5 remains open until independent confirmation.
Phases 1-4 remain complete; Phase 5 remains current. Phase 6 and all early
commit/push/PR/publication actions remain unstarted.

## Phase 5 Continuation 2026-09-12T03:25:13Z

The parent returned the intermediate canonical full Pester result. Read
`tests/last-run.json`: ranAt 2026-09-12T03:24:42Z, gitSha b94f585, total 2906,
passed 2904, failed 0, skipped 2, filteredFiles null. Preserve the reported
TestDrive cleanup qualification. This covers the intermediate snapshot only.
The user directs completion of all four remaining offline implementation areas
before full review. This supersedes the earlier suggestion to review the partial
snapshot. No full reviewer is dispatched now. Prior counters and evidence stay
unchanged; new testable recovery behavior receives red-before-green tests.

## Phase 5 Implementation Complete 2026-09-12T05:19:08Z

All four offline implementation areas identified at the earlier handoff are now
implemented and covered by executed tests. This supersedes that handoff's open
implementation list. **V5 and Phase 5 are not yet marked complete:** the parent
must obtain final full Pester and embedded full review evidence, apply any
ordinary in-scope review repairs, and verify them first. No full review ran while
the remaining implementation was open.

### Completed Recovery Paths

1. **Expired publication evidence.** `publication_rebuild.py` verifies current
   maintainer authority, exact remote effects and terminal/expired owner proof.
   It records the suspended intent and immutable source/tag facts, then returns
   to isolated build execution without clearing `publication_started` or old
   evidence. New tickets, registrations and artifact evidence lead to a fresh
   protected approval. Matching existing assets are retained, never clobbered.
   Already-published matching bytes can instead use retained verified CI evidence
   after Actions retention; `ReadOnlyPublication` prevents every remote write in
   that recovery mode.
2. **Audited recovery.** The trusted controller has a `recover` operation which
   reads only `.release-recovery.json` at the protected default commit and checks
   an explicit canonical digest plus current maintainer authority. Strict
   directives bind the repository, policy, reason and exact mirror or
   request/tag/commit/tree. Missing or safe-prefix state branches can be restored
   from a fully verified signed mirror, using creation or a non-force forward
   update. Divergent/edited heads are not overwritten; they require a separately
   reviewed protected replacement branch. Unknown remote effects, corrupt
   mirrors and denied reads fail before restore writes. A `RecoveryAudit` becomes
   part of the signed journal and survives response loss without duplicate audit.
   Audited stranded tags enter isolated builds with unchanged object bytes.
   Explicit source exceptions retain exact identities and use the protected
   override environment. Such recoveries have stable durable queue entries even
   when the original inbox issue is unavailable.
3. **Durable history and latest.** Newly published journal receipts augment
   bootstrap history without rewriting policy. The original receipt identifies
   its exact seal and input digest. Future admission verifies the tag object,
   Release identity/classification, notes and all asset IDs/bytes; mismatches stop
   admission. Latest selection uses complete managed remote history and SemVer,
   not publication timestamps. Tests include a real CLI preview after publication
   and pagination past 100 Releases.
4. **Checkpoint and transport coverage.** Full fake-wire tests execute the real
   start/control/build-registration/seal/publish entry points. They cancel before
   and after each irreversible write and key control checkpoint. A separate
   26-case matrix interrupts every local publication intent/result checkpoint.
   Denied read-back remains unknown rather than becoming absence. Fresh dispatch
   intent/acknowledgement records no longer overwrite an unresolved release
   effect. Early run registration and exact nonce/workflow discovery recover
   cancellation before a seal is written. Published hook recovery uses control
   reconciliation only and does not publish again.

### Additional Corrections

- Public provenance is tied to the actual immutable tagger and matching sealed
  asset bytes, not an arbitrary first dictionary entry or a later controller run.
  It can retain the existing manifest across branch movement and recovery, but
  cannot reuse a manifest which describes different rebuilt bytes.
- Recovery grants follow verified journal event order, not numeric run-ID or
  dictionary order. Every historical reconfirmer and direct human run trigger is
  excluded from approval; only current authorization is reused for a new ticket.
  Grant identity is included in sealed inputs so a later grant invalidates an
  earlier approval. Published reconciliation resolves the original receipt's
  seal rather than whichever seal happens to sort last as text.
- A published read-only recovery cannot create a missing tag, draft or asset,
  replace bytes, or publish a Release again, even if an observation changes.
- Global recovery audits retain repository identity, hash-chain, signed-writer,
  strict schema and exact tree checks. Event-envelope validation was moved into
  the existing journal model module to keep production modules within 300 lines.
- The old build-ticket unit fixture now declares `publication_started=False`.
  It still tests the normal Phase 4 contract; production fallback code was not
  added to conceal an incomplete fixture.

### Final Local Evidence

| Check | Result | Scope |
|---|---|---|
| Full locked/offline Python 3.12 package pytest | **683 passed, 0 failed, 188.42 s** | Includes installed-wheel tests, real temporary Git/GPG, full fake-wire lifecycle and fault matrices |
| Native preflight pytest | **52 passed, 0 failed, 0.40 s** | Existing native release preflight |
| Ruff for package and benchmark script | **All checks passed** | Final code snapshot |
| Production module bounds | **Passed** | Every production Python module is at most 300 lines; included in full pytest |
| `git diff --check` | **Passed** | Tracked changes; untracked package independently covered by Ruff/pytest |
| Canonical plan validator | **Passed** | Phase boundaries and prior completed phases unchanged |
| actionlint | Not on PATH | No actionlint or live workflow-validation result claimed |
| Final full Pester | Pending dedicated parent test sibling | No Pester executed in this implementation child |
| Embedded `review:auto` | Pending **full, 10 agents** | No Phase 5 reviewer result or repair cycle claimed yet |

Current evidence:
`.cg-docs/work-reports/release-controller/2026-09-12-phase5-implementation-evidence.json`.
The earlier 604-pass implementation snapshot and intermediate full Pester remain
historical evidence only. The intermediate Pester result at 03:24:42Z was
2904 passed, zero failed, two skipped, `filteredFiles: null`, with the TestDrive
cleanup qualification retained.

### Preserved Failure History

All earlier phase counters remain unchanged. Phase 5 Step 9 remains 2/2 resolved.
The Step 10 continuation used two resolved regression corrections: the new
stranded-recovery fixture's repository identity, and the old build-ticket
fixture's missing publication-state field. The latter was the sole failure in
the intermediate full run of **629 passed, one failed, 145.12 s**. That result is
superseded by 683/0, not erased. The prior successful 681/0 gate (185.63 s) is also
retained in the evidence JSON. Two final authority-history regression cases were
added before the 683/0 gate. Step 10 is now 2/2 resolved; no ordinary functional
retry allowance is reset or invented.

New required behavior used red-before-green tests. These exposed the separate
dispatch/effect-intent issue, the missing post-publication hook path and the
missing audited-recovery queue mapping before their implementations were
completed. New fake-wire fixture setup also required matching the existing
branch-head field, the actual stable override environment and GitHub pagination.
These setup/red-baseline results remain in the session tool evidence. The earlier
five GPG setup investigations remain recorded above. Review repair count stays
zero because full review has not run.

### Final Parent Handoff

The remaining work in this phase is verification and any resulting ordinary
in-scope repairs, not unfinished eligible implementation and not a new user
authorization gate. The parent can now dispatch the dedicated siblings in this
same worktree. Keep implementation writers paused while they inspect the final
snapshot.

1. **Final test sibling:** load the project instructions and Pester safety skill.
   Run `. tests\Run-Tests.ps1` with no flags and no pipeline. Read
   `tests/last-run.json` with the Read tool. Return only passed/failed/total/skipped
   counts, `failures`, `filteredFiles`, `ranAt`, `gitSha`, and any explicit cleanup
   error. Require `filteredFiles: null`. Preserve the TestDrive qualification;
   do not silently clean or alter unrelated files. This must be a new final run,
   not reuse of the 03:24:42Z result.
2. **After final test evidence is reconciled, full review sibling(s):** load the
   matching local `/cg-review` prompt, selected plan, routing/context contracts,
   this newest Phase 5 report section, and all ten agent specs. Review the full
   Phase 5 implementation and its Phase 4 interfaces. Required agents are
   code-quality, testing, documentation, version-control, reproducibility,
   performance, architecture, data-quality, learnings-researcher and adversarial.
   The actual generic CLI/worker/transport path, signing/approval/owner boundaries,
   audited recovery and retention behavior are mandatory scope, not optional
   abstractions. Honor protected workflow artifacts; reviewers must not edit
   canonical plans, reports, brain or active state. Return compact findings with
   evidence, or explicit no-issues results with two non-header lines, for every
   agent. Do not silently count missing/empty reviewers as success.
3. The parent writes
   `.cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase5-review.md`
   with normal finding tracking and validates any repairs. Ordinary in-scope
   repair remains authorized. Re-run affected tests and final gates after repairs
   before marking Phase 5/V5 complete. Preserve all counters and earlier reports.

Exact continuation is still
`/cg-work phase5 review:auto .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`.
No Phase 6 implementation, native-profile rollout, live release, remote setting
change, secret deployment, commit, push or PR occurred. Live GitHub control and
signing trials remain Phase 7 work under their specific authorization gates;
the offline tests are not represented as that evidence.

## Phase 5 Review Repair Cycle 1 Start 2026-09-12T05:45:09Z

Read all five open findings in the dedicated full review: P1.1, P1.2, P1.3,
P2.1 and P2.2. The review covered 10/10 specs sequentially in one dedicated
session, not ten independent sessions. The final pre-review Pester artifact was
read directly: 05:24:44Z, 2904 passed, zero failed, two skipped,
filteredFiles null, with the known TestDrive cleanup qualification retained.
The plan validator passed before edits. Prior phase/step counters are preserved;
this is authorized review repair cycle 1, not a reset of functional counters.
Regressions will cover the production process-input boundary, absent artifact
metadata, revoked original requester recovery, per-job transfer counts and
context-preserving worker errors. No later phase or remote operation is included.

## Phase 5 Review Repair Cycle 1 Handoff 2026-09-12T06:54:09Z

All five findings have implementation changes and passing regression evidence.
Their original review entries, severity and open status remain intact for
independent verification. Local test success is not independent confirmation.
Phase 5 and V5 remain current/pending; no later phase was started.

### Finding Disposition

| Finding | Local repair | Executed regression evidence |
|---|---|---|
| P1.1 | A bounded 256 KiB process envelope now accommodates duplicated/base64 journal records. `journal_transport.py` supplies the shared encoder for real writes and capacity preflight. The 64 KiB record bound remains. Publication checks the conservative complete remaining record and encoded transaction before irreversible writes; tagged recovery also checks capacity before retaining a new seal. Draft evidence references the existing full notes by digest instead of copying the body again. Relevant terminal owner facts are retained without copying full API run bodies. | Full fake-wire paths with 6,000 added note characters, four artifacts and two recovery runs; 15,000-character notes with four artifacts; real local Git stdin for the maximum bounded file envelope; valid near-capacity journal refuses before any tag or Release write. |
| P1.2 | `retained_archive` distinguishes verified absence/expiry from unreadable or conflicting inventory. Both pre-tag and post-tag recovery create a new exact-source build ticket when the authoritative artifact is absent. Previous ticket/evidence stays immutable. | Empty `total_count: 0` artifact inventory before and after tagging; successful new registration/approval; explicit 401/403, duplicate names, replaced IDs, renamed archive and wrong run identity rejection. |
| P1.3 | `authorize_record` uses ordinary `authorize_resume` unless a valid exact audited recovery grant exists. The separate grant path requires current maintainer authority and current policy without borrowing the revoked requester's authority. It is carried through controller resume, build tickets, build registration, publication rebuild, sealing and publishing. Initial reviewed recovery authorizes the maintainer directly after directive/digest checks. Original identity and all approval exclusions remain. | The full deleted-source recovery path now also revokes original requester 7, proves ordinary resume fails, then uses maintainer 456's reviewed grant through CLI resume, a new build and registration, fresh sealing and publication. No original permission is restored and no second tag write occurs. |
| P2.1 | A one-entry job-local cache retains verified immutable file bytes/inventory keyed by the complete sealed build, registration and current artifact identity. Policy, authority, approval, ownership, run/jobs and artifact metadata remain freshly checked. New jobs receive a new cache. | Protected publication performs one archive transfer rather than the reviewed seven. A separate regression proves a new job reacquires, skipped jobs still fail, and changed digest metadata forces a new verification rather than a stale cache hit. This is an operation count, not a live speedup claim. |
| P2.2 | The journal exposes only its last fully verified local records for diagnostics. Publisher errors use these records and parsed safe identity without additional recovery reads. Errors retain request, version, checkpoint/intent, expected state, last verified state, elapsed time and a reconciliation action. Workflow summary output was separated into `publication_output.py`. | Pre-write denial, post-tag denial and unknown draft-write errors assert all context fields and the exact known operation. No credentials, raw API body or inferred success is added. |

### Test And Counter Evidence

- All nine initial review reproduction cases failed against the prior code, as
  expected: transport/notes, artifact absence, revoked original authority,
  repeated transfer count, and missing error context. These are recorded red
  baselines, not hidden failures.
- Expanded negative and boundary tests were added without weakening prior
  behavior assertions. The process-size test now targets the intentional new
  `MAX_INPUT_BYTES + 1` boundary and retains its credential-shaped input rejection.
- One capacity-fixture construction was corrected to leave room for its own
  in-flight checkpoint before testing the publication preflight failure.
- The first full repair-cycle run had **699 passed, one failed, 232.66 s**. Its
  old build-stage fixture mocked `build_stage.inventory`, but artifact acquisition
  now goes through the shared retained-inventory boundary. The fixture now serves
  the real paginated response protocol, including `total_count`, instead of
  mocking that prior internal location. All original assertions remain.
- Final full package gate: **701 passed, zero failed, 239.83 s**, including the
  installed wheel, real temporary Git/GPG, full fake transport, review regressions
  and the 300-line production-module bound.
- Final native preflight gate: **52 passed, zero failed, 0.41 s**.
- Final package/benchmark Ruff, canonical plan validation and tracked whitespace
  checks passed. No IDE diagnostic or live workflow result is claimed.
- The 05:24:44Z full Pester result remains **pre-repair** evidence: 2904 passed,
  zero failed, two skipped, filteredFiles null, known TestDrive cleanup errors.
  No Pester was executed in this implementation session.
- Prior phase and step counters, including Step 9 and Step 10 2/2 resolved, are
  unchanged. These authorized repairs and fixture corrections are **review repair
  cycle 1**. No functional counter was reset and no second full review cycle or
  independent verification is claimed.

Current compact evidence:
`.cg-docs/work-reports/release-controller/2026-09-12-phase5-review-repair-1-evidence.json`.

### Exact Final Handoff

1. **Dedicated test sibling:** load project instructions and Pester safety, then
   run `. tests\Run-Tests.ps1` with no flags and no pipeline in this worktree.
   Read `tests/last-run.json` with the Read tool. Return passed/failed/total/skipped
   counts, failures, filteredFiles, ranAt, gitSha and any explicit cleanup error.
   Require filteredFiles null. Preserve the cleanup qualification rather than
   claiming successful cleanup or modifying unrelated files. This must be fresh
   post-repair evidence, not reuse of the 05:24:44Z result.
2. **Independent read-only verifier:** inspect all five original finding IDs in
   `.cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase5-review.md`,
   regardless of their retained open status. Read the repair code and regressions,
   reproduce the corrected boundaries and inspect for new regressions. Verify the
   ordinary and audited authorization paths separately; confirm that approval
   exclusions still include the original requester and all reconfirmers. Require
   current gate rechecks despite the job-local byte cache. Verify capacity and
   error context before and after irreversible-effect boundaries. Do not edit
   implementation, canonical plans, prior reports or active state in the verifier.
3. The parent records the independent result in
   `.cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase5-verify-review.md`
   and reconciles the original finding statuses. Any remaining ordinary in-scope
   defect is still authorized for repair, with the existing counters preserved.
   Only after final gates and independent confirmation may Phase 5/V5 be marked
   complete. Do not start Phase 6 in this handoff.

**Verification safety:** Do not reuse the original oversized-input probe which
called live `run_process` only above 65,536 bytes and relied on rejection before
execution. The corrected bound intentionally accepts those inputs. Use
`BoundedTransport` in `test_phase5_review_repairs.py`, which stubs `_capture` while
running the real process validation, or the real **local Git** stdin regression.
Never execute live `gh` mutations to verify this repair. All current GitHub
operations in the tests were simulated; real Git/GPG operations used temporary
local fixtures only.

No release, remote setting or secret deployment, commit, push, PR, or later-phase
operation occurred. The exact continuation remains
`/cg-work phase5 review:auto .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`.

## Phase 5 Review Repair Cycle 2 Handoff 2026-09-12T07:49:07Z

The independent verification report confirms the five original findings fixed
and leaves only new P1.4 open. P1.4 now has a local production repair and executed
regression evidence. Neither that finding nor Phase 5/V5 is marked complete here;
the user's required independent pass remains pending.

### P1.4 Repair

`publication_inputs.make_inputs` now computes the route with
`request.override_reason or (grant.directive.reason if grant is not None else None)`.
This matches the existing audited authority and recovery-admission checks. The
grant has already been verified against the exact directive, current policy,
maintainer and immutable release. Ordinary publication still has no fallback
reason when no verified grant exists. The grant-specific protected override
environment, original request identity and fresh independent approval checks
remain intact. The original request and its null override reason are not edited.

Two new full-path variants use `BoundedTransport`. They start an ordinary stable
release from initially eligible production branch `feature`, with no override
option or reason and the normal publish environment. After the exact tag/draft
exist, current production policy changes to `main`, `feature` is deleted, and
requester 7 either retains authority or is revoked to `read`. Maintainer 456's
reviewed directive supplies the recovery reason. The tests execute actual CLI
resume, controller recovery, replacement build ticket 2, run 22/artifact 52
registration, new seal 42 and publication through fake I/O.

Both new cases reproduced the reported `E_BRANCH` at
`publication-registration-2` after successful recovery/rebuild. After the narrow
repair, all four reviewed-recovery variants pass. Assertions confirm the original
request and exact tag object stay unchanged, the new seal uses the protected
override environment, requester 7 and maintainer 456 remain excluded from
approval, and the total tag-write count stays one. Ordinary resume still rejects
the changed policy before an audited grant. No unverified reason is accepted.

### Executed Gates

| Check | Result |
|---|---|
| Targeted reviewed-recovery variants | 4 passed, 0 failed, 36.12 s |
| Full locked/offline Python 3.12 package suite | **703 passed, 0 failed, 304.11 s** |
| Native preflight pytest | **52 passed, 0 failed, 0.47 s** |
| Package/benchmark Ruff | Passed |
| Production module bounds | Passed; also included in full pytest |
| Canonical plan validation and tracked whitespace | Passed |
| Post-cycle-2 Pester | Not run in this implementation session; dedicated sibling required |
| Independent P1.4 verification | Pending |

The pre-repair Pester artifact was read directly: 07:06:28Z, gitSha b94f585,
2904 passed, zero failed, two skipped, filteredFiles null. Retain the supplied
TestDrive cleanup caveat; do not reuse this as post-cycle-2 evidence. The original
independent verifier's 701-test pass, seven successful bounded probes and one new
P1.4 failure remain historical evidence and are not replaced or reclassified.

Cycle 2 used one production repair. Before establishing the P1.4 red baseline,
the new test's pre-grant rejection expectation was corrected to the existing
`E_STALE_POLICY` result for changed policy. The subsequent runs failed at the
intended sealing boundary with `E_BRANCH`. No existing assertion was weakened,
and no prior phase/step counter or cycle-1 record was reset.

Current evidence:
`.cg-docs/work-reports/release-controller/2026-09-12-phase5-review-repair-2-evidence.json`.

### Independent Handoff

1. Obtain fresh full Pester from a dedicated safe-runner sibling using
   `. tests\Run-Tests.ps1` with no flags or pipeline. Read `tests/last-run.json`;
   require filteredFiles null and retain any cleanup qualification. Do not run
   Pester in the implementation or verification context.
2. Dispatch an independent read-only verifier for P1.4 and nearby regressions.
   Read the first Phase 5 verification report, this cycle-2 handoff, the scoped
   production change and the four reviewed-recovery variants. Reproduce the new
   initially non-override stable release cases under changed current policy,
   including revoked requester 7. Check current maintainer authority, exact
   directive binding, immutable request/tag, ordinary-publication refusal and
   fresh independent override approval. Use the bounded fake transport; do not
   call live `gh` or network Git. The unsafe old over-64-KiB process probe remains
   forbidden because those inputs are now intentionally accepted.
3. The parent records the result in
   `.cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase5-verify-review-2.md`
   without overwriting the earlier independent report. Finish Phase 5 only after
   independent confirmation that P1.4 is fixed with no remaining blocker and the
   required final gates are satisfied. Do not start Phase 6 in this handoff.

No live remote operation, settings or secret change, commit, push, PR or
later-phase work occurred. Current phase remains 5 and the exact continuation is
`/cg-work phase5 review:auto .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`.

## Phase 5 Completion Evidence 2026-09-12T08:17:40Z

**Evidence decision: Success for Phase 5 Steps 9-10 and required row V5.**
No required Phase 5 evidence remains missing, failed or accepted by exception.
The fresh safe-runner artifact and second independent verification were read
directly before this decision. The implementation has not changed since those
checks. This invocation performs completion bookkeeping only.

### Required Row Reconciliation

| Required scope | Executed evidence | Decision |
|---|---|---|
| Step 9 / V5: bound approval, signing and verified publication | Full 703-test package pass, including temporary local Git/GPG, approval exclusions, exact tag/asset and no-force/no-clobber tests; original full 10-spec review; all six findings independently confirmed fixed | Passed |
| Step 10 / V5: partial-failure recovery and safe replay | Executed intent/result and remote-effect fault matrices, audited recovery, owner/credential, absent/expired artifact, byte/cache and error-context regressions; four full recovery variants plus seven independent refusal probes | Passed |
| Full safe native gate | Fresh 07:56:31Z Pester artifact: 2904 passed, 0 failed, 2 skipped, filteredFiles null; create-release 95/95 with no skips | Passed with the recorded cleanup qualification |
| Native preflight | Cycle-2 gate: 52 passed, 0 failed, 0.47 s; not independently repeated by verifier 2 and no later source edits | Passed |
| Review and repair verification | Full review 10/10 specs; two repair cycles; two independent verification passes using code-quality and testing; six fixed IDs, zero open/new scoped blockers | Passed |
| Diagnostics and plan preflight | Independent Ruff and tracked whitespace passed; module bounds passed in package tests; canonical plan validator passed before completion writes | Passed |

The independent package result is **703 passed, 0 failed, 267.34 s**. The
additional bounded verification result is **11 passed, 0 failed, 64.37 s**.
These are distinct from the implementation gate's 703/0 in 304.11 s. Both remain
recorded with their actual sources; no counts or durations are combined.

The latest Pester evidence is `tests/last-run.json`, ranAt
`2026-09-12T07:56:31Z`, gitSha `b94f585`, total 2906, passed true, failures [],
filteredFiles null. Retain the known TestDrive missing-path/nonempty-directory
cleanup caveat. Zero failed assertions does not prove successful cleanup. Both
skips are in `update`; their names and reasons are not supplied by the artifact.
No new Pester invocation or cleanup was performed in this completion session.

### Scope Qualification

The plan's Step 9 explicitly assigns actual GitHub approval and signing trials
to Phase 7; V7 requires the authorized sandbox, remote source-bound matrix,
secret/approval probes and measured handoff results. Those are not missing V5
tests and are not claimed as executed here. Phase 6 reader/bridge/profile work
also remains unstarted. This decision does not establish live enforcement,
production enablement, a delivered compatibility bridge, remote release success
or a measured end-to-end speedup.

The verifier used guarded offline execution, including rejection of real `gh`,
network Git URLs, sockets and `os.system`; its successful package and probe runs
reported zero guard blocks. Temporary local Git/GPG and fake GitHub protocol
tests are identified as such. The recorded verifier-wrapper and probe-fixture
corrections remain historical evidence, not product fixes or reset counters.

### Review And Counter Reconciliation

Only finding-tracking frontmatter is reconciled: the five IDs in the original
Phase 5 review and P1.4 in the first verification report now read `fixed`, using
the second independent report as authority. Original review narratives, initial
counts, reproductions and earlier handoff statements remain historical text.
Independent verification narratives and executed evidence are unchanged.

Step 9 remains 2/2 used and resolved. Step 10 remains 2/2 used and resolved.
Review repair cycles remain 1 and 2, both independently verified. Prior phase
counters, all pre-repair results, fixture/harness corrections and qualified
Pester results are preserved. No active `failing-steps` entry exists.

Final evidence is stored in
`.cg-docs/work-reports/release-controller/2026-09-12-phase5-final-evidence.json`.
Completion metadata was written in the required order and verified at
2026-09-12T08:22:56Z:

1. Appended 5 to `completed-phases: [1, 2, 3, 4, 5]` and re-read the canonical plan
   while `current-phase` still read 5.
2. Then set informational `current-phase: 6` and re-read both fields. The plan's
   `status: active` and execution-report pointer remain unchanged.
3. Ran `cg-render-artifact --automatic` for the canonical plan. It reported
   `HTML disabled; validated ...`. No derived HTML or source body was changed.
4. Recorded V5 passed and the paused next-phase handoff in active state. No
   implementation, test source, remote setting, secret, tag, Release, commit, push,
   PR or Phase 6 action was performed in this completion session.

**Definitive result: Success for Phase 5.** All required Phase 5 evidence is met,
all six findings are independently confirmed fixed, and no scoped blocker or
accepted exception remains. Phase 6 has not started. The parent-owned next
command is
`/cg-work phase6 review:auto .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`.
This pointer is a handoff only; it was not executed.

## Phase 6 Start 2026-09-12T08:26:25Z

Invocation: `/cg-work phase6 review:auto .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`.
Scope is Steps 11-12 only. The plan validator passed before this append.
Phases 1-5 and their counters remain unchanged. Step 11 and Step 12 each start
with 0/2 functional recovery attempts; no review repair has started.

The explicit user instruction permits all eligible offline reader/profile/docs/
adapter work before the external V6 gate. It does not authorize bridge
publication, controller activation, secrets, settings, live releases, commits,
pushes, PRs, or Phase 7. V6 cannot pass without authorized bridge delivery and
clean-client evidence. No exception is accepted and the stored policy is `ask`.

Brain query: `bin\\cg-index.cmd query --intent work --query "release SemVer updater attestation docs snapshot compatibility bridge" --budget 900 --format md`
succeeded with index warnings. The relevant prior dev-tag plan preserves the
separate four-part escape hatch; the docs deployment plan preserves exact rebuilt
artifact identity. The unrelated external-research result was discarded.
`open-brain` is not exposed in this session; local Brain and saved project
memory were consulted instead. The existing execution report was read only at
its latest Phase 5 completion section. No matching roadmap plan was found.

Test index: existing updater/Pester, release-policy, attestation/removal,
target-update/drift, payload/docs Node tests, and the package fixture corpus.
Tests and independent full-route review will use dedicated sessions. No source
build, remote mutation, or claimed live evidence is part of offline validation.

### Step 11 Initial Evidence

- Red: `python -m pytest scripts/tests/test_release_version_readers.py -q`: 7 failed,
  10 passed. Actual failures are numeric rc ordering, invalid SemVer acceptance,
  and rejected valid SemVer payloads.
- First regression: reader/attestation/contracts/removal pytest: 13 failed,
  199 passed, 4 skipped. The schema subset rejects nested regular-expression
  quantifiers. Step 11 recovery attempt 1/2 restored its supported lexical
  schema pattern with a length bound; the runtime parser supplies strict
  semantic validation. No assertion was weakened.
- Repeated exact pytest selection with `--tb=line`: 212 passed, 4 skipped,
  83.18 seconds. The four platform skips remain explicit.
- `node --test scripts/tests/generate-whats-new.test.js`: 16 passed, 0 failed.
- Dedicated Pester red handoff sent to parent for `release-version-readers`.
  Its actual updater-reader region is intentionally absent until red evidence
  returns. This result is pending and is not counted as passed.

### Phase 6 Reader Checkpoint 2026-09-12T08:50:00Z

The Pester red result was consumed before updater edits: 7 failed, 0 passed.
After implementation the dedicated session returned reader 7/7, updater 143/145
with two skips and no failures, and one passing Windows platform placeholder
for bash-scripts. The latter is not Bash integration evidence. Git Bash actually
executed the strict reader corpus in pytest; clean full PowerShell list commands
ran against fixture-only Git/profile helpers and preserved the stored rc pin.
The latest reader pytest result is 20 passed, 0 failed. Node reader corpus is
1 passed, and existing payload renderer tests are 16 passed.

Implemented so far: native PS/Bash strict SemVer and separate legacy readers,
numeric/ASCII sorting without new updater runtimes, opt-in pre-release/dev
listing, pin acceptance, newer-stable hints, strict Python attestation order,
equal-build-metadata grace exclusion, immutable Node payload grammar, and initial
static documentation snapshot/composition helpers behind explicit assembler
modes. Historical releases and attestations have not been edited. The schema
keeps its supported lexical pattern and bounds tag length; semantic validation
is in the strict reader. Step 11 recovery remains 1/2 used and resolved.

Initial snapshot red test failed for the absent module. Its two implemented
tests now pass; combined legacy/snapshot regression is 5 passed, 1 failed due
to an existing file-symlink fixture raising EPERM on this Windows host, not a
snapshot assertion failure. This environment failure is retained, not silently
skipped or charged as a product repair. No full gate or review is claimed yet.

Compact evidence: `.cg-docs/work-reports/release-controller/2026-09-12-phase6-readers-evidence.json`.
The Step 12 offline profile/workflow/launcher/adapter work, complete shell bridge
fixtures and workflow compatibility guards still need implementation. V6 remains
in progress, not externally blocked as a substitute for that remaining work.
The next implementation session must be the only source writer. The current
session will not make concurrent source edits.

## Phase 6 Review Repair Cycle 1 Start 2026-09-12

The sequential integration implementation and canonical generation finished.
The exact implementation and gate evidence is
`.cg-docs/work-reports/release-controller/2026-09-12-phase6-integration-evidence.json`.
Its source writer is now idle. All five interfaces were generated from canonical
sources; 1,486 generated outputs were written through the real generator.

Full gates exposed ordinary in-scope failures: controller 709 passed/1 failed
(two modules exceed 300 lines); native 2,539 passed/2 failed/50 skipped/2
deselected (C2 confuses the approved standalone package with relocated canonical
modules); Pester 2,916 passed/3 failed/2 skipped (obsolete inline routing
assertions); Node 26 passed/1 existing Windows file-symlink EPERM failure.
The implementation's frozen targeted behavior selection passed 38 tests and
native preflight unit tests passed 58. No failed gate has been called passed.

The independent full-route review completed all ten specs and found 34 issues:
P0=1, P1=18, P2=13, P3=2. The review and exact probes are
`.cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase6-review.md`
and `.cg-docs/work-reports/release-controller/2026-09-12-phase6-review-evidence.json`.
P0.1 is an inherited, explicitly scoped Pages authority defect. The review also
found real provider/process connection failures, immutable snapshot mismatches,
completion-policy and legacy authority defects, and missing offline bridge and
evidence generation paths. These are not external V6 evidence blockers.

The user's initial instruction authorizes ordinary scoped review repairs. Review
repair cycle 1 starts now, separate from preserved implementation counters:
Step 11 remains 1/2 used and resolved; Step 12 remains 2/2 used and resolved with
its final gate failed. No third implementation repair attempt, counter reset,
exception, Phase 7 advancement or publication action is implied. The repair
session will be the only source writer, use sequential groups if needed, and
freeze/regenerate before independent verification. All required offline findings
and gates must be addressed before an external-V6-only state can be claimed.

Environment probes for the retained file-symlink test: `wsl.exe --list --quiet`
returned installation usage, `wsl.exe --status` returned no usable distribution
information, and no Docker executable is installed. No runtime was installed,
permission was elevated or machine setting was changed. Existing directory-link
coverage does not substitute for the failed file-symlink case.

### Review Repair Cycle 1: Security Batch

The sole sequential implementation child completed source repairs for P0.1,
P1.7, P1.10, P1.15, P1.17, P1.18, P2.3 and P2.9. Exact source inventory,
RED/GREEN commands and interim failures are recorded in
`.cg-docs/work-reports/release-controller/2026-09-12-phase6-repair1-security.json`.
Focused GREEN checks: create-release Pester 105/0, docs-automation Pester 24/0,
controller/profile 59/0, Node 24/0 and parsed workflow tests 3/0. Only the
dedicated Pester executor ran Pester. No full gate or generation is claimed.

Legacy dev code now builds without Pages/OIDC authority. Trusted static
composition and constrained historical recovery use exact artifacts and fresh
protected remote-default policy. Completion requirements remain bound to the
approved build; delayed workers recheck requester/resumer authority. These
focused results do not establish the remaining full GPID adapter lifecycle.

Step 11 remains implementation 1/2 used and resolved. Step 12 remains
implementation 2/2 used and resolved with its final gate failed. Review repair
cycle 1 continues with the adapter batch. The untouched 323-line models.py and
305-line build_stage.py still fail the unchanged module bound at this point.
The writer remains disabled; Phase 6 and V6 remain incomplete.

### Review Repair Cycle 1: Adapter Batch

The second sequential source child completed the assigned provider, process,
snapshot, baseline, composition and evidence repairs. Evidence is
`.cg-docs/work-reports/release-controller/2026-09-12-phase6-repair1-adapters.json`.
It records P1.1, P1.3-P1.6, P1.8-P1.9, P1.12-P1.14, P1.16, P2.1, P2.5,
P2.10 for touched APIs, P2.11-P2.12 and P3.1 with RED/GREEN history.

Focused GREEN selections: adapter/lifecycle 52/0, security regressions 59/0,
dispatch recovery 7/0, and Node security/snapshot parity 49/0. These selections
overlap and are not a full-suite count. The real offline lifecycle uses the
production reader, journal, preparation, approval, publication, evidence PR,
installed Node helper and deployment verification interfaces, with outer I/O
supplied by fixtures. Synthetic identities are not delivery or enablement proof.

Repeated provider/docs reconciliation retained 49 separate composition records
with total history above 64 KiB and an unchanged linked parent release record.
Snapshot producer/approval/import bounds and path grammar now agree. The exact
nine-file canonical/native/ownership attestation edit set is sealed before its
evidence PR. Required authority and original-build hook checks remain enforced.
The unchanged module bound passes: models.py 296, build_stage.py 289 and
journal.py 299 lines. Lint and the disabled installation check passed.

The native dependency, actual delivered-bridge qualifier implementation,
packaging, ordinary CI selection, launcher/newline tests and remaining public
API help still require the next batch. No Pester or full gate was run in this
batch. No generation, Phase 6 completion, V6-only status or counter change is
claimed. The source writer remains disabled.

### Review Repair Cycle 1: Packaging And Qualification Batch

The third sequential source child completed P1.2, P1.11, P2.2, P2.4, P2.6-P2.8,
the remaining P2.10 API help, P2.13 and P3.2. Its exact source inventory and
RED/GREEN results are in
`.cg-docs/work-reports/release-controller/2026-09-12-phase6-repair1-packaging.json`.
Focused GREEN checks: packaging/qualification 41/0, security/adapter 58/0,
hooks/process 17/0, native/shell 159/0 with one existing host-related skip,
Node 49/0 and delegated install Pester 96/0. Selections overlap. No full gate
has been claimed from these counts.

The real bridge qualifier is now distinct from synthetic reader fixtures and
requires exact published distribution, installed tree, continuation and remote
run/artifact evidence. Only offline fixtures ran; actual delivery qualification
remains unauthorized and unexecuted. The native producer uses a separate locked
environment and receipt, and no longer duplicates six-cell-owned package gates.
Real shell tests exposed and repaired the cg-release CMD version-probe pattern.
Sdist builds use complete bundled resources. Frozen updater bytes are protected
by exact-path -text attributes without hash changes.

The unchanged Node file-symlink check was rerun: 3 passed, 1 failed with host
EPERM. No host setting, skip, replacement fixture or exception was introduced.
The source installation remains disabled. Implementation counters remain
unchanged. Next: actual canonical generation, source freeze and all eligible
offline final gates, followed by parent-owned finding tracking and handoff.

### Review Repair Cycle 1: First Frozen Gate Results

Actual canonical generation wrote 1,486 native files before the frozen gate.
The complete offline gate results are retained in
`.cg-docs/work-reports/release-controller/2026-09-12-phase6-repair1-gates.json`.
The full package passed 807/0, twice, including the exact local preflight
component. Actual prepare preflight failed in native pytest: 2,576 passed,
2 failed, 50 skipped and 2 deselected. Both failures assert the old Pages
workflow layout. Remaining selector components passed when run separately;
this does not make the full preflight pass.

Canonical Pester from the dedicated executor, ranAt 2026-09-12T15:25:19Z:
2,928 passed, 3 failed, 2 skipped, total 2,933, filteredFiles null. The failed
docs-automation assertion looks for byte-match in the former loader file.
The two docs-preview failures still expect privileged mutable-dev execution
in pages.yml. The full result was read from tests/last-run.json before any
subsequent targeted run. No Pester was run in the source thread.

Ordinary Node selection: 81 passed, 2 failed. One is the retained file-symlink
EPERM; the other is a docs validator that still requires configure-pages in
the now unprivileged builder. Canonical docs validation has the same failure.
Freshness checks identify docs/reference.md and docs/whats-new.md as stale.
Full touched-script Ruff reported 173 diagnostics; its default Python 3.10
upgrade suggestions must be reconciled with the native Python 3.8 contract,
not used to raise that minimum or suppress applicable errors.

Module validation, package lint/build/install, current-worktree generated
parity, 12 immutable payload validations, disabled installation checks and
workflow YAML checks passed. Both package runs took more than 12 minutes,
exceeding the current preflight component timeout of 600 seconds; the actual
preflight stopped earlier at native tests, so no timeout pass/failure is inferred.

These are ordinary offline integration corrections, not external V6 evidence.
Source is reopened only for a strict sequential final-gate repair batch under
the same review repair cycle 1. Prior failures and implementation counters are
retained. No Phase 6 completion or V6-only status is claimed.

### Review Repair Cycle 1: Final Frozen Handoff

Status: **source-frozen-ready-for-independent-verification**. All source children
have stopped editing. The requested compact handoff is
`.cg-docs/work-reports/release-controller/2026-09-12-phase6-repair1-evidence.json`.
The explicit Phase 6 review frontmatter now records all 34 source findings as
fixed, with a per-finding disposition/test table appended after the original
review. Original claims/probes remain intact. No finding was skipped or accepted
as an exception. Fixed means implemented and offline-checked, not independently
verified or externally delivered.

The final-gate repair batch corrected remaining obsolete workflow/loader
assertions, implemented the strict split-workflow docs validator, regenerated
stale docs/reference.md and docs/whats-new.md with the actual docs generator,
fixed applicable native Python 3.8 lint errors and gave only the full package
test command a measured, bounded 1,800-second timeout. The existing 600-second
limit remains for other preflight commands. Production release security
deadlines, test selections and the 300-line package bound remain unchanged.

After these corrections, actual canonical target generation again wrote 1,486
files. Final frozen evidence is
`.cg-docs/work-reports/release-controller/2026-09-12-phase6-repair1-final-gates.json`:

| Gate | Actual Final Result |
|---|---|
| Full prepare preflight with --format json | All nine commands passed; no timeout. |
| Full native selection | 2,585 passed, zero failed, 50 skipped, two deselected. |
| Full controller package within preflight | 807 passed, zero failed; 738.60 seconds. |
| Profile/launcher selection | 28 passed, zero failed. |
| Canonical unfiltered Pester | 2,931 passed, zero failed, two skipped; total 2,933. |
| Ordinary Node docs automation | 101 passed, one unchanged file-symlink EPERM failure. |
| Extra plan/working-tree parity | 56 passed, zero failed, eight existing POSIX-host skips. |
| Package and full touched-script lint | Passed; package py311 and all 18 scripts explicit py38. |
| Build/source-free isolated installation | Passed, including actual installed Node resources. |
| Disabled installation/YAML | Passed; 19 workflow/template documents parsed. |
| Canonical release/docs/freshness/fingerprint | Passed; 12 immutable payloads and 75 navigable pages. |
| Generated parity/dry-run and whitespace | Passed; 1,486 planned native outputs. |

The Pester parent read tests/last-run.json at ranAt 2026-09-12T16:38:16Z,
gitSha b94f585, passed true, filteredFiles null and empty failures. Only executor
ses_f6b3c8b92ffepfSp9BsF5x6KJC ran `. tests\Run-Tests.ps1`, without flags or
pipeline. All earlier failed/filtered results remain historical evidence.
Counts from overlapping selections are not added as unique tests.

The ordinary Node command still exits 1 at
scripts/tests/assemble-docs-site.test.js:154 because this host cannot create its
required file symlink. This is not a pass, skip, junction replacement or waiver.
No WSL/Docker/runtime installation, elevation or host setting change occurred.
No other ordinary source, validator or lint failure was observed in the final
frozen gate. Independent verification must still evaluate the repairs.

Step 11 remains implementation 1/2 used and resolved. Step 12 remains
implementation 2/2 used and resolved with its original final gate failed.
This review repair cycle 1 does not rewrite that accounting. Phase 6 remains
incomplete; completed-phases remains [1, 2, 3, 4, 5]. The writer and source
installation remain disabled with real authority unresolved.

The coordinator owns the next independent verification; it was not dispatched
here. Remaining required evidence includes the unchanged supported-host
file-symlink case, native Unix/real Python 3.8 execution, actual source-bound
six-cell release CI, reviewed committed-candidate preflight and genuine V6
bridge delivery/clean-client identities. Passing local synthetic bridge or
Git Bash fixtures are not those results. Actual bootstrap/settings/authority
need separate reviewed authorization. Phase 7, commits/push/PR, live release,
Pages deployment, settings/secrets/activation and historical tag/payload/
attestation rewrites were not performed. V6-only status is not claimed.

### Supplemental Bash Precision Repair And New Freeze

After the all34 repair session became idle, the main coordinator repaired a
separate, confirmed Step 11 boundary defect. POSIX awk coerced the scalar
equality comparison of adjacent large numeric identifiers to numbers. Distinct
valid values then compared equal and the newest-first list remained in the
wrong order. The independent all34 findings are unchanged; this is an additional
scoped self-review correction under the same user-authorized Phase 6 work.

Exact probe and repair evidence:
`.cg-docs/work-reports/release-controller/2026-09-12-phase6-bash-precision-probe.json`.
The new actual Bash regression cases failed first: one passed, two failed,
24 deselected. After forcing string equality as well as ordering, the complete
reader file passed 27 tests. Explicit py38 lint and whitespace validation passed.
Only `scripts/update.sh` and its existing reader test file changed as source.
No other source writer was active and no existing counter or result was reset.

Actual canonical generation then wrote all 1,486 outputs again. Source is now
frozen for final full preflight, dedicated full Pester and independent review
verification. Earlier full-gate results remain tied to their earlier freeze;
they are not silently presented as tests of this last correction. The unchanged
Node EPERM and external bridge/native-host/exact-source evidence requirements
remain explicit. No publication, activation, commit, push, PR or Phase 7 action
is authorized or performed.

### Phase 6 Verification Handoff 2026-09-12T18:34:48Z

Phase 6 is **incomplete and needs review-repair cycle 2**. It is not an
external-only V6 gate. Full10 independent verification confirmed 19 original
repairs, reopened 15, and found eight new issues: 23 active findings with
P0=1, P1=15 and P2=7. Draft P1.21 is merged into reopened P1.13 and is not
counted twice. Current severity for P1.8 is P2; P2.12 is P1. Original IDs remain.

Authoritative verification:
`.cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase6-verification.md`
and `.cg-docs/work-reports/release-controller/2026-09-12-phase6-verification-evidence.json`.
The old all34 fixed labels are historical source-repair claims, not the current
verification verdict. No finding is skipped or accepted as an exception.

After the last Bash precision repair and actual 1,486-file generation, the
main coordinator ran the complete prepare preflight: all nine commands passed,
including native 2,587 passed/50 skipped/two deselected, package 807 passed,
and profile/launchers 28 passed. Dedicated full Pester at 17:26:55Z returned
2,931 passed, zero failed and two skipped, filteredFiles null. Ordinary Node
returned 101 passed and the one unchanged file-symlink EPERM failure. Extra
plan/working-tree parity returned 56 passed/eight existing host skips. Full
18-script py38 lint, package lint/build, docs/fingerprint and disabled checks
passed. Exact final counts and critical diagnostics are in
`.cg-docs/work-reports/release-controller/2026-09-12-phase6-final-validation.json`.
These passing checks do not override the independently reproduced defects.

The numeric precision repair was verified, but the inherited suffix sentinel
also reverses nonnumeric prefix order, now P2.14. Other residual defects include
mutable dev contamination of stable output, incomplete locked environment
receipts, cross-language snapshot identity/candidate-capacity gaps, current
authority and historical Finalize gaps, bridge checkout/authentication defects,
and composition recovery/registration/performance faults. All are still eligible
offline work. Do not substitute bridge or host evidence for their repair.

Exact next-child instructions, current counters, all23 IDs and tool sessions are
in `.cg-docs/work-reports/release-controller/2026-09-12-phase6-handoff.json`.
The next child must remain under `/cg-work phase6 review:auto`, repair only the
current Phase6 findings in strict source-writer sequence, use the existing
dedicated Pester executor, regenerate and freeze before independent verification.
Step11 implementation remains 1/2; Step12 remains 2/2. Review repair cycle1 is
complete; cycle2 has not started. No source writer remains active at this handoff.
Completed phases remain [1,2,3,4,5]; the local controller configuration remains
disabled. No Phase7, commit/push/PR, live release/Pages, secret/settings/activation,
historical artifact rewrite, host elevation or unrelated revert occurred.

Handoff validation: the plan's canonical `--validate-only` and `git diff --check`
passed. Attempts to apply that renderer to the work report and verification
report returned its unsupported-root error: this installed command accepts only
brainstorms and plans. No document validation is claimed for those two attempts,
and no protected artifact was moved or rewritten to bypass the tool boundary.
The error does not change source-test counts or repair accounting. Final Agent
Manager inspection showed all implementation, Pester and review siblings idle.

### Phase 6 Review Repair Cycle 2 Started

The explicit continuation authorizes repair of all 23 current findings. Source
ownership is one writer. Step 11 implementation remains resolved at 1/2 used;
Step 12 remains resolved at 2/2 used. Review repair cycle 2 is separate and does
not reset either counter. No exception is accepted. The canonical plan passed
`cg-render-artifact --validate-only` before these writes. Previous gate results
remain historical; source is no longer frozen while this repair is active.

The first repair addresses P0.1 at the actual producer/composer boundary. Later
batches cover receipt/snapshot validation, authority and recovery, bridge and
reader portability, evidence lifecycle tests and measured journal replay.
Pester and independent review require the parent's dedicated native tasks after
canonical generation and the new freeze. No Phase 7 or remote mutation is part
of this continuation.

### Phase 6 Cycle 2 Interim Evidence, 2026-09-12 19:26 UTC

Current compact evidence and next actions are in
`.cg-docs/work-reports/release-controller/2026-09-12-phase6-repair2-progress.json`.
The exact handoff points there. The prior final-validation JSON is now explicitly
historical, not valid for the changed source. Step 11 remains resolved at 1/2;
Step 12 remains resolved at 2/2. Review repair cycle 2 is not complete.

There are 19 repair candidates, two partial repairs (P1.23 and P2.16), and two
unchanged Finalize defects (P1.10 and P1.17). Independent counts stay at 19 prior
verified findings and 23 open findings (1 P0, 15 P1, 7 P2). No new finding is
closed from targeted test success alone. The P0 candidate separates release/dev
build jobs and binds stable output bytes to separately checked producer data.

Actual pre-receipt tagged recovery cannot remove the original required hooks.
Actual admitted changed-policy recovery replaces a terminal composition without
using the revoked original actor. Real installed snapshot exporter/verifier/import
round trips pass for integer and punctuation-prefix paths. All nine merged
evidence output bytes are checked in the positive lifecycle. The detailed JSON
records narrower proof limits, including missing stranded/no-inbox and already
sealed evidence-input replacement coverage.

Current checks: broad targeted controller 69 passed; evidence/recovery lifecycle
13 passed; composition/cold-work/module bound 8 passed; reader/launcher 52 passed;
workflow contracts 26 passed; profile integration 7 passed; ordinary Node
selection 106 passed with zero skips; plan/generated parity 56 passed and eight
existing POSIX-host skips. Counts overlap. Package lint and docs checks passed.
Canonical generation wrote 1,486 files through the real generator. Disabled
workflow generation was corrected at its canonical installer after drift was
detected. No full prepare, full package, full Pester or independent verification
has run on this cycle's final source, because source repair is still incomplete.

Windows lacks SeCreateSymbolicLinkPrivilege. The scanner test now supplies only
the file-link directory-entry type at the OS boundary for exact win32/EPERM,
and still checks rejection before output. It retains real file-symlink creation
on capable hosts. This is portable scanner coverage, not a native symlink
qualification, skip, junction substitute, elevation or host-setting change.

Fresh authenticated journal measurements for 8/16/32 events are 27/51/99 provider
calls, 108/408/1,584 processed tree entries, and 37,578/105,338/332,834 decoded
bytes. Reusing the already verified operation view reduces composition append
history acquisitions from four to three. It does not remove cold quadratic tree
work. P2.16 stays open, without weakening integrity or increasing a cap.

The parent session accepted a precise native dedicated-Pester request. Run only
`. tests\Run-Tests.ps1 -File create-release`, load the safety skill first, and
read `tests/last-run.json` immediately. Four new RED cases cover historical grant
withdrawal after artifact reads, wrong default ref, skipped deploy job and failed
actual deployment. `create-release.ps1` and `scripts/release-legacy-authority.ps1`
have not yet been changed for those two findings. No Pester result was received
in this child. This is a test-executor handoff, not an authorization blocker.
After these repairs and the two partial repairs, regenerate, freeze, execute all
full gates, then request independent full10 verification. Phase 7, publication,
activation, commits, PRs and history rewrites remain outside this continuation.

### Phase6Cycle2 Candidate Freeze, 2026-09-12 20:17 UTC

All 23 findings now have repair candidates. Source and canonical outputs are
frozen for parent-owned native gates and independent verification. No new finding
is independently closed. The counts remain 19 earlier verified and 23 open
(1 P0, 15 P1, 7 P2). Step 11 remains resolved at 1/2 and Step 12 at 2/2. Review
repair cycle 2 is tracked separately and is not complete until its gates/review.

The parent supplied the dedicated Pester RED result; this child also read its
exact `tests/last-run.json`: SHA `b94f585`, 2026-09-12T19:33:05Z, filtered
`create-release`, 109 total, 105 pass, four expected failures, zero skips. The
production Finalize repairs now require the exact protected-default revision/ref,
the exact attempt's successful deploy job and Pages step, and a successful
github-pages deployment result tied to that job's repository log identity. The
historical recovery record is required again at the last guard and compared with
the original default/actor/record identity immediately before attestation. Both
PowerShell files passed parser checks; Pester GREEN is not yet claimed.

P1.23 now has an actual full no-inbox/no-preparation-PR target lifecycle. Only
immutable source Git data and an existing tag are imported from a separate
fixture; target admission, grants, builds, publication, docs, evidence and
completion use the actual controller and authenticated fixture journal. Recovery
uses its explicit reviewed protected evidence base. A separate versioned evidence
attempt preserves prior sealed evidence/PR bytes, can replay and merge, and records
reviewed recovery provenance. When evidence advances the default branch, a new
exact-controller docs deployment is correctly required. Existing audited
directives without the new optional evidence field retain their canonical digest.
Unknown external intents are not erased or silently treated as absent.

P2.16 now reads one complete head inventory and reconstructs every historical
canonical Git tree from verified event deltas. Each tree OID must match the signed
commit. Real `git mktree` parity and transient extra-file/mode/event-byte corruption
tests pass even when the final head is restored. Full history, signatures, parents,
root, event identities and final exact inventory remain checked. At 8/16/32
events, provider calls changed 27/51/99 to 20/36/68; decoded tree entries changed
108/408/1,584 to 24/48/96; decoded bytes changed 37,578/105,338/332,834 to
23,599/46,643/92,739. Incremental entry updates are 48/96/192. Flat-directory
binary hashing still consumes 9,388/33,944/128,560 bytes and is not described as
linear CPU work. No history rewrite/compaction, integrity waiver or cap increase
was used.

Additional boundary coverage now includes all three missing evidence-output
families, actual admitted-grant principal revocation after the final run read,
retry-budget-exhausted absence replay, and exact Git ancestry comparison without
opening path traversal. The remaining-repair selection passed 54 tests in 423.83s;
the final recovery/digest compatibility selection passed 30 in 88.85s. Counts
overlap and are not full-gate coverage. Package lint, format (213 files), module
bounds, disabled installation, documentation, fingerprint and whitespace checks
passed. The real adapter generator regenerated 1,486 files after repairs. No
protected release payload, historical attestation, view or activation diff exists.

Next parent task: dedicated native targeted Pester GREEN using only
`. tests\Run-Tests.ps1 -File create-release`, with an immediate compact read of
`tests/last-run.json`. After it passes, run the unfiltered dedicated Pester gate,
the full prepare gate with actual execution, ordinary Node and plan/parity gates,
then independent read-only full10 review. Exact commands and evidence are in
`2026-09-12-phase6-repair2-progress.json` and the refreshed handoff. No obsolete
peer executor handoff is active. No Phase 7, commit/push/PR, live release/Pages,
settings/secrets/activation or history rewrite was performed or authorized here.

### Phase6Cycle2 Postrepair Correction 1, 2026-09-12 20:29 UTC

The parent-owned targeted gate failed at 2026-09-12T20:24:12Z on SHA `b94f585`:
109 total, 103 passed, six failed, zero skipped, filtered `create-release`.
Exact failures remain unchanged in
`.cg-docs/work-reports/release-controller/2026-09-12-phase6-repair2-validation.json`.
Five failures reported hash-table addition; one reported a missing `id` property.
Later gates and independent verification did not run.

Both errors came from this repair's `$matches` accumulator in
`Assert-CgLegacyDeployment`. PowerShell variable names are case-insensitive.
The deployment-ID regex wrote the automatic `$Matches` hash table over the array.
Successful deployment accumulation then failed. With a failed deployment, the
single regex capture incorrectly satisfied Count=1, and indexing returned a
string without `id`. A native PowerShell probe reproduced both exact errors.

The production correction changes only four collection references to
`$successfulDeployments` and adds one explanatory comment. No validation,
authority check, fixture or test expectation was weakened or changed. The actual
helper, with only offline API substitution, now returns deployment50/job40 for
success and correctly rejects failed and duplicate deployment results. These
three direct probes are not a Pester GREEN result. Syntax, disabled-install and
docs-fingerprint checks passed; no adapter input changed or regeneration was
needed.

This is one postrepair failed targeted run and one source correction within review
repair cycle 2. Step 11 remains resolved1/2; Step 12 remains resolved2/2; the 19
earlier verified and 23 independently open findings remain unchanged. No limit or
counter was reset. The source is frozen again at 2026-09-12T20:29:38Z.

Next parent task is ONLY the dedicated targeted rerun:
`. tests\Run-Tests.ps1 -File create-release`. Load the safety skill, use no
concurrent Pester or source writes, and read `tests/last-run.json` immediately.
Return exact identity/counts/failures, preserving the failed20:24 artifact.
Later gates stay held pending targeted success. No Phase7 or remote action.

### Phase6Cycle2 Postrepair Correction 2, 2026-09-12 20:49 UTC

The parent preserved the targeted create-release GREEN at 20:33:47Z:
109/109 passed, zero failures/skips. The subsequent unfiltered full Pester gate
at 20:37:59Z reported 2,937 total, 2,933 passed, two failed and two skipped, with
`filteredFiles: null`; create-release was again 109/109. Exact evidence remains
unchanged in `2026-09-12-phase6-repair2-correction1-validation.json`, alongside
the earlier six-failure artifact. TestDrive cleanup errors and the two update
skips with unavailable individual names/reasons remain qualifications. Later
prepare/native/package/ordinary Node/parity gates and independent review did not
run after this failure.

Both failures asserted the obsolete combined release producer interface:
docs-automation searched its old upload display name, and docs-preview required
live `current-dev` checkout and assembly in the release builder. The approved
plan's GPID Documentation Provenance section (lines 431-445 and 458-462) explicitly
changes this interface: release builds use only immutable release input, dev
builds separately, and protected code composes verified static artifacts. The
independent P0.1 finding rejected the shared release/dev runner. Reintroducing
that topology to satisfy these assertions would violate the plan and repair.

This correction changes only `tests/docs-automation.Tests.ps1` and
`tests/docs-preview.Tests.ps1`, plus this workflow evidence. The payload-order
test now finds the pinned upload action and exact `release-docs-site` artifact
inside the release job, independent of its display name. The preview contracts
require distinct unprivileged jobs, one checkout each, immutable release ref,
separate named docs/metadata artifacts, no builder composition or publication
authority, and no source-script execution in the protected composer. Each exact
artifact ID/digest pair must be verified in one step before its own exact-run
download. Imports precede composition, and complete verification precedes Pages
upload. Existing legacy combined-helper tests remain intact. No test was deleted,
skipped or replaced by a success stub; the existing 24+10 test cases remain.

Both changed test files passed PowerShell syntax checks. The parsed-YAML security
selection passed four tests, and the actual stable-contamination refusal test
passed. Docs fingerprint remains current. These are scoped checks, not Pester
GREEN for the new assertions. No workflow, production helper, adapter input or
generated output was changed; no regeneration was needed.

Postrepair tracking now records one failed targeted gate, one failed full Pester
gate, one production correction and one test-contract correction, all within
review repair cycle 2. Step11 remains resolved1/2 and Step12 resolved2/2. The 19
earlier verified and 23 independently open findings are unchanged. No counter or
limit was reset. Source/tests are frozen again at 2026-09-12T20:49:39Z.

Next parent task: one dedicated native executor with the Pester safety skill,
running `. tests\Run-Tests.ps1 -File docs-automation,docs-preview`; immediately
read `tests/last-run.json` and preserve exact identity/counts/failures in distinct
evidence. After targeted success, rerun the unfiltered full Pester gate and retain
cleanup/skip qualifications. Only after full success proceed to the later gates
and independent full10 verification. No Phase7 or remote action.

### Phase6Cycle2 Postrepair Correction 3, 2026-09-12 21:45 UTC

The parent artifact `2026-09-12-phase6-repair2-correction2-validation-205721Z.json`
is preserved unchanged. Docs targeted Pester passed34/34. Full Pester at21:00:58Z
reported2,937 total,2,935 passed,0 failed,2 skipped,`filteredFiles:null`, with
cleanup errors and incomplete individual skip identity still qualified. Native
tests passed2,592 with50 skips and2 deselected; three module checks passed.
Ordinary Node passed106 without skips using the documented portable file-link
boundary. Plan/parity passed56 with8 platform skips. Counts overlap.

Full prepare selected9 commands but executed6:5 passed and the locked package
selection failed; the profile/launcher tests, package lint and build did not run.
Fourteen setup-error markers were visible, but preflight truncated output before
the final package summary. Exact package pass/fail/skip totals remain unknown;
no count is inferred from those markers.

The exact qualifier fixture error was reproduced with both ambient token variables
removed in an isolated test process. The production client correctly required a
credential before the fixture could redirect its approved HTTPS clone to local
Git. This was a missing unit-fixture input, not a reason to relax production
credential checks or obtain a real credential.

Only `test_bridge_qualification.py` and `test_bridge_client_roundtrip.py` changed.
The qualifier fixture supplies a clearly fake token inside a scoped MonkeyPatch
context and the synthetic Actions identity. At the real subprocess boundary it
asserts the exact repository-scoped Git HTTP header, disabled redirects and no
credential in argv or raw child GH/GITHUB variables, then rewrites only the
approved clone to local Git. Real subprocesses and updater descendants allow
only Git file transport; stray URL argv is rejected. The receipt must not contain
the fake credential or header. No verifier, helper, installed-byte check or
qualification result is replaced by a success stub.

Additional boundary cases cover both supported token variable names, missing,
empty and malformed credentials rejected before subprocess, unapproved
repository/host/path rejected before subprocess, and redaction of raw/encoded
credentials from process failures. The final locked offline two-file selection
passed25 tests in58.65s with both ambient token variables removed before pytest.
Package lint and formatting (213 files) passed. Docs fingerprint remains current.
This is local fixture evidence, not live bridge delivery, actual token-permission
proof, native opposite-host evidence or an OS network-sandbox claim.

Postrepair tracking records three corrections within review repair cycle2:
one production correction, one contract-test correction and one fixture
correction. The package failure is nested in the single failed prepare run.
Step11 remains resolved1/2,Step12 resolved2/2, and independent counts stay19
previously verified/23 open. No counter reset or new finding closure.

Candidates are frozen again at21:45:37Z. Request a complete parent-owned gate
rerun: full prepare with all selected commands executed, dedicated unfiltered
Pester, ordinary Node and plan/parity. No real or gate-level fake credentials
are needed; the fake is scoped inside the test fixture only. Preserve distinct
evidence and recover a complete package summary or JUnit report if preflight
truncates again. Independent full10 verification follows complete gate success.
No Phase7, publication, activation, commit/push/PR or history rewrite.

### Phase6 P1.15 Residual Repair, 2026-09-12 23:13 UTC

The completed full10 independent report is
`.cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase6-repair2-verification.md`.
It confirms22 of23 repair candidates, preserves the19 earlier confirmations and
leaves only existing P1.15 open:41 confirmed,1 open (P0=0,P1=1,P2=0,P3=0), no new
IDs. The report and all previous findings/evidence remain unchanged. These are
independent confirmations, not self-assessed test closures.

The correction3 full validation at22:28:29Z is also preserved:9 selected/executed/
passed prepare commands;853 package tests passed; native2,592 passed/50 skipped/
2 deselected; profile/launcher28 passed; full Pester2,935 passed/0 failed/2 skipped
with `filteredFiles:null`; Node106 passed and parity56 passed/8 skipped. Package
summary and streams are complete. Pester cleanup errors and skip/host/source
identity qualifications remain. These gates predate the residual source edit.

P1.15 was repaired inside the worker but remained at the connected workflow
boundary: two remote freshness reads followed `authorize-deploy`. The minimal
canonical correction keeps the local manifest, current-dev and stable-tag checks,
then invokes the real authorization operation as the final command immediately
before `actions/deploy-pages`. Explicit strict Bash error handling is retained
at that last step. The worker implementation and protected environment/authority
guards are unchanged. `packages/cg-release/templates/gpid-docs.yml` was edited;
`scripts/release_profile_install.py` regenerated the installed workflow. The
disabled installation check passed before editing and after generation.

The new connected regression reads both the template and generated workflow,
registers against the real Journal, and replays the exact final statement order.
Outer fake GETs revoke requester456 or resumer8 during either freshness read but
return matching SHA/tag values. It invokes real `authorize_deployment`; it does
not replace verification with a success result. The composition is seeded as in
the existing gate fixture, local manifest bytes are hashed, unknown statements
fail, and journal bytes stay unchanged. It also rejects authorization-step
continue-on-error and non-success deployment conditions. This is a bounded
command-order model, not complete Bash or live Pages execution.

Before the repair the selection produced11 failures/3 passes: eight revocations
were not rejected, two positive cases exposed trailing reads, and the native
structure check found authorization not last. After generation, the new cases
plus adjacent security/profile/module gates passed34 tests in3.66s. Package lint,
format (214 files), disabled parity, docs/fingerprint and whitespace checks passed.
Detailed compact evidence is in `2026-09-12-phase6-P1.15-repair.json`.

Existing implementation/review counter accounting is retained: Step11 resolved1/2,
Step12 resolved2/2 and current review-repair cycle2. This authorized post-verification
residual repair is recorded separately, without a reset or another finding ID.
Source is frozen at23:13:59Z; P1.15 remains open pending final gates and a separate
scoped independent verification that also preserves the41 prior confirmations.
The parent owns those native tasks. No Phase7, live deployment, publication,
activation, secret/settings change, commit/push/PR or history rewrite.

### Phase6 P1.15 Shared Helper Repair, 2026-09-13 00:50 UTC

The scoped report `2026-09-13-generic-asynchronous-release-controller-phase6-P1.15-final-verification.md`
is preserved unchanged. It confirms the workflow ordering but reproduces eight
final-helper counterexamples: repository/default reads followed human permission
checks. Its negative controls and41 earlier confirmations remain evidence.
P1.15 is still the same one open finding; no ID is added and no closure claimed.

The last complete gates are also retained in `2026-09-12-phase6-P1.15-validation-233019Z.json`:
prepare9/9, package863 passed, native2592/50skip/2deselected, profile/launcher28,
Pester2935/0fail/2skip with filteredFiles=null at23:30:19Z, Node106 and parity56/8skip.
Those results precede this helper change. Cleanup, skip identity, platform and
uncommitted-source qualifications remain.

The real shared `authorize_hooks` helper now finishes repository/default identity,
protection and SHA checks before its final `authorize_record` call. The latter
retains ordinary requester/resumer and exact admitted-recovery checks. Its
`fresh=False` behavior remains. Caller inspection found the same avoidable ordering
at composition ticket reads and the evidence base read; those now precede final
authority. Dispatch retains its pre-intent check and rechecks after durable intent
before the POST. An intent already recorded is preserved if authority is then lost.
The correct canonical/generated workflow order is not changed or regenerated.

Checks remain sequential observations, not an atomic snapshot or permission lease.
Separate principal identity/permission calls, journal CAS operations and later
GitHub effects cannot be made atomic by this helper. No guarantee is claimed
against a change after its last observation or while another principal is checked.
The correction removes avoidable post-authority reads at the audited boundaries.

Regression coverage extends the existing workflow replay with both final-helper
metadata delays and principals across both source copies, plus registration and
actual admitted recovery. Caller boundary cases cover intent-to-dispatch, both
composition effects and evidence intent. Exact policy guards and optional
freshness are preserved. Initial adjacent probes used actor constants from a
different fixture; they were corrected to derive actual bound principals before
the authoritative pre-edit RED run. That run reported25 failures/9 passes. Only
that corrected run is used as the combined RED evidence.

After the production correction, the two boundary modules passed34 tests. The
broader affected-path selection passed75 in510.32s, including existing security,
policy/recovery, dispatch, evidence, stranded-lifecycle and module-bound tests.
Workflow memory cases block process/socket use; larger lifecycle fixtures use
local Git/Node and fake provider I/O, not live remotes. These are not full Bash or
Pages qualification tests. Package lint, formatting (215 files), disabled-install,
docs/fingerprint and preserved history/activation checks passed. No generated
input changed. Exact compact evidence is `2026-09-13-phase6-P1.15-helper-repair.json`.

Source is frozen at2026-09-13T00:50:17Z. Step11 remains resolved1/2,Step12
resolved2/2 and current review-repair cycle2 accounting is retained. This is the
second authorized post-verification repair of existingP1.15, not a counter reset
or new finding. Counts remain41 confirmed/1 open.

Parent tasks: rerun full prepare with actual selected-command execution, dedicated
unfiltered Pester, ordinary Node and plan/parity, preserving complete summaries
and all qualifications. Then obtain separate scoped independent verification of
the shared-helper and affected call boundaries while preserving both old reports
and41 confirmations. No live remotes/credentials, deployment, publication,
settings/activation, commit/push/PR, history rewrite or Phase7.

### Phase6 P1.15 Continuation Audit, 2026-09-13 03:51 UTC

The latest helper-verification report is preserved unchanged:41 confirmed and
existingP1.15 open at pending dispatch reconciliation followed by registration.
The prior accepted gates remain9/9,891-package and2935-Pester assertions, with
their original cleanup/skip/platform qualifications. No new finding ID or closure.

The finite audit is recorded operation by operation in
`2026-09-13-phase6-P1.15-continuations-repair.json.audit`. It covers registration,
dispatch/absence recovery, namespace/checkpoint/composition creation, evidence
inputs/PR/binding and existing-PR continuation, owner release and hook completion,
required-hook sealing, native-source registration, and reviewed recovery audits.
Read-only and already guarded branches are classified separately. This is not a
future-feature or generic publication architecture expansion.

The reported registration branch now repeats authority after dispatch-result save.
Other separate operations receive explicit checks or a real before_write callback
on the existing checkpoint helper. Phase6 callers renew authority before both
intent and result. Owner release checks after state reads; native registration
checks after run/reconciliation/current-ticket reads; recovery audits check after
history acquisition before append attempts. Ten callback call sites have a wiring
regression in addition to actual runtime negative and authorized-positive cases.
No guard, schema, CAS bound, immutable ticket/grant or preserved history was relaxed.

The correction retains completed authorized prefixes and unresolved intents when
the next operation is denied. Identity/permission calls for separate principals,
one already-started CAS/read-back operation and later provider effects remain
non-atomic. No permission lease or endless check loop is claimed.

Pre-edit tests reproduced8 composition/registration continuation failures with4
controls;16 evidence/namespace/completion failures with8 passes;6 native/recovery
failures with6 controls. Three early owner-fixture setup errors are not product
evidence. The owner fixture was corrected using the existing publisher checkpoint
fault seam, a terminal run and actual credential-expiry evidence. The complete
continuation matrix, callback wiring and module checks then passed62 in301.73s.

A full locked package run completed and is retained unchanged as
`2026-09-13-phase6-P1.15-continuations-package.xml`:952 total,951 passed,1 failed
in1338.65s. The failing inventory-only test fixture had a disabled/mismatched
policy and lacked authority metadata responses. Its request/sealed inputs and
registration digest were bound to an enabled fixture policy; exact numeric-user,
permission/default/run responses were supplied. Production checks were not weakened.
After correcting the fixture adapters, its test passed and the final fixture/
registration/wiring/module selection passed24 in1.76s. This is not a replacement
for the failed full-run artifact: a complete passing rerun is still required.

Lint/format (220 files), module bounds, disabled installation, docs/fingerprint
and unchanged protected publication/activation checks passed. Workflows and
adapter inputs were unchanged, so no regeneration was needed. Tests use real
controller/journal paths with outer local provider/storage substitution, not live
remotes or Pages execution. Inventory-only fixture isolation is not authority proof.

Source is frozen at03:51:37Z. Step11 resolved1/2,Step12 resolved2/2 and current
review-repair cycle2 accounting remain. This third authorized residual repair is
tracked separately; no counter or limit was reset.

Parent handoff: rerun full prepare with all selected commands executed, dedicated
unfiltered Pester, ordinary Node and plan/parity. Preserve the failed package XML
and write distinct complete new evidence. Then independently verify every audit
row, including exact prefix retention and positive controls, rather than only the
reported registration branch. Preserve41 confirmations and all prior reports.
No remotes/credentials, publication/deployment, settings/activation, commit/push/PR,
history rewrite or Phase7.

### Phase 6 Final Evidence Assessment, 2026-09-13 05:36 UTC

**Definitive outcome: blocked by required V6 evidence, not by local code or review.**
The selected canonical plan passed validation before this reporting/checkpoint
operation. No production source, workflow, plan body, roadmap, remote, credential,
setting or activation was changed. The new final evidence record is
`2026-09-13-phase6-final-evidence.json`.

The final independent continuations report confirms all15 audit rows, P1.15 fixed
and all41 prior confirmations preserved:42 independently fixed,0 open,0 unverified,
no new IDs. Fresh independent checks passed62 matrix cases,78 adversarial/control
cases and94 adjacent security cases. This closes review-repair cycle2; original
Step11 functional repair use1/2 and Step12 use2/2 remain resolved and are not reset.
The three authorized post-verification repairs and all failed-gate artifacts are
retained. No evidence exception was requested, granted or inferred.

The latest complete local gates are retained in
`2026-09-13-phase6-P1.15-continuations-040753Z-validation.json`: prepare9/9 actual
commands,952 package tests,2592 native tests (50 skipped,2 deselected),28 profile/
launcher tests, module/lint/build passes,2935 Pester assertions (0 failed,2 skipped,
unfiltered),106 Node tests and56 plan/parity tests (8 skipped). Counts overlap.
Pester cleanup errors, unavailable individual skip identities, native-host and
portable file-link qualifications remain. These passes are not a live bridge,
registered remote matrix, committed-candidate or deployment result.

| Evidence | Current Result | Completion Consequence |
|---|---|---|
| V1-V5 | Previously accepted and checkpointed; preserved | No prior phase reset |
| V6 local reader/profile/target and required-hook/CI enforcement tests | Passed with the recorded scope limits | Local implementation/review work is complete |
| V6 authorized bridge delivery and native clean-client qualification | Not recorded | Phase6 completion is blocked |
| V6 registered exact-source release-mode producer/run tuple | Enforcement tests pass; real tuple not recorded | Record qualified source evidence under reviewed target/setup authority |
| V7/V8 | Not started as part of this scope | No Phase7, timing/sandbox, rollout documentation or committed final gate performed |

The decisive clause is plan step11 line673: ship reader changes through an already
accepted legacy-format channel with separate maintainer authorization, record the
bridge tag/Release ID/trusted revision, and verify old updater -> bridge -> new pin
on clean Windows and Unix. Line676 explicitly says delivery must be verified, not
just merged locally, and absent remote bridge authorization means V6 blocked before
writer cutover. Required rowV6 at826 and blocked-stop863 make this a phase gate.
These are Phase6 clauses, not a Phase7 requirement brought forward.

The local evidence inventory contains no accepted actual bridge delivery or native
Windows/Unix qualification record. Earlier reader/integration reports explicitly
exclude those claims. Current `.release-controller.json` remains disabled with
`profile.bridge:null`, unresolved repository/producer/controller/App/journal
identities and empty bootstrap. Its disabled-install check passed. This source
example is not remote policy or authorization; no unqueried remote is declared
absent. Existing valid external evidence may be supplied for verification instead
of repeating a release, if it satisfies the exact contract.

Required bridge evidence is the actual published legacy-compatible distribution
identity and reviewed authorization, followed by native Windows and Unix old-client
qualification against delivered bytes. The implementation contract specifies
previous/bridge/successor tag, Release ID, commit/tree/tag-object identities and
separate trusted workflow run/attempt/job/artifact IDs, archive digests and complete
qualification receipts. Synthetic fixtures or Git Bash emulation are not delivery.

Step12 line684 and V6 also require registered source-bound release-mode CI, whose
accepted tuple is specified at plan131-140. The required-check app IDs and actual
run tuple are not recorded. Local package tests prove enforcement, not six remote
cells and their aggregate. Record the qualified workflow/controller revision,
sealed request/source/nonce, actual run/attempt, all six cell job outcomes, Ruff,
aggregate and native/profile producer evidence under separately reviewed setup.
Phase7 special sandbox/final-SHA/security trials, performance samples and V8's
committed candidate are still later work and are not additional Phase6 blockers.

| Constraint | Reporting Assessment |
|---|---|
| C1/C5 immutable release identities/history | Local historical payload and attestation diff is empty; no remote writes or rewrite performed |
| C2/C3 trust/branch/approval separation | Executed offline gates and independent reviews pass; no live protection/approval proof invented |
| C4 no silent version change | Covered by accepted local protocol/reader tests; no new version decision or release executed |
| C6 safe Pester | Dedicated isolated foreground runner and immediate unfiltered artifact capture retained; cleanup qualifications not hidden |

The strict evidence gate therefore forbids appending6 to completed-phases or
advancing current-phase. The plan remains active with completed-phases[1,2,3,4,5]
and current-phase6. The reporting sequence writes durable final evidence and this
report first, then the compact blocked active-state snapshot/current pointer, and
rechecks both. This is a crash-safe blocked checkpoint, not a Phase6 success or
permission to start Phase7.

Resume only to consume/prove the authorized V6 bridge and qualified source evidence,
using the same Phase6 command. Do not rerun closed source repairs, invent IDs, enable
the new publisher, execute remote operations without separate authority, or waive
required evidence. Final status for this invocation is `blocked`.

Read-back verification completed: the blocked snapshot and current active-state
pointer reference the durable final evidence; the plan remains active with
completed-phases[1,2,3,4,5] and current-phase6. Canonical plan validation passed
again, and whitespace checks passed with existing LF/CRLF advisories only.

## Accepted Deferral 2026-09-13T13:36:27Z

Decision ID: `D-2026-09-13-defer-live-rollout`. Active policy remains `ask`, with
no runtime override. This explicit user decision supersedes the 05:36 UTC blocked
handoff for current local-delivery acceptance; it does not erase that evidence
assessment, its missing evidence, or any original requirement.

### User Approval

The user supplied the consequential answer **Defer Live Rollout** and approved:

> Explicitly revise acceptance to finish local implementation, documentation,
> reviews and the PR. Record bridge delivery, live CI, sandbox trials and
> performance proof as deferred, not passed. Keep the publisher disabled.

The same 2026-09-13T13:36:27Z instruction explicitly authorizes the V6/V7/V8 and
phase-scope revision, Phase 6 finalization under the accepted deferral, and the
crash-safe report/metadata/current-state update. It prohibits Phase 7 execution
here, implementation, activation, remotes, and commits. Ordinary PR CI remains
required; the committed gate stays after the planned pipeline step 11 commit is
authorized. That pipeline step is distinct from plan Step 11 (reader migration).
The approved local continuation needs no repeat scope question.

### Accepted Exceptions

| Evidence ID | Missing Evidence and Reason | Accepted Disposition and Remaining Obligation |
|---|---|---|
| V6 | No accepted published bridge identity, actual Windows/native Unix clean-client qualification, or real registered release-mode producer/run tuple is recorded. They need separate target/setup/delivery authority; this continuation permits no remote work. | Explicitly accept the live-evidence gap for Phase 6 local completion. Preserve passing local implementation/review evidence. Defer live delivery/qualification, do not mark it passed, and keep the publisher disabled. |
| V7 | Authorized generic/GPID live trials, native-host checks, non-integration final-SHA CI proof, security/approval probes, remote identities, and ten-sample live timing/legacy comparison are not recorded. No sandbox/setup authority or live evidence is supplied. | Defer these exact Step 13 live obligations. Phase 7 still owns remaining local implementation, offline harness checks, and tested rollout documentation. Phase 7 is not started or completed here; no performance claim is accepted. |
| V8 live component | Actual source-bound six-cell release-mode CI and aggregate remain absent with the deferred V6/V7 rollout evidence. Local checks cannot establish those identities. | Defer release-mode live CI to rollout. Preserve all required local regression, build/install, safe Pester, parity, documentation, and review gates; ordinary PR CI is not part of this deferral. |
| V8 pipeline timing | The candidate is uncommitted and the planned pipeline step 11 commit is not yet authorized. No committed preflight or ordinary PR CI result exists in this handoff. | Accept local phase checkpoint timing before that pipeline step, not a waiver of either gate. Leave V8 and whole-plan/final pipeline acceptance pending until the authorized candidate passes committed preflight and the PR passes ordinary required CI, including its six-cell package matrix and aggregate. Never move the commit earlier or label prepare as committed evidence. |

This is the explicit exception path in goal-execution / Accepted Exceptions and
Strict Evidence Gate, and `/cg-work` Step 2.5. It lowers no other required gate,
review priority, immutable-object rule, credential boundary, or runtime enablement
requirement. Historical review findings remain fixed by their independent evidence,
not by this exception. Recovery counters are not reset.

### Exact Deferred Obligations

1. Deliver the reviewed bridge through an accepted legacy-format channel. Retain the published legacy tag/Release ID, trusted revision, commit/tree/tag-object and previous/bridge/successor distribution identities, archive digests, producer/run/attempt/job/artifact IDs, and actual clean Windows and native Unix old updater -> delivered bridge -> new-format pin qualification receipts bound to delivered bytes.
2. Under reviewed setup authority, bind real repository/producer/controller identities and retain the sealed request/source SHA/nonce, workflow revision, actual release-mode run/attempt, all six Python 3.11/3.12 Windows/Linux/macOS jobs, Ruff, successful aggregate, and native/profile evidence. Include the non-integration-branch merged/squashed final-SHA scenario. Ordinary PR CI is still a current pipeline requirement.
3. Run the complete authorized generic and GPID Step 13 sandbox matrix: protected settings/App cross-role denial and hostile-source probes; approval visibility and independent reviewers; signing; exact tag/assets/latest identity; concurrency/dropped wakeup/lost response and second-machine recovery; expired evidence/journal restore; branch advancement; mutable-dev composition; failed post-hook and convergent resume. Retain exact argv, exits, remote identities, and authorization records.
4. Collect at least ten sequential warm-dependency start samples, excluding only confirmation wait, with min/median/p95, all failures, environment/history size, p95 <=120 seconds, and separate queue/review/approval/build/publication/recovery intervals. Compare the applicable legacy workload when available. Missing baseline is not zero; no measured live speedup or handoff success is claimed.

### Phase 6 Evidence

These are retained executed results read during this reporting operation, not
rerun suites. Gate and review paths remain unchanged:

- Local gates: `.cg-docs/work-reports/release-controller/2026-09-13-phase6-P1.15-continuations-040753Z-validation.json`.
- Independent review: `.cg-docs/reviews/2026-09-13-generic-asynchronous-release-controller-phase6-P1.15-continuations-verification.md`.
- Historical blocked assessment: `.cg-docs/work-reports/release-controller/2026-09-13-phase6-final-evidence.json`.
- Historical blocked checkpoint: `.cg-docs/active-state/2026-09-13-release-controller-phase6-V6-blocked.json`.

| Evidence | Result | Qualification |
|---|---|---|
| V1-V5 | Previously accepted, preserved | Not rerun for this reporting operation |
| V6 independent review | 42 fixed, 0 open, 0 new, 0 unverified; all 15 finite audit rows confirmed | Source/fixture verification, not atomic multi-API permission or live deployment proof |
| V6 prepare | 9 selected, 9 executed, 9 passed, 0 failed | Uncommitted prepare gate only |
| Package / native / profile | 952 package passed; 2592 native passed, 50 skipped, 2 deselected; 28 profile/launcher passed | Counts overlap; host and selection limits retained |
| Safe Pester | 2935 passed, 0 failed, 2 skipped; total 2937; filteredFiles null; 21 files | Cleanup errors remain; both update skip names/reasons are absent; Windows Bash placeholder is not native Unix proof |
| Node / parity / modules / build | 106 Node passed; 56 parity passed, 8 skipped; three module checks, Ruff, wheel/sdist passed | Portable file-link EPERM boundary is not native Windows symlink proof; POSIX skip groups remain |
| V6 live components | Deferred under the explicit accepted exception | Not passed; no remote existence or absence inferred |
| V7 | Local phase not started; live components deferred | Documentation, offline harness checks, and live timing results are not claimed complete |
| V8 | Pending local/final pipeline work; live component deferred | Ordinary PR CI and later authorized committed gate remain required |

The declared source freeze remains 2026-09-13T03:51:37Z and HEAD remains
`b94f585c8a485dfb03965ca9711fb83257aaa7de`. This declaration and unchanged HEAD
are not a cryptographic identity of dirty contents. No implementation or test
source is changed by this operation. No independent review is rerun or invented.

### Constraints and Reporting Checks

| Constraint | Current Assessment |
|---|---|
| C1/C5 | Historical payload/attestation diff check executed with exit 0; no remote mutation. Actual bridge/native-client proof stays deferred. |
| C2/C3 | Local tests/review retained. Live source-secret, App/ruleset, and approval proof stays deferred. No trust control or stable-override rule is changed. |
| C4 | Accepted local protocol/version checks retained; no new version selection or release performed. |
| C6 | Prior dedicated safe unfiltered Pester evidence retained with its qualifications. No Pester command run by this reporting session. |

Canonical plan validation passed before edits. The first post-edit validation
rejected a renamed Step 14 Tests metadata label; the label was corrected and the
same validator passed. This documentation-format correction is not a functional
recovery attempt. The expected HTML view is absent; no view rendering was requested
or performed. Disabled installation check
`packages/cg-release/.venv/Scripts/python.exe -B scripts/release_profile_install.py --check`
passed. `.release-controller.json` still has `enabled: false` and unresolved setup
identities; no source policy or workflow was edited.

`open-brain` is unavailable. The bounded local Brain query selected the historical
Phase 6 verification report and reported 616 index warnings. The later canonical
continuations review was read and takes precedence over that old open-finding
snapshot. No old failed report is deleted or relabeled as a new success.

Step 11 functional repair use 1/2 and Step 12 use 2/2 remain resolved; two review
repair cycles and three post-verification residual repairs remain recorded. No
new functional attempt, budget reset, or finding closure is attributed to this
scope decision.

### Completion Checkpoint

Phase 6 final status: **completed, Success-under-deferral**. The approved decision
and evidence were written first. Then `completed-phases: [1, 2, 3, 4, 5, 6]` was
written and re-read while `current-phase` was still 6. Only after that verification
was `current-phase: 7` written and re-read. `status: active` is unchanged; no
whole-plan completion date was added. This is a local Phase 6 completion under an
accepted evidence exception, not a live V6 pass or whole-plan completion.

The new evidence and current active-state pointer record the 2026-09-13T13:45:17Z
handoff. Phase 7 remains unstarted and is the parent's next handoff only:
`/cg-work phase7 review:auto .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`.
No Phase 7 step, implementation, remote, commit, push, PR, publisher activation,
roadmap write, or historical-evidence overwrite was performed.

New decision evidence:
`.cg-docs/work-reports/release-controller/2026-09-13-phase6-accepted-deferral.json`.

Final read-back confirms the plan's ordered phase writes and current pointer's
`handoff` state: V6 Success-under-deferral, V7 unstarted, V8 pending, no unresolved
scope decision, and the parent-only Phase 7 next command. Plan validation, both
JSON syntax validations, and whitespace checks for all four changed artifacts
passed. No full regression or Pester rerun was needed for this reporting-only
change; the exact prior executed gates and their limits remain the evidence.

## Phase 7 Start 2026-09-13T13:48:51Z

Authorized command: `/cg-work phase7 review:auto .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`.
Only Steps 13-14 local work and embedded review are in scope. Active deviation
policy is `ask`. Decision `D-2026-09-13-defer-live-rollout` remains authoritative:
the publisher stays disabled; V6/V7 live proof and release-mode CI are deferred,
not passed. V8 remains pending for the later authorized pipeline step 11 committed
gate and ordinary PR CI. No early commit or later pipeline command is permitted.

The canonical plan validator passed before mutation. Loaded project instructions,
amended plan, context/goal/active-state/artifact/release/review contracts, Python,
Pester safety and Brain-query skills. `open-brain` is not available. The bounded
Brain query succeeded with 616 index warnings; canonical Markdown authority and
the amended release contract take precedence over historical timing clauses.

Step 13 adds offline sandbox planning and measurement-summary validation without
a remote execution path. Step 14 documents installation, trusted setup, migration,
recovery, and deferred trial procedures. Existing CLI, timing, install, recovery,
profile and workflow tests form the test index; new behavior gets red/green tests.
Canonical outputs must be generated before review. The parent was asked for the
exact dedicated test/Pester/review handoff; no new managed session was created.

Prior counters remain unchanged: Step 11 used 1/2, Step 12 used 2/2, two review
repair cycles and three residual repairs. New Steps 13 and 14 start with zero
functional repair attempts; this does not reset any prior counter. Phase 7 local
tests, fresh full Pester, and embedded full-route review are not yet complete.

## Phase 7 Local Implementation Handoff 2026-09-13T14:16:14Z

Steps 13-14 local code, tests and documentation are implemented. Phase 7 is not
complete: the unfiltered package run timed out, fresh dedicated Pester and the
embedded full review remain pending. No live-evidence approval is needed again;
this is a local test/review handoff, not a live authorization blocker.

### Implemented Scope

- Added strict offline `trials.py` models, target-ID matching, deferred scenario
  checklists and supplied-measurement arithmetic. This narrow companion module
  keeps benchmark transport/timing separate from schema/statistics responsibilities.
- `scripts/benchmark_release.py` retains its three-call local Git default and adds
  `--sandbox-config`, `--repository-id` and `--measurements` for offline planning
  only. It does not discover origin, verify authority, run live trials or activate
  workflows. Supplied measurements always have `live_handoff_passed: false`.
- Samples retain all failures/outages, exclude only confirmation, report nearest-rank
  p95/min/median and separate intervals, and cannot turn missing legacy data into
  zero or a speedup. Unknown schemas/fields, duplicate keys, invalid durations,
  mismatched identities and oversized JSON fail.
- Added package README and public operator guide. Updated all listed guides plus
  the required navigation entry. Tested the four-command syntax, generic fixture
  preview, disabled copied template and site links. Documented setup pins/Apps,
  approval, lines/projections, journal backup/recovery, immutable objects, bridge
  ordering and complete deferred rollout scenarios. No unattended live sandbox
  driver or hidden opt-in pytest execution is claimed.

### Executed Checks

| Check | Result | Qualification |
|---|---|---|
| Step 13 red | 27 expected failures | Functions/options not yet implemented |
| Initial green / repair | 2 failed, 9 passed, 33 setup errors; then 44 passed | Repaired one wrong import using existing strict JSON decoder; Step 13 uses 1/2 functional repairs |
| Step 14 red / targeted combined green | 5 expected missing-doc failures; then 49 passed | Four-command syntax and fixture execution, not live operation |
| Complete package | Incomplete at 600-second tool timeout, last progress 51% | No final counts or pass; dedicated supervised rerun required |
| Build/install smoke | 13 passed | Actual sdist/wheel build, locked source-free install and installed profile; this host only |
| Node affected docs suite | 106 passed, 0 failed, 0 skipped | Windows EPERM portable file-link boundary, not native file-symlink qualification |
| Target byte drift tests | 19 passed | Separate from generator dry-run enumeration |
| Ruff / modules | Passed | New-file formatting repaired diagnostics; editor get_errors unavailable |
| Canonical generation | `rebuild-docs --all` and `cg_generate_targets --all` passed | 1486 native outputs; generation finished before review handoff |
| Docs freshness/site | Passed; 76 pages, 8 groups | All required public routes and links validated |
| Release set/historical diff | Passed; 12 immutable payloads; no historical diff | No remote existence/absence or publication inferred |
| Disabled installation | `release_profile_install.py --check` passed | Publisher remains disabled |
| Offline benchmark/trial checklist | Executed and captured | 3 local Git calls, 1 local gate, 0 remote writes; all remote intervals missing; synthetic target only |
| Fresh Pester / embedded review | Not executed here | Parent-dispatched dedicated siblings remain required |

Exact argv, exits, critical logs, scope files and counters are in
`.cg-docs/work-reports/release-controller/2026-09-13-phase7-implementation-evidence.json`.
Baseline and checklist outputs are the adjacent `2026-09-13-phase7-offline-*.json`
files. These outputs do not count as live performance or trial evidence.

### Review and Counter Boundary

Mechanical self-review found no added debug code, unresolved TODO or missing
imports after the correction. This is not the embedded independent review.
`review:auto` resolves to **full** because release automation, installation,
authority/recovery instructions and schema boundaries are security-risk triggers.
All ten required specs belong in the review sibling; it must not run the later
pipeline `/cg-review mode:verify`. Review findings are unknown, not zero.

Prior Step 11 1/2, Step 12 2/2, two review cycles and three residual repairs remain
unchanged. Step 13 uses 1/2 functional repairs; Step 14 uses 0/2. There are zero
Phase 7 review repair cycles. The package command timeout is an incomplete test
run, not a newly diagnosed assertion defect or an accepted final-gate exception.

### Exact Parent Handoff

1. Freeze writers. Dispatch the dedicated ordinary test sibling for complete package and required affected regression gates. Use a bounded supervisor with sufficient time and retained logs; the package run exceeded 600 seconds here. Return exact argv/exit, counts, skips and critical logs, not full output. Do not use a committed preflight or make an early commit.
2. Dispatch the dedicated Pester sibling after loading `cg-skill-pester-safety`: `. tests\Run-Tests.ps1`, no flags or pipeline. Read the fresh `tests/last-run.json` and return `passed`, `failedCount`, `failures`, `filteredFiles`, timestamp and counts/skip/cleanup qualifications. No cleanup of old fixture roots is authorized in this Phase 7 handoff.
3. After passing local gates, dispatch only embedded Phase 7 full review using `cg-code-quality`, `cg-testing`, `cg-documentation`, `cg-version-control`, `cg-reproducibility`, `cg-performance`, `cg-architecture`, `cg-data-quality`, `cg-learnings-researcher` and `cg-adversarial`. Read the amended scope and new evidence; review the listed Phase 7 files and relevant integration contracts. Preserve closed Phase 6 findings, historical evidence and all protected assets. Write a new Phase 7 review artifact; return actionable findings with P0/P1 strength. Do not start pipeline step 8 or another later command.
4. Return ordinary defects for authorized repairs and refreshed checks. Only after local gates and embedded review close may Phase 7 completion metadata be written in crash-safe order. Keep whole-plan status active and V8 pending for the later committed gate and ordinary PR CI.

Resume is the same exact Phase 7 command. No new Agent Manager session, Pester
execution, remote operation, publisher activation, commit/push/PR, roadmap change,
historical-evidence rewrite or later pipeline command occurred here. The parent
received targeted requests for dedicated sibling handoff; no sibling IDs or return
evidence arrived before this checkpoint.

Model advisory, implementation-to-review: use strong independent critical review
capability with high effort; a smaller code-capable reviewer can assist bounded
docs checks but cannot replace the required full route. This is advice only;
availability varies and the user controls model/effort selection. No switch made.

## Phase 7 Review Repair 1 2026-09-13T15:45:19Z

The 15:41:06Z user continuation authorized both P2 repairs and independent
verification, with no later pipeline steps and no unnecessary 22-minute rerun.
Read the actual `2026-09-13-phase7-1425Z-validation.json`: all 12 gates passed,
package 984 passed in 1338.30s (1320.33s again within prepare), full Pester 2935
passed/0 failed/2 skipped, unfiltered. The measured full runtime explains the old
600-second timeout. Those full records and their raw logs remain unchanged;
counts overlap and host/skip/cleanup limitations remain in effect.

Read the new full ten-spec Phase 7 review: P0=0, P1=0, P2=2, P3=0. Its P2.1 and
P2.2 evidence is retained, not rewritten as a clean original review.

### Repairs and Tests

- P2.1: replace the overflowing even median sum with the ordered nonnegative
  midpoint `lower + (upper - lower) / 2`; odd samples remain unchanged. Require
  a finite median before returning. Regression cases cover `1e308`, maximum
  finite doubles, unequal large values, odd count and the minimum subnormal.
  The full summary must serialize with `allow_nan=False`; a real CLI test writes
  the large finite result to a new output directory.
- P2.2: guard serialization, parent creation and exclusive output creation/write
  for expected `ValueError`/`OSError`. Exit 2 with documented `E_BENCHMARK_OUTPUT`
  and a new-writable-path action, without exception/path text. Retain `open('x')`.
  Real CLI tests cover existing file, parent-file and directory conflicts with
  exact protected-byte checks and empty stderr. A serialization error creates no
  output. No broad exception catch or destructive cleanup was introduced.

Red confirmation: `uv run --project packages/cg-release --locked pytest
packages/cg-release/tests/test_performance.py packages/cg-release/tests/test_sandbox.py
-q --tb=short` returned 8 failed, 29 passed, reproducing both findings.
Green: the same two modules plus `test_timing.py` and `test_documentation.py`
returned **59 passed in 5.34s**, including all original cases and ten new cases.
The separate `test_install.py` gate returned **13 passed in 7.30s**, with real
sdist/wheel and locked source-free installation. Ruff, docs site, documentation
regeneration/freshness, disabled installation and historical-byte checks passed.
Generation finished before the independent verification handoff.

Exact commands/exits, scope and handoff are recorded in
`.cg-docs/work-reports/release-controller/2026-09-13-phase7-review-repair1-evidence.json`.
Only five product/doc files changed: the two helpers, their two test modules and
the operator guide's output-error row. No dependency, publisher, workflow, Pester
or authority path changed. The full gates are retained **pre-repair** results;
focused post-repair checks are not labeled as a new full package/Pester run.

### Accounting and Independent Handoff

This is Phase 7 review repair cycle **1**, with no failed post-repair regression.
Step 13 implementation repairs remain 1/2 and Step 14 remain 0/2. All earlier
Step 11/12 and review/residual counters remain unchanged. Original P2 finding
statuses remain open until an independent reviewer confirms closure; repaired
locally is not independently verified.

Parent: dispatch a dedicated independent sibling to verify only P2.1/P2.2 and
their direct numeric/serialization/output/documentation boundaries. Re-run the
59-case focused command and inspect the five changed files against the original
review and this evidence. Return a new verification artifact with each finding
confirmed-fixed/open/unverified and any new defect. Do not invoke the later
`/cg-review mode:verify`, pipeline step 8 or another later command. A full rerun
is needed only for concrete uncovered impact; if required, use the proven
supervisor limits (package 3600s, prepare 7200s, Pester 1800s), not 600 seconds.

Phase 7 completion stays parent-owned and pending independent closure. Publisher
disabled and all accepted live deferrals unchanged. V8 still requires the later
authorized committed gate and ordinary PR CI. No remote, commit/push/PR, settings,
historical rewrite, new Agent Manager session or later pipeline step occurred.

## Phase 7 Final-Gate Decision 2026-09-13T15:58:16Z

The user requested a definitive qualified completion or an exact final-gate
handoff. Read the independent `phase7-verify-review.md`: **2 confirmed fixed,
0 open, 0 unverified, 0 new**, with 59 focused tests, 37 independent bounded probe
groups, Ruff/docs/disabled checks passing. The five current source Git blob IDs
match its recorded identities exactly. The original full ten-spec review and its
historical open labels remain untouched; independent closure is in the new review.

**Decision: one final test child is required.** `/cg-work` Step 2.5 requires a
full-suite phase-boundary gate. The 984-package and unfiltered 2935-Pester passing
runs preceded source repairs. The accepted live exception changes rollout evidence
and V8 timing, not the local full-gate requirement. Focused verification establishes
repair correctness but is not labeled as a full post-repair gate. The reviewer
found no additional impact that required a broad regression investigation; that
does not replace the command's explicit completion gate.

Request exactly one parent-dispatched dedicated test child using
`.cg-docs/work-reports/release-controller/2026-09-13-phase7-finalgate-handoff.json`.
It runs the entire package once with a 3600-second bound, then the canonical
unfiltered `. tests\Run-Tests.ps1` once with an 1800-second bound after loading
Pester safety. It captures fresh results and retains skip/cleanup qualifications.
It then checks lint, docs freshness/site, disabled installation, historical bytes
and plan validity. No full prepare is requested because that repeats the same
22-minute package suite. No unchanged native/Node/target rerun is requested without
a concrete new impact. Post-repair install13 and independent focused59/probes37
remain scoped evidence, not substituted full-suite results.

Freeze product writers; use a new private process-local temp root and new evidence
paths, never old-root cleanup. Compare reviewed source identities before/after and
return any unexpected source change instead of making a fix. No generation after
review, dependency change, remote operation or commit is allowed in the child.
Preserve raw-log paths and the later deliberate-staging caution for ignored logs.

No completion field changed here. Plan remains active, completed1-6/current7;
no failing-step or counter is added for this pending check. All review repair
counters remain as recorded. After this final gate passes on unchanged source,
the parent can record Phase 7 Success-qualified in crash-safe order, but plan
status must remain active with V8 pending for the pipeline step11 authorized
committed gate and step13 ordinary PR CI obligation. Publisher disabled; live
proof remains deferred, not passed. No step8 or later command was executed.

## Phase 7 Acceptance Evidence 2026-09-13T17:16:58Z

The final package gate is now complete: **994 passed, zero failed/errors/skipped**,
exit0, 1316.047 seconds under the3600-second bound. JUnit contains994 unique test
identities. Verified the result and JUnit SHA256 values against `integrity.json`
and read the raw log's final994-pass summary. All five current reviewed source
blobs match independent verification. The final child compared2743 product hashes
and29 prior gate artifacts; all remained unchanged. The seven other post-repair
gates therefore remain current, including unfiltered Pester **2935 passed,0 failed,
2 skipped**, `filteredFiles:null`, 21 files.

The earlier post-repair run remains **993 passed,1 failed**, not a rewritten pass.
Dedicated diagnosis reproduced bundled GPG's110-byte extra-socket path failure.
A fresh shorter process-local TEMP/TMP root resolved it without product changes,
weakened assertions, shared keyrings or global environment changes. The final root
was52 native path bytes, giving a predicted103-byte browser socket. The final full
run had no diagnostic observer. Initial unsuccessful probe limitations and all
old logs remain preserved; the diagnosis does not invent missing original stderr.

Independent embedded review closure remains **2 fixed,0 open,0 unverified,0 new**.
Its59 focused tests and37 bounded probe groups and the post-repair13 install tests
are supporting, overlapping evidence, not additional unique full-suite counts.
No source change after review invalidates their result. No further test or review
rerun is needed for metadata-only completion.

Exact current acceptance record:
`.cg-docs/work-reports/release-controller/2026-09-13-phase7-final-evidence.json`.
The final package evidence directory is
`.cg-docs/work-reports/release-controller/2026-09-13-phase7-pkg-165245Z-52219816/`.
The record links the initial failed gate, GPG diagnosis, independent review,
retained seven passing gates and all integrity/qualification records.

Local Phase7 evidence passes under `D-2026-09-13-defer-live-rollout`; checkpoint
write follows next in crash-safe order. Preserve all counters: Step11 1/2,
Step12 2/2, earlier review cycles2/residual repairs3, Step13 1/2, Step14 0/2,
Phase7 review repair cycle1. The GPG correction changed environment only and adds
no product repair attempt. No historic failure is removed or recounted as a pass.

Pester cleanup diagnostics remain (252 and1089 repeated diagnostic strings,
not distinct failed assertions); no cleanup success is claimed. Retain the two
unspecified update skips, platform/adapter-only qualifications, earlier native
skip/integration-selection limits and Windows portable-link limitation. Ignored
raw logs remain local evidence and need deliberate review at later authorized
staging/publication. No live host/matrix/security/performance proof is inferred.

Whole-plan V8 is still pending for the step11 authorized committed-input gate and
step13 ordinary PR CI, including the ordinary six-cell matrix/aggregate. The
publisher remains disabled; bridge, clean-client, registered release-mode CI,
sandbox/security and live performance evidence remains deferred, not passed.
No commit, step8, later command, roadmap change or remote operation is performed.

### Final Phase 7 Checkpoint

**Success-qualified.** Appended7 to the unquoted integer flow sequence first and
read back `[1, 2, 3, 4, 5, 6, 7]` while `current-phase: 7` remained. Then removed
`current-phase` and read the plan again. `status: active` remains; no
`completed-date` was added. Active-state now records local V7 success and pending
V8. The original review is not rewritten; the independent verification remains
the closure authority for both P2 findings.

Mechanical self-review is complete for the reviewed Phase7 changes: no remaining
debug/import/TODO issue. Independent numeric and error-boundary checks are
recorded separately; mechanical review alone is not statistical/logical proof.
The new final gate establishes current local test acceptance on unchanged product
source. It does not establish committed-input, ordinary PR CI or deferred live
acceptance. The final-phase whole-plan completion/roadmap step therefore does not
run under the explicit V8 timing amendment.

Only plan/report/checkpoint metadata changed during this completion. No code or
generated product output changed after review. No step8 or later pipeline command
ran. Suggested eventual commit subject, not executed:
`feat(release): complete local release controller delivery`.

## Step 11 Prepare Repair 2026-09-13T21:13:48Z

The user explicitly authorized commit/push/PR and selected base `dev`. Local
`dev`, `origin/dev`, and the live remote ref agreed at
`ae0def8ed991065d0afb11ca4c6ab8d0bfc6f6ec`. HEAD remains
`b94f585c8a485dfb03965ca9711fb83257aaa7de` on `improve-cg-release`.
The independent `2026-09-13-generic-asynchronous-release-controller-precommitrepairverify.md`
report confirms P1.1 fixed, both Bash fixture failures passing, and zero open/new
findings. Its five repair identities still match. This does not replace preflight.

Source provenance and containment passed. Required generation wrote 1,486 adapter
files; the refreshed inventory and generated diffs were inspected, and all four
new shared contracts match the canonical source. Both JavaScript syntax checks and
the docs-site check passed (76 pages, 8 groups). Selection-only preflight selected
nine commands but did not execute them.

The dedicated child subsequently ran the exact prepare command with `--base dev`,
`--run-native-target` and `--format json`. It exited 1 after 450.156 seconds:
two of nine selected commands executed; native pytest returned 2591 passed,
1 failed, 50 skipped and 2 deselected in 447.39 seconds. The failed assertion was
`scripts/tests/test_issue_dispatch.py::TestActiveStateIntegrity::test_handoff_targets_dev_branch`.
Pester and the remaining seven commands did not run. The executor reported no
product, protected-document, prior-evidence, index, branch or HEAD change.
External evidence remains at
`C:/Users/wb384996/AppData/Local/Temp/3/kilo/s11-evidence-20260913-2106-f183a065/handoff.json`.
It is a local retained artifact, not a committed or remote evidence claim.

The active-state contract permits null for an unknown next command. The test's
unconditional `.lower()` does not support that valid unknown state. However, this
current handoff was stale: it still named `/cg-work` and had no next command after
the user authorized step 11 and selected `dev`. The semantic correction updates
the workflow, timestamp and exact restart command to `/cg-commit-push-pr --base dev`,
links the independent review, and updates the current report pointer status.
The test and its branch assertion are unchanged; no dummy string or false
completion state was added. No new human decision is pending, so status remains
`handoff` and no blocking decision is invented.

Before the correction, the focused integrity class reproduced the same failure:
2 passed, 1 failed in 0.13 seconds. Plan validation passed before metadata writes.
After correction, `python -B -m pytest scripts/tests/test_issue_dispatch.py -q
--tb=short -p no:cacheprovider` passed all 83 tests in 0.16 seconds, exit 0,
including the three integrity checks. The five step 9 repair blobs remain equal
to the independent review; the assertion and active-state contract are unchanged.
The corrected active-state Git blob is
`144964651fecfac2ba56742a53c92abe8f4f1466`. Its tracked whitespace check passed.
The complete prepare gate must still pass before staging or commit. Pester remains a subsequent
dedicated safe-child obligation; the committed full gate remains after commits
and before push. PR creation targets `dev`; the parent owns the later 300-second
wait and PR verification.

Cleanup of the failed prepare's owned root was incomplete because a temporary
Git object returned WinError 5 after 622 read-only attributes were cleared. The
executor reported zero active owned job processes and no termination, not clean
filesystem removal. No old root is deleted by this metadata correction.
Prior failures, skip counts, cleanup qualifications, plan phases, counters,
V1-V8 evidence and `D-2026-09-13-defer-live-rollout` remain unchanged. V8 is pending,
the publisher is disabled, and live proof is deferred, not passed.
