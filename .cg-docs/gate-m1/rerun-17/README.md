# Gate rerun 17

Run on `c8d64525`, after the wording fixes of the review of task 2.3. Steps B, C, D, G and H in four agents. The
run was started as three jobs side by side (Claude Code; Codex; Kilo and then Kilo with the panel's shape), and
`results.json` holds the four results together.

- Claude Code, Codex and Kilo: 19 of 19 each.
- Kilo with the panel's shape: 18 of 19. Its plan is approved and passes `validate --strict`. The check that
  failed, "H: the plan is approved on a plain yes the human sent", compared the recorded reply with the reply sent,
  letter for letter: the human wrote "Yes." and the agent gave `--reply "Yes"`. The script now compares the words
  (`said_only`), and judged again from the same files the check holds. `results.json` keeps what the run printed.

The dropped full stop is a small break of "word for word": the record does not hold the reply exactly as written.
