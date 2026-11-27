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

I will read the required verifier instructions first, then inspect only P5 and its assigned review scope.
The P5 verifier requires runnable probes, and only failed, reproducible probes can become findings. I will read the approved plan and work report, then inspect the changed code and existing evidence without opening data files.
The source has likely edge-case mismatches for the line boundary, unnamed-region households, and invalid inputs. I will test these with small in-memory probes, record each through the required evidence command, and keep the survey files closed.
principle: P5
verdict: FLAG
findings:
  - .cg-docs/evidence/2026-11-27-poverty-brief/0012-20261127T123747Z-ad-hoc.json: The run shows R1 is broken because a household exactly at the poverty line is counted as poor by `pipeline.py:36` (P2; fix: count welfare strictly below the line).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0013-20261127T123747Z-ad-hoc.json: The run shows R2 is broken because `national` drops a household whose region has no name at `pipeline.py:41` (P1; fix: calculate the whole-survey ratio from all households, without filtering by named region).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0015-20261127T123747Z-ad-hoc.json: The run shows R3 is broken because `pipeline.py:12` converts a missing weight to zero instead of stopping with an error (P1; fix: reject a missing weight).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0014-20261127T123747Z-ad-hoc.json: The run shows R4 is broken because the table omits a named region with no households at `pipeline.py:47` (P2; fix: include every named region and stop with an error when its group has no weight).
dropped:
  - .cg-docs/evidence/2026-11-27-poverty-brief/0011-20261127T123747Z-ad-hoc.json: The probe could not test the code because the `python` command was unavailable; its rerun failed for the same environment reason.
note: I did not probe negative welfare, zero-weight groups with households, duplicate identifiers, merge behavior, currency or PPP differences, or first and last periods. These probes were outside the four reproduced cases; no plan rerun was present.

> code · gpt-6-luna

→ Read ~/.agents/skills/cg/worker.md
→ Read ~/.agents/skills/cg/principles/P05-adversarial-by-default.md
→ Read ~/.agents/skills/cg/verifier.md
→ Read ~/.agents/skills/cg/lenses/adversary.md

# Todos
[•] Inspect approved plan, work report, changed files, and evidence records
[ ] Run focused adversarial probes and record each run
[ ] Return the required P5 verdict block

→ Read .cg-docs/plans/2026-11-27-poverty-brief.md
→ Read .cg-docs/work-reports/2026-11-27-poverty-brief.md
✱ Glob ".cg-docs/evidence/2026-11-27-poverty-brief/**/*" in . · 0 matches
✱ Glob ".cg-docs/approvals/**/*" in . · 0 matches

$ git status --short && git diff --name-only 4b825dc642cb6eb9a060e54bf8d69288fbee4904 && git diff --stat 4b825dc642cb6eb9a060e54bf8d69288fbee4904
?? .cg-docs/
?? README.md
?? checks/
?? data/
?? output/
?? pipeline.py

→ Read README.md
→ Read pipeline.py
→ Read checks/headcount.py
→ Read checks/table.py
→ Read checks/inputs.py
→ Read .cg-docs/approvals/2026-11-27-poverty-brief.3ca981a13eeac4b7.1.json
✱ Glob "**/*" in . · 21 matches
✱ Glob "**/*" in .cg-docs/evidence · 5 matches
→ Read .cg-docs/verification.md
→ Read .cg-docs/config.json
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T123542Z-C3.json
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0001-20261127T123541Z-tier.json
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0004-20261127T123542Z-tier.json
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0005-20261127T123542Z-C2.json
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0002-20261127T123541Z-C1.json

# Todos
[✓] Inspect approved plan, work report, changed files, and evidence records
[•] Run focused adversarial probes and record each run
[ ] Return the required P5 verdict block

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'python -B -c "import pipeline; assert pipeline.headcount([{\"welfare\":3,\"weight\":1}])==0"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
/bin/sh: python: command not found
check: ad hoc (ad hoc)
exit: 127
verdict: not verified
output: 1 lines, 35 bytes, sha256:5b88129421a309958f7b958853b6f22857e43c88ca1fadbbb75c9398c5c14c63
record: .cg-docs/evidence/2026-11-27-poverty-brief/0006-20261127T123647Z-ad-hoc.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'python3 -B -c "import pipeline; assert pipeline.headcount([{\"welfare\":3,\"weight\":1}])==0"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import pipeline; assert pipeline.headcount([{"welfare":3,"weight":1}])==0
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
check: ad hoc (ad hoc)
exit: 1
verdict: not verified
output: 5 lines, 245 bytes, sha256:84c5c93f4f4dc30ec1acea41efb0257dc69bd50262a383948715c075922be4ce
record: .cg-docs/evidence/2026-11-27-poverty-brief/0007-20261127T123654Z-ad-hoc.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'python3 -B -c "import pipeline; assert pipeline.national([{\"region\":\"?\",\"welfare\":1,\"weight\":1}],[])==1"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import pipeline; assert pipeline.national([{"region":"?","welfare":1,"weight":1}],[])==1
                            ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<project>/pipeline.py", line 41, in national
    return headcount(named(rows, names))
  File "<project>/pipeline.py", line 35, in headcount
    raise ValueError("no household of this group has a weight")
ValueError: no household of this group has a weight
check: ad hoc (ad hoc)
exit: 1
verdict: not verified
output: 9 lines, 623 bytes, sha256:224be5ebe5c77bc74da8e8fe2402af57b2e65a58d83fcad362f1127457f022c0
record: .cg-docs/evidence/2026-11-27-poverty-brief/0008-20261127T123706Z-ad-hoc.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'python3 -B -c "import pipeline; r=[{\"welfare\":1,\"weight\":2},{\"welfare\":4,\"weight\":3}]; assert pipeline.headcount([pipeline.household({\"hhid\":\"a\",\"region\":\"x\",\"welfare\":\"1\",\"weight\":\"\"}),r[1]])"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import pipeline; r=[{"welfare":1,"weight":2},{"welfare":4,"weight":3}]; assert pipeline.headcount([pipeline.household({"hhid":"a","region":"x","welfare":"1","weight":""}),r[1]])
                                                                                   ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
check: ad hoc (ad hoc)
exit: 1
verdict: not verified
output: 5 lines, 453 bytes, sha256:ba1886ab6a18628f75aae8cb572cd4c1a867797c78bb4aa68c6273f7307f1679
record: .cg-docs/evidence/2026-11-27-poverty-brief/0009-20261127T123712Z-ad-hoc.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'python3 -B -c "import pipeline; assert pipeline.table([], [{\"region\":\"x\",\"name\":\"East\"}])=={\"East\":0}"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import pipeline; assert pipeline.table([], [{"region":"x","name":"East"}])=={"East":0}
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
check: ad hoc (ad hoc)
exit: 1
verdict: not verified
output: 5 lines, 271 bytes, sha256:180f12349c51f2497e46e1780cba6605c8a3c485a55bda11def2277b94762514
record: .cg-docs/evidence/2026-11-27-poverty-brief/0010-20261127T123722Z-ad-hoc.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'python -B -c "import pipeline; assert pipeline.headcount([{\"welfare\":3,\"weight\":1}])==0"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
/bin/sh: python: command not found
check: ad hoc (ad hoc)
exit: 127
verdict: not verified
output: 1 lines, 35 bytes, sha256:5b88129421a309958f7b958853b6f22857e43c88ca1fadbbb75c9398c5c14c63
record: .cg-docs/evidence/2026-11-27-poverty-brief/0011-20261127T123747Z-ad-hoc.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'python3 -B -c "import pipeline; assert pipeline.headcount([{\"welfare\":3,\"weight\":1}])==0"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import pipeline; assert pipeline.headcount([{"welfare":3,"weight":1}])==0
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
check: ad hoc (ad hoc)
exit: 1
verdict: not verified
output: 5 lines, 245 bytes, sha256:84c5c93f4f4dc30ec1acea41efb0257dc69bd50262a383948715c075922be4ce
record: .cg-docs/evidence/2026-11-27-poverty-brief/0012-20261127T123747Z-ad-hoc.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'python3 -B -c "import pipeline; assert pipeline.national([{\"region\":\"?\",\"welfare\":1,\"weight\":1}],[])==1"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import pipeline; assert pipeline.national([{"region":"?","welfare":1,"weight":1}],[])==1
                            ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<project>/pipeline.py", line 41, in national
    return headcount(named(rows, names))
  File "<project>/pipeline.py", line 35, in headcount
    raise ValueError("no household of this group has a weight")
ValueError: no household of this group has a weight
check: ad hoc (ad hoc)
exit: 1
verdict: not verified
output: 9 lines, 623 bytes, sha256:224be5ebe5c77bc74da8e8fe2402af57b2e65a58d83fcad362f1127457f022c0
record: .cg-docs/evidence/2026-11-27-poverty-brief/0013-20261127T123747Z-ad-hoc.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'python3 -B -c "import pipeline; assert pipeline.table([], [{\"region\":\"x\",\"name\":\"East\"}])=={\"East\":0}"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import pipeline; assert pipeline.table([], [{"region":"x","name":"East"}])=={"East":0}
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
check: ad hoc (ad hoc)
exit: 1
verdict: not verified
output: 5 lines, 271 bytes, sha256:180f12349c51f2497e46e1780cba6605c8a3c485a55bda11def2277b94762514
record: .cg-docs/evidence/2026-11-27-poverty-brief/0014-20261127T123747Z-ad-hoc.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'python3 -B -c "import pipeline; r=[{\"welfare\":1,\"weight\":2},{\"welfare\":4,\"weight\":3}]; assert pipeline.headcount([pipeline.household({\"hhid\":\"a\",\"region\":\"x\",\"welfare\":\"1\",\"weight\":\"\"}),r[1]])"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import pipeline; r=[{"welfare":1,"weight":2},{"welfare":4,"weight":3}]; assert pipeline.headcount([pipeline.household({"hhid":"a","region":"x","welfare":"1","weight":""}),r[1]])
                                                                                   ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
check: ad hoc (ad hoc)
exit: 1
verdict: not verified
output: 5 lines, 453 bytes, sha256:ba1886ab6a18628f75aae8cb572cd4c1a867797c78bb4aa68c6273f7307f1679
record: .cg-docs/evidence/2026-11-27-poverty-brief/0015-20261127T123747Z-ad-hoc.json

# Todos
[✓] Inspect approved plan, work report, changed files, and evidence records
[✓] Run focused adversarial probes and record each run
[✓] Return the required P5 verdict block



[exit code: 0]
