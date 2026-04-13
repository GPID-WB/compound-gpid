---
plan: .cg-docs/plans/2026-04-10-fix-problems-agent-and-prompt.md
findings:
  P2.1: fixed
  P3.1: fixed
  P3.2: fixed
---

## Review Report

**Review depth**: light (argument override; config is thorough)
**Files reviewed**: 12 (7 modified + 5 new untracked)
**Findings**: 0 P0 · 0 P1 · 1 P2 · 2 P3 = 3 total
**Date**: 2026-04-13
**Context**: Follow-up light review after applying all 35 findings from the thorough review
(`2026-04-10-fix-problems-agent-and-prompt-review.md`). Tests: 819 passed, 0 failed.

---

### P0 — BLOCKING
_(none)_

### P1 — CRITICAL
_(none)_

### P2 — IMPORTANT

- **[P2.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test covers the large-report
  batching notice added to `cg-fix-triage.prompt.md`
  **Why**: The large-report notice is the sole fix for the P0 response-length crash bug
  (the root cause of the entire `/cg-fix-triage` investigation). It has zero test coverage,
  so it could silently regress on any future edit to `cg-fix-triage.prompt.md` without
  failing tests.
  **Fix**: Add to the `"cg-fix-triage.prompt.md - per-finding status tracking"` Describe block
  (or a new Describe block):
  ```powershell
  It "warns the user when there are more than 15 open findings (large report guard)" {
      ($content -match '15 open|more than 15') | Should Be $true
  }
  It "recommends priority batches (P0 P1, P2, P3) in the large report warning" {
      ($content -match 'P0 P1.*P2.*P3|priority batch') | Should Be $true
  }
  ```

### P3 — MINOR

- **[P3.1]** [cg-code-quality] `.github/agents/cg-fix-problems.agent.md:4` — `terminalLastCommand`
  in `tools:` is not referenced in the documented protocol
  **Why**: The protocol documents `get_errors`, `read`, `search`, and `editFiles` explicitly.
  `terminalLastCommand` is never mentioned — its presence is unclear and adds to the tool
  surface without stated purpose.
  **Fix**: Either remove it from `tools:` or add a note near the Pester skill-load step:
  "Use `terminalLastCommand` to inspect the last VS Code terminal output if needed to
  diagnose test-runner errors."

- **[P3.2]** [cg-documentation] `.github/prompts/cg-fix-triage.prompt.md` — `[yes/batch]`
  response handler: "if batch → stop" is implicit
  **Why**: The wait instruction says "Wait for the user's response before continuing." but
  does not say what to do when the user responds `batch`. A rule-following model may
  continue if it doesn't interpret `batch` as a stop signal.
  **Fix**: Add one sentence after the wait:
  "If the user responds `batch`: display the three recommended commands
  (``/cg-fix-triage P0 P1``, ``/cg-fix-triage P2``, ``/cg-fix-triage P3``) and stop —
  do not proceed with triage."

### ✅ Passed

- `@cg-code-quality`: No style, naming, DRY, or linting issues. New prompt and agent files
  follow project conventions (frontmatter, step numbering, guard language, report formats).
  `docs/model-guide.md` and `docs/reference.md` counts updated correctly.
- `@cg-testing`: All 819 tests pass. New `prompt-tools.Tests.ps1` blocks (P1.33–P1.35)
  cover existence, frontmatter, no-tool-restriction, auto mode protocol, and dispatch
  behavior for the new files. Test patterns consistent with existing suite style.
