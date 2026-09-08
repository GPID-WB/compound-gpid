---
description: "Check CI status on current PR, classify failures, and auto-fix with review agents. Use --propose for observe-only diagnosis."
---

# Verify PR

You are a senior developer checking whether the current pull request's CI checks are passing, diagnosing failures, and (in the default mode) applying fixes automatically.

## File Permissions

- **READ**: Any file in the workspace.
- **MODIFY**: Source and test files related to CI fix (auto-fix mode only).
- **NEVER**: Modify `.cg-docs/` files, plan files, or `roadmap.json` directly.
- **`--propose` mode**:
  - READ-only.
  - No file creation or modification.
  - No git commits or pushes.
  - No CI-triggering or externally visible actions.

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md` in the project root for project context. If it does not exist, skip silently — this command is project-agnostic.
2. Read `compound-gpid.local.md` for user config if it exists; skip silently otherwise.
3. Read `compound-gpid.context.md` for project-specific context if it exists; skip silently otherwise.

### Step 0.6: Parse Invocation Flags

*(No prior-work scan — this command is stateless.)*

Check user input for the `--propose` flag:
- **Default (no flag)**: **auto-fix mode** — classify failures, dispatch agents, apply fixes, commit, push.
- **`--propose`**: **observe-only mode** — classify failures and present findings with suggested fixes. No file modification, no commits, no pushes.

Announce the active mode:
> "Running in **[auto-fix / observe-only (--propose)]** mode."

### Step 1: Pre-flight Checks And PR Base

1. Check `gh` CLI availability:
   - PowerShell: `Get-Command gh -ErrorAction SilentlyContinue`
   - bash/zsh: `command -v gh`
   - If `gh` is not found:
     > "`gh` CLI is required for `/cg-verify-pr`. Install it:
     > - Windows: `winget install GitHub.cli`
     > - macOS: `brew install gh`
     > - Linux: see https://cli.github.com/
     >
     > Cannot proceed without `gh`."
     Halt.

2. Check authentication: `gh auth status`
   - If not authenticated:
     > "Not authenticated with GitHub. Run `gh auth login` and try again."
     Halt.

3. Run `git branch --show-current` to get the current branch.
   - If output is empty: halt with "You appear to be in detached HEAD state. Checkout a branch first: `git checkout -b feat/<name>`"

4. Find the open PR for this branch and request the actual base in the same metadata query:
   ```
   gh pr view --json number,title,state,headRefName,baseRefName,statusCheckRollup
   ```
   - If the command fails because no PR exists, or the returned `state` is not `OPEN`:
     > "No open PR found for branch `<branch>`. Run `/cg-commit-push-pr` first to push and open one."
     Halt.
   - If metadata is missing, malformed, or does not contain a non-empty `baseRefName`, halt:
     > "The open PR's actual base branch could not be resolved. No fetch, comparison, preflight, rebase, or repair is safe until `baseRefName` is available."
   - Store the PR `number`, `title`, `headRefName`, `statusCheckRollup`, and the actual PR `baseRefName`.
   - Set `$baseBranch` exactly to that actual `baseRefName`. Do not infer it from a remote symbolic ref, a local default branch, or any other fallback. Every base-sensitive operation below uses `$baseBranch`.

### Step 2: Check CI Status

1. Parse `statusCheckRollup` from the PR view JSON. GitHub can return both
   `CheckRun` and `StatusContext` objects. Validate the provider-specific shape,
   then normalize every accepted entry to the internal fields `name`, `status`,
   `conclusion`, and `detailsUrl` before classification.

    - If `statusCheckRollup` is `null`, the key is absent, or the array is empty (`[]`): respond with "\u23f3 No CI checks have run yet on this PR. Wait for checks to start and re-invoke `/cg-verify-pr`." and halt.
    - A `CheckRun` is well-shaped only with a non-empty string `name`, a recognized
      `status` (`COMPLETED`, `IN_PROGRESS`, `QUEUED`, or `EXPECTED`), a recognized
      `conclusion` (`SUCCESS`, `NEUTRAL`, `SKIPPED`, `CANCELLED`,
      `ACTION_REQUIRED`, `STALE`, `FAILURE`, `TIMED_OUT`, or `null`), and a
      `detailsUrl` key whose value is a string or `null`.
    - A `StatusContext` is well-shaped only with a non-empty string `context`, a
      recognized `state` (`SUCCESS`, `FAILURE`, `ERROR`, `PENDING`, or `EXPECTED`),
      and a `targetUrl` key whose value is a string or `null`. Normalize it as:
      `context` to `name`; `targetUrl` to `detailsUrl`; `SUCCESS` to
      `COMPLETED/SUCCESS`; `FAILURE` or `ERROR` to `COMPLETED/FAILURE`; `PENDING`
      to `IN_PROGRESS/null`; and `EXPECTED` to `EXPECTED/null`.
    - Reject every other `__typename` and every malformed or unknown provider value.
      Halt with: "CI check metadata is malformed or uses an unknown
      status/conclusion. Manual diagnosis is required; no check may drive an
      auto-fix." Do not classify or mutate from unvalidated metadata. Classification
      below uses only the normalized list.

2. Classify overall status:
   - **All passing** (all `conclusion` values are `SUCCESS`, `NEUTRAL`, or `SKIPPED`):
     > "✅ All CI checks are passing. Nothing to fix."
     Halt with success.
   - **Pending** (any check has `status: IN_PROGRESS` or `status: QUEUED` and `conclusion: null`):
     > "CI checks are still running. Try again in a few minutes."
     Halt.
   - **Manual action required** (any check has `conclusion: ACTION_REQUIRED` or `conclusion: STALE`): halt with "Check `<name>` requires manual action — not auto-fixable."
   - **Cancelled** (any check has `conclusion: CANCELLED`): treat as non-blocking (skip for fix purposes; note in classification).
   - **All non-failing** (all remaining checks are `CANCELLED`, `SKIPPED`, `NEUTRAL`, or `SUCCESS` after excluding `FAILURE`/`TIMED_OUT`):
     > "✅ No failing checks. Nothing to fix."
     Halt.
   - **Failing**: at least one check has `conclusion: FAILURE` or `conclusion: TIMED_OUT`. Proceed to Step 3.

3. List failing checks by name and conclusion:
   > "Failing checks:
   > - `<workflow-name>` on `<platform>`: FAILURE
   > - ..."

### Step 3: Fetch The Exact Failed Job Log

For every failing check, use only that check's `detailsUrl` from `statusCheckRollup`:

1. Read `check.detailsUrl` from the same failed check object. Do not derive a URL from the workflow name, branch, check name, or another run.
2. Recognize only a GitHub Actions job URL with both numeric IDs. The accepted shape is:
   ```
   https://github.com/<owner>/<repo>/actions/runs/<run-id>/job/<job-id>
   ```
   Parse only URLs matching the equivalent anchored pattern
   `^https://github\.com/[^/]+/[^/]+/actions/runs/(?<runId>[0-9]+)/job/(?<jobId>[0-9]+)(?:[/?#].*)?$`.
   Reject missing URLs, non-GitHub URLs, non-Actions URLs, URLs without a run ID, URLs without a job ID, and unparseable URLs.
3. For a recognized URL, report the exact identifiers before reading logs:
   > "Failed check `<name>`: run ID `<run-id>`, job ID `<job-id>`."

   Retrieve only that job's failed output:
   ```
   gh run view <run-id> --job <job-id> --log-failed
   ```
   The command must use the parsed run and job IDs. Never substitute a run selected by workflow name, branch, recency, or a latest-run heuristic.
4. If `detailsUrl` is absent, non-Actions, unparseable, or the exact job log is unavailable or empty, do not guess. Report:
   > "Manual diagnosis required for `<name>`: the exact Actions run/job log is unavailable. No run found for workflow `<workflow-name>` is not evidence for selecting another run."

    Use this manual provider/UI diagnosis route: open the failed check's details URL in the GitHub UI when one exists, select **View details** for the failed job, and obtain the exact run ID, job ID, job summary, annotations, and failed-step output from the check provider. If the URL is absent, ask a maintainer to provide the provider's job URL or exact IDs and log. Once exact IDs are available, the command above is the only permitted log retrieval route. Do not auto-fix from an absent or unrelated log. There is no run list fallback and no latest-run heuristic.
5. Classify each retrieved failure by pattern-matching the exact job log output:

   | Category | Log patterns |
   |----------|-------------|
   | **Lint/Type errors** | `ESLint`, `mypy`, `lintr`, `pylint`, `styler`, `flake8`, `ruff`, `hadolint`, type annotation errors |
   | **Test failures** | `FAIL`, `pytest`, `testthat`, `Pester`, `FailedCount`, `assert`, `AssertionError`, `Expected:`, `Actual:` |
   | **Build errors** | `ModuleNotFoundError`, `ImportError`, `PackageError`, `cannot find package`, `compilation failed`, `No such file or directory` |
   | **Platform-specific** | Check passes on one OS runner but fails on another (for example, `ubuntu-latest` passes and `windows-2022` fails) |
   | **Unknown** | Does not match any above pattern |

6. Present classification:
   > "CI failures classified:
   > - 🧪 Test failures (N): `<file>`, `<file>`
   > - 🔧 Lint/type errors (N): `<file>`
   > - 🏗️ Build errors (N): `<file>`
   > - 🖥️ Platform-specific (N): `<platform>` only — `<check-name>`
   >
   > [Auto-fix mode: applying fixes now. | Propose mode: see suggested fixes below.]"

### Step 4: Fix Round

*(Auto-fix mode only. In `--propose` mode, skip all of Step 4 and continue to Step 6. Observe-only mode must not fetch, rebase, modify, stage, commit, push, or trigger CI.)*

Run this first and capture its complete output and exit code:
```
$preFixStatus = git status --porcelain
$preFixStatusExit = $LASTEXITCODE
```

**Before any auto-fix**, require `$preFixStatusExit -eq 0` and store the result as `$preFixStatus`. If the command fails or the result is non-empty, halt immediately. Treat any index status as pre-existing staged work, any worktree status as pre-existing unstaged work, and `??` as a pre-existing untracked file. Do not clean, stash, reset, stage, or overwrite user work. A dirty index or worktree is a hard stop.

If `$preFixStatus` is empty, continue only with a clean worktree. Do not begin a rebase or apply a source change before this check.

**Round cap and base-aware branch preparation**:

1. Fetch and validate only the resolved PR base before inspecting history:
   ```
   git fetch origin $baseBranch
   git merge-base HEAD $baseBranch
   git merge-base --is-ancestor origin/$baseBranch HEAD
   ```
   Require exit code zero and a non-empty merge-base from every command. If fetch,
   merge-base, or ancestry validation fails, halt with the exact command error;
   never count trailers or compare changes against an unavailable revision.
   - `$LASTEXITCODE -eq 0` for ancestry means the branch is not behind the fetched PR base; proceed.
   - `$LASTEXITCODE -ne 0` means the base has moved ahead; attempt:
     ```
     git rebase origin/$baseBranch
     ```
     - **Clean rebase**: set `$rebased = $true`, recompute `$mergeBase` with `$baseBranch`, validate it again, and then re-check the trailer cap only in the new `$mergeBase..HEAD` range.
     - **Simple conflict** (single file, fewer than 10 lines): show the conflicting region, propose a resolution, and ask for confirmation before continuing.
     - **Complex conflict**: halt with:
       > "Merge conflict in `<file>` needs interactive resolution.
       > Resolve manually: edit the file, then `git add <file>` and `git rebase --continue`.
       > Then re-invoke `/cg-verify-pr`."
2. Set `$mergeBase` from the validated current branch and PR base, using the first
   returned line when multiple merge bases are reported. Inspect only commit bodies
   in `$mergeBase..HEAD`:
   ```
   git log --first-parent --format=%B $mergeBase..HEAD
   ```
3. A CI-fix round is one commit whose body contains the exact trailer `CI-Fix-Round: <PR-number>/<round-number>`. Retain only trailers for the current PR number and count unique round numbers in `$mergeBase..HEAD`. Do not count historical `fix(ci):` subjects without this trailer; they are not evidence of a round for this PR.
4. If two unique current-PR round numbers already exist:
   > "2 fix rounds already attempted. Remaining CI failures require manual intervention. Review the exact failed job log using its reported run ID and job ID."
   Halt. Otherwise choose the next unused round number, `1` or `2`.
5. After the clean branch preparation, record the clean baseline commit and status:
   ```
    $baselineCommit = (git rev-parse HEAD)
    $baselineCommitExit = $LASTEXITCODE
    $baselineStatus = (git status --porcelain)
    $baselineStatusExit = $LASTEXITCODE
    ```
    Require `$baselineCommitExit -eq 0`, `$baselineStatusExit -eq 0`, and
    `$baselineStatus` to be empty. Report `$baselineCommit` and the clean baseline
    status before any fix edit. This baseline is the boundary for all later staging.

**Focused local reproduction and Kilo capability routing**:

6. Derive the committed PR changed-file set only after `$baseBranch` and `$mergeBase` are resolved:
   ```
   git diff --name-only $mergeBase..HEAD
   ```
   Preserve the repository-relative paths as repeated `--changed-file` arguments. If no exact changed-file set can be obtained, halt rather than compare an inferred revision.
7. Ask the authoritative preflight selector for the exact focused local reproduction, using the resolved base and every changed file:
   ```
   python scripts/cg_pr_preflight.py --phase prepare --base $baseBranch --changed-file <path-1> --changed-file <path-2> --selection-only --format json
   ```
   Read its `changed_files`, `selected_commands`, `pester_files`, `selection_error`, and any Kilo capability record. A selection error, nonzero result, or partial result is a hard stop.
8. Run the exact focused local reproduction selected by `scripts/cg_pr_preflight.py` with the same `$baseBranch` and changed-file arguments. For the selected native target, use:
   ```
   python scripts/cg_pr_preflight.py --phase prepare --base $baseBranch --changed-file <path-1> --changed-file <path-2> --run-native-target --format json
   ```
   If the selector returns registered Pester groups, run only those groups through the safe runner (`. tests\Run-Tests.ps1 -File <registered-name>`) and read `tests/last-run.json`; never run a Pester directory or an unselected suite. Apply a fix only when the focused reproduction matches the failed check. If it does not reproduce, halt for manual/platform diagnosis instead of guessing.
9. Consume the existing Kilo capability adapter and preserve its source status, exit code, version, executable hash, launcher requirement, and inventory evidence. Do not rename source statuses such as `ok`, `ok-no-coexistence`, `missing-kilo`, `unsupported-kilo-version`, `local-projection-missing`, `local-projection-invalid`, `local-content-invalid`, `local-inventory-missing`, `containment-unhonored`, `host-command-error`, and `host-schema-error`. `generic-not-applicable` is a neutral capability result for an absent or unsupported host and is not certified-host integration evidence. `certified-ready` is reported only when the certified evidence is present. Blocking configuration, content, containment, malformed, or unknown Kilo outcomes halt with their existing status and remediation; do not invent a new Kilo vocabulary.
   - The only local-reproduction exception is an **externally confirmed certified-host failure** whose exact Actions job log proves that the failure is host-dependent. Route that case to the certified-host remediation path and do not apply a generic linker fix.
   - Missing Kilo host evidence is not proof of Kilo integration. Generic linker failure evidence never proves Kilo integration. Deterministic Kilo behavior remains part of the selected generic preflight.

**Apply fixes by category**:

1. **Lint/Type errors**: Dispatch `@cg-fix-problems` with the relevant files and exact errors from the failed job log.
2. **Test failures**: Read the exact failure output carefully. Apply a targeted fix to the source file. If the root cause is unclear, dispatch `@cg-testing` for analysis first.
3. **Build errors**: Dispatch `@cg-code-quality` to analyze the dependency/import error; then apply the fix based on its diagnosis.
4. **Unknown**: Apply a best-effort targeted fix based on the exact log output only; note what was attempted.
5. **Platform-specific or certified-host failures**: follow the manual or certified-host remediation path when the focused local reproduction is unavailable. Do not claim the branch is fixed from a generic host or linker result.

**Commit and push fixes**:

1. After applying only the targeted fix, run:
   ```
   git diff --stat HEAD
   git status --porcelain
   ```
   Enumerate tracked paths changed after `$baselineCommit` with `git diff --name-only $baselineCommit` and `git diff --cached --name-only $baselineCommit`, and enumerate new paths from the post-baseline status. The stage set must be the intersection of those post-baseline paths and the targeted fix set from the exact failure. If any path outside that set changed, halt and leave it unstaged; never absorb it into the repair.
2. Do not use `git add .` or any broad staging command. Stage only the selected post-baseline paths individually:
   ```
   git add <targeted-post-baseline-files>
   ```
   Verify the `git add` exit code. If it is nonzero, report the exact Git error and halt without committing or pushing. Verify `git diff --cached --name-only` contains only the targeted post-baseline paths.
3. Collapse every correction from this verification pass into exactly one `fix(ci)` commit with exactly one unique current-PR trailer:
   ```
   git commit -m "fix(ci): <brief description of what was fixed>" -m "CI-Fix-Round: <PR-number>/<next-round>"
   ```
   Verify the `git commit` exit code. If it is nonzero, report the exact Git error and halt without pushing. Then verify `git show -s --format=%B HEAD` contains one and only one `CI-Fix-Round: <PR-number>/<next-round>` trailer and no second fix-round trailer.
4. Push only after the commit succeeds:
   - If `$rebased = $true`, run `git push --force-with-lease origin <branch>` and never plain force. A failed force-with-lease push must report the exact error and advise `git fetch`, inspect new remote commits, and re-invoke `/cg-verify-pr`.
   - If no rebase occurred, run `git push origin <branch>`.
   Verify the push exit code and report the exact failed-check run/job IDs that led to this one-round repair.

**Post-push notification**:

After pushing, run one non-blocking CI status poll with `gh pr checks <number>` or `gh pr view --json statusCheckRollup` to confirm whether checks have restarted. Do not use `--watch`. If checks are still pending or have not refreshed yet, tell the user to re-invoke `/cg-verify-pr` after checks complete. Report any new exact Actions run/job IDs from the refreshed `statusCheckRollup`; never replace them with an inferred latest run.

Shell note: examples using `$null`, `$LASTEXITCODE`, or `Select-Object` are PowerShell syntax. In bash/zsh, use `/dev/null`, `$?`, and `head -n 1` or equivalent shell pipelines.

> "Fixes committed and pushed (round N/2). CI is now re-running.
> Re-invoke `/cg-verify-pr` after checks complete to verify, or apply a second fix round if still failing."

### Step 5: Cross-Platform Notification

After classifying (or fixing) failures, if any failures are **platform-specific**:
> "⚠️ **Platform-specific failure detected**: CI passes on `<platform-A>` but fails on `<platform-B>`.
>
> The fix applied is based on CI log inference — local testing on `<platform-B>` is not possible from this environment.
>
> **This branch is NOT deployment-ready** until checks pass on all platforms.
>
> Suggested next steps:
> - Ask a team member with `<platform-B>` access to verify the fix locally.
> - Push and wait for the next CI run to confirm."

### Step 6: Summary and Handoff

Before the prose summary, output a markdown table with exactly these columns:

| Check Name | Prior Status | New Status | Action Taken |
|------------|--------------|------------|--------------|
| `<check>` | `<failure/pending/etc.>` | `<fixed/re-running/manual/etc.>` | `<commit/proposal/none>` |

- **Auto-fix mode**:
  > "✅ CI verification complete.
  > - Fix round: N/2
  > - Files modified: N
  > - Commits pushed: N
  > - CI status: [re-running — wait and re-invoke `/cg-verify-pr` to confirm | 2 rounds exhausted — manual intervention required]
  > - Triggering failed job: run `<run-id>`, job `<job-id>`
  >
  > PR: <URL>"

- **Observe-only mode (`--propose`)**:
  > "CI diagnosis complete. **No changes were made.**
  >
  > Suggested fixes:
  > - Test failures: <description of root cause and suggested fix>
  > - Lint errors: <specific files and rules violated>
  > - Build errors: <missing package or import>
  >
  > To apply fixes automatically: `/cg-verify-pr` (without `--propose`)
  > To apply manually: address the issues above, commit, and push."

## OpenCode Invocation Arguments

User-provided slash-command arguments:

```text
$ARGUMENTS
```
