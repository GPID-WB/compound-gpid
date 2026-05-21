# Team Brain Schema Reference

This document defines the canonical structure for a compound-gpid Team Brain
repository — a central GitHub repo that aggregates knowledge from all projects
using the plugin.

---

## Auto-Discovery

When a team member runs `/cg-setup` in a project hosted on GitHub, the plugin
automatically searches for a team brain before prompting the user:

1. **Parse the org** from `git remote get-url origin`.
2. **Check if the org exists** (`GET /orgs/{owner}`).
3. **Search for a brain repo** in the org — candidates in order: `team-brain`,
   `TeamBrain`, `team_brain`, `teambrain`.
4. **If found**: configure automatically, no prompt needed.
5. **If not found**: offer to create `{owner}/team-brain` or accept a custom `owner/repo`.

**Manager field**: Always set to the authenticated GitHub user's `login` (from
`GET https://api.github.com/user`). Never use the git config `user.name` (which
is a machine-local identity, not a GitHub username).

**Project name default**: The repository name parsed from the remote URL, not
the filesystem directory name.

---

## Central Repo Structure

```
team-brain/
├── TEAM-BRAIN.yml           # Configuration: manager, contributors, curation
├── TEAM-BRAIN.md            # Merged index (auto-rebuilt by CI on each push)
├── entries/
│   ├── compound-gpid/       # One folder per project
│   │   ├── 2026-05-20-pester-safety.md
│   │   └── ...
│   └── pcn-tools/
│       └── ...
├── patterns/
│   ├── compound-gpid.jsonl  # One file per project (no cross-project conflicts)
│   └── pcn-tools.jsonl
└── .github/
    └── workflows/
        ├── rebuild-index.yml    # Runs on push to entries/ or patterns/
        └── curation-bot.yml     # Weekly cron for contradiction detection
```

---

## TEAM-BRAIN.yml

The configuration file at the root of the team brain repo.

```yaml
schema-version: "1.0"          # Required. Must match plugin expectations.
manager: "wb384996"             # Required. GitHub username of the team brain manager.
                                #   The manager reviews curation issues and approves
                                #   supersession decisions.
contributors:                   # Required. Who can push to this brain.
  - org: "GPID-WB"             #   All members of a GitHub Organization.
  # OR
  - team: "GPID-WB/data-team" #   Members of a specific GitHub Team.

curation:
  schedule: "weekly"            # Cron preset (daily|weekly|monthly) or cron expression.
  auto-supersede: false         # If true, curation bot auto-applies supersession for
                                #   high-confidence cases without manager approval.

internal-url-patterns:          # Optional. Hostname patterns stripped by the privacy filter.
  - "*.worldbank.org"
  - "internal.wb.lan"
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema-version` | string | Must be `"1.0"` |
| `manager` | string | GitHub username of the team brain manager |
| `contributors` | list | At least one `org:` or `team:` entry |

### Optional Fields

| Field | Default | Description |
|-------|---------|-------------|
| `curation.schedule` | `weekly` | Curation bot run frequency |
| `curation.auto-supersede` | `false` | Auto-apply supersession without approval |
| `internal-url-patterns` | `[]` | Extra hostname patterns for privacy filter |

---

## Pattern JSONL Schema (`patterns/<project>.jsonl`)

Each line is a JSON object representing one distilled pattern from a solution.

```json
{
  "id": "2026-05-20-pester-safety",
  "date": "2026-05-20",
  "source-project": "compound-gpid",
  "topic": "PowerShell testing",
  "tags": ["pester", "powershell", "testing", "vscode"],
  "pattern": "Always use -Quiet with Pester 4 instead of -Output Minimal (Pester 5 flag).",
  "entry-path": "entries/compound-gpid/2026-05-20-pester-safety.md",
  "confidence": 1.0,
  "superseded-by": null
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Filename stem of the source solution (unique within project) |
| `date` | string | ✅ | ISO date (YYYY-MM-DD) of when the entry was pushed |
| `source-project` | string | ✅ | Project namespace (folder name under `entries/`) |
| `topic` | string | ✅ | Primary topic extracted from the solution |
| `tags` | array | ✅ | Searchable tag strings |
| `pattern` | string | ✅ | One-liner distilled pattern (≤ 200 chars) |
| `entry-path` | string | ✅ | Relative path to the full entry markdown file |
| `confidence` | number | ✅ | Base 1.0, boosted by cross-project validation |
| `superseded-by` | string\|null | — | Slug of superseding entry, or null |

### Confidence Scoring

- **Base**: `1.0` for all new entries
- **Boost**: `+0.1` for each additional project that independently validates the same solution (Jaccard similarity ≥ 0.6 on pattern text)
- **No decay**: Time-based decay is deferred to a future iteration

---

## Entry Markdown Schema (`entries/<project>/<filename>.md`)

Entry files use the same frontmatter format as local `.cg-docs/solutions/` files,
with two additional fields:

```markdown
---
date: YYYY-MM-DD
title: "<descriptive title>"
category: "<bugs|build-errors|performance-issues|testing-patterns|...>"
language: "<R|Python|Stata|both>"
tags: [<searchable tags>]
root-cause: "<brief root cause>"
severity: "<P0|P1|P2|P3>"
source-project: "compound-gpid"   # NEW: which project this came from
pushed-date: "2026-05-20"         # NEW: when it was pushed to team brain
---

# <Title>

## Problem
...

## Root Cause
...

## Solution
...

## Prevention
...
```

---

## Local Configuration (`compound-gpid.local.md`)

Projects configure their team brain connection in `compound-gpid.local.md`:

```yaml
team-brain:
  repo: "GPID-WB/team-brain"    # owner/repo on GitHub (required)
  project-name: "compound-gpid"  # namespace under entries/ and patterns/ (required)
  enabled: true                   # set false to opt out entirely
  llm-filter: true                # set false to disable LLM privacy layer
```

If the `team-brain` section is absent or `enabled: false`, all team brain
features are silently disabled.

---

## Onboarding a New Team Brain

Use the `cg-brain-init` command (available after `install.ps1` runs):

```bash
cg-brain-init --repo GPID-WB/team-brain --manager wb384996
```

This creates the repo on GitHub, scaffolds the directory structure, copies the
GH Actions workflow templates, and updates your local `compound-gpid.local.md`.

---

## GitHub Actions Workflows

### `rebuild-index.yml`

Triggers on every push to `entries/` or `patterns/`. Rebuilds `TEAM-BRAIN.md`
from all project namespaces and commits it if changed.

### `curation-bot.yml`

Runs on the configured curation schedule (default: weekly). Detects contradictions
using Jaccard similarity on pattern text (threshold ≥ 0.4). Opens GitHub Issues
for the manager to review. If `auto-supersede: true`, opens PRs for high-confidence
supersessions (Jaccard ≥ 0.8, same root-cause, newer date) instead of issues.

---

## `gh` Authentication Requirements

The push mechanism uses the GitHub Contents API via `gh api`. Required scope:

- **`repo`** scope (full repository access) — needed for Contents API writes

Verify with: `gh auth status`

Configure with: `gh auth login --scopes repo`
