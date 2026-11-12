# Your First Standard Workflow

Build a small tool that checks incoming CSV files before a pipeline uses them.
This illustrative exercise teaches the standard loop using synthetic fixtures;
it does not require confidential survey data or claim to be a finished tool.

## Before you begin

Complete [Getting Started](../getting-started/index.md), run `/cg-setup`, and
activate `suites: [cg]` or `suites: [cg, cr]`. Use a project branch and a
language you can review. The example brief uses Python, but the same workflow
can be adapted to R or another supported project language.

Slash commands below belong in the agent chat. Run each stage separately and
inspect its output before moving on.

## 1. Give the task a concrete shape

Start `/cg-brainstorm`, then supply this brief:

```text
Design a Python command-line tool that validates an incoming CSV file.
Required columns: record_id, year, value.
Reject missing columns, blank record_id values, duplicate record_id/year
pairs, non-integer years, and non-numeric values.
Do not change the input file. Report every failed rule with its row numbers.
Exit successfully only when every row passes.
Use small synthetic fixtures; do not read production data.
Discuss dependencies, missing-value conventions, and error messages first.
```

Settle ambiguous choices: whether an empty file is valid, how whitespace is
handled, which missing-value tokens count, and whether numeric strings may
be parsed. Do not let the implementation choose these rules silently.

## 2. Turn the brief into an approved plan

Run `/cg-plan` for the agreed task. Ask it to include the following acceptance
matrix, updated to reflect your decisions:

| Fixture | Expected result |
|---|---|
| Two valid records | Success; no validation errors |
| Required column absent | Failure naming the missing column |
| Blank identifier | Failure naming the affected row |
| Repeated identifier and year | Failure naming the duplicate key and rows |
| Invalid year or value | Failure with the relevant rule and row |
| Several violations | All supported violations reported in one run |
| Every fixture | Input bytes unchanged after validation |

The Plan should name the entry point, error contract, fixtures, commands to
run, and work that is out of scope. Read it and approve it before `/cg-work`.
Use `/cg-plan-review` if the design has uncertain assumptions or downstream
compatibility consequences.

## 3. Implement and inspect the evidence

Run `/cg-work` against that approved saved Plan. Look for source changes,
tests, and a Work Report recording the checks that actually ran.

Try both a valid and an invalid fixture yourself. Confirm the exit status,
diagnostic text, and input preservation. Ask to see the relevant evidence
if the report says only that the implementation is complete.

If a dependency is unavailable, record the blocker. If a test exposes an
ambiguous requirement, revise the decision and Plan before changing behavior.

## 4. Review and resolve findings

Run `/cg-review`. For this isolated synthetic file validator, the ordinary
technical route may be enough; integrating it into a production data pipeline
can warrant `data-risk` review. See [Review and Assure](assure.md).

Use `/cg-fix-triage` for actionable findings. After a fix, rerun the affected
checks. Confirm that P0/P1 findings are resolved and that any accepted
limitations are visible in the report.

## 5. Capture what will help next time

After verification, run `/cg-compound` if the task produced a useful lesson.
For example: collecting all row-level validation errors gives the next analyst
one actionable report, while leaving source data untouched preserves recovery.
The lesson should cite the actual verified behavior and its limits.

## What you should now have

- A saved Plan and acceptance criteria.
- A small implementation with synthetic regression fixtures.
- Executed checks covering success, failure, and input preservation.
- A Work Report and resolved or explicitly accepted review findings.
- A reusable lesson when warranted, stored with the project.

For smaller tasks, the [light-work route](deliver.md#complete-a-qualified-small-task)
combines planning, delivery, and review with its own approval gates. Next, try
[standard use cases](examples.md), or move to the
[research examples](../research/examples.md) for statistical work.
