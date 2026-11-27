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

I will read the verifier instructions, P5 rule, and adversary lens in the required order, then inspect only the assigned review materials and report findings in the required block.
P5 requires findings only from reproducible runs, with up to three rounds. I will now read the adversary lens, then inspect the approved plan, code evidence, and current project changes without opening data files.
The code exposes two high-risk contract cases suitable for isolated probes: welfare exactly at the poverty line, and households whose region has no name. The recorded checks all passed and contain no earlier failed probe to replay; I will test these two cases with synthetic inputs only.
principle: P5
verdict: FLAG
findings:
  - .cg-docs/evidence/2026-11-27-poverty-brief/0007-20261127T143040Z-ad-hoc.json:10: The boundary probe shows that `pipeline.py:36` counts welfare equal to the poverty line as poor, contrary to R1, which requires welfare at or above the line to be not poor (P1; fix: count only welfare strictly below the line).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0008-20261127T143046Z-ad-hoc.json:10: The unnamed-region probe shows that `pipeline.py:41` excludes a household without a named region from the national headcount, contrary to R2 (P1; fix: compute the national headcount from all survey households).
dropped:
  - none: Both tested cases reproduced as contract violations.
note: I did not probe other boundaries, missing or zero weights, missing or negative welfare, duplicate identifiers, unmatched or multiply matched region keys, currency or PPP differences, or input-size limits. The kickoff permits at most three rounds; two probes reproduced contract violations.

> code · gpt-6-luna

→ Read ~/.agents/skills/cg/worker.md
→ Read ~/.agents/skills/cg/verifier.md
→ Read ~/.agents/skills/cg/principles/P05-adversarial-by-default.md
→ Read ~/.agents/skills/cg/lenses/adversary.md

# Todos
[•] Inspect approved contract and work report within P5 scope
[ ] Review recorded probe failures and rerun eligible probes
[ ] Run up to three focused adversarial probes and return verdict

✱ Glob ".cg-docs/evidence/2026-11-27-poverty-brief/**/*" in . · 0 matches
→ Read .cg-docs/plans/2026-11-27-poverty-brief.md
→ Read .cg-docs/approvals/2026-11-27-poverty-brief.3ca981a13eeac4b7.1.json
→ Read .cg-docs/work-reports/2026-11-27-poverty-brief.md

$ git diff --name-only 4b825dc642cb6eb9a060e54bf8d69288fbee4904
(no output)

$ git status --short
?? .cg-docs/
?? README.md
?? checks/
?? data/
?? output/
?? pipeline.py

→ Read .cg-docs/evidence/2026-11-27-poverty-brief
→ Read pipeline.py
→ Read README.md
→ Read checks/inputs.py
→ Read checks/table.py
→ Read checks/headcount.py
✗ Read /Users/<user><user>/temp/cg-lens/adversary-2/toy-poverty-kilo/.cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T142921Z-C3.json failed
Error: File not found: /Users/<user><user>/temp/cg-lens/adversary-2/toy-poverty-kilo/.cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T142921Z-C3.json
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0001-20261127T142920Z-tier.json
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0002-20261127T142921Z-C1.json
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0004-20261127T142921Z-tier.json
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0005-20261127T142921Z-C2.json
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T142921Z-C3.json

# Todos
[✓] Inspect approved contract and work report within P5 scope
[✓] Review recorded probe failures and rerun eligible probes
[•] Run up to three focused adversarial probes and return verdict

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'python -B -c "import pipeline; assert pipeline.headcount([dict(weight=1,welfare=3)])==0"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
/bin/sh: python: command not found
check: ad hoc (ad hoc)
exit: 127
verdict: not verified
output: 1 lines, 35 bytes, sha256:5b88129421a309958f7b958853b6f22857e43c88ca1fadbbb75c9398c5c14c63
record: .cg-docs/evidence/2026-11-27-poverty-brief/0006-20261127T143025Z-ad-hoc.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run '/opt/homebrew/opt/python@3.14/bin/python3.14 -B -c "import pipeline; assert pipeline.national([dict(region=\"?\",weight=1,welfare=1)],[])==1"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "/Users/<user><user>/temp/cg-lens/adversary-2/toy-poverty-kilo"
no such folder: /Users/<user><user>/temp/cg-lens/adversary-2/toy-poverty-kilo

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run '/opt/homebrew/opt/python@3.14/bin/python3.14 -B -c "import pipeline; assert pipeline.headcount([dict(weight=1,welfare=3)])==0"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import pipeline; assert pipeline.headcount([dict(weight=1,welfare=3)])==0
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
check: ad hoc (ad hoc)
exit: 1
verdict: not verified
output: 5 lines, 245 bytes, sha256:d4b32a0d08a0cec1c5855b65fa9effb282225d8e4718f42634aaa543dd41dca6
record: .cg-docs/evidence/2026-11-27-poverty-brief/0007-20261127T143040Z-ad-hoc.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run '/opt/homebrew/opt/python@3.14/bin/python3.14 -B -c "import pipeline; assert pipeline.national([dict(region=\"?\",weight=1,welfare=1)],[])==1"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import pipeline; assert pipeline.national([dict(region="?",weight=1,welfare=1)],[])==1
                            ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<project>/pipeline.py", line 41, in national
    return headcount(named(rows, names))
  File "<project>/pipeline.py", line 35, in headcount
    raise ValueError("no household of this group has a weight")
ValueError: no household of this group has a weight
check: ad hoc (ad hoc)
exit: 1
verdict: not verified
output: 9 lines, 619 bytes, sha256:74c3757baff8f0cade2797a6b25d2797e5d706ca7c97f5da963738eac4dc74c4
record: .cg-docs/evidence/2026-11-27-poverty-brief/0008-20261127T143046Z-ad-hoc.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'python -B -c "import pipeline; assert pipeline.headcount([dict(weight=1,welfare=3)])==0"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
/bin/sh: python: command not found
check: ad hoc (ad hoc)
exit: 127
verdict: not verified
output: 1 lines, 35 bytes, sha256:5b88129421a309958f7b958853b6f22857e43c88ca1fadbbb75c9398c5c14c63
record: .cg-docs/evidence/2026-11-27-poverty-brief/0009-20261127T143056Z-ad-hoc.json

# Todos
[✓] Inspect approved contract and work report within P5 scope
[✓] Review recorded probe failures and rerun eligible probes
[✓] Run up to three focused adversarial probes and return verdict



[exit code: 0]
