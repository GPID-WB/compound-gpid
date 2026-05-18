---
branch: feat/command-default-behaviors
date: 2026-05-18
depth: thorough
type: standard
test-baseline: "1827 passed / 0 failures"
findings:
  # --- Autofix applied (prior session) ---
  P1.1: fixed
  P2.1-code-quality: fixed
  P2.1-testing: fixed
  P2.2-testing: fixed
  P3.2-code-quality: fixed
  P3.3-docs: fixed
  # --- Fixed in fix-triage session ---
  P1.1-adversarial: fixed
  P1.2-adversarial: fixed
  P1.3-adversarial: fixed
  P1.5-adversarial: fixed
  P2.3-code-quality: fixed
  P2.3-docs: fixed
  P2-arch-brainstorm: fixed
  P2-arch-uncommitted: fixed
  P2-arch-plan: fixed
  P2-arch-review: fixed
  P2-testing-tpmode: fixed
  P2-testing-mutual: fixed
  # --- Advisory: no action required ---
  P3.1-docs: advisory
  P3.2-docs: advisory
  P2.1-adversarial: advisory
  P2.2-adversarial: advisory
  P2.3-adversarial: advisory
  P2.4-adversarial: advisory
  P3.3-code-quality: advisory
---

# Review Report — feat/command-default-behaviors

**Branch**: `feat/command-default-behaviors`  
**Date**: 2026-05-18  
**Depth**: Thorough  
**Agents**: `cg-code-quality`, `cg-testing`, `cg-documentation` (×2), `cg-architecture`, `cg-adversarial`, `cg-version-control`  
**Test baseline**: 1,827 passed / 0 failures (after autofix)

---

## Autofix Applied

### **[P1.1]** `cg-compound.prompt.md` — `--no-enrich` did not gate Step 3c wiki dispatch  
**Root cause**: Step 5 checked `enrich = false` but Step 3c dispatched `@cg-wiki` unconditionally, violating the promise in `reference.md` ("skip context.md and wiki enrichment"), File Permissions, and Step 0.5 comment.  
**Fix applied**: Added `If enrich = false (i.e., --no-enrich was passed): skip this step entirely.` at the top of Step 3c. Also updated File Permissions: `"modify"` → `"create or modify"`.  
**Tests added**: `"Step 3c wiki dispatch is gated by enrich flag"` and `"enrich defaults to true when --no-enrich is absent"` in `tests/prompt-tools.Tests.ps1`.

### **[P2.1-code-quality / P2.1-testing]** Stale `It` block in `prompt-tools.Tests.ps1`  
**Root cause**: `It "offers phase breakdown for Deep scope"` used a broad regex `(?i)Deep.*phases` which passed vacuously on advisory text, not behavioral Step 3.5 code.  
**Fix applied**: Updated to `It "phases by default applies to Deep scope plans"` with scoped regex `(?s)Step 3.5.*organized into phases by default`.

### **[P2.2-testing]** Broad `auto-creates branch` regex matched File Permissions, not behavioral text  
**Root cause**: `automatically create|auto.*create|Created branch` matched the File Permissions line rather than Step 1.7's behavioral text.  
**Fix applied**: Narrowed to `automatically create and switch to the feature branch`.

### **[P3.2-code-quality]** Stale Describe title  
**Fix applied**: `"cg-review.prompt.md - mode:autofix argument"` → `"cg-review.prompt.md - mode:autofix backward compatibility"`.

### **[P2.2-testing / phases-default regex]** `phases-default` regex too coarse  
**Fix applied**: `($content -match 'phases-default')` → `($content -match '--no-phases.*phases-default|phases-default.*false')`.

---

## Manual Findings — Pending User Decision

### **[P1.1-adversarial]** `cg-brainstorm.prompt.md` — Auto-branch fires in detached HEAD  
`git branch --show-current` returns empty string (not a failure) in detached HEAD. The pre-flight guard only checks for command failure. A user in detached HEAD gets the "feature branch" path with an empty branch name, and if they choose "new", a branch is created from the wrong base commit.  
**Recommended fix**: Add a guard after `git branch --show-current` for empty output: "Detected detached HEAD. Cannot safely auto-branch. Reattach to a branch first or pass `--no-branch`."

### **[P1.2-adversarial]** `cg-brainstorm.prompt.md` — Missing branch name normalization  
`cg-plan.prompt.md` Step 0.7 normalizes branch names (strips `~^:?*[\`, collapses `..`, strips `@{`, truncates to 60 chars). `cg-brainstorm.prompt.md` Step 1.7 has no normalization spec. Special characters in the user's description (e.g., `&` on bash) could produce invalid or shell-dangerous branch names.  
**Recommended fix**: Copy the normalization block from `cg-plan.prompt.md` Step 0.7 into `cg-brainstorm.prompt.md` Step 1.7.

### **[P1.3-adversarial]** `cg-brainstorm.prompt.md` — `git init` offered when `git branch --show-current` fails for non-repo reasons  
The prompt uses `git branch --show-current` failure as a proxy for "not in a git repo." This fails on git < 2.22 (the flag didn't exist), `.git` with wrong permissions, or git not on PATH — all of which are in a git repo.  
**Recommended fix**: Use `git rev-parse --git-dir` as the "are we in a git repo?" test separately from branch detection.

### **[P1.5-adversarial]** `cg-compound.prompt.md` — Non-append-only context.md insertion can corrupt structured content  
Step 5 instructs inserting "logically within the existing structure, not appended at the end." On context.md with tables or code fences, an insertion mid-structure breaks formatting silently.  
**Recommended fix**: Change to append-only: "Append to the bottom of the matching section (add a new `###` subsection if needed) — never insert within existing lines."

### **[P2.3-code-quality]** `cg-brainstorm.prompt.md` — File Permissions lacks `git init` carve-out  
The absolute prohibition "You must NOT create files outside `.cg-docs/brainstorms/`" contradicts Step 1.7 offering to run `git init` (which creates `.git/`).  
**Recommended fix**: Add a File Permissions carve-out: "You may run `git init` in Step 1.7 when the user confirms in a non-git workspace."

### **[P2-arch-brainstorm]** `--no-branch` not parsed at Step 0 (convention violation)  
The write-permission flag convention requires flags to be evaluated at Step 0 or Step 0.5 before any tool dispatch. `--no-branch` is only evaluated inline at Step 1.7's pre-flight, after Steps 1, 1.1, and 1.5 have run.  
**Recommended fix**: Add `5. Parse flags: if --no-branch is present, set branch-enabled = false.` as the last item of Step 0. Reference `branch-enabled` in Step 1.7.

### **[P2-testing-mutual]** No test for `--report-only` + `mode:verify` mutual exclusion  
The prompt specifies that passing both flags should warn and use `mode:verify`. This contract has no test coverage.  
**Recommended fix**: Add `It "mutual exclusion: --report-only + mode:verify resolves to mode:verify"` asserting `($content -match 'ignore.*--report-only') | Should -Be $true`.

---

## Advisory Findings

- **[P3.1-docs]** `reference.md`: "(no prompt)" is inaccurate when uncommitted changes exist. Change to "(no prompt unless uncommitted changes exist)".
- **[P3.2-docs]** `reference.md`: "On a feature branch, prompts stay or new" missing default indicator. Add "(default: stay)".
- **[P2.1-adversarial]** Non-standard default branches (`trunk`, `develop`) cause silent fallback to "feature branch" path — auto-create never fires.
- **[P2.2-adversarial]** `phases: N` frontmatter in plan files may become stale after manual edits; downstream tooling may use it as authoritative.
- **[P2.3-adversarial]** `[safe_auto]` fixes that rename symbols don't check callers in unreviewed files.
- **[P2.4-adversarial]** `--propose` gates only wiki dispatch mode; context.md is written directly regardless.
- **[P3.3-code-quality]** `--report-only` flag name breaks the `--no-*` naming pattern used by all other new flags.

---

## Test Results After Autofix

```
TotalCount: 1827 | PassedCount: 1827 | FailedCount: 0
```

No regressions. 2 new tests added by autofix (Step 3c wiki gate, enrich=true default path).
