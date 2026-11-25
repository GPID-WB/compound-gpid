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
