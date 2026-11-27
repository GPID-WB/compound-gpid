# The verification lens on its planted project, first run

Run on `c518b463` (task 2.7 as reviewed) with `evals/planted/run_planted.py --verifier verification`, for Codex and
Kilo. Claude Code was left out while the account was at its Fable 5.2 limit. Each planted violation needs a finding
of its own, matched one to one.

| | Codex | Kilo |
|---|---|---|
| Review stage, 9 planted | 7 | 6 |
| Reran every check of the plan itself | yes | yes |
| Changed a file of the project | no | no |

Both missed the two violations that are the point of this verifier:

- **A number that measures something else.** `pipeline.py` drops each row whose weight is 0 (`if row["weight"]`),
  so the headcount is of people with a weight, not of the population. The lens asks "what else could this number be
  measuring?", and neither agent traced the reported number back to the line that computes it.
- **A claim of validation with no record.** The work report says the result "matches the figure", and no check or
  record stands behind it. Code's rule finds a claim that names a check; this one names none.

Kilo also missed an expected value computed the same way as the output (`expected = headcount(` in
`checks/headcount.py`). The second half of task 2.8 takes the first two: a lens wording that makes the verifier
trace each reported number to the line that computes it, and a code rule for a claim of success with no record.
