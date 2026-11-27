# Gate rerun 23

Run on `6e57ae1c`, task 2.6 as reviewed, for Codex and the two Kilo shapes, one after the other. Claude Code was
left out while the account was at its Fable 5.2 limit. Step W now asks that `cg.py repro` ran on the work.

- Codex: 34 of 34, `repro` included.
- Kilo: 30 of 34. Its plan put the tests in slice S1 and the function they test in slice S2, so S1's checks could
  pass only after S2. The agent ran them, saw them fail for the missing function, stopped as the plan's order told
  it to, and asked for an amendment. The script's human cannot give one, so the close of the work, the verifiers of
  the review stage and `repro` were never reached. The review of task 2.7 changed `plan.md` step 4 for this (V9).
- Kilo with the panel's shape: 31 of 34. R's help generator rewrote two help files that the slice did not list;
  `guard` named them, and the agent stopped and asked for an amendment, which the script's human cannot give.

In three of the last four runs the work step stopped on a weakness of the agent's own plan, which the plan-stage
verifiers had passed. The agent stopped rightly each time; the gate has no step in which the human approves an
amendment.
