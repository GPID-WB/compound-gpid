# ADR 0003: Packs and the contract between a pack and core

Date: 2026-11-24. Status: accepted by the maintainer on 2026-11-24 as the working contract. It is expected to change: see "How this contract changes" below. The file layout is provisional until tasks 1.1 and 1.5 test it on the hosts.

## Context

Version 1 installed everything for everyone and used a registry to filter it. The maintainer wants a small core that everyone installs and further content that people add as they need it, possibly from other repositories and other teams.

## Decision

### What a pack is

A pack is a set of skill folders that is installed as one unit. One of those folders, the pack's lead skill, holds a file named `pack.json`. Nothing else marks a pack.

In the hub, packs live under `packs/`:

```
packs/
  core/
    cg/                 lead skill of core: SKILL.md, pack.json, principles/, playbooks/, lenses/, scripts/
  lang-r/
    r-shared/           lead skill: SKILL.md, pack.json
    r-collapse/
    r-datatable/
    ...
  research/
    cr/                 lead skill: SKILL.md (the /cr alias), pack.json, playbooks/, lenses/
    research-identification/
    ...
```

Installing a pack copies its skill folders, unchanged, into the folder where the host looks for skills. Today's `skills/cg/` moves to `packs/core/cg/` in task 1.1.

### `pack.json`: six keys

| Key | Meaning |
|---|---|
| `name` | The pack's name, unique in the hub index. |
| `version` | The pack's version. |
| `requires-core` | The lowest core version the pack works with. |
| `skills` | The names of the pack's skill folders. |
| `lenses` | A list. Each entry: `id`, `file` (path inside the lead skill), `principle` (the principle it serves), `when` (file patterns and, optionally, a track). |
| `tracks` | A list. Each entry: `track`, `playbook` (path inside the lead skill), and optionally `alias` (a command name such as `cr`). |

A pack that only carries knowledge, such as a language pack with no lenses, leaves `lenses` and `tracks` empty.

### How core and packs meet

1. **Skills need no contract.** A pack's skills are loaded by the host from their descriptions. Core does not know they exist.
2. **Lenses and tracks are found by code.** `cg.py packs` looks in the folders beside the `cg` skill for a `pack.json` and reads it. `cg.py verifiers` adds every lens whose `when` matches the changed files and the track. The guide adds every track a pack declares.
3. **Core never imports from a pack, and a pack never imports from core.** A pack's script that needs core calls the `cg.py` command line, through the launcher that setup recorded.
4. **A pack's files stay in its own folders.** No file in one skill folder is reached by a relative path from another.
5. **Versions are checked, not assumed.** `cg.py packs` reports a pack whose `requires-core` is higher than the installed core, and `cg.py status` stops on it.
6. **A project says which packs it expects** in `.cg-docs/config.json`. `cg.py status` names any that are missing and prints the one command that adds them.
7. **A project's settings for a pack** sit in the same file, under `settings`, one object per pack with flat string values: `"settings": {"lang-r": {"r-syntax": "tidyverse"}}`. `cg.py status` prints them. A setting that is absent takes the default that the pack's lead skill states.

### Where packs come from

The hub's index lists every pack with its source. A source is a folder in the hub or another repository. A pack moves to its own repository when a different team owns it, when it is released on its own rhythm, or when it needs its own runtime. Until then it is a folder in the hub.

Another team publishes a pack by keeping it in its own repository, passing `tools/validate_pack.py`, and adding one line to the hub's index.

### Rules the validator enforces

- `pack.json` has only the six keys, and every path in it exists.
- Every skill name is unique across the whole index, because installed skills share one flat folder.
- Every lens names an existing principle.
- Skill files pass the skill linter and the glossary check.
- The pack's tooling is inside its budget (see `SCOPE.md`).

## Consequences

- Core can stay small: a feature someone wants becomes a pack, not a change to core.
- Nothing is discarded from version 1. Content moves into the pack where it belongs.
- A person installs only what they use, so the descriptions held in the model's context stay few.
- The contract is the one place two repositories can disagree, so every change to it is written down.

## How this contract changes

- **Before 2.0 is released,** no pack outside the hub depends on the contract. When a build task shows that a key, a path or a rule is wrong, change it in the same pull request: amend this record with a dated line under "Changes", and update the validator and every `pack.json` in the hub together.
- **After 2.0 is released,** other repositories depend on it. A change then needs a new decision record, and a change that breaks existing packs also raises the core version that packs name in `requires-core`.
- The six-key limit is a budget, not a law. A seventh key needs the same case as any other change to core (`SCOPE.md`).

## Changes

- 2026-11-24: accepted as the working contract.
- 2026-11-24, decided by the maintainer: `install.py` is the one supported install route, in every host. The hub's Claude Code marketplace files stay valid (CI checks them) but are not advertised, and a marketplace install is not supported: Claude Code keeps each plugin in its own folder, so the packs are not beside `cg` (tested in task 1.1). This settles the first open question below.
- 2026-11-24, decided by the maintainer: a project records a pack's settings in `.cg-docs/config.json` under `settings`, keyed by pack name (rule 7 above). No key is added to `pack.json`; a pack's lead skill says which settings it reads and what happens when one is absent.

## Open, to be settled by tests

- Settled 2026-11-24: marketplace installs are not supported (see "Changes"), so the folders beside `cg` are the place to look.
- Settled in task 1.1: the index (`.claude-plugin/marketplace.json`) points at each pack folder, and each pack's `.claude-plugin/plugin.json` lists its skill folders. Kept valid, not advertised.
- Whether `/cr` as an alias works the same in every host. Task 3.2.
