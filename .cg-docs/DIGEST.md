# Compound GPID — Solution Digest

_Generated 2026-05-18 · 126 active solutions_

## Append-only insertion prevents silent corruption in AI-written shared files

date: 2026-05-18
category: testing-patterns
status: 
tags: prompt-design, context-md, markdown, corruption, append-only, structured-content
path: .cg-docs/solutions/testing-patterns/2026-05-18-append-only-insertion-for-ai-written-shared-files.md

`/cg-compound` Step 5 was instructed to enrich `compound-gpid.context.md` by inserting "directly into the correct section — place it logically within the existing structure, not appended at the end." This is semantically correct for a human editor but dangerous for an AI model: the model must identify a target location inside existing text, and it may insert mid-table, inside a fenced code block, or between YAML key-value pairs — all of which are syntactically valid text positions that are semantically destructive.

## compound-gpid repo not wired as its own wiki consumer — docs/ folder ignored by /cg-wiki and /cg-compound

date: 2026-05-18
category: bugs
status: 
tags: cg-wiki, cg-compound, wiki-configuration, context-md, docs, bootstrap, self-referential
path: .cg-docs/solutions/bugs/2026-05-18-compound-gpid-repo-not-wired-as-wiki-consumer.md

Running `/cg-wiki` or `/cg-compound` (after a user-facing change) in the compound-gpid repo either reported "no manifest found" or silently skipped the wiki update step — even though `docs/` contains 9 hand-authored documentation pages that serve as the project's canonical user reference.

## PS 5.1 Set-StrictMode crashes on bare $IsWindows access (variable not set)

date: 2026-05-18
category: bugs
status: 
tags: powershell, ps51, strict-mode, IsWindows, automatic-variables, platform-detection, Test-Path, variable-provider, link, unlink
path: .cg-docs/solutions/bugs/2026-05-18-ps51-strict-mode-iswindows-variable-not-set-crash.md

Running `cg-link` on a project using Windows PowerShell 5.1 produced:

## Regex extraction vacuous pass — Groups[1].Value returns empty string on no match

date: 2026-05-18
category: testing-patterns
status: 
tags: pester, regex, vacuous-pass, false-positive, drift-detection, parse-guard, -match, comparison-test
path: .cg-docs/solutions/testing-patterns/2026-05-18-regex-extraction-vacuous-pass-empty-string-comparison.md

A drift-detection test in `tests/wiki.Tests.ps1` extracted a folder value from two files using `[regex]::Match(...).Groups[1].Value` and compared them with a single `Should -Be` assertion: ``` In the verify pass, `@cg-code-quality` and `@cg-testing` both independently flagged this: if either source file is absent or either regex pattern does not match, `.Groups[1].Value` returns `""` (not an exception, not `$null`). The test then evaluates `"" | Should -Be ""` — green, zero coverage. This is most dangerous exactly when it would matter most: if someone accidentally removes the `<!-- folder: docs -->` directive from `compound-gpid.context.md`, the test that was supposed to catch the drift...

## Use git rev-parse for repo detection; guard against detached HEAD state

date: 2026-05-18
category: git-workflows
status: 
tags: git, branch, detached-head, prompt-design, guard, repo-detection
path: .cg-docs/solutions/git-workflows/2026-05-18-git-rev-parse-for-repo-detection-detached-head-guard.md

Two prompts (`/cg-brainstorm` and `/cg-plan`) used `git branch --show-current` as a proxy for detecting whether the workspace is a git repository. The same command was used to obtain the current branch name. This conflates two operations that have different failure modes.

## cg-commit-push-pr always paused for user confirmation — no auto-proceed mode

date: 2026-05-15
category: bugs
status: 
tags: cg-commit-push-pr, ux, confirmation, interactive, flag, default-behavior, prompts
path: .cg-docs/solutions/bugs/2026-05-15-cg-commit-push-pr-always-waits-for-confirmation.md

`/cg-commit-push-pr` always halted twice mid-execution: 1. **Step 2.3** — after proposing the commit grouping: "Wait for user confirmation or adjustments before continuing." 2. **Step 3.3** — after generating commit messages: "Present all messages together for review before any `git commit` is run." There was no way to run the command non-interactively. Even routine, unambiguous commits required two interactive round-trips before any `git commit` was issued.

## cg-commit-push-pr skipped PR creation when gh not found — VS Code extension never tried

date: 2026-05-15
category: bugs
status: 
tags: cg-commit-push-pr, gh, vscode-extension, pr-creation, tool-detection, fallback, github-pull-request
path: .cg-docs/solutions/bugs/2026-05-15-cg-commit-push-pr-gh-only-tool-detection.md

When `gh` CLI was not installed, `/cg-commit-push-pr` set `$ghAvailable = false`, skipped Step 6 entirely, and dumped a manual `gh pr create` command in the handoff — even though the VS Code GitHub Pull Request extension was installed and fully capable of creating the PR. Users got a degraded experience with no actionable path to fix it for future runs.

## Circular error recovery: halt message suggests a command that itself requires the precondition that caused the halt

date: 2026-05-15
category: bugs
status: 
tags: prompt-design, agent-design, error-messages, ux, cg-wiki, pre-flight, bootstrap-trap
path: .cg-docs/solutions/bugs/2026-05-15-circular-error-recovery-command-in-halt-message.md

`@cg-wiki` halts in Pre-Flight when `_wiki.yml` is absent: ``` But `rebuild` mode is dispatched through `@cg-wiki` — which runs the **same Pre-Flight** and halts on the identical check. Following the suggested recovery: 1. User runs `/cg-wiki rebuild` 2. Pre-Flight: `_wiki.yml` not found → halt with the same message 3. User is stuck in an infinite loop with no forward path The same pattern appeared in `cg-wiki.prompt.md` Step 2 (fixed as P3.7 in the original review) and survived undetected in the **agent's own Pre-Flight halt message** — found only by the subsequent verify pass (P2.1 in verify review).

## Common-word regex false positives in security and behavioral test assertions

date: 2026-05-15
category: testing-patterns
status: 
tags: pester, regex, false-positive, security-tests, -match, wiki, injection-scan, behavioral-testing
path: .cg-docs/solutions/testing-patterns/2026-05-15-common-word-regex-false-positive-in-security-assertions.md

After the thorough review of the `@cg-wiki` feature, a verify pass found that several new Pester tests passed trivially rather than meaningfully: **Injection scan test** (P3.2 in verify review): ``` `Ignore`, `Override`, and `Forget` are ordinary English words. Any agent file containing "do not override user preferences" or "ignore this field when empty" passes this test regardless of whether an injection scan rule exists. **Nested marker test** (P3.3): ``` "Nested" appears in documentation for nested YAML, nested lists, nested JSON, and dozens of other contexts. The test passes without verifying the marker- nesting rule. **Code-block marker test** (P3.5): ``` "Code...

## Injection scan required for every agent that reads user-adjacent files, including 'internal' cg-docs/ solution files

date: 2026-05-15
category: testing-patterns
status: 
tags: prompt-injection, security, agent-design, ai-safety, cg-wiki, solution-files, cg-docs
path: .cg-docs/solutions/testing-patterns/2026-05-15-injection-scan-required-for-every-agent-that-reads-user-adjacent-files.md

`@cg-wiki` in `update` mode reads a solution file at `solution-path` and uses its content to synthesize updates to wiki pages. The initial implementation had only a policy-level "treat as untrusted" declaration — no phrase-level scan before the content entered the synthesis step. A `.cg-docs/solutions/` file containing: ``` would pass the path validation (`starts with .cg-docs/solutions/`, `ends with .md`, no `..`) and reach the wiki synthesis step with the injected instruction in context.

## No user-facing path to initialize wiki on existing projects

date: 2026-05-15
category: bugs
status: 
tags: prompt-design, cg-wiki, ux, bootstrap-trap, agent-design, subcommand-gap
path: .cg-docs/solutions/bugs/2026-05-15-cg-wiki-no-user-facing-init-path-for-existing-projects.md

On a project with no `_wiki.yml`, every wiki entry point either skips silently or halts with no forward path:

## Classification steps must exhaustively cover all enum values with terminal actions

date: 2026-05-14
category: testing-patterns
status: 
tags: prompt-design, classification, enum-exhaustion, guard-conditions, edge-cases, cg-verify-pr
path: .cg-docs/solutions/testing-patterns/2026-05-14-classification-step-must-exhaustively-cover-enum-values.md

A prompt step that classifies input into one of N categories must provide a terminal action (halt or proceed) for every possible combination of input values. When a value or combination is missing, control falls through to the next step with invalid state. **Example from this session**: `cg-verify-pr` Step 2 classified CI check conclusions into: All passing (SUCCESS/NEUTRAL/SKIPPED) | Pending | Manual action required (ACTION_REQUIRED/STALE) | Cancelled (non-blocking) | Failing (FAILURE/TIMED_OUT). The "Cancelled" rule said "treat as non-blocking, note in classification" — but had no terminal action. The "Failing" rule fired only when `FAILURE`/`TIMED_OUT` was present. If every check returned...

## gh pr create: use --body-file not inline --body to prevent shell injection

date: 2026-05-14
category: git-workflows
status: 
tags: gh, pull-request, shell-injection, security, prompt-design, cg-commit-push-pr
path: .cg-docs/solutions/git-workflows/2026-05-14-gh-pr-create-use-body-file-not-inline-body.md

A prompt using `gh pr create --title "..." --body "<plan content>"` passes the PR body inline on the command line. When plan content contains backticks, `$()`, `${VAR}`, or other shell metacharacters, PowerShell and bash interpolate them before `gh` receives the argument. Example: a plan `## Objective` value of `` feat: add `$(whoami)` `` would execute `whoami` silently if the body is passed inline. In bash, `$(rm -rf .)` would delete the working tree. Discovered as P0.1 in the `cg-commit-push-pr`/`cg-verify-pr` thorough review.

## git log without --first-parent double-counts upstream merge commits when measuring branch-local work

date: 2026-05-14
category: git-workflows
status: 
tags: git, git-log, first-parent, branch-commits, merge-commits, cg-verify-pr, ci
path: .cg-docs/solutions/git-workflows/2026-05-14-git-log-first-parent-for-branch-local-commits.md

When counting commits authored **on the current branch** since a branch point, the common pattern: ``` silently includes commits from any merged-in upstream branches. If `main` was rebased into the feature branch via a merge commit, all commits reachable from `main` between `$mergeBase` and `HEAD` are also included — inflating the count. **Example**: A feature branch with 1 `fix(ci):` commit, merged with an upstream `main` that has 3 unrelated commits, reports **4** `fix(ci):` commits if any of those upstream commits happen to match the grep pattern (unlikely but possible), and more subtly produces **wrong commit ordering** even without a pattern...

## git merge-base can return multiple ancestors — always take the first line

date: 2026-05-14
category: git-workflows
status: 
tags: git, merge-base, PowerShell, bash, prompt-design, branch-detection, cg-commit-push-pr, cg-verify-pr
path: .cg-docs/solutions/git-workflows/2026-05-14-git-merge-base-multiple-ancestors-take-first-line.md

Scripts and prompt instructions that compute the branch point with: ``` assume `git merge-base` returns exactly one hash. In repositories with a complex merge history (e.g., after an octopus merge or a criss-cross merge), the command can return **multiple SHA hashes on separate lines**. When assigned directly: - PowerShell: `$mergeBase` becomes a `string[]` array; subsequent commands such as `git diff $mergeBase..HEAD` receive `"sha1 sha2"` (space-joined) and fail or produce wrong output. - bash: `MERGE_BASE=$(git merge-base HEAD main)` captures a newline-delimited string; commands using it unquoted get word-split. Discovered as P2.3 in the `cg-commit-push-pr`/`cg-verify-pr` thorough review.

## Prompt injection via LLM-authored plan content embedded in AI-generated output

date: 2026-05-14
category: testing-patterns
status: 
tags: security, prompt-injection, plan-files, ai-safety, cg-commit-push-pr, untrusted-content
path: .cg-docs/solutions/testing-patterns/2026-05-14-prompt-injection-via-plan-content-in-ai-generated-output.md

A prompt reads a plan file's `## Objective` section and embeds it verbatim into AI-generated output (e.g., a PR body, a commit message body, or a summary). If the plan file's Objective contains adversarial instructions — either accidentally or by a malicious actor with write access to the plan file — those instructions are relayed to the user or forwarded to a downstream agent. Example plan content: ``` When the prompt reads this and writes it into a PR body: the LLM generating the PR body sees the injected text and may follow it. Discovered as P1.5 in the `cg-commit-push-pr`/`cg-verify-pr`...

## Sibling-prompt symmetry: apply guard fixes to all prompts with the same operation

date: 2026-05-14
category: testing-patterns
status: 
tags: prompt-design, guard-conditions, symmetry, code-review, verify-pass, cg-commit-push-pr, cg-verify-pr
path: .cg-docs/solutions/testing-patterns/2026-05-14-sibling-prompt-symmetry-guard-audit.md

When a P1 review finding adds a guard to prompt A (e.g., "exit-code check after `git add`"), the fix is scoped to that file. A sibling prompt B that performs the same operation (also `git add` → `git commit`) is not in scope, so the fix is never applied there. This pattern is invisible to per-file testing: all tests for prompt A pass because the guard is present; all tests for prompt B pass because there were no tests for the guard. The verify pass is the first time the gap surfaces. **Example from this session**: P1.1 in the original...

## Write-permission mode flags must be parsed before any tool dispatch, not deferred to a later step

date: 2026-05-14
category: testing-patterns
status: 
tags: prompt-design, file-permissions, mode-flags, propose, read-only, step-ordering, cg-verify-pr
path: .cg-docs/solutions/testing-patterns/2026-05-14-write-permission-flags-must-be-parsed-before-tool-dispatch.md

A prompt's File Permissions block declared: > `--propose` mode: READ-only — no file creation, modification, git commits, > or pushes of any kind. But the flag parsing was placed in **Step 0.6** — after bearings (Step 0.1–0.3) and other pre-flight work. An agent executing linearly could call `read_file` and other tool-dispatching steps (Steps 0.1–0.5) before it evaluated the `--propose` flag. If the agent's future steps included write operations, the READ-only constraint had not yet been established when those steps were entered. Discovered as P2.1 in the `cg-commit-push-pr`/`cg-verify-pr` thorough review.

## cg-link bootstrap index offer always fails on empty projects

date: 2026-05-13
category: bugs
status: 
tags: link, cg-index, bootstrap, empty-project, link.ps1, link.sh, ux
path: .cg-docs/solutions/bugs/2026-05-13-cg-link-bootstrap-index-offer-fails-on-empty-projects.md

Running `cg-link` on a new empty project completed the symlink/junction setup but then prompted to build the knowledge index. When the user answered `y`, the command failed:

## CI bypass flag pattern: [switch]$Force / --yes for interactive scripts

date: 2026-05-13
category: testing-patterns
status: 
tags: ci, powershell, bash, interactive, Read-Host, force-flag, non-interactive, e2e
path: .cg-docs/solutions/testing-patterns/2026-05-13-ci-bypass-flag-force-yes-interactive-scripts.md

PowerShell scripts (`link.ps1`, `unlink.ps1`) and bash scripts (`link.sh`, `unlink.sh`) contain interactive confirmation prompts (`Read-Host`, `read -r`). When these scripts are invoked from GitHub Actions E2E smoke tests or any non-interactive automation, the runner hangs indefinitely waiting for keyboard input that never arrives. The job eventually times out with a cryptic timeout error rather than a meaningful failure message. Secondary issue: even if the CI job is configured with a short timeout, the hanging step can freeze VS Code's terminal if the test runner is invoked interactively (e.g., Pester calling the script).

## Cross-script parity tests: keeping ps1 and sh scripts in sync

date: 2026-05-13
category: testing-patterns
status: 
tags: parity, powershell, bash, cross-platform, regression, managed-dirs, pester
path: .cg-docs/solutions/testing-patterns/2026-05-13-cross-script-parity-tests-ps1-sh.md

`link.ps1` and `link.sh` (and `unlink.ps1` / `unlink.sh`) must produce equivalent behaviour on Windows and macOS. When a managed directory is added to one but not the other, or when a bypass flag is added to one script but forgotten on its counterpart, the divergence is invisible. Individual unit tests for each script pass; only the combined behaviour breaks. Examples of silent divergence that occurred before parity tests existed: - `link.ps1` had `shared/` in `$ManagedDirs`; `link.sh` was missing it - `unlink.ps1` had `[switch]$Force`; `unlink.sh` had no `--yes` equivalent - Verification file path differed: `cg-setup.prompt.md` vs `cg-start.prompt.md`

## E2E smoke test in GitHub Actions with safe Windows junction teardown

date: 2026-05-13
category: git-workflows
status: 
tags: ci, github-actions, windows, junction, teardown, e2e, macos, symlink, smoke-test
path: .cg-docs/solutions/git-workflows/2026-05-13-e2e-smoke-test-github-actions-windows-junction-teardown.md

After adding an E2E smoke test step to CI, the Windows runner occasionally deleted source files from `$GITHUB_WORKSPACE/.github/prompts/*` during teardown. The step used `Remove-Item -Recurse -Force` to clean up the E2E working directory. On GitHub Actions Windows 2022 runners, Windows Defender can lock files accessed through junctions, causing `Remove-Item -Force` on the junction itself to fail silently (exit code 0). The subsequent `-Recurse` then traverses the surviving junction link and removes the source files.

## Join-Path with embedded backslash path separator is Windows-only

date: 2026-05-13
category: environment-issues
status: 
tags: powershell, cross-platform, join-path, path-separator, macos, linux, platform-guard, scripts
path: .cg-docs/solutions/environment-issues/2026-05-13-join-path-backslash-not-cross-platform.md

On Windows, `Join-Path $base "subdir\file.txt"` works correctly, producing `$base\subdir\file.txt`. The same call on macOS/Linux resolves to `$base/subdir\file.txt` — a single path component named `subdir\file.txt` (a literal backslash in the filename). `Test-Path`, `Get-Content`, and other cmdlets then fail silently: `Test-Path` returns `$false`, `Get-Content` throws "file not found", and there is no error at the `Join-Path` call site. This was the root cause of the `cg-link` macOS verification warning: ```

## link.ps1 runs on macOS via pwsh, Step 6 verification fails due to backslash path separator

date: 2026-05-13
category: bugs
status: 
tags: cg-link, link.ps1, link.sh, macos, symlinks, junctions, platform-guard, path-separator, verification
path: .cg-docs/solutions/bugs/2026-05-13-link-ps1-runs-on-macos-verification-fails.md

After running `cg-link` on macOS the terminal shows:

## Read-Host empty string throws PSArgumentException in cg-link bootstrap prompt

date: 2026-05-12
category: bugs
status: 
tags: link, Read-Host, bootstrap, cg-index, PSArgumentException, interactive
path: .cg-docs/solutions/bugs/2026-05-12-link-read-host-empty-string-throws-psargumentexception.md

Running `cg-link` in an interactive terminal completed the junction setup but then crashed at the "Would you like to build the initial knowledge index now? (y/N)" prompt:

## Source-scanning regression guard for PowerShell scripting anti-patterns

date: 2026-05-12
category: testing-patterns
status: 
tags: powershell, pester, regression-guard, source-scanning, Read-Host, anti-pattern, link
path: .cg-docs/solutions/testing-patterns/2026-05-12-source-scanning-regression-guard-for-scripting-anti-patterns.md

A scripting anti-pattern (`Read-Host ""`) was introduced during a feature addition to `scripts/link.ps1`. The anti-pattern threw `PSArgumentException: name cannot be null or empty` at runtime — preventing users from answering the interactive prompt entirely. Because the pattern looked superficially correct (the intent was to read input without printing a second prompt), it could easily re-enter on the next edit.

## PS 5.1 `python -c` here-string unreliable — write temp .py file for Pester Python tests

date: 2026-05-07
category: testing-patterns
status: 
tags: pester, powershell, ps51, python, here-string, temp-file, testing
path: .cg-docs/solutions/testing-patterns/2026-05-07-ps51-python-c-heredoc-unreliable-use-temp-file.md

Passing multi-line Python code to `python -c` via a PowerShell here-string (`@"..."@`) in Pester tests produces unreliable behaviour on PS 5.1 / Windows: ``` Symptoms: - Python receives garbled indentation (CRLF injected mid-string) - Variable expansion: `$data` becomes an empty PS variable before Python sees it - Backtick escapes (`\`n`) interact with PS escape rules - `SyntaxError` or silent wrong output, exit code 0 The failure mode is especially insidious: the test may pass on the CI machine and fail locally (or vice versa) depending on the PS version and locale.

## Python non-atomic Path.write_text() truncates on crash — use mkstemp + os.replace

date: 2026-05-07
category: bugs
status: 
tags: python, atomic-write, file-io, stdlib, mkstemp, crash-safety, data-integrity
path: .cg-docs/solutions/bugs/2026-05-07-python-nonatomic-path-write-use-mkstemp-replace.md

`Path.write_text(content)` and `open(path, 'w')` are not atomic. The OS truncates the destination file to zero bytes **before** writing any content. If the process is interrupted mid-write (SIGKILL, power failure, out-of-disk, exception after truncation), the destination file is left empty or partially written — the previous content is gone with no recovery path. This was flagged as P2.4 in the `cg_index.py` code review. The indexer wrote `search-index.json` and `DIGEST.md` using `path.write_text()`, meaning a crash during indexing would silently destroy the knowledge base files.

## scripts/link.sh missing executable bit in git index

date: 2026-05-07
category: bugs
status: 
tags: bash, git, permissions, install, cg-link, executable-bit
path: .cg-docs/solutions/bugs/2026-05-07-link-sh-missing-executable-bit.md

Running `cg-link` after a fresh install fails immediately with:

## Cross-prompt user journey must be validated end-to-end, not just per-prompt

date: 2026-05-06
category: testing-patterns
status: 
tags: powershell, pester, prompt-pipeline, cg-resume, cg-work, user-journey, contract-testing, phased-execution
path: .cg-docs/solutions/testing-patterns/2026-05-06-cross-prompt-user-journey-must-be-validated-end-to-end.md

During the phased execution verify review, a **P2** finding emerged that all individual-prompt tests had missed: - `cg-resume` Step 2a (all-phases-complete branch) instructed: *"All M phases completed. Run `/cg-work` to proceed to final quality checks."* - `cg-work` Step 1.2 dispatch table (Phased | none row) explicitly **halts** when `completed-phases` contains all phases: *"display 'All N phases are already complete. Nothing to run.' and halt."* A user following cg-resume's instruction would run `/cg-work` with no argument, hit the halt immediately, and never reach Step 3 quality checks. The prompts individually passed all their tests, but the **user journey** was broken. This...

## Fix applied as HTML comment not executed — prompt instruction must be prose, not markup

date: 2026-05-06
category: testing-patterns
status: 
tags: prompt-design, fix-triage, html-comment, executable-instruction, silent-failure, agent-design, cg-ideate
path: .cg-docs/solutions/testing-patterns/2026-05-06-html-comment-as-fix-never-executed.md

During fix-triage for the roadmap-visualization review, finding P2.15 required migrating `cg-ideate.prompt.md` to dispatch `@cg-roadmap-view` for the roadmap-add flow (Step 5, option 3). The applied fix was: ``` The verify pass (V-P2.1) found that **`cg-ideate` still had no `@cg-roadmap-view` dispatch**. The HTML comment served as a note-to-self for the developer but was invisible to the model executing the prompt. The user landing on option 3 still picks a milestone blindly — the bug was not fixed. Every other prompt that received the same P2.15 fix (`cg-plan-review`, `cg-brainstorm`) had the instruction written as executable prose and worked correctly.

## Implicit output template in agent spec — 'same as X but omit Y' causes non-deterministic rendering

date: 2026-05-06
category: testing-patterns
status: 
tags: agent-design, prompt-design, output-template, rendering, determinism, tasks-milestone, cg-roadmap-view
path: .cg-docs/solutions/testing-patterns/2026-05-06-implicit-output-template-same-as-x-but-omit-y-ambiguous.md

`cg-roadmap-view.agent.md` specifies the `tasks-milestone` view as: > Same as `milestone` view but focused on the feature table only (omit > objective and progress bar). Every other view mode in the same agent has a **concrete Markdown code block** showing exactly what the rendered output looks like. The `tasks-milestone` view has only prose description. This creates ambiguity: when "omitting" the objective and progress bar, is the `## 🏁 <milestone-title>` heading also omitted? Or retained? Different model invocations answer this differently, producing non-deterministic output across sessions. Identified as **V-P3.4** in the verify pass of the roadmap-visualization feature (`2026-05-06-roadmap-visualization-verify-review.md`).

## Pester write-guard regex with ^ always false without (?m) — silent false-positive

date: 2026-05-06
category: testing-patterns
status: 
tags: pester, regex, powershell, multiline, caret-anchor, write-guard, prompt-testing, silent-failure, false-positive
path: .cg-docs/solutions/testing-patterns/2026-05-06-pester-caret-anchor-requires-multiline-flag.md

A write-guard test for `cg-roadmap-view.agent.md` was written as: ``` This test **always passes** — not because the agent is safe, but because the pattern can never match. The agent file begins with `---` YAML frontmatter, not a write instruction. In .NET regex, `^` without `(?m)` anchors to the start of the entire string, so the pattern is evaluated exactly once at position 0 and immediately fails. **The test gives a green checkmark whether or not the agent contains dangerous write instructions anywhere in the body.** Discovered as **P2.3** in the thorough review of the roadmap-visualization feature (`2026-05-06-roadmap-visualization-review.md`).

## duplicates tag clears r(N) — insert count before conditional display

date: 2026-05-05
category: data-quality
status: 
tags: stata, duplicates, stored-results, r-class, data-validation, assertion
path: .cg-docs/solutions/data-quality/2026-05-05-duplicates-tag-clears-r-N-use-count-before-conditional-display.md

The following pattern produces a silently-suppressed diagnostic: `display as error` never fires even when duplicates exist, because `if r(N) > 0` evaluates to false. ``` The `assert` line does correctly fail when duplicates exist, but the informative error message is always suppressed — making failures harder to diagnose.

## JSON-escaped quotes leak literal backslash-quote into PowerShell files

date: 2026-05-05
category: bugs
status: 
tags: powershell, pester, json, escaping, multi-replace, tool-bug, string-literals
path: .cg-docs/solutions/bugs/2026-05-05-json-escaped-quotes-leak-into-ps1-files.md

After using `multi_replace_string_in_file` (or a second sequential `replace_string_in_file`) to insert PowerShell code containing double-quoted strings into a `.ps1` file, the file on disk contained literal `\"` escape sequences — producing malformed PowerShell: ``` This caused Pester 3.4 to fail to parse the `It` block, resulting in test failures with confusing messages ("file not found" or `{True}` expected but got `{}`).

## Pester regex for assert-with-string-message false-positives on inlist/inrange

date: 2026-05-05
category: testing-patterns
status: 
tags: pester, regex, powershell, stata, assert, inlist, inrange, false-positive, guard-test
path: .cg-docs/solutions/testing-patterns/2026-05-05-pester-regex-assert-string-message-false-positive-inlist.md

A Pester guard test intended to detect invalid Stata `assert expr, "message"` syntax used the regex `assert\b[^\`\r\n]+,\s*"`. This correctly rejects: ``` But it also incorrectly matched valid Stata: ``` Because the regex sees `assert inlist(survey_type,` followed by a space and `"` — the comma is **inside parentheses** and belongs to `inlist()`, not to the `assert` option syntax. The test returned `True` (match found) when it should have returned `False` (no bad assert).

## print_yellow inside command substitution corrupts captured variable with ANSI text

date: 2026-05-05
category: bugs
status: 
tags: bash, command-substitution, stdout, stderr, ansi-escape, shell-profile, detect_profile, print_yellow, silent-failure
path: .cg-docs/solutions/bugs/2026-05-05-print-yellow-stdout-corrupts-command-substitution-variable.md

`scripts/install.sh` added a warning branch to `detect_profile()` for unrecognized shells (fish, nushell, tcsh) as part of a P3.8 fix. The warning used `print_yellow`, a helper defined as: ``` The function is called via command substitution: ``` For any unrecognized shell, `PROFILE_FILE` received the concatenated stdout of the entire function: ``` Every subsequent use of `$PROFILE_FILE` silently failed: - `grep -qF "$CG_PROFILE_START" "$PROFILE_FILE"` — no error, no match - `>> "$PROFILE_FILE"` — created a junk file with the ANSI-escape string as its name - The PATH block was never written to the real shell profile The install appeared to succeed (exit...

## Regex alternation branches become stale dead code after prompt refactoring

date: 2026-05-05
category: testing-patterns
status: 
tags: pester, powershell, regex, alternation, dead-code, prompt-refactoring, stale-pattern, -match, coverage
path: .cg-docs/solutions/testing-patterns/2026-05-05-stale-alternation-after-prompt-refactoring.md

A test was written in two-branch alternation form to cover two possible phrasings of the "skip silently" guard in `cg-plan.prompt.md`: ``` The first branch (`not.*main.*master.*skip silently`) was written for the original prompt text, which checked the current branch against the literal names `main` or `master`. After P2.3 replaced this with dynamic default-branch detection, the prompt text changed to: > "If the current branch is not the default branch (i.e., already on a feature > branch): skip silently." The words `main` and `master` no longer appear in this clause. The first alternation branch became permanently non-matching. The test continued to pass...

## Within-step pre-flight operations must precede the user-facing offer template

date: 2026-05-05
category: testing-patterns
status: 
tags: prompt-design, step-ordering, preflight, derivation, offer-template, branch-offer, ux, sequential-model, cg-plan
path: .cg-docs/solutions/testing-patterns/2026-05-05-within-step-preflight-must-precede-offer-template.md

`cg-plan.prompt.md` Step 0.7 was written in this order: 1. Check current branch 2. **Show the offer template** (`feat/<short-description>`, Yes/No options) 3. Derive the branch type (`feat/` vs `fix/` vs `refactor/`) 4. If accepted: create branch 5. If the repo has uncommitted changes, warn This order causes two distinct bugs: **Bug 1 (P1.1 — wrong branch name shown)**: The offer template displays `` `feat/<short-description-from-request>` `` before the derivation rule is stated. A model executing linearly shows the user `feat/my-fix`, then derives `fix/my-fix` as the type, then creates `fix/my-fix`. The user approved a name they never saw. **Bug 2 (P1.2 — post-hoc...

## Branch offer must precede user-investment steps in interactive prompts

date: 2026-05-01
category: testing-patterns
status: 
tags: cg-brainstorm, branch-offer, step-ordering, indexof, prompt-design, ux, user-investment
path: .cg-docs/solutions/testing-patterns/2026-05-01-branch-offer-must-precede-user-investment-steps.md

`/cg-brainstorm` asked "would you like to create a new branch?" at **Step 4.5** — after the brainstorm document was saved. By that point the user had already: 1. Answered 3–6 clarifying questions 2. Chosen an approach from the proposed options 3. Responded to the devil's advocate pushback All of this happened on whatever branch they were on when they invoked the prompt (often `main`). The question was also easy to miss because it was bundled inside the same conversational turn as the broader handoff menu.

## cg-brainstorm branch offer asked too late and buried in handoff

date: 2026-05-01
category: bugs
status: 
tags: cg-brainstorm, branch-offer, step-ordering, ux, prompts
path: .cg-docs/solutions/bugs/2026-05-01-cg-brainstorm-branch-offer-asked-too-late.md

When running `/cg-brainstorm`, the prompt asked "would you like to create a new branch?" only at **Step 4.5**, which fires *after* the brainstorm document was already saved. By this point the user had answered 3–6 clarifying questions, chosen an approach, and reviewed the devil's advocate pushback — all on the wrong (often `main`) branch. The question was also easy to miss because it appeared in the same conversational turn as the broader "what would you like to do next?" handoff stream.

## Fix-triage changes to prompt text need co-authored Pester assertions

date: 2026-05-01
category: testing-patterns
status: 
tags: pester, powershell, prompt-testing, fix-triage, regression, coverage, verify-mode, co-authoring, cg-setup
path: .cg-docs/solutions/testing-patterns/2026-05-01-fix-triage-prompt-changes-need-co-authored-tests.md

A thorough review of the smart-setup Phase 2 changes produced 21 findings (P0–P3). Fix-triage was applied across four priority batches (P0 → P1 → P2 → P3). After all findings were marked `fixed`, a verify pass (`/cg-review mode:verify`) surfaced **10 new findings** — all of them test coverage gaps. Nearly half of the 21 fixed behaviors had no regression anchor: | Fixed behavior (original review) | Had a test? | |---|---| | Duplicate Mode B content truncated (P0.1) | ✓ (line count test) | | Unescaped `\|` in regex (P1.1) | ✓ (the fix itself was a test) | |...

## Regex alternation in Pester -match can mask coverage when first branch is always true

date: 2026-05-01
category: testing-patterns
status: 
tags: pester, powershell, regex, alternation, coverage, always-true, -match, prompt-testing, cg-setup
path: .cg-docs/solutions/testing-patterns/2026-05-01-regex-alternation-masks-coverage-split-into-independent-assertions.md

A test was written to verify that the scanner injection sanitization block in `cg-setup.prompt.md` named all three trigger words: "Ignore", "Override", "Forget". ``` The source text at line 62 is: > `sentences beginning with "Ignore", "Override", or "Forget"` The regex `Ignore.*Override` matches this line (both words appear in order), so the first alternation branch is satisfied. PowerShell's `-match` short-circuits on the first match — `Override.*Forget` is never evaluated. If "Forget" were removed from the source text, the test would still pass. Despite the `It` name claiming all three words are verified, only two are effectively tested.

## Two-phase injection guard: scan before extracting content from user-controlled files in AI agents

date: 2026-04-29
category: testing-patterns
status: 
tags: prompt-injection, security, agent-design, ai-safety, two-phase, README, DESCRIPTION, cg-project-scanner, compound-gpid
path: .cg-docs/solutions/testing-patterns/2026-04-29-two-phase-injection-guard-for-agent-file-reads.md

`@cg-project-scanner` reads user-controlled files — `README.md`, `DESCRIPTION`, `.gitignore` — to extract charter-draft content. The naive safety rule: ``` This rule is applied *after* reading the file. By the time it fires, injected text like: ``` is already in the model's context window. Haiku 4.5 (the scanner model) is more susceptible to mid-context steering than frontier models. The "content excluded" instruction is behavioral, not a pre-read filter — the model must resist text it has already processed. The initial review of the agent (P1.2 in `2026-04-29-project-scanner-skill-agent-phase1-review.md`) flagged this as a P1 correctness issue.

## Writing a Pester test for an unshipped schema marker creates a persistent pre-existing failure

date: 2026-04-29
category: testing-patterns
status: 
tags: pester, testing, schema-version, SCHEMA_VERSION, pre-existing-failure, tdd, test-hygiene, compound-gpid
path: .cg-docs/solutions/testing-patterns/2026-04-29-premature-schema-marker-test-creates-persistent-failure.md

A review finding (P2.6 in `2026-04-09-ce-improvements-phase3-fix-verify-review.md`) recommended bumping `SCHEMA_VERSION` to `2026-04-09-scope-fields` when the `scope:` frontmatter field was introduced in plan and brainstorm artifacts. A Pester test was written to enforce this contract: ``` The SCHEMA_VERSION update was never applied. The file continued to read `2026-04-07-r-syntax-dialect`, then `2026-04-28-release-scanner-agent` after a later unrelated bump — neither contained `scope-fields`. The test failed from the day it was committed (2026-04-09) until it was diagnosed and fixed on 2026-04-29 — a span of 20 days and multiple review/fix-triage cycles. Every test run reported 1 pre-existing failure in `prompt-tools.Tests.ps1`, creating noise that made it harder to...

## Agent Inputs description uses snake_case when prompt defines kebab-case variable names

date: 2026-04-28
category: bugs
status: 
tags: agents, prompt-design, naming-convention, kebab-case, snake_case, naming-drift, cg-release, cg-release-scanner
path: .cg-docs/solutions/bugs/2026-04-28-agent-inputs-snake-case-drift-from-kebab-case-prompt-variables.md

`cg-release.prompt.md` defines and passes a computed variable named `window-days` (hyphen) and `tag-date` (hyphen) to the `@cg-release-scanner` agent. The agent's `Inputs` section, however, described the formula using underscores: ``` The hyphens in the actual variable names were correct everywhere else in both files — this was a naming-convention inconsistency confined to the parenthetical formula in the Inputs description.

## Prompt guard conditions added without Pester regression tests

date: 2026-04-28
category: testing-patterns
status: 
tags: pester, powershell, prompt-testing, guard-conditions, regression, coverage, silent-failure, cg-release
path: .cg-docs/solutions/testing-patterns/2026-04-28-prompt-guard-conditions-need-immediate-pester-coverage.md

Five distinct guard conditions were added to `cg-release.prompt.md` during the P0–P3 fix-triage cycle for the cg-release scan optimization feature: | Guard | Prompt location | Symptom if missing | |---|---|---| | `--since` ISO date after today → warn + fallback | Arguments section | Silent bad date accepted | | Shallow-clone `git log -1` empty → fallback | Step 1b | No fallback on sparse checkout | | `window-start >= today` → zero-context warning | Step 1c | User confused by empty scan | | Commit log > 500 lines → context-truncation warning | Step 1d | Silent truncation, incomplete...

## Anti-loop exclusion: output file types must be excluded from input scan in iterative review modes

date: 2026-04-24
category: testing-patterns
status: 
tags: prompt-design, cg-review, mode-verify, anti-loop, review-convergence, scan-exclusion, fix-triage
path: .cg-docs/solutions/testing-patterns/2026-04-24-anti-loop-exclusion-in-iterative-review-modes.md

`/cg-review mode:verify` scans `.cg-docs/reviews/` for the most recent review file with at least one `fixed` entry to use as suppression context. The mode also writes its own output to that same directory with the suffix `-verify-review.md`. Without an explicit exclusion, a second `mode:verify` invocation on the same feature would find the first verify-review as the "most recent with fixed entries" (because `P3.1: fixed` appears in its frontmatter), use it as the parent, and write `<stem>-verify-review.md` — overwriting itself with no meaningful suppression context. On a third pass, the pattern repeats. The loop is silent: no error is raised, but every...

## Multi-day VS Code session (68h) accumulates event listeners — unresponsive freeze and controlled restart

date: 2026-04-24
category: environment-issues
status: 
tags: vscode, crash, long-session, listener-leak, environment, copilot, agent, fix-triage, session-management
path: .cg-docs/solutions/environment-issues/2026-04-24-multi-day-vscode-session-accumulates-listeners-crashes.md

After a multi-priority fix-triage session (P0→P1→P2→P3) spanning multiple hours, VS Code became unresponsive and restarted. All in-progress changes were uncommitted. **Key log evidence** (`main.log`): ``` The VS Code session had been open since **2026-04-21T15:03:41** — a continuous **68-hour** window with window12 being the active window at time of crash. No Pester forbidden patterns appeared in logs. No non-zero exit codes. No `listener LEAK` entries in `renderer.log`. This was **not** a Pester crash — it was pure time-based listener accumulation.

## Verify-mode suppression must be anchored to fixed-finding scope, not agent-inferred consequence code

date: 2026-04-23
category: testing-patterns
status: 
tags: prompt-design, cg-review, mode-verify, suppression-policy, review-loop, fix-triage, convergence, fixed-finding-scope
path: .cg-docs/solutions/testing-patterns/2026-04-23-verify-mode-suppression-must-be-anchored-to-fixed-finding-scope.md

`/cg-review mode:verify` was designed to suppress expected P2/P3 re-findings after a fix-triage cycle so the quality loop terminates. The original suppression policy wording was: > "Suppress expected fix-consequence P2/P3 findings (those that are a direct > consequence of the changes made to address prior findings)" This is dangerous. An AI review agent reading "direct consequence of the changes made to address prior findings" has no objective anchor. It can: - Suppress a genuine new P2 by inferring it is "related to" a prior fix - Over-suppress findings in adjacent code that wasn't explicitly touched - Produce inconsistent results across sessions...

## Schema constants mirroring JSON registries need value-equality tests and cross-file maintenance anchors

date: 2026-04-22
category: testing-patterns
status: 
tags: pester, testing, schema-version, json, registry, coupling, maintenance-anchor, prompt-design, value-equality
path: .cg-docs/solutions/testing-patterns/2026-04-22-schema-constant-coupling-value-equality-test-and-maintenance-anchor.md

`repos.json` contains a `schemaVersion` field: ``` `cg-review-repos.prompt.md` Step 1 checks that the file's `schemaVersion` matches a hardcoded expected value. The Pester test for `repos.json` only verified presence: ``` This test would pass even if: - The constant was bumped in `repos.json` but not in the prompt (or vice versa) - A typo was introduced during a manual schema bump - A future developer created a new `repos.json` from scratch with an incorrect constant Additionally, neither the JSON file nor the prompt file contained any comment directing developers to keep the two values in sync.

## Prompt step with forward dependency needs explicit deferred-execution marker

date: 2026-04-21
category: testing-patterns
status: 
tags: prompt-design, step-ordering, forward-dependency, deferred-execution, skill-loading, cg-fix-triage, sequential-model
path: .cg-docs/solutions/testing-patterns/2026-04-21-prompt-step-forward-dependency-deferred-marker.md

`cg-fix-triage.prompt.md` had a `### Step 0.5: Load Language Skills` section that appeared *before* `### Step 1` in document order, but whose body said: > "After Step 1.3 identifies which file types appear in findings, load > applicable skills only for those types" This is a **forward dependency**: Step 0.5 depends on information (which file types appear in findings) that isn't available until Step 1.3 completes. Sequential-reading models follow document order. Encountering Step 0.5 first, they attempted to load language skills immediately — before findings were parsed — producing session-to-session variance in skill selection.

## Test fixtures must match function input contract, not full document format

date: 2026-04-21
category: testing-patterns
status: 
tags: powershell, pester, fixtures, input-contract, yaml, frontmatter, get-toolslist, false-positive
path: .cg-docs/solutions/testing-patterns/2026-04-21-test-fixture-must-match-function-input-contract.md

`Get-ToolsList` in `tests/helpers.ps1` accepts an extracted frontmatter **body** — the inner content between `---` delimiters, as returned by `Get-Frontmatter`. The edge-case tests in `tests/helpers.Tests.ps1` were passing full YAML blocks including delimiters: ``` The test passed — but only because `---` does not match `^\s*tools:`, not because the function correctly handled frontmatter body input. The fixture was testing the function's tolerance of unexpected delimiters, not its core logic.

## Where-Object returns PSObject[] — regex on array coerces to space-joined string

date: 2026-04-21
category: testing-patterns
status: 
tags: powershell, pester, where-object, array, coercion, regex, select-object, get-toolslist
path: .cg-docs/solutions/testing-patterns/2026-04-21-where-object-returns-array-coercion-trap.md

`Get-ToolsList` in `tests/helpers.ps1` extracted the `tools:` line from a frontmatter string and passed it directly to `[regex]::Matches()`: ``` When the frontmatter contained two `tools:` keys (e.g., malformed YAML), `$line` was a `PSObject[]` with two elements. `.NET`'s `[regex]::Matches()` expects a `[string]`; when given an array it calls `.ToString()`, which joins elements with spaces: ``` The regex then matched across the merged string, returning incorrect merged tokens rather than raising an error.

## Behavioral Pester tests for SKILL.md files: guard contracts, not just existence

date: 2026-04-20
category: testing-patterns
status: 
tags: powershell, pester, skill, SKILL.md, behavioral-test, describe-block, compound-gpid, fix-triage
path: .cg-docs/solutions/testing-patterns/2026-04-20-behavioral-pester-tests-for-skill-md-files.md

When `cg-skill-fix-triage-migrate/SKILL.md` was added to the project, the Pester test suite gained only a reference test ("skill is loaded for `--migrate` mode by name") in the `cg-fix-triage.prompt.md` describe block. The skill's own behavioral contracts — all-open default, no-delegate rule, "No legacy review files found" response, and the `prepend` instruction — had no test coverage. Because behavioral contracts live in prose, they can silently regress: an editor rewriting the Step 3 report template can accidentally remove the all-open guarantee without breaking any existing test. ``` ---

## Canonical Run-Tests.ps1 + last-run.json artifact decouples test results from agent context window

date: 2026-04-17
category: testing-patterns
status: 
tags: powershell, pester, vscode, crash, context-overflow, run-tests, json-artifact, execution-subagent, agent-safety, long-session, canonical-runner
path: .cg-docs/solutions/testing-patterns/2026-04-17-canonical-run-tests-json-artifact-decouples-test-results-from-agent-context.md

Despite 18+ documented VS Code crashes and a comprehensive `cg-skill-pester-safety` skill, agents continued to compose `Invoke-Pester` commands directly. The failure modes were: **Category A (72% of crashes):** Agent composes a forbidden pattern after context compaction (the safety rules are no longer in the active context window): ``` **Category B (28% of crashes):** Agent uses a technically-safe pattern but the full Pester output floods the agent context window in a long session: ``` The root problem is that any `Invoke-Pester` call returns or prints information that goes through the agent's context window. For a 300-test file in a long session, even...

## Exact count assertions prevent silent regression when test name states a specific count

date: 2026-04-17
category: testing-patterns
status: 
tags: pester, testing, assertion, regression, count, begreatertan, shouldbe, ps5.1, test-quality
path: .cg-docs/solutions/testing-patterns/2026-04-17-exact-count-assertion-prevents-silent-regression-when-test-name-states-count.md

A test in `helpers.Tests.ps1` was named: > "all three unconfigured fields (project-type, language, review-depth) fall back" But the assertion used a range: ``` If one of the three fields silently stopped falling back to `<not configured>` (due to a regex change, a new default value, or a guard bug), the match count would drop from 3 to 2. The test would still **pass** because `2 BeGreaterThan 1` is `$true`. The regression would be invisible until a user encountered malformed `copilot-instructions.md` output in production.

## PS5.1 Get-Content default encoding (Windows-1252) breaks equality check when file was written with UTF-8

date: 2026-04-17
category: bugs
status: 
tags: powershell, ps51, encoding, utf8, windows-1252, get-content, set-content, equality-check, idempotency, copilot-instructions, link
path: .cg-docs/solutions/bugs/2026-04-17-ps51-get-content-default-encoding-breaks-equality-check.md

`link.ps1` reads the existing `copilot-instructions.md` to compare it with freshly generated content — skipping the write if nothing changed (idempotency): ``` **Symptom**: `cg-link` always reported "generated" and rewrote the file on every run, even when the template and config had not changed. The "up to date" branch was never reached.

## Template {{placeholder}} tokens inside HTML comments are substituted by .Replace() loop, corrupting generated output

date: 2026-04-17
category: bugs
status: 
tags: powershell, template, placeholder, replace, html-comment, copilot-instructions, generation, context-layer
path: .cg-docs/solutions/bugs/2026-04-17-template-placeholder-tokens-in-html-comments-substituted-by-replace.md

When adding a documentation comment to `copilot-instructions.template.md`, the comment was written with `{{placeholder}}` tokens to describe the variables: ``` Every generated `copilot-instructions.md` in consumer projects then contained: ``` The placeholder variable names disappeared and were replaced with the real config values from the user's project. The bug was discovered during a verification review — test runs still passed because no test checked the comment text, but every consumer project would receive a corrupted, misleading HTML comment.

## YAML single-quoted values retain literal apostrophes when regex only strips double-quote delimiters

date: 2026-04-17
category: data-quality
status: 
tags: powershell, yaml, frontmatter, regex, single-quote, parsing, helpers, r-syntax, copilot-instructions
path: .cg-docs/solutions/data-quality/2026-04-17-yaml-single-quote-values-retain-apostrophes-in-ps-regex-capture.md

`compound-gpid.local.md` uses YAML frontmatter to store configuration. The field extraction regex in `helpers.ps1` was: ``` A user who wrote their config with single-quoted values (valid YAML): ``` Would get `$rSyntax = "'data.table-collapse'"` — with the apostrophes included. The generated `copilot-instructions.md` would then contain: ``` Copilot receives an unknown dialect string and silently falls back to defaults, ignoring the user's configured dialect. No error is thrown. The same issue applies to `language`, `project-type`, `review-depth`, and `project-name` — all five fields used the double-quote-only regex.

## cg-work Step 3.7 silently skips plan:null features — no fallback

date: 2026-04-15
category: bugs
status: 
tags: cg-work, roadmap, step-3-7, plan-null, silent-skip, fallback
path: .cg-docs/solutions/bugs/2026-04-15-cg-work-step-3-7-silent-skip-plan-null-features.md

When `/cg-work` implements a plan that covers roadmap features where `plan: null` (either because the features were never linked, or because the plan itself adds new features not yet in the roadmap), Step 3.7 emits a single soft warning:

## Loop early-exit directive skips per-iteration cleanup steps

date: 2026-04-15
category: bugs
status: 
tags: prompt-design, cg-work, loop, early-exit, cleanup, validate, commit, step-ordering, anti-pattern
path: .cg-docs/solutions/bugs/2026-04-15-loop-early-exit-skips-per-iteration-cleanup.md

`cg-work.prompt.md` has a `For each step in the plan` outer loop. Inside that loop, the Test Failure Recovery (TFR) block for two-attempt exhaustion instructed: ``` "Continue to the next plan step" means the **outer loop's `continue`** — jump to iteration N+1. This silently skipped every remaining sub-step of the *current* iteration: - `get_errors` (Auto-Fix Diagnostics) - `@cg-fix-problems` dispatch - **Validate** (step 5) — acceptance criteria never checked - **Commit checkpoint** (step 6) — no conventional commit suggested - **Report** (step 7) — no step summary written Code with live diagnostic errors could advance to the next plan step unexamined. If...

## New validation branch added without a test for the new code path

date: 2026-04-15
category: testing-patterns
status: 
tags: pester, powershell, coverage, validation, schema, new-branch, silent-failure, test-gap
path: .cg-docs/solutions/testing-patterns/2026-04-15-new-validation-branch-requires-dedicated-test.md

`tests/roadmap.Tests.ps1`'s `Test-RoadmapSchema` function was extended with a cross-milestone duplicate feature ID check: ``` The existing test for duplicate feature IDs used a single-milestone fixture: ``` This test never reaches the `$allFeatureIds` cross-milestone branch — it fires the *intra-milestone* `$featureIds` check instead. Both checks produce a "Duplicate feature id" error, so the test passes, and there is no signal that the cross-milestone path is untested. The fix (P3.9 from the standard review) added the validation code. The light verify-review caught it as P1.1: the new branch had zero test coverage.

## Per-batch retry counter creates unbounded loop when cascading regressions occur

date: 2026-04-15
category: bugs
status: 
tags: prompt-design, cg-work, adversarial, retry-logic, bounded-retry, test-failure-recovery, anti-pattern, loop
path: .cg-docs/solutions/bugs/2026-04-15-per-batch-retry-counter-unbounded-loop.md

`cg-work.prompt.md`'s Test Failure Recovery block defined a 2-attempt limit scoped to a specific set of *targeted failures*: ``` The problem: rule 3's full-suite re-run can expose a **new** regression that wasn't in the original targeted set. Because the counter was scoped to targeted failures (now resolved), the new failure has a **fresh counter of zero**. The LLM starts another 2-attempt cycle. That fix may again resolve targeted failures but expose another full-suite regression — and so on indefinitely. **Discovered as P0.2** in the cg-adversarial thorough review of the per-step test failure handling feature (2026-04-15).

## Pester regex without (?s) gives silent false-negative on multi-line prompt content

date: 2026-04-15
category: testing-patterns
status: 
tags: pester, regex, powershell, dotall, multiline, prompt-testing, silent-failure
path: .cg-docs/solutions/testing-patterns/2026-04-15-pester-dotall-flag-required-for-multiline-regex.md

Several Pester tests for `cg-work.prompt.md` used `.*` to span across a prompt phrase that happened to wrap across a line break: ``` All three tests **pass** — but only via their fallback alternatives. The primary alternatives die silently because `.*` in `.NET` regex does not cross `\n`. The consequence: when the fallback phrase is later renamed/rephrased, the test still passes (false negative). The primary requirement goes undetected. **Discovered as P2.6, P2.7, P2.8** in the standard review of the per-step test failure handling feature (2026-04-15).

## Pester verbose output floods agent context window in long fix-triage sessions — crash even with safe PowerShell patterns

date: 2026-04-15
category: testing-patterns
status: 
tags: powershell, pester, vscode, crash, fix-triage, context-overflow, long-session, ai-agent, copilot, quiet, prompt-tools
path: .cg-docs/solutions/testing-patterns/2026-04-15-pester-verbose-output-floods-context-long-session.md

VS Code crashed **twice in a single fix-triage session** (2026-04-15) even though all terminal commands exited with code 0. The PowerShell patterns used were technically "safe" — no forbidden pipelines, no `2>&1`, no directory run — yet VS Code crashed immediately after the Pester run completed. The commands that caused the crash: ``` **Critical detail:** Both commands exited with code 0 (tests passed). The crash did not come from PowerShell or the test runner itself — it came from the agent context window being flooded by the test output that VS Code rendered. **Session context at time of crash:** The...

## Prompt step silent-skip anti-pattern: always provide fallback with candidates when primary key lookup fails

date: 2026-04-15
category: testing-patterns
status: 
tags: prompt-design, cg-work, step-3-7, silent-skip, fallback, recovery-path, roadmap, workflow
path: .cg-docs/solutions/testing-patterns/2026-04-15-prompt-step-silent-skip-antipattern-fallback-required.md

`/cg-work` Step 3.7 ("Update Roadmap Status") matched features by `plan` path. When no features matched (because they had `plan: null`), it printed: > "No matching feature found in `roadmap.json`. Verify the plan path is linked > with `@cg-roadmap`." …and silently exited. The user saw this message buried in a long completion sequence and moved on. The roadmap was never updated. The same plan could fail to update the roadmap every time it was re-run with the same setup. **The warning message was technically correct but completely useless.** It told the user *what to do* (`@cg-roadmap`) but not *which features to...

## Roadmap feature linkage must be audited when marking a plan complete

date: 2026-04-15
category: testing-patterns
status: 
tags: roadmap, cg-work, plan, feature-linkage, data-integrity, status-drift, quality-loop
path: .cg-docs/solutions/testing-patterns/2026-04-15-roadmap-plan-linkage-must-be-audited-at-completion.md

A plan was marked `status: completed` on 2026-04-14 but four features it delivered remained unlinked (`plan: null`) and at their old status (`idea`) in `roadmap.json`. The `quality-loop` milestone continued to show as `in-progress` for a day after everything was shipped. This is a silent data integrity failure — no error, no test failure, no visible indicator. The only way to catch it is to audit the roadmap against the plan's requirements.

## Roadmap out of sync when completed plan covered plan:null features

date: 2026-04-15
category: bugs
status: 
tags: roadmap, cg-work, step-3-7, plan-null, status-drift, quality-loop
path: .cg-docs/solutions/bugs/2026-04-15-roadmap-out-of-sync-after-plan-null-features-completed.md

Four Quality Loop features were delivered by plan `.cg-docs/plans/2026-04-14-pushback-plan-review-side-ideas-schema-bypass.md` (marked `status: completed` on 2026-04-14), but `roadmap.json` was never updated. Specifically:

## Self-defeating guardrail exception: exception triggers on the same evidence the rule guards against

date: 2026-04-15
category: bugs
status: 
tags: prompt-design, cg-work, adversarial, guardrail, llm-behavior, test-failure-recovery, anti-pattern
path: .cg-docs/solutions/bugs/2026-04-15-self-defeating-guardrail-exception-in-llm-prompts.md

`cg-work.prompt.md`'s Test Failure Recovery block contained this rule: ``` The guardrail was designed to prevent an LLM from silently updating tests to match a buggy implementation. But the exception was self-defeating: the LLM can always reason: 1. My implementation causes these tests to fail. 2. The tests expect behavior my code doesn't exhibit. 3. Therefore, I changed the interface. 4. Exception applies — I may update the tests. Test failure itself becomes *proof* of interface change. The guardrail is completely nullified. Any implementation bug can be rationalized as an interface change, and tests silently updated to match buggy behavior. **Discovered...

## Mirrored conditional guard creates redundant closing clause in prompt steps

date: 2026-04-14
category: bugs
status: 
tags: prompt-design, cg-work, redundant-guard, step-structure, anti-pattern, review-finding
path: .cg-docs/solutions/bugs/2026-04-14-mirrored-conditional-guard-redundancy-in-prompts.md

A prompt step was structured as: ``` The closing guard is logically redundant: the entire body is already wrapped in the positive condition. The duplication implies the two guards apply different conditions when they do not — misleading future authors who extend the step. Caught as **P3.2** in the `2026-04-13-cg-work-roadmap-bug-review.md` thorough review of the cg-work roadmap bug fix.

## cg-work roadmap status never updated to done after plan completion

date: 2026-04-13
category: bugs
status: 
tags: cg-work, roadmap, status-drift, step-ordering, dead-code
path: .cg-docs/solutions/bugs/2026-04-13-cg-work-roadmap-status-never-updated-to-done.md

When `/cg-work` completes a feature tracked in `roadmap.json`, it marks the plan file's status as `completed` (Step 3.5) but never updates the corresponding feature's status in `roadmap.json`. Features remain as `idea` or `active` in the roadmap long after they've been built and shipped.

## Dead-step-after-wait: prompt steps after a user-wait pause never execute

date: 2026-04-13
category: testing-patterns
status: 
tags: prompt-design, copilot, cg-work, roadmap, dead-code, step-ordering, session-terminator
path: .cg-docs/solutions/testing-patterns/2026-04-13-dead-step-after-wait-prompt-session-terminator.md

`cg-work.prompt.md` had a Step 5 ("Update Roadmap Status") placed **after** Step 4 ("Summary"), which ended with: > "Wait for the user's response before proceeding." After that pause, the user picks a next action — `/cg-review`, `/cg-compound`, etc. — which starts a new conversation. Step 5 was dead code: it executed in zero of the sessions where it was supposed to run. **Observable consequence**: Three `cg-fix-problems` features completed their plans (plan frontmatter marked `status: completed`) but `roadmap.json` still showed them as `idea` / `active`. Required manual correction in a `/cg-strategy` session.

## Prompt interaction guards: all response branches must be explicitly handled

date: 2026-04-13
category: testing-patterns
status: 
tags: prompt-design, copilot, interaction, guard, branch-handling, cg-fix-triage, response-length
path: .cg-docs/solutions/testing-patterns/2026-04-13-prompt-interaction-branch-completeness.md

`cg-fix-triage.prompt.md` gained a large-report guard: when more than 15 findings are open, the prompt warns the user and waits for `[yes/batch]` before continuing. The guard instruction ended with: > "Proceed with all N anyway? [yes/batch]" > Wait for the user's response before continuing. The instruction documented the wait but not what to do when the user responds `batch`. A rule-following model that receives `batch` has no instruction to follow, so it may: - Proceed as if the user said `yes` (ignore the unspecified branch) - Display the batch commands but then continue triage anyway - Stall with no further output...

## Prompt step-ordering tests using IndexOf position comparisons

date: 2026-04-13
category: testing-patterns
status: 
tags: powershell, pester, prompt-design, indexof, step-ordering, regression, cg-work, position-assertion
path: .cg-docs/solutions/testing-patterns/2026-04-13-prompt-step-ordering-indexof-tests.md

Content-presence tests (`$content -match 'status done'`) verify that a phrase exists in a prompt file but say nothing about **where** it appears. In prompt workflows, position matters: a step that exists but appears after a "Wait for the user" pause is dead code. Example regression: `cg-work.prompt.md` had its roadmap-update dispatch in Step 5 (after the summary wait). Content tests passed — the phrase was present. The step never ran because it was unreachable.

## AI agent uses 2>&1 | Select-String when debugging test failures — crash trigger during failure investigation

date: 2026-04-09
category: testing-patterns
status: 
tags: powershell, pester, vscode, crash, ai-agent, copilot, 2>&1, debugging, failure-inspection
path: .cg-docs/solutions/testing-patterns/2026-04-09-pester-2amp1-pipe-failure-debugging-trigger.md

VS Code crashed **multiple times in a single session** during a fix-triage cycle. The agent had been told tests were failing and attempted to inspect error messages using: ``` **What makes this session distinct from previous crashes:** The agent was actively investigating the Pester crash problem itself — it knew the dangerous patterns — yet still used the `2>&1 |` forbidden pattern when reasoning about how to see what was wrong with specific failing tests. The rules were documented, the skill was loaded, yet the pattern occurred anyway. **The cognitive trigger:** "I have a failing test. How do I see...

## cg-update --list never shows installed version arrow in latest mode

date: 2026-04-08
category: bugs
status: 
tags: powershell, cg-update, --list, version-pinning, git-tag, latest-mode, arrow-marker
path: .cg-docs/solutions/bugs/2026-04-08-cg-update-list-arrow-never-shows-in-latest-mode.md

Running `cg-update --list` shows the list of available releases but the `<-- current` arrow never appears next to the installed version when the user is in `latest` (unpin) mode:

## Cross-cutting enumeration propagation: quality gate inversion and the full-audit pattern

date: 2026-04-08
category: testing-patterns
status: 
tags: powershell, pester, prompt-pipeline, severity-tier, P0, enumeration, cross-cutting, quality-gate, audit, regression-tests
path: .cg-docs/solutions/testing-patterns/2026-04-08-cross-cutting-enumeration-propagation-audit.md

After adding a P0 severity tier to all 8 review agent output templates (`**[P0|P1|P2|P3]**`), the pipeline silently contained a **quality gate inversion**: the Step 2.5 subagent output quality check in `cg-review.prompt.md` validated output by checking for `**[P1.`, `**[P2.`, or `**[P3.` entries. An agent returning *only* P0 findings (e.g., `cg-version-control` finding committed credentials) would fail the quality check — the worst-possible inversion. The pipeline would log the most critical finding of all as *unusable output*. Additional gaps discovered by the follow-up light review: | Component | Gap | |-----------|-----| | `cg-fix-triage.prompt.md` — Step 2 | Priority-level example showed `(e.g., P1, P2,...

## Hardcoded R hierarchy in agent Expertise sections bypasses dialect configuration

date: 2026-04-08
category: bugs
status: 
tags: agents, r-syntax, dialect, copilot-instructions, configuration-drift, review-agents, tidyverse, data.table, collapse
path: .cg-docs/solutions/bugs/2026-04-08-hardcoded-r-hierarchy-in-agent-files-bypasses-dialect-config.md

When the R dialect skills architecture was introduced (new `r-syntax` field in `compound-gpid.local.md`, dialect routing in `r.instructions.md`), three review sub-agents were not updated: - `cg-code-quality.agent.md` — line 12: *"Preference hierarchy: collapse > data.table > tidyverse"* - `cg-data-quality.agent.md` — same hardcoded preference - `cg-performance.agent.md` — same line, plus a review section asking *"Are `collapse` functions used instead of dplyr?"* as if dplyr were always wrong **Symptoms on a `r-syntax: "tidyverse"` project:** - `cg-code-quality` flagged correct `filter()`, `if_else()`, and dplyr joins as violations and suggested data.table replacements. - `cg-data-quality` applied `checkmate` + data.table validation idioms to tibble-based code, ignoring the project's actual...

## New prompt/agent addition checklist: 7 files that must be updated together

date: 2026-04-08
category: testing-patterns
status: 
tags: powershell, pester, prompt-pipeline, compound-gpid, checklist, model-guide, reference, copilot-instructions, prompt-tools-tests, model-assignments-tests
path: .cg-docs/solutions/testing-patterns/2026-04-08-new-prompt-agent-addition-checklist.md

Adding a new prompt (`/cg-*`) or agent (`@cg-*`) to compound-gpid requires touching at minimum 4 files. Missing any one causes a silent inconsistency: model counts in docs drift from reality, tests don't guard the new file, or users reading `copilot-instructions.md` don't know the prompt exists. The gaps catch found in the Phase 2 follow-up light review: | Gap | Severity | File missed | |-----|----------|-------------| | `/cg-compound-refresh` and `/cg-ideate` not tested in Workflow Entry Points block | P1 | `tests/prompt-tools.Tests.ps1` | | `Delete` → `Archive` rename incomplete (example table + rules section) | P2 | `cg-compound-refresh.prompt.md` | | `cg-adversarial` omitted...

## Test instruction file applyTo frontmatter to prevent silent dialect routing failure

date: 2026-04-08
category: testing-patterns
status: 
tags: powershell, pester, instruction-files, applyTo, frontmatter, dialect-routing, r-instructions, copilot, silent-failure
path: .cg-docs/solutions/testing-patterns/2026-04-08-instruction-file-applyto-frontmatter-silent-failure.md

`.github/instructions/r.instructions.md` contains an `applyTo:` field in its YAML frontmatter that controls which file types automatically trigger the instruction: ``` If this field is accidentally deleted, misspelled, or set to the wrong pattern, VS Code Copilot silently stops applying the R dialect router to `.R` files. No error is raised. The agent simply never loads the dialect skill for R files. From the user's perspective, "AI seems wrong about R style" — an ambiguous, hard-to-diagnose symptom. There was no test asserting: - The `applyTo:` key exists - It includes `**/*.R` (uppercase) - It includes `**/*.r` (lowercase) - It includes `**/*.Rmd` Without...

## Four Pester test quality patterns: shared helpers, anchored regex, non-empty value checks, and named-criteria guards

date: 2026-04-07
category: testing-patterns
status: 
tags: powershell, pester, helpers, dot-source, dry, regex, frontmatter, named-criteria, prompt-testing
path: .cg-docs/solutions/testing-patterns/2026-04-07-pester-test-quality-patterns.md

Surfaced during the 2026-04-07 model-audit light review (P1.1, P2.1, P3.1–P3.4). All four patterns apply broadly to any Pester test suite that validates YAML frontmatter or Markdown prompt files.

## AI agent repeats Pester crash pattern despite documented rules — documentation alone is insufficient

date: 2026-04-06
category: testing-patterns
status: 
tags: powershell, pester, vscode, crash, ai-agent, copilot, enforcement, context-window, safety-rules
path: .cg-docs/solutions/testing-patterns/2026-04-06-ai-agent-ignores-pester-rules-despite-documentation.md

VS Code was crashed **multiple times in a single session** by the AI agent running forbidden Pester patterns — even though the dangerous patterns were explicitly documented in: - `.github/copilot-instructions.md` (Pester Safety Rules section) - `.cg-docs/solutions/testing-patterns/2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md` The agent used this pattern on each crash: ``` The rules had been written. The agent had processed them at session start. Yet the same pattern recurred under "test verification" pressure — when the agent was focused on confirming pass/fail results, the constraint in a non-prominent section of a large instructions file was no longer in the active context window.

## Invoke-Pester on full test directory with -PassThru pipeline crashes VS Code

date: 2026-04-02
category: testing-patterns
status: 
tags: powershell, pester, vscode, crash, passthru, pipeline, junctions, agent, copilot
path: .cg-docs/solutions/testing-patterns/2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md

VS Code crashes and requires a manual restart when the agent (or user) runs Pester against the entire `tests/` directory with the `-PassThru` flag followed by a multi-stage pipeline: ``` This crash happened **four confirmed times** in the `strategy` branch fix-triage session (2026-04-02). Each occurrence required a VS Code restart. **Recurrence (2026-04-06):** Crashed again during the `vision1` branch fix-triage session — four additional times. The agent used both `Invoke-Pester tests/ -PassThru` (directory form) and `Invoke-Pester ..., ... -PassThru | Select-Object -ExpandProperty TestResult | Where-Object ...` (multi-file + ExpandProperty pipeline). Recurrence confirms the pattern as reliably dangerous, not edge-case behaviour. Symptoms:...

## Charter drift prevention: four-section rule + archive-on-removal + staleness nudge

date: 2026-04-01
category: git-workflows
status: 
tags: charter, compound-gpid.md, staleness, archive, cg-resume, structural-rule, drift, last-reviewed, frontmatter
path: .cg-docs/solutions/git-workflows/2026-04-01-charter-drift-prevention.md

`compound-gpid.md` is read at the start of every Copilot session via "Step 0: Get Bearings" — it is the shared source of truth for project context, constraints, and current focus. Without any maintenance mechanism, it drifts in predictable ways: - **Section sprawl**: Architecture notes, roadmap items, historical decisions, and meeting summaries accumulate in whatever section is nearby, making the charter increasingly long and unfocused. - **Stale focus**: The "Current Focus" section stops being updated when no prompt enforces it, so Copilot operates on outdated priorities session after session. - **Deleted history**: When content is removed to keep the charter lean,...

## cg-review missing 'write' tool disables file creation during review sessions

date: 2026-03-30
category: bugs
status: 
tags: cg-review, prompt-frontmatter, tools, write, copilot, file-creation
path: .cg-docs/solutions/bugs/2026-03-30-cg-review-missing-write-tool-disables-file-creation.md

When running `/cg-review`, the Copilot agent was unable to write any files. This affected two capabilities:

## Do NOT delegate file-writing steps in AI workflow prompts

date: 2026-03-30
category: testing-patterns
status: 
tags: powershell, pester, prompt-authoring, subagent, delegation, file-write, silent-failure, cg-review, guardrails, agent-mode
path: .cg-docs/solutions/testing-patterns/2026-03-30-do-not-delegate-file-write-guardrail.md

A multi-step AI workflow prompt (`cg-review.prompt.md`) contained a step (Step 3.5) that was supposed to write the review report to disk: ``` At runtime, the agent chose to delegate this step to a subagent. The write succeeded — inside the subagent's execution context — but when the subagent returned control to the calling agent, the file was gone. No error was raised. The review report was silently lost. **Observable symptom**: User runs `/cg-review`, sees the report summary in the chat, then runs `/cg-fix-triage` in a new session and is told _"No review reports found in `.cg-docs/reviews/`."_ No file was ever...

## PS 5.1: ConvertFrom-Json returns bare PSCustomObject for single-element arrays

date: 2026-03-30
category: bugs
status: 
tags: powershell, ps51, json, convertfrom-json, array, coercion, type-guard, schema-validation
path: .cg-docs/solutions/bugs/2026-03-30-ps51-convertfrom-json-single-element-array-coercion.md

Schema validation code that loops over `roadmap.json` `milestones` and `features` arrays silently skipped records whenever a JSON array contained exactly one element. The `-isnot [array]` type guard — intended to reject strings incorrectly passed as arrays — evaluated to `$false` for a single-element array parsed in PS 5.1, so the element was never iterated. Symptom: a roadmap with one milestone validated as if it had zero milestones. No error was raised; ids, statuses, and required fields were never checked. ```

## Test prompt frontmatter tools: list to guard against silent write failures

date: 2026-03-30
category: testing-patterns
status: 
tags: powershell, pester, prompt-frontmatter, tools, copilot, write, agent-mode, guardrails
path: .cg-docs/solutions/testing-patterns/2026-03-30-test-prompt-frontmatter-tools-list.md

VS Code Copilot prompt files support a `tools:` key in their YAML frontmatter that restricts which tools the agent may use when executing that prompt. If a prompt's process steps involve writing files (creating reports, applying fixes, saving output), but `'write'` is absent from the `tools:` list, those steps silently fail — the agent cannot write, produces no error, and the user is left with no artifacts. This is especially insidious because: - The failure is **silent**: no exception, no error message from the runtime - The symptom (agent "can't write files") appears only at runtime, not at development time...

## Test the interface contract between chained prompts (review -> fix-triage pipeline)

date: 2026-03-30
category: testing-patterns
status: 
tags: powershell, pester, prompt-pipeline, compound-ids, cg-review, cg-fix-triage, guardrails, workflow
path: .cg-docs/solutions/testing-patterns/2026-03-30-prompt-pipeline-contract-testing.md

When two prompts are designed to work in sequence — the OUTPUT of one prompt is the INPUT of a follow-up prompt — the interface between them is fragile. If the upstream prompt silently changes its output format (ID scheme, file path, or cross-reference text), the downstream prompt breaks with no error: it simply finds no matching findings, reads the wrong file, or never gets invoked by the user because the upstream prompt forgot to mention it. Concretely, the review → fix-triage pipeline has three fragile joints: 1. **File location**: `cg-review.prompt.md` must write reports to `.cg-docs/reviews/`. If the path changes,...

## Validate derived state against stored state in schema tests

date: 2026-03-30
category: testing-patterns
status: 
tags: powershell, pester, schema-validation, derived-state, invariant, status-drift, roadmap
path: .cg-docs/solutions/testing-patterns/2026-03-30-derived-invariant-validation-in-schema-tests.md

`Test-RoadmapSchema` validated that `milestone.status` was a member of the allowed enum (`planned`, `in-progress`, `done`). It did **not** verify that the stored status matched the value that `Get-MilestoneStatus` would derive from the milestone's features array. A roadmap file could therefore contain `{"status":"done"}` while all its features had `status: "planned"`. The schema validator passed it; the discrepancy was invisible at commit time. ``` `Test-RoadmapSchema` would return 0 errors. `Get-MilestoneStatus` would return `"planned"`. No test caught the mismatch.

## .cg-docs/ must not be gitignored — institutional knowledge must be committed

date: 2026-03-23
category: git-workflows
status: 
tags: gitignore, cg-docs, compound-engineering, link, setup, institutional-knowledge, knowledge-sharing
path: .cg-docs/solutions/git-workflows/2026-03-23-cg-docs-must-not-be-gitignored.md

`.cg-docs/` contains the primary knowledge output of the Compound Engineering workflow: brainstorms, plans, and solutions captured via `/cg-compound`. If this directory is gitignored, the following breakdowns occur: - Solutions captured on one machine are invisible to all other team members. - When a new Copilot session starts, `cg-learnings-researcher` cannot find past solutions — the entire knowledge-compounding loop is broken. - Plans and brainstorms are silently lost when a branch is switched or a machine is wiped. - The `/cg-compound` prompt itself becomes pointless: it writes files that git immediately ignores. The bug was silent. No error was raised; the files...

## Case-insensitive regex silently accepts invalid git tag names

date: 2026-03-23
category: bugs
status: 
tags: powershell, regex, git, validation, case-sensitivity, tags, cg-update
path: .cg-docs/solutions/bugs/2026-03-23-case-insensitive-regex-fails-git-tag-validation.md

`cg-update V0.2.0` would pass the version validation check and then fail later at `git checkout V0.2.0` with a confusing "pathspec did not match any file(s) known to git" error. The user sees no helpful message pointing them back to the bad input.

## Idempotent .gitignore block management with remove-then-rewrite

date: 2026-03-23
category: git-workflows
status: 
tags: gitignore, idempotent, block-management, powershell, regex, vendor-section
path: .cg-docs/solutions/git-workflows/2026-03-23-idempotent-gitignore-block-management.md

A tool (Compound GPID's `cg-link`) maintains a named section in the project's `.gitignore`. When the set of managed entries changes between versions (e.g. an entry is renamed or removed), a simple "append if the header is absent" approach leaves orphaned lines from the old block in the file. Symptoms: - Running `cg-link` multiple times produces duplicate sections. - After a version upgrade that renames an entry, the old entry stays in `.gitignore` and keeps blocking commits of a file the user now wants tracked. - The file grows unboundedly on repeated tool invocations.

## PS 5.1: BOM-less UTF-8 em-dash silently corrupts AST, causing wrong if/else pairing

date: 2026-03-23
category: bugs
status: 
tags: powershell, ps51, encoding, utf8, bom, em-dash, ast, if-else, windows-1252, control-flow
path: .cg-docs/solutions/bugs/2026-03-23-ps51-utf8-bom-em-dash-corrupts-ast-silently.md

`cg-update` was always entering the pinned-mode branch even when `.cg-version` contained `"latest"`. No error was thrown. The output was coherent (e.g. "Checking out latest..." followed by `Release 'latest' not found`) -- it looked like a logic error, not a parse error. The relevant code: ``` Despite `$versionMode` being `"latest"`, execution always entered the `else` branch.

## Checklist for consolidating (merging/renaming) VS Code Copilot skills

date: 2026-03-22
category: git-workflows
status: 
tags: skills, copilot, consolidation, refactoring, instructions, SKILL.md
path: .cg-docs/solutions/git-workflows/2026-03-22-skill-consolidation-checklist.md

When two skills (`cg-skill-stata-core` + `cg-skill-stata-research`) were merged into `cg-skill-stata-best-practices`, several cross-references were left pointing at the deleted skills. The thorough review caught them, but they should have been caught at merge time. Symptoms that revealed the problem: - `docs/reference.md` still listed two old skill rows - `ROADMAP.md` still named the old skills in two places (lines 17–18 and 57) - `.cg-docs/solutions/bugs/*.md` Related sections linked to deleted skill files - `SKILL.md` grew to 412 lines with inline content that belonged in sub-files - `.github/instructions/stata.instructions.md` contained GPID-specific variable names (`$gpid_root`, `gpid_fgt`) in a file intended to be project-generic

## Bare catch {} on Invoke-RestMethod swallows non-404 HTTP errors

date: 2026-03-19
category: build-errors
status: 
tags: powershell, invoke-restmethod, github-api, error-handling, catch, http, 404, bearer-token
path: .cg-docs/solutions/build-errors/2026-03-19-invoke-restmethod-bare-catch-swallows-non-404-errors.md

A script checking for an existing GitHub Release before creating one used an empty `catch {}` around the `GET /releases/tags/<tag>` call: ``` The intent was: "if the release doesn't exist (404), proceed to create it." But the bare `catch {}` also swallowed 401 (bad token), 403 (insufficient scope), 429 (rate limit), 500 (server error), and network timeouts — all of which left `$existingRelease` as `$null`. The script would then fall through to the POST (create) path and fail there with a less informative error.

## Copilot hallucinates non-existent Stata functions for variable label checks

date: 2026-03-19
category: bugs
status: 
tags: stata, copilot-hallucination, labelled, variable-labels, validation, assert, regexm, PPP
path: .cg-docs/solutions/bugs/2026-03-19-copilot-hallucinates-stata-label-functions.md

Copilot generates calls to functions that do not exist in Stata when writing validation or assertion code that inspects variable labels, value labels, or variable metadata: ``` These statements produce an immediate error: `unknown function labelled()`. The analysis halts, but only if the assertion is actually reached — if guarded by `capture`, the error is silently swallowed and validation is bypassed.

## Explicit-unpin command does not persist when the target branch does not write back to state file

date: 2026-03-19
category: bugs
status: 
tags: powershell, state-management, cg-version, version-pinning, unpin, latest, regression
path: .cg-docs/solutions/bugs/2026-03-19-explicit-unpin-does-not-persist-missing-state-file-write.md

After pinning to `v0.2.0` with `cg-update v0.2.0`, running `cg-update latest` appeared to succeed: - The working tree switched back to `main`. - `git pull` ran and showed "up to date" or new commits. But on the next bare `cg-update` call, the output showed: ``` The unpin did not persist. `.cg-version` still contained `v0.2.0`.

## Fragile matrix indexing for regression results in Stata

date: 2026-03-19
category: bugs
status: 
tags: stata, regression, coefficients, e(b), matrix-indexing, poverty, FGT, survey
path: .cg-docs/solutions/bugs/2026-03-19-fragile-matrix-indexing-regression-results-stata.md

Code that extracts regression coefficients or standard errors using positional matrix indexing silently produces wrong results if the model specification changes (different variable order, additional controls, dropped observations): ``` In poverty analysis this manifests as extracting the wrong coefficient from a welfare regression — the estimated headcount ratio or standard error will be numerically plausible but correspond to the wrong regressor. There is no error message.

## Persistent state file written before validation causes permanent corruption on bad input

date: 2026-03-19
category: bugs
status: 
tags: powershell, state-management, file-write, validation, atomicity, cg-version, version-pinning
path: .cg-docs/solutions/bugs/2026-03-19-persistent-state-written-before-validation-causes-corruption.md

`cg-update v9.9.9` (a non-existent tag) would: 1. Write `v9.9.9` to `.cg-version` immediately on argument parse. 2. Fail on tag validation — `git tag --list` returns nothing for that tag. 3. Throw and exit with an error. After this, every subsequent bare `cg-update` would read `v9.9.9` from `.cg-version` and fail again — permanently — until the user manually deleted or edited the file. The machine was stuck. **Symptom**: `cg-update` consistently fails with "Release 'v9.9.9' not found" even when run with no arguments, for any user.

## PowerShell null interpolation silently corrupts pipe-delimited output contracts

date: 2026-03-19
category: data-quality
status: 
tags: powershell, null, interpolation, output-contract, api-response, invoke-restmethod, github-api, pipe-delimited
path: .cg-docs/solutions/data-quality/2026-03-19-api-response-null-fields-corrupt-output-contract.md

A script writes release metadata to `release-result.txt` in the format `CREATED|<id>|<url>`: ``` If the GitHub API response is missing `id` or `html_url` (schema change, partial error body, unexpected API version), PowerShell silently interpolates `$null` as `""`, producing: ``` The downstream consumer (a Copilot prompt parsing the file by splitting on `|`) reads these as structurally valid and reports "success" with a blank URL. No error is ever raised.

## Testing PowerShell [switch] parameters: magic-string API tests pass for the wrong reasons

date: 2026-03-19
category: testing-patterns
status: 
tags: powershell, pester, switch-parameter, magic-string, api-mismatch, regression, cg-update, --list
path: .cg-docs/solutions/testing-patterns/2026-03-19-testing-powershell-switch-parameters.md

After refactoring `update.ps1` to replace the magic string `--list` with a proper `[switch]$List` parameter, the existing test still passed: ``` The test was asserting that the old guard expression (`$Version -ne "--list"`) evaluates to `$false`. It never tested that `$List.IsPresent` is `$true`, and it never tested that `$Version` would actually be empty when `--list` is passed through PowerShell's parameter binder. This meant: - The test passed after the refactor because the expression `"--list" -ne "--list"` still evaluates to `$false`. - But if someone accidentally removed the `[switch]$List` declaration and reverted to magic-string handling, the test would still pass — providing...

## Broken relative links in deeply-nested skill files pointing to repo root

date: 2026-03-18
category: bugs
status: 
tags: markdown, links, relative-paths, skill-files, documentation, cross-references
path: .cg-docs/solutions/bugs/2026-03-18-broken-relative-links-in-nested-skill-files.md

A cross-reference link in `r-analytical-anti-patterns.md` read: ``` This path resolves *relative to the file's location*, which is: `.github/skills/cg-skill-r-analytical/references/` So the link actually resolves to: `.github/skills/cg-skill-r-analytical/references/.cg-docs/solutions/...` — which does not exist. The link was silently broken. GitHub renders it as a dead link; clicking it returns a 404.

## collapse na.rm global option differs from base R and affects all f* functions

date: 2026-03-18
category: data-quality
status: 
tags: collapse, na.rm, global-options, set_collapse, welfare-measurement, silent-errors
path: .cg-docs/solutions/data-quality/2026-03-18-collapse-na-rm-global-option-welfare-risk.md

All collapse Fast Statistical Functions (`fmean`, `fsum`, `fmedian`, `fvar`, etc.) default to `na.rm = TRUE` — the **opposite** of base R functions like `mean()` which propagate NA. This is controlled by a global option system, not a hardcoded default. Two failure modes: 1. **Unaware mode**: Code silently drops NA observations from welfare aggregations. A survey with 5% missing welfare values computes poverty rates over 95% of the population as if it were 100%. No warning. 2. **Changed-mode**: A script earlier in the session calls `set_collapse(na.rm = FALSE)`. All subsequent `fmean`/`fsum` calls now propagate NA and return `NA` instead of estimates....

## Plumber endpoint testing: make_req() helper pattern

date: 2026-03-18
category: testing-patterns
status: 
tags: plumber, testing, testthat, http, make_req, api, unit-test
path: .cg-docs/solutions/testing-patterns/2026-03-18-plumber-make-req-helper-for-unit-tests.md

When writing unit tests for plumber API endpoints using `pr$call()`, there is no built-in `make_req()` function in plumber. Skill documentation (and many blog posts) reference this helper without defining it, causing immediate `Error: could not find function "make_req"` when tests run. A secondary issue: naively implemented helpers accept `query` and `body` parameters but hardcode `QUERY_STRING = ""` and ignore `body`, so tests that exercise query parameters or POST bodies silently pass with wrong behaviour.

## Pre-compute GRP once for blocks with multiple aggregations over the same grouping

date: 2026-03-18
category: performance-issues
status: 
tags: collapse, GRP, fmean, fsum, grouped-aggregation, performance, welfare-measurement, regional-analysis
path: .cg-docs/solutions/performance-issues/2026-03-18-grp-precomputation-for-multi-aggregation.md

A common pattern in GPID welfare code computes several statistics by region in consecutive calls: ``` Each call passes `g = dt$region` (a raw vector). Internally, collapse must sort and hash that vector to build a `GRP` object for grouping every single time. With 4 calls on the same grouping variable, the group structure is built **4 times redundantly**. On surveys with 50k+ households and 20+ regions this is noticeable; on the full GPID microdata (millions of rows) it becomes a meaningful bottleneck.

## survey_mean_se() divides by zero on singleton PSU strata

date: 2026-03-18
category: data-quality
status: 
tags: collapse, survey, standard-errors, taylor-linearization, poverty-measurement, divide-by-zero
path: .cg-docs/solutions/data-quality/2026-03-18-survey-mean-se-singleton-psu-divide-by-zero.md

`survey_mean_se()` returns `se = Inf` and `ci_lower/ci_upper = ±Inf` with no error or warning when any stratum contains exactly one Primary Sampling Unit (PSU). This is silent — the function completes and returns a result that looks plausible but is meaningless. Certainty strata (strata with a single PSU selected with probability 1) are common in complex LSMS and household survey designs. Analysts may not notice the Inf values if they don't inspect SE output carefully.

## Unclosed code fence in Markdown skill files silently corrupts downstream rendering

date: 2026-03-18
category: bugs
status: 
tags: markdown, documentation, code-fence, rendering, skill-files, copy-paste
path: .cg-docs/solutions/bugs/2026-03-18-unclosed-code-fence-corrupts-markdown-rendering.md

In `welfare-patterns.md`, a ` ```r ` fence opened at the start of the Verification Tests section was never closed. An incomplete duplicate `test_that(...)` block was accidentally appended after the last test case, which consumed the opening fence of the *next* section. The result: - Everything after the last valid test case rendered as raw R code inside the fenced block - The `## Multiple Poverty Lines` section heading disappeared from navigation - Blockquote callouts (` > Run the pre-checks...`) rendered as literal text inside a code block - No parse error, no linter warning — visually looks fine in a...

## Zero or negative welfare values silently inflate FGT(1) and FGT(2) beyond their valid range

date: 2026-03-18
category: data-quality
status: 
tags: fgt, poverty-measurement, welfare, data-validation, collapse, fifelse, poverty-gap, silent-errors
path: .cg-docs/solutions/data-quality/2026-03-18-zero-negative-welfare-inflates-fgt-beyond-1.md

The FGT(1) poverty gap index and FGT(2) squared poverty gap index both assume welfare is **strictly positive**. When a welfare value is zero or negative, the gap formula produces a value **greater than 1**: ``` Since `fmean()` averages all gaps (including those > 1) without any bounds checking or warning, the resulting FGT(1) silently exceeds 1 — which is mathematically impossible for a correctly computed poverty gap index.

## httpx.AsyncClient requires ASGITransport for FastAPI async tests

date: 2026-03-17
category: testing-patterns
status: 
tags: httpx, fastapi, pytest, async, asgi, testing, deprecated
path: .cg-docs/solutions/testing-patterns/2026-03-17-httpx-async-client-asgi-transport.md

FastAPI async endpoint tests using `httpx.AsyncClient(app=app, ...)` fail or emit deprecation warnings on httpx ≥ 0.23. The `app=` shorthand was removed. ```

## Null welfare values silently bias poverty rate — must drop before computing

date: 2026-03-17
category: data-quality
status: 
tags: polars, poverty, welfare, null, weights, data-quality, gpid, survey-data
path: .cg-docs/solutions/data-quality/2026-03-17-null-welfare-silently-biases-poverty-rate.md

A headcount poverty rate computed over survey microdata is systematically lower than expected. No errors or warnings are raised. The issue is silent. ``` When `welfare_col` contains nulls, polars' `filter` excludes null-welfare rows from `poor` (they fail the `< poverty_line` comparison), but `df[weight_col].sum()` still counts their survey weights in the denominator. Those households are implicitly treated as **non-poor** rather than as **missing data**, understating the poverty rate. A second silent failure: `df[weight_col].sum()` with null weights silently drops those nulls, understating the denominator further.

## run_in_threadpool does not bypass the GIL for CPU-bound work — use ProcessPoolExecutor

date: 2026-03-17
category: bugs
status: 
tags: fastapi, async, gil, threading, multiprocessing, performance, cpu-bound, io-bound
path: .cg-docs/solutions/bugs/2026-03-17-run-in-threadpool-does-not-bypass-gil.md

A FastAPI endpoint offloads heavy computation to a thread pool using `run_in_threadpool`, expecting real parallel execution. Under concurrent load, all requests still serialise — performance is no better than running on the event loop directly, and the comment "offload to thread pool to avoid blocking the event loop" is misleading. ```

## Backslash-escaped quotes in PowerShell double-quoted strings break % operator parsing

date: 2026-03-13
category: build-errors
status: 
tags: powershell, string-escaping, backtick, backslash, cmd-wrapper, percent-operator, parse-error
path: .cg-docs/solutions/build-errors/2026-03-13-backslash-quote-in-powershell-string-breaks-percent-operator.md

`install.ps1` failed at parse time with: ``` The script was building `.cmd` wrapper content inside a PowerShell double-quoted string and used `\"` (backslash-escaped double quotes) to embed literal `"` characters, with `%~dp0` and `%*` as CMD batch tokens.

## CLM blocks .NET method calls — use reg.exe for PATH manipulation

date: 2026-03-13
category: environment-issues
status: 
tags: powershell, clm, constrained-language-mode, dotnet, environment-variable, PATH, reg-exe, applocker, wdac, enterprise
path: .cg-docs/solutions/environment-issues/2026-03-13-clm-blocks-dotnet-method-calls-use-reg-exe.md

On WBG enterprise machines, calling `[Environment]::GetEnvironmentVariable` or `[Environment]::SetEnvironmentVariable` in PowerShell throws: ``` This blocked the documented uninstall procedure (Step 2 — remove old PATH entry) and would also block `install.ps1`'s PATH registration step.

## Regression test for try/catch control-flow guards when script cannot be executed

date: 2026-03-13
category: testing-patterns
status: 
tags: powershell, pester, regression-test, try-catch, clm, OneDrive, control-flow, simulation
path: .cg-docs/solutions/testing-patterns/2026-03-13-regression-test-trycatch-guard-clm-environment.md

A PS5.1 bug (`ErrorActionPreference=Stop` promoting git stderr to a terminating error) was fixed in `update.ps1` by wrapping `git checkout .` in a `try/catch`. The fix needed a regression test to prevent it from being accidentally removed during future refactors. However, Pester 3.4 cannot dot-source or invoke scripts located under OneDrive paths due to Constrained Language Mode (CLM) — the same environment restriction the fix was addressing. Running `Invoke-Pester update.Tests.ps1` from the OneDrive workspace fails with `CommandNotFoundException` for the script path itself.

## Troubleshooting documentation belongs in manual, not README

date: 2026-03-13
category: environment-issues
status: 
tags: documentation, readme, manual, troubleshooting, structure, architecture
path: .cg-docs/solutions/environment-issues/2026-03-13-troubleshooting-doc-structure-readme-vs-manual.md

A troubleshooting section was added to `README.md` during a hotfix (documenting a `cg-update` bootstrap failure). Because it was the first such entry and README was the most visible file, it landed there. A second entry followed. With more issues inevitable, this created a divergence: `docs/manual.md` exists as the operational reference but troubleshooting content was accumulating in `README.md` instead.

## PS5.1 ErrorActionPreference=Stop promotes git informational stderr into terminating errors

date: 2026-03-05
category: git-workflows
status: 
tags: powershell, powershell-5.1, git, stderr, ErrorActionPreference, 2>null, git-checkout
path: .cg-docs/solutions/git-workflows/2026-03-05-ps51-stderr-stop-terminates-on-git-informational-output.md

After removing `2>$null` from `git checkout .` (following the general rule "don't suppress stderr"), the script started failing with: ``` `git checkout .` was succeeding — "Updated N paths from the index" is its normal stdout/stderr output — but the script was catching it as a fatal error. Running `cg-update` from any project directory would immediately abort.

## $$  is not a process ID in PowerShell

date: 2026-03-04
category: build-errors
status: 
tags: powershell, pid, temp-files, unique-names, guid
path: .cg-docs/solutions/build-errors/2026-03-04-powershell-dollar-dollar-is-not-pid.md

A script used `$$` to generate a unique temp directory name, as is idiomatic in Bash/sh: ``` The intent was to get the current process ID so temp paths would not collide across parallel runs. In testing: - On the first command of a session `$$` expands to an **empty string**. - On subsequent commands it expands to the **last token typed on the previous line** (e.g., `install.ps1`, or `True`). - Two instances running simultaneously get the same "PID" value. - The resulting paths are not unique and a duplicate-directory error is thrown.

## Add-if-missing config blocks create duplicate headers; use remove-then-rewrite

date: 2026-03-04
category: testing-patterns
status: 
tags: powershell, idempotency, gitignore, config-blocks, remove-then-rewrite, deduplication
path: .cg-docs/solutions/testing-patterns/2026-03-04-add-if-missing-creates-duplicate-config-headers.md

A script managed a named section in a text config file (`.gitignore`, a profile, an `.ini`) using an "add if missing" strategy: ``` After upgrading the tool and adding a new entry (e.g. `.github/instructions/`): ``` The existing entries are not duplicated, but the *header comment* is written again for each run that has new entries. Over multiple upgrades the file accumulates several identical headers, which confuses users and can break tooling that parses the section.

## Get-Item .Target property is string[] in PowerShell 5.1, not a scalar string

date: 2026-03-04
category: build-errors
status: 
tags: powershell, junctions, symlinks, get-item, target, string-array, comparison
path: .cg-docs/solutions/build-errors/2026-03-04-get-item-target-is-string-array.md

Code that checks whether a junction points to a specific directory passed all unit tests but produced confusing results in edge cases: ``` The intent is a boolean check. In practice: - `$item.Target` is `string[]`, not `string`. - `-like` on an array returns **all matching elements** (a filtered array), not `$true`/`$false`. - An empty array is falsy; a non-empty matching array is truthy — so the `if` block *happens* to work for the common case. - But code reviewers reading `$item.Target -like "pattern"` expect a boolean comparison and will misunderstand the code. - If `.Target` ever contains multiple entries (rare...

## git stderr swallowed by 2>&1 redirect into an unused variable

date: 2026-03-04
category: git-workflows
status: 
tags: powershell, git, stderr, redirection, exit-code, error-handling
path: .cg-docs/solutions/git-workflows/2026-03-04-git-pull-stderr-swallowed-by-redirect.md

A script captured git output like this: ``` The intent was to capture output so it could be formatted. In practice: - `2>&1` merges stderr into stdout. - Assigning the merged stream to `$pullOutput` swallows **both** stdout and stderr — nothing is printed to the terminal, not even git's progress/error messages. - The `$LASTEXITCODE` check fires on failure, but the user sees only the generic error message, not git's actual diagnostic (e.g., "Your local changes would be overwritten", "refusing to merge unrelated histories"). - When `$pullOutput` is never used again in the script, it is dead code — the capture...

## Pester $TestDrive cleanup follows junction links, hanging VS Code

date: 2026-03-04
category: testing-patterns
status: 
tags: powershell, pester, vscode, junctions, testdrive, freeze, cleanup, ms-vscode.powershell
path: .cg-docs/solutions/testing-patterns/2026-03-04-pester-testdrive-follows-junctions-freezes-vscode.md

VS Code froze completely and required a force-quit — reproducibly, every time the workspace was opened. The freeze happened silently: no error messages, no crash dialog. Symptoms: - VS Code becomes unresponsive within seconds of opening the workspace - PowerShell terminal and IntelliSense stop responding - Force-quitting and reopening causes the same freeze immediately - Only occurs in workspaces that contain `*.Tests.ps1` files that create directory junctions

## Pester 3.4 vs Pester 5 syntax — Windows built-in compatibility

date: 2026-03-04
category: testing-patterns
status: 
tags: powershell, pester, testing, windows, compatibility, pester3, pester5
path: .cg-docs/solutions/testing-patterns/2026-03-04-pester-3-vs-5-windows-compatibility.md

Tests were written using Pester 5 syntax and ran fine in CI but failed on team Windows machines with errors such as: ``` Root session example: ```

## Constraining file writes in output-producing prompts without agent: plan mode

date: 2026-03-02
category: testing-patterns
status: 
tags: prompts, guardrails, file-permissions, agent-mode, copilot
path: .cg-docs/solutions/testing-patterns/2026-03-02-prompt-file-permission-guardrails.md

When designing prompts that should not modify source code (e.g., `cg-brainstorm`, `cg-plan`), the natural instinct is to use `agent: plan` mode in the YAML frontmatter. However, `agent: plan` mode prevents **all** file writes — including writing the output documents these prompts are specifically designed to produce (`docs/brainstorms/`, `docs/plans/`). The symptoms: - Prompt runs correctly through Q&A - At the capture step, fails silently or errors when trying to write the output file - Or: switching to `agent: plan` means the output is only shown inline in chat, never persisted to disk

## Skills are not slash-command prompts — avoid advertising them as /skill-name

date: 2026-03-02
category: environment-issues
status: 
tags: prompts, skills, copilot, ux, naming, slash-commands
path: .cg-docs/solutions/environment-issues/2026-03-02-skill-vs-prompt-slash-command.md

Documentation (README, manual) instructed users to run `/cg-setup` in Copilot Chat to configure their project. However, there is no `.github/prompts/cg-setup.prompt.md` file — the setup entry point is `.github/skills/cg-skill-setup/SKILL.md`, which is a **skill**, not a prompt. Typing `/cg-setup` in Copilot Chat produces no result or an error because Copilot only resolves `/name` commands to `.prompt.md` files in `.github/prompts/`.
