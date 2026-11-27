### review stage

> Read ~/.agents/skills/cg/worker.md before anything else.

You are the verifier `adversary`. You check one principle, P5 Adversarial by default, at the review stage, and nothing else. Read these files in full, in this order: what every verifier does; your principle, whose section "Verifier" says what to inspect at this stage, what to flag, how to prove a flag and what to leave alone; and your lens, when a third file is listed. Write each finding down as rule 4 of the first file says.

1. ~/.agents/skills/cg/verifier.md
2. ~/.agents/skills/cg/principles/P05-adversarial-by-default.md
3. ~/.agents/skills/cg/lenses/adversary.md

The project root: <project>
Under review: every file that differs from commit 4b825dc642cb6eb9a060e54bf8d69288fbee4904 (`git diff 4b825dc642cb6eb9a060e54bf8d69288fbee4904`), each file that no commit holds (`git status --short`), and the work report .cg-docs/work-reports/2026-11-27-poverty-brief.md
The contract: the plan .cg-docs/plans/2026-11-27-poverty-brief.md, which the human approved as the record .cg-docs/approvals/2026-11-27-poverty-brief.3ca981a13eeac4b7.1.json holds it
What code recorded: .cg-docs/evidence/2026-11-27-poverty-brief/ and .cg-docs/approvals/
A run that code records: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run "<the command>" --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Every check of the plan, rerun by code: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --rerun --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Only the verifier `verification` runs the line above, once. Any other verifier leaves it, and reads the record of that rerun, `"kind": "rerun"`, when there is one.

Return one verdict block, as `verifier.md` gives it, and nothing else.

principle: P5  
verdict: FLAG  
findings:
  - .cg-docs/evidence/2026-11-27-poverty-brief/0011-20261127T200951Z-ad-hoc.json: R1 is broken because `pipeline.py:35` counts a household at the poverty line as poor (P1; fix: use a strict less-than comparison).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0012-20261127T200951Z-ad-hoc.json: R2 is broken because `pipeline.py:40` excludes households whose region has no name from the whole-survey ratio (P1; fix: calculate the ratio from all households).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0019-20261127T201013Z-ad-hoc.json: R3 is broken because `pipeline.py:12` turns a missing weight into zero and allows the calculation to continue (P1; fix: reject missing weights).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0020-20261127T201014Z-ad-hoc.json: R3 is broken because `pipeline.py:11` accepts negative welfare and allows the calculation to continue (P1; fix: reject negative welfare).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0018-20261127T201005Z-ad-hoc.json: R4 is broken because `pipeline.py:46` omits a named region with no households instead of stopping for a group with no weight (P1; fix: consider every named region and reject groups with no weight).
dropped:
  - .cg-docs/evidence/2026-11-27-poverty-brief/0016-20261127T201004Z-ad-hoc.json: A single household with a missing weight did stop the run because its group had zero total weight.
  - .cg-docs/evidence/2026-11-27-poverty-brief/0006-20261127T200933Z-ad-hoc.json: The initial probes could not run because `python` was unavailable; they were rerun with a temporary executable link.
  - .cg-docs/evidence/2026-11-27-poverty-brief/0017-20261127T201005Z-ad-hoc.json: The negative-welfare probe exceeded the command-length limit; the shorter probe above reproduced the fault.
note: Other input cases, including inputs larger than memory, were not probed.

[exit code: 0]
