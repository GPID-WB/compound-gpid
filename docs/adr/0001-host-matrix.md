# ADR 0001: Host matrix

Date: 2026-11-24. Status: **incomplete**. Live tests are pending (task 0.1, issue #211).

## Purpose

Record what each coding agent host does, from tests, before the design depends on it. Each fact carries its basis:

- **docs**: read in the vendor's documentation on 2026-11-23. Not yet tested here.
- **inspected**: seen on the maintainer's Mac by reading files and folders. No agent was run.
- **live**: observed by running the host. None yet.

## What is known

| Fact | Copilot (VS Code) | Kilo | Claude Code | Codex | Basis |
|---|---|---|---|---|---|
| Reads `~/.agents/skills` | yes | yes, by default | not listed | yes | docs |
| Reads `~/.claude/skills` | yes | only with Claude compatibility on | yes | not listed | docs |
| Own user-level folder | `~/.copilot/skills` | `~/.kilo/skills` | `~/.claude/skills` | `~/.agents/skills` | docs |
| Skills shown as slash commands | yes | yes | yes | `$name` or `/skills` | docs |
| Plugin marketplace from a GitHub repository | yes | none | yes | yes | docs |
| `disable-model-invocation` in frontmatter | documented | unknown | documented | set in `agents/openai.yaml` | docs |

## Seen on the maintainer's Mac (inspected)

- Installed: VS Code and Positron; extensions for Claude Code 2.1.331, Kilo Code 7.8.32 and the OpenAI Codex extension. Each extension bundles its own command-line binary. None is on `PATH`.
- No Copilot command-line client is installed.
- `~/.agents/skills` holds 56 entries (40 real folders, 16 links). `~/.claude/skills` holds 46, of which 45 are links: 29 point into `~/.agents/skills` and 16 into another project's folder. `~/.kilo/skills` holds 22 (6 real, 16 links).
- So the common installer layout on this machine is: real copy in `~/.agents/skills`, link from `~/.claude/skills`. Whether a host that reads both folders then lists such a skill twice is not known. That is the first thing the live test must settle.
- `~/.agents/.skill-lock.json` exists, written by the `skills` installer.
- Python 3.14, Node 25, `uv`, `gh` and `git` are present. The npm registry is the World Bank Artifactory.
- No GitHub marketplace is registered in Claude Code on this machine, so marketplace install is untested here.

## Live tests: not run

On 2026-11-24 the agent building v2 tried to run the bundled Claude Code, Codex and Kilo binaries without a UI to answer the checklist. The session's safety policy blocks one coding agent from starting another, so no live test ran. Copilot and Kilo inside the editor have no way to be driven from a script at all.

A script now covers the three command-line programs: the maintainer runs `bash spike/host-matrix/run_cli_checks.sh` once and the build session reads the results. Otherwise the live tests need one of:

1. the maintainer runs `spike/host-matrix/CHECKLIST.md` in each host (about ten minutes each); or
2. the maintainer adds a permission rule that lets the build session run the three bundled binaries, which covers Claude Code, Codex and the Kilo command line, but still not Copilot or Kilo inside the editor.

Windows results are needed either way and can only come from a World Bank Windows machine.

## Open questions the live tests answer

1. Is a skill that exists in `~/.agents/skills` and is linked from `~/.claude/skills` listed once or twice in Copilot and in Kilo?
2. What exact name does the user type for a skill installed in the user-level folder, and for one installed from a marketplace?
3. Is `disable-model-invocation` honored by Kilo and Codex?
4. Does the host tell the model where the skill folder is, so a skill can run its own script?
5. Which Python command works on Windows, and how many approval prompts does one script call cost?
6. Is `AGENTS.md` loaded on every turn in each host, and does it survive context compaction?
7. Which hosts have a todo tool and a subagent tool?
8. Does the smallest commonly used Copilot model follow a four-step skill?

## Kill criteria

Listed in `spike/host-matrix/CHECKLIST.md`. Until the answers are in, the design choices that rest on **docs** facts stay provisional: the primary install route (section 6.5 of the plan) and `/cg` being user-invoked only.
