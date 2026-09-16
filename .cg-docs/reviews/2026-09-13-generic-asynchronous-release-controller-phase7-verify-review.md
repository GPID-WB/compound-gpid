---
date: 2026-09-13
depth: light
type: verify
plan: .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md
phase: 7
decision: D-2026-09-13-defer-live-rollout
findings:
  P2.1: fixed
  P2.2: fixed
---

# Phase 7 Repair Verification

## Findings

**Confirmed fixed: 2. Open: 0. Unverified: 0. New findings: 0.** These counts cover only the two Phase 7 P2 repairs and their direct regression boundaries. No P0, P1, P2 or P3 finding was added.

| Original Finding | Independent Result | Evidence |
|---|---|---|
| P2.1: finite durations can produce an infinite median | Confirmed fixed | `trials.py:184-192` uses an overflow-safe midpoint for ordered nonnegative values and rejects a non-finite result. Large equal, maximum finite, unequal, odd, zero, subnormal and ordinary cases passed. Both real CLI file output and stdout accepted maximum-finite measurements as strict JSON. |
| P2.2: output-file failures escape the structured error boundary | Confirmed fixed | `benchmark_release.py:158-175` guards serialization, parent creation, exclusive creation, writing and context-manager close. Existing-file, parent-file, directory, retry and input/output-alias cases returned exit 2 with `E_BENCHMARK_OUTPUT`, a safe action and empty stderr. Existing bytes remained identical. Injected write/close errors and a collision at exclusive creation also passed. |

Current source references are relative to the worktree: `packages/cg-release/src/cg_release/trials.py` and `scripts/benchmark_release.py`. The original review remains unchanged, including its historical `open` statuses. This separate report records independent closure, not a rewrite of the original evidence.

## Scope and Method

Read the exact handoff in `.cg-docs/work-reports/release-controller/2026-09-13-phase7-review-repair1-evidence.json`, the original `.cg-docs/reviews/2026-09-13-generic-asynchronous-release-controller-phase7-review.md`, and the retained `2026-09-13-phase7-1425Z-validation.json` before verification.

Reviewed the five repair paths: `trials.py`, `benchmark_release.py`, `test_performance.py`, `test_sandbox.py` and `docs/release-controller.md`. Supporting scope was limited to timing/documentation fixtures, installation test coverage, the approved deferral and disabled installation controls. No broad Phase 1-6 review or full ten-spec review was repeated.

The requested specs were read and emulated sequentially in this session: first `.kilo/agents/cg-code-quality.md`, then `.kilo/agents/cg-testing.md`. No separate agent or Agent Manager session was started. The explicit report-only instruction controlled the work; no source repair or automatic triage was performed.

### 1. Code Quality

No new finding. The midpoint relies on validated, finite, nonnegative, ordered durations; subtraction cannot overflow that domain. Odd medians and nearest-rank p95 are unchanged. The finite guard is explicit. The CLI catches only expected `ValueError` and `OSError` classes and retains `open("x")`; there is no overwrite or deletion fallback. Structured stdout is intentional, not diagnostic logging.

Read the project/Python instructions and Python skill, including the anti-pattern reference. Fresh Ruff passed before the testing review started. `open-brain` was not available in this session. Local saved context and the two relevant existing solutions were consulted: `2026-08-10-typed-invalid-gh-cli-payloads-crash-exit-code-contract.md` and `2026-08-13-release-gate-fixtures-and-derived-evidence-hashes.md`. Current files and the dated scope decision controlled the conclusions.

### 2. Testing

No new finding. The repair tests exercise observable behavior with finite/JSON assertions, real CLI subprocesses, bounded timeouts, temporary paths and exact existing-byte comparisons. Original ordinary median/p95, confirmation exclusion, failed/blocked/unknown attempts, identity/shape validation, offline process budget and documentation checks remain covered.

The independent probes did not import repair test helpers. They verified that `cg_release.trials` came from this worktree, compared numeric cases with a `Fraction` reference using a one-ULP tolerance, and exercised the real CLI plus narrow injected failure boundaries. Unexpected serialization `TypeError` still propagates; no indiscriminate exception catch was introduced.

## Fresh Execution

All commands below exited 0. Verification used the existing package environment on Windows, Python 3.12.0. No package dependency installation or synchronization was requested.

| Check | Result |
|---|---|
| Focused performance, sandbox, timing and documentation suite | 59 passed in 3.10 seconds; no reported failures, skips or deselections |
| Independent local probe script | 37 assertion groups passed; seven real CLI children, each bounded to 20 seconds; outer bound 180 seconds |
| Ruff for package and benchmark | All checks passed; no autofix or cache write requested |
| Disabled installation `--check` | Passed without generation or activation |
| Documentation site | Passed: 76 navigable Markdown pages, 8 groups, complete skills catalog |
| Documentation freshness `--all --check` | Complete build current; no generation performed |
| Protected historical release diff | Empty; tracked payloads and attestations unchanged |

Exact focused command, run from the worktree root:

```powershell
uv run --offline --project packages/cg-release --locked --no-sync python -B -m pytest packages/cg-release/tests/test_performance.py packages/cg-release/tests/test_sandbox.py packages/cg-release/tests/test_timing.py packages/cg-release/tests/test_documentation.py -q --tb=short -p no:cacheprovider --basetemp "C:\Users\wb384996\AppData\Local\Temp\3\kilo\phase7-verify-20260913-1550"
```

The approved temporary parent existed and the selected test root did not exist before execution. No old test root was deleted. Exact probe command:

```powershell
& "packages/cg-release/.venv/Scripts/python.exe" -I -B "C:\Users\wb384996\AppData\Local\Temp\3\kilo\phase7-verify-probes-20260913-1550.py" "E:\PovcalNet\01.personal\wb384996\GPID-team\compound-gpid\.kilo\worktrees\improve-cg-release"
```

The probe source is outside the repository. Its fixtures use a separate temporary directory. GitHub token variables were omitted from real CLI child environments without logging their values. The CLI ran only explicit synthetic sandbox-plan/measurement operations. In-memory numeric/planning probes prohibited process and network access.

| Independent Probe Group | Count | Observed Boundary |
|---|---|---|
| Numeric cases | 10 | Large equal/unequal/max values, zero-to-max, adjacent max floats, odd/ordinary unsorted samples, single zero, equal minimum subnormals and 1,000 samples; finite median, min/p95 and strict JSON |
| Nearby arithmetic/retention | 4 | Maximum confirmation subtraction, target exactly 120 seconds, next float above 120 seconds, retained unknown attempt |
| Invalid inputs | 8 | Empty/over-limit samples, NaN, infinity, negative and boolean duration, wrong repository ID and missing intervals all rejected |
| Offline plan | 1 | Ten GPID case groups remain deferred; authorization false and remote writes zero; no process/network access |
| Real CLI | 7 | Maximum-finite file output and stdout, success then retry, input/output alias, existing binary file, unusable parent and directory target |
| Serialization order | 1 | Non-finite injected report returns the structured output error before creating even the output parent |
| Expected I/O failures | 4 | Injected mkdir/open/write/close `OSError` returns bounded JSON, exit 2 and empty stderr; synthetic private-path marker absent |
| Exclusive collision | 1 | A file inserted at the final open boundary wins; its exact bytes survive refusal |
| Unexpected error | 1 | A non-serializable programming object raises `TypeError`, not a false success or indiscriminate handled error |

For each expected output failure the probe required exactly `code` and `message`, at most 256 stdout characters, `E_BENCHMARK_OUTPUT`, the new-writable-path action, no traceback and empty stderr. Write/close faults used injected streams, not a physical disk-full experiment. The collision was injected at the exclusive-open boundary, not claimed as a multi-host concurrency trial.

Other exact commands:

```powershell
uv run --offline --project packages/cg-release --locked --no-sync ruff check --no-cache packages/cg-release scripts/benchmark_release.py
& "packages/cg-release/.venv/Scripts/python.exe" -I -B scripts/release_profile_install.py --check
node scripts/check-docs-site.js
node scripts/rebuild-docs.js --all --check
git diff --exit-code -- releases .github/shared/skill-management/release-attestations
```

The results above were observed through tool execution and recorded here. No prior raw log or JSON evidence file was replaced.

## Evidence Age

| Evidence | Correct Interpretation |
|---|---|
| Retained `2026-09-13-phase7-1425Z-validation.json` | All 12 full local gates passed before the two repairs. Package: 984 passed in 1338.30 seconds standalone and 1320.33 seconds inside prepare. These overlapping runs are not a current full post-repair pass. |
| Repair record at 15:45:19Z | Reports 59 focused tests in 5.34 seconds and 13 build/install tests in 7.30 seconds after repair. This reviewer independently repeated the 59-test selection, not the 13 installation tests. |
| This verification | Fresh 59-test selection, 37 independent probe groups and the checks above. Probe groups are not additional package test cases. Counts overlap and must not be added as unique coverage. |

No uncovered packaging, dependency, publisher or workflow impact justified another full package/prepare/Pester run. The retained Pester result remains 2935 passed, 2 skipped, with its cleanup diagnostics and native-host limits intact. Earlier platform skips and portable-link limitations are not removed by this report. The existing raw-log retention caution also remains: ignored `*.log` files are not automatically included by a later ordinary directory add.

## Source Identity

HEAD was `b94f585c8a485dfb03965ca9711fb83257aaa7de` in the existing dirty `improve-cg-release` worktree. `git hash-object -- <paths>` returned the same Git blob identities before and after verification for all five repair paths and both input review records:

| Path | Git Blob ID |
|---|---|
| `packages/cg-release/src/cg_release/trials.py` | `2583fedabca5033ba2404e6b8bcadf7540791952` |
| `scripts/benchmark_release.py` | `b1f6653364e3fa05350e019d757eabaafcab8385` |
| `packages/cg-release/tests/test_performance.py` | `c2186cfa3a8b3f9e5ae1b14cddae33ddb649a15c` |
| `packages/cg-release/tests/test_sandbox.py` | `0e78d7ec81a6bebfa14081aba0a62245078c316b` |
| `docs/release-controller.md` | `d8c3b9ead2083ffd11cc187720c8837d2f2b747c` |
| Original Phase 7 review | `3091a6e20e9d9c44dd6f4fd20d1ac7d40d5c45cb` |
| Repair 1 evidence JSON | `b26e671f5a53861574397e13075319f4ae43d03b` |

These are scoped Git blob identities, not an attestation of the complete dirty worktree or an exact committed candidate. The temporary probe and normal test fixtures are not product changes. This review file is the only repository content manually created by this reviewer.

## Authority and Recommendation

The accepted decision `D-2026-09-13-defer-live-rollout` remains in force. `.release-controller.json:3` is still `enabled: false`. Installed control/build/publish/docs guards and release-mode CI/bridge false guards remain disabled; the installation check passed. Ordinary PR CI remains a separate required final obligation.

Bridge delivery, native clean-client qualification, registered source-bound release-mode CI, sandbox/security/approval trials, exact remote identities and live timing are deferred, not passed. Their accepted absence is not a new finding. No speedup or live handoff pass is inferred from local arithmetic.

**Recommendation: accept P2.1 and P2.2 as independently confirmed fixed.** No further repair is required within this verification scope. The parent can use this evidence for the Phase 7 local checkpoint under the accepted deferral. This report does not change phase completion, counters, plan state or active state. V8 and whole-plan acceptance remain pending the later separately authorized committed gate and ordinary PR CI.

No source edit, regeneration, remote operation, writer activation, commit, push, PR, later `mode:verify` command or pipeline step 8 was performed. No protected infrastructure or historical evidence was deleted, replaced, renamed or moved.
