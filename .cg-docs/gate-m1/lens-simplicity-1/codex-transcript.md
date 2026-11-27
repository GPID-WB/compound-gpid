### review stage

> Read ~/.agents/skills/cg/worker.md before anything else.

You are the verifier `simplicity`. You check one principle, P6 Smallest change, simplest design, at the review stage, and nothing else. Read these files in full, in this order: what every verifier does; your principle, whose section "Verifier" says what to inspect at this stage, what to flag, how to prove a flag and what to leave alone; and your lens, when a third file is listed. Write each finding down as rule 4 of the first file says.

1. ~/.agents/skills/cg/verifier.md
2. ~/.agents/skills/cg/principles/P06-smallest-change.md
3. ~/.agents/skills/cg/lenses/simplicity.md

The project root: <project>
Under review: every file that differs from commit 55a6ba978088c5e1c2e721c8d6a64006d6fb4e71 (`git diff 55a6ba978088c5e1c2e721c8d6a64006d6fb4e71`), each file that no commit holds (`git status --short`), and the work report .cg-docs/work-reports/2026-11-27-poverty-brief.md
The contract: the plan .cg-docs/plans/2026-11-27-poverty-brief.md, which the human approved as the record .cg-docs/approvals/2026-11-27-poverty-brief.d57a059aa4ef8100.1.json holds it
What code recorded: .cg-docs/evidence/2026-11-27-poverty-brief/ and .cg-docs/approvals/
A run that code records: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run "<the command>" --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Every check of the plan, rerun by code: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --rerun --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Only the verifier `verification` runs the line above, once. Any other verifier leaves it, and reads the record of that rerun, `"kind": "rerun"`, when there is one.

Return one verdict block, as `verifier.md` gives it, and nothing else.

principle: P6  
verdict: FLAG  
findings:
  - pipeline.py:31: `share_text` has no caller or declared use (P2; fix: remove the function).

note: The plan explicitly calls for the layout change, scaling option, and poverty-line check, so those were left alone. The one-caller functions name distinct operations and were left alone.

[exit code: 0]

### plan stage

> Read ~/.agents/skills/cg/worker.md before anything else.

You are the verifier `simplicity`. You check one principle, P6 Smallest change, simplest design, at the plan stage, and nothing else. Read these files in full, in this order: what every verifier does; your principle, whose section "Verifier" says what to inspect at this stage, what to flag, how to prove a flag and what to leave alone; and your lens, when a third file is listed. Write each finding down as rule 4 of the first file says.

1. ~/.agents/skills/cg/verifier.md
2. ~/.agents/skills/cg/principles/P06-smallest-change.md
3. ~/.agents/skills/cg/lenses/simplicity.md

The project root: <project>
Under review: .cg-docs/plans/2026-11-27-poverty-brief.md
The contract: in the plan itself; the human decided the intent it is built on, .cg-docs/brainstorms/2026-11-27-poverty-brief.md
What code recorded: none
A run that code records: none at this stage, so point at a file and a line
Every check of the plan, rerun by code: none at this stage
Only the verifier `verification` runs the line above, once. Any other verifier leaves it, and reads the record of that rerun, `"kind": "rerun"`, when there is one.

Return one verdict block, as `verifier.md` gives it, and nothing else.

principle: P6
verdict: FLAG
findings:
  - .cg-docs/plans/2026-11-27-poverty-brief.md:56: The scaling option serves a future use that neither requirement asks for. (P2; fix: remove S2.)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:57: The negative poverty-line check guards against a value fixed as positive by the contract. (P3; fix: remove S3.)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:58: Relaying out the existing headcount check is unrelated to the requested table. (P2; fix: remove S4.)
note: Left the table in the existing script because the human chose that design.

[exit code: 0]
