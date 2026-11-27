### review stage

> Read ~/.agents/skills/cg/worker.md before anything else.

You are the verifier `verification`. You check one principle, P4 Prove it works, at the review stage, and nothing else. Read these files in full, in this order: what every verifier does; your principle, whose section "Verifier" says what to inspect at this stage, what to flag, how to prove a flag and what to leave alone; and your lens, when a third file is listed. Write each finding down as rule 4 of the first file says.

1. ~/.agents/skills/cg/verifier.md
2. ~/.agents/skills/cg/principles/P04-prove-it-works.md
3. ~/.agents/skills/cg/lenses/verification.md

The project root: <project>
Under review: every file that differs from commit 4b825dc642cb6eb9a060e54bf8d69288fbee4904 (`git diff 4b825dc642cb6eb9a060e54bf8d69288fbee4904`), each file that no commit holds (`git status --short`), and the work report .cg-docs/work-reports/2026-11-27-poverty-brief.md
The contract: the plan .cg-docs/plans/2026-11-27-poverty-brief.md, which the human approved as the record .cg-docs/approvals/2026-11-27-poverty-brief.87b710e319b25014.1.json holds it
What code recorded: .cg-docs/evidence/2026-11-27-poverty-brief/ and .cg-docs/approvals/
A run that code records: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run "<the command>" --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Every check of the plan, rerun by code: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --rerun --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"

Return one verdict block, as `verifier.md` gives it, and nothing else.

principle: P4
verdict: FLAG
findings:
  - .cg-docs/evidence/2026-11-27-poverty-brief/0008-20261127T112508Z-rerun.json:90-93: C2 checks only that the table file exists, not that the real output is correct (P1; fix: add a check of the real output against an independent expected value at the plan’s stated tolerance)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0008-20261127T112508Z-rerun.json:95-98: C3 pipes the check through `sort`, so its exit code does not reliably show whether the check passed (P1; fix: use a command whose exit code is the check’s own)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0008-20261127T112508Z-rerun.json:63-75: C4 fails on the current files, despite an earlier verified run (P1; fix: correct the code at the first place where it goes wrong, then rerun the check through `evidence`)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0008-20261127T112508Z-rerun.json:78-86: C5 has no recorded work run, but the work report claims it passes (P1; fix: record a run of the check through `evidence`, or remove the claim)
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:46: The report claims that the headcount ratio matches a published figure, but no record shows that comparison (P1; fix: record the comparison through `evidence`, or remove the claim)
  - .cg-docs/verification.md:32: The outputs map names no proof for the bootstrap interval (P1; fix: add an independent reference value, a cross-check in a second software, or the human’s prior expectation to the outputs map and a plan check)
note: C1 and C2 were rerun successfully but only on earlier file states; C3 was rerun successfully on the current files. No other P4 findings established.

> code · gpt-6-luna

→ Read ~/.agents/skills/cg/worker.md
→ Read ~/.agents/skills/cg/principles/P04-prove-it-works.md
→ Read ~/.agents/skills/cg/verifier.md
→ Read ~/.agents/skills/cg/lenses/verification.md
⚙ stata-mcp_stata_run_selection {"selection":"!"}

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --rerun --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
C1: exit 0; the work's run: exit 0, verified, on an earlier state of its files
C2: exit 0; the work's run: exit 0, verified, on an earlier state of its files
C3: exit 0; the work's run: exit 0, verified, on the files as they now are
C4: exit 1; the work's run: exit 0, verified, on an earlier state of its files
C5: exit 0; the work has no run of it
FLAG proxy: .cg-docs/plans/2026-11-27-poverty-brief.md:36; fix: a check on the value of the real output, against an expected value from a source independent of the code, at the tolerance the plan sets
FLAG cannot-fail: .cg-docs/plans/2026-11-27-poverty-brief.md:37; fix: a command whose exit code is the check's own: nothing after it that sets the exit code, such as || true, ; echo or a pipe; devtools::test(stop_on_failure = TRUE) and rcmdcheck::rcmdcheck(error_on = "warning") in R; no --exit-zero and no python -O
FLAG fails: .cg-docs/plans/2026-11-27-poverty-brief.md:38; fix: the fix in the code, at the first place where things go wrong, and the check run through evidence again; never a change to the check
FLAG not-run: .cg-docs/plans/2026-11-27-poverty-brief.md:39; fix: the check run through evidence on the files as they now are, before the work is called done
FLAG unrecorded: .cg-docs/work-reports/2026-11-27-poverty-brief.md:45; fix: the run of that check through evidence, or the claim taken out of the work report
FLAG no-validation: .cg-docs/verification.md:32; fix: a reference value, a cross-check in a second software, or the expectation the human stated before the run, named in the outputs map and held by a check of the plan
verdict: not verified
record: .cg-docs/evidence/2026-11-27-poverty-brief/0008-20261127T112508Z-rerun.json

→ Read .cg-docs/verification.md
→ Read .cg-docs/plans/2026-11-27-poverty-brief.md
→ Read .cg-docs/work-reports/2026-11-27-poverty-brief.md

$ git status --short && git diff --name-only 4b825dc642cb6eb9a060e54bf8d69288fbee4904 && git diff --stat 4b825dc642cb6eb9a060e54bf8d69288fbee4904
?? .cg-docs/
?? README.md
?? __pycache__/
?? checks/
?? data/
?? output/
?? pipeline.py

→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0008-20261127T112508Z-rerun.json


[exit code: 0]
