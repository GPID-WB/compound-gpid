# The adversary lens on its planted project, third run

Run on `77851d88` (task 2.9 as built, with its follow-up 1 to the adversary lens) with
`evals/planted/run_planted.py --verifier adversary`, for Codex and Kilo, from the installed core. Claude Code was
left out while the account was at its Fable 5.2 limit.

| | Codex | Kilo |
|---|---|---|
| Review stage, 8 checks (4 planted) | 8 | 8 |
| Listed what it dropped | yes | yes |
| Changed a file of the project | no | no |

Both agents found the four planted faults, each at a probe that failed: the household at the line counted as poor,
the missing weight read as 0, the negative welfare counted as poor, and the household whose region has no name left
out of the national figure. In run 2 (on `1b66979c`) Kilo stopped after two probes, reading "three rounds at most"
as a bound on its probes; here it ran eleven. Follow-up 1 of task 2.9 holds for this project.
