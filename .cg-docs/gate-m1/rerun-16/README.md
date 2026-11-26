# Gate rerun 16: stopped after two agents

Run on `c9051e07`, the first run with step H (the plan). It was stopped by hand after Claude Code and Codex,
because the review of task 2.3 had changed the wording under test by then; rerun 17 covers all four agents.
`results.json` was written from the script's log for the two agents that finished.

- Codex: 19 of 19.
- Claude Code: 18 of 19. In step H its draft plan waited for a number from the human, the expected value of the
  new measure, marked `VALUE-PENDING`. The script's human could only say "Yes.". The agent took that neither for
  the number nor for an approval, and the plan stayed a draft. `cg.py validate --strict` called that plan complete,
  which the review fixed (`2dfcfc49`), and the script's human now says that it has no figure to give.
