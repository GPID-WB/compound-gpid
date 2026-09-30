---
date: 2026-09-13
type: verification
depth: light
pipeline-step: 11
status: Success-qualified
parent-review: .cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase6-verify-review.md
repair-report: .cg-docs/reviews/2026-09-13-generic-asynchronous-release-controller-step9-fix-triage.md
findings:
  P1.1: fixed
---

# Precommit Repair Verification

**Result: Pass, qualified.** P1.1 is independently confirmed fixed. Both additional Bash fixture failures now pass. No new actionable defect was found in the five repair paths or the adjacent boundaries inspected. This is a report-only repair verification for step 11, not a commit, a full implementation review, a committed gate, or a phase transition.

The parent and repair reports above are the exact user-selected inputs. No report was auto-selected. The parent's fixed frontmatter and its historical failure/open-count body were read together; the historical body was not treated as a new current failure. Neither input report was edited.

## Finding Counts

| Measure | Count |
|---|---:|
| Parent source findings in this repair scope | 1 |
| Confirmed fixed | 1 |
| Still open | 0 |
| New findings | 0 |
| New P0 / P1 / P2 / P3 | 0 / 0 / 0 / 0 |
| Skipped or suppressed findings | 0 |
| Additional failed fixture checks confirmed passing | 2 |
| Required reviewer specs completed | 2 / 2 |
| Incomplete role outputs | 0 |

P1.1 is local to the exact parent report. The two fixture failures were not assigned finding IDs and do not add two source closures. The 71 earlier phase closures remain historical confirmations with their original limits; they were not independently repeated or added to this pass's count. No repair counter or prior closure map changed.

## Repair Results

### P1.1: Clean Default Test Dependency

**Confirmed fixed.** `packages/cg-release/pyproject.toml:17-25` adds `PyYAML==6.0.2` to default `dev` and retains the same separate `gpid-native` pin. The runtime list at lines 6-12 still excludes YAML. `packages/cg-release/uv.lock:32-69,296-329` agrees: PyYAML is in development groups, not the core runtime dependency metadata. Offline lock validation passed with 23 packages resolved.

`packages/cg-release/tests/test_install.py:15-38` tests the actual `FULL_PACKAGE_TEST_COMMAND` from `scripts/cg_pr_preflight.py:30-36`. It adds isolation and collection-only options, not a dependency group. It removes inherited Python variables and `VIRTUAL_ENV`, disables the user site, requires exit 0, and requires authority-test node IDs and the collection summary. Collection does not execute the test again, so this does not recursively run the package suite. Its package ownership also avoids duplicate package execution by the native producer.

Fresh independent full-package collection in an isolated, locked default environment collected **995 tests**, including **18 authority nodes**, with exit 0. No optional group or `--no-sync` was used. The original failing import remains unconditional at `packages/cg-release/tests/test_profile_workflow_authority.py:18`; it was not skipped or made optional. The authority/install selection then passed all 32 cases, including the real preflight-command regression.

The runtime-only wheel boundary also passed. `test_install.py:50-120` builds real sdist/wheel outputs outside the source tree, creates a new environment, exports locked requirements with `--no-dev`, installs those requirements with hashes, and installs the wheel with `--no-deps`. Lines 135-153 query the installed interpreter with `-I` and require that `yaml` is unavailable. The four installed command-help cases and source-free installed profile case passed as adjacent runtime checks. This is installed-package evidence, not just inspection of the dependency list.

The default producer command at `scripts/cg_pr_preflight.py:30-36`, the ordinary workflow invocation at `.github/workflows/tests.yml:253-280`, and the documented command at `docs/release-controller.md:292-310` remain compatible with this repair. The fix does not depend on PyYAML installed into the outer CI interpreter.

### Additional Bash Fixture Failures

**Both confirmed passing.** `scripts/tests/release_shell_fixture.py:140-158` compiles the existing C# dispatcher to neutral `fixture.exe`, then copies that same assembly to the mock package `python.exe` and `pwsh.exe`. This follows the existing CMD construction at lines 80-107. No product routing, authorization, or real publisher operation is substituted by this change.

The new direct regression at `scripts/tests/test_release_controller_launchers.py:18-37` passed for CMD and Bash. Each case starts both PE mock names before product dispatch, deletes the prior argv record between executions, requires exit 37, and compares the complete recorded argument list. The empty string, space and ampersand, embedded quote, and trailing backslash cases remain explicit.

The unchanged real-shell assertions at lines 40-59 also passed for both `--legacy-bridge-bash` and `--legacy-recovery-bash`. They still require exit 37, exact `-NoProfile -File` and `-LegacyOperation Bridge/Recovery` routing, the correct script path, and the original remaining arguments. Core operations still require exact `-I -m cg_release.cli` arguments. Fallback, Store-stub rejection, CMD-shim return, and PATH-shadow anti-recursion cases passed in the same selection. A permissive exit assertion or omitted argv assertion did not conceal the old failures.

Fresh SHA-256 hashes for both launchers and the router match the pre-repair Phase 7 evidence and the step 9 gate snapshots. The fix therefore did not change product launcher bytes to make these tests pass. The lower-level Windows/CLR or host cause of the old copied executable's opaque exit remains unknown. This result verifies the bounded fixture construction correction; it does not establish a general rule about renamed .NET executables or native Unix behavior.

## Reviewer Results

The `.kilo/agents/cg-code-quality.md` spec was read first, then `.kilo/agents/cg-testing.md`. Their review passes were applied in that order in this separate report-only session. No additional Agent Manager session or model switch was used.

**cg-code-quality:** Inspected all five repair files, including the complete lockfile, for dependency separation, coherent pins, minimal fixture changes, error handling, and preserved process/argument boundaries. Checked adjacent launcher/router code, the default preflight command, package build hook, producer tests, authority-test import, and relevant producer/documentation excerpts. No new actionable quality defect was found. Ruff passed without fixes or cache writes. No cosmetic refactor of the repaired blocks is proposed.

**cg-testing:** Checked real environment isolation, actual default command use, collection versus execution, package test ownership, runtime-only installation, direct fixture startup, and exact argv/exit assertions. Ran the focused tests below with fresh isolated environments. No failed, skipped, or missing scoped case was found. The producer/preflight tests exercise mocked process boundaries; this pass did not execute the full native preflight or contact a remote service.

Project instructions, charter/configuration, Python instructions and skill/anti-patterns, and PowerShell/CMD launcher guidance were applied. `open-brain` was not exposed by the available tools. The bounded local query `cg-index query --intent review --query "clean default release gate PyYAML executable fixture" --budget 800 --format md` selected `.cg-docs/solutions/testing-patterns/2026-09-13-clean-default-release-gates-and-executable-fixtures.md` and `.cg-docs/solutions/testing-patterns/2026-08-13-release-gate-fixtures-and-derived-evidence-hashes.md`. Their environment and runtime-boundary lessons informed the checks; the query's index warnings are not test evidence. No Brain or project-memory write was made.

## Fresh Checks

| Check | Result |
|---|---|
| Independent clean default full-package collection | 995 collected; 18 authority nodes; 0.38 seconds; exit 0 |
| Clean default authority and installed-package tests | 32 passed; 0 failed/errors/skipped; 15.30 seconds; exit 0 |
| Clean default launcher, producer, and preflight tests | 90 passed; 0 failed/errors/skipped; 30.19 seconds; exit 0 |
| Ruff: package and two repaired native fixture/test files | Passed; exit 0 |
| Offline locked dependency consistency | Passed; 23 packages resolved; exit 0 |
| Five repaired source blobs, before/after checks | All unchanged; all match step 9 |
| Five adjacent source blobs and two input reports, before/after checks | All unchanged |
| Retained gate result, integrity manifest, package JUnit, Pester snapshot hashes | All match the step 9 records |

The focused package and native runs were sequential. Both installed 23 packages into fresh isolated environments; cached distributions are not reuse of the project venv. For those commands, process-local `UV_OFFLINE=1`, `PYTHONNOUSERSITE=1`, and `PYTHONDONTWRITEBYTECODE=1` were set. The collection-summary wrapper separately removed inherited `PYTHON*`, `VIRTUAL_ENV`, `PYTEST_ADDOPTS`, and `PYTEST_PLUGINS`, then set `UV_OFFLINE=1` and `PYTHONNOUSERSITE=1`. No global environment setting changed. Test roots were new paths under the verified approved Kilo temporary parent; no prior roots were deleted.

Exact test argv, from the worktree root:

```powershell
uv run --isolated --offline --project packages/cg-release --locked --python ">=3.11,<3.13" --no-python-downloads python -B -m pytest packages/cg-release/tests --collect-only -q --tb=short -p no:cacheprovider
uv run --isolated --offline --project packages/cg-release --locked python -B -m pytest packages/cg-release/tests/test_profile_workflow_authority.py packages/cg-release/tests/test_install.py -q --tb=short -p no:cacheprovider --basetemp "C:\Users\wb384996\AppData\Local\Temp\3\kilo\s11rv-pkg-2045-b624" --junitxml "C:\Users\wb384996\AppData\Local\Temp\3\kilo\s11rv-pkg-2045-b624.xml"
uv run --isolated --offline --project packages/cg-release --locked python -B -m pytest scripts/tests/test_release_controller_launchers.py scripts/tests/test_release_producer_contracts.py scripts/tests/test_cg_pr_preflight.py -q --tb=short -p no:cacheprovider --basetemp "C:\Users\wb384996\AppData\Local\Temp\3\kilo\s11rv-native-2045-b624" --junitxml "C:\Users\wb384996\AppData\Local\Temp\3\kilo\s11rv-native-2045-b624.xml"
uv run --isolated --offline --project packages/cg-release --locked ruff check --no-cache packages/cg-release scripts/tests/test_release_controller_launchers.py scripts/tests/release_shell_fixture.py
uv lock --offline --project packages/cg-release --check
```

The first argv was executed through a bounded 180-second subprocess wrapper that returned the collection summary and authority-node count. Its first launch failed with a Python `SyntaxError` because PowerShell removed quotation marks, before it started uv or pytest. Corrected shell quotation produced the passing collection result above. This diagnostic launch error was not a product failure or a source repair. The successful focused tests each used a 300-second tool timeout. Counts overlap with the retained full package and must not be added to full-suite totals as unique coverage.

Fresh JUnit headers were read and agree with the captured pytest results. Complete temporary XML files are retained at the paths above; the long single-line file display was bounded, not a claim to have independently parsed every XML testcase. Their SHA-256 identities are:

| Temporary Artifact | SHA-256 |
|---|---|
| `s11rv-pkg-2045-b624.xml` | `713922a9c36d278cf5a0f21da3e27708a939ce712078d808ddcbeed63b634e27` |
| `s11rv-native-2045-b624.xml` | `6ce253f44faeb349816755bf6845388e83187b2800812b2b5221683b58bc2c49` |

## Source Identity

HEAD before and after the checks is `b94f585c8a485dfb03965ca9711fb83257aaa7de`, branch `improve-cg-release`. `git diff --cached --raw` was empty before and after. The pre-report `git status --short --branch` inventory was unchanged. Existing unrelated changes were preserved.

These are fresh `git hash-object` identities of the dirty working files, not committed source IDs. Both columns match the repair report's final five-path table:

| Repair Path | Before Verification | After Verification |
|---|---|---|
| `packages/cg-release/pyproject.toml` | `e78d51f6651dc1d32ee6f5f9241196bac158f90c` | `e78d51f6651dc1d32ee6f5f9241196bac158f90c` |
| `packages/cg-release/uv.lock` | `33d3f9741077086fca9d8215a7f0fbc0c0e51541` | `33d3f9741077086fca9d8215a7f0fbc0c0e51541` |
| `packages/cg-release/tests/test_install.py` | `f88e5097f3d670455062a0f77dd34352ba4daf05` | `f88e5097f3d670455062a0f77dd34352ba4daf05` |
| `scripts/tests/release_shell_fixture.py` | `e9bd2bae8212b9f8a04edded7b3d9f8ee11975d9` | `e9bd2bae8212b9f8a04edded7b3d9f8ee11975d9` |
| `scripts/tests/test_release_controller_launchers.py` | `3eab36e78f7f5d494acc06a844bb7950fd9e5b45` | `3eab36e78f7f5d494acc06a844bb7950fd9e5b45` |

The following identities were also captured twice and remained equal:

| Adjacent Source or Input | Before = After Git Blob |
|---|---|
| `scripts/tests/test_release_producer_contracts.py` | `4cda9f30ed26c27150bb561a2aa0f7019f311ee4` |
| `bin/cg-release` | `cb1ba4bd6e0d2f1111fad57cb406ed2692a33bb8` |
| `bin/cg-release.cmd` | `13eb2fc3bce6251362add447890f74f72effc51a` |
| `scripts/cg_release_cli.py` | `476f6052599ccf38967aa45dc614d3312724c043` |
| `scripts/cg_pr_preflight.py` | `68d55fc8b7401ff0354696d853c3f1f574c85c12` |
| Exact parent review named in frontmatter | `8137d621eb8773c01a00b6cfa6c6896d0640e83c` |
| Exact repair report named in frontmatter | `617c025c297eb8f679e256e0ac6ab2154b0459c9` |

Fresh exact-byte SHA-256 hashes below match both `source-before.json` and `source-after.json` in `.cg-docs/work-reports/release-controller/2026-09-13-phase7-pkg-165245Z-52219816/`, which precedes step 9. They also match step 9 `source-before.json` and `source-final.json`:

| Unchanged Product Path | SHA-256 |
|---|---|
| `bin/cg-release` | `1b0174cd7b5c65f3404c5a1b28c990a1a2dfa0d8166ae70d630cd7b8f13a4b42` |
| `bin/cg-release.cmd` | `03a27a54753d1dd16ec785f0b4be574824670b4731f5c61a7520b513af9cf3aa` |
| `scripts/cg_release_cli.py` | `e551e071007f747b6ebba997bf5aa4239dbc3c86f7a9b3bcf41911073baf7fdd` |
| `scripts/cg_pr_preflight.py` | `e5d3f12e15d7321bb5ecf97008b8a210a69ae44f9b45be85f79b685ddf6028e5` |

## Retained Gates

The user supplied the current full-gate result and identified the intervening work as documentation compounding only. This pass preserves that evidence rather than rerunning Pester or the full-package execution. It independently checked the scoped source identities above, not the complete 2743-product-file inventory.

Evidence directory: `.cg-docs/work-reports/release-controller/2026-09-13-step9-validation-180003Z-86e3cad4/`. Read `handoff.json`, `result.json`, `integrity.json`, `full-package-execution.json`, complete package stdout/stderr, and `pester-last-run.json`. The raw package output records **995 passed in 1316.49 seconds**; provisioning records 23 packages installed. The execution record confirms isolation, offline default dependencies, no optional-group selection, no `--no-sync`, exit 0, and no timeout. Pester records **2935 passed, 0 failed, 2 skipped**, 2937 total, 21 files, `filteredFiles: null`, and no failed assertions. These are retained executions, not fresh full gates in this session.

Fresh `certutil -hashfile ... SHA256` checks match the retained handoff/manifest:

| Retained Artifact | SHA-256 |
|---|---|
| `result.json` | `72bf406ce119f8b004fd4cc0d52ad22cc6e1098ff58373ed97a8a4e90aca10b0` |
| `integrity.json` | `91f5b6e626d961ddc682a9b671fe578d94ee16b988f8e86ddad5b28f311fe911` |
| `full-package.xml` | `34cbc576eeded882189e0e57ccead4bce6082b92501cae1f82521fc81394c8d3` |
| `pester-last-run.json` | `f3556bf5e0c3213daad763ead762db79943ff9e859db2d4dd363362f3ac3e2ba` |

Pester cleanup remains qualified: 615 diagnostic occurrences, comprising 580 `RemoveFileSystemItemIOError` and 35 `PathNotFound`; `cleanupSucceeded` remains false. The expected negative update-fixture error is separate. Both skips are in `update`; individual runtime names/reasons are not retained and are not inferred. Windows Bash placeholder, Git Bash versus native Unix, adapter-only Kilo containment, direct-child supervision, and ignored raw-log preservation limits remain. Zero failed assertions is not proof of successful cleanup.

## Boundary

This report is the only intentional repository write in this verification. Source files, both input reports, prior evidence, plan, active state, counters, Brain, generated targets, index, branch, and HEAD were not edited. Test/build artifacts are temporary; no existing environment was synchronized. No Pester rerun, full-package execution, prepare/committed preflight, staging, commit, remote command, publication, activation, or phase advance occurred.

The explicitly resolved PR base is `dev`, recorded for context only. It was not used to authorize a PR or any Git operation. The later authorized V8 committed gate and ordinary PR CI remain required and pending. The publisher remains disabled. Decision `D-2026-09-13-defer-live-rollout` and the deferred bridge, native clean-client, release-mode CI, sandbox/security/approval, remote identity, and live performance work remain unchanged and are not marked passed. The present result establishes repair convergence only for the exact parent finding and the two additional fixture failures.
