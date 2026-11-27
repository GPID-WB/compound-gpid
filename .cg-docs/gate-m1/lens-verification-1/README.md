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

Read again on 2026-11-27, in task 2.8 (#231), second half (ADR 0012). The counts stand, and two of the cases named
as missed do not. Codex flagged the filter on the weight at its line (`pipeline.py:12`), and Kilo the claim of
validation at its line. Each had folded the two cases of C5, a check that never ran and a claim that it passes, into
one finding, and the runner, which matched findings and cases one to one within three lines or a place under "or",
gave the finding at the right line to the case beside it. So Codex missed the claim of validation, which only its
note names, and Kilo the filter on the weight. A finding at the line of a case now catches that case alone. The two
points still hold, and the second half of task 2.8 takes both.
