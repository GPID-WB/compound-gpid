# The determinism lens on its planted project, third run

Run on `1b66979c` (task 2.8 as reviewed, item 55 of the handoff) from the installed core, for Codex and Kilo, and judged by the runner of that commit. Claude Code was left out while the account was at its Fable 5.2 limit. Each planted violation needs a finding of its own, matched one to one. Neither agent changed a file of the project.

| | Codex | Kilo |
|---|---|---|
| Plan and review stages, 26 checks | 23 | 22 |

Codex now flags the clock and points at the line of `regions = {` (S4 and S5 of item 55). It folded the clock and the
unsorted `glob.glob(` into one finding at `pipeline.py:40`, which the runner gives to one case; it put the fetch at the
line of the call, not of the address, and the unpinned environment at the record of `repro`, not at `renv.lock`.
Kilo flagged the listing and the fetch, but missed `date.today()` and put the unordered regions at the record of
`repro` again, though the lens now asks for the line. It also put the manual step at the work report, not at
`README.md`, and folded the Stata environment into a finding at the record.
