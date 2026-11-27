# The contract lens on its planted project, first run

Run on `b2bdaae3` (task 2.8 built, before its review) from the installed core, for Codex and Kilo, and judged by the runner of that commit. Claude Code was left out while the account was at its Fable 5.2 limit. Each planted violation needs a finding of its own, matched one to one. Neither agent changed a file of the project. The review of task 2.8 (item 55 of the handoff) reads these runs; its findings are named below.

| | Codex | Kilo |
|---|---|---|
| Plan and review stages, 13 checks | 12 | 12 |

Codex flagged the poverty gap that the contract puts out of scope at `pipeline.py:30`, the line that writes it, which
was outside the runner's window for `def gap(`; judged again by the runner of `61a48293`, it is 13 of 13 (S8).
Kilo missed the plan-stage case "the wrong result of the intent, with no check that fails on it"; its finding there
named a point that is not a planted case (S13).
