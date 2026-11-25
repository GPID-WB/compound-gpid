# Host matrix spike (task 0.1, issue #211)

Goal: replace assumptions about the four hosts with tested facts. Results go into `docs/adr/0001-host-matrix.md`.

Run this on one Mac and one World Bank Windows machine, in each host you use: Copilot (VS Code or Positron), Kilo, Claude Code, Codex. About ten minutes per host.

## Command-line part: one command

For Claude Code, Codex and the Kilo command line, the maintainer runs this from the repository root. It installs the test skills, asks each program the same four questions, saves the answers, and removes the test skills:

```
# macOS
python3 spike/host-matrix/run_cli_checks.py --kilo-model openai/gpt-6.2-sol

# Windows
py -3 spike\host-matrix\run_cli_checks.py --kilo-model openai/gpt-6.2-sol --report
```

The options are listed at the top of the script. `--report` writes a copy without local paths that can be committed. On Windows, [`WINDOWS.md`](WINDOWS.md) is a handoff an agent can follow from start to finish.

The build session then reads the results and fills in `docs/adr/0001-host-matrix.md`. The steps below are for the hosts that only run inside the editor (Copilot, and Kilo's editor panel).

## Editor part: Copilot and Kilo's panel

These two run only inside the editor, so a person does this part. The script prepares it and cleans up after it:

```
python3 spike/host-matrix/run_cli_checks.py --manual        # Windows: py -3 spike\host-matrix\run_cli_checks.py --manual
```

It installs the two test skills, makes a small test project named `cg-spike-project` in your home folder (with a marker line in `AGENTS.md`, `CLAUDE.md` and `.github/copilot-instructions.md`), and writes an answer sheet, `cg-spike-answers.txt`, also in your home folder.

1. Open the folder `cg-spike-project` in the editor. Restart the editor if the skills do not appear.
2. Open the answer sheet in a plain text program, not in the editor: the editor can show an open file to the agent, and the sheet holds the words the test looks for. For each host it lists four steps, each done in a new chat: paste the text, copy the reply under its heading. Nothing has to be run in a terminal.
3. Answer the three short questions per host at the end of its block.
4. Run the script again with `--manual-done`. It keeps the sheet with the results and removes the skills, the project and the sheet.

Two checks the sheet does not cover, for when there is time:

| Check | Record |
|---|---|
| In a long chat, after the host compacts or summarizes context, ask "is CG-SPIKE-POINTER still in your context?" | Yes or no |
| Copilot only: repeat step 2 on the smallest model your colleagues commonly pick | Did it follow all four steps? |

## Route A, the plugin marketplace (Claude Code, Codex, Copilot)

Needs the `v2` branch pushed with a manifest (task 1.1). Until then, record only whether your host lets you add a GitHub repository as a marketplace at all:

| Host | How | Record |
|---|---|---|
| Claude Code | `/plugin marketplace add addyosmani/agent-skills` | Allowed or blocked, and the error text |
| Codex | `codex plugin marketplace add addyosmani/agent-skills` | Allowed or blocked |
| Copilot in VS Code | Command Palette, "Chat: Install Plugin from Source", any public plugin repository | Allowed or blocked |

Remove the test marketplace afterwards.

## Duplicates

This Mac has 45 skills present in both `~/.agents/skills` and `~/.claude/skills`. In each host, type `/` and note whether one of those shared skills appears once or twice. That tells us which hosts read both folders.

## Kill criteria

- If a host cannot run a script from a skill folder without the user approving every call, the launcher design in the plan changes before M1.
- If `disable-model-invocation` is ignored on a host, `/cg` needs a description that cannot fire by accident on that host.
- If user-level skills in `~/.agents/skills` are not discovered by Copilot, Codex or Kilo, the primary install route changes.
- If always-loaded instructions are dropped after compaction, the guide must re-run `cg.py status` at the start of every turn that touches active work.
