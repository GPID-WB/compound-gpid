---
plan: ".cg-docs/plans/2026-04-06-review-finding-status-tracking.md"
findings:
  P1.1: fixed
  P1.2: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
---

## Review Report

**Review depth**: thorough
**Files reviewed**: 7 (5 modified + 2 untracked new files)
**Branch**: vision1
**Date**: 2026-04-06

**Changed files:**
- `.github/prompts/cg-review.prompt.md` — Step 3.5: YAML frontmatter with `findings:` map added to review output
- `.github/prompts/cg-fix-triage.prompt.md` — Step 1 updated to read frontmatter; Step 3/4 updated to write status back; `--migrate` mode added
- `.github/prompts/cg-resume.prompt.md` — Step 2e updated to count only `open` findings; legacy-file nudge added
- `tests/prompt-tools.Tests.ps1` — Pester contract tests added for all three prompt changes
- `roadmap.json` — Feature `review-finding-status-tracking` status set to `done`
- `.cg-docs/brainstorms/2026-04-06-review-finding-status-tracking.md` (untracked)
- `.cg-docs/plans/2026-04-06-review-finding-status-tracking.md` (untracked)

**Findings**: 2 P1, 6 P2, 4 P3

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-documentation] `.github/prompts/cg-fix-triage.prompt.md` — Step 3, item 4: Missing "Do NOT delegate this step to a subagent" guard.
  **Why**: Per past learning `.cg-docs/solutions/testing-patterns/2026-03-30-do-not-delegate-file-write-guardrail.md`, absent delegation guards cause silent file loss: the agent calls a subagent to perform the write, the subagent writes within its own context, and when the subagent returns the change vanishes. In this case the user would see "P1.1 marked fixed" in chat, but the YAML frontmatter would remain `open`, so `/cg-resume` would continue showing the finding as pending — incorrect results.
  **Fix**: Append to item 4: `**Do NOT delegate this frontmatter update to a subagent. Edit the file directly.**`

- **[P1.2]** [cg-documentation] `.github/prompts/cg-fix-triage.prompt.md` — `--migrate` section, step 2c ("Add YAML frontmatter to the file"): Missing "Do NOT delegate this step to a subagent" guard.
  **Why**: Same root cause as P1.1 — if the agent delegates the frontmatter write to a subagent during migration, the file remains unchanged, the migration appears to succeed, and `/cg-resume` continues showing the legacy-migration nudge indefinitely.
  **Fix**: Add to step 2c: `**Write the updated file directly. Do NOT delegate this step to a subagent.**`

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-architecture] `docs/reference.md` line 50 — `/cg-fix-triage --migrate` is absent from user-facing reference.
  **Why**: The `--migrate` mode triggers completely different batch-migration behavior (not interactive fixing). It is the only recovery path for users nudged by `/cg-resume`'s "Run `/cg-fix-triage --migrate`" message, but a user consulting the reference finds only "Apply review findings by ID or priority level" — the flag is undiscoverable without reading the full prompt source.
  **Fix**: Update the `/cg-fix-triage` row in `docs/reference.md`:
  ```markdown
  | `/cg-fix-triage [IDs\|PRIORITY\|--migrate]` | Claude Sonnet 4.6 | Apply review findings by ID or priority. Use `--migrate` to backfill per-finding status tracking on legacy review files. |
  ```

- **[P2.2]** [cg-code-quality] `.github/prompts/cg-fix-triage.prompt.md` line 93 — Placeholder letter `A` inconsistent with template convention.
  **Why**: The Fix-Triage Summary template uses lettered placeholders `N (in scope)`, `X (fixed)`, `Y (skipped)`, `Z (out of scope)`. The newly added `**Previously resolved**: A findings` uses `A`, which breaks the sequential convention and could confuse an AI reading the template.
  **Fix**: Change `A` to a letter that fits the sequence or use a semantic placeholder:
  ```markdown
  **Previously resolved**: R findings (from prior sessions)
  ```
  (or any consistent letter — just not `A` which clashes with "all").

- **[P2.3]** [cg-documentation] `.github/prompts/cg-resume.prompt.md` output template line — Trailing "open" is grammatically ambiguous.
  **Why**: `<open-P1-count> critical, <open-P2-count> important, <open-P3-count> minor open` reads as "minor open", implying "open" only modifies the last term. Rendered: "2 critical, 1 important, 3 minor open".
  **Fix**: Move the qualifier so it applies to all three terms or remove it (the section header already conveys "pending"):
  ```markdown
  1. `<filename>` — <open-P1-count> critical, <open-P2-count> important, <open-P3-count> minor open findings
  ```

- **[P2.4]** [cg-code-quality] `tests/prompt-tools.Tests.ps1` companion-plan heuristic test — Unescaped `.` wildcard in regex.
  **Why**: The pattern `'companion.plan|companion plan'` uses `.` as a wildcard, matching any character (e.g., "companionXplan"). The intent is to match either "companion-plan" or "companion plan". The `.` should be escaped or replaced with a character class.
  **Fix**:
  ```powershell
  ($content -match 'companion[- ]plan|companion plan') | Should Be $true
  ```

- **[P2.5]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test verifies that the finding-ID parsing pattern is documented in `cg-review.prompt.md`.
  **Why**: The tests verify that `findings:` appears, but not that the critical parsing patterns `` `**[P1.` ``, `` `**[P2.` ``, `` `**[P3.` `` are present. If those patterns were accidentally removed from the step instructions, the tests would still pass and the frontmatter generation step would be silently broken.
  **Fix**: Add to the `cg-review.prompt.md` Describe block:
  ```powershell
  It "documents the finding ID parsing patterns in Step 3.5" {
      ($content -match [regex]::Escape('**[P1.')) -and
      ($content -match [regex]::Escape('**[P2.')) -and
      ($content -match [regex]::Escape('**[P3.')) | Should Be $true
  }
  ```

- **[P2.6]** [cg-testing] `tests/prompt-tools.Tests.ps1` — `plan:` key test is a false-positive risk.
  **Why**: `($content -match 'plan:')` matches anywhere in the file, including prose like "Look for the active plan: ...". The test is intended to verify the `plan:` key appears in the YAML frontmatter template block, not in prose.
  **Fix**: Require proximity to `findings:` in the same frontmatter block:
  ```powershell
  It "includes plan: and findings: together in the YAML frontmatter template" {
      ($content -match '(?s)plan:.*findings:|(?s)findings:.*plan:') | Should Be $true
  }
  ```

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-architecture] `tests/prompt-tools.Tests.ps1` — Two `Describe` blocks for `cg-resume.prompt.md`: pre-existing `"cg-resume.prompt.md - pending review findings scan"` (one test) and new `"cg-resume.prompt.md - findings frontmatter and migration nudge"`. The old block's single test is now a subset of the new block's scope, causing minor fragmentation.
  **Fix**: Merge the single test from the old block into the new block and delete the old block.

- **[P3.2]** [cg-testing] `tests/prompt-tools.Tests.ps1` migration nudge test — Second regex alternation `migrate.*review` redundant.
  **Why**: `'Review migration needed|migrate.*review'` already covers the intent with the first alternation (`'Review migration needed'` is the exact phrase from the prompt). The second alternation `migrate.*review` is over-permissive and could match unrelated text.
  **Fix**: Use only the exact phrase: `($content -match 'Review migration needed') | Should Be $true`

- **[P3.3]** [cg-code-quality] `tests/prompt-tools.Tests.ps1` (new Describe blocks) — Inconsistent naming convention for `It` blocks. Some reference step numbers ("in Step 3.5", "in Step 2e"), others use inference verbs without step context ("references", "instructs", "describes"). Causes friction when running targeted tests by name.
  **Fix**: Adopt consistent pattern: `It "<verb> <what> [in <Step X>]"`, where step reference is included when the behavior is step-specific.

- **[P3.4]** [cg-code-quality] `tests/prompt-tools.Tests.ps1` line 246 — Multi-condition assertion using three chained `-and` operators is hard to read and produces an uninformative failure message.
  **Why**: `($content -match '\bopen\b') -and ($content -match '\bfixed\b') -and ($content -match '\bskipped\b')` gives no indication of which status value is missing on failure.
  **Fix**: Split into three separate `It` blocks:
  ```powershell
  It "mentions status: open" { ($content -match '\bopen\b') | Should Be $true }
  It "mentions status: fixed" { ($content -match '\bfixed\b') | Should Be $true }
  It "mentions status: skipped" { ($content -match '\bskipped\b') | Should Be $true }
  ```

---

### ✅ Passed

- **cg-architecture**: Overall inter-prompt schema contract is minimal, flat, and consistently consumed across all three prompts. The plan file `status: completed`. The `--migrate` --flag placement in `cg-fix-triage` is an acknowledged tradeoff (SRP tension low). No unrelated architecture regressions.
- **cg-code-quality**: Existing Pester test patterns are consistent with new tests; prompt instruction style clear. Frontmatter schema template is clean and well-formed.
- **cg-version-control**: No sensitive data, secrets, or gitignore violations in any changed file. Untracked `.cg-docs/` files should be staged before commit per project convention (informational). Suggested commit: `feat(review): add per-finding status tracking with YAML frontmatter`.
- **cg-reproducibility**: Migration defaults are deterministic (companion-plan `status: completed` → `fixed`, else `open`). Null `plan:` is handled explicitly. Status values are a closed enum (`open/fixed/skipped`).
- **cg-performance**: Not applicable (prompt/markdown files; no computational hotpaths).
- **cg-data-quality**: YAML frontmatter schema is minimal and unambiguous; `open/fixed/skipped` enum is explicitly documented; `plan: null` fallback is correctly specified.
- **cg-learnings-researcher**: Implementation correctly applies the `do-not-delegate` pattern from `.cg-docs/solutions/testing-patterns/2026-03-30-do-not-delegate-file-write-guardrail.md` in `cg-review.prompt.md` Step 3.5 (the file-creation step already has the guard). The `cg-fix-triage` frontmatter-update step is the gap (see P1.1, P1.2). The `tools:` frontmatter omission concern from the learnings doc is not applicable here — the project convention is to omit `tools:` entirely from orchestrating prompts (verified in `tests/prompt-tools.Tests.ps1` lines 7–15).
