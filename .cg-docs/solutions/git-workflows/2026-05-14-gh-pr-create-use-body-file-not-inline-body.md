---
date: 2026-05-14
title: "gh pr create: use --body-file not inline --body to prevent shell injection"
category: "git-workflows"
language: "both"
tags: [gh, pull-request, shell-injection, security, prompt-design, cg-commit-push-pr]
root-cause: "Plan content passed inline via --body is interpolated by the shell before gh sees it"
severity: "P0"
---

# gh pr create: use --body-file not inline --body to prevent shell injection

## Problem

A prompt using `gh pr create --title "..." --body "<plan content>"` passes the PR
body inline on the command line. When plan content contains backticks, `$()`,
`${VAR}`, or other shell metacharacters, PowerShell and bash interpolate them
before `gh` receives the argument.

Example: a plan `## Objective` value of `` feat: add `$(whoami)` `` would execute
`whoami` silently if the body is passed inline. In bash, `$(rm -rf .)` would delete
the working tree.

Discovered as P0.1 in the `cg-commit-push-pr`/`cg-verify-pr` thorough review.

## Root Cause

Shell argument interpolation happens before `gh` parses the flag. The `--body` flag
accepts a string argument, so any `$(...)`, backtick expansion, or variable
reference in the string is evaluated by the shell first.

Plan files are LLM-authored or human-authored and may contain any character. The
content is fully attacker-controlled from the shell's perspective.

## Solution

Write the PR body to a temp file first, then pass the path with `--body-file`:

```powershell
# PowerShell
$tmpFile = [System.IO.Path]::GetTempFileName()
try {
    $bodyContent | Set-Content $tmpFile -Encoding UTF8
    gh pr create --title $title --body-file $tmpFile
} finally {
    Remove-Item $tmpFile -ErrorAction SilentlyContinue
}
```

```bash
# bash/zsh
tmp=$(mktemp)
printf '%s' "$body_content" > "$tmp"
gh pr create --title "$title" --body-file "$tmp"
rm -f "$tmp"
```

`--body-file` reads the file contents verbatim — no shell interpolation occurs.

## Prevention

- **Prompt design rule**: Any prompt step that constructs a PR body from file
  content (plans, brainstorms, commit messages) must use `--body-file <tmp>`,
  never `--body "<inline>"`.
- **Test signal**: A test asserting `($content -match 'body-file')` catches
  regressions if the pattern is removed from the prompt.
- **Scope**: applies to any `gh pr create`, `gh pr edit`, or `gh issue create`
  call whose body comes from a file or variable — not just from a literal string
  known at write time.

## Related

- `.cg-docs/solutions/testing-patterns/2026-04-29-two-phase-injection-guard-for-agent-file-reads.md` — prompt injection via untrusted file content
- `.cg-docs/solutions/bugs/2026-06-11-cli-injection-in-llm-driven-gh-prompts.md` — extends `--body-file` pattern to `--label` quoting, `--title` sanitization, and symlink traversal prevention
- `.cg-docs/solutions/git-workflows/2026-03-04-git-pull-stderr-swallowed-by-redirect.md`
