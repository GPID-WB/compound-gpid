# Deliver and Resume

Delivery workflows implement a reviewed plan or a bounded bug fix and preserve
enough state to restart safely.

## Complete a qualified small task

Use `/cg-light-work <task>` only for a qualified small, low-risk technical task.
The first user gate approves and saves the Plan before source edits. The command
then maintains a Work Report and a Review Report. Its mandatory fixed light
Review runs deterministic checks followed by `@cg-code-quality` and
`@cg-testing`. It allows one initial Review pass and, only if Review fixes change
files, one verification pass.

After convergence, the second user gate asks for explicit compounding opt-in.
Skipping compounding has no permanent knowledge side effect. Reproducible bugs
use `/cg-fixbug`; research, statistical, and publication work uses `/cr-*`.
Larger, ambiguous, security-sensitive, schema, dependency, or destructive work
uses `/cg-brainstorm` -> `/cg-plan` -> `/cg-work`.

## Implement a plan

Run `/cg-work` after an approved Plan is saved. It executes that Plan; unmatched
inline tasks receive a copy-ready `/cg-light-work -- <verbatim user task>`
redirect and are not dispatched. For phased work, select a phase explicitly when
needed:

```text
/cg-work phase1
```

The workflow evaluates the plan's completion contract, records executed
evidence, reports deviations, and writes work reports. It should not mark work
complete because code merely looks plausible.

## Fix a reproducible bug

Use `/cg-fixbug` for expected-versus-actual behavior that can be reproduced.
The workflow establishes the expected-behavior source, classifies the test gap,
reproduces the problem, diagnoses the cause, demonstrates red-green evidence,
and verifies the fix before documentation.

## Resume interrupted work

Run `/cg-resume` at the start of a new session. It can use plans, Git history,
work reports, and the compact `.cg-docs/active-state/current.json` record. The
active-state record stores pointers, status, unresolved decisions, and an exact
next command; it is not a transcript or raw-output archive.

## Completion boundary

Delivery is ready for assurance when:

- Required files and behavior exist.
- Relevant validation commands have run.
- Results and failures are recorded accurately.
- Deviations from the plan are accepted or explained.
- High-risk changes have not been silently auto-fixed.

## Related pages

- [Review and Assure](assure.md)
- [Files and Artifacts](../reference/files.md)
- [Detailed Workflow Manual](../workflow.md)
