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
  - .cg-docs/plans/2026-11-27-poverty-brief.md:36: C2 checks only that the table exists, so it does not verify its values. (P1; fix: check the real table against independently established expected values)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:37: The pipe to `sort` masks a failure of the interval check. (P1; fix: run the check with its own exit code)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0008-20261127T112413Z-rerun.json:63: C4 fails on the current files after passing on an earlier state. (P1; fix: correct the first cause of the missing region and rerun C4 through evidence)
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:45: The work claims C5 passed without a recorded work run. (P1; fix: record the check through evidence or remove the claim)
  - checks/headcount.py:8: C1 derives its expected value using the same function as the output, so it cannot detect an error shared by that function. (P1; fix: compare the final output with an independent reference value)
  - .cg-docs/verification.md:31: The regional shares have no independent validation. (P1; fix: add a reference value, cross-check or prior human expectation to the outputs map and a plan check)
  - .cg-docs/verification.md:32: The bootstrap interval has no independent validation. (P1; fix: add a reference value, cross-check or prior human expectation to the outputs map and a plan check)
  - pipeline.py:12: Households with missing weights are silently excluded, so the reported estimates may describe a different population. (P1; fix: assert that weights are present or explicitly account for excluded households)
  - .cg-docs/verification.md:23: The verification profile has no doctor check, so the environment was not established as fit before trusting checks. (P1; fix: define and pass a read-only doctor check)

note: C5 passed the verifier rerun, but the work has no recorded run of it; the not-run flag is covered by the finding on the work report. The claimed published headcount comparison could not be verified from the recorded evidence. Checks for behavior outside the contract were not assessed.

[exit code: 0]
