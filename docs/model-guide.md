# Model Guide — Compound GPID

## Default Behavior

Ordinary workflow prompts (`/cg-brainstorm`, `/cg-ideate`, `/cg-plan`,
`/cg-plan-review`, `/cg-review-repos`, `/cg-strategy`) do NOT hard-code a
model. They inherit whichever model the user has selected in the GitHub
Copilot model picker.

When Copilot Auto is selected, Compound GPID prompts must not infer or name the
hidden underlying model. If that identity matters for a validation run, check
the GitHub Copilot UI or hover details.

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

## Validation Guardrails

Before merging model or prompt-governance changes in the `compound-gpid` repo,
run the context audit:

```bash
python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both
```

The generated guardrails must show no premium model usage, no model-guide drift,
and no ordinary model-picker prompt with an explicit `model:` frontmatter key.
When comparing token-optimization work against an earlier report, pass
`--baseline <previous-context-audit.json>` and review the Benchmark Summary
before release.

For release candidates, also complete
`.cg-docs/cost/token-optimization-release-checklist.md`. The static audit can
verify prompt metadata and guardrail text, but VS Code/Copilot must still
validate runtime model-picker behavior and routed agent dispatch.
