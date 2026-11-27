### review stage

> Read ~/.agents/skills/cg/worker.md before anything else.

You are the verifier `determinism`. You check one principle, P3 Deterministic by default, at the review stage, and nothing else. Read these files in full, in this order: what every verifier does; your principle, whose section "Verifier" says what to inspect at this stage, what to flag, how to prove a flag and what to leave alone; and your lens, when a third file is listed. Write each finding down as rule 4 of the first file says.

1. ~/.agents/skills/cg/verifier.md
2. ~/.agents/skills/cg/principles/P03-deterministic-by-default.md
3. ~/.agents/skills/cg/lenses/determinism.md

The project root: <project>
Under review: every file that differs from commit 4b825dc642cb6eb9a060e54bf8d69288fbee4904 (`git diff 4b825dc642cb6eb9a060e54bf8d69288fbee4904`), each file that no commit holds (`git status --short`), and the work report .cg-docs/work-reports/2026-11-27-poverty-brief.md
The contract: no plan: this is quick work, and what the human asked is under "Asked" in the work report
What code recorded: .cg-docs/evidence/2026-11-27-poverty-brief/ and .cg-docs/approvals/
A run that code records: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run "<the command>" --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Every check of the plan, rerun by code: none: no plan declares a check for this work
Only the verifier `verification` runs the line above, once. Any other verifier leaves it, and reads the record of that rerun, `"kind": "rerun"`, when there is one.

Return one verdict block, as `verifier.md` gives it, and nothing else.

I will read the verifier instructions, P3 principle, and determinism lens in the required order. Then I will inspect only the requested diff, uncommitted files, work report, and recorded evidence for P3.
The lens requires the existing `repro` record and prohibits running it or the recorded pipeline. I will inspect the requested review files and the existing repro evidence only; I will not run code or open data files.
principle: P3
verdict: FLAG
findings:
  - do/robustness.do:4: The bootstrap has no seed, so repeated runs can produce different intervals. (P1; fix: add `set seed <a seed>` above the first draw and record the seed in the work report)
  - pipeline.py:32: The bootstrap draws have no seed, so repeated runs can produce different intervals. (P1; fix: add a seeded random generator above the first draw and use it for each draw)
  - pipeline.py:10: The survey path is specific to one machine. (P2; fix: resolve the survey path from the project root or use a configured environment variable)
  - pipeline.py:11: The network source can change between runs and has no saved snapshot. (P2; fix: save a dated source copy in the project and read it from there)
  - pipeline.py:38: The input file listing is unsorted and can change the order written to an output. (P1; fix: sort the listing before writing)
  - report.qmd:10: The bootstrap has no seed, so repeated renders can produce different intervals. (P1; fix: set and record a seed before the first draw)
  - report.qmd:13: The reported headcount number is typed into prose instead of read from generated output. (P1; fix: use inline code to read the number from the output)
  - report.qmd:17-20: The regional headcount numbers are typed into the report instead of generated from inputs. (P1; fix: generate the table from the inputs in the report or pipeline)
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:19: The report says the pipeline overwrites outputs that no commit holds, but it does not prevent a run from replacing or creating those outputs. (P1; fix: write to a temporary path and rename after each output is complete)
  - .cg-docs/work-reports/2026-11-27-poverty-brief.md:25: The README directs a person to copy the interval into the brief and save a dated file, so the output depends on manual copying and naming. (P1; fix: generate the brief file from the pipeline)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T142419Z-repro.json: The repro record marks the bootstrap interval output as differing between runs. (P1; fix: seed the draws and write the output in a stable order)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T142419Z-repro.json: The repro record marks the regions output as differing between runs. (P1; fix: sort the region values before writing)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T142419Z-repro.json: The repro record marks the headcount output as changed from its prior contents. (P1; fix: regenerate the output from inputs and do not edit it afterwards)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T142419Z-repro.json: The repro record marks the regional table output as not written by the run. (P1; fix: add a pipeline step that generates the table from inputs)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T142419Z-repro.json: The repro record flags missing pinned Python and Stata environments. (P2; fix: pin Python dependencies and add the Stata version as the first do-file command)
note: Did not inspect data files. Did not run the recorded pipeline or `repro`; no such rerun is required by the kickoff. Set aside `clock` at `pipeline.py:40` because the run record does not show that notes.txt is a mapped output; the listing at line 38 still affects `output/regions.csv`. The report's bootstrap and output claims conflict with the repro evidence, so I relied on the recorded rerun for those findings.

> code · gpt-6-luna

→ Read ~/.agents/skills/cg/worker.md
→ Read ~/.agents/skills/cg/verifier.md
→ Read ~/.agents/skills/cg/principles/P03-deterministic-by-default.md
→ Read ~/.agents/skills/cg/lenses/determinism.md

$ git diff --name-only 4b825dc642cb6eb9a060e54bf8d69288fbee4904 && git status --short
?? .cg-docs/
?? README.md
?? data/
?? do/
?? output/
?? pipeline.py
?? report.qmd

✱ Glob ".cg-docs/evidence/2026-11-27-poverty-brief/**/*" in . · 0 matches
✱ Glob ".cg-docs/evidence/2026-11-27-poverty-brief/**" in . · 0 matches
→ Read .cg-docs/work-reports/2026-11-27-poverty-brief.md
✱ Glob ".cg-docs/**" in . · 0 matches

$ git diff --no-ext-diff --unified=3 4b825dc642cb6eb9a060e54bf8d69288fbee4904 -- README.md pipeline.py report.qmd do
(no output)

→ Read pipeline.py
✱ Glob "**/*" in do · 1 match
→ Read do/robustness.do
→ Read report.qmd
✱ Glob "output/**" in . · 5 matches

$ git ls-files --others --exclude-standard
.cg-docs/approvals/2026-11-27-poverty-brief.d490cb4ececdde76.1.json
.cg-docs/config.json
.cg-docs/evidence/2026-11-27-poverty-brief/0001-20261127T142419Z-tier.json
.cg-docs/evidence/2026-11-27-poverty-brief/0002-20261127T142419Z-tier.json
.cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T142419Z-repro.json
.cg-docs/plans/2026-11-27-poverty-brief.md
.cg-docs/verification.md
.cg-docs/work-reports/2026-11-27-poverty-brief.md
README.md
data/survey.csv
do/robustness.do
output/ci.csv
output/headcount.csv
output/notes.txt
output/regions.csv
output/table.csv
pipeline.py
report.qmd

→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T142419Z-repro.json
→ Read .cg-docs/verification.md
✱ Glob "README.md" in . · 1 match
→ Read README.md


[exit code: 0]

### plan stage

> Read ~/.agents/skills/cg/worker.md before anything else.

You are the verifier `determinism`. You check one principle, P3 Deterministic by default, at the plan stage, and nothing else. Read these files in full, in this order: what every verifier does; your principle, whose section "Verifier" says what to inspect at this stage, what to flag, how to prove a flag and what to leave alone; and your lens, when a third file is listed. Write each finding down as rule 4 of the first file says.

1. ~/.agents/skills/cg/verifier.md
2. ~/.agents/skills/cg/principles/P03-deterministic-by-default.md
3. ~/.agents/skills/cg/lenses/determinism.md

The project root: <project>
Under review: .cg-docs/plans/2026-11-27-poverty-brief.md
The contract: in the plan itself; it names no intent that the human decided
What code recorded: none
A run that code records: none at this stage, so point at a file and a line
Every check of the plan, rerun by code: none at this stage
Only the verifier `verification` runs the line above, once. Any other verifier leaves it, and reads the record of that rerun, `"kind": "rerun"`, when there is one.

Return one verdict block, as `verifier.md` gives it, and nothing else.

principle: P3
verdict: FLAG
findings:
  - .cg-docs/plans/2026-11-27-poverty-brief.md:57: S3 relies on reading regional shares from the console and typing them into output files, so the results are not produced by a tool from the inputs (P1; fix: have `pipeline.py` write `output/table.csv` and generate the report from that output in the Run command)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:58: S4 relies on copying the interval into a dated Word file, so a person must copy and save a result manually (P1; fix: generate `brief.docx` from `output/ci.csv` in the Run command, with a date passed as an input)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:56: S2 specifies bootstrap draws but no seed, so reruns can produce different intervals (P1; fix: set and record a seed before the bootstrap draws in `pipeline.py`)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:55-58: The plan names outputs to create but the project has no `.cg-docs/verification.md` Run command to regenerate them from inputs (P1; fix: add a Run command that calls the tools to produce each output from the inputs)
note: Did not inspect `.cg-docs/verification.md` because it is not present. Did not run code; this is the plan stage.

> code · gpt-6-luna

→ Read ~/.agents/skills/cg/worker.md
→ Read ~/.agents/skills/cg/verifier.md
→ Read ~/.agents/skills/cg/principles/P03-deterministic-by-default.md
→ Read ~/.agents/skills/cg/lenses/determinism.md
→ Read .cg-docs/plans/2026-11-27-poverty-brief.md
✱ Glob ".cg-docs/verification.md" in . · 0 matches


[exit code: 0]
