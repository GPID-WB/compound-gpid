---
date: 2026-09-11
depth: full
type: standard
plan: .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md
findings:
  P1.1: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
---

# Release Controller Phase 1 Review

## Review Status

**Status**: review completed; all four findings confirmed fixed by independent scoped verification. No remaining or new findings; no whole-plan or merge approval is implied.
**Review mode**: full, embedded `review:auto` only.
**Invocation**: `/cg-work phase1 review:auto .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md`.
**Coverage**: 10/10 agent specs read and emulated sequentially, once each, in the requested order. These were not independent sessions.
**Files reviewed**: 23 implementation/test/configuration files, plus the selected execution report, offline baseline, Pester evidence, and active-state checkpoint for consistency. The current Pester runner summary was also checked.
**Findings**: 4 unique findings (P0: 0, P1: 1, P2: 3, P3: 0). The original review below records the findings as discovered; current fix status and evidence are in frontmatter and the repair section.

## Scope And Authority

- Reviewed all 17 non-generated files in `packages/cg-release/`: package metadata, lockfile, seven source/typing files, three test files, and five fixtures. These files were untracked at review time and were included explicitly.
- Reviewed `.github/workflows/release-controller-ci.yml`, `scripts/cg_pr_preflight.py`, `scripts/tests/test_cg_pr_preflight.py`, `scripts/benchmark_release.py`, `create-release.ps1`, and `tests/create-release.Tests.ps1`.
- Used the Required Review Child section of the execution report, Phase 1 Steps 1-2, and the relevant package, CLI, security, timing, and completion contracts as authority. Plan text is not execution evidence.
- Read the local `cg-work` and `cg-review` commands; project charter/configuration; project and Python/PowerShell instructions; context-loading, review-routing, goal-execution, and active-state contracts; Python best-practices and Pester safety skills.
- Checked the unchanged native CI setup in `.github/workflows/tests.yml` only to trace the new preflight dependency. This is integration context, not a review of unrelated workflow code.
- Excluded virtual environments, distributions, build products, bytecode, test/lint caches, generated view bodies, unrelated changes, and future-phase implementation requirements. No live sandbox or remote matrix execution was required for this review.
- Applied this constraint to every emulated agent: never recommend deleting, replacing, renaming, or moving `.cg-docs/brainstorms/`, `.cg-docs/solutions/`, `.cg-docs/archive/`, `compound-gpid.md`, `compound-gpid.local.md`, `roadmap.json`, `SCHEMA_VERSION`, or `.github/` infrastructure. Content and security findings remain reportable.
- No implementation edits, autofix, later pipeline commands, commits, pushes, PRs, remote writes, or completion-state updates were made. This report is the only review artifact created.

## P0 Blocking

No P0 finding was established. No real credential exposure, publication, or remote mutation occurred during the review.

## P1 Critical

### P1.1 Reject Authorization Arguments Independently Of Token Shape

**[P1.1]** [cg-adversarial] `packages/cg-release/src/cg_release/process.py:36-41`; `packages/cg-release/src/cg_release/events.py:10-15`.

**Issue**: The process boundary treats `redact(arg) != arg` as its credential rejection rule. The redactor recognizes `Authorization: Bearer` and `Authorization: Basic`, but not GitHub's `Authorization: token <value>` form unless the value happens to match a separate token-prefix pattern. A header with an opaque token therefore passes the argv boundary unchanged. The same header remains in `ControllerError.message` and JSON event output.

**Proof**: An in-memory probe used only `Authorization: token SYNTHETIC_TEST_ONLY`. With `cg_release.process.subprocess.run` mocked, `run_process('gh', ['api', '-H', header, 'user'], cwd=Path.cwd())` passed that complete header to the mocked argv. A separate captured-output probe showed that `ControllerError('E_TEST', header)` and `emit_event(..., json_output=True)` retained the synthetic value. No real `gh` process or API request ran.

**Impact**: This defeats the Phase 1 promise that credentials cannot enter argv and that credential-bearing failures are redacted. Credentials need not use one recognized textual prefix. P1 reflects a demonstrated missing security check in the exported boundary; the current four-command CLI remains disabled, so this is not a claim of an active publication exploit or an observed production leak.

**Fix**: Reject authorization-bearing arguments based on the header/configuration key, independently of the authentication scheme and token prefix. Redact the complete authorization value in diagnostics. Include `token`, mixed-case header names, and opaque token values in negative process-boundary and event-output tests. Keep credentials out of argv rather than merely removing them from displayed logs.

**Status**: open. No fix applied.

## P2 Important

### P2.1 Empty Options Bypass The CLI Contract

**[P2.1]** [cg-data-quality, cg-adversarial] `packages/cg-release/src/cg_release/cli.py:59-67`.

**Issue**: Validation checks the truth value of `args.version` and `args.channel`, not whether those options were supplied. Argparse accepts an explicitly supplied empty value, so the required mutually exclusive group is satisfied while SemVer validation is skipped. An empty channel also bypasses both its identifier check and its exclusion from explicit-version mode.

**Proof**: Direct calls to `parse_args()` accepted all three cases: `['plan', '--version', '']`, `['plan', '--version', '1.0.0', '--channel', '']`, and `['start', '--version', '', '--channel', 'rc']`. The probe reported three accepted cases. This can occur when automation passes an empty environment-derived value.

**Impact**: The argument parser returns a supposedly validated namespace with no valid version or with a forbidden option combination. The disabled CLI still prevents submission, but reports the disabled-operation result instead of the argument error required by this implemented contract.

**Fix**: Use explicit `is not None` checks for supplied options, reject empty values, and apply option exclusion regardless of string truth value. Add these cases to `test_cli_rejects_invalid_options` and verify `E_ARGUMENT` through `main()`.

**Status**: open. No fix applied.

### P2.2 Provision The New Tool In Existing Preflight Producers

**[P2.2]** [cg-reproducibility] `scripts/cg_pr_preflight.py:867-876`; integration context `.github/workflows/tests.yml:245-265`.

**Issue**: The new controller route invokes `uv` by executable name. The existing native-target CI jobs now reach that route for package/integration changes and full-gate fallback, but their declared setup installs only Python, pytest, and PyYAML. They do not install or verify uv. The separate controller workflow installs `uv==0.11.3`, but its installation cannot supply another workflow's runner.

**Impact**: The native preflight now depends on an undeclared runner tool and its ambient version. On an otherwise valid clean environment without uv, it stops with the executable-not-found result before running the selected package tests. If the hosted image supplies uv, that image version rather than the tested pin controls this route. This is a reproducibility gap, not a claim that a remote CI run has already failed. The old scripts' Python import minimum is otherwise unchanged.

**Fix**: Add a pinned uv setup or explicit prerequisite check to each existing producer that must execute the controller route, including the native CI job. Document the local preflight requirement. Add a check that connects controller-route selection to the actual producer setup; the current missing-Python mock does not establish that uv exists.

**Status**: open. No fix applied.

### P2.3 Measure Subprocess Count At The Execution Boundary

**[P2.3]** [cg-testing, cg-learnings-researcher] `scripts/benchmark_release.py:25-41,69`; `packages/cg-release/tests/test_timing.py:100-116`.

**Issue**: The bounded-Git-call regression test checks a self-reported counter. That counter is increased manually after three selected calls, outside `run_process()`. The test does not observe subprocess execution. An extra Git call added without an adjacent counter increment leaves the report at three and the test green. The report's constant provider write count is also not an I/O prohibition.

**Impact**: The current implementation visibly makes three local Git calls and no provider calls; its present baseline is not disputed. However, the test does not enforce the resource-shape contract that it claims to enforce. It will not reliably catch the repeated-subprocess defect identified in the relevant Brain lesson or an accidental provider call in the benchmark.

**Fix**: Add a spy at the actual process boundary and assert the observed Git-call count and allowed operations. Reject gh/network calls in that benchmark test. Derive reported counters from the same observed boundary, or independently compare them with the spy. Preserve the real offline smoke test.

**Status**: open. No fix applied.

## Sequential Agent Results

### 1. cg-code-quality

Result: no issues found in the phase-scoped style and organization review of `cli.py`, `models.py`, `events.py`, `process.py`, `timing.py`, and the targeted preflight/timing changes.

Context: new source modules are narrow and under the project size limit. Explicit integer schema checks and the re-raised timing interrupt are intentional, not style violations. Existing larger script bodies were not treated as new refactoring requirements.

### 2. cg-testing

Result: P2.3. The subprocess-count assertion in `test_timing.py` checks reported metadata rather than observed execution.

Context: also checked negative schema/CLI tests, isolated wheel smoke tests, executable aggregate checks, and the three new legacy timing tests. The supplied passing evidence remains qualified as described below; it does not prove missing negative cases.

### 3. cg-documentation

Result: no additional issues found in `create-release.ps1` timing help, package module/public-function documentation, and the phase report's behavior statements.

Context: disabled operations, missing live timing, overlapping local spans, and the later release-mode CI connection are identified explicitly. Did not require final user guides or claim that Phase 2 confirmation behavior was already implemented.

### 4. cg-version-control

Result: no issues found in the reviewed source/fixture content, `uv.lock`, and the package ignore coverage supplied by `.gitignore`.

Context: no real credentials were found in the changed files; synthetic fixtures are not secrets. Work is off main. Untracked package files were reviewed, not omitted or treated as a request to commit. Environment/build/cache bodies were excluded.

### 5. cg-reproducibility

Result: P2.2. The new preflight commands have a uv prerequisite that the existing native CI producer does not declare.

Context: the package lock contains public registry sources and hashes, requested CI Python versions are explicit, and installed-wheel tests use a separate environment outside the source tree. No remote six-cell result was inferred from local installation evidence.

### 6. cg-performance

Result: no additional current performance issue found in `benchmark_release.py`, `TimingRecorder`, or the narrow legacy timing changes.

Context: the current benchmark has three local Git calls, records missing remote intervals as null, and warns against summing overlapping spans. P2.3 concerns the regression guard, not a demonstrated current N+1 defect. No live speedup is claimed.

### 7. cg-architecture

Result: no additional issues found in the `src/cg_release` runtime separation, subprocess boundary placement, or fail-closed workflow-dispatch interface.

Context: the runtime package does not import GPID scripts or require GPID files in a target directory. Metadata adapters, trusted-provider operations, journal transitions, and release admission remain future-phase work and were not required here.

### 8. cg-data-quality

Result: P2.1. Empty supplied CLI values bypass validation in `cli.py`.

Context: schema-version types, duplicate JSON keys, extra nested fields, input byte bounds, strict request SemVer, finite event durations, and missing remote timing were checked. Policy models explicitly describe shape-only validation; later policy semantics were not promoted into Phase 1 findings.

### 9. cg-learnings-researcher

Result: P2.3 is supported by the prior lesson about observed subprocess counts. No separate duplicate finding was added.

Context: the release-fixture lesson also supports keeping isolated install/preflight checks and preserving evidence qualifications. The matched older native-target plan adds no separate requirement to this Phase 1 review. Relevant sources are listed below.

### 10. cg-adversarial

Result: P1.1 and P2.1, confirmed by bounded in-memory probes against the installed development environment with bytecode writing disabled.

Context: probes used synthetic authorization text and a mocked process boundary. The public CLI's operations remain disabled. No remote protection, permission, future journal, or publication claim was tested or inferred.

All ten outputs have an explicit result and file context. No output was incomplete; no agent was retried.

## Evidence And Limits

| Check | Evidence used | Qualification |
|---|---|---|
| Package regression | Execution report: 77 passed on Windows, Python 3.12 | Existing evidence; pytest not rerun in this review |
| Native preflight regression | Execution report: 46 passed | Existing evidence; does not supply producer setup or missing negative cases |
| Build/install | Execution report and `test_install.py` commands | Wheel/sdist and generic-directory wheel smoke passed locally; remote cells not claimed |
| Diagnostics | Execution report: Ruff and diff check passed | Existing evidence, not a replacement for logical review |
| Targeted Pester | Durable phase evidence: 95/95, zero failures, `filteredFiles: create-release` | Dedicated test-child result; no Pester rerun |
| Full Pester | Durable evidence and current `tests/last-run.json`: 2906 total, 2904 passed, zero failed, two skipped, `filteredFiles: null` | `ranAt: 2026-09-11T17:40:51Z`, `gitSha: b94f585`; dirty/untracked content is not bound by that SHA alone |
| Cleanup | Existing child/parent qualification | TestDrive `RemoveFileSystemItemIOError` messages remain unresolved; successful cleanup is not claimed |
| Adversarial probes | Two local Python `-B -c` probes | Three empty-option cases accepted; synthetic token header reached mocked argv and remained in captured error/event output |

The two Pester skips are attributed to `update`, not the required `create-release` cases. Their names and reasons are not supplied by the durable summary. The reported cleanup messages concern temporary `fresh-manifest-kilo-project` paths. There is no supplied evidence that they invalidate the required Phase 1 assertions, but their cause and complete cleanup were not independently established. They remain a test-environment qualification, not an invented Phase 1 code defect.

The execution report and active-state checkpoint consistently retain Phase 1 as blocked pending review. Their completion fields were not changed. Review completion alone does not close V1 while an open critical finding remains.

## Related Learnings

The budgeted `cg-index query --intent review` returned two artifacts with 592 index warnings. The relevant solution was read directly. `open-brain` tools were unavailable; local Brain retrieval supplied context, not runtime evidence.

- `.cg-docs/solutions/testing-patterns/2026-08-13-release-gate-fixtures-and-derived-evidence-hashes.md`: fixtures must match actual command protocols and isolated checkouts. Applied to the install/preflight test review and evidence limits.
- `.cg-docs/solutions/bugs/2026-08-26-release-drift-ignore-checks-spawn-thousands-of-git-processes.md`: bound and observe Git subprocess counts instead of checking only final results. Applied to P2.3. The old N+1 defect is already fixed; no present speedup is inferred from it.
- The selected brainstorm's CLI option table was used only to verify the four-command argument contract. Untouched brainstorm content was not reviewed as an implementation change.

## Disposition

Review complete: 10/10 sequential agent passes. Four findings remain open. No fixes or later commands were executed. P1.1 must be resolved before merge; the three P2 findings should be addressed without enabling later-phase behavior.

## Authorized Repair 2026-09-11

The preceding findings and disposition describe the initial review. The user
explicitly authorized all four repairs on 2026-09-11T18:15:23Z. One implementation
repair pass was applied; the earlier functional-test recovery counts were not
reset. All four findings are now locally fixed with executed regression evidence;
independent verification and a refreshed safe phase gate remain pending.

| ID | Changed scope | Local verification |
|---|---|---|
| P1.1 | events.py authorization-field redaction; process.py independent key-based argv rejection; new test_process.py | 21 cases cover opaque token values, mixed case, arbitrary schemes, configuration strings, proxy authorization, folded headers, and human/JSON output. Process tests disable the display redactor and assert no subprocess call. |
| P2.1 | cli.py parse_args supplied-option checks; test_contracts.py | Four empty-option combinations now reject in parse_args and return E_ARGUMENT through main. |
| P2.2 | cg_pr_preflight.py selected commands and version validation; native-targets setup in tests.yml; test_cg_pr_preflight.py | Pinned uv installed before native producer execution; missing/wrong uv fails before package gates with install guidance. Python 3.8 selector boundary retained. 52 preflight tests pass; actual package-only prepare route passes all four commands. |
| P2.3 | benchmark_release.py OfflineGit boundary; test_timing.py | Real Popen spy compares observed count with reported count; only three exact local Git operations allowed; socket and gh/other-process paths forbidden. Injected duplicate calls trip the observed budget. OfflineGit rejects remote/config operations and a fourth call. Real offline smoke retained. |

Final local package regression: 108 passed. Ruff for the package and benchmark
passes. The package-only prepare route executed pinned uv verification, package
pytest, Ruff, and locked wheel/sdist build successfully. Its cache report was
local-only and nonfatal; no committed-candidate or remote CI success is inferred.

Post-repair baseline:
`.cg-docs/work-reports/release-controller/2026-09-11-offline-baseline-review-repair.json`.
Prior baseline and Pester cleanup qualifications remain preserved. The legacy
publisher source and Pester tests were not changed in this repair pass.

## Verification Confirmation

On 2026-09-11 the dedicated verification child confirmed P1.1, P2.1, P2.2, and
P2.3 fixed, with two sequential agent specs complete and no remaining/new findings.
See `2026-09-11-generic-asynchronous-release-controller-verify-review.md` for
executed regression/probe evidence and retained installation/Pester qualifications.
The fixed frontmatter statuses are now independently confirmed; earlier status
statements describe the original review and repair history.
