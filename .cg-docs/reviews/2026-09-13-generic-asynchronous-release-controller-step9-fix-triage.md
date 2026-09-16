---
date: 2026-09-13
type: fix-triage
pipeline-step: 9
parent-review: .cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase6-verify-review.md
status: Success-qualified
step9-completed: true
validation-evidence: .cg-docs/work-reports/release-controller/2026-09-13-step9-validation-180003Z-86e3cad4/handoff.json
findings:
  P1.1: fixed
---

# Pipeline Step 9 Fix Triage

**Status: Success, qualified. Step 9 is complete.** The repairs, focused checks, clean default full-package gate, and unfiltered full Pester assertion gate pass. Cleanup did not complete without errors, and two Pester skips retain unknown individual names/reasons. This is local fix-triage acceptance, not independent review convergence, a committed gate, live readiness, or permission to start step 10.

## Accounting

| Measure | Count |
|---|---:|
| Prior confirmed phase closures, retained unchanged | 71 |
| Previously resolved findings in this exact step 8 report | 0 |
| New source findings in scope | 1 |
| Fixed by this triage | 1 |
| Open source findings in this report | 0 |
| Skipped / out of scope | 0 / 0 |
| Additional failed fixture checks now passing | 2 |
| Required final local gates completed | 2 |
| Required final local gates still pending handoff | 0 |

P1.1 is local to the parent report. The two fixture checks are not new source finding IDs and do not add two closures. The 71 prior confirmations and their qualifications remain historical evidence. This pass adds one tested repair, not 72 independent new confirmations. No plan, active-state field, repair counter, prior closure map, or approval-only pause accounting was changed. Ordinary repairs used the existing user authorization; no redundant approval was requested.

Only the parent's `findings.P1.1` frontmatter changed. Its body, including the original failure and open-count prose, remains the historical step 8 record.

## Repairs

### P1.1: Default Package Test Dependency

Source finding: `cg-testing` and `cg-code-quality`, `packages/cg-release/tests/test_profile_workflow_authority.py:18`, `packages/cg-release/pyproject.toml:17-19`, and the default full-package command in `scripts/cg_pr_preflight.py`.

Added `PyYAML==6.0.2` to the default `dev` dependency group and regenerated `uv.lock` offline. The existing `gpid-native` pin and generic runtime dependencies are unchanged. No package versions were upgraded. The default documented suite and ordinary preflight now receive the test dependency without extra group flags. No producer command, workflow, integration contract, or documentation change is needed for that unchanged default command contract.

Added `test_default_locked_package_gate_collects_without_optional_groups` to the package-owned `test_install.py` suite. It uses the actual `FULL_PACKAGE_TEST_COMMAND`, adds `--isolated` and collection-only reporting, and removes inherited Python/user-site environment contamination. It does not add a dependency group, skip the authority module, or reuse the project venv. It requires successful full-package collection and authority test node IDs. The outer red run deliberately had the optional group; the inner default environment still failed, proving that the outer installation did not satisfy the regression.

The regression was first written and tested in the native producer-contract file. The final scope check moved it to the package suite so the native-profile producer does not repeat package pytest work. The native producer-contract file is back to its exact pre-task content. This is test ownership correction, not a skipped test or product repair retry. The intermediate 91-native/31-package passing results are retained history; final results are 90/32 below. The repair child ran collection and focused checks; the later dedicated gate passed all 995 package cases as recorded in the completion section.

Extended the installed-wheel test in `test_install.py` to require `importlib.util.find_spec('yaml') is None` in its runtime-only environment. That test builds and installs actual distributions with locked runtime dependencies. It passed after the dependency repair.

### Additional Fixture Failures

Before the repair, the new direct-executable regression passed for CMD and failed for Bash. The Bash fixture's copied `pwsh.exe` exited `3758096423` with empty streams before it recorded argv. The original compiled package `python.exe` worked. The real Bash legacy launcher independently reproduced exit 127 with no argv. This localizes the observed failure outside the product router.

A fresh probe compiled the same C# fixture source with neutral output names. Its direct controls returned 37, and replacement with the neutral `fixture.exe` assembly made the unchanged real Bash legacy launcher return 37 with the expected legacy argv. The fixture now follows its existing CMD construction: compile a neutral `fixture.exe`, then copy it to the mock package interpreter and `pwsh.exe`. Product launchers, router code, exit expectations, and argument assertions were not changed.

The new Windows-only regression directly executes both mock names before product dispatch, separately for CMD and Bash. It checks exit 37 and exact empty, quoted, space-containing, ampersand and trailing-backslash arguments. Both direct cases and both previously failed real legacy cases now pass. Native Unix qualification is not inferred from Windows Git Bash.

**Diagnosis limit:** The controlled fixture construction change is verified. The lower-level Windows/CLR or host reason for the old copied executable's opaque exit is not established. Renaming all .NET executables is not claimed to fail, and no product launcher defect or security-control bypass is claimed. No host protection, permission, runtime policy, or antivirus setting was changed.

## Executed Checks

| Check | Result |
|---|---|
| New isolated full-package collection regression, before repair | 1 failed; inner exit 2; 976 collected and 1 collection error: `ModuleNotFoundError: No module named 'yaml'` |
| New direct mock startup regression, before repair | 1 passed, 1 failed; Bash `pwsh.exe` exit `3758096423`, empty streams |
| Neutral-assembly diagnostic probe | Original real launcher exit 127; repaired control exit 37 with expected legacy argv |
| Final clean default native launchers + producer contracts + preflight selection | 90 passed, 0 failed/skipped; 27.88 seconds; exit 0 |
| Final clean default authority + install selection | 32 passed, 0 failed/skipped; 12.82 seconds; exit 0; includes all 18 authority tests and clean full-package collection regression |
| Final Ruff, entire package and two changed native fixture/test files | Passed; exit 0 |
| `uv lock --offline --project packages/cg-release --check` | Passed; 23 packages resolved; exit 0 |
| Scoped `git diff --check` | Passed; does not check untracked file bytes |
| Dedicated full Pester gate | 2935 passed, 0 failed, 2 skipped; 2937 total; 21 files; `filteredFiles: null`; exit 0; 177.938 seconds; cleanup qualified below |
| Dedicated clean default full-package gate | 995 passed, 0 failures/errors/skips; exit 0; 1318.453 seconds including provisioning; pytest reports 1316.49 seconds |

Passing test commands used fresh `uv --isolated` environments with the locked default dependencies. They did not use `--no-sync`, `--group gpid-native`, or the previously provisioned package environment. Offline cache reuse supplies package distributions, not an already provisioned environment. Counts overlap; do not add them to full-suite totals as unique coverage.

Exact passing test commands, run from the worktree root:

```powershell
uv run --isolated --offline --project packages/cg-release --locked python -B -m pytest scripts/tests/test_release_controller_launchers.py scripts/tests/test_release_producer_contracts.py scripts/tests/test_cg_pr_preflight.py -q --tb=short -p no:cacheprovider --basetemp "C:\Users\wb384996\AppData\Local\Temp\3\kilo\s9native-final-01" --junitxml "C:\Users\wb384996\AppData\Local\Temp\3\kilo\s9native-final-01.xml"
uv run --isolated --offline --project packages/cg-release --locked python -B -m pytest packages/cg-release/tests/test_profile_workflow_authority.py packages/cg-release/tests/test_install.py -q --tb=short -p no:cacheprovider --basetemp "C:\Users\wb384996\AppData\Local\Temp\3\kilo\s9package-final-01" --junitxml "C:\Users\wb384996\AppData\Local\Temp\3\kilo\s9package-final-01.xml"
uv run --isolated --offline --project packages/cg-release --locked ruff check --no-cache packages/cg-release scripts/tests/test_release_controller_launchers.py scripts/tests/release_shell_fixture.py
```

The red commands used these new test node IDs: `scripts/tests/test_release_producer_contracts.py::test_default_locked_package_gate_collects_without_optional_groups` (before its move to `packages/cg-release/tests/test_install.py`) and `scripts/tests/test_release_controller_launchers.py::test_windows_fixture_executables_run_before_product_dispatch`. The first outer command added `--group gpid-native` solely to load the native test module before it launched its clean default child. The mock red run used basetemp `C:/Users/wb384996/AppData/Local/Temp/3/kilo/s9red-shell-01`. All new roots were below the verified approved temporary parent; no prior roots were deleted.

Critical failure excerpts are retained above from tool output. They are not claimed as separate raw log files. The probe source is `C:/Users/wb384996/AppData/Local/Temp/3/kilo/s9-shell-probe.py`, and its fixture root is `C:/Users/wb384996/AppData/Local/Temp/3/kilo/s9d-m548xr39`. The two JUnit paths in the passing commands retain the focused results locally; temporary files are not committed evidence or remote proof.

## Gate Completion

The user returned the dedicated validation handoff at 2026-09-13T18:33:04Z and authorized this step 9 disposition. Evidence directory: `.cg-docs/work-reports/release-controller/2026-09-13-step9-validation-180003Z-86e3cad4/`. Read `handoff.json`, `result.json`, both full-gate execution records, `pester-last-run.json`, `pester-diagnostics.json`, `integrity.json`, and the complete 15-line package stdout plus provisioning stderr. The immutable executor records correctly retain their earlier parent-disposition-pending status; this report supplies the later completion decision without rewriting those records.

The dedicated child ran `. tests\Run-Tests.ps1` with no runner flags or pipeline in a separately captured Windows PowerShell process. The snapshot has `passed: true`, `failedCount: 0`, `failures: []`, and `filteredFiles: null`. Its 21 file rows cover the full runner selection, not a filtered substitute. The run ended at 18:03:17Z before the full-package run started at 18:03:43Z. Both gates exited 0 without a timeout. Their required sequential execution is satisfied.

The executed package argv was `uv run --isolated --offline --project packages/cg-release --locked python -B -m pytest packages/cg-release/tests -q --tb=short -p no:cacheprovider --junitxml <evidence-directory>/full-package.xml`. `full-package-execution.json` retains the absolute executable and JUnit paths. It selected default `dev`, with no optional-group selection or warming and no `--no-sync`. Stderr confirms `Installed 23 packages in 316ms`. The child used fresh `TEMP` and `TMP` directly at `C:/Users/wb384996/AppData/Local/Temp/3/kilo/6_tdhwj9`, isolated Git/GPG/GH configuration and user-site behavior, and injected no real credentials. Global environment and prior roots were unchanged. The full run ended at 18:25:42Z; JUnit records 995 distinct cases with no failures, errors or skips.

The dedicated child also repeated the native 90-case and authority/install 32-case selections, Ruff, offline lock consistency, and scoped whitespace checks. All passed. Its focused wall times were 29.860 and 15.750 seconds; these are separate executions from the earlier repair-child timings above. The 32 package cases overlap the full 995 and must not be added as unique coverage. Lock resolution remained 23 packages. Scoped whitespace is not an untracked-byte check; all six audited source paths are untracked in this candidate.

### Retained Qualifications

- Pester recorded **615 cleanup diagnostic occurrences**: 580 `RemoveFileSystemItemIOError` and 35 `PathNotFound`. `result.json`'s earlier count of 580 covers only removal records; `handoff.json` and the original diagnostic error-ID map establish the complete 615 count. These are occurrences, not 615 distinct defects or failed assertions. `cleanupSucceeded` remains false. No cleanup repair or clean-workspace claim is made.
- The separate `Update failed: Target mapping not found` error is the expected negative update fixture at `tests/update.Tests.ps1:387-419`. It is not part of the 615 cleanup occurrences and is not a skipped test.
- Both Pester skips are in `update`. The runner retains no individual runtime names or reasons, so those remain unavailable rather than inferred from source or treated as passed.
- Preserve the Windows Bash placeholder, Git Bash versus native Unix distinction, and prior adapter-only Kilo containment limits. The supervisor waited for direct child processes; no timeout occurred or process was killed, but it does not prove completion of every descendant.
- Raw `pester-stderr.log`, `pester-stdout.log`, `full-package-stderr.log`, `full-package-stdout.log`, diagnostic JSON and complete JUnit remain in the evidence directory under existing ignore rules. They were not rewritten, staged, or published.

### Evidence Identity

Fresh SHA-256 checks during disposition matched the saved handoff/manifest:

| Artifact | SHA-256 |
|---|---|
| `result.json` | `72bf406ce119f8b004fd4cc0d52ad22cc6e1098ff58373ed97a8a4e90aca10b0` |
| `integrity.json` | `91f5b6e626d961ddc682a9b671fe578d94ee16b988f8e86ddad5b28f311fe911` |
| `full-package.xml` | `34cbc576eeded882189e0e57ccead4bce6082b92501cae1f82521fc81394c8d3` |
| `pester-last-run.json` | `f3556bf5e0c3213daad763ead762db79943ff9e859db2d4dd363362f3ac3e2ba` |

Fresh current Git blob checks match all five changed paths below and the unchanged producer-contract sixth path. Current HEAD remains `b94f585c8a485dfb03965ca9711fb83257aaa7de` on `improve-cg-release`. The executor's retained before/final audit reports 2743 product hashes and 203 prior evidence files unchanged, with matching source blobs, protected documents, HEAD, branch and index. That complete inventory was not independently rehashed during this report-only disposition. This triage report is the intentional later status change; source and immutable gate evidence are not edited.

The command's required repair/status tracking and full regression gate are satisfied with these explicit qualifications. Keep P1.1 fixed, prior closures at 71, skipped findings at 0, and local pending gate count at 0. Do not reset or increment implementation repair counters for this evidence return. No additional repair, approval request, or test rerun is needed for this report-only completion.

## Original Gate Handoff

The following instructions are retained history and are now satisfied by the evidence above, not a request to rerun the gates. The repair child had no native Task/execution-subagent tool; it ran no Pester and created no Agent Manager session. Its requests went to the existing parent session `ses_f6e961f23ffeeFWeYOfNYElLY9`, which supplied the later dedicated validation return:

1. Use a dedicated safe execution child. Read project instructions and `cg-skill-pester-safety`. In this worktree, run `. tests\Run-Tests.ps1` with no flags and no pipeline. Read `tests/last-run.json` and return `passed`, `failedCount`, `failures`, and `filteredFiles`. Preserve an immutable timestamped snapshot and report total/pass/skip counts, 21-file coverage if unchanged, and critical cleanup diagnostics. Do not equate zero failed assertions with successful cleanup. Do not substitute a filtered run.
2. Run the full package sequentially in a clean default locked environment: `uv run --isolated --offline --project packages/cg-release --locked python -B -m pytest packages/cg-release/tests -q --tb=short -p no:cacheprovider --junitxml <new-evidence-directory>/full-package.xml`. Use a blocking, bounded supervisor, retain raw stdout/stderr, exact argv/environment treatment, duration, exit, JUnit totals and source identity. Do not use `--no-sync` or select `gpid-native`. Do not run two write-heavy gates together.
3. Retain the existing approved short-GPG-root correction for that full run: allocate a new `tempfile.mkdtemp(prefix='', dir='C:/Users/wb384996/AppData/Local/Temp/3/kilo')` and set only child `TEMP` and `TMP` directly to it. Do not add a `package` suffix. A short pytest `--basetemp` alone does not set the controller's temporary GPG home. Keep global environment and all prior roots unchanged. Source: `2026-09-13-phase7-gpg-repair-evidence.json` under `.cg-docs/work-reports/release-controller/`.
4. Compare the five changed source identities below before and after the gates. Save exact results in a new timestamped evidence artifact, then update this triage report's gate disposition. If a gate fails, retain the failure and diagnose it within step 9; do not mark complete or proceed to step 10. The command's suggested independent follow-up is `/cg-review mode:verify` against the exact parent report and these repairs; it was not executed here.

Git blob identities, captured after the passing focused tests:

| Source | Git Blob |
|---|---|
| `packages/cg-release/pyproject.toml` | `e78d51f6651dc1d32ee6f5f9241196bac158f90c` |
| `packages/cg-release/uv.lock` | `33d3f9741077086fca9d8215a7f0fbc0c0e51541` |
| `packages/cg-release/tests/test_install.py` | `f88e5097f3d670455062a0f77dd34352ba4daf05` |
| `scripts/tests/release_shell_fixture.py` | `e9bd2bae8212b9f8a04edded7b3d9f8ee11975d9` |
| `scripts/tests/test_release_controller_launchers.py` | `3eab36e78f7f5d494acc06a844bb7950fd9e5b45` |

The unchanged native producer-contract file has blob `4cda9f30ed26c27150bb561a2aa0f7019f311ee4`. This final identity table supersedes the intermediate six-path handoff sent before the test ownership correction.

These identify a dirty local candidate, not a committed exact input. The later authorized V8 gate remains `python scripts/cg_pr_preflight.py --phase committed --full-gate --run-native-target`, after the planned step 11 commit. Ordinary PR CI remains required and pending. Neither was run or moved earlier here.

## Scope And Advice

Read the matching local fix-triage command, project instructions/charter/configuration/context, Python instructions and skill, Pester safety skill, Brain-query skill, release-controller integration contract, model-advisory contract, and relevant plan/active-state evidence. The bounded Brain query selected `.cg-docs/solutions/testing-patterns/2026-08-13-release-gate-fixtures-and-derived-evidence-hashes.md`: fixture commands must match runtime boundaries. That lesson guided the direct-executable control and actual preflight-command regression. `open-brain` was unavailable; the local Brain CLI and targeted saved project context were used. Brain index warnings are not test evidence. No project-memory write was requested or performed.

The publisher remains disabled. Decision `D-2026-09-13-defer-live-rollout` and seven completed local phases are unchanged. Live bridge delivery, native clean-client qualification, registered release-mode CI, sandbox/security/approval trials, remote identity and performance proof remain deferred, not passed. No live deferral excuses a failed local check. Prior cleanup, skip, native-platform and retained-log qualifications remain intact.

Model advice, stage `fix-triage`: use strong dependency-boundary and evidence-review capability at high effort for the gate/verification handoff. An economical code-capable option is suitable only for later bounded documentation synthesis. This advice reflects the need to distinguish a clean dependency environment, local fixture proof, and deferred live evidence. Options are suggestions, availability differs by platform and date, and the user chooses the model and effort. No model or effort was changed.

No step 10 compounding, solution capture, commit, staging, remote command, publication, activation, or generated-target operation occurred. The final repository changes in the repair child are the five source/test/lock paths above, the exact parent finding's frontmatter, and this requested triage report. This completion continuation changes only this report. All pre-existing changes remain intact. The command's independent verify-review follow-up has not run; V8 committed validation and ordinary PR CI remain required and pending. Step 9 Success does not authorize step 10 or any deferred live gate.
