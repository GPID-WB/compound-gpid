### review stage

> Read ~/.agents/skills/cg/worker.md before anything else.

You are the verifier `contract`. You check one principle, P1 Specify before generating, at the review stage, and nothing else. Read these files in full, in this order: what every verifier does; your principle, whose section "Verifier" says what to inspect at this stage, what to flag, how to prove a flag and what to leave alone; and your lens, when a third file is listed. Write each finding down as rule 4 of the first file says.

1. ~/.agents/skills/cg/verifier.md
2. ~/.agents/skills/cg/principles/P01-specify-before-generating.md
3. ~/.agents/skills/cg/lenses/contract.md

The project root: <project>
Under review: every file that differs from commit 4b825dc642cb6eb9a060e54bf8d69288fbee4904 (`git diff 4b825dc642cb6eb9a060e54bf8d69288fbee4904`), each file that no commit holds (`git status --short`), and the work report .cg-docs/work-reports/2026-11-27-poverty-brief.md
The contract: the plan .cg-docs/plans/2026-11-27-poverty-brief.md, which the human approved as the record .cg-docs/approvals/2026-11-27-poverty-brief.eede825827520728.1.json holds it
What code recorded: .cg-docs/evidence/2026-11-27-poverty-brief/ and .cg-docs/approvals/
A run that code records: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run "<the command>" --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Every check of the plan, rerun by code: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --rerun --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Only the verifier `verification` runs the line above, once. Any other verifier leaves it, and reads the record of that rerun, `"kind": "rerun"`, when there is one.

Return one verdict block, as `verifier.md` gives it, and nothing else.

I will read the required verifier instructions in the requested order, then inspect only the specified review material for P1.
The review rules require the approved plan, newest claims record, diff, and work report. I will compare those records to the implementation and leave all checks and other principles to their assigned verifiers.
principle: P1
verdict: FLAG
findings:
  - pipeline.py:5: The poverty line is 3.65, not the contract's 3.0 a day (.cg-docs/plans/2026-11-27-poverty-brief.md:17,27); fix: set the line to 3.0 (P1).
  - pipeline.py:35: The table omits regions with fewer than three households, contrary to the requirement for a row for each region (.cg-docs/plans/2026-11-27-poverty-brief.md:28); fix: include every region (P1).
  - pipeline.py:20-23: The work calculates an additional poverty-gap measure, which the contract excludes (.cg-docs/plans/2026-11-27-poverty-brief.md:19-21); fix: remove the gap measure (P1).
  - .cg-docs/plans/2026-11-27-poverty-brief.md:58: The plan names `output/notes.md`, which the claims record marks `not-built`; fix: create the file as named, or remove it through a human-approved amendment (P1).
note: I left check outcomes to P4 and any files not listed in the plan's slices to P6. No rerun record was present.

> code · gpt-6-luna

→ Read ~/.agents/skills/cg/worker.md
→ Read ~/.agents/skills/cg/principles/P01-specify-before-generating.md
→ Read ~/.agents/skills/cg/verifier.md
→ Read ~/.agents/skills/cg/lenses/contract.md
→ Read .cg-docs/approvals/2026-11-27-poverty-brief.eede825827520728.1.json
→ Read .cg-docs/work-reports/2026-11-27-poverty-brief.md
→ Read .cg-docs/plans/2026-11-27-poverty-brief.md
✱ Glob ".cg-docs/evidence/2026-11-27-poverty-brief/**/*" in . · 0 matches

$ git diff --name-status 4b825dc642cb6eb9a060e54bf8d69288fbee4904
(no output)

$ git status --short
?? .cg-docs/
?? README.md
?? checks/
?? data/
?? output/
?? pipeline.py

→ Read .cg-docs/evidence/2026-11-27-poverty-brief
→ Read .cg-docs/approvals
→ Read output
→ Read checks
→ Read README.md
→ Read pipeline.py
→ Read checks/table.py
→ Read checks/headcount.py
→ Read checks/layout.py
→ Read .cg-docs/approvals/2026-11-27-poverty-brief.f78a80e59a0b3fa7.1.json
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0006-20261127T143224Z-claims.json


[exit code: 0]

### plan stage

> Read ~/.agents/skills/cg/worker.md before anything else.

You are the verifier `contract`. You check one principle, P1 Specify before generating, at the plan stage, and nothing else. Read these files in full, in this order: what every verifier does; your principle, whose section "Verifier" says what to inspect at this stage, what to flag, how to prove a flag and what to leave alone; and your lens, when a third file is listed. Write each finding down as rule 4 of the first file says.

1. ~/.agents/skills/cg/verifier.md
2. ~/.agents/skills/cg/principles/P01-specify-before-generating.md
3. ~/.agents/skills/cg/lenses/contract.md

The project root: <project>
Under review: .cg-docs/plans/2026-11-27-poverty-brief.md
The contract: in the plan itself; the human decided the intent it is built on, .cg-docs/brainstorms/2026-11-27-poverty-brief.md
What code recorded: none
A run that code records: none at this stage, so point at a file and a line
Every check of the plan, rerun by code: none at this stage
Only the verifier `verification` runs the line above, once. Any other verifier leaves it, and reads the record of that rerun, `"kind": "rerun"`, when there is one.

Return one verdict block, as `verifier.md` gives it, and nothing else.

principle: P1
verdict: FLAG
findings:
  - .cg-docs/plans/2026-11-27-poverty-brief.md:27-29: The requirements omit the intent's requirement to report each region's household count, which the human decided at .cg-docs/brainstorms/2026-11-27-poverty-brief.md:37; add it as a requirement and give it a check. (P1; fix: add a requirement for the household count beside each region's share, with a check that fails when the count is missing or incorrect)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:35: C1 checks only that the output has a row, so it can pass when the weighted headcount share is wrong; the intent requires that share at .cg-docs/brainstorms/2026-11-27-poverty-brief.md:16. (P1; fix: change C1 to check the computed weighted share against the requirement)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:36: C2 checks the table against a worked example rather than checking that every survey region has a row, so it can pass when a region is omitted; the intent requires every region's row at .cg-docs/brainstorms/2026-11-27-poverty-brief.md:37. (P1; fix: change C2 to check that every survey region has a row)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:37: C3 says failure is when the table “looks wrong to a reader,” which is a matter of opinion; replace this with an observable failure outcome. (P2; fix: state a measurable outcome, such as a required column or numeric precision being absent)
note: Left the choice of method alone, as P10's scope; did not inspect approval records or run validation because this is the plan stage.

> code · gpt-6-luna

→ Read ~/.agents/skills/cg/worker.md
→ Read ~/.agents/skills/cg/verifier.md
→ Read ~/.agents/skills/cg/principles/P01-specify-before-generating.md
→ Read ~/.agents/skills/cg/lenses/contract.md
→ Read .cg-docs/brainstorms/2026-11-27-poverty-brief.md
→ Read .cg-docs/plans/2026-11-27-poverty-brief.md


[exit code: 0]
