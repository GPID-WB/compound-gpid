# ADR 0001: Host matrix

Date: 2026-11-24. Status: **tested on macOS, not on Windows**. Claude Code, Codex and Kilo were run from the command line, and Copilot and Kilo in the editor. Windows is still open (issue #211).

## Purpose

Record what each coding agent host does, from tests, before the design depends on it. Each fact carries its basis:

- **live**: observed by running the host on the maintainer's Mac on 2026-11-24 with the script in `spike/host-matrix/` (now `run_cli_checks.py`). Claude Code, Codex and Kilo were run without a UI. Copilot and Kilo's panel were run by the maintainer in VS Code, from an answer sheet the script prepares (`--manual`).
- **docs**: read in the vendor's documentation on 2026-11-23. Not tested here.
- **inspected**: seen by reading files and folders. No host was run.

Versions run: Claude Code 2.1.331, Codex 0.171.0-alpha.13.2, Kilo 7.8.32 with the model `openai/gpt-6.2-sol`, and Copilot chat as built into VS Code 1.147.0, in agent mode. The models used in the two editor panels were not written down.

## Live results: command line

The two test skills were installed the way the `skills` installer already does it on this machine: a real folder in `~/.agents/skills` and a link to it from `~/.claude/skills`.

| Question | Claude Code | Codex | Kilo |
|---|---|---|---|
| Finds the skills | only in `~/.claude/skills`; a skill placed only in `~/.agents/skills` was not seen | only in `~/.agents/skills`; a skill placed only in `~/.claude/skills` was not listed | in both folders |
| Lists a skill twice | no | no | no |
| Honors `disable-model-invocation` | **yes**: the skill is hidden from the model and still runs when typed as `/cg-spike-hello` | **no**: the model saw the skill and ran it on a plain request | **no**: the model saw the skill and ran it on a plain request |
| Runs a skill typed as `/name` | yes | yes, as `$name` and as `/name` | yes |
| Loads a skill from its description | yes | yes | yes |
| Tells the model the skill's folder | yes ("Base directory for this skill: ...") | yes | yes |
| Runs the skill's script | yes, by absolute path; a `cd` into the skill folder was refused | yes, with the skill folder as working directory | yes, with the skill folder as working directory |
| Python command that worked | `python3` | `python3` | `python3` |
| Always-loaded instructions | `CLAUDE.md` only; `AGENTS.md` is loaded only when `CLAUDE.md` holds the line `@AGENTS.md` | `AGENTS.md` only | `AGENTS.md` only |
| Todo tool | none in this mode | none in this mode | `todowrite` |
| Subagent tool | `Agent` | `collaboration.spawn_agent`, on explicit request | `task` |

## Live results: in the editor

Same two test skills, link layout, in a test project with one marker each in `AGENTS.md`, `CLAUDE.md` and `.github/copilot-instructions.md`.

| Question | Copilot (agent mode) | Kilo's panel |
|---|---|---|
| Skill offered after typing `/` | yes, once | yes, once |
| Honors `disable-model-invocation` | **yes**: the model saw only the other skill, and `/cg-spike-hello` still ran | **no**: the model saw the skill and ran it on a plain request |
| Loads a skill from its description | yes | yes |
| Tells the model the skill's folder | yes | yes |
| Runs the skill's script | yes, after a `cd` into the skill folder | yes, with the skill folder as working directory |
| Always-loaded instructions | **all three files** | `AGENTS.md` only |
| Todo tool | a `todos` table reached through a tool named `sql` | `todowrite` |
| Subagent tool | `task` | `task` |
| Approval prompts seen for the script | none, with autopilot on, so the normal count is unknown | none |

Kilo's panel behaved as Kilo's command line did.

## Further findings


- **The import works.** With a `CLAUDE.md` that holds only `@AGENTS.md`, Claude Code loaded the marker from `AGENTS.md`. This was from documentation before; it is live now.
- **A hidden skill can be answered by the wrong one.** Asked "Please run the host probe", Claude Code could not see the user-invoked skill. In the first run it started the other test skill, although its description did not match. In the second run it started nothing and asked. Copilot did the same as that first run: it started the other test skill. This happens on both hosts that honor the flag.
- **Kilo depends on the model chosen.** Kilo's default model on this machine could not call tools, and every prompt stopped. A model name that starts with `kilo/` is billed to the Kilo account and stopped for lack of credits. `openai/gpt-6.2-sol`, through the maintainer's own subscription, worked. Skill discovery is the host's doing, but whether a skill runs depends on the model.

- **The script once pointed Kilo at the wrong project.** In one run Kilo reported that the test project's `AGENTS.md` was not loaded. The script had set the working folder but left the `PWD` variable on this repository. After the fix Kilo loaded the marker again, so Kilo takes its project from `PWD`. Anything that starts Kilo from code must set both.
- **An agent may hunt for a skill it was not given.** With the test skill only in `~/.claude/skills`, Codex did not list it. Asked for it by name, the model searched the home folder, found the file there, and ran it. A leftover copy of a skill is therefore not harmless.

## What this changes in the design

1. **One pointer block, in `AGENTS.md`, imported by `CLAUDE.md`.** Codex, Kilo and Copilot read `AGENTS.md`. Claude Code reads `CLAUDE.md` and follows the import line. Setup writes the block once in `AGENTS.md` and makes sure `CLAUDE.md` holds `@AGENTS.md`. Copilot loads `AGENTS.md`, `CLAUDE.md` and `.github/copilot-instructions.md` together, so the block must never be written into more than one of them, and setup writes nothing into `copilot-instructions.md`.
2. **The guide must be safe when the model starts it.** Codex and Kilo ignore `disable-model-invocation`; Claude Code and Copilot honor it. So the flag is a convenience on two hosts and not a guarantee. Task 1.3 designs the guide for that: its first action only reads state, it never starts work the human did not ask for, and its description is written so that ordinary requests do not match it. Task 1.3 also tests Codex's per-skill policy file (`agents/openai.yaml`) as an optional adapter (ADR 0004).
3. **Skills call their scripts by absolute path**, built from the folder the host reports. No playbook tells the agent to change directory. Codex and Kilo happened to start in the skill folder and Copilot changed into it; Claude Code refuses to go there.
4. **Install puts each skill in both user-level folders:** a real folder in `~/.agents/skills` (Codex, Kilo) and a link to it from `~/.claude/skills` (Claude Code, which reads nothing else). With a link, each of the four hosts lists the skill once, including Kilo, which reads both folders. Where a machine does not allow links, the fallback is a real copy in both. Kilo was run that way too: it listed each skill once and used the copy in `~/.agents/skills`. Copilot was run with the link only; a real copy in both folders is still to check there.
5. **Routing evals get a new kind of negative case:** a request aimed at a user-invoked skill must not be answered by some other skill.
6. **State stays in files.** The todo tool differs on every host and is missing on two when run without a UI, so the visible checklist cannot be the only record of progress.
7. **Uninstall and update remove every old copy.** An agent can find and run a stale copy by searching, so `install.py` must leave none behind (task 1.4).
8. **The install page says what Kilo needs:** a model that can call tools, chosen by the human. `cg.py doctor` cannot check this from outside the host, so the guide's first reply on a model without tools is the only signal.

## Still open

| Item | Why | What is needed |
|---|---|---|
| Windows | Python command, OneDrive paths with spaces, whether links are allowed, approval prompts | An agent on a World Bank Windows machine follows `spike/host-matrix/WINDOWS.md` and opens a pull request with the reports |
| Copilot with a real copy in both folders | Run with the link only | `--manual --layout copy`, question (a) of the answer sheet; it matters most on Windows |
| Does Copilot follow the `@AGENTS.md` line in `CLAUDE.md` | If it does, it loads the block twice | One Copilot chat in a project set up that way, at the gate (task 1.7) |
| Approval prompts | None seen, but Copilot was on autopilot and the command-line runs have no UI | Count them at the gate, with the defaults a new user has |
| Copilot on the smallest model colleagues commonly pick | The model used was not written down | Repeat step 2 of the answer sheet on that model, at the gate |
| Kilo with other models | One model was run | Repeat at the gate with the model the pilot users will have |
| Marketplace install | Not tried. From documentation: Claude Code, Codex and Copilot can add one from a GitHub repository; Kilo has none. Since task 1.1, `v2` has `.claude-plugin/marketplace.json` and one `.claude-plugin/plugin.json` per pack, and `claude plugin validate --strict` passes on both (inspected). The validator lists core's skill as `core:cg`: Claude Code names a plugin's skills `<plugin>:<skill>`, so the guide would be `/core:cg` from the marketplace and `/cg` from `install.py` | Install `core` from the marketplace in each host and note the name the guide gets |
| Behavior after context compaction | Needs a long session | A long chat in each editor |

## Seen on the maintainer's Mac (inspected)

- VS Code and Positron are installed, with extensions for Claude Code, Kilo Code and Codex. Each bundles its command-line program; none is on `PATH`. No Copilot command-line client is installed.
- `~/.agents/skills` holds 56 entries. `~/.claude/skills` holds 46, of which 45 are links (29 into `~/.agents/skills`). `~/.kilo/skills` holds 22.
- Python 3.14, Node 25, `uv`, `gh` and `git` are present. The npm registry is the World Bank Artifactory.

## How the live run was done

The build session may not start other coding agents, so the maintainer ran the script and the build session read the saved answers. The raw answers are kept out of git because they contain local paths.

## Kill criteria

Listed in `spike/host-matrix/CHECKLIST.md`. One was met: `disable-model-invocation` is ignored on Codex and Kilo, which design change 2 answers. The others were not met on the four hosts tested on macOS. No host is the base (ADR 0004): a host counts as supported once its rows here are live.
