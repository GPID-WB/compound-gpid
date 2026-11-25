# ADR 0001: Host matrix

Date: 2026-11-24. Status: **partly tested**. Claude Code and Codex were run on macOS. Kilo, Copilot and Windows are still open (issue #211).

## Purpose

Record what each coding agent host does, from tests, before the design depends on it. Each fact carries its basis:

- **live**: observed by running the host on the maintainer's Mac on 2026-11-24 with `spike/host-matrix/run_cli_checks.sh`. Both hosts were run without a UI, so the editor panels may differ.
- **docs**: read in the vendor's documentation on 2026-11-23. Not tested here.
- **inspected**: seen by reading files and folders. No host was run.

Versions run: Claude Code 2.1.331, Codex 0.171.0-alpha.13.2, Kilo 7.8.32 (failed before answering, see below).

## Live results

The two test skills were installed the way the `skills` installer already does it on this machine: a real folder in `~/.agents/skills` and a link to it from `~/.claude/skills`.

| Question | Claude Code | Codex |
|---|---|---|
| Finds the skills | yes, through `~/.claude/skills` | yes, in `~/.agents/skills` |
| Lists a skill twice | no | no |
| Honors `disable-model-invocation` | **yes**: the skill is hidden from the model and still runs when typed as `/cg-spike-hello` | **no**: the model saw the skill and ran it on a plain request |
| Loads a skill from its description | yes | yes |
| Tells the model the skill's folder | yes ("Base directory for this skill: ...") | yes |
| Runs the skill's script | yes, by absolute path; a `cd` into the skill folder was refused | yes, with the skill folder as working directory |
| Python command that worked | `python3` | `python3` |
| Always-loaded instructions | `CLAUDE.md` only; **`AGENTS.md` was not loaded** | `AGENTS.md` only |
| Todo tool | none in this mode | none in this mode |
| Subagent tool | `Agent` | `collaboration.spawn_agent`, on explicit request |

One unplanned finding: asked "Please run the host probe", Claude Code could not see the hidden skill and ran the other test skill instead, although its description did not match. A model-invoked skill can be picked for a request that was meant for a user-invoked one.

## What this changes in the design

1. **One pointer block, in `AGENTS.md`, imported by `CLAUDE.md`.** Claude Code does not read `AGENTS.md` and Codex does not read `CLAUDE.md`. Claude Code's documentation says a `CLAUDE.md` can pull in another file with a line such as `@AGENTS.md`, so setup writes the block once in `AGENTS.md` and makes sure `CLAUDE.md` holds that import line. The import is from documentation; the next run of the script tests it. If it fails, setup writes the block into both files.
2. **`/cg` needs a second mechanism on Codex.** The frontmatter flag alone does not keep the guide from firing by itself there. Task 1.3 tests Codex's own per-skill policy file (`agents/openai.yaml`); if that fails, the guide's description must be written so it does not match ordinary requests.
3. **Skills call their scripts by absolute path**, built from the folder the host reports. No playbook tells the agent to change directory.
4. **The link layout is safe on these two hosts.** A real folder in `~/.agents/skills` with a link from `~/.claude/skills` is listed once in each.
5. **Routing evals get a new kind of negative case:** a request aimed at a user-invoked skill must not be answered by some other skill.
6. **State stays in files.** Neither host offered a todo tool when run without a UI, so the visible checklist cannot be the only record of progress.

## Still open

| Item | Why | What is needed |
|---|---|---|
| Kilo | Two runs, no answer yet. Run 1: all four prompts stopped with "No endpoints found that support tool use", because the model set as Kilo's default cannot call tools. Run 2, with `kilo/openai/gpt-6.2-sol`: all four stopped with "Add credits to continue, or switch to a free model". A model name that starts with `kilo/` is billed to the Kilo account, which had no credits. Kilo also lists the same model under `openai/` and `github-copilot/`; from the listing, those go through the account signed in with that provider (inferred, not yet run). | Rerun through a provider that is already paid for: `ONLY=kilo KILO_MODEL=openai/gpt-6.2-sol bash spike/host-matrix/run_cli_checks.sh`, or `KILO_MODEL=github-copilot/gpt-6.2-sol` |
| Copilot in VS Code or Positron | No way to run it from a script. | The maintainer follows `spike/host-matrix/CHECKLIST.md` in the Copilot chat panel |
| Kilo's editor panel | Same reason | Same checklist |
| Windows | Python command, OneDrive paths with spaces, approval prompts | One run of the script and the checklist on a World Bank Windows machine |
| Marketplace install | Not tried | After task 1.1 puts a manifest on `v2` |
| Approval prompts | Cannot be counted without a UI | Checklist, in each editor |
| Behavior after context compaction | Needs a long session | Checklist |
| Does `@AGENTS.md` in `CLAUDE.md` load the block in Claude Code | From documentation only | Next run of the script, which now includes this case |
| Does Claude Code read `~/.agents/skills` directly | The test skill was also linked from `~/.claude/skills`, so the two were not separated | One run with the link removed |

## Facts from documentation, not yet tested

| Fact | Copilot (VS Code) | Kilo | Basis |
|---|---|---|---|
| Reads `~/.agents/skills` | yes | yes, by default | docs |
| Reads `~/.claude/skills` | yes | only with Claude compatibility on | docs |
| Skills shown as slash commands | yes | yes | docs |
| Plugin marketplace from a GitHub repository | yes | none | docs |
| `disable-model-invocation` | documented | unknown | docs |

Copilot reads both user-level folders according to its documentation, so the link layout that is safe on Claude Code and Codex might list a skill twice there. That is the first thing to check in Copilot.

## Seen on the maintainer's Mac (inspected)

- VS Code and Positron are installed, with extensions for Claude Code, Kilo Code and Codex. Each bundles its command-line program; none is on `PATH`. No Copilot command-line client is installed.
- `~/.agents/skills` holds 56 entries. `~/.claude/skills` holds 46, of which 45 are links (29 into `~/.agents/skills`). `~/.kilo/skills` holds 22.
- Python 3.14, Node 25, `uv`, `gh` and `git` are present. The npm registry is the World Bank Artifactory.

## How the live run was done

The build session may not start other coding agents, so the maintainer ran the script and the build session read the saved answers. The raw answers are kept out of git because they contain local paths.

## Kill criteria

Listed in `spike/host-matrix/CHECKLIST.md`. None was triggered by the two hosts tested. No host is the base (ADR 0004): a host counts as supported once its rows here are live.
