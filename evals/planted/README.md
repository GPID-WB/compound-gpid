# Planted violations

Each folder here holds the planted violations of one verifier (plan, section 4.3: "a verifier that misses its planted violation fails CI"). Task 2.6 (#229) made the first, `determinism/`; task 2.15 adds one for every other verifier. ADR 0009 gives the choices.

## A folder

- `project/`: the files of a small analytical project, with each violation planted in it. Nothing in its files says where a violation is: the verifier reads them as it would read real work.
- `verification.md`: the project's verification profile, which the runner copies to `.cg-docs/verification.md`.
- `plan.md`: a draft plan with the violations of the plan stage planted in it.
- `expected.json`: each case, the stage it belongs to, the file and the line text where it shows, the places a finding may also point at, and the rule of `cg.py repro` that finds its part, or `null` when only judgement can.

## Two parts

- **What code finds** runs in CI: `tests/core/test_determinism.py` copies `project/` and holds `cg.py repro` to each case whose `code` is a rule.
- **What is judged** needs a model reading the lens, and CI cannot start one. `run_planted.py` builds the project as the work leaves it, prints the kickoff code gives the verifier, starts a coding agent on it with approval prompts off, and judges the verdict block from the files. Run it after `install.py --update`, since it uses the installed core:

  ```
  python3 evals/planted/run_planted.py --verifier determinism --only claude,codex,kilo --kilo-model openai/gpt-6-luna
  ```

  `--dry-run` builds the copies in `~/temp/cg-lens` and prints each kickoff, and starts no agent. The transcripts and `results.json` go to `~/temp/cg-lens/out`, or to `--out`.
