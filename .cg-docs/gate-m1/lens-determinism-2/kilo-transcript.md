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

principle: P3
verdict: FLAG
findings:
  - do/robustness.do:1: Stata version is not pinned; add the project’s Stata `version` command as the first command. (P2; fix: add `version <the Stata version>` as the first command.)
  - do/robustness.do:4: The bootstrap has no seed; set and record one above the first draw. (P1; fix: add `set seed <a seed>` above the bootstrap and record the seed in the work report.)
  - pipeline.py:32: The bootstrap draws are unseeded; set and record a seed before the first draw. (P1; fix: seed the random generator before drawing and record the seed in the work report.)
  - pipeline.py:10: The survey path is specific to one machine; resolve it from the project root or a configured environment variable. (P2; fix: use a path from the project root, or a configured data-folder environment variable.)
  - pipeline.py:11: The PPP fetch has no saved snapshot; use a dated local copy and record its source. (P2; fix: save the dated download in the project, read it locally, and record its source in the data register.)
  - pipeline.py:38: The input listing is unsorted; sort it before writing the notes output. (P1; fix: wrap the listing in `sorted()`.)
  - report.qmd:10: The bootstrap has no seed; set and record a seed before the first draw. (P1; fix: add `set.seed(<a seed>)` above the bootstrap and record the seed in the work report.)
  - report.qmd:13: The reported headcount number is typed in prose; render it from the generated output. (P1; fix: use inline code to read and render the number from the output.)
  - report.qmd:17-20: The regional headcount numbers are typed in the report; render them from generated output. (P1; fix: generate the table from the output.)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T134446Z-repro.json: The recorded rerun reports differing `output/ci.csv` digests. (P1; fix: seed the bootstrap, sort outputs before writing, and exclude clock-dependent content from compared outputs.)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T134446Z-repro.json: The recorded rerun reports that `output/headcount.csv` changed from its prior digest. (P1; fix: write the output from the Run command without manual edits.)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T134446Z-repro.json: The recorded rerun reports differing `output/regions.csv` digests. (P1; fix: sort the region values before writing.)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T134446Z-repro.json: The recorded rerun reports `output/table.csv` was not written. (P1; fix: add a Run-command step that generates the table from the inputs.)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T134446Z-repro.json: The output map does not account for an output written by the rerun. (P1; fix: add the output to the map or write it outside the project.)
  - README.md:7: The instructions require a person to copy the interval, save a dated file, and render the report manually. (P1; fix: call a script from the Run command to generate and save the brief.)
note: No `cg.py repro`, pipeline, or Run command was run by this verifier. I left aside `unpinned` for Python because the lens says to leave an R package that declares its needs but pins nothing; this project has no Python lockfile, and the repro record already flags that. I did not inspect dataset contents.

> code · gpt-6-luna

→ Read ~/.agents/skills/cg/worker.md
→ Read ~/.agents/skills/cg/verifier.md
→ Read ~/.agents/skills/cg/principles/P03-deterministic-by-default.md
→ Read ~/.agents/skills/cg/lenses/determinism.md
→ Read .cg-docs/work-reports/2026-11-27-poverty-brief.md

$ git diff --name-only 4b825dc642cb6eb9a060e54bf8d69288fbee4904
(no output)

$ git status --short
?? .cg-docs/
?? README.md
?? data/
?? do/
?? output/
?? pipeline.py
?? report.qmd

→ Read pipeline.py
→ Read README.md
→ Read report.qmd
✱ Glob ".cg-docs/evidence/2026-11-27-poverty-brief/**" in . · 0 matches
✱ Glob "**/*" in do · 1 match
✱ Glob "*" in .cg-docs · 8 matches
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T134446Z-repro.json
→ Read do/robustness.do
→ Read .cg-docs/verification.md
→ Read .cg-docs/config.json
✱ Glob "**/*" in output · 5 matches
✱ Glob "**/*" in data · 1 match


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

I’ll read the verifier instructions, P3 principle, and determinism lens in the requested order, then inspect only the named plan.
The plan-stage lens requires inspection of the plan and `.cg-docs/verification.md`; I will check those files for P3 determinism only.
principle: P3
verdict: FLAG
findings:
  - .cg-docs/plans/2026-11-27-poverty-brief.md:57: The plan has the agent read regional shares from the console and type them into output files, so the regional table is not regenerated by code (<P1>; fix: have `pipeline.py` generate `output/table.csv` from the survey inputs and write the report values from that output).
  - .cg-docs/plans/2026-11-27-poverty-brief.md:58: The plan has an analyst copy the interval into a dated brief, which is manual work and makes the output depend on the date (<P1>; fix: add a script that reads `output/ci.csv` and generates `brief.docx` as part of the Run command without a date-specific output path).
  - .cg-docs/plans/2026-11-27-poverty-brief.md:56: The bootstrap uses 500 draws but the plan does not specify a seed (<P1>; fix: set and record a seed in `pipeline.py` before the first draw).
note: No code rerun record applies at plan stage; the plan’s explicit manual steps and unseeded bootstrap establish these findings.

> code · gpt-6-luna

→ Read ~/.agents/skills/cg/worker.md
→ Read ~/.agents/skills/cg/verifier.md
→ Read ~/.agents/skills/cg/principles/P03-deterministic-by-default.md
→ Read ~/.agents/skills/cg/lenses/determinism.md
→ Read .cg-docs/verification.md
→ Read .cg-docs/plans/2026-11-27-poverty-brief.md


[exit code: 0]
