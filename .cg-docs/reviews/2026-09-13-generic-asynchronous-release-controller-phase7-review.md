---
date: 2026-09-13
depth: full
type: standard
plan: .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md
phase: 7
decision: D-2026-09-13-defer-live-rollout
findings:
  P2.1: open
  P2.2: open
---

# Phase 7 Review

**Review mode**: Embedded `review:auto`, resolved `full`; report only by explicit instruction.
**Coverage**: All 10 requested specs read and emulated in sequence in one session. No separate agents or Agent Manager sessions were started.
**Primary scope**: The 16 files listed in the Phase 7 implementation evidence, plus their direct package, documentation, generated-command and disabled-installation interactions.
**Findings**: 2 (P0: 0, P1: 0, P2: 2, P3: 0). Both remain open; no fixes applied.
**Source**: Dirty `improve-cg-release` worktree at HEAD `b94f585c8a485dfb03965ca9711fb83257aaa7de`. This is not a committed-candidate or complete content-hash attestation.

## Findings

### P0 / P1

No blocking or critical issue found in the reviewed Phase 7 scope. No new authority bypass, publication activation, historical-evidence overwrite, or false live-performance pass was found. This statement does not certify deferred live operation or repeat the entire Phase 1-6 review.

### P2 - Important

**[P2.1]** [cg-data-quality, cg-adversarial] `packages/cg-release/src/cg_release/trials.py:198` - Accepted finite durations can produce an infinite median.

**Issue**: `Seconds` accepts any nonnegative finite float. For an even sample count, `statistics.median(durations)` adds the two middle values before division. Ten otherwise valid receipt samples with `total_seconds=1e308` and `confirmation_seconds=0.0` therefore return `median_seconds=inf`. The correct median is the finite value `1e308`.

**Impact**: A valid, bounded input can produce a summary that is not JSON-safe. The benchmark's `json.dumps(..., allow_nan=False)` at `scripts/benchmark_release.py:157` then raises an uncaught `ValueError`, so no report or structured failure is produced. This needs an extreme input; it does not affect the ordinary measured durations, grant a live pass, or alter release state. Severity is P2, not a silent published-statistics or security failure.

**Executed proof**: Used the existing package interpreter with `-I -B -c`, entirely in memory. The probe validated all ten finite samples, observed `median_is_infinite=True` and `live_handoff_passed=False`, and then serialized the returned result with `allow_nan=False`. It exited 1 with `ValueError: Out of range float values are not JSON compliant: inf`.

**Correction**: Compute the even-count midpoint without overflowing the sum, or reject an explicitly documented unsupported range before computation. Require finite output before returning the summary. Add a regression with large finite middle values and an assertion that the full result serializes with `allow_nan=False`; keep the ordinary median and percentile assertions.

**[P2.2]** [cg-adversarial, cg-testing] `scripts/benchmark_release.py:157-161` - Expected output-file failures escape the structured error boundary.

**Issue**: The `except (ValueError, OSError)` block ends before serialization, parent-directory creation and exclusive output creation. Reusing an evidence output path raises a raw `FileExistsError` and exits 1 instead of returning a bounded error code and safe action. Other output-path `OSError` cases have the same unguarded boundary. Input errors already return the structured `E_BENCHMARK_INPUT` response.

**Impact**: A normal retry with an existing `--output` path is indistinguishable from a program crash to a JSON consumer. The diagnostic also prints the complete caller-supplied path. Exclusive creation correctly preserves the existing file; this is an error-reporting gap, not a clobber or demonstrated credential exposure.

**Executed proof**: Ran the following from the worktree. The input fixture already existed and was also used as the output target. Exclusive creation refused it without changing its contents. The command exited 1 with a traceback at line 160 and `FileExistsError: [Errno 17] File exists`.

```powershell
& "packages/cg-release/.venv/Scripts/python.exe" -I -B scripts/benchmark_release.py --sandbox-config packages/cg-release/tests/fixtures/sandbox.example.json --repository-id 123 --output packages/cg-release/tests/fixtures/sandbox.example.json
```

**Correction**: Put expected serialization/output failures under a bounded CLI error boundary. Preserve exclusive creation and every existing evidence file. Return a documented structured error and an action such as selecting a new output path, without raw exception/path text. Add tests for existing output, unusable output parent and unchanged existing bytes; assert exit code, JSON shape and no traceback. Do not catch unexpected exceptions indiscriminately.

Parsed 2 distinct finding IDs; both are `open`. Missing tests for these two reproduced cases are included in their findings, not counted again.

## Sequential Coverage

### 1. cg-code-quality

No additional code-quality issue found in `trials.py`, `benchmark_release.py` or the three new test modules. Names, strict boundary models, explicit constants and limited responsibilities follow the package conventions.
Reviewed the Python instructions and Python best-practices/anti-pattern skill. The recorded Ruff gate passed. No debug output, stale import, new unresolved TODO or reason for a broad refactor was found; structured CLI stdout is intentional.

### 2. cg-testing

Reviewed `test_sandbox.py`, `test_performance.py`, `test_documentation.py` and their `test_timing.py`, preview and installed-wheel dependencies. All new public harness operations have test coverage; input shape, identity, non-finite durations, failed attempts, offline boundaries and documentation syntax have explicit assertions.
The saved package log confirms execution of the Phase 7 tests. The two reproduced edge cases above are not covered. Four-command parsing and offline preview are not claimed as four live command trials; source-free build/install coverage comes from the existing executed install tests.

### 3. cg-documentation

No additional documentation defect found in the 10 primary documentation/navigation files. Compared installation, line/version rules, flags, portable locator recovery, approval, journal retention, GPID hooks and legacy routing with the current implementation and shared integration contract.
The guide explicitly calls the future live trial path a maintainer procedure, not an implemented unattended driver. It retains all trial obligations, the ten-sample target and V8 sequencing. Site, navigation and documentation freshness checks passed in the supplied evidence.

### 4. cg-version-control

No new secret, tracked build output or Phase 7 commit-hygiene defect found. The index was empty; the existing branch is not `main`. No Phase 7 commit exists, and current remote freshness was not queried.
Checked `.gitignore`, package metadata and local history. Virtual environments/build outputs are ignored and `uv.lock` is not ignored. Read-only `git diff --check` passed with existing LF/CRLF conversion warnings. The pre-existing branch name is not reopened as a Phase 7 defect.

### 5. cg-reproducibility

No additional Phase 7 reproducibility defect found. New harness inputs are explicit, bounded and deterministic; confirmation is the only excluded duration. Missing remote intervals/baseline remain null or missing, not zero.
Checked the locked source-free installation procedure against `test_install.py` and its executed results. The saved evidence records exact argv, runtime, exits and host limits. Dirty path-state stability is explicitly not a cryptographic content identity; the later committed gate is still required. See the local-log retention note below.

### 6. cg-performance

No new performance regression found in the Phase 7 implementation. The local Git benchmark permits three exact local operations; the measurement list is limited to 1,000 records and JSON files to 64 KiB. Sorting this bounded list is appropriate; no new vectorization dependency is warranted.
Accepted the measured package durations, not a guessed hang or speedup: 1338.30 and 1320.33 seconds. The validation evidence attributes the slow paths to repeated offline lifecycle/refresh work and qualifies the earlier 600-second timeout. No full suite was rerun for this review.

### 7. cg-architecture

No new module-boundary or generated-output interaction defect found. `trials.py` has no provider access; the benchmark CLI owns local I/O. Generic use does not acquire the GPID optional-profile dependency. The new guide does not introduce a second publisher or command authority.
Compared canonical release dispatch with Kilo/Codex projections and the shared release-controller contract. Used the executed complete drift/parity and module checks for all adapters. Inspected disabled policy/workflow guards. Ordinary package CI remains separate from disabled release-mode registration. No generation occurred in this review.

### 8. cg-data-quality

Found P2.1. Otherwise strict IDs, duplicate-key rejection, exact interval keys, finite/nonnegative inputs, outcome/error consistency and sample retention are correct for an unverified local summary.
An additional in-memory probe confirmed target acceptance at exactly 120 seconds, rejection above 120 seconds, retention of an unknown attempt, and `live_handoff_passed=False`. No arithmetic output is accepted as independent remote evidence.

### 9. cg-learnings-researcher

No additional finding after comparison with the selected local Brain solutions and the decided controller brainstorm. `open-brain` was unavailable; no remote memory request was made.
Applied the lessons below to error boundaries, generated-evidence authority, process counts and current versus historical timing. The dated scope amendment supersedes earlier live-gate timing clauses, not the underlying safety requirements.

### 10. cg-adversarial

Reproduced P2.1 and P2.2 without network access or source edits. A separate in-memory probe rejected eight malformed inventories: null, empty object, unknown field, boolean repository ID, empty samples, 1,001 samples, missing intervals and coerced boolean text.
No additional exploitable issue found in this Phase 7 scope. Input data does not execute operations or grant authority. The GPID checklist contains all ten deferred case groups; authorization remains false and remote writes remain zero. Existing-output refusal preserved the fixture. No live or cross-platform security claim is made.

## Evidence Used

Primary records, relative to `.cg-docs/work-reports/release-controller/`:

- `2026-09-13-phase7-implementation-evidence.json`: scope, red/green history, generation ordering, previous timeout and restrictions.
- `2026-09-13-phase7-1425Z-validation.json`: latest result at 2026-09-13T15:29:00Z.
- `2026-09-13-phase7-1425Z-final-audit.json`: all 12 stage exits, sequence and path-state qualifications.
- `2026-09-13-phase7-1425Z-package-execution.json`, package log and Pester capture: checked underlying executed evidence rather than only the handoff summary.
- `2026-09-13-phase7-offline-baseline.json`: three local Git calls, one local gate, missing live intervals/baseline.

| Existing Executed Check | Result | Retained Qualification |
|---|---|---|
| Top-level local validation | 12/12 passed; no new timeout or source fix | This is the existing test child's result, not a fresh full rerun by this reviewer |
| Standalone package | 984 passed, 0 failed/errors/skipped/deselected; 1338.30 seconds | Windows Python 3.12.0; not six-host proof |
| Full prepare | 9 selected/executed/passed commands | Prepare mode, not committed mode; exact selected argv retained |
| Native Python inside prepare | 2592 passed, 50 skipped, 2 deselected, 1 warning | Canonical `not integration` selection; no inferred reasons for unnamed skips |
| Package inside prepare | 984 passed; 1320.33 seconds | Overlaps standalone coverage; not 984 additional unique tests |
| Profile/launcher inside prepare | 28 passed | Local host only |
| Node docs automation | 106 passed, 0 failed/skipped | Portable file-link fallback on Windows EPERM is not native file-symlink proof |
| Explicit target/release/update parity | 56 passed, 8 skipped | Three POSIX shims and five POSIX updater cases unavailable on Windows |
| Pester 4.10.1, full safe runner | 2935 passed, 0 failed, 2 skipped, 21 files; `filteredFiles: null` | Full assertion gate, not successful cleanup or native Unix proof |
| Build/install, Ruff, modules | Passed | Existing package and prepare records supply execution evidence |
| Docs freshness/site/release set | Passed; 76 pages, 8 groups, 12 payloads | No generator rerun in review |
| Disabled profile/protected historical diff/plan | Passed | No remote identity or publication inferred |

The counts overlap and must not be added as unique coverage. New review probes are separate: two reproduced error cases exited 1, and the ordinary-boundary and eight-invalid-shape probes exited 0. The former do not rewrite the recorded passing suite totals; they expose missing cases.

## Critical Logs

All existing log paths below are relative to `.cg-docs/work-reports/release-controller/`.

- `2026-09-13-phase7-1425Z-package.log:1025`: `984 passed in 1338.30s`; Phase 7 documentation, performance and sandbox cases appear at lines 234-238, 419-431 and 888-901.
- `2026-09-13-phase7-1425Z-prepare-commands.log`: decoded selected-command output; the native hard-link exclusion warning is recorded at lines 48-54 in the validation evidence.
- `2026-09-13-phase7-1425Z-node.log:108`: Windows EPERM portable file-link qualification; not a failed assertion or native symlink success.
- `2026-09-13-phase7-1425Z-planparity.log:3-6`: explicit eight platform skips and `56 passed`.
- `2026-09-13-phase7-1425Z-pester-last-run.json:1-10`: fresh 15:26:29Z capture, 2935 passed, zero failed, two skipped, no file filter.
- `2026-09-13-phase7-1425Z-pester-stderr-readable.log`: cleanup diagnostics from line 6572 onward; 133 `DirectoryNotFoundException` and 883 `RemoveFileSystemItemIOError` string occurrences per the retained audit. These are repeated diagnostic occurrences, not distinct assertion failures. The intentional missing-target-mapping failure boundary is at lines 2784-2792. No cleanup success or complete CLIXML parse is claimed.
- `2026-09-13-phase7-1425Z-pester-stderr.log` and `2026-09-13-phase7-1425Z-pester.log`: original streams; readable stderr is only a display derivative.
- `2026-09-13-phase7-implementation-evidence.json`: preserves the initial import repair and incomplete 600-second package run. The later complete runs supersede the incomplete gate result, not its history.

The new probe commands/results are recorded in this review's findings and coverage sections. Their short tool diagnostics were not written over any prior log.

**Retention note**: `git check-ignore -v` confirms that the existing global `*.log` rule ignores these local raw logs. JSON/XML captures are not subject to that rule. At the later authorized evidence-staging step, preserve any required raw logs deliberately; do not assume an ordinary directory add will include them. This is a pending staging caution, not a claim that this local gate lacked evidence or a request to change ignore rules during review.

## Scope and Authority

The primary files were:

- `packages/cg-release/src/cg_release/trials.py`
- `packages/cg-release/tests/test_sandbox.py`
- `packages/cg-release/tests/test_performance.py`
- `packages/cg-release/tests/test_documentation.py`
- `packages/cg-release/tests/fixtures/sandbox.example.json`
- `packages/cg-release/README.md`
- `scripts/benchmark_release.py`
- `docs/release-controller.md`
- `docs/navigation.json`
- `docs/versioning.md`
- `docs/development/index.md`
- `docs/workflow.md`
- `docs/reference.md`
- `docs/installation.md`
- `docs/skills/management/maintainers/release.md`
- `README.md`

The review covered all 16 paths in the handoff's `scopeFiles` array. Supporting files and generated projections were inspected only for direct interactions; they are not counted as additional Phase 7 implementation changes.

Read the matching `.kilo/commands/cg-work.md` and `cg-review.md`, review-routing, context-loading, goal-execution, artifact-view and model-advisory contracts, project charter/configuration, `.github/copilot-instructions.md`, Python instructions and relevant skills. The user's no-source-edit instruction overrides default review autofix and interactive triage.

Decision `D-2026-09-13-defer-live-rollout` controls local acceptance. Bridge delivery, native clean clients, registered source-bound release-mode CI, sandbox/approval/security proof, remote identities and live timing remain deferred, not passed. These omissions are not findings. No false claim that they passed was found.

Ordinary PR CI and the separately authorized pipeline step 11 commit plus committed gate remain final V8 obligations. The existing prepare gate cannot replace them. Phase 7 and whole-plan completion metadata remain parent-owned and unchanged. No required safety control or closed Phase 6 finding was waived or rewritten.

Protected assets were retained. No finding recommends deleting, replacing, moving or renaming protected project infrastructure or knowledge. No `.cg-docs/views/**` body or HTML diff was read. No remote operation, source regeneration, commit, push, PR, roadmap change, new Agent Manager session, later `mode:verify`, or pipeline step 8 occurred.

## Related Learnings

- `.cg-docs/solutions/testing-patterns/2026-08-13-release-gate-fixtures-and-derived-evidence-hashes.md`: test the real command boundary and distinguish dirty-worktree checks from exact committed release evidence. Applied without moving the approved later commit gate forward.
- `.cg-docs/solutions/bugs/2026-08-10-typed-invalid-gh-cli-payloads-crash-exit-code-contract.md`: guard downstream shape/output failures as well as input parsing; a raw exit 1 is not a typed protocol error. This supports P2.2 by analogy, not by importing another CLI's numeric exit-code contract.
- `.cg-docs/solutions/bugs/2026-08-26-release-drift-ignore-checks-spawn-thousands-of-git-processes.md`: bound process counts and compare current measurements. Its old fixed N+1 defect is not the diagnosis of this package's 22-minute runtime.
- `.cg-docs/brainstorms/2026-09-11-generic-asynchronous-release-controller.md`: the handoff target is not publication latency; missing baseline forbids a speedup claim. The amended plan controls when live proof is due.

## Handoff

The embedded full review is complete with two open P2 findings and no P0/P1 finding. The existing 12 local gates retain their recorded passing status and qualifications. Review findings are not automatically accepted or fixed. No phase/final completion is recorded by this report.

Capability advice for a later authorized repair: strong evidence-checking and narrow Python regression work, with high review effort; a smaller code-capable option can handle the bounded regression cases. This is advice only. Availability differs by platform and date, and the user selects the model and effort. No model switch or later workflow command was performed.
