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

### Step 1: Pre-flight Checks

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

4. Find the PR for this branch:
   ```
   gh pr view --json number,title,state,headRefName,statusCheckRollup
   ```
   - If no PR exists (exit code non-zero or `state` is not `OPEN`):
     > "No open PR found for branch `<branch>`. Run `/cg-commit-push-pr` first to push and open one."
     Halt.
   - Store the PR `number` for subsequent commands.

### Step 2: Check CI Status

1. Parse `statusCheckRollup` from the PR view JSON. This is an array of check objects with `name`, `conclusion`, and `status` fields.

   - If `statusCheckRollup` is `null`, the key is absent, or the array is empty (`[]`): respond with "\u23f3 No CI checks have run yet on this PR. Wait for checks to start and re-invoke `/cg-verify-pr`." and halt.

2. Classify overall status:
   - **All passing** (all `conclusion` values are `SUCCESS`, `NEUTRAL`, or `SKIPPED`):
     > "✅ All CI checks are passing. Nothing to fix."
     Halt with success.
   - **Pending** (any check has `status: IN_PROGRESS` or `status: QUEUED` and `conclusion: null`):
     > "⏳ CI checks are still running. Try again in a few minutes."
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

### Step 3: Fetch and Classify Failure Logs

For each failing check:

1. **Extract run ID**: use the workflow name from `statusCheckRollup` to find the run:
   ```
   gh run list --branch <branch> --workflow "<workflow-name>" --limit 1 --json databaseId
   ```
   Parse the `databaseId` integer.
   - If the returned array is empty: output "No run found for workflow `<workflow-name>` on branch `<branch>`. Try: `gh run list --branch <branch>`" and skip log fetching for this check.

2. **Fetch failure logs**:
   ```
   gh run view <run-id> --log-failed
   ```
   If the log is very large, focus on the first and last 100 lines of each job's failure output.

3. **Classify each failure** by pattern-matching the log output:

   | Category | Log patterns |
   |----------|-------------|
   | **Lint/Type errors** | `ESLint`, `mypy`, `lintr`, `pylint`, `styler`, `flake8`, `ruff`, `hadolint`, type annotation errors |
   | **Test failures** | `FAIL`, `pytest`, `testthat`, `Pester`, `FailedCount`, `assert`, `AssertionError`, `Expected:`, `Actual:` |
   | **Build errors** | `ModuleNotFoundError`, `ImportError`, `PackageError`, `cannot find package`, `compilation failed`, `No such file or directory` |
   | **Platform-specific** | Check passes on one OS runner but fails on another (e.g., `ubuntu-latest` passes, `windows-2022` fails) |
   | **Unknown** | Does not match any above pattern |

4. Present classification:
   > "CI failures classified:
   > - 🧪 Test failures (N): `<file>`, `<file>`
   > - 🔧 Lint/type errors (N): `<file>`
   > - 🏗️ Build errors (N): `<file>`
   > - 🖥️ Platform-specific (N): `<platform>` only — `<check-name>`
   >
   > [Auto-fix mode: applying fixes now. | Propose mode: see suggested fixes below.]"

### Step 4: Fix Round

*(Auto-fix mode only. In `--propose` mode, skip directly to Step 6.)*

**Do NOT use `gh pr checks --watch`** — it blocks the terminal indefinitely and will crash the agent session. This step is a one-shot fix; the user must re-invoke `/cg-verify-pr` after CI re-runs to apply a second round if needed.

**Detect default branch** (before round detection and rebase checks):
```
$defaultBranch = (git symbolic-ref refs/remotes/origin/HEAD --short 2>$null) -replace '^origin/', ''
if (-not $defaultBranch) {
    $defaultBranch = if (gh pr view --json baseRefName --jq '.baseRefName' 2>$null) { gh pr view --json baseRefName --jq '.baseRefName' } `
                     elseif (git rev-parse --verify main 2>$null) { 'main' } else { 'master' }
}
```

**Round detection** (enforce 2-round cap):
```
$mergeBase = (git merge-base HEAD <default-branch>) | Select-Object -First 1
git log --oneline --first-parent --grep="^fix(ci):" $mergeBase..HEAD
```
Count lines. If ≥ 2 `fix(ci):` commits exist since the branch point:
> "**2 fix rounds already attempted.** Remaining CI failures require manual intervention.
> Review the logs: `gh run view <run-id> --log-failed`"
Halt.

**Pre-push rebase check** (before applying fixes):
1. `git fetch origin <default-branch>`
2. Check divergence: `git merge-base --is-ancestor origin/<default-branch> HEAD`
   - `$LASTEXITCODE -eq 0` (true) → branches have not diverged; proceed.
   - `$LASTEXITCODE -ne 0` (false) → main has moved ahead; attempt rebase:
     ```
     git rebase origin/<default-branch>
     ```
     - **Clean rebase**: proceed.
     - **Simple conflict** (single file, < 10 lines): show the conflicting region, propose resolution, ask for confirmation before continuing.
     - **Complex conflict**: halt with:
       > "Merge conflict in `<file>` needs interactive resolution.
       > Resolve manually: edit the file, then `git add <file>` and `git rebase --continue`.
       > Then re-invoke `/cg-verify-pr`."

**Apply fixes by category**:

1. **Lint/Type errors**: Dispatch `@cg-fix-problems` with the relevant files and error descriptions from the CI log.
2. **Test failures**: Read the failure output carefully. Apply a targeted fix to the source file. If the root cause is unclear, dispatch `@cg-testing` for analysis first.
3. **Build errors**: Dispatch `@cg-code-quality` to analyse the dependency/import error; then apply the fix based on its diagnosis.
4. **Unknown**: Apply best-effort fix based on the log output; note what was attempted.

**Commit and push fixes**:
Before staging, run `git diff --stat HEAD` to enumerate exactly which files were modified by the fix round. Do not use `git add .`; stage only the intended fixed files individually.

```
git add <fixed-files>
```
Verify exit code after `git add`. If non-zero: report the exact git error and halt — do not attempt `git commit`.
```
git commit -m "fix(ci): <brief description of what was fixed>"
git push origin <branch>
```
*(If a rebase was performed, use `git push --force-with-lease origin <branch>` — never plain `--force`. If `git push --force-with-lease` exits non-zero: report the exact error. Advise the user to `git fetch`, check for new remote commits on the branch, and re-invoke `/cg-verify-pr` to restart the fix round.)*

**Post-push notification**:
After pushing, run one non-blocking CI status poll with `gh pr checks <number>` or `gh pr view --json statusCheckRollup` to confirm whether checks have restarted. Do not use `--watch`. If checks are still pending or have not refreshed yet, tell the user to re-invoke `/cg-verify-pr` after checks complete.

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
  >
  > PR: <URL>"

- **Observe-only mode (`--propose`)**:
  > "CI diagnosis complete. **No changes were made.**
  >
  > Suggested fixes:
  > - 🧪 Test failures: <description of root cause and suggested fix>
  > - 🔧 Lint errors: <specific files and rules violated>
  > - 🏗️ Build errors: <missing package or import>
  >
  > To apply fixes automatically: `/cg-verify-pr` (without `--propose`)
  > To apply manually: address the issues above, commit, and push."
