---
plan: .cg-docs/plans/2026-05-05-branch-creation-from-plan.md
date: 2026-05-05
depth: thorough
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P2.9: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: skipped
  P3.6: fixed
---

## Review Report

**Review depth**: thorough
**Files reviewed**: 4 (`.github/prompts/cg-plan.prompt.md`, `tests/prompt-tools.Tests.ps1`, `roadmap.json`, `.cg-docs/plans/2026-05-05-branch-creation-from-plan.md`)
**Findings**: 20 (P0: 0, P1: 5, P2: 9, P3: 6)

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-adversarial] `cg-plan.prompt.md` line ~53 — Offer hardcodes `feat/` but type derivation runs after the offer text
  **Why**: The offer template shows `` `feat/<short-description-from-request>` `` before the derivation rule (`feat/` vs `fix/` vs `refactor/`) is stated. A model executing linearly shows the user `feat/my-fix` then creates `fix/my-fix` — the user approved a branch name they never saw.
  **Fix**: Move the derivation rule to immediately before the offer block. Change the offer template to `` `<type>/<short-description>` `` with a note that type is derived first.

- **[P1.2]** [cg-adversarial] `cg-plan.prompt.md` line ~63 — Uncommitted-changes warning fires *after* user accepts branching
  **Why**: Instruction order: (1) check branch, (2) offer, (3) create if accepted, (4) warn about uncommitted changes. The user says "Yes" to branching, then gets a stash-or-proceed dialog — a post-hoc second confirmation after the first Yes/No. If the user expected a single interaction, this breaks the flow.
  **Fix**: Move the uncommitted-changes check to immediately after `git branch --show-current`, before the offer is shown, so the offer message can incorporate the warning when applicable.

- **[P1.3]** [cg-adversarial] `cg-plan.prompt.md` line ~60 — No error handling when `git checkout -b` fails (branch already exists)
  **Why**: If the branch already exists (e.g., user ran `/cg-plan` twice for the same feature), `git checkout -b` exits with error 128. The success confirmation "Switched to new branch…" would be emitted incorrectly, masking the failure.
  **Fix**: Add: "If `git checkout -b` fails because the branch already exists, offer: 'Branch `<name>` already exists — switch to it? (yes/no).' For other errors, report the git error verbatim and skip branching."

- **[P1.4]** [cg-adversarial] `cg-plan.prompt.md` — Branch created before plan is validated — no cleanup path
  **Why**: Step 0.7 runs before Step 1 (context) and Step 1.5 (scope). If the user discovers the task is out of scope or already done, an orphaned branch is left on `main` with no instruction to clean it up. High-frequency for exploratory `/cg-plan` use.
  **Fix**: Add at the end of Step 0.7: "If the planning session ends without producing a plan (abandoned at Step 0.5 or 1.5), suggest: `git branch -d <branch-name>` to remove the unused branch."

- **[P1.5]** [cg-adversarial] `cg-plan.prompt.md` — Branch type taxonomy is incomplete for ~50% of use cases
  **Why**: Only `feat/`, `fix/`, `refactor/` are specified. `/cg-plan` is also invoked for `docs/`, `test/`, `chore/`, `data/`, `analysis/` work — all valid conventional-commit types in this project. Underdetermined rule → model defaults to `feat/` for everything else.
  **Fix**: Extend the type table to match commit types in `cg-skill-git-workflow`: `feat/`, `fix/`, `refactor/`, `test/`, `docs/`, `chore/`, `data/`, `analysis/`.

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` line ~3489 — `$step07Idx` unguarded before use as comparand in ordering assertion
  **Why**: Convention requires asserting both IndexOf values `BeGreaterThan -1` before comparing them. If Step 0.7 is ever deleted, the test fails with a misleading "misordering" error instead of "step not found."
  **Fix**: Add `$step07Idx | Should BeGreaterThan -1` before `$step07Idx | Should BeGreaterThan $step05Idx`.

- **[P2.2]** [cg-testing] `tests/prompt-tools.Tests.ps1` line ~3496 — `$step1Idx` unguarded before use as comparand
  **Why**: Same pattern violation. Add `$step1Idx | Should BeGreaterThan -1` before the comparison assertion.
  **Fix**: Add guard line immediately after `$step1Idx = $content.IndexOf('### Step 1:')`.

- **[P2.3]** [cg-reproducibility] `cg-plan.prompt.md` line ~43 — `main`/`master` hardcoded — breaks for `develop`, `trunk`, custom defaults
  **Why**: Repos using `develop`, `trunk`, or any non-standard default branch will have Step 0.7 triggered on the default integration branch and silently skip on real feature branches — the reverse of the intended behavior.
  **Fix**: Replace hardcoded enumeration with: `git symbolic-ref refs/remotes/origin/HEAD --short 2>$null` (yields e.g. `origin/develop` → strip prefix → `develop`). Fall back to `main`/`master` only if unresolvable.

- **[P2.4]** [cg-reproducibility / cg-adversarial] `cg-plan.prompt.md` line ~43 — No guard for non-git workspace
  **Why**: `git branch --show-current` errors (exit 128) or returns empty in a non-git directory. No fallback specified; model behavior is undefined.
  **Fix**: Add: "If the command fails or returns empty output in a non-git context, skip this step silently."

- **[P2.5]** [cg-adversarial] `cg-plan.prompt.md` — No branch name sanitization rule
  **Why**: Git branch names forbid spaces, `~`, `^`, `:`, `?`, `*`, `[`, `\`, `..`, `@{`, and names ending in `.lock`. Feature descriptions from this analytical team routinely include %, :, and () — all invalid. No normalization instruction exists.
  **Fix**: Add: "Normalize the branch name: replace spaces with `-`, remove `~^:?*[\`, collapse `..` to `-`, strip `@{`, truncate to 60 characters. If empty after normalization, ask the user for a branch name."

- **[P2.6]** [cg-adversarial] `cg-plan.prompt.md` — `Refine` path in Step 0.5 triggers branch offer for already-planned work
  **Why**: If user chooses "Refine" in Step 0.5, Step 0.7 still runs unconditionally. The derived branch name likely already exists → hits P1.3 (no error handler). Compound failure: Refine mode + existing branch + no recovery.
  **Fix**: Add: "If Step 0.5 concluded with a 'Refine' decision, skip the branch offer silently — the branch for this plan likely already exists."

- **[P2.7]** [cg-data-quality] `cg-plan.prompt.md` — Branch name derivation listed after the offer template that already uses a derived name
  **Why**: Same as P1.1 but also a data-quality issue: the instruction ordering causes the offer to display before the derivation logic is applied.
  **Fix**: Addressed by P1.1 fix.

- **[P2.8]** [cg-data-quality] `cg-plan.prompt.md` — Uncommitted-changes check after user acceptance
  **Why**: Same as P1.2 but confirmed from a data-quality angle: the two-dialog pattern is a UX defect with predictable confusion.
  **Fix**: Addressed by P1.2 fix.

- **[P2.9]** [cg-documentation] `docs/reference.md` — `/cg-plan` entry does not mention the new branch-offer step
  **Why**: `/cg-brainstorm` row in `reference.md` explicitly advertises "Branch offer at Step 1.7". `/cg-plan` row says nothing about Step 0.7. Users consulting reference.md before choosing a prompt will not see this feature advertised for `/cg-plan`.
  **Fix**: Append to the `/cg-plan` description: "`**Branch offer at Step 0.7**` — before gathering context, offers to create a git branch derived from your request."

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `cg-plan.prompt.md` line ~51 — Placeholder `feat/<short-description-from-request>` diverges from Step 1.7's `feat/<short-description-from-your-request>`
  **Why**: "your" is dropped. Breaks the mirror relationship. Minor clarity loss.
  **Fix**: Change to `feat/<short-description-from-your-request>` to match cg-brainstorm Step 1.7.

- **[P3.2]** [cg-code-quality] `cg-plan.prompt.md` line ~55 — "If accepted:"/"If declined:" vs "If the user accepts:"/"If the user declines:"
  **Why**: Style divergence from the reference pattern in cg-brainstorm Step 1.7.
  **Fix**: Use "If the user accepts:" / "If the user declines:" to match.

- **[P3.3]** [cg-code-quality] `tests/prompt-tools.Tests.ps1` — Test description `"File Permissions allows branch creation"` conflates permission and step-citation checks
  **Why**: The regex checks both the permission and its Step 0.7 citation. Failure message is ambiguous.
  **Fix**: Rename to `"File Permissions references branch creation at Step 0.7"`.

- **[P3.4]** [cg-code-quality] `tests/prompt-tools.Tests.ps1` — Variable alignment style inconsistency vs parallel brainstorm block
  **Why**: Brainstorm block uses double-space padding (`$step15Idx  =`); new plan block uses single-space (`$step05Idx =`).
  **Fix**: Pad new block variables to match: `$step05Idx  =`, `$step07Idx  =`.

- **[P3.5]** [cg-documentation] `.cg-docs/plans/2026-05-05-branch-creation-from-plan.md` — Two Documentation Checklist items unchecked on a completed plan
  **Why**: `- [ ] No README update needed` and `- [ ] No function docs needed` on a `status: completed` plan signal outstanding work.
  **Fix**: Change both to `[x]` to record the affirmative decision.

- **[P3.6]** [cg-testing] `tests/prompt-tools.Tests.ps1` — Missing tests for branch name convention and `git checkout -b` command
  **Why**: The type-taxonomy rule (`feat/`, `fix/`, `refactor/`) and the exact creation command (`git checkout -b`) are behavioral specs not covered by any test.
  **Fix**: Add two `It` blocks — one matching `feat/.*fix/.*refactor/` and one matching `git checkout -b`.

---

### ✅ Passed

- **cg-architecture**: Step ordering (0.5 → 0.7 → 1) is correct; dual-offer design (brainstorm + plan) is architecturally sound; brainstorm→plan flow correctly skips via the non-main guard.
- **cg-version-control**: Branch naming, commit messages, and commit contents are all clean and compliant.
- **cg-learnings-researcher**: No past solutions contradict the implementation; known PS5.1 git stderr issue (#3) is noted as pre-existing.
- **roadmap.json**: Schema valid, status fields consistent.
