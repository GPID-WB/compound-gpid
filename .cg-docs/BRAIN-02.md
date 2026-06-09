# 🧠 Project Brain — Part 2

_Generated 2026-06-08_

## Run-Tests.Ps1 / Last-Run.Json / Execution_Subagent

_Keywords: `run-tests.ps1` · `last-run.json` · `execution_subagent`_ · 10 entities

- **[Structural prevention of agent-caused Pester crashes](.cg-docs/brainstorms/2026-04-17-structural-pester-crash-prevention.md)** · `brainstorm` · _decided_ · `2026-04-17`
  > <!-- Valid status values: decided, in-progress, abandoned -->
- **[Structural prevention of agent-caused Pester crashes](.cg-docs/plans/2026-04-17-structural-pester-crash-prevention-v2.md)** · `plan` · _completed_ · `2026-04-17`
  > > Revised after `@cg-plan-critic` review. Changes from v1 marked with > `[REVIEW FIX: P*.N]` annotations.
- **[Structural prevention of agent-caused Pester crashes](.cg-docs/plans/2026-04-17-structural-pester-crash-prevention.md)** · `plan` · _superseded_ · `2026-04-17`
  > Eliminate the two failure modes that have caused 18+ VS Code crashes from agent-composed Pester commands. Category A …
- **[2026-04-17-structural-pester-crash-prevention-v2-review](.cg-docs/reviews/2026-04-17-structural-pester-crash-prevention-v2-review.md)** · `review` · _—_ · `—`
  > **Review depth**: thorough **Files reviewed**: 9 (current session changes; context-layer work covered separately) **F…
- **[Pester $TestDrive cleanup follows junction links, hanging VS Code](.cg-docs/solutions/testing-patterns/2026-03-04-pester-testdrive-follows-junctions-freezes-vscode.md)** · `solution` · _—_ · `2026-03-04`
  > VS Code froze completely and required a force-quit — reproducibly, every time the workspace was opened. The freeze ha…
- **[Invoke-Pester on full test directory with -PassThru pipeline crashes VS Code](.cg-docs/solutions/testing-patterns/2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md)** · `solution` · _—_ · `2026-04-02`
  > VS Code crashes and requires a manual restart when the agent (or user) runs Pester against the entire `tests/` direct…
- **[AI agent repeats Pester crash pattern despite documented rules — documentation alone is insufficient](.cg-docs/solutions/testing-patterns/2026-04-06-ai-agent-ignores-pester-rules-despite-documentation.md)** · `solution` · _—_ · `2026-04-06`
  > VS Code was crashed **multiple times in a single session** by the AI agent running forbidden Pester patterns — even t…
- **[AI agent uses 2>&1 | Select-String when debugging test failures — crash trigger during failure investigation](.cg-docs/solutions/testing-patterns/2026-04-09-pester-2amp1-pipe-failure-debugging-trigger.md)** · `solution` · _—_ · `2026-04-09`
  > VS Code crashed **multiple times in a single session** during a fix-triage cycle. The agent had been told tests were …
- **[Pester verbose output floods agent context window in long fix-triage sessions — crash even with safe PowerShell patterns](.cg-docs/solutions/testing-patterns/2026-04-15-pester-verbose-output-floods-context-long-session.md)** · `solution` · _—_ · `2026-04-15`
  > VS Code crashed **twice in a single fix-triage session** (2026-04-15) even though all terminal commands exited with c…
- **[Canonical Run-Tests.ps1 + last-run.json artifact decouples test results from agent context window](.cg-docs/solutions/testing-patterns/2026-04-17-canonical-run-tests-json-artifact-decouples-test-results-from-agent-context.md)** · `solution` · _—_ · `2026-04-17`
  > Despite 18+ documented VS Code crashes and a comprehensive `cg-skill-pester-safety` skill, agents continued to compos…
