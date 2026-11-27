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
Only the verifier `verification` runs the line above, once. Any other verifier leaves it, and reads the record of that rerun, `"kind": "rerun"`, when there is one.

Return one verdict block, as `verifier.md` gives it, and nothing else.

principle: P4
verdict: FLAG
findings:
  - .cg-docs/evidence/2026-11-27-poverty-brief/0008-20261127T143450Z-rerun.json:63-75: C4 fails on the current files, so the table does not meet the check for including each survey region (P1; fix: fix the code at the first place where the region is omitted, then rerun C4 through `evidence`).
  - checks/headcount.py:8-11: C1 derives its expected value from the same `headcount()` code that produces the output, so it can repeat that code's misunderstanding instead of checking the weighted share independently (P1; fix: check the real output against an independent reference value).
  - .cg-docs/plans/2026-11-27-poverty-brief.md:36: C2 checks only that the table file exists, not that it contains the required result (P1; fix: check the real output against an independent expected result).
  - .cg-docs/plans/2026-11-27-poverty-brief.md:37: C3 pipes the check through `sort`, so the command's exit code can hide a failing interval check (P1; fix: use a command whose exit code is the check's own).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0008-20261127T143450Z-rerun.json:78-86: C5 has no recorded work run (P1; fix: run C5 through `evidence` on the current files before calling the work done).
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:45: The report claims C5 passes, but the rerun record shows no work run for C5 (P1; fix: record C5's run through `evidence`, or remove the claim).
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:46: The report claims the headcount matches a published figure, but no record backs that comparison (P1; fix: record an independent comparison through a plan check, or remove the claim).
  - .cg-docs/verification.md:32: The outputs map gives the bootstrap interval no proof of correctness, leaving that reported result without independent validation (P1; fix: add a reference value, a cross-check in a second software, or the human's prior expectation to the outputs map and a plan check).
note: The verification profile doctor is listed as not found, so the checks cannot be trusted under P4. The plan states that no check catches a share computed on the wrong households; left this gap alone because the contract does not specify a check for it.

> code · gpt-6-luna

→ Read ~/.agents/skills/cg/worker.md
→ Read ~/.agents/skills/cg/verifier.md
→ Read ~/.agents/skills/cg/principles/P04-prove-it-works.md
→ Read ~/.agents/skills/cg/lenses/verification.md

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
FLAG unbacked: .cg-docs/work-reports/2026-11-27-poverty-brief.md:46; fix: the check of the plan that compares it, run through evidence, or the record of its run named in the line; or the claim taken out of the work report
FLAG no-validation: .cg-docs/verification.md:32; fix: a reference value, a cross-check in a second software, or the expectation the human stated before the run, named in the outputs map and held by a check of the plan
verdict: not verified
record: .cg-docs/evidence/2026-11-27-poverty-brief/0008-20261127T143450Z-rerun.json

→ Read .cg-docs/verification.md
→ Read .cg-docs/work-reports/2026-11-27-poverty-brief.md
→ Read .cg-docs/plans/2026-11-27-poverty-brief.md
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0008-20261127T143450Z-rerun.json

$ git diff --name-status 4b825dc642cb6eb9a060e54bf8d69288fbee4904 && git status --short
?? .cg-docs/
?? README.md
?? __pycache__/
?? checks/
?? data/
?? output/
?? pipeline.py

→ Read pipeline.py
→ Read README.md
→ Read .cg-docs/approvals/2026-11-27-poverty-brief.87b710e319b25014.1.json
✱ Glob ".cg-docs/evidence/2026-11-27-poverty-brief/*.json" in . · 0 matches
✱ Glob "checks/*.py" in . · 4 matches
→ Read .cg-docs/evidence/2026-11-27-poverty-brief
→ Read checks/bounds.py
→ Read checks/regions.py
→ Read checks/interval.py
→ Read checks/headcount.py


[exit code: 0]
