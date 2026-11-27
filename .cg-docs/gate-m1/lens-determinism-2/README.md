# The determinism lens on its planted project, second run

Run on `b2bdaae3` (task 2.8 built, before its review) from the installed core, for Codex and Kilo, and judged by the runner of that commit. Claude Code was left out while the account was at its Fable 5.2 limit. Each planted violation needs a finding of its own, matched one to one. Neither agent changed a file of the project. The review of task 2.8 (item 55 of the handoff) reads these runs; its findings are named below. Since run 1 the lens says that the verifier accounts for each finding of code.

| | Codex | Kilo |
|---|---|---|
| Plan and review stages, 26 checks | 22 | 24 |

Codex accounted for each finding of `repro`, and set aside the clock (`date.today()`) and the unsorted
`glob.glob(` because their output "is not mapped for comparison", and the fetch over `https://` because the run does
not read the file. The lens limited those rows to an output that is compared and to an address the run reads; it now
says a file the run writes, mapped or not, and an address the run fetches (S5). Both agents found the unordered
`regions = {` in substance but pointed at the record of `repro`, as the lens then said; it now asks for the line of
code that writes the output in another order (S4). Kilo also missed `date.today()`.
