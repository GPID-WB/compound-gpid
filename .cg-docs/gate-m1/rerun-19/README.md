# Gate rerun 19

Run on `97325a71`, after the work that followed the review of task 2.4. Steps B, C, D, X, G, H and W, one agent after
the other.

- Claude Code and Codex: 30 of 30 each. This is the first run in which an agent goes through every step on one
  wording: setup, quick work with its record in `cg.py evidence`, a plain request, an action that cannot be undone,
  the brainstorm, the plan with its open questions, and the work on the plan.
- Kilo: 21 of 30. Asked for a plan, it read status, saw `open-artifacts: 0`, and said that no decided brainstorm
  existed. One did: a decided intent is closed, so no line of status showed it. No plan was written, so steps H and W
  failed together. Status now names each decided intent that no plan is built on yet (`ready-to-plan`, `2e42949d`).
- Kilo with the panel's shape: 23 of 30. After the human's yes to the setup it wrote nothing and said that typing
  `/cg` resumes setup. Setup was then written in step C, without the data rule the human had stated. From there:
  - the agent asked for the classification or for a decision to read the file, got "Yes, proceed.", and passed that
    reply to `cg.py approve --reads`, which recorded it: a plain yes to a question that offered two answers;
  - after the yes to the contract it ran `tier` again, which opened a new stop, and the script's three yeses were used
    up before any function was written;
  - in step W the work stopped on a check of its own plan that failed and on what `guard` found, and the agent left
    the work report in progress and said so. That is the playbook working, and the work is not done.

What this run leaves to do: a rerun of the two Kilo shapes with `ready-to-plan`; a sentence that tells the agent to
judge whether a reply answers the question it asked before it passes the reply to `approve`; and the maintainer's
open point on whether a second `tier` run with the same result opens a new stop.
