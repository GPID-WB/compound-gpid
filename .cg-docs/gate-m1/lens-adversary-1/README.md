# The adversary lens on its planted project, first run

Run on `bdbfc8c3` (the first half of task 2.8, before its review) with
`evals/planted/run_planted.py --verifier adversary`, for Codex and Kilo, and judged by the runner of that commit.
Claude Code was left out while the account was at its Fable 5.2 limit. Each planted violation needs a finding of its
own, matched one to one, and each finding stands only at the record of a probe that failed.

| | Codex | Kilo |
|---|---|---|
| Review stage, 8 checks (4 planted) | 8 | 7 |
| Listed what it dropped | yes | yes |
| Changed a file of the project | no | no |

Kilo missed one planted fault: a negative welfare is counted as poor and the run goes on (`"welfare":
float(row["welfare"])` in `pipeline.py`). Both agents found the household at the line, the missing weight read as 0
and the household whose region has no name, each by a probe that failed through `cg.py evidence --run`.
