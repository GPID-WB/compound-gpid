# Workflow Overview

Choose the shortest workflow that matches the uncertainty and risk of the task.
Commands are workflow entry points; skills and most agents are loaded by those
commands rather than invoked directly.

## Choose by situation

First choose the suite that owns the task. Use `/cg-*` for technical delivery,
infrastructure, and code-review workflows. Use `/cr-*` for research scoping,
identification, measurement, econometrics, replication, writing, and
publication output. The research suite composes shared implementation
capabilities without depending on the technical command suite.

For a guided first research workflow, use the [Research Handbook](../research/index.md).

| Situation | Start with | Continue with |
|---|---|---|
| Project direction is unclear | `/cg-strategy` | `/cg-ideate`, then `/cg-brainstorm` |
| One requirement is fuzzy | `/cg-brainstorm` | `/cg-plan` |
| One small technical task qualifies | `/cg-light-work <task>` | Mandatory light Review, then optional compounding |
| The task is known | `/cg-plan` | `/cg-plan-review` when consequential, then `/cg-work` |
| A bug can be reproduced | `/cg-fixbug` | Review and compound after verification |
| A plan already exists | `/cg-work` | `/cg-review`, `/cg-fix-triage` |
| Work was interrupted | `/cg-resume` | Run the returned next command |
| A change needs assurance | `/cg-review` | `/cg-fix-triage`, then verify |
| A solved problem should be reusable | `/cg-compound` | `/cg-brain-rebuild` when the Brain needs refreshing |
| CI is failing on a pull request | `/cg-verify-pr` | Apply confirmed fixes and rerun checks |
| VS Code or Positron crashed | `/cg-diagnose` | Follow the bounded recovery path |
| A research question or method is unclear | `/cr-brainstorm` | `/cr-plan` |
| A research plan is ready | `/cr-work` | `/cr-review`, then `/cr-compound` |

## The standard loop

```text
Understand -> Plan -> Deliver -> Assure -> Resolve -> Remember
```

```text
/cg-brainstorm -> /cg-plan -> /cg-work -> /cg-review -> /cg-fix-triage -> /cg-compound
```

`/cg-light-work` is only for a qualified small technical task. Its first user
gate approves a saved Plan before source edits. It then writes a Work Report and
Review Report, runs the fixed mandatory light Review with `@cg-code-quality` and
`@cg-testing`, and permits one initial pass plus one verification pass only when
Review fixes changed files. Its second user gate is explicit compounding opt-in;
skip creates no permanent knowledge side effect.

Reproducible bugs use `/cg-fixbug`. Research, statistical, and publication work
uses `/cr-*`. Larger, ambiguous, security-sensitive, schema, dependency, or
destructive work uses `/cg-brainstorm` -> `/cg-plan` -> `/cg-work`. `/cg-work`
executes approved saved Plans and redirects unmatched inline tasks without
dispatching them.

## Focused guides

## Task Recipes

These sequences are editorial examples, not a machine-executable workflow graph.
Run one step at a time and inspect its output. Chat blocks contain slash prompts;
terminal blocks do not. Use synthetic data and replace all placeholders with
reviewed project values. Do not infer permission to publish from a passing test.

### Start a Project

Use this for a new project, not to replace an existing team's settings. First
follow [Getting Started](../getting-started/index.md) to install once per machine.
From the project root, terminal (PowerShell or POSIX):

```text
cg-link --platforms copilot
```

Inspect any conflicting managed unit; do not overwrite user files. Choose
`suites: [cg]`, `[cr]`, or `[cg, cr]` using the [suite guide](../modular-guide.md).
Where the CG prompt is eligible, run `/cg-setup` in chat and confirm language,
review depth, and project scope. CR-only projects follow the [research activation
path](../research/index.md). Expected output is the configured project and its
knowledge structure, not a completed analysis. Verify the selected workflow is
eligible, then choose the smallest useful task.

### Fix a Software Error

Use this when expected-versus-actual behavior is reproducible; use planning for
a new feature. Record the launcher, operating system, path, and expected behavior.
Chat:

```text
/cg-fixbug The launcher fails when the project path contains spaces
```

Require a failing reproduction and a passing regression after the fix. Inspect
the actual invocation and test result; do not capture a solution before proof.
If reproduction is absent, keep the issue unresolved. Next, run risk-matched
technical review; compound only the verified lesson.

### Complete a Small Technical Task

Use this for one low-risk change with a clear check, not a reproducible bug,
research task, or security/schema/dependency/destructive change. Chat:

```text
/cg-light-work Add a missing explanatory label to the settings page
```

Confirm qualification and approve the saved Plan before source edits. Inspect
the Work Report, tests, and mandatory light Review Report. A failed gate is not
completion. After convergence, explicitly choose whether to compound; skipping
compounding causes no permanent knowledge side effect. If the task does not
qualify, use the larger-change route instead.

### Deliver a Larger Change

Use this when design choices or multiple steps matter, not to avoid a required
bug reproduction. With the technical suite active, chat:

```text
/cg-brainstorm Add offline validation to the importer
/cg-plan
/cg-plan-review
/cg-work phase1
```

These are separate handoffs. Confirm the brainstorm, save and review the Plan,
then approve work. Expect planned files, tests, and a Work Report with executed
evidence. Missing inputs or unapproved deviations block completion. Review and
verify all intended output before separately authorizing publication.

### Resolve Review Findings

Use this for a saved review, not a substitute for research review. Start from a
checkable diff and choose a route matched to risk. Chat:

```text
/cg-review standard --report-only
/cg-fix-triage P0 P1
/cg-review standard --report-only
```

Use `--report-only` for both review passes to disable automatic fixes. Decline
interactive **Fix** offers until you have selected findings for `/cg-fix-triage`.
Read the first report before selecting findings. Inspect each fix's evidence
and updated status; unresolved P0/P1 findings cannot be hidden by a green style
check. If the report is stale, reconcile it with current source before triage.
Use `/cr-review` for research claims and methods. Next, publish only after the
separate repository gates and authorization.

### Run Research

> [!RESEARCH] Use CR for a statistical comparison, not the language of the implementation. A technical review alone cannot establish comparable poverty measures.

With `cr` active, describe the survey rounds, population, welfare concept, price
base, PPP vintage, survey weights/design, and data access. Chat:

```text
/cr-brainstorm Compare poverty estimates across survey rounds
/cr-plan
/cr-work phase1
/cr-review
```

Confirm comparability assumptions and normative choices before planning or
execution. Expect a scoped brief, research plan, source/specification records,
outputs, and integrity findings. If a welfare definition or survey redesign is
unresolved, record the limitation and block the affected claim rather than infer
comparability. The researcher decides fitness for use; review does not certify
truth. Resolve serious findings, then `/cr-compound` the verified lesson.

### Resume or Recover

Use this after interruption, not to approve a pending decision. In chat:

```text
/cg-resume
```

Make saved plans, reports, Git history, and any active-state pointer available.
Verify the returned phase and next command against current files. The output is
a handoff, not automatic execution or publication authority. If the pointer is
stale, reconcile the canonical artifacts; for an IDE crash use `/cg-diagnose`.
Continue only after the unresolved decision or dependency is addressed.

### Manage Skills

Use this for a known skill need, not arbitrary installation or implicit
activation. Start with terminal discovery:

```text
cg-skill find
cg-skill info cg-skill-management
```

Read origin, eligibility, lifecycle, and manifest health. For a required change,
follow [Skill Management](../skills/management/index.md) to create a deterministic
plan, review evidence, explicitly approve the exact digest-bound apply, and
verify final state. A stale plan requires a new plan; a prospective result is
not active. Project import remains inactive until a separate activation.
Next, validate and audit, then return to the owning technical or research task.

### Focused Reading

- [Design the Work](design.md): strategy, ideation, brainstorming, planning, and plan review.
- [Deliver and Resume](deliver.md): implementation, bug fixing, phase boundaries, and restart records.
- [Review and Assure](assure.md): review routes, findings, CI, diagnostics, and verification.
- [Knowledge and Coordination](knowledge.md): solutions, Brain, roadmap, issues, and wiki.
- [Detailed Workflow Manual](../workflow.md): complete step behavior, scenarios, and edge cases.
- [Modular Guide](../modular-guide.md): suite selection, shared capabilities, and extension rules.

## Related pages

- [Commands](../reference/commands.md)
- [Skills Catalog](../skills/index.md)
- [Governance and Security](../governance/index.md)
