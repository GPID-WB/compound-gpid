---
date: 2026-04-08
title: "New prompt/agent addition checklist: 7 files that must be updated together"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, prompt-pipeline, compound-gpid, checklist, model-guide, reference, copilot-instructions, prompt-tools-tests, model-assignments-tests]
root-cause: "Adding a new prompt or agent to compound-gpid has 7 downstream files that must be updated in sync — missing any one produces a silent inconsistency that surfaces only in a follow-up light review"
severity: "P2"
---

# New Prompt/Agent Addition Checklist: 7 Files That Must Be Updated Together

Surfaced during Phase 2 of the CE-improvements integration (2026-04-08),
when `cg-compound-refresh`, `cg-ideate`, and `cg-adversarial` were added
and a follow-up light review found 4 gaps across 3 of the 7 files.

---

## Problem

Adding a new prompt (`/cg-*`) or agent (`@cg-*`) to compound-gpid requires
touching at minimum 4 files. Missing any one causes a silent inconsistency:
model counts in docs drift from reality, tests don't guard the new file,
or users reading `copilot-instructions.md` don't know the prompt exists.

The gaps catch found in the Phase 2 follow-up light review:

| Gap | Severity | File missed |
|-----|----------|-------------|
| `/cg-compound-refresh` and `/cg-ideate` not tested in Workflow Entry Points block | P1 | `tests/prompt-tools.Tests.ps1` |
| `Delete` → `Archive` rename incomplete (example table + rules section) | P2 | `cg-compound-refresh.prompt.md` |
| `cg-adversarial` omitted from thorough-depth description | P2 | `.github/copilot-instructions.md` |
| New prompts lacked file-existence + frontmatter Describe blocks | P2 | `tests/prompt-tools.Tests.ps1` |

None of these were caught by the initial review because the review ran on
the Phase 2 *implementation* commit — not the subsequent fix-triage commit.
The light review after the fix-triage commit is what surfaced the residual
gaps.

---

## Root Cause

The 7 downstream files that must be kept in sync are not linked to each
other at parse time. Each is a prose or PowerShell file that assumes the
other files are correct. Pester tests guard some of them (model counts,
frontmatter) but two categories of tests must be explicitly added per-prompt,
and they're easy to forget.

---

## Solution

### The 7-File Checklist

When adding a **new prompt file** (`.github/prompts/<name>.prompt.md`):

| # | File | What to update |
|---|------|----------------|
| 1 | `docs/model-guide.md` | Add a row to the Prompts table; increment count in title and drift-protection comment (e.g., 22 → 25) |
| 2 | `docs/reference.md` | Add a row to the Workflow menu table; increment the count in the model-selection note |
| 3 | `.github/copilot-instructions.md` | Add to Workflow Entry Points table; if it affects a workflow stage (e.g., review depth), update the relevant section |
| 4 | `tests/model-assignments.Tests.ps1` | Add stem to `$promptStems`; update count comment |
| 5 | `tests/prompt-tools.Tests.ps1` | Add three `Describe` blocks: file existence, frontmatter fields, no-tool-restriction |
| 6 | `tests/prompt-tools.Tests.ps1` | Add `It "references /<name> in Workflow Entry Points"` test to the Entry Points block |
| 7 | The prompt file itself | Set `description:`, `model:`, and do **not** include a `tools:` key (orchestrating prompts must have unrestricted tool access) |

When adding a **new agent file** (`.github/agents/<name>.agent.md`):

| # | File | What to update |
|---|------|----------------|
| 1 | `docs/model-guide.md` | Add a row to the Agents table; increment count |
| 2 | `docs/reference.md` | Add to the Agents section; increment count reference |
| 3 | `tests/model-assignments.Tests.ps1` | Add stem to `$agentStems`; update count comment |
| 4 | `tests/prompt-tools.Tests.ps1` | Add `Describe` blocks for frontmatter and tool-restriction (agents may have `tools:` — check the agent's role) |
| 5 | The agent file itself | Ensure output format uses `**[P0.N]** [<agent-name>]` — this pattern is parsed by `cg-review` and `cg-fix-triage`; a custom format is silently ignored |
| 6 | `.github/copilot-instructions.md` | If the agent is new to a review depth tier (e.g., thorough-only), update the Review Depth Tiers section |

### Agent Output Format Contract

Agents invoked by the review orchestrator (`cg-review.prompt.md`) **must**
use the standard finding format. Custom formats are not parseable:

```markdown
# WRONG — custom format (cg-adversarial original output)
### [P0|P1|P2]-ADV-<N>: <title>
**Attack vector**: ...

# CORRECT — standard format (parseable by cg-fix-triage)
- **[P0.N]** [cg-adversarial] `<file>`:<line> — <title>
  **Attack vector**: ...
  **Fix**: ...
```

The Step 2.5 quality check in `cg-review.prompt.md` validates output by
scanning for `**[P0.`, `**[P1.`, `**[P2.`, `**[P3.` prefixes. An agent
using any other format will have its output classified as "unusable" and
trigger a warning to the user.

### Verification After Adding

After committing the new prompt/agent and all 7 downstream updates, run:

```powershell
# Safe pattern — individual files only, no directory runs
$r = Invoke-Pester tests\model-assignments.Tests.ps1 -PassThru -Quiet
$r | Select-Object TotalCount, PassedCount, FailedCount

$r = Invoke-Pester tests\prompt-tools.Tests.ps1 -PassThru -Quiet
$r | Select-Object TotalCount, PassedCount, FailedCount
```

Then run `/cg-review light` on the commit. The light review agents
(`cg-code-quality` + `cg-testing`) will catch any remaining gaps in the
checklist.

---

## Prevention

### Add a comment to `tests/prompt-tools.Tests.ps1`

At the top of the Workflow Entry Points section, add:

```powershell
# When adding a new prompt to copilot-instructions.md:
# 1. Add an It block here (line ~210)
# 2. Add file-existence + frontmatter + no-tool-restriction Describe blocks (see cg-strategy pattern)
# 3. Update model-assignments.Tests.ps1 stem array + count comment
# 4. Update docs/model-guide.md and docs/reference.md counts
```

### Run the light review after every fix-triage

Fix-triage commits can introduce their own gaps (e.g., a rename applied to
the main occurrence but not all secondary occurrences). The pattern:

```
feat(x): implement feature
/cg-review standard
fix(x): apply review findings
/cg-review light        ← catches what fix-triage introduced
fix(x): apply light review findings
```

---

## Related

- [2026-04-08-cross-cutting-enumeration-propagation-audit.md](2026-04-08-cross-cutting-enumeration-propagation-audit.md) — related pattern for enumeration changes that cut across many files
- [2026-03-30-prompt-pipeline-contract-testing.md](2026-03-30-prompt-pipeline-contract-testing.md) — general pattern for testing interfaces between chained prompts
- [2026-03-30-test-prompt-frontmatter-tools-list.md](2026-03-30-test-prompt-frontmatter-tools-list.md) — specifically the `tools:` whitelist restriction pattern
- [2026-04-20-behavioral-pester-tests-for-skill-md-files.md](2026-04-20-behavioral-pester-tests-for-skill-md-files.md) — parallel checklist for **new skill files** (behavioral describe block + `docs/reference.md` skills table row)
