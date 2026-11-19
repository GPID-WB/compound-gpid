# Standard Module: Examples and Use Cases

Use these illustrative briefs as starting points after
[setup](../getting-started/index.md). Adapt paths, constraints, and acceptance
criteria to the real repository. They are task examples, not completed work.

## Build a reproducible import pipeline

**Situation:** a team receives monthly files with changing column names and
needs a reliable ingestion step. This is technical infrastructure; decisions
about statistical definitions belong in the research workflow.

Start `/cg-brainstorm` with:

```text
Design an ingestion pipeline for monthly CSV deliveries.
Use a documented column mapping, validate required fields and key uniqueness,
and create an audit of accepted and rejected files.
Preserve raw inputs. Do not silently coerce types or drop records.
Use synthetic examples representing valid data, schema drift, and duplicates.
Identify decisions that require the data owner's approval before planning.
```

Continue with `/cg-plan`, `/cg-plan-review` when warranted, and `/cg-work`.
Use `/cg-review data-risk` before accepting the result.

**Check:** rerunning the same delivery gives the same output; invalid inputs
fail visibly; accepted/rejected counts reconcile; the source remains intact;
logs contain no restricted record-level values. Keep the Plan, schema mapping,
tests, and run evidence with the implementation.

## Fix a repeatable export failure

**Situation:** an export works for a single-word directory but fails for a
path containing spaces.

Start `/cg-fixbug` with:

```text
The export command fails when its output directory contains a space.
Expected: the same file content and exit status as a directory without spaces.
Reproduce using a temporary directory and synthetic input.
Preserve existing files; do not change the public command syntax.
Show the failing regression test before fixing the cause.
```

**Check:** the regression fails before the fix and passes after it; an
ordinary path still works; no unrelated files change. Review the result and
capture the verified cause with `/cg-compound` when it will prevent recurrence.

## Make a small documentation improvement

**Situation:** a command's help text is technically correct but lacks an example.

```text
/cg-light-work -- Add one runnable synthetic example to the CSV validator's
help text. Keep its command-line behavior and dependencies unchanged.
```

Approve the saved Plan before edits. Inspect the example's actual output and
the mandatory light Review. Choose whether to compound afterward; skipping
that optional step should not create a permanent lesson.

**Check:** the example matches the implemented flags, runs in a clean temporary
directory, and reports the documented result. If the task reveals a behavior
change, stop and choose a larger workflow rather than stretching light-work.

## Resume a teammate's unfinished change

**Situation:** a Plan has several phases, and work stopped after the first.

Run `/cg-resume`. Ask it to identify the current Plan, completed evidence,
uncommitted changes, blockers, and exact next command. Inspect that recovery
summary before running the suggested command.

If the saved Plan really has a phase 2 ready to execute, the next step may be
`/cg-work phase2`. Do not infer readiness from a phase label alone.

**Check:** the recovered state matches the repository; previously completed
checks are not presented as new evidence; unresolved decisions remain visible;
your teammate's work is preserved.

## Pick a different route when the question changes

Estimating poverty, choosing an identification strategy, validating a
predictive model, or writing research conclusions needs the
[research module](../research/index.md). A project may use both suites,
but software correctness does not by itself establish research validity.

See the [complete walkthrough](first-workflow.md),
[workflow chooser](index.md), and [command reference](../reference/commands.md).
