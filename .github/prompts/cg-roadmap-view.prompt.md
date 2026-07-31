---
description: "Visualize the project roadmap in chat. Supports flags: --milestone, --tasks, --detail, --status, --wip, --plan, --help. Dispatches @cg-roadmap-view agent for rendering."
---

# Roadmap View

Display the project roadmap in a readable format directly in chat. Supports
multiple views controlled by flags. Names are fuzzy-matched — you do not need
to remember exact milestone or feature IDs.

## Usage Examples

```
/cg-roadmap-view                              # Summary: all milestones + progress
/cg-roadmap-view --wip                        # In-progress milestones with features
/cg-roadmap-view --milestone skills           # Detail for "Skills Enhancement" milestone
/cg-roadmap-view --tasks                      # All milestones with full feature lists
/cg-roadmap-view --tasks skills               # Features in "Skills Enhancement"
/cg-roadmap-view --detail stata testing       # Detail for feature matching "stata testing"
/cg-roadmap-view --detail stata testing --plan # Same, plus linked plan summary
/cg-roadmap-view --status idea                # All features with status "idea"
/cg-roadmap-view --help                       # Show this usage guide
```

## Flag Reference

| Flag | Argument | Description |
|------|----------|-------------|
| *(none)* | — | Summary table: all milestones, status, done/total |
| `--milestone` | `<name>` | One milestone: objective, progress, feature list |
| `--tasks` | *(optional name)* | Feature lists — all milestones, or one if name given |
| `--detail` | `<name>` | Feature detail: description, status, linked plan path |
| `--plan` | — | Add with `--detail` to include linked plan summary |
| `--status` | `idea\|planned\|active\|done` | All features matching that status |
| `--wip` | — | In-progress milestones with feature lists |
| `--help` | — | Show this usage guide |

> **Valid `--status` values** mirror the `status` field of `features[]` entries in `roadmap.json`.
> If the schema changes, update this table.

Names are fuzzy-matched — "skills" matches "Skills Enhancement", "stata
testing" matches "Testing skill for Stata (assert-based/reprun)". If multiple
milestones or features match, you will be shown the candidates and asked to
clarify.

## Process

### Step 1: Parse Arguments

Parse the user's input for flags and optional name arguments:

1. If `--help` is present (or the user typed just `help`): display the usage
   guide above and stop — do not proceed further.
2. If `--plan` is present without `--detail`: respond with:
   > "`--plan` requires `--detail`. Example: `/cg-roadmap-view --detail stata testing --plan`"
   and stop — do not proceed further.
3. If `--detail` is present but no name follows: respond with:
   > "`--detail` requires a feature name. Example: `/cg-roadmap-view --detail stata testing`"
   and stop — do not proceed further.
4. If `roadmap.json` does not exist in the project root: tell the user
   > "No roadmap found. Run `@cg-roadmap` to initialize one."
   and stop.
5. Otherwise, determine the view mode and filter from the flags:

| User input | view | filter | show-plan |
|---|---|---|---|
| *(no flags)* | `summary` | — | false |
| `--wip` | `wip` | — | false |
| `--milestone <name>` | `milestone` | `<name>` | false |
| `--tasks` | `tasks` | — | false |
| `--tasks <name>` | `tasks-milestone` | `<name>` | false |
| `--detail <name>` | `detail` | `<name>` | false |
| `--detail <name> --plan` | `detail` | `<name>` | true |
| `--status <status>` | `status` | `<status>` | false |

### Step 2: Dispatch Agent

Dispatch `@cg-roadmap-view` with:
- `view`: the resolved view mode
- `filter`: the resolved filter string (omit if not applicable)
- `show-plan`: true/false (omit if false)

### Step 3: Present Output

Present the agent's rendered output directly to the user. Do not add
commentary or reformatting — the agent output is the final response.
