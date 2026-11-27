# Planted violations

Each folder here holds the planted violations of one verifier (plan, section 4.3: "a verifier that misses its planted violation fails CI"). Task 2.6 (#229) made the first, `determinism/`, task 2.7 (#230) the second, `verification/`, and task 2.8 (#231) `adversary/`, `simplicity/`, `contract/` and `claims/`; task 2.15 adds one for every other verifier. ADR 0009 to ADR 0012 give the choices.

## A folder

- `project/`: the files of a small analytical project, with each violation planted in it. Nothing in its files says where a violation is: the verifier reads them as it would read real work.
- `verification.md`: the project's verification profile, which the runner copies to `.cg-docs/verification.md`.
- `plan.md`: a draft plan with the violations of the plan stage planted in it. Where the plan the human approved must differ from the one the plan stage judges, as in `simplicity/`, whose approved plan asks for none of its review cases, `draft.md` is the plan that the plan stage judges, which `"draft"` in `expected.json` names.
- `expected.json`: each case, the stage it belongs to, the file and the line text where it shows, the places a finding may also point at, and the rule of code that finds its part, or `null` when only judgement can. `@plan`, `@report` and `@profile` stand for the plan, the work report and the verification profile of the built project.
- For work on an approved plan, as in `verification/`: `intent.md`, which the runner approves with the plan; `report.md`, the body of the work report; and under `work` in `expected.json`, each slice with the checks the work ran and what its files held then.
- For a change on a commit, as in `simplicity/` and `claims/`: `before/`, the project at the commit the work began on, which the runner commits before it puts `project/` in its place.
- `"scope": true` or `"claims": true` in `expected.json` has the runner run that command of `cg.py` once every slice is done, as the work playbook does.
- For the adversary: under each case of `expected.json`, a `probe` that fails on the planted fault, which CI runs and the agent never sees, and a `decoy` whose probe passes.

## Two parts

- **What code finds** runs in CI: `tests/core/test_determinism.py` copies `project/` and holds `cg.py repro` to each case whose `code` is a rule, `tests/core/test_verification.py` builds the work as the runner does and holds `cg.py evidence --rerun` to each of its own, `tests/core/test_adversary_and_simplicity.py` runs each probe of the adversary and holds `cg.py conformance` and `cg.py scope` to theirs, and `tests/core/test_contract_and_claims.py` holds `cg.py claims` to the cases of `contract/` and `claims/`, and to naming nothing else.
- **What is judged** needs a model reading the lens, and CI cannot start one. `run_planted.py` builds the project as the work leaves it, prints the kickoff code gives the verifier, starts a coding agent on it with approval prompts off, and judges the verdict block it returns, with the files: each case needs a finding of its own, a finding at the line of a case catches that case alone, and one within three lines of it catches such a case and none that allows its file under `or`. For `verification/` it also asks that the verifier reran every check of the plan itself. For `adversary/` a case is caught only by a finding at a run of the verifier's turn that failed and that names the line of the fault, and the block lists what was dropped. Run it after `install.py --update`, since it uses the installed core:

  ```
  python3 evals/planted/run_planted.py --verifier determinism --only claude,codex,kilo --kilo-model openai/gpt-6-luna
  ```

  `--dry-run` builds the copies in `~/temp/cg-lens` and prints each kickoff, and starts no agent. The transcripts and `results.json` go to `~/temp/cg-lens/out`, or to `--out`.
