---
name: setup
derived-from: "mattpocock/skills@d653911:skills/engineering/setup-matt-pocock-skills/SKILL.md; addyosmani/agent-skills@e997ac5:skills/context-engineering/SKILL.md; cursor/plugins@ca782ed:pstack/skills/poteto-mode/playbooks/feature.md; v1:.github/prompts/cg-setup.prompt.md"
---

# Setup

**You own getting this project ready for the guide: explore, propose, confirm, then write.** Until the human confirms, you only read. You open no data file at any point in this playbook.

Setup can be run again at any time. Every step works from what exists and changes only what differs.

## 1. Explore

Read, and write nothing. Look things up instead of asking (P2).

1. **State.** Keep the status output the guide already has: the project root, `core`, `git`. Run `"<python>" "<cg>" packs --json` to see the packs installed on this machine, and the folder of each pack's lead skill (`path`).
2. **Files.** List the project's files: `git ls-files --cached --others --exclude-standard` in a repository (tracked and new files, without ignored ones), otherwise a listing of the folder without hidden and vendored folders. Count the files by extension.
3. **Packs the files call for.** `core` is always on the list. Add a pack only for files you found.

   | Files found | Pack |
   |---|---|
   | `.R`, `.r`, `.Rmd`, `.qmd`, `DESCRIPTION`, `renv.lock` | `lang-r` |
   | `.do`, `.ado` | `lang-stata` |
   | `.py`, `.ipynb`, `pyproject.toml` | `lang-python` |

4. **How outputs are made.** Look for the one command that produces the outputs from the inputs, and for the checks the project already has: `_targets.R`, a `Makefile`, a main script or do-file, `tests/`, `DESCRIPTION`, a lockfile. Read them. Do not run them.
5. **Pack settings.** For each pack on the list that is installed, read its lead skill for the settings it reads and their defaults. Find the value the project's code already shows: for a dialect, which packages the scripts load.
6. **Data.** Note which data files exist, by name and count only (`.dta`, `.csv`, `.parquet`, `.rds`, `.fst`, `.xlsx` and the like). Their classification is not known yet, so they are restricted data (P12). Do not open, print or summarize them.
7. **What is already here.** `AGENTS.md`, `CLAUDE.md`, a block between the markers `cg:start` and `cg:end`, `.cg-docs/`, `GLOSSARY.md`, and version 1 files (`compound-gpid.md`, `compound-gpid.local.md`). Artifacts from version 1 are read as they are. This playbook does not convert, edit or delete anything from version 1.

## 2. Propose

Put one proposal to the human, in this order. Give each part with what you found that supports it, and lead with the answer you recommend so the human can accept it in a word.

1. **Packs** this project expects, and for each one whether it is installed on this machine.
2. **Pack settings**, each with the value you recommend and the lines of code that show it. Where the code shows nothing, recommend the pack's default and say that it is the default.
3. **Verification profile** (P4), as a draft: the Run command, the Doctor command, and each output you could identify with what would prove it right. Where you found nothing, write "not found". Do not guess a command.
4. **Data rules** (P12). Only the human can state these three; you cannot look them up, and you do not judge the answers:
   - the names of the organization's classification levels, from public to most restricted;
   - the highest level this coding agent is approved for;
   - who to ask about the use of AI, about security and about personal data. P12 lists the defaults for World Bank Group staff.

   When the human does not know an answer yet, that item is recorded as open. While it is open, every dataset is treated as restricted data.
5. **Every file you will write or change**, by path, from section 4.

State the assumptions you made. Then end your turn.

## 3. Confirm

Only a clear yes is approval (P2). A correction is not a yes: change the proposal, show the part that changed, and ask again. "Sounds good" and "whatever you think" call for a question about what is unclear.

## 4. Write

Write what was confirmed and nothing else, in the project root.

1. **`.cg-docs/config.json`.** Keep every key that is already there. Set these:

   ```json
   {
     "packs": ["core", "lang-r"],
     "requires-core": "<the core version that status printed>",
     "settings": {"<pack>": {"<setting>": "<value>"}},
     "classification-levels": ["<level>", "<level>"],
     "approved-tools": {"<this coding agent, as the human names it>": "<highest level it is approved for>"},
     "contacts": {"ai-use": "<who>", "security": "<who>", "personal-data": "<who>"}
   }
   ```

   `cg.py status` reads the first three: `packs` is a list of names, `requires-core` is a version, and `settings` holds one object per pack with text values. Leave out a data key the human could not fill.
2. **`.cg-docs/verification.md`**, from `templates/verification.md`, filled with the confirmed draft. Its status stays `draft` until the Run command has been run from start to finish.
3. **`AGENTS.md`.** Copy `templates/pointer-block.md` as it is, markers included. If the file already has a block between `cg:start` and `cg:end`, replace that block. Otherwise add the block at the end, or create the file. Change nothing outside the markers.
4. **`CLAUDE.md`.** Make sure it holds the line `@AGENTS.md`. Create the file with that one line if it is missing. Write the pointer block in no other file, and write nothing into `.github/copilot-instructions.md`: one coding agent loads all three files and would read the block twice.
5. **`.Rbuildignore`**, only in an R package (a `DESCRIPTION` file in the root). Make sure it holds `^\.cg-docs$`, `^AGENTS\.md$` and `^CLAUDE\.md$`, so the package check does not report these files.

Commit nothing unless the human asks.

## 5. Check

Run status again, as section 1 of the guide says. It must print `phase: ready` and `stops: none`. If it does not, show the output and fix the file it names before you reply.

**Reply:** what you found (files by language, how outputs are made, data files by count), what the human confirmed, each file written or changed, the status lines that show `phase: ready`, the `settings` line of status, any pack still to add with its add command, and what stays open (a draft verification profile, data rules not yet stated). If the human gave a request together with `/cg`, say that setup is done and continue with section 3 of the guide.
