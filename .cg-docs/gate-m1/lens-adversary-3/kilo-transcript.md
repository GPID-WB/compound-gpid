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

The contract exposes two concrete failure cases in `pipeline.py`: the poverty-line boundary and households excluded from the national ratio when their region is unnamed. I will test those, plus missing-weight and negative-welfare handling, with isolated inputs and record each probe.
principle: P5
verdict: FLAG
findings:
  - .cg-docs/evidence/2026-11-27-poverty-brief/0008-20261127T201203Z-ad-hoc.json: R1 is broken because welfare exactly at the poverty line is counted as poor (`pipeline.py:36`; use a strict `< line` comparison). (P1; fix: change `<= line` to `< line`.)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0010-20261127T201222Z-ad-hoc.json: R2 is broken because `national()` excludes households whose region has no name (`pipeline.py:41`; calculate the national ratio from all survey rows). (P1; fix: pass all rows to `headcount()` for the national ratio.)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0013-20261127T201249Z-ad-hoc.json: R3 is broken because a blank weight is converted to zero instead of stopping the run with an error (`pipeline.py:12`). (P1; fix: reject missing or blank weights.)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0015-20261127T201303Z-ad-hoc.json: R3 is broken because negative welfare is accepted (`pipeline.py:11`). (P1; fix: reject negative welfare.)
dropped:
  - .cg-docs/evidence/2026-11-27-poverty-brief/0006-20261127T201134Z-ad-hoc.json: Boundary probe did not run because `python` was not available; the corrected Rscript probe is recorded in 0008.
  - .cg-docs/evidence/2026-11-27-poverty-brief/0009-20261127T201213Z-ad-hoc.json: The unnamed-region probe had a quoting error; the corrected probe is recorded in 0010.
  - .cg-docs/evidence/2026-11-27-poverty-brief/0011-20261127T201229Z-ad-hoc.json: The missing-weight probe used an absent field, which raised an error; the corrected blank-weight probe is recorded in 0013.
  - .cg-docs/evidence/2026-11-27-poverty-brief/0012-20261127T201240Z-ad-hoc.json: The blank-weight probe had a quoting error; the corrected probe is recorded in 0013.
  - .cg-docs/evidence/2026-11-27-poverty-brief/0014-20261127T201255Z-ad-hoc.json: The negative-welfare probe had a quoting error; the corrected probe is recorded in 0015.
note: I did not probe R4’s empty-weight group, first and last periods, duplicated identifiers, currency or PPP differences, or large inputs. The recorded rerun was not inspected. **Next steps: Done**
* **Your move:** Nothing.
* **Project:** P5 review is complete; four contract failures are recorded as reproduced probe findings.

> code · gpt-6-luna

→ Read ~/.agents/skills/cg/worker.md
→ Read ~/.agents/skills/cg/lenses/adversary.md
→ Read ~/.agents/skills/cg/principles/P05-adversarial-by-default.md
→ Read ~/.agents/skills/cg/verifier.md

# Todos
[•] Inspect contract, changes, report, and recorded evidence
[ ] Run bounded adversarial probes and record them
[ ] Return P5 verdict block with findings and dropped probes

✗ Glob ".cg-docs/evidence/2026-11-27-poverty-brief/**/*" failed in /Users/<user>/temp/cg-lens/adversary-3/toy-poverty-kilo
Error: ripgrep execution failed: NotFound: FileSystem.access (/Users/<user>/temp/cg-lens/adversary-3/toy-poverty-kilo)
→ Read .cg-docs/work-reports/2026-11-27-poverty-brief.md
→ Read .cg-docs/plans/2026-11-27-poverty-brief.md
✱ Glob ".cg-docs/evidence/2026-11-27-poverty-brief/**/*" in . · 0 matches
✱ Glob ".cg-docs/approvals/*" in . · 0 matches
✱ Glob "**/*" in . · 21 matches

$ git status --short && git diff --name-only 4b825dc642cb6eb9a060e54bf8d69288fbee4904
?? .cg-docs/
?? README.md
?? checks/
?? data/
?? output/
?? pipeline.py

→ Read pipeline.py
→ Read checks/inputs.py
→ Read .cg-docs/verification.md
→ Read checks/headcount.py
→ Read checks/table.py
→ Read .cg-docs/approvals/2026-11-27-poverty-brief.3ca981a13eeac4b7.1.json
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0004-20261127T201034Z-tier.json
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0001-20261127T201033Z-tier.json
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0005-20261127T201034Z-C2.json
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0002-20261127T201033Z-C1.json
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T201034Z-C3.json

# Todos
[✓] Inspect contract, changes, report, and recorded evidence
[•] Run bounded adversarial probes and record them
[ ] Return P5 verdict block with findings and dropped probes

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'python -B -c "import pipeline; assert pipeline.headcount([dict(welfare=3,weight=1)],3)==0"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
/bin/sh: python: command not found
check: ad hoc (ad hoc)
exit: 127
verdict: not verified
output: 1 lines, 35 bytes, sha256:5b88129421a309958f7b958853b6f22857e43c88ca1fadbbb75c9398c5c14c63
record: .cg-docs/evidence/2026-11-27-poverty-brief/0006-20261127T201134Z-ad-hoc.json

$ command -v python3 && command -v python3.14 && command -v Rscript
/opt/homebrew/bin/python3
/opt/homebrew/bin/python3.14
/usr/local/bin/Rscript

$ PATH=/opt/homebrew/bin:$PATH "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'python -B -c "import pipeline; assert pipeline.headcount([dict(welfare=3,weight=1)],3)==0"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
/bin/sh: python: command not found
check: ad hoc (ad hoc)
exit: 127
verdict: not verified
output: 1 lines, 35 bytes, sha256:5b88129421a309958f7b958853b6f22857e43c88ca1fadbbb75c9398c5c14c63
record: .cg-docs/evidence/2026-11-27-poverty-brief/0007-20261127T201150Z-ad-hoc.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'Rscript -e "stopifnot(system2(\"python3\", c(\"-B\", \"-c\", shQuote(\"import pipeline; assert pipeline.headcount([dict(welfare=3,weight=1)],3)==0\"))) == 0)"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Threading set to: 12 cores
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import pipeline; assert pipeline.headcount([dict(welfare=3,weight=1)],3)==0
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
Error: system2("python3", c("-B", "-c", shQuote("import pipeline; assert pipeline.headcount([dict(welfare=3,weight=1)],3)==0"))) ==  .... is not TRUE
Execution halted
check: ad hoc (ad hoc)
exit: 1
verdict: not verified
output: 8 lines, 443 bytes, sha256:f658f5ff4b6f1e9ad94be7c6ab5954b5bb11b482a261fe03e30052f2914fcb35
record: .cg-docs/evidence/2026-11-27-poverty-brief/0008-20261127T201203Z-ad-hoc.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'Rscript -e "stopifnot(system2(\"python3\", c(\"-B\", \"-c\", shQuote(\"import pipeline; rows=[dict(region=\"x\",welfare=1,weight=1),dict(region=\"?\",welfare=4,weight=1)]; assert pipeline.national(rows,[dict(region=\"x\",name=\"X\")])==0.5\"))) == 0)"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Threading set to: 12 cores
Error: unexpected symbol in "stopifnot(system2("python3", c("-B", "-c", shQuote("import pipeline; rows=[dict(region="x"
Execution halted
check: ad hoc (ad hoc)
exit: 1
verdict: not verified
output: 3 lines, 164 bytes, sha256:167e458f98ff7c34373846679b9ccf3b7ba520a28f9c69181fbb8a30db2f78f2
record: .cg-docs/evidence/2026-11-27-poverty-brief/0009-20261127T201213Z-ad-hoc.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'Rscript -e "stopifnot(system2(\"python3\", c(\"-B\", \"-c\", shQuote(\"import pipeline; rows=[dict(region=chr(120),welfare=1,weight=1),dict(region=chr(63),welfare=4,weight=1)]; assert pipeline.national(rows,[dict(region=chr(120),name=chr(88))])==0.5\"))) == 0)"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Threading set to: 12 cores
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import pipeline; rows=[dict(region=chr(120),welfare=1,weight=1),dict(region=chr(63),welfare=4,weight=1)]; assert pipeline.national(rows,[dict(region=chr(120),name=chr(88))])==0.5
                                                                                                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
Error: system2("python3", c("-B", "-c", shQuote("import pipeline; rows=[dict(region=chr(120),welfare=1,weight=1),dict(region=chr(63),welfare=4,weight=1)]; assert pipeline.national(rows,[dict(region=chr(120),name=chr(88))])==0.5"))) ==  .... is not TRUE
Execution halted
check: ad hoc (ad hoc)
exit: 1
verdict: not verified
output: 8 lines, 752 bytes, sha256:ced6dae9fb532711a638048b8a38d7600a114dbd251bf05acadf7f78b32af5b7
record: .cg-docs/evidence/2026-11-27-poverty-brief/0010-20261127T201222Z-ad-hoc.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'Rscript -e "stopifnot(system2(\"python3\", c(\"-B\", \"-c\", shQuote(\"import pipeline; assert pipeline.household(dict(hhid=chr(49),region=chr(120),welfare=1))['weight'] != 0\"))) == 0)"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Threading set to: 12 cores
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import pipeline; assert pipeline.household(dict(hhid=chr(49),region=chr(120),welfare=1))[weight] != 0
                            ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<project>/pipeline.py", line 12, in household
    "weight": float(row["weight"] or 0)}
                    ~~~^^^^^^^^^^
KeyError: 'weight'
Error: system2("python3", c("-B", "-c", shQuote("import pipeline; assert pipeline.household(dict(hhid=chr(49),region=chr(120),welfare=1))[weight] != 0"))) ==  .... is not TRUE
Execution halted
check: ad hoc (ad hoc)
exit: 1
verdict: not verified
output: 11 lines, 692 bytes, sha256:7314fc12cb67f055d824a67770669975f0f6ede7fd40f0391304cb4bf5db87a0
record: .cg-docs/evidence/2026-11-27-poverty-brief/0011-20261127T201229Z-ad-hoc.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'Rscript -e "stopifnot(system2(\"python3\", c(\"-B\", \"-c\", shQuote(\"import pipeline; assert list(pipeline.household(dict(hhid=chr(49),region=chr(120),welfare=1,weight='')) .values())[-1] != 0\"))) == 0)"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Threading set to: 12 cores
  File "<string>", line 1
    import pipeline; assert list(pipeline.household(dict(hhid=chr(49),region=chr(120),welfare=1,weight=)) .values())[-1] != 0
                                                                                                ^^^^^^^
SyntaxError: expected argument value expression
Error: system2("python3", c("-B", "-c", shQuote("import pipeline; assert list(pipeline.household(dict(hhid=chr(49),region=chr(120),welfare=1,weight=)) .values())[-1] != 0"))) ==  .... is not TRUE
Execution halted
check: ad hoc (ad hoc)
exit: 1
verdict: not verified
output: 7 lines, 544 bytes, sha256:88321b931748d7b5d9fd6bb5ee683e1219c297df3d5895684f131b6b81659e91
record: .cg-docs/evidence/2026-11-27-poverty-brief/0012-20261127T201240Z-ad-hoc.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'Rscript -e "stopifnot(system2(\"python3\", c(\"-B\", \"-c\", shQuote(\"import pipeline; assert list(pipeline.household(dict(hhid=chr(49),region=chr(120),welfare=1,weight=str())).values())[-1] != 0\"))) == 0)"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Threading set to: 12 cores
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import pipeline; assert list(pipeline.household(dict(hhid=chr(49),region=chr(120),welfare=1,weight=str())).values())[-1] != 0
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
Error: system2("python3", c("-B", "-c", shQuote("import pipeline; assert list(pipeline.household(dict(hhid=chr(49),region=chr(120),welfare=1,weight=str())).values())[-1] != 0"))) ==  .... is not TRUE
Execution halted
check: ad hoc (ad hoc)
exit: 1
verdict: not verified
output: 8 lines, 593 bytes, sha256:339c045a159551645ca344c1c2aba687efe58356f5054cfb6e2c279d3cd31b4a
record: .cg-docs/evidence/2026-11-27-poverty-brief/0013-20261127T201249Z-ad-hoc.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'Rscript -e "stopifnot(system2(\"python3\", c(\"-B\", \"-c\", shQuote(\"import pipeline; assert pipeline.household(dict(hhid=chr(49),region=chr(120),welfare=-1,weight=1))['welfare'] >= 0\"))) == 0)"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Threading set to: 12 cores
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import pipeline; assert pipeline.household(dict(hhid=chr(49),region=chr(120),welfare=-1,weight=1))[welfare] >= 0
                                                                                                       ^^^^^^^
NameError: name 'welfare' is not defined
Error: system2("python3", c("-B", "-c", shQuote("import pipeline; assert pipeline.household(dict(hhid=chr(49),region=chr(120),welfare=-1,weight=1))[welfare] >= 0"))) ==  .... is not TRUE
Execution halted
check: ad hoc (ad hoc)
exit: 1
verdict: not verified
output: 8 lines, 574 bytes, sha256:5f2b824ace76413d4a1ba7a2dfefb36620574aa89daa3f4340c8dca6069eccfc
record: .cg-docs/evidence/2026-11-27-poverty-brief/0014-20261127T201255Z-ad-hoc.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run 'Rscript -e "stopifnot(system2(\"python3\", c(\"-B\", \"-c\", shQuote(\"import pipeline; assert list(pipeline.household(dict(hhid=chr(49),region=chr(120),welfare=-1,weight=1)).values())[-2] >= 0\"))) == 0)"' --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Threading set to: 12 cores
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import pipeline; assert list(pipeline.household(dict(hhid=chr(49),region=chr(120),welfare=-1,weight=1)).values())[-2] >= 0
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
Error: system2("python3", c("-B", "-c", shQuote("import pipeline; assert list(pipeline.household(dict(hhid=chr(49),region=chr(120),welfare=-1,weight=1)).values())[-2] >= 0"))) ==  .... is not TRUE
Execution halted
check: ad hoc (ad hoc)
exit: 1
verdict: not verified
output: 8 lines, 584 bytes, sha256:9fc1a13768eba9f6e00caf0df156b52d7e3568fd60de8b31eda6129ff3a5655d
record: .cg-docs/evidence/2026-11-27-poverty-brief/0015-20261127T201303Z-ad-hoc.json

# Todos
[✓] Inspect contract, changes, report, and recorded evidence
[✓] Run bounded adversarial probes and record them
[✓] Return P5 verdict block with findings and dropped probes



[exit code: 0]
