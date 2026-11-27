# Gate rerun 24

Run on `c7aefa6e`, task 2.8 as reviewed, before task 2.9, for Codex and the two Kilo shapes, one after the other.
Claude Code was left out while the account was at its Fable 5.2 limit. Step W now approves an amendment on a plain
"Yes." and asks for the records of `scope` and `claims`.

- Codex: 39 of 39.
- Kilo: 39 of 39.
- Kilo with the panel's shape: 35 of 39. Its adversary found that `poverty_gap()` takes a negative welfare (P0).
  The agent judged it could not fix that inside the approved plan and asked whether to amend it (turn W3). From W4
  to W8 it drafted an amendment, ran the plan verifiers on each draft, met new findings, and revised again. Two
  turns hit the 1,200-second limit. The script ran out of turns with the amended plan not approved and the work
  report in progress, so the four checks on the close of the work and on the amendment failed.

**An approval recorded on text the human never saw.** In turn W7 the human's only words were "Yes.", given to the
agent's question whether it might revise the plan. In the same turn the agent rewrote the decided intent twice and
recorded that "Yes." against each new text (approval records at 17:16 and 17:20). The guide says a yes is approval
"for what was shown and nothing more". `cg.py approve` cannot see the conversation, so no code refused it. No check
of the gate looks at an intent approved after step G, so none failed for it.

`repro` refused once in the panel's run: its verification profile named a source file, `R/read_survey.R`, as an
output, and that file had uncommitted changes. Options 3 and 5 of #230 would still refuse there, because the file
is no output of a run.

The transcripts were cleaned by the sanitizer of `d2eafc91`. The only addresses left are public pages that the
agents fetched.
