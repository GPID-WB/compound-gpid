---
plan: .cg-docs/plans/2026-04-23-review-convergence-verify-mode.md
findings:
  P1.1: fixed
  P1.2: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P2.9: fixed
  P2.10: fixed
  P2.11: fixed
  P2.12: fixed
  P2.13: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: skipped
  P3.7: fixed
  P3.8: fixed
  P3.9: fixed
  P3.10: fixed
  P3.11: fixed
  P3.12: fixed
---

## Review Report

**Review depth**: thorough
**Files reviewed**: 6 modified + 2 untracked
**Findings**: 27 (P0: 0, P1: 2, P2: 13, P3: 12)

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-version-control] Branch — Changes are on `main`, not `feat/review-verify-mode`.
  **Why**: The plan explicitly names `feat/review-verify-mode` as the implementation branch. Direct commits to `main` bypass PR review and cannot be cleanly reverted.
  **Fix**: `git checkout -b feat/review-verify-mode` now; all current unstaged changes transfer automatically to the new branch.

- **[P1.2]** [cg-learnings-researcher] `.github/prompts/cg-review.prompt.md` Step 1.7.3 — Suppression policy is potentially self-defeating.
  **Why**: An LLM can always reason "this code was changed since the last review → it is fix-consequence code → suppress the P2/P3." The suppression trigger (code changed after the last review) is directly observable from git, making any P2/P3 on changed lines suppressible. This was documented in `.cg-docs/solutions/bugs/2026-04-15-self-defeating-guardrail-exception-in-llm-prompts.md`. The policy should anchor suppression to the **prior review's `fixed` map**, not to the agent's inference about "fix-consequence" code.
  **Fix**: Rewrite the P2/P3 suppression rule as: "Suppress P2/P3 only when the finding is on a function or block whose refactoring was explicitly listed as a `fixed` finding in the `parent-review` frontmatter. Do not suppress based on inference that code looks like a fix or was written recently."

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality + cg-architecture] `.github/prompts/cg-review.prompt.md:36` — Step 1.5 has no `mode:verify` skip guard at its header.
  **Why**: Step 1.5 is executed before Step 1.7. The retroactive skip instruction in Step 1.7 item 5 comes too late — a sequentially-processing model applies `light → standard` escalation from Step 1.5 before reading the override. The Step 2 verify dispatch block partially compensates but doesn't undo "always add" agent triggers.
  **Fix**: Add at the top of Step 1.5: `Skip this step if \`mode:verify\` was passed (Step 1.7 enforces light depth and disables overrides).` Remove item 5 from Step 1.7.

- **[P2.2]** [cg-code-quality] `.github/prompts/cg-review.prompt.md:114` — Verify-mode dispatch block is silent on language-specific skill loading.
  **Why**: The R/Python/Stata skill checks above say "all depth levels," but the verify dispatch block overrides Step 2 without confirming skill loading still applies. Different agents may omit skill loading during verify passes.
  **Fix**: Append to the verify dispatch block: `Language-specific skill loading still applies — see R/Python/Stata skill checks above.`

- **[P2.3]** [cg-code-quality] `.github/prompts/cg-review.prompt.md:177` — No deduplication rule for consecutive verify passes on the same parent review.
  **Why**: Two verify rounds against the same standard review produce the same filename (`foo-verify-review.md`), silently overwriting the first verify report.
  **Fix**: Add: `If \`<stem>-verify-review.md\` already exists, append a counter: \`<stem>-verify-review-2.md\`, etc. Or document overwrite as intentional ("latest verify pass supersedes prior ones").`

- **[P2.4]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test for verify-mode agent dispatch restriction.
  **Why**: The prompt's "Verify mode agent dispatch" block restricts to `@cg-code-quality` and `@cg-testing` only. If this block were deleted, no test would catch it.
  **Fix**: Add: `It "verify mode dispatches only cg-code-quality and cg-testing" { ($content -match '(?s)[Vv]erify mode.*cg-code-quality.*cg-testing|cg-code-quality.*cg-testing.*light.*forced') | Should Be $true }`

- **[P2.5]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test for the anti-loop exclusion rule (verify-review files excluded from prior-review scan).
  **Why**: The most important correctness invariant of `mode:verify` — without it a verify pass could select a previous verify review as its parent, looping indefinitely.
  **Fix**: Add: `It "excludes -verify-review.md files from prior review scan" { ($content -match '(?s)verify-review\.md.*[Ss]kip|[Ss]kip.*verify-review\.md') | Should Be $true }`

- **[P2.6]** [cg-testing + cg-code-quality] `tests/prompt-tools.Tests.ps1:2714` — Fix-triage test `"suggests mode:verify … in Step 5"` matches any occurrence of `mode:verify` in the file.
  **Why**: Passes even if `mode:verify` appears only in a comment. The test name asserts Step 5 placement but the regex doesn't enforce it.
  **Fix**: `($content -match '(?s)Step 5.*mode:verify') | Should Be $true`

- **[P2.7]** [cg-documentation] `docs/reference.md:51` — "checks only whether prior fixes landed" is inaccurate.
  **Why**: `mode:verify` runs a fresh `light` review with a suppression policy. P0/P1 and cross-file breakage are unconditionally reported. The phrase implies it's a diff against the old finding list.
  **Fix**: Replace with: "re-runs a `light` review with suppression of expected fix-consequence P2/P3 findings; P0/P1 and new cross-file breakage are always reported."

- **[P2.8]** [cg-documentation] `docs/reference.md:51` — Mutual exclusion of `mode:autofix` and `mode:verify` undocumented in reference.
  **Why**: The "can be combined" example implies broad combinability. Users may try `/cg-review mode:verify mode:autofix`.
  **Fix**: Add: `Note: \`mode:autofix\` and \`mode:verify\` are mutually exclusive — if both are passed, \`mode:verify\` wins.`

- **[P2.9]** [cg-documentation] `docs/workflow.md` Output section — Missing verify-review filename pattern.
  **Why**: The Output line shows only `<plan-stem>-review.md`. Verify-mode users won't know to look for `-verify-review.md`.
  **Fix**: Extend to: "`.cg-docs/reviews/<plan-stem>-review.md`; for `mode:verify` passes: `<plan-stem>-verify-review.md`."

- **[P2.10]** [cg-version-control] `.cg-docs/brainstorms/` and `.cg-docs/plans/` — Two new files are untracked and will be omitted from the commit.
  **Why**: Per project conventions, `.cg-docs/` files are institutional knowledge and must be committed.
  **Fix**: `git add .cg-docs/brainstorms/2026-04-23-review-convergence-verify-mode.md .cg-docs/plans/2026-04-23-review-convergence-verify-mode.md`

- **[P2.11]** [cg-data-quality] `.github/prompts/cg-review.prompt.md` Step 1.7.1 — Sort behavior undefined for legacy files without `date:` frontmatter.
  **Why**: Pre-v0.4.3 review files may lack `date:`. Behavior is unspecified — an agent could sort such files first, last, or error.
  **Fix**: Add: `If \`date:\` is absent, treat the file as oldest (sort last). If sorting is impossible, skip the file.`

- **[P2.12]** [cg-data-quality] `.github/prompts/cg-review.prompt.md` Step 1.7.1 — Implicit skip for files with no `findings:` map is undocumented.
  **Why**: The condition "where `findings:` contains at least one `fixed` entry" implicitly skips files with no `findings:` key, but doesn't state this. An agent encountering a file without `findings:` might proceed with it, yielding an empty suppression context.
  **Fix**: Add: `If \`findings:\` is absent or not a map, treat as no \`fixed\` entries — skip the file.`

- **[P2.13]** [cg-data-quality] `.github/prompts/cg-review.prompt.md` Step 1.7.1 — Inclusion filter too broad; non-standard `.md` files in `.cg-docs/reviews/` could be selected.
  **Why**: Only `-verify-review.md` files are excluded. Any other `.md` (notes, stubs) could be selected as the prior review context.
  **Fix**: Change inclusion to: `files ending in \`-review.md\` AND NOT ending in \`-verify-review.md\``.

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test for fallback warning when no prior review with fixed findings is found.
  **Fix**: `It "warns when no prior review with fixed findings found" { ($content -match '[Nn]o prior review with fixed findings found') | Should Be $true }`

- **[P3.2]** [cg-testing] `tests/prompt-tools.Tests.ps1` — Mutual exclusion test doesn't verify which mode wins.
  **Fix**: `It "mutual exclusion resolves in favour of mode:verify" { ($content -match 'using.*mode:verify|ignore.*mode:autofix') | Should Be $true }`

- **[P3.3]** [cg-testing] `tests/prompt-tools.Tests.ps1` — `"documents mode:verify argument"` trivially passes from any occurrence.
  **Fix**: Tighten to `($content -match 'mode:verify.*Enable verification|Enable verification.*mode:verify')` or drop since the unrecognized-argument test provides stronger coverage.

- **[P3.4]** [cg-documentation] `docs/workflow.md` "When to use" section — Doesn't point to `mode:verify` as the post-fix-triage tool.
  **Fix**: Add bullet: `After applying fix-triage results — use \`/cg-review mode:verify\` to check convergence (suppresses expected fix-consequence P2/P3).`

- **[P3.5]** [cg-documentation] `.github/prompts/cg-review.prompt.md` Step 5 — Option 1 is circular when the current session is a clean verify pass (no findings → suggests verify again).
  **Fix**: Add conditional: `If \`mode:verify\` was active and no findings were reported, move "Ready to merge" to position 1.`

- **[P3.6]** [cg-version-control] Commit atomicity — all 8 files (6 modified + 2 untracked) should land in a single commit.
  **Fix**: Stage all 8 together: `feat(review): add mode:verify to /cg-review for convergent fix cycles`

- **[P3.7]** [cg-architecture] `.github/prompts/cg-review.prompt.md:70,115` — Light depth enforced in two locations (DRY violation).
  **Why**: Step 1.7 item 4 and Step 2 verify dispatch block both state `light` depth. Two sources of truth.
  **Fix**: Remove redundant depth statement from Step 2 dispatch block; add back-reference: "(depth is `light` per Step 1.7)."

- **[P3.8]** [cg-architecture + cg-data-quality] `.github/prompts/cg-review.prompt.md` Step 1.7.2 — `plan:` field extracted but has no consumer (dead instruction).
  **Why**: The verify-review frontmatter schema has `parent-review:` but no `plan:` field.
  **Fix**: Either (a) remove `The \`plan:\` field and` from Step 1.7.2, or (b) add `plan: <parent-review's plan, or null>` to the verify frontmatter schema.

- **[P3.9]** [cg-reproducibility] `.github/prompts/cg-review.prompt.md` Step 1.7.1 — "then alphabetical" tie-breaking direction unspecified.
  **Fix**: Change to "alphabetically last (lexicographically greater filename wins)" — matching Step 3.5's phrasing.

- **[P3.10]** [cg-reproducibility] `.github/prompts/cg-review.prompt.md` Step 1.7.2 — "the review filename" is ambiguous (bare name vs. full relative path).
  **Fix**: Change to "the full relative path to the review file (e.g., `.cg-docs/reviews/2026-04-21-foo-review.md`)"

- **[P3.11]** [cg-code-quality] `docs/reference.md` — `depth + mode:verify` combination behavior undocumented (e.g., `/cg-review thorough mode:verify` silently runs at `light`).
  **Fix**: Add: `When \`mode:verify\` is active, any depth argument is ignored — verify always runs at \`light\`.`

- **[P3.12]** [cg-data-quality] `.github/prompts/cg-review.prompt.md` Step 3.5 — `parent-review:` path written without existence check.
  **Fix**: Add: `Before writing, confirm the \`parent-review:\` target exists. If not, warn: "parent-review: target not found — link may be stale."`

---

### ✅ Passed
- **cg-performance**: No concerns — `mode:verify` is a net cost reduction (2 agents vs 8+, Step 1.5 disabled)
- All files: No secrets, credentials, API keys, or PII found

### ⚠️ Incomplete Reviews
- `@cg-adversarial` did not produce usable output. Consider re-running `/cg-review` with a higher model tier, or invoke `@cg-adversarial` directly.
