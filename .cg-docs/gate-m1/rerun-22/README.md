# Gate rerun 22

Run on `f2d3334c`, the task 2.5 text with the wording fixes of its review, for Codex and the two Kilo shapes, one
after the other. Claude Code was left out while the account was at its Fable 5.2 limit.

- Codex: 33 of 33.
- Kilo: 33 of 33. The plan whose checks could not run on the machine (rerun 21) did not come back.
- Kilo with the panel's shape: 26 of 33. Asked with `/cg` to add a function, it ran `status --guide --playbook work`
  on its own judgement although status had named `quick.md`, read that the work playbook needs an approved plan,
  changed nothing, and sent the human to `/cg plan`. Four checks of step C and three of step W followed from that.
  Since task 2.7, `--playbook work` names quick work when no plan is approved as it now reads.
