# Working in this repository

This branch, `v2`, builds Compound GPID 2.0. Read `docs/v2/HANDOFF.md` first: it gives the state of the build, the order to read things in, and the working rules.

The block below is the pointer block that setup writes into every project (`packs/core/cg/templates/pointer-block.md`). It is here so that this repository is built with `/cg` from task 1.7 on. A test keeps the two copies the same.

<!-- cg:start (written by Compound GPID setup, which replaces what is between these two markers) -->
## Compound GPID

This project is run with Compound GPID. The record of the work is in `.cg-docs/`, never in the conversation.

- Before you change a file in a new session, see where the work stands. Read `~/.cg/launcher.json` and run `"<python>" "<cg>" status --project "<this folder>"` with the two paths it holds (in PowerShell, put `&` first). If that file is missing, say that Compound GPID is not installed on this machine, and carry on.
- Only the guide opens a playbook or writes a work report, and the human starts it by typing `/cg`. When they ask for a change in a message that holds neither `/cg` nor `$cg`, begin your first reply in the conversation with this sentence: "`/cg` would run this change with checks and a record." Then do what they asked.
- Never infer an approval from an earlier conversation. The project's `GLOSSARY.md`, when it has one, fixes its words.
<!-- cg:end -->

## ClickUp

This project is bound to the ClickUp task [Compound GPID](https://app.clickup.com/t/868hrz0p4) by `.clickup/project.json`. When that file exists, load the ClickUp project and task skills (`clickup-bind-project`, `clickup-work-task`, `clickup-github`) before task work. Verify the bound task and route CLI/MCP operations before writing.

- Each v2 milestone is a subtask of that task, and each task of a milestone (0.1, 1.1, ...) is a subtask of its milestone. Each one links to its GitHub milestone or issue, and the GitHub side links back.
- Review these subtasks whenever the state of the work changes: a task starts, is built, is reviewed, waits on the maintainer, or is accepted; a date moves; or the scope changes. Update the status, the dates and the description, and add a comment to the activity that says what changed and why, with links to the commits, pull requests and branch.
- When new work appears, open its GitHub issue first (label `v2`, the right milestone), then add a subtask under its milestone, with the same links both ways. Do not wait to be asked.
- Statuses: `to do`, `in progress`, `in review` (finished, waiting for the maintainer's acceptance and the close of the issue) and `done` (accepted and closed). Do not use `backlog` for v2 work. Assign v2 subtasks to the maintainer.
- Dates are tentative. When one moves, change it in ClickUp and say why in a comment.
