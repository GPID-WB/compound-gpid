# The determinism lens on its planted project, first run

Run on `6e57ae1c` (task 2.6 as reviewed) with `evals/planted/run_planted.py --verifier determinism`, for Codex and
Kilo. Claude Code was left out while the account was at its Fable 5.2 limit. Each planted violation needs a finding
of its own, matched one to one.

| | Codex | Kilo |
|---|---|---|
| Plan stage, 3 planted | 3 | 2 |
| Review stage, 19 planted | 16 | 16 |
| Changed a file of the project | no | no |

Both missed a `date.today()` that changes the output, which `cg.py repro`'s own search names (the clock): the
verifier had code's finding in the record and did not carry it into its verdict. Codex also missed an unsorted
`glob.glob` and a download with no saved copy; Kilo missed the Stata draw, the Stata version line and one unseeded
step in the plan. A lens should say that the verifier accounts for each finding of code, as kept or as set aside.
