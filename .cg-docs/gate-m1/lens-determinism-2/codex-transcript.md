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
  - do/robustness.do:1: The Stata version is not pinned (P2; fix: add `version 18` as the first command).
  - do/robustness.do:4: The bootstrap has no seed (P1; fix: add `set seed <seed>` before the bootstrap).
  - pipeline.py:32: The bootstrap has no seed (P1; fix: call `random.seed(<seed>)` before the first draw).
  - pipeline.py:10: The input path is specific to one machine and can change which input is used (P2; fix: use a project-relative path or a configured input directory).
  - report.qmd:10: The bootstrap has no seed (P1; fix: add `set.seed(<seed>)` before the draw).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T134333Z-repro.json: The R and Python environments are not pinned (P2; fix: add an `renv.lock` and a Python lockfile).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T134333Z-repro.json: The interval and region outputs differed between runs (P1; fix: seed the bootstrap and sort regions before writing them).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T134333Z-repro.json: The headcount output on file differed from the regenerated output (P1; fix: produce the delivered output with the Run command).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T134333Z-repro.json: The Run command did not write the mapped regional table (P1; fix: add a pipeline step that computes and writes the table from the input).
  - .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T134333Z-repro.json: The runs wrote outputs that are absent from the outputs map (P1; fix: map each delivered output and write intermediate files outside the project).
  - README.md:7: Delivery requires a person to copy a result and rename a document (P1; fix: generate the document and its filename in the Run command).
  - report.qmd:13: The reported result is typed into prose rather than read from the generated output (P1; fix: use inline code that reads the headcount output).
  - report.qmd:17-20: The regional table is typed into the report rather than generated from the input (P1; fix: render the table from the generated regional table output).
note: The Run command and `repro` were not rerun because they write outputs. The network entry was set aside because the downloaded file is not read by the run; the clock and unsorted listing were set aside because their output is not mapped for comparison. Dataset files were not opened.

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
  - .cg-docs/plans/2026-11-27-poverty-brief.md:56: The bootstrap has no specified seed, so reruns may produce different intervals (P1; fix: set a fixed seed in `pipeline.py` before drawing samples).
  - .cg-docs/plans/2026-11-27-poverty-brief.md:57: The regional table and report depend on the agent transcribing results by hand (P1; fix: have `pipeline.py` write the table from the survey and have the report read that output).
  - .cg-docs/plans/2026-11-27-poverty-brief.md:58: The brief depends on a person copying the interval and naming the output using the current date (P1; fix: generate the brief from `output/ci.csv` in the Run command and use a fixed output path).
note: The pipeline and repro were not run at the plan stage. Interpretation and choice of method were left alone.

[exit code: 0]
