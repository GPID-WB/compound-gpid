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

## Explicit Model Assignments

Ordinary workflow prompts omit `model:`. Operational prompts may retain explicit
standard or economy assignments when the assignment is intentional and not a
premium default.

Currently standard-pinned operational prompts include:

- `cg-work.prompt.md` — Claude Sonnet 4.6
- `cg-review.prompt.md` — Claude Sonnet 4.6

No ordinary workflow prompt may hard-code any model, including standard models.
No prompt currently has an explicit premium model assignment by default.
