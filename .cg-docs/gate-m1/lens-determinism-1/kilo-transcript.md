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

Return one verdict block, as `verifier.md` gives it, and nothing else.

principle: P3
verdict: FLAG
findings:
  - .cg-docs/evidence/2026-11-27-poverty-brief/0002-20261127T095223Z-repro.json: The bootstrap interval output differs between runs; set and record a seed above the first draw and keep the output order fixed (P1; fix: add a fixed seed before the draw and set an order before writing).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0002-20261127T095223Z-repro.json: The table output is not written by the Run command (P1; fix: add a command step that writes the table from the inputs).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0002-20261127T095223Z-repro.json: The outputs map does not list all outputs written by the run (P1; fix: add each output to the outputs map, or write non-output files outside the project).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0002-20261127T095223Z-repro.json: The reported headcount output differs from the file that existed before the run (P1; fix: produce the output from the Run command without manual edits).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0002-20261127T095223Z-repro.json: The Stata do-file has no pinned version (P2; fix: add `version <the Stata version>` as its first command).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0002-20261127T095223Z-repro.json: The Stata bootstrap has no recorded seed (P1; fix: set and record a seed above the first draw).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0002-20261127T095223Z-repro.json: The Python bootstrap has no recorded seed (P1; fix: set and record a seed above the first draw).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0002-20261127T095223Z-repro.json: The Python environment has no lockfile (P2; fix: add `pyproject.toml` and `uv.lock` for the imported packages).
  - pipeline.py:10: The survey path depends on a specific user's machine (P2; fix: resolve the survey path from the project root).
  - pipeline.py:11: The pipeline can fetch PPP data from the network without a saved snapshot (P2; fix: use a project copy with its date and source recorded).
  - pipeline.py:32: The bootstrap uses random draws without setting a seed (P1; fix: set and record a seed before the first draw).
  - pipeline.py:38: The input file listing is not sorted before it is written to an output (P1; fix: sort the listing before writing).
  - pipeline.py:40: The output includes the current date, so it can change between runs (P1; fix: pass the date in as an input and exclude the clock from compared outputs).
  - report.qmd:10: The bootstrap uses random draws without setting a seed (P1; fix: set and record a seed before the first draw).
  - report.qmd:13: The reported headcount number is typed instead of read from an output (P1; fix: render it from the generated output).
  - report.qmd:17-20: The regional results are typed instead of read from an output (P1; fix: render the table from generated output).
  - README.md:7: The instructions require a person to copy, rename and save the interval by date (P1; fix: add a script step to the Run command that writes the final brief).
note: I did not run `repro`, the Run command, or the pipeline, as the lens directs. I did not open data files. I left interpretation and choice of method alone. No approval records were present to inspect.

> code · gpt-6-luna

→ Read ~/.agents/skills/cg/worker.md
→ Read ~/.agents/skills/cg/verifier.md
→ Read ~/.agents/skills/cg/principles/P03-deterministic-by-default.md
→ Read ~/.agents/skills/cg/lenses/determinism.md

# Todos
[•] Identify changed files and required review evidence
[ ] Inspect diff, report, repro record, and approval records
[ ] Return P3 verdict in required block format

✱ Glob ".cg-docs/evidence/2026-11-27-poverty-brief/*" in . · 0 matches
→ Read .cg-docs/work-reports/2026-11-27-poverty-brief.md
✱ Glob ".cg-docs/evidence/2026-11-27-poverty-brief/**/*" in . · 0 matches

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

✱ Glob ".cg-docs/**/*" in . · 0 matches
→ Read .
→ Read pipeline.py
→ Read README.md
→ Read report.qmd

$ git diff --stat 4b825dc642cb6eb9a060e54bf8d69288fbee4904 && git diff 4b825dc642cb6eb9a060e54bf8d69288fbee4904
(no output)

→ Read .cg-docs
→ Read do
→ Read data
→ Read output
✗ Read .cg-docs/approvals failed
Error: File not found: <project>/.cg-docs/approvals
→ Read .cg-docs/evidence
→ Read .cg-docs/verification.md
→ Read do/robustness.do
→ Read .cg-docs/evidence/2026-11-27-poverty-brief
→ Read .cg-docs/plans
→ Read .cg-docs/config.json
→ Read .cg-docs
→ Read .cg-docs/plans/2026-11-27-poverty-brief.md
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0001-20261127T095222Z-tier.json
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0002-20261127T095223Z-repro.json

# Todos
[✓] Identify changed files and required review evidence
[✓] Inspect diff, report, repro record, and approval records
[✓] Return P3 verdict in required block format



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

Return one verdict block, as `verifier.md` gives it, and nothing else.

principle: P3
verdict: FLAG
findings:
  - .cg-docs/plans/2026-11-27-poverty-brief.md:57: The plan assigns a table of regional shares to judgement and asks the agent to read shares from the console and type them into files, instead of generating them from the inputs with a tool (P1; fix: add a `pipeline.py` step that calculates the regional shares and writes both outputs).
  - .cg-docs/plans/2026-11-27-poverty-brief.md:58: The plan asks an analyst to copy an interval into a dated document, so the delivered brief is not regenerated by a tool from the inputs (P1; fix: add a script to generate `brief.docx` from the interval output and call it from the Run command).
  - .cg-docs/verification.md:1: The plan names outputs to make but the verification profile has no Run command (P1; fix: define a Run command that generates the outputs from the inputs).
note: The verification profile file is absent, so its contents could not be inspected; no code has run at this plan stage. I did not inspect data or other principles.

> code · gpt-6-luna

→ Read ~/.agents/skills/cg/worker.md
→ Read ~/.agents/skills/cg/verifier.md
→ Read ~/.agents/skills/cg/principles/P03-deterministic-by-default.md
→ Read ~/.agents/skills/cg/lenses/determinism.md
→ Read .cg-docs/plans/2026-11-27-poverty-brief.md
✱ Glob ".cg-docs/verification.md" in . · 0 matches


[exit code: 0]
