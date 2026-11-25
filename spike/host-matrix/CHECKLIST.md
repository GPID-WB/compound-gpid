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

## Setup, once per machine

Route B, the user-level folder:

```
# macOS
mkdir -p ~/.agents/skills && cp -R spike/host-matrix/skills/cg-spike-* ~/.agents/skills/

# Windows PowerShell
New-Item -ItemType Directory -Force "$HOME\.agents\skills" | Out-Null
Copy-Item -Recurse spike\host-matrix\skills\cg-spike-* "$HOME\.agents\skills\"
```

Then open any test project that has a file `AGENTS.md` containing the line `CG-SPIKE-POINTER`. For Claude Code, put the same line in `CLAUDE.md`. Restart the host.

## Tests, per host

| # | Do this | Record |
|---|---|---|
| 1 | Type `/` and look for `cg-spike-hello` | Listed? Under what exact name? Listed twice? |
| 2 | Run `/cg-spike-hello` | Paste the reply: script output, Python command that worked, number of approval prompts, the four answers |
| 3 | In a new chat, write "I saw a purple heron today" | Did `cg-spike-auto` fire? |
| 4 | In a new chat, write "run the host probe" without a slash | Did `cg-spike-hello` run by itself? It should not (`disable-model-invocation`) |
| 5 | Is `cg-spike-auto` also offered as a slash command? | Yes or no |
| 6 | In a long chat, after the host compacts or summarizes context, ask "is CG-SPIKE-POINTER still in your context?" | Yes or no |
| 7 | Copilot only: repeat test 2 on the smallest model your colleagues commonly pick | Did it follow all four steps? |

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

## Cleanup

Delete `~/.agents/skills/cg-spike-hello` and `~/.agents/skills/cg-spike-auto`.
