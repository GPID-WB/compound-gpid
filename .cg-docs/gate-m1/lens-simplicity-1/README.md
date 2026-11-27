# The simplicity lens on its planted project, first run

Run on `bdbfc8c3` (the first half of task 2.8, before its review) with
`evals/planted/run_planted.py --verifier simplicity`, for Codex and Kilo, and judged by the runner of that commit.
Claude Code was left out while the account was at its Fable 5.2 limit. Each planted violation needs a finding of its
own, matched one to one.

| | Codex | Kilo |
|---|---|---|
| Plan stage, 6 checks (3 planted) | 6 | 6 |
| Review stage, 8 checks (5 planted) | 4 | 7 |
| Changed a file of the project | no | no |

**The planted project contradicts the lens.** Three review-stage cases are code that the planted plan asks for, in
slices the human approved: S2 (an option to scale the shares, the unused argument of `by_region`), S3 (the check
`if LINE < 0:`) and S4 (the check laid out again, `EXPECTED = 52 / 110`). Both agents flagged the three slices at the
plan stage, as they should. At the review stage the lens says to leave "a design the human chose in the plan", and
its row for a change that only tidies says to leave it when "the plan asked for that layout". Codex did so and gave
that reason in its note. Kilo flagged them anyway, which the runner counted as caught. The review-stage cases need
code that no slice asks for, or a plan without those slices; that is for the review of task 2.8.

Codex's one miss the lens does not explain is `members`, a function with one caller, which it judged to name a step
of its own. Kilo missed the check `if LINE < 0:`, for which code has no rule.
