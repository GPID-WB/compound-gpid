# Gate rerun 21

Run on `44f5eda4`, the task 2.5 text before its review, for Codex and the two Kilo shapes, one after the other.
Claude Code was left out: the account had reached its Fable 5.2 limit, and the gate starts Claude Code with the
account's default model. Steps B, C, D, X, G, H and W, with the two new checks of task 2.5 (each verifier gave a
verdict, with its kind of review).

- Codex: 33 of 33. Every verdict is recorded as an independent review. At the plan stage 14 of 16 verdicts passed,
  one flagged and one flag had no proof (recorded as `UNVERIFIED`); at the review stage 6 of 9 verifiers flagged.
  The plan was approved and the work completed with those flags open: nothing in code acts on a flag until tasks
  2.9 and 2.10.
- Kilo with the panel's shape: 33 of 33.
- Kilo: 30 of 33. Its own plan declared two checks that could not pass on the machine: one needed the package
  installed and the plan never installed it, and `R CMD check .` needs LaTeX, which the machine lacks. The agent
  verified the first slice, left the approved checks and the files outside the slice alone, kept the work report in
  progress and asked for an amendment, as the playbook says. The script's human can only say "go on", so the work
  never reached its close and no verifier of the review stage ran. `R CMD check .` also wrote a `..Rcheck` folder
  into the project, which `guard` counted as a change outside the slice. Task 2.6 took both points (item 42).
