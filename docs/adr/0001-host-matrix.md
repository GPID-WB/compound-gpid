# ADR 0001: Host matrix

Date: 2026-11-24. Status: **partly tested**. Claude Code, Codex and Kilo were run on macOS. Copilot and Windows are still open (issue #211).

## Purpose

Record what each coding agent host does, from tests, before the design depends on it. Each fact carries its basis:

- **live**: observed by running the host on the maintainer's Mac on 2026-11-24 with the script in `spike/host-matrix/` (now `run_cli_checks.py`). All three hosts were run without a UI, so the editor panels may differ.
- **docs**: read in the vendor's documentation on 2026-11-23. Not tested here.
- **inspected**: seen by reading files and folders. No host was run.

Versions run: Claude Code 2.1.331, Codex 0.171.0-alpha.13.2, Kilo 7.8.32 with the model `openai/gpt-6.2-sol`.

## Live results

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

Further findings:

- **The import works.** With a `CLAUDE.md` that holds only `@AGENTS.md`, Claude Code loaded the marker from `AGENTS.md`. This was from documentation before; it is live now.
- **A hidden skill can be answered by the wrong one.** Asked "Please run the host probe", Claude Code could not see the user-invoked skill. In the first run it started the other test skill, although its description did not match. In the second run it started nothing and asked. The behavior is not stable.
- **Kilo depends on the model chosen.** Kilo's default model on this machine could not call tools, and every prompt stopped. A model name that starts with `kilo/` is billed to the Kilo account and stopped for lack of credits. `openai/gpt-6.2-sol`, through the maintainer's own subscription, worked. Skill discovery is the host's doing, but whether a skill runs depends on the model.

- **An agent may hunt for a skill it was not given.** With the test skill only in `~/.claude/skills`, Codex did not list it. Asked for it by name, the model searched the home folder, found the file there, and ran it. A leftover copy of a skill is therefore not harmless.

## What this changes in the design

1. **One pointer block, in `AGENTS.md`, imported by `CLAUDE.md`.** Codex and Kilo read `AGENTS.md`. Claude Code reads `CLAUDE.md` and follows the import line. Setup writes the block once in `AGENTS.md` and makes sure `CLAUDE.md` holds `@AGENTS.md`. Tested live on all three.
2. **The guide must be safe when the model starts it.** Two of three hosts ignore `disable-model-invocation`, so the flag is a convenience on Claude Code and not a guarantee anywhere. Task 1.3 designs the guide for that: its first action only reads state, it never starts work the human did not ask for, and its description is written so that ordinary requests do not match it. Task 1.3 also tests Codex's per-skill policy file (`agents/openai.yaml`) as an optional adapter (ADR 0004).
3. **Skills call their scripts by absolute path**, built from the folder the host reports. No playbook tells the agent to change directory. Codex and Kilo happened to start in the skill folder; Claude Code refuses to go there.
4. **Install puts each skill in both user-level folders:** a real folder in `~/.agents/skills` (Codex, Kilo) and a link to it from `~/.claude/skills` (Claude Code, which reads nothing else). With a link, each of the three hosts lists the skill once, including Kilo, which reads both folders. Where a machine does not allow links, the fallback is a real copy in both; whether Kilo then lists the skill twice is still open.
5. **Routing evals get a new kind of negative case:** a request aimed at a user-invoked skill must not be answered by some other skill.
6. **State stays in files.** Only Kilo offered a todo tool when run without a UI, so the visible checklist cannot be the only record of progress.
7. **Uninstall and update remove every old copy.** An agent can find and run a stale copy by searching, so `install.py` must leave none behind (task 1.4).
8. **The install page says what Kilo needs:** a model that can call tools, chosen by the human. `cg.py doctor` cannot check this from outside the host, so the guide's first reply on a model without tools is the only signal.

## Still open

| Item | Why | What is needed |
|---|---|---|
| Copilot in VS Code or Positron | No way to run it from a script. | `python3 spike/host-matrix/run_cli_checks.py --manual`, then the answer sheet it writes |
| Kilo's editor panel | Same reason | Same answer sheet |
| Kilo with other models | One model was run | Repeat at the gate (task 1.7) with the model the pilot users will have |
| Windows | Python command, OneDrive paths with spaces, whether links are allowed, approval prompts | An agent on a World Bank Windows machine follows `spike/host-matrix/WINDOWS.md` and opens a pull request with the reports |
| Marketplace install | Not tried | After task 1.1 puts a manifest on `v2` |
| Approval prompts | Cannot be counted without a UI | Checklist, in each editor |
| Behavior after context compaction | Needs a long session | Checklist |
| Kilo with a real copy in both folders | Kilo reads both. With a link it lists a skill once; with two copies it is not known | `python3 spike/host-matrix/run_cli_checks.py --only kilo --layout copy --kilo-model openai/gpt-6.2-sol` |
| Kilo and `AGENTS.md`, second look | In the first Kilo run the marker was loaded. In a later run it was not. The script had by then been rewritten and left the `PWD` variable pointing at this repository, so Kilo probably loaded this repository's `AGENTS.md`. The script is fixed; the cause is not yet confirmed | The same rerun as the row above |

## Facts from documentation, not yet tested

| Fact | Copilot (VS Code) | Basis |
|---|---|---|
| Reads `~/.agents/skills` | yes | docs |
| Reads `~/.claude/skills` | yes | docs |
| Skills shown as slash commands | yes | docs |
| Plugin marketplace from a GitHub repository | yes; Kilo has none | docs |
| `disable-model-invocation` | documented | docs |

Copilot reads both user-level folders according to its documentation, so the link layout that is safe on the three tested hosts might list a skill twice there. That is the first thing to check in Copilot.

## Seen on the maintainer's Mac (inspected)

- VS Code and Positron are installed, with extensions for Claude Code, Kilo Code and Codex. Each bundles its command-line program; none is on `PATH`. No Copilot command-line client is installed.
- `~/.agents/skills` holds 56 entries. `~/.claude/skills` holds 46, of which 45 are links (29 into `~/.agents/skills`). `~/.kilo/skills` holds 22.
- Python 3.14, Node 25, `uv`, `gh` and `git` are present. The npm registry is the World Bank Artifactory.

## How the live run was done

The build session may not start other coding agents, so the maintainer ran the script and the build session read the saved answers. The raw answers are kept out of git because they contain local paths.

## Kill criteria

Listed in `spike/host-matrix/CHECKLIST.md`. None was triggered by the three hosts tested. No host is the base (ADR 0004): a host counts as supported once its rows here are live.
