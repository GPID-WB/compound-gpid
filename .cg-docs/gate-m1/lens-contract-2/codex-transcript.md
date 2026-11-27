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

principle: P1
verdict: FLAG
findings:
  - .cg-docs/plans/2026-11-27-poverty-brief.md:21: The plan has no statement of what a wrong result looks like, although the decided intent states one at .cg-docs/brainstorms/2026-11-27-poverty-brief.md:24. (P1; fix: add the wrong-result statement in an approved amendment)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:35: C1 passes whenever the output has a row, even if the weighted share required at line 27 is wrong. (P1; fix: approve an amended check that fails when the weighted share is incorrect)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:36: C2 checks shares against a fixed example and can pass while a survey region required by line 28 is missing. (P1; fix: approve an amended check that compares the table’s regions with the survey’s regions)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:37: C3’s failure condition, “looks wrong to a reader,” is a matter of opinion. (P2; fix: approve an amended check with an observable failure condition)
  - checks/layout.py:6: The check only tests the header and can pass when the six-decimal formatting required by .cg-docs/plans/2026-11-27-poverty-brief.md:29 is broken. (P1; fix: approve an amended check that fails when a share does not have six decimals)
  - pipeline.py:5: The poverty line is 3.65 instead of the 3.0 required by .cg-docs/plans/2026-11-27-poverty-brief.md:27. (P1; fix: use the contracted line or obtain approval for an amendment)
  - pipeline.py:35: The table omits regions with fewer than three households, contrary to .cg-docs/plans/2026-11-27-poverty-brief.md:28. (P1; fix: include every region or obtain approval for an amendment)
  - pipeline.py:30: The output includes a poverty gap measure that .cg-docs/plans/2026-11-27-poverty-brief.md:21 places out of scope. (P1; fix: remove the measure or obtain approval for an amendment)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:58: The required output/notes.md was not built, as recorded by .cg-docs/evidence/2026-11-27-poverty-brief/0006-20261127T143114Z-claims.json. (P1; fix: build the notes file or obtain approval for an amendment removing it)
note: Check execution results and files outside the slices were left to their respective verifiers; survey and output data were not opened.

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
  - .cg-docs/plans/2026-11-27-poverty-brief.md:23: The plan has no statement of the wrong result described in intent line 24. (P1; fix: state what a wrong result looks like in the plan)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:35: C1 can pass with an incorrect weighted share or households omitted, contrary to R1 and intent lines 16 and 24. (P1; fix: add a check that fails when the weighted share is incorrect or households are omitted)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:36: C2 can pass with a region missing because it checks shares against a worked example rather than checking region coverage required by intent lines 16 and 37. (P1; fix: add a check that fails when any survey region has no table row)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:37: C3 makes failure a matter of a reader’s opinion and does not check the six-decimal requirement derived from intent line 16. (P2; fix: specify an observable failure condition for six-decimal formatting)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:58: S2 delivers a note on each region that no requirement asks for and that intent lines 16–20 do not name. (P1; fix: remove the notes from the slice or add a requirement through a human-approved amendment)
note: Left wording preferences, method choices, and the measures and surveys explicitly deferred by intent line 20 alone.

[exit code: 0]
