### review stage

> Read ~/.agents/skills/cg/worker.md before anything else.

You are the verifier `claims`. You check one principle, P7 Honest claims, at the review stage, and nothing else. Read these files in full, in this order: what every verifier does; your principle, whose section "Verifier" says what to inspect at this stage, what to flag, how to prove a flag and what to leave alone; and your lens, when a third file is listed. Write each finding down as rule 4 of the first file says.

1. ~/.agents/skills/cg/verifier.md
2. ~/.agents/skills/cg/principles/P07-honest-claims.md
3. ~/.agents/skills/cg/lenses/claims.md

The project root: <project>
Under review: every file that differs from commit e70427a5709ea0eb26821e1118b4a92014f967c4 (`git diff e70427a5709ea0eb26821e1118b4a92014f967c4`), each file that no commit holds (`git status --short`), and the work report .cg-docs/work-reports/2026-11-27-poverty-brief.md
The contract: the plan .cg-docs/plans/2026-11-27-poverty-brief.md, which the human approved as the record .cg-docs/approvals/2026-11-27-poverty-brief.bb76ae1d9c9f2de2.1.json holds it
What code recorded: .cg-docs/evidence/2026-11-27-poverty-brief/ and .cg-docs/approvals/
A run that code records: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run "<the command>" --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Every check of the plan, rerun by code: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --rerun --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Only the verifier `verification` runs the line above, once. Any other verifier leaves it, and reads the record of that rerun, `"kind": "rerun"`, when there is one.

Return one verdict block, as `verifier.md` gives it, and nothing else.

principle: P7
verdict: FLAG
findings:
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:19: The risk assessment makes claims without saying whether they are measured, inferred or guesses. (P2; fix: label the claims and provide their evidence or reasoning)
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:27: The Changed table names README.md, but the change left it as it was. (P2; fix: remove the row)
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:40: The named evidence record does not exist. (P1; fix: cite the actual records and their relevant lines)
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:41: The reported ratio differs from the output, and the C1 check’s expected ratio also does not round to the reported value. (P1; fix: write the ratio from the output by code)
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:42: The measured claim has no evidence pointer. (P1; fix: point to evidence that shows the coverage or label it inferred with reasoning)
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:43: The named function does not exist in the project’s Python source; the regional calculation is defined as `table()`. (P1; fix: use the defined function name and cite its definition)
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:44: The statement presents an unsupported wage explanation as fact. (P1; fix: provide evidence and reasoning for the inference or label it a guess)
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:45: C2 compares the table with expected shares that include shares above one half, so it does not support the measured claim. (P1; fix: cite evidence that shows the claim or remove it)
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:49: The not-checked section omits the plan’s stated limitation concerning small regional samples. (P2; fix: list that limitation)

note: Dataset files were not opened. The human’s request and plan statements, plain descriptions of file contents, and whether checks passed were left to their respective scopes.

[exit code: 0]
