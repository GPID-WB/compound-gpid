---
date: 2026-09-11
depth: light
parent-review: .cg-docs/reviews/2026-09-11-generic-asynchronous-release-controller-review.md
type: verification
findings: {}
---

# Release Controller Repair Verification

## Result

All four prior repairs are confirmed: P1.1, P2.1, P2.2, and P2.3.
Remaining findings: 0 (P0: 0, P1: 0, P2: 0, P3: 0).
New findings: 0 (P0: 0, P1: 0, P2: 0, P3: 0).
Incomplete assigned review scopes: 0. Agent coverage: 2/2.

The empty findings map records no open or new verification findings. The four
prior IDs below are confirmation references, not new findings. The parent review
exists and retains its fixed statuses and original review history.

## Scope And Method

Followed the Exact Sequential Child Handoff in
`.cg-docs/work-reports/2026-09-11-generic-asynchronous-release-controller.md:463-486`
and the parent review's Authorized Repair section. Read both local agent specs
and performed cg-code-quality first, then cg-testing, in this dedicated child.
These were sequential in-thread agent passes, not two independent sessions.

Read the local review verification rules, project instructions, charter/config,
context-loading contract, Python instructions, and Python best-practices skill.
Applied the verification guard: always report P0/P1, cross-file breakage, and
genuine fix regressions; do not turn the fixed scopes into a new style-refactor
review. No candidate issue needed suppression.

Examined the repaired package source and tests, preflight implementation and
tests, offline benchmark, native CI producer in `tests.yml`, and the separate
`release-controller-ci.yml` producer. Excluded generated views, environments,
build outputs, caches, unrelated changes, and future phases. Preserved the
protected-artifact constraint from the handoff throughout both passes.

`open-brain` tools were unavailable. Read the directly relevant local solution
`.cg-docs/solutions/bugs/2026-08-26-release-drift-ignore-checks-spawn-thousands-of-git-processes.md`,
which requires observed resource-shape checks, not just correct final results.
This supplied review context, not new runtime evidence.

## Confirmed Repairs

| Prior ID | Result | Current evidence |
|---|---|---|
| P1.1 | Confirmed fixed | `packages/cg-release/src/cg_release/process.py:36-45` rejects authorization keys independently of `redact`. `events.py:10-17,29-31,45-48,60-69` removes complete values, including folded headers, before error/event output. `tests/test_process.py:13-60` covers seven header variants, no process invocation with display redaction disabled, and both output modes. Independent synthetic probes confirmed five variants, five error messages, and ten event outputs without token disclosure. |
| P2.1 | Confirmed fixed | `packages/cg-release/src/cg_release/cli.py:59-68` checks supplied values with `is not None`. `tests/test_contracts.py:134-163` asserts parser rejection and `E_ARGUMENT` from main. Independent probes confirmed all four empty-option combinations for both plan and start, eight cases total. |
| P2.2 | Confirmed fixed | `.github/workflows/tests.yml:245-252` installs `uv==0.11.3` before the native producer. The separate controller workflow also installs the same pin at lines 51-54 and 68-72. `scripts/cg_pr_preflight.py:10-14,877-886,932-943` documents the local prerequisite, checks the exact tool version first, stops on failure, and selects a supported interpreter without automatic Python download. `scripts/tests/test_cg_pr_preflight.py:14-109` checks producer order, wrong/missing uv, route selection, native-list separation, and missing-runtime failure. All 52 preflight tests passed. No new runtime-only dependency was added to the selector import path. |
| P2.3 | Confirmed fixed | `scripts/benchmark_release.py:19-47,59-70,98` restricts allowed local Git operations and counts at the wrapper boundary. `packages/cg-release/tests/test_timing.py:26-68` observes actual Popen calls, compares them with the reported count, blocks other process argv and Python socket connections, and detects an injected duplicate-call defect. Lines 71-107 reject unlisted operations and stop a fourth wrapper call before execution. The real offline subprocess smoke at lines 196-216 remains and passed. |

## Sequential Agent Results

### 1. cg-code-quality

No issues found in the repaired authorization, CLI supplied-option, uv prerequisite,
or offline-process blocks. The changes retain typed errors, explicit process argv,
bounded operations, and the disabled Phase 1 CLI. No broken reference, import,
producer contract, or new security defect was established in the reviewed scope.
Ruff subsequently passed for the package and benchmark.

### 2. cg-testing

No issues found in the repair regressions. Tests check observable rejection and
output rather than only implementation shape. The authorization test disables the
display redactor to prove independent rejection. The benchmark spy sits at Popen,
below the wrapper counter, and its injected defect proves that extra process
execution is detected. Producer tests connect the selected controller route to
the actual native CI setup. All focused tests and corrected independent probes
passed. Existing install and Pester evidence is qualified below.

## Executed Verification

Commands ran from the shared worktree. Package checks used its existing Python
3.12.0 environment without dependency synchronization or installation.

| Check | Command or method | Result |
|---|---|---|
| Package contracts, repair regressions, offline smoke, CI checks | `packages/cg-release/.venv/Scripts/python.exe -B -m pytest packages/cg-release/tests -k "not installed" -q --tb=short -p no:cacheprovider` | 102 passed, 6 deselected, 0 failed |
| Preflight regressions | `python -B -m pytest scripts/tests/test_cg_pr_preflight.py -q --tb=short -p no:cacheprovider` | 52 passed, 0 failed |
| Diagnostics | `packages/cg-release/.venv/Scripts/ruff.exe check --no-cache packages/cg-release scripts/benchmark_release.py` | Passed |
| Independent synthetic probes | Python `-B -c`; mocked subprocess.run; display redactor disabled for argv checks; captured human/JSON events; both CLI commands | 5 authorization variants, 10 event checks, 8 empty-option cases passed |
| Whitespace | `git diff --check` | Passed before this report was added |

The first independent-probe launch failed at Python parsing because PowerShell
removed embedded quote characters. No probe body executed. Corrected command
quoting passed without source/test edits. This was a verification command error,
not a product failure or an implementation recovery attempt.

## Existing Evidence And Limits

- Read `tests/last-run.json` directly: ranAt `2026-09-11T18:31:09Z`, passed true,
  totalCount 2906, passedCount 2904, failedCount 0, skippedCount 2, failures [],
  filteredFiles null. The create-release row is 95 passed with no failures/skips.
- Both Pester skips belong to update. Their names/reasons are not present in the
  summary. No Pester command was run by this verification child.
- The supplied TestDrive cleanup errors remain a known qualification. Successful
  cleanup and a root-cause repair are not claimed. The runner reports zero test
  failures; no evidence was found that these errors invalidate the four repairs.
- Six installed-wheel tests were deliberately deselected to avoid repeating
  build/install work in this bounded pass. The implementation report records
  108/108 package tests and a passing actual package-only prepare preflight after
  repair. That remains supplied evidence, not an independently repeated install.
- No remote six-cell CI run, live publication, speedup, Python 3.8 execution, or
  Python 3.11 execution is claimed by this child. The benchmark process/socket
  guards are regression checks, not a general operating-system network sandbox.
- The worktree contains existing modified and untracked files. The Pester
  gitSha `b94f585` alone does not identify their exact contents.

## Disposition

The four repaired findings pass independent scoped verification. No remaining or
new finding blocks this repair handoff. Phase completion and later-phase admission
remain the parent's decision. No implementation edits, parent-review edits,
completion metadata, pipeline steps, commits, pushes, PRs, or remote writes were
performed. This verification report is the only authored file.
