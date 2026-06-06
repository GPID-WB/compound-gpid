# Phase 2 Implementation Plan: Model Governance Cleanup

**Status**: Ready for implementation
**Implementor**: Codex
**Validator**: GitHub Copilot / VS Code
**Created**: 2026-06-05
**Source**: Phase 1 audit at `.cg-docs/cost/context-audit.md`

---

## Phase 2.1 — Remove Hard-Coded Premium Model Defaults

### Files to change

| # | File | Current state | Action |
|---|------|---------------|--------|
| 1 | `.github/prompts/cg-brainstorm.prompt.md` | `model: Claude Opus 4.6 (copilot)` in frontmatter | Remove `model:` line entirely |
| 2 | `.github/prompts/cg-ideate.prompt.md` | `model: Claude Opus 4.6 (copilot)` in frontmatter | Remove `model:` line entirely |
| 3 | `.github/prompts/cg-plan-review.prompt.md` | `model: Claude Opus 4.6 (copilot)` in frontmatter | Remove `model:` line entirely |
| 4 | `.github/prompts/cg-plan.prompt.md` | `model: Claude Opus 4.6 (copilot)` in frontmatter | Remove `model:` line entirely |
| 5 | `.github/prompts/cg-review-repos.prompt.md` | `model: Claude Opus 4.6 (copilot)` in frontmatter | Remove `model:` line entirely |
| 6 | `.github/prompts/cg-strategy.prompt.md` | `model: Claude Opus 4.6 (copilot)` in frontmatter | Remove `model:` line entirely |

### Model-metadata strategy

- **Do NOT** replace `model: Claude Opus 4.6 (copilot)` with `model: Auto` or any other value.
- **Delete** the `model:` key entirely from the YAML frontmatter block.
- When no `model:` key is present, GitHub Copilot uses whatever model the user has selected in the model picker. This is the desired behavior.
- The remaining frontmatter keys (`description`, `tools`, `mode`, etc.) stay unchanged.

### Implementation pattern

For each file, the edit looks like:

```yaml
# BEFORE
---
model: Claude Opus 4.6 (copilot)
description: "..."
tools:
  - ...
---

# AFTER
---
description: "..."
tools:
  - ...
---
```

If `model:` appears on a line by itself in the frontmatter, delete that entire line. Preserve all other frontmatter and the prompt body verbatim.

---

## Phase 2.2 — Update Model Guidance Documentation

### File: `docs/model-guide.md`

Create or update this file with the following content:

```markdown
# Model Guide — Compound GPID

## Default Behavior

Ordinary workflow prompts (`/cg-brainstorm`, `/cg-ideate`, `/cg-plan`,
`/cg-plan-review`, `/cg-review-repos`, `/cg-strategy`) do NOT hard-code a
model. They inherit whichever model the user has selected in the GitHub
Copilot model picker.

## Recommended Model Selection

| Use case | Recommended model |
|----------|-------------------|
| Normal daily use | Auto (let Copilot choose) |
| Routine planning and review | Standard or reasoning model (Sonnet, etc.) |
| High-stakes escalation | Premium model (Opus) — user-initiated only |

## Escalation Guidance

Premium models (e.g., Claude Opus) are appropriate when the user is doing:

- High-stakes architecture or framework redesign
- Statistical, survey, poverty, welfare, or data-correctness decisions
- Security, privacy, authentication, or Team Brain privacy-filtering work
- Release, install, update, linking, or schema-migration work
- A rerun after a lower-tier model produced an inadequate plan or missed an
  important issue

## Governance Principle

- Compound GPID does not hard-code expensive premium models for ordinary
  slash commands.
- The user-selected model controls ordinary workflow execution.
- If the user selects Auto, GitHub Copilot can choose the model.
- If the user selects Sonnet, the workflow runs on Sonnet.
- If the user deliberately selects Opus, that is an explicit budget decision.
- Premium usage is user-initiated or reserved for dedicated premium/deep-review
  workflows — never silently imposed by prompt metadata.

## Prompts That MAY Retain Explicit Model Assignment

(Reserved for future premium/deep-review commands. Currently none.)
```

---

## Phase 2.3 — Update Model-Assignment Tests

### File: `tests/prompt-tools.Tests.ps1` (or equivalent model-assignment test file)

Expected changes:

1. **Remove or update assertions** that expect `model: Claude Opus 4.6 (copilot)` in the six target prompts.
2. **Add a governance test**: Assert that these six prompts do NOT contain a `model:` key in their frontmatter.
3. **Pattern for new test**:

```powershell
Describe "Model governance - ordinary prompts" {
    $ordinaryPrompts = @(
        "cg-brainstorm.prompt.md",
        "cg-ideate.prompt.md",
        "cg-plan-review.prompt.md",
        "cg-plan.prompt.md",
        "cg-review-repos.prompt.md",
        "cg-strategy.prompt.md"
    )

    foreach ($prompt in $ordinaryPrompts) {
        It "$prompt should not hard-code a model" {
            $path = Join-Path $PSScriptRoot "../.github/prompts/$prompt"
            $content = Get-Content $path -Raw
            $content | Should -Not -Match '(?m)^model:'
        }
    }
}
```

4. If existing tests validate a list of "prompts with explicit model assignment," remove these six from that list.

---

## Phase 2.4 — Post-Implementation Audit

### Steps

1. Re-run the context/model audit script that generated `.cg-docs/cost/context-audit.md`.
2. Confirm the audit report no longer lists these six prompts under "premium model usage without escalation."
3. If the audit script is manual, grep all `.prompt.md` files:
   ```bash
   grep -l "^model:" .github/prompts/*.prompt.md
   ```
   The six target files must NOT appear in results.

---

## Phase 2.5 — Manual VS Code Validation

### Steps

1. Open VS Code with the workspace.
2. Set the Copilot model picker to **Auto**.
3. Run `/cg-brainstorm` with a simple prompt. Confirm it executes without error.
4. Set the model picker to **Sonnet**.
5. Run `/cg-plan` with a simple prompt. Confirm it executes on Sonnet.
6. Repeat for at least 2–3 of the six target commands.
7. Confirm no prompt fails due to missing `model:` frontmatter.

---

## Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|--------------|
| 1 | Six target prompts have no `model:` key in frontmatter | `grep -l "^model:" .github/prompts/cg-{brainstorm,ideate,plan-review,plan,review-repos,strategy}.prompt.md` returns empty |
| 2 | `docs/model-guide.md` documents the governance policy | File exists and contains escalation guidance, governance principle, and recommended model table |
| 3 | Model-assignment tests pass | Pester test suite passes (`. tests/Run-Tests.ps1` → check `tests/last-run.json`) |
| 4 | Context/model audit is clean | Re-run audit; zero "premium without escalation" findings for these six prompts |
| 5 | Prompts run in VS Code | Manual validation confirms at least 3 commands execute using user-selected model |
| 6 | No prompt bodies modified | `git diff --stat` shows only frontmatter line removals in the six files, plus `docs/model-guide.md` and test file changes |
| 7 | No non-goal changes | No skill refactoring, no agent changes, no Knowledge Brain changes, no review dispatch changes |

---

## Execution Order (for Codex)

```
1. Read each of the six target prompt files
2. Delete the `model:` line from each file's YAML frontmatter
3. Create/update docs/model-guide.md with governance policy
4. Update model-assignment tests (add governance test, remove stale assertions)
5. Run test suite → confirm pass
6. Run context/model audit → confirm clean
7. Commit: "fix(prompts): remove hard-coded Opus from ordinary workflow prompts"
```

---

## Non-Goals (DO NOT)

- Shrink prompt bodies
- Refactor skills
- Refactor agents
- Change Knowledge Brain retrieval
- Change review-agent dispatch logic
- Add new premium/deep-review commands
- Add `model: Auto` to any prompt (just remove `model:` entirely)
