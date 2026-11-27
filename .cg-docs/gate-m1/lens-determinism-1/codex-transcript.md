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
  - .cg-docs/evidence/2026-11-27-poverty-brief/0002-20261127T095118Z-repro.json:1: The bootstrap interval and region list differed across runs. (P1; fix: seed the bootstrap and sort regions before writing them)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0002-20261127T095118Z-repro.json:1: The recorded headcount output differed from the pipeline’s regenerated output. (P1; fix: regenerate and retain the headcount output directly from the pipeline)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0002-20261127T095118Z-repro.json:1: The pipeline did not write the mapped regional table. (P1; fix: add a pipeline step that calculates and writes the table from the survey)
  - pipeline.py:32: The bootstrap draws have no seed. (P1; fix: initialize a seeded random generator and draw through it)
  - report.qmd:10: The report’s bootstrap has no seed. (P1; fix: call `set.seed()` before the bootstrap)
  - do/robustness.do:4: The bootstrap has no seed. (P1; fix: add `set seed` before the bootstrap)
  - report.qmd:13: The reported headcount is typed into prose. (P1; fix: read the generated headcount output with inline code)
  - report.qmd:17-20: The regional results are typed into the report. (P1; fix: generate the table from the pipeline output when rendering)
  - README.md:7: Producing the brief requires manually copying and saving an output. (P1; fix: have the run command render and save the brief from generated inputs)
  - .cg-docs/verification.md:15: The run command does not render the report. (P1; fix: extend the command to render the report after generating its inputs)
  - pipeline.py:10: The survey path is specific to one machine and can override the project input. (P2; fix: use the project-relative input path or a configured input directory)
  - pipeline.py:25-26: The optional network fetch has no saved, dated source snapshot. (P2; fix: read a saved snapshot with its source and date recorded)
  - pipeline.py:38-40: The notes output depends on an unsorted file listing and the clock. (P1; fix: sort the listing and pass the date as an input)
  - do/robustness.do:1: The Stata version is not pinned. (P2; fix: put the project’s Stata `version` command first)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0002-20261127T095118Z-repro.json:1: The Python and R environments are not pinned. (P2; fix: record dependencies in Python and R lockfiles)
note: The repro command, run command, and pipeline were not rerun because they write outputs. Dataset and output rows were not opened. The clock and listing in the notes file were flagged because they reach an output; interpretation and method choices were left alone.

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
  - .cg-docs/plans/2026-11-27-poverty-brief.md:56: The bootstrap slice specifies no seed. (P1; fix: set and record a seed in `pipeline.py` before the bootstrap draws.)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:57: The regional table and report depend on the agent transcribing values from the console. (P1; fix: have `pipeline.py` calculate and write the table from the survey inputs and have `report.qmd` read it.)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:58: The brief depends on a person copying an interval and saving the document under a clock-dependent name. (P1; fix: have the Run command render `brief.docx` from the computed outputs at a stable path.)
note: Did not run the pipeline or repro because they write outputs. Left interpretation, method choices, and trivial edits alone.

[exit code: 0]
