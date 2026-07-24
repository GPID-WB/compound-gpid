# Review and Assure

Review routes match specialist attention to the changed files and their risk.
Explicit route selection overrides automatic routing, while detected risk
signals should still be reported.

## Choose a review route

| Route | Use for |
|---|---|
| `light` | Small documentation, metadata, prompt wording, or low-risk test changes |
| `standard` | Ordinary implementation and test changes without elevated signals |
| `data-risk` | Pipelines, statistics, survey, poverty, welfare, weights, joins, aggregation, and reproducibility-sensitive changes |
| `architecture` | Dependencies, module boundaries, performance, memory, API contracts, and large refactors |
| `full` | Credentials, authentication, releases, publishing, install/update/link paths, schema changes, and destructive filesystem behavior |

```text
/cg-review data-risk
```

Use `--report-only` to disable automatic fixes. The review report is still
written, and the workflow can offer a separate **Fix** action; decline that
offer when source files must remain unchanged. Automatic fixes have boundaries:
statistically sensitive functions, welfare or income variables, and weights
require manual handling.

## Resolve findings

Review findings use P0 through P3 priorities and are stored with per-finding
status. Run `/cg-fix-triage` by priority or finding ID, then verify behavior
rather than assuming a textual change resolved the issue.

```text
/cg-fix-triage P0 P1
/cg-fix-triage P2.3
```

P0 covers blocking risks such as credential exposure, silent data corruption,
or incorrect statistical results. P1 findings must be resolved before merge.

## CI and editor diagnostics

- `/cg-verify-pr` classifies current pull-request checks and can propose or
  apply bounded repairs.
- `/cg-fix-problems` works through editor diagnostics interactively.
- `/cg-diagnose` is the recovery entry point for VS Code or Positron crashes.

PowerShell tests in this repository have strict safety rules. Use the canonical
runner documented in [Contribute and Develop](../development/index.md), not an
ad hoc directory-wide Pester command.

## Related pages

- [Agents](../reference/agents.md)
- [Governance and Security](../governance/index.md)
- [Troubleshooting Reference](../troubleshooting.md)
- [Detailed Workflow Manual](../workflow.md)
