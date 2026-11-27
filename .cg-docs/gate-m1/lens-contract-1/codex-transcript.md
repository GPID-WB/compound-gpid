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
  - pipeline.py:5: The poverty line is 3.65, while the approved contract specifies 3.0 at .cg-docs/plans/2026-11-27-poverty-brief.md:27. (P1; fix: use the approved line or obtain an approved amendment.)
  - pipeline.py:35: The table omits regions with fewer than three households, contrary to the requirement for every region at .cg-docs/plans/2026-11-27-poverty-brief.md:28. (P1; fix: include every region or obtain an approved amendment.)
  - pipeline.py:30: The output includes a poverty gap measure, while .cg-docs/plans/2026-11-27-poverty-brief.md:21 puts other poverty measures out of scope. (P1; fix: remove the measure or obtain an approved amendment.)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:58: The required output/notes.md was not built, as recorded in .cg-docs/evidence/2026-11-27-poverty-brief/0006-20261127T133656Z-claims.json. (P1; fix: build the notes or obtain an approved amendment removing them.)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:35: C1 can pass when the weighted headcount required at line 27 is incorrect because it only requires an output row. (P1; fix: amend C1 to fail when the weighted headcount is incorrect.)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:36: C2 checks worked-example shares rather than whether the table contains every survey region as required at line 28. (P1; fix: amend C2 to compare the table's regions with the survey's regions.)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:37: C3 can pass without checking the six-decimal precision required at line 29. (P1; fix: amend C3 to check each share's precision.)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:37: C3's stated failure condition depends on a reader's opinion. (P2; fix: specify an observable failure condition in an approved amendment.)
note: Left method choices and wording preferences alone; no rerun record was present, and this verifier was instructed not to run it.

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
  - .cg-docs/plans/2026-11-27-poverty-brief.md:39: The plan does not state the wrong result described in intent line 24 or provide a check that fails when households are omitted without disclosure. (P1; fix: state that wrong result and add a check for household coverage and disclosure)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:35: C1 can pass when the weighted headcount required by intent line 16 is wrong because it checks only whether an output row exists. (P1; fix: check the weighted headcount against an independently worked example)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:36: C2 can pass when a survey region is missing, contrary to intent line 37, because it checks shares against a worked example without checking region coverage. (P1; fix: check that every survey region has a table row)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:37: C3 makes the six-decimal requirement for the regional table in intent line 16 depend on a reader’s opinion. (P2; fix: specify an observable check that each regional share has six decimal places)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:58: S2 delivers a note on each region, although no requirement asks for those notes and intent line 16 asks for a regional table. (P1; fix: remove the notes from the slice or add a requirement through an approved amendment)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:57-58: The slices deliver CSV files and notes but no brief for the country team requested by intent line 16. (P1; fix: add the brief as a deliverable with a corresponding requirement and check)
note: Left wording preferences, the choice of method, and items explicitly out of scope alone.

[exit code: 0]
