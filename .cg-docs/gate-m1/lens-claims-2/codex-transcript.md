### review stage

> Read ~/.agents/skills/cg/worker.md before anything else.

You are the verifier `claims`. You check one principle, P7 Honest claims, at the review stage, and nothing else. Read these files in full, in this order: what every verifier does; your principle, whose section "Verifier" says what to inspect at this stage, what to flag, how to prove a flag and what to leave alone; and your lens, when a third file is listed. Write each finding down as rule 4 of the first file says.

1. ~/.agents/skills/cg/verifier.md
2. ~/.agents/skills/cg/principles/P07-honest-claims.md
3. ~/.agents/skills/cg/lenses/claims.md

The project root: <project>
Under review: every file that differs from commit 07a839a6adc142351f6b814128d67e5c9fcd0669 (`git diff 07a839a6adc142351f6b814128d67e5c9fcd0669`), each file that no commit holds (`git status --short`), and the work report .cg-docs/work-reports/2026-11-27-poverty-brief.md
The contract: the plan .cg-docs/plans/2026-11-27-poverty-brief.md, which the human approved as the record .cg-docs/approvals/2026-11-27-poverty-brief.bb76ae1d9c9f2de2.1.json holds it
What code recorded: .cg-docs/evidence/2026-11-27-poverty-brief/ and .cg-docs/approvals/
A run that code records: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run "<the command>" --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Every check of the plan, rerun by code: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --rerun --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Only the verifier `verification` runs the line above, once. Any other verifier leaves it, and reads the record of that rerun, `"kind": "rerun"`, when there is one.

Return one verdict block, as `verifier.md` gives it, and nothing else.

principle: P7
verdict: FLAG
findings:
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:19: The risk assessment makes claims about the work without labels or supporting reasoning (P2; fix: label each claim and provide its evidence or reasoning).
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:27: The Changed table names README.md even though the diff shows it was unchanged (P2; fix: remove the row).
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:40: The named evidence record does not exist (P1; fix: use the paths of the records that exist or remove the claim).
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:41: The stated result differs from the output, as recorded by the claims check (P1; fix: have code write the number from the output).
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:42: The measured claim has no evidence pointer (P1; fix: provide a pointer that shows it or label it inferred with reasoning).
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:43: The named function is absent from pipeline.py, which defines the regional calculation as `table()` (P1; fix: use the defined function name).
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:44: The causal explanation is presented as fact without a label or evidence (P1; fix: label it as an inference with supporting reasoning, or as a guess).
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:45: The C2 record shows a check verdict, not the claimed upper bound (P1; fix: point to evidence that shows the bound or remove the claim).
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:49: The not-checked section omits the limitation that the plan says its checks cannot catch (P2; fix: list that limitation).
note: Claims about whether checks passed were left to P4; the plan’s human-approved claims and plain descriptions of file contents were left alone.

[exit code: 0]
