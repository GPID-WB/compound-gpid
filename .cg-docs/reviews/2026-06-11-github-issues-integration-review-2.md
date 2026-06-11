---
review-date: 2026-06-11
plan: .cg-docs/plans/2026-06-11-github-issues-integration.md
trigger: second review cycle (post-fix review of first-review changes)
mode: thorough
agents:
  - cg-code-quality
  - cg-adversarial
  - cg-testing
  - cg-documentation
  - cg-version-control
  - cg-learnings-researcher
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: deferred
  P3.1: deferred
  P3.2: deferred
  P3.3: deferred
  P3.4: deferred
  P3.5: fixed
  P3.6: fixed
  P3.7: deferred
---

# Second Review — GitHub Issues Integration

**Plan**: `.cg-docs/plans/2026-06-11-github-issues-integration.md`
**Review Date**: 2026-06-11
**Cycle**: Second review of Phase 1 security-hardening changes

---

## Passed ✅

- All new `tests/roadmap.Tests.ps1` tests (issueUrl issues/0 rejection, labelPrefix empty rejection, Adopt contract test, known-gap test) — correct and well-formed
- `features[].github` Default column in `docs/reference.md` — correctly shows `—`
- `[1-9]\d*` regex in `Test-RoadmapSchema` — correctly rejects issue 0
- Non-blocking touchpoint annotations in `docs/workflow.md` — accurate
- No credentials, API keys, or PII in any modified file
- `cg-skill-pester-safety` Pester safety rules — no violations in any test file

---

## P1 — CRITICAL (Must Fix Before Commit)

### [P1.1] [safe_auto] `cg-issues.prompt.md` step 6 — triple-backtick in untrusted content breaks fenced block

**Agent**: @cg-adversarial  
**File**: `.github/prompts/cg-issues.prompt.md`, step 6  
**Finding**: A plan file or roadmap description containing a ` ``` ` sequence closes the fenced ```` ```text ```` block prematurely. Any content after the closing fence is rendered outside the block and may be interpreted as agent instructions.  
**Fix**: Instruct the agent to escape or replace ` ``` ` occurrences in untrusted content before inserting it into the fenced block.  
**Status**: fixed

---

### [P1.2] [manual] `cg-issues.prompt.md` step 5 — realpath check is prose-only

**Agent**: @cg-adversarial  
**File**: `.github/prompts/cg-issues.prompt.md`, step 5  
**Finding**: "Resolve the path to its canonical real path" is an instruction to the LLM, but the LLM cannot call `readlink -f` or `Resolve-Path` — it can only reason about paths by string analysis. Symlink traversal is still exploitable in practice.  
**Fix**: Change the instruction to explicitly require executing `Resolve-Path` (PowerShell) or `readlink -f` (bash/Linux) via a tool call, then compare the resulting string against the expected prefix.  
**Status**: fixed

---

### [P1.3] [safe_auto] `cg-roadmap.agent.md` Configure GitHub Issues — `labelPrefix` not validated for shell-unsafe chars

**Agent**: @cg-adversarial  
**File**: `.github/agents/cg-roadmap.agent.md`, Configure GitHub Issues operation step 1  
**Finding**: `labelPrefix` is stored in `roadmap.json` and later embedded in `gh label list` and `gh issue create --label "prefix+name"` shell commands. A value containing `"` or other shell metacharacters injects extra CLI arguments.  
**Fix**: Add regex validation `^[A-Za-z0-9_.\ :/-]*$` for `labelPrefix` in the Configure operation. Also add label composition validation in the backfill step 8 label building.  
**Status**: fixed

---

### [P1.4] [manual] `docs/troubleshooting.md` line 622 — `in-progress` is not a valid feature status

**Agent**: @cg-code-quality, @cg-documentation (duplicate, deduplicated)  
**File**: `docs/troubleshooting.md`, ~line 622  
**Finding**: "Update feature `<feature-id>` in milestone `<milestone-id>` to status `in-progress`." — `in-progress` is a **milestone** status, not a valid **feature** status. Valid feature statuses are `idea`, `planned`, `active`, `done`. Using `in-progress` here would cause schema validation to fail and @cg-roadmap to reject the write.  
**Fix**: Change `in-progress` → `active`.  
**Status**: fixed

---

## P2 — IMPORTANT (Should Fix Before Commit)

### [P2.1] [safe_auto] `cg-issues.prompt.md` step 9 — TOCTOU warning is ambiguous (warn-but-proceed)

**Agent**: @cg-adversarial  
**File**: `.github/prompts/cg-issues.prompt.md`, step 9  
**Finding**: "warn the user before proceeding" is ambiguous — the agent may proceed to dispatch @cg-roadmap Attach after the warning, creating orphan duplicates (two issues linked to the same feature).  
**Fix**: Change to an explicit stop with three choices: (a) delete the newly-created issue and link the existing one; (b) proceed acknowledging the duplicate; (c) abort. Do NOT dispatch @cg-roadmap until the user chooses.  
**Status**: fixed

---

### [P2.2] [manual] `cg-issues.prompt.md` Safety Rules — blocklist out of sync with step 6

**Agent**: @cg-code-quality  
**File**: `.github/prompts/cg-issues.prompt.md`, Safety Rules section  
**Finding**: Step 6 strips `Assistant:`, `[INST]`, and `###` (case-insensitive) but the Safety Rules blocklist bullet does not list those tokens — it only lists `Ignore`, `Disregard`, `Forget`, `System:`, `<`, `>`. The canonical blocklist is inconsistently maintained across two locations.  
**Fix**: Sync the Safety Rules blocklist bullet to match step 6 exactly.  
**Status**: fixed

---

### [P2.3] [manual] `docs/reference.md` — `labelPrefix` Default column shows `""` but empty string fails schema

**Agent**: @cg-code-quality  
**File**: `docs/reference.md`, `features[].github` table  
**Finding**: The Default column for `labelPrefix` shows `""`, but an empty string would fail the new `^[A-Za-z0-9_.\ :/-]*$` validation (and even absent the new validation, empty string is semantically different from absent/null — no prefix should be represented as absent/null, not empty string).  
**Fix**: Change Default to `—` (absent/null means no prefix).  
**Status**: fixed

---

### [P2.4] [safe_auto] `tests/prompt-tools.Tests.ps1` ~line 2092 — Duplicate Describe block for P2.6 context exception

**Agent**: @cg-testing  
**File**: `tests/prompt-tools.Tests.ps1`, ~line 2092  
**Finding**: The "context layer - cg-issues intentionally omits Get Bearings" Describe block appears twice. The first copy uses `$cgIssuesContent`; the second uses `$content`. Both contain the same two tests, so they run four total assertions in two passes. The duplicate inflates the test count and can cause confusing output if one copy passes and the other fails.  
**Fix**: Delete the first copy (lines ~2092–2102, using `$cgIssuesContent`); keep the second copy (using `$content`).  
**Status**: fixed

---

### [P2.5] [safe_auto] `tests/prompt-tools.Tests.ps1` ~line 6188 — P2.9 test in wrong Describe block

**Agent**: @cg-testing  
**File**: `tests/prompt-tools.Tests.ps1`, ~line 6188  
**Finding**: The "gracefully handles missing gh — status mode continues without gh (P2.9)" test is in the `/cg-issues.prompt.md - pre-flight checks` Describe block. Graceful degradation is a **status mode safety** property; it belongs in the `/cg-issues.prompt.md - confirmation and safety` Describe block.  
**Fix**: Move the `It "gracefully handles missing gh..."` test from the pre-flight Describe to the confirmation/safety Describe.  
**Status**: fixed

---

### [P2.6] [manual] `tests/prompt-tools.Tests.ps1` — Missing test for `Closes #` / `Fixes #` / `Resolves #` title stripping

**Agent**: @cg-testing  
**File**: `tests/prompt-tools.Tests.ps1`, confirmation and safety Describe block  
**Finding**: Step 6 and the Safety Rules both call out that `Closes #`, `Fixes #`, and `Resolves #` must be stripped from feature titles. There is no test asserting this behavior.  
**Fix**: Add `It "strips Closes # / Fixes # / Resolves # from feature titles before --title"` in the confirmation/safety Describe block.  
**Status**: fixed

---

### [P2.7] [manual] `tests/prompt-tools.Tests.ps1` — Missing test for fenced `text` block instruction

**Agent**: @cg-testing  
**File**: `tests/prompt-tools.Tests.ps1`, confirmation and safety Describe block  
**Finding**: Step 6 requires that untrusted content be rendered in a fenced ` ```text ` block. There is no test asserting the prompt instructs this fencing.  
**Fix**: Add `It "renders untrusted content in fenced text block (prevents instruction injection)"` asserting `$content -match '` ```text`'`.  
**Status**: fixed

---

### [P2.8] [advisory] `cg-issues.prompt.md` PF2 + status step 1 — `gh issue view` before gh guard

**Agent**: @cg-adversarial  
**File**: `.github/prompts/cg-issues.prompt.md`, Mode: status, step 1  
**Finding**: Step 1 includes an imperative "run `gh issue view <number> --json state`" inside a conditional clause ("If `gh` is available"). In sequential LLM execution, this may be interpreted as a direct command before the conditional is evaluated.  
**Fix**: Rewrite step 1 to explicitly branch: "If `gh` is available: run `gh issue view <number> --json state`. Otherwise: note 'cannot verify — `gh` unavailable'."  
**Status**: deferred (advisory — current phrasing includes the conditional; re-test after P2.1/P2.2 fixes land to verify no regression)

---

## P3 — MINOR

### [P3.1] [advisory] `cg-roadmap.agent.md` Adopt step 1 — glob vs. strict regex inconsistency

**Agent**: @cg-adversarial  
**File**: `.github/agents/cg-roadmap.agent.md`, Adopt operation step 1  
**Finding**: Step 1 of Adopt says "issueUrl (string matching `https://github.com/*/issues/<number>`)", which is a glob-style description. The Attach operation uses the strict regex `^https://github\.com/[^/]+/[^/]+/issues/[1-9]\d*$`. An LLM using Adopt may pass a looser URL at dispatch time.  
**Fix**: Replace the glob with the strict regex in the Adopt step 1 description.  
**Status**: deferred

---

### [P3.2] [advisory] `cg-issues.prompt.md` step 6 — `Closes #` strip not applied to body content

**Agent**: @cg-adversarial  
**File**: `.github/prompts/cg-issues.prompt.md`, step 6  
**Finding**: `Closes #` / `Fixes #` / `Resolves #` stripping is documented for `--title` only. Plan file body content with `Closes #45` would survive into `--body-file`.  
**Fix**: Extend the strip to body content lines as well (or document that body references are intentional and trusted).  
**Status**: deferred

---

### [P3.3] [advisory] `cg-issues.prompt.md` step 6/8 — implicit `gh` shell quoting assumption

**Agent**: @cg-code-quality  
**File**: `.github/prompts/cg-issues.prompt.md`, steps 6 and 8  
**Finding**: Stripping `"` and backtick from titles relies on implicit `gh` CLI quoting rules. A comment explaining *why* these specific characters are stripped (and that `gh` wraps the title in double quotes) would make the intent clearer for future maintainers.  
**Fix**: Add inline comment: `# strip " and ` to prevent CLI argument injection (title is passed as --title "<sanitized>")`.  
**Status**: deferred

---

### [P3.4] [advisory] `cg-roadmap.agent.md` — `(required)` vs. `no` terminology clash

**Agent**: @cg-code-quality  
**File**: `.github/agents/cg-roadmap.agent.md`, Attach/Adopt step 1 and schema table  
**Finding**: Operation steps say `issueNumber` and `issueUrl` are `(required)`, but the schema table column header is "Required" with values of `no` for both fields. Minor inconsistency.  
**Fix**: Change schema table "Required" values for `issueNumber` and `issueUrl` to `yes (when github block present)` or restructure to avoid duplication.  
**Status**: deferred

---

### [P3.5] [advisory] `tests/prompt-tools.Tests.ps1` P2.10 — second regex arm over-broad

**Agent**: @cg-testing  
**File**: `tests/prompt-tools.Tests.ps1`, ~line 6194  
**Finding**: The P2.10 safety rules test has two regex arms: `Status mode is read.?only` and `read.?only.*status.*mode`. The second arm would match unrelated strings like "read-only mode for status reports". The first arm is precise and sufficient.  
**Fix**: Remove second regex arm; keep `Status mode is read.?only` only.  
**Status**: fixed

---

### [P3.6] [advisory] `tests/roadmap.Tests.ps1` known-gap test missing "how to fix" comment

**Agent**: @cg-testing  
**File**: `tests/roadmap.Tests.ps1`, known-gap test  
**Finding**: The test documents a known gap (issueUrl/issueNumber mismatch is allowed) but has no comment explaining what to do when the gap is eventually closed.  
**Fix**: Add inline comment: `# WHEN FIXING THIS GAP: delete this test and add a 'rejects issueUrl/issueNumber mismatch' test instead`.  
**Status**: fixed

---

### [P3.7] [advisory] `docs/workflow.md` — `/cg-commit-push-pr` touchpoint omits qualifier

**Agent**: @cg-documentation  
**File**: `docs/workflow.md`  
**Finding**: The `/cg-commit-push-pr` touchpoint row does not mention that `Closes #` in PR body triggers auto-close, which requires confirmation. Minor omission.  
**Status**: deferred

---

## Version Control Actions

Stage both untracked files before commit:
```powershell
git add .cg-docs/reviews/2026-06-11-github-issues-integration-review.md
git add .cg-docs/solutions/bugs/2026-06-11-cli-injection-in-llm-driven-gh-prompts.md
```

Commit message:
```
fix(cg-issues): security hardening round 2 from 2026-06-11 review
```
