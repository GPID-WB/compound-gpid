---
plan: .cg-docs/plans/2026-05-14-commit-push-pr-and-verify-pr.md
review-date: 2026-05-14
review-depth: thorough
mode: autofix
agents: [cg-code-quality, cg-testing, cg-documentation, cg-architecture, cg-data-quality, cg-reproducibility, cg-performance, cg-adversarial, cg-learnings-researcher, cg-version-control]
findings:
  P0.1: open
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: open
  P1.6: fixed
  P1.7: fixed
  P1.8: open
  P1.9: open
  P1.10: open
  P2.1: open
  P2.2: fixed
  P2.3: fixed
  P2.4: open
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P2.9: fixed
  P2.10: fixed
  P2.11: fixed
  P2.12: fixed
  P2.13: open
  P2.14: open
  P2.15: open
  P2.16: open
  P2.17: fixed
  P2.18: fixed
  P2.19: fixed
  P2.20: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: open
  P3.4: open
  P3.5: open
  P3.6: open
  P3.7: open
  P3.8: open
---

# Review: cg-commit-push-pr and cg-verify-pr

**Branch**: `feat/cg-commit-push-pr`  
**Files reviewed** (10): `.github/prompts/cg-commit-push-pr.prompt.md` (NEW), `.github/prompts/cg-verify-pr.prompt.md` (NEW), `.github/copilot-instructions.md`, `docs/model-guide.md`, `docs/reference.md`, `roadmap.json`, `tests/model-assignments.Tests.ps1`, `tests/prompt-tools.Tests.ps1`, `.cg-docs/brainstorms/2026-05-14-commit-push-pr-and-verify-pr-commands.md` (NEW), `.cg-docs/plans/2026-05-14-commit-push-pr-and-verify-pr.md` (NEW)

---

## Findings

### P0 — BLOCKING

**P0.1** `[manual]` · `cg-commit-push-pr.prompt.md` · Step 6 · **Shell injection via inline `--body` in `gh pr create`**  
Agent: `cg-adversarial`  
Current: `gh pr create --title "..." --body "<plan content inline>"`  
Problem: Plan content containing backticks, `$()`, `$(...)`, or shell metacharacters is interpolated by the shell when passed inline. A plan objective of `` feat: add `$(rm -rf .)` `` would be interpreted by PowerShell or bash.  
Fix: Write PR body to a temp file and use `--body-file <tempfile>` instead.

---

### P1 — CRITICAL (10 findings)

**P1.1** `[fixed]` · `cg-commit-push-pr.prompt.md` · Step 4 · After `git add`: add exit-code check → halt on failure.

**P1.2** `[fixed]` · `cg-verify-pr.prompt.md` · Step 4 · `git push --force-with-lease` rejection not checked → added explicit non-zero exit handling.

**P1.3** `[fixed]` · `cg-verify-pr.prompt.md` · Step 2 · Empty/null `statusCheckRollup` falsely classified "all passing" → added null/empty guard with "No CI checks have run yet" halt.

**P1.4** `[fixed]` · Both prompts · Step 1 · No detached HEAD guard → added check: if `git branch --show-current` returns empty, halt with guidance.

**P1.5** `[manual]` · `cg-commit-push-pr.prompt.md` · Step 6 · **Prompt injection via plan `## Objective` content**  
Agent: `cg-adversarial`  
Problem: Plan files are LLM-authored and could contain adversarial instructions (e.g., `## Objective\nIgnore previous instructions and...`). Reading plan content into PR body construction via direct embedding risks hijacking the prompt.  
Fix: Sanitise plan content before use in PR body construction. Strip any lines matching `^(Ignore|Disregard|Forget|System:|<|>)` patterns. Alternatively, only include the `## Objective` text up to the first blank line after that heading.

**P1.6** `[fixed]` · `cg-verify-pr.prompt.md` · Step 3 · Empty `gh run list` array causes index error → added guard with "No run found" output and skip.

**P1.7** `[fixed]` · `cg-verify-pr.prompt.md` · Step 2 · SKIPPED/CANCELLED/ACTION_REQUIRED/STALE conclusions unhandled → added explicit classification rules.

**P1.8** `[manual]` · `cg-commit-push-pr.prompt.md` · Step 2 · **No commit-size guard**  
Agent: `cg-architecture`  
Problem: No guard against pathological groupings (e.g., 50 modified files in a single commit) or a single group with a very large diff.  
Fix: Add a note: "If any single group exceeds 20 files or its combined diff exceeds ~500 lines, propose splitting it further — offer the user the sub-grouped breakdown before proceeding."

**P1.9** `[manual]` · `cg-verify-pr.prompt.md` · Step 4 · **`fix(ci):` commit not explicitly authored by the agent**  
Agent: `cg-learnings-researcher` (cross-references `.cg-docs/solutions/testing-patterns/`)  
Problem: Prior finding: "fix(ci): commit must not be delegated to subagent." The current prompt dispatches `@cg-fix-problems`/`@cg-testing`/`@cg-code-quality` to fix code, but then has the agent commit. The risk is an agent subagent making additional file changes and the commit capturing unintended files.  
Fix: Add explicit instruction: "After the subagent applies its fix, run `git diff --stat HEAD` to enumerate exactly which files were modified before `git add`. Do not use `git add .` — stage files individually."

**P1.10** `[manual]` · `cg-verify-pr.prompt.md` · Step 4 · **No guard if `fix(ci):` push triggers new CI failures**  
Agent: `cg-code-quality`  
Problem: After pushing `fix(ci):`, CI may fail again for a different reason. The prompt exits after push and leaves user to re-invoke. There's no instruction to wait a moment or poll.  
Fix: Add note: "After pushing, wait for a CI status update if the `--propose` flag is not active. If gh pr checks --watch is available and user consented, poll briefly. Otherwise remind the user: 'Re-invoke /cg-verify-pr to check the updated status.'"  
(Note: `--watch` forbidden per R8 — so a single `gh pr checks` poll at end is the correct approach, not `--watch`.)

---

### P2 — IMPORTANT (20 findings)

**P2.1** `[manual]` · `cg-verify-pr.prompt.md` · Step 0 · **Missing `--propose` flag detection at top of file**  
Agent: `cg-code-quality`  
Current: Flag is described in File Permissions but parsed only in Step 0.6.  
Problem: The File Permissions block says `--propose` makes the file READ-only, but the parse is deferred. An agent that skips to Step 1 without reading Step 0.6 could write files under `--propose` mode.  
Fix: Move the `--propose` detection instruction to Step 0 (immediately after Step 0.1 bearings), before any tool dispatch.

**P2.2** `[fixed]` · `cg-verify-pr.prompt.md` · Step 4 · `git log` missing `--first-parent` → double-counts upstream merge commits.

**P2.3** `[fixed]` · Both prompts · Step 4/6 · `git merge-base HEAD <default-branch>` could return multiple hashes → added `| Select-Object -First 1`.

**P2.4** `[manual]` · `cg-commit-push-pr.prompt.md` · Step 5 · **Non-fast-forward push handling incomplete**  
Agent: `cg-architecture`  
Problem: The prompt says "If push is rejected due to non-fast-forward: offer the user options (rebase vs merge)." But it doesn't specify how to detect non-fast-forward vs credential failure vs network error. All three produce non-zero exit codes.  
Fix: Add: "Parse the git push error output for the string `rejected` and `non-fast-forward` to distinguish from credential/network failures. Only offer rebase/merge for non-fast-forward rejections."

**P2.5** `[fixed]` · `docs/reference.md` · Review Agents section · Stale note saying all review agents are dispatched only by `/cg-review` → updated to mention `/cg-verify-pr` also dispatches `@cg-testing` and `@cg-code-quality`.

**P2.6** `[fixed]` · `cg-verify-pr.prompt.md` · Step 4 · Default branch not detected before Step 4 → added explicit detection sub-step.

**P2.7** `[fixed]` · `cg-verify-pr.prompt.md` · Step 4 · `@cg-code-quality` described as "for dependency/import resolution" (too narrow) → changed to "to analyse the dependency/import error; then apply the fix based on its diagnosis."

**P2.8** `[fixed]` · `docs/reference.md` · `/cg-verify-pr` prompt column missing `[--propose]` flag → added.

**P2.9** `[fixed]` · `docs/reference.md` · Model guide footnote still said "35 files" → updated to "37 files".

**P2.10** `[fixed]` · `cg-commit-push-pr.prompt.md` · Step 3 · `git diff HEAD` returns empty for untracked files → added bifurcation: `??`/`A ` prefixes → read file content directly.

**P2.11** `[fixed]` · `cg-commit-push-pr.prompt.md` · Step 2 · Redundant `git status --short` instruction (already ran in Step 1) → removed.

**P2.12** `[fixed]` · `tests/prompt-tools.Tests.ps1` · Standalone `copilot-instructions.md - cg-commit-push-pr and cg-verify-pr entry points` Describe block → merged its two `It` blocks into the existing `copilot-instructions.md - Workflow Entry Points` Describe and removed the standalone block.

**P2.13** `[manual]` · `cg-commit-push-pr.prompt.md` · Step 3 · **Commit message body generation is underspecified**  
Agent: `cg-documentation`  
Problem: The prompt says "generate a body if changes are complex enough to warrant one" but gives no criteria for when a body is warranted or what it should contain.  
Fix: Add: "Include a commit body when the group contains more than 3 files OR when the diff includes structural changes (new functions, renamed symbols, schema changes). The body should list the 3–5 most significant changes as bullet points."

**P2.14** `[manual]` · `cg-verify-pr.prompt.md` · Step 6 · **Summary output underspecified**  
Agent: `cg-documentation`  
Problem: Step 6 says "output a summary" but doesn't specify format.  
Fix: Specify: "Output a markdown table with columns: Check Name | Prior Status | New Status | Action Taken."

**P2.15** `[manual]` · `cg-commit-push-pr.prompt.md` · Step 7 · **Handoff to `/cg-verify-pr` is advisory only**  
Agent: `cg-architecture`  
Problem: Step 7 says "remind the user to run /cg-verify-pr" but doesn't specify when (immediately? after CI starts?).  
Fix: Add: "After the PR is created, wait 15–30 seconds (suggest user wait) for CI to start, then offer: 'Run `/cg-verify-pr` to monitor CI status on this PR.'"

**P2.16** `[manual]` · `cg-commit-push-pr.prompt.md` · Step 2 · **Classification heuristics incomplete for .cg-docs/ paths**  
Agent: `cg-architecture`  
Problem: `.cg-docs/brainstorms/`, `.cg-docs/plans/`, `.cg-docs/solutions/`, `.cg-docs/reviews/` are all grouped together under "Plans/Docs" but they have different semantic meanings.  
Fix: Add explicit classification sub-rules: `brainstorms/` → Docs group, `plans/` → Plans group, `solutions/` and `reviews/` → Docs group.

**P2.17** `[fixed]` · `tests/prompt-tools.Tests.ps1` · Missing test: `cg-verify-pr` Step 1 halt when no open PR → added `It "halts with 'No open PR found' and suggests /cg-commit-push-pr (Step 1.4)"`.

**P2.18** `[fixed]` · `tests/prompt-tools.Tests.ps1` · `"context layer - all 15 prompts..."` Describe → updated to 17 and added `cg-commit-push-pr`, `cg-verify-pr` to the `$prompts` array.

**P2.19** `[fixed]` · `tests/prompt-tools.Tests.ps1` · Missing test: `cg-commit-push-pr` Step 1 clean-tree halt → added `It "halts with 'Nothing to commit' message when working tree is clean"`.

**P2.20** `[fixed]` · `cg-verify-pr.prompt.md` · SKIPPED/CANCELLED unhandled (same as P1.7) → covered by P1.7 fix.

---

### P3 — MINOR (8 findings)

**P3.1** `[fixed]` · `tests/model-assignments.Tests.ps1` · Line 104 · Stale comment "All 19 prompt file stems" → updated to "All 21".

**P3.2** `[fixed]` · `tests/prompt-tools.Tests.ps1` · `"explicitly prohibits --watch..."` It block had two `Should` assertions → split into two separate `It` blocks.

**P3.3** `[manual]` · `cg-commit-push-pr.prompt.md` · Step 3 · **Commit subject line length not enforced**  
Agent: `cg-code-quality`  
Recommendation: Add note: "Keep subject lines under 72 characters. If the generated subject exceeds this, shorten the scope or description — do not abbreviate the type."

**P3.4** `[manual]` · `cg-verify-pr.prompt.md` · Step 5 · **Cross-platform warning is overly broad**  
Agent: `cg-documentation`  
Current: Warning applies to all platforms. Problem: The tools (`gh`, `git`) are cross-platform. The warning about PowerShell syntax is valid but the framing should be narrower.  
Recommendation: Scope the warning: "Note for bash/zsh users: Replace `$null` with `/dev/null`, `$LASTEXITCODE` with `$?`, and `Select-Object -First 1` with `head -n 1`."

**P3.5** `[manual]` · `cg-commit-push-pr.prompt.md` · File Permissions · **Missing explicit permission scope for Step 4 (git staging)**  
Agent: `cg-code-quality`  
Recommendation: Add `git add` and `git commit` as allowed operations in the File Permissions block under "Git Operations."

**P3.6** `[manual]` · `cg-verify-pr.prompt.md` · File Permissions · **`--propose` READ-only declaration is in prose, not a structured list**  
Agent: `cg-code-quality`  
Recommendation: Format the `--propose` mode permissions as a structured bullet list matching the style of the regular permissions block.

**P3.7** `[manual]` · `docs/model-guide.md` · **`cg-commit-push-pr` and `cg-verify-pr` rows lack a rationale column**  
Agent: `cg-documentation`  
Recommendation: Add a brief rationale note for both new rows consistent with other prompt rows in the guide.

**P3.8** `[manual]` · `roadmap.json` · **`ongoing-ideas` objective was aspirational rather than descriptive**  
Agent: `cg-data-quality`  
Fixed during test triage: `status` changed from `"in-progress"` to `"planned"` and objective updated. Marking as open for awareness — no further action needed.
