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
  - .cg-docs/plans/2026-11-27-poverty-brief.md:36: C2 checks only that the table exists, so it does not verify its values (P1; fix: check the real table values against independent expected values).
  - .cg-docs/plans/2026-11-27-poverty-brief.md:37: The pipe makes C3 report the exit status of `sort` even when the interval check fails (P1; fix: make the command return the interval check’s exit status).
  - .cg-docs/plans/2026-11-27-poverty-brief.md:38: C4 fails on the current files after an earlier verified run (P1; fix: correct the first cause of the missing region and rerun C4 through evidence).
  - .cg-docs/plans/2026-11-27-poverty-brief.md:39: C5 has no recorded work run on the current files (P1; fix: run C5 through evidence).
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:45: The claim that C5 passed has no recorded work run (P1; fix: record the check through evidence or remove the claim).
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:46: The claimed comparison with the published figure has no recorded supporting check (P1; fix: record the comparison through evidence or remove the claim).
  - .cg-docs/verification.md:32: The bootstrap interval has no independent validation (P1; fix: add a reference value, independent cross-check, or prior human expectation to the outputs map and a plan check).
  - checks/headcount.py:8: C1 derives its expected value using the same function that produces the output (P1; fix: compare the output with an independently established expected value).
  - pipeline.py:12: Households with missing weights are silently excluded, so the reported estimates can measure a subset of the intended survey (P1; fix: assert that required weights are present or account explicitly for excluded households).
  - .cg-docs/verification.md:23: The verification profile has no doctor command, so environment fitness has not been established before trusting checks (P1; fix: provide and pass a read-only doctor check).
note: The rerun passed C1, C2, C3, and C5 and failed C4; C1 and C2 were previously recorded on an earlier file state. Checks for behavior outside the contract were not assessed.

[exit code: 0]
