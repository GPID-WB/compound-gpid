# The verification lens on its planted project, second run

Run on `b2bdaae3` (task 2.8 built, before its review) from the installed core, for Codex and Kilo, and judged by the runner of that commit. Claude Code was left out while the account was at its Fable 5.2 limit. Each planted violation needs a finding of its own, matched one to one. Neither agent changed a file of the project. The review of task 2.8 (item 55 of the handoff) reads these runs; its findings are named below. The lens and code changed since run 1: the verifier traces each reported number back to the line that computes
it, and `evidence --rerun` has the rule `unbacked` for a claim of validation that names no record.

| | Codex | Kilo |
|---|---|---|
| Review stage, 13 checks | 13 | 11 |

Codex caught every case, the number that measures something else and the claim of validation among them. Kilo
flagged the filter on the weight at `pipeline.py:11`, a line above it, and the runner gave that finding to another
case. The runner now gives a finding within three lines of a case's line only to such a case (S8); judged again, Kilo
still misses 2, now named as C4 and the expected value computed the same way as the output, as in run 1.
