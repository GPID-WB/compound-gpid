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
  - .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T142319Z-repro.json: The recorded runs changed the existing headcount output. (P1; fix: regenerate the output with `python3 pipeline.py` and retain the generated file)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T142319Z-repro.json: Neither recorded run wrote the mapped regional table. (P1; fix: add a pipeline step that computes and writes `output/table.csv` from the survey)
  - pipeline.py:32: The bootstrap draws have no seed, and the repro record reports different interval outputs. (P1; fix: create a seeded `random.Random` instance and use it for each draw)
  - pipeline.py:36-37: The regional output uses set iteration order, and the repro record reports different outputs across runs. (P1; fix: iterate over `sorted(regions)` before writing)
  - pipeline.py:40: The notes output includes the current date and an unsorted file listing. (P1; fix: pass the date as an input and use `sorted(glob.glob(...))`)
  - pipeline.py:10: The survey path is specific to one machine. (P2; fix: use the project-relative survey path or a configured environment variable)
  - pipeline.py:25-26: The optional network fetch has no dated, sourced snapshot. (P2; fix: save a dated snapshot with its source and read it locally)
  - do/robustness.do:1: The Stata environment has no version declaration. (P2; fix: add `version` with the intended Stata version as the first command)
  - do/robustness.do:4: The bootstrap runs without a seed. (P1; fix: add `set seed` with a recorded seed before the bootstrap)
  - report.qmd:10: The bootstrap runs without a seed. (P1; fix: call `set.seed()` with a recorded seed before `boot()`)
  - report.qmd:13: The reported headcount is typed into prose rather than read from a generated output. (P1; fix: use inline code to read and format the generated headcount)
  - report.qmd:15-20: The regional table is typed into the brief rather than generated from the inputs. (P1; fix: render the table from the pipeline’s regional output)
  - README.md:6-7: Producing the brief requires separate rendering and manual copying and renaming. (P1; fix: add rendering and document generation to the pipeline command)
  - .cg-docs/evidence/2026-11-27-poverty-brief/0003-20261127T142319Z-repro.json: The R and Python environments are not pinned. (P2; fix: record the R dependencies in `renv.lock` and the Python environment in a lockfile)
  - .cg-docs/verification.md:28-33: The outputs map omits the notes file written by the pipeline. (P1; fix: add `output/notes.txt` to the map or write temporary material outside the project)
note: The repro, pipeline and render commands were not rerun because they write outputs. The typed-number entries were assessed as manually authored report content; dataset files remained closed, so their values were not compared with the prose. The unsorted listing was flagged because it reaches the notes output.

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
  - .cg-docs/plans/2026-11-27-poverty-brief.md:56: The bootstrap slice specifies no seed for its draws. (P1; fix: set a fixed seed in `pipeline.py` before sampling)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:57: The regional table and report require the agent to transcribe results. (P1; fix: have `pipeline.py` write the table and have `report.qmd` read it during rendering)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:58: The brief requires manual copying and a clock-dependent filename. (P1; fix: generate the document from `output/ci.csv` in the pipeline and use a fixed filename or a date supplied as an input)
note: No pipeline or reproducibility check was run at the plan stage; interpretation and choice of method were left alone.

[exit code: 0]
