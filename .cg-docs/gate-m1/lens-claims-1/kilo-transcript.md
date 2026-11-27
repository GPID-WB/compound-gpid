### review stage

> Read ~/.agents/skills/cg/worker.md before anything else.

You are the verifier `claims`. You check one principle, P7 Honest claims, at the review stage, and nothing else. Read these files in full, in this order: what every verifier does; your principle, whose section "Verifier" says what to inspect at this stage, what to flag, how to prove a flag and what to leave alone; and your lens, when a third file is listed. Write each finding down as rule 4 of the first file says.

1. ~/.agents/skills/cg/verifier.md
2. ~/.agents/skills/cg/principles/P07-honest-claims.md
3. ~/.agents/skills/cg/lenses/claims.md

The project root: <project>
Under review: every file that differs from commit 8212bc4b21eb38cefe54b3ba05da4fbeb438bd7f (`git diff 8212bc4b21eb38cefe54b3ba05da4fbeb438bd7f`), each file that no commit holds (`git status --short`), and the work report .cg-docs/work-reports/2026-11-27-poverty-brief.md
The contract: the plan .cg-docs/plans/2026-11-27-poverty-brief.md, which the human approved as the record .cg-docs/approvals/2026-11-27-poverty-brief.bb76ae1d9c9f2de2.1.json holds it
What code recorded: .cg-docs/evidence/2026-11-27-poverty-brief/ and .cg-docs/approvals/
A run that code records: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run "<the command>" --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Every check of the plan, rerun by code: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --rerun --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Only the verifier `verification` runs the line above, once. Any other verifier leaves it, and reads the record of that rerun, `"kind": "rerun"`, when there is one.

Return one verdict block, as `verifier.md` gives it, and nothing else.

principle: P7
verdict: FLAG
findings:
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:27: The Changed table lists README.md, but the worktree shows no change to that file (P2; fix: remove the README.md row).
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:40: The cited evidence record does not exist at the named path; the C2 record is stored under a different filename (P1; fix: cite the existing record and its line, or remove the claim).
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:42: The measured claim that every region has a row has no evidence pointer (P1; fix: add a pointer that shows this, or label the claim inferred with its reasoning or guess).
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:43: `regional_shares()` is not defined in the project code, and the line gives no package documentation citation for it (P1; fix: use the defined function name with a documentation citation, or remove the claim).
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:44: The causal claim that higher wage earnings explain lower poverty in the East is stated as fact without a label or pointer that shows the cause (P1; fix: label it inferred and give valid reasoning, or label it guess).
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:45: The measured claim about regional headcount ratios points only to C2, not to a record or other evidence that shows the claim (P1; fix: add a pointer to evidence that shows it, or label the claim inferred with its reasoning or guess).
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:49: The “Not checked” section says “Nothing” but does not identify what the checks do not cover (P2; fix: list what was not checked, including what the plan says no check would catch).
note: I set aside the unmatched number at line 41 because checking it requires opening output data, which the verifier rules prohibit. I left the claim that checks passed for P4, the plan's statements for the human, and plain statements of file contents alone.

> code · gpt-6-luna

→ Read ~/.agents/skills/cg/worker.md
→ Read ~/.agents/skills/cg/verifier.md
→ Read ~/.agents/skills/cg/principles/P07-honest-claims.md
→ Read ~/.agents/skills/cg/lenses/claims.md

$ git status --short && git diff --name-only 8212bc4b21eb38cefe54b3ba05da4fbeb438bd7f
M pipeline.py
?? .cg-docs/
?? checks/table.py
?? output/
pipeline.py

✱ Glob ".cg-docs/evidence/2026-11-27-poverty-brief/**/*" in . · 0 matches
✱ Glob ".cg-docs/evidence/2026-11-27-poverty-brief/**" in . · 0 matches
→ Read .cg-docs/work-reports/2026-11-27-poverty-brief.md
✱ Glob ".cg-docs/evidence/2026-11-27-poverty-brief/*.json" in . · 0 matches
→ Read .cg-docs
→ Read .cg-docs/evidence/2026-11-27-poverty-brief
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0004-20261127T134020Z-claims.json
→ Read README.md
→ Read pipeline.py
→ Read checks/table.py
✱ Glob "**/*" in . · 18 matches


[exit code: 0]
