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
  - .cg-docs/plans/2026-11-27-poverty-brief.md:36: C2 checks only that the table exists, leaving its shares unchecked against independent expected values (P1; fix: check the values in the final table against an independent reference).
  - .cg-docs/plans/2026-11-27-poverty-brief.md:37: The pipe to `sort` masks a failure of the interval check (P1; fix: make the command return the check’s own exit code).
  - .cg-docs/plans/2026-11-27-poverty-brief.md:38: C4 passed on an earlier state but fails on the current files (P1; fix: correct the first cause in the pipeline and rerun C4 through evidence).
  - .cg-docs/plans/2026-11-27-poverty-brief.md:39: The work has no recorded run of C5 (P1; fix: run C5 through evidence on the current files).
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:45: The claim that C5 passed has no work evidence record (P1; fix: record the check through evidence or remove the claim).
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:46: The claimed comparison with a published figure has no recorded comparison (P1; fix: record an independent comparison or remove the claim).
  - .cg-docs/verification.md:32: The regional shares have no independent validation (P1; fix: add a reference value, independent cross-check or prior human expectation to the outputs map and a plan check).
  - checks/headcount.py:8: C1 derives its expected value using the same functions as the output, so it cannot detect a shared calculation error (P1; fix: compare the final output with an independently established expected value).
  - pipeline.py:12: Households with missing weights are silently excluded, so the reported statistics measure the retained households without accounting for the exclusion (P1; fix: assert that required weights are present or explicitly account for excluded households).
  - .cg-docs/verification.md:22: The profile has no usable doctor command, so the environment has not been shown fit for the checks (P1; fix: provide and pass a read-only environment check).
note: The interval has no independent validation in the outputs map. Checks outside the approved contract were not assessed. The rerun record is .cg-docs/evidence/2026-11-27-poverty-brief/0008-20261127T134142Z-rerun.json; the source inspection record is .cg-docs/evidence/2026-11-27-poverty-brief/0009-20261127T134204Z-ad-hoc.json.

[exit code: 0]
