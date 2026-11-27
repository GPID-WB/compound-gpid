# The adversary lens on its planted project, second run

Run on `1b66979c` (task 2.8 as reviewed, item 55 of the handoff) from the installed core, for Codex and Kilo, and judged by the runner of that commit. Claude Code was left out while the account was at its Fable 5.2 limit. Each planted violation needs a finding of its own, matched one to one. Neither agent changed a file of the project.

| | Codex | Kilo |
|---|---|---|
| Review stage, 8 checks (4 planted) | 7 | 6 |

Each finding of both agents points at a probe of its own turn. Codex probed all four planted faults and one more, but
put the negative welfare at `pipeline.py:33`, not at line 11 where welfare is read, and three lines from the case at
line 36 (`<=`), which its own finding had taken, so the runner gave it to no case. Kilo probed two faults and stopped: its note says "The kickoff permits at most three
rounds; two probes reproduced contract violations." It read the bound on rounds as a bound on probes, and left the
missing weight and the negative welfare unprobed. The lens should say that one round holds as many probes as the
contract needs.
