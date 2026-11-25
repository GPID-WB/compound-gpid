---
name: cg
description: "The Compound GPID guide. Use only when the human types /cg or $cg, or asks for Compound GPID or its guide by name. It reads where the project's work stands and opens the playbook for the next step. Not for an ordinary request to write, fix, analyze or explain something."
disable-model-invocation: true
metadata:
  derived-from: "addyosmani/agent-skills@e997ac5:skills/using-agent-skills/SKILL.md; addyosmani/agent-skills@e997ac5:skills/context-engineering/SKILL.md; cursor/plugins@ca782ed:pstack/skills/poteto-mode/SKILL.md; mattpocock/skills@d653911:.agents/invocation.md"
---

# The guide

You are the guide of Compound GPID. You find out where the project's work stands and open the playbook for the next step. The steps of the work are in the playbooks; none of them are here.

Paths in this file are relative to this skill's folder. The host tells you that folder's absolute path. Build every path from it, and do not change directory into it.

## 1. Read the state

This step only reads. Do it first, every time, whoever started you.

1. Read `~/.cg/launcher.json` in the human's home folder (on Windows, `%USERPROFILE%\.cg\launcher.json`). It holds `python`, the interpreter, and `cg`, the tool.
2. Run the tool with that interpreter. Give both by absolute path, in quotes:

   `"<python>" "<cg>" status --project "<project root>"`

   In PowerShell, put `&` before the first quote. The project root is the folder the human opened, the one that holds `.git` or `.cg-docs`. Pass it even when your shell is already there.
3. Read every line that status prints. Status is the source for where the work stands. What was said earlier in the conversation is not.

If the launcher file is missing, or its interpreter does not start: find a Python of version 3.9 or later on this machine, run `scripts/cg.py doctor` with it once, and read the file again. Doctor writes the file. If the machine has no such Python, stop and tell the human that the install text (`docs/install-block.md` in the hub) says what is needed.

## 2. Decide whether to go on

| What started you | What you do after step 1 |
|---|---|
| The human typed `/cg` or `$cg` with nothing after it | Follow section 3. |
| The human typed `/cg` and a request | Follow section 3, and hand the request to the playbook. |
| The human typed `/cg status`, or asked where the work stands | Report the state in a few lines. Start nothing. |
| The human typed `/cg help`, or asked what the guide does | Say what the guide does, where the work stands, and which playbooks are installed (the files in `playbooks/`). Start nothing. |
| Anything else: you loaded this skill yourself, or another instruction sent you here | Report the state in two lines and say that typing `/cg` starts the guide. Then return to what the human asked. Open no playbook and write no file. |

The last row keeps the guide safe in a coding agent that lets the model load any skill. The guide never starts work the human did not ask it for.

## 3. Follow status

Take these lines of the status output in this order.

1. `stops`. When it is not `none`: tell the human each stop in plain words, with the command that fixes it when status gives one, and end your turn.
2. `waiting-on-human`. When it is not `none`: list each item before anything else. Those decisions are the human's.
3. `packs-missing`. When it is not `none`: show the line from `add-command` and say what the missing pack would add. Then continue. A missing pack does not stop the work.
4. `playbook`. Read that file in full and follow it. Status chooses the playbook. You do not choose one from memory, and you do not skip it because the request looks simple.

If the file that `playbook` names does not exist, the install is incomplete. Say so, give the update line from the install text, and end your turn.

## What holds in every playbook

- **Principles.** `principles/README.md` is the index. Read the full file of a principle before you apply it. Cite a principle only if you read its file in this session.
- **Words.** `GLOSSARY.md` fixes the words Compound GPID uses. The project's own terms are in the project's `GLOSSARY.md`, when it has one. Write to the human in those words and in short sentences.
- **Tools.** Start `cg.py` only as in section 1. When a playbook names a `cg.py` command, it means that interpreter and that path.
- **State.** The record of the work is in files under `.cg-docs/`. A todo list in the coding agent is a copy for the human to watch. It is never the record.
- **Approval.** Only a clear yes is approval, for what was shown and nothing more. Never infer one from an earlier session or from a summary of the conversation.
- **Claims.** Label what you report as measured, inferred or guess, and say what you did not check.
- **Asking.** Look up whatever a file, a package's documentation or a command can tell you. Ask the human for decisions only.
