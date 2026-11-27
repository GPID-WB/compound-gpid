### review stage

> Read ~/.agents/skills/cg/worker.md before anything else.

You are the verifier `simplicity`. You check one principle, P6 Smallest change, simplest design, at the review stage, and nothing else. Read these files in full, in this order: what every verifier does; your principle, whose section "Verifier" says what to inspect at this stage, what to flag, how to prove a flag and what to leave alone; and your lens, when a third file is listed. Write each finding down as rule 4 of the first file says.

1. ~/.agents/skills/cg/verifier.md
2. ~/.agents/skills/cg/principles/P06-smallest-change.md
3. ~/.agents/skills/cg/lenses/simplicity.md

The project root: <project>
Under review: every file that differs from commit fb55a9c2d958dc035cbbecf2c0536e364e15b18a (`git diff fb55a9c2d958dc035cbbecf2c0536e364e15b18a`), each file that no commit holds (`git status --short`), and the work report .cg-docs/work-reports/2026-11-27-poverty-brief.md
The contract: the plan .cg-docs/plans/2026-11-27-poverty-brief.md, which the human approved as the record .cg-docs/approvals/2026-11-27-poverty-brief.7e093512474ab9ac.1.json holds it
What code recorded: .cg-docs/evidence/2026-11-27-poverty-brief/ and .cg-docs/approvals/
A run that code records: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run "<the command>" --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Every check of the plan, rerun by code: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --rerun --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Only the verifier `verification` runs the line above, once. Any other verifier leaves it, and reads the record of that rerun, `"kind": "rerun"`, when there is one.

Return one verdict block, as `verifier.md` gives it, and nothing else.

principle: P6  
verdict: FLAG  
findings:
  - checks/headcount.py:5-9: The changes only reformat a check whose layout the plan did not ask to change. (P2; fix: restore the file to its base-commit version)
  - pipeline.py:24: The `scale` argument is unused and no requirement asks for it. (P2; fix: remove the argument)
  - pipeline.py:26-27: The check tests a fixed poverty line that the code itself sets to a positive value. (P3; fix: remove the check)
  - pipeline.py:31-32: `share_text` has no caller and is not an entry point. (P2; fix: remove the function)

note: The one-caller findings for `members` and `by_region` were set aside because their names describe their respective operations. The plan requires the regional table and its output file.

[exit code: 0]

### plan stage

> Read ~/.agents/skills/cg/worker.md before anything else.

You are the verifier `simplicity`. You check one principle, P6 Smallest change, simplest design, at the plan stage, and nothing else. Read these files in full, in this order: what every verifier does; your principle, whose section "Verifier" says what to inspect at this stage, what to flag, how to prove a flag and what to leave alone; and your lens, when a third file is listed. Write each finding down as rule 4 of the first file says.

1. ~/.agents/skills/cg/verifier.md
2. ~/.agents/skills/cg/principles/P06-smallest-change.md
3. ~/.agents/skills/cg/lenses/simplicity.md

The project root: <project>
Under review: .cg-docs/plans/2026-11-26-poverty-brief.md
The contract: in the plan itself; the human decided the intent it is built on, .cg-docs/brainstorms/2026-11-27-poverty-brief.md
What code recorded: none
A run that code records: none at this stage, so point at a file and a line
Every check of the plan, rerun by code: none at this stage
Only the verifier `verification` runs the line above, once. Any other verifier leaves it, and reads the record of that rerun, `"kind": "rerun"`, when there is one.

Return one verdict block, as `verifier.md` gives it, and nothing else.

principle: P6
verdict: FLAG
findings:
  - .cg-docs/plans/2026-11-26-poverty-brief.md:55: The scaling option serves a future use that neither requirement asks for. (P2; fix: remove slice S2.)
  - .cg-docs/plans/2026-11-26-poverty-brief.md:56: The negative-line check guards against a state the contract fixes by setting the poverty line to 3.0. (P3; fix: remove slice S3.)
  - .cg-docs/plans/2026-11-26-poverty-brief.md:57: Reformatting the existing headcount check does not serve the goal or requirements. (P2; fix: remove slice S4.)
note: Left the regional table and its check alone because the contract requires them.

[exit code: 0]
