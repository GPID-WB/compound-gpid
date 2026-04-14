---
plan: .cg-docs/plans/2026-04-10-fix-problems-agent-and-prompt.md
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
  P2.6: skipped
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
---

## Review Report

**Review depth**: thorough  
**Files reviewed**: 2 substantive (`.github/prompts/cg-work.prompt.md`, `tests/prompt-tools.Tests.ps1`) + 6 protected artifacts  
**Findings**: 4 P1 · 6 P2 · 6 P3

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-adversarial] `.github/prompts/cg-work.prompt.md`:Step 3.7 — Missing "already done" guard; fires misleading warning on re-runs  
  **Why**: Step 1.5 explicitly skips the dispatch if the feature is already `done` "to avoid regression." Step 3.7 has no equivalent guard. Re-running `/cg-work` on a completed plan causes Step 3.7 to dispatch `@cg-roadmap` for a `done → done` no-op write; the no-change write triggers the verification warning "Roadmap update may not have been applied" — a false alarm.  
  **Fix**: Add: "If the feature's current status is already `done`, skip this step silently."

- **[P1.2]** [cg-adversarial] `roadmap.json` + `.github/prompts/cg-work.prompt.md`:Step 3.7.2 — Multiple features sharing the same plan path; only the first match gets updated  
  **Why**: `cg-fix-problems-agent` and `cg-fix-problems-prompt` both reference `.cg-docs/plans/2026-04-10-fix-problems-agent-and-prompt.md`. Step 3.7 says "Find the feature entry whose `plan` path matches" (singular). An LLM following this wording finds the first match only; the second feature silently stays `active`.  
  **Fix**: Change Step 3.7.2 to "Find **all** feature entries whose `plan` path matches" and loop the dispatch for each match.

- **[P1.3]** [cg-adversarial / cg-data-quality] `.github/prompts/cg-work.prompt.md`:Step 3.7.2 — No path normalization instruction; absolute-vs-relative mismatch silently skips the entire step  
  **Why**: On Windows, the plan file path held by the agent may be absolute or use backslashes. `roadmap.json` stores bare relative forward-slash paths. A literal string comparison fails and falls through to "skip silently" — the roadmap-drift bug survives the fix in that scenario.  
  **Fix**: Add: "Normalize both paths to forward slashes, workspace-relative (strip any absolute prefix or leading `./`), before comparing."

- **[P1.4]** [cg-version-control] git log — HEAD commit is non-conventional with typos and mixed concerns  
  **Why**: HEAD commit is `Fix compund historiy` — two typos (`compund`, `historiy`), no `type(scope):` prefix, and bundles four unrelated concerns: charter history archival, strategy doc, `compound-gpid.md` update, and `roadmap.json` status corrections.  
  **Fix**: Amend or rebase before merging. Suggested split:
  ```
  docs(charter): archive history and update current focus
  feat(roadmap): mark cg-fix-problems items as done
  ```

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality / cg-testing / cg-data-quality / cg-adversarial] `tests/prompt-tools.Tests.ps1`:~1482 — `IndexOf("status done")` first-occurrence fragility  
  **Why**: Any future prose earlier in the file containing "status done" (guard clause, example, comment) shifts `$donePos` before the actual dispatch line, giving a false-pass even if Step 3.7's dispatch sentence were moved after the wait.  
  **Fix**: Use the unique full dispatch phrase: `$content.IndexOf("to status done.")`.

- **[P2.2]** [cg-testing] `tests/prompt-tools.Tests.ps1` — Step 3.7 structural placement (between 3.5 and 4) is untested  
  **Why**: The test only confirms lexical ordering. Embedding the dispatch in Step 4 prose before the wait would pass the test while reintroducing the structural regression.  
  **Fix**: Add a second `It` block:
  ```powershell
  It "Step 3.7 appears between Step 3.5 and Step 4 in the file" {
      $step35Pos = $content.IndexOf("### Step 3.5:")
      $step37Pos = $content.IndexOf("### Step 3.7:")
      $step4Pos  = $content.IndexOf("### Step 4:")
      $step35Pos | Should BeGreaterThan -1
      $step37Pos | Should BeGreaterThan -1
      $step4Pos  | Should BeGreaterThan -1
      $step37Pos | Should BeGreaterThan $step35Pos
      $step37Pos | Should BeLessThan $step4Pos
  }
  ```

- **[P2.3]** [cg-adversarial] `.github/prompts/cg-work.prompt.md`:Step 3.7 — No prerequisite gate; fires for incomplete implementations  
  **Why**: Nothing prevents Step 3.7 from running if Step 2 was skipped or tests were bypassed. The roadmap feature gets marked `done` for genuinely incomplete work and `/cg-resume` never surfaces it again.  
  **Fix**: Add a prerequisite sentence: "Only proceed if all Step 2 sub-steps and the Step 3 quality checklist were completed and all tests are passing."

- **[P2.4]** [cg-data-quality] `.github/prompts/cg-work.prompt.md`:Step 3.7.4 — "Skip silently" conflates intentional absence with path-format mismatch  
  **Why**: Two very different failure modes both produce no-match: (a) plan was never linked (intentional), (b) a path-format failure (unintentional). Both are invisible, making format failures undiagnosable.  
  **Fix**: Add: "If `roadmap.json` contains features with non-null `plan` fields but none matched, surface a soft warning: 'No matching feature found in roadmap.json. Verify the plan path is linked with `@cg-roadmap`.'"

- **[P2.5]** [cg-architecture] `.github/prompts/cg-work.prompt.md`:Step 1 inline plan skip note — Omits Step 3.7  
  **Why**: `"Skip Step 1.5 (roadmap linking)"` is behaviorally correct (Step 3.7 self-defends via "if not found: skip silently"), but incomplete. The omission misleads future authors extending the inline-plan path.  
  **Fix**: Change to `"Skip Step 1.5 and Step 3.7 (no roadmap entry exists for inline plans)."`

- **[P2.6]** [cg-version-control] branch `bug/cg-work_roadmap` — Wrong prefix and non-standard separator  
  **Why**: Convention is `type/short-description` with hyphen separators and conventional-commit type names. `bug/` is not a conventional type; `_` is not the separator convention.  
  **Fix**: Informational — should have been `fix/cg-work-roadmap`. Already pushed; no action needed for this branch.

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `tests/prompt-tools.Tests.ps1`:~1471 — Missing opening `# ---` separator before new block  
  **Fix**: Add `# ---------------------------------------------------------------------------` immediately before the comment block.

- **[P3.2]** [cg-architecture] `.github/prompts/cg-work.prompt.md`:Step 3.7 — Redundant closing "If roadmap.json does not exist, skip" guard  
  **Why**: Repeats the opening guard in opposite polarity. Implies the conditions are subtly different when they are not.  
  **Fix**: Remove the final paragraph; the opening guard is sufficient.

- **[P3.3]** [cg-reproducibility] `.github/prompts/cg-work.prompt.md`:Step 3.7.5 — "After dispatch" missing "after @cg-roadmap returns"  
  **Fix**: Change to "After `@cg-roadmap` returns, verify..." to make sequencing dependency explicit.

- **[P3.4]** [cg-performance] `.github/prompts/cg-work.prompt.md`:Step 3.7.1 — Redundant `roadmap.json` re-read  
  **Why**: The file was already read at Step 1.5.  
  **Fix**: "Using the plan path resolved in Step 1.5, find all matching features" — no fresh read needed.

- **[P3.5]** [cg-reproducibility] `tests/prompt-tools.Tests.ps1` — Three assertions in one `It` block (presence + ordering)  
  **Fix**: Split into three `It` blocks for clearer failure messages. Low urgency.

- **[P3.6]** [cg-data-quality] `.github/prompts/cg-work.prompt.md`:Step 3.7 — No explicit "skip null plan entries" instruction  
  **Fix**: Add: "Skip features where `plan` is null."

---

### ✅ Passed

- **cg-documentation**: No issues on `cg-work.prompt.md` body or test comment block
- **cg-performance**: No P0/P1/P2 issues found
- **cg-learnings-researcher**: All related past patterns confirmed documented; path normalization identified as a new open gap not covered by any prior solution
