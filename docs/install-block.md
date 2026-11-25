# Install Compound GPID

This is the one install text. Other pages link here instead of repeating it.

You need git and Python 3.9 or later. Nothing else: no Node, no admin rights.

## 1. Get the hub

Clone it into a folder that OneDrive does not sync. OneDrive and git do not mix well: a sync can delete files from a checkout.

macOS:

```
git clone --branch v2 https://github.com/GPID-WB/compound-gpid ~/compound-gpid
```

Windows (PowerShell):

```
git clone --branch v2 https://github.com/GPID-WB/compound-gpid "$env:USERPROFILE\compound-gpid"
```

Until 2.0 is released the hub is on branch `v2`.

## 2. Install packs

Pick a profile, or name the packs. Core is always included.

macOS:

```
python3 ~/compound-gpid/install.py --profile economist
python3 ~/compound-gpid/install.py --packs core,lang-r
```

Windows: the same, with `py -3` (or `python`) in place of `python3`, and `"$env:USERPROFILE\compound-gpid\install.py"` as the path.

| Profile | Packs |
|---|---|
| `economist` | core, lang-r, lang-stata, research, writing-wb |
| `developer` | core, lang-r, lang-python |
| `everything` | every pack in the hub |

A pack that is not in the hub yet is skipped with a note.

The skills go into `~/.agents/skills` (read by Copilot, Codex and Kilo) with a link from `~/.claude/skills` (read by Claude Code). Where links are not allowed, the second folder gets a copy. Nothing is written into your projects. Restart your coding agent afterwards so it sees the new skills.

`install.py` ends by running `cg.py doctor`, which checks Python, git and the install, and lists any copy that a coding agent would show twice.

In Kilo, choose a model that can call tools; with one that cannot, nothing runs.

## 3. Later

| To | Run |
|---|---|
| add a pack | `install.py --add lang-stata` |
| remove a pack | `install.py --remove lang-stata` |
| update | `git -C ~/compound-gpid pull`, then `install.py --update` |
| remove everything | `install.py --uninstall` |
| see what a command would change | add `--dry-run` |

`install.py` only touches folders it installed, and refuses to overwrite one you changed since then (`--force` overrides that).

## Coming from version 1

`install.py` reports what version 1 left on the machine. `install.py --remove-v1` removes what version 1 owned: its links and the folders it marked as managed copies, in your user skill folders and, with `--project <folder>`, in one project. It prints the steps for the rest, which sit in files you own: the PATH block in your shell profile, the version 1 folder itself, and an entry in Kilo's settings.
