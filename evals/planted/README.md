# Planted violations

Each folder here holds the planted violations of one verifier (plan, section 4.3: "a verifier that misses its planted violation fails CI"). Task 2.6 (#229) made the first, `determinism/`, and task 2.7 (#230) the second, `verification/`; task 2.15 adds one for every other verifier. ADR 0009 and ADR 0010 give the choices.

## A folder

- `project/`: the files of a small analytical project, with each violation planted in it. Nothing in its files says where a violation is: the verifier reads them as it would read real work.
- `verification.md`: the project's verification profile, which the runner copies to `.cg-docs/verification.md`.
- `plan.md`: a draft plan with the violations of the plan stage planted in it.
- `expected.json`: each case, the stage it belongs to, the file and the line text where it shows, the places a finding may also point at, and the rule of code that finds its part, or `null` when only judgement can. `@plan`, `@report` and `@profile` stand for the plan, the work report and the verification profile of the built project.
- For work on an approved plan, as in `verification/`: `intent.md`, which the runner approves with the plan; `report.md`, the body of the work report; and under `work` in `expected.json`, each slice with the checks the work ran and what its files held then.

## Two parts

- **What code finds** runs in CI: `tests/core/test_determinism.py` copies `project/` and holds `cg.py repro` to each case whose `code` is a rule, and `tests/core/test_verification.py` builds the work as the runner does and holds `cg.py evidence --rerun` to each of its own.
- **What is judged** needs a model reading the lens, and CI cannot start one. `run_planted.py` builds the project as the work leaves it, prints the kickoff code gives the verifier, starts a coding agent on it with approval prompts off, and judges the verdict block it returns, with the files: each case needs a finding of its own. For `verification/` it also asks that the verifier reran every check of the plan itself. Run it after `install.py --update`, since it uses the installed core:

  ```
  python3 evals/planted/run_planted.py --verifier determinism --only claude,codex,kilo --kilo-model openai/gpt-6-luna
  ```

  `--dry-run` builds the copies in `~/temp/cg-lens` and prints each kickoff, and starts no agent. The transcripts and `results.json` go to `~/temp/cg-lens/out`, or to `--out`.
