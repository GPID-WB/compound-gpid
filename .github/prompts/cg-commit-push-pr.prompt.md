---
description: "Stage changes into logical commits, push, and open a PR with plan-driven description."
model: Claude Sonnet 4.6 (copilot)
---

# Commit, Push, and Open PR

You are a senior developer helping the user package their work into well-structured commits, push the branch, and open a pull request with a plan-driven description.

## File Permissions

- **READ**: Any file in the workspace.
- **EXECUTE**: `git add`, `git commit`, `git push`, `gh pr create`.
- **NEVER**: Modify `.cg-docs/` files, plan files, or `roadmap.json` directly.

## Flags

- **`--ask`** (or **`--wait`**): Enable interactive confirmation mode. When set, pause after proposing the commit structure (Step 2) and after generating commit messages (Step 3) to wait for user approval before proceeding. **Default (no flag): auto-proceed without confirmation** — classify, generate messages, commit, push, and open the PR in one uninterrupted pass.

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md` in the project root for project context (objective, constraints, current focus). If it does not exist, skip silently — this command is project-agnostic and works without a charter.
2. Read `compound-gpid.local.md` for user config if it exists; skip silently otherwise.
3. Read `compound-gpid.context.md` for project-specific context if it exists; skip silently otherwise.

### Step 1: Pre-flight Checks

1. Run `git status --short` to inventory staged, unstaged, and untracked changes.
   - If output is empty: "Nothing to commit. Working tree is clean." — halt.

2. Run `git branch --show-current` to get the current branch name.
   - If output is empty: halt with "You appear to be in detached HEAD state (`git branch --show-current` returned empty). Checkout a branch first: `git checkout -b feat/<name>`"
3. Detect the default branch:
   - Run `git symbolic-ref refs/remotes/origin/HEAD --short 2>$null` and strip the `origin/` prefix.
   - If the command fails or returns empty, check for `main` then `master` as fallbacks.

4. If the current branch is the default branch:
   > "⚠️ You're on the default branch (`<branch>`). It's recommended to work on a feature branch first.
   > `git checkout -b feat/<name>`
   >
   > Continue anyway? (yes/no)"
   - If user declines: halt.

5. Check `gh` CLI availability:
   - PowerShell: `Get-Command gh -ErrorAction SilentlyContinue`
   - bash/zsh: `command -v gh`
   - If `gh` is not found:
     > "`gh` CLI not found. Install it for full PR creation support:
     > - Windows: `winget install GitHub.cli`
     > - macOS: `brew install gh`
     > - Linux: see https://cli.github.com/
     >
     > Continuing — will commit and push, then provide the manual `gh pr create` command."
   - Store availability as `$ghAvailable` for later steps.

### Step 2: Analyze Changes and Propose Commits

1. Run `git diff HEAD --stat` for the combined staged+unstaged view relative to HEAD. Use the `git status --short` output from Step 1 to identify untracked (`??`) files.

2. Classify each changed file into a group using these heuristics (evaluated in order; first match wins):

   | Group | Patterns |
   |-------|---------|
   | **Tests** | Path contains `tests/`, `test/`, `spec/`, `__tests__/`; filename matches `test_*`, `*_test.*`, `*.Tests.*`, `*-test.*`, `*.spec.*` |
   | **Docs** | Extension is `.md`, `.Rd`, `.rst`, `.txt`; path contains `docs/`, `man/`; filename starts with `README`, `CHANGELOG`, `CONTRIBUTING`, `LICENSE` |
   | **Config** | Extension is `.json`, `.yaml`, `.yml`, `.toml`, `.ini`, `.env.example`; filename is `renv.lock`, `poetry.lock`, `uv.lock`, `Makefile`, `Dockerfile`; path contains `.github/workflows/` |
   | **Plans/Knowledge** | Path starts with `.cg-docs/` |
   | **Code** | Extension is `.R`, `.r`, `.py`, `.do`, `.ado`, `.ps1`, `.sh`, `.bash`, `.zsh`, `.ts`, `.js`, `.mjs`, `.cs`, `.java`, `.go`, `.rs` |
   | **Other** | Everything else |

3. Group files and present proposed commit structure:
   > "I see N changed files. Here's my proposed commit structure:
   >
   > 1. **feat(scope): <description>** — `file1.R`, `file2.R` (code)
   > 2. **test(scope): <description>** — `tests/test-foo.R` (tests)
   > 3. **docs: <description>** — `README.md` (docs)
   >
   > The scope is inferred from the most-changed directory. Adjust the grouping or message? Or accept to proceed."

   - If all changes fall into one group: propose a single commit.
   - If `.cg-docs/plans/` files are present: group them separately as Plans/Knowledge.
   - **If `--ask` (or `--wait`) was passed**: wait for user confirmation or adjustments before continuing. **Otherwise (default): auto-proceed** to Step 3 with the proposed grouping.

### Step 3: Generate Commit Messages

For each confirmed group:

1. Run `git diff HEAD -- <files-in-group>` to read the actual diff.
   - For files listed as `??` (untracked) or `A ` (staged new) in `git status --short`: read the file content directly via `Get-Content <file>` (PowerShell) or `cat <file>` (bash/zsh) — `git diff HEAD` returns empty for files not yet tracked.
   - For modified tracked files (`M `, `MM`, etc.): use `git diff HEAD -- <file>` as normal.
2. Generate a conventional commit message:
   - **Subject**: `type(scope): description` — max 72 characters, imperative mood, lowercase after colon.
   - **Types**: `feat` (new feature), `fix` (bug fix), `docs` (documentation), `test` (tests), `refactor` (restructuring), `chore` (maintenance), `data` (data changes), `analysis` (analysis work).
   - **Scope**: the most changed module, directory, or component (e.g., `link`, `tests`, `ci`).
   - **Body** (if diff is non-trivial): bullet list of key changes, separated from subject by a blank line.
3. **If `--ask` (or `--wait`) was passed**: present all messages together and wait for user approval before any `git commit` is run. **Otherwise (default): auto-proceed** to Step 4 immediately after generating the messages.
4. If the project has `compound-gpid.md` with a Constraints section, use the declared commit-type taxonomy if documented there.

### Step 4: Execute Commits

For each confirmed commit group, in order:

1. `git add <files-in-group>`
   - Verify exit code after `git add`. If non-zero: report the exact git error and halt — do not attempt `git commit` for this group.
2. `git commit -m "<subject>"` (append `--message "<body>"` if a body was generated)
3. If commit fails: report the exact git error and halt — do not continue to the next group.

### Step 5: Push

1. Check if the current branch has an upstream: `git rev-parse --abbrev-ref @{u} 2>$null`
   - If no upstream: `git push --set-upstream origin <branch>`
   - If upstream exists: `git push origin <branch>`
2. If push is rejected (non-fast-forward):
   > "Push rejected — the remote has changes not in your local branch.
   > Options:
   > - `git pull --rebase` then push again
   > - `git push --force-with-lease` (overwrites remote — only safe if you own this branch)
   >
   > Which would you like? (rebase / force-with-lease / cancel)"
   - **Never `--force`** without the `--lease` safety guard.
   - If user chooses rebase: run `git pull --rebase`, then re-attempt push. Report result.
   - If user chooses force-with-lease: run `git push --force-with-lease origin <branch>`. Report result.
   - If user cancels: halt.
3. If push fails for any other reason: report the git error verbatim and halt.

### Step 6: Open PR

*(Skip this step if `$ghAvailable` is false — jump to Step 7 with manual instructions.)*

1. **Check for an existing PR** on this branch:
   ```
   gh pr view --json url,title 2>$null
   ```
   - If a PR already exists: set `$existingPR = <url>`. Skip sub-steps 2–4 — the new commits are automatically included in the open PR. Jump to Step 7.
   - If no PR exists (command returns empty or non-zero): proceed to sub-step 2.

2. Detect plans added since the branch point:
   ```
   $mergeBase = (git merge-base HEAD <default-branch>) | Select-Object -First 1
   git diff --name-only $mergeBase..HEAD -- .cg-docs/plans/
   ```
   This produces the list of plan files added or modified on this branch.

3. Compose PR body:
   - **If plan files found**: read each plan's `## Objective` section (and `## Requirements` table if present). Aggregate into PR body under sections:
     ```
     ## What this PR does
     <Objective text from plan 1>

     ## Requirements addressed
     <Requirements table from plan 1>

     ---
     <Repeat for additional plans>
     ```
   - **If no plan files found**: generate PR body from commit subjects as a bullet list.

4. Derive PR title from the branch name (replace `feat/`, `fix/`, etc. prefix, convert hyphens to spaces, title-case) or from the primary commit subject.

5. Run: `gh pr create --title "<title>" --body "<body>"`
   - On success: report the PR URL.
   - On failure: show the git/gh error verbatim and provide the equivalent manual command:
     ```
     gh pr create --title "<title>" --body "<body>"
     ```

### Step 7: Handoff

- **If `gh` was available and a PR already existed (`$existingPR` is set)**:
  > "✅ Done.
  > - N commits pushed to `<branch>`
  > - PR already open — new commits included automatically: <existingPR URL>
  >
  > **Next steps:**
  > 1. `/cg-verify-pr` — Check CI status and auto-fix failures
  > 2. Wait for reviewer approval"

- **If `gh` was available and a new PR was created**:
  > "✅ Done.
  > - N commits pushed to `<branch>`
  > - PR: <URL>
  >
  > **Next steps:**
  > 1. `/cg-verify-pr` — Check CI status and auto-fix failures
  > 2. Wait for reviewer approval"

- **If `gh` was unavailable or PR creation failed**:
  > "✅ Commits pushed to `<branch>`.
  >
  > Open a PR manually:
  > ```
  > gh pr create --title "<title>" --body "<body>"
  > ```
  > Or visit: `https://github.com/<org>/<repo>/compare/<branch>`"
